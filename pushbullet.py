import json
import requests
import os

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory+'/secrets/pushbullet_keys.json') as f:
    pbkeys = json.load(f)
PBKEY = pbkeys['PBKEY']
DEVID = pbkeys['DEVID']


def send_analytics(req):
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": "Carrier: " + req["Carrier"] + "\nOS: " + req["Operating System"] + "\nBrowser: " + req["Browser"] + "\nDate-Time: " + req["Date & Time"] + "\nIP: " + req["Ip Address"],
        "title": "Someone from " + req["City"] + ", " + req["Country"] + " visited your Website @" + req["Page"],
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    try:
        requests.post(url, data=json.dumps(content), headers=headers)
    except Exception as e:
        return (":( An error occurred while sending data to Pushbullet:", {e})

def send_form(formData):
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": "Name: " + formData["name"] + "\nEmail: " + formData["email"] + "\nAbout: " + formData["about"] + "\nMessage: " + formData["message"],
        "title": "Someone sent you a message via contact form",
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    try:
        requests.post(url, data=json.dumps(content), headers=headers)
    except Exception as e:
        return (":( An error occurred while sending data to Pushbullet:", {e})


def delete():
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {'Access-Token': PBKEY}
    try:
        requests.delete(url, headers=headers)
        return ("Deleted All Messages on Pushbullet", 200)
    except Exception as e:
        return (":( An error occurred while deleting data from Pushbullet:", {e})

