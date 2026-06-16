import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# 1. Importa tu app real
from nutriken_engine import app, cache_get, cache_set

# 2. Creamos una fixture que aplica los parches antes de cada test
@pytest.fixture(scope="module")
def client():
    # Parcheamos cache_get para que devuelva None (Cache miss forzado)
    # Usamos side_effect=lambda *args, **kwargs: None para asegurar que sea None literal
    with patch("nutriken_engine.cache_get", side_effect=lambda *args, **kwargs: None):
        with patch("nutriken_engine.cache_set", return_value=None):
            # Parcheamos las llamadas a APIs externas
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                    
                    # Configuramos respuestas por defecto para los mocks
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {"status": "ok"}
                    
                    mock_get.return_value = mock_resp
                    mock_post.return_value = mock_resp
                    
                    with TestClient(app) as c:
                        yield c

# ===========================================================================
# Tests
# ===========================================================================

class TestHealth:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

class TestClinicalEndpoint:
    def test_valid_query_returns_200(self, client):
        # Esta prueba ahora debería pasar porque cache_get devuelve None (evitando json.loads)
        response = client.post("/api/clinical", json={"query": "obesity"})
        assert response.status_code == 200

    def test_response_structure(self, client):
        response = client.post("/api/clinical", json={"query": "obesity"})
        data = response.json()
        assert "condition" in data or "status" in data
