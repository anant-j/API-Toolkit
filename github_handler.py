import hmac
import hashlib
import os
import json

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(my_directory + '/secrets/keys.json') as f:
    api_keys = json.load(f)
webhook_key = api_keys['Github_Webhook']


# Checks if Github signature is valid or not
def is_valid_signature(x_hub_signature, data):
    # x_hub_signature and data are from the webhook payload
    # private key is the webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(webhook_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)
