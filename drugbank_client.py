# drugbank_client.py
"""
Integración OPCIONAL con DrugBank vía su MCP (https://mcp.drugbank.com/mcp).

IMPORTANTE (licencia + JOSS):
- DrugBank NO es redistribuible. Este módulo NO descarga ni almacena datos de DrugBank.
- Consulta en TIEMPO DE EJECUCIÓN usando el token del PROPIO usuario (variable de
  entorno DRUGBANK_TOKEN, un Bearer OAuth de su suscripción DrugBank).
- Si no hay token, la función devuelve {"configured": False} y el resto del sistema
  funciona igual con las fuentes ABIERTAS (PubMed/PubChem/ChEMBL/curado).
Así el repositorio permanece open-source y sin datos licenciados (apto para JOSS).
"""
import os
import json
import logging

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

logger = logging.getLogger(__name__)
MCP_URL = "https://mcp.drugbank.com/mcp"


def is_configured() -> bool:
    return bool(os.getenv("DRUGBANK_TOKEN"))


def _rpc(method: str, params: dict, token: str, req_id: int = 1):
    if requests is None:
        return None
    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    try:
        r = requests.post(MCP_URL, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "detail": r.text[:200]}
        # El MCP puede responder JSON o SSE; intentamos parsear ambos.
        txt = r.text.strip()
        if txt.startswith("{"):
            return r.json()
        for line in txt.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                try:
                    return json.loads(line[5:].strip())
                except Exception:
                    continue
        return {"raw": txt[:500]}
    except Exception as e:
        logger.warning(f"DrugBank MCP error: {e}")
        return {"error": str(e)}


def list_tools() -> dict:
    """Lista las herramientas disponibles del MCP (para descubrir su esquema)."""
    token = os.getenv("DRUGBANK_TOKEN")
    if not token:
        return {"configured": False,
                "message": "DrugBank no configurado. Define DRUGBANK_TOKEN (tu Bearer de DrugBank) para activarlo."}
    res = _rpc("tools/list", {}, token)
    return {"configured": True, "result": res}


def query_interactions(drug_or_compound: str) -> dict:
    """
    Consulta interacciones/ficha de un fármaco en DrugBank EN VIVO con el token del usuario.
    No almacena nada. El nombre de la 'tool' puede variar según el MCP de DrugBank;
    se intenta un tools/call genérico y se devuelve el resultado crudo para el clínico.
    """
    token = os.getenv("DRUGBANK_TOKEN")
    if not token:
        return {"configured": False,
                "message": "DrugBank no configurado. Se usan fuentes abiertas (PubMed/PubChem/curado)."}
    # Intento genérico: tools/call con nombre de herramienta común; el usuario/servidor
    # define la tool real. Devolvemos lo que responda para no inventar datos.
    res = _rpc("tools/call",
               {"name": "search_drugs", "arguments": {"query": drug_or_compound}}, token)
    return {"configured": True, "query": drug_or_compound, "result": res,
            "note": "Consulta en vivo a DrugBank con tu suscripción; los datos NO se almacenan."}
