from twilio.rest import Client
import json
import travel_time_api
import os
import requests
import timings
import cordinate_converter
from twilio.http.http_client import TwilioHttpClient

proxy_client = TwilioHttpClient()
# proxy_client.session.proxies = {'https': os.environ['https_proxy']}

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)

account_sid = api_keys["Twilio"]['MY_ACCOUNT_SID']
auth_token = api_keys["Twilio"]['MY_AUTH_TOKEN']
from_number = api_keys["Twilio"]['MY_TWILIO_NUMBER']

client = Client(account_sid, auth_token, http_client=proxy_client)


def send(message_content, contact):
    original_message = message_content
    message_content = message_content.lower().strip()

    if (message_content == "about" or message_content ==
            "usage" or message_content == "help"):
        response = "\nThank you for using this service. \nThis SMS Service will return distance and traffic time without using any data. \nPlease type:\n 1)'From: Origin Location - To: Destination Location' \n2)Coordinates from Compass App \n3)'BALANCE' for remaining balance.\n4)'Bus Home' for saved route.\n5)'Go to work' for saved route.\n6)'Next Bus' for upcoming bus service \n7)'Next Train' for upcoming train service. \nThank You"

    elif (message_content == "balance"):
        response = "\n" + balance()

    elif (message_content == "bus home"):
        time = travel_time_api.bus_home()
        response = "The estimated total time to reach home by bus is: " + time

    elif (message_content == "go to work"):
        time = travel_time_api.gowork()
        response = "The estimated total time to reach work by bus is: " + time

    elif (message_content == "next bus"):
        response = bus_timing()

    elif (message_content == "next train"):
        response = train_timing()

    elif ("°" and "′" and "″" and ("n" or "w" or "e" or "s") in message_content):
        val = cordinate_converter.coordinates(original_message)
        if (val != "An Error Occurred"):
            response = travel_time_api.coordinater(val)
        else:
            response = "Could not process request. Please enter co-ordinates in format: x°y′z″ N  a°b′c″ W"
    else:
        locations = message_decoder(message_content)
        if(locations == "ERROR"):
            response = "Please format your message correctly. Type USAGE for more info!"
        else:
            try:
                travel = travel_time_api.TravelTime(
                    locations['from'], locations['to'])
                traffictime = travel.get_traffictime()
                distance = travel.get_distance()
                response = "The distance is: " + distance + \
                    ". The travel time with traffic right now is: " + traffictime
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
            result[el[0]] = el[1].strip()
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


def bus_timing():
    fs = "\nNext Bus:\n"
    time = ""
    b15mt = timings.b15mt
    b16th = timings.b16th
    b16ht = timings.b16ht
    try:
        curr_time = str(travel_time_api.current_time().time())[0:5]
    except BaseException:
        return("Time Fetching Error :(")
    try:
        r1 = (list(b15mt.keys()))
        for time in r1:
            if time >= curr_time:
                fs = fs + "15: McMaster - Toronto @ " + \
                    time + "-" + str(b15mt[time]) + "\n"
                time = ""
                break
        r2 = (list(b16th.keys()))
        for time in r2:
            if time >= curr_time:
                fs = fs + "16: Toronto - Hamilton @ " + \
                    time + "-" + str(b16th[time]) + "\n"
                time = ""
                break
        r3 = (list(b16ht.keys()))
        for time in r3:
            if time >= curr_time:
                fs = fs + "16: Hamilton - Toronto @ " + \
                    time + "-" + str(b16ht[time]) + "\n"
                time = ""
                break
        if fs == "\nNext Bus:\n":
            return("No Bus Available")
        return(fs)
    except BaseException:
        return("Bus timings could not be retrieved :(")


def train_timing():
    fs = "\nNext Train:\n"
    time = ""
    tLWht = timings.tLWht
    tLEth = timings.tLEth
    try:
        curr_time = str(travel_time_api.current_time().time())[0:5]
    except BaseException:
        return("Time Fetching Error :(")
    try:
        r1 = (list(tLWht.keys()))
        for time in r1:
            if time >= curr_time:
                fs = fs + "LW: Hamilton - Toronto @ " + \
                    time + "-" + str(tLWht[time]) + "\n"
                time = ""
                break
        r2 = (list(tLEth.keys()))
        for time in r2:
            if time >= curr_time:
                fs = fs + "LE: Toronto - Hamilton @ " + \
                    time + "-" + str(tLEth[time]) + "\n"
                time = ""
                break
        if fs == "\nNext Train:\n":
            return("No Trains Available")
        return(fs)
    except BaseException:
        return("Bus timings could not be retrieved :(")
