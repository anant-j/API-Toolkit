from twilio.rest import Client
import json
import travel_time_api
with open('secrets/twilio_keys.json') as f:
    tw_keys = json.load(f)

def send_sms(location, contact):
    account_sid = tw_keys['MY_ACCOUNT_SID']
    auth_token = tw_keys['MY_AUTH_TOKEN']
    travel=travel_time_api.TravelTime("229 Emerson Street, Hamilton", "33 Yonge Street, Toronto")
    item=travel.print_traffictime()
    # lst = ["Some", "Data"]
    # items = "\n".join(lst)
    client = Client(account_sid, auth_token)
    client.messages.create(
            to = contact,
            from_ = tw_keys['MY_TWILIO_NUMBER'],
            body=item
        )
