# plan_template.py
"""
Renderiza el "Plan Clínico Nutrigenómico" como HTML auto-contenido (sin CDN),
al estilo del reporte de referencia (hsa04920): pestañas Cronograma · Mecanismos ·
Nutrigenética/SNPs · Interacciones · Resultados. Pura función, sin dependencias.
"""
import html as _html


def _esc(s):
    return _html.escape(str(s if s is not None else ""))


def _t(lang, es, en):
    return en if lang == "en" else es


def render_plan_html(plan: dict, lang: str = "es") -> str:
    L = lang
    cond = _esc(plan.get("condition", ""))
    pw = plan.get("pathway", {}) or {}
    pw_id = _esc(pw.get("id", ""))
    pw_name = _esc(pw.get("name", ""))
    pw_url = _esc(pw.get("url", ""))

    # ── Cronograma ──
    crono_cards = ""
    for blk in plan.get("chronogram", []):
        items = ""
        for it in blk.get("items", []):
            note = it.get("note", "")
            items += f"""
              <div class="row">
                <div class="tcat">{_esc(it.get('category',''))}</div>
                <div class="tbody">
                  <div class="tname">{_esc(it.get('name',''))}</div>
                  <div class="tdose">{_esc(it.get('dose',''))}</div>
                  {f'<div class="tnote">{_esc(note)}</div>' if note else ''}
                </div>
              </div>"""
        crono_cards += f"""
          <div class="card">
            <div class="card-hd"><span class="ic">{_esc(blk.get('icon','⏰'))}</span>
              <div><div class="card-ti">{_esc(blk.get('time',''))} — {_esc(blk.get('title',''))}</div>
              <div class="card-su">{_esc(blk.get('subtitle',''))}</div></div></div>
            <div class="card-bd">{items or '<div class="muted">—</div>'}</div>
          </div>"""

    # ── Mecanismos (intervenciones con dosis/mecanismo/seguridad) ──
    mech_rows = ""
    for iv in plan.get("interventions", []):
        saf = iv.get("safety_text", "")
        refs = ""
        if iv.get("reference"):
            refs = f'<div class="ref">📚 {_esc(iv["reference"])}</div>'
        mech_rows += f"""
          <tr>
            <td><b>{_esc(iv.get('name',''))}</b><div class="muted">{_esc(iv.get('category',''))}</div></td>
            <td>{_esc(iv.get('standard_dose',''))}<div class="muted">{_t(L,'terap.','ther.')}: {_esc(iv.get('therapeutic_dose',''))}</div></td>
            <td>{_esc(iv.get('timing',''))}</td>
            <td>{_esc(iv.get('mechanism',''))}{refs}</td>
            <td>{f'<span class="warn">{_esc(saf)}</span>' if saf else '<span class="muted">—</span>'}</td>
          </tr>"""

    # ── Fármacos + timing (cronoterapia) ──
    drug_rows = ""
    for dt in plan.get("drugs_timing", []):
        warn = dt.get("warning", "")
        drug_rows += f"""
          <div class="card">
            <div class="card-hd"><span class="ic">💊</span>
              <div><div class="card-ti">{_esc(dt.get('drug',''))} <span class="muted">· {_esc(dt.get('class',''))}</span></div>
              <div class="card-su">⏱️ {_esc(dt.get('timing',''))}</div></div></div>
            <div class="card-bd">
              <div style="font-size:13px;margin-bottom:6px;">{_esc(dt.get('why',''))}</div>
              {f'<div class="warn">⚠️ {_esc(warn)}</div>' if warn else ''}
              <div class="muted">{_t(L,'Evidencia','Evidence')}: {_esc(dt.get('evidence',''))}</div>
            </div>
          </div>"""

    # ── SNPs / Nutrigenética ──
    gene_cards = ""
    for g in plan.get("genes", []):
        lk = g.get("links", {}) or {}
        links = " · ".join(
            f'<a href="{_esc(v)}" target="_blank">{_esc(k)}</a>'
            for k, v in lk.items() if v)
        vip = ' <span class="pill">VIP</span>' if g.get("is_vip") else ""
        gene_cards += f"""
          <div class="gcard">
            <div class="gsym">{_esc(g.get('symbol',''))}{vip}</div>
            <div class="muted">{_esc(g.get('name',''))}</div>
            <div class="glinks">{links}</div>
          </div>"""
    nutri_rows = ""
    for n in plan.get("nutrigenetics", []):
        pmid = n.get("pmids", "")
        pmid_l = (f'<a href="https://pubmed.ncbi.nlm.nih.gov/{_esc(pmid.split(";")[0].split(",")[0])}" '
                  f'target="_blank">PMID {_esc(pmid.split(";")[0].split(",")[0])}</a>') if pmid else ""
        nutri_rows += f"""<tr><td><b>{_esc(n.get('gene',''))}</b></td>
          <td>{_esc(n.get('chemical',''))}</td><td>{_esc(n.get('association',''))}</td>
          <td>{pmid_l}</td></tr>"""

    # ── Interacciones ──
    inter_rows = ""
    sev_color = {"alta": "#e34a5f", "media": "#f0b34b", "baja": "#4fc3a1",
                 "high": "#e34a5f", "moderate": "#f0b34b", "low": "#4fc3a1"}
    for it in plan.get("interactions", []):
        sev = (it.get("severity", "") or "").lower()
        col = sev_color.get(sev, "#8892a0")
        inter_rows += f"""
          <tr>
            <td><b>{_esc(it.get('herb',''))}</b> × {_esc(it.get('drug_class',''))}</td>
            <td><span class="sev" style="background:{col}">{_esc(it.get('severity',''))}</span></td>
            <td>{_esc(it.get('effect',''))}<div class="muted">{_esc(it.get('mechanism',''))}</div></td>
            <td class="muted">{_esc(it.get('source',''))}</td>
          </tr>"""

    # ── Resultados ──
    results = "".join(f"<li>{_esc(r)}</li>" for r in plan.get("results", []))

    refs_list = "".join(
        f'<li>{_esc(r.get("authors",""))} {_esc(r.get("title",""))} '
        f'<i>{_esc(r.get("journal",""))}</i>. {_esc(r.get("year",""))}. '
        f'<a href="{_esc(r.get("url",""))}" target="_blank">PMID {_esc(r.get("pmid",""))}</a>.</li>'
        for r in plan.get("references", []))

    tabs = [
        ("cronograma", _t(L, "⏰ Cronograma diario", "⏰ Daily schedule")),
        ("mecanismos", _t(L, "⚡ Mecanismos + Dosis", "⚡ Mechanisms + Dosing")),
        ("farmacos", _t(L, "💊 Fármacos + timing", "💊 Drugs + timing")),
        ("nutrigenetica", _t(L, "🧬 Nutrigenética / SNPs", "🧬 Nutrigenetics / SNPs")),
        ("interacciones", _t(L, "⚠️ Interacciones", "⚠️ Interactions")),
        ("resultados", _t(L, "📊 Resultados esperados", "📊 Expected outcomes")),
    ]
    nav = "".join(
        f'<button class="pill{" on" if i == 0 else ""}" onclick="show(\'{tid}\',this)">{lbl}</button>'
        for i, (tid, lbl) in enumerate(tabs))

    disclaimer = _esc(plan.get("disclaimer", ""))
    kegg_line = (f'{_t(L,"Ruta molecular","Molecular pathway")}: '
                 f'<a href="{pw_url}" target="_blank">{pw_id} · {pw_name}</a>') if pw_id else ""

    return f"""<!DOCTYPE html>
<html lang="{L}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_t(L,'Plan Clínico Nutrigenómico','Nutrigenomic Clinical Plan')} — {cond}</title>
<style>
:root{{--bg:#0f1116;--card:#171a21;--bd:#252a33;--txt:#e8eaed;--mut:#8b95a5;--gold:#c8a96e;--teal:#4fc3a1}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'DM Sans',-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.55;padding:24px}}
.wrap{{max-width:1000px;margin:0 auto}}
h1{{font-size:1.5rem;font-weight:600;margin-bottom:2px}}
.sub{{color:var(--mut);font-size:.9rem;margin-bottom:4px}}
.kegg{{color:var(--teal);font-size:.85rem;margin-bottom:16px}}
.kegg a,.glinks a,.ref a{{color:var(--teal);text-decoration:none}}
.nav{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}}
.pill{{background:var(--card);border:1px solid var(--bd);color:var(--mut);padding:7px 14px;border-radius:20px;font-size:.82rem;cursor:pointer;font-family:inherit}}
.pill.on{{background:var(--gold);color:#12151b;border-color:var(--gold);font-weight:600}}
.sec{{display:none;animation:f .3s}}.sec.vis{{display:block}}
@keyframes f{{from{{opacity:.4}}to{{opacity:1}}}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;margin-bottom:12px;overflow:hidden}}
.card-hd{{display:flex;gap:12px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--bd)}}
.ic{{font-size:1.5rem}}
.card-ti{{font-weight:600}}.card-su{{color:var(--mut);font-size:.8rem}}
.card-bd{{padding:12px 16px}}
.row{{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid var(--bd)}}
.row:last-child{{border-bottom:0}}
.tcat{{color:var(--gold);font-size:.7rem;font-weight:600;min-width:90px;text-transform:uppercase}}
.tname{{font-weight:600}}.tdose{{color:var(--teal);font-size:.85rem}}.tnote{{color:var(--mut);font-size:.8rem;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{text-align:left;color:var(--mut);font-weight:600;padding:8px;border-bottom:1px solid var(--bd)}}
td{{padding:8px;border-bottom:1px solid var(--bd);vertical-align:top}}
.muted{{color:var(--mut);font-size:.78rem}}
.warn{{color:#e34a5f;font-size:.8rem}}
.sev{{color:#12151b;font-weight:700;padding:2px 8px;border-radius:10px;font-size:.72rem}}
.pill-vip,.pill{{}}
.gcard{{display:inline-block;background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 14px;margin:4px}}
.gsym{{font-weight:700;color:var(--gold)}}
.glinks{{font-size:.75rem;margin-top:4px}}
.ref{{color:var(--mut);font-size:.72rem;margin-top:3px}}
.info{{background:rgba(200,169,110,.08);border-left:3px solid var(--gold);border-radius:6px;padding:10px 12px;margin-bottom:12px;font-size:.85rem}}
.foot{{color:var(--mut);font-size:.72rem;margin-top:20px;border-top:1px solid var(--bd);padding-top:12px}}
.badge{{display:inline-block;background:rgba(79,195,161,.12);color:var(--teal);padding:1px 8px;border-radius:10px;font-size:.65rem;margin-left:6px}}
</style></head><body><div class="wrap">
<h1>{_t(L,'Plan Clínico Nutrigenómico','Nutrigenomic Clinical Plan')}: {cond}</h1>
<div class="sub">NUTRIKEN · Cesar Manzo · {_t(L,'compilado de','compiled from')} MSK · KEGG · PharmGKB · NCBI</div>
<div class="kegg">{kegg_line}</div>
<div class="nav">{nav}</div>

<div id="cronograma" class="sec vis">
  <div class="info">{_esc(pw.get('context','')) or _t(L,'Cada intervención se sitúa en su ventana circadiana (cortisol, insulina, AMPK). El horario NO es arbitrario: optimiza el efecto y reduce interacciones con fármacos.','Each intervention is placed in its circadian window (cortisol, insulin, AMPK). Timing is NOT arbitrary: it optimizes effect and reduces drug interactions.')}</div>
  {crono_cards or '<div class="muted">—</div>'}
</div>

<div id="mecanismos" class="sec">
  <table><tr><th>{_t(L,'Intervención','Intervention')}</th><th>{_t(L,'Dosis','Dose')}</th><th>{_t(L,'Horario','Timing')}</th><th>{_t(L,'Mecanismo / evidencia','Mechanism / evidence')}</th><th>{_t(L,'Seguridad','Safety')}</th></tr>{mech_rows}</table>
</div>

<div id="farmacos" class="sec">
  <div class="info">{_t(L,'Cronoterapia: a qué hora tomar cada fármaco y por qué. Reduce efectos adversos e interacciones con los suplementos del cronograma.','Chronotherapy: when to take each drug and why. Reduces adverse effects and interactions with the schedule supplements.')}</div>
  {drug_rows or '<div class="muted">—</div>'}
</div>

<div id="nutrigenetica" class="sec">
  <h3 style="margin-bottom:10px">{_t(L,'Genes de la ruta','Pathway genes')}</h3>
  <div>{gene_cards or '<div class="muted">—</div>'}</div>
  <h3 style="margin:16px 0 8px">{_t(L,'Asociaciones gen–nutriente (PharmGKB)','Gene–nutrient associations (PharmGKB)')}</h3>
  <table><tr><th>{_t(L,'Gen','Gene')}</th><th>{_t(L,'Nutriente/fármaco','Nutrient/drug')}</th><th>{_t(L,'Asociación','Association')}</th><th>{_t(L,'Evidencia','Evidence')}</th></tr>{nutri_rows or '<tr><td colspan=4 class=muted>—</td></tr>'}</table>
</div>

<div id="interacciones" class="sec">
  <table><tr><th>{_t(L,'Combinación','Combination')}</th><th>{_t(L,'Severidad','Severity')}</th><th>{_t(L,'Efecto / mecanismo','Effect / mechanism')}</th><th>{_t(L,'Fuente','Source')}</th></tr>{inter_rows or '<tr><td colspan=4 class=muted>Sin interacciones detectadas</td></tr>'}</table>
</div>

<div id="resultados" class="sec">
  <ul style="padding-left:18px">{results or '<li class=muted>—</li>'}</ul>
  <h3 style="margin:16px 0 8px">{_t(L,'Bibliografía (Vancouver)','References (Vancouver)')}</h3>
  <ol style="padding-left:18px;font-size:.82rem">{refs_list or '<li class=muted>—</li>'}</ol>
</div>

<div class="foot">{disclaimer}</div>
</div>
<script>
function show(id,btn){{document.querySelectorAll('.sec').forEach(s=>s.classList.remove('vis'));
document.getElementById(id).classList.add('vis');
document.querySelectorAll('.pill').forEach(p=>p.classList.remove('on'));btn.classList.add('on');}}
</script></body></html>"""
