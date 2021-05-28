import os
import datetime
from firebase_admin import credentials, firestore, initialize_app

my_directory = os.path.dirname(os.path.abspath(__file__))

# Initialize Firestore DB
# Loading firebase credentials
cred = credentials.Certificate(f'{my_directory}/secrets/firebase_keys.json')
# Initializing application with credentials
default_app = initialize_app(cred)
# Loading database reference as client
db = firestore.client()


def upload_analytics(Page, Country, City, Fingerprint, Ip_address, Time, request_data):
    now = datetime.datetime.now()
    month = now.strftime("%B")
    month_year = f"{month}_{'{:02d}'.format(now.year)}"
    """Sends analytics data to Firebase Firestore

    Args:
        Page (string): The page for which the analytics data is to be stored
        Fingerprint (string): The fingerprint id of the requester
        Ip_address (string): The IP address of the requester
        Time (string): The time when the request was received
        request_data (string): The request data containing all IP
                                and other information
    """
    db.collection(Page).document(f"{City}, {Country}").collection(Fingerprint).document(Time).set(request_data)
    db.collection(Page).document(f"{City}, {Country}").collection(Fingerprint).document("Statistics").set({}, merge=True)
    db.collection(Page).document(f"{City}, {Country}").collection(Fingerprint).document("Statistics").update({"visits": firestore.Increment(1)})

    db.collection(Page).document("Statistics").set({}, merge=True)
    db.collection(Page).document("Statistics").update({month_year: firestore.Increment(1)})


def upload_form(data):
    now = datetime.datetime.now()
    data["time"] = now
    """Sends Form data to Firebase Firestore

    Args:
        data (dict): Hashmap containing all form data
    """
    db.collection("Form").document(data["email"]).set(data)
