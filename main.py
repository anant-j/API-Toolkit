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
# Depreciated, using Telegram in place of Pushbullet
# import pushbullet_handler as pushbullet
import telegram_handler as telegram
import sms_handler as sms

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
Expected_Origin = api_keys["Hosts"]["Origin"]
IP_access_token = api_keys["IpInfo"]
IP_handler = ipinfo.getHandler(IP_access_token)
Processing_time = {}  # Stores performance data for each request

# Initialize Flask App
app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
# Enabling Cross Origin Resource Sharing
cors = CORS(app)


# Default API Endpoint
@app.route('/')
@limiter.exempt
def homepage():
    return redirect(Redirect_address, code=302)


@app.route('/favicon.ico')
@limiter.exempt
def favicon():
    """ Retrieve Favicon """
    return send_from_directory(
        os.path.join(
            app.root_path,
            'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


@app.route('/status')
@limiter.exempt
def health():
    """Health Check Endpoint

    Returns:
        string: Status message confirming the service is functional
    """
    return "UP"


@app.route('/performance')
@limiter.exempt
def performance():
    """ Performance Check Endpoint.

    Updates the API keys.
    Computes the average time for each key in Processing_time storage map.
    If average is greater than the allowed response time,
    a Telegram notification is sent.

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
                    telegram.send_performance(key, average, allowed_time)
        return (str(snapshot))
    except Exception as error_message:
        return utility.handle_exception("Performance", {error_message})


@app.route('/git')
@limiter.exempt
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
@limiter.limit(configuration["Rate_Limit"]["Analytics"], deduct_when=lambda response: response.status_code == 200)
def analytics():
    """Endpoint for Analytics
    Goals : Push messages via Telegram & Add Data to Firestore
    Request flow : (web) client ->  (this) server   ->  IpInfo API
                                                    -> Telegram Notification
                                                    -> Firebase Firestore

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()  # Start timer
        Request_data = request.get_json()
        Page = Request_data['Page']
        if (Page == "DENIED"):
            return "Allowed", 200
        Time = Request_data['Date & Time']
        Fingerprint = str(Request_data['Fingerprint Id'])
        Ip_address = get_ip_address(request)
        # Using IpInfo Python Library to retrieve IP details
        Ip_details = IP_handler.getDetails(Ip_address)
        Request_data.update(Ip_details.all)
        # Hostname Verification
        if request.environ['HTTP_ORIGIN'] == Expected_Origin:
            if denied(Ip_details.country_name, Ip_address, Fingerprint):
                firebase.upload_analytics("DENIED", Ip_details.country_name, Ip_details.city, Fingerprint, Ip_address, Time, Request_data)
                return "DENIED", 403
            if not ignored(Ip_address, Fingerprint):
                telegram.send_analytics(Request_data, Fingerprint)
            firebase.upload_analytics(
                Page, Ip_details.country_name, Ip_details.city, Fingerprint, Ip_address, Time, Request_data)
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
@limiter.limit(configuration["Rate_Limit"]["SMS"])
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


@app.route('/form', methods=['POST'])
@limiter.limit(configuration["Rate_Limit"]["FORM"], deduct_when=lambda response: response.status_code == 200)
def form():
    """Sends contact form data to Telegram and Firebase Firestore

    Returns:
        string: Success/Error Message
    """
    try:
        timer = utility.Timer()
        form_data = request.get_json(force=True)
        parsed_data = {}
        parsed_data["name"] = str(form_data["name"])
        parsed_data["email"] = str(form_data["email"])
        parsed_data["about"] = str(form_data["about"])
        parsed_data["message"] = str(form_data["message"])
        telegram.send_form(parsed_data)
        firebase.upload_form(parsed_data)
        processing_time = timer.end()
        record_performance("form", processing_time)
        utility.log_request("Form Upload", processing_time)
        return "Form sent"
    except Exception as error_message:
        return utility.handle_exception(
            "Contact Form Data", {error_message})


@app.route('/update_server', methods=['POST'])
@limiter.exempt
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


@app.errorhandler(429)
def ratelimit_handler(e):
    return "DENIED", 429


def denied(country, ip, fingerprint):
    if (country in configuration["Denied"]["Countries"]) or (ip in configuration["Denied"]["IPs"]) or (fingerprint in configuration["Denied"]["Fingerprints"]):
        return True
    return False


def ignored(ip, fingerprint):
    if (ip in configuration["Ignored"]["IPs"]) or (fingerprint in configuration["Ignored"]["Fingerprints"]):
        return True
    return False


@limiter.request_filter
def ip_whitelist():
    return request.remote_addr in configuration["Ignored"]["IPs"]


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
