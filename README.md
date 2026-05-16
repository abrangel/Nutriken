# NutriKen — Plataforma Bioinformática Nutricional

**Desarrollado por: Cesar Manzo**
**Especialidad:** Bioinformática Clínica Aplicada a Nutrición | **Estado:** En producción

> NutriKen es una plataforma web que traduce datos bioinformáticos a lenguaje clínico nutricional. Permite a nutricionistas consultar genes, condiciones clínicas y suplementos con evidencia científica en tiempo real desde NCBI, KEGG, SNPedia y el Memorial Sloan Kettering Cancer Center.

🔗 **Aplicación en línea:** [NutriKen en Hugging Face Spaces](https://huggingface.co/spaces/)

---

## ¿Qué hace NutriKen?

NutriKen integra tres módulos de consulta en una sola interfaz:

### Módulo 1 — Condición Clínica (lenguaje natural)
El nutricionista escribe "obesidad", "diabetes", "intolerancia a la lactosa" y la app:
- Identifica los genes involucrados (FTO, MTHFR, LCT, etc.)
- Muestra la ruta metabólica desde KEGG
- Trae evidencia clínica de suplementos desde MSK
- Señala riesgos y efectos adversos reales
- Genera referencias de PubMed

### Módulo 2 — Análisis de Gen
El usuario ingresa genes directamente (MTHFR, VDR, APOE) y obtiene:
- Ficha completa desde NCBI: nombre, cromosoma, función
- Links directos a SNPedia y Ensembl
- Condiciones clínicas relacionadas
- Suplementos con evidencia según MSK

### Módulo 3 — Suplemento / Hierba
Búsqueda directa de cualquier suplemento con datos en tiempo real de MSK:
- Usos clínicos y beneficios
- Efectos adversos
- Contraindicaciones y advertencias
- Interacciones farmacológicas
- Mecanismo de acción
- Resumen clínico para profesionales de salud

---

## Arquitectura

| Componente | Tecnología |
|---|---|
| Backend | FastAPI + Python 3.11 |
| Frontend | HTML/CSS/JS (vanilla) |
| Caché | SQLite (crece con uso) |
| Scraping | BeautifulSoup + httpx |
| Despliegue | Hugging Face Spaces |

## APIs Integradas

| API / Base de datos | Función |
|---|---|
| MSK About Herbs | Evidencia clínica de suplementos, efectos adversos, interacciones |
| NCBI eUtils | Información de genes, función biológica |
| KEGG REST API | Rutas metabólicas, enzimas, genes involucrados |
| SNPedia | Variantes genéticas relevantes en nutrición |
| Ensembl | Estructura genómica, variantes |
| PubMed | Referencias científicas en tiempo real |

## Sistema de Caché

NutriKen no pre-descarga datos. Cada consulta se hace en tiempo real y se guarda en SQLite local:
- Primera consulta: fetch en vivo → guardado en caché
- Consultas siguientes: respuesta instantánea desde caché
- La base de datos crece orgánicamente con el uso

## Instalación Local

```bash
git clone https://github.com/abrangel/NutriKen.git
cd NutriKen
pip install -r requirements.txt
python nutriken_engine.py
# → http://localhost:7860
```

## Uso en el Taller

NutriKen está diseñado para ser la herramienta práctica del taller "Bioinformática para Nutricionistas":

- **Día 1:** Demostración de cómo los genes se conectan con la nutrición
- **Día 2:** Exploración en vivo de NCBI, KEGG, SNPedia desde una sola interfaz
- **Día 3:** Generación de casos clínicos con recomendación nutricional basada en datos

---

*NutriKen Bioinformatics Engine — Cesar Manzo*
*Basado en la arquitectura Kenryu*

