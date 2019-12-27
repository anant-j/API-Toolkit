from twilio.rest import Client
import json

with open('twilio_keys.json') as f:
    tw_keys = json.load(f)


def send_sms(location, contact):
    
    # lst = []
    
    account_sid = tw_keys['MY_ACCOUNT_SID']
    auth_token = tw_keys['MY_AUTH_TOKEN']
    
    # lst = ["Some", "Data"]
    # items = "\n".join(lst)
    items=location
    client = Client(account_sid, auth_token)
    client.messages.create(
            to = contact,
            from_ = tw_keys['MY_TWILIO_NUMBER'],
            body=items
        )
