import firebase_admin
from firebase_admin import credentials
from firebase_admin import db, storage
import hashlib
import os

# This file contains functions to communicate with the database

# loading the firebase credentials
cred = credentials.Certificate("firebase_cred.json")

# Retrieving the database url
with open('dburl.txt', 'r') as file:
    url = file.read()

# Retrieving the storage url
with open("storagebucket.txt", 'r') as file:
    store_bkt = file.read()

# initializing firebase admin
firebase_admin.initialize_app(cred, {'databaseURL': url, 'storageBucket': store_bkt})
ref = db.reference()

# Retrieves everything stored in the database
def get_data():
    # Returns a dictionary
    return ref.get()

def create_user(user_name, pswd):
    pswd = bytes(pswd, 'utf-8')
    # The password is saved as SHA256 of the string entered
    encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
    # Creating a new entry in the database
    ref.update({user_name: [encryptedPWD, 0, 0, 300]})

# Checking if the user name is already taken
def check_availability(user_name):
    user_dict = get_data()
    if user_dict:
        if user_name in user_dict:
            return 0
    # Returns 1 if the user name entered is unique
    return 1

# Check the user name and password against the data in the database
def check_cred(user_name, pswd):
    user_name = user_name.lower()
    user_dict = get_data()
    if user_dict:
        for user in user_dict:
            if user == user_name:
                # Converting the password entered to SHA256 for comparison
                pswd = bytes(pswd, 'utf-8')
                encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
                if encryptedPWD == user_dict[user][0]:
                    # 1 -> correct password
                    return 1
                # 0 -> incorrect password
                return 0
    # 2 -> empty database or username not found
    return 2

# Updating the user score
def update_score(user_name, inf_score, time_score):
    pswd = ref.get()[user_name][0] # The password entered by the user is not stored in flask session
    ref.update({user_name: [pswd, inf_score, time_score, 300]})

# get the image url from the image number that is randomly chosen
def get_img_url(image_no):
    bucket = storage.bucket()
    image = bucket.blob(f'{image_no}.jpg')
    # the image is made public to make sure the user can view the image
    image.make_public()
    return image.public_url

# This function can be used to automatically upload images to firebase
# The images can be place in static/images
# Otherwise change the path argunment to match the directory in which the images are stored
def upload_images(path="./photos/"):
    bucket = storage.bucket()
    for image in os.listdir(path):
        os.rename(path+image, path+image.lower())
        image = image.lower()
        if image.endswith('.jpg'):
            blob = bucket.blob(image)
            blob.upload_from_filename(path+image)
            # Remove the image from local machine
            # comment this out if you wish to keep local copies of the images
            os.remove(path+image)

if __name__ == "__main__":
    upload_images()
