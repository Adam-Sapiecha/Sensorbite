import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from shapely.geometry import LineString

from src.core.graph_builder import RoadGraphBuilder, RoadGraphBuilderWithDict
from src.core.flood_loader import FloodLoader
from src.core.flood_intersector import mark_blocked_edges
from src.core.router import EvacRouter


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EvacService:
    """
    Serwis spajający:
    - wczytanie grafu dróg,
    - wczytanie flood zones,
    - oznaczenie zagrożonych krawędzi,
    - wyznaczenie trasy.
    """

    def __init__(self, roads_path: Path, flood_path: Path):
        self.roads_path = roads_path
        self.flood_path = flood_path

        logger.info("Buduję graf dróg z pliku %s", self.roads_path)
        builder = RoadGraphBuilder(self.roads_path)
        self.graph = builder.build_graph()
        logger.info(
            "Graf zbudowany: %d węzłów, %d krawędzi",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    def reload_graph(self, geojson: Dict[str, Any]) -> None:
        """
        Przeładowuje graf dróg na podstawie nowego GeoJSON-a
        pobranego z Overpass API (bezpośrednio z pamięci).
        """
        logger.info(
            "Przeładowuję graf na podstawie nowego GeoJSON-a (%d features)",
            len(geojson.get("features", []))
        )

        builder = RoadGraphBuilderWithDict(geojson)
        self.graph = builder.build_graph()

        logger.info(
            "Graf przeładowany: %d węzłów, %d krawędzi",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Tuple[LineString, Dict[str, Any]]]:
        """
        Główna metoda wołana przez API.
        """
        logger.info("Wyznaczanie trasy start=%s end=%s", start, end)

        # 1. Wczytaj flood zones

        blocked_edges_count = mark_blocked_edges(self.graph, self.flood_path)
        logger.info("Zablokowano %d krawędzi grafu", blocked_edges_count)


        # 3. Router
        router = EvacRouter(self.graph)
        result = router.find_route(start, end)

        if result is None:
            logger.warning("Nie udało się znaleźć trasy dla zadanych punktów")
            return None

        route_line, meta = result
        meta["blocked_edges_count"] = blocked_edges_count

        return route_line, meta


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROADS_PATH = PROJECT_ROOT / "data" / "roads.geojson"
FLOOD_PATH = PROJECT_ROOT / "data" / "flood.geojson"

evac_service_singleton = EvacService(ROADS_PATH, FLOOD_PATH)
