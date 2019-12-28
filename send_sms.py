from twilio.rest import Client
import json
import maps_api
with open('secrets/twilio_keys.json') as f:
    tw_keys = json.load(f)

def send_sms(location, contact):
    account_sid = tw_keys['MY_ACCOUNT_SID']
    auth_token = tw_keys['MY_AUTH_TOKEN']
    travel_time=maps_api.travel_time("229 Emerson Street, Hamilton", "33 Yonge Street, Toronto")
    # lst = ["Some", "Data"]
    # items = "\n".join(lst)
    items=travel_time
    client = Client(account_sid, auth_token)
    client.messages.create(
            to = contact,
            from_ = tw_keys['MY_TWILIO_NUMBER'],
            body=items
        )
