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
from openrouteservice import convert


#Hier einfach nur API-Keys festlegen
GEO_API_KEY = "c3575e31c8034abb8369480f3829584a"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJkZDQ5OWM3ZmM2NWI2ZmY2ZGVhYTRlMTdiOTk2YzZiOGNhYzVjZjRlNWE5YjVmZjBjMGM3NTRmIiwiaCI6Im11cm11cjY0In0="


#Fortbewegungsart wählen (Auto / Fahrrad / zu Fuß)
def choose_profile():
    print("Bitte Fortbewegungsart wählen")
    print(" 1 = Auto")
    print(" 2 = Fahrrad")
    print(" 3 = Zu Fuß")

    choice = input("> ").strip()

    if choice == "2":
        return "cycling-regular", "Fahrrad"
    elif choice == "3":
        return "foot-walking", "zu Fuß"
    else:
        return "driving-car", "Auto"

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

def get_route_ors(profile: str, start_lat, start_lon, end_lat, end_lon):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }

    body = {
        "coordinates": [
            [start_lon, start_lat],
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
    
    #Zeit und Distanz holen
    summary = data["routes"][0]["summary"]
    distance_m = summary["distance"]    # Meter
    duration_s = summary["duration"]    # Sekunden

    #ORS liefert eine encoded polyline:
    encoded_line = data["routes"][0]["geometry"]

    #Polyline decodieren
    decoded = convert.decode_polyline(encoded_line)

    #Ergebnis ist GeoJSON-Liste: [[lon,lat], ...]
    coords = decoded["coordinates"]

    #Für Folium drehen wir sie zu [lat, lon]
    route_points = [(lat, lon) for lon, lat in coords]

    return route_points, distance_m, duration_s

#Hauptprogramm
#Profil wählen
profile, profile_label = choose_profile()

#hier Adresse eingeben
print("Bitte Startadresse eingeben:")
start_address = input("> ")

print("Bitte Zieladresse eingeben:")
end_address = input("> ")


print("Suche Koordinaten (Geoapify)...")
start_lat, start_lon = geocode_geoapify(start_address)
end_lat, end_lon = geocode_geoapify(end_address)

print("Hole Route (OpenRouteService)...")
try:
    route_points, distance_m, duration_s = get_route_ors(profile, start_lat, start_lon, end_lat, end_lon)
except ValueError as e:
    print("Fehler bei der Routenberechnung:", e)
    sys.exit(1)

#Distanz umrechnen in km und min
distance_km = distance_m / 1000.0
# Dauer in Minuten ganzzahlig runden
total_minutes = int(round(duration_s / 60.0))

if total_minutes >= 60:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    dauer_text_console = f"{hours} Stunden {minutes} Minuten"
    dauer_text_popup = f"{hours} h {minutes} min"
else:
    minutes = total_minutes
    dauer_text_console = f"{minutes} Minuten"
    dauer_text_popup = f"{minutes} min"

print(f"Strecke: {distance_km:.2f} km")
print(f"Fahrzeit ({profile_label}): {dauer_text_console}")
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
    [min(lats), min(lons)],
    [max(lats), max(lons)]  
]
m.fit_bounds(bounds)


#Info-Box im Fenster einbauen
info_html = f"""
<div style ="
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 9999;
    background-color: white;
    padding: 10px 15px;
    border-radius: 8px;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
    font-size: 14px;
">
    <b>Route-Info ({profile_label})</b><br>
    Start: {start_address}<br>
    Ziel: {end_address}<br>
    Entfernung: {distance_km:.2f} km<br>
    Fahrzeit: {dauer_text_popup}
</div>
"""
m.get_root().html.add_child(folium.Element(info_html))

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

