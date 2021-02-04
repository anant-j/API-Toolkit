import os
from firebase_admin import credentials, firestore, initialize_app

my_directory = os.path.dirname(os.path.abspath(__file__))
# Initialize Firestore DB
# Loading firebase credentials
cred = credentials.Certificate(my_directory + '/secrets/firebase_keys.json')
# Initializing application with credentials
default_app = initialize_app(cred)
# Loading database reference as client
db = firestore.client()


def upload_analytics(Page, Fingerprint, Ip_address, Time, request_data):
    db.collection(Page).document(Fingerprint).collection(
        "IP: " + Ip_address).document(Time).set(request_data)


def upload_form(data):
    db.collection("Form").document(data["email"]).set(data)
