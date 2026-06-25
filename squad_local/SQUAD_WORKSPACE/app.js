// ── STATE ──────────────────────────────────────────────
const state = {
  personal: {},
  experiencias: [],
  educacion: [],
  habilidades: []
};

// ── UTILS ──────────────────────────────────────────────
function toast(msg, type = 'ok') {
  const el = document.createElement('div');
  el.className = 'toast' + (type === 'error' ? ' error' : '');
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function val(id) { return (document.getElementById(id) || {}).value || ''; }
function clear(...ids) { ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; }); }

// ── NAVIGATION ─────────────────────────────────────────
document.querySelectorAll('.sidebar-nav a[data-section]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const sec = link.dataset.section;
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    link.classList.add('active');
    const target = document.getElementById('section-' + sec);
    if (target) target.classList.add('active');
  });
});

// ── PERSONAL ───────────────────────────────────────────
document.getElementById('form-personal').addEventListener('submit', async e => {
  e.preventDefault();
  state.personal = {
    nombre: val('nombre'), apellido: val('apellido'),
    email: val('email'), telefono: val('telefono'),
    direccion: val('direccion'), fecha_nacimiento: val('fecha_nacimiento'),
    ciudad: val('ciudad'), nacionalidad: val('nacionalidad')
  };
  updatePreview();
  // Persist to backend
  try {
    const res = await fetch('/api/candidatos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre: state.personal.nombre,
        apellido: state.personal.apellido,
        email: state.personal.email,
        telefono: state.personal.telefono,
        direccion: state.personal.direccion,
        fecha_nacimiento: state.personal.fecha_nacimiento,
        ciudad_residencia: state.personal.ciudad,
        nacionalidad: state.personal.nacionalidad
      })
    });
    const data = await res.json();
    if (data.id) { state.candidatoId = data.id; toast('✅ Datos guardados correctamente'); }
    else toast('⚠️ Error al guardar: ' + (data.error || 'desconocido'), 'error');
  } catch (err) {
    toast('⚠️ Backend no disponible, datos guardados localmente', 'error');
  }
});

// ── EXPERIENCIA ────────────────────────────────────────
document.getElementById('form-experiencia').addEventListener('submit', async e => {
  e.preventDefault();
  const item = {
    puesto: val('exp-puesto'), empresa: val('exp-empresa'),
    lugar: val('exp-lugar'), inicio: val('exp-inicio'),
    fin: val('exp-fin'), desc: val('exp-desc')
  };
  state.experiencias.push(item);
  renderExperiencias();
  updatePreview();
  if (state.candidatoId) {
    try {
      await fetch('/api/experiencia-laboral', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidato_id: state.candidatoId,
          titulo_puesto: item.puesto, empresa: item.empresa,
          lugar_trabajo: item.lugar, fecha_inicio: item.inicio,
          fecha_fin: item.fin, descripcion_responsabilidades: item.desc
        })
      });
    } catch (_) {}
  }
  clear('exp-puesto', 'exp-empresa', 'exp-lugar', 'exp-inicio', 'exp-fin', 'exp-desc');
  toast('✅ Experiencia agregada');
});

function renderExperiencias() {
  const el = document.getElementById('lista-experiencia');
  el.innerHTML = state.experiencias.map((x, i) => `
    <div class="item-card">
      <div class="item-info">
        <div class="item-title">💼 ${x.puesto} — ${x.empresa}</div>
        <div class="item-sub">${x.lugar} · ${x.inicio}${x.fin ? ' → ' + x.fin : ' (actual)'}</div>
        ${x.desc ? `<div class="item-sub" style="margin-top:4px;">${x.desc.substring(0,80)}${x.desc.length>80?'…':''}</div>` : ''}
      </div>
      <div class="item-actions">
        <button class="btn btn-danger btn-sm" onclick="removeExp(${i})">✕</button>
      </div>
    </div>`).join('');
}

window.removeExp = function(i) {
  state.experiencias.splice(i, 1);
  renderExperiencias();
  updatePreview();
};

// ── EDUCACIÓN ──────────────────────────────────────────
document.getElementById('form-educacion').addEventListener('submit', async e => {
  e.preventDefault();
  const item = { institucion: val('edu-institucion'), titulo: val('edu-titulo'), anio: val('edu-anio') };
  state.educacion.push(item);
  renderEducacion();
  updatePreview();
  if (state.candidatoId) {
    try {
      await fetch('/api/educacion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidato_id: state.candidatoId, nombre_institucion: item.institucion, titulo_obtenido: item.titulo, anio_graduacion: item.anio })
      });
    } catch (_) {}
  }
  clear('edu-institucion', 'edu-titulo', 'edu-anio');
  toast('✅ Educación agregada');
});

function renderEducacion() {
  const el = document.getElementById('lista-educacion');
  el.innerHTML = state.educacion.map((x, i) => `
    <div class="item-card">
      <div class="item-info">
        <div class="item-title">🎓 ${x.titulo}</div>
        <div class="item-sub">${x.institucion}${x.anio ? ' · ' + x.anio : ''}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-danger btn-sm" onclick="removeEdu(${i})">✕</button>
      </div>
    </div>`).join('');
}

window.removeEdu = function(i) {
  state.educacion.splice(i, 1);
  renderEducacion();
  updatePreview();
};

// ── HABILIDADES ────────────────────────────────────────
document.getElementById('btn-agregar-hab').addEventListener('click', () => {
  const val2 = document.getElementById('input-habilidad').value.trim();
  if (!val2) return;
  if (state.habilidades.includes(val2)) { toast('Ya agregada', 'error'); return; }
  state.habilidades.push(val2);
  renderHabilidades();
  updatePreview();
  document.getElementById('input-habilidad').value = '';
  if (state.candidatoId) {
    fetch('/api/habilidades-certificaciones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidato_id: state.candidatoId, habilidad_certificacion: val2 })
    }).catch(() => {});
  }
});

document.getElementById('input-habilidad').addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); document.getElementById('btn-agregar-hab').click(); }
});

function renderHabilidades() {
  const el = document.getElementById('lista-habilidades');
  el.innerHTML = state.habilidades.map((h, i) => `
    <span class="tag">${h} <span class="tag-remove" onclick="removeHab(${i})">×</span></span>`).join('');
}

window.removeHab = function(i) {
  state.habilidades.splice(i, 1);
  renderHabilidades();
  updatePreview();
};

// ── LIVE PREVIEW ───────────────────────────────────────
function updatePreview() {
  const p = state.personal;
  document.getElementById('cv-nombre-preview').textContent =
    `${p.nombre || 'Tu Nombre'} ${p.apellido || ''}`.trim();
  document.getElementById('cv-contact-preview').textContent =
    [p.email, p.telefono, p.ciudad].filter(Boolean).join(' · ');

  // Experiencia
  const expEl = document.getElementById('cv-exp-preview');
  if (state.experiencias.length) {
    expEl.innerHTML = `<div class="cv-section-title">Experiencia Laboral</div>` +
      state.experiencias.map(x => `
        <div class="cv-entry">
          <div class="cv-entry-title">${x.puesto}</div>
          <div class="cv-entry-sub">${x.empresa}${x.lugar ? ' · ' + x.lugar : ''} · ${x.inicio}${x.fin ? ' – ' + x.fin : ' – Actual'}</div>
          ${x.desc ? `<div class="cv-entry-desc">${x.desc}</div>` : ''}
        </div>`).join('') + '<hr class="cv-divider">';
  } else { expEl.innerHTML = ''; }

  // Educación
  const eduEl = document.getElementById('cv-edu-preview');
  if (state.educacion.length) {
    eduEl.innerHTML = `<div class="cv-section-title">Educación</div>` +
      state.educacion.map(x => `
        <div class="cv-entry">
          <div class="cv-entry-title">${x.titulo}</div>
          <div class="cv-entry-sub">${x.institucion}${x.anio ? ' · ' + x.anio : ''}</div>
        </div>`).join('') + '<hr class="cv-divider">';
  } else { eduEl.innerHTML = ''; }

  // Habilidades
  const habEl = document.getElementById('cv-hab-preview');
  if (state.habilidades.length) {
    habEl.innerHTML = `<div class="cv-section-title">Habilidades</div>` +
      state.habilidades.map(h => `<span class="cv-skill-chip">${h}</span>`).join('');
  } else { habEl.innerHTML = ''; }
}

// ── PRINT ──────────────────────────────────────────────
document.getElementById('btn-print').addEventListener('click', () => {
  const cvHtml = document.getElementById('cv-preview').innerHTML;
  const win = window.open('', '_blank');
  win.document.write(`<!DOCTYPE html><html><head>
    <meta charset="UTF-8">
    <title>CV - ${state.personal.nombre || ''} ${state.personal.apellido || ''}</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
      body { background:#fff; color:#1a1a2e; padding:32px; font-family:'Inter',sans-serif; }
      @media print { body { padding:0; } }
    </style>
  </head><body>${cvHtml}</body></html>`);
  win.document.close();
  win.focus();
  setTimeout(() => win.print(), 500);
});
