from pathlib import Path
from typing import Dict, Any

import json
import networkx as nx
from shapely.geometry import LineString, shape

from .utils import haversine_distance_m


def _add_linestring_to_graph(G: nx.Graph, line: LineString) -> None:
    """
    Dodaje do grafu kolejne odcinki z LineStringa.
    Węzły są identyfikowane przez współrzędne (lat, lon),
    krawędzie mają długość w metrach i geometrię shapely.
    """
    coords = list(line.coords)
    if len(coords) < 2:
        return

    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]      
        lon2, lat2 = coords[i + 1]

        n1 = (lat1, lon1)        
        n2 = (lat2, lon2)

        if n1 not in G:
            G.add_node(n1, pos=n1)
        if n2 not in G:
            G.add_node(n2, pos=n2)

        length_m = haversine_distance_m(n1, n2)

        segment = LineString([(lon1, lat1), (lon2, lat2)])

        G.add_edge(
            n1,
            n2,
            length_m=length_m,
            geometry=segment,
            blocked=False,
        )


class RoadGraphBuilder:
    """
    Odpowiada za zbudowanie grafu dróg na podstawie pliku GeoJSON.
    Bez użycia geopandas – ręczne parsowanie JSON.
    """

    def __init__(self, roads_path: Path):
        self.roads_path = roads_path

    def build_graph(self) -> nx.Graph:
        G = nx.Graph()

        if not self.roads_path.exists():
            # brak pliku z drogami – zwracamy pusty graf
            return G

        with open(self.roads_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])

        for feature in features:
            geom_dict = feature.get("geometry")
            if not geom_dict:
                continue

            geom = shape(geom_dict)

            if isinstance(geom, LineString):
                _add_linestring_to_graph(G, geom)
            elif geom.geom_type == "MultiLineString":
                for line in geom.geoms:
                    _add_linestring_to_graph(G, line)

        return G


class RoadGraphBuilderWithDict:
    """
    Wersja buildera, która przyjmuje już wczytany GeoJSON (dict),
    np. z Overpass API – używana w reload_graph().
    """

    def __init__(self, geojson: Dict[str, Any]):
        self.geojson = geojson

    def build_graph(self) -> nx.Graph:
        G = nx.Graph()

        features = self.geojson.get("features", [])

        for feature in features:
            geom_dict = feature.get("geometry")
            if not geom_dict:
                continue

            geom = shape(geom_dict)

            if isinstance(geom, LineString):
                _add_linestring_to_graph(G, geom)
            elif geom.geom_type == "MultiLineString":
                for line in geom.geoms:
                    _add_linestring_to_graph(G, line)

        return G
