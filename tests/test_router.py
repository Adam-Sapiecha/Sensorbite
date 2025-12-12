import networkx as nx
from shapely.geometry import LineString

from src.core.router import EvacRouter


def test_router_returns_length_m_sum():
    G = nx.Graph()

    a = (52.0, 21.0)
    b = (52.0, 21.001)

    G.add_node(a)
    G.add_node(b)

    G.add_edge(
        a, b,
        length_m=123.0,
        geometry=LineString([(a[1], a[0]), (b[1], b[0])]),
        blocked=False
    )

    r = EvacRouter(G)
    res = r.find_route(a, b)

    assert res is not None
    route_line, meta = res
    assert meta["length_m"] == 123.0
    assert meta["segments"] == 1
