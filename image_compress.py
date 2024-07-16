from PIL import Image, ImageOps
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

cred = credentials.Certificate("firebase_cred.json")

with open("storagebucket.txt", 'r') as file:
    store_bkt = file.read()

firebase_admin.initialize_app(cred, {'storageBucket': store_bkt})

"""def download_images(path="photos"):
    import csv_handler
    locs = list(csv_handler.get_loc_data().keys())
    print(locs)
    print(len(locs))
    bucket = storage.bucket()
    for img in locs:
        blob_name = f"{img}.jpg"

        #The path to which the file should be downloaded
        destination_file = f"{path}/{blob_name}"

        blob = bucket.blob(blob_name)
        blob.download_to_filename(destination_file)
        blob.delete()"""
        
def resize(path="photos", remove=False):
    for img in os.listdir(path):
        with Image.open(f"{path}/{img}") as image:
            ImageOps.exif_transpose(image, in_place=True)
            resized = image.resize((500,500), 4)
            resized.save(f"resized/{img}")
    if remove:
        for i in os.listdir(path):
            os.remove(f"{path}/{i}")



def upload_images(path):
    bucket = storage.bucket()
    for image in os.listdir(path):
        os.rename(path+image, path+image.lower())
        image = image.lower()
        if image.endswith('.jpg'):
            blob = bucket.blob(image)
            blob.upload_from_filename(path+image)

if __name__ == "__main__":
    resize("photos")
    inp = input("Do you want to upload the images y/n >>> ")
    if inp in ('y', 'Y'):
        upload_images("resized/")