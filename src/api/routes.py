from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from shapely.geometry import box, mapping
import json
from pathlib import Path
from fastapi import HTTPException
from src.services.evac_service import evac_service_singleton
from src.core.osm_downloader import download_osm_roads
from src.core.osm_to_geojson import osm_to_roads_geojson
from src.core.sentinel_flood_ogc_client import create_default_ogc_client

router = APIRouter(tags=["evacuation"])


# ========= pomocnicze: parsowanie lat,lon =========

def parse_latlon(param: str) -> tuple[float, float]:
    """Parsuje string w formacie 'lat,lon' na krotkę (lat, lon)."""
    try:
        parts = param.split(",")
        if len(parts) != 2:
            raise ValueError("Parametr musi być w formacie lat,lon")
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Nieprawidłowy format współrzędnych: {param}. Błąd: {e}"
        )


# ========= 1) Wyznaczanie trasy =========

@router.get("/evac/route")
def get_evac_route(
    start: str = Query(..., description="Punkt startowy w formacie 'lat,lon'"),
    end: str = Query(..., description="Punkt końcowy w formacie 'lat,lon'"),
):
    """
    Wyznacza trasę ewakuacji między punktami start i end, omijając flood zones.
    Zwraca GeoJSON linii + metadane.
    """
    start_lat, start_lon = parse_latlon(start)
    end_lat, end_lon = parse_latlon(end)

    result = evac_service_singleton.get_route((start_lat, start_lon), (end_lat, end_lon))

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Nie udało się znaleźć trasy między zadanymi punktami"
        )

    route_line, meta = result

    geojson_feature = {
        "type": "Feature",
        "geometry": route_line.__geo_interface__,
        "properties": {
            "length_m": meta["length_m"],
            "segments": meta["segments"],
        },
    }

    return {
        "route": geojson_feature,
        "meta": {
            "calc_time_ms": meta["calc_time_ms"],
            "blocked_edges_count": meta["blocked_edges_count"],
        },
    }


# ========= 2) Admin – update dróg (Overpass) =========

class BBOX(BaseModel):
    south: float
    west: float
    north: float
    east: float


@router.post("/admin/update-roads")
async def update_roads(bbox: BBOX):
    """
    Pobiera nowe dane drogowe z Overpass API i przeładowuje graf w pamięci.
    """
    osm_xml = download_osm_roads(
        (bbox.south, bbox.west, bbox.north, bbox.east)
    )

    geojson = osm_to_roads_geojson(osm_xml)

    evac_service_singleton.reload_graph(geojson)

    return {
        "status": "OK",
        "roads": len(geojson["features"]),
        "bbox": bbox,
    }

@router.post("/admin/set-test-flood-rect")
def set_test_flood_rect(bbox: BBOX):
    """
    Zapisuje testowy, średniej wielkości prostokąt jako flood zones
    (1 poligon) w środku aktualnego BBOX.
    """
    # “Średni” prostokąt: zostawiamy margines 25% z każdej strony
    dx = (bbox.east - bbox.west) * 0.25
    dy = (bbox.north - bbox.south) * 0.25

    west = bbox.west + dx
    east = bbox.east - dx
    south = bbox.south + dy
    north = bbox.north - dy

    geom = box(west, south, east, north)

    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"source": "test-rect"},
                "geometry": mapping(geom),
            }
        ],
    }

    out = Path("data/flood.geojson")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    return {"status": "OK", "polygons": 1, "bbox": bbox}

# ========= 3) Admin – update flood (Sentinel Hub OGC) =========

_sentinel_flood_client = None


def get_sentinel_client():
    global _sentinel_flood_client
    if _sentinel_flood_client is None:
        _sentinel_flood_client = create_default_ogc_client()
    return _sentinel_flood_client


@router.post("/admin/update-flood")
def update_flood(bbox: BBOX):
    """
    Aktualizuje flood zones na podstawie Sentinel Hub OGC WMS
    dla podanego BBOX (south, west, north, east).
    Zapisuje data/flood.geojson, z którego korzysta EvacService.
    """
    try:
        client = get_sentinel_client()
    except RuntimeError as e:
        # Brak INSTANCE_ID – ładny komunikat dla użytkownika
        raise HTTPException(status_code=500, detail=str(e))

    try:
        count = client.update_flood_for_bbox(
            (bbox.south, bbox.west, bbox.north, bbox.east)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Nie udało się zaktualizować flood zones z Sentinel Hub: {e}",
        )

    return {
        "status": "OK",
        "polygons": count,
        "bbox": bbox,
    }


@router.get("/debug/flood-geojson")
def get_flood_geojson():
    path = Path("data/flood.geojson")
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Brak pliku flood.geojson – najpierw wywołaj /api/admin/update-flood"
        )
    return json.loads(path.read_text(encoding="utf-8"))