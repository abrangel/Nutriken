"""
Enriquece las 307 hierbas del catálogo MSK con evidencia ABIERTA (JOSS-compatible):
  - pubmed_pmids (PubMed/NCBI) + reference formateada
  - pubchem_cid + inchikey (PubChem) por nombre científico
Genera local_db/herbs_evidence.json (clave = slug). No usa datos con licencia.
Ejecutar:  python scripts/enrich_herbs.py [limite]
"""
import os, sys, json, time, threading, requests

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
API_KEY = os.getenv("NCBI_API_KEY", "")
_MIN = 0.11 if API_KEY else 0.34
_last = [0.0]; _lock = threading.Lock()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "local_db", "herbs_evidence.json")
IDX = "/tmp/herbs_index.json"


def _thr():
    with _lock:
        g = time.time() - _last[0]
        if g < _MIN: time.sleep(_MIN - g)
        _last[0] = time.time()


def _get(url, params, tries=3, timeout=15):
    if API_KEY: params = {**params, "api_key": API_KEY}
    delay = 0.6
    for _ in range(tries):
        _thr()
        try:
            r = requests.get(url, params=params, timeout=timeout)
        except Exception:
            time.sleep(delay); delay *= 2; continue
        if r.status_code == 429:
            time.sleep(delay); delay *= 2; continue
        if r.status_code == 200: return r
        return None
    return None


def pubchem(name):
    if not name: return None, None
    q = name.split(";")[0].strip()
    r = _get(f"{PUBCHEM}/compound/name/{requests.utils.quote(q)}/property/InChIKey/JSON", {})
    if not r: return None, None
    try:
        p = r.json()["PropertyTable"]["Properties"][0]
        return p.get("CID"), p.get("InChIKey")
    except Exception:
        return None, None


def pubmed(name, n=4):
    term = f'{name} AND (supplement OR dose OR clinical trial OR efficacy)'
    r = _get(f"{EUTILS}/esearch.fcgi",
             {"db": "pubmed", "term": term, "retmode": "json", "retmax": n, "sort": "relevance"})
    if not r: return []
    try: return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception: return []


def cite(pmid):
    r = _get(f"{EUTILS}/esummary.fcgi", {"db": "pubmed", "id": pmid, "retmode": "json"})
    if not r: return None
    try:
        d = r.json()["result"][pmid]; a = d.get("authors", [])
        return f"{a[0]['name'] if a else ''}{' et al.' if len(a)>1 else ''} {d.get('title','')} {d.get('source','')} {d.get('pubdate','')[:4]}. PMID {pmid}"
    except Exception: return None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    idx = json.load(open(IDX, encoding="utf-8"))
    herbs = []
    for arr in idx["by_letter"].values():
        herbs.extend(arr)
    if limit: herbs = herbs[:limit]
    existing = {}
    if os.path.exists(OUT):
        existing = json.load(open(OUT, encoding="utf-8"))
    print(f"Enriqueciendo {len(herbs)} hierbas (PubMed + PubChem)…")
    done = 0
    for h in herbs:
        slug = h["slug"]
        if slug in existing and existing[slug].get("pubmed_pmids"):
            done += 1; continue
        name = h.get("name", slug)
        sci = h.get("scientific_name", "")
        cid, ik = pubchem(sci or name)
        pmids = pubmed(sci.split(";")[0] if sci else name) or pubmed(name)
        rec = {"slug": slug, "name": name, "scientific_name": sci,
               "pubchem_cid": cid, "inchikey": ik, "pubmed_pmids": pmids}
        if pmids:
            c = cite(pmids[0])
            if c: rec["reference"] = c
        existing[slug] = rec
        done += 1
        if done % 25 == 0:
            print(f"  {done}/{len(herbs)} … {name} (CID={cid}, PMIDs={len(pmids)})")
            json.dump(existing, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(existing, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK: {len(existing)} hierbas -> {OUT}")


if __name__ == "__main__":
    main()
