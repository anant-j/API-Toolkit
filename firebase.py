from firebase_admin import credentials, firestore, initialize_app

# Initialize Firestore DB
cred = credentials.Certificate('secrets/firebase_keys.json')
default_app = initialize_app(cred)
database = firestore.client()