// ── GLOBALS ───────────────────────────────────────────────────────────────────
let lastResult = null;
const VIEW_TITLES = {
  clinical:'Condición Clínica', gene:'Análisis de Gen',
  nutrient:'Suplemento / Hierba', report:'Editor de Informe'
};

// ── NAV ───────────────────────────────────────────────────────────────────────
function switchView(name) {
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('view-'+name).classList.add('active');
  document.getElementById('nav-'+name).classList.add('active');
  document.getElementById('view-title').textContent = VIEW_TITLES[name];
}

function qt(tab, val) {
  switchView(tab);
  document.getElementById(tab+'-input').value = val;
  if (tab==='clinical') runClinical();
  else if (tab==='gene') runGene();
  else if (tab==='nutrient') runNutrient();
}

// ── TERMINAL ──────────────────────────────────────────────────────────────────
function log(tid, msg, type='ok') {
  const t=document.getElementById(tid); if(!t) return;
  const ts=new Date().toTimeString().slice(0,8);
  const d=document.createElement('div'); d.className='log-line';
  d.innerHTML=`<span class="log-ts">${ts}</span><span class="log-msg ${type}">${msg}</span>`;
  t.appendChild(d); t.scrollTop=t.scrollHeight;
}

// ── LOADER ────────────────────────────────────────────────────────────────────
function showLoader(msg) {
  document.getElementById('loader-msg').textContent=msg;
  document.getElementById('loader').classList.remove('hidden');
}
function hideLoader() { document.getElementById('loader').classList.add('hidden'); }

// ── API ───────────────────────────────────────────────────────────────────────
async function post(url, body) {
  const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw new Error(e.detail||'Error servidor');}
  return r.json();
}

// ── MÓDULO 1: CLÍNICO ─────────────────────────────────────────────────────────
async function runClinical() {
  const q=document.getElementById('clinical-input').value.trim(); if(!q) return;
  const btn=document.getElementById('btn-clinical'); btn.disabled=true;
  showLoader('Buscando en MSK, NCBI y PubMed…');
  log('term-clinical',`Consulta: "${q}"`, 'info');
  try {
    const d=await post('/api/clinical',{query:q});
    lastResult=d;
    if(d.query_en && d.query_en!==q.toLowerCase()) log('term-clinical',`Traducido: "${d.query_en}"`, 'info');
    log('term-clinical',`Condición: ${d.condition}`, 'ok');
    log('term-clinical',`Suplementos MSK: ${(d.supplements||[]).map(s=>s.name).join(', ')||'—'}`, 'ok');
    log('term-clinical',`Alertas fármacos: ${(d.drug_alerts||[]).length} | Alimentos: ${(d.food_alerts||[]).length}`, 'ok');
    log('term-clinical',`Referencias PubMed: ${(d.references||[]).length}`, 'ok');
    renderClinical(d); populateReport(d);
  } catch(e) { log('term-clinical',`Error: ${e.message}`,'err'); alert(e.message); }
  finally { hideLoader(); btn.disabled=false; }
}

function renderClinical(d) {
  document.getElementById('clinical-out').style.display='block';

  // Description header
  const rw=document.getElementById('risk-box-wrap');
  rw.innerHTML=`<div style="background:var(--bg1);border:1px solid var(--border);border-radius:var(--r);padding:16px 20px;margin-bottom:20px">
    <div style="font-family:var(--font-mono);font-size:9px;color:var(--gold);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Descripción Clínica</div>
    <div style="font-size:13px;color:var(--text-dim);line-height:1.7">${d.description||''}</div>
  </div>`;

  // Drug alerts
  if(d.drug_alerts && d.drug_alerts.length) {
    rw.innerHTML+=`<div class="risk-box" style="margin-bottom:16px">
      <div class="risk-title">💊 Interacciones con Fármacos (fuente: MSK)</div>
      ${d.drug_alerts.map(a=>`<div class="risk-item">
        <strong style="color:var(--amber)">${a.drug}</strong> + <strong style="color:var(--gold)">${a.herb}</strong>
        <span style="color:var(--red);font-size:10px;margin-left:6px">${a.severity}</span>
        <div style="font-size:11px;margin-top:3px">${a.alert}</div>
        ${a.source?`<div style="font-size:10px;margin-top:2px"><a style="color:var(--teal)" href="${a.source}" target="_blank">Ver fuente MSK →</a></div>`:''}
      </div>`).join('')}
    </div>`;
  }

  // Food alerts
  if(d.food_alerts && d.food_alerts.length) {
    rw.innerHTML+=`<div class="risk-box" style="margin-bottom:16px;background:rgba(245,166,35,.06);border-color:rgba(245,166,35,.2)">
      <div class="risk-title" style="color:var(--amber)">🍊 Interacciones con Alimentos</div>
      ${d.food_alerts.map(a=>`<div class="risk-item">
        <strong style="color:var(--amber)">❌ ${a.food}</strong>
        <div style="font-size:11px;margin-top:2px">${a.description}</div>
        ${a.source?`<div style="font-size:10px"><a style="color:var(--teal)" href="${a.source}" target="_blank">Ver fuente MSK →</a></div>`:''}
      </div>`).join('')}
    </div>`;
  }

  // Related drugs
  if(d.drugs_related && d.drugs_related.length) {
    rw.innerHTML+=`<div style="background:var(--bg3);border:1px solid var(--border-md);border-radius:var(--r);padding:12px 16px;margin-bottom:16px">
      <div style="font-family:var(--font-mono);font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Fármacos Relacionados con esta Condición</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        ${d.drugs_related.map(dr=>`<span style="background:var(--blue-dim);border:1px solid rgba(110,170,220,.2);color:var(--blue);font-family:var(--font-mono);font-size:11px;padding:3px 10px;border-radius:4px">${dr}</span>`).join('')}
      </div>
    </div>`;
  }

  // Genes
  if(d.genes && d.genes.length) {
    show('c-genes');
    document.getElementById('c-genes-body').innerHTML=d.genes.map(g=>`
      <div class="gene-pill" onclick='openGP(${safeJSON(g)})'>
        <span class="gene-sym">${g.symbol}</span>
        <span class="gene-loc">Chr${g.chromosome||'?'} · ${g.location||''}</span>
      </div>`).join('');
  }

  // Pathway
  if(d.pathway && d.pathway.name) {
    show('c-pathway');
    const chips=(d.pathway.genes||[]).slice(0,14).map(g=>`<span class="pg-tag">${g.symbol}</span>`).join('');
    document.getElementById('c-pathway-body').innerHTML=`
      <div class="pathway-box">
        <div class="pathway-id">${d.pathway.id}</div>
        <div class="pathway-name">${d.pathway.name}</div>
        ${d.pathway.description?`<div class="pathway-desc">${d.pathway.description.slice(0,400)}…</div>`:''}
        ${chips?`<div class="pathway-genes">${chips}</div>`:''}
        <a class="ext-link teal" href="${d.pathway.kegg_url}" target="_blank">🗺 Ver ruta en KEGG</a>
        ${d.pathway.image_url?`<a class="ext-link gold" href="${d.pathway.image_url}" target="_blank">🖼 Imagen de ruta</a>`:''}
      </div>`;
  }

  // Supplements
  if(d.supplements && d.supplements.length) {
    show('c-supps'); renderSuppTabs('c-supp-tabs','c-supp-panels',d.supplements);
  }

  // References
  if(d.references && d.references.length) {
    show('c-refs');
    document.getElementById('c-refs-body').innerHTML=d.references.map(r=>`
      <tr><td>${r.title||'—'}</td>
      <td>${r.authors||''} · ${r.journal||''} · ${r.year||''}</td>
      <td><a class="ref-link" href="${r.url}" target="_blank">PMID ${r.pmid}</a></td></tr>`).join('');
  }
}

// ── MÓDULO 2: GEN ─────────────────────────────────────────────────────────────
async function runGene() {
  const raw=document.getElementById('gene-input').value.trim(); if(!raw) return;
  const genes=raw.split(',').map(g=>g.trim().toUpperCase()).filter(Boolean);
  showLoader(`Consultando ${genes.length} gen(es) — MyGene.info + NCBI…`);
  log('term-gene',`Genes: ${genes.join(', ')}`,'info');
  try {
    const d=await post('/api/gene',{genes});
    lastResult=d;
    log('term-gene',`Info obtenida: ${(d.genes_info||[]).length} genes`,'ok');
    log('term-gene',`Condiciones: ${(d.related_conditions||[]).length}`,'ok');
    renderGene(d);
  } catch(e){log('term-gene',`Error: ${e.message}`,'err');alert(e.message);}
  finally{hideLoader();}
}

function renderGene(d) {
  document.getElementById('gene-out').style.display='block';
  if(d.genes_info && d.genes_info.length){
    show('g-info');
    document.getElementById('g-info-body').innerHTML=d.genes_info.map(g=>`
      <div class="gene-pill" onclick='openGP(${safeJSON(g)})'>
        <span class="gene-sym">${g.symbol}</span>
        <span class="gene-loc">Chr${g.chromosome||'?'} · ${g.location||''}</span>
      </div>`).join('');
  }
  if(d.related_conditions && d.related_conditions.length){
    show('g-cond');
    document.getElementById('g-cond-body').innerHTML=d.related_conditions.map(c=>`
      <div class="cond-item">
        <div class="cond-name">${c.condition}</div>
        <div class="cond-genes">${c.matching_genes.map(g=>`<span class="cond-gene-tag">${g}</span>`).join('')}</div>
        ${c.drugs&&c.drugs.length?`<div style="font-size:10px;color:var(--blue);margin-top:4px">💊 ${c.drugs.slice(0,3).join(' · ')}</div>`:''}
      </div>`).join('');
  }
  if(d.supplements&&d.supplements.length){show('g-supps');renderSuppTabs('g-supp-tabs','g-supp-panels',d.supplements);}
  if(d.references&&d.references.length){
    show('g-refs');
    document.getElementById('g-refs-body').innerHTML=d.references.map(r=>`
      <tr><td>${r.title||'—'}</td><td>${r.journal||''} · ${r.year||''}</td>
      <td><a class="ref-link" href="${r.url}" target="_blank">PMID ${r.pmid}</a></td></tr>`).join('');
  }
}

// ── MÓDULO 3: SUPLEMENTO ──────────────────────────────────────────────────────
async function runNutrient() {
  const nut=document.getElementById('nutrient-input').value.trim(); if(!nut) return;
  showLoader(`Buscando "${nut}" en MSK…`);
  log('term-nutrient',`Consultando MSK: ${nut}`,'info');
  try {
    const d=await post('/api/nutrient',{nutrient:nut});
    lastResult=d;
    const h=d.msk_data;
    log('term-nutrient',`Encontrado: ${h.name}`,'ok');
    if(h.scientific_name) log('term-nutrient',`Nombre científico: ${h.scientific_name}`,'ok');
    log('term-nutrient',`Interacciones fármacos: ${(h.drug_interactions||[]).length}`,'ok');
    log('term-nutrient',`Referencias PubMed: ${(d.references||[]).length}`,'ok');
    renderNutrient(d);
  } catch(e){log('term-nutrient',`Error: ${e.message}`,'err');alert(e.message);}
  finally{hideLoader();}
}

function renderNutrient(d) {
  const h=d.msk_data;
  document.getElementById('nutrient-out').style.display='block';
  document.getElementById('n-herb-title').textContent=h.name||d.nutrient;

  const sections=[
    {id:'benefits',           label:'Beneficios',              cls:''},
    {id:'side_effects',       label:'Efectos Adversos',        cls:'danger'},
    {id:'warnings',           label:'Advertencias',            cls:'warn'},
    {id:'drug_interactions',  label:'Interacciones Fármacos',  cls:'danger'},
    {id:'food_interactions',  label:'Interacciones Alimentos', cls:'warn'},
    {id:'mechanism_of_action',label:'Mecanismo de Acción',     cls:''},
    {id:'clinical_summary',   label:'Resumen Clínico',         cls:''},
    {id:'contraindications',  label:'Contraindicaciones',      cls:'danger'},
    {id:'dosage',             label:'Dosificación',            cls:''},
  ].filter(s=>{const v=h[s.id]; return v&&(Array.isArray(v)?v.length>0:v.length>10);});

  const headerBox=`
    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0 18px;border-bottom:1px solid var(--border);margin-bottom:16px">
      <div>
        <div style="font-family:var(--font-serif);font-size:20px;color:var(--gold)">${h.name||d.nutrient}</div>
        ${h.scientific_name?`<div style="font-size:11px;color:var(--text-dim);font-style:italic;margin-top:3px">${h.scientific_name}</div>`:''}
        ${h.common_names&&h.common_names.length?`<div style="font-size:10px;color:var(--text-faint);margin-top:2px">${h.common_names.join(' · ')}</div>`:''}
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <a class="ext-link gold" href="${d.msk_url}" target="_blank">MSK →</a>
        <a class="ext-link blue" href="https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(d.nutrient)}" target="_blank">PubMed →</a>
      </div>
    </div>`;

  const tabs=sections.map((s,i)=>`<div class="supp-tab ${i===0?'active':''}" onclick="nhTab(${i},this)">${s.label}</div>`).join('');

  const panels=sections.map((s,i)=>{
    const v=h[s.id]; let inner='';
    if(Array.isArray(v)){
      inner=`<div class="supp-sec ${s.cls}"><div class="supp-sec-title">${s.label}</div>
        <ul class="supp-list">${v.map(x=>`<li>${x}</li>`).join('')}</ul></div>`;
    } else {
      inner=`<div class="moa-box"><div class="moa-title">${s.label}</div>
        <p class="supp-text">${v.slice(0,1200)}${v.length>1200?'…':''}</p></div>`;
    }
    return `<div class="supp-panel ${i===0?'active':''}" id="nh-panel-${i}">${inner}
      ${h.url?`<div style="margin-top:14px"><a class="ext-link gold" href="${h.url}" target="_blank">📖 Ficha completa en MSK →</a></div>`:''}
    </div>`;
  }).join('');

  document.getElementById('n-herb-body').innerHTML=headerBox+
    `<div class="supp-tabs" id="nh-tabs">${tabs}</div>`+panels;

  if(d.references&&d.references.length){
    show('n-refs');
    document.getElementById('n-refs-body').innerHTML=d.references.map(r=>`
      <tr><td>${r.title||'—'}</td><td>${r.journal||''} · ${r.year||''}</td>
      <td><a class="ref-link" href="${r.url}" target="_blank">PMID ${r.pmid}</a></td></tr>`).join('');
  }
}

function nhTab(i){
  document.querySelectorAll('#nh-tabs .supp-tab').forEach((t,j)=>t.classList.toggle('active',i===j));
  document.querySelectorAll('[id^="nh-panel-"]').forEach((p,j)=>p.classList.toggle('active',i===j));
}

// ── SUPP TABS ─────────────────────────────────────────────────────────────────
function renderSuppTabs(tabsId, panelsId, supps) {
  if(!supps||!supps.length) return;
  document.getElementById(tabsId).innerHTML=supps.map((s,i)=>
    `<div class="supp-tab ${i===0?'active':''}" onclick="swSupp('${tabsId}','${panelsId}',${i})">${s.name||'Sup.'+(i+1)}</div>`).join('');
  document.getElementById(panelsId).innerHTML=supps.map((s,i)=>`
    <div class="supp-panel ${i===0?'active':''}" id="${panelsId}-${i}">
      <div class="supp-grid">
        ${s.benefits&&s.benefits.length?`<div class="supp-sec"><div class="supp-sec-title">✅ Beneficios</div><ul class="supp-list">${s.benefits.slice(0,8).map(b=>`<li>${b}</li>`).join('')}</ul></div>`:''}
        ${s.side_effects&&s.side_effects.length?`<div class="supp-sec danger"><div class="supp-sec-title">⚠ Efectos Adversos</div><ul class="supp-list">${s.side_effects.slice(0,8).map(e=>`<li>${e}</li>`).join('')}</ul></div>`:''}
        ${s.warnings&&s.warnings.length?`<div class="supp-sec warn"><div class="supp-sec-title">⚠ Advertencias</div><ul class="supp-list">${s.warnings.slice(0,6).map(w=>`<li>${w}</li>`).join('')}</ul></div>`:''}
        ${s.drug_interactions&&s.drug_interactions.length?`<div class="supp-sec danger"><div class="supp-sec-title">💊 Interacciones con Fármacos</div><ul class="supp-list">${s.drug_interactions.slice(0,8).map(x=>`<li>${x}</li>`).join('')}</ul></div>`:''}
        ${s.food_interactions&&s.food_interactions.length?`<div class="supp-sec warn"><div class="supp-sec-title">🍊 Interacciones con Alimentos</div><ul class="supp-list">${s.food_interactions.slice(0,6).map(x=>`<li>${x}</li>`).join('')}</ul></div>`:''}
      </div>
      ${s.mechanism_of_action?`<div class="moa-box" style="margin-top:14px"><div class="moa-title">⚙ Mecanismo de Acción</div><p class="supp-text">${s.mechanism_of_action.slice(0,600)}…</p></div>`:''}
      ${s.contraindications?`<div class="moa-box" style="margin-top:10px;background:rgba(224,92,92,.05);border-color:rgba(224,92,92,.15)"><div class="moa-title" style="color:var(--red)">🚫 Contraindicaciones</div><p class="supp-text">${s.contraindications.slice(0,400)}</p></div>`:''}
      ${s.url?`<div style="margin-top:14px"><a class="ext-link gold" href="${s.url}" target="_blank">📖 Ver ficha completa en MSK →</a></div>`:''}
    </div>`).join('');
}

function swSupp(tabsId, panelsId, i) {
  document.querySelectorAll(`#${tabsId} .supp-tab`).forEach((t,j)=>t.classList.toggle('active',i===j));
  document.querySelectorAll(`#${panelsId} .supp-panel`).forEach((p,j)=>p.classList.toggle('active',i===j));
}

// ── GENE DETAIL PANEL — con Ensembl correcto ──────────────────────────────────
function safeJSON(obj){return JSON.stringify(obj).replace(/'/g,"&#39;");}

function openGP(gene) {
  if(typeof gene==='string') try{gene=JSON.parse(gene);}catch(e){}
  document.getElementById('gp-name').textContent=gene.symbol||'—';
  document.getElementById('gene-panel-body').innerHTML=`
    <div class="gp-field"><div class="gp-label">Nombre Completo</div><div class="gp-val">${gene.name||'—'}</div></div>
    <div class="gp-field"><div class="gp-label">Cromosoma</div><div class="gp-val gp-mono">Chr${gene.chromosome||'?'} · ${gene.location||'—'}</div></div>
    ${gene.ensembl_id?`<div class="gp-field"><div class="gp-label">Ensembl ID</div><div class="gp-val gp-mono">${gene.ensembl_id}</div></div>`:''}
    ${gene.summary?`<div class="gp-field"><div class="gp-label">Función Biológica</div><div class="gp-summary">${gene.summary.slice(0,600)}…</div></div>`:''}
    <div class="gp-field"><div class="gp-label">Explorar en</div>
      <div class="gp-links">
        <a class="ext-link gold" href="${gene.ncbi_url||'#'}" target="_blank"><i class="fas fa-external-link-alt"></i> NCBI Gene</a>
        ${gene.ensembl_url?`<a class="ext-link teal" href="${gene.ensembl_url}" target="_blank"><i class="fas fa-dna"></i> Ensembl ${gene.ensembl_id||''}</a>`:''}
        <a class="ext-link" style="background:rgba(200,169,110,.1);border:1px solid rgba(200,169,110,.2);color:var(--gold)" href="${gene.snpedia_url||'#'}" target="_blank"><i class="fas fa-flask"></i> SNPedia</a>
        <a class="ext-link blue" href="${gene.omim_url||'#'}" target="_blank"><i class="fas fa-database"></i> OMIM</a>
      </div>
    </div>`;
  document.getElementById('gene-panel').classList.add('open');
}
function closeGenePanel(){document.getElementById('gene-panel').classList.remove('open');}

// ── EDITOR ────────────────────────────────────────────────────────────────────
function fmt(cmd){document.execCommand(cmd);}
function switchPanel(name){
  document.querySelectorAll('.panel-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel-content').forEach(p=>{p.classList.remove('active');if(p.id==='panel-'+name)p.classList.add('active');});
  event.currentTarget.classList.add('active');
}
function addPage(){
  const cc=document.getElementById('report-canvas-content');
  const n=cc.querySelectorAll('.a4-page').length+1;
  const p=document.createElement('div');p.className='a4-page';
  p.innerHTML=`<div class="page-inner"><div class="report-section"><div class="section-heading">Contenido adicional</div><div class="editable-block" contenteditable="true" data-placeholder="Escribe aquí…"></div></div><div class="page-footer"><span>NutriKen v2.0 — Cesar Manzo</span><span>MSK · NCBI · KEGG · PubMed</span><span>Página ${n}</span></div></div>`;
  cc.appendChild(p);p.scrollIntoView({behavior:'smooth'});
}
function insertBlock(type){
  const sel=window.getSelection();if(!sel.rangeCount)return;
  const range=sel.getRangeAt(0);let el;
  if(type==='note'){el=document.createElement('div');el.style.cssText='background:#fffde7;border-left:4px solid #fbc02d;padding:12px;margin:12px 0;font-style:italic';el.contentEditable='true';el.textContent='Nota clínica…';}
  else if(type==='gene'){el=document.createElement('div');el.className='gene-block';el.innerHTML='<div class="gene-block-name" contenteditable="true">GEN</div><div class="gene-block-text" contenteditable="true">Descripción…</div>';}
  if(el)range.insertNode(el);
}
function exportText(){
  const blob=new Blob([document.getElementById('report-canvas-content').innerText],{type:'text/plain'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`NutriKen_${Date.now()}.txt`;a.click();
}
function exportMarkdown(){
  const txt=document.getElementById('report-canvas-content').innerText;
  const blob=new Blob(['# Informe NutriKen\n\n'+txt],{type:'text/markdown'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`NutriKen_${Date.now()}.md`;a.click();
}

// ── POPULATE REPORT ───────────────────────────────────────────────────────────
function populateReport(d) {
  const cc=document.getElementById('report-canvas-content');
  const ee=document.getElementById('editor-empty');
  ee.style.display='none';cc.style.display='block';
  const now=new Date().toLocaleDateString('es-ES',{year:'numeric',month:'long',day:'numeric'});
  const id='NK-'+Date.now().toString().slice(-6);
  const genesHTML=(d.genes||[]).map(g=>`<div class="gene-block"><div class="gene-block-name">${g.symbol} — Chr${g.chromosome||'?'}</div><div class="gene-block-text">${g.name||''}<br/>${g.summary?g.summary.slice(0,200)+'…':''}</div></div>`).join('');
  const suppsHTML=(d.supplements||[]).map(s=>`<p><strong>${s.name}</strong>${s.scientific_name?` <em>(${s.scientific_name})</em>`:''}</p>${s.benefits&&s.benefits.length?`<p style="font-size:11px;color:#555">Beneficios: ${s.benefits.slice(0,3).join('; ')}</p>`:''}`).join('<hr style="border:none;border-top:1px solid #ddd;margin:8px 0"/>');
  const drugsHTML=(d.drug_alerts||[]).map(a=>`<li><strong>${a.drug}</strong> + ${a.herb}: ${a.alert.slice(0,150)}</li>`).join('');
  const foodHTML=(d.food_alerts||[]).map(a=>`<li>❌ <strong>${a.food}</strong>: ${a.description}</li>`).join('');
  const refsHTML=`<ol style="padding-left:18px;font-size:11px;line-height:1.8">`+(d.references||[]).map(r=>`<li>${r.authors||''} (${r.year||''}). ${r.title||''}. <em>${r.journal||''}</em>. PMID: ${r.pmid}</li>`).join('')+'</ol>';

  cc.innerHTML=`<div class="a4-page" id="page-1"><div class="page-inner">
    <div class="report-header">
      <div><div class="report-title">NutriKen</div><div class="report-subtitle">Informe Bioinformático Nutricional</div></div>
      <div class="report-meta"><div class="meta-id">${id}</div><div>${now}</div><div>Cesar Manzo</div></div>
    </div>
    <div class="report-section"><div class="section-heading">Consulta</div>
      <div class="editable-block" contenteditable="true">${d.query||''}</div></div>
    <div class="report-section"><div class="section-heading">Descripción Clínica</div>
      <div class="editable-block" contenteditable="true">${d.description||''}</div></div>
    <div class="report-section"><div class="section-heading">Genes Involucrados</div>
      <div contenteditable="true">${genesHTML||'<p style="color:#aaa;font-style:italic">—</p>'}</div></div>
    ${drugsHTML?`<div class="report-section"><div class="section-heading">Interacciones con Fármacos</div>
      <ul contenteditable="true" style="padding-left:18px;font-size:11px">${drugsHTML}</ul></div>`:''}
    ${foodHTML?`<div class="report-section"><div class="section-heading">Interacciones con Alimentos</div>
      <ul contenteditable="true" style="padding-left:18px;font-size:11px">${foodHTML}</ul></div>`:''}
    <div class="report-section"><div class="section-heading">Suplementos con Evidencia MSK</div>
      <div contenteditable="true">${suppsHTML||'<p style="color:#aaa;font-style:italic">—</p>'}</div></div>
    <div class="report-section"><div class="section-heading">Referencias Científicas (PubMed)</div>
      <div contenteditable="true">${refsHTML}</div></div>
    <div class="report-section"><div class="section-heading">Recomendación Nutricional</div>
      <div class="editable-block" contenteditable="true" data-placeholder="Escribe aquí la recomendación nutricional personalizada basada en los datos…"></div></div>
    <button class="add-section-btn" onclick="addPage()">+ Agregar página</button>
    <div class="page-footer"><span>NutriKen v2.0 — Cesar Manzo</span><span>MSK · NCBI · KEGG · PubMed</span><span>Página 1</span></div>
  </div></div>`;
}

// ── STATS ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const r=await fetch('/api/stats');if(!r.ok)return;
    const s=await r.json();
    document.getElementById('stats-line').textContent=`Hierbas: ${s.herbs_in_cache} · Genes: ${s.genes_in_cache} · Consultas: ${s.total_queries}`;
  } catch(e){}
}

function show(id){const e=document.getElementById(id);if(e)e.style.display='';}

document.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){
    const a=document.activeElement;
    if(a&&a.id==='clinical-input'){e.preventDefault();runClinical();}
    if(a&&a.id==='gene-input'){e.preventDefault();runGene();}
    if(a&&a.id==='nutrient-input'){e.preventDefault();runNutrient();}
  }
  if(e.key==='Escape')closeGenePanel();
});

window.addEventListener('load',()=>{loadStats();setInterval(loadStats,30000);});

