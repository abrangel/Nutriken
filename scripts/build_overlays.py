"""
Genera local_db/plan_overlays.json â€” contenido experto por condiciÃ³n para el Plan ClÃ­nico
(nivel de los informes de referencia): mecanismo ligado a la ruta KEGG + SNP concreto +
detalle prÃ¡ctico + resultados esperados. BilingÃ¼e ES/EN. Reproducible.
Ejecutar:  python scripts/build_overlays.py
"""
import json, os


def iv(m_es, m_en, snp_es, snp_en, p_es, p_en, ev, kin_es="", kin_en="", contra_es="", contra_en=""):
    d = {"mechanism_es": m_es, "mechanism_en": m_en, "snp_es": snp_es, "snp_en": snp_en,
         "practical_es": p_es, "practical_en": p_en, "evidence": ev}
    if kin_es or kin_en:
        d["kinetics_es"], d["kinetics_en"] = kin_es, (kin_en or kin_es)
    if contra_es or contra_en:
        d["contra_es"], d["contra_en"] = contra_es, (contra_en or contra_es)
    return d


OV = {
 "_doc": "Contenido experto curado por condiciÃ³n. Mecanismo ligado a ruta KEGG + SNP + detalle prÃ¡ctico + resultados. Requiere validaciÃ³n clÃ­nica.",

 "diabetes": {
   "pathway_context_es": "Ruta KEGG hsa04930 (diabetes tipo 2): la resistencia a insulina y la disfunciÃ³n de cÃ©lulas Î² convergen en PI3K-Akt, AMPK y estrÃ©s oxidativo. Las intervenciones se cronometran a la ventana de mayor sensibilidad insulÃ­nica (maÃ±ana) y a las comidas con carbohidratos.",
   "pathway_context_en": "KEGG hsa04930 (type 2 diabetes): insulin resistance and Î²-cell dysfunction converge on PI3K-Akt, AMPK and oxidative stress. Interventions are timed to the window of highest insulin sensitivity (morning) and to carbohydrate meals.",
   "interventions": {
     "berberine": iv("Activa AMPK (nodo central de hsa04930), aumenta GLUT4 y sensibilidad a insulina; inhibe gluconeogÃ©nesis hepÃ¡tica (efecto tipo metformina).","Activates AMPK (central node of hsa04930), raises GLUT4 and insulin sensitivity; inhibits hepatic gluconeogenesis (metformin-like).","TCF7L2 (rs7903146, riesgo T): mayor disfunciÃ³n de cÃ©lula Î².","TCF7L2 (rs7903146, T risk): greater Î²-cell dysfunction.","[DOSIS_CLINICA_REMOVIDA] 15â€“30 min antes de las 2â€“3 comidas con carbohidratos. Baja HbA1c ~0.7â€“1%.","[DOSIS_CLINICA_REMOVIDA] 15â€“30 min before the 2â€“3 carbohydrate meals. Lowers HbA1c ~0.7â€“1%.","Meta-anÃ¡lisis"),
     "chromium": iv("Potencia la autofosforilaciÃ³n del receptor de insulina (brazo PI3K-Akt).","Potentiates insulin-receptor autophosphorylation (PI3K-Akt arm).","Mayor beneficio en resistencia a insulina establecida.","Greater benefit in established insulin resistance.","200 Âµg/dÃ­a (picolinato) con la comida principal. Separar de levotiroxina.","[DOSIS_CLINICA_REMOVIDA] (picolinate) with the main meal. Separate from levothyroxine.","ClÃ­nico (mixto)"),
     "cinnamon": iv("Polifenoles mejoran la captaciÃ³n de glucosa y ralentizan el vaciado gÃ¡strico â†’ menor pico posprandial.","Polyphenols improve glucose uptake and slow gastric emptying â†’ lower postprandial spike.","Sin SNP validado; efecto dosis-dependiente.","No validated SNP; dose-dependent effect.","1â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a de CEYLÃN (Cinnamomum verum), NO Cassia (cumarina hepatotÃ³xica), con el desayuno.","1â€“[DOSIS_CLINICA_REMOVIDA]y CEYLON (Cinnamomum verum), NOT Cassia (hepatotoxic coumarin), with breakfast.","ClÃ­nico (modesto)"),
     "ala": iv("Antioxidante que reduce el estrÃ©s oxidativo de hsa04930 y mejora la sensibilidad a insulina; alivia neuropatÃ­a.","Antioxidant that reduces hsa04930 oxidative stress and improves insulin sensitivity; relieves neuropathy.","Beneficio marcado en neuropatÃ­a sintomÃ¡tica.","Marked benefit in symptomatic neuropathy.","[DOSIS_CLINICA_REMOVIDA] (R-ALA) en ayunas 30 min antes del desayuno. Puede bajar glucosa.","[DOSIS_CLINICA_REMOVIDA] (R-ALA) fasting 30 min before breakfast. May lower glucose.","ClÃ­nico"),
     "fenugreek": iv("Fibra soluble + 4-hidroxiisoleucina: enlentece la absorciÃ³n de glucosa y estimula la insulina.","Soluble fiber + 4-hydroxyisoleucine: slows glucose absorption and stimulates insulin.","Efecto posprandial consistente.","Consistent postprandial effect.","5â€“[DOSIS_CLINICA_REMOVIDA] de semilla molida con las comidas de carbohidratos.","5â€“[DOSIS_CLINICA_REMOVIDA] ground seed with carbohydrate meals.","ClÃ­nico (moderado)"),
     "magnesium": iv("Cofactor de la cascada del receptor de insulina; el dÃ©ficit empeora la resistencia.","Cofactor of the insulin-receptor cascade; deficiency worsens resistance.","TRPM6 influye en el estatus de magnesio.","TRPM6 influences magnesium status.","300â€“[DOSIS_CLINICA_REMOVIDA] (glicinato) por la noche. Separar de antibiÃ³ticos.","300â€“[DOSIS_CLINICA_REMOVIDA] (glycinate) at night. Separate from antibiotics.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["HbA1c: berberina ~-0.7 a -1%; aditivo con dieta/ejercicio.","Glucosa posprandial: canela + fenogreco + fibra reducen el pico.","NeuropatÃ­a: ALA [DOSIS_CLINICA_REMOVIDA]/dÃ­a mejora sÃ­ntomas a 4â€“8 semanas.","Seguridad: vigilar hipoglucemia si se combinan con antidiabÃ©ticos."],
   "expected_outcomes_en": ["HbA1c: berberine ~-0.7 to -1%; additive with diet/exercise.","Postprandial glucose: cinnamon + fenugreek + fiber blunt the spike.","Neuropathy: ALA [DOSIS_CLINICA_REMOVIDA] improves symptoms at 4â€“8 weeks.","Safety: watch for hypoglycemia when combined with antidiabetics."],
 },

 "obesity": {
   "pathway_context_es": "Ruta KEGG hsa04920 (adipocitoquinas): leptina/adiponectina (LEPR, ADIPOQ) y AMPK regulan apetito y gasto energÃ©tico. FTO modula la saciedad. Se cronometra a las ventanas de cortisol/insulina y a la ansiedad vespertina por dulce.",
   "pathway_context_en": "KEGG hsa04920 (adipocytokines): leptin/adiponectin (LEPR, ADIPOQ) and AMPK regulate appetite and energy expenditure. FTO modulates satiety. Timed to cortisol/insulin windows and the evening sweet craving.",
   "interventions": {
     "egcg": iv("EGCG inhibe la COMT â†’ prolonga la noradrenalina â†’ termogÃ©nesis leve; potenciado por cafeÃ­na.","EGCG inhibits COMT â†’ prolongs noradrenaline â†’ mild thermogenesis; potentiated by caffeine.","FTO (rs9939609, riesgo A): mayor apetito; el ejercicio es su 'antÃ­doto'.","FTO (rs9939609, A risk): higher appetite; exercise is its 'antidote'.","300â€“[DOSIS_CLINICA_REMOVIDA] EGCG por la tarde (16 h), NO en ayunas; con comida (riesgo hepÃ¡tico). ~-1.4 kg/12 sem.","300â€“[DOSIS_CLINICA_REMOVIDA] EGCG in the afternoon (4 pm), NOT fasting; with food (liver risk). ~-1.4 kg/12 wk.","Meta-anÃ¡lisis"),
     "glucomannan": iv("Fibra viscosa (konjac): forma gel, distiende el estÃ³mago y frena NPY/AGRP â†’ saciedad.","Viscous fiber (konjac): forms a gel, distends the stomach and curbs NPY/AGRP â†’ satiety.","Respuesta de saciedad general.","General satiety response.","[DOSIS_CLINICA_REMOVIDA] con 1â€“2 vasos de agua 15â€“30 min antes de las comidas. SIEMPRE con agua (riesgo de atragantamiento).","[DOSIS_CLINICA_REMOVIDA] with 1â€“2 glasses of water 15â€“30 min before meals. ALWAYS with water (choking risk).","ClÃ­nico"),
     "berberine": iv("Activa AMPK â†’ mejora sensibilidad a insulina y perfil lipÃ­dico; reduce adipogÃ©nesis.","Activates AMPK â†’ improves insulin sensitivity and lipids; reduces adipogenesis.","Ãštil en obesidad con resistencia a insulina.","Useful in obesity with insulin resistance.","[DOSIS_CLINICA_REMOVIDA] antes de las comidas principales.","[DOSIS_CLINICA_REMOVIDA] before main meals.","ClÃ­nico"),
     "chromium": iv("Mejora la seÃ±alizaciÃ³n de insulina y puede reducir el antojo de carbohidratos.","Improves insulin signaling and may reduce carbohydrate cravings.","Mayor efecto en resistencia a insulina.","Greater effect in insulin resistance.","200 Âµg/dÃ­a con comida.","[DOSIS_CLINICA_REMOVIDA] with food.","ClÃ­nico (mixto)"),
     "cla": iv("Modula PPARÎ³ y la lipÃ³lisis; efecto modesto en composiciÃ³n corporal.","Modulates PPARÎ³ and lipolysis; modest effect on body composition.","Evidencia inconsistente.","Inconsistent evidence.","3â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a con comida; puede empeorar resistencia a insulina a dosis altas.","3â€“[DOSIS_CLINICA_REMOVIDA]y with food; may worsen insulin resistance at high doses.","ClÃ­nico (mixto)"),
   },
   "expected_outcomes_es": ["Peso: EGCG ~-1.4 kg/12 sem; glucomanano aÃ±ade saciedad y baja LDL.","MetabÃ³lico: berberina + cromo mejoran sensibilidad a insulina.","Clave: el efecto es aditivo a dÃ©ficit calÃ³rico y ejercicio, no sustituto.","FTO: el ejercicio neutraliza gran parte del riesgo genÃ©tico."],
   "expected_outcomes_en": ["Weight: EGCG ~-1.4 kg/12 wk; glucomannan adds satiety and lowers LDL.","Metabolic: berberine + chromium improve insulin sensitivity.","Key: effect is additive to caloric deficit and exercise, not a substitute.","FTO: exercise neutralizes much of the genetic risk."],
 },

 "hypertension": {
   "pathway_context_es": "Ruta KEGG hsa04614 (sistema renina-angiotensina): ACE/AGT/AGTR1 regulan la vasoconstricciÃ³n. Ã“xido nÃ­trico y magnesio modulan el tono vascular. Cronoterapia: en no-dippers, mover un antihipertensivo a la noche.",
   "pathway_context_en": "KEGG hsa04614 (renin-angiotensin system): ACE/AGT/AGTR1 drive vasoconstriction. Nitric oxide and magnesium modulate vascular tone. Chronotherapy: in non-dippers, shift one antihypertensive to night.",
   "interventions": {
     "garlic": iv("La alicina aumenta el Ã³xido nÃ­trico (vasodilataciÃ³n) e inhibe levemente la ECA.","Allicin raises nitric oxide (vasodilation) and mildly inhibits ACE.","ACE (rs4646994 I/D): el genotipo DD asocia PA mÃ¡s alta.","ACE (rs4646994 I/D): DD genotype associates with higher BP.","600â€“[DOSIS_CLINICA_REMOVIDA] de extracto aÃ±ejado/dÃ­a. Baja PAS ~5â€“8 mmHg. Suspender 7â€“10 d antes de cirugÃ­a.","600â€“[DOSIS_CLINICA_REMOVIDA] aged extract/day. Lowers SBP ~5â€“8 mmHg. Stop 7â€“10 d before surgery.","Meta-anÃ¡lisis"),
     "magnesium": iv("Antagonista natural del calcio en el mÃºsculo liso vascular â†’ vasodilataciÃ³n.","Natural calcium antagonist in vascular smooth muscle â†’ vasodilation.","DÃ©ficit frecuente empeora la PA.","Common deficiency worsens BP.","300â€“[DOSIS_CLINICA_REMOVIDA] (glicinato) por la noche. Baja PAS ~2â€“4 mmHg.","300â€“[DOSIS_CLINICA_REMOVIDA] (glycinate) at night. Lowers SBP ~2â€“4 mmHg.","ClÃ­nico"),
     "omega3": iv("EPA/DHA mejoran la funciÃ³n endotelial y bajan la PA levemente.","EPA/DHA improve endothelial function and mildly lower BP.","Beneficio dependiente de la dosis.","Dose-dependent benefit.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal.","Meta-anÃ¡lisis"),
     "coq10": iv("Mejora la eficiencia mitocondrial endotelial; efecto hipotensor modesto.","Improves endothelial mitochondrial efficiency; modest hypotensive effect.","Mayor beneficio en dÃ©ficit (uso de estatinas).","Greater benefit in deficiency (statin use).","100â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a (ubiquinol) con comida grasa.","100â€“[DOSIS_CLINICA_REMOVIDA] (ubiquinol) with a fatty meal.","ClÃ­nico (mixto)"),
   },
   "expected_outcomes_es": ["PA: ajo ~-5â€“8 mmHg PAS; magnesio y omega-3 aditivos.","Cronoterapia: en no-dippers (MAPA), un antihipertensivo nocturno mejora el perfil.","Seguridad: ajo + anticoagulantes = riesgo de sangrado; vigilar antes de cirugÃ­a."],
   "expected_outcomes_en": ["BP: garlic ~-5â€“8 mmHg SBP; magnesium and omega-3 additive.","Chronotherapy: in non-dippers (ABPM), a nighttime antihypertensive improves the profile.","Safety: garlic + anticoagulants = bleeding risk; watch before surgery."],
 },

 "cholesterol": {
   "pathway_context_es": "La sÃ­ntesis hepÃ¡tica de colesterol (HMGCR) pica de noche; LDLR/PCSK9/APOB regulan el aclaramiento de LDL. Intervenciones nocturnas y con las comidas grasas.",
   "pathway_context_en": "Hepatic cholesterol synthesis (HMGCR) peaks at night; LDLR/PCSK9/APOB regulate LDL clearance. Night and fatty-meal timing.",
   "interventions": {
     "red_yeast_rice": iv("Contiene monacolina K = lovastatina natural: inhibe HMGCR (misma diana que las estatinas).","Contains monacolin K = natural lovastatin: inhibits HMGCR (same target as statins).","SLCO1B1 (rs4149056): mayor riesgo de miopatÃ­a (igual que con estatinas).","SLCO1B1 (rs4149056): higher myopathy risk (as with statins).","~[DOSIS_CLINICA_REMOVIDA] monacolina K/noche con comida. Baja LDL 15â€“25%. NO combinar con estatinas; aÃ±adir CoQ10.","~[DOSIS_CLINICA_REMOVIDA] monacolin K/night with food. Lowers LDL 15â€“25%. Do NOT combine with statins; add CoQ10.","ClÃ­nico"),
     "plant_sterols": iv("Compiten con el colesterol por la absorciÃ³n intestinal â†’ menos LDL.","Compete with cholesterol for intestinal absorption â†’ less LDL.","Sin SNP relevante de rutina.","No routine relevant SNP.","[DOSIS_CLINICA_REMOVIDA]/dÃ­a repartidos con las comidas grasas. Bajan LDL 8â€“10%.","[DOSIS_CLINICA_REMOVIDA]y split with fatty meals. Lower LDL 8â€“10%.","ClÃ­nico (fuerte)"),
     "bergamot": iv("Polifenoles inhiben HMGCR y ACAT; bajan LDL y triglicÃ©ridos.","Polyphenols inhibit HMGCR and ACAT; lower LDL and triglycerides.","Alternativa/complemento en intolerancia a estatinas.","Alternative/complement in statin intolerance.","500â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a antes de comidas.","500â€“[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico (moderado)"),
     "omega3": iv("Bajan la sÃ­ntesis hepÃ¡tica de VLDL â†’ menos triglicÃ©ridos.","Lower hepatic VLDL synthesis â†’ fewer triglycerides.","Efecto marcado en hipertrigliceridemia.","Marked effect in hypertriglyceridemia.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa. TG -20â€“30%.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal. TG -20â€“30%.","Meta-anÃ¡lisis"),
     "berberine": iv("Sube el receptor de LDL (LDLR) por vÃ­a distinta a las estatinas â†’ sinergia.","Upregulates the LDL receptor (LDLR) via a non-statin route â†’ synergy.","Complemento a estatina/dieta.","Complement to statin/diet.","[DOSIS_CLINICA_REMOVIDA] antes de las comidas.","[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["LDL: levadura roja 15â€“25%, fitoesteroles 8â€“10%, bergamota aditiva.","TG: omega-3 -20â€“30%.","Seguridad: levadura roja ES estatina â†’ NO sumar a estatina; vigilar hÃ­gado/CK y aÃ±adir CoQ10."],
   "expected_outcomes_en": ["LDL: red yeast rice 15â€“25%, phytosterols 8â€“10%, bergamot additive.","TG: omega-3 -20â€“30%.","Safety: red yeast rice IS a statin â†’ do NOT add to a statin; monitor liver/CK and add CoQ10."],
 },

 "liver": {
   "pathway_context_es": "HÃ­gado graso (NAFLD/NASH): PNPLA3/TM6SF2 aumentan la susceptibilidad; el estrÃ©s oxidativo y la lipotoxicidad impulsan la inflamaciÃ³n. Objetivo: reducir grasa hepÃ¡tica y oxidaciÃ³n.",
   "pathway_context_en": "Fatty liver (NAFLD/NASH): PNPLA3/TM6SF2 increase susceptibility; oxidative stress and lipotoxicity drive inflammation. Goal: reduce liver fat and oxidation.",
   "interventions": {
     "vite": iv("Antioxidante que reduce la peroxidaciÃ³n lipÃ­dica hepÃ¡tica (recomendado en NASH sin diabetes).","Antioxidant that reduces hepatic lipid peroxidation (recommended in NASH without diabetes).","PNPLA3 (rs738409, riesgo G): mayor esteatosis; puede modular la respuesta.","PNPLA3 (rs738409, G risk): more steatosis; may modulate response.","â‰¤[DOSIS_CLINICA_REMOVIDA]/dÃ­a con comida grasa (guÃ­as NASH). No exceder crÃ³nicamente.","â‰¤[DOSIS_CLINICA_REMOVIDA] with a fatty meal (NASH guidelines). Don't exceed chronically.","ClÃ­nico"),
     "milkthistle": iv("Silimarina: antioxidante hepatoprotector, estabiliza la membrana del hepatocito.","Silymarin: antioxidant hepatoprotector, stabilizes the hepatocyte membrane.","Buen perfil de seguridad; evidencia mixta.","Good safety; mixed evidence.","200â€“[DOSIS_CLINICA_REMOVIDA] silimarina/dÃ­a con comida.","200â€“[DOSIS_CLINICA_REMOVIDA] silymarin/day with food.","ClÃ­nico (moderado)"),
     "berberine": iv("Activa AMPK â†’ reduce lipogÃ©nesis hepÃ¡tica y grasa del hÃ­gado.","Activates AMPK â†’ reduces hepatic lipogenesis and liver fat.","Ãštil en NAFLD con resistencia a insulina.","Useful in NAFLD with insulin resistance.","[DOSIS_CLINICA_REMOVIDA] antes de las comidas.","[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico"),
     "omega3": iv("Bajan triglicÃ©ridos hepÃ¡ticos y activan PPARÎ± (oxidaciÃ³n de Ã¡cidos grasos).","Lower hepatic triglycerides and activate PPARÎ± (fatty-acid oxidation).","Beneficio en el componente de TG.","Benefit on the TG component.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal.","ClÃ­nico"),
     "choline": iv("Necesaria para exportar VLDL; su dÃ©ficit causa acumulaciÃ³n de grasa hepÃ¡tica.","Needed to export VLDL; deficiency causes hepatic fat accumulation.","MTHFD1/PEMT influyen en el requerimiento.","MTHFD1/PEMT influence requirement.","Citicolina/alfa-GPC; asegurar aporte adecuado.","Citicoline/alpha-GPC; ensure adequate intake.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["Grasa hepÃ¡tica: berberina + omega-3 la reducen; vitamina E mejora histologÃ­a en NASH.","Enzimas: descenso de ALT/AST a 3â€“6 meses con pÃ©rdida de peso.","Base: la pÃ©rdida de peso del 7â€“10% es la intervenciÃ³n mÃ¡s potente."],
   "expected_outcomes_en": ["Liver fat: berberine + omega-3 reduce it; vitamin E improves NASH histology.","Enzymes: ALT/AST decline at 3â€“6 months with weight loss.","Foundation: 7â€“10% weight loss is the most powerful intervention."],
 },

 "inflammation": {
   "pathway_context_es": "Ruta KEGG hsa04668 (seÃ±alizaciÃ³n TNF/NF-ÎºB): TNF, IL6, PTGS2 (COX-2) impulsan la inflamaciÃ³n. FitoquÃ­micos inhiben NF-ÎºB, COX-2 y 5-LOX, y resuelven vÃ­a SPMs.",
   "pathway_context_en": "KEGG hsa04668 (TNF/NF-ÎºB signaling): TNF, IL6, PTGS2 (COX-2) drive inflammation. Phytochemicals inhibit NF-ÎºB, COX-2 and 5-LOX, and resolve via SPMs.",
   "interventions": {
     "curcumin": iv("Inhibe NF-ÎºB y COX-2 (nodos de hsa04668) â†’ menos citoquinas proinflamatorias.","Inhibits NF-ÎºB and COX-2 (hsa04668 nodes) â†’ fewer pro-inflammatory cytokines.","Sin SNP de rutina; efecto dependiente de biodisponibilidad.","No routine SNP; effect depends on bioavailability.","1000â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a con piperina o fitosoma, con comida grasa. Suspender antes de cirugÃ­a.","1000â€“[DOSIS_CLINICA_REMOVIDA] with piperine or phytosome, with a fatty meal. Stop before surgery.","ClÃ­nico"),
     "omega3": iv("EPA/DHA generan resolvinas/protectinas (SPMs) que RESUELVEN activamente la inflamaciÃ³n.","EPA/DHA generate resolvins/protectins (SPMs) that actively RESOLVE inflammation.","Ratio omega-6/3 alto amplifica la inflamaciÃ³n.","High omega-6/3 ratio amplifies inflammation.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal.","Meta-anÃ¡lisis"),
     "boswellia": iv("Los Ã¡cidos boswÃ©licos (AKBA) inhiben 5-LOX â†’ menos leucotrienos (artrosis, EII).","Boswellic acids (AKBA) inhibit 5-LOX â†’ fewer leukotrienes (osteoarthritis, IBD).","Beneficio en artrosis y enfermedad inflamatoria intestinal.","Benefit in osteoarthritis and IBD.","100â€“[DOSIS_CLINICA_REMOVIDA] AKBA/dÃ­a con comida grasa.","100â€“[DOSIS_CLINICA_REMOVIDA] AKBA/day with a fatty meal.","ClÃ­nico"),
     "quercetin": iv("Estabiliza mastocitos e inhibe NF-ÎºB; antiinflamatorio/antihistamÃ­nico.","Stabilizes mast cells and inhibits NF-ÎºB; anti-inflammatory/antihistamine.","Baja biodisponibilidad â†’ con bromelina/vit C.","Low bioavailability â†’ with bromelain/vit C.","[DOSIS_CLINICA_REMOVIDA] 2Ã—/dÃ­a con comida.","[DOSIS_CLINICA_REMOVIDA] 2Ã—/day with food.","PreclÃ­nico/clÃ­nico"),
   },
   "expected_outcomes_es": ["PCR/citoquinas: curcumina + omega-3 bajan marcadores inflamatorios.","Dolor articular: boswellia y curcumina mejoran a 4â€“8 semanas.","Seguridad: curcumina/omega-3 a dosis altas + anticoagulantes = sangrado."],
   "expected_outcomes_en": ["CRP/cytokines: curcumin + omega-3 lower inflammatory markers.","Joint pain: boswellia and curcumin improve at 4â€“8 weeks.","Safety: high-dose curcumin/omega-3 + anticoagulants = bleeding."],
 },

 "triglycerides": {
   "pathway_context_es": "Hipertrigliceridemia (hsa04977, digestiÃ³n/absorciÃ³n de lÃ­pidos): APOA5/LPL/APOC3 regulan el aclaramiento de VLDL. Objetivo: reducir sÃ­ntesis hepÃ¡tica de VLDL y mejorar la lipÃ³lisis.",
   "pathway_context_en": "Hypertriglyceridemia (hsa04977, lipid digestion/absorption): APOA5/LPL/APOC3 regulate VLDL clearance. Goal: reduce hepatic VLDL synthesis and improve lipolysis.",
   "interventions": {
     "omega3": iv("EPA/DHA reducen la sÃ­ntesis hepÃ¡tica de VLDL â†’ menos triglicÃ©ridos (efecto dosis-dependiente).","EPA/DHA reduce hepatic VLDL synthesis â†’ fewer triglycerides (dose-dependent).","APOA5 (rs662799): portadores con TG basales mÃ¡s altos responden bien.","APOA5 (rs662799): carriers with higher baseline TG respond well.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa. TG -20â€“30%.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal. TG -20â€“30%.","Meta-anÃ¡lisis"),
     "berberine": iv("Activa AMPK â†’ baja lipogÃ©nesis y mejora el perfil lipÃ­dico.","Activates AMPK â†’ lowers lipogenesis and improves lipids.","Sinergia con dieta baja en carbohidratos.","Synergy with low-carb diet.","[DOSIS_CLINICA_REMOVIDA] antes de comidas.","[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico"),
     "red_yeast_rice": iv("Monacolina K (lovastatina) inhibe HMGCR; baja LDL y algo de TG.","Monacolin K (lovastatin) inhibits HMGCR; lowers LDL and some TG.","SLCO1B1: riesgo de miopatÃ­a.","SLCO1B1: myopathy risk.","~[DOSIS_CLINICA_REMOVIDA] monacolina K/noche. NO combinar con estatina; aÃ±adir CoQ10.","~[DOSIS_CLINICA_REMOVIDA] monacolin K/night. Do NOT combine with a statin; add CoQ10.","ClÃ­nico"),
     "fenugreek": iv("Fibra soluble reduce absorciÃ³n de lÃ­pidos y glucosa.","Soluble fiber reduces lipid and glucose absorption.","Efecto posprandial.","Postprandial effect.","5â€“[DOSIS_CLINICA_REMOVIDA] de semilla con comidas.","5â€“[DOSIS_CLINICA_REMOVIDA] seed with meals.","ClÃ­nico (moderado)"),
   },
   "expected_outcomes_es": ["TG: omega-3 -20â€“30% a 2â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a (efecto mÃ¡s potente).","LDL: levadura roja/berberina aditivos.","Base: reducir azÃºcares simples y alcohol es clave para los TG."],
   "expected_outcomes_en": ["TG: omega-3 -20â€“30% at 2â€“[DOSIS_CLINICA_REMOVIDA]y (strongest effect).","LDL: red yeast rice/berberine additive.","Foundation: cutting simple sugars and alcohol is key for TG."],
 },

 "gut microbiota": {
   "pathway_context_es": "Eje intestino-huÃ©sped: la fibra fermentable â†’ SCFA (butirato) que nutre el colonocito e inhibe HDAC (epigenÃ©tica). ProbiÃ³ticos cepa-especÃ­ficos modulan inmunidad y barrera.",
   "pathway_context_en": "Gut-host axis: fermentable fiber â†’ SCFAs (butyrate) that feed the colonocyte and inhibit HDAC (epigenetics). Strain-specific probiotics modulate immunity and barrier.",
   "interventions": {
     "probiotics": iv("Cepas especÃ­ficas restauran la barrera intestinal y compiten con patÃ³genos; efecto CEPA-dependiente.","Specific strains restore the gut barrier and outcompete pathogens; STRAIN-dependent effect.","Sin SNP de rutina; elegir cepa por indicaciÃ³n.","No routine SNP; choose strain by indication.","10â€“50 mil millones UFC/dÃ­a con o antes de comida. Elegir cepa segÃºn objetivo, no 'genÃ©rico'.","10â€“50 billion CFU/day with or before a meal. Choose strain by goal, not 'generic'.","ClÃ­nico (cepa-dependiente)"),
     "psyllium": iv("Fibra soluble â†’ fermenta a SCFA (butirato), alimenta la microbiota y regula el trÃ¡nsito.","Soluble fiber â†’ ferments to SCFAs (butyrate), feeds microbiota and regulates transit.","Beneficio general en disbiosis.","General benefit in dysbiosis.","[DOSIS_CLINICA_REMOVIDA] 1â€“3Ã—/dÃ­a con agua abundante; subir gradual (gases). Separar 2â€“4 h de fÃ¡rmacos.","[DOSIS_CLINICA_REMOVIDA] 1â€“3Ã—/day with plenty of water; titrate up (gas). Separate 2â€“4 h from drugs.","ClÃ­nico"),
     "glutamine": iv("Combustible del enterocito: mantiene la integridad de la barrera intestinal.","Enterocyte fuel: maintains gut barrier integrity.","Ãštil en estrÃ©s/daÃ±o de mucosa.","Useful in stress/mucosal damage.","[DOSIS_CLINICA_REMOVIDA]/dÃ­a (hasta 10â€“[DOSIS_CLINICA_REMOVIDA] en daÃ±o intestinal).","[DOSIS_CLINICA_REMOVIDA]y (up to 10â€“[DOSIS_CLINICA_REMOVIDA] in gut damage).","ClÃ­nico (mixto)"),
     "omega3": iv("EPA/DHA modulan la microbiota y bajan la inflamaciÃ³n de mucosa.","EPA/DHA modulate microbiota and lower mucosal inflammation.","Ratio omega-6/3 afecta la disbiosis.","Omega-6/3 ratio affects dysbiosis.","[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa.","[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["Barrera: glutamina + probiÃ³ticos mejoran permeabilidad intestinal.","SCFA: fibra soluble (psyllium) sube butirato (efecto HDACi/epigenÃ©tico).","Clave: la cepa del probiÃ³tico define el efecto â€” no todos sirven para lo mismo."],
   "expected_outcomes_en": ["Barrier: glutamine + probiotics improve gut permeability.","SCFAs: soluble fiber (psyllium) raises butyrate (HDACi/epigenetic effect).","Key: the probiotic strain defines the effect â€” not interchangeable."],
 },

 "celiac": {
   "pathway_context_es": "Enfermedad celÃ­aca (HLA-DQ2/DQ8): la Ãºnica terapia es la dieta SIN GLUTEN estricta. Los suplementos corrigen los dÃ©ficits por malabsorciÃ³n, NO tratan la enfermedad.",
   "pathway_context_en": "Celiac disease (HLA-DQ2/DQ8): the only therapy is a strict GLUTEN-FREE diet. Supplements correct malabsorption deficiencies, they do NOT treat the disease.",
   "interventions": {
     "vitd": iv("Corrige el dÃ©ficit por malabsorciÃ³n de la mucosa daÃ±ada; salud Ã³sea.","Corrects deficiency from damaged-mucosa malabsorption; bone health.","DÃ©ficit muy frecuente al diagnÃ³stico.","Very common deficiency at diagnosis.","2000â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a con control de 25-OH-D; con comida grasa.","2000â€“[DOSIS_CLINICA_REMOVIDA] with 25-OH-D monitoring; with a fatty meal.","ClÃ­nico"),
     "iron": iv("La atrofia vellositaria causa anemia ferropÃ©nica; reponer hierro.","Villous atrophy causes iron-deficiency anemia; replete iron.","Anemia frecuente al diagnÃ³stico.","Anemia common at diagnosis.","Bisglicinato en dÃ­as alternos + vit C; confirmar con ferritina.","Bisglycinate alternate-day + vit C; confirm with ferritin.","ClÃ­nico"),
     "b12": iv("MalabsorciÃ³n ileal â†’ dÃ©ficit de B12; reponer.","Ileal malabsorption â†’ B12 deficiency; replete.","Verificar con Ã¡cido metilmalÃ³nico.","Confirm with methylmalonic acid.","500â€“1000 Âµg/dÃ­a (sublingual si malabsorciÃ³n).","500â€“[DOSIS_CLINICA_REMOVIDA] (sublingual if malabsorption).","ClÃ­nico"),
     "probiotics": iv("Pueden ayudar a restaurar la microbiota alterada; adyuvante, no tratamiento.","May help restore altered microbiota; adjuvant, not treatment.","Cepa-dependiente.","Strain-dependent.","10â€“20 mil millones UFC/dÃ­a.","10â€“20 billion CFU/day.","ClÃ­nico (limitado)"),
   },
   "expected_outcomes_es": ["Ãšnico tratamiento: dieta sin gluten estricta de por vida.","DÃ©ficits: reponer Vit D, hierro, B12, folato tras el diagnÃ³stico y revisar.","Seguimiento: anticuerpos y densitometrÃ­a; la mucosa se recupera en meses."],
   "expected_outcomes_en": ["Only treatment: strict lifelong gluten-free diet.","Deficiencies: replete Vit D, iron, B12, folate after diagnosis and re-check.","Follow-up: antibodies and bone density; mucosa recovers over months."],
 },

 "folate": {
   "pathway_context_es": "Metabolismo de un carbono (folato/B12/B6): MTHFR regula la conversiÃ³n a metilfolato activo; su dÃ©ficit sube la homocisteÃ­na.",
   "pathway_context_en": "One-carbon metabolism (folate/B12/B6): MTHFR regulates conversion to active methylfolate; its deficiency raises homocysteine.",
   "interventions": {
     "folate": iv("Dador de metilo esencial; en MTHFR C677T conviene el metilfolato (5-MTHF) ya activo.","Essential methyl donor; in MTHFR C677T prefer already-active methylfolate (5-MTHF).","MTHFR (rs1801133 C677T): menor actividad enzimÃ¡tica â†’ preferir metilfolato.","MTHFR (rs1801133 C677T): lower enzyme activity â†’ prefer methylfolate.","400â€“800 Âµg/dÃ­a de metilfolato. No enmascarar dÃ©ficit de B12.","400â€“[DOSIS_CLINICA_REMOVIDA] methylfolate. Don't mask B12 deficiency.","ClÃ­nico"),
     "b12": iv("Coopera con el folato en la remetilaciÃ³n de homocisteÃ­na; dÃ©ficit comÃºn en veganos/metformina/IBP.","Works with folate in homocysteine remethylation; deficiency common in vegans/metformin/PPIs.","Verificar antes de suplementar folato solo.","Confirm before supplementing folate alone.","500â€“1000 Âµg/dÃ­a (metilcobalamina).","500â€“[DOSIS_CLINICA_REMOVIDA] (methylcobalamin).","ClÃ­nico"),
   },
   "expected_outcomes_es": ["HomocisteÃ­na: folato + B12 (+ B6) la reducen.","MTHFR C677T: usar metilfolato mejora el estatus en portadores.","Seguridad: descartar dÃ©ficit de B12 antes de dar folato en dosis altas."],
   "expected_outcomes_en": ["Homocysteine: folate + B12 (+ B6) lower it.","MTHFR C677T: methylfolate improves status in carriers.","Safety: rule out B12 deficiency before high-dose folate."],
 },

 "weight loss": {
   "pathway_context_es": "Balance energÃ©tico (hsa04920): saciedad (LEPR/FTO), termogÃ©nesis y sensibilidad a insulina. Las intervenciones apoyan el dÃ©ficit calÃ³rico; no lo sustituyen.",
   "pathway_context_en": "Energy balance (hsa04920): satiety (LEPR/FTO), thermogenesis and insulin sensitivity. Interventions support the caloric deficit; they do not replace it.",
   "interventions": {
     "egcg": iv("EGCG inhibe COMT â†’ prolonga noradrenalina â†’ termogÃ©nesis leve.","EGCG inhibits COMT â†’ prolongs noradrenaline â†’ mild thermogenesis.","FTO (rs9939609, A): mayor apetito; el ejercicio lo contrarresta.","FTO (rs9939609, A): higher appetite; exercise counteracts it.","300â€“[DOSIS_CLINICA_REMOVIDA] EGCG por la tarde, con comida. ~-1.4 kg/12 sem.","300â€“[DOSIS_CLINICA_REMOVIDA] EGCG in the afternoon, with food. ~-1.4 kg/12 wk.","Meta-anÃ¡lisis", kin_es="Por la tarde: el pico de noradrenalina no interfiere con el sueÃ±o; con comida evita hepatotoxicidad.", kin_en="Afternoon: the noradrenaline peak doesn't disrupt sleep; with food avoids hepatotoxicity.", contra_es="Evitar en hepatopatÃ­a y en ayunas a dosis altas (riesgo hepÃ¡tico).", contra_en="Avoid in liver disease and fasting at high doses (liver risk)."),
     "berberine": iv("Activa AMPK â†’ mejora insulina y perfil lipÃ­dico; reduce adipogÃ©nesis.","Activates AMPK â†’ improves insulin and lipids; reduces adipogenesis.","Ãštil con resistencia a insulina.","Useful with insulin resistance.","[DOSIS_CLINICA_REMOVIDA] antes de las comidas.","[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico"),
     "chromium": iv("Mejora la seÃ±alizaciÃ³n de insulina; puede reducir el antojo de carbohidratos.","Improves insulin signaling; may reduce carbohydrate cravings.","Mayor efecto en resistencia a insulina.","Greater effect in insulin resistance.","200 Âµg/dÃ­a con comida.","[DOSIS_CLINICA_REMOVIDA] with food.","ClÃ­nico (mixto)"),
     "carnitine": iv("Transporta Ã¡cidos grasos a la mitocondria para su oxidaciÃ³n (efecto modesto).","Shuttles fatty acids into mitochondria for oxidation (modest effect).","Mayor beneficio en dÃ©ficit o mayores.","Greater benefit in deficiency or elderly.","[DOSIS_CLINICA_REMOVIDA]/dÃ­a con carbohidrato; efecto pequeÃ±o sin ejercicio.","[DOSIS_CLINICA_REMOVIDA]y with a carb; small effect without exercise.","ClÃ­nico (mixto)"),
     "5htp": iv("Precursor de serotonina â†’ aumenta la saciedad y reduce el picoteo.","Serotonin precursor â†’ increases satiety and reduces snacking.","Respuesta variable.","Variable response.","50â€“[DOSIS_CLINICA_REMOVIDA] antes de comidas o noche.","50â€“[DOSIS_CLINICA_REMOVIDA] before meals or at night.","ClÃ­nico (limitado)", contra_es="NO combinar con ISRS/IMAO (riesgo de sÃ­ndrome serotoninÃ©rgico).", contra_en="Do NOT combine with SSRIs/MAOIs (serotonin syndrome risk)."),
   },
   "expected_outcomes_es": ["Peso: apoyo de -1 a -3 kg/12 sem sobre un dÃ©ficit calÃ³rico.","Antojo: 5-HTP y fibra ayudan a la adherencia.","Clave: dieta + ejercicio siguen siendo el 80% del resultado."],
   "expected_outcomes_en": ["Weight: -1 to -3 kg/12 wk support on top of a caloric deficit.","Cravings: 5-HTP and fiber aid adherence.","Key: diet + exercise remain 80% of the result."],
 },

 "lactose intolerance": {
   "pathway_context_es": "Hipolactasia (gen LCT/MCM6): dÃ©ficit de lactasa. Estrategia: reducir lactosa, aportar lactasa exÃ³gena y prevenir el dÃ©ficit de calcio/Vit D por evitar lÃ¡cteos.",
   "pathway_context_en": "Hypolactasia (LCT/MCM6 gene): lactase deficiency. Strategy: reduce lactose, provide exogenous lactase and prevent calcium/Vit D deficiency from dairy avoidance.",
   "interventions": {
     "probiotics": iv("Cepas con Î²-galactosidasa (p. ej. Lactobacillus) ayudan a digerir la lactosa residual.","Strains with Î²-galactosidase (e.g., Lactobacillus) help digest residual lactose.","LCT/MCM6 (rs4988235): genotipo no persistente = hipolactasia adulta.","LCT/MCM6 (rs4988235): non-persistent genotype = adult hypolactasia.","10â€“20 mil millones UFC/dÃ­a con lÃ¡cteos.","10â€“20 billion CFU/day with dairy.","ClÃ­nico (moderado)"),
     "calcium": iv("Evitar lÃ¡cteos reduce el aporte de calcio â†’ suplementar para el hueso.","Avoiding dairy lowers calcium intake â†’ supplement for bone.","Riesgo Ã³seo si se evitan lÃ¡cteos.","Bone risk if dairy is avoided.","â‰¤[DOSIS_CLINICA_REMOVIDA] por toma (citrato), con Vit D y K2.","â‰¤[DOSIS_CLINICA_REMOVIDA] per dose (citrate), with Vit D and K2.","ClÃ­nico", contra_es="Separar 4 h de levotiroxina, hierro y quinolonas.", contra_en="Separate 4 h from levothyroxine, iron and quinolones."),
     "vitd": iv("Cofactor de la absorciÃ³n de calcio; frecuente dÃ©ficit al evitar lÃ¡cteos fortificados.","Cofactor for calcium absorption; common deficiency when avoiding fortified dairy.","Objetivo 25-OH-D 30â€“50 ng/mL.","Target 25-OH-D 30â€“50 ng/mL.","[DOSIS_CLINICA_REMOVIDA]/dÃ­a con comida grasa.","[DOSIS_CLINICA_REMOVIDA] with a fatty meal.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["SÃ­ntomas: lactasa exÃ³gena antes de lÃ¡cteos elimina la mayorÃ­a de molestias.","Hueso: calcio + Vit D compensan la restricciÃ³n de lÃ¡cteos.","Nota: la mayorÃ­a tolera yogur/quesos madurados (baja lactosa)."],
   "expected_outcomes_en": ["Symptoms: exogenous lactase before dairy removes most discomfort.","Bone: calcium + Vit D offset dairy restriction.","Note: most tolerate yogurt/aged cheeses (low lactose)."],
 },

 "gallstones": {
   "pathway_context_es": "Colelitiasis: sobresaturaciÃ³n biliar de colesterol y estasis vesicular. Objetivo: mejorar el flujo biliar y el perfil lipÃ­dico. La cirugÃ­a es el tratamiento definitivo si hay sÃ­ntomas.",
   "pathway_context_en": "Cholelithiasis: biliary cholesterol supersaturation and gallbladder stasis. Goal: improve bile flow and lipids. Surgery is definitive if symptomatic.",
   "interventions": {
     "artichoke": iv("ColerÃ©tico: la cinarina aumenta el flujo biliar y mejora la digestiÃ³n de grasas.","Choleretic: cynarin increases bile flow and improves fat digestion.","Sin SNP de rutina.","No routine SNP.","300â€“[DOSIS_CLINICA_REMOVIDA] antes de las comidas.","300â€“[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico (moderado)", contra_es="CONTRAINDICADO si hay obstrucciÃ³n de la vÃ­a biliar (puede precipitar cÃ³lico).", contra_en="CONTRAINDICATED in bile duct obstruction (may precipitate colic)."),
     "milkthistle": iv("Hepatoprotector; apoya la funciÃ³n hepatobiliar.","Hepatoprotector; supports hepatobiliary function.","Buen perfil de seguridad.","Good safety.","200â€“[DOSIS_CLINICA_REMOVIDA] silimarina/dÃ­a.","200â€“[DOSIS_CLINICA_REMOVIDA] silymarin/day.","ClÃ­nico (moderado)"),
     "vitc": iv("La vitamina C favorece la conversiÃ³n de colesterol a Ã¡cidos biliares (menos saturaciÃ³n).","Vitamin C promotes cholesterol-to-bile-acid conversion (less saturation).","Efecto poblacional modesto.","Modest population-level effect.","[DOSIS_CLINICA_REMOVIDA]/dÃ­a con comida.","[DOSIS_CLINICA_REMOVIDA] with food.","EpidemiolÃ³gico"),
   },
   "expected_outcomes_es": ["Flujo biliar: alcachofa mejora sÃ­ntomas dispÃ©pticos (si no hay obstrucciÃ³n).","Definitivo: colecistectomÃ­a si cÃ³lico recurrente/complicaciones.","PrevenciÃ³n: pÃ©rdida de peso gradual (no >1 kg/sem) para no precipitar cÃ¡lculos."],
   "expected_outcomes_en": ["Bile flow: artichoke improves dyspeptic symptoms (if no obstruction).","Definitive: cholecystectomy for recurrent colic/complications.","Prevention: gradual weight loss (not >1 kg/wk) to avoid precipitating stones."],
 },

 "statins": {
   "pathway_context_es": "Terapia con estatinas (HMGCR/SLCO1B1): la coenzima Q10 mitiga la mialgia; se vigilan interacciones CYP3A4 y la miopatÃ­a.",
   "pathway_context_en": "Statin therapy (HMGCR/SLCO1B1): coenzyme Q10 mitigates myalgia; CYP3A4 interactions and myopathy are monitored.",
   "interventions": {
     "coq10": iv("Las estatinas bajan la CoQ10; reponerla mejora la mialgia asociada.","Statins lower CoQ10; repletion improves associated myalgia.","SLCO1B1 (rs4149056): mayor riesgo de miopatÃ­a por estatinas.","SLCO1B1 (rs4149056): higher statin-myopathy risk.","100â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a (ubiquinol) con comida grasa.","100â€“[DOSIS_CLINICA_REMOVIDA] (ubiquinol) with a fatty meal.","ClÃ­nico (mixto)", contra_es="", contra_en=""),
     "milkthistle": iv("Hepatoprotector; Ãºtil ante elevaciÃ³n leve de transaminasas.","Hepatoprotector; useful for mild transaminase elevation.","â€”","â€”","200â€“[DOSIS_CLINICA_REMOVIDA] silimarina/dÃ­a.","200â€“[DOSIS_CLINICA_REMOVIDA] silymarin/day.","ClÃ­nico (moderado)"),
     "red_yeast_rice": iv("ES una estatina natural (lovastatina).","It IS a natural statin (lovastatin).","SLCO1B1: mismo riesgo de miopatÃ­a.","SLCO1B1: same myopathy risk.","No usar como 'suplemento' si ya toma estatina.","Don't use as a 'supplement' if already on a statin.","ClÃ­nico", contra_es="NO combinar con estatinas de prescripciÃ³n (doble dosis de estatina).", contra_en="Do NOT combine with prescription statins (double statin dose)."),
     "omega3": iv("Reduce triglicÃ©ridos, complemento Ãºtil del tratamiento hipolipemiante.","Reduces triglycerides, useful complement to lipid therapy.","â€”","â€”","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/dÃ­a con comida grasa.","2â€“[DOSIS_CLINICA_REMOVIDA] EPA+DHA/day with a fatty meal.","ClÃ­nico"),
   },
   "expected_outcomes_es": ["Mialgia: CoQ10 puede aliviarla en algunos pacientes.","Seguridad crÃ­tica: NO sumar levadura roja de arroz a una estatina.","Toronja: evitar con simvastatina/atorvastatina (CYP3A4)."],
   "expected_outcomes_en": ["Myalgia: CoQ10 may relieve it in some patients.","Critical safety: do NOT add red yeast rice to a statin.","Grapefruit: avoid with simvastatin/atorvastatin (CYP3A4)."],
 },

 "silymarin": {
   "pathway_context_es": "Silimarina (cardo mariano): antioxidante hepatoprotector; modula CYP levemente (vigilar interacciones).",
   "pathway_context_en": "Silymarin (milk thistle): antioxidant hepatoprotector; mildly modulates CYP (watch interactions).",
   "interventions": {
     "milkthistle": iv("La silibinina estabiliza la membrana del hepatocito y es antioxidante.","Silibinin stabilizes the hepatocyte membrane and is antioxidant.","Buen perfil de seguridad.","Good safety.","200â€“[DOSIS_CLINICA_REMOVIDA] silimarina/dÃ­a con comida.","200â€“[DOSIS_CLINICA_REMOVIDA] silymarin/day with food.","ClÃ­nico (moderado)", contra_es="InhibiciÃ³n leve de CYP2C9/3A4: precauciÃ³n con warfarina y sustratos.", contra_en="Mild CYP2C9/3A4 inhibition: caution with warfarin and substrates."),
     "vite": iv("Antioxidante complementario en daÃ±o hepÃ¡tico oxidativo.","Complementary antioxidant in oxidative liver damage.","â€”","â€”","â‰¤[DOSIS_CLINICA_REMOVIDA]/dÃ­a con comida grasa.","â‰¤[DOSIS_CLINICA_REMOVIDA] with a fatty meal.","ClÃ­nico"),
     "ala": iv("Regenera glutatiÃ³n y otros antioxidantes; apoyo hepÃ¡tico.","Regenerates glutathione and other antioxidants; liver support.","â€”","â€”","300â€“[DOSIS_CLINICA_REMOVIDA]/dÃ­a en ayunas.","300â€“[DOSIS_CLINICA_REMOVIDA] fasting.","ClÃ­nico"),
     "artichoke": iv("ColerÃ©tico y digestivo; complementa el soporte hepatobiliar.","Choleretic and digestive; complements hepatobiliary support.","â€”","â€”","300â€“[DOSIS_CLINICA_REMOVIDA] antes de comidas.","300â€“[DOSIS_CLINICA_REMOVIDA] before meals.","ClÃ­nico (moderado)", contra_es="Evitar en obstrucciÃ³n biliar.", contra_en="Avoid in bile duct obstruction."),
   },
   "expected_outcomes_es": ["Transaminasas: descenso leve en hepatopatÃ­a con soporte antioxidante.","Interacciones: vigilar warfarina con silimarina.","Base: eliminar el hepatotÃ³xico (alcohol, fÃ¡rmaco) es lo primero."],
   "expected_outcomes_en": ["Transaminases: mild decline in liver disease with antioxidant support.","Interactions: watch warfarin with silymarin.","Foundation: removing the hepatotoxin (alcohol, drug) comes first."],
 },
}


def main():
    dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "local_db", "plan_overlays.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(OV, f, ensure_ascii=False, indent=2)
    conds = [k for k in OV if not k.startswith("_")]
    print(f"OK: {len(conds)} condiciones -> {dst}  ({', '.join(conds)})")


if __name__ == "__main__":
    main()

