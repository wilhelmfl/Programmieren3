from flask import Flask, render_template, request
from datetime import datetime, timezone
import folium
import requests
import json
from openrouteservice import convert

app = Flask(__name__)

# --------------------------------------------------
# API-Keys und Labels
# --------------------------------------------------
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="
PROFILE_LABELS = {
    "driving-car": "Auto",
    "cycling-regular": "Fahrrad",
    "foot-walking": "zu Fuß"
}

# --------------------------------------------------
# Geocoding
# --------------------------------------------------
def geocode_geoapify(address: str):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": address, "apiKey": GEO_API_KEY, "format": "json"}
    r = requests.get(url, params=params, verify=False)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise ValueError(f"Adresse nicht gefunden: {address}")
    return data["results"][0]["lat"], data["results"][0]["lon"]

# --------------------------------------------------
# Route berechnen
# --------------------------------------------------
def get_route_ors(profile, start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}

    r = requests.post(url, headers=headers, json=body, verify=False)
    data = r.json()

    if "routes" not in data or not data["routes"]:
        raise ValueError("Keine Route erhalten")

    route = data["routes"][0]
    summary = route["summary"]

    decoded = convert.decode_polyline(route["geometry"])
    points = [(lat, lon) for lon, lat in decoded["coordinates"]]

    return points, summary["distance"], summary["duration"]

# --------------------------------------------------
# Seiten
# --------------------------------------------------
@app.route("/")
def routenplaner():
    return render_template("routenplaner.html", active_page="Routenplaner")

@app.route("/infos")
def infos():
    return render_template("infos.html", active_page="Infos")

@app.route("/route", methods=["POST"])
def route_ergebnis():

    start_address = request.form.get("start")
    end_address   = request.form.get("ziel")
    profile       = request.form.get("profile", "driving-car")
    profile_label = PROFILE_LABELS.get(profile, "Auto")

    start_coords_raw = request.form.get("start_coords")
    ziel_coords_raw  = request.form.get("ziel_coords")

    # START
    if start_address == "Mein Standort" and start_coords_raw:
        c = json.loads(start_coords_raw)
        start_lat, start_lon = c["lat"], c["lon"]
    else:
        start_lat, start_lon = geocode_geoapify(start_address)

    # ZIEL
    if end_address == "Mein Standort" and ziel_coords_raw:
        c = json.loads(ziel_coords_raw)
        end_lat, end_lon = c["lat"], c["lon"]
    else:
        end_lat, end_lon = geocode_geoapify(end_address)

    try:
        route_points, distance_m, duration_s = get_route_ors(
            profile, start_lat, start_lon, end_lat, end_lon
        )

        distance_km = round(distance_m / 1000, 2)
        total_minutes = int(round(duration_s / 60))

        if total_minutes >= 60:
            dauer_text = f"{total_minutes//60} h {total_minutes%60} min"
        else:
            dauer_text = f"{total_minutes} min"

        m = folium.Map(
            location=[(start_lat + end_lat)/2, (start_lon + end_lon)/2],
            zoom_start=12
        )

        folium.Marker([start_lat, start_lon], tooltip="Start",
                      icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([end_lat, end_lon], tooltip="Ziel",
                      icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine(route_points, color="blue", weight=5).add_to(m)

        m.fit_bounds(route_points)
        map_html = m.get_root().render()

    except Exception as e:
        map_html = f"<p style='color:red'>Fehler: {e}</p>"
        distance_km = "-"
        dauer_text = "-"
        duration_s = 0

    return render_template(
        "route.html",
        active_page="Routenplaner",
        start=start_address,
        ziel=end_address,
        profile=profile_label,
        distance_km=distance_km,
        dauer_text=dauer_text,
        map_html=map_html,
        route_duration=duration_s
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)