import math
from api import geocode, get_route

def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371  # км
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))

def build_ors_route(origin, destination, profile, mode_name, speed_kmh, price_per_km):
    slon, slat, _ = geocode(origin)
    elon, elat, _ = geocode(destination)

    result = get_route((slon, slat), (elon, elat), profile)

    dist_km = result["distance_m"] / 1000
    time_min = int(result["duration_s"] / 60)

    return {
        "mode": mode_name,
        "time_min": time_min,
        "price": round(dist_km * price_per_km, 2),
        "distance_km": round(dist_km, 1),
        "transfers": 0,
        "description": f"{origin} → {destination}",
        "geometry": result["geometry"],
        "start": (slon, slat),
        "end": (elon, elat),
        "source": "OpenRouteService"
    }

def build_car_route(origin, destination):
    return build_ors_route(
        origin,
        destination,
        profile="driving-car",
        mode_name="Авто",
        speed_kmh=80,
        price_per_km=0.10
    )

def build_bike_route(origin, destination):
    return build_ors_route(
        origin,
        destination,
        profile="cycling-regular",
        mode_name="Велосипед",
        speed_kmh=15,
        price_per_km=0.0
    )

def build_walk_route(origin, destination):
    return build_ors_route(
        origin,
        destination,
        profile="foot-walking",
        mode_name="Пішки",
        speed_kmh=5,
        price_per_km=0.0
    )

def build_plane_route(origin, destination):
    slon, slat, _ = geocode(origin)
    elon, elat, _ = geocode(destination)
    dist = haversine_km(slon, slat, elon, elat)

    return {
        "mode": "Літак",
        "time_min": int(dist / 700 * 60 + 90),
        "price": round(dist * 0.12, 2),
        "distance_km": round(dist, 1),
        "transfers": 0,
        "description": "Прямий авіарейс",
        "geometry": None,
        "source": "Mock Aviation API"
    }

def build_train_route(origin, destination):
    slon, slat, _ = geocode(origin)
    elon, elat, _ = geocode(destination)
    dist = haversine_km(slon, slat, elon, elat)

    transfers = 0 if dist < 600 else 1

    return {
        "mode": "Потяг",
        "time_min": int(dist / 130 * 60),
        "price": round(dist * 0.08, 2),
        "distance_km": round(dist, 1),
        "transfers": transfers,
        "description": "Прямий поїзд" if transfers == 0 else "Маршрут з пересадкою",
        "geometry": None,
        "source": "Mock Rail API"
    }

def build_bus_route(origin, destination):
    slon, slat, _ = geocode(origin)
    elon, elat, _ = geocode(destination)
    dist = haversine_km(slon, slat, elon, elat)

    return {
        "mode": "Автобус",
        "time_min": int(dist / 80 * 60),
        "price": round(dist * 0.05, 2),
        "distance_km": round(dist, 1),
        "transfers": 1,
        "description": "Маршрут з пересадкою",
        "geometry": None,
        "source": "Mock Bus API"
    }

def build_all_routes(origin, destination):
    return [
        build_car_route(origin, destination),
        build_bike_route(origin, destination),
        build_walk_route(origin, destination),
        build_train_route(origin, destination),
        build_bus_route(origin, destination),
        build_plane_route(origin, destination),
    ]


def rank_routes(routes, w_time=0.5, w_price=0.3, w_comfort=0.2):
    max_time = max(r["time_min"] for r in routes)
    max_price = max(r["price"] for r in routes) or 1
    max_transfers = max(r["transfers"] for r in routes) or 1

    for r in routes:
        r["score"] = (
            w_time * (r["time_min"] / max_time) +
            w_price * (r["price"] / max_price) +
            w_comfort * (r["transfers"] / max_transfers)
        )

    return sorted(routes, key=lambda x: x["score"])
