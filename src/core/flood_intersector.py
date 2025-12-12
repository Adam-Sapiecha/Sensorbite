import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from shapely.geometry import shape

logger = logging.getLogger(__name__)


def _load_flood_gdf(
    flood_source: Optional[Union[str, Path, gpd.GeoDataFrame]] = None
) -> gpd.GeoDataFrame:
    """
    Ładuje strefy zalania jako GeoDataFrame.

    - jeśli flood_source to GeoDataFrame -> zwraca ją bez zmian (po drobnej normalizacji),
    - jeśli flood_source to ścieżka lub None -> czyta 'data/flood.geojson' (domyślnie).
    """
    if isinstance(flood_source, gpd.GeoDataFrame):
        gdf = flood_source.copy()
    else:
        if flood_source is None:
            flood_source = Path("data/flood.geojson")
        else:
            flood_source = Path(flood_source)

        if not flood_source.exists():
            logger.warning(
                "Plik flood.geojson (%s) nie istnieje – nie blokuję żadnych krawędzi.",
                flood_source,
            )
            return gpd.GeoDataFrame(geometry=[])

        try:
            gdf = gpd.read_file(flood_source)
        except Exception as e:
            logger.error("Nie udało się odczytać %s: %s", flood_source, e)
            return gpd.GeoDataFrame(geometry=[])

    if "geometry" not in gdf:
        logger.warning("GeoDataFrame flood nie ma kolumny geometry – pomijam.")
        return gdf

    # trochę sprzątania geometrii
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()].copy()

    if gdf.empty:
        return gdf


    if gdf.crs is None:

        gdf.set_crs(epsg=4326, inplace=True)

    try:
        gdf["geometry"] = gdf.geometry.buffer(0)
    except Exception:
        pass

    return gdf


def mark_blocked_edges(
    graph,
    flood: Optional[Union[str, Path, gpd.GeoDataFrame]] = None,
    min_overlap_ratio: float = 0.2,
) -> int:
    """
    Oznacza krawędzie grafu jako „zablokowane”, jeśli w sensowny sposób
    przecinają się z poligonami zalania.

    Parametry:
    ----------
    graph : networkx.Graph / DiGraph
        Graf zbudowany na podstawie dróg. Krawędzie powinny mieć atrybut
        'geometry' (LineString / MultiLineString) w WGS84.
    flood : None / ścieżka / GeoDataFrame
        - None  -> czyta 'data/flood.geojson'
        - str/Path -> czyta podaną ścieżkę
        - GeoDataFrame -> używa bezpośrednio
    min_overlap_ratio : float
        Minimalny stosunek (długość_przecięcia / długość_krawędzi), żeby uznać
        krawędź za zalaną. Dzięki temu ignorujemy pojedyncze „pikselki”
        szumu SAR, a blokujemy krawędzie, które faktycznie biegną przez wodę.

    Zwraca:
    -------
    int
        Liczbę zablokowanych krawędzi.
    """
    gdf = _load_flood_gdf(flood)


    for _, _, data in graph.edges(data=True):
        data["blocked"] = False

    if gdf.empty:
        logger.info(
            "Brak stref zalania – nie zablokowano żadnej krawędzi grafu."
        )
        return 0


    try:
        sindex = gdf.sindex
    except Exception as e:
        logger.warning(
            "Nie udało się utworzyć spatial index dla flood polygons: %s", e
        )
        sindex = None

    blocked_count = 0

    # Iterujemy po krawędziach i patrzymy tylko na poligony, które mają
    # przecinające się bounding boxy 
    for u, v, data in graph.edges(data=True):
        geom: Optional[BaseGeometry] = data.get("geometry")
        if geom is None:
            continue
        if geom.is_empty:
            continue

        # Odrzucamy bardzo krótkie odcinki
        if geom.length == 0:
            continue

        candidate_idxs = None
        if sindex is not None:
            try:
                candidate_idxs = list(
                    sindex.intersection(geom.bounds)
                )
            except Exception:
                candidate_idxs = None

        if not candidate_idxs:

            continue

        max_ratio = 0.0
        for idx in candidate_idxs:
            poly = gdf.geometry.iloc[idx]
            if poly is None or poly.is_empty:
                continue

            inter = geom.intersection(poly)
            if inter.is_empty:
                continue

            try:
                inter_length = inter.length
            except Exception:

                continue

            if inter_length <= 0:
                continue

            ratio = inter_length / geom.length
            if ratio > max_ratio:
                max_ratio = ratio


            if max_ratio >= min_overlap_ratio:
                break

        if max_ratio >= min_overlap_ratio:
            data["blocked"] = True
            blocked_count += 1

    logger.info("Zablokowano %d krawędzi grafu.", blocked_count)
    return blocked_count
