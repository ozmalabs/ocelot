"""arc_ls20_percell — RUNG 222000: the mechanical host adapter + drivers for the
PER-CELL live-mechanic model. Attacks 221000's honestly-flagged residual (its
live model converged trivially on the aggregate ~52-cell change-magnitude).

The model predicts WHICH cells change and to WHAT value: `action x current-frame
-> per-cell next-frame`. Each ACTION carries a graph `Hypothesis` = a discovered
217000 `Transform{dim,delta}` (generator / k / shift deltas / subst) + the
region-selector (the object colour). ALL decisions live in the graph rules
(seeds/ls20_percell.json, built by domains/ls20_percell_seed.py). This adapter is
ONLY mechanical I/O:

  PERCEIVE  — SEE frames through the 216000 pixel eye; RECOGNISE the transform an
              observed action applied (object before->after) with the GENERAL
              217000 sd-loop (TransformDecode/DimInfer). Stamp the perception
              facts (observed_key + the applicable spec) the rules read. There is
              NO action->transform table -- the map is minted from observation.
  TICK      — drive the phase machinery (pick -> predict -> observe -> advance).
  APPLY     — read a graph-held Transform off the Hypothesis and RENDER the
              predicted next frame per-cell (the 221000 apply_transform/
              render_and_see pattern; a mechanical cross-frame map, never a
              decision).
  MEASURE   — score the prediction on the CHANGE-SET (location F1 + value-accuracy
              + strict changed-cell F1 + exact-frame match) -- a scored diagnostic,
              never fed to a decision. RAW accuracy is reported ONLY to exhibit the
              metric trap; it is never the gate.

The world reuses worlds/arc's pixel eye + cells_to_signature and worlds/
arc_ls20_scenario's transforms/recogniser. In-frame values are INTEGER (the
integer lattice); the Transform is the CROSS-FRAME map (a float shift/rotation
lives in the map, never in a frame's cells).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import cells_to_signature, SHAPE_DIM_TYPES  # noqa: E402
from worlds.arc_ls20_scenario import CORPUS, RECOLOUR_MAP, apply_transform, _reposition  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from domains.ls20_percell_seed import RULES  # noqa: E402

DT = SHAPE_DIM_TYPES
BG = 0
FURN = 4          # real ls20 palette wall value ("dark-grey field/walls")
AVATAR_COLOUR = 9
SYMBOL_COLOUR = 11

# The action vocabulary — the mechanic to be understood. Ground-truth (family,
# param) is world PHYSICS; the agent does NOT read it, it LEARNS the map.
ACTIONS = ["move_up", "move_down", "move_left", "move_right",
           "rot1", "rot2", "rot3", "refl_c", "refl_r", "recolour"]

_MOVE = {"move_up": (-1, 0), "move_down": (1, 0),
         "move_left": (0, -1), "move_right": (0, 1)}
_XFORM = {"rot1": ("rotate", 1), "rot2": ("rotate", 2), "rot3": ("rotate", 3),
          "refl_c": ("reflect", "c"), "refl_r": ("reflect", "r"),
          "recolour": ("recolour", {SYMBOL_COLOUR: RECOLOUR_MAP[SYMBOL_COLOUR]})}


# ============================================================================
# SCENE + WORLD PHYSICS (ground truth; the agent never reads these tables)
# ============================================================================
def _furniture(H, W):
    """A fixed static field the agent must NOT predict changing: a vertical wall
    (value 4) at col W-24, rows 10..H-14. Static -> never in any change-set; it
    only pads raw accuracy toward 100% (exhibiting the trap)."""
    col = W - 24
    return {(r, col) for r in range(10, H - 14)}


def make_scene(rng, H=64, W=64):
    """One ls20-shaped frame: static furniture + an avatar polyomino (colour 9) in
    a clear band + a carried symbol polyomino (colour 11) at a fixed top-left
    anchor. Positions are random (the avatar roams; the eval must apply a learned
    transform to the CURRENT position, not a memorised one)."""
    furn = _furniture(H, W)
    a_name = rng.choice(list(CORPUS.keys()))
    a_offs, _ = CORPUS[a_name]
    ah = max(r for r, c in a_offs) + 1
    aw = max(c for r, c in a_offs) + 1
    # avatar band: rows [20, H-15), cols [10, W-30) -- clear of furniture + carry.
    ar = int(rng.integers(20, H - 15 - ah))
    ac = int(rng.integers(10, W - 30 - aw))
    avatar = [(ar + r, ac + c, AVATAR_COLOUR) for (r, c) in a_offs]
    s_name = rng.choice(list(CORPUS.keys()))
    s_offs, _ = CORPUS[s_name]
    car, cac = 2, 2       # fixed carry anchor (top-left)
    symbol = [(car + r, cac + c, SYMBOL_COLOUR) for (r, c) in s_offs]
    return {"H": H, "W": W, "furn": furn, "avatar": avatar, "symbol": symbol,
            "avatar_anchor": (ar, ac), "carry_anchor": (car, cac)}


def scene_grid(scene):
    g = np.zeros((scene["H"], scene["W"]), dtype=np.int32)
    for (r, c) in scene["furn"]:
        g[r, c] = FURN
    for (r, c, v) in scene["symbol"]:
        g[r, c] = v
    for (r, c, v) in scene["avatar"]:
        g[r, c] = v
    return g


def _reanchor(cells, ar, ac):
    """Reposition `cells` to the origin then shift to (ar, ac) -- the world's
    in-place 'top-left preserved' convention (and the model's, discovered)."""
    rp = _reposition(cells)
    return [(r + ar, c + ac, v) for (r, c, v) in rp]


def world_next(scene, cur_grid, action):
    """World PHYSICS: apply an action to the current frame -> the next frame.
    Movement translates the avatar over background; a station transform replaces
    the carried symbol by its transformed self, anchored at its current top-left.
    Ground truth -- the agent never reads this."""
    g = cur_grid.copy()
    if action in _MOVE:
        dr, dc = _MOVE[action]
        av = [(r, c, v) for (r, c, v) in scene["avatar"]]
        for (r, c, v) in av:                      # erase avatar -> background
            g[r, c] = BG
        for (r, c, v) in av:                      # redraw at shifted position
            g[r + dr, c + dc] = v
    else:
        fam, param = _XFORM[action]
        sym = scene["symbol"]
        mr = min(r for r, c, v in sym); mc = min(c for r, c, v in sym)
        after = _reanchor(apply_transform(sym, fam, param), mr, mc)
        for (r, c, v) in sym:                      # erase symbol -> background
            g[r, c] = BG
        for (r, c, v) in after:                    # redraw transformed
            if 0 <= r < scene["H"] and 0 <= c < scene["W"]:
                g[r, c] = v
    return g


# ============================================================================
# DISCOVERY (the GENERAL 217000 sd-loop) — recognise the observed Transform
# ============================================================================
def _parse_v(tok):
    return int(tok[1:]) if isinstance(tok, str) and tok.startswith("v") else int(tok)


def _recognise_transform(before_obj, after_obj):
    """Run the GENERAL TransformDecode/DimInfer on the two SEEN objects' absolute-
    coordinate signatures. Returns the transform node's applicable spec:
    {gen, k, shift:(dr,dc), subst:{int:int}} or None if not recognised.

    NOTHING ls20-specific: this is the same op 217000 measured for Omniglot / ARC
    transforms. The sd-loop exposes generator/k for rotation/reflection, shift
    `deltas` on the coordinate dims for translation, and a `subst` on the value
    dim for recolour."""
    base_sig = cells_to_signature(before_obj)
    goal_sig = cells_to_signature(after_obj)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.add_node("ShapeSignature", {"name": "sym", "signature": json.dumps(base_sig),
                                  "kind": "faculty", "faculty": "sym", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal_sig, "key": ["probe"],
                                     "status": "decoded", "residual": goal_sig,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    if at.get("status") not in ("recognized_transformed",) or at.get("covered_by") != "sym":
        return None
    for n in s.neighbours(obs, "has_transform"):
        t = s.node(n)["attrs"]
        gen = t.get("generator")
        k = int(t.get("k") or 1)
        dr = dc = 0
        subst = {}
        for tr in (t.get("transforms") or []):
            if tr.get("kind") == "shift":
                if tr.get("dim") == 1:
                    dr = int(tr.get("delta") or 0)
                elif tr.get("dim") == 2:
                    dc = int(tr.get("delta") or 0)
            elif tr.get("kind") == "subst":
                for pair in (tr.get("delta") or []):
                    a, b = pair
                    subst[_parse_v(a)] = _parse_v(b)
        return {"gen": gen, "k": k, "dr": dr, "dc": dc, "subst": subst}
    return None


def _grid_object(grid, colour):
    """All cells of `colour` in the grid (the object -- colours are unique per
    object, so a colour IS a region-selector). Mechanical read."""
    rows, cols = np.where(grid == colour)
    return [(int(r), int(c), int(colour)) for r, c in zip(rows, cols)]


def discover_spec(cur_grid, next_grid, max_obj_cells=None):
    """The agent's discovery from ONE observed (before, after) frame pair:
    identify the changed region's colour (region-selector), extract the object
    before/after, RECOGNISE the transform (general sd-loop), and build the stored
    spec: {key, region_colour, gen, k, dr, dc, subst}. Returns None on no change.

    key is the STABLE categorical mechanic (used by the confirm/revise rules): for
    an in-place generator the absolute anchor is EXCLUDED (re-derived at predict
    from the current object); for a translate the RELATIVE shift is included; for
    a recolour the substitution. Nothing here reads a ground-truth table."""
    diff = cur_grid != next_grid
    if not diff.any():
        return None
    cur_ch = cur_grid[diff]
    nxt_ch = next_grid[diff]
    before_colour = _mode_nonbg(cur_ch)
    after_colour = _mode_nonbg(nxt_ch)
    if before_colour is None:
        before_colour = after_colour
    if after_colour is None:
        after_colour = before_colour
    before_obj = _grid_object(cur_grid, before_colour)
    after_obj = _grid_object(next_grid, after_colour)
    # Perception guard (live only; default None = offline byte-identical): do not
    # attempt shape recognition on an implausibly large blob (a whole dense field
    # is not one transforming object). A mechanical size check, not a decision.
    if max_obj_cells is not None and (len(before_obj) > max_obj_cells or
                                      len(after_obj) > max_obj_cells):
        return None
    spec = _recognise_transform(before_obj, after_obj)
    if spec is None:
        return None
    gen, k, dr, dc, subst = spec["gen"], spec["k"], spec["dr"], spec["dc"], spec["subst"]
    subst_tok = ",".join(f"{a}>{b}" for a, b in sorted(subst.items()))
    if gen:                                   # in-place generator: anchor excluded
        key = f"{gen}:{k}" + (f"|subst:{subst_tok}" if subst_tok else "")
        store_dr = store_dc = 0
    elif subst and dr == 0 and dc == 0:       # recolour
        key = f"subst:{subst_tok}"
        store_dr = store_dc = 0
    elif dr != 0 or dc != 0:                  # translate
        key = f"shift:{dr}:{dc}" + (f"|subst:{subst_tok}" if subst_tok else "")
        store_dr, store_dc = dr, dc
    else:
        return None                           # identity / unrecognised
    return {"key": key, "region_colour": int(before_colour), "gen": gen or "",
            "k": int(k), "dr": int(store_dr), "dc": int(store_dc),
            "subst": subst_tok}


def _mode_nonbg(vals):
    vals = [int(v) for v in vals if int(v) != BG]
    if not vals:
        return None
    from collections import Counter
    return Counter(vals).most_common(1)[0][0]


# ============================================================================
# APPLY (render a graph-held Transform to the CURRENT frame) — mechanical
# ============================================================================
def _apply_spec_to_grid(cur_grid, spec):
    """Apply a stored Transform spec to the current frame: select the object of
    `region_colour`, transform it (generator in place at its own top-left, or a
    relative shift, then a recolour subst), erase the old object, draw the new.
    Returns the predicted next grid. A mechanical cross-frame render -- the 221000
    apply_transform/render_and_see pattern, no decision."""
    H, W = cur_grid.shape
    colour = spec["region_colour"]
    obj = _grid_object(cur_grid, colour)
    if not obj:
        return cur_grid.copy()
    if spec["gen"]:
        mr = min(r for r, c, v in obj); mc = min(c for r, c, v in obj)
        fam, param = _gen_to_family(spec["gen"], spec["k"])
        after = _reanchor(apply_transform(obj, fam, param), mr, mc)
    else:
        after = [(r + spec["dr"], c + spec["dc"], v) for (r, c, v) in obj]
    if spec["subst"]:
        smap = {}
        for pair in spec["subst"].split(","):
            if ">" in pair:
                a, b = pair.split(">")
                smap[int(a)] = int(b)
        after = [(r, c, smap.get(v, v)) for (r, c, v) in after]
    g = cur_grid.copy()
    for (r, c, v) in obj:                       # erase old object -> background
        g[r, c] = BG
    for (r, c, v) in after:                     # draw transformed object
        if 0 <= r < H and 0 <= c < W:
            g[r, c] = v
    return g


def _gen_to_family(gen, k):
    if gen == "rotation90":
        return ("rotate", k)
    if gen == "reflection_c":
        return ("reflect", "c")
    if gen == "reflection_r":
        return ("reflect", "r")
    raise ValueError(gen)


# ============================================================================
# METRICS — scored on the CHANGE-SET (never raw accuracy)
# ============================================================================
def score_prediction(cur, true_next, pred_next):
    """Change-set metrics. location F1 (predicted-changed vs actually-changed
    cells), value-accuracy on the actually-changed cells, strict changed-cell F1
    (TP = actually changed AND correct value), exact-frame match, and raw per-cell
    accuracy (reported ONLY to exhibit the trap -- never the gate)."""
    cur = np.asarray(cur); true_next = np.asarray(true_next); pred_next = np.asarray(pred_next)
    actual = (cur != true_next)
    pred = (cur != pred_next)
    na = int(actual.sum()); npch = int(pred.sum())
    tp = int((actual & pred).sum())
    prec = tp / npch if npch else (1.0 if na == 0 else 0.0)
    rec = tp / na if na else 1.0
    f1_loc = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    val_acc = (float(((pred_next == true_next) & actual).sum()) / na) if na else 1.0
    correct = (pred_next == true_next)
    tp_s = int((actual & pred & correct).sum())
    prec_s = tp_s / npch if npch else (1.0 if na == 0 else 0.0)
    rec_s = tp_s / na if na else 1.0
    f1_strict = 2 * prec_s * rec_s / (prec_s + rec_s) if (prec_s + rec_s) else 0.0
    return {"f1_loc": f1_loc, "prec_loc": prec, "rec_loc": rec,
            "val_acc": val_acc, "f1_strict": f1_strict,
            "exact": 1.0 if np.array_equal(pred_next, true_next) else 0.0,
            "raw_acc": float(correct.mean()), "n_changed": na}


# ============================================================================
# THE AGENT (graph-native model; adapter = perceive/apply/measure)
# ============================================================================
class Percell:
    """Holds the game + Action nodes + the ls20_percell rules. The adapter stamps
    perception facts and drives the phase machinery; the RULES maintain the model
    (mint/confirm/revise + the curiosity pick). Reading a Hypothesis spec back to
    render a prediction is mechanical, like reading a waypoint."""

    def __init__(self):
        self.s, self.ag = boot_core()
        self.n = rf._native_eval2(self.s)
        for r in RULES:
            self.n.add_rule(r)
        self.g = self.s.add_node("Game", {
            "percell_on": 1.0, "arm": "percell", "phase": "idle",
            "probe_action": "", "observed_key": "", "predicted_key": "none",
            "obs_region": 0.0, "obs_gen": "", "obs_k": 0.0,
            "obs_dr": 0.0, "obs_dc": 0.0, "obs_subst": "", "obs_epoch": 0.0,
            "attend_action": ""})
        self.actions = {}
        for name in ACTIONS:
            an = self.s.add_node("Action", {"name": name, "visits": 0.0})
            self.n.add_edge_unchecked(self.g, "has_action", an)
            self.actions[name] = an

    def _tick(self, phase):
        self.n.set_attr(self.g, "phase", phase)
        self.n.run_rules()

    def _read(self, key):
        return self.s.node(self.g)["attrs"].get(key)

    def probe_action(self):
        self._tick("pick")
        return self._read("probe_action") or ""

    def probing(self):
        for an in self.s.neighbours(self.g, "probing"):
            return an
        return None

    def attend(self, action):
        """Point the `probing` attention at `action` via the graph rule pc_attend
        (used on the LIVE path where the ENVIRONMENT dictates the action, not the
        curiosity pick). Setting attend_action + ticking is mechanical; the rule
        does the attach. Offline uses probe_action (the curiosity pick) instead."""
        self.n.set_attr(self.g, "attend_action", action)
        self._tick("attend")

    def observe(self, action, cur_grid, next_grid, max_obj_cells=None, spec=None):
        """One investigation observation of `action`: discover the transform spec
        (sd-loop), stamp the perception facts, predict (from the model), then the
        residual mints/confirms/revises. Returns (predicted_key, observed_key).
        `max_obj_cells` (live only) guards against recognising a huge blob;
        default None keeps the offline path byte-identical. `spec` (live only)
        supplies a PRE-COMPUTED transform spec from a local-region tracker,
        bypassing the whole-frame discover_spec (which cannot isolate the moving
        object on dense real frames); when None the offline discovery runs."""
        if spec is None:
            spec = discover_spec(cur_grid, next_grid, max_obj_cells=max_obj_cells)
        if spec is None:
            spec = {"key": "unrecognised", "region_colour": 0, "gen": "",
                    "k": 0, "dr": 0, "dc": 0, "subst": ""}
        self.n.set_attr(self.g, "observed_key", spec["key"])
        self.n.set_attr(self.g, "obs_region", float(spec["region_colour"]))
        self.n.set_attr(self.g, "obs_gen", spec["gen"])
        self.n.set_attr(self.g, "obs_k", float(spec["k"]))
        self.n.set_attr(self.g, "obs_dr", float(spec["dr"]))
        self.n.set_attr(self.g, "obs_dc", float(spec["dc"]))
        self.n.set_attr(self.g, "obs_subst", spec["subst"])
        self.n.set_attr(self.g, "predicted_key", "none")
        # bump the observation epoch so confirm fires exactly once this observation
        self.n.set_attr(self.g, "obs_epoch", float(self._read("obs_epoch") or 0.0) + 1.0)
        self._tick("predict")
        predicted = self._read("predicted_key")
        self._tick("observe")
        self._tick("advance")
        return predicted, spec["key"]

    def hypothesis(self, action):
        """Read the graph Hypothesis spec for `action` ('' if unmodelled). A
        mechanical graph read (like reading a waypoint) the adapter uses to render
        the prediction."""
        an = self.actions.get(action)
        if an is None:
            return None
        for h in self.s.neighbours(an, "has_hyp"):
            a = self.s.node(h)["attrs"]
            return {"key": a.get("key") or "", "region_colour": int(a.get("region_colour") or 0),
                    "gen": a.get("gen") or "", "k": int(a.get("k") or 0),
                    "dr": int(a.get("dr") or 0), "dc": int(a.get("dc") or 0),
                    "subst": a.get("subst") or "", "conf": float(a.get("conf") or 0)}
        return None

    def predict_next(self, cur_grid, action):
        """Predict the per-cell next frame for `action` from the LEARNED model.
        Modelled -> apply the graph-held Transform; unmodelled -> persistence
        fallback (predict no change)."""
        h = self.hypothesis(action)
        if h is None or not h["key"] or h["key"] == "unrecognised":
            return cur_grid.copy()
        return _apply_spec_to_grid(cur_grid, h)

    def model(self):
        return {a: self.hypothesis(a) for a in ACTIONS}

    def confirmed_count(self):
        return sum(1 for a in ACTIONS
                   if (self.hypothesis(a) or {}).get("conf", 0) >= 2.0)


# ============================================================================
# DRIVERS — investigate (learn) + evaluate (held-out change-set teeth)
# ============================================================================
def investigate(agent, rng, cycles=None, probe_scenes=None):
    """Curiosity-driven investigation: each cycle the RULE picks the least-observed
    action; the world gives ONE (cur, next) observation on a fresh scene; the
    residual mints/confirms/revises the Hypothesis. Records the per-cycle CHANGE-SET
    surprise (mean strict-F1 error over a fixed probe set, partial model with a
    persistence fallback for unmodelled actions) -- the convergence staircase."""
    cycles = cycles or (2 * len(ACTIONS))
    curve = []
    for _t in range(cycles):
        action = agent.probe_action()
        if not action:
            break
        scene = make_scene(rng)
        cur = scene_grid(scene)
        nxt = world_next(scene, cur, action)
        agent.observe(action, cur, nxt)
        if probe_scenes is not None:
            curve.append(_convergence_point(agent, probe_scenes))
    return curve


def _convergence_point(agent, probe_scenes):
    """Mean strict-F1 SURPRISE (1 - f1_strict) over the probe set with the CURRENT
    partial model (unmodelled action -> persistence)."""
    errs = []
    for scene, action in probe_scenes:
        cur = scene_grid(scene)
        true = world_next(scene, cur, action)
        pred = agent.predict_next(cur, action)
        errs.append(1.0 - score_prediction(cur, true, pred)["f1_strict"])
    return float(np.mean(errs)) if errs else 1.0


def make_probe_set(rng, n_scenes):
    return [(make_scene(rng), a) for _ in range(n_scenes) for a in ACTIONS]


# ---- the three arms scored on held-out triples -------------------------------
def learned_predict(agent, scene, action):
    cur = scene_grid(scene)
    return _apply_spec_to_grid_or_persist(agent, cur, action)


def _apply_spec_to_grid_or_persist(agent, cur, action):
    return agent.predict_next(cur, action)


def persistence_predict(cur):
    """NULL (a): predict next = current (predicts NO changed cell)."""
    return cur.copy()


class AggregateCountNull:
    """NULL (b): the 221000 aggregate model, on the change-set. Learns the per-
    action mean CHANGED-CELL COUNT (the `_changed_fraction` x total) during the
    same investigation, then predicts THAT MANY cells changing at UNINFORMED
    (seeded-random) locations, to the per-action modal new value. Right count,
    wrong locations -> low change-set F1."""

    def __init__(self, seed=0):
        self.count = {}      # action -> mean changed-cell count
        self._n = {}
        self.newval = {}     # action -> modal new (changed-to) value
        self.rng = np.random.default_rng(seed)

    def observe(self, action, cur, nxt):
        diff = (cur != nxt)
        c = int(diff.sum())
        n = self._n.get(action, 0) + 1
        self.count[action] = self.count.get(action, 0.0) + (c - self.count.get(action, 0.0)) / n
        self._n[action] = n
        vals = nxt[diff]
        v = _mode_nonbg(vals)
        if v is not None:
            self.newval[action] = v

    def predict(self, cur, action):
        H, W = cur.shape
        n = int(round(self.count.get(action, 0.0)))
        g = cur.copy()
        if n <= 0:
            return g
        idx = self.rng.choice(H * W, size=min(n, H * W), replace=False)
        v = self.newval.get(action, 1)
        flat = g.reshape(-1)
        flat[idx] = v            # right count, uninformed locations + value
        return g
