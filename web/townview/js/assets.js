// assets.js — load the pixel-art sheets (manifest-driven) and provide tinted
// per-resident character frames (MULTIPLY the light body by a class/role colour).

const BASE = 'assets/';

function loadImage(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error('failed to load ' + src));
    im.src = src;
  });
}

// a cohesive tint per class/role so residents are visually distinct
export const ROLE_TINT = {
  mayor: '#c9a13b', banker: '#6f8bbf', pastor: '#8a6db0', baker: '#c98a5a',
  fishmonger: '#4f97b0', teacher: '#5aa46a', doctor: '#c76f6f', innkeeper: '#b08a4a',
  villager: '#9fae7a', farmer: '#7fa050', smith: '#8a7a6a',
};
export const CLASS_TINT = { rich: '#c9a13b', middle: '#7fa06a', poor: '#9a8a6a' };

export function residentTint(r) {
  return ROLE_TINT[r.role] || (r.cls && CLASS_TINT[r.cls.split('(')[0]]) || '#8fa06a';
}

export class Assets {
  constructor() {
    this.manifest = null;
    this.tileset = null;
    this.characters = null;
    this.buildings = null;
    this._tintCache = new Map();      // color -> tinted character canvas
  }

  async load() {
    this.manifest = await (await fetch(BASE + 'manifest.json')).json();
    [this.tileset, this.characters, this.buildings] = await Promise.all([
      loadImage(BASE + this.manifest.tileset.file),
      loadImage(BASE + this.manifest.characters.file),
      loadImage(BASE + this.manifest.buildings.file),
    ]);
    this.T = this.manifest.tileset.tile;
    this.C = this.manifest.characters.frame;
    this.B = this.manifest.buildings.frame;
    return this;
  }

  tileIndex(name) {
    const t = this.manifest.tileset.tiles;
    return t[name] != null ? t[name] : t[this.manifest.tile_map[name]] != null
      ? t[this.manifest.tile_map[name]] : t.grass;
  }

  buildingIndex(type) {
    const b = this.manifest.buildings.sprites;
    const mapped = this.manifest.building_map[type] || type;
    return b[mapped] != null ? b[mapped] : b.house;
  }

  featureTile(type) {
    const mapped = (this.manifest.feature_map || {})[type] || 'bush';
    return this.tileIndex(mapped);
  }

  // return a canvas of the whole character sheet tinted by `color` (cached)
  tintedChars(color) {
    if (this._tintCache.has(color)) return this._tintCache.get(color);
    const w = this.characters.width, h = this.characters.height;
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const g = c.getContext('2d');
    g.imageSmoothingEnabled = false;
    g.drawImage(this.characters, 0, 0);
    // multiply tint over the sprite, then re-apply alpha via destination-in
    g.globalCompositeOperation = 'multiply';
    g.fillStyle = color;
    g.fillRect(0, 0, w, h);
    g.globalCompositeOperation = 'destination-in';
    g.drawImage(this.characters, 0, 0);
    g.globalCompositeOperation = 'source-over';
    this._tintCache.set(color, c);
    return c;
  }

  charFrameRect(direction, frameCol) {
    const dirs = this.manifest.characters.directions;
    const row = dirs[direction] != null ? dirs[direction] : 0;
    return { sx: frameCol * this.C, sy: row * this.C, s: this.C };
  }
}
