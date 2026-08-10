// app.js — TownView bootstrap. Wires assets + renderer + player + panels + the two
// modes (replay / live). All UI glue; no sim logic.
import { Assets } from './assets.js';
import { Renderer } from './renderer.js';
import { Player } from './player.js';
import { LiveStream } from './live.js';
import { normalizeDoc, normFrame } from './schema.js';
import * as ui from './ui.js';

const $ = (id) => document.getElementById(id);

const state = {
  assets: null, renderer: null, player: null, model: null,
  mode: 'replay', selected: null, live: null,
};

// ---- panels -----------------------------------------------------------------------
function renderStaticPanels() {
  const m = state.model;
  ui.renderRoster($('roster'), m, state.selected, select);
  ui.renderInspector($('inspector'), m, state.selected, state.assets);
  ui.renderPaper($('paper'), m);
  ui.renderCouncil($('council'), m);
}

function select(id) {
  state.selected = id;
  state.renderer.selected = id;
  ui.renderRoster($('roster'), state.model, id, select);
  ui.renderInspector($('inspector'), state.model, id, state.assets);
}

function rebuildChronicle() {
  const c = $('chronicle');
  c.innerHTML = '';
}

function pushChronicle(frame) {
  const c = $('chronicle');
  for (const ev of frame.events) c.prepend(ui.chronicleLine(frame, ev));
  while (c.children.length > 200) c.removeChild(c.lastChild);
}

// ---- HUD --------------------------------------------------------------------------
function updateHUD(p) {
  const n = p.count;
  const fi = Math.floor(p.fi);
  const fr = p.frames[fi];
  const t = fr ? fr.t : 0;
  const day = fr ? (fr.day != null ? fr.day : Math.floor(t / 36)) : 0;
  const hour = ((t % 36) / 36 * 24) | 0;
  $('hud-day').textContent = 'Day ' + day;
  $('hud-time').textContent = String(hour).padStart(2, '0') + ':00';
  $('hud-tick').textContent = 'tick ' + t + ' / ' + (state.mode === 'live' ? '∞' : (state.model ? state.model.ticks : n));
  const sc = $('scrub');
  sc.max = Math.max(0, n - 1);
  if (document.activeElement !== sc) sc.value = fi;
  $('btn-play').textContent = p.playing ? '⏸' : '▶';
  $('btn-speed').textContent = p.speed + '×';
}

// ---- load a normalised model into the stage ---------------------------------------
function loadModel(model, { live = false } = {}) {
  state.model = model;
  state.renderer.setModel(model);
  state.player.live = live;
  state.player.follow = live;
  state.player._lastInt = -1;
  state.player.fi = 0;
  state.selected = model.residents[0] ? model.residents[0].id : null;
  state.renderer.selected = state.selected;
  rebuildChronicle();
  renderStaticPanels();
  if (!live) { state.player.seek(0); state.player.play(); }
}

// ---- REPLAY -----------------------------------------------------------------------
async function refreshRuns() {
  try {
    const { runs } = await (await fetch('api/runs')).json();
    const sel = $('run-select');
    sel.innerHTML = '';
    for (const r of runs) {
      const o = document.createElement('option');
      o.value = r.name;
      o.textContent = r.label + '  (' + (r.size / 1024).toFixed(1) + ' KB)';
      sel.append(o);
    }
    return runs;
  } catch (e) {
    setStatus('idle', 'backend offline — use the file picker');
    return [];
  }
}

async function loadRun(name) {
  setStatus('idle', 'loading ' + name + '…');
  const raw = await (await fetch('api/replay/' + name)).json();
  loadModel(normalizeDoc(raw, name), { live: false });
  setStatus('idle', 'replay: ' + name);
}

function loadFromFile(file) {
  const fr = new FileReader();
  fr.onload = () => {
    try { loadModel(normalizeDoc(JSON.parse(fr.result), file.name), { live: false });
      setStatus('idle', 'replay: ' + file.name); }
    catch (e) { setStatus('idle', 'bad file: ' + e.message); }
  };
  fr.readAsText(file);
}

// ---- LIVE -------------------------------------------------------------------------
function startLive() {
  stopLive();
  const cast = parseInt($('live-cast').value, 10) || 8;
  const skeleton = normalizeDoc({
    grid: [20, 12], square: [10, 6],
    map: { w: 20, h: 12, tiles: null }, residents: [], frames: [], ticks: 0,
  }, 'live');
  // placeholder until meta arrives
  state.live = new LiveStream({
    onMeta: (msg) => {
      const model = normalizeDoc({
        grid: msg.grid, square: msg.square, map: msg.map,
        residents: msg.residents, institutions: msg.institutions,
        shops: msg.shops, frames: [], ticks: 0,
      }, 'live');
      loadModel(model, { live: true });
      state.player.play();
      setStatus('live', 'streaming · cast ' + msg.cast + ' · seed ' + msg.seed);
    },
    onFrame: (msg) => {
      if (!state.model) return;
      state.model.frames.push(normFrame(msg));
      state.model.ticks = msg.t;
      state.player.onLiveAppend();
    },
    onPaper: (msg) => {
      if (!state.model) return;
      Object.assign(state.model, {
        paper: msg.paper || state.model.paper,
        council_board: msg.council_board || state.model.council_board,
        collective_action: msg.collective_action || state.model.collective_action,
        institutions: msg.institutions || state.model.institutions,
      });
      ui.renderPaper($('paper'), state.model);
      ui.renderCouncil($('council'), state.model);
    },
    onStatus: (s) => setStatus(s, {
      connecting: 'connecting to the town…', live: 'live', reconnecting: 'reconnecting…',
      ended: 'stream ended', idle: 'idle',
    }[s] || s),
    onEnd: () => {},
  });
  state.live.connect({ cast, seed: 276000, ticks: 400 });
}

function stopLive() {
  if (state.live) { state.live.close(); state.live = null; }
}

function setStatus(kind, text) {
  const dot = $('status-dot');
  dot.className = 'status-dot ' + kind;
  $('status-text').textContent = text;
}

function setMode(mode) {
  state.mode = mode;
  $('mode-replay').classList.toggle('active', mode === 'replay');
  $('mode-live').classList.toggle('active', mode === 'live');
  $('replay-controls').style.display = mode === 'replay' ? '' : 'none';
  $('live-controls').style.display = mode === 'live' ? '' : 'none';
  if (mode === 'replay') { stopLive(); }
  else { startLive(); }
}

// ---- wiring -----------------------------------------------------------------------
function wireControls() {
  $('btn-play').onclick = () => state.player.toggle();
  $('btn-speed').onclick = () => state.player.cycleSpeed();
  $('btn-restart').onclick = () => { state.player.seek(0); state.player.play(); };
  $('scrub').oninput = (e) => { state.player.pause(); state.player.seek(parseInt(e.target.value, 10)); };
  $('mode-replay').onclick = () => setMode('replay');
  $('mode-live').onclick = () => setMode('live');
  $('run-select').onchange = (e) => loadRun(e.target.value);
  $('btn-load-run').onclick = () => { const s = $('run-select'); if (s.value) loadRun(s.value); };
  $('file-input').onchange = (e) => { if (e.target.files[0]) loadFromFile(e.target.files[0]); };
  $('btn-relive').onclick = () => startLive();

  const canvas = $('stage');
  canvas.onclick = (e) => {
    const rect = canvas.getBoundingClientRect();
    const cx = (e.clientX - rect.left) / rect.width * canvas.width;
    const cy = (e.clientY - rect.top) / rect.height * canvas.height;
    const id = state.renderer.pickResident(cx, cy, Math.floor(state.player.fi), state.player.fi % 1);
    if (id) select(id);
  };

  // theme toggle
  $('btn-theme').onclick = () => {
    const root = document.documentElement;
    const cur = root.getAttribute('data-theme')
      || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    root.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
  };
}

// ---- boot -------------------------------------------------------------------------
async function boot() {
  state.assets = await new Assets().load();
  state.renderer = new Renderer($('stage'), state.assets);
  state.player = new Player(state.renderer);
  state.player.onFrameEnter = (idx, frame) => pushChronicle(frame);
  state.player.onTick = updateHUD;
  state.player.start();
  wireControls();

  const runs = await refreshRuns();
  const preferred = runs.find((r) => r.name.includes('living_town_play'))
    || runs.find((r) => r.name.includes('richplay')) || runs[0];
  if (preferred) {
    $('run-select').value = preferred.name;
    await loadRun(preferred.name);
  } else {
    setStatus('idle', 'no runs found — start the backend or use the file picker');
  }
}

boot().catch((e) => { console.error(e); setStatus('idle', 'boot error: ' + e.message); });
