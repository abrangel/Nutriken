---
title: NutriKen
emoji: 🧬
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
---

# NUTRIKEN — Plataforma Bioinformática Nutricional

**Desarrollado por: Cesar Manzo**
**Especialidad:** Bioinformática Clínica Aplicada a Nutrición | **Estado:** En producción

> NutriKen es una plataforma bioinformática diseñada para traducir datos genómicos y evidencia científica a lenguaje clínico nutricional. Integra en tiempo real NCBI, KEGG, SNPedia, Ensembl, PubMed y la base de datos de suplementos del Memorial Sloan Kettering Cancer Center (MSK), sin necesidad de programación.

🔗 **Aplicación en línea:** [NutriKen en Hugging Face Spaces](https://huggingface.co/spaces/Kenryu007/Nutriken)
🔗 **Repositorio GitHub:** [abrangel/Nutriken](https://github.com/abrangel/Nutriken)

---

## 📊 Bases de Datos Integradas y Motor Bioinformático

El sistema NutriKen integra múltiples fuentes de datos clínicos y genómicos para proporcionar análisis de alta precisión:

| Base de Datos | Fuente | Contenido | Tamaño / Estado |
| :--- | :--- | :--- | :--- |
| **GENE_DB** | PharmGKB (CC BY-SA) | 100 genes clave con ENSG real, estados VIP y CPIC | 69 KB |
| **herb_drug_interactions** | tapirro (MIT/EMA/ESCOP) | 592 interacciones detalladas hierba-fármaco | 223 KB |
| **pharmgkb_nutrition** | PharmGKB (CC BY-SA) | 1,642 relaciones gen-químico | 313 KB |
| **MSKcc en Vivo** | MSK Scraper | 307 hierbas y suplementos en tiempo real | Caché SQLite |
| **NCBI / PubMed** | E-Utils API | Bibliografía científica y datos genómicos NCBI | Conexión Directa |

---

## 📄 Editor de Informes Profesionales (Estándar A4)

Se ha implementado un nuevo motor de generación de informes basado en el estándar científico de Bioinformática:
- **Paginación A4 Real:** El informe se visualiza y divide automáticamente en hojas físicas para una presentación impecable.
- **Contenido Técnico Detallado:** Incluye síntesis de investigación, panel de biomarcadores core con descripción de funciones, interacciones farmacológicas y evidencia clínica.
- **Hipervínculos Dinámicos:** El PDF generado incluye enlaces funcionales a fichas NCBI, Ensembl, MSKcc y PubMed.
- **Exportación de Alta Calidad:** Generación de PDF optimizado con un solo clic conservando el formato científico.

---

## Cómo funciona — Tres Módulos Integrados

### 🩺 Módulo 1 — Condición Clínica (lenguaje natural)

El nutricionista escribe la condición en lenguaje cotidiano. El sistema identifica automáticamente los genes involucrados, consulta las rutas metabólicas afectadas, trae evidencia clínica de suplementos desde MSK y señala los riesgos reales.

### 🔬 Módulo 2 — Análisis de Gen

Para quien maneja terminología técnica. Ingresa uno o varios genes y obtiene fichas completas, variantes SNP relevantes (SNPedia), estructura genómica (Ensembl) y condiciones asociadas.

### 🌿 Módulo 3 — Suplemento / Hierba

Búsqueda directa en la base de datos del Memorial Sloan Kettering en tiempo real con resúmenes técnicos de seguridad, eficacia y mecanismos de acción.

---

## Arquitectura y Estructura del Repositorio

```
Nutriken/
├── nutriken_engine.py    # Motor principal (FastAPI + scraping + caché)
├── requirements.txt      # Dependencias (aiofiles, lxml, bs4, etc.)
├── Dockerfile            # Configuración de despliegue producción
├── static/               # Interfaz de Usuario
│   ├── index.html        # Estructura del Dashboard y Editor
│   ├── script.js         # Lógica de APIs y Motor de Reportes
│   └── style.css         # Diseño visual Gold/Dark y Estilos PDF
├── local_db/             # Bases de datos JSON y Caché SQLite
└── README.md             # Documentación
```

---

## Instalación y Ejecución Local

### Requisitos
- Python 3.11 o superior
- pip

### Instalación

```bash
git clone https://github.com/abrangel/Nutriken.git
cd Nutriken
pip install -r requirements.txt
python nutriken_engine.py
```

Acceso: `http://localhost:7860`

---

**Aviso clínico:** Esta plataforma es una herramienta educativa. La información presentada no reemplaza el criterio clínico profesional ni constituye una recomendación médica.

---
*NUTRIKEN Bioinformatics Engine — Cesar Manzo*
*Basado en la arquitectura Kenryu · Especialidad: Análisis Genómico y Bioinformática Clínica*
