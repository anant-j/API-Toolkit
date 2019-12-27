#https://cloud.google.com/community/tutorials/building-flask-api-with-cloud-firestore-and-deploying-to-cloud-run

from flask import Flask, request,redirect,send_from_directory
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
import requests,json
import os

with open('pushbullet_keys.json') as f:
    pbkeys = json.load(f)


PBKEY=pbkeys['PBKEY']
DEVID=pbkeys['DEVID']
Known_Users = dict({"1479666974": 'ANANT-WORK', "740348567": 'ANANT-PC', "2668425016":'ANANT-PHONE'})  #Users whose Unique Id is known
Fallback = "https://www.anant-j.com" #Fallback original website

# Initialize Flask App
app = Flask(__name__)
cors = CORS(app)

# Initialize Firestore DB
cred = credentials.Certificate('firebase_key.json')
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
    return ("Up",200)

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
        pbsend(req_data) # Send Notification Function Call
    if(req_data['Host']=="www.anant-j.com"): #Hostname Verification to prevent spoofing
      try:
        db.collection(Page).document("UID: "+Fid).collection("IP: "+Ip).document(Time).set(req_data) #Add data to Firebase Firestore
        return ("Sent", 200) 
      except Exception as e:
        return (":( An Error Occured while sending data to Firebase:",{e})
    else: #If user is unauthorized to call the api
      return ("Unauthorized User",401)

def pbsend(req): #Function to send notification
  url = 'https://api.pushbullet.com/v2/pushes'
  content = {
  "body":"Carrier: " + req["Carrier"] + "\nOS: " + req["Operating System"]+ "\nBrowser: " + req["Browser"] + "\nDate-Time: " + req["Date & Time"] + "\nIP: " + req["Ip Address"],
  "title": "Someone from " + req["City"] + ", " + req["Country"] + " visited your Website @" + req["Page"],
  "device_iden": DEVID,
  "type":"note"}
  headers = {'Access-Token': PBKEY,'content-type': 'application/json'}
  try:
    requests.post(url, data=json.dumps(content), headers=headers)
  except Exception as e:
    return (":( An error occurred while sending data to Pushbullet:",{e})

#Route to Delete All Pushbullet Notifications
@app.route('/pb', methods=['GET'])
def pbdel():
  AuthCode = request.args.get('auth')
  url="https://api.pushbullet.com/v2/pushes"
  headers = {'Access-Token': PBKEY}
  if(AuthCode=="AnantJain"):
    try:
      requests.delete(url, headers=headers)
      return ("Deleted All Messages on Pushbullet",200)
    except Exception as e:
      return (":( An error occurred while deleting data from Pushbullet:",{e})
  else:
    return ("Unauthorized User",401)

# To list all user devices
  # headers = {'Access-Token': PBKEY}
  # s=requests.get('https://api.pushbullet.com/v2/devices',headers=headers)
  # print(s.json())

@app.route("/sms", methods=["GET", "POST"])
def sms_reply():
    location = request.values.get('Body', None)
    contact = request.values.get('From', None)
    res = send_sms.send_sms(location, contact)
    resp = MessagingResponse()
    resp.message(res)
    return str(resp)

@app.errorhandler(500)
def e500(e):  
  return ("Internal Server Error", 500)

# If user enter wrong api link -> Redirect to main website
@app.errorhandler(404)
def e404(e):  
  return redirect(Fallback, code=302)

#Run App
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=8080)