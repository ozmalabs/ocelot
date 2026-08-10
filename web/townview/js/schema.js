// schema.js — normalise every producer (simple replay / rich play_doc / live) into
// ONE unified document. See DATA_CONTRACT.md. No data is invented; simple docs get a
// SYNTHESISED tilemap so both modes render as a town.

export const ACT_COLOR = {
  help: 'help', give: 'give', transfer: 'give', gift: 'give',
  harm: 'harm', violence: 'harm', kindness: 'help',
};
export const SPEECH_KINDS = new Set(['drama', 'council', 'paper', 'loud']);

export function actClass(act, kind) {
  return ACT_COLOR[act] || ACT_COLOR[kind] || 'neutral';
}

// --- relationship merge: simple {who,feeling,affection,resentment} + rich {to,kind} --
function mergeRels(res) {
  const by = new Map();
  const put = (who) => {
    if (!by.has(who)) by.set(who, { who, feeling: 'neutral', ties: [] });
    return by.get(who);
  };
  for (const r of (res.rels || [])) {
    const e = put(r.who);
    e.feeling = r.feeling || e.feeling;
    if (r.affection != null) e.affection = r.affection;
    if (r.resentment != null) e.resentment = r.resentment;
  }
  for (const r of (res.rel || [])) {           // rich _rel: {to, kind: hates|kin|owes}
    const who = r.to;
    const e = put(who);
    if (r.kind === 'hates') e.feeling = 'hostile';
    if (r.kind) e.ties.push(r.kind);
  }
  return [...by.values()];
}

function normResident(r) {
  const id = r.id != null ? r.id : r.name;
  return {
    id,
    name: r.name != null ? r.name : id,
    face: r.face || '🧑',
    role: r.role || 'villager',
    cls: r.cls || 'middle',
    home: r.home || (r.x != null ? [r.x, r.y] : [0, 0]),
    health: r.health != null ? r.health : 100,
    coin: r.coin != null ? r.coin : null,
    held: r.held != null ? r.held : null,
    journal: r.journal != null ? r.journal : null,
    alive: r.alive != null ? r.alive : true,
    landPlots: r.land_plots != null ? r.land_plots : null,
    predicts: r.predicts || [],
    rels: mergeRels(r),
  };
}

// --- frame events: simple `events` OR rich `says`+`acts` -> one unified list ---------
export function normFrame(fr) {
  const events = [];
  if (Array.isArray(fr.events)) {
    for (const e of fr.events) {
      events.push({
        actor: e.actor != null ? e.actor : e.id,
        act: e.act || e.kind || '',
        target: e.target != null ? e.target : null,
        text: e.text || '',
        kind: e.kind || '',
        at: e.at || null,
      });
    }
  }
  for (const key of ['says', 'acts']) {          // rich play_doc frames
    for (const e of (fr[key] || [])) {
      events.push({
        actor: e.id != null ? e.id : e.actor,
        act: e.act || e.kind || (key === 'says' ? 'say' : ''),
        target: e.target != null ? e.target : null,
        text: e.text || '',
        kind: e.kind || '',
        at: e.at || null,
        speech: key === 'says' || SPEECH_KINDS.has(e.kind),
      });
    }
  }
  return { t: fr.t, day: fr.day != null ? fr.day : Math.floor((fr.t || 0) / 36),
    pos: fr.pos || {}, events };
}

// --- synthesise a tilemap for a SIMPLE doc that has no map.tiles ----------------------
function synthMap(grid, square, residents) {
  const [w, h] = grid;
  const tiles = [];
  for (let y = 0; y < h; y++) {
    const row = [];
    for (let x = 0; x < w; x++) row.push('grass');
    tiles.push(row);
  }
  // a plaza around the square + a cross of paths through it
  const [sx, sy] = square;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (Math.abs(x - sx) <= 2 && Math.abs(y - sy) <= 2) tiles[y][x] = 'square';
  }
  for (let x = 0; x < w; x++) if (tiles[sy] && tiles[sy][x] === 'grass') tiles[sy][x] = 'path';
  for (let y = 0; y < h; y++) if (tiles[y][sx] === 'grass') tiles[y][sx] = 'path';
  // scatter a few trees deterministically at the edges
  let seed = w * 131 + h * 17;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  for (let i = 0; i < Math.max(6, (w * h) / 30); i++) {
    const x = Math.floor(rnd() * w), y = Math.floor(rnd() * h);
    if (tiles[y][x] === 'grass' && (Math.abs(x - sx) > 3 || Math.abs(y - sy) > 3)) tiles[y][x] = 'tree';
  }
  // buildings: townhall at the square, houses at resident homes
  const buildings = [{ id: 'townhall', type: 'townhall', x: sx, y: sy, w: 3, h: 3, name: 'Town Square' }];
  for (const r of residents) {
    const [hx, hy] = r.home || [0, 0];
    buildings.push({ id: 'home_' + r.id, type: 'house', x: hx, y: hy, w: 2, h: 2, name: r.name });
  }
  return { w, h, tiles, buildings, features: [] };
}

export function normalizeDoc(raw, title) {
  const rich = raw.map && raw.map.tiles;
  const residents = (raw.residents || []).map(normResident);
  const grid = raw.grid || (rich ? [raw.map.w, raw.map.h] : [20, 12]);
  let square = raw.square;
  if (!square && rich) {
    const th = (raw.map.buildings || []).find((b) => b.id === 'townhall' || b.type === 'townhall');
    square = th ? [th.x, th.y] : [Math.floor(grid[0] / 2), Math.floor(grid[1] / 2)];
  }
  square = square || [Math.floor(grid[0] / 2), Math.floor(grid[1] / 2)];
  const map = rich ? raw.map : synthMap(grid, square, residents);
  return {
    schema: 'townview/1',
    title: title || raw.title || 'town',
    grid, square, map,
    shops: raw.shops || {},
    residents,
    paper: raw.paper || [],
    council_board: raw.council_board || [],
    collective_action: raw.collective_action || null,
    institutions: raw.institutions || {},
    frames: (raw.frames || []).map(normFrame),
    ticks: raw.ticks != null ? raw.ticks : (raw.frames || []).length,
    days: raw.days != null ? raw.days : Math.floor(((raw.frames || []).length) / 36),
  };
}

// facing direction from movement delta (for sprite orientation)
export function facing(dx, dy, prev) {
  if (dx === 0 && dy === 0) return prev || 'down';
  if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}
