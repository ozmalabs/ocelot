// ui.js — DOM panels: roster, resident inspector (the glass-box payoff), the
// Bigville Times, the council board, and the chronicle log. Pure renderers over the
// unified model — no sim logic.
import { residentTint } from './assets.js';

const el = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
};

const FEEL_LABEL = { warm: 'warm toward', hostile: 'hostile toward', neutral: 'neutral toward' };

// ---- resident portrait: tinted idle sprite scaled up -------------------------------
export function portraitCanvas(assets, resident, size = 72) {
  const c = document.createElement('canvas');
  c.width = size; c.height = size; c.className = 'portrait';
  const g = c.getContext('2d');
  g.imageSmoothingEnabled = false;
  g.fillStyle = 'rgba(0,0,0,0)';
  const sheet = assets.tintedChars(residentTint(resident));
  const T = assets.C;
  const rect = assets.charFrameRect('down', 0);
  g.drawImage(sheet, rect.sx, rect.sy, T, T, 0, 0, size, size);
  return c;
}

// ---- roster ------------------------------------------------------------------------
export function renderRoster(container, model, selectedId, onSelect) {
  container.innerHTML = '';
  for (const r of model.residents) {
    const row = el('button', 'roster-row' + (r.id === selectedId ? ' sel' : ''));
    row.style.setProperty('--tint', residentTint(r));
    const dot = el('span', 'roster-dot');
    const nm = el('span', 'roster-name', r.face + ' ' + r.name);
    const role = el('span', 'roster-role', r.role + (r.alive === false ? ' ·dead' : ''));
    row.append(dot, nm, role);
    row.onclick = () => onSelect(r.id);
    container.append(row);
  }
}

// ---- inspector ---------------------------------------------------------------------
export function renderInspector(container, model, id, assets) {
  container.innerHTML = '';
  const r = model.residents.find((x) => x.id === id);
  if (!r) { container.append(el('div', 'muted', 'Click a resident to read their mind.')); return; }
  const byId = Object.fromEntries(model.residents.map((x) => [x.id, x]));
  const nameOf = (rid) => (byId[rid] ? byId[rid].name : rid);

  const head = el('div', 'insp-head');
  head.append(portraitCanvas(assets, r, 72));
  const ttl = el('div', 'insp-title');
  ttl.append(el('div', 'insp-name', r.name));
  ttl.append(el('div', 'insp-role', r.role + ' · ' + r.cls));
  head.append(ttl);
  container.append(head);

  // vitals
  const vit = el('div', 'insp-vitals');
  vit.append(stat('health', r.health, '#c0453b'));
  if (r.coin != null) vit.append(stat('coin', r.coin, '#cf9a3a'));
  if (r.landPlots != null) vit.append(stat('plots', r.landPlots, '#4f8355'));
  container.append(vit);

  // held state (deep_held — real graph read)
  if (r.held) {
    container.append(el('h4', null, 'Held state'));
    const h = el('div', 'insp-held');
    for (const part of r.held.split(';').map((s) => s.trim()).filter(Boolean)) {
      h.append(el('span', 'chip', part));
    }
    container.append(h);
  }
  // journal (self-narration)
  if (r.journal) {
    container.append(el('h4', null, 'Journal'));
    container.append(el('div', 'insp-journal', '“' + r.journal + '”'));
  }
  // bonds
  if (r.rels.length) {
    container.append(el('h4', null, 'Bonds'));
    const list = el('div', 'insp-bonds');
    for (const b of r.rels) {
      const row = el('div', 'bond ' + b.feeling);
      row.append(el('span', 'bond-feel', FEEL_LABEL[b.feeling] || b.feeling));
      row.append(el('span', 'bond-who', nameOf(b.who)));
      const meta = [];
      if (b.affection != null) meta.push('affection ' + b.affection);
      if (b.resentment != null && b.resentment) meta.push('resentment ' + b.resentment);
      if (b.ties && b.ties.length) meta.push(b.ties.join(', '));
      if (meta.length) row.append(el('span', 'bond-meta', meta.join(' · ')));
      list.append(row);
    }
    container.append(list);
  }
  // predictions (who they expect to meet)
  if (r.predicts && r.predicts.length) {
    container.append(el('h4', null, 'Predicts meeting'));
    const p = el('div', 'insp-held');
    for (const w of r.predicts) p.append(el('span', 'chip', nameOf(w)));
    container.append(p);
  }
}

function stat(label, val, col) {
  const s = el('div', 'stat');
  const v = el('div', 'stat-val', val);
  v.style.color = col;
  s.append(v, el('div', 'stat-label', label));
  return s;
}

// ---- the Bigville Times ------------------------------------------------------------
export function renderPaper(container, model) {
  container.innerHTML = '';
  container.append(el('div', 'paper-masthead', 'The Bigville Times'));
  const items = model.paper || [];
  if (!items.length) {
    container.append(el('div', 'muted', 'No editions printed yet. The press reports as stories break.'));
    return;
  }
  for (const p of items.slice(-12).reverse()) {
    const art = el('article', 'paper-item');
    const head = p.headline || p.title || p.kind || 'Notice';
    art.append(el('div', 'paper-head', head));
    const body = p.text || p.body || p.summary ||
      (p.printed === false ? 'Suppressed by the press.' : '');
    if (body) art.append(el('div', 'paper-body', body));
    const tag = [];
    if (p.tick != null) tag.push('tick ' + p.tick);
    if (p.printed === false) tag.push('suppressed');
    if (tag.length) art.append(el('div', 'paper-tag', tag.join(' · ')));
    container.append(art);
  }
}

// ---- council board -----------------------------------------------------------------
export function renderCouncil(container, model) {
  container.innerHTML = '';
  const ca = model.collective_action;
  if (ca) {
    const box = el('div', 'council-metric');
    const printed = (ca.printings || []);
    const share = printed.length ? printed[printed.length - 1].share : 0;
    const thr = ca.chenoweth_threshold != null ? ca.chenoweth_threshold : 0.035;
    box.append(el('div', 'cm-label', 'Informed share vs the 3.5% threshold'));
    const bar = el('div', 'cm-bar');
    const fill = el('div', 'cm-fill');
    fill.style.width = Math.min(100, (share / Math.max(thr * 2, 0.07)) * 100) + '%';
    if (share >= thr) fill.classList.add('over');
    const mark = el('div', 'cm-mark');
    mark.style.left = ((thr / Math.max(thr * 2, 0.07)) * 100) + '%';
    bar.append(fill, mark);
    box.append(bar);
    box.append(el('div', 'cm-note',
      (share * 100).toFixed(1) + '% informed · threshold ' + (thr * 100).toFixed(1) +
      '% · coalitions formed: ' + (ca.coalitions_formed || 0)));
    container.append(box);
  }
  const inst = model.institutions || {};
  if (Object.keys(inst).length) {
    const grid = el('div', 'inst-grid');
    for (const [k, v] of Object.entries(inst)) {
      const card = el('div', 'inst-card');
      card.append(el('div', 'inst-name', k));
      card.append(el('div', 'inst-body', typeof v === 'object'
        ? Object.entries(v).map(([a, b]) => a + ': ' + b).join(' · ') : String(v)));
      grid.append(card);
    }
    container.append(grid);
  }
  const board = model.council_board || [];
  if (board.length) {
    container.append(el('h4', null, 'Posted decisions'));
    for (const c of board.slice(-10).reverse()) {
      const row = el('div', 'council-row');
      row.append(el('div', 'council-title', c.title || c.headline || c.kind || 'Decision'));
      const body = c.text || c.body || c.recorded || '';
      if (body) row.append(el('div', 'council-body', String(body)));
      container.append(row);
    }
  }
  if (!ca && !Object.keys(inst).length && !board.length) {
    container.append(el('div', 'muted', 'The council has posted nothing yet.'));
  }
}

// ---- chronicle ---------------------------------------------------------------------
export function chronicleLine(frame, ev) {
  const cls = { help: 'help', harm: 'harm', give: 'give', transfer: 'give' }[ev.act] || 'neutral';
  const row = el('div', 'chron-row ' + cls);
  row.append(el('span', 'chron-t', 't' + frame.t));
  const isSpeech = ev.speech || ['drama', 'council', 'paper', 'loud', 'say'].includes(ev.kind);
  row.append(el('span', 'chron-tag', isSpeech ? 'said' : (ev.act || ev.kind || 'act')));
  row.append(el('span', 'chron-text', ev.text || (ev.actor + ' ' + (ev.act || '') + ' ' + (ev.target || ''))));
  return row;
}
