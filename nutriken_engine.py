import os, json, asyncio, logging, re, sqlite3, datetime
from pathlib import Path
from typing import List, Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "local_db" / "nutriken_cache.db"
Path("local_db").mkdir(exist_ok=True)

# ── BASE DE CONOCIMIENTO: condición clínica → genes + nutrientes ──────────────
CLINICAL_MAP = {
    "obesidad": {
        "genes": ["FTO", "MC4R", "LEP", "LEPR", "PPARG", "ADIPOQ"],
        "nutrients": ["omega-3", "vitamin-d", "chromium", "berberine", "green-tea"],
        "risks": ["Pérdida de peso rápida puede causar cálculos biliares", "Déficit de vitaminas liposolubles en dietas muy restrictivas", "Riesgo de sarcopenia si no se preserva masa muscular"],
        "kegg_pathway": "hsa04920",
        "description": "La obesidad involucra alteraciones en genes reguladores del apetito, metabolismo energético y adipogénesis."
    },
    "perdida de peso": {
        "genes": ["FTO", "MC4R", "LEP", "LEPR", "PPARG"],
        "nutrients": ["omega-3", "green-tea", "chromium", "l-carnitine"],
        "risks": ["Pérdida de peso > 1.5kg/semana aumenta riesgo de cálculos biliares", "Déficit proteico puede causar pérdida muscular", "Rebote metabólico si no hay cambio de hábitos"],
        "kegg_pathway": "hsa04920",
        "description": "La regulación del peso corporal depende de señales hormonales (leptina, grelina) y variantes genéticas que modulan el gasto energético."
    },
    "diabetes": {
        "genes": ["TCF7L2", "PPARG", "KCNJ11", "SLC30A8", "HNF1A"],
        "nutrients": ["chromium", "berberine", "cinnamon", "magnesium", "vitamin-d"],
        "risks": ["Hipoglucemia con combinación de suplementos + metformina", "Berberina puede potenciar efecto hipoglucemiante", "Cromo en exceso puede ser nefrotóxico"],
        "kegg_pathway": "hsa04930",
        "description": "La diabetes tipo 2 involucra resistencia a insulina mediada por variantes en genes de señalización insulínica y función de célula beta pancreática."
    },
    "intolerancia lactosa": {
        "genes": ["LCT", "MCM6"],
        "nutrients": ["probiotics", "calcium", "vitamin-d"],
        "risks": ["Déficit de calcio si se elimina lácteos sin sustitución", "Déficit de vitamina D asociado", "Disbioisis intestinal si no se maneja bien"],
        "kegg_pathway": "hsa00052",
        "description": "La intolerancia a la lactosa se debe a variantes en el gen LCT que reducen la expresión de lactasa intestinal en la edad adulta."
    },
    "enfermedad celiaca": {
        "genes": ["HLA-DQ2", "HLA-DQ8", "IL2", "IL21"],
        "nutrients": ["vitamin-d", "folic-acid", "vitamin-b12", "iron", "zinc"],
        "risks": ["Déficit múltiple de micronutrientes por malabsorción", "Riesgo de contaminación cruzada con gluten", "Osteoporosis por malabsorción crónica de calcio"],
        "kegg_pathway": "hsa04940",
        "description": "La enfermedad celíaca es una respuesta autoinmune al gluten mediada por haplotipos HLA-DQ2/DQ8 que causa atrofia intestinal y malabsorción."
    },
    "deficit vitamina d": {
        "genes": ["VDR", "CYP27B1", "CYP2R1", "GC"],
        "nutrients": ["vitamin-d", "calcium", "magnesium", "vitamin-k"],
        "risks": ["Toxicidad por hipervitaminosis D (>4000 UI/día)", "Hipercalcemia si se combina con calcio en dosis altas", "Interacción con medicamentos antiepilépticos"],
        "kegg_pathway": "hsa04978",
        "description": "El metabolismo de la vitamina D depende de variantes en el receptor VDR y enzimas de hidroxilación que determinan la disponibilidad del calcitriol activo."
    },
    "deficit folato": {
        "genes": ["MTHFR", "FOLH1", "SLC19A1", "DHFR"],
        "nutrients": ["folic-acid", "vitamin-b12", "vitamin-b6"],
        "risks": ["Defectos del tubo neural en embarazo si hay déficit", "Hiperhomocisteinemia por variante MTHFR C677T", "Riesgo de enmascarar déficit B12 con altas dosis de folato"],
        "kegg_pathway": "hsa00670",
        "description": "El metabolismo del folato involucra al gen MTHFR cuya variante C677T reduce la actividad enzimática hasta 70%, aumentando homocisteína y riesgo cardiovascular."
    },
    "deficit b12": {
        "genes": ["TCN2", "MTRR", "MTR", "FUT2"],
        "nutrients": ["vitamin-b12", "folic-acid"],
        "risks": ["Neuropatía irreversible si el déficit es prolongado", "Anemia megaloblástica", "Puede enmascararse con altas dosis de folato"],
        "kegg_pathway": "hsa00670",
        "description": "El metabolismo de la vitamina B12 depende de transportadores como la transcobalamina II (TCN2) y enzimas como MTR y MTRR involucradas en el ciclo de metilación."
    },
    "microbiota": {
        "genes": ["NOD2", "FUT2", "IL23R", "CARD9"],
        "nutrients": ["probiotics", "prebiotics", "omega-3", "vitamin-d", "zinc"],
        "risks": ["Probióticos en inmunosuprimidos pueden causar infecciones", "Cambios rápidos de dieta pueden causar disbiosis transitoria"],
        "kegg_pathway": "hsa05321",
        "description": "La composición de la microbiota intestinal está influenciada por variantes genéticas del huésped que modulan la respuesta inmune y el reconocimiento bacteriano."
    },
    "colesterol": {
        "genes": ["APOE", "LDLR", "PCSK9", "HMGCR", "APOB"],
        "nutrients": ["fish-oil", "resveratrol", "garlic", "flaxseed", "green-tea"],
        "risks": ["Interacción de omega-3 con anticoagulantes", "Riesgo de sangrado con altas dosis de omega-3", "Ajo puede potenciar efecto de warfarina"],
        "kegg_pathway": "hsa04977",
        "description": "El metabolismo lipídico está regulado por variantes en APOE y LDLR que determinan el riesgo de hipercolesterolemia familiar y respuesta a intervención dietética."
    },
    "inflamacion": {
        "genes": ["TNF", "IL6", "CRP", "IL1B", "PTGS2"],
        "nutrients": ["omega-3", "turmeric", "resveratrol", "vitamin-d", "quercetin"],
        "risks": ["Cúrcuma puede inhibir absorción de hierro", "Altas dosis de omega-3 pueden afectar coagulación", "Resveratrol puede interactuar con anticoagulantes"],
        "kegg_pathway": "hsa04668",
        "description": "La inflamación crónica de bajo grado involucra citoquinas como TNF-α e IL-6, moduladas por nutrientes que actúan sobre vías de señalización NF-κB y COX-2."
    }
}

# Mapa de nutrientes a URL en MSK
MSK_HERB_MAP = {
    "omega-3": "fish-oil", "fish-oil": "fish-oil",
    "vitamin-d": "vitamin-d", "vitamina d": "vitamin-d",
    "chromium": "chromium", "cromo": "chromium",
    "berberine": "berberine", "berberina": "berberine",
    "green-tea": "green-tea", "te verde": "green-tea",
    "cinnamon": "cinnamon", "canela": "cinnamon",
    "magnesium": "magnesium", "magnesio": "magnesium",
    "l-carnitine": "l-carnitine", "carnitina": "l-carnitine",
    "probiotics": "probiotics", "probioticos": "probiotics",
    "folic-acid": "folic-acid", "folato": "folic-acid",
    "vitamin-b12": "vitamin-b12", "b12": "vitamin-b12",
    "zinc": "zinc",
    "selenium": "selenium", "selenio": "selenium",
    "turmeric": "turmeric", "curcuma": "turmeric",
    "resveratrol": "resveratrol",
    "garlic": "garlic", "ajo": "garlic",
    "flaxseed": "flaxseed", "linaza": "flaxseed",
    "quercetin": "quercetin", "quercetina": "quercetin",
    "aloe-vera": "aloe-vera",
    "ginger": "ginger", "jengibre": "ginger",
    "vitamin-c": "vitamin-c", "vitamina c": "vitamin-c",
    "vitamin-e": "vitamin-e", "vitamina e": "vitamin-e",
    "melatonin": "melatonin", "melatonina": "melatonin",
    "milk-thistle": "milk-thistle", "cardo mariano": "milk-thistle",
    "echinacea": "echinacea", "equinacea": "echinacea",
    "ginseng": "ginseng",
    "ashwagandha": "ashwagandha",
    "coenzyme-q10": "coenzyme-q10", "coq10": "coenzyme-q10",
}

# ── BASE DE DATOS SQLITE (caché) ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS herb_cache (
        slug TEXT PRIMARY KEY,
        name TEXT,
        data TEXT,
        fetched_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS gene_cache (
        gene_id TEXT PRIMARY KEY,
        data TEXT,
        fetched_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS query_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        query_type TEXT,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

def cache_get_herb(slug: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT data FROM herb_cache WHERE slug=?", (slug,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def cache_set_herb(slug: str, name: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO herb_cache VALUES (?,?,?,?)",
              (slug, name, json.dumps(data, ensure_ascii=False), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def cache_get_gene(gene_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT data FROM gene_cache WHERE gene_id=?", (gene_id.upper(),))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def cache_set_gene(gene_id: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO gene_cache VALUES (?,?,?)",
              (gene_id.upper(), json.dumps(data, ensure_ascii=False), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_query(query: str, qtype: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO query_log (query, query_type, timestamp) VALUES (?,?,?)",
              (query, qtype, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ── SCRAPERS ──────────────────────────────────────────────────────────────────
async def fetch_msk_herb(slug: str, client: httpx.AsyncClient) -> dict:
    """Fetch herb data from MSK in real time, with SQLite cache."""
    cached = cache_get_herb(slug)
    if cached:
        logger.info(f"💾 Cache hit: {slug}")
        return cached

    url = f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}"
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        if r.status_code != 200 or "Page Not Found" in r.text:
            return {"error": f"No encontrado en MSK: {slug}"}

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n")

        herb = {
            "name": slug.replace("-", " ").title(),
            "url": url,
            "scientific_name": "",
            "common_names": [],
            "what_is_it": "",
            "benefits": [],
            "side_effects": [],
            "warnings": [],
            "clinical_summary": "",
            "mechanism_of_action": "",
            "drug_interactions": [],
            "adverse_reactions": "",
            "purported_uses": []
        }

        # Scientific name
        m = re.search(r'Scientific Name\s*\n+([^\n]{3,100})', text)
        if m: herb["scientific_name"] = m.group(1).strip()

        # What is it
        m = re.search(r'What is it\?\s*\n+(.*?)(?=What are the potential|What are the side)', text, re.DOTALL)
        if m: herb["what_is_it"] = m.group(1).strip()[:600]

        # Benefits
        m = re.search(r'What are the potential uses and benefits\?\s*\n+(.*?)(?=What are the side effects)', text, re.DOTALL)
        if m:
            lines = [l.strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 5]
            herb["benefits"] = lines[:10]

        # Side effects
        m = re.search(r'What are the side effects\?\s*\n+(.*?)(?=What else do I need)', text, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 5]
            herb["side_effects"] = [l for l in lines if len(l) > 8][:12]

        # Warnings
        m = re.search(r'What else do I need to know\?\s*\n+(.*?)(?=For Healthcare|##)', text, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 10]
            herb["warnings"] = lines[:8]

        # Clinical summary
        m = re.search(r'Clinical Summary\s*\n+(.*?)(?=Food Sources|Purported Uses|Mechanism of Action|Pharmacology|Adverse)', text, re.DOTALL)
        if m: herb["clinical_summary"] = m.group(1).strip()[:1500]

        # Mechanism of action
        m = re.search(r'Mechanism of Action\s*\n+(.*?)(?=Pharmacology|Adverse Reactions|Herb-Drug|Dosage|References)', text, re.DOTALL)
        if m: herb["mechanism_of_action"] = m.group(1).strip()[:1200]

        # Drug interactions
        m = re.search(r'Herb-Drug Interactions\s*\n+(.*?)(?=Dosage|References|##)', text, re.DOTALL)
        if m:
            lines = [l.strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 10]
            herb["drug_interactions"] = lines[:10]

        # Adverse reactions
        m = re.search(r'Adverse Reactions\s*\n+(.*?)(?=Herb-Drug|Dosage|References)', text, re.DOTALL)
        if m: herb["adverse_reactions"] = m.group(1).strip()[:800]

        # Purported uses
        m = re.search(r'Purported Uses and Benefits\s*\n+(.*?)(?=Food Sources|Mechanism)', text, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip()]
            herb["purported_uses"] = [l for l in lines if len(l) > 3][:12]

        cache_set_herb(slug, herb["name"], herb)
        logger.info(f"✅ MSK scraped and cached: {slug}")
        return herb

    except Exception as e:
        logger.error(f"Error fetching MSK {slug}: {e}")
        return {"error": str(e), "slug": slug}


async def fetch_ncbi_gene(gene_symbol: str, client: httpx.AsyncClient) -> dict:
    """Fetch gene info from NCBI eUtils."""
    cached = cache_get_gene(gene_symbol)
    if cached:
        return cached

    try:
        # Search gene ID
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "gene", "term": f"{gene_symbol}[Gene Name] AND Homo sapiens[Organism]",
                  "retmode": "json", "retmax": 1}
        r = await client.get(search_url, params=params, timeout=10.0)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"symbol": gene_symbol, "error": "Gen no encontrado en NCBI"}

        gene_id = ids[0]

        # Fetch summary
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params2 = {"db": "gene", "id": gene_id, "retmode": "json"}
        r2 = await client.get(summary_url, params2, timeout=10.0)
        doc = r2.json().get("result", {}).get(gene_id, {})

        gene_data = {
            "symbol": gene_symbol.upper(),
            "gene_id": gene_id,
            "name": doc.get("description", ""),
            "full_name": doc.get("otheraliases", ""),
            "chromosome": doc.get("chromosome", ""),
            "location": doc.get("maplocation", ""),
            "summary": doc.get("summary", "")[:1000],
            "organism": "Homo sapiens",
            "ncbi_url": f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}"
        }

        cache_set_gene(gene_symbol, gene_data)
        return gene_data

    except Exception as e:
        return {"symbol": gene_symbol, "error": str(e)}


async def fetch_kegg_pathway(pathway_id: str, client: httpx.AsyncClient) -> dict:
    """Fetch KEGG pathway info."""
    try:
        url = f"https://rest.kegg.jp/get/{pathway_id}"
        r = await client.get(url, timeout=10.0)
        text = r.text

        pathway = {
            "id": pathway_id,
            "name": "",
            "description": "",
            "genes": [],
            "kegg_url": f"https://www.kegg.jp/pathway/{pathway_id}"
        }

        name_m = re.search(r'NAME\s+(.+)', text)
        if name_m: pathway["name"] = name_m.group(1).strip()

        desc_m = re.search(r'DESCRIPTION\s+(.*?)(?=\nCLASS|\nPATHWAY)', text, re.DOTALL)
        if desc_m: pathway["description"] = desc_m.group(1).strip()[:600]

        genes_m = re.search(r'GENE\s+(.*?)(?=\nCOMPOUND|\nREFERENCE|\nORG)', text, re.DOTALL)
        if genes_m:
            gene_lines = genes_m.group(1).strip().split('\n')
            for line in gene_lines[:20]:
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    pathway["genes"].append({"id": parts[0], "symbol": parts[1].rstrip(';')})

        return pathway
    except Exception as e:
        return {"id": pathway_id, "error": str(e)}


async def search_pubmed(query: str, client: httpx.AsyncClient, max_results: int = 5) -> list:
    """Search PubMed for references."""
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results, "sort": "relevance"}
        r = await client.get(search_url, params=params, timeout=10.0)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids: return []

        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params2 = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
        r2 = await client.get(fetch_url, params=params2, timeout=10.0)
        result = r2.json().get("result", {})

        refs = []
        for pmid in ids:
            art = result.get(pmid, {})
            authors = art.get("authors", [])
            author_str = authors[0].get("name", "") + " et al." if authors else ""
            refs.append({
                "pmid": pmid,
                "title": art.get("title", ""),
                "authors": author_str,
                "journal": art.get("fulljournalname", ""),
                "year": art.get("pubdate", "")[:4],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
        return refs
    except Exception as e:
        logger.warning(f"PubMed error: {e}")
        return []


# ── MODELOS DE REQUEST ─────────────────────────────────────────────────────────
class ClinicalQuery(BaseModel):
    query: str          # condición clínica en lenguaje natural
    language: str = "es"

class GeneQuery(BaseModel):
    genes: List[str]    # lista de genes ej: ["MTHFR", "VDR"]

class NutrientQuery(BaseModel):
    nutrient: str       # nombre del suplemento/nutriente


# ── APP FASTAPI ────────────────────────────────────────────────────────────────
app = FastAPI(title="NutriKen - Plataforma Bioinformática Nutricional", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve static files exactly like Kenryu
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    init_db()
    logger.info("🌿 NutriKen iniciado — base de datos lista")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/script.js")
async def get_script():
    return FileResponse("static/script.js")

@app.get("/style.css")
async def get_style():
    return FileResponse("static/style.css")

@app.get("/health")
async def health():
    return {"status": "ok", "platform": "NutriKen v1.0"}


# ── ENDPOINT 1: CONSULTA CLÍNICA (lenguaje natural) ───────────────────────────
@app.post("/api/clinical")
async def clinical_analysis(req: ClinicalQuery):
    query_clean = req.query.lower().strip()
    log_query(req.query, "clinical")

    # Buscar match en mapa clínico
    matched_key = None
    matched_data = None
    for key, data in CLINICAL_MAP.items():
        if key in query_clean or any(word in query_clean for word in key.split()):
            matched_key = key
            matched_data = data
            break

    if not matched_data:
        # Búsqueda flexible por palabras clave
        for key, data in CLINICAL_MAP.items():
            words = key.split()
            if any(w in query_clean for w in words if len(w) > 3):
                matched_key = key
                matched_data = data
                break

    if not matched_data:
        raise HTTPException(status_code=404, detail=f"Condición '{req.query}' no encontrada. Prueba: obesidad, diabetes, intolerancia lactosa, déficit vitamina D, folato, B12, colesterol, inflamación, microbiota.")

    async with httpx.AsyncClient(headers={"User-Agent": "NutriKen/1.0 (educational tool)"}) as client:
        # Genes info
        gene_tasks = [fetch_ncbi_gene(g, client) for g in matched_data["genes"][:4]]
        genes_info = await asyncio.gather(*gene_tasks)

        # KEGG pathway
        pathway_info = await fetch_kegg_pathway(matched_data["kegg_pathway"], client)

        # MSK herbs
        herb_slugs = [MSK_HERB_MAP.get(n, n) for n in matched_data["nutrients"][:4]]
        herb_tasks = [fetch_msk_herb(slug, client) for slug in herb_slugs]
        herbs_info = await asyncio.gather(*herb_tasks)

        # PubMed references
        pubmed_query = f"{matched_key} nutrigenomics nutrition genetics"
        references = await search_pubmed(pubmed_query, client, max_results=5)

    return {
        "query": req.query,
        "condition": matched_key.title(),
        "description": matched_data["description"],
        "risks": matched_data["risks"],
        "genes": [g for g in genes_info if "error" not in g],
        "pathway": pathway_info,
        "supplements": [h for h in herbs_info if "error" not in h],
        "references": references,
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT 2: CONSULTA POR GEN ──────────────────────────────────────────────
@app.post("/api/gene")
async def gene_analysis(req: GeneQuery):
    genes = [g.upper().strip() for g in req.genes[:6]]
    log_query(",".join(genes), "gene")

    async with httpx.AsyncClient(headers={"User-Agent": "NutriKen/1.0"}) as client:
        gene_tasks = [fetch_ncbi_gene(g, client) for g in genes]
        genes_info = await asyncio.gather(*gene_tasks)

        # Buscar qué condiciones clínicas están relacionadas
        related_conditions = []
        for key, data in CLINICAL_MAP.items():
            overlap = [g for g in genes if g in data["genes"]]
            if overlap:
                related_conditions.append({
                    "condition": key.title(),
                    "matching_genes": overlap,
                    "nutrients": data["nutrients"],
                    "risks": data["risks"]
                })

        # PubMed
        pubmed_query = f"{' '.join(genes[:3])} nutrition SNP nutrigenomics"
        references = await search_pubmed(pubmed_query, client, max_results=5)

        # MSK herbs para los nutrientes relacionados
        all_nutrients = list(set(n for c in related_conditions for n in c["nutrients"][:2]))
        herb_slugs = [MSK_HERB_MAP.get(n, n) for n in all_nutrients[:4]]
        herb_tasks = [fetch_msk_herb(slug, client) for slug in herb_slugs]
        herbs_info = await asyncio.gather(*herb_tasks)

    return {
        "genes_queried": genes,
        "genes_info": [g for g in genes_info if "error" not in g],
        "related_conditions": related_conditions,
        "supplements": [h for h in herbs_info if "error" not in h],
        "references": references,
        "snpedia_urls": [f"https://www.snpedia.com/index.php/{g}" for g in genes],
        "ensembl_urls": [f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?q={g}" for g in genes],
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT 3: CONSULTA POR SUPLEMENTO/HIERBA ────────────────────────────────
@app.post("/api/nutrient")
async def nutrient_analysis(req: NutrientQuery):
    nutrient_clean = req.nutrient.lower().strip()
    log_query(req.nutrient, "nutrient")

    slug = MSK_HERB_MAP.get(nutrient_clean, nutrient_clean.replace(" ", "-"))

    async with httpx.AsyncClient(headers={"User-Agent": "NutriKen/1.0"}) as client:
        herb_data = await fetch_msk_herb(slug, client)
        if "error" in herb_data:
            raise HTTPException(status_code=404, detail=f"Suplemento '{req.nutrient}' no encontrado en MSK. Verifica el nombre.")

        # Buscar pathway en KEGG relacionado
        kegg_search_url = f"https://rest.kegg.jp/find/pathway/{slug.replace('-', '+')}"
        pathway_info = {}
        try:
            r = await client.get(kegg_search_url, timeout=8.0)
            lines = r.text.strip().split('\n')
            if lines and lines[0]:
                parts = lines[0].split('\t')
                if len(parts) >= 2:
                    pathway_info = {"id": parts[0].replace("path:", ""), "name": parts[1], "kegg_url": f"https://www.kegg.jp/pathway/{parts[0].replace('path:','')}"}
        except:
            pass

        references = await search_pubmed(f"{req.nutrient} clinical trial nutrition", client, max_results=5)

    return {
        "nutrient": req.nutrient,
        "msk_data": herb_data,
        "pathway": pathway_info,
        "references": references,
        "msk_url": f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}",
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT: ESTADÍSTICAS DE CACHÉ ───────────────────────────────────────────
@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM herb_cache")
    herbs_cached = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gene_cache")
    genes_cached = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM query_log")
    total_queries = c.fetchone()[0]
    c.execute("SELECT query, timestamp FROM query_log ORDER BY id DESC LIMIT 5")
    recent = c.fetchall()
    conn.close()
    return {
        "herbs_in_cache": herbs_cached,
        "genes_in_cache": genes_cached,
        "total_queries": total_queries,
        "recent_queries": [{"query": r[0], "time": r[1]} for r in recent]
    }


if __name__ == "__main__":
    uvicorn.run("nutriken_engine:app", host="0.0.0.0", port=7860, reload=False)


