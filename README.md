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

> NutriKen es una plataforma bioinformática diseñada para traducir datos genómicos y evidencia científica a lenguaje clínico nutricional. Integra en tiempo real NCBI, KEGG, SNPedia, Ensembl, PubMed y la base de datos de hierbas del Memorial Sloan Kettering Cancer Center (MSK), sin necesidad de programación.

🔗 **Aplicación en línea:** [NutriKen en Hugging Face Spaces](https://huggingface.co/spaces/Kenryu007/Nutriken)
🔗 **Repositorio GitHub:** [abrangel/Nutriken](https://github.com/abrangel/Nutriken)

---

## ¿Qué es este proyecto?

Los nutricionistas clínicos necesitan interpretar datos genéticos, rutas metabólicas y evidencia de suplementos para diseñar intervenciones personalizadas — pero las herramientas bioinformáticas tradicionales están diseñadas para investigadores con conocimientos de programación.

NutriKen resuelve esto: integra múltiples bases de datos científicas en una sola interfaz accesible, donde el nutricionista puede consultar en lenguaje natural ("obesidad", "déficit vitamina D") o en lenguaje técnico ("MTHFR", "VDR"), y recibe un análisis estructurado listo para aplicar clínicamente.

---

## Cómo funciona — Tres Módulos Integrados

### 🩺 Módulo 1 — Condición Clínica (lenguaje natural)

El nutricionista escribe la condición en lenguaje cotidiano. El sistema identifica automáticamente los genes involucrados, consulta las rutas metabólicas afectadas, trae evidencia clínica de suplementos desde MSK y señala los riesgos reales.

**Ejemplos de consulta:**
- *"obesidad"* → genes FTO, MC4R, LEP → ruta metabólica hsa04920 → omega-3, cromo, berberina → riesgo de cálculos biliares con pérdida rápida de peso
- *"intolerancia a la lactosa"* → gen LCT → déficit calcio/vitamina D → probióticos con evidencia
- *"déficit de folato"* → MTHFR C677T → hiperhomocisteinemia → ácido fólico, B6, B12

### 🔬 Módulo 2 — Análisis de Gen

Para quien maneja terminología técnica. Ingresa uno o varios genes y obtiene:

- Ficha completa desde NCBI: nombre oficial, cromosoma, localización, función biológica
- Variantes SNP relevantes en nutrición (SNPedia)
- Estructura genómica (Ensembl)
- Condiciones clínicas asociadas con sus riesgos
- Suplementos con evidencia según MSK

### 🌿 Módulo 3 — Suplemento / Hierba

Búsqueda directa en la base de datos del Memorial Sloan Kettering en tiempo real:

- Usos clínicos y beneficios con evidencia
- Efectos adversos documentados
- Contraindicaciones y advertencias
- Interacciones farmacológicas
- Mecanismo de acción (sección para profesionales de salud)
- Resumen clínico completo
- Referencias de PubMed relacionadas

---

## Sistema de Caché Inteligente

NutriKen no pre-descarga ni almacena datos masivos. Funciona bajo demanda:

```
Primera consulta → Fetch en tiempo real → Guardado en SQLite local
Consultas siguientes → Respuesta instantánea desde caché
Base de datos crece orgánicamente con el uso
```

Esto garantiza datos siempre actualizados para consultas nuevas y respuesta instantánea para las recurrentes, sin costo de procesamiento previo.

---

## Arquitectura y APIs Integradas

| API / Base de Datos | Función en el sistema |
| --- | --- |
| **MSK About Herbs** | Evidencia clínica de suplementos, efectos adversos, interacciones, mecanismo de acción |
| **NCBI eUtils** | Información genómica: nombre, cromosoma, función biológica, resumen clínico |
| **KEGG REST API** | Rutas metabólicas: enzimas, genes involucrados, diagrama de ruta |
| **SNPedia** | Variantes genéticas (SNPs) relevantes en nutrición personalizada |
| **Ensembl** | Estructura genómica, variantes, expresión génica |
| **PubMed** | Referencias científicas en tiempo real por condición o suplemento |

---

## Condiciones Clínicas Cubieras

| Condición | Genes Clave | Nutrientes con Evidencia |
| --- | --- | --- |
| Obesidad | FTO, MC4R, LEP, LEPR, PPARG | Omega-3, Cromo, Berberina, Té verde |
| Diabetes tipo 2 | TCF7L2, PPARG, KCNJ11 | Berberina, Canela, Magnesio, Vitamina D |
| Intolerancia lactosa | LCT, MCM6 | Probióticos, Calcio, Vitamina D |
| Enfermedad celíaca | HLA-DQ2/DQ8, IL2 | Vitamina D, Folato, B12, Zinc |
| Déficit vitamina D | VDR, CYP27B1, CYP2R1 | Vitamina D, Calcio, Magnesio, Vitamina K |
| Déficit folato | MTHFR, FOLH1, SLC19A1 | Ácido fólico, B12, B6 |
| Déficit B12 | TCN2, MTRR, MTR, FUT2 | Vitamina B12, Folato |
| Microbiota | NOD2, FUT2, IL23R | Probióticos, Prebióticos, Omega-3 |
| Colesterol | APOE, LDLR, PCSK9 | Omega-3, Ajo, Resveratrol, Linaza |
| Inflamación crónica | TNF, IL6, CRP, IL1B | Omega-3, Cúrcuma, Quercetina |

---

## Estructura del Repositorio

```
Nutriken/
├── nutriken_engine.py    # Motor principal (FastAPI + scraping + caché)
├── requirements.txt      # Dependencias mínimas
├── Dockerfile            # Configuración de despliegue
├── index.html            # Interfaz de usuario
├── script.js             # Lógica frontend y renderizado de resultados
├── style.css             # Diseño visual profesional
├── local_db/             # Caché SQLite (generado automáticamente)
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

### Despliegue en Hugging Face Spaces

El proyecto está optimizado para Docker en Hugging Face Spaces. El frontend se sirve directamente desde FastAPI y el backend consulta las APIs externas en tiempo real.

---

## Uso en el Taller de Bioinformática para Nutricionistas

NutriKen está diseñado como herramienta práctica para el taller de 3 días:

| Día | Tema | Uso de NutriKen |
| --- | --- | --- |
| Día 1 | Fundamentos genómicos y nutrigenómica | Demostración de cómo genes se conectan a nutrición |
| Día 2 | Herramientas: NCBI, KEGG, SNPedia | Exploración en vivo desde una sola interfaz |
| Día 3 | Aplicación clínica y casos integradores | Generación de recomendaciones con evidencia |

---

## Contexto Académico

NutriKen fue desarrollado como herramienta educativa y de soporte clínico para nutricionistas que buscan integrar datos genómicos en su práctica. La plataforma cubre los tres días del programa "Bioinformática para Nutricionistas" sin requerir conocimientos de programación, conectando directamente las bases de datos científicas más relevantes del campo.

**Aviso clínico:** Esta plataforma es una herramienta educativa. La información presentada no reemplaza el criterio clínico profesional ni constituye una recomendación médica.

---

*NUTRIKEN Bioinformatics Engine — Cesar Manzo*
*Basado en la arquitectura Kenryu · Especialidad: Análisis Genómico y Bioinformática Clínica*

