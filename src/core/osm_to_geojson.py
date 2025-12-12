import xml.etree.ElementTree as ET
import json
from typing import Dict, Any


def osm_to_roads_geojson(osm_content: str) -> Dict[str, Any]:
    """
    Konwertuje dane OSM (XML w formie string) na GeoJSON zawierający tylko drogi (highway=*).
    Zwraca dict w formacie FeatureCollection.
    """

    root = ET.fromstring(osm_content)

    # indeks node_id -> (lon, lat)
    nodes = {}

    for node in root.findall("node"):
        nid = node.get("id")
        lat = float(node.get("lat"))
        lon = float(node.get("lon"))
        nodes[nid] = (lon, lat)  # GeoJSON używa (lon, lat)

    features = []

    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}


        if "highway" not in tags:
            continue

        coords = []
        for nd in way.findall("nd"):
            ref = nd.get("ref")
            if ref in nodes:
                coords.append(nodes[ref])

        if len(coords) >= 2:
            feature = {
                "type": "Feature",
                "properties": tags,
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    return geojson


def save_geojson(geojson: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
