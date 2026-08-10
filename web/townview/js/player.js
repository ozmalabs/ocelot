// player.js — the playback clock. Owns the rAF loop, current (fractional) frame
// position, speed, play/pause and scrub. Drives the renderer and fires callbacks so
// the HUD / chronicle stay in sync. Works for a fixed replay AND a growing live feed.

const SPEEDS = [0.5, 1, 2, 4, 8];
const BASE_FPS = 2.2;        // frames (ticks) per second at speed 1

export class Player {
  constructor(renderer) {
    this.r = renderer;
    this.fi = 0;             // fractional frame position
    this.playing = false;
    this.speedIdx = 1;       // -> SPEEDS[1] == 1x
    this.last = 0;
    this._lastInt = -1;
    this.live = false;
    this.follow = true;      // live: stick to the newest frame
    this.onFrameEnter = () => {};
    this.onTick = () => {};   // per-rAF, for HUD
    this._raf = null;
  }

  get speed() { return SPEEDS[this.speedIdx]; }
  get frames() { return this.r.model ? this.r.model.frames : []; }
  get count() { return this.frames.length; }

  start() {
    const loop = (now) => {
      this._step(now);
      this._raf = requestAnimationFrame(loop);
    };
    this._raf = requestAnimationFrame(loop);
  }

  stop() { if (this._raf) cancelAnimationFrame(this._raf); }

  play() { this.playing = true; this.last = performance.now(); }
  pause() { this.playing = false; }
  toggle() { this.playing ? this.pause() : this.play(); }

  cycleSpeed() { this.speedIdx = (this.speedIdx + 1) % SPEEDS.length; return this.speed; }

  seek(idx) {
    const n = this.count;
    this.fi = Math.max(0, Math.min(n - 1, idx));
    this._lastInt = Math.floor(this.fi);
    this.r.clearEphemeral();
    this.follow = this.live && this.fi >= n - 1.02;
  }

  // live: a frame just arrived; if following, keep us pinned to the end
  onLiveAppend() {
    if (this.live && this.follow) this.fi = Math.max(this.fi, this.count - 1.0001);
  }

  _step(now) {
    const n = this.count;
    if (n === 0) { this.onTick(this); return; }
    const dt = Math.min(80, now - this.last);
    this.last = now;
    if (this.playing) {
      this.fi += (dt / 1000) * BASE_FPS * this.speed;
      const maxi = n - 1;
      if (this.fi >= maxi) {
        this.fi = maxi;
        if (!this.live) this.playing = false;      // replay ends; live holds
        else this.follow = true;
      }
    }
    const fiInt = Math.floor(this.fi);
    if (fiInt !== this._lastInt) {
      // entered new integer frame(s) -> emit their events in order
      const from = Math.max(0, this._lastInt + 1);
      for (let k = from; k <= fiInt && k < n; k++) {
        this.r.emitFrameEvents(this.frames[k], now);
        this.onFrameEnter(k, this.frames[k]);
      }
      this._lastInt = fiInt;
    }
    const alpha = this.fi - fiInt;
    this.r.draw(fiInt, alpha, now);
    this.onTick(this);
  }
}
