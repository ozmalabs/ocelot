"""LiveAudioWorld — a streaming audio WORLD ADAPTER wiring the strong ear + the graph-native selective-action faculty.

Per the architecture rule (CLAUDE.md): a world adapter does only mechanical I/O. This one:
  INGEST  — run the strong (wav2vec2) EAR on an incoming utterance (perception primitive, like FFT/cochlea), slice each
            word, recognise it against the banked exemplars -> write a Recognition{word, margin} node + `gated_by` edge.
  TICK    — substrate.master_tick();tick(): the SEEDED faculty decides ACT/DEFER (graph Rules over margin-vs-threshold) and
            the agent's OWN delta-rule trainer tunes the gate threshold online to a target coverage (teacher-free).
  EMIT    — read back each Recognition's decision -> (word, ACT|DEFER).

NO Python decision: the host never compares margin; every ACT/DEFER and every threshold move is a graph Rule. The gate
adapts online over the stream (nothing frozen). Mic is a trivial input swap of `ingest_utterance`'s audio source.
"""
from __future__ import annotations

import numpy as np


# ---- the selective-action faculty as graph data (the trainer/backprop Rule idiom) ----
def _V(n): return {"type": "Var", "name": n}
def _A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
def _L(v): return {"type": "Lit", "value": v}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}

ACT_RULE = {
    "id": "sa_act", "name": "sa_act",
    "match": [["rec", "gated_by", "gate"]],
    "where": _Gt(_A("rec", "margin"), _A("gate", "threshold")),
    "effects": [["set_attr", "rec", "act", 1.0], ["set_attr", "rec", "deferred", 0.0]]}
DEFER_RULE = {
    "id": "sa_defer", "name": "sa_defer",
    "match": [["rec", "gated_by", "gate"]],
    "where": _Gt(_A("gate", "threshold"), _A("rec", "margin")),
    "effects": [["set_attr", "rec", "deferred", 1.0], ["set_attr", "rec", "act", 0.0]]}
TUNE_RULE = {
    "id": "sa_tune", "name": "sa_tune",
    "match": [["root", "has_gate", "gate"]],
    "where": _Gt(_A("gate", "frame"), _A("gate", "uframe")),
    "effects": [
        ["set_attr", "gate", "threshold", {"__term__": _Plus(
            _A("gate", "threshold"),
            _Times(_L("__eta__"), _Minus(_A("gate", "observed_coverage"), _A("gate", "target_coverage"))))}],
        ["set_attr", "gate", "uframe", {"__term__": _A("gate", "frame")}]]}


def _l2rows(M):
    M = np.asarray(M, np.float32); n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


class GrowingBank:
    """the agent's lexicon — exemplars per word, GROWS online via teach (nothing frozen)."""
    def __init__(self, dtw, prune=30):
        self.bank = {}; self.vocab = []; self.PW = np.zeros((0, 0), np.float32); self.dtw = dtw; self.prune = prune
    def _proto(self, w):
        return _l2rows(np.stack([e.mean(0) for e in self.bank[w]]).mean(0)[None])[0]
    def add(self, w, exemplar):
        new = w not in self.bank
        self.bank.setdefault(w, []).append(np.asarray(exemplar, np.float32))
        p = self._proto(w)
        if new:
            self.vocab.append(w)
            self.PW = p[None] if self.PW.size == 0 else np.vstack([self.PW, p])
        else:
            self.PW[self.vocab.index(w)] = p
    def recognise(self, traj):
        pv = traj.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        top = np.argsort(-(self.PW @ pv))[:self.prune]
        scored = sorted(((self.vocab[i], min(self.dtw(traj, e) for e in self.bank[self.vocab[i]])) for i in top),
                        key=lambda x: x[1])
        (w1, d1), (w2, d2) = scored[0], scored[1]
        return w1, (d2 - d1) / (d2 + d1 + 1e-9)


class LiveAudioWorld:
    def __init__(self, agent, *, ear, bank, vocab, PW, pca_mu, pca_V, dtw, prune=30,
                 target_coverage=0.5, eta=0.3, cov_ema=0.15, init_threshold=0.05, teacher=None, learn=False):
        """agent: a WorldAdapter. ear: callable(audio, fs)->[T,768] wav2vec2 latent (perception primitive).
        bank/vocab/PW/pca_*: the strong-ear exemplar recogniser. dtw: the DTW distance fn.
        teacher: callable(traj)->word (pluggable label source, mechanical host I/O); learn: defer-and-learn on."""
        self.a = agent
        self.ear = ear
        # the lexicon is a GROWING bank (seeded from the initial exemplars); recognition routes through it
        self.lex = GrowingBank(dtw, prune)
        for w in vocab:
            for e in bank[w]:
                self.lex.add(w, e)
        self.teacher = teacher; self.learn = learn; self._traj = {}; self.unknowns = []
        self._initial_words = set(self.lex.vocab); self._learned_words = set()
        self.mu = pca_mu; self.V = pca_V; self.dtw = dtw; self.prune = prune
        self.target = float(target_coverage); self.cov_ema = float(cov_ema)
        self.running_cov = float(target_coverage)
        self.frame = 0
        # install the faculty (graph data): Gate + Recognition Rules + trainer Rule
        eta_lit = {"type": "Lit", "value": float(eta)}
        tune = _deep_sub(TUNE_RULE, "__eta__", float(eta))
        self.gate = self.a.s.add_node("Gate", {"threshold": float(init_threshold), "target_coverage": self.target,
                                               "observed_coverage": self.target, "frame": 0.0, "uframe": 0.0})
        root = self.a.s.add_node("Root", {"is_root": 1.0})
        self.a.inner.add_edge_unchecked(root, "has_gate", self.gate)
        for r in (ACT_RULE, DEFER_RULE, tune):
            self.a.inner.add_rule(r)

    def _project(self, latent_word):
        return _l2rows((np.asarray(latent_word, np.float32) - self.mu) @ self.V)

    def _recognise(self, traj):
        """perception -> (word, margin) via the GROWING banked-exemplar DTW. mechanical (no decision over the result)."""
        return self.lex.recognise(traj)

    def ingest_utterance(self, audio, fs, word_spans):
        """PERCEPTION + INGEST: encode the utterance, recognise each word, write Recognition nodes. Returns [(rid, word, gold)]."""
        lat = self.ear(audio, fs)                                # wav2vec2 latent [T,768] (full-utterance context)
        T = lat.shape[0]; dur = len(audio) / fs; fps = T / dur if dur > 0 else 50.0
        out = []
        for (gold, t0, t1) in word_spans:
            a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
            seg = lat[a:b]
            if seg.shape[0] < 1:
                continue
            ptraj = self._project(seg)
            word, margin = self._recognise(ptraj)
            rid = self.a.s.add_node("Recognition", {"margin": float(margin), "word": word, "act": 0.0,
                                                    "deferred": 0.0, "gold": gold})
            self.a.inner.add_edge_unchecked(rid, "gated_by", self.gate)
            self._traj[rid] = ptraj                              # host holds the latent (not graph-storable) for learning
            out.append((rid, word, gold))
        return out

    def step(self, rids):
        """TICK: the faculty decides ACT/DEFER and the trainer tunes the gate. Host only writes a running coverage + clock."""
        self.frame += 1
        self.a.s.set_attr(self.gate, "observed_coverage", float(self.running_cov))
        self.a.s.set_attr(self.gate, "frame", float(self.frame))
        self.a.master_tick(); self.a.tick()
        acts = [self.a.s.node(r)["attrs"].get("act", 0.0) for (r, _w, _g) in rids]
        if acts:
            self.running_cov = (1 - self.cov_ema) * self.running_cov + self.cov_ema * float(np.mean(acts))

    def learn_pass(self, rids):
        """DEFER -> reify an Unknown ('teach me' queue, graph) -> pluggable teacher labels (mechanical) -> append to the
        GROWING bank (in-vocab next time). The DEFER decision was the graph Rule; the teach is host I/O. Returns #taught."""
        if not self.learn or self.teacher is None:
            return 0
        taught = 0
        for (rid, _w, gold) in rids:
            if self.a.s.node(rid)["attrs"].get("act", 0.0) >= 0.5:
                continue                                         # ACTed (confident) -> never ask: cheap-first
            unk = self.a.s.add_node("Unknown", {"pending": 1.0})   # the agent's graph-visible 'teach me'
            self.a.inner.add_edge_unchecked(rid, "raises", unk)
            traj = self._traj.get(rid)
            if traj is None:
                continue
            word = self.teacher(traj, gold)                      # pluggable teacher (oracle/whisper/human) -> the word
            if word is not None:
                self.lex.add(word, traj)                         # LEARN: one-shot append -> in-vocab next time
                if word not in self._initial_words:
                    self._learned_words.add(word)
                self.a.s.set_attr(unk, "pending", 0.0); self.a.s.set_attr(unk, "taught_word", word)
                taught += 1
            self.unknowns.append(unk)
        return taught

    def teach_word(self, word, traj):
        """mechanical: append a taught exemplar to the GROWING bank + track it for persistence (the learn step)."""
        self.lex.add(word, np.asarray(traj, np.float32))
        if word not in self._initial_words:
            self._learned_words.add(word)

    def persist(self, category="learned_speech"):
        """Persist the LEARNED words to a seed via the teach facility so they survive reboot (mechanical host I/O).
        Stores each new word's exemplars as WordExemplar nodes + the PCA-ear basis once. Returns #exemplars saved."""
        from domains.teach import teach
        V = np.asarray(self.V)
        teach(self.a, "PcaEarBasis", {"mu": np.asarray(self.mu).tolist(), "V_flat": V.flatten().tolist(),
                                      "rows": int(V.shape[0]), "cols": int(V.shape[1])}, category=category)
        n = 0
        for w in sorted(self._learned_words):
            for e in self.lex.bank[w]:
                e = np.asarray(e, np.float32)
                teach(self.a, "WordExemplar", {"word": w, "traj_flat": e.flatten().tolist(),
                                               "T": int(e.shape[0]), "D": int(e.shape[1])}, category=category)
                n += 1
        return n

    def emit(self, rid):
        """read back the GRAPH's decision (mechanical query)."""
        at = self.a.s.node(rid)["attrs"]
        return at.get("word"), ("ACT" if at.get("act", 0.0) >= 0.5 else "DEFER")

    def threshold(self):
        return self.a.s.node(self.gate)["attrs"]["threshold"]

    @property
    def vset(self):
        return set(self.lex.vocab)                               # the CURRENT (growing) vocabulary

    def bank_size(self):
        return len(self.lex.vocab)


def load_learned_seed(category="learned_speech", seeds_dir=None):
    """Read a persisted learned-lexicon seed -> (pca_mu, pca_V, {word: [trajectories]}). The fresh-boot side of persist()."""
    import json
    from pathlib import Path
    sd = Path(seeds_dir) if seeds_dir else Path(__file__).resolve().parent.parent / "seeds"
    path = sd / f"{category}.json"
    if not path.exists():
        return None, None, {}
    m = json.loads(path.read_text())
    mu = V = None; learned = {}
    for n in m.get("nodes", []):
        a = n.get("attrs", {})
        if n.get("type") == "PcaEarBasis":
            mu = np.asarray(a["mu"], np.float32); V = np.asarray(a["V_flat"], np.float32).reshape(a["rows"], a["cols"])
        elif n.get("type") == "WordExemplar":
            learned.setdefault(a["word"], []).append(np.asarray(a["traj_flat"], np.float32).reshape(a["T"], a["D"]))
    return mu, V, learned


def _deep_sub(obj, marker, value):
    """replace the eta placeholder literal in a copy of the rule dict."""
    import copy
    r = copy.deepcopy(obj)
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if v == marker:
                    o[k] = value
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(r)
    return r
