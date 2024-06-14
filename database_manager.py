import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import hashlib
import os

cred = credentials.Certificate("firebase_cred.json")

with open('dburl.txt', 'r') as file:
    url = file.read()

firebase_admin.initialize_app(cred, {'databaseURL': url})
ref = db.reference()

def get_data():
    return ref.get()

def create_user(user_name, pswd):
    pswd = bytes(pswd, 'utf-8')
    encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
    ref.update({user_name: [encryptedPWD, 0]})

def check_cred(user_name, pswd):
    user_name = user_name.lower()
    user_dict = get_data()
    if user_dict:
        for user in user_dict:
            if user == user_name:
                pswd = bytes(pswd, 'utf-8')
                encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
                if encryptedPWD == user_dict[user][0]:
                    return 1
                return 0
    create_user(user_name, pswd)
    return 2

def update_score(user_name, score):
    pswd = ref.get()[user_name][0]
    ref.update({user_name: [pswd, score]})
