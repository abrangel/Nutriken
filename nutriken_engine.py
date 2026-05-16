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

# MSK slug map
MSK_SLUGS = {
    "omega-3":"fish-oil","omega3":"fish-oil","fish oil":"fish-oil","fish-oil":"fish-oil",
    "vitamin d":"vitamin-d","vitamin-d":"vitamin-d","vitamina d":"vitamin-d",
    "chromium":"chromium","cromo":"chromium",
    "berberine":"berberine","berberina":"berberine",
    "green tea":"green-tea","green-tea":"green-tea","te verde":"green-tea",
    "cinnamon":"cinnamon","canela":"cinnamon",
    "magnesium":"magnesium","magnesio":"magnesium",
    "l-carnitine":"l-carnitine","carnitina":"l-carnitine","carnitine":"l-carnitine",
    "probiotics":"probiotics","probioticos":"probiotics",
    "folic acid":"folic-acid","folic-acid":"folic-acid","folato":"folic-acid","acido folico":"folic-acid",
    "vitamin b12":"vitamin-b12","vitamin-b12":"vitamin-b12","b12":"vitamin-b12",
    "vitamin b6":"vitamin-b6","vitamin-b6":"vitamin-b6","piridoxina":"vitamin-b6",
    "vitamin c":"vitamin-c","vitamin-c":"vitamin-c","vitamina c":"vitamin-c",
    "vitamin e":"vitamin-e","vitamin-e":"vitamin-e","vitamina e":"vitamin-e",
    "zinc":"zinc","selenium":"selenium","selenio":"selenium",
    "turmeric":"turmeric","curcuma":"turmeric","cúrcuma":"turmeric","curcumin":"turmeric",
    "resveratrol":"resveratrol",
    "garlic":"garlic","ajo":"garlic",
    "flaxseed":"flaxseed","linaza":"flaxseed",
    "quercetin":"quercetin","quercetina":"quercetin",
    "aloe vera":"aloe-vera","aloe-vera":"aloe-vera",
    "ginger":"ginger","jengibre":"ginger",
    "melatonin":"melatonin","melatonina":"melatonin",
    "milk thistle":"milk-thistle","milk-thistle":"milk-thistle","cardo mariano":"milk-thistle","silimarina":"milk-thistle","silymarin":"milk-thistle",
    "echinacea":"echinacea","equinacea":"echinacea",
    "ginseng":"ginseng","ashwagandha":"ashwagandha",
    "coenzyme q10":"coenzyme-q10","coenzyme-q10":"coenzyme-q10","coq10":"coenzyme-q10","ubiquinol":"coenzyme-q10",
    "red yeast rice":"red-yeast-rice","red-yeast-rice":"red-yeast-rice","arroz levadura roja":"red-yeast-rice",
    "alpha lipoic acid":"alpha-lipoic-acid","alpha-lipoic-acid":"alpha-lipoic-acid","acido lipoico":"alpha-lipoic-acid",
    "fenugreek":"fenugreek","fenogreco":"fenugreek",
    "artichoke":"artichoke","alcachofa":"artichoke",
    "dandelion":"dandelion","diente de leon":"dandelion",
    "boswellia":"boswellia","glucomannan":"glucomannan",
    "conjugated linoleic acid":"conjugated-linoleic-acid","cla":"conjugated-linoleic-acid",
    "garcinia":"garcinia","gymnema":"gymnema",
    "bitter melon":"bitter-melon","bitter-melon":"bitter-melon",
    "hawthorn":"hawthorn","espino blanco":"hawthorn",
    "hibiscus":"hibiscus","jamaica":"hibiscus",
    "niacin":"niacin","niacina":"niacin",
    "calcium":"calcium","calcio":"calcium",
    "iron":"iron","hierro":"iron",
    "glutamine":"glutamine","glutamina":"glutamine",
    "fish oil":"fish-oil","omega-3":"fish-oil","omega3":"fish-oil","omega 3":"fish-oil","pyruvate":"pyruvate","chitosan":"chitosan",
    "kava":"kava","valerian":"valerian","valeriana":"valerian",
    "5-htp":"5-htp-01","serotonin":"5-htp-01",
    "ginkgo":"ginkgo","ginkgo biloba":"ginkgo",
    "saw palmetto":"saw-palmetto",
    "black cohosh":"black-cohosh",
    "evening primrose":"evening-primrose-oil",
    "dhea":"dhea","melatonin":"melatonin",
}

GENE_DB = {
  "APOE": {
    "symbol": "APOE",
    "gene_id": "348",
    "ensembl_id": "ENSG00000130203",
    "name": "apolipoprotein E",
    "chromosome": "19",
    "location": "19q13.32",
    "summary": "The protein encoded by this gene is a major apoprotein of the chylomicron. It binds to a specific liver and peripheral cell receptor, and is essential for the normal catabolism of triglyceride-rich lipoprotein constituents. Mutations result in familial dysbetalipoproteinemia (type III hyperlipoproteinemia), in which increased plasma cholesterol and triglycerides are the consequence of impaired clearance of chylomicron and VLDL remnants.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/348",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000130203",
    "snpedia_url": "https://www.snpedia.com/index.php/APOE",
    "omim_url": "https://omim.org/search?index=entry&search=APOE"
  },
  "LDLR": {
    "symbol": "LDLR",
    "gene_id": "3949",
    "ensembl_id": "ENSG00000130164",
    "name": "low density lipoprotein receptor",
    "chromosome": "19",
    "location": "19p13.2",
    "summary": "The LDL receptor mediates the endocytosis of cholesterol-rich LDL. Mutations cause familial hypercholesterolemia (FH), an autosomal dominant disorder characterized by elevated LDL and premature cardiovascular disease. Statins upregulate LDLR expression in the liver.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3949",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000130164",
    "snpedia_url": "https://www.snpedia.com/index.php/LDLR",
    "omim_url": "https://omim.org/search?index=entry&search=LDLR"
  },
  "PCSK9": {
    "symbol": "PCSK9",
    "gene_id": "255738",
    "ensembl_id": "ENSG00000169174",
    "name": "proprotein convertase subtilisin/kexin type 9",
    "chromosome": "1",
    "location": "1p32.3",
    "summary": "PCSK9 promotes degradation of the LDL receptor. Loss-of-function variants are associated with reduced LDL and cardiovascular protection. PCSK9 inhibitors (evolocumab, alirocumab) are approved treatments for hypercholesterolemia.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/255738",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000169174",
    "snpedia_url": "https://www.snpedia.com/index.php/PCSK9",
    "omim_url": "https://omim.org/search?index=entry&search=PCSK9"
  },
  "HMGCR": {
    "symbol": "HMGCR",
    "gene_id": "3156",
    "ensembl_id": "ENSG00000197142",
    "name": "3-hydroxy-3-methylglutaryl-CoA reductase",
    "chromosome": "5",
    "location": "5q13.3",
    "summary": "HMG-CoA reductase is the rate-limiting enzyme for cholesterol synthesis. It is the pharmacological target of statins (atorvastatin, rosuvastatin, simvastatin). Inhibition of this enzyme reduces LDL cholesterol. Variants in HMGCR affect statin efficacy and risk of familial hypercholesterolemia.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3156",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000197142",
    "snpedia_url": "https://www.snpedia.com/index.php/HMGCR",
    "omim_url": "https://omim.org/search?index=entry&search=HMGCR"
  },
  "APOB": {
    "symbol": "APOB",
    "gene_id": "338",
    "ensembl_id": "ENSG00000084674",
    "name": "apolipoprotein B",
    "chromosome": "2",
    "location": "2p24.1",
    "summary": "apolipoprotein B. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/338",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000084674",
    "snpedia_url": "https://www.snpedia.com/index.php/APOB",
    "omim_url": "https://omim.org/search?index=entry&search=APOB"
  },
  "APOA5": {
    "symbol": "APOA5",
    "gene_id": "116519",
    "ensembl_id": "ENSG00000110244",
    "name": "apolipoprotein A5",
    "chromosome": "11",
    "location": "11q23.3",
    "summary": "apolipoprotein A5. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/116519",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000110244",
    "snpedia_url": "https://www.snpedia.com/index.php/APOA5",
    "omim_url": "https://omim.org/search?index=entry&search=APOA5"
  },
  "LPL": {
    "symbol": "LPL",
    "gene_id": "4023",
    "ensembl_id": "ENSG00000175445",
    "name": "lipoprotein lipase",
    "chromosome": "8",
    "location": "8p21.3",
    "summary": "lipoprotein lipase. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/4023",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000175445",
    "snpedia_url": "https://www.snpedia.com/index.php/LPL",
    "omim_url": "https://omim.org/search?index=entry&search=LPL"
  },
  "APOC3": {
    "symbol": "APOC3",
    "gene_id": "345",
    "ensembl_id": "ENSG00000110245",
    "name": "apolipoprotein C3",
    "chromosome": "11",
    "location": "11q23.3",
    "summary": "apolipoprotein C3. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/345",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000110245",
    "snpedia_url": "https://www.snpedia.com/index.php/APOC3",
    "omim_url": "https://omim.org/search?index=entry&search=APOC3"
  },
  "FTO": {
    "symbol": "FTO",
    "gene_id": "79068",
    "ensembl_id": "ENSG00000140718",
    "name": "FTO alpha-ketoglutarate dependent dioxygenase",
    "chromosome": "16",
    "location": "16q12.2",
    "summary": "The FTO gene encodes an alpha-ketoglutarate-dependent dioxygenase involved in regulation of fat mass and obesity. Variants in FTO are among the strongest genetic determinants of BMI in genome-wide association studies. FTO regulates energy homeostasis and food intake.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/79068",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000140718",
    "snpedia_url": "https://www.snpedia.com/index.php/FTO",
    "omim_url": "https://omim.org/search?index=entry&search=FTO"
  },
  "MC4R": {
    "symbol": "MC4R",
    "gene_id": "25927",
    "ensembl_id": "ENSG00000166603",
    "name": "melanocortin 4 receptor",
    "chromosome": "18",
    "location": "18q21.32",
    "summary": "melanocortin 4 receptor. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/25927",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000166603",
    "snpedia_url": "https://www.snpedia.com/index.php/MC4R",
    "omim_url": "https://omim.org/search?index=entry&search=MC4R"
  },
  "LEP": {
    "symbol": "LEP",
    "gene_id": "3952",
    "ensembl_id": "ENSG00000174697",
    "name": "leptin",
    "chromosome": "7",
    "location": "7q32.1",
    "summary": "Leptin is a hormone secreted by adipose tissue that regulates energy balance by inhibiting hunger. LEP variants affect leptin levels and obesity risk. Leptin resistance is common in obese individuals despite high leptin levels.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3952",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000174697",
    "snpedia_url": "https://www.snpedia.com/index.php/LEP",
    "omim_url": "https://omim.org/search?index=entry&search=LEP"
  },
  "LEPR": {
    "symbol": "LEPR",
    "gene_id": "3953",
    "ensembl_id": "ENSG00000116678",
    "name": "leptin receptor",
    "chromosome": "1",
    "location": "1p31.3",
    "summary": "leptin receptor. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3953",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000116678",
    "snpedia_url": "https://www.snpedia.com/index.php/LEPR",
    "omim_url": "https://omim.org/search?index=entry&search=LEPR"
  },
  "PPARG": {
    "symbol": "PPARG",
    "gene_id": "5468",
    "ensembl_id": "ENSG00000132170",
    "name": "peroxisome proliferator activated receptor gamma",
    "chromosome": "3",
    "location": "3p25.2",
    "summary": "peroxisome proliferator activated receptor gamma. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/5468",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000132170",
    "snpedia_url": "https://www.snpedia.com/index.php/PPARG",
    "omim_url": "https://omim.org/search?index=entry&search=PPARG"
  },
  "ADIPOQ": {
    "symbol": "ADIPOQ",
    "gene_id": "9370",
    "ensembl_id": "ENSG00000181092",
    "name": "adiponectin, C1Q and collagen domain containing",
    "chromosome": "3",
    "location": "3q27.3",
    "summary": "adiponectin, C1Q and collagen domain containing. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/9370",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000181092",
    "snpedia_url": "https://www.snpedia.com/index.php/ADIPOQ",
    "omim_url": "https://omim.org/search?index=entry&search=ADIPOQ"
  },
  "TCF7L2": {
    "symbol": "TCF7L2",
    "gene_id": "6934",
    "ensembl_id": "ENSG00000148737",
    "name": "transcription factor 7 like 2",
    "chromosome": "10",
    "location": "10q25.2",
    "summary": "TCF7L2 variants are the strongest genetic risk factors for type 2 diabetes identified to date. The gene encodes a transcription factor involved in Wnt signaling and beta-cell function. Risk alleles reduce insulin secretion and increase glucagon levels.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/6934",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000148737",
    "snpedia_url": "https://www.snpedia.com/index.php/TCF7L2",
    "omim_url": "https://omim.org/search?index=entry&search=TCF7L2"
  },
  "KCNJ11": {
    "symbol": "KCNJ11",
    "gene_id": "3767",
    "ensembl_id": "ENSG00000187486",
    "name": "potassium inwardly rectifying channel subfamily J member 11",
    "chromosome": "11",
    "location": "11p15.1",
    "summary": "potassium inwardly rectifying channel subfamily J member 11. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3767",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000187486",
    "snpedia_url": "https://www.snpedia.com/index.php/KCNJ11",
    "omim_url": "https://omim.org/search?index=entry&search=KCNJ11"
  },
  "HNF1A": {
    "symbol": "HNF1A",
    "gene_id": "6927",
    "ensembl_id": "ENSG00000135100",
    "name": "HNF1 homeobox A",
    "chromosome": "12",
    "location": "12q24.31",
    "summary": "HNF1 homeobox A. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/6927",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000135100",
    "snpedia_url": "https://www.snpedia.com/index.php/HNF1A",
    "omim_url": "https://omim.org/search?index=entry&search=HNF1A"
  },
  "ACE": {
    "symbol": "ACE",
    "gene_id": "1636",
    "ensembl_id": "ENSG00000159640",
    "name": "angiotensin I converting enzyme",
    "chromosome": "17",
    "location": "17q23.3",
    "summary": "angiotensin I converting enzyme. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1636",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000159640",
    "snpedia_url": "https://www.snpedia.com/index.php/ACE",
    "omim_url": "https://omim.org/search?index=entry&search=ACE"
  },
  "AGT": {
    "symbol": "AGT",
    "gene_id": "183",
    "ensembl_id": "ENSG00000135744",
    "name": "angiotensinogen",
    "chromosome": "1",
    "location": "1q42.2",
    "summary": "angiotensinogen. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/183",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000135744",
    "snpedia_url": "https://www.snpedia.com/index.php/AGT",
    "omim_url": "https://omim.org/search?index=entry&search=AGT"
  },
  "AGTR1": {
    "symbol": "AGTR1",
    "gene_id": "185",
    "ensembl_id": "ENSG00000144891",
    "name": "angiotensin II receptor type 1",
    "chromosome": "3",
    "location": "3q24",
    "summary": "angiotensin II receptor type 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/185",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000144891",
    "snpedia_url": "https://www.snpedia.com/index.php/AGTR1",
    "omim_url": "https://omim.org/search?index=entry&search=AGTR1"
  },
  "VDR": {
    "symbol": "VDR",
    "gene_id": "7421",
    "ensembl_id": "ENSG00000111424",
    "name": "vitamin D receptor",
    "chromosome": "12",
    "location": "12q13.11",
    "summary": "The vitamin D receptor mediates the action of calcitriol (active vitamin D). VDR variants affect vitamin D absorption, bone metabolism, immune function, and cancer risk. Relevant in supplementation decisions for vitamin D deficiency.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/7421",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000111424",
    "snpedia_url": "https://www.snpedia.com/index.php/VDR",
    "omim_url": "https://omim.org/search?index=entry&search=VDR"
  },
  "CYP27B1": {
    "symbol": "CYP27B1",
    "gene_id": "1594",
    "ensembl_id": "ENSG00000111012",
    "name": "cytochrome P450 family 27 subfamily B member 1",
    "chromosome": "12",
    "location": "12q14.1",
    "summary": "cytochrome P450 family 27 subfamily B member 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1594",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000111012",
    "snpedia_url": "https://www.snpedia.com/index.php/CYP27B1",
    "omim_url": "https://omim.org/search?index=entry&search=CYP27B1"
  },
  "CYP2R1": {
    "symbol": "CYP2R1",
    "gene_id": "120227",
    "ensembl_id": "ENSG00000186104",
    "name": "cytochrome P450 family 2 subfamily R member 1",
    "chromosome": "11",
    "location": "11p15.2",
    "summary": "cytochrome P450 family 2 subfamily R member 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/120227",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000186104",
    "snpedia_url": "https://www.snpedia.com/index.php/CYP2R1",
    "omim_url": "https://omim.org/search?index=entry&search=CYP2R1"
  },
  "MTHFR": {
    "symbol": "MTHFR",
    "gene_id": "4524",
    "ensembl_id": "ENSG00000177000",
    "name": "methylenetetrahydrofolate reductase",
    "chromosome": "1",
    "location": "1p36.22",
    "summary": "Methylenetetrahydrofolate reductase catalyzes the conversion of 5,10-methylenetetrahydrofolate to 5-methyltetrahydrofolate. The C677T variant (rs1801133) reduces enzyme activity by 30-70%, leading to elevated homocysteine. This variant affects folate and vitamin B12 metabolism and is relevant in cardiovascular risk, neural tube defects, and depression.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/4524",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000177000",
    "snpedia_url": "https://www.snpedia.com/index.php/MTHFR",
    "omim_url": "https://omim.org/search?index=entry&search=MTHFR"
  },
  "FOLH1": {
    "symbol": "FOLH1",
    "gene_id": "2346",
    "ensembl_id": "ENSG00000086205",
    "name": "folate hydrolase 1",
    "chromosome": "11",
    "location": "11p11.2",
    "summary": "folate hydrolase 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/2346",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000086205",
    "snpedia_url": "https://www.snpedia.com/index.php/FOLH1",
    "omim_url": "https://omim.org/search?index=entry&search=FOLH1"
  },
  "SLC19A1": {
    "symbol": "SLC19A1",
    "gene_id": "6573",
    "ensembl_id": "ENSG00000173638",
    "name": "solute carrier family 19 member 1",
    "chromosome": "21",
    "location": "21q22.3",
    "summary": "solute carrier family 19 member 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/6573",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000173638",
    "snpedia_url": "https://www.snpedia.com/index.php/SLC19A1",
    "omim_url": "https://omim.org/search?index=entry&search=SLC19A1"
  },
  "TCN2": {
    "symbol": "TCN2",
    "gene_id": "6948",
    "ensembl_id": "ENSG00000185339",
    "name": "transcobalamin 2",
    "chromosome": "22",
    "location": "22q12.2",
    "summary": "transcobalamin 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/6948",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000185339",
    "snpedia_url": "https://www.snpedia.com/index.php/TCN2",
    "omim_url": "https://omim.org/search?index=entry&search=TCN2"
  },
  "MTRR": {
    "symbol": "MTRR",
    "gene_id": "4552",
    "ensembl_id": "ENSG00000124275",
    "name": "5-methyltetrahydrofolate-homocysteine methyltransferase reductase",
    "chromosome": "5",
    "location": "5p15.31",
    "summary": "5-methyltetrahydrofolate-homocysteine methyltransferase reductase. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/4552",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000124275",
    "snpedia_url": "https://www.snpedia.com/index.php/MTRR",
    "omim_url": "https://omim.org/search?index=entry&search=MTRR"
  },
  "MTR": {
    "symbol": "MTR",
    "gene_id": "4548",
    "ensembl_id": "ENSG00000116984",
    "name": "5-methyltetrahydrofolate-homocysteine methyltransferase",
    "chromosome": "1",
    "location": "1q43",
    "summary": "5-methyltetrahydrofolate-homocysteine methyltransferase. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/4548",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000116984",
    "snpedia_url": "https://www.snpedia.com/index.php/MTR",
    "omim_url": "https://omim.org/search?index=entry&search=MTR"
  },
  "FUT2": {
    "symbol": "FUT2",
    "gene_id": "2524",
    "ensembl_id": "ENSG00000176920",
    "name": "fucosyltransferase 2",
    "chromosome": "19",
    "location": "19q13.33",
    "summary": "fucosyltransferase 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/2524",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000176920",
    "snpedia_url": "https://www.snpedia.com/index.php/FUT2",
    "omim_url": "https://omim.org/search?index=entry&search=FUT2"
  },
  "NOD2": {
    "symbol": "NOD2",
    "gene_id": "64127",
    "ensembl_id": "ENSG00000167207",
    "name": "nucleotide binding oligomerization domain containing 2",
    "chromosome": "16",
    "location": "16q12.1",
    "summary": "nucleotide binding oligomerization domain containing 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/64127",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000167207",
    "snpedia_url": "https://www.snpedia.com/index.php/NOD2",
    "omim_url": "https://omim.org/search?index=entry&search=NOD2"
  },
  "PNPLA3": {
    "symbol": "PNPLA3",
    "gene_id": "80339",
    "ensembl_id": "ENSG00000100344",
    "name": "patatin like phospholipase domain containing 3",
    "chromosome": "22",
    "location": "22q13.31",
    "summary": "patatin like phospholipase domain containing 3. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/80339",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000100344",
    "snpedia_url": "https://www.snpedia.com/index.php/PNPLA3",
    "omim_url": "https://omim.org/search?index=entry&search=PNPLA3"
  },
  "TM6SF2": {
    "symbol": "TM6SF2",
    "gene_id": "53345",
    "ensembl_id": "ENSG00000197142",
    "name": "transmembrane 6 superfamily member 2",
    "chromosome": "19",
    "location": "19p13.11",
    "summary": "transmembrane 6 superfamily member 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/53345",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000197142",
    "snpedia_url": "https://www.snpedia.com/index.php/TM6SF2",
    "omim_url": "https://omim.org/search?index=entry&search=TM6SF2"
  },
  "TNF": {
    "symbol": "TNF",
    "gene_id": "7124",
    "ensembl_id": "ENSG00000232810",
    "name": "tumor necrosis factor",
    "chromosome": "6",
    "location": "6p21.33",
    "summary": "tumor necrosis factor. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/7124",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000232810",
    "snpedia_url": "https://www.snpedia.com/index.php/TNF",
    "omim_url": "https://omim.org/search?index=entry&search=TNF"
  },
  "IL6": {
    "symbol": "IL6",
    "gene_id": "3569",
    "ensembl_id": "ENSG00000136244",
    "name": "interleukin 6",
    "chromosome": "7",
    "location": "7p15.3",
    "summary": "interleukin 6. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3569",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000136244",
    "snpedia_url": "https://www.snpedia.com/index.php/IL6",
    "omim_url": "https://omim.org/search?index=entry&search=IL6"
  },
  "IL1B": {
    "symbol": "IL1B",
    "gene_id": "3553",
    "ensembl_id": "ENSG00000125538",
    "name": "interleukin 1 beta",
    "chromosome": "2",
    "location": "2q14.1",
    "summary": "interleukin 1 beta. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3553",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000125538",
    "snpedia_url": "https://www.snpedia.com/index.php/IL1B",
    "omim_url": "https://omim.org/search?index=entry&search=IL1B"
  },
  "CRP": {
    "symbol": "CRP",
    "gene_id": "1401",
    "ensembl_id": "ENSG00000132693",
    "name": "C-reactive protein",
    "chromosome": "1",
    "location": "1q23.2",
    "summary": "C-reactive protein. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1401",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000132693",
    "snpedia_url": "https://www.snpedia.com/index.php/CRP",
    "omim_url": "https://omim.org/search?index=entry&search=CRP"
  },
  "PTGS2": {
    "symbol": "PTGS2",
    "gene_id": "5743",
    "ensembl_id": "ENSG00000073756",
    "name": "prostaglandin-endoperoxide synthase 2",
    "chromosome": "1",
    "location": "1q31.1",
    "summary": "prostaglandin-endoperoxide synthase 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/5743",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000073756",
    "snpedia_url": "https://www.snpedia.com/index.php/PTGS2",
    "omim_url": "https://omim.org/search?index=entry&search=PTGS2"
  },
  "CYP3A4": {
    "symbol": "CYP3A4",
    "gene_id": "1576",
    "ensembl_id": "ENSG00000160868",
    "name": "cytochrome P450 family 3 subfamily A member 4",
    "chromosome": "7",
    "location": "7q22.1",
    "summary": "CYP3A4 is the most abundant cytochrome P450 enzyme in the liver, responsible for metabolizing approximately 50% of drugs. Inhibitors (grapefruit, ketoconazole) increase drug levels. Inducers (rifampin, St. John's Wort) decrease drug levels. Critical for statin metabolism — grapefruit inhibits CYP3A4 and can increase atorvastatin/simvastatin toxicity.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1576",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000160868",
    "snpedia_url": "https://www.snpedia.com/index.php/CYP3A4",
    "omim_url": "https://omim.org/search?index=entry&search=CYP3A4"
  },
  "SLCO1B1": {
    "symbol": "SLCO1B1",
    "gene_id": "10599",
    "ensembl_id": "ENSG00000134538",
    "name": "solute carrier organic anion transporter family member 1B1",
    "chromosome": "12",
    "location": "12p12.1",
    "summary": "Encodes the OATP1B1 transporter, responsible for hepatic uptake of statins. The rs4149056 variant (521T>C) reduces statin uptake and is associated with statin-induced myopathy, particularly with simvastatin. Relevant for pharmacogenomics of lipid-lowering therapy.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/10599",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000134538",
    "snpedia_url": "https://www.snpedia.com/index.php/SLCO1B1",
    "omim_url": "https://omim.org/search?index=entry&search=SLCO1B1"
  },
  "ABCB1": {
    "symbol": "ABCB1",
    "gene_id": "5243",
    "ensembl_id": "ENSG00000085563",
    "name": "ATP binding cassette subfamily B member 1",
    "chromosome": "7",
    "location": "7q21.12",
    "summary": "ATP binding cassette subfamily B member 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/5243",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000085563",
    "snpedia_url": "https://www.snpedia.com/index.php/ABCB1",
    "omim_url": "https://omim.org/search?index=entry&search=ABCB1"
  },
  "FADS1": {
    "symbol": "FADS1",
    "gene_id": "3992",
    "ensembl_id": "ENSG00000149485",
    "name": "fatty acid desaturase 1",
    "chromosome": "11",
    "location": "11q12.2",
    "summary": "fatty acid desaturase 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3992",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000149485",
    "snpedia_url": "https://www.snpedia.com/index.php/FADS1",
    "omim_url": "https://omim.org/search?index=entry&search=FADS1"
  },
  "FADS2": {
    "symbol": "FADS2",
    "gene_id": "9415",
    "ensembl_id": "ENSG00000134824",
    "name": "fatty acid desaturase 2",
    "chromosome": "11",
    "location": "11q12.2",
    "summary": "fatty acid desaturase 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/9415",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000134824",
    "snpedia_url": "https://www.snpedia.com/index.php/FADS2",
    "omim_url": "https://omim.org/search?index=entry&search=FADS2"
  },
  "LCT": {
    "symbol": "LCT",
    "gene_id": "3938",
    "ensembl_id": "ENSG00000115850",
    "name": "lactase",
    "chromosome": "2",
    "location": "2q21.3",
    "summary": "lactase. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/3938",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000115850",
    "snpedia_url": "https://www.snpedia.com/index.php/LCT",
    "omim_url": "https://omim.org/search?index=entry&search=LCT"
  },
  "MCM6": {
    "symbol": "MCM6",
    "gene_id": "4175",
    "ensembl_id": "ENSG00000076003",
    "name": "minichromosome maintenance complex component 6",
    "chromosome": "2",
    "location": "2q21.3",
    "summary": "minichromosome maintenance complex component 6. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/4175",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000076003",
    "snpedia_url": "https://www.snpedia.com/index.php/MCM6",
    "omim_url": "https://omim.org/search?index=entry&search=MCM6"
  },
  "ABCG5": {
    "symbol": "ABCG5",
    "gene_id": "64240",
    "ensembl_id": "ENSG00000138075",
    "name": "ATP binding cassette subfamily G member 5",
    "chromosome": "2",
    "location": "2p21",
    "summary": "ATP binding cassette subfamily G member 5. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/64240",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000138075",
    "snpedia_url": "https://www.snpedia.com/index.php/ABCG5",
    "omim_url": "https://omim.org/search?index=entry&search=ABCG5"
  },
  "ABCG8": {
    "symbol": "ABCG8",
    "gene_id": "64241",
    "ensembl_id": "ENSG00000143921",
    "name": "ATP binding cassette subfamily G member 8",
    "chromosome": "2",
    "location": "2p21",
    "summary": "ATP binding cassette subfamily G member 8. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/64241",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000143921",
    "snpedia_url": "https://www.snpedia.com/index.php/ABCG8",
    "omim_url": "https://omim.org/search?index=entry&search=ABCG8"
  },
  "GCKR": {
    "symbol": "GCKR",
    "gene_id": "2646",
    "ensembl_id": "ENSG00000084734",
    "name": "glucokinase regulator",
    "chromosome": "2",
    "location": "2p23.3",
    "summary": "glucokinase regulator. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/2646",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000084734",
    "snpedia_url": "https://www.snpedia.com/index.php/GCKR",
    "omim_url": "https://omim.org/search?index=entry&search=GCKR"
  },
  "SLC30A8": {
    "symbol": "SLC30A8",
    "gene_id": "169026",
    "ensembl_id": "ENSG00000164756",
    "name": "solute carrier family 30 member 8",
    "chromosome": "8",
    "location": "8q24.11",
    "summary": "solute carrier family 30 member 8. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/169026",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000164756",
    "snpedia_url": "https://www.snpedia.com/index.php/SLC30A8",
    "omim_url": "https://omim.org/search?index=entry&search=SLC30A8"
  },
  "ADD1": {
    "symbol": "ADD1",
    "gene_id": "118",
    "ensembl_id": "ENSG00000087274",
    "name": "adducin 1",
    "chromosome": "4",
    "location": "4p16.3",
    "summary": "adducin 1. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/118",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000087274",
    "snpedia_url": "https://www.snpedia.com/index.php/ADD1",
    "omim_url": "https://omim.org/search?index=entry&search=ADD1"
  },
  "CYP11B2": {
    "symbol": "CYP11B2",
    "gene_id": "1585",
    "ensembl_id": "ENSG00000179142",
    "name": "cytochrome P450 family 11 subfamily B member 2",
    "chromosome": "8",
    "location": "8q24.3",
    "summary": "cytochrome P450 family 11 subfamily B member 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1585",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000179142",
    "snpedia_url": "https://www.snpedia.com/index.php/CYP11B2",
    "omim_url": "https://omim.org/search?index=entry&search=CYP11B2"
  },
  "GC": {
    "symbol": "GC",
    "gene_id": "2638",
    "ensembl_id": "ENSG00000145321",
    "name": "GC, vitamin D binding protein",
    "chromosome": "4",
    "location": "4q13.3",
    "summary": "GC, vitamin D binding protein. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/2638",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000145321",
    "snpedia_url": "https://www.snpedia.com/index.php/GC",
    "omim_url": "https://omim.org/search?index=entry&search=GC"
  },
  "IL23R": {
    "symbol": "IL23R",
    "gene_id": "149233",
    "ensembl_id": "ENSG00000162594",
    "name": "interleukin 23 receptor",
    "chromosome": "1",
    "location": "1p31.3",
    "summary": "interleukin 23 receptor. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/149233",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000162594",
    "snpedia_url": "https://www.snpedia.com/index.php/IL23R",
    "omim_url": "https://omim.org/search?index=entry&search=IL23R"
  },
  "CARD9": {
    "symbol": "CARD9",
    "gene_id": "64170",
    "ensembl_id": "ENSG00000187796",
    "name": "caspase recruitment domain family member 9",
    "chromosome": "9",
    "location": "9q34.3",
    "summary": "caspase recruitment domain family member 9. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/64170",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000187796",
    "snpedia_url": "https://www.snpedia.com/index.php/CARD9",
    "omim_url": "https://omim.org/search?index=entry&search=CARD9"
  },
  "DHFR": {
    "symbol": "DHFR",
    "gene_id": "1719",
    "ensembl_id": "ENSG00000228716",
    "name": "dihydrofolate reductase",
    "chromosome": "5",
    "location": "5q14.1",
    "summary": "dihydrofolate reductase. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/1719",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000228716",
    "snpedia_url": "https://www.snpedia.com/index.php/DHFR",
    "omim_url": "https://omim.org/search?index=entry&search=DHFR"
  },
  "ELOVL2": {
    "symbol": "ELOVL2",
    "gene_id": "54898",
    "ensembl_id": "ENSG00000197142",
    "name": "ELOVL fatty acid elongase 2",
    "chromosome": "6",
    "location": "6p24.2",
    "summary": "ELOVL fatty acid elongase 2. Gen relevante en nutricion clinica y farmacogenetica. Ver NCBI para informacion completa.",
    "ncbi_url": "https://www.ncbi.nlm.nih.gov/gene/54898",
    "ensembl_url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000197142",
    "snpedia_url": "https://www.snpedia.com/index.php/ELOVL2",
    "omim_url": "https://omim.org/search?index=entry&search=ELOVL2"
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
        gene_id TEXT PRIMARY KEY, data TEXT, fetched_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS query_cache (
        query_key TEXT PRIMARY KEY, data TEXT, fetched_at TEXT)""")
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
    cached = cache_get("herb_cache","slug", slug)
    if cached: logger.info(f"💾 Cache MSK: {slug}"); return cached

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
                "kegg_url":f"https://www.kegg.jp/pathway/{pathway_id}",
                "image_url":f"https://www.kegg.jp/kegg/pathway/{pathway_id}/{pathway_id}.png"}
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
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup(): init_db(); logger.info("🌿 NutriKen v2 iniciado")

@app.get("/")
async def root(): return FileResponse("static/index.html")

@app.get("/script.js")
async def js(): return FileResponse("static/script.js")

@app.get("/style.css")
async def css(): return FileResponse("static/style.css")

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


