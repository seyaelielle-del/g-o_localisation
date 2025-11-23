import requests
import folium
import webbrowser
import os

# Coordonnées départ/arrivée
UPN = (-4.40416, 15.25830)  # Université Pédagogique Nationale
UNIVERSITE_KIM = (-4.37200, 15.39200)  # Université Révérend Kim (ajustez selon les coordonnées réelles)

# Points intermédiaires pour générer des routes alternatives
VIA_POINTS = [
    (-4.390, 15.300),
    (-4.410, 15.320),
    (-4.420, 15.350),
    (-4.380, 15.380),
]

# Couleurs pour les routes
COLORS = ["green", "red", "blue", "orange", "purple", "darkcyan", "magenta"]

# Fonction pour obtenir un itinéraire via OSRM
def get_route(start, end, via=None):
    coords = [start] + (via if via else []) + [end]
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        r = data["routes"][0]
        path = [[lat, lon] for lon, lat in r["geometry"]["coordinates"]]
        dist_km = r["distance"] / 1000
        dur_min = r["duration"] / 60
        return {"path": path, "distance_km": dist_km, "duration_min": dur_min}
    except Exception as e:
        print(f"Erreur lors de la récupération de l'itinéraire : {e}")
        return None

# Générer toutes les routes
routes = [get_route(UPN, UNIVERSITE_KIM)]  # Route directe
routes += [get_route(UPN, UNIVERSITE_KIM, via=[via]) for via in VIA_POINTS]  # Routes via points

# Identifier la plus courte et la plus longue
shortest_idx = min(range(len(routes)), key=lambda i: routes[i]["distance_km"])
longest_idx = max(range(len(routes)), key=lambda i: routes[i]["distance_km"])

# Création de la carte
center_lat = (UPN[0] + UNIVERSITE_KIM[0]) / 2
center_lon = (UPN[1] + UNIVERSITE_KIM[1]) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# Marqueurs départ et arrivée
folium.Marker(UPN, popup="Université Pédagogique Nationale", icon=folium.Icon(color="blue")).add_to(m)

# Marqueur pour l'Université Révérend Kim avec notification
popup_message = "Vous êtes arrivé à l'Université Révérend Kim !"
folium.Marker(
    UNIVERSITE_KIM,
    popup=popup_message,
    icon=folium.Icon(color="red")
).add_to(m)

# Tracer la ligne directe entre UPN et Université Révérend Kim
folium.PolyLine([UPN, UNIVERSITE_KIM], color="black", weight=2, opacity=0.7, 
                 popup="Ligne directe entre UPN et Université Révérend Kim").add_to(m)

# Tracer les routes et ajouter popups
for i, r in enumerate(routes):
    if r is None:  # Vérifier si nous avons reçu une réponse valide
        continue
    color = COLORS[i % len(COLORS)]
    if i == shortest_idx:
        color = "green"
    elif i == longest_idx:
        color = "red"

    popup_text = f"Route #{i+1}<br>Distance: {r['distance_km']:.2f} km<br>Durée: {r['duration_min']:.1f} min"
    folium.PolyLine(r["path"], color=color, weight=6 if i in [shortest_idx, longest_idx] else 4,
                    opacity=0.8, popup=folium.Popup(popup_text, max_width=300)).add_to(m)

# Légende simple
legend_html = """
<div style="
 position: fixed; 
 bottom: 50px; left: 10px; width: 200px; height: 120px; 
 background-color: white; z-index:9999; padding: 10px; border:2px solid grey;
">
<b>Légende</b><br>
<i style="background:green; width:12px; height:12px; display:inline-block"></i> Plus courte<br>
<i style="background:red; width:12px; height:12px; display:inline-block"></i> Plus longue<br>
<i style="background:blue; width:12px; height:12px; display:inline-block"></i> Alternative<br>
<i style="background:black; width:12px; height:12px; display:inline-block"></i> Ligne directe<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Sauvegarde et ouverture automatique
outfile = "routes_upn_universite_kim_alternatives.html"
m.save(outfile)
webbrowser.open('file://' + os.path.realpath(outfile))

# Affichage distances et durées dans la console
for i, r in enumerate(routes):
    if r is not None:
        print(f"Route #{i+1} : Distance = {r['distance_km']:.2f} km, Durée = {r['duration_min']:.0f} min")
