---
title: NutriKen
emoji: 🧬
colorFrom: green
colorTo: teal
sdk: docker
app_port: 7860
pinned: true
---

# NutriKen — Plataforma Bioinformática Nutricional

**Desarrollado por: Cesar Manzo**
**Especialidad:** Bioinformática Clínica Aplicada a Nutrición | **Estado:** En producción

> NutriKen traduce datos bioinformáticos a lenguaje clínico nutricional. Permite a nutricionistas consultar genes, condiciones clínicas y suplementos con evidencia científica en tiempo real desde NCBI, KEGG, SNPedia y el Memorial Sloan Kettering Cancer Center.

## Módulos

### 🩺 Módulo 1 — Condición Clínica
Escribe "obesidad", "diabetes", "intolerancia a la lactosa" y obtén:
- Genes involucrados (NCBI)
- Ruta metabólica (KEGG)
- Evidencia clínica de suplementos (MSK)
- Riesgos y efectos adversos reales
- Referencias PubMed

### 🔬 Módulo 2 — Análisis de Gen
Ingresa MTHFR, VDR, FTO y obtén:
- Ficha completa NCBI
- Links a SNPedia y Ensembl
- Condiciones clínicas relacionadas

### 🌿 Módulo 3 — Suplemento / Hierba
Búsqueda directa en MSK en tiempo real:
- Mecanismo de acción
- Efectos adversos y contraindicaciones
- Interacciones farmacológicas
- Resumen clínico para profesionales

## APIs Integradas

| API | Función |
|---|---|
| MSK About Herbs | Evidencia clínica de suplementos |
| NCBI eUtils | Información de genes |
| KEGG REST API | Rutas metabólicas |
| PubMed | Referencias científicas |

## Arquitectura
- Backend: FastAPI + Python 3.11
- Caché: SQLite (crece con uso, sin costo)
- Frontend: HTML/CSS/JS
- Despliegue: Docker en Hugging Face Spaces

*NutriKen v1.0 — Cesar Manzo | Basado en arquitectura Kenryu*
