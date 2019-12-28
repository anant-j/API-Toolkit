from twilio.rest import Client
import json
import travel_time_api
with open('secrets/twilio_keys.json') as f:
    tw_keys = json.load(f)


def send_sms(message_content, contact):
    account_sid = tw_keys['MY_ACCOUNT_SID']
    auth_token = tw_keys['MY_AUTH_TOKEN']
    locations=message_decoder(message_content)
    travel = travel_time_api.TravelTime(locations['from'],locations['to'])
    item = travel.print_traffictime()
    # lst = ["Some", "Data"]
    # items = "\n".join(lst)
    client = Client(account_sid, auth_token)
    client.messages.create(
        to=contact,
        from_=tw_keys['MY_TWILIO_NUMBER'],
        body=item
    )


def message_decoder(text):
    first_split = text.split("-")
    result = {}
    for element in first_split:
        element = element.strip()
        el = element.split(":")
        result[el[0].lower()] = el[1].lower().strip()
    return(result)
