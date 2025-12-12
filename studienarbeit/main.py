## Imports für Flask & DB
#from flask import Flask, render_template, request
#from flask_sqlalchemy import SQLAlchemy
#from datetime import datetime, timezone
#from flask import session
#
## Imports für Folium & ORS
#import folium
#import requests
#from openrouteservice import convert
#
#app = Flask(__name__)
#
##Variablen für die DB
#varb = "qwertz"
#varc = "qwertz"
#print(varb, varc)
#
## DB Konfiguration
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)
#
#class Route(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    user = db.Column(db.String(120))        # optional
#    start_address = db.Column(db.String(255))
#    end_address = db.Column(db.String(255))
#    profile = db.Column(db.String(50))
#    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
#
#with app.app_context():
#    db.create_all()
#
## -------------------------
## Karte / ORS Funktionen
## -------------------------
#GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
#ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="
#
#
##Labels für die Anzeige
#PROFILE_LABELS = {
#    "driving-car": "Auto",
#    "cycling-regular": "Fahrrad",
#    "foot-walking": "zu Fuß",
#}
#    
#
#def geocode_geoapify(address: str):
#    url = "https://api.geoapify.com/v1/geocode/search"
#    params = {"text": address, "apiKey": GEO_API_KEY, "format": "json"}
#    r = requests.get(url, params=params, verify=False)
#    r.raise_for_status()
#    data = r.json()
#    if not data.get("results"):
#        raise ValueError(f"Adresse nicht gefunden: {address}")
#    lat = data["results"][0]["lat"]
#    lon = data["results"][0]["lon"]
#    return lat, lon
#
#def get_route_ors(profile: str, start_lat, start_lon, end_lat, end_lon):
#    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
#    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json; charset=utf-8"}
#    body = {"coordinates": [[start_lon, start_lat],[end_lon, end_lat]]}
#    r = requests.post(url, headers=headers, json=body, verify=False)
#    data = r.json()
#    if "routes" not in data or not data["routes"]:
#        raise ValueError(f"Keine Route von ORS erhalten: {data}")
#
#    summary = data["routes"][0]["summary"]
#    distance_m = summary["distance"]       # Meter
#    duration_s = summary["duration"]       # Sekunden
#
#    encoded = data["routes"][0]["geometry"]
#    decoded = convert.decode_polyline(encoded)
#    coords = decoded["coordinates"]        # [[lon, lat], ...]
#
#    route_points = [(lat, lon) for lon, lat in coords]
#    return route_points, distance_m, duration_s
#
## -------------------------
## Flask Route erweitern
## -------------------------
#
#
#@app.route("/", methods=['GET', 'POST'])
#@app.route("/<name>", methods=['GET', 'POST'])
#def home(name=None):
#    last_input = ""
#    map_html = ""  # default leer
#
#    # --- Nachrichten speichern ---
#    if request.method == 'POST':
#        print("Wurde ausgeführt")
#        start_address = request.form.get('start')
#        end_address = request.form.get('ziel')
#        profile = request.form.get('profile', 'driving-car')
#        profile_label = PROFILE_LABELS.get(profile, "Auto")
#        print(start_address, end_address, profile)
#        
#        #if content:
#        #    new_message = Message(user=name, content=content)
#        #    db.session.add(new_message)
#        #    db.session.commit()
#        #    last_input = content
#
#        # --- Karte erzeugen ---
#        if start_address and end_address:
#            
#            # Neue Route in DB speichern
#            neue_route = Route(
#                user=name,
#                start_address=start_address,
#                end_address=end_address,
#                profile=profile
#            )
#            db.session.add(neue_route)
#            #db.session.commit()        #Auskommentiert zum Testen
#
#            print("Startadresse gespeichert:", start_address)
#            print("wurde leider nicht ausgeführt")
#            #new_message = Message(user=name)
#            #db.session.add(new_message)
#            #db.session.commit()
#            try:
#                start_lat, start_lon = geocode_geoapify(start_address)
#                end_lat, end_lon = geocode_geoapify(end_address)
#                route_points, distance_m, duration_s = get_route_ors(profile, start_lat, start_lon, end_lat, end_lon)
#                distance_km = distance_m / 1000.0
#                total_minutes = int(round(duration_s / 60.0))
#                if total_minutes >= 60:
#                    hours = total_minutes // 60
#                    minutes = total_minutes % 60
#                    dauer_text = f"{hours} h {minutes} min"
#                else:
#                    dauer_text = f"{total_minutes} min"
#
#                center_lat = (start_lat + end_lat) / 2
#                center_lon = (start_lon + end_lon) / 2
#                m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
#                folium.Marker([start_lat, start_lon], popup="Start", tooltip=start_address).add_to(m)
#                folium.Marker([end_lat, end_lon], popup="Ziel", tooltip=end_address).add_to(m)
#                folium.PolyLine(route_points, color="blue", weight=5, opacity=0.8).add_to(m)
#
#                #Auto-Zoom
#                if route_points:
#                    lats = [p[0] for p in route_points]
#                    lons = [p[1] for p in route_points]
#
#                    bounds = [
#                        [min(lats), min(lons)],   
#                        [max(lats), max(lons)]    
#                    ]
#                    m.fit_bounds(bounds)
#
#
#                # Info Box
#                info_html = f"""
#                <div style="
#                    position: absolute;
#                    top: 75px;
#                    left: 12px;
#                    z-index: 9999;
#                    background-color: white;
#                    padding: 12px 18px;
#                    border-radius: 10px;
#                    box-shadow: 0 0 10px rgba(0,0,0,0.3);
#                    /* Schriftgröße passt sich an: auf kleineren Screens etwas kleiner,
#                    auf großen Screens deutlich größer als vorher */
#                    font-size: clamp(0.95rem, 0.5vw + 0.6rem, 1.15rem);
#                    line-height: 1.4;
#                ">
#                    <b>Route-Info ({profile_label})</b><br>
#                    Start: {start_address}<br>
#                    Ziel: {end_address}<br>
#                    Entfernung: {distance_km:.2f} km<br>
#                    Dauer: {dauer_text}
#                </div>
#                """
#                m.get_root().html.add_child(folium.Element(info_html))
#                map_html = m.get_root().render()
#            except Exception as e:
#                map_html = f"<p style='color:red;'>Fehler bei der Routenberechnung: {e}</p>"
#    
#    return render_template('index.html', vara=last_input, map_html=map_html)
#
#
#
#
#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=5000)
#    
#    

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import folium
import requests
import json
from openrouteservice import convert


app = Flask(__name__)

last_start_coords = None
last_ziel_coords = None

# DB Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120))
    start_address = db.Column(db.String(255))
    end_address = db.Column(db.String(255))
    profile = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

with app.app_context():
    db.create_all()

# API-Keys und Labels
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="
PROFILE_LABELS = {"driving-car": "Auto", "cycling-regular": "Fahrrad", "foot-walking": "zu Fuß"}

# Geocoding + Route-Funktionen
def geocode_geoapify(address: str):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": address, "apiKey": GEO_API_KEY, "format": "json"}
    r = requests.get(url, params=params, verify=False)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise ValueError(f"Adresse nicht gefunden: {address}")
    lat = data["results"][0]["lat"]
    lon = data["results"][0]["lon"]
    return lat, lon


from openrouteservice import convert

def get_route_ors(profile: str, start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json; charset=utf-8"}
    body = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}
    r = requests.post(url, headers=headers, json=body, verify=False)
    data = r.json()
    if "routes" not in data or not data["routes"]:
        raise ValueError(f"Keine Route von ORS erhalten: {data}")

    summary = data["routes"][0]["summary"]
    distance_m = summary["distance"]
    duration_s = summary["duration"]

    encoded = data["routes"][0]["geometry"]
    decoded = convert.decode_polyline(encoded)
    coords = decoded["coordinates"]
    route_points = [(lat, lon) for lon, lat in coords]

    return route_points, distance_m, duration_s



# Temporärer Speicher für aktuelle Koordinaten
CURRENT_COORDS = {"start": None, "ziel": None}


#standort aufrufen
@app.route("/location", methods=["POST"])
def location():
    global last_start_coords, last_ziel_coords

    data = request.json
    print(">>> Standort erhalten:", data)

    if data.get("target") == "start":
        last_start_coords = {"lat": data["lat"], "lon": data["lon"]}
    elif data.get("target") == "ziel":
        last_ziel_coords = {"lat": data["lat"], "lon": data["lon"]}

    return "Standort empfangen!"

@app.route("/")
def routenplaner():
    return render_template('routenplaner.html', active_page='Routenplaner')

@app.route("/infos")
def infos():
    return render_template('infos.html', active_page='Infos')

@app.route("/route", methods=['POST'])
def route_ergebnis():
    global last_start_coords, last_ziel_coords

    start_address = request.form.get("start")
    end_address = request.form.get("ziel")
    profile = request.form.get("profile", "driving-car")
    profile_label = PROFILE_LABELS.get(profile, "Auto")

    #if abfrage ob mein standort im start eingabefeld steht
    if start_address == "Mein Standort" and last_start_coords:
        start_lat = last_start_coords["lat"]
        start_lon = last_start_coords["lon"]
    else:
        start_lat, start_lon = geocode_geoapify(start_address)

    #if abfrage ob mein standort im ziel eingabefeld steht
    if end_address == "Mein Standort" and last_ziel_coords:
        end_lat = last_ziel_coords["lat"]
        end_lon = last_ziel_coords["lon"]
    else:
        end_lat, end_lon = geocode_geoapify(end_address)


    #Route berechnen
    try:
        route_points, distance_m, duration_s = get_route_ors(profile, start_lat, start_lon, end_lat, end_lon)
        distance_km = distance_m / 1000.0
        total_minutes = int(round(duration_s / 60.0))
        if total_minutes >= 60:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            dauer_text = f"{hours} h {minutes} min"
        else:
            dauer_text = f"{total_minutes} min"

        # Kartenzentrum
        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        folium.Marker([start_lat, start_lon], popup="Start", tooltip=start_address).add_to(m)
        folium.Marker([end_lat, end_lon], popup="Ziel", tooltip=end_address).add_to(m)
        folium.PolyLine(route_points, color="blue", weight=5, opacity=0.8).add_to(m)

        # Auto-Zoom
        lats = [p[0] for p in route_points]
        lons = [p[1] for p in route_points]
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        m.fit_bounds(bounds)

        info_html = f"""
        <div style="
            position: absolute;
            top: 75px;
            left: 12px;
            z-index: 9999;
            background-color: white;
            padding: 12px 18px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            font-size: clamp(0.95rem, 0.5vw + 0.6rem, 1.15rem);
            line-height: 1.4;
        ">
            <b>Route-Info ({profile_label})</b><br>
            Start: {start_address}<br>
            Ziel: {end_address}<br>
            Entfernung: {distance_km:.2f} km<br>
            Dauer: {dauer_text}
        </div>
        """
        m.get_root().html.add_child(folium.Element(info_html))
        map_html = m.get_root().render()

    except Exception as e:
        map_html = f"<p style='color:red; font-size:1.2rem'>Fehler bei der Routenberechnung: {e}<br><br>Möglicher Fehler:<br>Keine neuen Orte eingegeben!<br><br>Ansonsten:<br>Bitte überprüfen Sie die Eingaben und versuchen Sie es erneut.<br><br>Ansonsten bitte den Support kontaktieren</p>"

    neue_route = Route(start_address=start_address, end_address=end_address, profile=profile)
    db.session.add(neue_route)

    return render_template('route.html', active_page='Routenplaner',
                           start=start_address, ziel=end_address,
                           profile=profile, map_html=map_html,
                           route_duration=duration_s)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

#rebase