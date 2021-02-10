import json
import os
from datetime import timedelta

import requests
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

import utilities as utility
import cordinate_converter

proxy_client = TwilioHttpClient()
if "https_proxy" in os.environ:
    proxy_client.session.proxies = {'https': os.environ['https_proxy']}

my_directory = os.path.dirname(os.path.abspath(__file__))
with open(f'{my_directory}/secrets/keys.json') as f:
    api_keys = json.load(f)

account_sid = api_keys["Twilio"]['MY_ACCOUNT_SID']
auth_token = api_keys["Twilio"]['MY_AUTH_TOKEN']
from_number = api_keys["Twilio"]['MY_TWILIO_NUMBER']
home_location = api_keys["Hosts"]["Home_Location"]

client = Client(account_sid, auth_token, http_client=proxy_client)


def send(message_content, contact):
    """ Formulate Twilio Response based on request Content

    Args:
        message_content (string): The message content from Twilio Request
        contact (string): Phone Number to which the response should be sent

    Returns:
        string: response content that was sent to contact
    """
    try:
        original_message = message_content
        message_content = message_content.lower().strip()

        if any(word in message_content for word in ["about", "usage", "help"]):
            response = "\nThank you for using this service. \nThis SMS Service will return distance and traffic time without using any data." + \
                "\nPlease type:\n 1)'From: Origin Location - To: Destination Location' " + \
                "\n2)Coordinates from Compass App \n3)'BALANCE' for remaining balance.\nThank You"

        elif message_content == "balance":
            response = f'\n{balance()}'

        elif all(char in message_content for char in ["°", "′", "″"]):
            val = cordinate_converter.coordinates(original_message)
            if val is not None:
                cordinate_str = f'({str(val[0])[0:10]} , {str(val[1])[0:10]})'
                response = generate_route(cordinate_str)
            else:
                response = "Could not process request. Please enter co-ordinates in format: x°y′z″ N  a°b′c″ W"
        else:
            locations = message_decoder(message_content)
            if locations is None:
                response = "Please format your message correctly. Type USAGE for more info!"
            else:
                if locations["to"] == "home":
                    response = generate_route(locations['from'])
                else:
                    response = generate_route(
                        locations['from'], locations['to'])
    except Exception as error_message:
        err_code = utility.log_error(
            f'( Twilio SMS Send ) : {str(error_message)}')
        response = f'An unexpected error occurred while processing your request. Error code : {err_code}'

    client.messages.create(
        to=contact,
        from_=from_number,
        body=response
    )
    return response


def message_decoder(text):
    """ Decodes message content by splitting, splicing and stripping text

    Args:
        text (string): Input text

    Returns:
        dict : A hashmap containing all key value pairs of decoded text
    """
    try:
        first_split = text.split("-")
        result = {}
        for element in first_split:
            element = element.strip()
            el = element.split(":")
            result[el[0].strip()] = el[1].strip()
        return result
    except Exception:
        return None


def balance():
    """ Account balance for Twilio Account

    Returns:
        string: A message with the remaining balance for Twilio account
    """
    response = requests.get(
        f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Balance.json',
        auth=(
            account_sid,
            auth_token))
    result = json.loads(response.text)
    return f'The account balance is: ${result["balance"]}'


def generate_route(origin, destination=home_location):
    """Generates a text response with route information by using the TravelTime class

    Args:
        origin (string): Starting location or co-ordinates.
        destination (string, optional): Destination location. Defaults to home_location (from storage).

    Returns:
        string: Response message with travel details.
    """
    res = ".\n"
    Route = TravelTime(
        origin,
        destination)
    res += f'Showing travel details for destination: {destination} \n'
    res += f'Distance : {Route.distance} \n'
    res += f'Estimated Time : {Route.traffic_time} \n'
    res += f'ETA : {eta(Route.start_time, Route.traffic_time_sec)} \n'
    return res


class TravelTime:
    """ Class that uses Google's Distance Matrix API to compute travel details """

    def __init__(self, start, end):
        """Initialize the class

        Args:
            start (string): Origin address/co-ordinates
            end (string): Destination address/co-ordinates
        """
        # URL for Google's Distance Matrix API
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        # API key
        apikey = api_keys["Google_Distance_Matrix"]
        # Generating Query Parameters
        self.start_time = utility.current_time_from_api()
        query_parameters = {
            "units": "metric",
            "departure_time": str(int(self.start_time.timestamp())),
            "traffic_model": "best_guess",
            "origins": start,
            "destinations": end,
            "key": apikey
        }
        # Formulating Request Headers
        headers = {
            'cache-control': "no-cache",
        }
        # Calling API
        response = requests.request(
            "GET", url, headers=headers, params=query_parameters)
        # Converting response to JSON/Dict
        result = json.loads(response.text)
        # Assigning response results
        self.distance = result['rows'][0]['elements'][0]['distance']['text']
        self.traffic_time = result['rows'][0]['elements'][0]['duration_in_traffic']['text']
        self.traffic_time_sec = result['rows'][0]['elements'][0]['duration_in_traffic']['value']


def eta(start_time, travel_time):
    """Computes estimated time of arrival

    Args:
        start_time (time): Time when travelling begins
        travel_time (time): Estimated duration of travel

    Returns:
        string:  Date and time message with the estimated travel time added
    """
    return str(start_time + timedelta(seconds=travel_time))[0:19]
