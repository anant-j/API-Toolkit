import json
import requests
import os

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(f'{my_directory}/secrets/keys.json') as f:
    api_keys = json.load(f)
PBKEY = api_keys["Pushbullet"]["Key"]
DEVID = api_keys["Pushbullet"]["DeviceID"]


def send_analytics(req, fingerprint):
    """Sends analytics data to Pushbullet API

    Args:
        req (dict): Hashmap containing request information
    """
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": f'Carrier: {req["org"]} \nOS: {req["Operating System"]} \nBrowser: {req["Browser"]} \nDate-Time: {req["Date & Time"]} \nIP: {req["Ip Address"]}\nFingerprint: {fingerprint}',
        "title": f'Someone from {req["city"]} , {req["country_name"]} visited your Website @ {req["Page"]}',
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    requests.post(url, data=json.dumps(content), headers=headers)


def send_form(formData):
    """Sends Form data to Pushbullet API

    Args:
        formData (dict): Hashmap containing form data
    """
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": f'Name: {formData["name"]} \nEmail: {formData["email"]} \nAbout: {formData["about"]}  \nMessage: {formData["message"]}',
        "title": "Someone sent you a message via contact form",
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    requests.post(url, data=json.dumps(content), headers=headers)


def send_performance(name, response_time, allowed):
    """Sends Performance data to Pushbullet API

    Args:
        name (string): The name of the endpoint that the alert is raised for
        response_time (float): The average response time for the alert
        allowed (float): The allowed response time for the service
    """
    url = 'https://api.pushbullet.com/v2/pushes'
    content = {
        "body": f'The {name} endpoint took an average of : {response_time} to compute \n while the allowed time is : {allowed}',
        "title": "Performance Alert",
        "device_iden": DEVID,
        "type": "note"}
    headers = {'Access-Token': PBKEY, 'content-type': 'application/json'}
    requests.post(url, data=json.dumps(content), headers=headers)


def delete():
    """Deletes all notifications via Pushbullet API"""
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {'Access-Token': PBKEY}
    requests.delete(url, headers=headers)


# def list_devices():
#     """ Lists all Devices registered with Pushbullet Account """
#     headers = {'Access-Token': PBKEY}
#     response = requests.get(
#         'https://api.pushbullet.com/v2/devices',
#         headers=headers)
#     print(response.text)
