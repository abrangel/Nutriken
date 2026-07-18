# Fuentes de datos y licencias (NutriKen)

Documento de procedencia para revisión (JOSS / evidencia científica). Todo el dato que
se DISTRIBUYE con el software proviene de fuentes abiertas/redistribuibles y se cita.
Las fuentes con licencia restrictiva (DrugBank) se consultan SOLO en tiempo de ejecución
con las credenciales del propio usuario y NO se almacenan ni redistribuyen.

## Datos incluidos en el repositorio (redistribuibles)

| Dato | Archivo | Fuente | Licencia / términos |
|---|---|---|---|
| Dosis de suplementos/hierbas | `local_db/supplement_dosing.json` | EFSA, NIH-ODS, EMA/HMPC, Cochrane, MSK About Herbs (resumen curado) | Valores de dominio público / guías; se citan. Texto curado propio (MIT). |
| PMIDs + citas por suplemento | `local_db/supplement_dosing.json` (`pubmed_pmids`, `reference`) | PubMed / NCBI E-utilities | Datos públicos del gobierno de EE. UU. |
| CID / InChIKey | `local_db/supplement_dosing.json` (`pubchem_cid`, `inchikey`) | PubChem | Dominio público |
| Interacciones hierba–fármaco | `local_db/herb_drug_interactions.json` | EMA/HMPC + literatura (curado con cita `source`) | Curado propio con citas (MIT) |
| Genes PGx | `local_db/pharmgkb_genes_nutrition.json` | PharmGKB (metadatos + enlaces) | CC-BY-SA 4.0 — atribuir PharmGKB |
| Asociaciones gen–nutriente | `local_db/pharmgkb_nutrition.json` | PharmGKB | CC-BY-SA 4.0 — atribuir PharmGKB |
| Índice botánico (planta→fitoquímicos) | `local_db/botanical_index.json` | LOTUS (naturalproducts.net) | **CC0 (dominio público)** — 193 plantas · 32.068 pares planta-compuesto |

## Fuentes consultadas EN VIVO (no se almacenan)

| Fuente | Uso | Términos |
|---|---|---|
| KEGG REST | Rutas metabólicas (Plan Clínico) | Gratis para uso académico; consulta en vivo, sin redistribución |
| MSK About Herbs | Ficha de hierbas | Consulta en vivo |
| OpenTargets | Genes de enfermedad | Datos abiertos |
| ChEMBL | Bioactividad | CC-BY-SA |
| **DrugBank (opcional)** | Interacciones/ficha de fármaco vía MCP | **Licencia NO redistribuible.** Se consulta SOLO con el `DRUGBANK_TOKEN` del usuario, en vivo; NO se descarga ni sube nada al repo. |

## Por qué esto es apto para JOSS
1. El software es open-source (MIT) y NO empaqueta datos con licencia restrictiva.
2. Toda la evidencia distribuida es trazable (PMID/CID/fuente citada).
3. DrugBank se ofrece como integración opcional "trae-tu-propia-clave" — patrón
   estándar y legal; el usuario que tenga suscripción la activa con su token.

## Reproducibilidad
- `scripts/build_dosing_db.py` regenera la base de dosis curada.
- `scripts/enrich_evidence.py` re-consulta PubChem + PubMed y actualiza PMIDs/CID.
Ambos usan solo APIs públicas y respetan el rate-limit de NCBI (usar `NCBI_API_KEY`).

## Descargo
Software para uso en investigación/educación (RUO). No sustituye el criterio clínico.
