// renderer.js — canvas tilemap + animated pixel-art residents (hop-by-hop
// interpolation, direction facing, idle bob) + speech bubbles + action popups.
import { residentTint } from './assets.js';
import { facing, actClass } from './schema.js';

const MAXW = 980;            // target backing-store width budget

export class Renderer {
  constructor(canvas, assets) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.assets = assets;
    this.model = null;
    this.tile = 24;
    this.popups = [];        // {x,y,text,cls,born}
    this.bubbles = [];       // {x,y,text,born}
    this._facing = {};       // id -> last direction
    this._tintFor = {};      // id -> css color
    this.selected = null;
  }

  setModel(model) {
    this.model = model;
    const [w, h] = model.grid;
    this.tile = Math.max(14, Math.min(40, Math.floor(MAXW / w)));
    this.canvas.width = w * this.tile;
    this.canvas.height = h * this.tile;
    this._tintFor = {};
    for (const r of model.residents) this._tintFor[r.id] = residentTint(r);
    this.ctx.imageSmoothingEnabled = false;
  }

  // spawn popups/bubbles for the events of a freshly-entered frame
  emitFrameEvents(frame, now) {
    const posOf = (id) => frame.pos[id];
    for (const e of frame.events) {
      let cell = e.at;
      if (!cell && e.actor && posOf(e.actor)) cell = posOf(e.actor);
      if (!cell) cell = this.model.square;
      const [cx, cy] = this._cellCenter(cell[0], cell[1]);
      if (e.speech || ['drama', 'council', 'paper', 'loud', 'say'].includes(e.kind) || e.act === 'say') {
        this.bubbles.push({ x: cx, y: cy - this.tile * 0.7, text: e.text, born: now });
      } else {
        this.popups.push({ x: cx, y: cy - this.tile * 0.4, text: this._popText(e),
          cls: actClass(e.act, e.kind), born: now });
      }
    }
    // cap
    if (this.popups.length > 40) this.popups.splice(0, this.popups.length - 40);
    if (this.bubbles.length > 14) this.bubbles.splice(0, this.bubbles.length - 14);
  }

  _popText(e) {
    const verb = { help: 'helps', harm: 'strikes', transfer: 'shares', give: 'gives', gift: 'gives' }[e.act] || e.act;
    return e.text || (e.actor + ' ' + verb + (e.target ? ' ' + e.target : ''));
  }

  clearEphemeral() { this.popups = []; this.bubbles = []; }

  _cellCenter(x, y) { return [(x + 0.5) * this.tile, (y + 0.5) * this.tile]; }

  // ------------------------------------------------------------------ draw ----------
  draw(fi, alpha, now) {
    const m = this.model;
    if (!m) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this._drawTiles();
    this._drawFeatures();
    this._drawBuildings();
    this._drawResidents(fi, alpha, now);
    this._drawBubbles(now);
    this._drawPopups(now);
  }

  _drawTiles() {
    const { assets, tile } = this;
    const tiles = this.model.map.tiles;
    const src = assets.tileset, T = assets.T;
    for (let y = 0; y < tiles.length; y++) {
      const row = tiles[y];
      for (let x = 0; x < row.length; x++) {
        const idx = assets.tileIndex(row[x]);
        this.ctx.drawImage(src, idx * T, 0, T, T, x * tile, y * tile, tile, tile);
      }
    }
  }

  _drawFeatures() {
    const { assets, tile } = this;
    const src = assets.tileset, T = assets.T;
    for (const f of (this.model.map.features || [])) {
      const idx = assets.featureTile(f.type);
      for (let y = f.y; y < f.y + (f.h || 1); y++) {
        for (let x = f.x; x < f.x + (f.w || 1); x++) {
          this.ctx.drawImage(src, idx * T, 0, T, T, x * tile, y * tile, tile, tile);
        }
      }
    }
  }

  _drawBuildings() {
    const { assets, tile, ctx } = this;
    const src = assets.buildings, B = assets.B;
    // sort by y so lower buildings overlap correctly
    const blds = [...(this.model.map.buildings || [])].sort((a, b) => a.y - b.y);
    for (const b of blds) {
      const idx = assets.buildingIndex(b.type);
      const bw = (b.w || 3) * tile, bh = (b.h || 3) * tile;
      // draw so the sprite sits ON the footprint, feet at bottom
      ctx.drawImage(src, idx * B, 0, B, B, b.x * tile, b.y * tile - (bh - (b.h || 3) * tile), bw, bh);
      // label
      if (b.name && b.type !== 'house') {
        ctx.font = `${Math.max(9, tile * 0.42)}px ui-monospace, monospace`;
        ctx.textAlign = 'center';
        const tx = b.x * tile + bw / 2, ty = b.y * tile - 3;
        ctx.fillStyle = 'rgba(20,16,10,.55)';
        ctx.fillText(b.name, tx + 1, ty + 1);
        ctx.fillStyle = '#f4ecd8';
        ctx.fillText(b.name, tx, ty);
      }
    }
  }

  _drawResidents(fi, alpha, now) {
    const m = this.model;
    const fA = m.frames[fi], fB = m.frames[Math.min(fi + 1, m.frames.length - 1)] || fA;
    const T = this.assets.C, tile = this.tile, ctx = this.ctx;
    for (const r of m.residents) {
      const a = fA.pos[r.id], b = fB.pos[r.id];
      if (!a && !b) continue;
      const pa = a || b, pb = b || a;
      const x = (pa[0] + (pb[0] - pa[0]) * alpha);
      const y = (pa[1] + (pb[1] - pa[1]) * alpha);
      const dx = pb[0] - pa[0], dy = pb[1] - pa[1];
      const moving = Math.abs(dx) + Math.abs(dy) > 0.001;
      const dir = facing(dx, dy, this._facing[r.id]);
      this._facing[r.id] = dir;
      // walk cycle 0,1,0,2 ; idle = 0 with a bob
      let col = 0, bob = 0;
      if (moving) {
        const cyc = [0, 1, 0, 2];
        col = cyc[Math.floor(now / 140) % 4];
      } else {
        bob = Math.sin(now / 380 + (r.id.length)) > 0.6 ? -1 : 0;
      }
      const rect = this.assets.charFrameRect(dir, col);
      const sheet = this.assets.tintedChars(this._tintFor[r.id] || '#8fa06a');
      const px = x * tile + (tile - tile) / 2;
      const py = y * tile + bob - tile * 0.15;
      // shadow
      ctx.fillStyle = 'rgba(20,16,10,.22)';
      ctx.beginPath();
      ctx.ellipse(px + tile / 2, py + tile * 0.92, tile * 0.32, tile * 0.14, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.drawImage(sheet, rect.sx, rect.sy, T, T, px, py, tile, tile);
      // selection ring + name
      if (this.selected === r.id) {
        ctx.strokeStyle = '#f4c542';
        ctx.lineWidth = Math.max(1.5, tile * 0.08);
        ctx.strokeRect(px + 1, py + 1, tile - 2, tile - 2);
      }
      if (this.selected === r.id || moving) {
        const label = r.face + ' ' + this._short(r.name);
        ctx.font = `${Math.max(8, tile * 0.36)}px ui-sans-serif, system-ui`;
        ctx.textAlign = 'center';
        const lx = px + tile / 2, ly = py - 3;
        ctx.fillStyle = 'rgba(20,16,10,.6)';
        ctx.fillText(label, lx + 1, ly + 1);
        ctx.fillStyle = '#f4ecd8';
        ctx.fillText(label, lx, ly);
      }
    }
  }

  _short(n) { return n.length > 14 ? n.split(' ')[0] : n; }

  _drawBubbles(now) {
    const ctx = this.ctx;
    this.bubbles = this.bubbles.filter((b) => now - b.born < 3200);
    for (const b of this.bubbles) {
      const age = (now - b.born) / 3200;
      ctx.globalAlpha = age < 0.85 ? 1 : (1 - (age - 0.85) / 0.15);
      const pad = 5, fs = Math.max(10, this.tile * 0.42);
      ctx.font = `${fs}px ui-sans-serif, system-ui`;
      ctx.textAlign = 'left';
      const tw = ctx.measureText(b.text).width;
      const bx = Math.max(2, Math.min(this.canvas.width - tw - 2 * pad - 2, b.x - tw / 2 - pad));
      const by = b.y - fs - 2 * pad - age * 8;
      this._roundRect(bx, by, tw + 2 * pad, fs + 2 * pad, 6);
      ctx.fillStyle = '#fbf6ea'; ctx.fill();
      ctx.strokeStyle = 'rgba(40,30,16,.35)'; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = '#2a2620';
      ctx.fillText(b.text, bx + pad, by + pad + fs - 3);
      ctx.globalAlpha = 1;
    }
  }

  _drawPopups(now) {
    const ctx = this.ctx;
    const COL = { help: '#3f9d5a', give: '#3d84c4', harm: '#c0453b', neutral: '#8a8271' };
    this.popups = this.popups.filter((p) => now - p.born < 1900);
    for (const p of this.popups) {
      const age = (now - p.born) / 1900;
      ctx.globalAlpha = 1 - age;
      const fs = Math.max(9, this.tile * 0.38);
      ctx.font = `600 ${fs}px ui-sans-serif, system-ui`;
      ctx.textAlign = 'center';
      const y = p.y - age * this.tile * 1.4;
      const tw = ctx.measureText(p.text).width;
      this._roundRect(p.x - tw / 2 - 6, y - fs, tw + 12, fs + 8, 999);
      ctx.fillStyle = COL[p.cls] || COL.neutral; ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillText(p.text, p.x, y + 4);
      ctx.globalAlpha = 1;
    }
  }

  _roundRect(x, y, w, h, r) {
    const ctx = this.ctx; r = Math.min(r, h / 2, w / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // click hit-test -> resident id (canvas-space coords)
  pickResident(cx, cy, fi, alpha) {
    const m = this.model; if (!m) return null;
    const fA = m.frames[fi], fB = m.frames[Math.min(fi + 1, m.frames.length - 1)] || fA;
    let best = null, bestD = this.tile * this.tile;
    for (const r of m.residents) {
      const a = fA.pos[r.id] || fB.pos[r.id], b = fB.pos[r.id] || a;
      if (!a) continue;
      const x = (a[0] + (b[0] - a[0]) * alpha + 0.5) * this.tile;
      const y = (a[1] + (b[1] - a[1]) * alpha + 0.5) * this.tile;
      const d = (x - cx) ** 2 + (y - cy) ** 2;
      if (d < bestD) { bestD = d; best = r.id; }
    }
    return best;
  }
}
