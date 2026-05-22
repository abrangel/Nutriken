<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:1a1d24,50:c8a96e,100:1a1d24&text=NUTRIKEN&fontColor=ffffff&fontSize=80&fontAlignY=40&desc=Plataforma%20Bioinform%C3%A1tica%20Nutricional&descAlignY=68&descSize=18&animation=fadeIn" alt="NutriKen banner" width="100%"/>

<p align="center">
  <strong>Plataforma SaaS de bioinformática nutricional clínica para profesionales de la salud</strong><br/>
  <em>Análisis genómico · Evidencia MSK · Interacciones farmacológicas · Informes clínicos profesionales</em>
</p>

<p align="center">
  <a href="https://kenryu007-nutriken.hf.space"><img src="https://img.shields.io/badge/Demo-Hugging%20Face%20Space-c8a96e?style=for-the-badge&logo=huggingface&logoColor=white" alt="Demo"/></a>
  <a href="#-stack-tecnol%C3%B3gico"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="#-stack-tecnol%C3%B3gico"><img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://supabase.com"><img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/hierbas%20indexadas-307-c8a96e?style=flat-square&labelColor=1a1d24" alt="307 hierbas"/>
  <img src="https://img.shields.io/badge/condiciones%20cl%C3%ADnicas-18-4fc3a1?style=flat-square&labelColor=1a1d24" alt="18 condiciones"/>
  <img src="https://img.shields.io/badge/genes%20indexados-100%2B-6eaadc?style=flat-square&labelColor=1a1d24" alt="100+ genes"/>
  <img src="https://img.shields.io/badge/interacciones%20farmaco--hierba-592-f5a623?style=flat-square&labelColor=1a1d24" alt="592 interacciones"/>
  <img src="https://img.shields.io/badge/relaciones%20gen--qu%C3%ADmico-1642-c8a96e?style=flat-square&labelColor=1a1d24" alt="1642 relaciones"/>
  <img src="https://img.shields.io/badge/idioma-Espa%C3%B1ol-e63946?style=flat-square&labelColor=1a1d24" alt="Español"/>
</p>

<p align="center">
  <a href="#-resumen"><b>Resumen</b></a> ·
  <a href="#-caracter%C3%ADsticas-principales"><b>Características</b></a> ·
  <a href="#%EF%B8%8F-arquitectura"><b>Arquitectura</b></a> ·
  <a href="#-instalaci%C3%B3n-local"><b>Instalación</b></a> ·
  <a href="#-api"><b>API</b></a> ·
  <a href="#-bases-de-datos"><b>Bases de datos</b></a> ·
  <a href="#-licencia"><b>Licencia</b></a>
</p>

</div>

---

## 📋 Resumen

**NutriKen** es una plataforma de bioinformática nutricional clínica diseñada para nutricionistas, médicos, farmacéuticos clínicos y educadores en salud. Integra **evidencia clínica del Memorial Sloan Kettering Cancer Center (MSK)**, **NCBI Gene**, **Ensembl**, **KEGG Pathway** y **PubMed/PMC** en un único motor que produce informes profesionales en español sobre la relación entre suplementos, fármacos, genes y condiciones clínicas.

A diferencia de buscadores web genéricos, NutriKen entrega:

- **Mecanismos moleculares concretos** (CYP3A4, AMPK, NF-κB, GLP-1, HMGCR…)
- **Magnitudes de efecto cuantificadas** (no "tiene mayor evidencia" sino "reduce TG 20-30% con 2-4 g/día de EPA+DHA")
- **Interacciones farmacológicas clasificadas por severidad** (crítica / precaución / monitorear) con su mecanismo de acción y recomendación clínica
- **Dosis estudiadas y contraindicaciones explícitas**
- **Bibliografía científica indexada en Vancouver**

> 🌐 **Demo en producción:** [kenryu007-nutriken.hf.space](https://kenryu007-nutriken.hf.space)

---

## ✨ Características principales

### 🔬 Cuatro módulos clínicos

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🩺 Condición Clínica</h4>
      <p>Búsqueda en lenguaje natural por condición (obesidad, hipertensión, diabetes, dislipidemia, déficits vitamínicos…). Devuelve:</p>
      <ul>
        <li>Visión general clínica extensa (~3.000 caracteres)</li>
        <li>Base genética y fisiopatología</li>
        <li>Fármacos disponibles con mecanismo y eficacia</li>
        <li>Suplementos con evidencia, dosis y magnitud de efecto</li>
        <li>Interacciones críticas + advertencias</li>
        <li>Recomendaciones nutricionales</li>
        <li>Genes implicados con enlaces a NCBI, Ensembl, OMIM, SNPedia, ClinGen, GeneCards</li>
        <li>Ruta metabólica KEGG asociada</li>
        <li>6 referencias PubMed</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🧬 Análisis de Gen</h4>
      <p>Análisis molecular de uno o varios genes (MTHFR, VDR, FTO, LCT, APOE…):</p>
      <ul>
        <li>Información genómica completa (Chr, locus, NCBI ID, Ensembl ID)</li>
        <li>Función biológica</li>
        <li>Enlaces directos a 7 bases de datos genómicas</li>
        <li>Condiciones clínicas relacionadas</li>
        <li>Suplementos relevantes</li>
      </ul>
      <h4>🌿 Suplemento / Hierba</h4>
      <p>Catálogo alfabético A–Z de 307 hierbas indexadas:</p>
      <ul>
        <li>Navegador A–Z con conteo por letra</li>
        <li>Filtro en vivo por nombre o nombre científico</li>
        <li>Ficha completa con secciones para pacientes y profesionales</li>
        <li>Hasta 17 interacciones hierba-fármaco por planta</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td colspan="2" valign="top">
      <h4>📄 Editor de Informe Profesional</h4>
      <p>Editor visual estilo cliente clínico que genera automáticamente informes en formato A4 multi-página con paginación inteligente:</p>
      <ul>
        <li><b>6 secciones en romanos:</b> Síntesis de investigación · Biomarcadores genómicos · Ruta metabólica KEGG · Interacciones farmacológicas · Evidencia de suplementación · Bibliografía Vancouver</li>
        <li><b>Paginación A4 recursiva</b> que respeta tarjetas (no las parte entre páginas)</li>
        <li><b>Exportación PDF</b> de calidad clínica (generado en backend con reportlab)</li>
        <li><b>Exportación Markdown.zip</b> con bibliografía Vancouver + datos crudos JSON</li>
      </ul>
    </td>
  </tr>
</table>

### 🎨 Diseño profesional

- **Tema oscuro** con acentos dorados (#C8A96E) y teal (#4FC3A1) — paleta inspirada en interfaces médicas premium
- **Tipografía clínica:** DM Serif Display (cabeceras), DM Sans (cuerpo), IBM Plex Mono (datos técnicos), Spectral (énfasis)
- **Tarjetas separadas por audiencia:** bloque "Para Pacientes" (dorado, lenguaje accesible) + bloque "Para Profesionales de la Salud" (teal, lenguaje técnico)
- **Iconografía FontAwesome** consistente en cada subsección
- **Severidad de interacciones** codificada por color: crítica (rojo) · precaución (ámbar) · monitorear (azul)
- **Responsive grid** y scroll dorado visible

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (HTML/JS/CSS)                        │
│   index.html · script.js · style.css   (single-page application)     │
│   • Navegación SPA · Editor A4 paginado · Exportación PDF/MD-zip     │
│   • Helper _es() para mapeo automático ES/EN                         │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                       HTTP/REST  │  (FastAPI, CORS abierto)
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  BACKEND (Python 3.11 · FastAPI · Uvicorn)           │
│   nutriken_engine.py                                                 │
│  ┌─────────────────┬─────────────────┬──────────────────────────┐    │
│  │  API endpoints  │  Análisis core  │   Generación reportes    │    │
│  │  /api/clinical  │  CLINICAL_MAP   │   /api/report-pdf        │    │
│  │  /api/gene      │  analyze_       │   reportlab A4 nativo    │    │
│  │  /api/nutrient  │   interactions  │   Bibliografía Vancouver │    │
│  │  /api/herbs-    │  DESCRIPTIONS   │                          │    │
│  │   index         │   (18 cond.)    │                          │    │
│  └─────────────────┴─────────────────┴──────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
            │                                              │
            │ httpx REST                          httpx + cache SQLite
            ▼                                              ▼
   ┌──────────────────┐               ┌────────────────────────────────┐
   │  Supabase (PG)   │               │      Fuentes externas          │
   │  307 hierbas en  │               │  • MSK Integrative Medicine    │
   │   español        │               │  • NCBI Gene + Ensembl REST    │
   │  msk_herbs table │               │  • KEGG Pathway API            │
   └──────────────────┘               │  • PubMed/PMC eUtils           │
                                      │  • MyGene.info                 │
                                      └────────────────────────────────┘
            │                                              │
            └──────────────┬───────────────────────────────┘
                           ▼
            ┌──────────────────────────────┐
            │   SQLite local cache         │
            │   • herb_cache · gene_cache  │
            │   • query_log                │
            └──────────────────────────────┘
```

### Decisiones arquitectónicas

| Decisión | Justificación |
|---|---|
| **FastAPI + HTML estático en raíz** | Despliegue ligero en HF Spaces Docker. Sin compilación, sin SSR, sin framework JS. Tiempo de carga < 1s. |
| **Supabase publishable key vía REST httpx directo** | El cliente Python `supabase` 2.3.4 rechaza el formato de clave nuevo (`sb_publishable_...`). El REST API sí la acepta — más simple y sin dependencia extra. |
| **Cache SQLite local** | Reduce llamadas a NCBI eUtils (limitado a 3 req/s sin API key). Persiste entre reinicios del contenedor. |
| **307 hierbas pre-traducidas al español en Supabase** | El scraping en vivo + traducción es lento (~30s por hierba) y consume cuota de Google Translate. La pre-carga permite respuestas en < 200ms. |
| **Fallback MSK scraping** | Si una hierba no está en Supabase, el motor cae al scraping en vivo de MSK (con BeautifulSoup) en lugar de fallar. |
| **Paginación A4 client-side** | Algoritmo recursivo `nkPaginateReport` con `pageStack` que divide secciones respetando tarjetas atómicas. Sin librería externa pesada. |
| **Reportlab para PDF** | Generación server-side de PDF clínicos sin dependencias nativas (no requiere wkhtmltopdf, headless Chrome, etc.). Funciona en cualquier Docker. |

---

## 🛠️ Stack tecnológico

### Backend
- **Python 3.11**
- **FastAPI** 0.109 — framework HTTP asíncrono
- **Uvicorn** 0.27 — servidor ASGI
- **httpx** 0.26 — cliente HTTP asíncrono (Supabase REST + NCBI + KEGG)
- **BeautifulSoup4** + **lxml** — parsing MSK
- **reportlab** 4.0 — generación PDF A4
- **Pydantic** 2.5 — validación de modelos
- **SQLite3** (stdlib) — cache local

### Frontend
- **HTML5 / CSS3 / Vanilla JS** — sin frameworks ni build system
- **FontAwesome 6.4** — iconografía
- **JSZip 3.10** — exportación Markdown comprimido
- **Google Fonts:** DM Serif Display · DM Sans · IBM Plex Mono · Spectral

### Infraestructura
- **Hugging Face Spaces** (Docker SDK) — hosting de producción
- **Supabase PostgreSQL** — base de datos de hierbas en español
- **GitHub** — control de versiones

### Fuentes de datos integradas
- **MSK Integrative Medicine Herbs Database** — evidencia clínica
- **NCBI Gene & PubMed eUtils** — información genómica y bibliográfica
- **Ensembl REST API** — IDs genómicos y variantes
- **KEGG Pathway** — rutas metabólicas
- **MyGene.info** — agregador de IDs genómicos
- **PharmGKB** (1642 relaciones gen-químico, CC BY-SA)
- **Tapirro** (592 interacciones herba-fármaco, EMA/HMPC/ESCOP)

---

## 📦 Instalación local

### Requisitos
- Python 3.11+
- Acceso a internet para consultar fuentes externas
- (Opcional) Cuenta Supabase con la tabla `msk_herbs` poblada

### Pasos

```bash
# 1. Clonar el repo
git clone https://github.com/abrangel/Nutriken.git
cd Nutriken

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Variables de entorno para Supabase
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="sb_publishable_xxxxxxxxxxxx"

# 4. Lanzar el servidor
python nutriken_engine.py
# → http://localhost:7860
```

### Despliegue en Hugging Face Spaces

El `Dockerfile` incluido funciona out-of-the-box. Solo crea un Space tipo Docker, conecta este repo y publica:

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

## 🔌 API

### `POST /api/clinical`
Análisis de condición clínica en lenguaje natural (español o inglés).

```json
{ "query": "obesidad" }
```

Respuesta:
```json
{
  "condition": "Obesity",
  "description": "**Visión general clínica.** La obesidad es una enfermedad crónica...",
  "genes": [{"symbol": "FTO", "name": "...", "ensembl_id": "ENSG...", ...}],
  "pathway": {"id": "hsa04920", "name": "Adipocytokine signaling pathway", ...},
  "supplements": [/* 7 hierbas con todos los campos en español */],
  "drug_alerts": [{"drug": "...", "herb": "...", "severity_tone": "crit|warn|info", ...}],
  "food_alerts": [...],
  "references": [/* 6 PubMed refs */]
}
```

### `POST /api/gene`
Análisis genómico (uno o varios genes separados por coma).

```json
{ "genes": ["MTHFR", "VDR", "FTO"] }
```

### `POST /api/nutrient`
Ficha completa de un suplemento o hierba.

```json
{ "nutrient": "berberina" }
```

### `GET /api/herbs-index`
Devuelve las 307 hierbas agrupadas alfabéticamente. Cacheado 30 min.

```json
{
  "total": 307,
  "letters": ["A", "B", "C", ..., "Z", "#"],
  "by_letter": { "A": [{"slug": "acai-berry", "name": "Acai Berry", ...}, ...] }
}
```

### `POST /api/report-pdf`
Genera un PDF clínico A4 desde el resultado de cualquier endpoint anterior.

```json
{
  "data": { /* respuesta completa de /api/clinical */ },
  "report_id": "NK-ABC123",
  "date": "22 de mayo de 2026"
}
```
Respuesta: `application/pdf` (multi-página, con bibliografía Vancouver).

### `GET /api/stats`
Estadísticas de uso en tiempo real.

### `GET /health`
Health check para monitoreo.

---

## 🗄️ Bases de datos

### Supabase — tabla `msk_herbs` (307 filas en español)

| Columna | Tipo | Descripción |
|---|---|---|
| `slug` | TEXT (PK) | Identificador URL-friendly (`green-tea`, `milk-thistle`…) |
| `name` | TEXT | Nombre común |
| `scientific_name` | TEXT | Nombre científico (binomial) |
| `common_names` | JSONB | Lista de nombres alternativos |
| `what_is_it` | TEXT | Descripción para pacientes |
| `clinical_summary` | TEXT | Resumen clínico técnico |
| `mechanism_of_action` | TEXT | Mecanismo de acción molecular |
| `purported_uses` | JSONB | Usos clínicos respaldados |
| `benefits` | JSONB | Beneficios potenciales (lenguaje paciente) |
| `dosage` | TEXT | Dosis estudiadas |
| `adverse_reactions` | TEXT | Reacciones adversas |
| `contraindications` | TEXT | Contraindicaciones |
| `drug_interactions` | JSONB | Lista de interacciones hierba-fármaco |
| `food_interactions` | JSONB | Interacciones con alimentos |
| `side_effects` | JSONB | Efectos secundarios |
| `warnings` | JSONB | Advertencias críticas |
| `url` | TEXT | Enlace a ficha MSK original |

El esquema completo está en [`supabase_schema.sql`](supabase_schema.sql).

### Cache SQLite local (`nutriken.db`)
- `herb_cache` — respuestas MSK cacheadas
- `gene_cache` — fichas NCBI/Ensembl cacheadas
- `query_log` — auditoría de consultas

---

## 🎯 Ejemplos de uso clínico

| Escenario | Resultado de NutriKen |
|---|---|
| **Paciente con obesidad pierde 2 kg/semana** | Alerta automática: pérdida rápida → riesgo de cálculos biliares. Sugiere UDCA profiláctico 300-600 mg/día. |
| **Paciente toma atorvastatina y bebe jugo de toronja** | Alerta crítica: inhibición CYP3A4 → AUC × 2.5 → riesgo miopatía/rabdomiólisis. Sugiere cambiar a rosuvastatina o pravastatina. |
| **Paciente con diabetes inicia berberina** | Alerta: efecto aditivo con metformina/insulina → riesgo hipoglucemia. Monitorizar glucemia capilar. |
| **Paciente con MTHFR C677T heterocigoto** | Sugiere L-metilfolato (forma activa) en lugar de ácido fólico estándar. Asociar B12. |
| **Vegano estricto con metformina** | Alerta: déficit de B12 frecuente. Recomienda cianocobalamina 1000 µg/día oral. |
| **Paciente pre-cirugía bariátrica** | UDCA profiláctico 300-600 mg/día durante la fase de pérdida rápida. Suplementación basal de micronutrientes. |

---

## 📊 Capacidad actual del motor

```
┌─────────────────────────────────────────────────┐
│  18 condiciones clínicas con análisis extenso   │
│  307 hierbas indexadas en español               │
│  100+ genes con ENSG verificado                 │
│  592 interacciones herba-fármaco (EMA/HMPC)     │
│  1642 relaciones gen-químico (PharmGKB)         │
│  Acceso en vivo a NCBI, Ensembl, KEGG, PubMed   │
└─────────────────────────────────────────────────┘
```

### Condiciones clínicas con análisis profundo

`Obesidad` · `Pérdida de peso` · `Triglicéridos` · `Colesterol` · `Atorvastatina/Estatinas` · `Silimarina` · `Hígado graso` · `Inflamación` · `Hipertensión` · `Diabetes` · `Cálculos biliares` · `Microbiota intestinal` · `Intolerancia a la lactosa` · `Enfermedad celíaca` · `Déficit Vit. D` · `Déficit Folato (MTHFR)` · `Déficit B12`

---

## 👨‍⚕️ Autor

<table>
<tr>
<td valign="top">

**César Manzo**
Creador y arquitecto principal de Kenryu y NutriKen

- 🏥 Bioinformática clínica
- 🧬 Genómica nutricional aplicada
- 💊 Farmacología nutricional
- 📊 Interfaces clínicas profesionales

</td>
<td valign="top">

**Vinculado al proyecto Kenryu**
- Mismo equipo de desarrollo
- Misma identidad visual (oro/teal · dark mode · A4 editor)
- Misma filosofía: bioinformática accesible para profesionales sin formación técnica avanzada

</td>
</tr>
</table>

---

## 📜 Licencia

Este proyecto está disponible bajo la **Licencia MIT** para uso académico y de investigación. Para uso clínico en producción, consulta con el autor.

**Disclaimer médico:** NutriKen es una herramienta de soporte a la decisión clínica. No sustituye el juicio profesional ni la evaluación individualizada del paciente. La evidencia mostrada proviene de fuentes públicas (MSK, NCBI, PubMed) y debe ser verificada por el profesional sanitario antes de cualquier intervención.

---

## 🤝 Contribuir

Las contribuciones son bienvenidas, especialmente en:

- **Traducciones** de fichas MSK adicionales
- **Validación clínica** de las descripciones de condiciones
- **Nuevas interacciones farmacológicas** documentadas en literatura
- **Mejoras de UI/UX**
- **Optimización de performance** del backend

Para contribuir:

```bash
1. Fork del repo
2. Crear rama feature: git checkout -b feature/mi-mejora
3. Commit: git commit -m "feat: descripción clara"
4. Push: git push origin feature/mi-mejora
5. Abrir Pull Request
```

---

<div align="center">

<sub>Construido con cuidado clínico y curiosidad bioinformática · Cesar Manzo · 2026</sub>

<br/>

<a href="https://kenryu007-nutriken.hf.space">
  <img src="https://img.shields.io/badge/▶_ABRIR_DEMO_EN_VIVO-c8a96e?style=for-the-badge&logoColor=white" alt="Demo en vivo"/>
</a>

</div>

