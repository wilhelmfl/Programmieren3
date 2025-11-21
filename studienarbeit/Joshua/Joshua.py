import subprocess
import sys
import os 
import webbrowser
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Eine Ebene hoch in Studienarbeit
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(script_dir, ".."))
req_path = os.path.join(project_dir, "requirements.txt")


#Ab hier kontrollieren ob folium & requests installiert sind
def ensure_requirements():
    try: 
        import folium
        import requests
        return
    except ImportError:
        print("Benötigte Pakete fehlen.")
        print("Versuche, requirements.txt zu installieren...")

        if not os.path.exists(req_path):
            print("Fehler: requirements.txt wurte nicht gefunden.")
            print("Erwarte sie im Ordner:", project_dir)
            sys.exit(1)

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_path],
                check= True
            )
            print("Installation aus requirements.txt abgeschlossen. \n")
        except subprocess.CalledProcessError as e:
            print("Die automatische Installation ist fehlgeschlagen:", e)
            print("Bitte im Terminal ausführen: pip install -r requirements.txt")
            sys.exit(1)


ensure_requirements()

import folium 
import requests


#Hier einfach nur API-Keys festlegen
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="


#Ab hier mithilfe von Geoapify die Adresse in Koordinaten umwandeln
def geocode_geoapify(adress: str):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": adress,
        "apiKey": GEO_API_KEY,
        "format": "json"
    }

    r = requests.get(url, params=params, verify=False, timeout=10)
    r.raise_for_status()
    data = r.json()

    if not data.get("results"):
        raise ValueError(f"Adresse nicht gefunden: {adress}")

    lat = data["results"][0]["lat"]
    lon = data["results"][0]["lon"]
    return lat, lon


#Ab hier mithilfe von OpenRouteService die Route zwischen 2 Koordinaten 
from openrouteservice import convert

def get_route_ors(start_lat, start_lon, end_lat, end_lon):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }

    body = {
        "coordinates": [
            [start_lon, start_lat],   # ORS: [lon, lat]
            [end_lon, end_lat],
        ]
    }

    r = requests.post(url, headers=headers, json=body, verify=False, timeout=10)

    print("ORS-HTTP-Status:", r.status_code)
    data = r.json()

    if "routes" not in data or not data["routes"]:
        print("Fehler-Antwort von ORS:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        raise ValueError("Keine Route von OpenRouteService erhalten.")

    #ORS liefert eine encoded polyline:
    encoded_line = data["routes"][0]["geometry"]

    #Polyline decodieren
    decoded = convert.decode_polyline(encoded_line)

    #Ergebnis ist GeoJSON-Liste: [[lon,lat], ...]
    coords = decoded["coordinates"]

    #Für Folium drehen wir sie zu [lat, lon]
    route_points = [(lat, lon) for lon, lat in coords]

    return route_points


#hier Adresse eingeben
print("Bitte Startadresse eingeben:")
start_address = input("> ")

print("Bitte Zieladresse eingeben:")
end_address = input("> ")


print("Suche Koordinaten (Geoapify)...")
start_lat, start_lon = geocode_geoapify(start_address)
end_lat, end_lon = geocode_geoapify(end_address)

print("Hole Route (OpenRouteService)...")
route_points = get_route_ors(start_lat, start_lon, end_lat, end_lon)

#Jetzt Mittelpunkt für die Karte
center_lat = (start_lat + end_lat) / 2
center_lon = (start_lon + end_lon) / 2


#Jetzt Karte bauen, mit Folium und Route anzeigen lassen
m = folium.Map(location=[center_lat, center_lon], zoom_start= 12)

#Hier jetzt Startmarker
folium.Marker(
    location=[start_lat, start_lon],
    popup="Start",
    tooltip=start_address
).add_to(m)

#Hier jetzt Zielmarker
folium.Marker(
    location=[end_lat, end_lon],
    popup="Ziel",
    tooltip=end_address
).add_to(m)

#Hier jetzt Route einzeichnen
folium.PolyLine(
    locations=route_points,
    weight=5,
    opacity=0.8,
    tooltip="Route"
).add_to(m)

#Hier jetzt automatischer Zoom auf die Karte
lats = [p[0] for p in route_points]
lons = [p[1] for p in route_points]

bounds = [
    [min(lats), min(lons)],   # Süd-West
    [max(lats), max(lons)]    # Nord-Ost
]

m.fit_bounds(bounds)


#Ab jetzt Karte speichern und im Browser öffnen
map_file = "karte_route.html"
if os.path.exists("karte_route.html"):
    try:
        os.remove("karte_route.html")
        print("Alte Karte entfernt.")
    except PermissionError:
        print("Konnte alte Karte nicht löschen (evtl. im Browser geöffnet).")
m.save(map_file)

webbrowser.open("file://" + os.path.realpath(map_file))

print(f"Karte gespeichert als {map_file} und im Browser geöffnet.")

