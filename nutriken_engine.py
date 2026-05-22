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
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "local_db" / "nutriken_cache.db"
Path("local_db").mkdir(exist_ok=True)

# Supabase — base de datos persistente con 307+ hierbas en espanol
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ewhcinmihogmusmldeds.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_X7hVXnbUmyJGL0JbO0jpbw_Gw1dznI2")
try:
    from supabase import create_client, Client as _SBClient
    _supabase: Optional[_SBClient] = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info(f"Supabase conectado: {SUPABASE_URL}")
except Exception as e:
    _supabase = None
    logger.warning(f"Supabase no disponible: {e}")

async def supabase_get_herb(slug):
    """Consulta Supabase msk_herbs por slug. Devuelve None si no existe."""
    if not _supabase: return None
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None,
            lambda: _supabase.table("msk_herbs").select("*").eq("slug", slug).execute()
        )
        if res.data and len(res.data) > 0:
            row = res.data[0]
            for f in ("name","scientific_name","what_is_it","clinical_summary",
                      "mechanism_of_action","adverse_reactions","contraindications","dosage","url"):
                if row.get(f) is None: row[f] = ""
            for f in ("common_names","benefits","drug_interactions","food_interactions",
                      "side_effects","warnings"):
                if row.get(f) is None: row[f] = []
            row.setdefault("purported_uses", [])
            row.setdefault("herb_interactions", [])
            row.setdefault("drug_interactions_raw", " ".join(row.get("drug_interactions", [])))
            # Como ya esta en espanol, copiar a campos _es para el frontend
            for fld in ("clinical_summary","mechanism_of_action","what_is_it",
                        "adverse_reactions","contraindications","dosage"):
                row[f"{fld}_es"] = row.get(fld, "")
            for fld in ("benefits","side_effects","warnings","drug_interactions",
                        "food_interactions","purported_uses"):
                row[f"{fld}_es"] = row.get(fld, [])
            if not row.get("url"):
                row["url"] = f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}"
            return row
    except Exception as e:
        logger.warning(f"Supabase get_herb({slug}) fallo: {e}")
    return None

# ── TRADUCCIÓN ES→EN ──────────────────────────────────────────────────────────
ES_EN = {
    "trigliceridos":"triglycerides","triglicéridos":"triglycerides",
    "colesterol":"cholesterol","obesidad":"obesity","diabetes":"diabetes",
    "inflamacion":"inflammation","inflamación":"inflammation",
    "higado":"liver","hígado":"liver","hepatico":"hepatic","hepático":"hepatic",
    "riñon":"kidney","riñón":"kidney","renal":"renal",
    "corazon":"heart","corazón":"heart","cardiovascular":"cardiovascular",
    "presion arterial":"blood pressure","presión arterial":"blood pressure",
    "hipertension":"hypertension","hipertensión":"hypertension",
    "azucar":"blood sugar","azúcar":"blood sugar","glucosa":"glucose",
    "insulina":"insulin","resistencia insulina":"insulin resistance",
    "tiroides":"thyroid","hipotiroidismo":"hypothyroidism","hipertiroidismo":"hyperthyroidism",
    "artritis":"arthritis","reumatoide":"rheumatoid",
    "anemia":"anemia","hierro":"iron","ferritina":"ferritin",
    "vitamina d":"vitamin D","vitamina c":"vitamin C","vitamina e":"vitamin E",
    "vitamina b12":"vitamin B12","vitamina b6":"vitamin B6",
    "acido folico":"folic acid","ácido fólico":"folic acid","folato":"folate",
    "magnesio":"magnesium","calcio":"calcium","zinc":"zinc","selenio":"selenium",
    "omega 3":"omega-3","acidos grasos":"fatty acids","ácidos grasos":"fatty acids",
    "curcuma":"turmeric","cúrcuma":"turmeric","jengibre":"ginger",
    "ajo":"garlic","canela":"cinnamon","te verde":"green tea","té verde":"green tea",
    "cardo mariano":"milk thistle","silimarina":"silymarin",
    "berberina":"berberine","probioticos":"probiotics","probióticos":"probiotics",
    "carnitina":"carnitine","coq10":"coenzyme Q10","ubiquinol":"ubiquinol",
    "melatonina":"melatonin","equinacea":"echinacea","ginseng":"ginseng",
    "acido lipoico":"lipoic acid","ácido lipoico":"lipoic acid",
    "linaza":"flaxseed","alcachofa":"artichoke","diente de leon":"dandelion",
    "fenogreco":"fenugreek","gymnema":"gymnema",
    "atorvastatina":"atorvastatin","rosuvastatina":"rosuvastatin",
    "simvastatina":"simvastatin","estatina":"statin","estatinas":"statins",
    "metformina":"metformin","warfarina":"warfarin","aspirina":"aspirin",
    "ibuprofeno":"ibuprofen","naproxeno":"naproxen","prednisona":"prednisone",
    "perdida de peso":"weight loss","pérdida de peso":"weight loss",
    "intolerancia lactosa":"lactose intolerance",
    "enfermedad celiaca":"celiac disease","celiaca":"celiac",
    "microbiota":"gut microbiota","intestino":"intestine",
    "embarazo":"pregnancy","lactancia":"breastfeeding",
    "menopausia":"menopause","osteoporosis":"osteoporosis",
    "cancer":"cancer","cáncer":"cancer","tumor":"tumor",
    "toronja":"grapefruit","granada":"pomegranate","alcohol":"alcohol",
    "cafeina":"caffeine","cafeína":"caffeine",
    "calculos biliares":"gallstones","cálculos biliares":"gallstones",
    "vesícula":"gallbladder","vesicula":"gallbladder",
    "udca":"ursodeoxycholic acid","acido ursodesoxicolico":"ursodeoxycholic acid",
    "miopatia":"myopathy","miopatía":"myopathy",
}

# MSK slug map — slugs verificados 2026
MSK_SLUGS = {
    "omega-3":"omega-3","omega3":"omega-3","fish oil":"omega-3","fish-oil":"omega-3",
    "aceite de pescado":"omega-3","omega 3":"omega-3","epa":"omega-3","dha":"omega-3",
    "red yeast rice":"red-yeast-rice","red-yeast-rice":"red-yeast-rice","arroz levadura roja":"red-yeast-rice",
    "coenzyme q10":"coenzyme-q10","coenzyme-q10":"coenzyme-q10","coq10":"coenzyme-q10","ubiquinol":"coenzyme-q10","coenzima q10":"coenzyme-q10",
    "berberine":"berberine","berberina":"berberine","berberis":"berberine",
    "garlic":"garlic","ajo":"garlic",
    "flaxseed":"flaxseed","linaza":"flaxseed","lino":"flaxseed",
    "resveratrol":"resveratrol",
    "artichoke":"artichoke","alcachofa":"artichoke",
    "niacin":"niacin","niacina":"niacin","nicotinic acid":"niacin",
    "chromium":"chromium","cromo":"chromium",
    "cinnamon":"cinnamon","canela":"cinnamon",
    "fenugreek":"fenugreek","fenogreco":"fenugreek",
    "bitter melon":"bitter-melon","bitter-melon":"bitter-melon","amargoso":"bitter-melon","momordica":"bitter-melon",
    "gymnema":"gymnema","gymnema sylvestre":"gymnema",
    "alpha lipoic acid":"alpha-lipoic-acid","alpha-lipoic-acid":"alpha-lipoic-acid","acido lipoico":"alpha-lipoic-acid","lipoic acid":"alpha-lipoic-acid",
    "milk thistle":"milk-thistle","milk-thistle":"milk-thistle","cardo mariano":"milk-thistle","silimarina":"milk-thistle","silymarin":"milk-thistle",
    "dandelion":"dandelion","diente de leon":"dandelion","taraxacum":"dandelion",
    "vitamin d":"vitamin-d","vitamin-d":"vitamin-d","vitamina d":"vitamin-d","colecalciferol":"vitamin-d","vit d":"vitamin-d",
    "vitamin c":"vitamin-c","vitamin-c":"vitamin-c","vitamina c":"vitamin-c","ascorbic acid":"vitamin-c",
    "vitamin e":"vitamin-e","vitamin-e":"vitamin-e","vitamina e":"vitamin-e","tocopherol":"vitamin-e",
    "vitamin b12":"vitamin-b12","vitamin-b12":"vitamin-b12","b12":"vitamin-b12","cobalamina":"vitamin-b12","cianocobalamina":"vitamin-b12",
    "vitamin b6":"vitamin-b6","vitamin-b6":"vitamin-b6","piridoxina":"vitamin-b6","b6":"vitamin-b6",
    "folic acid":"folate","folic-acid":"folate","folato":"folate","folate":"folate","acido folico":"folate","methylfolate":"folate","metilfolato":"folate",
    "magnesium":"magnesium","magnesio":"magnesium",
    "zinc":"zinc","cinc":"zinc",
    "selenium":"selenium","selenio":"selenium",
    "calcium":"calcium","calcio":"calcium",
    "iron":"iron","hierro":"iron",
    "ashwagandha":"ashwagandha","withania":"ashwagandha",
    "rhodiola":"rhodiola","rhodiola rosea":"rhodiola",
    "valerian":"valerian","valeriana":"valerian",
    "kava":"kava","kava kava":"kava",
    "melatonin":"melatonin","melatonina":"melatonin",
    "turmeric":"turmeric","curcuma":"turmeric","curcumin":"turmeric","curcumina":"turmeric","cúrcuma":"turmeric",
    "ginger":"ginger","jengibre":"ginger",
    "boswellia":"boswellia","incienso":"boswellia","frankincense":"boswellia",
    "quercetin":"quercetin","quercetina":"quercetin",
    "echinacea":"echinacea","equinacea":"echinacea",
    "ginseng":"ginseng","panax ginseng":"ginseng","panax":"ginseng",
    "green tea":"green-tea","green-tea":"green-tea","te verde":"green-tea","té verde":"green-tea","egcg":"green-tea",
    "aloe vera":"aloe-vera","aloe-vera":"aloe-vera","sabila":"aloe-vera","aloe":"aloe-vera",
    "probiotics":"probiotics","probioticos":"probiotics","lactobacillus":"probiotics","bifidobacterium":"probiotics",
    "l-carnitine":"l-carnitine","carnitina":"l-carnitine","carnitine":"l-carnitine",
    "5-htp":"5-htp-01","5htp":"5-htp-01","serotonina":"5-htp-01",
    "glucosamine":"glucosamine","glucosamina":"glucosamine",
    "dhea":"dhea",
    "saw palmetto":"saw-palmetto","palmito":"saw-palmetto",
    "black cohosh":"black-cohosh","cohosh negro":"black-cohosh",
    "evening primrose":"evening-primrose-oil","onagra":"evening-primrose-oil",
    "ginkgo":"ginkgo","ginkgo biloba":"ginkgo",
    "st johns wort":"st-johns-wort","hypericum":"st-johns-wort","hierba san juan":"st-johns-wort","hipérico":"st-johns-wort",
    "glucomannan":"glucomannan","konjac":"glucomannan",
    "conjugated linoleic acid":"conjugated-linoleic-acid","cla":"conjugated-linoleic-acid",
    "garcinia":"garcinia","garcinia cambogia":"garcinia",
    "acai":"acai-berry","acai berry":"acai-berry","acai-berry":"acai-berry",
    "spirulina":"spirulina","espirulina":"spirulina",
    "chlorella":"chlorella","clorela":"chlorella",
    "astragalus":"astragalus","astragalo":"astragalus",
    "chondroitin":"chondroitin","condroitina":"chondroitin",
    "prebiotics":"probiotics","prebioticos":"probiotics",
    "ahcc":"ahcc","agaricus":"agaricus",
}

GENE_DB = {
    'ABCB1': {
        "symbol": 'ABCB1',
        "gene_id": '5243',
        "ensembl_id": 'ENSG00000085563',
        "pharmgkb_id": 'PA267',
        "name": 'ATP binding cassette subfamily B member 1',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'ATP binding cassette subfamily B member 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5243',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000085563',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA267',
        "snpedia_url": 'https://www.snpedia.com/index.php/ABCB1',
        "omim_url": 'https://omim.org/search?index=entry&search=ABCB1'
    },
    'ABCG5': {
        "symbol": 'ABCG5',
        "gene_id": '64240',
        "ensembl_id": 'ENSG00000138075',
        "pharmgkb_id": 'PA24411',
        "name": 'ATP binding cassette subfamily G member 5',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'ATP binding cassette subfamily G member 5. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/64240',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000138075',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA24411',
        "snpedia_url": 'https://www.snpedia.com/index.php/ABCG5',
        "omim_url": 'https://omim.org/search?index=entry&search=ABCG5'
    },
    'ABCG8': {
        "symbol": 'ABCG8',
        "gene_id": '64241',
        "ensembl_id": 'ENSG00000143921',
        "pharmgkb_id": 'PA24412',
        "name": 'ATP binding cassette subfamily G member 8',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'ATP binding cassette subfamily G member 8. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/64241',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000143921',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA24412',
        "snpedia_url": 'https://www.snpedia.com/index.php/ABCG8',
        "omim_url": 'https://omim.org/search?index=entry&search=ABCG8'
    },
    'ACE': {
        "symbol": 'ACE',
        "gene_id": '1636',
        "ensembl_id": 'ENSG00000159640',
        "pharmgkb_id": 'PA139',
        "name": 'angiotensin I converting enzyme',
        "chromosome": '17',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'angiotensin I converting enzyme. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1636',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000159640',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA139',
        "snpedia_url": 'https://www.snpedia.com/index.php/ACE',
        "omim_url": 'https://omim.org/search?index=entry&search=ACE'
    },
    'ADD1': {
        "symbol": 'ADD1',
        "gene_id": '118',
        "ensembl_id": 'ENSG00000087274',
        "pharmgkb_id": 'PA31',
        "name": 'adducin 1',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'adducin 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/118',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000087274',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA31',
        "snpedia_url": 'https://www.snpedia.com/index.php/ADD1',
        "omim_url": 'https://omim.org/search?index=entry&search=ADD1'
    },
    'ADIPOQ': {
        "symbol": 'ADIPOQ',
        "gene_id": '9370',
        "ensembl_id": 'ENSG00000181092',
        "pharmgkb_id": 'PA134933118',
        "name": 'adiponectin, C1Q and collagen domain containing',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'adiponectin, C1Q and collagen domain containing. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/9370',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000181092',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134933118',
        "snpedia_url": 'https://www.snpedia.com/index.php/ADIPOQ',
        "omim_url": 'https://omim.org/search?index=entry&search=ADIPOQ'
    },
    'ADRB1': {
        "symbol": 'ADRB1',
        "gene_id": '153',
        "ensembl_id": 'ENSG00000043591',
        "pharmgkb_id": 'PA38',
        "name": 'adrenoceptor beta 1',
        "chromosome": '10',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'adrenoceptor beta 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/153',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000043591',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA38',
        "snpedia_url": 'https://www.snpedia.com/index.php/ADRB1',
        "omim_url": 'https://omim.org/search?index=entry&search=ADRB1'
    },
    'ADRB2': {
        "symbol": 'ADRB2',
        "gene_id": '154',
        "ensembl_id": 'ENSG00000169252',
        "pharmgkb_id": 'PA39',
        "name": 'adrenoceptor beta 2',
        "chromosome": '5',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'adrenoceptor beta 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/154',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000169252',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA39',
        "snpedia_url": 'https://www.snpedia.com/index.php/ADRB2',
        "omim_url": 'https://omim.org/search?index=entry&search=ADRB2'
    },
    'AGT': {
        "symbol": 'AGT',
        "gene_id": '183',
        "ensembl_id": 'ENSG00000135744',
        "pharmgkb_id": 'PA42',
        "name": 'angiotensinogen',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'angiotensinogen. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/183',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000135744',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA42',
        "snpedia_url": 'https://www.snpedia.com/index.php/AGT',
        "omim_url": 'https://omim.org/search?index=entry&search=AGT'
    },
    'AGTR1': {
        "symbol": 'AGTR1',
        "gene_id": '185',
        "ensembl_id": 'ENSG00000144891',
        "pharmgkb_id": 'PA43',
        "name": 'angiotensin II receptor type 1',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'angiotensin II receptor type 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/185',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000144891',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA43',
        "snpedia_url": 'https://www.snpedia.com/index.php/AGTR1',
        "omim_url": 'https://omim.org/search?index=entry&search=AGTR1'
    },
    'APOA1': {
        "symbol": 'APOA1',
        "gene_id": '335',
        "ensembl_id": 'ENSG00000118137',
        "pharmgkb_id": 'PA49',
        "name": 'apolipoprotein A1',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'apolipoprotein A1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/335',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000118137',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA49',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOA1',
        "omim_url": 'https://omim.org/search?index=entry&search=APOA1'
    },
    'APOA5': {
        "symbol": 'APOA5',
        "gene_id": '116519',
        "ensembl_id": 'ENSG00000110243',
        "pharmgkb_id": 'PA24888',
        "name": 'apolipoprotein A5',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'apolipoprotein A5. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/116519',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000110243',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA24888',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOA5',
        "omim_url": 'https://omim.org/search?index=entry&search=APOA5'
    },
    'APOB': {
        "symbol": 'APOB',
        "gene_id": '338',
        "ensembl_id": 'ENSG00000084674',
        "pharmgkb_id": 'PA50',
        "name": 'apolipoprotein B',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'apolipoprotein B. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/338',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000084674',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA50',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOB',
        "omim_url": 'https://omim.org/search?index=entry&search=APOB'
    },
    'APOC2': {
        "symbol": 'APOC2',
        "gene_id": '344',
        "ensembl_id": 'ENSG00000234906',
        "pharmgkb_id": 'PA52',
        "name": 'apolipoprotein C2',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'apolipoprotein C2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/344',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000234906',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA52',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOC2',
        "omim_url": 'https://omim.org/search?index=entry&search=APOC2'
    },
    'APOC3': {
        "symbol": 'APOC3',
        "gene_id": '345',
        "ensembl_id": 'ENSG00000110245',
        "pharmgkb_id": 'PA53',
        "name": 'apolipoprotein C3',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'apolipoprotein C3. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/345',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000110245',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA53',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOC3',
        "omim_url": 'https://omim.org/search?index=entry&search=APOC3'
    },
    'APOE': {
        "symbol": 'APOE',
        "gene_id": '348',
        "ensembl_id": 'ENSG00000130203',
        "pharmgkb_id": 'PA55',
        "name": 'apolipoprotein E',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Major apoprotein of the chylomicron essential for catabolism of triglyceride-rich lipoprotein. Mutations cause familial dysbetalipoproteinemia. APOE4 allele is a major risk factor for cardiovascular disease and Alzheimer.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/348',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000130203',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA55',
        "snpedia_url": 'https://www.snpedia.com/index.php/APOE',
        "omim_url": 'https://omim.org/search?index=entry&search=APOE'
    },
    'ATG16L1': {
        "symbol": 'ATG16L1',
        "gene_id": '55054',
        "ensembl_id": 'ENSG00000085978',
        "pharmgkb_id": 'PA134902949',
        "name": 'autophagy related 16 like 1',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'autophagy related 16 like 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/55054',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000085978',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134902949',
        "snpedia_url": 'https://www.snpedia.com/index.php/ATG16L1',
        "omim_url": 'https://omim.org/search?index=entry&search=ATG16L1'
    },
    'BCO1': {
        "symbol": 'BCO1',
        "gene_id": '53630',
        "ensembl_id": 'ENSG00000135697',
        "pharmgkb_id": 'PA37812',
        "name": 'beta-carotene oxygenase 1',
        "chromosome": '16',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'beta-carotene oxygenase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/53630',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000135697',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA37812',
        "snpedia_url": 'https://www.snpedia.com/index.php/BCO1',
        "omim_url": 'https://omim.org/search?index=entry&search=BCO1'
    },
    'CARD9': {
        "symbol": 'CARD9',
        "gene_id": '64170',
        "ensembl_id": 'ENSG00000187796',
        "pharmgkb_id": 'PA26077',
        "name": 'caspase recruitment domain family member 9',
        "chromosome": '9',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'caspase recruitment domain family member 9. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/64170',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000187796',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA26077',
        "snpedia_url": 'https://www.snpedia.com/index.php/CARD9',
        "omim_url": 'https://omim.org/search?index=entry&search=CARD9'
    },
    'CAT': {
        "symbol": 'CAT',
        "gene_id": '847',
        "ensembl_id": 'ENSG00000121691',
        "pharmgkb_id": 'PA26099',
        "name": 'catalase',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'catalase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/847',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000121691',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA26099',
        "snpedia_url": 'https://www.snpedia.com/index.php/CAT',
        "omim_url": 'https://omim.org/search?index=entry&search=CAT'
    },
    'CDKAL1': {
        "symbol": 'CDKAL1',
        "gene_id": '54901',
        "ensembl_id": 'ENSG00000145996',
        "pharmgkb_id": 'PA134871999',
        "name": 'CDK5 regulatory subunit associated protein 1 like 1',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'CDK5 regulatory subunit associated protein 1 like 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/54901',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000145996',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134871999',
        "snpedia_url": 'https://www.snpedia.com/index.php/CDKAL1',
        "omim_url": 'https://omim.org/search?index=entry&search=CDKAL1'
    },
    'CDKN2A': {
        "symbol": 'CDKN2A',
        "gene_id": '1029',
        "ensembl_id": 'ENSG00000147889',
        "pharmgkb_id": 'PA106',
        "name": 'cyclin dependent kinase inhibitor 2A',
        "chromosome": '9',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cyclin dependent kinase inhibitor 2A. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1029',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000147889',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA106',
        "snpedia_url": 'https://www.snpedia.com/index.php/CDKN2A',
        "omim_url": 'https://omim.org/search?index=entry&search=CDKN2A'
    },
    'COMT': {
        "symbol": 'COMT',
        "gene_id": '1312',
        "ensembl_id": 'ENSG00000093010',
        "pharmgkb_id": 'PA117',
        "name": 'catechol-O-methyltransferase',
        "chromosome": '22',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'catechol-O-methyltransferase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1312',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000093010',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA117',
        "snpedia_url": 'https://www.snpedia.com/index.php/COMT',
        "omim_url": 'https://omim.org/search?index=entry&search=COMT'
    },
    'CRP': {
        "symbol": 'CRP',
        "gene_id": '1401',
        "ensembl_id": 'ENSG00000132693',
        "pharmgkb_id": 'PA120',
        "name": 'C-reactive protein',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'C-reactive protein. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1401',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000132693',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA120',
        "snpedia_url": 'https://www.snpedia.com/index.php/CRP',
        "omim_url": 'https://omim.org/search?index=entry&search=CRP'
    },
    'CYP11B2': {
        "symbol": 'CYP11B2',
        "gene_id": '1585',
        "ensembl_id": 'ENSG00000179142',
        "pharmgkb_id": 'PA134',
        "name": 'cytochrome P450 family 11 subfamily B member 2',
        "chromosome": '8',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cytochrome P450 family 11 subfamily B member 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1585',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000179142',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP11B2',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP11B2'
    },
    'CYP1A2': {
        "symbol": 'CYP1A2',
        "gene_id": '1544',
        "ensembl_id": 'ENSG00000140505',
        "pharmgkb_id": 'PA27093',
        "name": 'cytochrome P450 family 1 subfamily A member 2',
        "chromosome": '15',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cytochrome P450 family 1 subfamily A member 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1544',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000140505',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27093',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP1A2',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP1A2'
    },
    'CYP24A1': {
        "symbol": 'CYP24A1',
        "gene_id": '1591',
        "ensembl_id": 'ENSG00000019186',
        "pharmgkb_id": 'PA27097',
        "name": 'cytochrome P450 family 24 subfamily A member 1',
        "chromosome": '20',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cytochrome P450 family 24 subfamily A member 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1591',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000019186',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27097',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP24A1',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP24A1'
    },
    'CYP27B1': {
        "symbol": 'CYP27B1',
        "gene_id": '1594',
        "ensembl_id": 'ENSG00000111012',
        "pharmgkb_id": 'PA27099',
        "name": 'cytochrome P450 family 27 subfamily B member 1',
        "chromosome": '12',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cytochrome P450 family 27 subfamily B member 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1594',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000111012',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27099',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP27B1',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP27B1'
    },
    'CYP2C19': {
        "symbol": 'CYP2C19',
        "gene_id": '1557',
        "ensembl_id": 'ENSG00000165841',
        "pharmgkb_id": 'PA124',
        "name": 'cytochrome P450 family 2 subfamily C member 19',
        "chromosome": '10',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Metabolizes proton pump inhibitors, antidepressants, and clopidogrel. Poor metabolizers (PM) have significantly altered drug response. VIP gene in clinical pharmacogenomics.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1557',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000165841',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA124',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP2C19',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP2C19'
    },
    'CYP2C9': {
        "symbol": 'CYP2C9',
        "gene_id": '1559',
        "ensembl_id": 'ENSG00000138109',
        "pharmgkb_id": 'PA126',
        "name": 'cytochrome P450 family 2 subfamily C member 9',
        "chromosome": '10',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Metabolizes warfarin, NSAIDs, and many other drugs. Variants cause poor metabolism increasing drug toxicity. Critical for warfarin dosing and herb-drug interaction assessment.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1559',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000138109',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA126',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP2C9',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP2C9'
    },
    'CYP2D6': {
        "symbol": 'CYP2D6',
        "gene_id": '1565',
        "ensembl_id": 'ENSG00000100197',
        "pharmgkb_id": 'PA128',
        "name": 'cytochrome P450 family 2 subfamily D member 6',
        "chromosome": '22',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Metabolizes ~25% of commonly used drugs including antidepressants, antipsychotics, and opioids. Poor metabolizers (PM) have 2-3x higher drug exposure. Very important pharmacogene (VIP).',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1565',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000100197',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA128',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP2D6',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP2D6'
    },
    'CYP2R1': {
        "symbol": 'CYP2R1',
        "gene_id": '120227',
        "ensembl_id": 'ENSG00000186104',
        "pharmgkb_id": 'PA134986407',
        "name": 'cytochrome P450 family 2 subfamily R member 1',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'cytochrome P450 family 2 subfamily R member 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/120227',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000186104',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134986407',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP2R1',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP2R1'
    },
    'CYP3A4': {
        "symbol": 'CYP3A4',
        "gene_id": '1576',
        "ensembl_id": 'ENSG00000160868',
        "pharmgkb_id": 'PA130',
        "name": 'cytochrome P450 family 3 subfamily A member 4',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Most abundant hepatic cytochrome P450, metabolizes ~50% of drugs. Grapefruit inhibits CYP3A4 increasing statin levels and toxicity. St. John Wort induces CYP3A4 reducing drug efficacy.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1576',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000160868',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA130',
        "snpedia_url": 'https://www.snpedia.com/index.php/CYP3A4',
        "omim_url": 'https://omim.org/search?index=entry&search=CYP3A4'
    },
    'DHFR': {
        "symbol": 'DHFR',
        "gene_id": '1719',
        "ensembl_id": 'ENSG00000228716',
        "pharmgkb_id": 'PA143',
        "name": 'dihydrofolate reductase',
        "chromosome": '5',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'dihydrofolate reductase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1719',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000228716',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA143',
        "snpedia_url": 'https://www.snpedia.com/index.php/DHFR',
        "omim_url": 'https://omim.org/search?index=entry&search=DHFR'
    },
    'DPYD': {
        "symbol": 'DPYD',
        "gene_id": '1806',
        "ensembl_id": 'ENSG00000188641',
        "pharmgkb_id": 'PA145',
        "name": 'dihydropyrimidine dehydrogenase',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'dihydropyrimidine dehydrogenase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/1806',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000188641',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA145',
        "snpedia_url": 'https://www.snpedia.com/index.php/DPYD',
        "omim_url": 'https://omim.org/search?index=entry&search=DPYD'
    },
    'ELOVL2': {
        "symbol": 'ELOVL2',
        "gene_id": '54898',
        "ensembl_id": 'ENSG00000197977',
        "pharmgkb_id": 'PA27761',
        "name": 'ELOVL fatty acid elongase 2',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'ELOVL fatty acid elongase 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/54898',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000197977',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27761',
        "snpedia_url": 'https://www.snpedia.com/index.php/ELOVL2',
        "omim_url": 'https://omim.org/search?index=entry&search=ELOVL2'
    },
    'FADS1': {
        "symbol": 'FADS1',
        "gene_id": '3992',
        "ensembl_id": 'ENSG00000149485',
        "pharmgkb_id": 'PA27973',
        "name": 'fatty acid desaturase 1',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'fatty acid desaturase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3992',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000149485',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27973',
        "snpedia_url": 'https://www.snpedia.com/index.php/FADS1',
        "omim_url": 'https://omim.org/search?index=entry&search=FADS1'
    },
    'FADS2': {
        "symbol": 'FADS2',
        "gene_id": '9415',
        "ensembl_id": 'ENSG00000134824',
        "pharmgkb_id": 'PA27974',
        "name": 'fatty acid desaturase 2',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'fatty acid desaturase 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/9415',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000134824',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA27974',
        "snpedia_url": 'https://www.snpedia.com/index.php/FADS2',
        "omim_url": 'https://omim.org/search?index=entry&search=FADS2'
    },
    'FOLH1': {
        "symbol": 'FOLH1',
        "gene_id": '2346',
        "ensembl_id": 'ENSG00000086205',
        "pharmgkb_id": 'PA28205',
        "name": 'folate hydrolase 1',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'folate hydrolase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2346',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000086205',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA28205',
        "snpedia_url": 'https://www.snpedia.com/index.php/FOLH1',
        "omim_url": 'https://omim.org/search?index=entry&search=FOLH1'
    },
    'FTO': {
        "symbol": 'FTO',
        "gene_id": '79068',
        "ensembl_id": 'ENSG00000140718',
        "pharmgkb_id": 'PA152208656',
        "name": 'FTO alpha-ketoglutarate dependent dioxygenase',
        "chromosome": '16',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Alpha-ketoglutarate dependent dioxygenase involved in fat mass and obesity regulation. FTO variants are among the strongest genetic determinants of BMI in genome-wide association studies.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/79068',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000140718',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA152208656',
        "snpedia_url": 'https://www.snpedia.com/index.php/FTO',
        "omim_url": 'https://omim.org/search?index=entry&search=FTO'
    },
    'FUT2': {
        "symbol": 'FUT2',
        "gene_id": '2524',
        "ensembl_id": 'ENSG00000176920',
        "pharmgkb_id": 'PA28429',
        "name": 'fucosyltransferase 2 (H blood group)',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'fucosyltransferase 2 (H blood group). Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2524',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000176920',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA28429',
        "snpedia_url": 'https://www.snpedia.com/index.php/FUT2',
        "omim_url": 'https://omim.org/search?index=entry&search=FUT2'
    },
    'GC': {
        "symbol": 'GC',
        "gene_id": '2638',
        "ensembl_id": 'ENSG00000145321',
        "pharmgkb_id": 'PA28601',
        "name": 'GC vitamin D binding protein',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'GC vitamin D binding protein. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2638',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000145321',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA28601',
        "snpedia_url": 'https://www.snpedia.com/index.php/GC',
        "omim_url": 'https://omim.org/search?index=entry&search=GC'
    },
    'GCKR': {
        "symbol": 'GCKR',
        "gene_id": '2646',
        "ensembl_id": 'ENSG00000084734',
        "pharmgkb_id": 'PA28611',
        "name": 'glucokinase regulator',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'glucokinase regulator. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2646',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000084734',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA28611',
        "snpedia_url": 'https://www.snpedia.com/index.php/GCKR',
        "omim_url": 'https://omim.org/search?index=entry&search=GCKR'
    },
    'GHRL': {
        "symbol": 'GHRL',
        "gene_id": '51738',
        "ensembl_id": 'ENSG00000157017',
        "pharmgkb_id": 'PA142671740',
        "name": 'ghrelin and obestatin prepropeptide',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'ghrelin and obestatin prepropeptide. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/51738',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000157017',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA142671740',
        "snpedia_url": 'https://www.snpedia.com/index.php/GHRL',
        "omim_url": 'https://omim.org/search?index=entry&search=GHRL'
    },
    'GNB3': {
        "symbol": 'GNB3',
        "gene_id": '2784',
        "ensembl_id": 'ENSG00000111664',
        "pharmgkb_id": 'PA176',
        "name": 'G protein subunit beta 3',
        "chromosome": '12',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'G protein subunit beta 3. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2784',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000111664',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA176',
        "snpedia_url": 'https://www.snpedia.com/index.php/GNB3',
        "omim_url": 'https://omim.org/search?index=entry&search=GNB3'
    },
    'GPX1': {
        "symbol": 'GPX1',
        "gene_id": '2876',
        "ensembl_id": 'ENSG00000233276',
        "pharmgkb_id": 'PA28949',
        "name": 'glutathione peroxidase 1',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'glutathione peroxidase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2876',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000233276',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA28949',
        "snpedia_url": 'https://www.snpedia.com/index.php/GPX1',
        "omim_url": 'https://omim.org/search?index=entry&search=GPX1'
    },
    'GSTM1': {
        "symbol": 'GSTM1',
        "gene_id": '2944',
        "ensembl_id": 'ENSG00000134184',
        "pharmgkb_id": 'PA182',
        "name": 'glutathione S-transferase mu 1',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'glutathione S-transferase mu 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2944',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000134184',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA182',
        "snpedia_url": 'https://www.snpedia.com/index.php/GSTM1',
        "omim_url": 'https://omim.org/search?index=entry&search=GSTM1'
    },
    'GSTT1': {
        "symbol": 'GSTT1',
        "gene_id": '2952',
        "ensembl_id": 'ENSG00000277656',
        "pharmgkb_id": 'PA183',
        "name": 'glutathione S-transferase theta 1',
        "chromosome": '22',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'glutathione S-transferase theta 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/2952',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000277656',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA183',
        "snpedia_url": 'https://www.snpedia.com/index.php/GSTT1',
        "omim_url": 'https://omim.org/search?index=entry&search=GSTT1'
    },
    'HLA-DQA1': {
        "symbol": 'HLA-DQA1',
        "gene_id": '3117',
        "ensembl_id": 'ENSG00000196735',
        "pharmgkb_id": 'PA35066',
        "name": 'major histocompatibility complex, class II, DQ alpha 1',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'major histocompatibility complex, class II, DQ alpha 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3117',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000196735',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA35066',
        "snpedia_url": 'https://www.snpedia.com/index.php/HLA-DQA1',
        "omim_url": 'https://omim.org/search?index=entry&search=HLA-DQA1'
    },
    'HLA-DQB1': {
        "symbol": 'HLA-DQB1',
        "gene_id": '3119',
        "ensembl_id": 'ENSG00000179344',
        "pharmgkb_id": 'PA35068',
        "name": 'major histocompatibility complex, class II, DQ beta 1',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'major histocompatibility complex, class II, DQ beta 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3119',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000179344',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA35068',
        "snpedia_url": 'https://www.snpedia.com/index.php/HLA-DQB1',
        "omim_url": 'https://omim.org/search?index=entry&search=HLA-DQB1'
    },
    'HMGCR': {
        "symbol": 'HMGCR',
        "gene_id": '3156',
        "ensembl_id": 'ENSG00000113161',
        "pharmgkb_id": 'PA189',
        "name": '3-hydroxy-3-methylglutaryl-CoA reductase',
        "chromosome": '5',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Rate-limiting enzyme for cholesterol synthesis and pharmacological target of statins. Competitive inhibitors (atorvastatin, simvastatin) reduce LDL cholesterol by upregulating hepatic LDL receptors.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3156',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000113161',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA189',
        "snpedia_url": 'https://www.snpedia.com/index.php/HMGCR',
        "omim_url": 'https://omim.org/search?index=entry&search=HMGCR'
    },
    'HNF1A': {
        "symbol": 'HNF1A',
        "gene_id": '6927',
        "ensembl_id": 'ENSG00000135100',
        "pharmgkb_id": 'PA36380',
        "name": 'HNF1 homeobox A',
        "chromosome": '12',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'HNF1 homeobox A. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6927',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000135100',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA36380',
        "snpedia_url": 'https://www.snpedia.com/index.php/HNF1A',
        "omim_url": 'https://omim.org/search?index=entry&search=HNF1A'
    },
    'HNF4A': {
        "symbol": 'HNF4A',
        "gene_id": '3172',
        "ensembl_id": 'ENSG00000101076',
        "pharmgkb_id": 'PA29349',
        "name": 'hepatocyte nuclear factor 4 alpha',
        "chromosome": '20',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'hepatocyte nuclear factor 4 alpha. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3172',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000101076',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA29349',
        "snpedia_url": 'https://www.snpedia.com/index.php/HNF4A',
        "omim_url": 'https://omim.org/search?index=entry&search=HNF4A'
    },
    'HSD17B13': {
        "symbol": 'HSD17B13',
        "gene_id": '345275',
        "ensembl_id": 'ENSG00000170509',
        "pharmgkb_id": 'PA38634',
        "name": 'hydroxysteroid 17-beta dehydrogenase 13',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'hydroxysteroid 17-beta dehydrogenase 13. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/345275',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000170509',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA38634',
        "snpedia_url": 'https://www.snpedia.com/index.php/HSD17B13',
        "omim_url": 'https://omim.org/search?index=entry&search=HSD17B13'
    },
    'IGF2BP2': {
        "symbol": 'IGF2BP2',
        "gene_id": '10644',
        "ensembl_id": 'ENSG00000073792',
        "pharmgkb_id": 'PA128394577',
        "name": 'insulin like growth factor 2 mRNA binding protein 2',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'insulin like growth factor 2 mRNA binding protein 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/10644',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000073792',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA128394577',
        "snpedia_url": 'https://www.snpedia.com/index.php/IGF2BP2',
        "omim_url": 'https://omim.org/search?index=entry&search=IGF2BP2'
    },
    'IL1B': {
        "symbol": 'IL1B',
        "gene_id": '3553',
        "ensembl_id": 'ENSG00000125538',
        "pharmgkb_id": 'PA29808',
        "name": 'interleukin 1 beta',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'interleukin 1 beta. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3553',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000125538',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA29808',
        "snpedia_url": 'https://www.snpedia.com/index.php/IL1B',
        "omim_url": 'https://omim.org/search?index=entry&search=IL1B'
    },
    'IL2': {
        "symbol": 'IL2',
        "gene_id": '3558',
        "ensembl_id": 'ENSG00000109471',
        "pharmgkb_id": 'PA195',
        "name": 'interleukin 2',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'interleukin 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3558',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000109471',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA195',
        "snpedia_url": 'https://www.snpedia.com/index.php/IL2',
        "omim_url": 'https://omim.org/search?index=entry&search=IL2'
    },
    'IL21': {
        "symbol": 'IL21',
        "gene_id": '59067',
        "ensembl_id": 'ENSG00000138684',
        "pharmgkb_id": 'PA29820',
        "name": 'interleukin 21',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'interleukin 21. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/59067',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000138684',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA29820',
        "snpedia_url": 'https://www.snpedia.com/index.php/IL21',
        "omim_url": 'https://omim.org/search?index=entry&search=IL21'
    },
    'IL23R': {
        "symbol": 'IL23R',
        "gene_id": '149233',
        "ensembl_id": 'ENSG00000162594',
        "pharmgkb_id": 'PA134935109',
        "name": 'interleukin 23 receptor',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'interleukin 23 receptor. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/149233',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000162594',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134935109',
        "snpedia_url": 'https://www.snpedia.com/index.php/IL23R',
        "omim_url": 'https://omim.org/search?index=entry&search=IL23R'
    },
    'IL6': {
        "symbol": 'IL6',
        "gene_id": '3569',
        "ensembl_id": 'ENSG00000136244',
        "pharmgkb_id": 'PA198',
        "name": 'interleukin 6',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'interleukin 6. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3569',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000136244',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA198',
        "snpedia_url": 'https://www.snpedia.com/index.php/IL6',
        "omim_url": 'https://omim.org/search?index=entry&search=IL6'
    },
    'KCNJ11': {
        "symbol": 'KCNJ11',
        "gene_id": '3767',
        "ensembl_id": 'ENSG00000187486',
        "pharmgkb_id": 'PA217',
        "name": 'potassium inwardly rectifying channel subfamily J member 11',
        "chromosome": '11',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'potassium inwardly rectifying channel subfamily J member 11. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3767',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000187486',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA217',
        "snpedia_url": 'https://www.snpedia.com/index.php/KCNJ11',
        "omim_url": 'https://omim.org/search?index=entry&search=KCNJ11'
    },
    'LCT': {
        "symbol": 'LCT',
        "gene_id": '3938',
        "ensembl_id": 'ENSG00000115850',
        "pharmgkb_id": 'PA30315',
        "name": 'lactase',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'lactase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3938',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000115850',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA30315',
        "snpedia_url": 'https://www.snpedia.com/index.php/LCT',
        "omim_url": 'https://omim.org/search?index=entry&search=LCT'
    },
    'LDLR': {
        "symbol": 'LDLR',
        "gene_id": '3949',
        "ensembl_id": 'ENSG00000130164',
        "pharmgkb_id": 'PA227',
        "name": 'low density lipoprotein receptor',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'LDL receptor mediates endocytosis of cholesterol-rich LDL. Mutations cause familial hypercholesterolemia. Statins upregulate LDLR expression to lower plasma LDL.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3949',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000130164',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA227',
        "snpedia_url": 'https://www.snpedia.com/index.php/LDLR',
        "omim_url": 'https://omim.org/search?index=entry&search=LDLR'
    },
    'LEP': {
        "symbol": 'LEP',
        "gene_id": '3952',
        "ensembl_id": 'ENSG00000174697',
        "pharmgkb_id": 'PA228',
        "name": 'leptin',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Leptin hormone secreted by adipose tissue regulates energy balance by inhibiting hunger. Leptin resistance is common in obesity despite elevated leptin levels.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3952',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000174697',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA228',
        "snpedia_url": 'https://www.snpedia.com/index.php/LEP',
        "omim_url": 'https://omim.org/search?index=entry&search=LEP'
    },
    'LEPR': {
        "symbol": 'LEPR',
        "gene_id": '3953',
        "ensembl_id": 'ENSG00000116678',
        "pharmgkb_id": 'PA229',
        "name": 'leptin receptor',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'leptin receptor. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/3953',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000116678',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA229',
        "snpedia_url": 'https://www.snpedia.com/index.php/LEPR',
        "omim_url": 'https://omim.org/search?index=entry&search=LEPR'
    },
    'LPL': {
        "symbol": 'LPL',
        "gene_id": '4023',
        "ensembl_id": 'ENSG00000175445',
        "pharmgkb_id": 'PA232',
        "name": 'lipoprotein lipase',
        "chromosome": '8',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'lipoprotein lipase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4023',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000175445',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA232',
        "snpedia_url": 'https://www.snpedia.com/index.php/LPL',
        "omim_url": 'https://omim.org/search?index=entry&search=LPL'
    },
    'MBOAT7': {
        "symbol": 'MBOAT7',
        "gene_id": '79143',
        "ensembl_id": 'ENSG00000125505',
        "pharmgkb_id": 'PA162395057',
        "name": 'membrane bound O-acyltransferase domain containing 7',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'membrane bound O-acyltransferase domain containing 7. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/79143',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000125505',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA162395057',
        "snpedia_url": 'https://www.snpedia.com/index.php/MBOAT7',
        "omim_url": 'https://omim.org/search?index=entry&search=MBOAT7'
    },
    'MC4R': {
        "symbol": 'MC4R',
        "gene_id": '4160',
        "ensembl_id": 'ENSG00000166603',
        "pharmgkb_id": 'PA30676',
        "name": 'melanocortin 4 receptor',
        "chromosome": '18',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'melanocortin 4 receptor. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4160',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000166603',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA30676',
        "snpedia_url": 'https://www.snpedia.com/index.php/MC4R',
        "omim_url": 'https://omim.org/search?index=entry&search=MC4R'
    },
    'MCM6': {
        "symbol": 'MCM6',
        "gene_id": '4175',
        "ensembl_id": 'ENSG00000076003',
        "pharmgkb_id": 'PA30696',
        "name": 'minichromosome maintenance complex component 6',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'minichromosome maintenance complex component 6. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4175',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000076003',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA30696',
        "snpedia_url": 'https://www.snpedia.com/index.php/MCM6',
        "omim_url": 'https://omim.org/search?index=entry&search=MCM6'
    },
    'MTHFR': {
        "symbol": 'MTHFR',
        "gene_id": '4524',
        "ensembl_id": 'ENSG00000177000',
        "pharmgkb_id": 'PA245',
        "name": 'methylenetetrahydrofolate reductase',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Catalyzes folate metabolism. The C677T variant reduces enzyme activity 30-70%, elevating homocysteine. Relevant for cardiovascular risk, neural tube defects, and response to folate/B12 supplementation.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4524',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000177000',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA245',
        "snpedia_url": 'https://www.snpedia.com/index.php/MTHFR',
        "omim_url": 'https://omim.org/search?index=entry&search=MTHFR'
    },
    'MTR': {
        "symbol": 'MTR',
        "gene_id": '4548',
        "ensembl_id": 'ENSG00000116984',
        "pharmgkb_id": 'PA31272',
        "name": '5-methyltetrahydrofolate-homocysteine methyltransferase',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": '5-methyltetrahydrofolate-homocysteine methyltransferase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4548',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000116984',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA31272',
        "snpedia_url": 'https://www.snpedia.com/index.php/MTR',
        "omim_url": 'https://omim.org/search?index=entry&search=MTR'
    },
    'MTRR': {
        "symbol": 'MTRR',
        "gene_id": '4552',
        "ensembl_id": 'ENSG00000124275',
        "pharmgkb_id": 'PA31277',
        "name": '5-methyltetrahydrofolate-homocysteine methyltransferase reductase',
        "chromosome": '5',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": '5-methyltetrahydrofolate-homocysteine methyltransferase reductase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4552',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000124275',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA31277',
        "snpedia_url": 'https://www.snpedia.com/index.php/MTRR',
        "omim_url": 'https://omim.org/search?index=entry&search=MTRR'
    },
    'NAT2': {
        "symbol": 'NAT2',
        "gene_id": '10',
        "ensembl_id": 'ENSG00000156006',
        "pharmgkb_id": 'PA18',
        "name": 'N-acetyltransferase 2',
        "chromosome": '8',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'N-acetyltransferase 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/10',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000156006',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA18',
        "snpedia_url": 'https://www.snpedia.com/index.php/NAT2',
        "omim_url": 'https://omim.org/search?index=entry&search=NAT2'
    },
    'NFE2L2': {
        "symbol": 'NFE2L2',
        "gene_id": '4780',
        "ensembl_id": 'ENSG00000116044',
        "pharmgkb_id": 'PA31588',
        "name": 'NFE2 like bZIP transcription factor 2',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'NFE2 like bZIP transcription factor 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4780',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000116044',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA31588',
        "snpedia_url": 'https://www.snpedia.com/index.php/NFE2L2',
        "omim_url": 'https://omim.org/search?index=entry&search=NFE2L2'
    },
    'NOD2': {
        "symbol": 'NOD2',
        "gene_id": '64127',
        "ensembl_id": 'ENSG00000167207',
        "pharmgkb_id": 'PA26074',
        "name": 'nucleotide binding oligomerization domain containing 2',
        "chromosome": '16',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'nucleotide binding oligomerization domain containing 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/64127',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000167207',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA26074',
        "snpedia_url": 'https://www.snpedia.com/index.php/NOD2',
        "omim_url": 'https://omim.org/search?index=entry&search=NOD2'
    },
    'NOS3': {
        "symbol": 'NOS3',
        "gene_id": '4846',
        "ensembl_id": 'ENSG00000164867',
        "pharmgkb_id": 'PA254',
        "name": 'nitric oxide synthase 3',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'nitric oxide synthase 3. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4846',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000164867',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA254',
        "snpedia_url": 'https://www.snpedia.com/index.php/NOS3',
        "omim_url": 'https://omim.org/search?index=entry&search=NOS3'
    },
    'NPY': {
        "symbol": 'NPY',
        "gene_id": '4852',
        "ensembl_id": 'ENSG00000122585',
        "pharmgkb_id": 'PA255',
        "name": 'neuropeptide Y',
        "chromosome": '7',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'neuropeptide Y. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/4852',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000122585',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA255',
        "snpedia_url": 'https://www.snpedia.com/index.php/NPY',
        "omim_url": 'https://omim.org/search?index=entry&search=NPY'
    },
    'PCSK9': {
        "symbol": 'PCSK9',
        "gene_id": '255738',
        "ensembl_id": 'ENSG00000169174',
        "pharmgkb_id": 'PA38617',
        "name": 'proprotein convertase subtilisin/kexin type 9',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Promotes degradation of the LDL receptor. Loss-of-function variants reduce LDL and protect against cardiovascular disease. PCSK9 inhibitors are approved cholesterol-lowering treatments.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/255738',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000169174',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA38617',
        "snpedia_url": 'https://www.snpedia.com/index.php/PCSK9',
        "omim_url": 'https://omim.org/search?index=entry&search=PCSK9'
    },
    'PNPLA3': {
        "symbol": 'PNPLA3',
        "gene_id": '80339',
        "ensembl_id": 'ENSG00000100344',
        "pharmgkb_id": 'PA38592',
        "name": 'patatin like phospholipase domain containing 3',
        "chromosome": '22',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'patatin like phospholipase domain containing 3. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/80339',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000100344',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA38592',
        "snpedia_url": 'https://www.snpedia.com/index.php/PNPLA3',
        "omim_url": 'https://omim.org/search?index=entry&search=PNPLA3'
    },
    'POMC': {
        "symbol": 'POMC',
        "gene_id": '5443',
        "ensembl_id": 'ENSG00000115138',
        "pharmgkb_id": 'PA33526',
        "name": 'proopiomelanocortin',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'proopiomelanocortin. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5443',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000115138',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA33526',
        "snpedia_url": 'https://www.snpedia.com/index.php/POMC',
        "omim_url": 'https://omim.org/search?index=entry&search=POMC'
    },
    'PPARG': {
        "symbol": 'PPARG',
        "gene_id": '5468',
        "ensembl_id": 'ENSG00000132170',
        "pharmgkb_id": 'PA281',
        "name": 'peroxisome proliferator activated receptor gamma',
        "chromosome": '3',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'peroxisome proliferator activated receptor gamma. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5468',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000132170',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA281',
        "snpedia_url": 'https://www.snpedia.com/index.php/PPARG',
        "omim_url": 'https://omim.org/search?index=entry&search=PPARG'
    },
    'PTGIS': {
        "symbol": 'PTGIS',
        "gene_id": '5740',
        "ensembl_id": 'ENSG00000124212',
        "pharmgkb_id": 'PA292',
        "name": 'prostaglandin I2 synthase',
        "chromosome": '20',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'prostaglandin I2 synthase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5740',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000124212',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA292',
        "snpedia_url": 'https://www.snpedia.com/index.php/PTGIS',
        "omim_url": 'https://omim.org/search?index=entry&search=PTGIS'
    },
    'PTGS2': {
        "symbol": 'PTGS2',
        "gene_id": '5743',
        "ensembl_id": 'ENSG00000073756',
        "pharmgkb_id": 'PA293',
        "name": 'prostaglandin-endoperoxide synthase 2',
        "chromosome": '1',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'prostaglandin-endoperoxide synthase 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5743',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000073756',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA293',
        "snpedia_url": 'https://www.snpedia.com/index.php/PTGS2',
        "omim_url": 'https://omim.org/search?index=entry&search=PTGS2'
    },
    'RBP4': {
        "symbol": 'RBP4',
        "gene_id": '5950',
        "ensembl_id": 'ENSG00000138207',
        "pharmgkb_id": 'PA34289',
        "name": 'retinol binding protein 4',
        "chromosome": '10',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'retinol binding protein 4. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/5950',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000138207',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA34289',
        "snpedia_url": 'https://www.snpedia.com/index.php/RBP4',
        "omim_url": 'https://omim.org/search?index=entry&search=RBP4'
    },
    'SLC19A1': {
        "symbol": 'SLC19A1',
        "gene_id": '6573',
        "ensembl_id": 'ENSG00000173638',
        "pharmgkb_id": 'PA327',
        "name": 'solute carrier family 19 member 1',
        "chromosome": '21',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'solute carrier family 19 member 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6573',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000173638',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA327',
        "snpedia_url": 'https://www.snpedia.com/index.php/SLC19A1',
        "omim_url": 'https://omim.org/search?index=entry&search=SLC19A1'
    },
    'SLC30A8': {
        "symbol": 'SLC30A8',
        "gene_id": '169026',
        "ensembl_id": 'ENSG00000164756',
        "pharmgkb_id": 'PA134915546',
        "name": 'solute carrier family 30 member 8',
        "chromosome": '8',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'solute carrier family 30 member 8. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/169026',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000164756',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134915546',
        "snpedia_url": 'https://www.snpedia.com/index.php/SLC30A8',
        "omim_url": 'https://omim.org/search?index=entry&search=SLC30A8'
    },
    'SLCO1B1': {
        "symbol": 'SLCO1B1',
        "gene_id": '10599',
        "ensembl_id": 'ENSG00000134538',
        "pharmgkb_id": 'PA134865839',
        "name": 'solute carrier organic anion transporter family member 1B1',
        "chromosome": '12',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Encodes OATP1B1 transporter for hepatic uptake of statins. The rs4149056 variant reduces statin uptake and is strongly associated with statin-induced myopathy, especially simvastatin.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/10599',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000134538',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134865839',
        "snpedia_url": 'https://www.snpedia.com/index.php/SLCO1B1',
        "omim_url": 'https://omim.org/search?index=entry&search=SLCO1B1'
    },
    'SOD1': {
        "symbol": 'SOD1',
        "gene_id": '6647',
        "ensembl_id": 'ENSG00000142168',
        "pharmgkb_id": 'PA334',
        "name": 'superoxide dismutase 1',
        "chromosome": '21',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'superoxide dismutase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6647',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000142168',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA334',
        "snpedia_url": 'https://www.snpedia.com/index.php/SOD1',
        "omim_url": 'https://omim.org/search?index=entry&search=SOD1'
    },
    'SOD2': {
        "symbol": 'SOD2',
        "gene_id": '6648',
        "ensembl_id": 'ENSG00000112096',
        "pharmgkb_id": 'PA36017',
        "name": 'superoxide dismutase 2',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'superoxide dismutase 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6648',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000112096',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA36017',
        "snpedia_url": 'https://www.snpedia.com/index.php/SOD2',
        "omim_url": 'https://omim.org/search?index=entry&search=SOD2'
    },
    'TCF7L2': {
        "symbol": 'TCF7L2',
        "gene_id": '6934',
        "ensembl_id": 'ENSG00000148737',
        "pharmgkb_id": 'PA36394',
        "name": 'transcription factor 7 like 2',
        "chromosome": '10',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Strongest genetic risk factor for type 2 diabetes identified in GWAS. Encodes transcription factor in Wnt signaling pathway affecting beta-cell function and insulin secretion.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6934',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000148737',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA36394',
        "snpedia_url": 'https://www.snpedia.com/index.php/TCF7L2',
        "omim_url": 'https://omim.org/search?index=entry&search=TCF7L2'
    },
    'TCN2': {
        "symbol": 'TCN2',
        "gene_id": '6948',
        "ensembl_id": 'ENSG00000185339',
        "pharmgkb_id": 'PA36404',
        "name": 'transcobalamin 2',
        "chromosome": '22',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'transcobalamin 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/6948',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000185339',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA36404',
        "snpedia_url": 'https://www.snpedia.com/index.php/TCN2',
        "omim_url": 'https://omim.org/search?index=entry&search=TCN2'
    },
    'TM6SF2': {
        "symbol": 'TM6SF2',
        "gene_id": '53345',
        "ensembl_id": 'ENSG00000213996',
        "pharmgkb_id": 'PA36562',
        "name": 'transmembrane 6 superfamily member 2',
        "chromosome": '19',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'transmembrane 6 superfamily member 2. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/53345',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000213996',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA36562',
        "snpedia_url": 'https://www.snpedia.com/index.php/TM6SF2',
        "omim_url": 'https://omim.org/search?index=entry&search=TM6SF2'
    },
    'TNF': {
        "symbol": 'TNF',
        "gene_id": '7124',
        "ensembl_id": 'ENSG00000204490, ENSG00000206439, ENSG00000223952, ENSG00000228321, ENSG00000228849, ENSG00000230108, ENSG00000232810',
        "pharmgkb_id": 'PA435',
        "name": 'tumor necrosis factor',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'tumor necrosis factor. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/7124',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000204490, ENSG00000206439, ENSG00000223952, ENSG00000228321, ENSG00000228849, ENSG00000230108, ENSG00000232810',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA435',
        "snpedia_url": 'https://www.snpedia.com/index.php/TNF',
        "omim_url": 'https://omim.org/search?index=entry&search=TNF'
    },
    'TPMT': {
        "symbol": 'TPMT',
        "gene_id": '7172',
        "ensembl_id": 'ENSG00000137364',
        "pharmgkb_id": 'PA356',
        "name": 'thiopurine S-methyltransferase',
        "chromosome": '6',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'thiopurine S-methyltransferase. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/7172',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000137364',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA356',
        "snpedia_url": 'https://www.snpedia.com/index.php/TPMT',
        "omim_url": 'https://omim.org/search?index=entry&search=TPMT'
    },
    'TRIB1': {
        "symbol": 'TRIB1',
        "gene_id": '10221',
        "ensembl_id": 'ENSG00000173334',
        "pharmgkb_id": 'PA134963922',
        "name": 'tribbles pseudokinase 1',
        "chromosome": '8',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'tribbles pseudokinase 1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/10221',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000173334',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA134963922',
        "snpedia_url": 'https://www.snpedia.com/index.php/TRIB1',
        "omim_url": 'https://omim.org/search?index=entry&search=TRIB1'
    },
    'TTR': {
        "symbol": 'TTR',
        "gene_id": '7276',
        "ensembl_id": 'ENSG00000118271',
        "pharmgkb_id": 'PA37069',
        "name": 'transthyretin',
        "chromosome": '18',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'transthyretin. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/7276',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000118271',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA37069',
        "snpedia_url": 'https://www.snpedia.com/index.php/TTR',
        "omim_url": 'https://omim.org/search?index=entry&search=TTR'
    },
    'UGT1A1': {
        "symbol": 'UGT1A1',
        "gene_id": '54658',
        "ensembl_id": 'ENSG00000241635',
        "pharmgkb_id": 'PA420',
        "name": 'UDP glucuronosyltransferase 1 family, polypeptide A1',
        "chromosome": '2',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'UDP glucuronosyltransferase 1 family, polypeptide A1. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/54658',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000241635',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA420',
        "snpedia_url": 'https://www.snpedia.com/index.php/UGT1A1',
        "omim_url": 'https://omim.org/search?index=entry&search=UGT1A1'
    },
    'VDR': {
        "symbol": 'VDR',
        "gene_id": '7421',
        "ensembl_id": 'ENSG00000111424',
        "pharmgkb_id": 'PA37301',
        "name": 'vitamin D receptor',
        "chromosome": '12',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'Vitamin D receptor mediates action of calcitriol (active vitamin D). Variants affect vitamin D absorption, bone metabolism, and immune function. Critical for vitamin D supplementation decisions.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/7421',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000111424',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA37301',
        "snpedia_url": 'https://www.snpedia.com/index.php/VDR',
        "omim_url": 'https://omim.org/search?index=entry&search=VDR'
    },
    'VKORC1': {
        "symbol": 'VKORC1',
        "gene_id": '79001',
        "ensembl_id": 'ENSG00000167397',
        "pharmgkb_id": 'PA133787052',
        "name": 'vitamin K epoxide reductase complex subunit 1',
        "chromosome": '16',
        "location": '',
        "is_vip": True,
        "has_cpic": True,
        "summary": 'Vitamin K epoxide reductase — target of warfarin anticoagulant. Variants determine warfarin sensitivity and required dosing. Relevant when combining vitamin K supplements with anticoagulant therapy.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/79001',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000167397',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA133787052',
        "snpedia_url": 'https://www.snpedia.com/index.php/VKORC1',
        "omim_url": 'https://omim.org/search?index=entry&search=VKORC1'
    },
    'WFS1': {
        "symbol": 'WFS1',
        "gene_id": '7466',
        "ensembl_id": 'ENSG00000109501',
        "pharmgkb_id": 'PA37365',
        "name": 'wolframin ER transmembrane glycoprotein',
        "chromosome": '4',
        "location": '',
        "is_vip": True,
        "has_cpic": False,
        "summary": 'wolframin ER transmembrane glycoprotein. Gen relevante en farmacogenetica y nutricion clinica.',
        "ncbi_url": 'https://www.ncbi.nlm.nih.gov/gene/7466',
        "ensembl_url": 'https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000109501',
        "pharmgkb_url": 'https://www.pharmgkb.org/gene/PA37365',
        "snpedia_url": 'https://www.snpedia.com/index.php/WFS1',
        "omim_url": 'https://omim.org/search?index=entry&search=WFS1'
    }
}

# Mapa clínico ampliado
CLINICAL_MAP = {
    "obesity":{"genes":["FTO","MC4R","LEP","LEPR","PPARG","ADIPOQ"],"kegg":"hsa04920",
        "msk_slugs":["green-tea","chromium","berberine","conjugated-linoleic-acid","garcinia","glucomannan","5-htp-01","l-carnitine","cinnamon","alpha-lipoic-acid","pyruvate","chitosan"],
        "drugs":["orlistat","semaglutide","phentermine","metformin","liraglutide","topiramate"],
        "pubmed":"obesity supplement herbal weight loss clinical trial"},
    "triglycerides":{"genes":["APOA5","LPL","APOC3","GCKR","TRIB1"],"kegg":"hsa04977",
        "msk_slugs":["fish-oil","niacin","garlic","berberine","flaxseed","red-yeast-rice","green-tea","fenugreek"],
        "drugs":["fenofibrate","gemfibrozil","niacin","omega-3-ethyl-esters"],
        "pubmed":"hypertriglyceridemia omega-3 supplement herbal clinical trial"},
    "cholesterol":{"genes":["APOE","LDLR","PCSK9","HMGCR","APOB"],"kegg":"hsa04977",
        "msk_slugs":["fish-oil","garlic","red-yeast-rice","flaxseed","green-tea","resveratrol","milk-thistle","berberine","coenzyme-q10","niacin","artichoke"],
        "drugs":["atorvastatin","rosuvastatin","simvastatin","ezetimibe","fenofibrate"],
        "pubmed":"cholesterol statin supplement interaction silymarin CoQ10 clinical"},
    "atorvastatin":{"genes":["HMGCR","APOE","LDLR","CYP3A4","SLCO1B1"],"kegg":"hsa04977",
        "msk_slugs":["milk-thistle","coenzyme-q10","red-yeast-rice","fish-oil","vitamin-d","garlic","niacin","berberine"],
        "drugs":["atorvastatin","rosuvastatin","simvastatin","pravastatin"],
        "pubmed":"atorvastatin statin supplement interaction CoQ10 silymarin myopathy hepatotoxicity"},
    "statins":{"genes":["HMGCR","CYP3A4","SLCO1B1","ABCB1"],"kegg":"hsa04977",
        "msk_slugs":["milk-thistle","coenzyme-q10","red-yeast-rice","fish-oil","vitamin-d","garlic","niacin"],
        "drugs":["atorvastatin","rosuvastatin","simvastatin"],
        "pubmed":"statin supplement interaction myopathy hepatotoxicity CoQ10 clinical"},
    "silymarin":{"genes":["CYP3A4","CYP2C9","ABCB1","UGT1A"],"kegg":"hsa00591",
        "msk_slugs":["milk-thistle","vitamin-e","alpha-lipoic-acid","artichoke","dandelion"],
        "drugs":["statins","metformin","cyclosporine","anticoagulants","warfarin"],
        "pubmed":"silymarin milk thistle hepatoprotective statin interaction CYP3A4 clinical"},
    "diabetes":{"genes":["TCF7L2","PPARG","KCNJ11","SLC30A8","HNF1A"],"kegg":"hsa04930",
        "msk_slugs":["berberine","chromium","cinnamon","magnesium","fenugreek","alpha-lipoic-acid","gymnema","bitter-melon","aloe-vera","ginseng"],
        "drugs":["metformin","glipizide","insulin","sitagliptin","empagliflozin","semaglutide"],
        "pubmed":"diabetes type 2 herbal supplement glycemic control berberine clinical"},
    "hypertension":{"genes":["ACE","AGT","AGTR1","ADD1","CYP11B2"],"kegg":"hsa04614",
        "msk_slugs":["garlic","fish-oil","coenzyme-q10","magnesium","hibiscus","hawthorn"],
        "drugs":["enalapril","losartan","amlodipine","hydrochlorothiazide","metoprolol"],
        "pubmed":"hypertension herbal supplement blood pressure garlic magnesium clinical"},
    "liver":{"genes":["PNPLA3","TM6SF2","MBOAT7","GCKR","HSD17B13"],"kegg":"hsa04932",
        "msk_slugs":["milk-thistle","artichoke","dandelion","alpha-lipoic-acid","vitamin-e","berberine"],
        "drugs":["atorvastatin","acetaminophen","alcohol","methotrexate"],
        "pubmed":"NAFLD NASH herbal liver hepatoprotective silymarin clinical"},
    "inflammation":{"genes":["TNF","IL6","CRP","IL1B","PTGS2","NF-kB"],"kegg":"hsa04668",
        "msk_slugs":["turmeric","fish-oil","resveratrol","quercetin","vitamin-d","boswellia","ginger","green-tea"],
        "drugs":["ibuprofen","naproxen","celecoxib","prednisone","methotrexate"],
        "pubmed":"inflammation herbal anti-inflammatory supplement curcumin omega-3 clinical"},
    "weight loss":{"genes":["FTO","MC4R","LEP","LEPR","PPARG"],"kegg":"hsa04920",
        "msk_slugs":["green-tea","chromium","berberine","conjugated-linoleic-acid","garcinia","5-htp-01","l-carnitine","cinnamon"],
        "drugs":["orlistat","semaglutide","phentermine"],
        "pubmed":"weight loss supplement herbal nutrition clinical evidence adverse effects"},
    "lactose intolerance":{"genes":["LCT","MCM6"],"kegg":"hsa00052",
        "msk_slugs":["probiotics","calcium","vitamin-d"],
        "drugs":["lactase"],
        "pubmed":"lactose intolerance probiotics calcium vitamin D supplement"},
    "celiac":{"genes":["HLA-DQ2","HLA-DQ8","IL2","IL21","CTLA4"],"kegg":"hsa04940",
        "msk_slugs":["vitamin-d","folic-acid","selenium","zinc","iron","vitamin-b12","magnesium"],
        "drugs":[],
        "pubmed":"celiac disease gluten micronutrient deficiency vitamin D zinc supplement"},
    "vitamin D":{"genes":["VDR","CYP27B1","CYP2R1","GC"],"kegg":"hsa04978",
        "msk_slugs":["vitamin-d","calcium","magnesium","vitamin-k"],
        "drugs":["cholecalciferol","ergocalciferol","antiepilecticos"],
        "pubmed":"vitamin D deficiency supplementation clinical evidence safety"},
    "folate":{"genes":["MTHFR","FOLH1","SLC19A1","DHFR"],"kegg":"hsa00670",
        "msk_slugs":["folic-acid","vitamin-b12","vitamin-b6"],
        "drugs":["methotrexate","sulfasalazine","anticonvulsants"],
        "pubmed":"folate deficiency MTHFR supplementation homocysteine clinical"},
    "vitamin B12":{"genes":["TCN2","MTRR","MTR","FUT2"],"kegg":"hsa00670",
        "msk_slugs":["vitamin-b12","folic-acid"],
        "drugs":["metformin","proton pump inhibitors","colchicine"],
        "pubmed":"vitamin B12 deficiency supplementation cobalamin clinical"},
    "gut microbiota":{"genes":["NOD2","FUT2","IL23R","CARD9","ATG16L1"],"kegg":"hsa05321",
        "msk_slugs":["probiotics","glutamine","fish-oil","vitamin-d","zinc"],
        "drugs":["antibiotics","rifaximin","metronidazole"],
        "pubmed":"gut microbiota probiotic prebiotic nutrition clinical evidence"},
    "gallstones":{"genes":["ABCG5","ABCG8","LITH1"],"kegg":"hsa04976",
        "msk_slugs":["artichoke","dandelion","milk-thistle","vitamin-c"],
        "drugs":["ursodeoxycholic acid","cholestyramine"],
        "pubmed":"gallstones cholelithiasis herbal supplement ursodeoxycholic acid clinical"},
    "omega-3":{"genes":["FADS1","FADS2","ELOVL2"],"kegg":"hsa00592",
        "msk_slugs":["fish-oil","flaxseed"],
        "drugs":["warfarin","aspirin","anticoagulants","clopidogrel"],
        "pubmed":"omega-3 fish oil cardiovascular supplement interaction anticoagulant clinical"},
    "grapefruit":{"genes":["CYP3A4","CYP1A2","ABCB1"],"kegg":"hsa00982",
        "msk_slugs":["milk-thistle","garlic","ginger","green-tea"],
        "drugs":["statins","calcium channel blockers","immunosuppressants","benzodiazepines"],
        "pubmed":"grapefruit CYP3A4 drug interaction pharmacokinetics clinical"},
}

# ── SQLITE ────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS herb_cache (
        slug TEXT PRIMARY KEY, name TEXT, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS gene_cache (
        gene_id TEXT PRIMARY KEY, extra TEXT, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS query_cache (
        query_key TEXT PRIMARY KEY, extra TEXT, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS query_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT, query_type TEXT, timestamp TEXT)""")
    conn.commit(); conn.close()

def cache_get(table, key_col, key):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute(f"SELECT data FROM {table} WHERE {key_col}=?", (key,))
    row = c.fetchone(); conn.close()
    return json.loads(row[0]) if row else None

def cache_set(table, key_col, key, extra_col, extra_val, data):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?)",
              (key, extra_val, json.dumps(data, ensure_ascii=False), now))
    conn.commit(); conn.close()

def log_query(query, qtype):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO query_log (query,query_type,timestamp) VALUES (?,?,?)",
              (query, qtype, datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()

# ── TRADUCCIÓN ────────────────────────────────────────────────────────────────
async def translate_to_en(text: str, client: httpx.AsyncClient) -> str:
    """Translate Spanish query to English using MyMemory API."""
    t = text.lower().strip()
    # Direct dict lookup first
    if t in ES_EN: return ES_EN[t]
    for es, en in ES_EN.items():
        if es in t: t = t.replace(es, en)
    # If still looks Spanish, call MyMemory
    if any(c in t for c in ['á','é','í','ó','ú','ñ','ü']):
        try:
            r = await client.get("https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": "es|en"}, timeout=5.0)
            translated = r.json().get("responseData",{}).get("translatedText","")
            if translated and translated != text:
                return translated.lower()
        except: pass
    return t

# ── MSK SCRAPER ───────────────────────────────────────────────────────────────
async def fetch_msk_herb(slug: str, client: httpx.AsyncClient) -> dict:
    # 1) Probar Supabase primero (datos pre-traducidos al espanol)
    sb_data = await supabase_get_herb(slug)
    if sb_data:
        logger.info(f"Supabase hit: {slug}")
        # Tambien guardamos en cache local para acceso aun mas rapido
        try: cache_set("herb_cache","slug",slug,"name", sb_data.get("name",""), sb_data)
        except Exception: pass
        return sb_data

    # 2) Cache local SQLite
    cached = cache_get("herb_cache","slug", slug)
    if cached: logger.info(f"Cache SQLite: {slug}"); return cached

    # 3) Fallback: scraping MSK en vivo (solo si no esta en Supabase ni en SQLite)
    url = f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}"
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        if r.status_code != 200 or "Page Not Found" in r.text:
            return {"error": f"No encontrado: {slug}", "slug": slug}

        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.get_text(separator="\n")

        herb = {"name": slug.replace("-"," ").title(), "slug": slug, "url": url,
                "scientific_name":"","common_names":[],"what_is_it":"",
                "benefits":[],"side_effects":[],"warnings":[],
                "clinical_summary":"","mechanism_of_action":"",
                "drug_interactions":[],"drug_interactions_raw":"",
                "food_interactions":[],"herb_interactions":[],
                "adverse_reactions":"","purported_uses":[],"contraindications":"",
                "dosage":""}

        def _extract(pattern, text, flags=re.DOTALL, limit=2000):
            m = re.search(pattern, text, flags)
            return m.group(1).strip()[:limit] if m else ""

        def _list(pattern, text, limit=20):
            m = re.search(pattern, text, re.DOTALL)
            if not m: return []
            return [l.strip('- •*').strip() for l in m.group(1).split('\n')
                    if l.strip() and len(l.strip()) > 5][:limit]

        herb["scientific_name"] = _extract(r'Scientific Name\s*\n+([^\n]{3,120})', content, 0)
        herb["common_names"]    = _list(r'## Common Names\s*\n(.*?)(?=\nJump to|\n##)', content)[:6]
        herb["what_is_it"]      = _extract(r'What is it\?\s*\n+(.*?)(?=What are the potential|What are the side)', content, re.DOTALL, 800)
        herb["benefits"]        = _list(r'What are the potential uses and benefits\?\s*\n+(.*?)(?=What are the side effects)', content)
        herb["side_effects"]    = _list(r'What are the side effects\?\s*\n+(.*?)(?=What else do I need)', content)
        herb["warnings"]        = _list(r'What else do I need to know\?\s*\n+(.*?)(?=For Healthcare|##)', content)
        herb["clinical_summary"]    = _extract(r'Clinical Summary\s*\n+(.*?)(?=Food Sources|Purported Uses|Mechanism of Action|Pharmacology|Adverse)', content, re.DOTALL, 2500)
        herb["mechanism_of_action"] = _extract(r'Mechanism of Action\s*\n+(.*?)(?=Pharmacology|Adverse Reactions|Herb-Drug|Dosage|References)', content, re.DOTALL, 1800)
        herb["adverse_reactions"]   = _extract(r'Adverse Reactions\s*\n+(.*?)(?=Herb-Drug|Dosage|References)', content, re.DOTALL, 1200)
        herb["contraindications"]   = _extract(r'Contraindications\s*\n+(.*?)(?=Adverse|References|##)', content, re.DOTALL, 600)
        herb["dosage"]              = _extract(r'Dosage\s*\n+(.*?)(?=References|##)', content, re.DOTALL, 400)
        herb["purported_uses"]      = _list(r'Purported Uses and Benefits\s*\n+(.*?)(?=Food Sources|Mechanism)', content)

        # Drug interactions — full raw + parsed
        di_raw = _extract(r'Herb-Drug Interactions\s*\n+(.*?)(?=Dosage|References|##)', content, re.DOTALL, 4000)
        herb["drug_interactions_raw"] = di_raw
        herb["drug_interactions"] = [l.strip('- •*').strip() for l in di_raw.split('\n')
                                      if l.strip() and len(l.strip()) > 15][:25]

        # Food interactions — extract from content
        food_section = _extract(r'Food(?:\s+and\s+Drug)?\s+Interactions?\s*\n+(.*?)(?=Herb-Drug|Adverse|Dosage|##)', content, re.DOTALL, 1500)
        if food_section:
            herb["food_interactions"] = [l.strip('- •*').strip() for l in food_section.split('\n')
                                          if l.strip() and len(l.strip()) > 10][:15]

        # Also extract food mentions from clinical summary and interactions
        food_keywords = ["grapefruit","pomegranate","alcohol","food","diet","juice","dairy","caffeine","toronja","granada"]
        for line in herb["drug_interactions"] + [herb["clinical_summary"][:500]]:
            if any(kw in line.lower() for kw in food_keywords):
                if line not in herb["food_interactions"]:
                    herb["food_interactions"].append(line)

        cache_set("herb_cache","slug",slug,"name",herb["name"],herb)
        logger.info(f"✅ MSK cached: {slug}")
        return herb
    except Exception as e:
        logger.error(f"Error MSK {slug}: {e}")
        return {"error": str(e), "slug": slug}


# ── GENE LOOKUP — local DB first, NCBI fallback ───────────────────────────────
async def fetch_ncbi_gene(gene_symbol: str, client: httpx.AsyncClient) -> dict:
    sym = gene_symbol.upper().strip()

    # 1. Check SQLite cache
    cached = cache_get("gene_cache","gene_id", sym)
    if cached: return cached

    # 2. Local GENE_DB (works offline, no external calls needed)
    if sym in GENE_DB:
        data = dict(GENE_DB[sym])
        cache_set("gene_cache","gene_id",sym,"data","",data)
        logger.info(f"💾 Gene from local DB: {sym}")
        return data

    # 3. Try MyGene.info (may be blocked on some hosts)
    try:
        r = await client.get("https://mygene.info/v3/query",
            params={"q": sym, "species":"human",
                    "fields":"ensembl.gene,symbol,name,chromosome,genomic_pos,summary"},
            timeout=8.0)
        hits = r.json().get("hits",[])
        hit = next((h for h in hits if h.get("symbol","").upper()==sym), hits[0] if hits else None)
        if hit:
            ens = hit.get("ensembl",{})
            if isinstance(ens, list): ens = ens[0] if ens else {}
            ensembl_id = ens.get("gene","") if isinstance(ens, dict) else ""
            gpos = hit.get("genomic_pos",{})
            if isinstance(gpos, list): gpos = gpos[0] if gpos else {}
            chrom = str(gpos.get("chr","")) or str(hit.get("chromosome",""))
            ncbi_id = hit.get("_id","")
            data = {
                "symbol": sym, "gene_id": ncbi_id, "ensembl_id": ensembl_id,
                "name": hit.get("name",""), "chromosome": chrom,
                "location": hit.get("location", chrom+"q" if chrom else ""),
                "summary": (hit.get("summary","") or "")[:800],
                "ncbi_url": f"https://www.ncbi.nlm.nih.gov/gene/{ncbi_id}",
                "ensembl_url": f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={ensembl_id}" if ensembl_id else f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?q={sym}",
                "snpedia_url": f"https://www.snpedia.com/index.php/{sym}",
                "omim_url": f"https://omim.org/search?index=entry&search={sym}",
            }
            cache_set("gene_cache","gene_id",sym,"data","",data)
            return data
    except Exception as e:
        logger.warning(f"MyGene.info unavailable for {sym}: {e}")

    # 4. Minimal fallback
    return {
        "symbol": sym, "gene_id": "", "ensembl_id": "", "name": sym,
        "chromosome": "?", "location": "?",
        "summary": f"Gen {sym} — ver informacion completa en NCBI.",
        "ncbi_url": f"https://www.ncbi.nlm.nih.gov/gene/?term={sym}+Homo+sapiens",
        "ensembl_url": f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?q={sym}",
        "snpedia_url": f"https://www.snpedia.com/index.php/{sym}",
        "omim_url": f"https://omim.org/search?index=entry&search={sym}",
    }


# ── KEGG ──────────────────────────────────────────────────────────────────────
async def fetch_kegg_pathway(pathway_id: str, client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"https://rest.kegg.jp/get/{pathway_id}", timeout=10.0)
        text = r.text
        def _m(pat): m=re.search(pat,text); return m.group(1).strip() if m else ""
        name = _m(r'NAME\s+(.+)')
        desc = _m(r'DESCRIPTION\s+(.*?)(?=\nCLASS|\nKEGG)')[:600]
        genes = []
        gm = re.search(r'GENE\s+(.*?)(?=\nCOMPOUND|\nREFERENCE|\nORG)',text,re.DOTALL)
        if gm:
            for line in gm.group(1).strip().split('\n')[:20]:
                parts = line.strip().split(None,2)
                if len(parts)>=2: genes.append({"id":parts[0],"symbol":parts[1].rstrip(';')})
        return {"id":pathway_id,"name":name,"description":desc,"genes":genes,
                "kegg_url":f"https://www.kegg.jp/pathway/{pathway_id}"}
    except Exception as e:
        return {"id":pathway_id,"error":str(e)}


# ── PUBMED ────────────────────────────────────────────────────────────────────
async def search_pubmed(query: str, client: httpx.AsyncClient, n: int = 6) -> list:
    try:
        r = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":query,"retmode":"json","retmax":n,"sort":"relevance"},
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
            refs.append({"pmid":pmid,"title":art.get("title","")[:200],
                         "authors":authors[0].get("name","")+" et al." if authors else "",
                         "journal":art.get("fulljournalname",""),"year":art.get("pubdate","")[:4],
                         "url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
        return refs
    except: return []


# ── DRUG/FOOD INTERACTION ANALYZER ───────────────────────────────────────────
def analyze_interactions(herbs: list, drugs: list) -> dict:
    drug_alerts = []
    food_alerts = []
    herb_alerts = []
    seen_drugs = set()
    seen_foods = set()

    food_keywords = {
        "grapefruit":   "Inhibe CYP3A4 — aumenta niveles plasmáticos del fármaco",
        "pomegranate":  "Puede inhibir metabolismo hepático — riesgo de toxicidad",
        "pomelo":       "Inhibe CYP3A4 similar a la toronja",
        "alcohol":      "Aumenta riesgo de daño hepático y potencia efectos adversos",
        "caffeine":     "Puede aumentar absorción y efectos secundarios",
        "dairy":        "Puede reducir absorción de algunos fármacos",
        "juice":        "Jugos cítricos pueden alterar metabolismo hepático",
        "st. john":     "Inductor CYP3A4 — reduce niveles plasmáticos del fármaco",
        "toronja":      "Inhibe CYP3A4 — aumenta niveles plasmáticos del fármaco",
        "granada":      "Puede inhibir metabolismo hepático",
    }

    for herb in herbs:
        if not herb or "error" in herb: continue
        hname = herb.get("name","")
        di_raw = herb.get("drug_interactions_raw","").lower()
        di_list = herb.get("drug_interactions",[])
        fi_list = herb.get("food_interactions",[])

        # Drug interactions
        for drug in drugs:
            dl = drug.lower()
            if dl in di_raw and dl not in seen_drugs:
                for line in di_list:
                    if dl in line.lower():
                        drug_alerts.append({
                            "drug": drug, "herb": hname, "alert": line,
                            "source": herb.get("url",""),
                            "severity": "⚠ PRECAUCIÓN" if any(w in line.lower() for w in
                                ["avoid","caution","increase","toxic","inhibit","serious","severe","bleeding"]) else "ℹ MONITOREAR"
                        })
                        seen_drugs.add(dl)
                        break

        # Food interactions from herb data
        all_text = " ".join(di_list + fi_list + [herb.get("clinical_summary","")[:300]])
        for food_kw, food_desc in food_keywords.items():
            if food_kw in all_text.lower() and food_kw not in seen_foods:
                food_alerts.append({"food": food_kw.title(), "herb": hname,
                                    "description": food_desc, "source": herb.get("url","")})
                seen_foods.add(food_kw)

    return {"drug_alerts": drug_alerts, "food_alerts": food_alerts}


# ── FREE SEARCH — cualquier término ──────────────────────────────────────────
async def free_search(query_en: str, query_orig: str, client: httpx.AsyncClient) -> dict:
    """Search MSK for any term not in CLINICAL_MAP."""
    # Search PubMed for related supplements
    refs = await search_pubmed(f"{query_en} supplement herbal clinical nutrition", client, n=6)

    # Try to find MSK herbs related to this query
    related_slugs = []
    for slug, kw_list in [
        ("fish-oil", ["triglyceride","lipid","heart","cardiovascular","omega"]),
        ("berberine", ["glucose","cholesterol","triglyceride","diabetes","lipid"]),
        ("milk-thistle", ["liver","hepatic","statin","cholesterol"]),
        ("coenzyme-q10", ["statin","myopathy","energy","mitochondria","heart"]),
        ("green-tea", ["weight","obesity","lipid","antioxidant","cancer"]),
        ("turmeric", ["inflammation","arthritis","cancer","pain","antioxidant"]),
        ("garlic", ["blood pressure","cholesterol","lipid","cardiovascular","infection"]),
        ("magnesium", ["muscle","heart","diabetes","migraine","anxiety","bone"]),
        ("vitamin-d", ["bone","immune","cancer","depression","cardiovascular"]),
        ("ginger", ["nausea","inflammation","digestion","pain","arthritis"]),
        ("probiotics", ["gut","microbiota","diarrhea","immune","bowel"]),
        ("artichoke", ["liver","cholesterol","digestion","gallstone","lipid"]),
        ("red-yeast-rice", ["cholesterol","statin","lipid","cardiovascular"]),
        ("alpha-lipoic-acid", ["diabetes","neuropathy","antioxidant","liver","weight"]),
        ("flaxseed", ["cholesterol","triglyceride","omega","cardiovascular","fiber"]),
        ("resveratrol", ["cardiovascular","antioxidant","inflammation","cancer","aging"]),
        ("niacin", ["cholesterol","triglyceride","pellagra","cardiovascular"]),
        ("chromium", ["diabetes","insulin","weight","glucose","obesity"]),
        ("fenugreek", ["diabetes","cholesterol","testosterone","lactation"]),
    ]:
        if any(kw in query_en for kw in kw_list):
            related_slugs.append(slug)

    # Fetch up to 6 related herbs
    herb_tasks = [fetch_msk_herb(slug, client) for slug in related_slugs[:6]]
    herbs = [h for h in await asyncio.gather(*herb_tasks) if "error" not in h]

    return {"herbs": herbs, "references": refs, "related_slugs": related_slugs}


# ── DESCRIPTIONS ─────────────────────────────────────────────────────────────
DESCRIPTIONS = {
    "obesity": "La obesidad involucra genes reguladores del apetito (FTO, MC4R, LEP) y metabolismo energético (PPARG). Fármacos como orlistat y semaglutide interactúan con múltiples suplementos. Pérdida de peso rápida (>1.5 kg/sem) aumenta riesgo de cálculos biliares — el UDCA (ácido ursodesoxicólico) se usa como protección. El té verde, berberina y cromo tienen mayor evidencia clínica.",
    "triglycerides": "Los triglicéridos elevados (hipertrigliceridemia) involucran genes APOA5, LPL y APOC3. Los omega-3 (EPA/DHA) son el suplemento con mayor evidencia — reducen triglicéridos 20-30%. La niacina también es eficaz pero interactúa con estatinas. El ajo y la berberina tienen evidencia secundaria.",
    "cholesterol": "El metabolismo lipídico depende de APOE, LDLR y HMGCR. Las estatinas (atorvastatina, rosuvastatina) son la base del tratamiento. La toronja inhibe CYP3A4 y AUMENTA los niveles de estatinas — riesgo de miopatía y hepatotoxicidad. El CoQ10 es recomendado como coadyuvante en miopatía por estatinas. La silimarina (cardo mariano) tiene efecto hepatoprotector documentado.",
    "atorvastatin": "La atorvastatina inhibe HMGCR (enzima limitante de la síntesis de colesterol). Interacciones críticas: TORONJA inhibe CYP3A4 → aumenta niveles de atorvastatina → mayor toxicidad. La SILIMARINA puede interactuar via CYP3A4. El CoQ10 puede atenuar la miopatía inducida. La CANELA EN EXCESO (cumarina) tiene efecto hepatotóxico aditivo. Kava, chaparral y comfrey son hepatotóxicos — CONTRAINDICADOS con estatinas.",
    "statins": "Las estatinas (atorvastatina, rosuvastatina, simvastatina) inhiben HMGCR. Coadyuvantes con evidencia: CoQ10 para miopatía, silimarina para hepatoprotección. Contraindicados: toronja, kava, chaparral, comfrey. La pravastatin y rosuvastatina son más seguras hepaticamente.",
    "silymarin": "La silimarina actúa sobre CYP3A4 y CYP2C9, modificando el metabolismo de múltiples fármacos. Tiene efecto hepatoprotector documentado en MSK. Interactúa con estatinas, anticoagulantes y ciclosporina. Es el hepatoprotector natural con mayor evidencia clínica.",
    "liver": "La salud hepática depende de PNPLA3 y TM6SF2. El cardo mariano (silimarina) es el hepatoprotector con mayor evidencia. La alcachofa tiene efecto colerético. Evitar: kava, chaparral, comfrey, canela en exceso — hepatotóxicos.",
    "inflammation": "La inflamación crónica involucra TNF-α, IL-6 y NF-kB. Curcumina (cúrcuma), omega-3 y quercetina tienen mayor evidencia. Interacciones: curcumina potencia anticoagulantes. Omega-3 aumenta riesgo de sangrado con warfarina.",
    "hypertension": "El ajo reduce presión arterial modestamente (evidencia Cochrane). CoQ10 tiene efecto vasodilatador. El magnesio es esencial para función vascular. El espino blanco (hawthorn) tiene evidencia en ICC leve. Cuidado: ajo + antihipertensivos puede causar hipotensión.",
    "diabetes": "La berberina tiene eficacia comparable a metformina en glucosa (estudios chinos). El cromo mejora sensibilidad a insulina. La canela reduce glucosa en ayunas modestamente. PRECAUCIÓN: combinación con metformina o insulina puede causar hipoglucemia.",
    "weight loss": "Pérdida rápida de peso aumenta riesgo de cálculos biliares — UDCA (ursodiol) es preventivo. Déficit de micronutrientes es común. El té verde (EGCG) tiene evidencia en metabolismo. La berberina actúa sobre AMPK similar a metformina.",
    "gallstones": "Los cálculos biliares se forman por saturación de colesterol biliar. El UDCA (ácido ursodesoxicólico) es el tratamiento farmacológico de primera línea. La alcachofa tiene efecto colerético documentado. Pérdida de peso rápida es factor de riesgo — usar UDCA profiláctico.",
    "gut microbiota": "La microbiota depende de NOD2, FUT2 y genes de inmunidad innata. Los probióticos tienen mayor evidencia en SII y prevención de diarrea por antibióticos. En inmunosuprimidos pueden causar infecciones — PRECAUCIÓN.",
}

def get_description(key): return DESCRIPTIONS.get(key, f"Análisis basado en evidencia clínica de MSK, NCBI y PubMed para: {key.title()}")


# ── MODELS ────────────────────────────────────────────────────────────────────
class ClinicalQuery(BaseModel):
    query: str
    drugs_used: Optional[List[str]] = []

class GeneQuery(BaseModel):
    genes: List[str]

class NutrientQuery(BaseModel):
    nutrient: str


# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="NutriKen", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup(): init_db(); logger.info("🌿 NutriKen v2 iniciado")

@app.get("/")
async def root(): return FileResponse("index.html")

@app.get("/script.js")
async def js(): return FileResponse("script.js")

@app.get("/style.css")
async def css(): return FileResponse("style.css")

@app.get("/health")
async def health(): return {"status":"ok","version":"NutriKen 2.0"}


# ── ENDPOINT 1: CLÍNICO — búsqueda libre en cualquier idioma ─────────────────
@app.post("/api/clinical")
async def clinical_analysis(req: ClinicalQuery):
    log_query(req.query, "clinical")

    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/2.0 (educational)"}) as client:
        # 1. Translate to English
        query_en = await translate_to_en(req.query, client)
        logger.info(f"Query: '{req.query}' → EN: '{query_en}'")

        # 2. Find matching condition (flexible)
        matched_key = None
        matched_data = None
        for key, data in CLINICAL_MAP.items():
            if key in query_en or query_en in key or any(w in query_en for w in key.split() if len(w)>3):
                matched_key = key; matched_data = data; break

        if matched_data:
            # Known condition — full structured response
            genes_tasks = [fetch_ncbi_gene(g, client) for g in matched_data["genes"][:5]]
            genes_info  = await asyncio.gather(*genes_tasks)
            pathway     = await fetch_kegg_pathway(matched_data["kegg"], client)
            slugs       = matched_data["msk_slugs"][:10]
            herb_tasks  = [fetch_msk_herb(slug, client) for slug in slugs]
            herbs_raw   = await asyncio.gather(*herb_tasks)
            herbs       = [h for h in herbs_raw if "error" not in h]

            # All drugs: user-provided + condition defaults
            all_drugs = list(set((req.drugs_used or []) + matched_data.get("drugs",[])))
            interactions = analyze_interactions(herbs, all_drugs)

            refs = await search_pubmed(matched_data["pubmed"], client, n=6)

            return {
                "query": req.query, "query_en": query_en,
                "condition": matched_key.title(),
                "description": get_description(matched_key),
                "genes": [g for g in genes_info if "error" not in g],
                "pathway": pathway,
                "supplements": herbs,
                "drug_alerts": interactions["drug_alerts"],
                "food_alerts": interactions["food_alerts"],
                "drugs_related": matched_data.get("drugs",[]),
                "references": refs,
                "msk_sources": [f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{s}" for s in slugs[:6]],
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            # FREE SEARCH — any unknown term
            free = await free_search(query_en, req.query, client)
            herbs = free["herbs"]
            all_drugs = req.drugs_used or []
            interactions = analyze_interactions(herbs, all_drugs)
            return {
                "query": req.query, "query_en": query_en,
                "condition": req.query.title(),
                "description": f"Búsqueda libre en MSK y PubMed para: '{req.query}'. Suplementos relacionados encontrados con mayor evidencia disponible.",
                "genes": [], "pathway": {},
                "supplements": herbs,
                "drug_alerts": interactions["drug_alerts"],
                "food_alerts": interactions["food_alerts"],
                "drugs_related": all_drugs,
                "references": free["references"],
                "msk_sources": [f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{s}" for s in free["related_slugs"][:6]],
                "timestamp": datetime.datetime.now().isoformat()
            }


# ── ENDPOINT 2: GEN ───────────────────────────────────────────────────────────
@app.post("/api/gene")
async def gene_analysis(req: GeneQuery):
    genes = [g.upper().strip() for g in req.genes[:6]]
    log_query(",".join(genes), "gene")
    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/2.0"}) as client:
        genes_info = await asyncio.gather(*[fetch_ncbi_gene(g, client) for g in genes])
        related = []
        for key, data in CLINICAL_MAP.items():
            overlap = [g for g in genes if g in data["genes"]]
            if overlap:
                related.append({"condition":key.title(),"matching_genes":overlap,
                                 "nutrients":data["msk_slugs"][:4],"drugs":data.get("drugs",[])})
        all_slugs = list(set(s for r in related for s in r["nutrients"][:2]))[:6]
        herbs = [h for h in await asyncio.gather(*[fetch_msk_herb(s,client) for s in all_slugs]) if "error" not in h]
        refs = await search_pubmed(f"{' '.join(genes[:3])} nutrition SNP nutrigenomics clinical", client, n=5)
    return {
        "genes_queried": genes,
        "genes_info": [g for g in genes_info if "error" not in g],
        "related_conditions": related, "supplements": herbs, "references": refs,
        "timestamp": datetime.datetime.now().isoformat()
    }


# ── ENDPOINT 3: SUPLEMENTO ────────────────────────────────────────────────────
@app.post("/api/nutrient")
async def nutrient_analysis(req: NutrientQuery):
    nut = req.nutrient.lower().strip()
    log_query(req.nutrient, "nutrient")
    slug = MSK_SLUGS.get(nut, nut.replace(" ","-"))
    async with httpx.AsyncClient(headers={"User-Agent":"NutriKen/2.0"}) as client:
        # Try direct slug, if fail try translated
        herb = await fetch_msk_herb(slug, client)
        if "error" in herb:
            en = await translate_to_en(nut, client)
            slug2 = MSK_SLUGS.get(en, en.replace(" ","-"))
            if slug2 != slug:
                herb = await fetch_msk_herb(slug2, client)
                if "error" not in herb: slug = slug2
        if "error" in herb:
            raise HTTPException(status_code=404,
                detail=f"'{req.nutrient}' no encontrado en MSK. Prueba: omega-3, vitamin-d, berberine, turmeric, milk-thistle, coenzyme-q10, garlic, green-tea, magnesium, probiotics")

        refs = await search_pubmed(f"{req.nutrient} clinical evidence safety efficacy interaction", client, n=6)
        pathway = {}
        try:
            r = await client.get(f"https://rest.kegg.jp/find/compound/{slug.replace('-','+')}", timeout=6.0)
            lines = r.text.strip().split('\n')
            if lines and lines[0] and '\t' in lines[0]:
                parts = lines[0].split('\t'); cid = parts[0].replace("cpd:","")
                pathway = {"id":cid,"name":parts[1] if len(parts)>1 else slug,"kegg_url":f"https://www.kegg.jp/entry/{cid}"}
        except: pass

    return {"nutrient":req.nutrient,"slug":slug,"msk_data":herb,"pathway":pathway,
            "references":refs,"msk_url":f"https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}",
            "timestamp":datetime.datetime.now().isoformat()}




# ── ENDPOINT 4: GENERACION DE PDF (reportlab, layout A4 nativo) ──────────────
class PDFReportRequest(BaseModel):
    data: dict
    report_id: str = ""
    date: str = ""

@app.post("/api/report-pdf")
async def generate_pdf_report(req: PDFReportRequest):
    """Genera un PDF A4 profesional con todo el texto del informe.
    Usa reportlab (sin dependencias nativas, perfecto para HF Spaces Docker)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
    from reportlab.platypus.flowables import HRFlowable
    from io import BytesIO
    import html as html_module
    import re as re_module

    d = req.data or {}
    report_id = req.report_id or f"NK-{datetime.datetime.now().strftime('%H%M%S')}"
    report_date = req.date or datetime.datetime.now().strftime("%d de %B de %Y")
    condition = d.get("condition", "Consulta")

    def _escape(text):
        if not text: return ""
        text = html_module.escape(str(text))
        text = re_module.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        return text

    def _clean(text, max_len=None):
        if not text: return ""
        text = str(text).strip()
        if max_len and len(text) > max_len:
            text = text[:max_len].rstrip() + "..."
        return _escape(text)

    styles = getSampleStyleSheet()
    NAVY = HexColor("#1a3a6b")
    GRAY = HexColor("#555555")
    LIGHT = HexColor("#f8f9fb")
    TEAL = HexColor("#0d9488")
    GREEN = HexColor("#15803d")
    RED = HexColor("#b91c1c")
    AMBER = HexColor("#d97706")

    h_title = ParagraphStyle("Title", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=22, textColor=black, spaceAfter=6, leading=24)
    h_meta  = ParagraphStyle("Meta", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=GRAY, alignment=TA_RIGHT, leading=12)
    h_section = ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, spaceBefore=16, spaceAfter=8, leading=18)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10, textColor=black, alignment=TA_JUSTIFY, spaceAfter=6, leading=14)
    body_small = ParagraphStyle("BodySmall", parent=body, fontSize=9, leading=12)
    card_title = ParagraphStyle("CardTitle", parent=body, fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, spaceAfter=4)
    ref_style = ParagraphStyle("Ref", parent=body_small, leftIndent=18, firstLineIndent=-18, spaceAfter=8)

    elements = []
    header_data = [[
        Paragraph("INFORME", h_title),
        Paragraph(f"ID: <b>{_escape(report_id)}</b><br/>Fecha: {_escape(report_date)}<br/><font color='#1a3a6b'><b>NutriKen SaaS</b></font>", h_meta)
    ]]
    header_table = Table(header_data, colWidths=[110*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
        ("LINEBELOW", (0,0), (-1,0), 1.5, black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # I. SINTESIS
    elements.append(Paragraph("I. SINTESIS DE INVESTIGACION NUTRICIONAL", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))
    desc = d.get("description") or "Analisis molecular detallado."
    paragraphs = desc.split("\n\n")
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        if p.startswith("•") or "\n• " in p or "\n•" in p:
            lines = [ln.lstrip("• ").strip() for ln in p.split("\n") if ln.strip()]
            bullet_html = "<br/>".join(f"&bull; {_escape(ln)}" for ln in lines)
            elements.append(Paragraph(bullet_html, body))
        else:
            p_clean = _escape(p).replace("\n", "<br/>")
            elements.append(Paragraph(p_clean, body))
        elements.append(Spacer(1, 4))

    # II. BIOMARCADORES
    elements.append(Paragraph("II. PANEL DE BIOMARCADORES GENOMICOS", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))
    genes = d.get("genes", [])
    if genes:
        for g in genes:
            sym = _escape(g.get("symbol", ""))
            name = _escape(g.get("name", ""))
            ncbi = g.get("ncbi_url", "")
            ensembl = g.get("ensembl_url", "")
            card = [
                [Paragraph(f"<b>Biomarcador: {sym}</b>", card_title)],
                [Paragraph(_escape(name), body_small)],
                [Paragraph(f'<font color="#1a3a6b"><link href="{ncbi}">Ficha NCBI</link> &middot; <link href="{ensembl}">Ensembl</link></font>', body_small)]
            ]
            t = Table(card, colWidths=[170*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), LIGHT),
                ("LINEBEFORE", (0,0), (0,-1), 3, NAVY),
                ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
                ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("No se identificaron biomarcadores especificos para esta condicion.", body_small))

    # III. RUTA
    elements.append(Paragraph("III. RUTA METABOLICA RELACIONADA (KEGG)", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))
    pw = d.get("pathway") or {}
    if pw.get("name"):
        pw_card = [
            [Paragraph(f"<b>Ruta Metabolica: {_escape(pw.get('name', ''))}</b>", ParagraphStyle("PwTitle", parent=card_title, textColor=TEAL))],
            [Paragraph(_clean(pw.get("description", ""), 600), body_small)],
            [Paragraph(f'<font color="#0d9488"><link href="{pw.get("kegg_url","")}">Explorar en KEGG</link></font>', body_small)]
        ]
        t = Table(pw_card, colWidths=[170*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), LIGHT),
            ("LINEBEFORE", (0,0), (0,-1), 3, TEAL),
            ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No se identificaron rutas especificas adicionales.", body_small))

    # IV. INTERACCIONES
    elements.append(Paragraph("IV. INTERACCIONES FARMACOLOGICAS", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))

    def _sev_color(tone):
        return {"crit": RED, "warn": AMBER, "info": NAVY}.get(tone, NAVY)
    def _sev_label(tone):
        return {"crit": "CRITICA", "warn": "PRECAUCION", "info": "MONITOREAR"}.get(tone, "MONITOREAR")

    all_ix = list(d.get("drug_alerts", [])) + list(d.get("food_alerts", []))
    if all_ix:
        for a in all_ix:
            tone = a.get("severity_tone", "info")
            color = _sev_color(tone)
            left = a.get("drug") or a.get("food") or ""
            right = a.get("herb", "")
            mech = a.get("mechanism") or a.get("description") or a.get("alert") or "-"
            rec = a.get("recommendation", "-")
            sev_lbl = _sev_label(tone)
            header_row = Table(
                [[Paragraph(f"<b>{_escape(left)}</b> &harr; <b>{_escape(right)}</b>", card_title),
                  Paragraph(f'<font color="#{color.hexval()[2:].upper()}"><b>{sev_lbl}</b></font>', body_small)]],
                colWidths=[120*mm, 50*mm]
            )
            header_row.setStyle(TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("ALIGN", (1,0), (1,0), "RIGHT"),
                ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ]))
            ix_card = [
                [header_row],
                [Paragraph(f"<b>Mecanismo:</b> {_escape(mech)}", body_small)],
                [Paragraph(f"<b>Recomendacion:</b> {_escape(rec)}", body_small)]
            ]
            t = Table(ix_card, colWidths=[170*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), LIGHT),
                ("LINEBEFORE", (0,0), (0,-1), 3, color),
                ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
                ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            elements.append(KeepTogether(t))
            elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("No se detectaron interacciones criticas en este perfil.", body_small))

    # V. SUPLEMENTOS
    elements.append(Paragraph("V. EVIDENCIA DE SUPLEMENTACION (MSKCC)", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))
    supplements = d.get("supplements", [])
    if supplements:
        for s in supplements:
            name = _escape(s.get("name", ""))
            sci = _escape(s.get("scientific_name", ""))
            cs = _clean(s.get("clinical_summary_es") or s.get("clinical_summary", ""), 700)
            moa = _clean(s.get("mechanism_of_action_es") or s.get("mechanism_of_action", ""), 500)
            uses_list = (s.get("purported_uses_es") or s.get("purported_uses")
                         or s.get("benefits_es") or s.get("benefits") or [])
            uses_list = [u for u in uses_list if not re_module.search(r"(used to|usado para):?$", u, re_module.IGNORECASE)][:5]
            uses = _escape(", ".join(uses_list))
            warns_list = s.get("warnings_es") or s.get("warnings") or [""]
            warning = _escape(warns_list[0]) if warns_list and warns_list[0] else ""
            slug = s.get("slug", "")
            title_html = f"<b>{name}</b>" + (f" <i><font size='9' color='#666666'>- {sci}</font></i>" if sci else "")
            rows = [[Paragraph(title_html, ParagraphStyle("SuppT", parent=card_title, textColor=GREEN))]]
            if cs:   rows.append([Paragraph(f"<b>Resumen clinico:</b> {cs}", body_small)])
            if moa:  rows.append([Paragraph(f"<b>Mecanismo:</b> {moa}", body_small)])
            if uses: rows.append([Paragraph(f"<b>Usos respaldados:</b> {uses}", body_small)])
            if warning: rows.append([Paragraph(f"<font color='#b45309'><b>Advertencia:</b> {warning}</font>", body_small)])
            if slug: rows.append([Paragraph(f'<font color="#15803d"><link href="https://www.mskcc.org/cancer-care/integrative-medicine/herbs/{slug}">Ficha completa en MSKCC</link></font>', body_small)])
            t = Table(rows, colWidths=[170*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), LIGHT),
                ("LINEBEFORE", (0,0), (0,-1), 3, GREEN),
                ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
                ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            elements.append(KeepTogether(t))
            elements.append(Spacer(1, 10))

    # VI. BIBLIOGRAFIA
    elements.append(PageBreak())
    elements.append(Paragraph("VI. BIBLIOGRAFIA CIENTIFICA (Vancouver)", h_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=10))
    refs = d.get("references", [])
    if refs:
        for i, r in enumerate(refs, 1):
            authors = _escape(r.get("authors", "Autores no especificados"))
            title = _escape((r.get("title", "") or "").rstrip("."))
            journal = _escape(r.get("journal", ""))
            year = _escape(r.get("year", ""))
            pmid = r.get("pmid", "")
            url = r.get("url", "")
            ref_html = f"<b>{i}.</b> <b>{authors}</b> {title}."
            if journal: ref_html += f" <i>{journal}</i>."
            if year: ref_html += f" {year}."
            if pmid: ref_html += f' <font color="#1a3a6b"><link href="{url}">PMID: {_escape(pmid)}</link></font>.'
            elements.append(Paragraph(ref_html, ref_style))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm,
        title=f"Informe NutriKen - {condition}", author="NutriKen")
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    cond_slug = re_module.sub(r"[^a-z0-9]+", "-", condition.lower()).strip("-")
    filename = f"nutriken-{cond_slug}-{report_id}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ── STATS ─────────────────────────────────────────────────────────────────────
@app.get("/api/stats")
async def stats():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM herb_cache"); h = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gene_cache"); g = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM query_log"); t = c.fetchone()[0]
    c.execute("SELECT query,query_type,timestamp FROM query_log ORDER BY id DESC LIMIT 8")
    recent = c.fetchall(); conn.close()
    return {"herbs_in_cache":h,"genes_in_cache":g,"total_queries":t,
            "recent_queries":[{"query":r[0],"type":r[1],"time":r[2]} for r in recent]}


if __name__ == "__main__":
    uvicorn.run("nutriken_engine:app", host="0.0.0.0", port=7860, reload=False)


