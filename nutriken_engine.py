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

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "local_db" / "nutriken_cache.db"
Path("local_db").mkdir(exist_ok=True)

# ── MAPA CONDICIÓN → SLUGS MSK + TÉRMINOS PUBMED ──────────────────────────────
# Cada condición tiene:
#   msk_slugs: hierbas/suplementos de MSK directamente relacionados
#   genes: genes NCBI asociados
#   kegg: ruta metabólica KEGG
#   pubmed_terms: términos de búsqueda PubMed
#   drugs: fármacos convencionales relacionados (para buscar interacciones)
CLINICAL_MAP = {
    "obesidad": {
        "genes": ["FTO","MC4R","LEP","LEPR","PPARG","ADIPOQ"],
        "kegg": "hsa04920",
        "msk_slugs": ["green-tea","chromium","berberine","conjugated-linoleic-acid","garcinia","glucomannan","pyruvate","chitosan","5-htp-01","l-carnitine","cinnamon","alpha-lipoic-acid"],
        "drugs": ["orlistat","semaglutide","phentermine","metformin","liraglutide","topiramate"],
        "pubmed_terms": "obesity supplement herbal weight loss clinical trial",
    },
    "perdida de peso": {
        "genes": ["FTO","MC4R","LEP","LEPR","PPARG"],
        "kegg": "hsa04920",
        "msk_slugs": ["green-tea","chromium","berberine","conjugated-linoleic-acid","garcinia","glucomannan","5-htp-01","l-carnitine","cinnamon"],
        "drugs": ["orlistat","semaglutide","phentermine"],
        "pubmed_terms": "weight loss supplement herbal nutrition clinical evidence",
    },
    "diabetes": {
        "genes": ["TCF7L2","PPARG","KCNJ11","SLC30A8","HNF1A"],
        "kegg": "hsa04930",
        "msk_slugs": ["berberine","chromium","cinnamon","magnesium","fenugreek","alpha-lipoic-acid","gymnema","bitter-melon","aloe-vera","ginseng"],
        "drugs": ["metformin","glipizide","insulin","sitagliptin","empagliflozin","semaglutide"],
        "pubmed_terms": "diabetes type 2 herbal supplement glycemic control clinical",
    },
    "colesterol": {
        "genes": ["APOE","LDLR","PCSK9","HMGCR","APOB"],
        "kegg": "hsa04977",
        "msk_slugs": ["fish-oil","garlic","red-yeast-rice","flaxseed","green-tea","resveratrol","milk-thistle","berberine","coenzyme-q10","niacin"],
        "drugs": ["atorvastatina","rosuvastatina","simvastatina","ezetimibe","fenofibrato"],
        "pubmed_terms": "cholesterol statin supplement interaction silymarin CoQ10 clinical",
    },
    "intolerancia lactosa": {
        "genes": ["LCT","MCM6"],
        "kegg": "hsa00052",
        "msk_slugs": ["probiotics","lactobacillus","calcium","vitamin-d"],
        "drugs": ["lactasa"],
        "pubmed_terms": "lactose intolerance probiotics calcium vitamin D supplement",
    },
    "enfermedad celiaca": {
        "genes": ["HLA-DQ2","HLA-DQ8","IL2","IL21"],
        "kegg": "hsa04940",
        "msk_slugs": ["vitamin-d","folic-acid","selenium","zinc","iron","vitamin-b12","magnesium"],
        "drugs": [],
        "pubmed_terms": "celiac disease gluten micronutrient deficiency supplement",
    },
    "deficit vitamina d": {
        "genes": ["VDR","CYP27B1","CYP2R1","GC"],
        "kegg": "hsa04978",
        "msk_slugs": ["vitamin-d","calcium","magnesium","vitamin-k"],
        "drugs": ["colecalciferol","ergocalciferol"],
        "pubmed_terms": "vitamin D deficiency supplementation clinical evidence",
    },
    "deficit folato": {
        "genes": ["MTHFR","FOLH1","SLC19A1","DHFR"],
        "kegg": "hsa00670",
        "msk_slugs": ["folic-acid","vitamin-b12","vitamin-b6"],
        "drugs": ["acido folico","methotrexate"],
        "pubmed_terms": "folate deficiency MTHFR supplementation homocysteine clinical",
    },
    "deficit b12": {
        "genes": ["TCN2","MTRR","MTR","FUT2"],
        "kegg": "hsa00670",
        "msk_slugs": ["vitamin-b12","folic-acid"],
        "drugs": ["cianocobalamina","hidroxocobalamina"],
        "pubmed_terms": "vitamin B12 deficiency supplementation cobalamin clinical",
    },
    "microbiota": {
        "genes": ["NOD2","FUT2","IL23R","CARD9"],
        "kegg": "hsa05321",
        "msk_slugs": ["probiotics","prebiotics","omega-3-fatty-acids","vitamin-d","zinc","glutamine"],
        "drugs": ["antibioticos","rifaximina"],
        "pubmed_terms": "gut microbiota probiotic prebiotic nutrition clinical evidence",
    },
    "inflamacion": {
        "genes": ["TNF","IL6","CRP","IL1B","PTGS2"],
        "kegg": "hsa04668",
        "msk_slugs": ["turmeric","fish-oil","resveratrol","quercetin","vitamin-d","boswellia","ginger","green-tea"],
        "drugs": ["ibuprofeno","naproxeno","celecoxib","prednisona"],
        "pubmed_terms": "inflammation herbal anti-inflammatory supplement clinical trial",
    },
    "higado": {
        "genes": ["PNPLA3","TM6SF2","MBOAT7","GCKR"],
        "kegg": "hsa04932",
        "msk_slugs": ["milk-thistle","artichoke","dandelion","alpha-lipoic-acid","vitamin-e","berberine"],
        "drugs": ["atorvastatina","silimarina"],
        "pubmed_terms": "liver hepatoprotective silymarin milk thistle supplement clinical",
    },
    "hipertension": {
        "genes": ["ACE","AGT","AGTR1","ADD1"],
        "kegg": "hsa04614",
        "msk_slugs": ["garlic","fish-oil","coenzyme-q10","magnesium","hibiscus","hawthorn"],
        "drugs": ["enalapril","losartan","amlodipino","hidroclorotiazida"],
        "pubmed_terms": "hypertension herbal supplement blood pressure clinical",
    },
    "atorvastatina": {
        "genes": ["HMGCR","APOE","LDLR"],
        "kegg": "hsa04977",
        "msk_slugs": ["milk-thistle","coenzyme-q10","red-yeast-rice","fish-oil","vitamin-d"],
        "drugs": ["atorvastatina","rosuvastatina","simvastatina"],
        "pubmed_terms": "statin atorvastatin supplement interaction CoQ10 silymarin myopathy",
    },
    "silimarina": {
        "genes": ["CYP3A4","CYP2C9","ABCB1"],
        "kegg": "hsa00591",
        "msk_slugs": ["milk-thistle","vitamin-e","alpha-lipoic-acid","artichoke"],
        "drugs": ["estatinas","metformin","ciclosporina","anticoagulantes"],
        "pubmed_terms": "silymarin milk thistle hepatoprotective statin interaction clinical",
    },
    "omega 3": {
        "genes": ["FADS1","FADS2","ELOVL2"],
        "kegg": "hsa00592",
        "msk_slugs": ["fish-oil","flaxseed"],
        "drugs": ["warfarina","aspirina","anticoagulantes"],
        "pubmed_terms": "omega-3 fish oil cardiovascular supplement clinical evidence",
    },
}

# Mapa de slugs MSK
MSK_SLUGS = {
    "omega-3": "fish-oil", "omega 3": "fish-oil", "fish-oil": "fish-oil",
    "vitamin-d": "vitamin-d", "vitamina d": "vitamin-d", "vit d": "vitamin-d",
    "chromium": "chromium", "cromo": "chromium",
    "berberine": "berberine", "berberina": "berberine",
    "green-tea": "green-tea", "te verde": "green-tea", "green tea": "green-tea",
    "cinnamon": "cinnamon", "canela": "cinnamon",
    "magnesium": "magnesium", "magnesio": "magnesium",
    "l-carnitine": "l-carnitine", "carnitina": "l-carnitine",
    "probiotics": "probiotics", "probioticos": "probiotics",
    "folic-acid": "folic-acid", "folato": "folic-acid", "acido folico": "folic-acid",
    "vitamin-b12": "vitamin-b12", "b12": "vitamin-b12", "cobalamina": "vitamin-b12",
    "zinc": "zinc",
    "selenium": "selenium", "selenio": "selenium",
    "turmeric": "turmeric", "curcuma": "turmeric", "curcumin": "turmeric",
    "resveratrol": "resveratrol",
    "garlic": "garlic", "ajo": "garlic",
    "flaxseed": "flaxseed", "linaza": "flaxseed",
    "quercetin": "quercetin", "quercetina": "quercetin",
    "aloe-vera": "aloe-vera", "aloe vera": "aloe-vera",
    "ginger": "ginger", "jengibre": "ginger",
    "vitamin-c": "vitamin-c", "vitamina c": "vitamin-c",
    "vitamin-e": "vitamin-e", "vitamina e": "vitamin-e",
    "melatonin": "melatonin", "melatonina": "melatonin",
    "milk-thistle": "milk-thistle", "cardo mariano": "milk-thistle", "silimarina": "milk-thistle",
    "echinacea": "echinacea", "equinacea": "echinacea",
    "ginseng": "ginseng",
    "ashwagandha": "ashwagandha",
    "coenzyme-q10": "coenzyme-q10", "coq10": "coenzyme-q10", "ubiquinol": "coenzyme-q10",
    "fish oil": "fish-oil",
    "red-yeast-rice": "red-yeast-rice", "arroz levadura roja": "red-yeast-rice",
    "alpha-lipoic-acid": "alpha-lipoic-acid", "acido lipoico": "alpha-lipoic-acid",
    "fenugreek": "fenugreek", "fenogreco": "fenugreek",
    "artichoke": "artichoke", "alcachofa": "artichoke",
    "dandelion": "dandelion", "diente de leon": "dandelion",
    "boswellia": "boswellia",
    "glucomannan": "glucomannan",
    "conjugated-linoleic-acid": "conjugated-linoleic-acid", "cla": "conjugated-linoleic-acid",
    "garcinia": "garcinia",
    "gymnema": "gymnema",
    "bitter-melon": "bitter-melon", "amargoso": "bitter-melon",
    "hawthorn": "hawthorn", "espino blanco": "hawthorn",
    "hibiscus": "hibiscus", "jamaica": "hibiscus",
    "vitamin-b6": "vitamin-b6", "piridoxina": "vitamin-b6",
    "niacin": "niacin", "niacina": "niacin",
    "calcium": "calcium", "calcio": "calcium",
    "iron": "iron", "hierro": "iron",
    "glutamine": "glutamine", "glutamina": "glutamine",
    "omega-3-fatty-acids": "fish-oil",
    "prebiotics": "probiotics",
    "pyruvate": "pyruvate",
    "chitosan": "chitosan",
}

# ── SQLITE CACHE ──────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS herb_cache (
        slug TEXT PRIMARY KEY, name TEXT, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS gene_cache (
        gene_id TEXT PRIMARY KEY, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS query_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT, query_type TEXT, timestamp TEXT)""")
    conn.commit(); conn.close()

def cache_get_herb(slug):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT data FROM herb_cache WHERE slug=?", (slug,))
    row = c.fetchone(); conn.close()
    return json.loads(row[0]) if row else None

def cache_set_herb(slug, name, data):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO herb_cache VALUES (?,?,?,?)",
              (slug, name, json.dumps(data, ensure_ascii=False), datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()

def cache_get_gene(gene_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT data FROM gene_cache WHERE gene_id=?", (gene_id.upper(),))
    row = c.fetchone(); conn.close()
    return json.loads(row[0]) if row else None

def cache_set_gene(gene_id, data):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO gene_cache VALUES (?,?,?)",
              (gene_id.upper(), json.dumps(data, ensure_ascii=False), datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()

def log_query(query, qtype):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO query_log (query,query_type,timestamp) VALUES (?,?,?)",
              (query, qtype, datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()

# ── MSK SCRAPER ───────────────────────────────────────────────────────────────
async def fetch_msk_herb(slug: str, client: httpx.AsyncClient) -> dict:
    """Fetch herb from MSK in real time. Cache on first fetch."""
    cached = cache_get_herb(slug)
    if cached:
        logger.info(f"💾 Cache hit MSK: {slug}")
        return cached

    url = f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}"
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        if r.status_code != 200 or "Page Not Found" in r.text:
            return {"error": f"No encontrado: {slug}", "slug": slug}

        text = r.text
        soup = BeautifulSoup(text, "html.parser")
        content = soup.get_text(separator="\n")

        herb = {
            "name": slug.replace("-", " ").title(),
            "slug": slug,
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
            "purported_uses": [],
            "contraindications": "",
        }

        # Scientific name
        m = re.search(r'Scientific Name\s*\n+([^\n]{3,120})', content)
        if m: herb["scientific_name"] = m.group(1).strip()

        # Common names (patient section)
        m = re.search(r'## Common Names\s*\n(.*?)(?=\nJump to|\n##)', content, re.DOTALL)
        if m:
            herb["common_names"] = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 2][:6]

        # What is it (patient)
        m = re.search(r'What is it\?\s*\n+(.*?)(?=What are the potential|What are the side)', content, re.DOTALL)
        if m: herb["what_is_it"] = m.group(1).strip()[:700]

        # Benefits (patient)
        m = re.search(r'What are the potential uses and benefits\?\s*\n+(.*?)(?=What are the side effects)', content, re.DOTALL)
        if m:
            lines = [l.strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 5]
            herb["benefits"] = lines[:12]

        # Side effects (patient)
        m = re.search(r'What are the side effects\?\s*\n+(.*?)(?=What else do I need)', content, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 5]
            herb["side_effects"] = [l for l in lines if len(l) > 8][:15]

        # Warnings / what else (patient)
        m = re.search(r'What else do I need to know\?\s*\n+(.*?)(?=For Healthcare|##)', content, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip() and len(l.strip()) > 10]
            herb["warnings"] = lines[:10]

        # Clinical summary (HCP)
        m = re.search(r'Clinical Summary\s*\n+(.*?)(?=Food Sources|Purported Uses|Mechanism of Action|Pharmacology|Adverse)', content, re.DOTALL)
        if m: herb["clinical_summary"] = m.group(1).strip()[:2000]

        # Purported uses (HCP)
        m = re.search(r'Purported Uses and Benefits\s*\n+(.*?)(?=Food Sources|Mechanism|Pharmacology)', content, re.DOTALL)
        if m:
            lines = [l.strip('- •').strip() for l in m.group(1).split('\n') if l.strip()]
            herb["purported_uses"] = [l for l in lines if len(l) > 3][:15]

        # Mechanism of action (HCP)
        m = re.search(r'Mechanism of Action\s*\n+(.*?)(?=Pharmacology|Adverse Reactions|Herb-Drug|Dosage|References)', content, re.DOTALL)
        if m: herb["mechanism_of_action"] = m.group(1).strip()[:1500]

        # Adverse reactions (HCP)
        m = re.search(r'Adverse Reactions\s*\n+(.*?)(?=Herb-Drug|Dosage|References)', content, re.DOTALL)
        if m: herb["adverse_reactions"] = m.group(1).strip()[:1000]

        # Drug interactions — FULL DETAIL (HCP) — most important section
        m = re.search(r'Herb-Drug Interactions\s*\n+(.*?)(?=Dosage|References|##)', content, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            herb["drug_interactions_raw"] = raw[:3000]  # Store full text
            # Parse individual interactions
            interactions = []
            for line in raw.split('\n'):
                line = line.strip('- •').strip()
                if len(line) > 15:
                    interactions.append(line)
            herb["drug_interactions"] = interactions[:20]

        # Contraindications
        m = re.search(r'Contraindications\s*\n+(.*?)(?=Adverse|References|##)', content, re.DOTALL)
        if m: herb["contraindications"] = m.group(1).strip()[:500]

        cache_set_herb(slug, herb["name"], herb)
        logger.info(f"✅ MSK fetched & cached: {slug}")
        return herb

    except Exception as e:
        logger.error(f"Error MSK {slug}: {e}")
        return {"error": str(e), "slug": slug}


# ── NCBI GENE FETCH ───────────────────────────────────────────────────────────
async def fetch_ncbi_gene(gene_symbol: str, client: httpx.AsyncClient) -> dict:
    cached = cache_get_gene(gene_symbol)
    if cached: return cached
    try:
        r = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"gene","term":f"{gene_symbol}[Gene Name] AND Homo sapiens[Organism]","retmode":"json","retmax":1},
            timeout=10.0)
        ids = r.json().get("esearchresult",{}).get("idlist",[])
        if not ids: return {"symbol":gene_symbol,"error":"No encontrado"}
        gene_id = ids[0]
        r2 = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db":"gene","id":gene_id,"retmode":"json"}, timeout=10.0)
        doc = r2.json().get("result",{}).get(gene_id,{})
        data = {
            "symbol": gene_symbol.upper(), "gene_id": gene_id,
            "name": doc.get("description",""), "full_name": doc.get("otheraliases",""),
            "chromosome": doc.get("chromosome",""), "location": doc.get("maplocation",""),
            "summary": doc.get("summary","")[:1000], "organism": "Homo sapiens",
            "ncbi_url": f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}"
        }
        cache_set_gene(gene_symbol, data)
        return data
    except Exception as e:
        return {"symbol": gene_symbol, "error": str(e)}


# ── KEGG PATHWAY ──────────────────────────────────────────────────────────────
async def fetch_kegg_pathway(pathway_id: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"https://rest.kegg.jp/get/{pathway_id}", timeout=10.0)
        text = r.text
        pathway = {"id": pathway_id, "name":"","description":"","genes":[],"kegg_url":f"https://www.kegg.jp/pathway/{pathway_id}"}
        m = re.search(r'NAME\s+(.+)', text)
        if m: pathway["name"] = m.group(1).strip()
        m = re.search(r'DESCRIPTION\s+(.*?)(?=\nCLASS|\nPATHWAY|\nKEGG)', text, re.DOTALL)
        if m: pathway["description"] = m.group(1).strip()[:500]
        m = re.search(r'GENE\s+(.*?)(?=\nCOMPOUND|\nREFERENCE|\nORG)', text, re.DOTALL)
        if m:
            for line in m.group(1).strip().split('\n')[:20]:
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    pathway["genes"].append({"id":parts[0],"symbol":parts[1].rstrip(';')})
        return pathway
    except Exception as e:
        return {"id": pathway_id, "error": str(e)}


# ── PUBMED SEARCH ─────────────────────────────────────────────────────────────
async def search_pubmed(query: str, client: httpx.AsyncClient, max_results: int = 6) -> list:
    try:
        r = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":query,"retmode":"json","retmax":max_results,"sort":"relevance"},
            timeout=10.0)
        ids = r.json().get("esearchresult",{}).get("idlist",[])
        if not ids: return []
        r2 = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db":"pubmed","id":",".join(ids),"retmode":"json"}, timeout=10.0)
        result = r2.json().get("result",{})
        refs = []
        for pmid in ids:
            art = result.get(pmid,{})
            authors = art.get("authors",[])
            author_str = authors[0].get("name","")+" et al." if authors else ""
            refs.append({"pmid":pmid,"title":art.get("title",""),"authors":author_str,
                         "journal":art.get("fulljournalname",""),"year":art.get("pubdate","")[:4],
                         "url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
        return refs
    except Exception as e:
        logger.warning(f"PubMed error: {e}"); return []


# ── DRUG INTERACTION ANALYSIS ─────────────────────────────────────────────────
def analyze_drug_interactions(herbs_data: list, drugs: list) -> list:
    """Cross-reference drugs mentioned by user with herb interaction data."""
    drug_alerts = []
    for herb in herbs_data:
        if not herb or "error" in herb: continue
        interactions_raw = herb.get("drug_interactions_raw", "") + " ".join(herb.get("drug_interactions", []))
        for drug in drugs:
            drug_lower = drug.lower()
            if drug_lower in interactions_raw.lower():
                # Find the relevant sentence
                for line in herb.get("drug_interactions", []):
                    if drug_lower in line.lower():
                        drug_alerts.append({
                            "drug": drug,
                            "herb": herb.get("name", herb.get("slug","")),
                            "interaction": line,
                            "source": herb.get("url",""),
                            "severity": "⚠ Revisar" if any(w in line.lower() for w in ["caution","avoid","increase","decrease","toxic","inhibit"]) else "ℹ Monitorear"
                        })
    return drug_alerts


# ── MODELS ────────────────────────────────────────────────────────────────────
class ClinicalQuery(BaseModel):
    query: str
    drugs_used: Optional[List[str]] = []  # fármacos que el paciente usa

class GeneQuery(BaseModel):
    genes: List[str]

class NutrientQuery(BaseModel):
    nutrient: str


# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="NutriKen", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    init_db()
    logger.info("🌿 NutriKen iniciado")

@app.get("/")
async def root(): return FileResponse("static/index.html")

@app.get("/script.js")
async def get_script(): return FileResponse("static/script.js")

@app.get("/style.css")
async def get_style(): return FileResponse("static/style.css")

@app.get("/health")
async def health(): return {"status": "ok", "version": "NutriKen 1.0"}


# ── ENDPOINT 1: CLÍNICO ───────────────────────────────────────────────────────
@app.post("/api/clinical")
async def clinical_analysis(req: ClinicalQuery):
    q = req.query.lower().strip()
    log_query(req.query, "clinical")

    # Match condition
    matched_key = None
    matched_data = None
    for key, data in CLINICAL_MAP.items():
        if key in q or any(w in q for w in key.split() if len(w) > 3):
            matched_key = key; matched_data = data; break

    if not matched_data:
        raise HTTPException(status_code=404,
            detail=f"Condición '{req.query}' no reconocida. Prueba: obesidad, diabetes, colesterol, intolerancia lactosa, déficit vitamina D, atorvastatina, silimarina, inflamación, microbiota.")

    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/1.0 (educational)"}) as client:

        # 1. Fetch genes from NCBI
        genes_tasks = [fetch_ncbi_gene(g, client) for g in matched_data["genes"][:5]]
        genes_info = await asyncio.gather(*genes_tasks)

        # 2. KEGG pathway
        pathway = await fetch_kegg_pathway(matched_data["kegg"], client)

        # 3. Fetch ALL relevant MSK herbs in parallel (real data, cached after first fetch)
        slugs = matched_data["msk_slugs"][:10]
        herb_tasks = [fetch_msk_herb(slug, client) for slug in slugs]
        herbs_raw = await asyncio.gather(*herb_tasks)
        herbs = [h for h in herbs_raw if "error" not in h]

        # 4. Drug interactions analysis (if drugs provided or from condition map)
        all_drugs = list(set((req.drugs_used or []) + matched_data.get("drugs", [])))
        drug_alerts = analyze_drug_interactions(herbs, all_drugs)

        # 5. PubMed references
        refs = await search_pubmed(matched_data["pubmed_terms"], client, max_results=6)

    # Build risks from REAL herb data + drug alerts
    risks = []
    for h in herbs[:6]:
        for w in h.get("warnings", [])[:2]:
            if w and len(w) > 15:
                risks.append(f"{h.get('name','')}: {w}")
    for w in h.get("side_effects", [])[:1] if herbs else []:
        if w: risks.append(w)

    return {
        "query": req.query,
        "condition": matched_key.title(),
        "description": _condition_description(matched_key),
        "genes": [g for g in genes_info if "error" not in g],
        "pathway": pathway,
        "supplements": herbs,
        "drug_alerts": drug_alerts,
        "drugs_related": matched_data.get("drugs", []),
        "risks": risks[:8],
        "references": refs,
        "msk_sources": [f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{s}" for s in slugs[:6]],
        "timestamp": datetime.datetime.now().isoformat()
    }


def _condition_description(key):
    descs = {
        "obesidad": "La obesidad involucra alteraciones en genes reguladores del apetito (LEP, FTO, MC4R) y metabolismo energético. Los suplementos con mayor evidencia incluyen té verde, berberina y cromo. El uso de fármacos como orlistat o semaglutide puede interactuar con suplementos herbales.",
        "perdida de peso": "La regulación del peso corporal depende de señales hormonales moduladas por variantes genéticas. La pérdida rápida de peso (>1.5 kg/semana) aumenta el riesgo de cálculos biliares, déficit de micronutrientes y sarcopenia.",
        "colesterol": "El metabolismo lipídico está regulado por APOE y LDLR. Las estatinas (atorvastatina, rosuvastatina) pueden interactuar con suplementos como CoQ10, arroz de levadura roja y silimarina. El CoQ10 es recomendado como coadyuvante en terapia con estatinas.",
        "atorvastatina": "La atorvastatina es una estatina que puede agotar CoQ10 y causar miopatía. La silimarina (cardo mariano) tiene efecto hepatoprotector y puede interactuar con el metabolismo de estatinas vía CYP3A4.",
        "silimarina": "La silimarina actúa sobre CYP3A4 y puede modificar el metabolismo de múltiples fármacos incluyendo estatinas, anticoagulantes y ciclosporina. Tiene efecto hepatoprotector documentado.",
        "diabetes": "La diabetes tipo 2 involucra resistencia insulínica. Berberina, canela y cromo tienen evidencia en control glucémico. Pueden potenciar el efecto hipoglucemiante de metformina — monitoreo necesario.",
        "microbiota": "La composición de la microbiota depende de variantes genéticas del huésped. Los probióticos tienen evidencia sólida. En inmunosuprimidos pueden causar infecciones — usar con precaución.",
        "inflamacion": "La inflamación crónica involucra TNF-α e IL-6. Cúrcuma (curcumina), omega-3 y quercetina tienen evidencia antiinflamatoria. Pueden interactuar con AINEs y anticoagulantes.",
        "higado": "La salud hepática se ve afectada por PNPLA3 y otros genes. El cardo mariano (silimarina) es el hepatoprotector con mayor evidencia en MSK.",
        "hipertension": "El ajo, CoQ10 y magnesio tienen evidencia en reducción de presión arterial. Pueden interactuar con antihipertensivos — monitoreo necesario.",
        "deficit vitamina d": "El déficit de vitamina D es modulado por el receptor VDR. La suplementación es segura en dosis de 600-2000 UI/día. Dosis altas (>4000 UI) pueden causar hipercalcemia.",
        "deficit folato": "La variante MTHFR C677T reduce la actividad enzimática hasta 70%. El metilfolato (5-MTHF) es más eficiente que el ácido fólico en portadores de esta variante.",
        "deficit b12": "El déficit prolongado puede causar neuropatía irreversible. La cianocobalamina y metilcobalamina son las formas suplementarias más usadas.",
        "intolerancia lactosa": "La variante LCT-13910 T/T determina la persistencia de lactasa. Los probióticos mejoran la digestión de lactosa y previenen la disbiosis.",
        "enfermedad celiaca": "La malabsorción crónica causa déficits múltiples. La suplementación con vitamina D, folato, B12 y zinc es fundamental en celíacos.",
        "omega 3": "Los omega-3 (EPA/DHA) tienen evidencia cardiovascular. Pueden aumentar el riesgo de sangrado en combinación con anticoagulantes (warfarina, aspirina).",
    }
    return descs.get(key, f"Análisis clínico basado en evidencia MSK para: {key}")


# ── ENDPOINT 2: GEN ───────────────────────────────────────────────────────────
@app.post("/api/gene")
async def gene_analysis(req: GeneQuery):
    genes = [g.upper().strip() for g in req.genes[:6]]
    log_query(",".join(genes), "gene")

    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/1.0"}) as client:
        genes_info = await asyncio.gather(*[fetch_ncbi_gene(g, client) for g in genes])

        # Find related conditions
        related = []
        for key, data in CLINICAL_MAP.items():
            overlap = [g for g in genes if g in data["genes"]]
            if overlap:
                related.append({"condition": key.title(), "matching_genes": overlap,
                                 "nutrients": data["msk_slugs"][:4], "drugs": data.get("drugs",[]),
                                 "risks": []})

        # Fetch relevant supplements
        all_slugs = list(set(s for r in related for s in r["nutrients"][:3]))[:6]
        herbs = await asyncio.gather(*[fetch_msk_herb(slug, client) for slug in all_slugs])
        herbs = [h for h in herbs if "error" not in h]

        refs = await search_pubmed(f"{' '.join(genes[:3])} nutrition SNP nutrigenomics", client, max_results=5)

    return {
        "genes_queried": genes,
        "genes_info": [g for g in genes_info if "error" not in g],
        "related_conditions": related,
        "supplements": herbs,
        "references": refs,
        "snpedia_urls": {g: f"https://www.snpedia.com/index.php/{g}" for g in genes},
        "ensembl_urls": {g: f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?q={g}" for g in genes},
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT 3: SUPLEMENTO ────────────────────────────────────────────────────
@app.post("/api/nutrient")
async def nutrient_analysis(req: NutrientQuery):
    nut = req.nutrient.lower().strip()
    log_query(req.nutrient, "nutrient")
    slug = MSK_SLUGS.get(nut, nut.replace(" ","-"))

    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/1.0"}) as client:
        herb = await fetch_msk_herb(slug, client)
        if "error" in herb:
            raise HTTPException(status_code=404,
                detail=f"'{req.nutrient}' no encontrado en MSK. Slug intentado: {slug}. Prueba nombres en inglés: omega-3, vitamin-d, berberine, turmeric, milk-thistle, coenzyme-q10")

        # KEGG search
        pathway = {}
        try:
            r = await client.get(f"https://rest.kegg.jp/find/compound/{slug.replace('-','+')}", timeout=8.0)
            lines = r.text.strip().split('\n')
            if lines and lines[0] and '\t' in lines[0]:
                parts = lines[0].split('\t')
                cid = parts[0].replace("cpd:","")
                pathway = {"id": cid, "name": parts[1] if len(parts)>1 else slug,
                           "kegg_url": f"https://www.kegg.jp/entry/{cid}"}
        except: pass

        refs = await search_pubmed(f"{req.nutrient} clinical evidence safety efficacy", client, max_results=6)

    return {
        "nutrient": req.nutrient, "slug": slug,
        "msk_data": herb, "pathway": pathway, "references": refs,
        "msk_url": f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}",
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT: STATS ───────────────────────────────────────────────────────────
@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM herb_cache"); herbs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gene_cache"); genes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM query_log"); total = c.fetchone()[0]
    c.execute("SELECT query, query_type, timestamp FROM query_log ORDER BY id DESC LIMIT 8")
    recent = c.fetchall(); conn.close()
    return {"herbs_in_cache": herbs, "genes_in_cache": genes, "total_queries": total,
            "recent_queries": [{"query":r[0],"type":r[1],"time":r[2]} for r in recent]}


if __name__ == "__main__":
    uvicorn.run("nutriken_engine:app", host="0.0.0.0", port=7860, reload=False)

