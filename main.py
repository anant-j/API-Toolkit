# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
import json
import os

import git
import ipinfo
from flask import Flask, abort, redirect, request, send_from_directory
from flask_cors import CORS

import utilities as utility
import firebase_handler as firebase
import github_handler as github
import pushbullet_handler as pushbullet
import sms_handler as sms

my_directory = os.path.dirname(os.path.abspath(__file__))

configuration = {}

""" Reads and storeas API keys """
with open(f'{my_directory}/secrets/keys.json') as f:
    api_keys = json.load(f)


def load_config():
    """ Reads keys and configuration paramters from storage
    and updates in-memory store with the data """
    with open(f'{my_directory}/secrets/config.json') as f:
        configuration.update(json.load(f))


load_config()  # Load keys when application is started
Redirect_address = api_keys["Hosts"]["Redirect_address"]
Pushbullet_Delete_Secret = api_keys["Pushbullet"]["Delete"]
Expected_Origin = api_keys["Hosts"]["Origin"]
IP_access_token = api_keys["IpInfo"]
IP_handler = ipinfo.getHandler(IP_access_token)
Rate_limit_buffer = []
Processing_time = {}  # Stores performance data for each request

# Initialize Flask App
app = Flask(__name__)
# Enabling Cross Origin Resource Sharing
cors = CORS(app)


# Default API Endpoint
@app.route('/')
def homepage():
    return redirect(Redirect_address, code=302)


@app.route('/favicon.ico')
def favicon():
    """ Retrieve Favicon """
    return send_from_directory(
        os.path.join(
            app.root_path,
            'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@app.route('/status')
def health():
    """Health Check Endpoint

    Returns:
        string: Status message confirming the service is functional
    """
    return "UP"


@app.route('/isRateLimited')
def rate_limit_check():
    """Rate Limit Check Endpoint.
    Dynamically checks if API is rate limited based on request time

    Returns:
        string: True/False value based on the Rate Limit status
    """
    return str(is_rate_limited(utility.current_time()))


@app.route('/performance')
def performance():
    """ Performance Check Endpoint.

    Updates the API keys.
    Computes the average time for each key in Processing_time storage map.
    If average is greater than the allowed response time,
    a Pushbullet notification is sent.

    Returns:
        string: A snapshot of the performance check
        that was processed by the request
    """
    try:
        load_config()
        # Making a local copy of the key before it is cleared
        snapshot = Processing_time.copy()
        for key, value in Processing_time.items():
            if len(value) > 0:
                average = float('%.2f' % (sum(value) / len(value)))
                allowed_time = configuration["Performance"]["Allowed"]
                Processing_time[key] = []  # Clear storage for that key
                if average >= allowed_time:
                    pushbullet.send_performance(key, average, allowed_time)
        return (str(snapshot))
    except Exception as error_message:
        return utility.handle_exception("Performance", {error_message})


@app.route('/git')
def git_sha():
    """  Git Branch check Endpoint
    Displays the current deployed branch
    with SHA for Pytest verification

    Returns:
        string: A message in the format of branch, sha
    """
    return str(utility.read("tests/gitstats.txt"))


def get_ip_address(input_request):
    """Gets Ip Address from request

    Args:
        input_request (http request): The request for which the IP Address needs to be retrieved

    Returns:
        string: Request's IP Address
    """
    if input_request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return input_request.environ['REMOTE_ADDR']
    else:
        return input_request.environ['HTTP_X_FORWARDED_FOR']


@app.route('/analytics', methods=['POST'])  # GET requests will be blocked
def analytics():
    """Endpoint for Analytics
    Goals : Push messages via Pushbullet & Add Data to Firestore
    Request flow : (web) client ->  (this) server   ->  IpInfo API
                                                    -> Pushbullet Notification
                                                    -> Firebase Firestore

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()  # Start timer
        Request_data = request.get_json()
        Page = Request_data['Page']
        Time = Request_data['Date & Time']
        Fingerprint = str(Request_data['Fingerprint Id'])
        Ip_address = get_ip_address(request)
        # Using IpInfo Python Library to retrieve IP details
        Ip_details = IP_handler.getDetails(Ip_address)
        Request_data["Ip Address"] = Ip_address
        Request_data.update(Ip_details.all)
        # Hostname Verification
        if request.environ['HTTP_ORIGIN'] == Expected_Origin:
            if rate_limit():
                return "Rate Limited", 429
            if denied(Ip_details.country_name, Ip_address, Fingerprint):
                return ("DENIED", 403)
            pushbullet.send_analytics(Request_data, Fingerprint)
            firebase.upload_analytics(
                Page, Fingerprint, Ip_address, Time, Request_data)
            processing_time = timer.end()
            record_performance("analytics",
                               processing_time)  # Record Performance
            utility.log_request(
                f"analytics : {Fingerprint} - {Ip_address} - {Request_data}",
                processing_time)  # Logging
            return "Sent"
        else:
            return "Unauthorized User", 401
    except Exception as error_message:
        return utility.handle_exception("analytics", {error_message})


@app.route("/sms", methods=["POST"])
def sms_reply():
    """Process incoming request and send response via SMS
    This method/endpoint is expected to be called by Twilio's webhook only

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()
        # Receive message content
        message_content = request.values.get('Body', None)
        # Receive sender's info
        contact = request.values.get('From', None)
        # Send message and assign response
        message = sms.send(message_content, contact)
        processing_time = timer.end()
        record_performance("sms", processing_time)
        utility.log_request(
            f"SMS - From : {contact}, Message : {message_content}, Response : {message}",
            processing_time)
        return "SMS Message Sent"
    except Exception as error_message:
        return utility.handle_exception("SMS", {error_message})


@app.route('/pbdel', methods=['GET'])
def pushbullet_clear():
    """Delete All Pushbullet Notifications

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()
        AuthCode = request.args.get('auth')
        if AuthCode == Pushbullet_Delete_Secret:
            pushbullet.delete()
            processing_time = timer.end()
            record_performance("pb delete", processing_time)
            utility.log_request("Pushbullet Delete", processing_time)
            return "Deleted All Messages on Pushbullet"
        else:
            return "Unauthorized User", 401
    except Exception as error_message:
        return utility.handle_exception(
            "Pushbullet Delete", {error_message})


@app.route('/form', methods=['POST'])
def form():
    """Sends contact form data to Pushbullet and Firebase Firestore

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()
        form_data = request.get_json(force=True)
        pushbullet.send_form(form_data)
        firebase.upload_form(form_data)
        processing_time = timer.end()
        record_performance("form", processing_time)
        utility.log_request("Form Upload", processing_time)
        return "Form sent"
    except Exception as error_message:
        return utility.handle_exception(
            "Contact Form Data", {error_message})


@app.route('/update_server', methods=['POST'])
def webhook():
    """ CI with GitHub & PythonAnywhere
        Author : Aadi Bajpai
        https://medium.com/@aadibajpai/deploying-to-pythonanywhere-via-github-6f967956e664 """
    try:
        event = request.headers.get('X-GitHub-Event')
        # Get payload from GitHub webhook request
        payload = request.get_json()
        x_hub_signature = request.headers.get('X-Hub-Signature')
        # Check if signature is valid
        if not github.is_valid_signature(x_hub_signature, request.data):
            abort(401)
        if event == "ping":
            return json.dumps({'msg': 'Ping Successful!'})
        if event != "push":
            return json.dumps({'msg': "Wrong event type"})
        repo = git.Repo(my_directory)
        branch = payload['ref'][11:]
        # Checking that branch is a non staging deployments
        if my_directory != "/home/stagingapi/mysite":
            if branch != 'master':
                return json.dumps({'msg': 'Not master; ignoring'})
        repo.git.reset('--hard')
        origin = repo.remotes.origin
        try:
            origin.pull(branch)
            utility.write("tests/gitstats.txt",
                          f'{branch} ,' + str(payload["after"]))
            return f'Updated PythonAnywhere successfully with branch: {branch}'
        except Exception:
            origin.pull('master')
            utility.write("tests/gitstats.txt",
                          f'{branch} ,' + str(payload["after"]))
            return 'Updated PythonAnywhere successfully with branch: master'
    except Exception as error_message:
        return utility.handle_exception(
            "Github Update Server", {error_message})


# Handle Internal Server Errors
@app.errorhandler(500)
def e500(error_message):
    return "Internal Server Error", 500


# If user enters wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(error_message):
    return redirect(Redirect_address, code=302)


def rate_limit():
    """ In memory rate limiting function (Queue/Buffer based)
    Dynamically loads rate limiting parameters from storage

    Returns:
        boolean: True/False: Rate Limited
    """
    request_time = utility.current_time()
    Rate_limit_buffer.append(request_time)
    return is_rate_limited(request_time)


def denied(country, ip, fingerprint):
    if (country in configuration["Denied"]["Countries"]) or (ip in configuration["Denied"]["IPs"]) or (fingerprint in configuration["Denied"]["Fingerprints"]):
        return True
    return False


def is_rate_limited(request_time):
    """Checks if the request is rate limited or not

    Args:
        request_time (time): Request Time

    Returns:
        boolean: True/False: Rate Limited
    """
    # Reload config values (dynamic config)
    load_config()
    refresh_buffer(request_time)
    max_requests = configuration["Rate_Limit"]["Maximum_requests_allowed"]
    # If buffer has more requests than allowed, then rateLimit
    if len(Rate_limit_buffer) > max_requests:
        return True
    return False


def refresh_buffer(request_time):
    """ Refreshes buffer by expelling stale requests from buffer

    Args:
        request_time (time): Request Time
    """
    # For each date time value in buffer
    for value in Rate_limit_buffer:
        # If the time difference between current time and stored time
        # is greater than the specified time
        if utility.seconds_between(request_time,
                                   value) >= configuration["Rate_Limit"]["Seconds"]:
            # Expell that value from the buffer
            Rate_limit_buffer.remove(value)
        # If the difference for the current value
        # isn't greater, it will be smaller for the subsequent ones
        # Therefore, no need to check
        else:
            break


def record_performance(caller, time_taken):
    """Adds performance data in global performance storage

    Args:
        caller (string): The caller of the request
        time_taken (float): The time taken to process the request.
    """
    if caller not in Processing_time:
        Processing_time[caller] = []
    Processing_time[caller].append(time_taken)


# # For debugging purposes only
if __name__ == "__main__":
    app.run(debug=True)
