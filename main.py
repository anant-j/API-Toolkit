# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
import json
import os

import git
import ipinfo
from flask import Flask, abort, redirect, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.messaging_response import MessagingResponse

# Importing local "modules"/libraries
import file_handler as file_store
import firebase_handler as firebase
import github_handler as github
import pushbullet_handler as pushbullet
import sms_handler as sms
# import common_methods as utility

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)

Redirect_address = api_keys["Hosts"]["Redirect_address"]
Pushbullet_Delete_Secret = api_keys["Pushbullet"]["Delete"]
Expected_Origin = api_keys["Hosts"]["Origin"]
IP_access_token = api_keys["IpInfo"]
IP_handler = ipinfo.getHandler(IP_access_token)

# Initialize Flask App
app = Flask(__name__)
# Enabling Cross Origin Resource Sharing
cors = CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "5 per minute"]
)

# Default API Endpoint
@app.route('/')
@limiter.exempt
def homepage():
    return redirect(Redirect_address, code=302)


# Load Favicon
@app.route('/favicon.ico')
@limiter.exempt
def favicon():
    return send_from_directory(
        os.path.join(
            app.root_path,
            'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


# Health Check Endpoint
@app.route('/status')
@limiter.exempt
def health():
    return ("UP", 200)


# Git Branch check Endpoint
# Displays the current deployed branch with SHA for Pytest verification
@app.route('/git')
@limiter.exempt
def git_sha():
    return (str(file_store.read()), 200)


# Function : get_ip_address
# Input :  Request (HTTP)
# Output : Request's IP Address
def get_ip_address(input_request):
    try:
        if input_request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return input_request.environ['REMOTE_ADDR']
        else:
            return input_request.environ['HTTP_X_FORWARDED_FOR']
    except Exception:
        return 0


# Endpoint for Analytics
# Goals : Push messages via Pushbullet + Add Data to Firestore
# Request flow : (web) client -> (this) server -> IpInfo API
#                                              -> Pushbullet Notification
#                                              -> Firebase Firestore
@app.route('/analytics', methods=['POST'])  # GET requests will be blocked
def analytics():
    # https://scotch.io/bar-talk/processing-incoming-request-data-in-flask
    Request_data = request.get_json()
    # Get required parameters from request and assign to variables
    Page = Request_data['Page']
    Time = Request_data['Date & Time']
    Fingerprint = str(Request_data['Fingerprint Id'])
    # Get request's IP Address
    Ip_address = get_ip_address(request)
    # Using IpInfo Python Library to retrieve IP details
    Ip_details = IP_handler.getDetails(Ip_address)
    # Adding Ip Address to our dataset (for uploading)
    Request_data["Ip Address"] = Ip_address
    # Updating dataset with Ip information
    Request_data.update(Ip_details.all)
    # Hostname Verification to prevent spoofing
    if (request.environ['HTTP_ORIGIN'] == Expected_Origin):
        # if (rate_limit()): # For in-house rate limiter
        #     return ("Rate Limited")
        try:
            # Send Pushbullet Notification ( Function Call )
            pushbullet.send_analytics(Request_data)
            # Add data to Firebase Firestore
            firebase.upload_analytics(
                Page, Fingerprint, Ip_address, Time, Request_data)
            return ("Sent", 200)
        except Exception as e:
            return ("An Error occurred while sending data to Firebase:", {e})
    else:  # If user is unauthorized to call the api
        return ("Unauthorized User", 401)


# Endpoint for SMS. Uses Twilio API
# This endpoint is expected to be called by Twilio's webhook
@app.route("/sms", methods=["POST"])
def sms_reply():
    # Receive message content
    message_content = request.values.get('Body', None)
    # Receive sender's info
    contact = request.values.get('From', None)
    try:
        # Formulate response
        message = sms.send(message_content, contact)
        # Starting TwiML response
        # https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python
        response = MessagingResponse()
        # Sending SMS
        response.message(message)
        return ("SMS Message Sent", 200)
    except Exception as e:
        return ("An Error Occurred while sending SMS", e)


# Endpoint to Delete All Pushbullet Notifications
@app.route('/pbdel', methods=['GET'])
@limiter.exempt
def pushbullet_clear():
    # Get authorization code provided in request
    AuthCode = request.args.get('auth')
    # Check if authorization code is valid
    if (AuthCode == Pushbullet_Delete_Secret):
        # Delete all notifications
        return (pushbullet.delete())
    else:
        return ("Unauthorized User", 401)


# Endpoint to send contact form data to Pushbullet and Firebase Firestore
@app.route('/form', methods=['POST'])
def form():
    try:
        # Get Form data
        form_data = request.get_json(force=True)
        # Send Form data to Pushbullet
        pushbullet.send_form(form_data)
        # Send Form data to Firebase
        firebase.upload_form(form_data)
        return ("Form sent")
    except BaseException:
        return ("Form Could not be sent", 500)


# CI with GitHub & PythonAnywhere
# Author : Aadi Bajpai
# https://medium.com/@aadibajpai/deploying-to-pythonanywhere-via-github-6f967956e664
@app.route('/update_server', methods=['POST'])
@limiter.exempt
def webhook():
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
    # Checking that branch is master for non staging deployments
    if (my_directory != "/home/stagingapi/mysite"):
        if payload['ref'] != 'refs/heads/master':
            return json.dumps({'msg': 'Not master; ignoring'})
    try:
        repo = git.Repo(my_directory)
        branch = str(payload['ref'][11:])
        repo.git.reset('--hard')
        origin = repo.remotes.origin
        origin.pull(branch)
        file_store.write(branch + "," + str(payload['after']))
        return 'Updated PythonAnywhere successfully', 200
    except BaseException:
        try:
            repo = git.Repo(my_directory)
            repo.git.reset('--hard')
            origin = repo.remotes.origin
            origin.pull('master')
            file_store.write("master" + "," + str(payload['after']))
            return 'Updated PythonAnywhere successfully (Master branch)', 200
        except Exception as e:
            return (str(e))


# Handle Internal Server Errors
@app.errorhandler(500)
def e500(e):
    return ("Internal Server Error", 500)


# If user enters wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(e):
    return redirect(Redirect_address, code=302)


## For debugging purposes only
# if (__name__ == "__main__"):
#     app.run(debug=True)


#  --------------------------------------------------------------

# Rate_limit_storage = {}
# # In memory rate limiting function (Hashmap based)
# # Dynamically loads rate limiting parameters from storage (keys)
# # Returns boolean value (Rate limited - true or fase)
# def rate_limit():
#     # Setting the initial rate limit flag to false
#     rate_limit_flag = False
#     # Get current request time
#     request_time = utility.current_time()
#     # Initialize key-value if the in-memory storage is not set up properly
#     if ("Last_request_time" not in Rate_limit_storage):
#         Rate_limit_storage["Last_request_time"] = request_time
#     # Initialize key-value if the in-memory storage is not set up properly
#     if ("Number_of_requests" not in Rate_limit_storage):
#         Rate_limit_storage["Number_of_requests"] = 0
#     # Set last request's time (local variable) from storage
#     last_request_time = Rate_limit_storage["Last_request_time"]
#     # Compute seconds between current request and last request
#     time_difference = utility.seconds_between(request_time, last_request_time)
#     # Check if time difference is greater than allowed
#     if time_difference >= api_keys["Rate_Limit"]["Seconds"]:
#         # Since elapsed time is more than allowed time
#         # Set Number of requests as 1
#         Rate_limit_storage["Number_of_requests"] = 1
#     # Time elapsed is less than specified time
#     else:
#         # If number of requests is greater than allowed requests in given time
#         if (Rate_limit_storage["Number_of_requests"] >=
#                 api_keys["Rate_Limit"]["Maximum_requests_allowed"]):
#             # Set rate limited flag to True
#             rate_limit_flag = True
#         # Increase number of requests by 1
#         Rate_limit_storage["Number_of_requests"] += 1
#     # Set latest request time as current request's time
#     Rate_limit_storage["Last_request_time"] = request_time
#     return rate_limit_flag


#  --------------------------------------------------------------

# Rate_limit_buffer = []
# # In memory rate limiting function (Queue based)
# # Dynamically loads rate limiting parameters from storage (keys)
# # Returns boolean value (Rate limited - true or fase)
# def rate_limit():
#     # Get current request time
#     request_time = utility.current_time()
#     # Append request time to buffer
#     Rate_limit_buffer.append(request_time)
#     # Return if request is rate limited according to the request time
#     return (is_rate_limited(request_time))


# # Checks if the request is rate limited or not
# def is_rate_limited(request_time):
#     # Refresh buffer
#     refresh_rate_limit(request_time)
#     # If buffer has more requests than allowed, then rateLimit
#     if (len(Rate_limit_buffer) >
#             api_keys["Rate_Limit"]["Maximum_requests_allowed"]):
#         return True
#     # Return False if buffer can accomodate the request
#     return False


# # Refreshes buffer by expelling stale requests
# def refresh_rate_limit(request_time):
#     # For each date time value is buffer
#     for value in Rate_limit_buffer:
#         # If the time difference between current time and stored time
#         # is greater than the specified time
#         if (utility.seconds_between(request_time, value)
#                 >= api_keys["Rate_Limit"]["Seconds"]):
#             # Expell that value from the buffer
#             Rate_limit_buffer.remove(value)

# Rate Limit Check Endpoint
# @app.route('/isRateLimited')
# def rate_limit_check():
#     rate_limit()
#     return (str(is_rate_limited(utility.current_time())))

#  --------------------------------------------------------------
