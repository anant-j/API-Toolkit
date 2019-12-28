import requests
import time
import json
with open('secrets/distance_matrix_keys.json') as f:
    api_keys = json.load(f)

class TravelTime:
    def __init__(self, start,end):
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        apikey = api_keys["API_key"]
        self.origin=start
        self.destination=end
        querystring = {"units":"metric","departure_time":str(int(time.time())),"traffic_model":"best_guess","origins":self.origin,"destinations":self.destination,"key":apikey}
        headers = {
            'cache-control': "no-cache",
            'postman-token': "something"
            }
        response = requests.request("GET", url, headers=headers, params=querystring)
        result = json.loads(response.text)
        self.current_time=time.strftime("%I:%M:%S")
        self.distance = result['rows'][0]['elements'][0]['distance']['text']
        self.traffic_time= result['rows'][0]['elements'][0]['duration_in_traffic']['text']
        
    def print_distance(self):
        return self.distance
    
    def print_traffictime(self):
        return self.traffic_time