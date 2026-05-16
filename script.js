// ── GLOBALS ───────────────────────────────────────────────────────────────────
let lastResult = null;
const TITLES = {
  clinical: 'Condición Clínica',
  gene: 'Análisis de Gen',
  nutrient: 'Suplemento / Hierba',
  report: 'Editor de Informe'
};

// ── NAVIGATION ────────────────────────────────────────────────────────────────
function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
  document.getElementById('topbar-title').textContent = TITLES[name];
}

// ── QUICK TAG FILL ────────────────────────────────────────────────────────────
function qt(tab, value) {
  switchView(tab);
  document.getElementById(tab + '-input').value = value;
  if (tab === 'clinical') runClinical();
  else if (tab === 'gene') runGene();
  else if (tab === 'nutrient') runNutrient();
}

// ── TERMINAL LOG ──────────────────────────────────────────────────────────────
function log(termId, msg, type = 'ok') {
  const t = document.getElementById(termId);
  if (!t) return;
  const now = new Date();
  const ts = now.toTimeString().slice(0,8);
  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `<span class="log-ts">${ts}</span><span class="log-msg ${type}">${msg}</span>`;
  t.appendChild(line);
  t.scrollTop = t.scrollHeight;
}

// ── LOADING ───────────────────────────────────────────────────────────────────
function showLoading(msg) {
  document.getElementById('loading-msg').textContent = msg;
  document.getElementById('loading').style.display = 'flex';
}
function hideLoading() {
  document.getElementById('loading').style.display = 'none';
}

// ── API BASE ──────────────────────────────────────────────────────────────────
const API = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
  ? 'http://localhost:7860'
  : '';

async function apiPost(endpoint, body) {
  const r = await fetch(API + endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({detail: r.statusText}));
    throw new Error(err.detail || 'Error en el servidor');
  }
  return r.json();
}

// ── MÓDULO 1: CONDICIÓN CLÍNICA ───────────────────────────────────────────────
async function runClinical() {
  const query = document.getElementById('clinical-input').value.trim();
  if (!query) return;

  const btn = document.getElementById('btn-clinical');
  btn.disabled = true;
  showLoading('Analizando condición clínica…');
  log('terminal-clinical', `Iniciando análisis: "${query}"`, 'info');
  log('terminal-clinical', 'Consultando mapa clínico…', 'ok');

  try {
    const data = await apiPost('/api/clinical', {query});
    lastResult = data;
    log('terminal-clinical', `Condición identificada: ${data.condition}`, 'ok');
    log('terminal-clinical', `Genes encontrados: ${(data.genes||[]).map(g=>g.symbol).join(', ')||'—'}`, 'ok');
    log('terminal-clinical', `Suplementos MSK: ${(data.supplements||[]).map(s=>s.name).join(', ')||'—'}`, 'ok');
    log('terminal-clinical', `Referencias PubMed: ${(data.references||[]).length}`, 'ok');
    renderClinical(data);
    populateReport(data);
  } catch(e) {
    log('terminal-clinical', `Error: ${e.message}`, 'err');
    alert(e.message);
  } finally {
    hideLoading();
    btn.disabled = false;
  }
}

function renderClinical(data) {
  document.getElementById('clinical-results').style.display = 'block';

  // Risks
  if (data.risks && data.risks.length) {
    const riskEl = document.getElementById('risk-section');
    riskEl.style.display = 'block';
    riskEl.innerHTML = `
      <div class="risk-box">
        <div class="risk-box-title">⚠ Riesgos y Consideraciones Clínicas</div>
        ${data.risks.map(r => `<div class="risk-item">${r}</div>`).join('')}
      </div>`;
  }

  // Genes
  if (data.genes && data.genes.length) {
    document.getElementById('genes-card').style.display = 'block';
    document.getElementById('genes-content').innerHTML = data.genes.map(g => `
      <div class="gene-pill" onclick="openGenePanel(${JSON.stringify(g).replace(/"/g,'&quot;')})">
        <span class="gene-sym">${g.symbol}</span>
        <span class="gene-chr">Chr ${g.chromosome||'?'} · ${g.location||''}</span>
      </div>
    `).join('');
  }

  // Pathway
  if (data.pathway && data.pathway.name) {
    document.getElementById('pathway-card').style.display = 'block';
    const geneChips = (data.pathway.genes||[]).slice(0,14).map(g =>
      `<span class="pathway-gene-tag">${g.symbol}</span>`).join('');
    document.getElementById('pathway-content').innerHTML = `
      <div class="pathway-box">
        <div class="pathway-id">${data.pathway.id}</div>
        <div class="pathway-name">${data.pathway.name}</div>
        ${data.pathway.description ? `<div class="pathway-desc">${data.pathway.description.slice(0,300)}…</div>` : ''}
        ${geneChips ? `<div class="pathway-genes">${geneChips}</div>` : ''}
        <a class="ext-btn" href="${data.pathway.kegg_url}" target="_blank">🗺 Ver en KEGG →</a>
      </div>`;
  }

  // Supplements
  renderSuppTabs('supp-tabs', 'supp-panels', data.supplements || []);
  if (data.supplements && data.supplements.length) {
    document.getElementById('supps-card').style.display = 'block';
  }

  // References
  if (data.references && data.references.length) {
    document.getElementById('refs-card').style.display = 'block';
    document.getElementById('refs-body').innerHTML = data.references.map(r => `
      <tr>
        <td>${r.title||'—'}</td>
        <td>${r.authors||''} · ${r.journal||''} · ${r.year||''}</td>
        <td><a class="ref-link" href="${r.url}" target="_blank">PubMed ${r.pmid}</a></td>
      </tr>`).join('');
  }
}

// ── MÓDULO 2: GEN ─────────────────────────────────────────────────────────────
async function runGene() {
  const raw = document.getElementById('gene-input').value.trim();
  if (!raw) return;
  const genes = raw.split(',').map(g => g.trim().toUpperCase()).filter(Boolean);
  showLoading(`Consultando ${genes.length} gen(es) en NCBI…`);
  log('terminal-gene', `Genes: ${genes.join(', ')}`, 'info');

  try {
    const data = await apiPost('/api/gene', {genes});
    lastResult = data;
    log('terminal-gene', `Info NCBI obtenida: ${(data.genes_info||[]).length} genes`, 'ok');
    log('terminal-gene', `Condiciones relacionadas: ${(data.related_conditions||[]).length}`, 'ok');
    renderGene(data);
  } catch(e) {
    log('terminal-gene', `Error: ${e.message}`, 'err');
    alert(e.message);
  } finally {
    hideLoading();
  }
}

function renderGene(data) {
  document.getElementById('gene-results').style.display = 'block';

  // Gene pills
  if (data.genes_info && data.genes_info.length) {
    document.getElementById('gene-info-card').style.display = 'block';
    document.getElementById('gene-pills').innerHTML = data.genes_info.map(g => `
      <div class="gene-pill" onclick="openGenePanel(${JSON.stringify(g).replace(/"/g,'&quot;')})">
        <span class="gene-sym">${g.symbol}</span>
        <span class="gene-chr">${g.name ? g.name.slice(0,28)+'…' : ''}</span>
      </div>
    `).join('');
  }

  // Related conditions
  if (data.related_conditions && data.related_conditions.length) {
    document.getElementById('cond-card').style.display = 'block';
    document.getElementById('cond-content').innerHTML = data.related_conditions.map(c => `
      <div class="cond-item">
        <div class="cond-name">${c.condition}</div>
        <div class="cond-genes">${c.matching_genes.map(g => `<span class="cond-gene-tag">${g}</span>`).join('')}</div>
        ${c.risks.length ? `<div class="cond-risk">⚠ ${c.risks[0]}</div>` : ''}
      </div>`).join('');
  }

  // Supplements
  if (data.supplements && data.supplements.length) {
    document.getElementById('gene-supps-card').style.display = 'block';
    renderSuppTabs('gene-supp-tabs', 'gene-supp-panels', data.supplements);
  }

  // References
  if (data.references && data.references.length) {
    document.getElementById('gene-refs-card').style.display = 'block';
    document.getElementById('gene-refs-body').innerHTML = data.references.map(r => `
      <tr>
        <td>${r.title||'—'}</td>
        <td>${r.journal||''} · ${r.year||''}</td>
        <td><a class="ref-link" href="${r.url}" target="_blank">PubMed ${r.pmid}</a></td>
      </tr>`).join('');
  }
}

// ── MÓDULO 3: SUPLEMENTO ──────────────────────────────────────────────────────
async function runNutrient() {
  const nutrient = document.getElementById('nutrient-input').value.trim();
  if (!nutrient) return;
  showLoading(`Buscando "${nutrient}" en MSK…`);
  log('terminal-nutrient', `Consultando MSK: ${nutrient}`, 'info');

  try {
    const data = await apiPost('/api/nutrient', {nutrient});
    lastResult = data;
    log('terminal-nutrient', `Datos MSK obtenidos: ${data.msk_data.name}`, 'ok');
    if (data.msk_data.scientific_name)
      log('terminal-nutrient', `Nombre científico: ${data.msk_data.scientific_name}`, 'ok');
    log('terminal-nutrient', `Referencias PubMed: ${(data.references||[]).length}`, 'ok');
    renderNutrient(data);
  } catch(e) {
    log('terminal-nutrient', `Error: ${e.message}`, 'err');
    alert(e.message);
  } finally {
    hideLoading();
  }
}

function renderNutrient(data) {
  const herb = data.msk_data;
  document.getElementById('nutrient-results').style.display = 'block';
  document.getElementById('herb-card-title').textContent = herb.name || data.nutrient;

  // Section tabs
  const sections = [
    {id:'benefits', label:'Beneficios'},
    {id:'side_effects', label:'Efectos Adversos'},
    {id:'warnings', label:'Advertencias'},
    {id:'drug_interactions', label:'Interacciones'},
    {id:'mechanism_of_action', label:'Mecanismo'},
    {id:'clinical_summary', label:'Resumen Clínico'},
  ].filter(s => {
    const v = herb[s.id];
    return v && (Array.isArray(v) ? v.length > 0 : v.length > 10);
  });

  document.getElementById('herb-tabs-header').innerHTML = sections.map((s,i) =>
    `<div class="supp-tab ${i===0?'active':''}" onclick="switchHerbTab(${i},this)">${s.label}</div>`
  ).join('');

  document.getElementById('herb-main-content').innerHTML = sections.map((s,i) => {
    const v = herb[s.id];
    let content = '';
    if (Array.isArray(v)) {
      const cls = s.id === 'side_effects' || s.id === 'drug_interactions' ? 'danger' :
                  s.id === 'warnings' ? 'warning' : '';
      content = `<div class="supp-section ${cls}">
        <ul class="supp-list">${v.map(x=>`<li>${x}</li>`).join('')}</ul>
      </div>`;
    } else {
      const cls = s.id === 'clinical_summary' ? '' : '';
      content = `<div class="supp-moa"><div class="supp-moa-title">${s.label}</div><p class="supp-text">${v.slice(0,900)}${v.length>900?'…':''}</p></div>`;
    }
    return `<div class="supp-panel ${i===0?'active':''}" id="herb-panel-${i}">${content}
      ${herb.url ? `<div style="margin-top:14px"><a class="ext-btn gold" href="${herb.url}" target="_blank">📖 Ver ficha completa en MSK →</a></div>` : ''}
    </div>`;
  }).join('');

  // Header info
  const header = `
    <div style="margin-bottom:16px; padding:14px 18px; background:var(--bg3); border-radius:var(--r); display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-family:var(--font-serif);font-size:18px;color:var(--gold)">${herb.name||data.nutrient}</div>
        ${herb.scientific_name ? `<div style="font-size:11px;color:var(--text-dim);font-style:italic;margin-top:2px">${herb.scientific_name}</div>` : ''}
        ${herb.common_names && herb.common_names.length ? `<div style="font-size:10px;color:var(--text-faint);margin-top:2px">${herb.common_names.join(' · ')}</div>` : ''}
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <a class="ext-btn" href="${data.msk_url}" target="_blank">MSK →</a>
        <a class="ext-btn blue" href="https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(data.nutrient)}" target="_blank">PubMed →</a>
      </div>
    </div>`;

  document.getElementById('herb-main-content').insertAdjacentHTML('afterbegin', header);

  // References
  if (data.references && data.references.length) {
    document.getElementById('nutrient-refs-card').style.display = 'block';
    document.getElementById('nutrient-refs-body').innerHTML = data.references.map(r => `
      <tr>
        <td>${r.title||'—'}</td>
        <td>${r.journal||''} · ${r.year||''}</td>
        <td><a class="ref-link" href="${r.url}" target="_blank">PubMed ${r.pmid}</a></td>
      </tr>`).join('');
  }
}

function switchHerbTab(idx, el) {
  document.querySelectorAll('#herb-tabs-header .supp-tab').forEach((t,i) => t.classList.toggle('active', i===idx));
  document.querySelectorAll('#herb-main-content .supp-panel').forEach((p,i) => p.classList.toggle('active', i===idx));
}

// ── SUPP TABS (shared) ────────────────────────────────────────────────────────
function renderSuppTabs(tabsId, panelsId, supplements) {
  if (!supplements || !supplements.length) return;
  document.getElementById(tabsId).innerHTML = supplements.map((s,i) =>
    `<div class="supp-tab ${i===0?'active':''}" onclick="switchSuppTab('${tabsId}','${panelsId}',${i},this)">${s.name||s.slug||'Suplemento '+(i+1)}</div>`
  ).join('');

  document.getElementById(panelsId).innerHTML = supplements.map((s,i) => `
    <div class="supp-panel ${i===0?'active':''}" id="${panelsId}-${i}">
      <div class="supp-grid">
        ${s.benefits && s.benefits.length ? `
        <div class="supp-section">
          <div class="supp-section-title">Beneficios</div>
          <ul class="supp-list">${s.benefits.slice(0,7).map(b=>`<li>${b}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.side_effects && s.side_effects.length ? `
        <div class="supp-section danger">
          <div class="supp-section-title">Efectos Adversos</div>
          <ul class="supp-list">${s.side_effects.slice(0,7).map(e=>`<li>${e}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.warnings && s.warnings.length ? `
        <div class="supp-section warning">
          <div class="supp-section-title">Advertencias</div>
          <ul class="supp-list">${s.warnings.slice(0,5).map(w=>`<li>${w}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.drug_interactions && s.drug_interactions.length ? `
        <div class="supp-section danger">
          <div class="supp-section-title">Interacciones Farmacológicas</div>
          <ul class="supp-list">${s.drug_interactions.slice(0,5).map(d=>`<li>${d}</li>`).join('')}</ul>
        </div>` : ''}
      </div>
      ${s.mechanism_of_action ? `
      <div class="supp-moa" style="margin-top:14px">
        <div class="supp-moa-title">Mecanismo de Acción</div>
        <p class="supp-text">${s.mechanism_of_action.slice(0,500)}…</p>
      </div>` : ''}
      ${s.url ? `<div style="margin-top:14px"><a class="ext-btn gold" href="${s.url}" target="_blank">📖 Ver en MSK →</a></div>` : ''}
    </div>
  `).join('');
}

function switchSuppTab(tabsId, panelsId, idx, el) {
  document.querySelectorAll(`#${tabsId} .supp-tab`).forEach((t,i) => t.classList.toggle('active', i===idx));
  document.querySelectorAll(`#${panelsId} .supp-panel`).forEach((p,i) => p.classList.toggle('active', i===idx));
}

// ── GENE DETAIL PANEL ─────────────────────────────────────────────────────────
function openGenePanel(gene) {
  if (typeof gene === 'string') gene = JSON.parse(gene.replace(/&quot;/g, '"'));
  document.getElementById('gp-name').textContent = gene.symbol;
  document.getElementById('gp-body').innerHTML = `
    <div class="gp-field">
      <div class="gp-label">Nombre Completo</div>
      <div class="gp-value">${gene.name||'—'}</div>
    </div>
    <div class="gp-field">
      <div class="gp-label">Localización</div>
      <div class="gp-value mono">Chr ${gene.chromosome||'?'} · ${gene.location||'—'}</div>
    </div>
    ${gene.summary ? `
    <div class="gp-field">
      <div class="gp-label">Función Biológica</div>
      <div class="gp-summary">${gene.summary.slice(0,600)}…</div>
    </div>` : ''}
    <div class="gp-field">
      <div class="gp-label">Explorar en</div>
      <div class="gp-links">
        <a class="ext-btn gold" href="${gene.ncbi_url}" target="_blank">NCBI Gene →</a>
        <a class="ext-btn" href="https://www.snpedia.com/index.php/${gene.symbol}" target="_blank">SNPedia →</a>
        <a class="ext-btn blue" href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?q=${gene.symbol}" target="_blank">Ensembl →</a>
        <a class="ext-btn" style="background:var(--green-dim);border-color:rgba(63,185,80,.2);color:var(--green)" href="https://omim.org/search?index=entry&search=${gene.symbol}" target="_blank">OMIM →</a>
      </div>
    </div>
  `;
  document.getElementById('gene-detail-panel').classList.add('open');
}
function closeGenePanel() {
  document.getElementById('gene-detail-panel').classList.remove('open');
}

// ── POPULATE REPORT ───────────────────────────────────────────────────────────
function populateReport(data) {
  const q = document.getElementById('report-query');
  if (q) q.textContent = data.query || '';
  const d = document.getElementById('report-desc');
  if (d) d.textContent = data.description || '';

  // Genes
  const genesEl = document.getElementById('report-genes');
  if (genesEl && data.genes && data.genes.length) {
    genesEl.innerHTML = data.genes.map(g => `
      <div class="gene-block">
        <div class="gene-block-name">${g.symbol}</div>
        <div class="gene-block-text">${g.name||''} — ${g.summary ? g.summary.slice(0,200)+'…' : ''}</div>
      </div>`).join('');
  }

  // Supplements
  const suppsEl = document.getElementById('report-supps');
  if (suppsEl && data.supplements && data.supplements.length) {
    suppsEl.innerHTML = data.supplements.map(s => `
      <p><strong>${s.name}</strong>${s.scientific_name ? ` <em>(${s.scientific_name})</em>` : ''}</p>
      ${s.benefits && s.benefits.length ? `<p style="font-size:11px;color:#555">Beneficios: ${s.benefits.slice(0,3).join('; ')}</p>` : ''}
      ${s.side_effects && s.side_effects.length ? `<p style="font-size:11px;color:#8b1a1a">Efectos adversos: ${s.side_effects.slice(0,2).join('; ')}</p>` : ''}
    `).join('<hr style="border:none;border-top:1px solid #ddd;margin:10px 0"/>');
  }

  // References
  const refsEl = document.getElementById('report-refs');
  if (refsEl && data.references && data.references.length) {
    refsEl.innerHTML = `<ol style="padding-left:18px;font-size:11px;line-height:1.8">` +
      data.references.map(r =>
        `<li>${r.authors||''} (${r.year||''}). ${r.title||''}. <em>${r.journal||''}</em>. PMID: ${r.pmid}</li>`
      ).join('') + '</ol>';
  }

  // Report date and ID
  const dateEl = document.getElementById('report-date');
  if (dateEl) dateEl.textContent = new Date().toLocaleDateString('es-ES', {year:'numeric',month:'long',day:'numeric'});
  const idEl = document.getElementById('report-id');
  if (idEl) idEl.textContent = 'NK-' + Date.now().toString().slice(-6);
}

// ── EDITOR FUNCTIONS ──────────────────────────────────────────────────────────
function execCmd(cmd) { document.execCommand(cmd); }

function addPage() {
  const canvas = document.getElementById('report-canvas-content');
  const pages = canvas.querySelectorAll('.a4-page');
  const num = pages.length + 1;
  const page = document.createElement('div');
  page.className = 'a4-page';
  page.id = 'page-' + num;
  page.innerHTML = `
    <div class="page-inner">
      <div class="report-section">
        <div class="section-heading">Contenido adicional</div>
        <div class="editable-block" contenteditable="true" data-placeholder="Escribe aquí…"></div>
      </div>
      <div class="page-footer">
        <span>NutriKen v1.0 — Cesar Manzo</span>
        <span>MSK · NCBI · KEGG · PubMed</span>
        <span>Página ${num}</span>
      </div>
    </div>`;
  canvas.appendChild(page);
  page.scrollIntoView({behavior:'smooth'});
}

function insertBlock(type) {
  const sel = window.getSelection();
  if (!sel.rangeCount) return;
  const range = sel.getRangeAt(0);
  let el;
  if (type === 'note') {
    el = document.createElement('div');
    el.style.cssText = 'background:#fffde7;border-left:4px solid #fbc02d;padding:12px;margin:12px 0;font-style:italic;font-size:12px';
    el.contentEditable = 'true';
    el.textContent = 'Nota clínica…';
  } else if (type === 'gene') {
    el = document.createElement('div');
    el.className = 'gene-block';
    el.innerHTML = '<div class="gene-block-name" contenteditable="true">GEN</div><div class="gene-block-text" contenteditable="true">Descripción del gen…</div>';
  } else if (type === 'table') {
    el = document.createElement('table');
    el.className = 'rep-table';
    el.innerHTML = '<thead><tr><th>Columna 1</th><th>Columna 2</th><th>Columna 3</th></tr></thead><tbody><tr><td contenteditable="true">—</td><td contenteditable="true">—</td><td contenteditable="true">—</td></tr></tbody>';
  }
  if (el) { range.insertNode(el); }
}

function exportTXT() {
  const canvas = document.getElementById('report-canvas-content');
  const text = canvas.innerText;
  const blob = new Blob([text], {type: 'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `NutriKen_Informe_${Date.now()}.txt`;
  a.click();
}

// ── STATS ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const r = await fetch(API + '/api/stats');
    if (!r.ok) return;
    const s = await r.json();
    document.getElementById('stats-mini').textContent =
      `Hierbas: ${s.herbs_in_cache} · Genes: ${s.genes_in_cache} · Consultas: ${s.total_queries}`;
  } catch(e) {}
}

// ── KEYBOARD SHORTCUTS ────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    const ac = document.activeElement;
    if (ac && ac.id === 'clinical-input') { e.preventDefault(); runClinical(); }
    if (ac && ac.id === 'gene-input') { e.preventDefault(); runGene(); }
    if (ac && ac.id === 'nutrient-input') { e.preventDefault(); runNutrient(); }
  }
  if (e.key === 'Escape') closeGenePanel();
});

// ── INIT ──────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  loadStats();
  setInterval(loadStats, 30000);
  document.getElementById('report-date').textContent =
    new Date().toLocaleDateString('es-ES', {year:'numeric',month:'long',day:'numeric'});
});

