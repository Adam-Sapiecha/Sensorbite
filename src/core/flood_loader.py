from pathlib import Path
from typing import List

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, base


class FloodLoader:
    """
    Na razie prosta implementacja: wczytujemy poligony z lokalnego pliku GeoJSON.
    W przyszłości można tu wpiąć pobieranie z Sentinel Hub.
    """

    def __init__(self, flood_path: Path):
        self.flood_path = flood_path

    def load_polygons(self) -> List[base.BaseGeometry]:
        if not self.flood_path.exists():

            return []

        gdf = gpd.read_file(self.flood_path)

        polygons: List[base.BaseGeometry] = []

        for _, row in gdf.iterrows():
            geom = row.geometry
            if isinstance(geom, Polygon):
                polygons.append(geom)
            elif isinstance(geom, MultiPolygon):
                polygons.extend(list(geom.geoms))

        return polygons
