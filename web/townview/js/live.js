// live.js — SSE client for /api/live. Reconnects, and reports status to the caller.
// The stream emits `meta` (once), `frame` (per tick), `paper` (on board changes),
// `end`. The caller folds `frame` into the same timeline the replay uses.

export class LiveStream {
  constructor({ onMeta, onFrame, onPaper, onStatus, onEnd }) {
    this.onMeta = onMeta; this.onFrame = onFrame; this.onPaper = onPaper;
    this.onStatus = onStatus; this.onEnd = onEnd;
    this.es = null; this.closed = false; this.retries = 0;
  }

  connect({ cast = 8, seed = 276000, ticks = 160 } = {}) {
    this.closed = false;
    this._open({ cast, seed, ticks });
  }

  _open(params) {
    const qs = new URLSearchParams(params).toString();
    this.onStatus('connecting');
    const es = new EventSource('api/live?' + qs);
    this.es = es;
    es.onopen = () => { this.retries = 0; this.onStatus('live'); };
    es.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.type === 'meta') this.onMeta(msg);
      else if (msg.type === 'frame') this.onFrame(msg);
      else if (msg.type === 'paper') this.onPaper(msg);
      else if (msg.type === 'end') { this.onStatus('ended'); this.onEnd(msg); this._closeES(); }
    };
    es.onerror = () => {
      this._closeES();
      if (this.closed) return;
      // ended cleanly? EventSource fires error on server close too.
      this.retries += 1;
      if (this.retries > 5) { this.onStatus('ended'); return; }
      this.onStatus('reconnecting');
      setTimeout(() => { if (!this.closed) this._open(params); }, 800 * this.retries);
    };
  }

  _closeES() { if (this.es) { this.es.close(); this.es = null; } }

  close() { this.closed = true; this._closeES(); this.onStatus('idle'); }
}
