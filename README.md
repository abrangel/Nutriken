<div align="center">

<p align="center">
  <a href="README.es.md">🇪🇸 Leer en Español</a> | 🇬🇧 <b>Read in English</b>
</p>

<img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:1a1d24,50:c8a96e,100:1a1d24&text=NUTRIKEN&fontColor=ffffff&fontSize=80&fontAlignY=40&desc=Clinical%20Nutritional%20Bioinformatics%20Platform&descAlignY=68&descSize=18&animation=fadeIn" alt="NutriKen banner" width="100%"/>

<p align="center">
  <strong>Clinical nutritional bioinformatics SaaS platform for healthcare professionals</strong><br/>
  <em>Genomic Analysis · MSK Evidence · Pharmacological Interactions · Professional Clinical Reports</em>
</p>

<p align="center">
  <a href="https://kenryu007-nutriken.hf.space"><img src="https://img.shields.io/badge/Demo-Hugging%20Face%20Space-c8a96e?style=for-the-badge&logo=huggingface&logoColor=white" alt="Demo"/></a>
  <a href="#%EF%B8%8F-tech-stack"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="#%EF%B8%8F-tech-stack"><img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://supabase.com"><img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/indexed%20herbs-307-c8a96e?style=flat-square&labelColor=1a1d24" alt="307 herbs"/>
  <img src="https://img.shields.io/badge/clinical%20conditions-18-4fc3a1?style=flat-square&labelColor=1a1d24" alt="18 conditions"/>
  <img src="https://img.shields.io/badge/indexed%20genes-100%2B-6eaadc?style=flat-square&labelColor=1a1d24" alt="100+ genes"/>
  <img src="https://img.shields.io/badge/herb--drug%20interactions-592-f5a623?style=flat-square&labelColor=1a1d24" alt="592 interactions"/>
  <img src="https://img.shields.io/badge/gene--chemical%20relations-1642-c8a96e?style=flat-square&labelColor=1a1d24" alt="1642 relations"/>
  <img src="https://img.shields.io/badge/language-English-005b9f?style=flat-square&labelColor=1a1d24" alt="English"/>
</p>

<p align="center">
  <a href="#-overview"><b>Overview</b></a> ·
  <a href="#-key-features"><b>Features</b></a> ·
  <a href="#%EF%B8%8F-architecture"><b>Architecture</b></a> ·
  <a href="#-local-installation"><b>Installation</b></a> ·
  <a href="#-api"><b>API</b></a> ·
  <a href="#-databases"><b>Databases</b></a> ·
  <a href="#-license"><b>License</b></a>
</p>

</div>

---

## 📋 Overview

**NutriKen** is a clinical nutritional bioinformatics platform designed for nutritionists, physicians, clinical pharmacists, and health educators. It integrates **clinical evidence from Memorial Sloan Kettering Cancer Center (MSK)**, **NCBI Gene**, **Ensembl**, **KEGG Pathway**, and **PubMed/PMC** into a single engine that generates professional reports regarding the relationship between supplements, drugs, genes, and clinical conditions.

Unlike generic web search engines, NutriKen delivers:

- **Concrete molecular mechanisms** (CYP3A4, AMPK, NF-κB, GLP-1, HMGCR…)
- **Quantified effect magnitudes** (not just "has higher evidence" but "reduces TG 20-30% with 2-4 g/day of EPA+DHA")
- **Pharmacological interactions classified by severity** (critical / caution / monitor) alongside their mechanism of action and clinical recommendation
- **Studied dosages and explicit contraindications**
- **Scientific bibliography indexed in Vancouver style**

> 🌐 **Live Production Demo:** [kenryu007-nutriken.hf.space](https://kenryu007-nutriken.hf.space)

---

## ✨ Key Features

### 🔬 Four Clinical Modules

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🩺 Clinical Condition</h4>
      <p>Natural language search by condition (obesity, hypertension, diabetes, dyslipidemia, vitamin deficiencies…). Returns:</p>
      <ul>
        <li>Extensive clinical overview (~3,000 characters)</li>
        <li>Genetic basis and pathophysiology</li>
        <li>Available drugs with mechanisms and efficacy</li>
        <li>Supplements with evidence, dosages, and effect magnitude</li>
        <li>Critical interactions + warnings</li>
        <li>Nutritional recommendations</li>
        <li>Implicated genes with links to NCBI, Ensembl, OMIM, SNPedia, ClinGen, GeneCards</li>
        <li>Associated KEGG metabolic pathways</li>
        <li>6 PubMed references</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🧬 Gene Analysis</h4>
      <p>Molecular analysis of one or multiple genes (MTHFR, VDR, FTO, LCT, APOE…):</p>
      <ul>
        <li>Complete genomic info (Chr, locus, NCBI ID, Ensembl ID)</li>
        <li>Biological function</li>
        <li>Direct links to 7 genomic databases</li>
        <li>Related clinical conditions</li>
        <li>Relevant supplements</li>
      </ul>
      <h4>🌿 Supplement / Herb</h4>
      <p>A–Z alphabetical catalog of 307 indexed herbs:</p>
      <ul>
        <li>A–Z navigator with counts per letter</li>
        <li>Live filtering by common or scientific name</li>
        <li>Comprehensive profile with patient and professional sections</li>
        <li>Up to 17 herb-drug interactions per plant</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td colspan="2" valign="top">
      <h4>📄 Professional Report Editor</h4>
      <p>A visual, clinical-client style editor that automatically generates A4 multi-page reports with smart pagination:</p>
      <ul>
        <li><b>6 roman numeral sections:</b> Research Synthesis · Genomic Biomarkers · KEGG Metabolic Pathway · Pharmacological Interactions · Supplementation Evidence · Vancouver Bibliography</li>
        <li><b>Recursive A4 pagination</b> that respects atomic cards (prevents awkward page breaks)</li>
        <li><b>Clinical-grade PDF export</b> (generated server-side via reportlab)</li>
        <li><b>Markdown.zip export</b> including Vancouver bibliography + raw JSON data</li>
      </ul>
    </td>
  </tr>
</table>

### 🎨 Professional Design

- **Dark theme** with gold (#C8A96E) and teal (#4FC3A1) accents — palette inspired by premium medical interfaces
- **Clinical typography:** DM Serif Display (headers), DM Sans (body), IBM Plex Mono (technical data), Spectral (emphasis)
- **Audience-separated cards:** "For Patients" block (gold, accessible language) + "For Healthcare Professionals" block (teal, technical language)
- **Consistent FontAwesome iconography** across subsections
- **Interaction severity color-coded:** critical (red) · caution (amber) · monitor (blue)
- **Responsive grid** and custom visible gold scrollbar

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (HTML/JS/CSS)                        │
│   index.html · script.js · style.css   (single-page application)     │
│   • SPA Navigation · Paginated A4 Editor · PDF/MD-zip Export         │
│   • _es() Helper for automatic ES/EN mapping                         │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                        HTTP/REST │  (FastAPI, Open CORS)
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│               BACKEND (Python 3.11 · FastAPI · Uvicorn)              │
│   nutriken_engine.py                                                 │
│  ┌─────────────────┬─────────────────┬──────────────────────────┐    │
│  │  API endpoints  │  Core Analysis  │     Report Generation    │    │
│  │  /api/clinical  │  CLINICAL_MAP   │   /api/report-pdf        │    │
│  │  /api/gene      │  analyze_       │   Native reportlab A4    │    │
│  │  /api/nutrient  │   interactions  │   Vancouver Bibliography │    │
│  │  /api/herbs-    │  DESCRIPTIONS   │                          │    │
│  │   index         │  (18 cond.)     │                          │    │
│  └─────────────────┴─────────────────┴──────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
            │                                              │
            │ httpx REST                           httpx + SQLite cache
            ▼                                              ▼
   ┌──────────────────┐               ┌────────────────────────────────┐
   │  Supabase (PG)   │               │       External Sources         │
   │  307 Spanish     │               │ • MSK Integrative Medicine     │
   │   herbs          │               │ • NCBI Gene + Ensembl REST     │
   │  msk_herbs table │               │ • KEGG Pathway API             │
   └──────────────────┘               │ • PubMed/PMC eUtils            │
                                      │ • MyGene.info                  │
                                      └────────────────────────────────┘
            │                                              │
            └──────────────┬───────────────────────────────┘
                           ▼
            ┌──────────────────────────────┐
            │       Local SQLite cache     │
            │   • herb_cache · gene_cache  │
            │   • query_log                │
            └──────────────────────────────┘
Architectural DecisionsDecisionJustificationFastAPI + Static HTML at rootLightweight deployment on HF Spaces Docker. No compilation, no SSR, no JS framework. Load time < 1s.Supabase publishable key via direct REST httpxPython client supabase 2.3.4 rejects the new key format (sb_publishable_...). REST API accepts it — simpler with no extra dependencies.Local SQLite CacheReduces NCBI eUtils calls (limited to 3 req/s without API key). Persists across container restarts.307 Pre-translated herbs in SupabaseLive scraping + translation is slow (~30s per herb) and consumes Google Translate quota. Pre-loading allows < 200ms responses.MSK scraping fallbackIf an herb isn't in Supabase, the engine falls back to live MSK scraping (with BeautifulSoup) instead of failing.Client-side A4 PaginationRecursive algorithm nkPaginateReport with pageStack that divides sections respecting atomic cards. No heavy external library.Reportlab for PDFServer-side generation of clinical PDFs without native dependencies (no wkhtmltopdf, headless Chrome, etc. required). Runs on any Docker.🛠️ Tech StackBackendPython 3.11FastAPI 0.109 — asynchronous HTTP frameworkUvicorn 0.27 — ASGI serverhttpx 0.26 — asynchronous HTTP client (Supabase REST + NCBI + KEGG)BeautifulSoup4 + lxml — MSK parsingreportlab 4.0 — A4 PDF generationPydantic 2.5 — model validationSQLite3 (stdlib) — local cachingFrontendHTML5 / CSS3 / Vanilla JS — no frameworks or build systemsFontAwesome 6.4 — iconographyJSZip 3.10 — compressed Markdown exportGoogle Fonts: DM Serif Display · DM Sans · IBM Plex Mono · SpectralInfrastructureHugging Face Spaces (Docker SDK) — production hostingSupabase PostgreSQL — translated herb databaseGitHub — version controlIntegrated Data SourcesMSK Integrative Medicine Herbs Database — clinical evidenceNCBI Gene & PubMed eUtils — genomic and bibliographic informationEnsembl REST API — genomic IDs and variantsKEGG Pathway — metabolic pathwaysMyGene.info — genomic ID aggregatorPharmGKB (1642 gene-chemical relations, CC BY-SA)Tapirro (592 herb-drug interactions, EMA/HMPC/ESCOP)📦 Local InstallationPrerequisitesPython 3.11+Internet access to query external sources(Optional) Supabase account with populated msk_herbs tableStepsBash# 1. Clone the repo
git clone [https://github.com/abrangel/Nutriken.git](https://github.com/abrangel/Nutriken.git)
cd Nutriken

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Supabase environment variables
export SUPABASE_URL="[https://your-project.supabase.co](https://your-project.supabase.co)"
export SUPABASE_KEY="sb_publishable_xxxxxxxxxxxx"

# 4. Launch the server
python nutriken_engine.py
# → http://localhost:7860
Hugging Face Spaces DeploymentThe included Dockerfile works out-of-the-box. Simply create a Docker Space, connect this repo, and publish:DockerfileFROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY nutriken_engine.py index.html script.js style.css ./
EXPOSE 7860
CMD ["python", "nutriken_engine.py"]
🔌 APIPOST /api/clinicalNatural language clinical condition analysis (English or Spanish).JSON{ "query": "obesity" }
Response:JSON{
  "condition": "Obesity",
  "description": "**Clinical overview.** Obesity is a chronic disease...",
  "genes": [{"symbol": "FTO", "name": "...", "ensembl_id": "ENSG...", ...}],
  "pathway": {"id": "hsa04920", "name": "Adipocytokine signaling pathway", ...},
  "supplements": [/* 7 herbs with localized fields */],
  "drug_alerts": [{"drug": "...", "herb": "...", "severity_tone": "crit|warn|info", ...}],
  "food_alerts": [...],
  "references": [/* 6 PubMed refs */]
}
POST /api/geneGenomic analysis (one or multiple comma-separated genes).JSON{ "genes": ["MTHFR", "VDR", "FTO"] }
POST /api/nutrientComplete profile of a supplement or herb.JSON{ "nutrient": "berberine" }
GET /api/herbs-indexReturns 307 herbs grouped alphabetically. Cached 30 min.JSON{
  "total": 307,
  "letters": ["A", "B", "C", ..., "Z", "#"],
  "by_letter": { "A": [{"slug": "acai-berry", "name": "Acai Berry", ...}, ...] }
}
POST /api/report-pdfGenerates an A4 clinical PDF from any of the previous endpoints.JSON{
  "data": { /* full response from /api/clinical */ },
  "report_id": "NK-ABC123",
  "date": "May 22, 2026"
}
Response: application/pdf (multi-page, with Vancouver bibliography).GET /api/statsReal-time usage statistics.GET /healthHealth check for monitoring.🗄️ DatabasesSupabase — msk_herbs table (307 rows)ColumnTypeDescriptionslugTEXT (PK)URL-friendly identifier (green-tea, milk-thistle…)nameTEXTCommon namescientific_nameTEXTScientific (binomial) namecommon_namesJSONBList of alternative nameswhat_is_itTEXTPatient-friendly descriptionclinical_summaryTEXTTechnical clinical summarymechanism_of_actionTEXTMolecular mechanism of actionpurported_usesJSONBClinically backed usesbenefitsJSONBPotential benefits (patient language)dosageTEXTStudied dosagesadverse_reactionsTEXTAdverse reactionscontraindicationsTEXTContraindicationsdrug_interactionsJSONBHerb-drug interactions listfood_interactionsJSONBFood interactionsside_effectsJSONBSide effectswarningsJSONBCritical warningsurlTEXTLink to original MSK profileThe full schema is available in supabase_schema.sql.🎯 Clinical Use CasesScenarioNutriKen OutputPatient with obesity losing 2 kg/weekAutomatic alert: rapid weight loss → gallstone risk. Suggests prophylactic UDCA 300-600 mg/day.Patient on atorvastatin drinks grapefruit juiceCritical alert: CYP3A4 inhibition → AUC × 2.5 → myopathy/rhabdomyolysis risk. Suggests switching to rosuvastatin or pravastatin.Diabetic patient starts berberineAlert: additive effect with metformin/insulin → hypoglycemia risk. Monitor capillary blood glucose.Heterozygous MTHFR C677T patientSuggests L-methylfolate (active form) instead of standard folic acid. Associate with B12.Strict vegan on metforminAlert: frequent B12 deficiency. Recommends oral cyanocobalamin 1000 µg/day.Pre-bariatric surgery patientProphylactic UDCA 300-600 mg/day during rapid loss phase. Baseline micronutrient supplementation.📊 Current Engine CapacityPlaintext┌─────────────────────────────────────────────────┐
│  18 clinical conditions with deep analysis      │
│  307 indexed herbs                              │
│  100+ genes with verified ENSG                  │
│  592 herb-drug interactions (EMA/HMPC)          │
│  1642 gene-chemical relations (PharmGKB)        │
│  Live access to NCBI, Ensembl, KEGG, PubMed     │
└─────────────────────────────────────────────────┘
👨‍⚕️ AuthorCésar ManzoCreator and Lead Architect of Kenryu & NutriKen🏥 Clinical Bioinformatics🧬 Applied Nutritional Genomics💊 Nutritional Pharmacology📊 Professional Clinical InterfacesLinked to the Kenryu ProjectSame development teamSame visual identity (gold/teal · dark mode · A4 editor)Same philosophy: accessible bioinformatics for professionals without advanced technical training📜 LicenseThis project is available under the MIT License for academic and research purposes. For clinical use in production environments, please consult the author.Medical Disclaimer: NutriKen is a clinical decision support tool. It does not substitute professional judgment or individualized patient evaluation. The evidence shown comes from public sources (MSK, NCBI, PubMed) and must be verified by a healthcare professional prior to any intervention.🤝 ContributingContributions are welcome, particularly in:Translations of additional MSK profilesClinical validation of condition descriptionsNew pharmacological interactions documented in literatureUI/UX improvementsBackend performance optimizationTo contribute:Bash1. Fork the repo
2. Create a feature branch: git checkout -b feature/my-improvement
3. Commit: git commit -m "feat: clear description"
4. Push: git push origin feature/my-improvement
5. Open a Pull Request
Built with clinical care and bioinformatic curiosity · Cesar Manzo · 20262. Modificación a tu README.es.md (Versión en Español actual)Para terminar el ecosistema bilingüe, simplemente añade este pequeño bloque justo al inicio de tu actual archivo en español (README.es.md):HTML<p align="center">
  🇪🇸 <b>Leer en Español</b> | <a href="README.md">🇬🇧 Read in English</a>
</p>
