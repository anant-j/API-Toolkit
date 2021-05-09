import json
import requests
import os

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(f'{my_directory}/secrets/keys.json') as f:
    api_keys = json.load(f)
TGKEY = api_keys["Telegram"]["Key"]
DEVID = api_keys["Telegram"]["DeviceID"]


def send_analytics(req, fingerprint):
    """Sends analytics data to Telegram API

    Args:
        req (dict): Hashmap containing request information
    """
    content = f'Someone from {req["city"]} , {req["country_name"]} visited your Website @ {req["Page"]} \nCarrier: {req["org"]} \nOS: {req["Operating System"]} \nBrowser: {req["Browser"]} \nDate-Time: {req["Date & Time"]} \nIP: {req["ip"]}\nFingerprint: {fingerprint}'
    push(content)


def send_form(formData):
    """Sends Form data to Telegram API

    Args:
        formData (dict): Hashmap containing form data
    """
    content = f'Someone sent you a message via contact form.\nName: {formData["name"]}\nEmail: {formData["email"]}\nAbout: {formData["about"]}\nMessage: {formData["message"]}'
    push(content)


def send_performance(name, response_time, allowed):
    """Sends Performance data to Telegram API

    Args:
        name (string): The name of the endpoint that the alert is raised for
        response_time (float): The average response time for the alert
        allowed (float): The allowed response time for the service
    """
    content = f'Perfomance Alert\nThe {name} endpoint took an average of : {response_time} to compute \n while the allowed time is : {allowed}'
    push(content)


def push(content):
    url = f'https://api.telegram.org/{TGKEY}/sendMessage?text={content}&chat_id={DEVID}'
    requests.post(url)