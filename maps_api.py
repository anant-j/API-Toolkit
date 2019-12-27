import requests
import time
import json

with open('maps_keys.json') as f:
    map_keys = json.load(f)

def travel_time(from_add, to_add):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    querystring = {"units":"metric","departure_time":str(int(time.time())),"traffic_model":"best_guess","origins":from_add,"destinations":to_add,"key":map_keys["API_key"]}

    headers = {
        'cache-control': "no-cache",
        'postman-token': "something"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)
    d = json.loads(response.text)
    # print(d)
    print("On", time.strftime("%I:%M:%S"),"time duration is",d['rows'][0]['elements'][0]['duration']['text'], " & traffic time is ",d['rows'][0]['elements'][0]['duration_in_traffic']['text'])
    # print(response.text)
    return (response.text)