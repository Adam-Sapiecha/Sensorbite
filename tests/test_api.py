import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_healthcheck_docs_available():
    """
    Sprawdza, czy aplikacja FastAPI uruchamia sie poprawnie
    i udostepnia dokumentacje Swagger.
    """
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_update_roads_invalid_payload():
    """
    Sprawdza walidacje danych wejsciowych dla endpointu update-roads.
    """
    response = client.post("/api/admin/update-roads", json={})
    assert response.status_code in (400, 422)


def test_set_test_flood_rect():
    """
    Sprawdza, czy testowy prostokat flood moze zostac wygenerowany.
    """
    payload = {
        "south": 52.20,
        "west": 20.90,
        "north": 52.30,
        "east": 21.00
    }

    response = client.post("/api/admin/set-test-flood-rect", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "message" in data or "status" in data


def test_route_without_roads_fails_gracefully():
    """
    Sprawdza, czy wyznaczanie trasy bez zaladowanych drog
    zwraca kontrolowany blad zamiast 500.
    """
    response = client.get(
        "/api/evac/route",
        params={
            "start": "52.229,21.012",
            "end": "52.231,21.015"
        }
    )

    assert response.status_code in (400, 404, 422)


def test_route_with_invalid_params():
    """
    Sprawdza walidacje parametrow zapytania.
    """
    response = client.get(
        "/api/evac/route",
        params={
            "start": "invalid",
            "end": "invalid"
        }
    )

    assert response.status_code == 422
