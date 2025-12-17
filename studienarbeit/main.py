from flask import Flask, render_template, request, jsonify
from datetime import datetime, timezone
import folium
import requests
import json
from openrouteservice import convert

app = Flask(__name__)

last_start_coords = None
last_ziel_coords = None


# API-Keys und Labels
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="
PROFILE_LABELS = {
    "driving-car": "Auto",
    "cycling-regular": "Fahrrad",
    "foot-walking": "zu Fuß"
}

# Geocoding
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

# Routing
def get_route_ors(profile: str, start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}
    r = requests.post(url, headers=headers, json=body, verify=False)
    data = r.json()

    if "routes" not in data or not data["routes"]:
        raise ValueError("Keine Route erhalten")

    summary = data["routes"][0]["summary"]
    distance_m = summary["distance"]
    duration_s = summary["duration"]

    encoded = data["routes"][0]["geometry"]
    decoded = convert.decode_polyline(encoded)
    coords = decoded["coordinates"]
    route_points = [(lat, lon) for lon, lat in coords]

    return route_points, distance_m, duration_s


@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "")
    if len(query) < 2:
        return jsonify([])  # Mindestens 2 Buchstaben

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
    }

    # ✅ User-Agent gesetzt + Timeout
    headers = {
        "Accept-Language": "de",
        "User-Agent": "MeinRoutenplaner/1.0 (meine.email@domain.de)"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()  # HTTP Fehler abfangen
        results = r.json()    # JSON dekodieren
    except requests.RequestException as e:
        print("Request-Fehler:", e)
        return jsonify([])
    except ValueError as e:  # JSONDecodeError
        print("Fehler beim Dekodieren von JSON:", e)
        return jsonify([])

    suggestions = []
    for item in results:
        city = (
            item["address"].get("city")
            or item["address"].get("town")
            or item["address"].get("village")
            or item["address"].get("hamlet")
            or item["address"].get("county")
        )
        state = item["address"].get("state")
        if city and state:
            label = f"{city}, {state}"
        elif city:
            label = city
        else:
            continue

        suggestions.append({
            "label": label,
            "lat": item["lat"],
            "lon": item["lon"]
        })

    return jsonify(suggestions)


@app.route("/")
def routenplaner():
    return render_template("routenplaner.html", active_page="Routenplaner")

@app.route("/infos")
def infos():
    return render_template("infos.html", active_page="Infos")

@app.route("/route", methods=["POST"])
def route_ergebnis():
    start_address = request.form.get("start")
    end_address = request.form.get("ziel")
    profile = request.form.get("profile", "driving-car")

    profile_label = PROFILE_LABELS.get(profile, "Auto")

    # Koordinaten aus Formular (Mein Standort)
    start_coords = request.form.get("start_coords")
    ziel_coords = request.form.get("ziel_coords")

    if start_coords:
        coords = json.loads(start_coords)
        start_lat = coords["lat"]
        start_lon = coords["lon"]
    else:
        start_lat, start_lon = geocode_geoapify(start_address)

    if ziel_coords:
        coords = json.loads(ziel_coords)
        end_lat = coords["lat"]
        end_lon = coords["lon"]
    else:
        end_lat, end_lon = geocode_geoapify(end_address)

    try:
        route_points, distance_m, duration_s = get_route_ors(
            profile, start_lat, start_lon, end_lat, end_lon
        )

        distance_km_zwei = round(distance_m / 1000, 2)

        total_minutes = int(round(duration_s / 60))
        if total_minutes >= 60:
            dauer_text = f"{total_minutes // 60} h {total_minutes % 60} min"
        else:
            dauer_text = f"{total_minutes} min"

        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        folium.Marker([start_lat, start_lon], tooltip=start_address,
                      icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([end_lat, end_lon], tooltip=end_address,
                      icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine(route_points, color="blue", weight=5).add_to(m)

        lats = [p[0] for p in route_points]
        lons = [p[1] for p in route_points]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

        map_html = m.get_root().render()

    except Exception as e:
        map_html = f"<p style='color:red'>Fehler: {e}</p>"
        distance_km_zwei = "-"
        dauer_text = "-"
        duration_s = 0

    return render_template(
        "route.html",
        active_page="Routenplaner",
        start=start_address,
        ziel=end_address,
        profile=profile,               
        profile_label=profile_label,   
        distance_km=distance_km_zwei,
        dauer_text=dauer_text,
        map_html=map_html,
        route_duration=duration_s
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)