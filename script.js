// ── TABS ──────────────────────────────────────────────────────────────────────
let currentTab = 'clinical';
let lastResult = null;

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    currentTab = btn.dataset.tab;
    document.getElementById('tab-' + currentTab).classList.add('active');
    clearResults();
  });
});

// ── FILL AND RUN ──────────────────────────────────────────────────────────────
function fillAndRun(tab, value) {
  // Switch tab if needed
  if (tab !== currentTab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
    currentTab = tab;
  }
  document.getElementById(tab + '-input').value = value;
  if (tab === 'clinical') runClinical();
  else if (tab === 'gene') runGene();
  else if (tab === 'nutrient') runNutrient();
}

// ── API CALLS ─────────────────────────────────────────────────────────────────
async function runClinical() {
  const query = document.getElementById('clinical-input').value.trim();
  if (!query) return;
  showLoading('Analizando condición clínica… consultando NCBI, KEGG y MSK…');
  try {
    const res = await fetch('/api/clinical', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query})
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error en el servidor');
    }
    const data = await res.json();
    lastResult = data;
    renderClinicalResult(data);
  } catch(e) {
    showError(e.message);
  } finally {
    hideLoading();
  }
}

async function runGene() {
  const raw = document.getElementById('gene-input').value.trim();
  if (!raw) return;
  const genes = raw.split(',').map(g => g.trim().toUpperCase()).filter(Boolean);
  showLoading(`Consultando ${genes.length} gen(es) en NCBI, SNPedia y Ensembl…`);
  try {
    const res = await fetch('/api/gene', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({genes})
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error en el servidor');
    }
    const data = await res.json();
    lastResult = data;
    renderGeneResult(data);
  } catch(e) {
    showError(e.message);
  } finally {
    hideLoading();
  }
}

async function runNutrient() {
  const nutrient = document.getElementById('nutrient-input').value.trim();
  if (!nutrient) return;
  showLoading(`Buscando "${nutrient}" en MSK · KEGG · PubMed…`);
  try {
    const res = await fetch('/api/nutrient', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({nutrient})
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error en el servidor');
    }
    const data = await res.json();
    lastResult = data;
    renderNutrientResult(data);
  } catch(e) {
    showError(e.message);
  } finally {
    hideLoading();
  }
}

// ── RENDERERS ─────────────────────────────────────────────────────────────────

function renderClinicalResult(data) {
  // Header
  document.getElementById('result-header').innerHTML = `
    <h1>🩺 ${data.condition}</h1>
    <p>${data.description}</p>
  `;

  // Risks
  if (data.risks && data.risks.length) {
    document.getElementById('risk-alert').style.display = 'block';
    document.getElementById('risk-list').innerHTML =
      data.risks.map(r => `<li>${r}</li>`).join('');
  }

  // Genes
  if (data.genes && data.genes.length) {
    document.getElementById('genes-card').style.display = 'block';
    document.getElementById('genes-content').innerHTML = data.genes.map(g => `
      <div class="gene-item">
        <div class="gene-symbol">${g.symbol}</div>
        <div class="gene-name">${g.name || ''}</div>
        <div class="gene-location">Chr ${g.chromosome || '?'} · ${g.location || ''}</div>
        ${g.summary ? `<div class="gene-summary">${g.summary.slice(0, 220)}…</div>` : ''}
        <div class="gene-links">
          <a class="gene-link" href="${g.ncbi_url}" target="_blank">NCBI Gene</a>
          <a class="gene-link" href="https://www.snpedia.com/index.php/${g.symbol}" target="_blank">SNPedia</a>
          <a class="gene-link" href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?q=${g.symbol}" target="_blank">Ensembl</a>
        </div>
      </div>
    `).join('');
  }

  // Pathway
  if (data.pathway && data.pathway.name) {
    document.getElementById('pathway-card').style.display = 'block';
    const geneChips = (data.pathway.genes || []).slice(0, 16).map(g =>
      `<span class="pathway-gene-tag">${g.symbol}</span>`).join('');
    document.getElementById('pathway-content').innerHTML = `
      <div class="pathway-box">
        <div class="pathway-id">${data.pathway.id}</div>
        <div class="pathway-name">${data.pathway.name}</div>
        ${data.pathway.description ? `<div class="pathway-desc">${data.pathway.description.slice(0,400)}…</div>` : ''}
        ${geneChips ? `<div class="pathway-gene-list">${geneChips}</div>` : ''}
        <a class="pathway-link" href="${data.pathway.kegg_url}" target="_blank">🗺 Ver ruta en KEGG →</a>
      </div>
    `;
  }

  // Supplements
  renderSupplements(data.supplements || []);

  // References
  renderReferences(data.references || []);

  // External links
  const extLinks = (data.genes || []).map(g => `
    <a class="ext-link" href="${g.ncbi_url}" target="_blank">🔗 NCBI: ${g.symbol}</a>
    <a class="ext-link" href="https://www.snpedia.com/index.php/${g.symbol}" target="_blank">🧬 SNPedia: ${g.symbol}</a>
  `).join('');
  if (extLinks) {
    document.getElementById('external-links').style.display = 'block';
    document.getElementById('ext-links-content').innerHTML = `<div class="ext-links-grid">${extLinks}</div>`;
  }

  showResults();
}

function renderGeneResult(data) {
  // Header
  document.getElementById('result-header').innerHTML = `
    <h1>🔬 Análisis Genómico: ${data.genes_queried.join(', ')}</h1>
    <p>Análisis de ${data.genes_queried.length} gen(es) — datos en tiempo real de NCBI · SNPedia · Ensembl</p>
  `;

  // Genes info
  if (data.genes_info && data.genes_info.length) {
    document.getElementById('genes-card').style.display = 'block';
    document.getElementById('genes-content').innerHTML = data.genes_info.map(g => `
      <div class="gene-item">
        <div class="gene-symbol">${g.symbol}</div>
        <div class="gene-name">${g.name || ''}</div>
        <div class="gene-location">Chr ${g.chromosome || '?'} · ${g.location || ''}</div>
        ${g.summary ? `<div class="gene-summary">${g.summary.slice(0, 280)}…</div>` : ''}
        <div class="gene-links">
          <a class="gene-link" href="${g.ncbi_url}" target="_blank">NCBI Gene</a>
          <a class="gene-link" href="https://www.snpedia.com/index.php/${g.symbol}" target="_blank">SNPedia</a>
          <a class="gene-link" href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?q=${g.symbol}" target="_blank">Ensembl</a>
        </div>
      </div>
    `).join('');
  }

  // Related conditions
  if (data.related_conditions && data.related_conditions.length) {
    document.getElementById('conditions-card').style.display = 'block';
    document.getElementById('conditions-content').innerHTML = data.related_conditions.map(c => `
      <div class="condition-item">
        <div class="condition-name">${c.condition}</div>
        <div class="condition-genes">
          ${c.matching_genes.map(g => `<span class="cond-gene-tag">${g}</span>`).join('')}
        </div>
        ${c.risks.length ? `<div style="color:var(--amber-400);font-size:0.8rem;margin-top:6px;">⚠ ${c.risks[0]}</div>` : ''}
      </div>
    `).join('');
  }

  // Supplements
  renderSupplements(data.supplements || []);

  // References
  renderReferences(data.references || []);

  // External links
  const extLinks = data.genes_queried.map(g => `
    <a class="ext-link" href="https://www.ncbi.nlm.nih.gov/gene/?term=${g}+Homo+sapiens" target="_blank">🔗 NCBI: ${g}</a>
    <a class="ext-link" href="https://www.snpedia.com/index.php/${g}" target="_blank">🧬 SNPedia: ${g}</a>
    <a class="ext-link" href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?q=${g}" target="_blank">🌐 Ensembl: ${g}</a>
  `).join('');
  document.getElementById('external-links').style.display = 'block';
  document.getElementById('ext-links-content').innerHTML = `<div class="ext-links-grid">${extLinks}</div>`;

  showResults();
}

function renderNutrientResult(data) {
  const herb = data.msk_data;

  document.getElementById('result-header').innerHTML = `
    <h1>🌿 ${herb.name || data.nutrient}</h1>
    ${herb.scientific_name ? `<p style="color:var(--teal-400);font-style:italic">${herb.scientific_name}</p>` : ''}
    <p style="margin-top:8px">${herb.what_is_it ? herb.what_is_it.slice(0,300) + '…' : 'Datos disponibles abajo.'}</p>
  `;

  // Full herb detail card
  document.getElementById('herb-card').style.display = 'block';
  document.getElementById('herb-content').innerHTML = `
    <div class="card-header">
      <span class="card-icon">🌿</span>
      <h2>Ficha Clínica Completa — MSK</h2>
      <span class="card-badge">Memorial Sloan Kettering</span>
    </div>
    <div class="supp-detail-grid">
      ${herb.benefits && herb.benefits.length ? `
      <div class="supp-section">
        <h4>Usos y Beneficios</h4>
        <ul>${herb.benefits.map(b => `<li>${b}</li>`).join('')}</ul>
      </div>` : ''}
      ${herb.side_effects && herb.side_effects.length ? `
      <div class="supp-section danger">
        <h4>Efectos Adversos</h4>
        <ul>${herb.side_effects.map(s => `<li>${s}</li>`).join('')}</ul>
      </div>` : ''}
      ${herb.warnings && herb.warnings.length ? `
      <div class="supp-section warning">
        <h4>Advertencias Clínicas</h4>
        <ul>${herb.warnings.map(w => `<li>${w}</li>`).join('')}</ul>
      </div>` : ''}
      ${herb.drug_interactions && herb.drug_interactions.length ? `
      <div class="supp-section danger">
        <h4>Interacciones Farmacológicas</h4>
        <ul>${herb.drug_interactions.map(d => `<li>${d}</li>`).join('')}</ul>
      </div>` : ''}
    </div>
    ${herb.mechanism_of_action ? `
    <div class="supp-section" style="margin-top:16px">
      <h4>Mecanismo de Acción</h4>
      <p>${herb.mechanism_of_action.slice(0, 600)}…</p>
    </div>` : ''}
    ${herb.clinical_summary ? `
    <div class="supp-section" style="margin-top:12px">
      <h4>Resumen Clínico (Para Profesionales)</h4>
      <p>${herb.clinical_summary.slice(0, 800)}…</p>
    </div>` : ''}
    <a class="supp-msk-link" href="${data.msk_url}" target="_blank">📖 Ver ficha completa en MSK →</a>
  `;

  // Pathway if available
  if (data.pathway && data.pathway.name) {
    document.getElementById('pathway-card').style.display = 'block';
    document.getElementById('pathway-content').innerHTML = `
      <div class="pathway-box">
        <div class="pathway-id">${data.pathway.id}</div>
        <div class="pathway-name">${data.pathway.name}</div>
        <a class="pathway-link" href="${data.pathway.kegg_url}" target="_blank">🗺 Ver en KEGG →</a>
      </div>
    `;
  }

  // References
  renderReferences(data.references || []);

  // External links
  document.getElementById('external-links').style.display = 'block';
  document.getElementById('ext-links-content').innerHTML = `
    <div class="ext-links-grid">
      <a class="ext-link" href="${data.msk_url}" target="_blank">🌿 MSK Herbs</a>
      <a class="ext-link" href="https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(data.nutrient)}" target="_blank">📚 PubMed</a>
      <a class="ext-link" href="https://www.kegg.jp/kegg/compound/" target="_blank">🗺 KEGG Compound</a>
    </div>
  `;

  showResults();
}

function renderSupplements(supplements) {
  if (!supplements || !supplements.length) return;
  document.getElementById('supplements-card').style.display = 'block';

  const tabs = supplements.map((s, i) =>
    `<button class="supp-tab ${i===0?'active':''}" onclick="switchSupp(${i})">${s.name || s.slug}</button>`
  ).join('');

  const panels = supplements.map((s, i) => `
    <div class="supp-panel ${i===0?'active':''}" id="supp-panel-${i}">
      <div class="supp-detail-grid">
        ${s.benefits && s.benefits.length ? `
        <div class="supp-section">
          <h4>Beneficios</h4>
          <ul>${s.benefits.slice(0,6).map(b => `<li>${b}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.side_effects && s.side_effects.length ? `
        <div class="supp-section danger">
          <h4>Efectos Adversos</h4>
          <ul>${s.side_effects.slice(0,6).map(e => `<li>${e}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.warnings && s.warnings.length ? `
        <div class="supp-section warning">
          <h4>Advertencias</h4>
          <ul>${s.warnings.slice(0,4).map(w => `<li>${w}</li>`).join('')}</ul>
        </div>` : ''}
        ${s.drug_interactions && s.drug_interactions.length ? `
        <div class="supp-section danger">
          <h4>Interacciones</h4>
          <ul>${s.drug_interactions.slice(0,4).map(d => `<li>${d}</li>`).join('')}</ul>
        </div>` : ''}
      </div>
      ${s.mechanism_of_action ? `
      <div class="supp-section" style="margin-top:14px">
        <h4>Mecanismo de Acción</h4>
        <p>${s.mechanism_of_action.slice(0,400)}…</p>
      </div>` : ''}
      <a class="supp-msk-link" href="${s.url}" target="_blank">📖 Ver en MSK →</a>
    </div>
  `).join('');

  document.getElementById('supplements-content').innerHTML = `
    <div class="supp-tabs">${tabs}</div>
    ${panels}
  `;
}

function switchSupp(idx) {
  document.querySelectorAll('.supp-tab').forEach((t, i) =>
    t.classList.toggle('active', i === idx));
  document.querySelectorAll('.supp-panel').forEach((p, i) =>
    p.classList.toggle('active', i === idx));
}

function renderReferences(refs) {
  if (!refs || !refs.length) return;
  document.getElementById('refs-card').style.display = 'block';
  document.getElementById('refs-content').innerHTML = refs.map(r => `
    <div class="ref-item">
      <div class="ref-title">${r.title || 'Sin título'}</div>
      <div class="ref-meta">${r.authors || ''} · ${r.journal || ''} · ${r.year || ''}</div>
      <a class="ref-link" href="${r.url}" target="_blank">PubMed ${r.pmid} →</a>
    </div>
  `).join('');
}

// ── UI HELPERS ────────────────────────────────────────────────────────────────
function showLoading(msg) {
  document.getElementById('loading-msg').textContent = msg;
  document.getElementById('loading').style.display = 'flex';
  document.getElementById('results').style.display = 'none';
}
function hideLoading() {
  document.getElementById('loading').style.display = 'none';
}
function showResults() {
  document.getElementById('results').style.display = 'block';
  document.getElementById('report-actions').style.display = 'flex';
  document.getElementById('results').scrollIntoView({behavior: 'smooth', block: 'start'});
}
function showError(msg) {
  hideLoading();
  document.getElementById('result-header').innerHTML = `
    <h1 style="color:#f87171">Error</h1>
    <p style="color:var(--gray-400)">${msg}</p>
  `;
  document.getElementById('results').style.display = 'block';
  document.getElementById('report-actions').style.display = 'none';
}
function clearResults() {
  document.getElementById('results').style.display = 'none';
  ['genes-card','pathway-card','supplements-card','herb-card',
   'conditions-card','refs-card','external-links','risk-alert','report-actions']
    .forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
  lastResult = null;
}

// ── REPORT PDF ────────────────────────────────────────────────────────────────
function generateReport() {
  if (!lastResult) return;
  const content = buildReportHTML(lastResult);
  const blob = new Blob([content], {type: 'text/html'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `NutriKen_Reporte_${Date.now()}.html`;
  a.click();
  URL.revokeObjectURL(url);
}

function buildReportHTML(data) {
  const now = new Date().toLocaleDateString('es-ES', {year:'numeric',month:'long',day:'numeric'});
  const genes = (data.genes_info || data.genes || []);
  const supplements = (data.supplements || (data.msk_data ? [data.msk_data] : []));
  const references = data.references || [];
  const condition = data.condition || (data.genes_queried ? data.genes_queried.join(', ') : data.nutrient);

  return `<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"/>
<title>NutriKen — Reporte ${condition}</title>
<style>
  body{font-family:'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:40px;color:#1a1a1a;line-height:1.6}
  h1{color:#047857;border-bottom:3px solid #047857;padding-bottom:10px}
  h2{color:#065f46;margin-top:30px}
  h3{color:#047857}
  .badge{background:#d1fae5;color:#065f46;padding:3px 10px;border-radius:20px;font-size:0.75rem;margin-right:6px}
  .risk-box{background:#fee2e2;border-left:4px solid #ef4444;padding:12px 16px;border-radius:4px;margin:16px 0}
  .gene-box{background:#f0fdf4;border:1px solid #bbf7d0;padding:14px;border-radius:8px;margin:10px 0}
  .supp-box{background:#f0fdf4;border:1px solid #a7f3d0;padding:16px;border-radius:8px;margin:12px 0}
  .ref-item{border-bottom:1px solid #e5e7eb;padding:10px 0}
  .footer{margin-top:40px;padding-top:20px;border-top:2px solid #d1fae5;color:#6b7280;font-size:0.8rem}
  a{color:#047857}
</style></head><body>
<h1>🧬 NutriKen — Reporte Clínico Nutricional</h1>
<p><strong>Consulta:</strong> ${condition} &nbsp;|&nbsp; <strong>Fecha:</strong> ${now}</p>
<p><span class="badge">MSK Evidence</span><span class="badge">NCBI</span><span class="badge">KEGG</span><span class="badge">PubMed</span></p>

${data.description ? `<h2>Descripción</h2><p>${data.description}</p>` : ''}

${data.risks && data.risks.length ? `
<h2>⚠ Riesgos y Consideraciones</h2>
<div class="risk-box"><ul>${data.risks.map(r=>`<li>${r}</li>`).join('')}</ul></div>` : ''}

${genes.length ? `
<h2>Genes Involucrados</h2>
${genes.map(g=>`
<div class="gene-box">
  <strong>${g.symbol}</strong> — ${g.name || ''}<br/>
  <small>Cromosoma: ${g.chromosome || '?'} · ${g.location || ''}</small><br/>
  ${g.summary ? `<p>${g.summary.slice(0,300)}…</p>` : ''}
  <a href="${g.ncbi_url}" target="_blank">NCBI Gene</a> |
  <a href="https://www.snpedia.com/index.php/${g.symbol}" target="_blank">SNPedia</a> |
  <a href="https://www.ensembl.org/Homo_sapiens/Gene/Summary?q=${g.symbol}" target="_blank">Ensembl</a>
</div>`).join('')}` : ''}

${supplements.length ? `
<h2>Suplementos con Evidencia Clínica (MSK)</h2>
${supplements.map(s=>`
<div class="supp-box">
  <h3>${s.name || ''} ${s.scientific_name ? `<em>(${s.scientific_name})</em>` : ''}</h3>
  ${s.benefits && s.benefits.length ? `<p><strong>Beneficios:</strong></p><ul>${s.benefits.slice(0,5).map(b=>`<li>${b}</li>`).join('')}</ul>` : ''}
  ${s.side_effects && s.side_effects.length ? `<p><strong>Efectos adversos:</strong></p><ul>${s.side_effects.slice(0,5).map(e=>`<li>${e}</li>`).join('')}</ul>` : ''}
  ${s.drug_interactions && s.drug_interactions.length ? `<p><strong>Interacciones:</strong></p><ul>${s.drug_interactions.slice(0,3).map(d=>`<li>${d}</li>`).join('')}</ul>` : ''}
  ${s.url ? `<a href="${s.url}" target="_blank">Ver ficha completa en MSK →</a>` : ''}
</div>`).join('')}` : ''}

${references.length ? `
<h2>Referencias Científicas (PubMed)</h2>
${references.map(r=>`
<div class="ref-item">
  <strong>${r.title}</strong><br/>
  <small>${r.authors} · ${r.journal} · ${r.year}</small><br/>
  <a href="${r.url}" target="_blank">PubMed ${r.pmid} →</a>
</div>`).join('')}` : ''}

<div class="footer">
  <strong>NutriKen v1.0</strong> — Plataforma Bioinformática Nutricional · Desarrollado por Cesar Manzo<br/>
  Fuentes: MSK About Herbs · NCBI eUtils · KEGG REST API · PubMed<br/>
  <em>Este reporte es una herramienta educativa. No reemplaza el criterio clínico profesional.</em>
</div>
</body></html>`;
}

// ── ESTADÍSTICAS ──────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const s = await res.json();
    document.getElementById('stats-display').textContent =
      `Hierbas en caché: ${s.herbs_in_cache} · Genes en caché: ${s.genes_in_cache} · Consultas totales: ${s.total_queries}`;
  } catch(e) { /* silencioso */ }
}

// Enter key support
['clinical-input','gene-input','nutrient-input'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('keypress', e => {
    if (e.key === 'Enter') {
      if (id === 'clinical-input') runClinical();
      else if (id === 'gene-input') runGene();
      else if (id === 'nutrient-input') runNutrient();
    }
  });
});

// Init
window.addEventListener('load', () => {
  loadStats();
  setInterval(loadStats, 30000);
});

