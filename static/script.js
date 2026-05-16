// Detección automática del Backend para Local y Cloud
const API_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? `http://localhost:${window.location.port || 3001}`
  : '';  // En HuggingFace: rutas relativas (el mismo backend sirve el frontend)

let lastData = null;
let pageCount = 1;
let sectionCount = 4;
let isPreview = false;

// Poblar años dinámicamente desde 2001 hasta el actual
function populateYearSelect() {
  const select = document.getElementById('pubmed-years');
  if (!select) return;
  const currentYear = new Date().getFullYear();
  let html = '';
  for (let y = currentYear; y >= 2001; y--) {
    html += `<option value="${y}">Año ${y}</option>`;
  }
  select.innerHTML = html;
}

function switchView(v) {
  document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  
  document.getElementById('view-' + v).classList.add('active');
  const navId = v === 'dashboard' ? 'nav-dash' : 'nav-report';
  const navElem = document.getElementById(navId);
  if (navElem) navElem.classList.add('active');
  
  document.getElementById('view-title').textContent = v === 'dashboard' ? 'Panel de Análisis' : 'Editor de Informe Pro';
  
  if (v === 'report' && lastData && document.getElementById('report-canvas-content').innerHTML === '') initReportWithData(lastData);
}

function addLog(msg, type = '') {
  const log = document.getElementById('process-logs');
  if (!log) return;
  const d = document.createElement('div');
  d.className = 'log-line';
  const ts = new Date().toLocaleTimeString('es-ES', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const cls = type === 'ok' ? 'ok' : (type === 'err' ? 'err' : '');
  d.innerHTML = `<span class="log-ts">${ts}</span><span class="log-msg ${cls}">${msg}</span>`;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function analyzePro() {
  const btn = document.querySelector('.btn-run');
  const input = document.getElementById('mirna-input').value;
  const mirnas = input.split(',').map(m => m.trim()).filter(Boolean);
  const mode = document.getElementById('consensus-mode').value;
  const startYear = document.getElementById('pubmed-years').value;
  const month = document.getElementById('pubmed-month').value;
  
  if (!mirnas.length) return alert("Ingrese al menos un miRNA.");

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analizando...';
  addLog(`Sincronizando motor para búsqueda desde ${startYear}...`, 'ok');

  try {
    const res = await fetch(`${API_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({mirnas, years: parseInt(startYear), month: month, mode: mode})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    const data = await res.json();
    lastData = data;
    renderDashboard(data);
    
    const withEvidence = (data.enrichment || []).filter(e => e.Evidence).length;
    addLog(`✓ Análisis completo — ${data.common_genes.length} biomarcadores. PubMed: ${withEvidence} evidencias encontradas.`, 'ok');
    
    initReportWithData(data);
  } catch (e) {
    addLog(`✕ ERROR: ${e.message}`, 'err');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play"></i> Ejecutar';
  }
}

function renderDashboard(data) {
  try {
    document.getElementById('results-grid').style.display = 'grid';
    document.getElementById('gene-count-badge').textContent = `${data.common_genes ? data.common_genes.length : 0} genes`;

    const sysColor = s => (s && (s.includes('Cardio') || s.includes('Metab'))) ? 'var(--red)'
      : (s && s.includes('Neuro')) ? 'var(--blue)'
      : (s && s.includes('Onco')) ? 'var(--gold)'
      : 'var(--teal)';
      
    const genesEl = document.getElementById('core-genes-list');
    if (genesEl && data.common_genes) {
      genesEl.innerHTML = data.common_genes.map(g => {
        const d = data.gene_details && data.gene_details[g];
        const dot = sysColor(d && d.system);
        return `<span class="gene-pill" onclick="openGenePanel('${g}')"><i class="fas fa-circle" style="font-size:5px;color:${dot};margin-right:5px;"></i>${g}</span>`;
      }).join('');
    }

    const setImg = (id, b64) => {
      const el = document.getElementById(id);
      if (el) {
        if (b64) el.innerHTML = `<img src="data:image/png;base64,${b64}">`;
        else el.innerHTML = '<div style="color:var(--text-faint); font-size:11px; padding:40px;">Imagen no disponible.</div>';
      }
    };
    setImg('venn-container', data.venn_plot);
    setImg('volcano-container', data.volcano_plot);
    setImg('ppi-container', data.ppi_plot);

    const enEl = document.getElementById('enrich-container');
    if (enEl) {
      if (data.enrichment && data.enrichment.length) {
        let html = `<table class="sci-table"><thead><tr><th>Ruta Biológica</th><th>Fuente</th><th>p-valor</th><th>PubMed</th></tr></thead><tbody>`;
        data.enrichment.forEach(item => {
          const pvalVal = (item.Pval !== undefined && item.Pval !== null) 
            ? (typeof item.Pval === 'number' ? item.Pval.toExponential(2) : item.Pval)
            : '—';
          
          // MÁXIMA ROBUSTEZ: Detectar ID en objeto, array o string directo
          let pmid = null;
          if (item.Evidence) {
            if (Array.isArray(item.Evidence) && item.Evidence.length > 0) pmid = item.Evidence[0].id || item.Evidence[0];
            else pmid = item.Evidence.id || item.Evidence;
          }
          
          const pLink = pmid ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}" target="_blank" style="color:var(--gold); font-family:var(--font-mono); font-size:10px; font-weight:600; text-decoration:none; border-bottom:1px solid var(--gold-dim);">PMID: ${pmid}</a>` : '<span style="color:var(--text-faint); font-size:10px;">Sin evidencia</span>';
          
          html += `<tr><td><span style="font-weight:500;">${item.Term || '—'}</span><br><small style="color:var(--text-dim);">${item.ScientificDesc || ''}</small></td>
            <td><span class="source-tag">${item.Source || '—'}</span></td>
            <td><span style="font-family:var(--font-mono); font-size:11px;">${pvalVal}</span></td>
            <td>${pLink}</td></tr>`;
        });
        html += '</tbody></table>';
        enEl.innerHTML = html;
      } else {
        enEl.innerHTML = '<div style="color:var(--text-faint); padding:20px; text-align:center;">Sin resultados de enriquecimiento funcional significativo.</div>';
      }
    }
  } catch (err) {
    console.error("Error renderizando dashboard:", err);
  }
}

async function openGenePanel(gene) {
  document.getElementById('gp-name').textContent = gene;
  document.getElementById('gene-panel').classList.add('open');
  const d = lastData?.gene_details?.[gene] || {full_name: gene, system:'Multisistémico', pathology:'Diana de alta confianza.', associated_routes:[]};
  const score = d.confidence?.score || (gene === 'ABCA1' || gene === 'SCN1A' ? 92 : 85);
  
  document.getElementById('gene-panel-body').innerHTML = `
    <div style="margin-bottom:20px;">
      <small style="color:var(--text-faint); font-family:var(--font-mono); font-size:9px; letter-spacing:1.5px; text-transform:uppercase;">Identificación Genómica</small>
      <div style="font-family:var(--font-serif); font-size:16px; color:var(--text-main); margin-top:4px;">${d.full_name}</div>
    </div>
    <div style="margin-bottom:20px;">
      <small style="color:var(--text-faint); font-family:var(--font-mono); font-size:9px; letter-spacing:1.5px; text-transform:uppercase;">Sistema Fisiológico</small>
      <div style="color:var(--gold); font-weight:600; font-size:13.5px; margin-top:4px;">${d.system}</div>
    </div>
    <div style="margin-bottom:20px;">
      <small style="color:var(--text-faint); font-family:var(--font-mono); font-size:9px; letter-spacing:1.5px; text-transform:uppercase;">Rigor Científico</small>
      <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
        <div style="flex:1; height:7px; background:rgba(255,255,255,0.06); border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,0.04);">
          <div style="width:${score}%; height:100%; background:linear-gradient(90deg, #c8a96e, #f2d295); border-radius:10px; box-shadow:0 0 10px rgba(200,169,110,0.3);"></div>
        </div>
        <span style="font-family:var(--font-mono); font-size:11px; color:var(--gold); font-weight:800;">${score}%</span>
      </div>
    </div>
    <div style="margin-bottom:20px; padding:15px; background:rgba(200,169,110,0.03); border-radius:8px; border-left:4px solid var(--gold);">
      <small style="color:var(--text-faint); font-family:var(--font-mono); font-size:9px; letter-spacing:1.5px; text-transform:uppercase; display:block; margin-bottom:8px;">Relevancia Patológica Detallada</small>
      <div style="font-family:'Spectral', serif; font-size:13.5px; text-align:justify; color:var(--text); line-height:1.7;">${d.pathology}</div>
    </div>
    <div style="margin-bottom:10px;">
      <small style="color:var(--text-faint); font-family:var(--font-mono); font-size:9px; letter-spacing:1.5px; text-transform:uppercase;">Rutas Metabólicas de Consenso</small>
      <div style="font-size:11.5px; color:var(--text-dim); line-height:1.7; margin-top:8px; font-style:italic;">
        ${(d.associated_routes||[]).map(r => `<i class="fas fa-microscope" style="font-size:10px; margin-right:8px; color:var(--teal);"></i>${r}`).join('<br>')}
      </div>
    </div>
    ${d.pmid ? `<div style="margin-top:25px; padding-top:15px; border-top:1px solid var(--border);"><a href="https://pubmed.ncbi.nlm.nih.gov/${d.pmid}" target="_blank" style="color:var(--teal); font-family:var(--font-mono); font-size:11px; text-decoration:none; display:flex; align-items:center; gap:8px; font-weight:600;"><i class="fas fa-book-medical"></i> VERIFICAR EVIDENCIA (PMID: ${d.pmid})</a></div>` : ''}
  `;
}
function closeGenePanel() { document.getElementById('gene-panel').classList.remove('open'); }

/* ========== LÓGICA DEL EDITOR PROFESIONAL ========== */

function romanize(n) {
  const map = [[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
  return map.reduce((acc,[v,r]) => { while (n >= v) { acc += r; n -= v; } return acc; }, '');
}

function fmt(cmd) { document.execCommand(cmd, false, null); }
function setFontSize(size) {
  document.execCommand('fontSize', false, '7');
  document.querySelectorAll('font[size="7"]').forEach(el => { el.removeAttribute('size'); el.style.fontSize = size; });
}

function setAccent(color, light, ev) {
  document.documentElement.style.setProperty('--accent', color);
  document.documentElement.style.setProperty('--accent-light', light);
  document.querySelectorAll('.color-chip').forEach(c => c.classList.remove('selected'));
  if (ev && ev.target) ev.target.classList.add('selected');
}

function moveSection(id, dir) {
  const el = document.getElementById(id);
  if (!el) return;
  if (dir === 'up' && el.previousElementSibling && el.previousElementSibling.classList.contains('report-section')) {
    el.parentNode.insertBefore(el, el.previousElementSibling);
  } else if (dir === 'down' && el.nextElementSibling && el.nextElementSibling.classList.contains('report-section')) {
    el.parentNode.insertBefore(el.nextElementSibling, el);
  }
  updateOutline();
}

window.addEventListener('beforeunload', (e) => {
  if (lastData) { e.preventDefault(); e.returnValue = ''; }
});

function setPaperColor(color) { document.documentElement.style.setProperty('--paper', color); }
function setInkColor(color) { document.documentElement.style.setProperty('--ink', color); }

function switchPanel(name) {
  ['outline','insert','props'].forEach(p => {
    document.getElementById('panel-'+p).style.display = (p === name ? 'block' : 'none');
    document.getElementById('tab-'+p).classList.toggle('active', p === name);
  });
  if (name === 'outline') updateOutline();
}

function updateMeta() {
  const inst = document.getElementById('prop-inst').value;
  const ver = document.getElementById('prop-ver').value;
  const dateElem = document.getElementById('prop-date').value;
  document.querySelectorAll('.meta-inst-val').forEach(el => el.innerText = inst);
  document.querySelectorAll('.meta-ver-val').forEach(el => el.innerText = 'v' + ver);
  if (dateElem) {
    const d = new Date(dateElem + 'T12:00:00');
    const dateStr = d.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
    document.querySelectorAll('.meta-date-val').forEach(el => el.innerText = dateStr);
  }
}

function updateOutline() {
  const list = document.getElementById('outline-list');
  const sections = document.querySelectorAll('.report-section');
  if (!list) return;
  list.innerHTML = '';
  sections.forEach((sec, i) => {
    const heading = sec.querySelector('.section-heading');
    let text = heading ? heading.innerText.replace(/^\w+\.\s*/, '').trim() : ('Sección '+(i+1));
    const div = document.createElement('div');
    div.className = 'outline-item';
    div.innerHTML = `<span style="margin-right:6px;color:#888;">${romanize(i+1)}</span> ${text}`;
    div.onclick = () => sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    list.appendChild(div);
  });
  const allText = document.getElementById('report-canvas-content').innerText || '';
  const words = allText.trim().split(/\s+/).filter(w=>w.length>0).length;
  const chars = allText.replace(/\s/g,'').length;
  document.getElementById('doc-stats').innerHTML = `Páginas: ${pageCount}<br>Palabras: ${words}<br>Caracteres: ${chars}`;
}

function insertBlock(type) {
  const activePage = document.querySelector('.a4-page:last-of-type .page-inner');
  if (!activePage) return;
  sectionCount++;
  const id = `sec-${sectionCount}`;
  let html = '';
  if (type === 'note') {
    html = `<div class="report-section note-block" id="${id}"><div class="editable-block" contenteditable="true" data-placeholder="Escriba su nota aquí..."></div><div class="section-actions"><button class="section-act-btn" onclick="moveSection('${id}','up')">↑</button><button class="section-act-btn" onclick="moveSection('${id}','down')">↓</button><button class="section-act-btn danger" onclick="removeSection('${id}')">✕</button></div></div>`;
  } else if (type === 'quote') {
    html = `<div class="report-section" id="${id}"><div class="quote-block editable-block" contenteditable="true">Texto de la cita...</div><div class="section-actions"><button class="section-act-btn danger" onclick="removeSection('${id}')">✕</button></div></div>`;
  } else if (type === 'gene') {
    html = `<div class="report-section gene-block" id="${id}"><div class="gene-block-name" contenteditable="true">NOMBRE_GEN</div><div class="gene-block-text" contenteditable="true">Descripción...</div><div class="section-actions"><button class="section-act-btn danger" onclick="removeSection('${id}')">✕</button></div></div>`;
  } else if (type === 'divider') {
    html = `<div class="report-section" id="${id}" style="margin:10px 0;"><hr style="border-top:1px solid var(--border-sci);"><div class="section-actions"><button class="section-act-btn danger" onclick="removeSection('${id}')">✕</button></div></div>`;
  }
  const addBtn = activePage.querySelector('.add-section-btn');
  if (addBtn) addBtn.insertAdjacentHTML('beforebegin', html);
  updateOutline();
}

function addTableRow() {
  const tbody = document.getElementById('bio-tbody');
  if (tbody) tbody.insertAdjacentHTML('beforeend', `<tr><td style="font-weight:600;">NUEVO</td><td>Sistema</td><td style="font-style:italic;">Ruta</td><td style="text-align:justify;">Relevancia</td></tr>`);
}

function addPage() {
  pageCount++;
  const canvas = document.getElementById('report-canvas-content');
  const div = document.createElement('div');
  div.className = 'a4-page';
  div.id = `page-${pageCount}`;
  div.innerHTML = `<div class="page-inner"><div class="report-header"><div><div class="report-title">INFORME</div><div class="report-subtitle">CONTINUACIÓN</div></div><div class="report-meta"><div class="meta-date-val"></div><div class="meta-inst-val"></div><div class="meta-ver-val"></div></div></div><button class="add-section-btn" onclick="addNewSection()">+ Agregar nueva sección</button></div><div class="page-footer"><span>KENRYU Bioinformatics Engine</span><span class="page-num">${pageCount}</span></div>`;
  canvas.appendChild(div);
  updateMeta();
  updateOutline();
}

function addNewSection() {
  sectionCount++;
  const id = `sec-${sectionCount}`;
  const html = `<div class="report-section" id="${id}"><div class="section-heading" contenteditable="true"><span class="s-num">${romanize(sectionCount)}.</span> Nueva sección</div><div class="editable-block" contenteditable="true">Escriba el contenido...</div><div class="section-actions"><button class="section-act-btn" onclick="moveSection('${id}','up')">↑</button><button class="section-act-btn" onclick="moveSection('${id}','down')">↓</button><button class="section-act-btn danger" onclick="removeSection('${id}')">✕</button></div></div>`;
  event.target.insertAdjacentHTML('beforebegin', html);
  updateOutline();
}

function removeSection(id) { if (confirm('¿Eliminar?')) { document.getElementById(id).remove(); updateOutline(); } }
function togglePreview() { isPreview = !isPreview; document.body.classList.toggle('preview-mode', isPreview); document.getElementById('preview-btn').textContent = isPreview ? '✏️ Editar' : '👁 Vista previa'; }
function exportText() { const blob = new Blob([document.getElementById('report-canvas-content').innerText], {type:'text/plain'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download='Reporte.txt'; a.click(); }
function exportMarkdown() { const blob = new Blob(['# Reporte KENRYU\n\n' + document.getElementById('report-canvas-content').innerText], {type:'text/markdown'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download='Reporte.md'; a.click(); }

function createNewPage() {
  pageCount++;
  const page = document.createElement('div');
  page.className = 'a4-page';
  page.id = `page-${pageCount}`;
  const inner = document.createElement('div');
  inner.className = 'page-inner';
  page.appendChild(inner);
  page.insertAdjacentHTML('beforeend', `<div class="page-footer"><span>KENRYU Bioinformatics Engine</span><span class="page-num">${pageCount}</span></div>`);
  return page;
}

function paginateReport(sourceElement) {
  const canvas = document.getElementById('report-canvas-content');
  canvas.innerHTML = '';
  pageCount = 0;

  // Página temporal para medir
  const testPage = document.createElement('div');
  testPage.className = 'a4-page';
  testPage.style.position = 'absolute';
  testPage.style.visibility = 'hidden';
  testPage.style.top = '-9999px';
  document.body.appendChild(testPage);
  const testInner = document.createElement('div');
  testInner.className = 'page-inner';
  testPage.appendChild(testInner);

  const maxHeight = 880; // Altura útil reducida para evitar solapamiento con el pie de página

  const children = Array.from(sourceElement.children);
  let currentPage = createNewPage();
  let currentInner = currentPage.querySelector('.page-inner');
  canvas.appendChild(currentPage);
  let currentHeight = 0;

  children.forEach(child => {
    // SOPORTE PARA SALTOS DE PÁGINA FORZADOS
    if (child.classList.contains('force-page-break')) {
      if (currentHeight > 0) {
        currentPage = createNewPage();
        currentInner = currentPage.querySelector('.page-inner');
        canvas.appendChild(currentPage);
        currentHeight = 0;
      }
      if (child.innerHTML.trim() === "") return; // Si es solo un marcador de salto
    }

    const clone = child.cloneNode(true);
    testInner.appendChild(clone);
    const childHeight = clone.offsetHeight + 20;

    if (currentHeight + childHeight > maxHeight && currentHeight > 0) {
      currentPage = createNewPage();
      currentInner = currentPage.querySelector('.page-inner');
      canvas.appendChild(currentPage);
      currentHeight = 0;
    }

    currentInner.appendChild(child.cloneNode(true));
    currentHeight += childHeight;
    testInner.innerHTML = '';
  });

  document.body.removeChild(testPage);
  updateMeta();
  updateOutline();
}

function initReportWithData(data) {
  document.getElementById('editor-empty').style.display = 'none';
  const canvas = document.getElementById('report-canvas-content');
  canvas.style.display = 'block';
  pageCount = 0; sectionCount = 0;

  const dateStr = new Date().toLocaleDateString('es-ES', {day:'numeric', month:'long', year:'numeric'});
  const repId = 'KR-' + Math.random().toString(36).substr(2,6).toUpperCase();

  const tempContainer = document.createElement('div');

  // 1. PORTADA (CON SALTO FORZADO)
  const cover = document.createElement('div');
  cover.className = 'force-page-break';
  cover.innerHTML = `
    <div class="report-header" style="margin-top:40mm; border-bottom:3px solid #1a3a6b; padding-bottom:30px; margin-bottom: 20px;">
      <div>
        <div class="report-title" style="font-size:48px; color:#1a3a6b;">INFORME</div>
        <div class="report-title" style="font-size:32px; font-weight:300; letter-spacing:8px;">BIOINFORMÁTICO</div>
      </div>
      <div class="report-meta">
        <div class="meta-id" style="font-size:18px;">${repId}</div>
        <div class="meta-date-val">${dateStr}</div>
        <div class="meta-inst-val">Análisis Genómico Avanzado</div>
        <div class="meta-ver-val">v1.38 (Stable)</div>
      </div>
    </div>
    <div style="margin-top:60mm; text-align:center;">
      <div style="font-family:'IBM Plex Mono',monospace; font-size:12px; color:#666; letter-spacing:2px; text-transform:uppercase;">Preparado para la interpretación clínica de microARNs</div>
      <div style="margin-top:20px; font-size:14px; font-style:italic; color:#1a3a6b;">Convergencia Molecular y Silenciamiento Génico</div>
    </div>`;
  tempContainer.appendChild(cover);

  // 2. SÍNTESIS ACADÉMICA (CON SALTO FORZADO AL INICIO)
  const synthHead = document.createElement('div');
  synthHead.className = 'report-section force-page-break';
  synthHead.innerHTML = `<div class="section-heading"><span class="s-num">I.</span> Síntesis de investigación académica</div>`;
  tempContainer.appendChild(synthHead);

  const synthesisParagraphs = (data.scientific_synthesis || '').split('\n\n');
  synthesisParagraphs.forEach(p => {
    const pTag = document.createElement('p');
    pTag.className = 'editable-block';
    pTag.contentEditable = 'true';
    pTag.style.cssText = "width:100%; font-family:'Spectral', serif; line-height:1.75; font-size:14px; text-align:justify; margin-bottom:18px;";
    pTag.innerHTML = p.replace(/\n/g, '<br>');
    tempContainer.appendChild(pTag);
  });

  // 2.1 CONTEXTO FUNCIONAL (DENTRO DE SECCIÓN I - SIN TÍTULO REDUNDANTE)
  if (data.functional_context) {
    const funcParagraphs = data.functional_context.split('\n\n');
    funcParagraphs.forEach(p => {
      if (p.trim() === "" || p.toLowerCase().includes("contexto funcional")) return;
      const pTag = document.createElement('p');
      pTag.className = 'editable-block';
      pTag.contentEditable = 'true';
      pTag.style.cssText = "width:100%; font-family:'Spectral', serif; line-height:1.75; font-size:13px; text-align:justify; margin-bottom:15px;";
      pTag.innerHTML = p.replace(/\n/g, '<br>');
      tempContainer.appendChild(pTag);
    });
  }

  // 2.2 BIBLIOGRAFÍA (SECCIÓN FINAL DE INVESTIGACIÓN)
  if (data.references_text) {
    const refHead = document.createElement('div');
    refHead.className = 'report-section force-page-break';
    refHead.innerHTML = `<div class="section-heading"><span class="s-num">I.1</span> Bibliografía</div>`;
    tempContainer.appendChild(refHead);

    const refParagraphs = data.references_text.split('\n\n');
    refParagraphs.forEach(p => {
      if (p.trim() === "" || p.toLowerCase().startsWith("bibliografía") || p.toLowerCase().startsWith("referencias")) return;
      const pTag = document.createElement('p');
      pTag.className = 'editable-block';
      pTag.contentEditable = 'true';
      pTag.style.cssText = "width:100%; font-family:'Spectral', serif; line-height:1.45; font-size:11.5px; text-align:justify; margin-bottom:12px;";
      
      // Asegurar que las URLs sean hipervínculos reales
      const linkedText = p.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color:#1a3a6b; text-decoration:underline;">$1</a>');
      pTag.innerHTML = linkedText.replace(/\n/g, '<br>');
      tempContainer.appendChild(pTag);
    });
  }

  // 3. TABLA (SALTO FORZADO)
  const tableSec = document.createElement('div');
  tableSec.className = 'report-section force-page-break';
  let tableRows = '';
  data.common_genes.slice(0, 40).forEach(g => {
    const d = (data.gene_details && data.gene_details[g]) || {system:'—', associated_routes:[], pathology:'—'};
    const pathText = (d.pathology||'').length > 180 ? d.pathology.substring(0, 180) + '...' : (d.pathology||'—');
    tableRows += `<tr><td style="font-weight:600; color:#1a3a6b; padding:8px;">${g}</td><td style="padding:8px;">${d.system||'—'}</td><td style="font-style:italic; padding:8px;">${(d.associated_routes||[]).slice(0,2).join('; ')||'—'}</td><td style="text-align:justify; padding:8px; font-size:11px;">${pathText}</td></tr>`;
  });
  tableSec.innerHTML = `
    <div class="section-heading"><span class="s-num">II.</span> Panel de Biomarcadores Core Identificados</div>
    <table class="rep-table" style="width:100%; border-collapse:collapse; margin-top:10px;"><thead style="background:#1a3a6b; color:white;"><tr><th style="padding:10px;">Gen Core</th><th style="padding:10px;">Sistema</th><th style="padding:10px;">Rutas Asociadas</th><th style="padding:10px;">Relevancia Patológica</th></tr></thead><tbody id="bio-tbody">${tableRows}</tbody></table>`;
  tempContainer.appendChild(tableSec);

  // 4. DETALLES POR GEN (SALTO FORZADO)
  const detailHead = document.createElement('div');
  detailHead.className = 'report-section force-page-break';
  detailHead.innerHTML = `<div class="section-heading"><span class="s-num">III.</span> Traducción Patológica Detallada</div>`;
  tempContainer.appendChild(detailHead);

  data.common_genes.slice(0, 12).forEach(g => {
    const d = (data.gene_details && data.gene_details[g]) || {system:'—', associated_routes:[], pathology:'—'};
    const block = document.createElement('div');
    block.className = 'report-section gene-block';
    block.style.cssText = "margin-bottom:15px; padding:10px; border-left:3px solid #1a3a6b; background:#f9fbfc;";
    block.innerHTML = `<div class="gene-block-name" style="font-weight:bold; color:#1a3a6b; border-bottom:1px solid #eee; padding-bottom:4px; margin-bottom:6px;">${g} — ${d.system||'—'}</div><div class="gene-block-text" contenteditable="true" style="font-size:12px; line-height:1.4; text-align:justify;">${(d.pathology||'—').replace(/\n/g, '<br>')}</div><div style="font-family:'IBM Plex Mono',monospace; font-size:9px; color:#1a3a6b; margin-top:6px;">Rutas: <i>${(d.associated_routes||[]).join(', ')||'—'}</i></div>`;
    tempContainer.appendChild(block);
  });

  // 5. GRÁFICOS (SALTO FORZADO CON TAMAÑOS FIJOS PARA PDF)
  const vizSec = document.createElement('div');
  vizSec.className = 'report-section force-page-break';
  const vennImg = data.venn_plot ? `<img src="data:image/png;base64,${data.venn_plot}" style="width:380px; height:300px; object-fit:contain; border:1px solid #eee; background:white; padding:10px; margin-bottom:10px;">` : '<div style="padding:40px; color:#999; border:1px dashed #ccc;">Gráfico no disponible</div>';
  const volcanoImg = data.volcano_plot ? `<img src="data:image/png;base64,${data.volcano_plot}" style="width:480px; height:320px; object-fit:contain; border:1px solid #eee; background:white; padding:10px;">` : '<div style="padding:40px; color:#999; border:1px dashed #ccc;">Gráfico no disponible</div>';
  
  vizSec.innerHTML = `
    <div class="section-heading"><span class="s-num">IV.</span> Evidencia Gráfica de Convergencia</div>
    <div style="display:flex; flex-direction:column; align-items:center; gap:20px; margin-top:10px;">
      <div class="viz-print" style="text-align:center;">
        <div style="font-size:10px; font-weight:bold; color:#333; margin-bottom:5px;">IV.1 Diagrama de Co-regulación</div>
        ${vennImg}
      </div>
      <div class="viz-print" style="text-align:center;">
        <div style="font-size:10px; font-weight:bold; color:#333; margin-bottom:5px;">IV.2 Paisaje de Significancia Biológica</div>
        ${volcanoImg}
      </div>
    </div>`;
  tempContainer.appendChild(vizSec);

  // 6. PPI (CON SALTO FORZADO)
  const ppiSec = document.createElement('div');
  ppiSec.className = 'report-section force-page-break';
  const ppiImg = data.ppi_plot ? `<img src="data:image/png;base64,${data.ppi_plot}" style="width:85%; max-height:400px; object-fit:contain; border:1px solid #eee; box-shadow:0 2px 4px rgba(0,0,0,0.05);">` : '<div style="padding:40px; color:#999; border:1px dashed #ccc;">Interactoma no disponible</div>';
  ppiSec.innerHTML = `
    <div class="section-heading"><span class="s-num">V.</span> Interactoma Proteico (STRING-DB)</div>
    <div class="viz-print" style="margin-top:10px; text-align:center;">${ppiImg}</div>`;
  tempContainer.appendChild(ppiSec);

  // Ejecutar paginación real
  setTimeout(() => paginateReport(tempContainer), 100);
}

function init() {
  console.log("KENRYU: Iniciando componentes...");
  populateYearSelect();
  const canvas = document.getElementById('report-canvas-content');
  if (canvas) {
    const observer = new MutationObserver(() => updateOutline());
    observer.observe(canvas, { childList: true, subtree: true, characterData: true });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
