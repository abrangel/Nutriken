# NutriKen — Nuevas funciones: Dosis de suplementos + Idioma EN/ES

## 1. Base de DOSIS basada en evidencia (cuánto tomar realmente)
El hueco que pediste cubrir: no solo qué suplemento, sino **cuánto**.

- Nuevo archivo de datos: `local_db/supplement_dosing.json` (43 suplementos/hierbas,
  bilingüe ES/EN). Campos por entrada: dosis estándar, dosis terapéutica, forma,
  cuándo tomar, límite superior (UL), nivel de evidencia, interacciones y notas clínicas.
  Fuentes: EFSA, NIH-ODS, EMA/HMPC, Examine, Cochrane, MSK.
- Generador reproducible: `scripts/build_dosing_db.py` (edítalo para añadir más y
  ejecútalo: `python scripts/build_dosing_db.py`). Así escalas el catálogo fácil.
- Backend (`nutriken_engine.py`):
  - Carga la base al arrancar.
  - Nuevo endpoint `GET /api/dosing?q=<nombre>&lang=es|en` (verificado en vivo).
  - `GET /api/dosing` sin `q` = catálogo completo.
  - La respuesta de `/api/nutrient` ahora incluye `dosing` automáticamente.
- Frontend: en el módulo "Suplemento / Hierba" aparece una tarjeta
  **"Dosis basada en evidencia"** con toda la posología, encima de la ficha MSK.

Cómo añadir más suplementos/hierbas: agrega una fila en `scripts/build_dosing_db.py`
(o directamente en el JSON) y, si el nombre es nuevo, un alias en `_DOSING_ALIASES`
dentro de `nutriken_engine.py`.

## 2. Cambio de idioma ES / EN
- Nuevo archivo: `i18n.js` (diccionario ES/EN + `setLang()` + `toggleLang()`,
  persiste la elección en `localStorage`).
- Botón de idioma (EN/ES) en la barra lateral. Traduce módulos, títulos, hints,
  placeholders, botones y la tarjeta de dosis. Los datos de dosis salen en el idioma
  elegido (campos `_es` / `_en`).
- Servido por el backend en `GET /i18n.js`.

## Archivos tocados
- NUEVOS: `local_db/supplement_dosing.json`, `scripts/build_dosing_db.py`, `i18n.js`
- MODIFICADOS: `index.html`, `script.js`, `style.css`, `nutriken_engine.py`

## Verificación hecha
- `nutriken_engine.py` compila; servidor arranca con tus `requirements.txt`.
- En vivo: `/health`, `/i18n.js`, `/api/dosing?q=berberina&lang=es`,
  `/api/dosing?q=omega-3&lang=en` (campos en inglés + disclaimer EN), catálogo=43.

## Nada roto
No se cambió ningún endpoint existente ni la lógica clínica: solo se AÑADIÓ el
endpoint de dosis, el i18n y la tarjeta. `/api/clinical`, `/api/gene`,
`/api/nutrient`, `/api/report-pdf` siguen igual (nutrient solo gana el campo `dosing`).
