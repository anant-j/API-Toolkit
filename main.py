#https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run

from flask import Flask, request,redirect,send_from_directory
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from twilio.twiml.messaging_response import MessagingResponse
import os
import sms_handler
import pushbullet

Known_Users = dict({"2193543988": 'ANANT-WORK', "117193127": 'ANANT-PC', "4069111623":'ANANT-PHONE'})  #Users whose Unique Id is known
Fallback = "https://www.anant-j.com" #Fallback original website
Statuspage = "https://www.anant-j.com/api_status.html"
Auth_Token = "QBLHnUhSdCzrh1DKXYDtR77gMsq4y6Ev"
Auth_Host = "www.anant-j.com"
my_directory = os.path.dirname(os.path.abspath(__file__))

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

#Load Favicon
@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')

# Health Check Route
@app.route('/status')
def health():
  return redirect(Statuspage, code=302)

# Core API to Add Data to Firestore + Push messages via Pushbullet
@app.route('/api', methods=['POST']) #GET requests will be blocked
def add():
  # https://scotch.io/bar-talk/processing-incoming-request-data-in-flask
    req_data = request.get_json()
    Page = req_data['Page']
    Ip = req_data['Ip Address']
    Time = req_data['Date & Time']
    Fid = str(req_data['Fingerprint Id'])

    #Check if User is already known
    if(Fid in Known_Users):
      Fid=Known_Users[Fid]
    else:
      if(req_data['Host']==Auth_Host):
        pushbullet.send(req_data) # Send Notification Function Call
    if(req_data['Host']==Auth_Host): # Hostname Verification to prevent spoofing
      try:
        db.collection(Page).document("UID: "+Fid).collection("IP: "+Ip).document(Time).set(req_data) #Add data to Firebase Firestore
        return ("Sent", 200)
      except Exception as e:
        return (":( An Error Occured while sending data to Firebase:",{e})
    else: #If user is unauthorized to call the api
      return ("Unauthorized User",401)

#Route to Delete All Pushbullet Notifications. # Route to Shut Down API. Uses 256-bit key encryption.
@app.route('/pbdel', methods=['GET'])
def pbdelete():
  AuthCode = request.args.get('auth')
  if(AuthCode==Auth_Token):
    return(pushbullet.delete())
  else:
    return ("Unauthorized User",401)

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

# Handle Internal Server Errors
@app.errorhandler(500)
def e500(e):
  return ("Internal Server Error", 500)

# If user enters wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(e):
  return redirect(Fallback, code=302)

#Run App
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=8080)