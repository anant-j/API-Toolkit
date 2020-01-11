# https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run
from flask import Flask, request, redirect, send_from_directory, abort
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from twilio.twiml.messaging_response import MessagingResponse
import os
import sms_handler
import pushbullet
import github_verify
import git
import json
import params
import file_handler
my_directory = os.path.dirname(os.path.abspath(__file__))

Known_Users = params.Known_Users
Fallback = params.Fallback
Statuspage = params.Statuspage
Auth_Token = params.Auth_Token
Auth_Host = params.Auth_Host

# Initialize Flask App
app = Flask(__name__)
cors = CORS(app)

# Initialize Firestore DB
cred = credentials.Certificate(my_directory+'/secrets/firebase_keys.json')
default_app = initialize_app(cred)
db = firestore.client()

# Basic API Route
@app.route('/')
def redirected():
    return redirect(Fallback, code=302)

# Load Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Health Check Route
@app.route('/status')
def health():
    return ("UP", 200)

# Health Check Route
@app.route('/git')
def gitstats():
    return (str(file_handler.read()), 200)

# Core API to Add Data to Firestore + Push messages via Pushbullet
@app.route('/analytics', methods=['POST'])  # GET requests will be blocked
def add():
    if(my_directory == "/home/stagingapi/mysite"):
        return("Blocked. This is is not available on the staging API.", 401)
    # https://scotch.io/bar-talk/processing-incoming-request-data-in-flask
    req_data = request.get_json()
    Page = req_data['Page']
    Ip = req_data['Ip Address']
    # Ip_details = req_data['Ip Details']
    Time = req_data['Date & Time']
    Fid = str(req_data['Fingerprint Id'])

    # Hostname Verification to prevent spoofing
    if(req_data['Host'] == Auth_Host):
        if(Fid in Known_Users): # Check if User is already registered
            Fid = Known_Users[Fid]
        else:
            pushbullet.send_analytics(req_data)  # Send Pushbullet Notification ( Function Call ) 
        try:
            db.collection(Page).document(Fid).collection("IP: " + Ip).document(Time).set(req_data)  # Add data to Firebase Firestore
            return ("Sent", 200)
        except Exception as e:
            return (":( An Error Occured while sending data to Firebase:", {e})
    else:  # If user is unauthorized to call the api
        return ("Unauthorized User", 401)

# Route to Delete All Pushbullet Notifications. # Route to Shut Down API. Uses 256-bit key encryption.
@app.route('/pbdel', methods=['GET'])
def pbdelete():
    if(my_directory == "/home/stagingapi/mysite"):
        return("Blocked. This is is not available on the staging API.", 401)
    AuthCode = request.args.get('auth')
    if(AuthCode == Auth_Token):
        return(pushbullet.delete())
    else:
        return ("Unauthorized User", 401)

# Route for SMS. Uses Twilio API
@app.route("/sms", methods=["POST"])
def sms_reply():
    if(my_directory == "/home/stagingapi/mysite"):
        return("Blocked. This is is not available on the staging API.", 401)
    message_content = request.values.get('Body', None)
    contact = request.values.get('From', None)
    try:
        res = sms_handler.send_sms(message_content, contact)
        resp = MessagingResponse()
        resp.message(res)
        return ("SMS Message Sent", 200)
    except Exception as e:
        return ("An Error Occured while sending SMS", e)


@app.route('/form', methods=['POST'])
def formdata():
    data=request.form
    # pushbullet.send_form(data)
    return(data)

# CI with GitHub https://medium.com/@aadibajpai/deploying-to-pythonanywhere-via-github-6f967956e664
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
        file_handler.write(branch+","+str(payload['after']))
        return 'Updated PythonAnywhere successfully', 200
    except:
        try:
            repo = git.Repo(my_directory)
            repo.git.reset('--hard')
            origin = repo.remotes.origin
            origin.pull('master')
            file_handler.write("master"+","+str(payload['after']))
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
