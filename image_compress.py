from PIL import Image
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db, storage

cred = credentials.Certificate("firebase_cred.json")

with open("storagebucket.txt", 'r') as file:
    store_bkt = file.read()

firebase_admin.initialize_app(cred, {'storageBucket': store_bkt})
path="./photos/"

def download_images(path):
    bucket = storage.bucket()


def upload_images(path):
    bucket = storage.bucket()
    for image in os.listdir(path):
        os.rename(path+image, path+image.lower())
        image = image.lower()
        if image.endswith('.jpg'):
            blob = bucket.blob(image)
            blob.upload_from_filename(path+image)
            os.remove(path+image)
