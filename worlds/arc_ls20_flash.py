"""arc_ls20_flash — RUNG 223000: the mechanical host adapter + drivers for
FLASH-ONSET-GUIDED mechanic discovery.

Tests the owner's claim: *"the flash when the avatar goes to the shape is a
salience indicator of what the rules are."* The transient flash on avatar<->shape
contact is ls20's OWN supervision signal -- it LOCALISES (where a rule fires) and
TIMES (which step). This attacks 222000's measured live residual: the avatar is
NOT colour-separable from static structure amid clutter, so blind mode-colour
region-selection lands on the wrong object; the flash points to the right one.

Flash-guided discovery = the SAME 222000 sd-loop TransformDecode discovery, but
curiosity/ATTENTION is routed by the flash ONSET (which region + which step)
instead of by blind mode-colour. The flash only changes WHERE/WHEN the sd-loop is
pointed FIRST; the transform is STILL discovered by the identical sd-loop.

KEY DISTINCTION (earned by the gates): the flash is a POINTER (salience+timing),
DISTINCT from the persistent TRANSFORM it announces -- the flash is TRANSIENT (it
reverts), the rule's effect PERSISTS. Separate them: the flash localises/times,
the transform is the content.

ANTI-CIRCULARITY (stated explicitly): the flash appearance is IDENTICAL for all
10 actions (a fixed FLASH_COLOUR blob at the rule object's contact location).
Given ONLY the flash you cannot tell move_up from rotate -- you must read the
object geometry. Both arms discover the transform via the IDENTICAL sd-loop; the
flash changes only the region handed to it first. The blind arm ALSO converges
(222000 offline F1 1.0) -- the comparison is SAMPLE-EFFICIENCY, not can-converge.

This adapter is ONLY mechanical I/O:
  PERCEIVE  -- reuse 222000's pixel-eye round-trip + sd-loop transform recogniser.
  ONSET     -- run the REAL GraphEye 2-D onset stream (the general onset machinery
               that serves Doom / the photon eye) on (prev,cur); read the
               RetinalOnsetEvents. The flash is the brightest transient.
  ATTEND    -- copy the onset events into the agent graph as FlashOnset nodes; the
               graph RULE fg_pick_flash (Argmax magnitude_db) picks the attended
               flash location. A graph DECISION, not Python.
  DISCOVER  -- the region-selector fed to the IDENTICAL 222000 sd-loop is the ONLY
               difference between arms (blind=mode-colour over ALL changed cells;
               flash=mode non-bg-non-flash colour among changed cells in a window
               around the attended flash onset).
  APPLY/MEASURE -- 222000's render + CHANGE-SET metrics, unchanged.

Reuses worlds/arc_ls20_percell wholesale; adds only the clutter arena, the
transient flash, the onset driver, and the region-hinted discovery variants.
Nothing here reads a ground-truth action->transform table.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import worlds.arc_ls20_percell as PC  # noqa: E402
from worlds.arc_ls20_percell import (  # noqa: E402
    ACTIONS, AVATAR_COLOUR, SYMBOL_COLOUR, BG, FURN,
    CORPUS, RECOLOUR_MAP, apply_transform, _reposition, _reanchor,
    _recognise_transform, _grid_object, _mode_nonbg, world_next,
    score_prediction, Percell,
)
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# A fixed transient marker colour, distinct from bg/furniture/avatar/symbol and
# every distractor colour. It is the SAME for all 10 actions -> it carries WHERE
# + WHEN, never WHAT (the anti-circularity guarantee).
FLASH_COLOUR = 8
DISTRACTOR_COLOURS = [5, 6, 7, 13, 15]

# Luminance look-up for the onset eye. The flash is the BRIGHTEST transient (a
# flash IS bright -- realistic, not rigged: it does not encode the transform, it
# is simply the most salient onset). Static field/furniture dim -> adapts to
# silence; moving objects medium -> their motion fires ambient onsets below the
# flash.
_LUMA_LUT = np.full(64, 12.0, dtype=np.float64)
_LUMA_LUT[BG] = 8.0
_LUMA_LUT[FURN] = 20.0
for _c in DISTRACTOR_COLOURS:
    _LUMA_LUT[_c] = 55.0
_LUMA_LUT[AVATAR_COLOUR] = 55.0
_LUMA_LUT[SYMBOL_COLOUR] = 55.0
# The flash is the BRIGHTEST transient by a wide margin (a flash IS bright): its
# onset dB departure dominates any object-motion onset, so Argmax(magnitude_db)
# points to it. This is realism, not rigging -- the flash does not encode the
# transform, it is simply the most salient onset.
_LUMA_LUT[FLASH_COLOUR] = 255.0


def luma(grid):
    """Map an ls20 colour grid to a luminance grid for the onset eye."""
    return _LUMA_LUT[np.asarray(grid, dtype=np.int64)]


# ============================================================================
# THE CLUTTER ARENA (persistent, streamed) + the TRANSIENT FLASH
# ============================================================================
def _small_furniture(n):
    """A static field the agent must NOT predict changing: a short vertical wall.
    Static -> never in any change-set; it only pads raw accuracy (the trap) and
    is what the onset floor adapts to (-> silence)."""
    col = n - 6
    return {(r, col) for r in range(4, n - 4)}


class FlashArena:
    """A persistent ls20-shaped arena the floor can adapt to, streamed one action
    at a time. Furniture (static) + avatar (colour 9) + carried symbol (colour 11)
    + n_distractors sprites (distinct colours) that RANDOM-WALK every step
    independently of the action (ambient clutter). On EVERY action a TRANSIENT
    flash (FLASH_COLOUR) marks the rule object's post-action location; the flash
    is present only in the returned next frame and does NOT persist in the arena.

    The rule object per action: moves -> avatar (9); station transforms -> symbol
    (11). Ground-truth physics reuses 222000's world_next; the agent never reads
    the action->transform table.
    """

    def __init__(self, rng, n=24, n_distractors=2):
        self.rng = rng
        self.n = n
        self.n_d = n_distractors
        self.furn = _small_furniture(n)
        # avatar polyomino (colour 9) in a clear band.
        a_name = rng.choice(list(CORPUS.keys()))
        a_offs, _ = CORPUS[a_name]
        self.a_offs = a_offs
        ah = max(r for r, c in a_offs) + 1
        aw = max(c for r, c in a_offs) + 1
        self.ar = int(rng.integers(6, n - 8 - ah))
        self.ac = int(rng.integers(2, n - 10 - aw))
        # carried symbol (colour 11) at a fixed top-left carry anchor; held as
        # absolute (r,c,v) cells so station transforms apply CUMULATIVELY.
        s_name = rng.choice(list(CORPUS.keys()))
        s_offs, _ = CORPUS[s_name]
        self.car, self.cac = 1, 1
        # the CANONICAL carried symbol (colour 11, original orientation). It is
        # RE-PRESENTED fresh each step (a station transform acts on the canonical
        # symbol, exactly like 222000's fresh-scene semantics) so every transform
        # is valid and recognisable -- recolour (11->14) is a one-shot that would
        # otherwise no-op on an already-recoloured persistent symbol.
        self._symbol_canonical = [(self.car + r, self.cac + c, SYMBOL_COLOUR)
                                  for (r, c) in s_offs]
        self.symbol_cells = list(self._symbol_canonical)
        # distractors: distinct colours, random anchors, own offsets.
        self.distractors = []
        for i in range(n_distractors):
            d_name = rng.choice(list(CORPUS.keys()))
            d_offs, _ = CORPUS[d_name]
            dh = max(r for r, c in d_offs) + 1
            dw = max(c for r, c in d_offs) + 1
            dr = int(rng.integers(2, n - 4 - dh))
            dc = int(rng.integers(2, n - 8 - dw))
            self.distractors.append({"offs": d_offs, "colour": DISTRACTOR_COLOURS[i % len(DISTRACTOR_COLOURS)],
                                     "r": dr, "c": dc})

    # -- rendering -----------------------------------------------------------
    def grid(self):
        g = np.zeros((self.n, self.n), dtype=np.int32)
        for (r, c) in self.furn:
            g[r, c] = FURN
        for d in self.distractors:
            for (r, c) in d["offs"]:
                rr, cc = d["r"] + r, d["c"] + c
                if 0 <= rr < self.n and 0 <= cc < self.n:
                    g[rr, cc] = d["colour"]
        for (r, c, v) in self.symbol_cells:
            if 0 <= r < self.n and 0 <= c < self.n:
                g[r, c] = v
        for (r, c) in self.a_offs:
            rr, cc = self.ar + r, self.ac + c
            if 0 <= rr < self.n and 0 <= cc < self.n:
                g[rr, cc] = AVATAR_COLOUR
        return g

    _WALK = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]

    def _walk_distractors(self):
        for d in self.distractors:
            dr, dc = self._WALK[int(self.rng.integers(0, len(self._WALK)))]
            nr, nc = d["r"] + dr, d["c"] + dc
            dh = max(r for r, c in d["offs"]) + 1
            dw = max(c for r, c in d["offs"]) + 1
            if 2 <= nr <= self.n - 2 - dh and 2 <= nc <= self.n - 2 - dw:
                d["r"], d["c"] = nr, nc

    def rule_only_next(self, action):
        """The flash-free, distractor-STATIC next frame: apply ONLY the rule
        object's transform to the current grid (non-mutating). This isolates the
        MECHANIC for the held-out change-set F1 probe -- the model predicts the
        rule object's transform, and distractor motion is unmodellable clutter, so
        the probe target must be the rule alone. WORLD PHYSICS."""
        g = self.grid()
        out = g.copy()
        if action in PC._MOVE:
            dr, dc = PC._MOVE[action]
            for (r, c) in self.a_offs:
                rr, cc = self.ar + r, self.ac + c
                if 0 <= rr < self.n and 0 <= cc < self.n:
                    out[rr, cc] = BG
            for (r, c) in self.a_offs:
                rr, cc = self.ar + r + dr, self.ac + c + dc
                if 0 <= rr < self.n and 0 <= cc < self.n:
                    out[rr, cc] = AVATAR_COLOUR
        else:
            fam, param = PC._XFORM[action]
            sym = list(self._symbol_canonical)
            mr = min(r for r, c, v in sym); mc = min(c for r, c, v in sym)
            after = _reanchor(apply_transform(sym, fam, param), mr, mc)
            for (r, c, v) in sym:
                if 0 <= r < self.n and 0 <= c < self.n:
                    out[r, c] = BG
            for (r, c, v) in after:
                if 0 <= r < self.n and 0 <= c < self.n:
                    out[r, c] = v
        return g, out

    def step(self, action, n_flash=5):
        """Apply the action to the arena and return
        (prev_grid, next_grid, flash_cells, rule_centroid) -- BOTH colour grids are
        FLASH-FREE.

        The flash is a pure LUMINANCE transient (a glow on background cells
        adjacent to the rule object's new location) that the ONSET eye detects but
        that does NOT alter the discrete colour grid. This is the load-bearing
        design choice that keeps the comparison honest: the COLOUR grid (the
        content both arms decode + score on) is identical whether or not there is
        a flash, so the blind arm is NEVER confused by the flash -- its only
        problem is the distractor clutter. At n_distractors=0 the colour grid is a
        clean 222000-style single-object scene, so blind's mode-colour localises
        perfectly and the flash gives NO advantage (the anti-rig prediction). The
        flash is returned as `flash_cells` (the luminance-glow overlay the onset
        eye boosts), NEVER written into the colour grid -- it is a POINTER
        (where/when), not content (what)."""
        # re-present the canonical carried symbol so prev shows it un-transformed
        # (every station transform acts on the canonical symbol -- fresh-scene
        # semantics for the symbol while the avatar roams cumulatively).
        self.symbol_cells = list(self._symbol_canonical)
        prev = self.grid()
        # advance the persistent world: distractors walk, avatar/symbol transform.
        # WORLD PHYSICS (the arena is ground truth; it may read the _MOVE/_XFORM
        # tables exactly as 222000's world_next does -- the AGENT never does).
        self._walk_distractors()
        if action in PC._MOVE:
            dr, dc = PC._MOVE[action]
            self.ar += dr
            self.ac += dc
            obj_cells = [(self.ar + r, self.ac + c) for (r, c) in self.a_offs]
        else:
            fam, param = PC._XFORM[action]
            sym = list(self._symbol_canonical)     # re-present the canonical symbol
            mr = min(r for r, c, v in sym); mc = min(c for r, c, v in sym)
            self.symbol_cells = _reanchor(apply_transform(sym, fam, param), mr, mc)
            obj_cells = [(r, c) for (r, c, v) in self.symbol_cells]
        nxt = self.grid()   # persistent next frame (flash-free)
        # a small transient flash HALO on background cells adjacent to the rule
        # object's new location (non-occluding), nearest its centroid.
        obj = [(r, c) for (r, c) in obj_cells if 0 <= r < self.n and 0 <= c < self.n]
        if obj:
            oc_r = float(np.mean([r for r, c in obj]))
            oc_c = float(np.mean([c for r, c in obj]))
        else:
            oc_r = oc_c = 0.0
        border = set()
        for (r, c) in obj:
            for (fr, fc) in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1),
                             (r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)):
                if 0 <= fr < self.n and 0 <= fc < self.n and nxt[fr, fc] == BG:
                    border.add((fr, fc))
        border = sorted(border, key=lambda rc: (rc[0] - oc_r) ** 2 + (rc[1] - oc_c) ** 2)
        flash_cells = border[:n_flash]
        # NOTE: the flash is NOT written into `nxt` -- it is a luminance-only
        # pointer returned separately. The colour grid stays flash-free.
        if flash_cells:
            fr = float(np.mean([r for r, c in flash_cells]))
            fc = float(np.mean([c for r, c in flash_cells]))
        else:
            fr, fc = oc_r, oc_c
        return prev, nxt, flash_cells, (fr, fc)


# ============================================================================
# ONSET DRIVER (the REAL GraphEye 2-D onset stream) — flash detection
# ============================================================================
class OnsetEye:
    """A thin wrapper over the existing GraphEye 2-D onset stream. NOT a bespoke
    flash detector -- the same async onset machinery (photon_transduce_onset Rust
    kernel + retinal_onset_2d seed) that serves Doom / the photon eye. Detects
    transient brightenings that depart the adapting floor by a dB threshold."""

    def __init__(self, n, adapt_rate=0.3, threshold_db=6.0):
        from domains.photon_eye import GraphEye
        from domains import doom_photon_world as dpw
        self._dpw = dpw
        ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1,
               "visual_onset": True, "onset_threshold_db": threshold_db,
               "onset_refractory_epochs": 0.0}
        self.eye = GraphEye(n_az=n, n_el=n, adapt_rate=adapt_rate, context=ctx).build()
        self.inner = self.eye.substrate._inner

    def _submit(self, colour_grid, flash_cells=None):
        lm = luma(colour_grid)
        if flash_cells:
            for (r, c) in flash_cells:
                lm[r, c] = _LUMA_LUT[FLASH_COLOUR]   # the luminance glow overlay
        packets = self._dpw.packets_from_counts(
            self._dpw.photon_counts(lm, None), None)
        self.eye.submit_photons_2d(packets)
        self.inner.run_cognitive_tasks(1)
        self.inner.run_rules()
        # prune settled CognitiveTask/TaskResult nodes -- else the eye substrate
        # grows unboundedly (one task per cell per frame) and slows superlinearly.
        try:
            self.eye.prune_settled_tasks()
        except Exception:
            pass

    def adapt(self, colour_grid, frames=12):
        """Hold a static frame so the floor adapts (static field -> silence)."""
        for _ in range(frames):
            self._submit(colour_grid)
        self._clear()

    def _clear(self):
        for nid in list(self.eye.substrate.nodes("RetinalOnsetEvent")):
            self.eye.substrate.remove_node(nid)

    def _read_events(self):
        out = []
        for nid in self.eye.substrate.nodes("RetinalOnsetEvent"):
            a = self.eye.substrate.node(nid)["attrs"]
            out.append((int(a["row_index"]), int(a["column_index"]),
                        float(a["magnitude_db"])))
        return out

    def onset_events(self, colour_grid):
        """Present a frame; return [(row,col,magnitude_db)] for the onsets it
        fires (the transient brightenings that departed the adapted floor)."""
        self._clear()
        self._submit(colour_grid)
        return self._read_events()

    def onset_on_transition(self, prev_grid, nxt_grid, flash_cells, settle=2):
        """The streaming onset semantics: adapt the floor to the flash-FREE prev
        frame (settle ticks), then present the next frame WITH the luminance-flash
        overlay and read the onsets it fires. The flash is a bright luminance
        transient relative to the preceding field, so its onset dB dominates --
        exactly how the async onset stream detects a transient in a continuous
        video, not a bespoke trick. Both grids are flash-free colour grids; the
        flash lives only in the luminance overlay (`flash_cells`)."""
        for _ in range(settle):
            self._submit(prev_grid)
        self._clear()
        self._submit(nxt_grid, flash_cells=flash_cells)
        return self._read_events()

    def stop(self):
        try:
            self.eye.stop()
        except Exception:
            pass


# ============================================================================
# REGION-SELECTORS — the ONLY difference between arms
# ============================================================================
# The generators 222000's renderer (_apply_spec_to_grid/_gen_to_family) can apply.
# The sd-loop's DimInfer can also propose exotic generators (cycle4/scale2/...);
# a spec carrying one is not renderable by the 222000 machinery, so it is treated
# as unrecognised (never a decision -- a mechanical capability guard that keeps
# both arms inside the identical 222000 render path). Applies to BOTH arms.
_RENDERABLE_GENS = {"", "rotation90", "reflection_c", "reflection_r"}


def _renderable(spec):
    return spec is not None and (spec.get("gen") or "") in _RENDERABLE_GENS


def discover_blind(prev, nxt):
    """BLIND (the 222000 control): region = mode non-bg colour over ALL changed
    cells. Amid clutter this lands on whichever object has the most changed cells
    -- often a distractor. Reuses 222000's discover_spec verbatim (+ the renderable
    guard both arms share)."""
    spec = PC.discover_spec(prev, nxt)
    return spec if _renderable(spec) else None


def _window_region_spec(prev, nxt, centre, radius):
    """The region-hinted discovery: pick the region colour among changed cells
    WITHIN `radius` of `centre` (the attended flash location), then run the
    IDENTICAL 222000 sd-loop on that object. The flash is a luminance-only pointer
    (never in the colour grid), so the windowed cells are the persistent rule
    object -- the pointer localises, the sd-loop supplies the content."""
    prev = np.asarray(prev); nxt = np.asarray(nxt)
    diff = prev != nxt
    if not diff.any():
        return None
    cr, cc = centre
    rows, cols = np.where(diff)
    inwin = (np.abs(rows - cr) <= radius) & (np.abs(cols - cc) <= radius)
    if not inwin.any():
        return None
    cand_cols = cols[inwin]
    cand_rows = rows[inwin]
    # region-colour vote among the windowed changed cells.
    before_vals = [int(prev[r, c]) for r, c in zip(cand_rows, cand_cols)]
    after_vals = [int(nxt[r, c]) for r, c in zip(cand_rows, cand_cols)]
    def _mode(vals):
        vv = [v for v in vals if v != BG]
        return Counter(vv).most_common(1)[0][0] if vv else None
    before_colour = _mode(before_vals)
    after_colour = _mode(after_vals)
    if before_colour is None:
        before_colour = after_colour
    if after_colour is None:
        after_colour = before_colour
    if before_colour is None:
        return None
    before_obj = _grid_object(prev, before_colour)
    after_obj = _grid_object(nxt, after_colour)
    return _spec_from_objs(prev, nxt, before_obj, after_obj, before_colour)


def _spec_from_objs(prev, nxt, before_obj, after_obj, before_colour):
    """Run the IDENTICAL 222000 sd-loop on the chosen objects and build the stored
    spec (same key convention as 222000's discover_spec)."""
    spec = _recognise_transform(before_obj, after_obj)
    if spec is None or (spec.get("gen") or "") not in _RENDERABLE_GENS:
        return None
    gen, k, dr, dc, subst = spec["gen"], spec["k"], spec["dr"], spec["dc"], spec["subst"]
    subst_tok = ",".join(f"{a}>{b}" for a, b in sorted(subst.items()))
    if gen:
        key = f"{gen}:{k}" + (f"|subst:{subst_tok}" if subst_tok else "")
        store_dr = store_dc = 0
    elif subst and dr == 0 and dc == 0:
        key = f"subst:{subst_tok}"
        store_dr = store_dc = 0
    elif dr != 0 or dc != 0:
        key = f"shift:{dr}:{dc}" + (f"|subst:{subst_tok}" if subst_tok else "")
        store_dr, store_dc = dr, dc
    else:
        return None
    return {"key": key, "region_colour": int(before_colour), "gen": gen or "",
            "k": int(k), "dr": int(store_dr), "dc": int(store_dc), "subst": subst_tok}


def discover_flash_separate(prev, nxt, centre, radius=2):
    """FLASH as POINTER: use the attended flash location to WINDOW the region and
    decode the PERSISTENT rule object there with the identical 222000 sd-loop. The
    flash localises; the sd-loop supplies the content."""
    return _window_region_spec(prev, nxt, centre, radius)


# ============================================================================
# THE FLASH-GUIDED AGENT — reuses 222000's Percell + pc_* rules, adds the
# fg_pick_flash graph attention rule (Argmax onset magnitude).
# ============================================================================
def _load_flash_rules(agent):
    from domains.ls20_flash_seed import RULES as FLASH_RULES
    for r in FLASH_RULES:
        agent.n.add_rule(r)
    agent.n.set_attr(agent.g, "flash_on", 1.0)
    agent.n.set_attr(agent.g, "flash_row", 0.0)
    agent.n.set_attr(agent.g, "flash_col", 0.0)
    agent.n.set_attr(agent.g, "flash_mag", 0.0)


class FlashAgent:
    """Wraps a 222000 Percell (identical pc_* rules + sd-loop) and adds the
    graph-native flash attention. The adapter copies onset events into the agent
    graph; the fg_pick_flash RULE (Argmax magnitude_db) decides the attended
    location; the adapter reads it back and windows the region for the sd-loop.
    The transform is discovered by the IDENTICAL 222000 machinery."""

    def __init__(self, arm="flash_separate", radius=2):
        self.pc = Percell()
        self.arm = arm
        self.radius = radius
        if arm.startswith("flash"):
            _load_flash_rules(self.pc)

    # -- graph-native flash attention ---------------------------------------
    def attend_flash(self, onset_events):
        """Copy onset events into the agent graph as FlashOnset nodes; tick the
        fg_pick_flash rule (Argmax magnitude) to set the attended location; read
        it back. Returns (row, col) or None if no onset. The DECISION (which onset
        is the flash) is the graph rule, not Python."""
        s, n, g = self.pc.s, self.pc.n, self.pc.g
        for nid in list(s.neighbours(g, "has_flash_onset")):
            s.remove_node(nid)
        if not onset_events:
            return None
        for (r, c, mag) in onset_events:
            fo = s.add_node("FlashOnset", {"row_index": float(r),
                                           "column_index": float(c),
                                           "magnitude_db": float(mag)})
            n.add_edge_unchecked(g, "has_flash_onset", fo)
        n.set_attr(g, "flash_mag", -1.0)
        n.set_attr(g, "phase", "attend_flash")
        n.run_rules()
        a = s.node(g)["attrs"]
        if float(a.get("flash_mag") or -1.0) < 0.0:
            return None
        return (float(a.get("flash_row")), float(a.get("flash_col")))

    # -- one observation ----------------------------------------------------
    def observe(self, action, prev, nxt, centre_hint):
        """Discover the spec via the arm's region-selector, stamp the perception
        facts, and drive the IDENTICAL 222000 mint/confirm/revise machinery. Both
        colour grids are flash-free; the flash arms use the attended location
        (centre_hint) to window the region. The CONFLATE arm decodes the SAME
        persistent object as SEPARATE -- the pointer/content difference is in the
        PREDICTION (conflate additionally predicts the transient flash as a
        persistent change; see predict_conflate), never in the discovery."""
        if self.arm == "blind":
            spec = discover_blind(prev, nxt)
        else:  # flash_separate / flash_conflate share the windowed discovery
            spec = discover_flash_separate(prev, nxt, centre_hint, self.radius) if centre_hint else None
        if spec is None:
            spec = {"key": "unrecognised", "region_colour": 0, "gen": "",
                    "k": 0, "dr": 0, "dc": 0, "subst": ""}
        pc, g, n = self.pc, self.pc.g, self.pc.n
        n.set_attr(g, "observed_key", spec["key"])
        n.set_attr(g, "obs_region", float(spec["region_colour"]))
        n.set_attr(g, "obs_gen", spec["gen"])
        n.set_attr(g, "obs_k", float(spec["k"]))
        n.set_attr(g, "obs_dr", float(spec["dr"]))
        n.set_attr(g, "obs_dc", float(spec["dc"]))
        n.set_attr(g, "obs_subst", spec["subst"])
        n.set_attr(g, "predicted_key", "none")
        n.set_attr(g, "obs_epoch", float(pc._read("obs_epoch") or 0.0) + 1.0)
        # attend the env-dictated action (graph rule pc_attend), then the sd loop.
        pc.attend(action)
        pc._tick("predict")
        pc._tick("observe")
        pc._tick("advance")
        return spec

    # -- prediction (arm-aware) --------------------------------------------
    def predict_next(self, cur, action):
        if self.arm == "flash_conflate":
            return predict_conflate(self.pc, cur, action)
        return self.pc.predict_next(cur, action)

    def hypothesis(self, action):
        return self.pc.hypothesis(action)

    def confirmed_count(self):
        return self.pc.confirmed_count()

    def next_probe(self):
        """The 222000 curiosity pick (Argmin visits) -- shared by all arms."""
        return self.pc.probe_action()


def predict_conflate(pc, cur, action):
    """The CONFLATE arm's prediction: apply the (garbage) transform AND stamp the
    transient flash as a PERSISTENT change at the object's location. Because the
    real next frame reverts the flash, these are false-positive changes -> the
    conflate arm's change-set F1 is penalised (the pointer/content distinction is
    load-bearing)."""
    h = pc.hypothesis(action)
    base = pc.predict_next(cur, action)
    if h is None or not h.get("key") or h["key"] == "unrecognised":
        return base
    # predict the transient flash (a glow HALO on background cells adjacent to the
    # predicted object) as if it PERSISTED. The true next frame has NO flash in the
    # colour grid, so every one of these is a false-positive changed cell -> the
    # conflate arm's change-set F1 is penalised. Conflating the pointer with the
    # content is what the metric punishes.
    colour = h["region_colour"]
    obj = _grid_object(base, colour)
    g = base.copy()
    for (r, c, v) in obj:
        for (fr, fc) in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= fr < g.shape[0] and 0 <= fc < g.shape[1] and g[fr, fc] == BG:
                g[fr, fc] = FLASH_COLOUR
    return g


# ============================================================================
# DRIVERS — sample-efficiency (the headline) + held-out evaluation
# ============================================================================
def make_eval_scenes(rng, n_scenes, n, n_distractors):
    """Held-out fresh arenas for the change-set F1 probe. Uses the FLASH-FREE,
    distractor-STATIC next frame (the rule transform ONLY) so F1 measures the
    persistent mechanic, not the marker or the clutter. Returns
    [(prev, action, true_next_rule_only)]."""
    out = []
    for _ in range(n_scenes):
        ar = FlashArena(rng, n=n, n_distractors=n_distractors)
        for a in ACTIONS:
            prev, true_next = ar.rule_only_next(a)
            out.append((prev, a, true_next))
    return out


def held_out_f1(agent, eval_scenes):
    """Mean change-set strict-F1 of the agent's per-cell prediction over the probe
    set (persistence fallback for unmodelled actions). Scored on the persistent
    (flash-free) next frame -- the flash marker is never part of the target."""
    f1s = []
    for (prev, action, true_next) in eval_scenes:
        pred = agent.predict_next(prev, action)
        f1s.append(score_prediction(prev, true_next, pred)["f1_strict"])
    return float(np.mean(f1s)) if f1s else 0.0


def observations_to_converge(arm, seed, *, n=20, n_distractors=2, tau=0.9,
                             budget=500, eval_scenes=None, eye=None, eval_every=5):
    """Run the arm's flash-guided (or blind) investigation on a persistent clutter
    arena, streamed one action at a time, and return the number of OBSERVATIONS
    (world queries) until the held-out change-set strict-F1 first reaches `tau`
    (or `budget` if it never does -- right-censored). The SAMPLE-EFFICIENCY
    measurement. Both arms share the 222000 curiosity pick + confirm machinery;
    only the region-selector differs. F1 is checked every `eval_every` obs (the
    convergence count is rounded up to that grain)."""
    rng = np.random.default_rng(seed)
    agent = FlashAgent(arm=arm)
    arena = FlashArena(rng, n=n, n_distractors=n_distractors)
    own_eye = eye is None and arm.startswith("flash")
    if own_eye:
        eye = OnsetEye(n)
        eye.adapt(arena.grid())
    for t in range(1, budget + 1):
        action = agent.next_probe()
        if not action:
            action = ACTIONS[t % len(ACTIONS)]
        prev, nxt, flash_cells, rule_centroid = arena.step(action)
        centre_hint = None
        if arm.startswith("flash"):
            # perceive -> onset -> attend (graph rule Argmax magnitude). The onset
            # is computed on the transition INTO the next frame with the luminance
            # flash overlay (adapt to the flash-free prev, then present it) -- the
            # streaming async semantics. Both colour grids are flash-free.
            events = (eye.onset_on_transition(prev, nxt, flash_cells)
                      if eye is not None else [])
            centre_hint = agent.attend_flash(events)
        agent.observe(action, prev, nxt, centre_hint)
        if t % eval_every == 0 or t == budget:
            f1 = held_out_f1(agent, eval_scenes)
            if f1 >= tau:
                if own_eye:
                    eye.stop()
                return {"observations": t, "converged": True, "final_f1": f1}
    if own_eye:
        eye.stop()
    return {"observations": budget, "converged": False,
            "final_f1": held_out_f1(agent, eval_scenes)}
