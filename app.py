from flask import Flask, render_template, request, session, flash
import folium
import folium.plugins as plugins
from geopy.distance import distance
from math import radians, cos, sin, atan2, sqrt, degrees, ceil, floor
from database_manager import check_cred, get_data, update_score

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'
user = ''

locations = {'2357': [1.3428501826653902, 103.68000869738859], '1125': [1.354337, 103.684495], '3073': [1.3430637978922473, 103.68270773978031]
             , '5781': [1.3426374150718514, 103.68248648102774], '7320': [1.3543630333902696, 103.687998625503], '2232': [1.3445351444618483, 103.68029557491711]
             , '4350': [1.344064, 103.681253], '0053':[1.353260, 103.681938], '0611': [1.342805, 103.680186], '0490': [1.354852, 103.685161]
             , '0409': [1.3433272604917854, 103.67937904297112], '0271': [1.355080, 103.684446], '9839': [1.354637, 103.684121]
             , '9736':[1.3551276581734117, 103.68477283283985], '9708': [1.342645, 103.682446], '7574': [1.344573890732655, 103.68024249467516]
             , '2342': [1.3449737175166359, 103.67980527543415], '2573': [1.343868733946231, 103.68407336885876], '2122':[1.342594, 103.682440]
             , '2575': [1.347729, 103.680613], '3273': [1.346123, 103.680747], '3673':[1.3424588814010432, 103.68243687619389]
             , '4852': [1.3478507792463952, 103.6810190585185], '4385': [1.3467837383125467, 103.68088003575274], '3285': [1.342433, 103.685106]
             , '3890': [1.344464509231369, 103.68020687747625], '3890': [1.344464509231369, 103.68020687747625], '2873': [1.3486769552055542, 103.68743311950114]
             , '7384': [1.3429490019690558, 103.68012193301584], '6030': [1.3476890123734664, 103.68078966579428], '6250': [1.342079071592156, 103.68179564131339]
             , '6270': [1.3485072973819439, 103.6884057079587], '6987': [1.3490293867939036, 103.68828138752339], '7284': [1.3482555748743439, 103.68106349542785]
             , }

@app.route("/")
def home():
    if user:
        location_keys = list(locations.keys())
        return render_template("difficulty.html", location_keys=location_keys)
    session['total_points'] = 0
    return render_template("index.html")

@app.route('/', methods =["POST"])
def get_faction():
    if request.method == "POST":
        user_name = request.form.get("f_name")
        password = request.form.get("pswd")
        if not user_name or not password:
            flash("Enter username and password", "error")
            return render_template("index.html")
        if check_cred(user_name, password) == 0:
            flash("Incorrect password or username already taken!", "error")
            return render_template("index.html")
        location_keys = list(locations.keys())
        session['total_points'] = get_data()[user_name][1]
        global user
        user = user_name
        return render_template("difficulty.html", location_keys=location_keys)


@app.route("/map/<loc_code>", methods = ['POST', 'GET'])
def map(loc_code):
    if request.method == 'GET':
        name = request.form.get("f_name")
        print(name)

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

        return render_template("map.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['total_points'])
    
@app.route("/data", methods = ['POST', 'GET'])
@app.route("/data/<data>", methods = ['POST', 'GET'])
def data(data):

    combined_data = data.split(",") # split the combined data into a list of the coordinates and the location code
    LatLong = combined_data[:-1] # extract the Lat-Long coordinates of the data

    print(combined_data[2])
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
    session['total_points'] += points_earned
    update_score(user, session['total_points'])
    

    dist_label = format(floor(dist_btwn_locs), 'd') + " m"
    attr = {'fill': '#000000', 'font-weight': 'bold', 'font-size': '15'}
    plugins.PolyLineTextPath(dist_line, dist_label, offset=-5, center=True, attributes=attr).add_to(m)

    m.get_root().width = "1000px"
    m.get_root().height = "500px"
    map_iframe = m.get_root()._repr_html_()

    return render_template("map_holder.html", map_iframe=map_iframe, dist_label=dist_label, points_earned=points_earned)
    # return m.get_root().render()

@app.route("/location_photo/<loc_code>", methods = ['GET'])
def location_photo(loc_code):
    return render_template("location_photo.html", loc_code=loc_code)

@app.route("/location_photo/<loc_code>/2", methods = ['GET'])
def location_photo_hard(loc_code):
    return render_template("location_photo_hard.html", loc_code=loc_code)


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

        return render_template("map_hard.html", map_iframe=map_iframe, location_keys=location_keys, total_points=session['total_points'])


@app.route("/leaderboard")
def disp_leaders():
    user_info = get_data()
    sorted_lst = []
    for i in user_info:
        sorted_lst.append((i, user_info[i][1]))
    
    sorted_lst.sort(key=lambda x: x[1])
    for i in sorted_lst[::-1]:
        flash(i)

    return render_template("leaderboard.html")