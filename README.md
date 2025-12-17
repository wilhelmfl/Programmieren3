# Programmieren3
# Studienarbeit

# Routenplaner
Ein webbasiertes Routenplaner-Projekt mit Flask.  
Der Nutzer kann Start und Ziel eingeben (inkl. Autovervollständigung oder aktuellem Standort) und sich eine Route mit Karte, Entfernung und Dauer anzeigen lassen.
Das Projekt wurde mit Python (Flask) im Backend und mit HTML/JavaScript im frontend umgesetzt

## Funtkionen
- Start- und Zieladresse mit Autocomplete
- Aktueller Standort per GPS („Mein Standort“)
- Routing für:
    Auto
    Fahrrad
    Fußgänger
- Anzeige der Route auf einer Karte (Folium)
- Berechnung von:
    Entfernung
    Dauer
    Ankunftszeit

## Verwendete Technologien
- Python 3
- Flask
- Folium
- OpenRouteService API
    - Zweck: Routenberechnung (Distanz, Dauer, Streckenverlauf)
    - Einsatz: Backend (Python)
    - Unterstützt verschiedene Verkehrsprofile (Auto, Fahrrad, Fuß)
- Geoapify Geocoding API
    - Zweck: Adresse -> Koordinaten (Latitude / Longitude)
- OpenStreetMap / Nominatim
    - Zweck: Autocomplete / Ortsvorschläge
    - Einsatz: Frontend über Flask-Endpunkt /autocomplete
    - Liefert Städtenamen und Koordinaten
- Browser Geolocation API
    - Zweck: Aktueller Standort des Nutzers
    - Einsatz: Frontend (JavaScript)
    - Kein API-Key erforderlich
- Kartenmaterial
    - OpenstreetMap
    - Darstellung über Folium / Leaflet


## Installation
- Vorrausetzungen
    - Python 3.10 oder höher
    - Internetverbindung

1. Virtuelle Umgebung aktivieren (optional)
2. Abhängigkeiten installieren
    - pip install...
        - flask
        - folium
        - requests
        - openrouteservice

## Starten der Anwendung
1. Programm starten
    - Entweder
    In main.py gehen und oben auf ausführen (Pfeil drücken)
    - oder 
    Terminal öffnen und mit - cd C:\Users\flori\Documents\Workspace\Programmieren3\studienarbeit in den Ordner Studienarbeit - wechseln und dann - python main.py - eingeben

2. Im Terminal erscheint eineam Anfang was normal ist (development Server) darunter stehen zwei http:... Seiten

3. Im Browser anzeigen
- entweder
    Einer der beiden Links mit Strg+LinkeMaustaste anklicken und öffnen
- oder
    http://127.0.0.1:5000 in den Brwoser kopieren und mit Enter bestätigen

## Schließen der Anwendung
1. Mit Strg+c im Terminal kann die Anwendung geschlossen werden und neu geöffnet werden

# Hinweise
- Für Geoapify und Openroutservise werden API-Keys benötigt
- Diese sind im Code als Variablen hinterlegt
- Die Anwendung ist für Lern- und Projektzwecke gedacht

# Autoren
- Florian Wilhelm (Projektleiter / Entwicklung)
- Johannes Maier (Entwickler)
- Joshua Holzapfel (Entwickler)

