// ── NUTRIKEN i18n (ES/EN) ──────────────────────────────────────────────────
// Traduce la interfaz sin frameworks: marca elementos con data-i18n / data-i18n-ph
// y llama setLang('en'|'es'). Persiste la elección en localStorage.
(function () {
  const DICT = {
    es: {
      "nav.modules": "Módulos",
      "nav.clinical": "Condición Clínica",
      "nav.gene": "Análisis de Gen",
      "nav.nutrient": "Suplemento / Hierba",
      "nav.plan": "Plan Clínico Nutrigenómico",
      "plan.label": "Plan Clínico Nutrigenómico",
      "plan.hint": "Compila ruta KEGG · genes · dosis · cronograma circadiano · interacciones · SNPs · bibliografía",
      "plan.ph": "ej: diabetes, obesidad, hipertensión, hígado graso…",
      "plan.generate": "Generar plan",
      "plan.download": "Descargar / Imprimir",
      "nav.report_label": "Informe",
      "nav.report": "Editor de Informe",
      "status.active": "SISTEMA ACTIVO",
      "topbar.meta": "NUTRIKEN CLINICAL ENGINE · MSK · NCBI · KEGG",
      "clinical.label": "Consulta Clínica",
      "clinical.hint": "Escribe en lenguaje natural — sin necesidad de conocer bioinformática",
      "clinical.ph": "ej: obesidad, hipertensión, diabetes, déficit vitamina D…",
      "btn.analyze": "Analizar",
      "btn.search": "Buscar",
      "btn.plan": "Plan Clínico",
      "gene.label": "Análisis Genómico",
      "gene.hint": "Ingresa uno o varios genes separados por coma",
      "gene.ph": "ej: MTHFR, VDR, FTO, LCT, APOE…",
      "nutrient.label": "Suplemento / Hierba",
      "nutrient.hint": "Datos en tiempo real desde MSK · 375+ suplementos indexados",
      "nutrient.ph": "ej: omega-3, vitamina D, berberina, cúrcuma…",
      "hb.title": "Catálogo alfabético",
      "hb.filter": "Filtrar por nombre…",
      "hb.select": "Selecciona una letra para ver las hierbas disponibles.",
      "cl.genes": "Genes Involucrados", "cl.pathway": "Ruta Metabólica",
      "cl.supps": "Evidencia Clínica de Suplementos", "cl.refs": "Referencias Científicas",
      "cl.th_title": "Título", "cl.th_auth": "Autores · Revista · Año", "cl.th_link": "Enlace",
      "cl.drug_ix": "Interacciones fármaco-suplemento", "cl.food_ix": "Interacciones con alimentos",
      "cl.kegg_link": "Ver en KEGG",
      "term.ready": "NutriKen iniciado — motor clínico listo.",
      "dosing.title": "Dosis basada en evidencia",
      "dosing.standard": "Dosis estándar",
      "dosing.therapeutic": "Dosis terapéutica",
      "dosing.form": "Forma",
      "dosing.timing": "Cuándo tomar",
      "dosing.ul": "Límite superior",
      "dosing.evidence": "Evidencia",
      "dosing.interactions": "Interacciones",
      "dosing.notes": "Notas clínicas",
      "tag.obesidad": "Obesidad", "tag.perdida_peso": "Pérdida de peso", "tag.diabetes": "Diabetes",
      "tag.hipertension": "Hipertensión", "tag.colesterol": "Colesterol", "tag.trigliceridos": "Triglicéridos",
      "tag.higado_graso": "Hígado graso", "tag.calculos_biliares": "Cálculos biliares",
      "tag.intolerancia_lactosa": "Intolerancia lactosa", "tag.celiaca": "Enfermedad celíaca",
      "tag.vitd": "Déficit Vit. D", "tag.folato": "Déficit Folato", "tag.b12": "Déficit B12",
      "tag.omega3": "Omega-3", "tag.microbiota": "Microbiota", "tag.inflamacion": "Inflamación",
      "lang.toggle": "EN"
    },
    en: {
      "nav.modules": "Modules",
      "nav.clinical": "Clinical Condition",
      "nav.gene": "Gene Analysis",
      "nav.nutrient": "Supplement / Herb",
      "nav.plan": "Nutrigenomic Clinical Plan",
      "plan.label": "Nutrigenomic Clinical Plan",
      "plan.hint": "Compiles KEGG pathway · genes · dosing · circadian schedule · interactions · SNPs · bibliography",
      "plan.ph": "e.g.: diabetes, obesity, hypertension, fatty liver…",
      "plan.generate": "Generate plan",
      "plan.download": "Download / Print",
      "nav.report_label": "Report",
      "nav.report": "Report Editor",
      "status.active": "SYSTEM ACTIVE",
      "topbar.meta": "NUTRIKEN CLINICAL ENGINE · MSK · NCBI · KEGG",
      "clinical.label": "Clinical Query",
      "clinical.hint": "Write in natural language — no bioinformatics knowledge required",
      "clinical.ph": "e.g.: obesity, hypertension, diabetes, vitamin D deficiency…",
      "btn.analyze": "Analyze",
      "btn.search": "Search",
      "btn.plan": "Clinical Plan",
      "gene.label": "Genomic Analysis",
      "gene.hint": "Enter one or more genes separated by comma",
      "gene.ph": "e.g.: MTHFR, VDR, FTO, LCT, APOE…",
      "nutrient.label": "Supplement / Herb",
      "nutrient.hint": "Real-time data from MSK · 375+ supplements indexed",
      "nutrient.ph": "e.g.: omega-3, vitamin D, berberine, turmeric…",
      "hb.title": "Alphabetical catalog",
      "hb.filter": "Filter by name…",
      "hb.select": "Select a letter to see the available herbs.",
      "cl.genes": "Genes Involved", "cl.pathway": "Metabolic Pathway",
      "cl.supps": "Clinical Evidence of Supplements", "cl.refs": "Scientific References",
      "cl.th_title": "Title", "cl.th_auth": "Authors · Journal · Year", "cl.th_link": "Link",
      "cl.drug_ix": "Drug–supplement interactions", "cl.food_ix": "Food interactions",
      "cl.kegg_link": "View on KEGG",
      "term.ready": "NutriKen started — clinical engine ready.",
      "dosing.title": "Evidence-based dosing",
      "dosing.standard": "Standard dose",
      "dosing.therapeutic": "Therapeutic dose",
      "dosing.form": "Form",
      "dosing.timing": "When to take",
      "dosing.ul": "Upper limit",
      "dosing.evidence": "Evidence",
      "dosing.interactions": "Interactions",
      "dosing.notes": "Clinical notes",
      "tag.obesidad": "Obesity", "tag.perdida_peso": "Weight loss", "tag.diabetes": "Diabetes",
      "tag.hipertension": "Hypertension", "tag.colesterol": "Cholesterol", "tag.trigliceridos": "Triglycerides",
      "tag.higado_graso": "Fatty liver", "tag.calculos_biliares": "Gallstones",
      "tag.intolerancia_lactosa": "Lactose intolerance", "tag.celiaca": "Celiac disease",
      "tag.vitd": "Vit. D deficiency", "tag.folato": "Folate deficiency", "tag.b12": "B12 deficiency",
      "tag.omega3": "Omega-3", "tag.microbiota": "Microbiota", "tag.inflamacion": "Inflammation",
      "lang.toggle": "ES"
    }
  };

  let current = localStorage.getItem("nk_lang") || "es";

  function t(key) {
    return (DICT[current] && DICT[current][key]) || (DICT.es[key] || key);
  }

  function apply() {
    document.documentElement.lang = current;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      const k = el.getAttribute("data-i18n");
      const val = t(k);
      if (val) el.textContent = val;
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      const k = el.getAttribute("data-i18n-ph");
      const val = t(k);
      if (val) el.setAttribute("placeholder", val);
    });
    // Títulos de vista bilingües (los usa switchView)
    window.VIEW_TITLES = {
      clinical: t("nav.clinical"), gene: t("nav.gene"),
      nutrient: t("nav.nutrient"), report: t("nav.report")
    };
    const tt = document.getElementById("view-title");
    const active = document.querySelector(".nav-item.active");
    if (tt && active) {
      const id = active.id.replace("nav-", "");
      if (window.VIEW_TITLES[id]) tt.textContent = window.VIEW_TITLES[id];
    }
    const btn = document.getElementById("lang-toggle");
    if (btn) btn.textContent = t("lang.toggle");
  }

  window.setLang = function (lang) {
    current = (lang === "en") ? "en" : "es";
    localStorage.setItem("nk_lang", current);
    apply();
  };
  window.toggleLang = function () { window.setLang(current === "es" ? "en" : "es"); };
  window.getLang = function () { return current; };
  window.nkT = t;

  document.addEventListener("DOMContentLoaded", apply);
})();
