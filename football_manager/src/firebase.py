import firebase_admin
from firebase_admin import credentials, firestore, auth


def init_firebase():
    cred = credentials.Certificate("/Users/orito/MyProjects/football_app/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)


def get_db_client():
    db = firestore.client()
    return db