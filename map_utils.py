import folium

def _lonlat_to_latlon(lonlat):
    lon, lat = lonlat
    return (lat, lon)

def build_route_map_html(start_lonlat, end_lonlat, geometry, title="MandruyUA Route"):
    # geometry: GeoJSON LineString => {"coordinates": [[lon,lat],...]}
    coords_lonlat = geometry["coordinates"]
    coords_latlon = [(lat, lon) for lon, lat in coords_lonlat]

    start_latlon = _lonlat_to_latlon(start_lonlat)
    end_latlon = _lonlat_to_latlon(end_lonlat)

    m = folium.Map(location=start_latlon, zoom_start=6, control_scale=True)

    folium.Marker(start_latlon, tooltip="Start", popup="Start").add_to(m)
    folium.Marker(end_latlon, tooltip="End", popup="End").add_to(m)

    folium.PolyLine(coords_latlon, weight=6).add_to(m)

    folium.LayerControl().add_to(m)

    return m.get_root().render()
