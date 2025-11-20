import subprocess
import sys
import os 
import webbrowser

def ensure_requirements():
    try: 
        import folium
        return
    except ImportError:
        print("Benötigte Pakete fehlen.")
        print("Versuche, requirements.txt zu installieren...")

script_dir = os.path.dirname(os.path.abspath(__file__))                                         #Ordner ermitteln: Joshua/ -> eine Ebene hoch -> STUDIENARBEIT/
project_dir = os.path.abspath(os.path.join(script_dir, ".."))
req_path = os.path.join(project_dir, "requirements.txt")

if not os.path.exists(req_path):
    print("Fehler: requirements.txt wurde nicht gefunden.")
    print("Erwarte sie im Ordner:", project_dir)
    sys.exit(1)

try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req_path],
        check=True
    )
    print("Installation aus requirements.txt abgeschlossen.\n")
except subprocess.CalledProcessError as e:
    print("Die automatische Installation ist fehlgeschlagen:", e)
    print("Bitte im Terminal ausführen: pip install -r requirements.txt")
    sys.exit(1)


ensure_requirements()                                                                           #Sicherstellen, dass alle Pakete da sind


import folium 

center_lat = 47.728226723543656
center_lon = 10.316527762817902

m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

folium.Marker(
    location = [center_lat, center_lon],
    popup = "Mitte der Karte",
    tooltip = "Klick mich"
).add_to(m)

map_file = "karte.html"
m.save(map_file)

webbrowser.open('file://'+ os.path.realpath(map_file))

print("Karte gespeichert als {map_file} und im Browser geöffnet.")