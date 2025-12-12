import networkx as nx
import geopandas as gpd
from shapely.geometry import LineString, Polygon

from src.core.flood_intersector import mark_blocked_edges


def test_mark_blocked_edges_blocks_when_overlap_large_enough():
    G = nx.Graph()

    a = (0.0, 0.0)
    b = (0.0, 10.0)

    G.add_node(a)
    G.add_node(b)

    # krawędź jako linia od lon=0 do lon=10 na lat=0
    geom = LineString([(0.0, 0.0), (10.0, 0.0)])
    G.add_edge(a, b, geometry=geom, blocked=False, length_m=1000)

    # flood przecina ~60% długości
    flood_poly = Polygon([(2.0, -1.0), (8.0, -1.0), (8.0, 1.0), (2.0, 1.0)])

    gdf = gpd.GeoDataFrame({"geometry": [flood_poly]}, crs="EPSG:4326")

    blocked = mark_blocked_edges(G, gdf, min_overlap_ratio=0.2)

    assert blocked == 1
    assert G.edges[a, b]["blocked"] is True


def test_mark_blocked_edges_does_not_block_when_overlap_too_small():
    G = nx.Graph()

    a = (0.0, 0.0)
    b = (0.0, 10.0)

    geom = LineString([(0.0, 0.0), (10.0, 0.0)])
    G.add_edge(a, b, geometry=geom, blocked=False, length_m=1000)

    # flood przecina malutki kawałek ~5%
    flood_poly = Polygon([(0.0, -1.0), (0.5, -1.0), (0.5, 1.0), (0.0, 1.0)])
    gdf = gpd.GeoDataFrame({"geometry": [flood_poly]}, crs="EPSG:4326")

    blocked = mark_blocked_edges(G, gdf, min_overlap_ratio=0.2)

    assert blocked == 0
    assert G.edges[a, b]["blocked"] is False
