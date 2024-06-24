import firebase_admin
from firebase_admin import credentials
from firebase_admin import db, storage
import hashlib
import os
import requests

cred = credentials.Certificate("firebase_cred.json")

with open('dburl.txt', 'r') as file:
    url = file.read()

with open("storagebucket.txt", 'r') as file:
    store_bkt = file.read()

firebase_admin.initialize_app(cred, {'databaseURL': url, 'storageBucket': store_bkt})
ref = db.reference()

def get_data():
    return ref.get()

def create_user(user_name, pswd):
    pswd = bytes(pswd, 'utf-8')
    encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
    ref.update({user_name: [encryptedPWD, 0]})

def check_availability(user_name):
    user_dict = get_data()
    if user_dict:
        if user_name in user_dict:
            return 0
    return 1

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
    return 2

def update_score(user_name, score):
    pswd = ref.get()[user_name][0]
    ref.update({user_name: [pswd, score]})

def get_img_url(image_no):
    bucket = storage.bucket()
    image = bucket.blob(f'{image_no}.jpg')
    image.make_public()
    return image.public_url

def upload_images(path="./static/images/"):
    bucket = storage.bucket()
    for image in os.listdir(path):
        os.rename(path+image, path+image.lower())
        image = image.lower()
        if image.endswith('.jpg'):
            blob = bucket.blob(image)
            blob.upload_from_filename(path+image)
            os.remove(path+image)

if __name__ == "__main__":
    upload_images("./NewPictures/")
