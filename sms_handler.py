import json
import os

import requests
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

import cordinate_converter
import travel_handler as traffic

proxy_client = TwilioHttpClient()
if "https_proxy" in os.environ:
    proxy_client.session.proxies = {'https': os.environ['https_proxy']}

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)

account_sid = api_keys["Twilio"]['MY_ACCOUNT_SID']
auth_token = api_keys["Twilio"]['MY_AUTH_TOKEN']
from_number = api_keys["Twilio"]['MY_TWILIO_NUMBER']
home_location = api_keys["Hosts"]["Home_Location"]

client = Client(account_sid, auth_token, http_client=proxy_client)


def send(message_content, contact):
    original_message = message_content
    message_content = message_content.lower().strip()

    if (message_content == "about" or message_content ==
            "usage" or message_content == "help"):
        response = "\nThank you for using this service. \nThis SMS Service will return distance and traffic time without using any data. \nPlease type:\n 1)'From: Origin Location - To: Destination Location' \n2)Coordinates from Compass App \n3)'BALANCE' for remaining balance.\nThank You"

    elif (message_content == "balance"):
        response = "\n" + balance()

    elif ("°" in message_content and "′" in message_content and "″" in message_content and ("n" in message_content or "w" in message_content or "e" in message_content or "s" in message_content)):
        val = cordinate_converter.coordinates(original_message)
        if (val != "An Error Occurred"):
            cordinate_str = (str(val[0])[0:10] +
                             ", " + str(val[1])[0:10])
            response = generate_route(cordinate_str)
        else:
            response = "Could not process request. Please enter co-ordinates in format: x°y′z″ N  a°b′c″ W"
    else:
        locations = message_decoder(message_content)
        if(locations == "ERROR"):
            response = "Please format your message correctly. Type USAGE for more info!"
        else:
            try:
                response = generate_route(locations['from'], locations['to'])
            except BaseException:
                response = "Travel time cannot be retrieved for the input co-ordinates 😟."

    client.messages.create(
        to=contact,
        from_=from_number,
        body=response
    )


def message_decoder(text):
    try:
        first_split = text.split("-")
        result = {}
        for element in first_split:
            element = element.strip()
            el = element.split(":")
            result[el[0].strip()] = el[1].strip()
        return(result)
    except BaseException:
        return("ERROR")


def balance():
    try:
        response = requests.get(
            'https://api.twilio.com/2010-04-01/Accounts/' +
            account_sid +
            '/Balance.json',
            auth=(
                account_sid,
                auth_token))
        result = json.loads(response.text)
        return ("The account balance is: $" + result["balance"])
    except BaseException:
        return ("The account balance could not be retrieved at this time :(")


def generate_route(origin, destination="home"):
    res = ".\n"
    if destination == "home":
        destination = home_location
    try:
        Route = traffic.TravelTime(
            origin,
            destination)
        res += "Showing travel details for destination: " + destination + "\n"
        res += "Distance : " + Route.distance + "\n"
        res += "Estimated Time : " + Route.traffic_time + "\n"
        res += "ETA : " + traffic.eta(Route.traffic_time_sec) + "\n"
    except BaseException:
        res += "Could not get distance to" + destination
    return (res)
