import math
from typing import Tuple


def haversine_distance_m(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Odległość w metrach między dwoma punktami (lat, lon) w układzie WGS84.
    Prosty wzór haversine – wystarczający na prototyp.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371000 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
