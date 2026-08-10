"""arc_ls20_consume — RUNG 225000: FOLD the flash consume-marking (223000) onto the
object-permanence tracker (224000) to close ls20's trail/consume residual.

224000's tracker translates the tracked object per-cell and gets live change-set
F1 0.9639 on real ls20; the honest ~0.036 gap is the TRAIL/CONSUME residual -- when
the avatar moves it drops/consumes cells a rigid-translate model cannot predict
(224's synthetic trail scene scored 0.86 for exactly this reason). 223000's flash
rung already DETECTS + LOCALISES the consume event on real frames (the general
onset stream, Argmax fg_pick_flash) -- it was just never wired into prediction.

This module FOLDS them: the flash onset localises WHERE the consume happened this
step (a COARSE luminance region, NOT the exact consumed set); the 224 tracker
supplies the object translation (hence the VACATED footprint); the model marks the
VACATED cells the flash localises as consumed -> a discovered trail value T. The
combined per-cell prediction = translate the object (224) + mark the flash-
localised consumed cells (225).

ANTI-CIRCULARITY (the fatal trap, kept airtight -- same discipline as 223):
  * The flash is a LUMINANCE-only transient (FLASH_COLOUR halo on FIELD cells
    ADJACENT to the consumed region), NEVER written into the colour grid and never
    on the consumed cells themselves. It carries WHERE, never WHAT.
  * The consumed VALUE T is DISCOVERED from observation (a graph ConsumeHypothesis),
    never handed by the flash and never hardcoded.
  * The consumed region VARIES per step (a per-step contiguous sub-block of the
    vacated footprint), so a fixed object-relative offset CANNOT predict it -- the
    per-step flash is genuinely needed. The flash marks a REGION; the model still
    intersects it with the tracker's VACATED set + applies the discovered T.
  * The RANDOM-FLASH control (same fold, flash location randomised) is the anti-rig
    null: if the benefit were the marking MECHANISM (not the flash's localisation)
    the random-flash arm would win too. It does not -> the win is the localisation.

The 224 LiveObjectTracker is reused UNCHANGED (imported, never modified); the flash
attention is 223's fg_pick_flash rule (reused); the consume value is a graph
ConsumeHypothesis minted by a rule (seeds/ls20_consume.json). The adapter is
mechanical: perceive -> onset -> attend (graph rule) -> translate (224) -> mark
(vacated ∩ flash-region) -> discovered T. Integer-native. No Rust.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_percell import Percell, score_prediction  # noqa: E402
from worlds.arc_ls20_percell_track import LiveObjectTracker, field_colours  # noqa: E402
from worlds.arc_ls20_flash import OnsetEye, FLASH_COLOUR  # noqa: E402

# ls20-shaped palette. Field = {BG, FIELD}; figure = avatar + trail.
BG = 0
FIELD = 4          # nested play-field / walls (dark grey)
AVATAR = 9
TRAIL = 11         # the DROPPED/CONSUMED trail value T (discovered by the agent)
DISTRACTORS = [5, 6, 7]

_DIRS = {"move_up": (-1, 0), "move_down": (1, 0), "move_left": (0, -1), "move_right": (0, 1)}


# ============================================================================
# THE CONSUME ARENA (world PHYSICS; the agent never reads these tables)
# ============================================================================
class ConsumeArena:
    """A streamed ls20-shaped arena: a solid avatar block (colour 9) roams a nested
    field; each move VACATES its whole old footprint (the step is >= the block
    extent, so old/new do not overlap) and CONSUMES a per-step-varying contiguous
    sub-block of that footprint -> a dropped TRAIL value (colour 11). A transient
    luminance FLASH halo marks the consumed region (on FIELD cells adjacent to it,
    never on the consumed cells, never in the colour grid). Optional random-walking
    distractors add clutter. WORLD PHYSICS -- ground truth; the agent never reads it.
    """

    def __init__(self, rng, n=24, block=5, step=6, n_distractors=0, csize=3):
        self.rng = rng
        self.n = n
        self.block = block
        self.step = step
        self.csize = csize      # consumed sub-block side (a csize x csize interior blob)
        self.n_d = n_distractors
        # nested field block (value 4) the avatar roams inside; BG (0) is the outer
        # field. field_colours(k=2) -> {0, 4}.
        self.f0, self.f1 = 3, n - 3
        # avatar top-left, kept clear of the field border so a `step` move stays in.
        m = block + step + 1
        self.ar = int(rng.integers(self.f0 + 1, self.f1 - m))
        self.ac = int(rng.integers(self.f0 + 1, self.f1 - m))
        self.distractors = []
        for i in range(n_distractors):
            dr = int(rng.integers(self.f0 + 1, self.f1 - 2))
            dc = int(rng.integers(self.f0 + 1, self.f1 - 2))
            self.distractors.append({"r": dr, "c": dc, "colour": DISTRACTORS[i % len(DISTRACTORS)]})

    def _avatar_cells(self, ar, ac):
        return [(ar + r, ac + c) for r in range(self.block) for c in range(self.block)]

    def grid(self):
        g = np.full((self.n, self.n), BG, dtype=np.int32)
        g[self.f0:self.f1, self.f0:self.f1] = FIELD
        for d in self.distractors:
            if 0 <= d["r"] < self.n and 0 <= d["c"] < self.n:
                g[d["r"], d["c"]] = d["colour"]
        for (r, c) in self._avatar_cells(self.ar, self.ac):
            if 0 <= r < self.n and 0 <= c < self.n:
                g[r, c] = AVATAR
        return g

    _WALK = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]

    def _walk_distractors(self):
        for d in self.distractors:
            wr, wc = self._WALK[int(self.rng.integers(0, len(self._WALK)))]
            nr, nc = d["r"] + wr, d["c"] + wc
            if self.f0 + 1 <= nr < self.f1 - 1 and self.f0 + 1 <= nc < self.f1 - 1:
                d["r"], d["c"] = nr, nc

    def _consumed_blob(self, ar, ac):
        """A per-step-varying contiguous csize x csize sub-block of the OLD footprint
        that is consumed to the trail value, placed at a RANDOM interior offset. It
        VARIES per step (seeded) so a fixed object-relative offset cannot predict it
        -- the per-step flash is genuinely needed."""
        span = self.block - self.csize
        off_r = int(self.rng.integers(0, span + 1))
        off_c = int(self.rng.integers(0, span + 1))
        return [(ar + off_r + i, ac + off_c + j)
                for i in range(self.csize) for j in range(self.csize)]

    def _flash_glow(self, consumed):
        """The transient luminance flash = a soft GLOW BLOB: every consumed cell
        DILATED by one (Chebyshev-1). This is a realistic glow of light around the
        consume, NOT a pixel-perfect outline of the consumed set -- it spills onto
        the surrounding cells (including non-consumed vacated interior), so the onset
        localises a REGION and the model must still intersect it with the tracker's
        VACATED set + apply the discovered value. The glow is luminance-only (never
        the colour grid, never handing the exact consumed cells)."""
        cset = set(consumed)
        glow = set()
        for (r, c) in cset:
            for ddr in (-1, 0, 1):
                for ddc in (-1, 0, 1):
                    hr, hc = r + ddr, c + ddc
                    if 0 <= hr < self.n and 0 <= hc < self.n:
                        glow.add((hr, hc))
        return sorted(glow)

    def step_action(self, action):
        """Apply the action; return (prev, nxt, flash_cells, consumed_cells). Both
        colour grids are FLASH-FREE; the flash lives only in `flash_cells` (a
        luminance overlay the onset eye reads)."""
        prev = self.grid()
        old_ar, old_ac = self.ar, self.ac
        self._walk_distractors()
        dr, dc = _DIRS[action]
        self.ar += dr * self.step
        self.ac += dc * self.step
        consumed = self._consumed_blob(old_ar, old_ac)
        nxt = self.grid()
        # drop the trail on the consumed blob (world physics writes the colour grid)
        for (r, c) in consumed:
            if 0 <= r < self.n and 0 <= c < self.n:
                nxt[r, c] = TRAIL
        flash = self._flash_glow(consumed)
        return prev, nxt, flash, consumed


# ============================================================================
# THE CONSUME FOLD — reuses the 224 tracker + 223 flash attention, adds a graph
# ConsumeHypothesis (discovered T) and the flash-localised consume marking.
# ============================================================================
def _load_consume_rules(pc):
    """Load 223's fg_pick_flash (attention) + this rung's consume rules onto a
    Percell, and arm the flags. Reuses graph data; the tracker stays unchanged."""
    from domains.ls20_flash_seed import RULES as FLASH_RULES
    from domains.ls20_consume_seed import RULES as CONSUME_RULES
    for r in FLASH_RULES + CONSUME_RULES:
        pc.n.add_rule(r)
    pc.n.set_attr(pc.g, "flash_on", 1.0)
    pc.n.set_attr(pc.g, "flash_row", 0.0)
    pc.n.set_attr(pc.g, "flash_col", 0.0)
    pc.n.set_attr(pc.g, "flash_mag", 0.0)
    pc.n.set_attr(pc.g, "consume_on", 1.0)
    pc.n.set_attr(pc.g, "obs_consume_value", 0.0)
    # a single hub node so cm_mint_consume matches the game exactly once (mint-once).
    cs = pc.s.add_node("ConsumeState", {"armed": 1.0})
    pc.n.add_edge_unchecked(pc.g, "has_consume_state", cs)


class ConsumeTracker:
    """Wraps a 222000 Percell + the 224000 LiveObjectTracker (unchanged) and folds
    in the flash-localised consume marking. `mode`:
      * "translate"    -- 224-alone (translate only; the baseline arm A).
      * "flash"        -- 224 + flash-localised consume (the headline arm B).
      * "random"       -- 224 + consume at a RANDOM location (anti-rig control C).
      * "blind_all"    -- 224 + mark ALL vacated cells as consumed (over-predicts, D).
    The graph decides the flash location (fg_pick_flash) and holds the discovered
    trail value (ConsumeHypothesis); the adapter renders mechanically."""

    def __init__(self, mode="flash", cap=200, n_field=2, mag_band=6.0, win=2, rng=None):
        self.mode = mode
        self.pc = Percell()
        self.trk = LiveObjectTracker(self.pc, cap=cap, n_field=n_field)
        # flash onsets are the brightest transients; a cell whose onset dB is within
        # mag_band of the attended (Argmax) onset is part of the flash glow cluster
        # (dimmer avatar-motion / distractor onsets fall below the band). The glow is
        # a soft blob whose brightest onsets ring the consumed cells (the dim field
        # around them jumps furthest), so the model windows `win` cells around the
        # cluster CENTROID to reach inward to the consumed figure cells -- the same
        # attend-then-window pattern as 223's _window_region_spec.
        self.mag_band = mag_band
        self.win = win
        self.rng = rng if rng is not None else np.random.default_rng(0)
        if mode in ("flash", "random", "blind_all"):
            _load_consume_rules(self.pc)

    # -- graph-native flash attention (223's fg_pick_flash) -----------------
    def _attend_flash(self, onset_events):
        """Returns (row, col, magnitude_db) of the attended (brightest) onset, via
        the graph rule fg_pick_flash (Argmax magnitude), or None."""
        s, n, g = self.pc.s, self.pc.n, self.pc.g
        for nid in list(s.neighbours(g, "has_flash_onset")):
            s.remove_node(nid)
        if not onset_events:
            return None
        for (r, c, mag) in onset_events:
            fo = s.add_node("FlashOnset", {"row_index": float(r), "column_index": float(c),
                                           "magnitude_db": float(mag)})
            n.add_edge_unchecked(g, "has_flash_onset", fo)
        n.set_attr(g, "flash_mag", -1.0)
        n.set_attr(g, "phase", "attend_flash")
        n.run_rules()
        a = s.node(g)["attrs"]
        if float(a.get("flash_mag") or -1.0) < 0.0:
            return None
        return (float(a.get("flash_row")), float(a.get("flash_col")), float(a.get("flash_mag")))

    # -- graph-native consume value (ConsumeHypothesis) ---------------------
    def _learn_consume_value(self, tval):
        """Stamp the observed trail value + tick the consume-mint rule (graph). The
        VALUE is a perception readout (like the shift dr/dc); WHICH cells and WHETHER
        to mint is the graph rule's call."""
        n, g = self.pc.n, self.pc.g
        n.set_attr(g, "obs_consume_value", float(tval))
        n.set_attr(g, "phase", "consume_obs")
        n.run_rules()

    def _consume_value(self):
        """Read the discovered trail value from the graph ConsumeHypothesis."""
        s, g = self.pc.s, self.pc.g
        for h in s.neighbours(g, "has_consume"):
            return int(float(s.node(h)["attrs"].get("value") or 0))
        return 0

    # -- one observation (learn shift via 224; learn T via graph) -----------
    def observe(self, prev, cur, action, consumed_cells=None):
        """Learn the shift (224, unchanged) and the trail value T (graph). T is
        derived ORACLE-FREE: the consumed cells are the VACATED positions (old object
        minus its translate) that did NOT revert to the field in `cur`; their value
        is the trail value. No ground-truth consumed set is read (`consumed_cells` is
        ignored for learning -- it exists only as the offline gate's separate truth).
        At OBSERVE time `cur` is available so the consume is directly visible; the
        flash is needed only at PREDICT time, where `cur` is not yet known."""
        old_obj = set(self.trk.obj.keys()) if self.trk.obj else set()
        self.trk.observe(prev, cur, action)   # 224: learns shift, updates obj to new
        if self.mode not in ("flash", "random", "blind_all") or not old_obj:
            return
        h = self.pc.hypothesis(action)
        if h is None or (h["dr"] == 0 and h["dc"] == 0):
            return
        new = {(r + h["dr"], c + h["dc"]) for (r, c) in old_obj}
        vacated = old_obj - new
        fields = field_colours(prev, self.trk.n_field)
        H, W = cur.shape
        vals = [int(cur[r, c]) for (r, c) in vacated
                if 0 <= r < H and 0 <= c < W and int(cur[r, c]) not in fields]
        tval = _mode(vals)
        if tval is not None:
            self._learn_consume_value(tval)

    # -- vacated footprint (from the 224 tracker's object + learned shift) ---
    def _vacated(self, action):
        h = self.pc.hypothesis(action)
        if h is None or self.trk.obj is None or (h["dr"] == 0 and h["dc"] == 0):
            return set(), (0, 0)
        dr, dc = h["dr"], h["dc"]
        old = set(self.trk.obj.keys())
        new = {(r + dr, c + dc) for (r, c) in old}
        return (old - new), (dr, dc)

    # -- flash-localised consume region -------------------------------------
    def _consume_region(self, onset_events):
        """The flash-localised region: fg_pick_flash (graph rule, Argmax) attends the
        brightest onset; the FLASH CLUSTER is every onset within mag_band dB of it
        (the bright glow ring; dimmer avatar-motion onsets fall below the band); the
        region is a `win`-cell window around the cluster CENTROID. A graph decision
        (fg_pick_flash) + mechanical window assembly, exactly like 223's
        _window_region_spec. The glow is COARSE (a soft blob, not the exact consumed
        cells -- measured precision ~0.75, never 1.0), so intersecting it with the
        tracker's VACATED set is what pins the consumed cells -- the non-trivial step
        224 supplies. The window alone (no vacated intersection) would also mark
        FIELD cells; the object model is required."""
        attended = self._attend_flash(onset_events)
        if attended is None:
            return set()
        _ar, _ac, amag = attended
        cluster = [(r, c) for (r, c, m) in onset_events if m >= amag - self.mag_band]
        if not cluster:
            return set()
        cr = int(round(float(np.mean([r for r, c in cluster]))))
        cc = int(round(float(np.mean([c for r, c in cluster]))))
        w = self.win
        return {(cr + ddr, cc + ddc) for ddr in range(-w, w + 1) for ddc in range(-w, w + 1)}

    def predict_consumed(self, prev, action, onset_events):
        """The model's predicted consumed-cell SET for this step (vacated ∩ flash-
        region). Exposed for the flash-localises-consume precision/recall gate."""
        vacated, _ = self._vacated(action)
        if not vacated:
            return set()
        if self.mode == "blind_all":
            return set(vacated)
        if self.mode == "random":
            # anti-rig: the SAME win-window at a RANDOM location (no real signal). If
            # the benefit were the marking MECHANISM (not the flash's localisation),
            # this would win too. It does not -> the win is the localisation.
            H, W = prev.shape
            rr = int(self.rng.integers(0, H)); rc = int(self.rng.integers(0, W))
            w = self.win
            region = {(rr + ddr, rc + ddc) for ddr in range(-w, w + 1) for ddc in range(-w, w + 1)}
            return vacated & region
        region = self._consume_region(onset_events)
        return vacated & region

    def predict(self, prev, action, onset_events=None):
        """Predict the per-cell next frame = translate the tracked object (224) +
        mark the flash-localised consumed cells to the discovered trail value."""
        base = self.trk.predict(prev, action)
        if self.mode == "translate":
            return base
        consumed = self.predict_consumed(prev, action, onset_events or [])
        if not consumed:
            return base
        t = self._consume_value()
        if t == 0:
            return base
        g = base.copy()
        H, W = g.shape
        for (r, c) in consumed:
            if 0 <= r < H and 0 <= c < W:
                g[r, c] = t
        return g


def _mode(vals):
    vals = [int(v) for v in vals]
    if not vals:
        return None
    from collections import Counter
    return Counter(vals).most_common(1)[0][0]


# ============================================================================
# METRICS — precision/recall of the predicted consumed set vs the actual set
# ============================================================================
def consume_pr(pred_set, true_set):
    if not pred_set and not true_set:
        return 1.0, 1.0, 1.0
    tp = len(pred_set & true_set)
    prec = tp / len(pred_set) if pred_set else 0.0
    rec = tp / len(true_set) if true_set else (1.0 if not pred_set else 0.0)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


# ============================================================================
# PAIRED-EPISODE DRIVER — all arms see IDENTICAL frames + onsets (the eye is run
# ONCE per seed; the arms differ ONLY in the consume fold, so the ablation is a
# clean paired comparison of 224-alone vs the fold).
# ============================================================================
def record_episode(seed, steps=40, n=24, block=5, step=6, csize=3, n_distractors=0):
    """Stream one arena, running the REAL onset eye once, and record
    (action, prev, nxt, flash_cells, consumed_cells, onset_events) per step. The
    onset is the general GraphEye 2-D onset stream on the flash-overlay transition
    (223's machinery). Deterministic per seed (ls20 is deterministic)."""
    rng = np.random.default_rng(seed)
    arena = ConsumeArena(rng, n=n, block=block, step=step, csize=csize,
                         n_distractors=n_distractors)
    eye = OnsetEye(n)
    eye.adapt(arena.grid())
    records = []
    dirs = list(_DIRS)
    for t in range(steps):
        action = dirs[t % 4]
        prev, nxt, flash, consumed = arena.step_action(action)
        onset = eye.onset_on_transition(prev, nxt, flash)
        records.append((action, prev, nxt, flash, consumed, onset))
        # keep the avatar inside the field (mechanical bounds reset -- world physics)
        if not (arena.f0 < arena.ar < arena.f1 - block and
                arena.f0 < arena.ac < arena.f1 - block):
            arena.ar = (arena.f0 + arena.f1) // 2
            arena.ac = (arena.f0 + arena.f1) // 2
    eye.stop()
    return records


def eval_arm(mode, records, seed=0):
    """Replay a recorded episode for one arm. Returns (f1_list, pr_list) over the
    steps where the action had a learned shift AND a tracked object (identical set
    across arms -- observe is the same; only the fold differs)."""
    trk = ConsumeTracker(mode=mode, rng=np.random.default_rng(seed + 13))
    f1s, prs = [], []
    for (action, prev, nxt, flash, consumed, onset) in records:
        had = (trk.pc.hypothesis(action) is not None) and (trk.trk.obj is not None)
        pred = trk.predict(prev, action, onset)
        if had:
            f1s.append(score_prediction(prev, nxt, pred)["f1_strict"])
            pset = trk.predict_consumed(prev, action, onset)
            prs.append(consume_pr(pset, set(consumed)))
        trk.observe(prev, nxt, action, consumed)
    return f1s, prs
