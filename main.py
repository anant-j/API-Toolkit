# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
import json
import os

import git
import ipinfo
from flask import Flask, abort, redirect, request, send_from_directory
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse

import common_methods as utility
import file_handler as file_store
import firebase_handler as firebase
import github_handler as github
import pushbullet_handler as pushbullet
import sms_handler as sms

my_directory = os.path.dirname(os.path.abspath(__file__))


api_keys = {}


def load_keys():
    with open(f'{my_directory}/secrets/keys.json') as f:
        api_keys.update(json.load(f))


load_keys()
Redirect_address = api_keys["Hosts"]["Redirect_address"]
Pushbullet_Delete_Secret = api_keys["Pushbullet"]["Delete"]
Expected_Origin = api_keys["Hosts"]["Origin"]
IP_access_token = api_keys["IpInfo"]
IP_handler = ipinfo.getHandler(IP_access_token)
Rate_limit_buffer = []

# Initialize Flask App
app = Flask(__name__)
# Enabling Cross Origin Resource Sharing
cors = CORS(app)


# Default API Endpoint
@app.route('/')
def homepage():
    return redirect(Redirect_address, code=302)


# Load Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(
            app.root_path,
            'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


# Health Check Endpoint
@app.route('/status')
def health():
    return "UP"


# Rate Limit Check Endpoint
@app.route('/isRateLimited')
def rate_limit_check():
    return str(is_rate_limited(utility.current_time()))


# Git Branch check Endpoint
# Displays the current deployed branch with SHA for Pytest verification
@app.route('/git')
def git_sha():
    return str(file_store.read())


# Function : get_ip_address
# Input :  Request (HTTP)
# Output : Request's IP Address
def get_ip_address(input_request):
    if input_request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return input_request.environ['REMOTE_ADDR']
    else:
        return input_request.environ['HTTP_X_FORWARDED_FOR']


# Endpoint for Analytics
# Goals : Push messages via Pushbullet & Add Data to Firestore
# Request flow : (web) client -> (this) server -> IpInfo API
#                                              -> Pushbullet Notification
#                                              -> Firebase Firestore
@app.route('/analytics', methods=['POST'])  # GET requests will be blocked
def analytics():
    try:
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
            pushbullet.send_analytics(Request_data)
            firebase.upload_analytics(
                Page, Fingerprint, Ip_address, Time, Request_data)
            return "Sent"
        else:
            return "Unauthorized User", 401
    except Exception as error_message:
        return utility.handle_exception("analytics", str(error_message))


# Endpoint for SMS. Uses Twilio API
# This endpoint is expected to be called by Twilio's webhook
@app.route("/sms", methods=["POST"])
def sms_reply():
    try:
        # Receive message content
        message_content = request.values.get('Body', None)
        # Receive sender's info
        contact = request.values.get('From', None)
        # Formulate response
        message = sms.send(message_content, contact)
        # Starting TwiML response
        # https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python
        response = MessagingResponse()
        # Sending SMS
        response.message(message)
        return "SMS Message Sent"
    except Exception as error_message:
        return utility.handle_exception("SMS", str(error_message))


# Endpoint to Delete All Pushbullet Notifications
@app.route('/pbdel', methods=['GET'])
def pushbullet_clear():
    try:
        AuthCode = request.args.get('auth')
        if AuthCode == Pushbullet_Delete_Secret:
            pushbullet.delete()
            return "Deleted All Messages on Pushbullet"
        else:
            return "Unauthorized User", 401
    except Exception as error_message:
        return utility.handle_exception("Pushbullet Delete", str(error_message))


# Endpoint to send contact form data to Pushbullet and Firebase Firestore
@app.route('/form', methods=['POST'])
def form():
    try:
        form_data = request.get_json(force=True)
        pushbullet.send_form(form_data)
        firebase.upload_form(form_data)
        return "Form sent"
    except Exception as error_message:
        return utility.handle_exception("Contact Form Data", str(error_message))


# CI with GitHub & PythonAnywhere
# Author : Aadi Bajpai
# https://medium.com/@aadibajpai/deploying-to-pythonanywhere-via-github-6f967956e664
@app.route('/update_server', methods=['POST'])
def webhook():
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
        origin.pull(branch)
        file_store.write(f'{branch} ,' + str(payload["after"]))
        return f'Updated PythonAnywhere successfully with branch: {branch}'
    except Exception as error_message:
        return utility.handle_exception("Update Server", str(error_message))


# Handle Internal Server Errors
@app.errorhandler(500)
def e500(error_message):
    return "Internal Server Error", 500


# If user enters wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(error_message):
    return redirect(Redirect_address, code=302)


# In memory rate limiting function (Queue/Buffer based)
# Dynamically loads rate limiting parameters from storage
# Returns : boolean value (Rate limited - true or fase)
def rate_limit():
    request_time = utility.current_time()
    Rate_limit_buffer.append(request_time)
    return is_rate_limited(request_time)


# Checks if the request is rate limited or not
# Returns : boolean value (Rate limited - true or fase)
def is_rate_limited(request_time):
    # Reload api_key values (dynamic keys)
    load_keys()
    refresh_buffer(request_time)
    max_requests = api_keys["Rate_Limit"]["Maximum_requests_allowed"]
    # If buffer has more requests than allowed, then rateLimit
    if len(Rate_limit_buffer) > max_requests:
        return True
    return False


# Refreshes buffer by expelling stale requests from buffer
def refresh_buffer(request_time):
    # For each date time value in buffer
    for value in Rate_limit_buffer:
        # If the time difference between current time and stored time
        # is greater than the specified time
        if utility.seconds_between(request_time,
                                   value) >= api_keys["Rate_Limit"]["Seconds"]:
            # Expell that value from the buffer
            Rate_limit_buffer.remove(value)
        # If the difference for the current value
        # isn't greater, it will be smaller for the subsequent ones
        # Therefore, no need to check
        else:
            break


# For debugging purposes only
if __name__ == "__main__":
    app.run(debug=True)
