import json
import requests
import os

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)
PBKEY = api_keys["Pushbullet"]["Key"]
DEVID = api_keys["Pushbullet"]["DeviceID"]


# Sends analytics data to Pushbullet API
def send_analytics(req):
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": "Carrier: " +
        req["org"] +
        "\nOS: " +
        req["Operating System"] +
        "\nBrowser: " +
        req["Browser"] +
        "\nDate-Time: " +
        req["Date & Time"] +
        "\nIP: " +
        req["Ip Address"],
        "title": "Someone from " +
        req["city"] +
        ", " +
        req["country_name"] +
        " visited your Website @" +
        req["Page"],
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    requests.post(url, data=json.dumps(content), headers=headers)


# Sends Form data to Pushbullet API
def send_form(formData):
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": "Name: " +
        formData["name"] +
        "\nEmail: " +
        formData["email"] +
        "\nAbout: " +
        formData["about"] +
        "\nMessage: " +
        formData["message"],
        "title": "Someone sent you a message via contact form",
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    requests.post(url, data=json.dumps(content), headers=headers)


# Deletes all notifications via Pushbullet API
def delete():
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {'Access-Token': PBKEY}
    requests.delete(url, headers=headers)


# def list_devices():
#     headers = {'Access-Token': PBKEY}
#     response = requests.get(
#         'https://api.pushbullet.com/v2/devices',
#         headers=headers)
#     print(response.text)
