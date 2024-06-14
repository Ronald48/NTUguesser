import csv

location_file = "locations.csv"

def get_loc_data(location_file="locations.csv"):
    with open(location_file, 'r') as file:
        reader = list(csv.reader(file))
    location_dict = {}
    for line in reader:
        if line:
            location_dict[line[0]] = (float(line[1]), float(line[2]))
    return location_dict