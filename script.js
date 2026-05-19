// ── GLOBALS ───────────────────────────────────────────────────────────────────
const API_URL = window.location.hostname.includes('github.io') 
  ? "https://kenryu007-nutriken.hf.space" 
  : "";
let lastResult = null;
const GENE_STORE = new Map();
let geneStoreIdx = 0;
const VIEW_TITLES = {
  clinical:'Condicion Clinica', gene:'Analisis de Gen',
  nutrient:'Suplemento / Hierba', report:'Editor de Informe'
};

// ── NAV ───────────────────────────────────────────────────────────────────────
function switchView(name) {
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('view-'+name).classList.add('active');
  document.getElementById('nav-'+name).classList.add('active');
  document.getElementById('view-title').textContent = VIEW_TITLES[name];
  
  if (name === 'report' && lastResult) populateReportFull();
}

function qt(tab, val) {
  switchView(tab);
  document.getElementById(tab+'-input').value = val;
  if (tab==='clinical') runClinical();
  else if (tab==='gene') runGene();
  else if (tab==='nutrient') runNutrient();
}

// ── TERMINAL ──────────────────────────────────────────────────────────────────
function log(tid, msg, type) {
  type = type || 'ok';
  var t = document.getElementById(tid);
  if (!t) return;
  var ts = new Date().toTimeString().slice(0,8);
  var d = document.createElement('div');
  d.className = 'log-line';
  d.innerHTML = '<span class="log-ts">'+ts+'</span><span class="log-msg '+type+'">'+msg+'</span>';
  t.appendChild(d);
  t.scrollTop = t.scrollHeight;
}

// ── LOADER ────────────────────────────────────────────────────────────────────
function showLoader(msg) {
  document.getElementById('loader-msg').textContent = msg;
  document.getElementById('loader').classList.remove('hidden');
}
function hideLoader() {
  document.getElementById('loader').classList.add('hidden');
}

// ── API ───────────────────────────────────────────────────────────────────────
async function post(url, body) {
  var r = await fetch(API_URL + url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    var e = await r.json().catch(function(){ return {detail: r.statusText}; });
    throw new Error(e.detail || 'Error servidor');
  }
  return r.json();
}

// ── GENE PILLS ────────────────────────────────────────────────────────────────
function makeGenePills(genes, containerId) {
  var container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  genes.forEach(function(g) {
    var key = 'g' + (++geneStoreIdx);
    GENE_STORE.set(key, g);
    var pill = document.createElement('div');
    pill.className = 'gene-pill';
    var ensgLabel = g.ensembl_id
      ? '<span style="font-family:var(--font-mono);font-size:9px;color:var(--teal);margin-top:2px">'+g.ensembl_id+'</span>'
      : '';
    pill.innerHTML =
      '<span class="gene-sym">'+g.symbol+'</span>'+
      '<span class="gene-loc">Chr'+(g.chromosome||'?')+' &middot; '+(g.location||'')+' </span>'+
      ensgLabel;
    pill.addEventListener('click', (function(k){ return function(){ openGP(k); }; })(key));
    container.appendChild(pill);
  });
}

function openGP(key) {
  var g = GENE_STORE.get(key);
  if (!g) return;

  document.getElementById('gp-name').textContent = g.symbol || '---';
  var body = document.getElementById('gene-panel-body');

  var html = '';
  if (g.name) html += '<div class="gp-field"><div class="gp-label">Nombre Completo</div><div class="gp-val">'+g.name+'</div></div>';
  if (g.chromosome) html += '<div class="gp-field"><div class="gp-label">Cromosoma</div><div class="gp-val gp-mono">Chr'+g.chromosome+'</div></div>';
  if (g.location) html += '<div class="gp-field"><div class="gp-label">Localizacion Genomica</div><div class="gp-val gp-mono">'+g.location+'</div></div>';
  if (g.ensembl_id) html += '<div class="gp-field"><div class="gp-label">Ensembl Gene ID</div><div class="gp-val gp-mono" style="color:var(--teal);font-size:13px">'+g.ensembl_id+'</div></div>';
  if (g.gene_id) html += '<div class="gp-field"><div class="gp-label">NCBI Gene ID</div><div class="gp-val gp-mono">'+g.gene_id+'</div></div>';
  if (g.summary) html += '<div class="gp-field"><div class="gp-label">Funcion Biologica</div><div class="gp-summary">'+g.summary+'</div></div>';

  var links = '';
  if (g.ncbi_url) links += '<a class="ext-link gold" href="'+g.ncbi_url+'" target="_blank"><i class="fas fa-external-link-alt"></i> NCBI Gene</a>';
  if (g.ensembl_url) links += '<a class="ext-link teal" href="'+g.ensembl_url+'" target="_blank"><i class="fas fa-dna"></i> Ensembl</a>';
  if (g.ensembl_id) links += '<a class="ext-link teal" style="opacity:0.8" href="https://www.ensembl.org/Homo_sapiens/Gene/Variation_Gene/Table?g='+g.ensembl_id+'" target="_blank"><i class="fas fa-project-diagram"></i> Ensembl Variantes</a>';
  if (g.snpedia_url) links += '<a class="ext-link" style="background:rgba(200,169,110,.1);border:1px solid rgba(200,169,110,.2);color:var(--gold)" href="'+g.snpedia_url+'" target="_blank"><i class="fas fa-flask"></i> SNPedia</a>';
  if (g.omim_url) links += '<a class="ext-link blue" href="'+g.omim_url+'" target="_blank"><i class="fas fa-database"></i> OMIM</a>';
  if (g.symbol) {
    links += '<a class="ext-link" style="background:rgba(79,195,161,.08);border:1px solid rgba(79,195,161,.15);color:var(--teal)" href="https://www.genecards.org/cgi-bin/carddisp.pl?gene='+g.symbol+'" target="_blank"><i class="fas fa-id-card"></i> GeneCards</a>';
    links += '<a class="ext-link" style="background:rgba(110,170,220,.08);border:1px solid rgba(110,170,220,.15);color:var(--blue)" href="https://clinicalgenome.org/gene/'+g.symbol+'" target="_blank"><i class="fas fa-heartbeat"></i> ClinGen</a>';
  }

  if (links) html += '<div class="gp-field"><div class="gp-label">Bases de Datos</div><div class="gp-links">'+links+'</div></div>';

  body.innerHTML = html;
  document.getElementById('gene-panel').classList.add('open');
}

function closeGenePanel() { document.getElementById('gene-panel').classList.remove('open'); }

// ── MODULO 1: CLINICO ─────────────────────────────────────────────────────────
async function runClinical() {
  var q = document.getElementById('clinical-input').value.trim();
  if (!q) return;
  var btn = document.getElementById('btn-clinical');
  btn.disabled = true;
  showLoader('Analizando...');
  log('term-clinical', 'Consulta: "'+q+'"', 'info');
  try {
    var d = await post('/api/clinical', {query: q});
    lastResult = d;
    renderClinical(d);
    populateReportFull();
  } catch(e) { log('term-clinical', 'Error: '+e.message, 'err'); }
  finally { hideLoader(); btn.disabled = false; }
}

function renderClinical(d) {
  document.getElementById('clinical-out').style.display = 'block';
  var rw = document.getElementById('risk-box-wrap');
  var html = '<div style="background:var(--bg1);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:20px">'+
    '<div style="font-size:13px;color:var(--text-dim);line-height:1.7">'+(d.description||'')+'</div></div>';

  if (d.drug_alerts && d.drug_alerts.length) {
    html += '<div class="risk-box"><div class="risk-title">Interacciones Farmaco-Nutriente</div>';
    d.drug_alerts.forEach(function(a) {
      html += `<div class="risk-item"><strong>${a.drug}</strong> + <strong>${a.herb}</strong>: ${a.alert}</div>`;
    });
    html += '</div>';
  }
  if (d.food_alerts && d.food_alerts.length) {
    html += '<div class="risk-box" style="background:rgba(245,166,35,.06);border-color:rgba(245,166,35,.2)"><div class="risk-title" style="color:var(--amber)">Interacciones con Alimentos</div>';
    d.food_alerts.forEach(function(a) {
      html += `<div class="risk-item"><strong>${a.food}</strong>: ${a.description}</div>`;
    });
    html += '</div>';
  }
  rw.innerHTML = html;

  if (d.genes && d.genes.length) { show('c-genes'); makeGenePills(d.genes, 'c-genes-body'); }
  if (d.pathway && d.pathway.name) {
    show('c-pathway');
    document.getElementById('c-pathway-body').innerHTML = `
      <div class="pathway-box">
        <div class="pathway-id">${d.pathway.id}</div><div class="pathway-name">${d.pathway.name}</div>
        <p class="pathway-desc">${(d.pathway.description||'').slice(0,400)}...</p>
        <a class="ext-link teal" href="${d.pathway.kegg_url}" target="_blank">Ver en KEGG</a>
      </div>`;
  }
  if (d.supplements) { show('c-supps'); renderSuppTabs('c-supp-tabs','c-supp-panels', d.supplements); }
  if (d.references) {
    show('c-refs');
    document.getElementById('c-refs-body').innerHTML = d.references.map(r => 
      `<tr><td>${r.title}</td><td>${r.authors} &middot; ${r.journal} &middot; ${r.year}</td><td><a class="ref-link" href="${r.url}" target="_blank">PMID ${r.pmid}</a></td></tr>`
    ).join('');
  }
}

// ── MODULO 2: GEN ─────────────────────────────────────────────────────────────
async function runGene() {
  var raw = document.getElementById('gene-input').value.trim();
  if (!raw) return;
  var genes = raw.split(',').map(function(g){ return g.trim().toUpperCase(); }).filter(Boolean);
  showLoader('Consultando genes...');
  log('term-gene', 'Genes: '+genes.join(', '), 'info');
  try {
    var d = await post('/api/gene', {genes: genes});
    lastResult = d;
    renderGene(d);
  } catch(e) { log('term-gene', 'Error: '+e.message, 'err'); }
  finally { hideLoader(); }
}
function renderGene(d) {
  document.getElementById('gene-out').style.display = 'block';
  if (d.genes_info) { show('g-info'); makeGenePills(d.genes_info, 'g-info-body'); }
  if (d.related_conditions) {
    show('g-cond');
    document.getElementById('g-cond-body').innerHTML = d.related_conditions.map(c => 
      `<div class="cond-item"><div class="cond-name">${c.condition}</div><div class="cond-risk">${c.matching_genes.join(', ')}</div></div>`
    ).join('');
  }
  if (d.supplements) { show('g-supps'); renderSuppTabs('g-supp-tabs','g-supp-panels', d.supplements); }
  if (d.references) {
    show('g-refs');
    document.getElementById('g-refs-body').innerHTML = d.references.map(r => 
      `<tr><td>${r.title}</td><td>${r.journal} &middot; ${r.year}</td><td><a class="ref-link" href="${r.url}" target="_blank">PubMed</a></td></tr>`
    ).join('');
  }
}

// ── MODULO 3: SUPLEMENTO ──────────────────────────────────────────────────────
async function runNutrient() {
  var nut = document.getElementById('nutrient-input').value.trim();
  if (!nut) return;
  showLoader('Buscando...');
  log('term-nutrient', 'Buscando: '+nut, 'info');
  try {
    var d = await post('/api/nutrient', {nutrient: nut});
    lastResult = d;
    renderNutrient(d);
  } catch(e) { log('term-nutrient', 'Error: '+e.message, 'err'); }
  finally { hideLoader(); }
}
function renderNutrient(d) {
  var h = d.msk_data;
  document.getElementById('nutrient-out').style.display = 'block';
  document.getElementById('n-herb-title').textContent = h.name;
  document.getElementById('n-herb-body').innerHTML = `<div style="padding:15px; background:var(--bg3); border-radius:8px">
    <h3 style="color:var(--gold)">${h.name}</h3><p style="font-size:12px; margin-top:10px">${h.clinical_summary||''}</p></div>`;
  if (d.references) {
    show('n-refs');
    document.getElementById('n-refs-body').innerHTML = d.references.map(r => 
      `<tr><td>${r.title}</td><td>${r.authors} &middot; ${r.year}</td><td><a class="ref-link" href="${r.url}" target="_blank">PubMed</a></td></tr>`
    ).join('');
  }
}

// ── UTILS ─────────────────────────────────────────────────────────────────────
function renderSuppTabs(tabsId, panelsId, supps) {
  if (!supps || !supps.length) return;
  document.getElementById(tabsId).innerHTML = supps.map(function(s,i) {
    return `<div class="supp-tab${i===0?' active':''}" onclick="swSupp('${tabsId}','${panelsId}',${i})">${s.name||'Sup.'}</div>`;
  }).join('');
  document.getElementById(panelsId).innerHTML = supps.map(function(s,i) {
    return `<div class="supp-panel${i===0?' active':''}" id="${panelsId}-${i}">
      <div class="supp-sec"><p class="supp-text" style="color:var(--text-dim)">${s.clinical_summary||'Sin datos.'}</p></div></div>`;
  }).join('');
}
function swSupp(tabsId, panelsId, i) {
  document.querySelectorAll('#'+tabsId+' .supp-tab').forEach(function(t,j){ t.classList.toggle('active', i===j); });
  document.querySelectorAll('#'+panelsId+' .supp-panel').forEach(function(p,j){ p.classList.toggle('active', i===j); });
}

// ── EDITOR ENGINE (KENRYU STYLE - FULL CONTENT & HYPERLINKS) ──────────────────
function populateReportFull() {
  if (!lastResult) return;
  const d = lastResult;
  const date = new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
  const id = 'NK-' + Math.random().toString(36).substr(2, 6).toUpperCase();

  const preview = document.getElementById('report-web-preview');
  document.getElementById('editor-empty').style.display = 'none';
  preview.style.display = 'block';
  preview.innerHTML = ''; 

  // PAGE 1: PORTADA Y ANÁLISIS GENÓMICO
  var p1 = document.createElement('div'); p1.className='a4-page';
  p1.innerHTML = `<div class="page-inner">
    <div class="report-header">
      <div><div class="report-title">INFORME DE ANÁLISIS<br>BIOMÉDICO NUTRICIONAL</div><div style="color:#1a3a6b; font-weight:700; font-size:12px; margin-top:5px">PLATAFORMA DE PRECISIÓN NUTRIKEN</div></div>
      <div class="report-meta"><div>EXPEDIENTE: <span class="meta-id-val">${id}</span></div><div>FECHA: ${date}</div><div>INVESTIGADOR: Cesar Manzo</div></div>
    </div>
    
    <section class="report-section">
      <div class="header-pdf">I. RESUMEN CLÍNICO EXPERTO</div>
      <div class="editable-block" contenteditable="true">
        <p>Este informe detalla la investigación bioinformática realizada para la consulta: <b>${d.query||'N/A'}</b>. El análisis integra datos de farmacogenómica, metabolismo molecular y evidencia clínica de suplementación.</p>
        <p>${d.description||'Análisis detallado basado en bases de datos moleculares.'}</p>
      </div>
    </section>

    <section class="report-section">
      <div class="header-pdf">II. PANEL DE BIOMARCADORES GENÓMICOS CORE</div>
      <div class="editable-block" contenteditable="true">
        <p style="font-size:10.5pt; color:#444">A continuación se presentan los genes clave identificados mediante el análisis de consenso. Estos biomarcadores regulan procesos críticos en la condición estudiada:</p>
        ${(d.genes||[]).map(g => `
          <div class="tarjeta-pdf">
            <p style="margin:0; font-size:14px; color: black;"><b>Gen: ${g.symbol}</b></p>
            <p style="margin:4px 0; font-size:11.5px; color: black;">${g.name || 'Información genómica indexada.'}</p>
            <p style="margin:0; font-size:11px; color:#1a3a6b;">
              <a href="${g.ncbi_url}" target="_blank" style="color:#1a3a6b; text-decoration:none">Ver Ficha NCBI: ${g.gene_id || 'N/A'}</a> &middot; 
              <a href="${g.ensembl_url}" target="_blank" style="color:#1a3a6b; text-decoration:none">Ensembl</a>
            </p>
          </div>
        `).join('') || '<p>Análisis de consenso genómico realizado sin detección de variantes críticas adicionales.</p>'}
      </div>
    </section>
    <div class="page-footer"><span>ID: ${id}</span><span>Página 1</span></div>
  </div>`;
  preview.appendChild(p1);

  // PAGE 2: RUTAS Y SUPLEMENTACIÓN
  if (d.pathway || d.supplements) {
    var p2 = document.createElement('div'); p2.className='a4-page';
    var pathwayHTML = d.pathway && d.pathway.name ? `
      <div class="tarjeta-pdf" style="border-left-color: #0d9488; background: #f0fdfa">
        <p style="margin:0; font-size:14px; color:#0f766e"><b>Ruta Metabólica: ${d.pathway.name}</b></p>
        <p style="margin:8px 0; font-size:11.5px; color: black;">${d.pathway.description || 'Proceso biológico regulado por los biomarcadores identificados.'}</p>
        <p style="margin:0; font-size:11px"><a href="${d.pathway.kegg_url}" target="_blank" style="color:#0d9488">Explorar en base de datos KEGG</a></p>
      </div>` : '';

    var suppHTML = (d.supplements || []).map(s => `
      <div class="tarjeta-pdf" style="border-left-color: #15803d;">
        <p style="margin:0; font-size:14px; color:#166534"><b>Suplementación: ${s.name}</b></p>
        <p style="margin:8px 0; font-size:11.5px; color: black; line-height:1.5">${(s.clinical_summary || '').slice(0, 800)}...</p>
        <p style="margin:0; font-size:11px"><a href="https://www.mskcc.org/cancer-care/integrative-medicine/herbs/${s.slug}" target="_blank" style="color:#15803d">Ver Evidencia Completa (MSKcc)</a></p>
      </div>
    `).join('');

    p2.innerHTML = `<div class="page-inner">
      <div class="report-header"><div><div class="report-title" style="font-size:24px">ANÁLISIS METABÓLICO Y EVIDENCIA</div></div></div>
      ${pathwayHTML ? `<section class="report-section"><div class="header-pdf">III. INTERCONEXIÓN METABÓLICA (KEGG)</div>${pathwayHTML}</section>` : ''}
      <section class="report-section">
        <div class="header-pdf">IV. EVIDENCIA CLÍNICA DE SUPLEMENTACIÓN</div>
        <div class="editable-block" contenteditable="true">
          <p style="font-size:10.5pt; color:#444">Investigación basada en el centro Memorial Sloan Kettering Cancer Center para asegurar la máxima seguridad y eficacia:</p>
          ${suppHTML || '<p>No se identificaron suplementos específicos con grado de evidencia alto para esta fase.</p>'}
        </div>
      </section>
      <div class="page-footer"><span>ID: ${id}</span><span>Página 2</span></div>
    </div>`;
    preview.appendChild(p2);
  }

  // PAGE 3: INTERACCIONES Y BIBLIOGRAFÍA
  if (d.drug_alerts || d.references) {
    var p3 = document.createElement('div'); p3.className='a4-page';
    var alertHTML = (d.drug_alerts || []).map(a => `<li style="color:#b91c1c; margin-bottom:12px; font-size:11pt"><b>${a.drug}</b> + ${a.herb}: ${a.alert}</li>`).join('');
    var refsHTML = (d.references || []).map(r => `
      <li style="margin-bottom:12px; font-size:10.5pt; line-height:1.5">
        <b>${r.authors}</b> (${r.year}). ${r.title}. <i>${r.journal||'Journal'}</i>. 
        <a href="${r.url}" target="_blank" style="color:#1f6feb; text-decoration:none">PMID: ${r.pmid}</a>
      </li>
    `).join('');

    p3.innerHTML = `<div class="page-inner">
      <div class="report-header"><div><div class="report-title" style="font-size:24px">SEGURIDAD Y BIBLIOGRAFÍA</div></div></div>
      ${alertHTML ? `<section class="report-section"><div class="header-pdf">V. ALERTAS DE INTERACCIÓN FARMACO-NUTRIENTE</div><ul style="padding-left:25px" contenteditable="true">${alertHTML}</ul></section>` : ''}
      <section class="report-section">
        <div class="header-pdf">VI. REFERENCIAS CIENTÍFICAS (PubMed / NCBI)</div>
        <div class="editable-block" contenteditable="true"><ol style="padding-left:25px">${refsHTML}</ol></div>
      </section>
      <footer class="report-footer" style="margin-top:auto">
        <p>Este informe clínico ha sido generado bajo criterios de medicina de precisión. Cesar Manzo.</p>
      </footer>
      <div class="page-footer"><span>ID: ${id}</span><span>Página 3</span></div>
    </div>`;
    preview.appendChild(p3);
  }
}

function exportToPDF() {
  if (!lastResult) return alert("Realice un análisis clínico primero.");
  const element = document.getElementById('report-web-preview');
  const opt = {
    margin: 0,
    filename: 'informe.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, letterRendering: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    pagebreak: { mode: 'css', after: '.a4-page' }
  };
  html2pdf().set(opt).from(element).save();
}

async function loadStats() {
  try {
    var r = await fetch('/api/stats');
    if (!r.ok) return;
    var s = await r.json();
    document.getElementById('stats-line').textContent = `Hierbas: ${s.herbs_in_cache} - Genes: ${s.genes_in_cache} - Consultas: ${s.total_queries}`;
  } catch(e) {}
}
function show(id) { var e = document.getElementById(id); if (e) e.style.display = ''; }
window.addEventListener('load', function() { loadStats(); setInterval(loadStats, 30000); });

document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    var a = document.activeElement;
    if (a && a.id === 'clinical-input')  { e.preventDefault(); runClinical(); }
    if (a && a.id === 'gene-input')      { e.preventDefault(); runGene(); }
    if (a && a.id === 'nutrient-input')  { e.preventDefault(); runNutrient(); }
  }
  if (e.key === 'Escape') closeGenePanel();
});

// Stubs for Nutriken compatibility
function fmt(cmd) { document.execCommand(cmd); }
function switchPanel(name) {
  document.querySelectorAll('.panel-tab').forEach(t => t.classList.toggle('active', t.textContent.toLowerCase().includes(name==='outline'?'esquema':name)));
  document.querySelectorAll('.panel-content').forEach(p => p.classList.toggle('active', p.id === 'panel-'+name));
}
function insertBlock() {}
function addPage() {}
function exportText() {}
function exportMarkdown() {}
function populateReport() { populateReportFull(); }
