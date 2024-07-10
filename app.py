from flask import Flask, render_template, request, session, flash, jsonify
import folium
import folium.plugins as plugins
from geopy.distance import distance
from math import radians, cos, sin, atan2, sqrt, degrees, ceil, floor
from database_manager import check_cred, get_data, update_score, get_img_url, check_availability, create_user
from csv_handler import get_loc_data
import time

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'

locations = get_loc_data()

user_time_left = {}
prev_time = time.time()

def reduce_time():
    if user_time_left:
        for user in user_time_left:
            if user_time_left[user] > 0:
                user_time_left[user] -= 1


# update the remaining time for time trials game mode
# do not use the threading moodule for updating time
# pythonanywhere DOES NOT support threading
@app.route('/remaining_time')
def remaining_time():
    global prev_time
    if time.time() - prev_time >=1:  
        reduce_time()
        prev_time = time.time()
    remaining_time_in_seconds = user_time_left[session["user"]]
    return jsonify({'remaining_time_in_seconds': remaining_time_in_seconds})

# creating session variables for new user instance
def create_sesison(user_name):
    data = get_data() # fetch the user data from firebase -> reffer to database_manager.py for more info
    session['inf_points'] = data[user_name][1]
    session['time_points'] = data[user_name][2]
    session['session_score'] = 0
    session['time_left'] = data[user_name][3] # Only used to start the timer
    session['user'] = user_name
    session['mode'] = 2

# code for home page - index.html 
# This is the first page that is shown when someone visits the site
@app.route("/")
def home():
    # To avoid key error if the key 'user' is not in session
    if 'user' not in session:
        session['user'] = ''
        session['score'] = 0
    # If the user has already logged-in, redirect them to the game mode selection page
    if session['user'] != '':
        # Reset the session score to make sure the previous score does not app up
        session['session_score'] = 0
        if session["user"] in user_time_left:
            user_time_left.pop(session["user"])
        return render_template("game_mode.html", user_name=session['user'].title())
    # If the user is not logged-in redirect them to the login page
    return render_template("index.html")

# This is the function that logs in the user
@app.route('/', methods =["POST"])
def login():
    # using the POST method to get the info filled in by the user on the login page
    if request.method == "POST":
        # f_name and pswd are the names of the input tags on the login page
        user_name = request.form.get("f_name")
        password = request.form.get("pswd")
        # Checking if both user name and passwords are filled by the user
        if not user_name or not password:
            flash("Enter username and password", "error")
            return render_template("index.html")
        # Reffer to database_manager.py for check_cred
        # check_cred will return 1 if the user name and password match the ones in the database
        # if the user name and passwords do not match, the logn page flashes the error
        if check_cred(user_name, password) != 1:
            flash("Incorrect password or username!", "error")
            return render_template("index.html")
        # Create all the keys in the flask session
        create_sesison(user_name)
        # Redirect the user to the select game mode screen after login
        return render_template("game_mode.html", user_name=session['user'].title())

# creating new user accounts and storing data in firebase database
@app.route("/create_acc", methods=['GET', 'POST'])
def create_account():
    if request.method == "POST":
        user_name = request.form.get("f_name")
        password = request.form.get("pswd")
        rep_password = request.form.get("r_pswd")
        if not user_name:
            flash("Enter username", "error")
            return render_template("create_acc.html")
        elif check_availability(user_name) == 0:
            flash("Username not available!", "error")
            return render_template("create_acc.html")
        elif not password:
            flash("Enter a password", "error")
            return render_template("create_acc.html")
        elif not rep_password:
            flash("Repeat the new password", "error")
            return render_template("create_acc.html")
        elif password != rep_password:
            flash("The passwords do not match", "error")
            return render_template("create_acc.html")
        else:
            create_user(user_name, password)
            location_keys = list(locations.keys())
            create_sesison(user_name)
            return render_template("index.html", location_keys=location_keys, user_name=session['user'].title())
    return render_template("create_acc.html")

# logout functionality for the site
@app.route("/logout")
def logout():
    # only update the score if the game mode was time trials
    # the score is automatically updated for infinite run
    if session["mode"] == 1:
        # remove the user info from flask session
        if session["user"] in user_time_left:
            user_time_left.pop(session["user"])
        # only update time trials score if it is grater than the PB
        if session["session_score"] > session["time_points"]:
            update_score(session['user'], session['inf_points'], session['session_score'])
    session["user"]=''
    # Redirect to login screen
    return render_template("index.html")

# Easy difficulty
@app.route("/location_photo/<loc_code>", methods = ['GET'])
def location_photo(loc_code):
    url = get_img_url(loc_code)
    if session["user"] not in user_time_left:
        user_time_left[session["user"]] = session["time_left"]

    if session['mode'] == 1:
        if user_time_left[session["user"]] <= 0:
            if session["session_score"] > session["time_points"]:
                update_score(session['user'], session['inf_points'], session['session_score'])
            return render_template("game_over.html", score=session["session_score"], high_score=session["session_score"] > session["time_points"])
        
    return render_template("location_photo.html", url=url, loc_code=loc_code, mode=session['mode'])

@app.route("/map/<loc_code>", methods = ['POST', 'GET'])
def map(loc_code):
    if request.method == 'GET':
        location_keys = list(locations.keys())

        #set the iframe dimensions
        m = folium.Map(location=(1.348431, 103.683846), zoom_start=16)
        
        # add a marker on the position clicked on the map
        m.add_child(folium.ClickForMarker())

        # show the LongLat values on the location clicked on the map
        m.add_child(folium.LatLngPopup())

        m.get_root().width = "1000px"
        m.get_root().height = "600px"
        map_iframe = m.get_root()._repr_html_()

        if session['mode'] == 0:
            return render_template("map.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['inf_points'], mode=session['mode'])
        return render_template("map.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['session_score'], mode=session['mode'])

# Hard difficulty
@app.route("/location_photo/<loc_code>/2", methods = ['GET'])
def location_photo_hard(loc_code):
    url = get_img_url(loc_code)
    if session["user"] not in user_time_left:
        user_time_left[session["user"]] = session["time_left"]
    
    if session['mode'] == 1:
        if user_time_left[session["user"]] <= 0:
            if session["session_score"] > session["time_points"]:
                update_score(session['user'], session['inf_points'], session['session_score'])
            return render_template("game_over.html", score=session["session_score"], high_score=session["session_score"] > session["time_points"])
            
    return render_template("location_photo_hard.html", url=url, loc_code=loc_code, mode=session['mode'])


@app.route("/map/<loc_code>/2", methods = ['POST', 'GET'])
def map_hard(loc_code):
    if request.method == 'GET':
        location_keys = list(locations.keys())

        #set the iframe dimensions
        m = folium.Map(location=(1.348431, 103.683846), zoom_start=16, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        , attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community')
        
        # add a marker on the position clicked on the map
        m.add_child(folium.ClickForMarker())

        # show the LongLat values on the location clicked on the map
        m.add_child(folium.LatLngPopup())

        m.get_root().width = "1000px"
        m.get_root().height = "600px"
        map_iframe = m.get_root()._repr_html_()

        if session['mode'] == 0:
            return render_template("map_hard.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['inf_points'])
        return render_template("map_hard.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['session_score'], mode=session['mode'])


# game mode selection
@app.route("/inf")
def inf_mode():
    session["mode"] = 0
    return render_template("difficulty.html", location_keys = list(locations.keys()))

@app.route("/time")
def time_mode():
    session["mode"] = 1
    return render_template("difficulty.html", location_keys = list(locations.keys()))

# displays the game leaderboard with real time updates
@app.route("/leaderboard")
def disp_leaders():
    user_info = get_data()
    inf_scores = [(i.title(), user_info[i][1]) for i in user_info]
    time_scores = [(i.title(), user_info[i][2]) for i in user_info]

    inf_scores.sort(key=lambda x: x[1])
    time_scores.sort(key=lambda x: x[1])
    return render_template("leaderboard.html", log=session['user'], inf_score=inf_scores[::-1], time_score=time_scores[::-1])


# calculating and updating user score based on the selected point  
@app.route("/data", methods = ['POST', 'GET'])
@app.route("/data/<data>", methods = ['POST', 'GET'])
def data(data):

    combined_data = data.split(",") # split the combined data into a list of the coordinates and the location code
    LatLong = combined_data[:-1] # extract the Lat-Long coordinates of the data

    # calculate the midpoint of the 2 selected coordinates
    dLon = radians(locations[combined_data[2]][1] - float(LatLong[1]))

    lat1 = radians(float(LatLong[0]))
    lat2 = radians(locations[combined_data[2]][0])
    lon1 = radians(float(LatLong[1]))

    Bx = cos(lat2) * cos(dLon)
    By = cos(lat2) * sin(dLon)
    lat3 = degrees(atan2(sin(lat1) + sin(lat2), sqrt((cos(lat1) + Bx) * (cos(lat1) + Bx) + By * By)))
    lon3 = degrees(lon1 + atan2(By, cos(lat1) + Bx))

    m = folium.Map(location=(lat3, lon3))

    # set the zoom of the map to fit the actual location and the players guess while remaining compact
    m.fit_bounds([LatLong,locations[combined_data[2]]], padding=(0.05,0.05))

    # mark the actual location
    folium.Marker(locations[combined_data[2]],
                popup="",
                icon=folium.Icon(color="red")
                ).add_to(m)
    
    # mark the location of the players guess
    folium.Marker(LatLong,
                popup="",
                icon=folium.Icon(color="blue")
                ).add_to(m)
    
    dist_line = folium.PolyLine([locations[combined_data[2]], 
                     LatLong]).add_to(m)
    
    dist_btwn_locs = float(str(distance(locations[combined_data[2]], LatLong)*1000)[:-3])

    points_earned = ceil(1000/float(str(dist_btwn_locs)[:-2]))

    # Updating the score
    session['session_score'] += points_earned

    if session['mode'] == 0: # infinite run
        session['inf_points'] += points_earned
        update_score(session['user'], session['inf_points'], session['time_points'])

    dist_label = format(floor(dist_btwn_locs), 'd') + " m"
    attr = {'fill': '#000000', 'font-weight': 'bold', 'font-size': '15'}
    plugins.PolyLineTextPath(dist_line, dist_label, offset=-5, center=True, attributes=attr).add_to(m)

    m.get_root().width = "1000px"
    m.get_root().height = "500px"
    map_iframe = m.get_root()._repr_html_()

    return render_template("map_holder.html", map_iframe=map_iframe, dist_label=dist_label, points_earned=points_earned)
