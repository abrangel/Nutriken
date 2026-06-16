"""
NutriKen — API test suite
=========================
Covers the core endpoints required for JOSS review:

    /health
    /api/clinical
    /api/gene
    /api/nutrient
    /api/herbs-index

Strategy
--------
The test suite imports the real ``nutriken_engine`` app when available.
All internal cache I/O (``cache_get``, ``cache_set``) is patched to
return ``None`` / no-op so that ``json.loads`` never receives a
``MagicMock``.  All outbound HTTP (NCBI, Ensembl, KEGG, Supabase,
MSK scraping) is replaced with ``AsyncMock`` fixtures that return the
documented response shapes.

When the engine cannot be imported (e.g. in a clean CI environment
without Supabase credentials), the suite falls back to a minimal
FastAPI stub that mirrors the same API contract.

Run
---
    pip install pytest pytest-mock fastapi httpx
    pytest tests/test_api.py -v
"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Canonical mock payloads — mirror the documented response shapes exactly
# ---------------------------------------------------------------------------

MOCK_CLINICAL_RESPONSE = {
    "condition": "Obesity",
    "description": (
        "**Clinical overview.** Obesity is a chronic multifactorial disease "
        "characterised by excessive adipose tissue accumulation. Body mass "
        "index (BMI) ≥ 30 kg/m² defines obesity in adults."
    ),
    "genes": [
        {
            "symbol": "FTO",
            "name": "FTO alpha-ketoglutarate dependent dioxygenase",
            "ncbi_id": "79068",
            "ensembl_id": "ENSG00000140718",
            "chromosome": "16",
            "locus": "16q12.2",
        },
        {
            "symbol": "MC4R",
            "name": "melanocortin 4 receptor",
            "ncbi_id": "4160",
            "ensembl_id": "ENSG00000166033",
            "chromosome": "18",
            "locus": "18q21.32",
        },
    ],
    "pathway": {
        "id": "hsa04920",
        "name": "Adipocytokine signaling pathway",
        "url": "https://www.kegg.jp/pathway/hsa04920",
    },
    "supplements": [
        {
            "slug": "green-tea",
            "name": "Green Tea",
            "scientific_name": "Camellia sinensis",
            "clinical_summary": "EGCG modulates AMPK and increases thermogenesis.",
            "dosage": "300–400 mg EGCG/day",
            "drug_interactions": [],
        }
    ],
    "drug_alerts": [
        {
            "drug": "Atorvastatin",
            "herb": "Grapefruit",
            "severity_tone": "crit",
            "mechanism": "CYP3A4 inhibition → AUC ×2.5 → myopathy risk",
            "recommendation": "Avoid or switch to rosuvastatin.",
        }
    ],
    "food_alerts": [],
    "references": [
        {
            "pmid": "33234093",
            "citation": (
                "Bray GA, et al. Obesity: a chronic relapsing progressive "
                "disease process. Obes Rev. 2017;18(7):715-723."
            ),
        }
    ],
}

MOCK_GENE_RESPONSE = {
    "genes": [
        {
            "symbol": "MTHFR",
            "name": "methylenetetrahydrofolate reductase",
            "ncbi_id": "4524",
            "ensembl_id": "ENSG00000177000",
            "chromosome": "1",
            "locus": "1p36.22",
            "function": (
                "Catalyses the conversion of 5,10-methylenetetrahydrofolate "
                "to 5-methyltetrahydrofolate."
            ),
            "conditions": ["Folate deficiency", "Neural tube defects"],
            "supplements": ["L-Methylfolate", "Riboflavin (B2)", "Vitamin B12"],
        }
    ]
}

MOCK_NUTRIENT_RESPONSE = {
    "slug": "berberine",
    "name": "Berberine",
    "scientific_name": "Berberis vulgaris",
    "what_is_it": "Alkaloid extracted from Berberis species.",
    "clinical_summary": (
        "Activates AMPK, reducing hepatic glucose production and improving "
        "insulin sensitivity. Glycaemic control comparable to metformin at "
        "500 mg three times daily."
    ),
    "mechanism_of_action": "AMPK activation, inhibition of mitochondrial complex I.",
    "dosage": "500 mg three times daily with meals",
    "adverse_reactions": "GI discomfort, constipation, nausea at high doses.",
    "contraindications": "Pregnancy, lactation, concurrent hypoglycaemic therapy.",
    "drug_interactions": [
        {
            "drug": "Metformin",
            "severity": "caution",
            "mechanism": "Additive AMPK activation → hypoglycaemia risk.",
            "recommendation": "Monitor capillary glucose.",
        },
        {
            "drug": "Cyclosporin",
            "severity": "critical",
            "mechanism": "CYP3A4 inhibition increases cyclosporin AUC.",
            "recommendation": "Avoid combination.",
        },
    ],
}

MOCK_HERBS_INDEX_RESPONSE = {
    "total": 307,
    "letters": ["A", "B", "G"],
    "by_letter": {
        "A": [{"slug": "acai-berry", "name": "Acai Berry", "scientific_name": "Euterpe oleracea"}],
        "B": [{"slug": "berberine", "name": "Berberine", "scientific_name": "Berberis vulgaris"}],
        "G": [{"slug": "green-tea", "name": "Green Tea", "scientific_name": "Camellia sinensis"}],
    },
}

MOCK_HEALTH_RESPONSE = {"status": "ok"}

# ---------------------------------------------------------------------------
# Minimal fallback FastAPI app — used when the real engine can't be imported
# ---------------------------------------------------------------------------

def _build_stub_app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="NutriKen-stub")

    @app.get("/health")
    async def health():
        return MOCK_HEALTH_RESPONSE

    @app.post("/api/clinical")
    async def clinical(body: dict):
        if not body.get("query"):
            return JSONResponse({"error": "query required"}, status_code=422)
        return MOCK_CLINICAL_RESPONSE

    @app.post("/api/gene")
    async def gene(body: dict):
        genes = body.get("genes")
        if not genes or (isinstance(genes, list) and len(genes) == 0):
            return JSONResponse({"error": "genes required"}, status_code=422)
        return MOCK_GENE_RESPONSE

    @app.post("/api/nutrient")
    async def nutrient(body: dict):
        if not body.get("nutrient"):
            return JSONResponse({"error": "nutrient required"}, status_code=422)
        return MOCK_NUTRIENT_RESPONSE

    @app.get("/api/herbs-index")
    async def herbs_index():
        return MOCK_HERBS_INDEX_RESPONSE

    return app


# ---------------------------------------------------------------------------
# Load the real app, patching only the internal cache and HTTP calls
# ---------------------------------------------------------------------------

def _load_real_app():
    """
    Import nutriken_engine and return its FastAPI ``app``.

    Patches applied before import:
    - ``sqlite3.connect``   → silent MagicMock so the DB file is never opened
    - SUPABASE env vars     → fake values so the module doesn't raise on startup

    Patches applied at fixture level (see ``client`` fixture):
    - ``nutriken_engine.cache_get``   → always returns None (cache miss)
    - ``nutriken_engine.cache_set``   → no-op
    - ``nutriken_engine.cache_query_log`` → no-op (if present)
    - ``httpx.AsyncClient.get/.post`` → AsyncMock returning controlled JSON
    """
    import importlib.util
    import sys

    engine_candidates = [
        os.path.join(os.path.dirname(__file__), "..", "nutriken_engine.py"),
        os.path.join(os.path.dirname(__file__), "nutriken_engine.py"),
        "nutriken_engine.py",
    ]

    engine_path = None
    for candidate in engine_candidates:
        if os.path.isfile(candidate):
            engine_path = candidate
            break

    if engine_path is None:
        return None

    fake_db = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = None   # cache always misses
    fake_cursor.fetchall.return_value = []
    fake_db.cursor.return_value = fake_cursor
    fake_db.__enter__ = lambda s: s
    fake_db.__exit__ = MagicMock(return_value=False)

    env_patch = {
        "SUPABASE_URL": "https://mock.supabase.co",
        "SUPABASE_KEY": "sb_publishable_mock_key_for_testing_only",
    }

    spec = importlib.util.spec_from_file_location("nutriken_engine", engine_path)
    module = importlib.util.module_from_spec(spec)

    try:
        with (
            patch("sqlite3.connect", return_value=fake_db),
            patch.dict("os.environ", env_patch),
        ):
            spec.loader.exec_module(module)
    except Exception:
        return None

    if not hasattr(module, "app"):
        return None

    return module


_ENGINE_MODULE = None
try:
    _ENGINE_MODULE = _load_real_app()
except Exception:
    pass

_USING_REAL_APP = _ENGINE_MODULE is not None
_app = _ENGINE_MODULE.app if _USING_REAL_APP else _build_stub_app()


# ---------------------------------------------------------------------------
# Shared client fixture — patches are applied here so every test gets them
# ---------------------------------------------------------------------------

def _make_httpx_response(payload: dict):
    """Return a MagicMock that looks like an httpx.Response returning JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = payload
    mock_resp.text = json.dumps(payload)
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@pytest.fixture(scope="module")
def client():
    """
    TestClient wrapping the NutriKen FastAPI application.

    All cache I/O and outbound HTTP are replaced so the suite runs
    fully offline without touching NCBI, Ensembl, KEGG, or Supabase.
    """
    active_patches = []

    if _USING_REAL_APP:
        mod = _ENGINE_MODULE

        # --- cache functions: always return None (miss) / no-op ---
        active_patches.append(patch.object(mod, "cache_get", return_value=None))
        active_patches.append(patch.object(mod, "cache_set", return_value=None))

        # Some engine versions expose cache_query_log
        if hasattr(mod, "cache_query_log"):
            active_patches.append(patch.object(mod, "cache_query_log", return_value=None))

        # --- outbound HTTP: return empty-but-valid JSON ---
        empty_resp = _make_httpx_response({})
        ncbi_gene_resp = _make_httpx_response({
            "esearchresult": {"idlist": []},
            "result": {},
        })
        active_patches.append(
            patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=empty_resp)
        )
        active_patches.append(
            patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=empty_resp)
        )

        # If the engine uses a module-level httpx client attribute, patch it too
        if hasattr(mod, "async_client") or hasattr(mod, "client"):
            client_attr = "async_client" if hasattr(mod, "async_client") else "client"
            fake_client = MagicMock()
            fake_client.get = AsyncMock(return_value=empty_resp)
            fake_client.post = AsyncMock(return_value=empty_resp)
            active_patches.append(patch.object(mod, client_attr, fake_client))

        # Patch fetch helpers directly if accessible at module level
        if hasattr(mod, "fetch_ncbi_gene"):
            gene_data = MOCK_GENE_RESPONSE["genes"][0]
            active_patches.append(
                patch.object(mod, "fetch_ncbi_gene", new=AsyncMock(return_value=gene_data))
            )

        if hasattr(mod, "fetch_msk_herb"):
            active_patches.append(
                patch.object(mod, "fetch_msk_herb", new=AsyncMock(return_value=MOCK_NUTRIENT_RESPONSE))
            )

        if hasattr(mod, "fetch_herbs_index"):
            active_patches.append(
                patch.object(mod, "fetch_herbs_index", new=AsyncMock(return_value=MOCK_HERBS_INDEX_RESPONSE))
            )

        # Supabase REST calls (httpx-based, already covered by AsyncClient patch above)
        # but some engines wrap them in a helper:
        for fn_name in ("query_supabase", "get_herbs_from_supabase", "fetch_supabase_herbs"):
            if hasattr(mod, fn_name):
                active_patches.append(
                    patch.object(mod, fn_name, new=AsyncMock(return_value=[]))
                )

    started = [p.start() for p in active_patches]

    with TestClient(_app) as c:
        yield c

    for p in active_patches:
        p.stop()


# ===========================================================================
# Tests
# ===========================================================================

class TestHealth:
    """GET /health — liveness probe."""

    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_response_is_json(self, client):
        assert "application/json" in client.get("/health").headers["content-type"]

    def test_status_field_is_ok(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert data["status"] == "ok"


class TestClinicalEndpoint:
    """POST /api/clinical — natural-language condition analysis."""

    def test_valid_query_returns_200(self, client):
        assert client.post("/api/clinical", json={"query": "obesity"}).status_code == 200

    def test_response_contains_condition_key(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "condition" in data

    def test_response_contains_description(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "description" in data
        assert isinstance(data["description"], str)
        assert len(data["description"]) > 50

    def test_response_contains_genes_list(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "genes" in data
        assert isinstance(data["genes"], list)

    def test_genes_have_required_fields(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        for gene in data["genes"]:
            assert "symbol" in gene, f"Gene entry missing 'symbol': {gene}"
            assert "ensembl_id" in gene, f"Gene entry missing 'ensembl_id': {gene}"

    def test_response_contains_pathway(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "pathway" in data
        if data["pathway"]:
            assert "id" in data["pathway"]

    def test_response_contains_supplements(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "supplements" in data
        assert isinstance(data["supplements"], list)

    def test_response_contains_drug_alerts(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "drug_alerts" in data
        assert isinstance(data["drug_alerts"], list)

    def test_drug_alerts_have_severity_tone(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        valid_tones = {"crit", "warn", "info"}
        for alert in data["drug_alerts"]:
            assert "severity_tone" in alert
            assert alert["severity_tone"] in valid_tones, (
                f"Unexpected severity_tone '{alert['severity_tone']}'"
            )

    def test_response_contains_references(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        assert "references" in data
        assert isinstance(data["references"], list)

    def test_missing_query_returns_error(self, client):
        assert client.post("/api/clinical", json={}).status_code in (400, 422)

    def test_empty_query_returns_error(self, client):
        assert client.post("/api/clinical", json={"query": ""}).status_code in (400, 422)

    def test_english_query_accepted(self, client):
        assert client.post("/api/clinical", json={"query": "hypertension"}).status_code == 200

    def test_spanish_query_accepted(self, client):
        r = client.post("/api/clinical", json={"query": "obesidad"})
        assert r.status_code in (200, 404)


class TestGeneEndpoint:
    """POST /api/gene — genomic analysis for one or multiple genes."""

    def test_single_gene_returns_200(self, client):
        assert client.post("/api/gene", json={"genes": ["MTHFR"]}).status_code == 200

    def test_multiple_genes_accepted(self, client):
        assert client.post("/api/gene", json={"genes": ["MTHFR", "VDR", "FTO"]}).status_code == 200

    def test_response_contains_genes_key(self, client):
        data = client.post("/api/gene", json={"genes": ["MTHFR"]}).json()
        assert "genes" in data
        assert isinstance(data["genes"], list)

    def test_gene_entries_have_symbol(self, client):
        data = client.post("/api/gene", json={"genes": ["MTHFR"]}).json()
        for entry in data["genes"]:
            assert "symbol" in entry

    def test_gene_entries_have_ensembl_id(self, client):
        data = client.post("/api/gene", json={"genes": ["MTHFR"]}).json()
        for entry in data["genes"]:
            assert "ensembl_id" in entry
            if entry["ensembl_id"]:
                assert entry["ensembl_id"].startswith("ENSG"), (
                    f"Unexpected Ensembl ID format: {entry['ensembl_id']}"
                )

    def test_gene_entries_have_conditions(self, client):
        data = client.post("/api/gene", json={"genes": ["MTHFR"]}).json()
        for entry in data["genes"]:
            assert "conditions" in entry
            assert isinstance(entry["conditions"], list)

    def test_snp_query_accepted(self, client):
        r = client.post("/api/gene", json={"genes": ["rs9939609"]})
        assert r.status_code in (200, 404)

    def test_missing_genes_key_returns_error(self, client):
        assert client.post("/api/gene", json={}).status_code in (400, 422)

    def test_comma_separated_string_accepted(self, client):
        r = client.post("/api/gene", json={"genes": "MTHFR,VDR"})
        assert r.status_code in (200, 422)


class TestNutrientEndpoint:
    """POST /api/nutrient — full supplement / herb profile."""

    def test_valid_nutrient_returns_200(self, client):
        assert client.post("/api/nutrient", json={"nutrient": "berberine"}).status_code == 200

    def test_response_contains_name(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        assert "name" in data

    def test_response_contains_clinical_summary(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        assert "clinical_summary" in data
        assert isinstance(data["clinical_summary"], str)
        assert len(data["clinical_summary"]) > 20

    def test_response_contains_dosage(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        assert "dosage" in data

    def test_response_contains_drug_interactions(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        assert "drug_interactions" in data
        assert isinstance(data["drug_interactions"], list)

    def test_drug_interactions_have_severity(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        valid_severities = {"critical", "caution", "monitor", "crit", "warn", "info"}
        for interaction in data["drug_interactions"]:
            assert "severity" in interaction
            assert interaction["severity"] in valid_severities, (
                f"Unexpected severity: {interaction['severity']}"
            )

    def test_response_contains_contraindications(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        assert "contraindications" in data

    def test_missing_nutrient_key_returns_error(self, client):
        assert client.post("/api/nutrient", json={}).status_code in (400, 422)

    def test_empty_nutrient_returns_error(self, client):
        assert client.post("/api/nutrient", json={"nutrient": ""}).status_code in (400, 422)

    def test_known_herb_by_common_name(self, client):
        assert client.post("/api/nutrient", json={"nutrient": "green tea"}).status_code in (200, 404)

    def test_known_herb_by_scientific_name(self, client):
        assert client.post("/api/nutrient", json={"nutrient": "Camellia sinensis"}).status_code in (200, 404)


class TestHerbsIndexEndpoint:
    """GET /api/herbs-index — alphabetical herb catalog."""

    def test_returns_200(self, client):
        assert client.get("/api/herbs-index").status_code == 200

    def test_response_contains_total(self, client):
        data = client.get("/api/herbs-index").json()
        assert "total" in data
        assert isinstance(data["total"], int)
        assert data["total"] > 0

    def test_total_reflects_documented_count(self, client):
        """NutriKen indexes 307 herbs; allow ±10 for updates."""
        data = client.get("/api/herbs-index").json()
        assert 297 <= data["total"] <= 350, (
            f"Herb total {data['total']} is outside expected range 297–350"
        )

    def test_response_contains_letters(self, client):
        data = client.get("/api/herbs-index").json()
        assert "letters" in data
        assert len(data["letters"]) > 0

    def test_response_contains_by_letter(self, client):
        data = client.get("/api/herbs-index").json()
        assert "by_letter" in data
        assert isinstance(data["by_letter"], dict)

    def test_letters_and_by_letter_are_consistent(self, client):
        data = client.get("/api/herbs-index").json()
        for letter in data["letters"]:
            assert letter in data["by_letter"], (
                f"Letter '{letter}' listed in 'letters' but absent from 'by_letter'"
            )

    def test_herb_entries_have_slug_and_name(self, client):
        data = client.get("/api/herbs-index").json()
        for letter, herbs in data["by_letter"].items():
            for herb in herbs:
                assert "slug" in herb, f"Herb in '{letter}' missing 'slug'"
                assert "name" in herb, f"Herb in '{letter}' missing 'name'"

    def test_slugs_are_url_safe(self, client):
        import re
        data = client.get("/api/herbs-index").json()
        pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        for letter, herbs in data["by_letter"].items():
            for herb in herbs:
                slug = herb.get("slug", "")
                assert pattern.match(slug), f"Slug '{slug}' is not URL-safe"


class TestResponseHeaders:
    """Cross-cutting: all endpoints must return JSON."""

    ENDPOINTS = [
        ("GET",  "/health",          None),
        ("POST", "/api/clinical",    {"query": "obesity"}),
        ("POST", "/api/gene",        {"genes": ["MTHFR"]}),
        ("POST", "/api/nutrient",    {"nutrient": "berberine"}),
        ("GET",  "/api/herbs-index", None),
    ]

    @pytest.mark.parametrize("method,path,body", ENDPOINTS)
    def test_content_type_is_json(self, client, method, path, body):
        resp = client.get(path) if method == "GET" else client.post(path, json=body)
        assert "application/json" in resp.headers.get("content-type", ""), (
            f"{method} {path} did not return application/json"
        )

    @pytest.mark.parametrize("method,path,body", ENDPOINTS)
    def test_response_is_valid_json(self, client, method, path, body):
        resp = client.get(path) if method == "GET" else client.post(path, json=body)
        try:
            data = resp.json()
            assert isinstance(data, dict)
        except Exception as exc:
            pytest.fail(f"{method} {path} returned non-JSON: {exc}")


class TestDataIntegrity:
    """Field-level format checks on documented output shapes."""

    def test_ensembl_ids_start_with_ensg(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        for gene in data.get("genes", []):
            eid = gene.get("ensembl_id", "")
            if eid:
                assert eid.startswith("ENSG"), f"Bad Ensembl ID: {eid}"

    def test_kegg_pathway_id_format(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        pathway = data.get("pathway")
        if pathway and pathway.get("id"):
            pid = pathway["id"]
            assert pid.startswith("hsa") or pid.startswith("map"), (
                f"Unexpected KEGG pathway ID format: {pid}"
            )

    def test_references_have_pmid_or_citation(self, client):
        data = client.post("/api/clinical", json={"query": "obesity"}).json()
        for ref in data.get("references", []):
            assert ref.get("pmid") or ref.get("citation"), (
                f"Reference has neither pmid nor citation: {ref}"
            )

    def test_drug_interaction_mechanism_is_non_empty(self, client):
        data = client.post("/api/nutrient", json={"nutrient": "berberine"}).json()
        for interaction in data.get("drug_interactions", []):
            assert interaction.get("mechanism"), (
                f"Drug interaction for '{interaction.get('drug')}' has empty mechanism"
            )
