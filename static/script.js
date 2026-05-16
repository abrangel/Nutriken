// ── GLOBALS ───────────────────────────────────────────────────────────────────
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
  var r = await fetch(url, {
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

// ── GENE PILLS — usa GENE_STORE, sin JSON inline en onclick ──────────────────
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

// ── GENE PANEL LATERAL DINAMICO ───────────────────────────────────────────────
function openGP(key) {
  var g = GENE_STORE.get(key);
  if (!g) return;

  document.getElementById('gp-name').textContent = g.symbol || '---';
  var body = document.getElementById('gene-panel-body');

  var html = '';

  if (g.name) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Nombre Completo</div>'+
      '<div class="gp-val">'+g.name+'</div>'+
    '</div>';

  if (g.chromosome) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Cromosoma</div>'+
      '<div class="gp-val gp-mono">Chr'+g.chromosome+'</div>'+
    '</div>';

  if (g.location) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Localizacion Genomica</div>'+
      '<div class="gp-val gp-mono">'+g.location+'</div>'+
    '</div>';

  if (g.ensembl_id) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Ensembl Gene ID</div>'+
      '<div class="gp-val gp-mono" style="color:var(--teal);font-size:13px">'+g.ensembl_id+'</div>'+
    '</div>';

  if (g.gene_id) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">NCBI Gene ID</div>'+
      '<div class="gp-val gp-mono">'+g.gene_id+'</div>'+
    '</div>';

  if (g.summary) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Funcion Biologica</div>'+
      '<div class="gp-summary">'+g.summary+'</div>'+
    '</div>';

  // Links section
  var links = '';
  if (g.ncbi_url) links +=
    '<a class="ext-link gold" href="'+g.ncbi_url+'" target="_blank">'+
      '<i class="fas fa-external-link-alt"></i> NCBI Gene'+
    '</a>';

  if (g.ensembl_url) links +=
    '<a class="ext-link teal" href="'+g.ensembl_url+'" target="_blank">'+
      '<i class="fas fa-dna"></i> Ensembl'+
      (g.ensembl_id ? ' ('+g.ensembl_id+')' : '')+
    '</a>';

  if (g.ensembl_id) links +=
    '<a class="ext-link teal" style="opacity:0.8" href="https://www.ensembl.org/Homo_sapiens/Gene/Variation_Gene/Table?g='+g.ensembl_id+'" target="_blank">'+
      '<i class="fas fa-project-diagram"></i> Ensembl Variantes'+
    '</a>';

  if (g.snpedia_url) links +=
    '<a class="ext-link" style="background:rgba(200,169,110,.1);border:1px solid rgba(200,169,110,.2);color:var(--gold)" href="'+g.snpedia_url+'" target="_blank">'+
      '<i class="fas fa-flask"></i> SNPedia'+
    '</a>';

  if (g.omim_url) links +=
    '<a class="ext-link blue" href="'+g.omim_url+'" target="_blank">'+
      '<i class="fas fa-database"></i> OMIM'+
    '</a>';

  links +=
    '<a class="ext-link" style="background:rgba(79,195,161,.08);border:1px solid rgba(79,195,161,.15);color:var(--teal)" href="https://www.genecards.org/cgi-bin/carddisp.pl?gene='+g.symbol+'" target="_blank">'+
      '<i class="fas fa-id-card"></i> GeneCards'+
    '</a>';

  if (g.symbol) links +=
    '<a class="ext-link" style="background:rgba(110,170,220,.08);border:1px solid rgba(110,170,220,.15);color:var(--blue)" href="https://clinicalgenome.org/gene/'+g.symbol+'" target="_blank">'+
      '<i class="fas fa-heartbeat"></i> ClinGen'+
    '</a>';

  if (links) html +=
    '<div class="gp-field">'+
      '<div class="gp-label">Bases de Datos</div>'+
      '<div class="gp-links">'+links+'</div>'+
    '</div>';

  body.innerHTML = html;
  document.getElementById('gene-panel').classList.add('open');
}

function closeGenePanel() {
  document.getElementById('gene-panel').classList.remove('open');
}

// ── MODULO 1: CLINICO ─────────────────────────────────────────────────────────
async function runClinical() {
  var q = document.getElementById('clinical-input').value.trim();
  if (!q) return;
  var btn = document.getElementById('btn-clinical');
  btn.disabled = true;
  showLoader('Buscando en MSK, NCBI y PubMed...');
  log('term-clinical', 'Consulta: "'+q+'"', 'info');
  try {
    var d = await post('/api/clinical', {query: q});
    lastResult = d;
    if (d.query_en && d.query_en !== q.toLowerCase())
      log('term-clinical', 'Traducido al ingles: "'+d.query_en+'"', 'info');
    log('term-clinical', 'Condicion: '+d.condition, 'ok');
    log('term-clinical', 'Suplementos MSK: '+((d.supplements||[]).map(function(s){return s.name;}).join(', ')||'---'), 'ok');
    log('term-clinical', 'Alertas farmacos: '+(d.drug_alerts||[]).length+' | Alimentos: '+(d.food_alerts||[]).length, 'ok');
    log('term-clinical', 'Referencias PubMed: '+(d.references||[]).length, 'ok');
    renderClinical(d);
    populateReport(d);
  } catch(e) {
    log('term-clinical', 'Error: '+e.message, 'err');
    alert(e.message);
  } finally {
    hideLoader();
    btn.disabled = false;
  }
}

function renderClinical(d) {
  document.getElementById('clinical-out').style.display = 'block';
  var rw = document.getElementById('risk-box-wrap');
  var html = '';

  // Description
  html += '<div style="background:var(--bg1);border:1px solid var(--border);border-radius:var(--r);padding:16px 20px;margin-bottom:20px">'+
    '<div style="font-family:var(--font-mono);font-size:9px;color:var(--gold);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Descripcion Clinica</div>'+
    '<div style="font-size:13px;color:var(--text-dim);line-height:1.7">'+(d.description||'')+'</div>'+
  '</div>';

  // Drug alerts
  if (d.drug_alerts && d.drug_alerts.length) {
    html += '<div class="risk-box" style="margin-bottom:16px">'+
      '<div class="risk-title">Interacciones con Farmacos (fuente: MSK)</div>';
    d.drug_alerts.forEach(function(a) {
      html += '<div class="risk-item">'+
        '<strong style="color:var(--amber)">'+a.drug+'</strong> + '+
        '<strong style="color:var(--gold)">'+a.herb+'</strong>'+
        '<span style="color:var(--red);font-size:10px;margin-left:6px">'+a.severity+'</span>'+
        '<div style="font-size:11px;margin-top:3px">'+a.alert+'</div>'+
        (a.source ? '<div style="font-size:10px;margin-top:2px"><a style="color:var(--teal)" href="'+a.source+'" target="_blank">Ver fuente MSK</a></div>' : '')+
      '</div>';
    });
    html += '</div>';
  }

  // Food alerts
  if (d.food_alerts && d.food_alerts.length) {
    html += '<div class="risk-box" style="margin-bottom:16px;background:rgba(245,166,35,.06);border-color:rgba(245,166,35,.2)">'+
      '<div class="risk-title" style="color:var(--amber)">Interacciones con Alimentos</div>';
    d.food_alerts.forEach(function(a) {
      html += '<div class="risk-item">'+
        '<strong style="color:var(--amber)">'+a.food+'</strong>'+
        '<div style="font-size:11px;margin-top:2px">'+a.description+'</div>'+
        (a.source ? '<div style="font-size:10px"><a style="color:var(--teal)" href="'+a.source+'" target="_blank">Ver fuente MSK</a></div>' : '')+
      '</div>';
    });
    html += '</div>';
  }

  // Related drugs
  if (d.drugs_related && d.drugs_related.length) {
    html += '<div style="background:var(--bg3);border:1px solid var(--border-md);border-radius:var(--r);padding:12px 16px;margin-bottom:16px">'+
      '<div style="font-family:var(--font-mono);font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Farmacos Relacionados</div>'+
      '<div style="display:flex;flex-wrap:wrap;gap:6px">';
    d.drugs_related.forEach(function(dr) {
      html += '<span style="background:var(--blue-dim);border:1px solid rgba(110,170,220,.2);color:var(--blue);font-family:var(--font-mono);font-size:11px;padding:3px 10px;border-radius:4px">'+dr+'</span>';
    });
    html += '</div></div>';
  }

  rw.innerHTML = html;

  // Genes — usando makeGenePills
  if (d.genes && d.genes.length) {
    show('c-genes');
    makeGenePills(d.genes, 'c-genes-body');
  }

  // Pathway
  if (d.pathway && d.pathway.name) {
    show('c-pathway');
    var chips = (d.pathway.genes||[]).slice(0,14).map(function(g){
      return '<span class="pg-tag">'+g.symbol+'</span>';
    }).join('');
    document.getElementById('c-pathway-body').innerHTML =
      '<div class="pathway-box">'+
        '<div class="pathway-id">'+d.pathway.id+'</div>'+
        '<div class="pathway-name">'+d.pathway.name+'</div>'+
        (d.pathway.description ? '<div class="pathway-desc">'+d.pathway.description.slice(0,400)+'</div>' : '')+
        (chips ? '<div class="pathway-genes">'+chips+'</div>' : '')+
        '<a class="ext-link teal" href="'+d.pathway.kegg_url+'" target="_blank">Ver ruta en KEGG</a>'+
        (d.pathway.image_url ? '<a class="ext-link gold" href="'+d.pathway.image_url+'" target="_blank">Imagen de ruta</a>' : '')+
      '</div>';
  }

  // Supplements
  if (d.supplements && d.supplements.length) {
    show('c-supps');
    renderSuppTabs('c-supp-tabs','c-supp-panels', d.supplements);
  }

  // References
  if (d.references && d.references.length) {
    show('c-refs');
    document.getElementById('c-refs-body').innerHTML = d.references.map(function(r) {
      return '<tr><td>'+(r.title||'---')+'</td>'+
        '<td>'+(r.authors||'')+' &middot; '+(r.journal||'')+' &middot; '+(r.year||'')+'</td>'+
        '<td><a class="ref-link" href="'+r.url+'" target="_blank">PMID '+r.pmid+'</a></td></tr>';
    }).join('');
  }
}

// ── MODULO 2: GEN ─────────────────────────────────────────────────────────────
async function runGene() {
  var raw = document.getElementById('gene-input').value.trim();
  if (!raw) return;
  var genes = raw.split(',').map(function(g){ return g.trim().toUpperCase(); }).filter(Boolean);
  showLoader('Consultando '+genes.length+' gen(es) — MyGene.info + NCBI...');
  log('term-gene', 'Genes: '+genes.join(', '), 'info');
  try {
    var d = await post('/api/gene', {genes: genes});
    lastResult = d;
    log('term-gene', 'Info NCBI: '+(d.genes_info||[]).length+' genes', 'ok');
    log('term-gene', 'Condiciones relacionadas: '+(d.related_conditions||[]).length, 'ok');
    renderGene(d);
  } catch(e) {
    log('term-gene', 'Error: '+e.message, 'err');
    alert(e.message);
  } finally {
    hideLoader();
  }
}

function renderGene(d) {
  document.getElementById('gene-out').style.display = 'block';

  if (d.genes_info && d.genes_info.length) {
    show('g-info');
    makeGenePills(d.genes_info, 'g-info-body');
  }

  if (d.related_conditions && d.related_conditions.length) {
    show('g-cond');
    document.getElementById('g-cond-body').innerHTML = d.related_conditions.map(function(c) {
      return '<div class="cond-item">'+
        '<div class="cond-name">'+c.condition+'</div>'+
        '<div class="cond-genes">'+c.matching_genes.map(function(g){
          return '<span class="cond-gene-tag">'+g+'</span>';
        }).join('')+'</div>'+
        (c.drugs&&c.drugs.length ? '<div style="font-size:10px;color:var(--blue);margin-top:4px">'+c.drugs.slice(0,3).join(' &middot; ')+'</div>' : '')+
      '</div>';
    }).join('');
  }

  if (d.supplements && d.supplements.length) {
    show('g-supps');
    renderSuppTabs('g-supp-tabs','g-supp-panels', d.supplements);
  }

  if (d.references && d.references.length) {
    show('g-refs');
    document.getElementById('g-refs-body').innerHTML = d.references.map(function(r) {
      return '<tr><td>'+(r.title||'---')+'</td>'+
        '<td>'+(r.journal||'')+' &middot; '+(r.year||'')+'</td>'+
        '<td><a class="ref-link" href="'+r.url+'" target="_blank">PMID '+r.pmid+'</a></td></tr>';
    }).join('');
  }
}

// ── MODULO 3: SUPLEMENTO ──────────────────────────────────────────────────────
async function runNutrient() {
  var nut = document.getElementById('nutrient-input').value.trim();
  if (!nut) return;
  showLoader('Buscando "'+nut+'" en MSK...');
  log('term-nutrient', 'Consultando MSK: '+nut, 'info');
  try {
    var d = await post('/api/nutrient', {nutrient: nut});
    lastResult = d;
    var h = d.msk_data;
    log('term-nutrient', 'Encontrado: '+h.name, 'ok');
    if (h.scientific_name) log('term-nutrient', 'Nombre cientifico: '+h.scientific_name, 'ok');
    log('term-nutrient', 'Interacciones farmacos: '+(h.drug_interactions||[]).length, 'ok');
    log('term-nutrient', 'Referencias PubMed: '+(d.references||[]).length, 'ok');
    renderNutrient(d);
  } catch(e) {
    log('term-nutrient', 'Error: '+e.message, 'err');
    alert(e.message);
  } finally {
    hideLoader();
  }
}

function renderNutrient(d) {
  var h = d.msk_data;
  document.getElementById('nutrient-out').style.display = 'block';
  document.getElementById('n-herb-title').textContent = h.name || d.nutrient;

  var sections = [
    {id:'benefits',            label:'Beneficios',              cls:''},
    {id:'side_effects',        label:'Efectos Adversos',        cls:'danger'},
    {id:'warnings',            label:'Advertencias',            cls:'warn'},
    {id:'drug_interactions',   label:'Interacciones Farmacos',  cls:'danger'},
    {id:'food_interactions',   label:'Interacciones Alimentos', cls:'warn'},
    {id:'mechanism_of_action', label:'Mecanismo de Accion',     cls:''},
    {id:'clinical_summary',    label:'Resumen Clinico',         cls:''},
    {id:'contraindications',   label:'Contraindicaciones',      cls:'danger'},
    {id:'dosage',              label:'Dosificacion',            cls:''},
  ].filter(function(s) {
    var v = h[s.id];
    return v && (Array.isArray(v) ? v.length > 0 : v.length > 10);
  });

  var headerBox =
    '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0 18px;border-bottom:1px solid var(--border);margin-bottom:16px">'+
      '<div>'+
        '<div style="font-family:var(--font-serif);font-size:20px;color:var(--gold)">'+(h.name||d.nutrient)+'</div>'+
        (h.scientific_name ? '<div style="font-size:11px;color:var(--text-dim);font-style:italic;margin-top:3px">'+h.scientific_name+'</div>' : '')+
        (h.common_names&&h.common_names.length ? '<div style="font-size:10px;color:var(--text-faint);margin-top:2px">'+h.common_names.join(' &middot; ')+'</div>' : '')+
      '</div>'+
      '<div style="display:flex;gap:8px;flex-wrap:wrap">'+
        '<a class="ext-link gold" href="'+d.msk_url+'" target="_blank">MSK</a>'+
        '<a class="ext-link blue" href="https://pubmed.ncbi.nlm.nih.gov/?term='+encodeURIComponent(d.nutrient)+'" target="_blank">PubMed</a>'+
      '</div>'+
    '</div>';

  var tabs = sections.map(function(s, i) {
    return '<div class="supp-tab'+(i===0?' active':'')+'" onclick="nhTab('+i+',this)">'+s.label+'</div>';
  }).join('');

  var panels = sections.map(function(s, i) {
    var v = h[s.id];
    var inner = '';
    if (Array.isArray(v)) {
      inner = '<div class="supp-sec '+s.cls+'"><div class="supp-sec-title">'+s.label+'</div>'+
        '<ul class="supp-list">'+v.map(function(x){ return '<li>'+x+'</li>'; }).join('')+'</ul></div>';
    } else {
      inner = '<div class="moa-box"><div class="moa-title">'+s.label+'</div>'+
        '<p class="supp-text">'+v.slice(0,1500)+(v.length>1500?'...':'')+'</p></div>';
    }
    return '<div class="supp-panel'+(i===0?' active':'')+'" id="nh-panel-'+i+'">'+inner+
      (h.url ? '<div style="margin-top:14px"><a class="ext-link gold" href="'+h.url+'" target="_blank">Ficha completa en MSK</a></div>' : '')+
    '</div>';
  }).join('');

  document.getElementById('n-herb-body').innerHTML =
    headerBox +
    '<div class="supp-tabs" id="nh-tabs">'+tabs+'</div>' +
    panels;

  if (d.references && d.references.length) {
    show('n-refs');
    document.getElementById('n-refs-body').innerHTML = d.references.map(function(r) {
      return '<tr><td>'+(r.title||'---')+'</td>'+
        '<td>'+(r.journal||'')+' &middot; '+(r.year||'')+'</td>'+
        '<td><a class="ref-link" href="'+r.url+'" target="_blank">PMID '+r.pmid+'</a></td></tr>';
    }).join('');
  }
}

function nhTab(i) {
  document.querySelectorAll('#nh-tabs .supp-tab').forEach(function(t,j){ t.classList.toggle('active', i===j); });
  document.querySelectorAll('[id^="nh-panel-"]').forEach(function(p,j){ p.classList.toggle('active', i===j); });
}

// ── SUPP TABS ─────────────────────────────────────────────────────────────────
function renderSuppTabs(tabsId, panelsId, supps) {
  if (!supps || !supps.length) return;
  document.getElementById(tabsId).innerHTML = supps.map(function(s,i) {
    return '<div class="supp-tab'+(i===0?' active':'')+'" onclick="swSupp(\''+tabsId+'\',\''+panelsId+'\','+i+')">'+(s.name||'Sup.'+(i+1))+'</div>';
  }).join('');

  document.getElementById(panelsId).innerHTML = supps.map(function(s,i) {
    var grid = '';
    if (s.benefits&&s.benefits.length)
      grid += '<div class="supp-sec"><div class="supp-sec-title">Beneficios</div>'+
        '<ul class="supp-list">'+s.benefits.slice(0,8).map(function(b){ return '<li>'+b+'</li>'; }).join('')+'</ul></div>';
    if (s.side_effects&&s.side_effects.length)
      grid += '<div class="supp-sec danger"><div class="supp-sec-title">Efectos Adversos</div>'+
        '<ul class="supp-list">'+s.side_effects.slice(0,8).map(function(e){ return '<li>'+e+'</li>'; }).join('')+'</ul></div>';
    if (s.warnings&&s.warnings.length)
      grid += '<div class="supp-sec warn"><div class="supp-sec-title">Advertencias</div>'+
        '<ul class="supp-list">'+s.warnings.slice(0,6).map(function(w){ return '<li>'+w+'</li>'; }).join('')+'</ul></div>';
    if (s.drug_interactions&&s.drug_interactions.length)
      grid += '<div class="supp-sec danger"><div class="supp-sec-title">Interacciones con Farmacos</div>'+
        '<ul class="supp-list">'+s.drug_interactions.slice(0,10).map(function(x){ return '<li>'+x+'</li>'; }).join('')+'</ul></div>';
    if (s.food_interactions&&s.food_interactions.length)
      grid += '<div class="supp-sec warn"><div class="supp-sec-title">Interacciones con Alimentos</div>'+
        '<ul class="supp-list">'+s.food_interactions.slice(0,6).map(function(x){ return '<li>'+x+'</li>'; }).join('')+'</ul></div>';

    var extra = '';
    if (s.mechanism_of_action)
      extra += '<div class="moa-box" style="margin-top:14px">'+
        '<div class="moa-title">Mecanismo de Accion</div>'+
        '<p class="supp-text">'+s.mechanism_of_action.slice(0,700)+'...</p></div>';
    if (s.contraindications)
      extra += '<div class="moa-box" style="margin-top:10px;background:rgba(224,92,92,.05);border-color:rgba(224,92,92,.15)">'+
        '<div class="moa-title" style="color:var(--red)">Contraindicaciones</div>'+
        '<p class="supp-text">'+s.contraindications.slice(0,400)+'</p></div>';
    if (s.url)
      extra += '<div style="margin-top:14px"><a class="ext-link gold" href="'+s.url+'" target="_blank">Ficha completa en MSK</a></div>';

    return '<div class="supp-panel'+(i===0?' active':'')+'" id="'+panelsId+'-'+i+'">'+
      '<div class="supp-grid">'+grid+'</div>'+extra+'</div>';
  }).join('');
}

function swSupp(tabsId, panelsId, i) {
  document.querySelectorAll('#'+tabsId+' .supp-tab').forEach(function(t,j){ t.classList.toggle('active', i===j); });
  document.querySelectorAll('#'+panelsId+' .supp-panel').forEach(function(p,j){ p.classList.toggle('active', i===j); });
}

// ── EDITOR ────────────────────────────────────────────────────────────────────
function fmt(cmd) { document.execCommand(cmd); }

function switchPanel(name) {
  document.querySelectorAll('.panel-content').forEach(function(p){
    p.classList.toggle('active', p.id === 'panel-'+name);
  });
}

function addPage() {
  var cc = document.getElementById('report-canvas-content');
  var n = cc.querySelectorAll('.a4-page').length + 1;
  var p = document.createElement('div');
  p.className = 'a4-page';
  p.innerHTML = '<div class="page-inner">'+
    '<div class="report-section">'+
      '<div class="section-heading">Contenido adicional</div>'+
      '<div class="editable-block" contenteditable="true" data-placeholder="Escribe aqui..."></div>'+
    '</div>'+
    '<div class="page-footer">'+
      '<span>NutriKen v2.0 - Cesar Manzo</span>'+
      '<span>MSK - NCBI - KEGG - PubMed</span>'+
      '<span>Pagina '+n+'</span>'+
    '</div>'+
  '</div>';
  cc.appendChild(p);
  p.scrollIntoView({behavior:'smooth'});
}

function insertBlock(type) {
  var sel = window.getSelection();
  if (!sel.rangeCount) return;
  var range = sel.getRangeAt(0);
  var el;
  if (type === 'note') {
    el = document.createElement('div');
    el.style.cssText = 'background:#fffde7;border-left:4px solid #fbc02d;padding:12px;margin:12px 0;font-style:italic';
    el.contentEditable = 'true';
    el.textContent = 'Nota clinica...';
  } else if (type === 'gene') {
    el = document.createElement('div');
    el.className = 'gene-block';
    el.innerHTML = '<div class="gene-block-name" contenteditable="true">GEN</div>'+
      '<div class="gene-block-text" contenteditable="true">Descripcion...</div>';
  }
  if (el) range.insertNode(el);
}

function exportText() {
  var blob = new Blob([document.getElementById('report-canvas-content').innerText], {type:'text/plain'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'NutriKen_'+Date.now()+'.txt';
  a.click();
}

function exportMarkdown() {
  var txt = document.getElementById('report-canvas-content').innerText;
  var blob = new Blob(['# Informe NutriKen\n\n'+txt], {type:'text/markdown'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'NutriKen_'+Date.now()+'.md';
  a.click();
}

// ── POPULATE REPORT ───────────────────────────────────────────────────────────
function populateReport(d) {
  var cc = document.getElementById('report-canvas-content');
  document.getElementById('editor-empty').style.display = 'none';
  cc.style.display = 'block';
  var now = new Date().toLocaleDateString('es-ES', {year:'numeric',month:'long',day:'numeric'});
  var id = 'NK-'+Date.now().toString().slice(-6);

  var genesHTML = (d.genes||[]).map(function(g) {
    return '<div class="gene-block">'+
      '<div class="gene-block-name">'+g.symbol+' - Chr'+(g.chromosome||'?')+'</div>'+
      '<div class="gene-block-text">'+(g.name||'')+
        (g.ensembl_id ? '<br/><span style="font-size:10px;color:#666">'+g.ensembl_id+'</span>' : '')+
        (g.summary ? '<br/>'+g.summary.slice(0,200)+'...' : '')+
      '</div>'+
    '</div>';
  }).join('');

  var suppsHTML = (d.supplements||[]).map(function(s) {
    return '<p><strong>'+s.name+'</strong>'+
      (s.scientific_name ? ' <em>('+s.scientific_name+')</em>' : '')+'</p>'+
      (s.benefits&&s.benefits.length ? '<p style="font-size:11px;color:#555">Beneficios: '+s.benefits.slice(0,3).join('; ')+'</p>' : '');
  }).join('<hr style="border:none;border-top:1px solid #ddd;margin:8px 0"/>');

  var drugsHTML = (d.drug_alerts||[]).map(function(a) {
    return '<li><strong>'+a.drug+'</strong> + '+a.herb+': '+a.alert.slice(0,150)+'</li>';
  }).join('');

  var foodHTML = (d.food_alerts||[]).map(function(a) {
    return '<li><strong>'+a.food+'</strong>: '+a.description+'</li>';
  }).join('');

  var refsHTML = '<ol style="padding-left:18px;font-size:11px;line-height:1.8">'+
    (d.references||[]).map(function(r) {
      return '<li>'+(r.authors||'')+' ('+(r.year||'')+') '+
        (r.title||'')+'. <em>'+(r.journal||'')+'</em>. PMID: '+r.pmid+'</li>';
    }).join('')+'</ol>';

  cc.innerHTML =
    '<div class="a4-page" id="page-1"><div class="page-inner">'+
      '<div class="report-header">'+
        '<div>'+
          '<div class="report-title">NutriKen</div>'+
          '<div class="report-subtitle">Informe Bioinformatico Nutricional</div>'+
        '</div>'+
        '<div class="report-meta">'+
          '<div class="meta-id">'+id+'</div>'+
          '<div>'+now+'</div>'+
          '<div>Cesar Manzo</div>'+
        '</div>'+
      '</div>'+
      '<div class="report-section"><div class="section-heading">Consulta</div>'+
        '<div class="editable-block" contenteditable="true">'+(d.query||'')+'</div></div>'+
      '<div class="report-section"><div class="section-heading">Descripcion Clinica</div>'+
        '<div class="editable-block" contenteditable="true">'+(d.description||'')+'</div></div>'+
      '<div class="report-section"><div class="section-heading">Genes Involucrados</div>'+
        '<div contenteditable="true">'+(genesHTML||'<p style="color:#aaa;font-style:italic">---</p>')+'</div></div>'+
      (drugsHTML ? '<div class="report-section"><div class="section-heading">Interacciones con Farmacos</div>'+
        '<ul contenteditable="true" style="padding-left:18px;font-size:11px">'+drugsHTML+'</ul></div>' : '')+
      (foodHTML ? '<div class="report-section"><div class="section-heading">Interacciones con Alimentos</div>'+
        '<ul contenteditable="true" style="padding-left:18px;font-size:11px">'+foodHTML+'</ul></div>' : '')+
      '<div class="report-section"><div class="section-heading">Suplementos con Evidencia MSK</div>'+
        '<div contenteditable="true">'+(suppsHTML||'<p style="color:#aaa;font-style:italic">---</p>')+'</div></div>'+
      '<div class="report-section"><div class="section-heading">Referencias Cientificas PubMed</div>'+
        '<div contenteditable="true">'+refsHTML+'</div></div>'+
      '<div class="report-section"><div class="section-heading">Recomendacion Nutricional</div>'+
        '<div class="editable-block" contenteditable="true" data-placeholder="Escribe aqui la recomendacion nutricional personalizada basada en los datos..."></div></div>'+
      '<button class="add-section-btn" onclick="addPage()">+ Agregar pagina</button>'+
      '<div class="page-footer">'+
        '<span>NutriKen v2.0 - Cesar Manzo</span>'+
        '<span>MSK - NCBI - KEGG - PubMed</span>'+
        '<span>Pagina 1</span>'+
      '</div>'+
    '</div></div>';
}

// ── STATS ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    var r = await fetch('/api/stats');
    if (!r.ok) return;
    var s = await r.json();
    document.getElementById('stats-line').textContent =
      'Hierbas: '+s.herbs_in_cache+' - Genes: '+s.genes_in_cache+' - Consultas: '+s.total_queries;
  } catch(e) {}
}

function show(id) {
  var e = document.getElementById(id);
  if (e) e.style.display = '';
}

// ── KEYBOARD ──────────────────────────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    var a = document.activeElement;
    if (a && a.id === 'clinical-input')  { e.preventDefault(); runClinical(); }
    if (a && a.id === 'gene-input')      { e.preventDefault(); runGene(); }
    if (a && a.id === 'nutrient-input')  { e.preventDefault(); runNutrient(); }
  }
  if (e.key === 'Escape') closeGenePanel();
});

window.addEventListener('load', function() {
  loadStats();
  setInterval(loadStats, 30000);
});

