# Imports für Flask & DB
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Imports für Folium & ORS
import folium
import requests
from openrouteservice import convert

app = Flask(__name__)

# DB Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=True)
    content = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# -------------------------
# Karte / ORS Funktionen
# -------------------------
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="

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

def get_route_ors(profile: str, start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": [[start_lon, start_lat],[end_lon, end_lat]]}
    r = requests.post(url, headers=headers, json=body, verify=False)
    data = r.json()
    coords = convert.decode_polyline(data["routes"][0]["geometry"])["coordinates"]
    route_points = [(lat, lon) for lon, lat in coords]
    return route_points

# -------------------------
# Flask Route erweitern
# -------------------------
@app.route("/", methods=['GET', 'POST'])
@app.route("/<name>", methods=['GET', 'POST'])
def home(name=None):
    last_input = ""
    map_html = ""  # default leer

    # --- Nachrichten speichern ---
    if request.method == 'POST':
        content = request.form.get('content')
        start_address = request.form.get('start')
        end_address = request.form.get('ziel')

        if content:
            new_message = Message(user=name, content=content)
            db.session.add(new_message)
            db.session.commit()
            last_input = content

        # --- Karte erzeugen ---
        if start_address and end_address:
            try:
                profile = "driving-car"
                start_lat, start_lon = geocode_geoapify(start_address)
                end_lat, end_lon = geocode_geoapify(end_address)
                route_points = get_route_ors(profile, start_lat, start_lon, end_lat, end_lon)

                center_lat = (start_lat + end_lat) / 2
                center_lon = (start_lon + end_lon) / 2
                m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
                folium.Marker([start_lat, start_lon], popup="Start", tooltip=start_address).add_to(m)
                folium.Marker([end_lat, end_lon], popup="Ziel", tooltip=end_address).add_to(m)
                folium.PolyLine(route_points, color="blue", weight=5, opacity=0.8).add_to(m)

                # Info Box
                distance_km = sum(
                    ((route_points[i+1][0]-route_points[i][0])**2 + 
                     (route_points[i+1][1]-route_points[i][1])**2)**0.5
                    for i in range(len(route_points)-1)
                ) * 111  # grobe Umrechnung in km
                info_html = f"""
                <div style='position: fixed; top: 10px; left: 10px; z-index: 9999; background-color: white; padding: 10px; border-radius: 8px; box-shadow: 0 0 8px rgba(0,0,0,0.3);'>
                <b>Route Info</b><br>Start: {start_address}<br>Ziel: {end_address}<br>Distanz: {distance_km:.1f} km
                </div>
                """
                m.get_root().html.add_child(folium.Element(info_html))
                map_html = m.get_root().render()
            except Exception as e:
                map_html = f"<p style='color:red;'>Fehler bei der Routenberechnung: {e}</p>"

    return render_template('index.html', last_input=last_input, map_html=map_html)

if __name__ == "__main__":
    app.run(debug=True)