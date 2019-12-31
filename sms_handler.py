from twilio.rest import Client
import json
import travel_time_api
import os
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
    if (message_content.lower().strip()=="usage"):
        response ="\nThank you for using this service. \nPlease format your message in the following format: \n'From: Origin Location - To: Destination Location' \nThank you"
    elif(message_content.lower().strip()=="verify"):
        verify(contact)
    else:
        try:
            locations = message_decoder(message_content)
            travel = travel_time_api.TravelTime(locations['from'], locations['to'])
            traffictime = travel.print_traffictime()
            distance = travel.print_distance()
            response = "The distance is: "+distance + \
                ". The travel time with traffic right now is: "+traffictime
        except:
            response = "Please format your message correctly. Type usage for more info!"
    client.messages.create(
        to=contact,
        from_=tw_keys['MY_TWILIO_NUMBER'],
        body=response
    )


def message_decoder(text):
    first_split = text.split("-")
    result = {}
    for element in first_split:
        element = element.strip()
        el = element.split(":")
        result[el[0].lower()] = el[1].lower().strip()
    return(result)

def verify(contact):
    try:
        validation_request = client.validation_requests \
                            .create(
                                    friendly_name=contact,
                                    phone_number=contact,
                                )
        print(validation_request.friendly_name)
        return ("Contact created")
    except:
        return ("An Error Occured")