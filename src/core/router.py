from typing import Tuple, Optional, Dict, Any

import networkx as nx
from shapely.geometry import LineString

from .utils import haversine_distance_m


class EvacRouter:
    """
    Odpowiada za wyznaczenie trasy z wykorzystaniem grafu dróg,
    z pominięciem krawędzi z atrybutem blocked=True.
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def _find_nearest_node(self, coord: Tuple[float, float]) -> Tuple[float, float]:
        """
        Znajdź najbliższy węzeł w grafie do zadanych współrzędnych (lat, lon).
        Prosta implementacja – przejście po wszystkich węzłach.
        """
        lat, lon = coord
        best_node = None
        best_dist = float("inf")

        for node in self.graph.nodes:
            node_lat, node_lon = node  # bo używamy (lat, lon) jako identyfikatora
            d = haversine_distance_m((lat, lon), (node_lat, node_lon))
            if d < best_dist:
                best_dist = d
                best_node = node

        if best_node is None:
            raise ValueError("Graf nie zawiera żadnych węzłów")

        return best_node

    def find_route(
        self, start_coord: Tuple[float, float], end_coord: Tuple[float, float]
    ) -> Optional[Tuple[LineString, Dict[str, Any]]]:
        """
        Znajduje trasę z punktu start do end, omijając blocked edges.
        Zwraca: (geometry LineString, meta) lub None jeśli nie ma ścieżki.
        """
        # budujemy podgraf z odblokowanych krawędzi
        G_walkable = nx.Graph()
        G_walkable.add_nodes_from(self.graph.nodes(data=True))

        blocked_edges_count = 0

        for u, v, data in self.graph.edges(data=True):
            if data.get("blocked", False):
                blocked_edges_count += 1
                continue
            G_walkable.add_edge(u, v, **data)

        if G_walkable.number_of_edges() == 0:
            return None

        start_node = self._find_nearest_node(start_coord)
        end_node = self._find_nearest_node(end_coord)

        try:
            path_nodes = nx.shortest_path(
                G_walkable,
                source=start_node,
                target=end_node,
                weight="length_m",
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None


        coords = []
        total_length = 0.0

        for i in range(len(path_nodes) - 1):
            curr_node = path_nodes[i]
            next_node = path_nodes[i + 1]

            # dodajemy koordynaty w formie (lon, lat) do LineString
            curr_lat, curr_lon = curr_node
            coords.append((curr_lon, curr_lat))

            edge_data = G_walkable.get_edge_data(curr_node, next_node)
            if edge_data:
                total_length += edge_data.get("length_m", 0.0)


        last_lat, last_lon = path_nodes[-1]
        coords.append((last_lon, last_lat))

        route_line = LineString(coords)

        meta = {
            "length_m": total_length,
            "segments": len(path_nodes) - 1,
            "calc_time_ms": 0,
            "blocked_edges_count": blocked_edges_count,
        }

        return route_line, meta
