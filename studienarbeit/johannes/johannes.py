import folium 
import webbrowser
import os

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

#webbrowser.open('file://'+ os.path.realpath(map_file))

print("Karte gespeichert als {map_file} und im Browser geöffnet.")



##Benutzeroberfläche

#from tkinter import *

#fenster = Tk() ##fenster erstellen

#fenster.title("Routenplaner") ## fenstertitel oder überschrift

#fenster.mainloop() #

import tkinter as tk

root = tk.Tk()
root.title("Start- und Endpunkt mit Dropdown")

# row Zeile, column spalte muss aufeinander folgen,padx und pady bestimmen abstand nach unten oben bzw links und rechts
tk.Label(root, text="Startpunkt:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
entry_start = tk.Entry(root, width=25)
entry_start.grid(row=0, column=3, padx=10, pady=5)

tk.Label(root, text="Endpunkt:").grid(row=0, column=4, padx=10, pady=5, sticky="w")
entry_end = tk.Entry(root, width=25)
entry_end.grid(row=0, column=5, padx=10, pady=5)

# dropdown menü erstllen und positionieren
tk.Label(root, text="Reiseart:").grid(row=0, column=0, padx=10, pady=5, sticky="w")

reiseart = tk.StringVar(value="Auto")  
optionen = ["Auto", "Fahrrad", "Zu Fuß"]

dropdown = tk.OptionMenu(root, reiseart, *optionen)
dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

# beschriftung der dropdown menüs und eingabefelder
def anzeigen():
    print("Startpunkt:", entry_start.get())
    print("Endpunkt:", entry_end.get())
    print("Reiseart:", reiseart.get())
    print("---")



root.mainloop()
