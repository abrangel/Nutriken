<div align="center">

<p align="center">
  <a href="README.es.md">🇪🇸 Leer en Español</a> &nbsp;|&nbsp; 🇬🇧 <b>Read in English</b>
</p>

<img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:1a1d24,50:c8a96e,100:1a1d24&text=NUTRIKEN&fontColor=ffffff&fontSize=80&fontAlignY=40&desc=Clinical%20Nutritional%20Bioinformatics%20Platform&descAlignY=68&descSize=18&animation=fadeIn" alt="NutriKen banner" width="100%"/>

<p align="center">
  <strong>Clinical nutritional bioinformatics SaaS platform for healthcare professionals</strong><br/>
  <em>Genomic Analysis · MSK Evidence · Pharmacological Interactions · Professional Clinical Reports</em>
</p>

<!-- ACTION BADGES -->
<p align="center">
  <a href="https://kenryu007-nutriken.hf.space" target="_blank">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Live%20Demo-Hugging%20Face-c8a96e?style=for-the-badge" alt="Demo"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://www.bestpractices.dev/projects/13117" target="_blank">
    <img src="https://www.bestpractices.dev/projects/13117/badge" alt="OpenSSF Best Practices" />
  </a>
</p>

<!-- TECH BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white&labelColor=1a1d24"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white&labelColor=1a1d24"/>
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white&labelColor=1a1d24"/>
  <img src="https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square&labelColor=1a1d24"/>
</p>

<!-- DATA METRICS -->
<p align="center">
  <img src="https://img.shields.io/badge/indexed%20herbs-307-c8a96e?style=flat-square&labelColor=1a1d24" alt="307 herbs"/>
  <img src="https://img.shields.io/badge/clinical%20conditions-18-4fc3a1?style=flat-square&labelColor=1a1d24" alt="18 conditions"/>
  <img src="https://img.shields.io/badge/indexed%20genes-100%2B-6eaadc?style=flat-square&labelColor=1a1d24" alt="100+ genes"/>
  <img src="https://img.shields.io/badge/herb--drug%20interactions-592-f5a623?style=flat-square&labelColor=1a1d24" alt="592 interactions"/>
  <img src="https://img.shields.io/badge/gene--chemical%20relations-1642-c8a96e?style=flat-square&labelColor=1a1d24" alt="1642 relations"/>
</p>

<!-- NAVIGATION -->
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
## ⚠️ Medical Disclaimer & Safety Note
NutriKen is intended for clinical education and decision support. It does not replace professional medical judgment, individualized patient evaluation, local clinical guidelines, or review by a qualified healthcare professional. The evidence shown by the system is sourced from public databases (MSKCC, NCBI, PubMed) and must be rigorously verified by the clinician before any therapeutic or nutritional intervention. 

*   **Regulatory Status:** NutriKen is for **Research Use Only (RUO)**. Not for use in diagnostic or therapeutic procedures.
*   **Data Privacy:** The platform operates as a decision-support utility and does not store or process patient-identifiable information (PII) or protected health information (PHI).
*   **Infrastructure Note:** Deployed and hosted on Hugging Face Spaces
  
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

#### 🧬 Real-World Genomic Analysis Scenario (Genomics vs. Variant-Level)
The clinical engine resolves both broad phenotypic natural language terms and specific Single Nucleotide Polymorphisms (SNPs) synchronously, mapping the entire biological cascade without hardcoded limits:

* **User Input:** `rs9939609` (The high-risk genetic variant for adiposity)
* **Dynamic Locus Resolution:** Automatically maps to FTO (Chr16 · ENSG00000140718)
* **Polygenic Network Expansion:** Interrogates co-expression and triggers cascading parallel lookups for interacting nodes: MC4R, LEP, LEPR, and PPARG.
* **Functional Annotation:** Integrates directly with KEGG Pathway hsa04920 (Adipocytokine signaling pathway - Homo sapiens).
* **Clinical Output:** Generates targeted MSK-backed supplement evidence with quantified effect magnitudes and custom multi-page A4 print layout.

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
```
### Architectural Decisions

| Decision | Justification |
|---|---|
| **FastAPI + static HTML in root** | Lightweight deployment on HF Spaces Docker. No compilation, no SSR, no JS framework. Load time < 1s. |
| **Supabase publishable key via direct REST httpx** | The `supabase` Python client 2.3.4 rejects the new key format (`sb_publishable_...`). The REST API accepts it — simpler and no extra dependency. |
| **Local SQLite cache** | Reduces calls to NCBI eUtils (limited to 3 req/s without API key). Persists across container restarts. |
| **307 pre-translated herbs in Supabase** | Live scraping + translation is slow (~30s per herb) and consumes Google Translate quota. Pre-loading enables responses < 200ms. |
| **MSK scraping fallback** | If an herb is not in Supabase, the engine falls back to live scraping from MSK (with BeautifulSoup) instead of failing. |
| **A4 client-side pagination** | Recursive `nkPaginateReport` algorithm with `pageStack` that splits sections while respecting atomic cards. No heavy external library. |
| **Reportlab for PDF** | Server-side clinical PDF generation without native dependencies (no wkhtmltopdf, headless Chrome, etc.). Works on any Docker. |

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11**
- **FastAPI** 0.109 — asynchronous HTTP framework
- **Uvicorn** 0.27 — ASGI server
- **httpx** 0.26 — asynchronous HTTP client (Supabase REST + NCBI + KEGG)
- **BeautifulSoup4** + **lxml** — MSK parsing
- **reportlab** 4.0 — A4 PDF generation
- **Pydantic** 2.5 — model validation
- **SQLite3** (stdlib) — local cache

### Frontend
- **HTML5 / CSS3 / Vanilla JS** — no frameworks or build system
- **FontAwesome 6.4** — iconography
- **JSZip 3.10** — compressed Markdown export
- **Google Fonts:** DM Serif Display · DM Sans · IBM Plex Mono · Spectral

### Infrastructure
- **Hugging Face Spaces** (Docker SDK) — production hosting
- **Supabase PostgreSQL** — Spanish herb database
- **GitHub** — version control

### Integrated Data Sources
- **MSK Integrative Medicine Herbs Database** — clinical evidence
- **NCBI Gene & PubMed eUtils** — genomic and bibliographic information
- **Ensembl REST API** — genomic IDs and variants
- **KEGG Pathway** — metabolic routes
- **MyGene.info** — genomic ID aggregator
- **PharmGKB** (1,642 gene–chemical relationships, CC BY-SA)
- **Tapirro** (592 herb–drug interactions, EMA/HMPC/ESCOP)

---

## 📦 Local Installation

### Requirements
- Python 3.11+
- Internet access to query external sources
- (Optional) Supabase account with populated `msk_herbs` table

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/abrangel/Nutriken.git
cd Nutriken

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Environment variables for Supabase
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="sb_publishable_xxxxxxxxxxxx"

# 4. Launch the server
python nutriken_engine.py
# → http://localhost:7860
```

### Deploy to Hugging Face Spaces
The included Dockerfile works out-of-the-box. Just create a Docker Space, connect this repo, and publish:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY nutriken_engine.py index.html script.js style.css ./
EXPOSE 7860
CMD ["python", "nutriken_engine.py"]
```
---

##🔌 API

### POST /api/clinical
Analyzes a clinical condition in natural language (Spanish or English).

```json
{ "query": "obesity" }
```

Response:

```json
{
  "condition": "Obesity",
  "description": "**Clinical overview.** Obesity is a chronic disease...",
  "genes": [{"symbol": "FTO", "name": "...", "ensembl_id": "ENSG...", ...}],
  "pathway": {"id": "hsa04920", "name": "Adipocytokine signaling pathway", ...},
  "supplements": [/* 7 herbs with all fields in Spanish */],
  "drug_alerts": [{"drug": "...", "herb": "...", "severity_tone": "crit|warn|info", ...}],
  "food_alerts": [...],
  "references": [/* 6 PubMed refs */]
}
```

### POST /api/gene
Genomic analysis (one or more comma-separated genes).

```json
{ "genes": ["MTHFR", "VDR", "FTO"] }
```

### POST /api/nutrient
Complete profile of a supplement or herb.

```json
{ "nutrient": "berberine" }
```

### GET /api/herbs-index
Returns the 307 herbs grouped alphabetically. Cached for 30 minutes.

```json
{
  "total": 307,
  "letters": ["A", "B", "C", ..., "Z", "#"],
  "by_letter": { "A": [{"slug": "acai-berry", "name": "Acai Berry", ...}, ...] }
}
```

### POST /api/report-pdf
Generates an A4 clinical PDF from the result of any previous endpoint.

```json
{
  "data": { /* full response from /api/clinical */ },
  "report_id": "NK-ABC123",
  "date": "May 22, 2026"
}
```

Response: application/pdf (multi-page, Vancouver bibliography).

### GET /api/stats
Real-time usage statistics.

### GET /health
Health check for monitoring.

---

## 🗄️ Databases
### Supabase — msk_herbs table (307 rows in Spanish)

| Column | Type | Description |
|---|---|---|
| `slug` | TEXT (PK) | URL-friendly identifier (`green-tea`, `milk-thistle`…) |
| `name` | TEXT | Common name |
| `scientific_name` | TEXT | Scientific name (binomial) |
| `common_names` | JSONB | List of alternative names |
| `what_is_it` | TEXT | Description for patients |
| `clinical_summary` | TEXT | Technical clinical summary |
| `mechanism_of_action` | TEXT | Molecular mechanism of action |
| `purported_uses` | JSONB | Supported clinical uses |
| `benefits` | JSONB | Potential benefits (patient language) |
| `dosage` | TEXT | Studied doses |
| `adverse_reactions` | TEXT | Adverse reactions |
| `contraindications` | TEXT | Contraindications |
| `drug_interactions` | JSONB | List of herb–drug interactions |
| `food_interactions` | JSONB | Food interactions |
| `side_effects` | JSONB | Side effects |
| `warnings` | JSONB | Critical warnings |
| `url` | TEXT | Link to original MSK monograph |

The full schema is in [`supabase_schema.sql`](supabase_schema.sql).

### Local SQLite cache (`nutriken.db`)
- `herb_cache` — cached MSK responses
- `gene_cache` — cached NCBI/Ensembl records
- `query_log` — query audit log

---

## 🎯 Clinical Use Examples

| Scenario | NutriKen Output |
|---|---|
| **Patient with obesity loses 2 kg/week** | Automatic alert: rapid loss → risk of gallstones. Suggests prophylactic UDCA 300-600 mg/day. |
| **Patient takes atorvastatin and drinks grapefruit juice** | Critical alert: CYP3A4 inhibition → AUC × 2.5 → risk of myopathy/rhabdomyolysis. Suggests switching to rosuvastatin or pravastatin. |
| **Patient with diabetes starts berberine** | Alert: additive effect with metformin/insulin → risk of hypoglycemia. Monitor capillary glucose. |
| **Patient with MTHFR C677T heterozygous** | Suggests L-methylfolate (active form) instead of standard folic acid. Pair with B12. |
| **Strict vegan on metformin** | Alert: frequent B12 deficiency. Recommends cyanocobalamin 1000 µg/day oral. |
| **Pre-bariatric surgery patient** | Prophylactic UDCA 300-600 mg/day during rapid loss phase. Baseline micronutrient supplementation. |

---

## 📊 Current Engine Capabilities

```
┌─────────────────────────────────────────────────┐
│ 18 clinical conditions with extensive analysis  │
│ 307 herbs indexed in Spanish                    │
│ 100+ genes with verified ENSG                   │
│ 592 herb–drug interactions (EMA/HMPC)           │
│ 1,642 gene–chemical relationships (PharmGKB)    │
│ Live access to NCBI, Ensembl, KEGG, PubMed      │
└─────────────────────────────────────────────────┘
```

### Clinical Conditions with Deep Analysis

`Obesity` · `Weight loss` · `Triglycerides` · `Cholesterol` · `Atorvastatin/Statins` · `Silymarin` · `Fatty liver` · `Inflammation` · `Hypertension` · `Diabetes` · `Gallstones` · `Gut microbiota` · `Lactose intolerance` · `Celiac disease` · `Vitamin D deficiency` · `Folate deficiency (MTHFR)` · `B12 deficiency`

---

## 👨‍⚕️ Author

<table>
<tr>
<td valign="top">

**César Manzo**
Creator and lead architect of Kenryu and NutriKen

- 🏥 Clinical bioinformatics
- 🧬 Applied nutritional genomics
- 💊 Nutritional pharmacology
- 📊 Professional clinical interfaces

</td>
<td valign="top">

**Connected to the Kenryu project**
- Same development team
- Same visual identity (gold/teal · dark mode · A4 editor)
- Same philosophy: accessible bioinformatics for professionals without advanced technical training

</td>
</tr>
</table>

---

## 📜 License

This project is available under the **MIT License** for academic and research use. For clinical production use, please consult the author.

**Medical disclaimer:** NutriKen is a clinical decision support tool. It does not replace professional judgment or individual patient evaluation. The evidence shown comes from public sources (MSK, NCBI, PubMed) and must be verified by the healthcare professional before any intervention.

---

## 🤝 Contributing

Contributions are welcome, especially in:

- **Translations** of additional MSK monographs
- **Clinical validation** of condition descriptions
- **New drug interactions** documented in literature
- **UI/UX improvements**
- **Backend performance optimizations**

To contribute:

```bash
1. Fork the repo
2. Create a feature branch: git checkout -b feature/my-improvement
3. Commit: git commit -m "feat: clear description"
4. Push: git push origin feature/my-improvement
5. Open a Pull Request
```

---
<div align="center">
<sub>Built with clinical care and bioinformatic curiosity · Cesar Manzo · 2026</sub>

<br/>

<a href="https://abrangel.github.io/Nutriken/">
  <img src="https://img.shields.io/badge/▶_OPEN_LIVE_DEMO-c8a96e?style=for-the-badge&logoColor=white" alt="Live demo"/>
</a>

</div>


