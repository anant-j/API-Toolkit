#https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run

from flask import Flask, request,redirect,send_from_directory
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from twilio.twiml.messaging_response import MessagingResponse
import os
import send_sms
import pushbullet

Known_Users = dict({"2193543988": 'ANANT-WORK', "117193127": 'ANANT-PC', "4069111623":'ANANT-PHONE'})  #Users whose Unique Id is known
Fallback = "https://www.anant-j.com" #Fallback original website
Statuspage = "https://www.anant-j.com/api_status.html"

# Initialize Flask App
app = Flask(__name__)
cors = CORS(app)

# Initialize Firestore DB
cred = credentials.Certificate('secrets/firebase_keys.json')
default_app = initialize_app(cred)
db = firestore.client()

# Basic API Route
@app.route('/')
def redirected(): 
  return redirect(Fallback, code=302)

#Load Favicon
@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')
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
      if(req_data['Host']=="www.anant-j.com"):
        pushbullet.send(req_data) # Send Notification Function Call
    if(req_data['Host']=="www.anant-j.com"): #Hostname Verification to prevent spoofing
      try:
        db.collection(Page).document("UID: "+Fid).collection("IP: "+Ip).document(Time).set(req_data) #Add data to Firebase Firestore
        return ("Sent", 200) 
      except Exception as e:
        return (":( An Error Occured while sending data to Firebase:",{e})
    else: #If user is unauthorized to call the api
      return ("Unauthorized User",401)

#Route to Delete All Pushbullet Notifications
@app.route('/pb', methods=['GET'])
def pbdel():
  pushbullet.delete(request.args.get('auth'))

@app.route("/sms", methods=["GET", "POST"])
def sms_reply():
    location = request.values.get('Body', None)
    contact = request.values.get('From', None)
    res = send_sms.send_sms(location, contact)
    resp = MessagingResponse()
    resp.message(res)
    print("Message received from: " + contact)
    return str(resp)

@app.errorhandler(500)
def e500(e):  
  return ("Internal Server Error", 500)

# If user enter wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(e):  
  return redirect(Fallback, code=302)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    AuthCode = request.args.get('auth')
    if (AuthCode=="AnantJain"):
      shutdown_server()
      return 'Server shut down...'
    else:
      return ("Unauthorized User",401)

#Run App
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=8080)
    # from os import system #For force kill
    # system("pkill -9 python")