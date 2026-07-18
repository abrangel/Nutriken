"""
Genera local_db/drug_timing.json — CRONOTERAPIA de fármacos (a qué hora y por qué).
Basado en farmacocinética y estudios de cronoterapia publicados. Bilingüe ES/EN.
Ejecutar:  python scripts/build_drug_timing.py
"""
import json, os

# fila: key, name, class_es, class_en, timing_es, timing_en, why_es, why_en, warn_es, warn_en, evidence
R = [
("metformin","Metformina","Antidiabético (biguanida)","Antidiabetic (biguanide)",
 "Con las comidas (nunca en ayunas)","With meals (never fasting)",
 "Tomar con comida reduce náuseas/diarrea. Esquema 2×/día: desayuno + almuerzo. Inicio progresivo 500 mg→1 g→2 g.",
 "With food reduces nausea/diarrhea. 2×/day: breakfast + lunch. Titrate 500 mg→1 g→2 g.",
 "Nunca en ayunas. Deplece B12 con uso crónico (revisar cada 12 meses). Separar 2 h de fibra suplementada.",
 "Never fasting. Depletes B12 with chronic use (check yearly). Separate 2 h from supplemental fiber.","Clínico"),
("simvastatin","Simvastatina","Estatina","Statin",
 "Noche (obligatorio)","Night (mandatory)",
 "Vida media corta (~2 h); la síntesis hepática de colesterol pica de noche → noche es más efectiva.",
 "Short half-life (~2 h); hepatic cholesterol synthesis peaks at night → night is more effective.",
 "Evitar toronja (CYP3A4). Vigilar mialgia/CK. Separar de dosis altas de niacina.",
 "Avoid grapefruit (CYP3A4). Monitor myalgia/CK. Separate from high-dose niacin.","Clínico"),
("atorvastatin","Atorvastatina","Estatina","Statin",
 "Cualquier hora (preferible noche)","Any time (night preferred)",
 "Vida media larga (~14 h): flexible, aunque la noche sigue siendo ligeramente superior.",
 "Long half-life (~14 h): flexible, though night is slightly better.",
 "CYP3A4: cuidado con toronja y levadura roja de arroz. Vigilar CK si mialgia.",
 "CYP3A4: caution with grapefruit and red yeast rice. Monitor CK if myalgia.","Clínico"),
("rosuvastatin","Rosuvastatina","Estatina","Statin",
 "Cualquier hora","Any time",
 "Vida media ~19 h: horario flexible, sin ventaja nocturna clara.",
 "Half-life ~19 h: flexible timing, no clear night advantage.",
 "Menos interacción CYP3A4. Vigilar función renal a dosis altas.",
 "Less CYP3A4 interaction. Monitor renal function at high doses.","Clínico"),
("levothyroxine","Levotiroxina","Hormona tiroidea","Thyroid hormone",
 "En ayunas, 30–60 min antes del desayuno","Fasting, 30–60 min before breakfast",
 "La comida, el café y minerales reducen su absorción. Alternativa: al acostarse (≥3 h tras cenar).",
 "Food, coffee and minerals reduce absorption. Alternative: at bedtime (≥3 h after dinner).",
 "SEPARAR 4 h de calcio, hierro, magnesio y del café. Ajustar con TSH.",
 "SEPARATE 4 h from calcium, iron, magnesium and coffee. Titrate by TSH.","Clínico"),
("losartan","Losartán / antihipertensivos","Antihipertensivo (ARA-II)","Antihypertensive (ARB)",
 "Dippers: mañana · No-dippers: noche","Dippers: morning · Non-dippers: night",
 "En no-dippers (PA nocturna alta en MAPA), la dosis vespertina mejora el control circadiano (estudios de cronoterapia).",
 "In non-dippers (high nocturnal BP on ABPM), evening dosing improves circadian control (chronotherapy studies).",
 "Verificar con MAPA 24 h antes de mover a la noche. Vigilar potasio (IECA/ARA-II).",
 "Confirm with 24 h ABPM before switching to night. Monitor potassium (ACEi/ARB).","Clínico (cronoterapia)"),
("enalapril","Enalapril / IECA","Antihipertensivo (IECA)","Antihypertensive (ACEi)",
 "No-dippers: noche","Non-dippers: night",
 "IECA vespertino convierte a muchos no-dippers en dippers (mejor perfil circadiano de PA).",
 "Evening ACEi converts many non-dippers to dippers (better circadian BP profile).",
 "Hiperpotasemia con K/ahorradores. Tos seca. Suspender en embarazo.",
 "Hyperkalemia with K/sparing agents. Dry cough. Stop in pregnancy.","Clínico (cronoterapia)"),
("amlodipine","Amlodipino","Antihipertensivo (calcioantagonista)","Antihypertensive (CCB)",
 "Cualquier hora (vida media larga)","Any time (long half-life)",
 "Vida media ~35–50 h: cobertura de 24 h, horario flexible.",
 "Half-life ~35–50 h: 24 h coverage, flexible timing.",
 "Edema maleolar dependiente de dosis.",
 "Dose-dependent ankle edema.","Clínico"),
("semaglutide","Semaglutida","Agonista GLP-1","GLP-1 agonist",
 "Semanal (inyectable) · mismo día","Weekly (injectable) · same day",
 "Oral: en ayunas con poca agua, 30 min antes de comer/beber/otros fármacos.",
 "Oral: fasting with little water, 30 min before food/drink/other drugs.",
 "Náuseas al escalar dosis. Precaución en gastroparesia y antes de cirugía/anestesia.",
 "Nausea on dose escalation. Caution in gastroparesis and before surgery/anesthesia.","Clínico"),
("insulin","Insulina","Antidiabético (hormona)","Antidiabetic (hormone)",
 "Según tipo: basal (noche) · prandial (con comidas)","By type: basal (night) · prandial (with meals)",
 "Basal cubre 24 h; rápida se ajusta a carbohidratos de cada comida.",
 "Basal covers 24 h; rapid matches each meal's carbohydrates.",
 "Riesgo de hipoglucemia: no saltarse comidas. Ajustar con glucemias.",
 "Hypoglycemia risk: don't skip meals. Titrate by glucose.","Clínico"),
("fenofibrate","Fenofibrato","Fibrato","Fibrate",
 "Con la comida principal","With the main meal",
 "La comida mejora la absorción (formulaciones no micronizadas).",
 "Food improves absorption (non-micronized forms).",
 "Riesgo de miopatía con estatinas. Vigilar función hepática y renal.",
 "Myopathy risk with statins. Monitor liver and kidney function.","Clínico"),
("omega-3-ethyl-esters","Omega-3 (ésteres etílicos, Rx)","Hipolipemiante","Lipid-lowering",
 "Con comida grasa","With a fatty meal",
 "2–4 g/día bajan TG 20–30%; la grasa mejora la absorción.",
 "2–4 g/day lower TG 20–30%; fat improves absorption.",
 "Sangrado con anticoagulantes a dosis altas.",
 "Bleeding with anticoagulants at high doses.","Clínico"),
("niacin","Niacina (Rx)","Hipolipemiante","Lipid-lowering",
 "Noche, con comida","Night, with food",
 "Dosificación nocturna con comida reduce el flushing; sube HDL y baja Lp(a).",
 "Night dosing with food reduces flushing; raises HDL and lowers Lp(a).",
 "Flushing, hepatotoxicidad a dosis altas, hiperglucemia. Vigilar hígado.",
 "Flushing, hepatotoxicity at high doses, hyperglycemia. Monitor liver.","Clínico"),
("prednisone","Prednisona","Corticoide","Corticosteroid",
 "Mañana (con desayuno)","Morning (with breakfast)",
 "Imita el pico matutino de cortisol → menos supresión del eje HPA e insomnio.",
 "Mimics the morning cortisol peak → less HPA-axis suppression and insomnia.",
 "No suspender bruscamente (crisis suprarrenal). Hiperglucemia, gastritis, osteoporosis.",
 "Do not stop abruptly (adrenal crisis). Hyperglycemia, gastritis, osteoporosis.","Clínico"),
("ibuprofen","Ibuprofeno / AINE","Antiinflamatorio (AINE)","Anti-inflammatory (NSAID)",
 "Con comida","With food",
 "Con alimento reduce la irritación gástrica.",
 "With food reduces gastric irritation.",
 "Riesgo GI/renal/cardiovascular. Evitar con anticoagulantes; separar del omega-3 alto.",
 "GI/renal/cardiovascular risk. Avoid with anticoagulants; separate from high-dose omega-3.","Clínico"),
("methotrexate","Metotrexato","Inmunosupresor / antineoplásico","Immunosuppressant / antineoplastic",
 "SEMANAL (no diario) · mismo día","WEEKLY (not daily) · same day",
 "Dosis SEMANAL en artritis/psoriasis; suplementar ácido fólico en día distinto.",
 "WEEKLY dose in arthritis/psoriasis; supplement folic acid on a different day.",
 "ERROR MORTAL si se toma a diario. Hepatotóxico. Teratógeno. Vigilar hemograma/hígado.",
 "FATAL ERROR if taken daily. Hepatotoxic. Teratogenic. Monitor CBC/liver.","Clínico"),
("acetaminophen","Paracetamol (acetaminofén)","Analgésico","Analgesic",
 "Cualquier hora","Any time",
 "Analgésico/antipirético; no antiinflamatorio.",
 "Analgesic/antipyretic; not anti-inflammatory.",
 "Hepatotóxico >3–4 g/día o con alcohol. Sumar todas las fuentes.",
 "Hepatotoxic >3–4 g/day or with alcohol. Count all sources.","Clínico"),
]

FIELDS = ["key","name","class_es","class_en","timing_es","timing_en","why_es","why_en",
          "warn_es","warn_en","evidence"]

# alias fármaco individual -> clave (para mapear los de CLINICAL_MAP)
ALIASES = {
    "glipizide": "insulin", "sitagliptin": "metformin", "empagliflozin": "metformin",
    "liraglutide": "semaglutide", "pravastatin": "rosuvastatin", "gemfibrozil": "fenofibrate",
    "hydrochlorothiazide": "losartan", "metoprolol": "amlodipine", "naproxen": "ibuprofen",
    "celecoxib": "ibuprofen", "orlistat": "metformin", "phentermine": "semaglutide",
    "topiramate": "semaglutide", "ezetimibe": "atorvastatin", "statins": "atorvastatin",
    "warfarin": "acetaminophen", "anticoagulants": "acetaminophen",
}

def main():
    items = {}
    for row in R:
        d = dict(zip(FIELDS, row))
        items[d["key"]] = d
    out = {"version": "1.0", "count": len(items), "aliases": ALIASES,
           "note_es": "Cronoterapia educativa basada en farmacocinética y estudios publicados. No sustituye la prescripción médica.",
           "note_en": "Educational chronotherapy based on pharmacokinetics and published studies. Not a substitute for medical prescription.",
           "drugs": items}
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "local_db", "drug_timing.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(items)} fármacos -> {dst}")

if __name__ == "__main__":
    main()
