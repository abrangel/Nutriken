"""
Enriquecimiento científico de la base de dosis (JOSS-compatible, fuentes ABIERTAS).
Para cada suplemento/hierba añade, desde fuentes redistribuibles:
  - pubchem_cid + inchikey  (PubChem, dominio público)
  - pubmed_pmids            (PubMed/NCBI, público) — provenance de dosificación
  - reference               (cita formateada de la mejor evidencia)
NO usa DrugBank (licencia no redistribuible). Ejecutar:
  python scripts/enrich_evidence.py            # todos
  python scripts/enrich_evidence.py 20         # primeros 20 (prueba)
Respeta el rate-limit de NCBI (backoff 429 + espaciado; usa NCBI_API_KEY si existe).
"""
import os, sys, json, time, threading
import requests

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
API_KEY = os.getenv("NCBI_API_KEY", "")
_MIN = 0.11 if API_KEY else 0.34
_last = [0.0]
_lock = threading.Lock()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "local_db", "supplement_dosing.json")

# Término de búsqueda en INGLÉS por slug (los nombres visibles están en español).
ABBREV = {
    "vitc": "vitamin C ascorbic acid", "vitd": "vitamin D cholecalciferol", "vita": "vitamin A retinol",
    "vite": "vitamin E tocopherol", "vitk1": "vitamin K1 phylloquinone", "k2": "vitamin K2 menaquinone MK-7",
    "b12": "vitamin B12 cobalamin", "b1": "thiamine", "b2": "riboflavin", "b3": "niacin nicotinic acid",
    "b6": "pyridoxine vitamin B6", "biotin": "biotin", "folate": "folate folic acid",
    "ala": "alpha-lipoic acid", "tmg": "betaine trimethylglycine", "ps": "phosphatidylserine",
    "nr": "nicotinamide riboside", "nmn": "nicotinamide mononucleotide", "mct": "medium chain triglycerides",
    "cla": "conjugated linoleic acid", "dim": "diindolylmethane", "hmb": "beta-hydroxy-beta-methylbutyrate",
    "bcaa": "branched chain amino acids", "egcg": "epigallocatechin gallate", "coq10": "coenzyme Q10 ubiquinol",
    "5htp": "5-hydroxytryptophan", "same": "S-adenosylmethionine SAMe", "pqq": "pyrroloquinoline quinone",
    "dmannose": "D-mannose", "ltheanine": "L-theanine", "nac": "N-acetylcysteine",
    "iodine": "iodine", "iron": "iron ferrous", "zinc": "zinc", "calcium": "calcium",
    "magnesium": "magnesium", "chromium": "chromium picolinate", "selenium": "selenium",
    "copper": "copper", "manganese": "manganese", "boron": "boron", "potassium": "potassium",
    "omega3": "omega-3 fatty acids EPA DHA", "berberine": "berberine", "curcumin": "curcumin turmeric",
    "creatine": "creatine monohydrate", "melatonin": "melatonin", "quercetin": "quercetin",
    "resveratrol": "resveratrol", "milkthistle": "silymarin milk thistle", "sawpalmetto": "saw palmetto",
    "ginkgo": "ginkgo biloba", "ginseng": "panax ginseng", "garlic": "garlic allium sativum",
    "cinnamon": "cinnamon cinnamomum", "inositol": "myo-inositol", "taurine": "taurine",
    "glycine": "glycine", "collagen": "collagen peptides", "glucosamine": "glucosamine sulfate",
    "psyllium": "psyllium", "probiotics": "probiotics", "ashwagandha": "ashwagandha withania somnifera",
    "rhodiola": "rhodiola rosea", "lysine": "L-lysine", "glutamine": "L-glutamine", "caffeine": "caffeine",
    "mucuna": "mucuna pruriens", "tulsi": "holy basil ocimum sanctum", "schisandra": "schisandra chinensis",
    "eleuthero": "eleutherococcus senticosus", "astragalus": "astragalus membranaceus",
    "andrographis": "andrographis paniculata", "glutathione": "glutathione", "tudca": "tauroursodeoxycholic acid",
    "artichoke": "artichoke cynara", "red_yeast_rice": "red yeast rice monacolin", "plant_sterols": "phytosterols",
    "bergamot": "bergamot citrus bergamia", "chondroitin": "chondroitin sulfate", "hyaluronic": "hyaluronic acid",
    "glucomannan": "glucomannan konjac", "capsaicin": "capsaicin", "gotu_kola": "centella asiatica gotu kola",
    "sulforaphane": "sulforaphane", "policosanol": "policosanol", "apigenin": "apigenin",
    "lions_mane": "hericium erinaceus lions mane", "cordyceps": "cordyceps", "spirulina": "spirulina",
    "boswellia": "boswellia serrata", "msm": "methylsulfonylmethane MSM", "lutein": "lutein zeaxanthin",
    "astaxanthin": "astaxanthin", "beta_alanine": "beta-alanine", "citrulline": "L-citrulline",
    "carnitine": "L-carnitine", "tyrosine": "L-tyrosine", "bacopa": "bacopa monnieri",
    "chromium": "chromium picolinate", "nitrate": "dietary nitrate beetroot", "fenugreek": "fenugreek trigonella",
    "maca": "maca lepidium meyenii", "saffron": "saffron crocus sativus", "cranberry": "cranberry proanthocyanidin",
    "elderberry": "elderberry sambucus", "echinacea": "echinacea", "valerian": "valerian valeriana",
    "lemon_balm": "lemon balm melissa officinalis", "genistein": "genistein", "vitc2": "vitamin C",
}

def qname(it):
    return ABBREV.get(it.get("slug", ""), (it.get("slug", "") or it.get("name", "")).replace("_", " "))


def _throttle():
    with _lock:
        gap = time.time() - _last[0]
        if gap < _MIN:
            time.sleep(_MIN - gap)
        _last[0] = time.time()


def _get(url, params, tries=4, timeout=20):
    if API_KEY:
        params = {**params, "api_key": API_KEY}
    delay = 0.6
    for _ in range(tries):
        _throttle()
        try:
            r = requests.get(url, params=params, timeout=timeout)
        except Exception:
            time.sleep(delay); delay *= 2; continue
        if r.status_code == 429:
            time.sleep(delay); delay *= 2; continue
        if r.status_code == 200:
            return r
        return None
    return None


def pubchem_ids(name):
    r = _get(f"{PUBCHEM}/compound/name/{requests.utils.quote(name)}/property/InChIKey/JSON", {})
    if not r:
        return None, None
    try:
        p = r.json()["PropertyTable"]["Properties"][0]
        return p.get("CID"), p.get("InChIKey")
    except Exception:
        return None, None


def pubmed_pmids(name, n=5):
    term = f'{name} AND (dose OR dosage OR supplementation) AND (randomized OR "clinical trial" OR meta-analysis)'
    r = _get(f"{EUTILS}/esearch.fcgi",
             {"db": "pubmed", "term": term, "retmode": "json", "retmax": n, "sort": "relevance"})
    if not r:
        return []
    try:
        return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


def pubmed_citation(pmid):
    r = _get(f"{EUTILS}/esummary.fcgi", {"db": "pubmed", "id": pmid, "retmode": "json"})
    if not r:
        return None
    try:
        d = r.json()["result"][pmid]
        authors = d.get("authors", [])
        first = authors[0]["name"] if authors else ""
        etal = " et al." if len(authors) > 1 else ""
        return f"{first}{etal} {d.get('title','')} {d.get('source','')} {d.get('pubdate','')[:4]}. PMID {pmid}"
    except Exception:
        return None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    db = json.load(open(DB_PATH, encoding="utf-8"))
    items = db["items"][:limit] if limit else db["items"]
    print(f"Enriqueciendo {len(items)} entradas desde PubChem + PubMed (abiertas)…")
    done = 0
    for it in items:
        name = qname(it)
        cid, inchikey = pubchem_ids(name)
        pmids = pubmed_pmids(name)
        it["pubchem_cid"] = cid
        it["inchikey"] = inchikey
        it["pubmed_pmids"] = pmids
        if pmids:
            cit = pubmed_citation(pmids[0])
            if cit:
                it["reference"] = cit
        done += 1
        if done % 10 == 0:
            print(f"  {done}/{len(items)} … último: {name} (CID={cid}, PMIDs={len(pmids)})")
    db["enriched"] = True
    db["enrichment_sources"] = "PubChem (public domain) + PubMed/NCBI (public)"
    json.dump(db, open(DB_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: {done} entradas enriquecidas -> {DB_PATH}")


if __name__ == "__main__":
    main()
