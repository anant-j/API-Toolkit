# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
from flask import Flask, request, redirect, send_from_directory, abort
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from twilio.twiml.messaging_response import MessagingResponse
import ipinfo
import os
import sms_handler
import pushbullet
import github_verify
import git
import json
import file_handler
my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)

Fallback = api_keys["Hosts"]["Fallback"]
Pushbullet_Delete_Secret = api_keys["Pushbullet"]["Delete"]
Expected_Origin = api_keys["Hosts"]["Origin"]
IP_access_token = api_keys["IpInfo"]
IP_handler = ipinfo.getHandler(IP_access_token)

# Initialize Flask App
app = Flask(__name__)
cors = CORS(app)

# Initialize Firestore DB
cred = credentials.Certificate(my_directory + '/secrets/firebase_keys.json')
default_app = initialize_app(cred)
db = firestore.client()


# Basic API Route
@app.route('/')
def redirected():
    return redirect(Fallback, code=302)


# Load Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(
            app.root_path,
            'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


# Health Check Route
@app.route('/status')
def health():
    return ("UP", 200)


# Git Branch check Route
@app.route('/git')
def gitstats():
    return (str(file_handler.read()), 200)


def get_ip(req):
    try:
        if req.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return req.environ['REMOTE_ADDR']
        else:
            return req.environ['HTTP_X_FORWARDED_FOR']
    except Exception:
        return 0


# Core API to Add Data to Firestore + Push messages via Pushbullet
@app.route('/analytics', methods=['POST'])  # GET requests will be blocked
def add():
    # https://scotch.io/bar-talk/processing-incoming-request-data-in-flask
    req_data = request.get_json()
    Page = req_data['Page']
    Ip_address = get_ip(request)
    Ip_details = IP_handler.getDetails(Ip_address)
    req_data["Ip Address"] = Ip_address
    req_data.update(Ip_details.all)
    Time = req_data['Date & Time']
    Fid = str(req_data['Fingerprint Id'])
    # Hostname Verification to prevent spoofing
    if(request.environ['HTTP_ORIGIN'] == Expected_Origin):
        try:
            # Send Pushbullet Notification ( Function Call )
            pushbullet.send_analytics(req_data)
            # Add data to Firebase Firestore
            db.collection(Page).document(Fid).collection(
                "IP: " + Ip_address).document(Time).set(req_data)
            return ("Sent", 200)
        except Exception as e:
            return (":( An Error Occured while sending data to Firebase:", {e})
    else:  # If user is unauthorized to call the api
        return ("Unauthorized User", 401)


# Route for SMS. Uses Twilio API
@app.route("/sms", methods=["POST"])
def sms_reply():
    message_content = request.values.get('Body', None)
    contact = request.values.get('From', None)
    try:
        res = sms_handler.send_sms(message_content, contact)
        resp = MessagingResponse()
        resp.message(res)
        return ("SMS Message Sent", 200)
    except Exception as e:
        return ("An Error Occured while sending SMS", e)


# Route to Delete All Pushbullet Notifications
# Uses 256-bit key encryption.
@app.route('/pbdel', methods=['GET'])
def pbdelete():
    AuthCode = request.args.get('auth')
    if(AuthCode == Pushbullet_Delete_Secret):
        return(pushbullet.delete())
    else:
        return ("Unauthorized User", 401)


@app.route('/form', methods=['POST'])
def formdata():
    try:
        data = request.get_json(force=True)
        pushbullet.send_form(data)
        db.collection("Form").document(data["email"]).set(
            data)  # Add data to Firebase Firestore
        return("Form sent")
    except BaseException:
        return("Form Could not be sent", 500)


# CI with GitHub
# https://medium.com/@aadibajpai/deploying-to-pythonanywhere-via-github-6f967956e664
@app.route('/update_server', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.get_json()
    x_hub_signature = request.headers.get('X-Hub-Signature')
    if not github_verify.is_valid_signature(x_hub_signature, request.data):
        print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
        abort(401)
    if event == "ping":
        return json.dumps({'msg': 'Ping Successful!'})
    if event != "push":
        return json.dumps({'msg': "Wrong event type"})

    if(my_directory != "/home/stagingapi/mysite"):
        if payload['ref'] != 'refs/heads/master':
            return json.dumps({'msg': 'Not master; ignoring'})
    try:
        repo = git.Repo(my_directory)
        branch = str(payload['ref'][11:])
        repo.git.reset('--hard')
        origin = repo.remotes.origin
        origin.pull(branch)
        file_handler.write(branch + "," + str(payload['after']))
        return 'Updated PythonAnywhere successfully', 200
    except BaseException:
        try:
            repo = git.Repo(my_directory)
            repo.git.reset('--hard')
            origin = repo.remotes.origin
            origin.pull('master')
            file_handler.write("master" + "," + str(payload['after']))
            return 'Updated PythonAnywhere successfully(Master branch)', 200
        except Exception as e:
            return (str(e))


# Handle Internal Server Errors
@app.errorhandler(500)
def e500(e):
    return ("Internal Server Error", 500)


# If user enters wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(e):
    return redirect(Fallback, code=302)


# if (__name__ == "__main__"):
#     app.run(debug=True)
