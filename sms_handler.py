from twilio.rest import Client
import json
import travel_time_api
import os
import requests
from twilio.http.http_client import TwilioHttpClient

proxy_client = TwilioHttpClient() 
proxy_client.session.proxies = {'https': os.environ['https_proxy']} 

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory+'/secrets/twilio_keys.json') as f:
    tw_keys = json.load(f)
account_sid = tw_keys['MY_ACCOUNT_SID']
auth_token = tw_keys['MY_AUTH_TOKEN']

client = Client(account_sid, auth_token, http_client=proxy_client)


def send_sms(message_content, contact):
    message_content=message_content.lower().strip()
    if (message_content == "usage"):
        response = "Please format your message in the following format: \n'From: Origin Location - To: Destination Location' \nThank you."

    elif (message_content == "about"):
        response = "\nThank you for using this service. \nThis SMS Service will return distance and traffic time without using any data. \nPlease type 'USAGE' for mor info." 

    elif (message_content == "balance"):
        response = "\n"+balance()

    elif (message_content == "bus home"):
        time = travel_time_api.bus_home()
        response = "The estimated total time to reach home by bus is: "+time

    elif (message_content == "go to work"):
        time = travel_time_api.gowork()
        response = "The estimated total time to reach work by bus is: "+time

    else:
        locations = message_decoder(message_content)
        if(locations=="ERROR"):
            response = "Please format your message correctly. Type USAGE for more info!"       
        else:
            try:
                travel = travel_time_api.TravelTime(
                    locations['from'], locations['to'])
                traffictime = travel.get_traffictime()
                distance = travel.get_distance()
                response = "The distance is: "+distance + \
                    ". The travel time with traffic right now is: "+traffictime
            except:
                response = "Travel time cannot be retrieved for the input co-ordinates 😟."
    
    client.messages.create(
        to=contact,
        from_=tw_keys['MY_TWILIO_NUMBER'],
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
    except:
        return("ERROR")


def balance():
    try:
        response = requests.get('https://api.twilio.com/2010-04-01/Accounts/'+account_sid+'/Balance.json', auth=(account_sid, auth_token))
        result = json.loads(response.text)
        return ("The account balance is: $"+result["balance"])
    except:
        return ("The account balance could not be retrieved at this time :(")

