// ── GLOBALS ───────────────────────────────────────────────────────────────────
const API_URL = window.location.hostname.includes('github.io')
  ? "https://kenryu007-nutriken.hf.space"
  : "";
let lastResult = null;
const GENE_STORE = new Map();
let geneStoreIdx = 0;
const VIEW_TITLES = {
  clinical:'Condición Clínica', gene:'Análisis de Gen',
  nutrient:'Suplemento / Hierba', plan:'Plan Clínico Nutrigenómico', report:'Editor de Informe'
};

// ── MARKDOWN RENDERER LIGERO ──────────────────────────────────────────────────
// Convierte **bold** → <strong>, \n\n → <p>, líneas "• item" → <ul><li>
function renderMarkdown(text) {
  if (!text) return '';
  text = String(text);
  const paragraphs = text.split(/\n\n+/);
  const out = [];
  paragraphs.forEach(p => {
    p = p.trim();
    if (!p) return;
    // ¿Es bloque de bullets?
    if (/^[•·\-]\s/m.test(p)) {
      const items = p.split(/\n/).filter(l => /^[•·\-]\s/.test(l.trim()))
        .map(l => l.replace(/^[•·\-]\s*/, '').trim())
        .map(l => l.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>'));
      out.push('<ul class="md-bullets">' + items.map(i => '<li>' + i + '</li>').join('') + '</ul>');
    } else {
      const html = p
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br/>');
      out.push('<p>' + html + '</p>');
    }
  });
  // Post-proceso: fusionar <ul> consecutivos en uno solo
  const merged = [];
  for (let i = 0; i < out.length; i++) {
    if (out[i].startsWith('<ul') && merged.length && merged[merged.length-1].startsWith('<ul')) {
      const prev = merged[merged.length-1];
      const inner = out[i].slice(out[i].indexOf('>')+1, out[i].lastIndexOf('</ul>'));
      merged[merged.length-1] = prev.replace('</ul>', inner + '</ul>');
    } else {
      merged.push(out[i]);
    }
  }
  return merged.join('');
}

// Helper de idioma para mensajes dinámicos del terminal
function _LG() { return (typeof getLang === 'function') ? getLang() : 'es'; }

// Helper: prefiere campo en español si existe
function _es(obj, field) {
  if (!obj) return '';
  const esVal = obj[field + '_es'];
  if (esVal !== undefined && esVal !== null && esVal !== '') return esVal;
  return obj[field] || '';
}

// ── NAV ───────────────────────────────────────────────────────────────────────
function switchView(name) {
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('view-'+name).classList.add('active');
  document.getElementById('nav-'+name).classList.add('active');
  document.getElementById('view-title').textContent = (window.VIEW_TITLES || VIEW_TITLES)[name];
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
  if (g.location) html += '<div class="gp-field"><div class="gp-label">Localización Genómica</div><div class="gp-val gp-mono">'+g.location+'</div></div>';
  if (g.ensembl_id) html += '<div class="gp-field"><div class="gp-label">Ensembl Gene ID</div><div class="gp-val gp-mono" style="color:var(--teal);font-size:13px">'+g.ensembl_id+'</div></div>';
  if (g.gene_id) html += '<div class="gp-field"><div class="gp-label">NCBI Gene ID</div><div class="gp-val gp-mono">'+g.gene_id+'</div></div>';
  if (g.summary) html += '<div class="gp-field"><div class="gp-label">Función Biológica</div><div class="gp-summary">'+g.summary+'</div></div>';
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
  showLoader(_LG()==='en'?'Analyzing...':'Analizando...');
  log('term-clinical', (_LG()==='en'?'Query: "':'Consulta: "')+q+'"', 'info');
  try {
    var d = await post('/api/clinical', {query: q, lang: (typeof getLang==='function'?getLang():'es')});
    lastResult = d;
    renderClinical(d);
    populateReportFull();
  } catch(e) { log('term-clinical', 'Error: '+e.message, 'err'); }
  finally { hideLoader(); btn.disabled = false; }
}

function renderClinical(d) {
  document.getElementById('clinical-out').style.display = 'block';
  var rw = document.getElementById('risk-box-wrap');
  var html = '<div style="background:var(--bg1);border:1px solid var(--border);border-radius:var(--r);padding:16px;margin-bottom:20px">' +
    '<div class="md-content" style="font-size:13px;color:var(--text-dim);line-height:1.7">' + renderMarkdown(d.description || '') + '</div></div>';

  if (d.drug_alerts && d.drug_alerts.length) {
    html += renderInteractionsBlock((typeof nkT==='function'?nkT('cl.drug_ix'):'Interacciones fármaco-suplemento'), d.drug_alerts, 'drug');
  }
  if (d.food_alerts && d.food_alerts.length) {
    html += renderInteractionsBlock((typeof nkT==='function'?nkT('cl.food_ix'):'Interacciones con alimentos'), d.food_alerts, 'food');
  }
  rw.innerHTML = html;

  if (d.genes && d.genes.length) { show('c-genes'); makeGenePills(d.genes, 'c-genes-body'); }
  if (d.pathway && d.pathway.name) {
    show('c-pathway');
    document.getElementById('c-pathway-body').innerHTML =
      '<div class="pathway-box">' +
      '<div class="pathway-id">' + d.pathway.id + '</div>' +
      '<div class="pathway-name">' + d.pathway.name + '</div>' +
      '<p class="pathway-desc">' + (d.pathway.description||'').slice(0,400) + '...</p>' +
      '<a class="ext-link teal" href="' + d.pathway.kegg_url + '" target="_blank">' + (typeof nkT==='function'?nkT('cl.kegg_link'):'Ver en KEGG') + '</a>' +
      '</div>';
  }
  if (d.supplements) { show('c-supps'); renderSuppTabs('c-supp-tabs','c-supp-panels', d.supplements); }
  if (d.references) {
    show('c-refs');
    document.getElementById('c-refs-body').innerHTML = d.references.map(function(r) {
      return '<tr><td>' + r.title + '</td><td>' + r.authors + ' &middot; ' + r.journal + ' &middot; ' + r.year + '</td><td><a class="ref-link" href="' + r.url + '" target="_blank">PMID ' + r.pmid + '</a></td></tr>';
    }).join('');
  }
}

// ── MODULO 2: GEN ─────────────────────────────────────────────────────────────
async function runGene() {
  var raw = document.getElementById('gene-input').value.trim();
  if (!raw) return;
  var genes = raw.split(',').map(function(g){ return g.trim().toUpperCase(); }).filter(Boolean);
  showLoader(_LG()==='en'?'Querying genes...':'Consultando genes...');
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
    document.getElementById('g-cond-body').innerHTML = d.related_conditions.map(function(c) {
      return '<div class="cond-item"><div class="cond-name">' + c.condition + '</div><div class="cond-risk">' + c.matching_genes.join(', ') + '</div></div>';
    }).join('');
  }
  if (d.supplements) { show('g-supps'); renderSuppTabs('g-supp-tabs','g-supp-panels', d.supplements); }
}

// ── MODULO 3: SUPLEMENTO ──────────────────────────────────────────────────────
async function runNutrient() {
  var nut = document.getElementById('nutrient-input').value.trim();
  if (!nut) return;
  showLoader(_LG()==='en'?'Searching...':'Buscando...');
  log('term-nutrient', (_LG()==='en'?'Searching: ':'Buscando: ')+nut, 'info');
  try {
    var d = await post('/api/nutrient', {nutrient: nut, lang: (typeof getLang==='function'?getLang():'es')});
    lastResult = d;
    renderNutrient(d);
  } catch(e) {
    log('term-nutrient', 'MSK: '+e.message+' — buscando dosis…', 'info');
    // Aunque MSK no tenga ficha, mostrar la DOSIS si existe en la base local
    try {
      var lang = (typeof getLang==='function') ? getLang() : 'es';
      var dz = await (await fetch(API_URL + '/api/dosing?q=' + encodeURIComponent(nut) + '&lang=' + lang)).json();
      if (dz && dz.found) {
        document.getElementById('nutrient-out').style.display = 'block';
        document.getElementById('n-herb-title').textContent = (dz.dosing['name_'+lang]||dz.dosing.name||nut);
        document.getElementById('n-herb-body').innerHTML = '';
        renderDosing(dz.dosing);
        log('term-nutrient', 'Dosis encontrada en base local.', 'ok');
      } else {
        log('term-nutrient', 'Sin ficha MSK ni dosis para: '+nut, 'err');
      }
    } catch(e2) { log('term-nutrient', 'Error: '+e.message, 'err'); }
  }
  finally { hideLoader(); }
}
function renderNutrient(d) {
  var h = d.msk_data || {};
  document.getElementById('nutrient-out').style.display = 'block';
  document.getElementById('n-herb-title').textContent = h.name || d.nutrient || 'Ficha clínica';

  // Asegurar que el slug y url se propagan al renderizador
  if (!h.slug && d.slug) h.slug = d.slug;
  if (!h.url && d.msk_url) h.url = d.msk_url;

  // Tarjeta de DOSIS basada en evidencia (cuánto tomar realmente)
  renderDosing(d.dosing);
  // Evidencia científica (PubMed) para CUALQUIER hierba del catálogo (307)
  renderHerbEvidence(d.herb_evidence, d.dosing);
  // Fitoquímicos de la planta desde LOTUS (CC0) — escala botánica masiva
  renderBotanical(d.botanical);

  // Preparar contenedores para la tarjeta detallada (reutiliza renderSuppTabs)
  var body = document.getElementById('n-herb-body');
  body.innerHTML = '<div class="supp-tabs" id="n-supp-tabs" style="display:none"></div>' +
                   '<div id="n-supp-panels"></div>';

  // Render con la tarjeta completa (igual que en el módulo Condición Clínica)
  renderSuppTabs('n-supp-tabs', 'n-supp-panels', [h]);

  // Si hay ruta KEGG asociada, mostrarla debajo
  if (d.pathway && d.pathway.name) {
    body.insertAdjacentHTML('beforeend',
      '<div class="pathway-box" style="margin-top:18px">' +
      '<div class="pathway-id">' + (d.pathway.id || '') + '</div>' +
      '<div class="pathway-name">' + d.pathway.name + '</div>' +
      (d.pathway.description ? '<p class="pathway-desc">' + d.pathway.description.slice(0, 400) + '...</p>' : '') +
      '<a class="ext-link teal" href="' + d.pathway.kegg_url + '" target="_blank">Ver en KEGG</a>' +
      '</div>');
  }

  // Referencias científicas si vinieron
  if (d.references && d.references.length) {
    var refsHTML = '<div class="card" style="margin-top:18px">' +
      '<div class="card-head"><span class="card-title">Referencias científicas</span><span class="card-badge blue">PubMed</span></div>' +
      '<div class="card-body"><table class="sci-table"><thead><tr><th>Título</th><th>Autores · Revista · Año</th><th>Link</th></tr></thead><tbody>' +
      d.references.map(function(r) {
        return '<tr><td>' + r.title + '</td><td>' + r.authors + ' · ' + r.journal + ' · ' + r.year + '</td><td><a class="ref-link" href="' + r.url + '" target="_blank">PMID ' + r.pmid + '</a></td></tr>';
      }).join('') + '</tbody></table></div></div>';
    body.insertAdjacentHTML('beforeend', refsHTML);
  }

  // Hacer este resultado disponible para el editor de informe (como en clinical)
  lastResult = {
    condition: h.name || d.nutrient,
    query: d.nutrient,
    description: _es(h, 'clinical_summary') || _es(h, 'what_is_it') || '',
    supplements: [h],
    references: d.references || [],
    pathway: d.pathway || {},
    drug_alerts: [],
    food_alerts: [],
    genes: []
  };
}

// ── BLOQUE 4: INTERACCIONES CONTEXTUALIZADAS ─────────────────────────────────
function renderInteractionsBlock(title, alerts, kind) {
  if (!alerts || !alerts.length) return '';
  const counts = { crit: 0, warn: 0, info: 0 };
  alerts.forEach(function(a) { counts[a.severity_tone || 'info'] = (counts[a.severity_tone || 'info'] || 0) + 1; });
  const chips = [
    counts.crit ? '<span class="ix-summary-chip ix-chip-crit">' + counts.crit + ' crítica' + (counts.crit > 1 ? 's' : '') + '</span>' : '',
    counts.warn ? '<span class="ix-summary-chip ix-chip-warn">' + counts.warn + ' precaución</span>' : '',
    counts.info ? '<span class="ix-summary-chip ix-chip-info">' + counts.info + ' monitorear</span>' : ''
  ].filter(Boolean).join('');

  let html = '<div class="ix-block">' +
    '<div class="ix-block-head"><h3 class="ix-block-title">' + title + '</h3>' +
    '<div class="ix-block-chips">' + chips + '</div></div>' +
    '<div class="ix-block-body">';

  alerts.forEach(function(a) {
    const isDrug = kind === 'drug';
    const left = isDrug ? (a.drug || '') : (a.food || '');
    const right = a.herb || '';
    const tone = a.severity_tone || 'info';
    const sevLabel = a.severity_label || (tone === 'crit' ? 'Crítica' : tone === 'warn' ? 'Precaución' : 'Monitorear');
    const mech = a.mechanism || a.description || a.alert || '—';
    const rec = a.recommendation || 'Vigilar respuesta clínica.';
    html += '<div class="ix-card ix-' + tone + '">' +
      '<div class="ix-card-head">' +
      '<div class="ix-pair"><span class="ix-left">' + left + '</span><span class="ix-arrow">↔</span><span class="ix-right">' + right + '</span></div>' +
      '<span class="ix-sev ix-sev-' + tone + '">' + sevLabel + '</span>' +
      '</div>' +
      '<div class="ix-card-body">' +
      '<div class="ix-row"><span class="ix-row-lbl">Mecanismo</span><span class="ix-row-val">' + mech + '</span></div>' +
      (isDrug && a.alert ? '<div class="ix-row"><span class="ix-row-lbl">Evidencia MSK</span><span class="ix-row-val ix-row-quote">' + a.alert + '</span></div>' : '') +
      '<div class="ix-row ix-row-action"><span class="ix-row-lbl">Recomendación</span><span class="ix-row-val">' + rec + '</span></div>' +
      '</div></div>';
  });
  html += '</div></div>';
  return html;
}

// ── EVIDENCE GRADING ──────────────────────────────────────────────────────────
function gradeEvidence(s) {
  const cs = (_es(s, 'clinical_summary') || '').length;
  const moa = (_es(s, 'mechanism_of_action') || '').length;
  const di = ((s.drug_interactions_es && s.drug_interactions_es.length) || (s.drug_interactions || []).length);
  const score = (cs > 1500 ? 2 : cs > 600 ? 1 : 0) +
                (moa > 800 ? 2 : moa > 300 ? 1 : 0) +
                (di > 8 ? 1 : 0);
  var _lg = (typeof getLang === 'function') ? getLang() : 'es';
  if (score >= 4) return { label: _lg==='en'?'High evidence':'Evidencia alta', tone: 'high' };
  if (score >= 2) return { label: _lg==='en'?'Moderate evidence':'Evidencia media', tone: 'mid' };
  return { label: _lg==='en'?'Limited evidence':'Evidencia limitada', tone: 'low' };
}

function parseInteraction(raw) {
  const m = raw.match(/^([^:]{2,80}):\s*(.+)$/s);
  if (m) return { drug: m[1].trim(), detail: m[2].trim() };
  return { drug: '', detail: raw };
}

function renderList(items, max) {
  if (!items || !items.length) return '';
  const limit = max || items.length;
  return '<ul class="supp-list">' + items.slice(0, limit).map(function(x) {
    return '<li>' + x + '</li>';
  }).join('') + '</ul>';
}

function renderSuppTabs(tabsId, panelsId, supps) {
  if (!supps || !supps.length) return;
  var _L = (typeof getLang === 'function') ? getLang() : 'es';
  function TT(es, en) { return _L === 'en' ? en : es; }

  document.getElementById(tabsId).innerHTML = supps.map(function(s,i) {
    return '<div class="supp-tab' + (i===0?' active':'') + '" onclick="swSupp(\'' + tabsId + '\',\'' + panelsId + '\',' + i + ')">' + (s.name||'Sup.') + '</div>';
  }).join('');

  document.getElementById(panelsId).innerHTML = supps.map(function(s,i) {
    const ev = gradeEvidence(s);

    // ── Recolectar TODOS los campos disponibles ─────────────────────────────
    const sci = s.scientific_name || '';
    const commonNames = (s.common_names && Array.isArray(s.common_names) && s.common_names.length)
                        ? s.common_names : [];
    const whatIsIt   = _es(s, 'what_is_it');
    const summary    = _es(s, 'clinical_summary');
    const moa        = _es(s, 'mechanism_of_action');
    const dosage     = _es(s, 'dosage');
    const adverse    = _es(s, 'adverse_reactions');
    const contra     = _es(s, 'contraindications');

    const uses     = (s.purported_uses_es && s.purported_uses_es.length) ? s.purported_uses_es : (s.purported_uses || []);
    const benefits = (s.benefits_es && s.benefits_es.length) ? s.benefits_es : (s.benefits || []);
    const sideEff  = (s.side_effects_es && s.side_effects_es.length) ? s.side_effects_es : (s.side_effects || []);
    const warnings = (s.warnings_es && s.warnings_es.length) ? s.warnings_es : (s.warnings || []);
    const foodIx   = (s.food_interactions_es && s.food_interactions_es.length) ? s.food_interactions_es : (s.food_interactions || []);
    const drugIxRaw= (s.drug_interactions_es && s.drug_interactions_es.length) ? s.drug_interactions_es : (s.drug_interactions || []);
    const drugIx   = drugIxRaw.map(parseInteraction);

    // ── Filtros suaves: descartar líneas que SOLO son títulos de subsección ─
    // (cosas como "include:", "Advertencias para el paciente:", "usado para:")
    function looksLikeSubheader(line) {
      if (!line) return true;
      const t = line.trim();
      if (t.length < 4) return true;
      // Solo descartamos si termina con ":" Y es corta (es un encabezado de subsección)
      if (t.endsWith(':') && t.length < 60) return true;
      // Patrones específicos de basura conocida
      if (/^(include|incluir|used to|usado para|side effects|efectos secundarios|warnings|advertencias)\s*:?\s*$/i.test(t)) return true;
      return false;
    }
    const benefitsClean = benefits.filter(function(x) { return !looksLikeSubheader(x); });
    const sideEffClean  = sideEff.filter(function(x) { return !looksLikeSubheader(x); });
    const warningsClean = warnings.filter(function(x) { return !looksLikeSubheader(x); });
    const usesClean     = uses.filter(function(x) { return !looksLikeSubheader(x); });
    const foodIxClean   = foodIx.filter(function(x) { return !looksLikeSubheader(x); });

    // ── Construir bloques (sólo si tienen contenido real) ──────────────────
    let patientHTML = '';
    if (whatIsIt) {
      patientHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-info-circle"></i> ' + TT('¿Qué es?','What is it?') + '</h4><p class="supp-text">' + whatIsIt + '</p></div>';
    }
    if (benefitsClean.length) {
      patientHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-check-circle"></i> ' + TT('Usos y beneficios potenciales','Potential uses and benefits') + '</h4>' + renderList(benefitsClean, 12) + '</div>';
    }
    if (sideEffClean.length) {
      patientHTML += '<div class="supp-card-sec supp-warn"><h4 class="supp-h supp-h-warn"><i class="fas fa-exclamation-triangle"></i> ' + TT('Efectos secundarios','Side effects') + '</h4>' + renderList(sideEffClean, 14) + '</div>';
    }
    if (warningsClean.length) {
      patientHTML += '<div class="supp-card-sec supp-warn-crit"><h4 class="supp-h supp-h-warn"><i class="fas fa-shield-alt"></i> ' + TT('¿Qué más debe saber?','What else should you know?') + '</h4>' + renderList(warningsClean, 14) + '</div>';
    }

    let proHTML = '';
    if (summary) {
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-stethoscope"></i> ' + TT('Resumen clínico','Clinical summary') + '</h4><p class="supp-text">' + summary + '</p></div>';
    }
    if (usesClean.length) {
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-flask"></i> ' + TT('Usos clínicos respaldados','Supported clinical uses') + '</h4>' + renderList(usesClean, 12) + '</div>';
    }
    if (moa) {
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-atom"></i> ' + TT('Mecanismo de acción','Mechanism of action') + '</h4><p class="supp-text">' + moa + '</p></div>';
    }
    if (dosage) {
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-prescription-bottle"></i> ' + TT('Dosis estudiadas','Studied doses') + '</h4><p class="supp-text">' + dosage + '</p></div>';
    }
    if (contra) {
      proHTML += '<div class="supp-card-sec supp-warn"><h4 class="supp-h supp-h-warn"><i class="fas fa-ban"></i> ' + TT('Contraindicaciones','Contraindications') + '</h4><p class="supp-text">' + contra + '</p></div>';
    }
    if (adverse) {
      proHTML += '<div class="supp-card-sec supp-warn"><h4 class="supp-h supp-h-warn"><i class="fas fa-notes-medical"></i> ' + TT('Reacciones adversas','Adverse reactions') + '</h4><p class="supp-text">' + adverse + '</p></div>';
    }
    if (drugIx.length) {
      const initialIx = drugIx.slice(0, 6);
      const restIx = drugIx.slice(6);
      const ixHTML = initialIx.map(function(ix) {
        return '<div class="supp-ix-row">' + (ix.drug ? '<span class="supp-ix-drug">' + ix.drug + '</span>' : '') + '<span class="supp-ix-detail">' + ix.detail + '</span></div>';
      }).join('');
      const restHTML = restIx.length ? '<details class="supp-more"><summary>' + TT('Ver ' + restIx.length + ' interacciones más','See ' + restIx.length + ' more interactions') + '</summary>' +
        restIx.map(function(ix) {
          return '<div class="supp-ix-row">' + (ix.drug ? '<span class="supp-ix-drug">' + ix.drug + '</span>' : '') + '<span class="supp-ix-detail">' + ix.detail + '</span></div>';
        }).join('') + '</details>' : '';
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-capsules"></i> ' + TT('Interacciones hierba–fármaco','Herb–drug interactions') + ' <span class="supp-count">(' + drugIx.length + ')</span></h4><div class="supp-ix-list">' + ixHTML + restHTML + '</div></div>';
    }
    if (foodIxClean.length) {
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-utensils"></i> ' + TT('Interacciones con alimentos','Food interactions') + '</h4>' + renderList(foodIxClean, 10) + '</div>';
    }
    // Evidencia científica enriquecida (PubMed/PubChem) — refleja el enriquecimiento de las 307
    var evz = s.herb_evidence;
    if (evz && (evz.pubmed_pmids || evz.reference)) {
      var evH = '';
      if (evz.reference) evH += '<p class="supp-text">' + evz.reference + '</p>';
      if (evz.pubmed_pmids && evz.pubmed_pmids.length)
        evH += '<div style="font-size:12px;margin-top:4px;"><strong>PMID:</strong> ' +
          evz.pubmed_pmids.slice(0,5).map(function(p){return '<a href="https://pubmed.ncbi.nlm.nih.gov/'+p+'" target="_blank" style="color:var(--teal);">'+p+'</a>';}).join(' · ') + '</div>';
      if (evz.pubchem_cid) evH += '<div style="font-size:11px;margin-top:3px;color:var(--text-faint);">PubChem CID: <a href="https://pubchem.ncbi.nlm.nih.gov/compound/'+evz.pubchem_cid+'" target="_blank" style="color:var(--text-faint);">'+evz.pubchem_cid+'</a></div>';
      proHTML += '<div class="supp-card-sec"><h4 class="supp-h"><i class="fas fa-book-medical"></i> ' + TT('Evidencia científica (PubMed)','Scientific evidence (PubMed)') + '</h4>' + evH + '</div>';
    }

    // ── Header (nombre + sci + nombres comunes + chip de evidencia) ────────
    const cnHTML = commonNames.length
                   ? '<span class="supp-common">' + TT('También: ','Also: ') + commonNames.slice(0,5).join(' · ') + '</span>'
                   : '';
    const sciHTML = sci ? '<span class="supp-sci">' + sci + '</span>' : '';

    // ── Wrapper de sección por audiencia ───────────────────────────────────
    let sections = '';
    if (patientHTML) {
      sections += '<div class="supp-audience supp-aud-patient">' +
                  '<div class="supp-aud-head"><i class="fas fa-user"></i> ' + TT('Para pacientes','For patients') + '</div>' +
                  patientHTML + '</div>';
    }
    if (proHTML) {
      sections += '<div class="supp-audience supp-aud-pro">' +
                  '<div class="supp-aud-head"><i class="fas fa-user-md"></i> ' + TT('Para profesionales de la salud','For healthcare professionals') + '</div>' +
                  proHTML + '</div>';
    }
    if (!patientHTML && !proHTML) {
      sections = '<div class="supp-card-sec"><p class="supp-text">Sin datos disponibles.</p></div>';
    }

    const mskUrl = s.url || ('https://www.mskcc.org/cancer-care/integrative-medicine/herbs/' + (s.slug || ''));
    sections += '<div class="supp-card-foot"><a href="' + mskUrl + '" target="_blank" class="supp-link"><i class="fas fa-external-link-alt"></i> Ficha completa en MSKCC</a></div>';

    return '<div class="supp-panel' + (i===0?' active':'') + '" id="' + panelsId + '-' + i + '">' +
      '<div class="supp-card">' +
      '<div class="supp-card-head">' +
      '<div class="supp-card-title"><h3>' + (s.name || 'Suplemento') + '</h3>' + sciHTML + cnHTML + '</div>' +
      '<span class="supp-chip supp-chip-' + ev.tone + '">' + ev.label + '</span>' +
      '</div>' + sections + '</div></div>';
  }).join('');
}

function swSupp(tabsId, panelsId, i) {
  document.querySelectorAll('#'+tabsId+' .supp-tab').forEach(function(t,j){ t.classList.toggle('active', i===j); });
  document.querySelectorAll('#'+panelsId+' .supp-panel').forEach(function(p,j){ p.classList.toggle('active', i===j); });
}

// ── BLOQUE 3: EDITOR ESTILO KENRYU (PAGINACIÓN A4 + VANCOUVER) ────────────────
function _vancouverRef(r, idx) {
  const authors = r.authors || 'Autores no especificados';
  const title = (r.title || '').replace(/\.$/, '');
  const journal = r.journal || '';
  const year = r.year || '';
  const pmid = r.pmid || '';
  const url = r.url || (pmid ? 'https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/' : '');
  return '<li style="margin-bottom:10px;font-size:10pt;line-height:1.55;color:#111"><b>' + authors + '</b> ' +
    (title ? title + '. ' : '') +
    (journal ? '<i>' + journal + '</i>. ' : '') +
    (year ? year + '. ' : '') +
    (pmid ? '<a href="' + url + '" target="_blank" style="color:#1a3a6b;text-decoration:none">PMID: ' + pmid + '</a>.' : '') +
    '</li>';
}

function _refMarkdown(r, idx) {
  const authors = r.authors || 'Autores no especificados';
  const title = (r.title || '').replace(/\.$/, '');
  const journal = r.journal || '';
  const year = r.year || '';
  const pmid = r.pmid || '';
  const url = r.url || (pmid ? 'https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/' : '');
  return (idx+1) + '. **' + authors + '** ' + (title ? title + '. ' : '') +
    (journal ? '*' + journal + '*. ' : '') +
    (year ? year + '. ' : '') +
    (pmid ? '[PMID: ' + pmid + '](' + url + ').' : '');
}

// Paginación A4 estilo Kenryu
let nkPageCount = 0;

function nkCreateNewPage() {
  nkPageCount++;
  const page = document.createElement('div');
  page.className = 'a4-page';
  page.id = 'a4-page-' + nkPageCount;
  const inner = document.createElement('div');
  inner.className = 'page-inner';
  page.appendChild(inner);
  page.insertAdjacentHTML('beforeend',
    '<div class="page-footer"><span>NUTRIKEN Bioinformatics Engine</span><span class="page-num">' + nkPageCount + '</span></div>');
  return page;
}

function nkPaginateReport(sourceElement) {
  const canvas = document.getElementById('report-canvas-content');
  if (!canvas) return;
  canvas.innerHTML = '';
  nkPageCount = 0;

  const testPage = document.createElement('div');
  testPage.className = 'a4-page';
  testPage.style.position = 'absolute';
  testPage.style.visibility = 'hidden';
  testPage.style.top = '-9999px';
  document.body.appendChild(testPage);
  const testInner = document.createElement('div');
  testInner.className = 'page-inner';
  testPage.appendChild(testInner);

  const MAX_HEIGHT = 960;
  let currentPage = nkCreateNewPage();
  let currentInner = currentPage.querySelector('.page-inner');
  canvas.appendChild(currentPage);
  let currentHeight = 0;
  const pageStack = [];

  function newPage() {
    currentPage = nkCreateNewPage();
    currentInner = currentPage.querySelector('.page-inner');
    canvas.appendChild(currentPage);
    currentHeight = 0;
    let parent = currentInner;
    pageStack.forEach(function(info) {
      const fresh = document.createElement(info.tag);
      if (info.className) fresh.className = info.className;
      parent.appendChild(fresh);
      info.current = fresh;
      parent = fresh;
    });
  }
  function getInsertionPoint() {
    return pageStack.length ? pageStack[pageStack.length - 1].current : currentInner;
  }
  function measure(node) {
    const clone = node.cloneNode(true);
    testInner.appendChild(clone);
    const h = clone.offsetHeight;
    testInner.innerHTML = '';
    return h;
  }

  const SUBDIVISIBLE_TAGS = new Set(['SECTION','DIV','OL','UL','ARTICLE']);
  const ATOMIC_TAGS = new Set(['P','H1','H2','H3','H4','H5','H6','LI','TABLE','BLOCKQUOTE','PRE','IMG']);

  function placeNode(node) {
    if (!node || node.nodeType !== 1) return;
    if (node.classList && node.classList.contains('force-page-break')) {
      if (currentHeight > 0) newPage();
      return;
    }
    const tag = node.tagName;
    const h = measure(node);
    if (currentHeight + h <= MAX_HEIGHT) {
      getInsertionPoint().appendChild(node.cloneNode(true));
      currentHeight += h + 6;
      return;
    }
    if (ATOMIC_TAGS.has(tag) || (node.classList && node.classList.contains('tarjeta-pdf')) || h <= MAX_HEIGHT) {
      if (currentHeight > 0) newPage();
      getInsertionPoint().appendChild(node.cloneNode(true));
      currentHeight += Math.min(h, MAX_HEIGHT) + 6;
      return;
    }
    if (SUBDIVISIBLE_TAGS.has(tag) && node.children.length > 0) {
      const firstHead = node.querySelector(':scope > h1, :scope > h2, :scope > h3, :scope > h4');
      if (firstHead) {
        const headH = measure(firstHead);
        if (currentHeight + headH + 150 > MAX_HEIGHT && currentHeight > 0) newPage();
      }
      const wrap = document.createElement(tag);
      if (node.className) wrap.className = node.className;
      if (node.id) wrap.id = node.id;
      getInsertionPoint().appendChild(wrap);
      pageStack.push({tag: tag, className: node.className, current: wrap});
      Array.from(node.children).forEach(placeNode);
      pageStack.pop();
      return;
    }
    if (currentHeight > 0) newPage();
    getInsertionPoint().appendChild(node.cloneNode(true));
    currentHeight += Math.min(h, MAX_HEIGHT) + 6;
  }

  Array.from(sourceElement.children).forEach(placeNode);
  document.body.removeChild(testPage);

  const rtMeta = document.getElementById('rt-meta');
  if (rtMeta && window._currentReportId) {
    const base = rtMeta.textContent.split(' · ').slice(0, 3).join(' · ');
    rtMeta.textContent = base + ' · ' + nkPageCount + ' pág.';
  }
}

function populateReportFull() {
  if (!lastResult) return;
  const d = lastResult;
  const date = new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
  const id = 'NK-' + Math.random().toString(36).substr(2, 6).toUpperCase();
  window._currentReportId = id;
  window._currentReportDate = date;

  const template = document.getElementById('clinical-report-template');
  const preview = document.getElementById('report-web-preview');
  document.getElementById('editor-empty').style.display = 'none';
  preview.style.display = 'none';

  document.getElementById('rep-id').innerText = id;
  document.getElementById('rep-date').innerText = "Fecha: " + date;
  const rtMeta = document.getElementById('rt-meta');
  if (rtMeta) rtMeta.textContent = (d.condition || 'Consulta') + ' · ' + id + ' · ' + date;
  document.getElementById('rep-summary').innerHTML = renderMarkdown(d.description || 'Análisis molecular detallado.');

  document.getElementById('rep-genes').innerHTML = (d.genes || []).map(function(g) {
    return '<div class="tarjeta-pdf">' +
      '<p style="margin:0;font-size:13px;color:#1a3a6b;font-weight:bold">Biomarcador:</p>' +
      '<p style="margin:0;font-size:15px;color:black"><b>mRNA: ' + g.symbol + '</b></p>' +
      '<p style="margin:5px 0;font-size:11.5px;color:black">' + (g.name || '') + '</p>' +
      '<p style="margin:0;font-size:11px;color:#1a3a6b">' +
      '<a href="' + g.ncbi_url + '" target="_blank" style="color:#1a3a6b">Ver Ficha NCBI</a> · ' +
      '<a href="' + g.ensembl_url + '" target="_blank" style="color:#1a3a6b">Ensembl</a>' +
      '</p></div>';
  }).join('') || '<p>No se identificaron biomarcadores específicos para esta condición.</p>';

  const pathwayHTML = d.pathway && d.pathway.name ?
    '<div class="tarjeta-pdf" style="border-left-color:#0d9488">' +
    '<p style="margin:0;font-size:14px;color:#0f766e"><b>Ruta Metabólica: ' + d.pathway.name + '</b></p>' +
    '<p style="margin:8px 0;font-size:11.5px;color:black">' + (d.pathway.description || 'Interconexión metabólica regulada.') + '</p>' +
    '<p style="margin:0;font-size:11px"><a href="' + d.pathway.kegg_url + '" target="_blank" style="color:#0d9488">Explorar en KEGG</a></p>' +
    '</div>' : '<p>No se identificaron rutas específicas adicionales.</p>';
  document.getElementById('rep-pathway').innerHTML = pathwayHTML;

  const sevColor = function(t) { return t === 'crit' ? '#b91c1c' : t === 'warn' ? '#d97706' : '#1a3a6b'; };
  const sevLbl = function(t) { return t === 'crit' ? 'CRÍTICA' : t === 'warn' ? 'PRECAUCIÓN' : 'MONITOREAR'; };
  const drugRows = (d.drug_alerts || []).map(function(a) {
    const tone = a.severity_tone || 'info';
    return '<div class="tarjeta-pdf" style="border-left-color:' + sevColor(tone) + ';margin-bottom:10px">' +
      '<p style="margin:0 0 4px 0;font-size:13px;color:#111"><b>' + a.drug + '</b> ↔ <b>' + a.herb + '</b> <span style="float:right;font-size:10px;color:' + sevColor(tone) + ';letter-spacing:.5px">' + sevLbl(tone) + '</span></p>' +
      '<p style="margin:0 0 4px 0;font-size:11.5px;color:#333"><b>Mecanismo:</b> ' + (a.mechanism || '—') + '</p>' +
      '<p style="margin:0;font-size:11.5px;color:#333"><b>Recomendación:</b> ' + (a.recommendation || '—') + '</p></div>';
  }).join('');
  const foodRows = (d.food_alerts || []).map(function(a) {
    const tone = a.severity_tone || 'warn';
    return '<div class="tarjeta-pdf" style="border-left-color:' + sevColor(tone) + ';margin-bottom:10px">' +
      '<p style="margin:0 0 4px 0;font-size:13px;color:#111"><b>' + a.food + '</b> ↔ <b>' + a.herb + '</b> <span style="float:right;font-size:10px;color:' + sevColor(tone) + ';letter-spacing:.5px">' + sevLbl(tone) + '</span></p>' +
      '<p style="margin:0 0 4px 0;font-size:11.5px;color:#333"><b>Mecanismo:</b> ' + (a.mechanism || a.description || '—') + '</p>' +
      '<p style="margin:0;font-size:11.5px;color:#333"><b>Recomendación:</b> ' + (a.recommendation || '—') + '</p></div>';
  }).join('');
  document.getElementById('rep-interactions').innerHTML = (drugRows + foodRows) || '<p>No se detectaron interacciones críticas en este perfil.</p>';

  document.getElementById('rep-supplements').innerHTML = (d.supplements || []).map(function(s) {
    const moa = (_es(s, 'mechanism_of_action') || '').slice(0, 500);
    const usesArr = (s.purported_uses_es && s.purported_uses_es.length) ? s.purported_uses_es : (s.purported_uses || []);
    const benArr = (s.benefits_es && s.benefits_es.length) ? s.benefits_es : (s.benefits || []);
    const uses = usesArr.slice(0,5).join(', ') || benArr.slice(0,4).filter(function(b){ return !b.match(/(used to|usado para):?$/i); }).join(', ');
    const warning = ((s.warnings_es && s.warnings_es.length) ? s.warnings_es : (s.warnings || []))[0] || '';
    return '<div class="tarjeta-pdf" style="border-left-color:#15803d;margin-bottom:12px">' +
      '<p style="margin:0 0 6px 0;font-size:14px;color:#166534"><b>' + s.name + '</b>' + (s.scientific_name ? ' <i style="font-size:11px;color:#555">— ' + s.scientific_name + '</i>' : '') + '</p>' +
      '<p style="margin:0 0 6px 0;font-size:11.5px;color:#111"><b>Resumen clínico:</b> ' + (_es(s, 'clinical_summary') || '').slice(0, 500) + ((_es(s, 'clinical_summary') || '').length > 500 ? '…' : '') + '</p>' +
      (moa ? '<p style="margin:0 0 6px 0;font-size:11.5px;color:#111"><b>Mecanismo:</b> ' + moa + (moa.length >= 500 ? '…' : '') + '</p>' : '') +
      (uses ? '<p style="margin:0 0 6px 0;font-size:11.5px;color:#111"><b>Usos respaldados:</b> ' + uses + '</p>' : '') +
      (warning ? '<p style="margin:0 0 6px 0;font-size:11px;color:#b45309"><b>Advertencia:</b> ' + warning + '</p>' : '') +
      '<p style="margin:0;font-size:11px"><a href="https://www.mskcc.org/cancer-care/integrative-medicine/herbs/' + s.slug + '" target="_blank" style="color:#15803d">Ficha completa en MSKCC</a></p>' +
      '</div>';
  }).join('') || '<p>Investigación de suplementos completada.</p>';

  const refs = d.references || [];
  document.getElementById('rep-refs').innerHTML = refs.length
    ? '<ol style="padding-left:25px;margin:0">' + refs.map(_vancouverRef).join('') + '</ol>'
    : '<p>No se encontraron referencias bibliográficas indexadas para esta consulta.</p>';

  preview.innerHTML = template.innerHTML;
  nkPaginateReport(preview);
}

async function exportToPDF() {
  if (!lastResult) return alert("Realice un análisis clínico primero.");
  const btn = document.querySelector('.rt-btn-primary');
  const originalHTML = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando…'; }
  try {
    const res = await fetch(API_URL + '/api/report-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data: lastResult,
        report_id: window._currentReportId || ('NK-' + Math.random().toString(36).substr(2, 6).toUpperCase()),
        date: window._currentReportDate || new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
      })
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const blob = await res.blob();
    const cond = (lastResult.condition || 'informe').toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const filename = 'nutriken-' + cond + '-' + (window._currentReportId || 'reporte') + '.pdf';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('Error al generar el PDF: ' + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = originalHTML; }
  }
}

function exportToMDZip() {
  if (!lastResult) return alert("Realice un análisis clínico primero.");
  const d = lastResult;
  const date = window._currentReportDate || new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
  const id = window._currentReportId || ('NK-' + Math.random().toString(36).substr(2, 6).toUpperCase());
  const cond = (d.condition || 'informe').toLowerCase().replace(/[^a-z0-9]+/g, '-');

  let md = '# Informe Clínico Nutricional NutriKen\n\n';
  md += '**ID:** ' + id + '  \n**Fecha:** ' + date + '  \n**Condición:** ' + (d.condition || '—') + '  \n**Consulta original:** ' + (d.query || '') + '\n\n---\n\n';
  md += '## I. Síntesis de Investigación Nutricional\n\n' + (d.description || '').replace(/\*\*/g, '**') + '\n\n';
  md += '## II. Panel de Biomarcadores Genómicos\n\n';
  if (d.genes && d.genes.length) {
    d.genes.forEach(function(g) {
      md += '### ' + g.symbol + '\n' + (g.name || '') + '\n\n- NCBI: ' + (g.ncbi_url || '') + '\n- Ensembl: ' + (g.ensembl_url || '') + '\n\n';
    });
  } else { md += '_No se identificaron biomarcadores específicos._\n\n'; }
  md += '## III. Ruta Metabólica Relacionada (KEGG)\n\n';
  if (d.pathway && d.pathway.name) {
    md += '**' + d.pathway.name + '**\n\n' + (d.pathway.description || '') + '\n\nKEGG: ' + (d.pathway.kegg_url || '') + '\n\n';
  } else { md += '_No se identificaron rutas metabólicas específicas._\n\n'; }
  md += '## IV. Interacciones Farmacológicas\n\n';
  const allIx = [].concat(d.drug_alerts || [], d.food_alerts || []);
  if (allIx.length) {
    (d.drug_alerts || []).forEach(function(a) {
      md += '### ' + a.drug + ' ↔ ' + a.herb + ' — ' + (a.severity_label || 'Monitorear') + '\n\n- **Mecanismo:** ' + (a.mechanism || '') + '\n- **Recomendación:** ' + (a.recommendation || '') + '\n\n';
    });
    (d.food_alerts || []).forEach(function(a) {
      md += '### ' + a.food + ' ↔ ' + a.herb + ' — ' + (a.severity_label || 'Precaución') + '\n\n- **Mecanismo:** ' + (a.mechanism || a.description || '') + '\n- **Recomendación:** ' + (a.recommendation || '') + '\n\n';
    });
  } else { md += '_No se detectaron interacciones críticas en este perfil._\n\n'; }
  md += '## V. Evidencia de Suplementación (MSKCC)\n\n';
  (d.supplements || []).forEach(function(s) {
    md += '### ' + s.name + (s.scientific_name ? ' — *' + s.scientific_name + '*' : '') + '\n\n';
    const cs = _es(s, 'clinical_summary');
    const moa = _es(s, 'mechanism_of_action');
    if (cs) md += '**Resumen clínico:** ' + cs.slice(0, 800) + '\n\n';
    if (moa) md += '**Mecanismo de acción:** ' + moa.slice(0, 600) + '\n\n';
    const usesArr = (s.purported_uses_es && s.purported_uses_es.length) ? s.purported_uses_es : (s.purported_uses || []);
    if (usesArr.length) md += '**Usos respaldados:** ' + usesArr.join(', ') + '\n\n';
    md += '**Fuente:** https://www.mskcc.org/cancer-care/integrative-medicine/herbs/' + s.slug + '\n\n';
  });
  md += '## VI. Bibliografía Científica (Vancouver)\n\n';
  (d.references || []).forEach(function(r, i) { md += _refMarkdown(r, i) + '\n\n'; });

  if (typeof JSZip === 'undefined') {
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'nutriken-' + cond + '-' + id + '.md';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    return;
  }
  const zip = new JSZip();
  zip.file('informe.md', md);
  zip.file('datos.json', JSON.stringify(d, null, 2));
  zip.file('README.md', '# NutriKen — Informe ' + id + '\n\nGenerado: ' + date + '  \nCondición: ' + (d.condition || '—') + '\n\nArchivos incluidos:\n- informe.md — informe clínico completo en Markdown\n- datos.json — datos crudos\n');
  zip.generateAsync({ type: 'blob' }).then(function(blob) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'nutriken-' + cond + '-' + id + '.zip';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  });
}

// ── UTILS ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    var r = await fetch(API_URL + '/api/stats');
    if (!r.ok) return;
    var s = await r.json();
    document.getElementById('stats-line').textContent = 'Hierbas: ' + s.herbs_in_cache + ' · Genes: ' + s.genes_in_cache + ' · Consultas: ' + s.total_queries;
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


// ══ NAVEGADOR ALFABETICO DE HIERBAS A-Z ══════════════════════════════════════
let HERBS_INDEX = null;
let HERBS_CURRENT_LETTER = null;

async function loadHerbsIndex() {
  if (HERBS_INDEX) return HERBS_INDEX;
  try {
    const r = await fetch(API_URL + '/api/herbs-index');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    HERBS_INDEX = await r.json();
    return HERBS_INDEX;
  } catch (e) {
    console.error('herbs-index error:', e);
    return null;
  }
}

async function initHerbBrowser() {
  const lettersBox = document.getElementById('hb-letters');
  const countBox = document.getElementById('hb-count');
  if (!lettersBox || lettersBox.children.length) return;
  countBox.textContent = 'Cargando…';

  const data = await loadHerbsIndex();
  if (!data || !data.letters) {
    countBox.textContent = 'Error al cargar';
    return;
  }

  const ALL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  let html = '';
  ALL.forEach(function(L) {
    const available = data.letters.indexOf(L) !== -1;
    const count = available ? (data.by_letter[L] || []).length : 0;
    html += '<button class="hb-letter' + (available ? '' : ' disabled') + '" ' +
            (available ? 'onclick="selectHerbLetter(\'' + L + '\')"' : 'disabled') + '>' +
            L + (available ? '<span class="hb-letter-n">' + count + '</span>' : '') +
            '</button>';
  });
  if (data.letters.indexOf('#') !== -1) {
    const count = (data.by_letter['#'] || []).length;
    html += '<button class="hb-letter" onclick="selectHerbLetter(\'#\')">#<span class="hb-letter-n">' + count + '</span></button>';
  }
  lettersBox.innerHTML = html;
  countBox.textContent = data.total + (typeof getLang==='function' && getLang()==='en' ? ' herbs available' : ' hierbas disponibles');

  // Auto-select first available letter
  if (data.letters.length) selectHerbLetter(data.letters[0]);
}

function selectHerbLetter(letter) {
  HERBS_CURRENT_LETTER = letter;
  document.querySelectorAll('.hb-letter').forEach(function(b) {
    b.classList.toggle('active', b.textContent.replace(/\d+/g, '').trim() === letter);
  });
  renderHerbList(letter, document.getElementById('hb-filter').value);
}

function renderHerbList(letter, filter) {
  const list = document.getElementById('hb-list');
  if (!HERBS_INDEX || !letter) return;
  let herbs = HERBS_INDEX.by_letter[letter] || [];
  filter = (filter || '').trim().toLowerCase();
  if (filter) {
    herbs = herbs.filter(function(h) {
      return (h.name || '').toLowerCase().indexOf(filter) !== -1 ||
             (h.scientific_name || '').toLowerCase().indexOf(filter) !== -1;
    });
  }
  if (!herbs.length) {
    list.innerHTML = '<div class="hb-empty">' + (filter ? 'Ninguna hierba con "' + filter + '"' : 'Sin resultados') + '</div>';
    return;
  }
  list.innerHTML = herbs.map(function(h) {
    const sci = h.scientific_name ? '<span class="hb-item-sci">' + h.scientific_name + '</span>' : '';
    return '<button class="hb-item" onclick="pickHerb(\'' + (h.slug || '').replace(/\W/g,'') + '\', \'' + (h.name || '').replace(/\'/g, "\\'") + '\')">' +
           '<span class="hb-item-name">' + h.name + '</span>' + sci + '</button>';
  }).join('');
}

function filterHerbsLetter() {
  if (!HERBS_CURRENT_LETTER) return;
  renderHerbList(HERBS_CURRENT_LETTER, document.getElementById('hb-filter').value);
}

function pickHerb(slug, name) {
  document.getElementById('nutrient-input').value = name;
  runNutrient();
}

// Inicializar el navegador la primera vez que el usuario entra al modulo nutrient
(function hookSwitchView() {
  if (typeof switchView !== 'function') { setTimeout(hookSwitchView, 50); return; }
  const _orig = switchView;
  window.switchView = function(name) {
    _orig(name);
    if (name === 'nutrient') initHerbBrowser();
  };
})();



// Stubs de compatibilidad
function fmt(cmd) { document.execCommand(cmd); }
function switchPanel(name) {
  document.querySelectorAll('.panel-tab').forEach(function(t){ t.classList.toggle('active', t.textContent.toLowerCase().includes(name==='outline'?'esquema':name)); });
  document.querySelectorAll('.panel-content').forEach(function(p){ p.classList.toggle('active', p.id === 'panel-'+name); });
}
function insertBlock() {}
function addPage() {}
function exportText() {}
function exportMarkdown() {}

// ── PLAN CLÍNICO (módulo): genera el plan compilado dentro de la app ─────────
let _lastPlanUrl = '';
function _planUrl() {
  var q = (document.getElementById('plan-input').value || '').trim();
  if (!q) { document.getElementById('plan-input').focus(); return ''; }
  var lang = (typeof getLang === 'function') ? getLang() : 'es';
  return API_URL + '/api/plan/export?q=' + encodeURIComponent(q) + '&lang=' + lang;
}
function generatePlan() {
  var url = _planUrl();
  if (!url) return;
  _lastPlanUrl = url;
  document.getElementById('plan-frame').src = url;
  document.getElementById('plan-frame-wrap').style.display = 'block';
  document.getElementById('plan-dl').style.display = '';
}
function qtPlan(q) {
  document.getElementById('plan-input').value = q;
  generatePlan();
}
function downloadPlan() {
  if (_lastPlanUrl) window.open(_lastPlanUrl, '_blank');
}

// ── DOSIS basada en evidencia (bilingüe ES/EN) ──────────────────────────────
function renderDosing(dose) {
  var card = document.getElementById('n-dosing');
  var body = document.getElementById('n-dosing-body');
  if (!card || !body) return;
  if (!dose) { card.style.display = 'none'; body.innerHTML = ''; return; }
  var lang = (typeof getLang === 'function') ? getLang() : 'es';
  var T = (typeof nkT === 'function') ? nkT : function (k) { return k; };
  function pick(base) { return dose[base + '_' + lang] || dose[base + '_es'] || dose[base] || '—'; }
  var rows = [
    [T('dosing.standard'), dose.standard_dose || '—'],
    [T('dosing.therapeutic'), dose.therapeutic_dose || '—'],
    [T('dosing.form'), pick('form')],
    [T('dosing.timing'), pick('timing')],
    [T('dosing.ul'), dose.upper_limit || '—'],
    [T('dosing.evidence'), dose.evidence || '—'],
    [T('dosing.interactions'), pick('interactions')]
  ];
  var html = '<div class="dosing-name" style="font-weight:600;font-size:1.05rem;margin-bottom:10px;">' +
             (dose['name_' + lang] || dose.name || '') +
             ' <span style="color:#8892a0;font-weight:400;font-size:.85rem;">· ' + pick('category') + '</span></div>';
  html += '<table class="sci-table" style="width:100%;border-collapse:collapse;">';
  rows.forEach(function (r) {
    html += '<tr><td style="padding:6px 10px;color:#8892a0;white-space:nowrap;vertical-align:top;font-weight:600;">' +
            r[0] + '</td><td style="padding:6px 10px;">' + r[1] + '</td></tr>';
  });
  html += '</table>';
  html += '<div style="margin-top:12px;padding:10px 12px;background:rgba(200,169,110,.08);border-left:3px solid #c8a96e;border-radius:6px;font-size:.9rem;line-height:1.5;">' +
          '<strong>' + T('dosing.notes') + ':</strong> ' + pick('notes') + '</div>';
  // Seguridad / horario (cirugía, quimio, separación de fármacos)
  var s = dose.safety;
  if (s) {
    var warns = [];
    if (s.stop_days_before_surgery)
      warns.push((lang === 'en' ? '🔪 Stop ' + s.stop_days_before_surgery + ' days before surgery' : '🔪 Suspender ' + s.stop_days_before_surgery + ' días antes de cirugía') + (s.bleeding_risk ? (lang === 'en' ? ' (bleeding risk)' : ' (riesgo de sangrado)') : ''));
    else if (s.bleeding_risk)
      warns.push(lang === 'en' ? '🩸 Bleeding risk with anticoagulants/antiplatelets' : '🩸 Riesgo de sangrado con anticoagulantes/antiplaquetarios');
    if (s['separate_from_' + lang] || s.separate_from_es) warns.push('⏱️ ' + (s['separate_from_' + lang] || s.separate_from_es));
    if (s['oncology_caution_' + lang] || s.oncology_caution_es) warns.push('☢️ ' + (s['oncology_caution_' + lang] || s.oncology_caution_es));
    if (s['note_' + lang] || s.note_es) warns.push('⚠️ ' + (s['note_' + lang] || s.note_es));
    if (warns.length) {
      html += '<div style="margin-top:10px;padding:10px 12px;background:rgba(227,74,95,.09);border-left:3px solid #e34a5f;border-radius:6px;font-size:.85rem;line-height:1.6;">' +
              '<strong>' + (lang === 'en' ? 'Safety & timing' : 'Seguridad y horario') + ':</strong><br>' +
              warns.join('<br>') + '</div>';
    }
  }
  body.innerHTML = html;
  card.style.display = 'block';
  // Referencias científicas (PubMed) — provenance para uso clínico/JOSS
  var refBlock = '';
  if (dose.reference) refBlock += '<div style="margin-top:10px;font-size:.82rem;"><strong>' + (lang==='en'?'Reference':'Referencia') + ':</strong> ' + dose.reference + '</div>';
  if (dose.pubmed_pmids && dose.pubmed_pmids.length) {
    refBlock += '<div style="margin-top:6px;font-size:.78rem;"><strong>PMID:</strong> ' +
      dose.pubmed_pmids.slice(0,5).map(function(p){return '<a href="https://pubmed.ncbi.nlm.nih.gov/'+p+'" target="_blank" style="color:#4fc3a1;">'+p+'</a>';}).join(' · ') + '</div>';
  }
  if (dose.pubchem_cid) refBlock += '<div style="margin-top:4px;font-size:.75rem;color:#8892a0;">PubChem CID: <a href="https://pubchem.ncbi.nlm.nih.gov/compound/'+dose.pubchem_cid+'" target="_blank" style="color:#8892a0;">'+dose.pubchem_cid+'</a></div>';
  if (refBlock) body.innerHTML += '<div style="margin-top:12px;padding:10px 12px;background:rgba(79,195,161,.07);border-left:3px solid #4fc3a1;border-radius:6px;">' + refBlock + '</div>';
}
// ── Evidencia científica por hierba (307) — PubMed, para JOSS/uso clínico ────
function renderHerbEvidence(ev, dosing) {
  if (!ev || (!ev.pubmed_pmids && !ev.reference)) return;
  var card = document.getElementById('n-dosing');
  var body = document.getElementById('n-dosing-body');
  if (!card || !body) return;
  var lang = (typeof getLang === 'function') ? getLang() : 'es';
  var h = '';
  if (!dosing) {
    // No hay dosis curada, pero sí evidencia: mostrar encabezado
    h += '<div style="font-weight:600;font-size:1.02rem;margin-bottom:8px;">' + (ev.name || '') +
         (ev.scientific_name ? ' <span style="color:#8892a0;font-weight:400;font-size:.82rem;">· ' + ev.scientific_name + '</span>' : '') + '</div>';
  }
  h += '<div style="margin-top:6px;padding:10px 12px;background:rgba(79,195,161,.07);border-left:3px solid #4fc3a1;border-radius:6px;">';
  h += '<strong style="font-size:.85rem;">' + (lang === 'en' ? 'Scientific evidence (PubMed)' : 'Evidencia científica (PubMed)') + '</strong>';
  if (ev.reference) h += '<div style="margin-top:6px;font-size:.82rem;">' + ev.reference + '</div>';
  if (ev.pubmed_pmids && ev.pubmed_pmids.length)
    h += '<div style="margin-top:6px;font-size:.78rem;"><strong>PMID:</strong> ' +
         ev.pubmed_pmids.slice(0,5).map(function(p){return '<a href="https://pubmed.ncbi.nlm.nih.gov/'+p+'" target="_blank" style="color:#4fc3a1;">'+p+'</a>';}).join(' · ') + '</div>';
  if (ev.pubchem_cid) h += '<div style="margin-top:4px;font-size:.75rem;color:#8892a0;">PubChem CID: <a href="https://pubchem.ncbi.nlm.nih.gov/compound/'+ev.pubchem_cid+'" target="_blank" style="color:#8892a0;">'+ev.pubchem_cid+'</a></div>';
  h += '</div>';
  if (!dosing) { body.innerHTML = h; card.style.display = 'block'; }
  else { body.innerHTML += h; }
}
// ── Fitoquímicos de la planta (LOTUS, CC0) — escala botánica masiva ─────────
function renderBotanical(bot) {
  if (!bot || !bot.compound_count) return;
  var card = document.getElementById('n-dosing');
  var body = document.getElementById('n-dosing-body');
  if (!card || !body) return;
  var lang = (typeof getLang === 'function') ? getLang() : 'es';
  var comps = (bot.compounds || []).slice(0, 12).map(function(c) {
    var wd = c.wikidata_id ? '<a href="'+c.wikidata_id+'" target="_blank" style="color:var(--teal);">'+(c.lotus_id||'LOTUS')+'</a>' : (c.lotus_id||'');
    return '<div style="font-size:11px;color:var(--text-dim);border-bottom:1px solid var(--border);padding:3px 0;">' +
           wd + (c.smiles ? ' <span style="color:var(--text-faint);font-family:var(--font-mono);">'+ c.smiles.slice(0,42) +'</span>' : '') + '</div>';
  }).join('');
  var h = '<div style="margin-top:10px;padding:10px 12px;background:rgba(21,128,61,.07);border-left:3px solid #15803d;border-radius:6px;">' +
    '<strong style="font-size:.85rem;">' + (lang==='en'?'Phytochemicals (LOTUS)':'Fitoquímicos (LOTUS)') + '</strong> ' +
    '<span style="color:var(--text-faint);font-size:.78rem;">· ' + bot.compound_count + (lang==='en'?' compounds':' compuestos') + '</span>' +
    '<div style="margin-top:6px;">' + comps + '</div>' +
    '<a href="'+ (bot.lotus_query||'#') +'" target="_blank" style="color:var(--teal);font-size:.75rem;">' + (lang==='en'?'View all on LOTUS':'Ver todo en LOTUS') + '</a>' +
    '<div style="color:var(--text-faint);font-size:.7rem;margin-top:3px;">' + (bot.source||'') + '</div></div>';
  if (card.style.display !== 'block') { body.innerHTML = h; card.style.display = 'block'; }
  else { body.innerHTML += h; }
}
function populateReport() { populateReportFull(); }