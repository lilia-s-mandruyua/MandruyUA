import folium

def _lonlat_to_latlon(lonlat):
    lon, lat = lonlat
    return (lat, lon)

def build_route_map_html(geometry):
    import folium

    coords = [(lat, lon) for lon, lat in geometry["coordinates"]]

    m = folium.Map(location=coords[0], zoom_start=6)
    folium.PolyLine(coords, weight=5, color="blue").add_to(m)

    folium.Marker(coords[0], tooltip="Початок").add_to(m)
    folium.Marker(coords[-1], tooltip="Кінець").add_to(m)

    return m._repr_html_()

