import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# ---------- ENV ----------
ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"

print("ENV PATH:", ENV_PATH)
print("ENV EXISTS:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("ORS_API_KEY")
print("Loaded ORS key:", "OK" if API_KEY else "NOT FOUND")

BASE = "https://api.openrouteservice.org"

PROFILES = {
    "Car": "driving-car",
    "Bicycle": "cycling-regular",
    "Walking": "foot-walking",
}

def _require_key():
    if not API_KEY:
        raise RuntimeError("ORS_API_KEY not found. Check your .env file (ORS_API_KEY=...).")

def geocode(place: str):
    _require_key()

    url = f"{BASE}/geocode/search"
    params = {
        "api_key": API_KEY,
        "text": place,
        "size": 1,
        "layers": "locality"  # ⬅️ ТІЛЬКИ міста
    }

    r = requests.get(url, params=params, timeout=30)
    data = r.json()

    features = data.get("features", [])
    if not features:
        raise ValueError(f"Місто не знайдено: {place}")

    lon, lat = features[0]["geometry"]["coordinates"]
    label = features[0]["properties"].get("label", place)

    return lon, lat, label


# ---------- ROUTE ----------
def get_route(start_lonlat, end_lonlat, profile: str):
    """
    start_lonlat: (lon, lat)
    end_lonlat: (lon, lat)
    profile: 'driving-car', 'cycling-regular', 'foot-walking', ...
    Returns dict with distance_m, duration_s, geometry (GeoJSON LineString)
    """
    _require_key()

    # ВАЖЛИВО: беремо geojson endpoint -> завжди буде features[]
    url = f"{BASE}/v2/directions/{profile}/geojson"
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}

    body = {
        "coordinates": [
            [float(start_lonlat[0]), float(start_lonlat[1])],
            [float(end_lonlat[0]), float(end_lonlat[1])],
        ]
    }

    r = requests.post(url, json=body, headers=headers, timeout=60)
    data = r.json()

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"Directions ORS error: {data['error']}")
    if "features" not in data or not data["features"]:
        raise RuntimeError(f"Unexpected ORS response (no features): {data}")

    feature = data["features"][0]
    summary = feature["properties"]["summary"]
    geometry = feature["geometry"]  # GeoJSON LineString with coordinates array

    return {
        "distance_m": float(summary["distance"]),
        "duration_s": float(summary["duration"]),
        "geometry": geometry,
    }
