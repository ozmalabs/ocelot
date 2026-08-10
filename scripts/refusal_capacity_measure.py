#!/usr/bin/env python3
"""REFUSAL CAPACITY — THE CONFIRMATORY MEASUREMENT.

Pre-registration `VISION_REFUSAL_CAPACITY_PREREG.md`, committed `eac0bdd1`
before any number here.  Run from the gamma-substrate dir:

    PYTHONPATH=runners/dsl/python:. python3 scripts/refusal_capacity_measure.py

WHAT IS COUNTED, and why it is the right unit (PROTOCOL 3, declared in the
pre-registration and repeated here because a runner that does not say what it
counts is a rumour):

    Delta_M = P(null | UNEXPLAINABLE) - P(null | EXPLAINABLE)

over MATCHED PAIRS that are identical in every guard-visible property (arity,
frame count, cell count, non-emptiness, types).  A refusal RATE is a property
of the stimulus DISTRIBUTION; Delta is a property of the MECHANISM.

The engine's own `checked` counter is NOT the classifier -- it counts CODEBOOK
candidates only, so a fully stimulus-determined refusal can read `checked = 0`.
It is recorded as a COST.

Every confirmatory draw is materialised HERE from an explicit `range` bound to a
module-level constant, so `scripts/seed_audit.py` can RESOLVE every seed
statically instead of reporting an unknown sink.
"""
from __future__ import annotations

import json
import math
import time

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
import substrate_rs as srs                            # noqa: E402

# --- the engine this rung's numbers are attributed to (PROTOCOL 10.1 rule 1).
# Printed from INSIDE the measuring process and compared; divergence ABORTS.
EXPECT_ENGINE = "9931e144d19b"
_line = provenance_line()
print(_line)
if EXPECT_ENGINE not in _line:
    raise SystemExit(f"** WRONG ENGINE ** expected {EXPECT_ENGINE}: {_line}")

# --------------------------------------------------------------------------- #
#  SEEDS -- every confirmatory draw, materialised from an explicit range.
# --------------------------------------------------------------------------- #
N_PAIRS = 200
SEQ_LO, SEQ_HI = 106000, 106200          # sequence + goal families
DEPTH_LO, DEPTH_HI = 106200, 106400      # P2: DepthInfer two-layer arm
BLINK_LO, BLINK_HI = 106400, 106600      # P3: BlinkBridge gap arm
SEQ_SEEDS = list(range(SEQ_LO, SEQ_HI))
DEPTH_SEEDS = list(range(DEPTH_LO, DEPTH_HI))
BLINK_SEEDS = list(range(BLINK_LO, BLINK_HI))

# --- stimulus configuration (construction only, never a verdict threshold) ---
DOT, H, W, ROW, BG, FG = 4, 24, 200, 8, 0, 255
DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
NCELL = len(BASE)


# --------------------------------------------------------------------------- #
#  world: the adapter renders and translates.  It decides nothing.
# --------------------------------------------------------------------------- #
def render(col):
    f = np.full((H, W), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


def cells_fig(frame):
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame != modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def seq(cols):
    return [([] if c is None else cells_fig(render(c))) for c in cols]


def lin(M, base=BASE):
    rs = [c[1] for c in base]; cs = [c[2] for c in base]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in base:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0] * r0 + M[1] * c0, M[2] * r0 + M[3] * c0, v])
    return out


def shift(dr, dc, base=BASE):
    return [["cell", r + dr, c + dc, v] for _, r, c, v in base]


def rand_cells(rng, n=NCELL, span=10):
    """An UNEXPLAINABLE cell set: same cardinality, same predicate, same value
    as BASE -- identical in every guard-visible property.  Only the ARRANGEMENT
    differs, which is precisely what the mechanism claims to test."""
    seen = set()
    while len(seen) < n:
        seen.add((int(rng.integers(0, span)), int(rng.integers(0, span))))
    return [["cell", r, c, "red"] for r, c in sorted(seen)]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def diff_ci(k1, n1, k0, n0):
    """Newcombe's method: the CI for a difference of two proportions, built
    from the two Wilson intervals.  No normal approximation at the extremes,
    which is the regime every arm here lands in."""
    p1, l1, u1 = wilson(k1, n1)
    p0, l0, u0 = wilson(k0, n0)
    d = p1 - p0
    lo = d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)
    return (d, max(-1.0, lo), min(1.0, hi))


# --------------------------------------------------------------------------- #
#  substrate
# --------------------------------------------------------------------------- #
def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells_fig(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    s.add_node("ShapeSignature",
               {"name": "base_L", "signature": json.dumps(BASE),
                "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


S, AG, NATIVE = boot()


def as_dict(v):
    """The engine returns a Python DICT for a whole-verdict read (`field=""`).

    THIS FUNCTION IS WHERE THIS RUNG'S OWN INSTRUMENT DIED ONCE. Its first
    version accepted only a list/tuple of pairs and returned None for a dict,
    so EVERY mechanism read as a bare null and the whole audit reported a
    uniform, perfectly-formed, entirely fake Delta = 0. It was caught by the
    PRE-REGISTERED POSITIVE CONTROL (arm A), not by inspection."""
    if isinstance(v, dict):
        return v
    if isinstance(v, (list, tuple)):
        try:
            return {k: val for k, val in v}
        except Exception:
            return None
    return None


def ev_seq(term, frames):
    t = srs.Term(term, sequence=srs.Lit(frames), codebook_type="ShapeSignature",
                 max_b=8, field="")
    return as_dict(S.evaluate(t, {}))


GOAL_KW = {
    "ShapeDecode": dict(beam=4, max_steps=4, cand_k=4, wild="?",
                        wild_objects=False),
    "TransformDecode": dict(max_dims=4),
    "DimInfer": dict(generator_type="DimensionGenerator", max_dims=4),
    "GenInfer": dict(max_dims=4),
}


def ev_goal(term, goal):
    t = srs.Term(term, goal=srs.Lit(goal), codebook_type="ShapeSignature",
                 field="", **GOAL_KW[term])
    return as_dict(S.evaluate(t, {}))


def g(d, k):
    """Safe read: a BARE `Value::None` is itself a verdict (the shrug), and a
    runner that crashes on it has thrown away the finding."""
    return d.get(k) if isinstance(d, dict) else None


def is_null(term, d):
    """The mechanism's OWN null, read off the engine's verdict."""
    if d is None:
        return True                       # a bare Value::None -- the shrug
    if term == "ShapeDecode":
        return d.get("authored") is not True
    return d.get("explained") is not True


RESULTS = {}
COST = {}
NOTES = []


def record(name, k_u, k_e, n, cost_u=None, cost_e=None, extra=None):
    d, lo, hi = diff_ci(k_u, n, k_e, n)
    RESULTS[name] = {"n": n, "null_U": k_u, "null_E": k_e,
                     "p_U": k_u / n, "p_E": k_e / n,
                     "delta": d, "ci": [lo, hi],
                     "ci_excludes_0": (lo > 0.0 or hi < 0.0)}
    if extra:
        RESULTS[name].update(extra)
    if cost_u is not None:
        COST[name] = {"checked_U": cost_u, "checked_E": cost_e}
    sep = "SEPARATED" if (lo > 0 or hi < 0) else "includes 0"
    print(f"  {name:16s} null_U={k_u:3d}/{n} null_E={k_e:3d}/{n}  "
          f"D={d:+.4f} [{lo:+.4f},{hi:+.4f}] {sep}")


# =========================================================================== #
print("\n" + "=" * 74)
print("ARM G -- THE GUARD ARM (deterministic, 0 seeds)")
print("  does the mechanism emit its null on a DEGENERATE input, and at what")
print("  cost?  A null that appears ONLY here decided nothing.")
print("=" * 74)

GUARD = {}
EMPTY_SEQ = seq([None, None, None])
for term in ("TimeInfer", "DepthInfer", "BlinkBridge", "GapAbduce"):
    d = ev_seq(term, EMPTY_SEQ)
    GUARD[term] = {"null": is_null(term, d), "checked": g(d, "checked"),
                   "reason": g(d, "reason"), "kind": g(d, "kind"),
                   "bare_none": d is None}
for term in GOAL_KW:
    d = ev_goal(term, [])
    GUARD[term] = {"null": is_null(term, d), "checked": g(d, "checked"),
                   "reason": g(d, "reason"), "bare_none": d is None}
for k, v in GUARD.items():
    print(f"  {k:16s} null={str(v['null']):5s} checked={v['checked']} "
          f"reason={v['reason']} bare_None={v['bare_none']}")

# =========================================================================== #
print("\n" + "=" * 74)
print("ARM A -- THE POSITIVE CONTROL (deterministic, 0 seeds)")
print("  PROTOCOL 1.1 IN REFUSAL FORM: a mechanism you have not made ACCEPT")
print("  is one whose refusals mean NOTHING.  It scores a perfect refusal arm")
print("  by being dead.")
print("=" * 74)

ACCEPT = {}
ACCEPT["TimeInfer"] = not is_null("TimeInfer", ev_seq("TimeInfer", seq([0, 4, 8])))
ACCEPT["BlinkBridge"] = not is_null("BlinkBridge",
                                    ev_seq("BlinkBridge", seq([0, 4, 8])))
ACCEPT["GapAbduce"] = not is_null("GapAbduce", ev_seq("GapAbduce", seq([0, 4, 8])))
ACCEPT["ShapeDecode"] = not is_null("ShapeDecode", ev_goal("ShapeDecode", BASE))
ACCEPT["TransformDecode"] = not is_null("TransformDecode",
                                        ev_goal("TransformDecode", shift(3, 3)))
ACCEPT["DimInfer"] = not is_null("DimInfer",
                                 ev_goal("DimInfer", lin([0, -1, 1, 0])))
ACCEPT["GenInfer"] = not is_null("GenInfer", ev_goal("GenInfer", lin([1, 0, 1, 1])))


def depth_two_layer(c0, v0, c1, v1, n=3):
    """P2's construction: TWO surfaces at TWO velocities in one field.
    `DepthInfer` refused every single-surface stimulus with `single_velocity`,
    which is a statement about the STIMULUS, not necessarily about the
    mechanism.  This is the arm that decides between them."""
    out = []
    for t in range(n):
        f = np.full((H, W), BG, dtype=np.uint8)
        a, b = c0 + v0 * t, c1 + v1 * t
        f[ROW:ROW + DOT, a:a + DOT] = FG
        f[ROW + 8:ROW + 8 + DOT, b:b + DOT] = 128
        out.append(cells_fig(f))
    return out


_d2 = ev_seq("DepthInfer", depth_two_layer(0, 2, 60, 6))
ACCEPT["DepthInfer"] = not is_null("DepthInfer", _d2)
print(f"  DepthInfer two-layer probe -> explained={g(_d2,'explained')} "
      f"reason={g(_d2,'reason')} n_layers={g(_d2,'n_layers')} "
      f"checked={g(_d2,'checked')}")

for k, v in ACCEPT.items():
    print(f"  {k:16s} ACCEPTS={v}   {'' if v else '<-- DEAD on this family'}")
DEAD = [k for k, v in ACCEPT.items() if not v]
if len(DEAD) == len(ACCEPT):
    raise SystemExit(
        "** DEAD INSTRUMENT ** every mechanism refused its own best case. "
        "That is a broken reader, not a result -- PROTOCOL 1 clause 4. "
        f"dead={DEAD}")

# =========================================================================== #
print("\n" + "=" * 74)
print(f"ARM DELTA -- {N_PAIRS} MATCHED PAIRS, seeds {SEQ_LO}-{SEQ_HI - 1}")
print("=" * 74)

# ---- sequence family --------------------------------------------------------
pairs_seq = []
for sd in SEQ_SEEDS:
    rng = np.random.default_rng(sd)
    c = int(rng.integers(0, 40))
    v = int(rng.integers(2, 12))
    # E: constant velocity.  U: SAME three columns re-ordered so the velocity
    # is not constant -- identical cell count, identical frame count, identical
    # non-emptiness.  Only the ARRANGEMENT IN TIME differs.
    e = [c, c + v, c + 2 * v]
    u = [c, c + 2 * v, c + v]
    pairs_seq.append((e, u))

for term in ("TimeInfer", "DepthInfer", "BlinkBridge", "GapAbduce"):
    ku = ke = 0
    cu = ce = 0
    t0 = time.time()
    for e, u in pairs_seq:
        de = ev_seq(term, seq(e))
        du = ev_seq(term, seq(u))
        ke += is_null(term, de)
        ku += is_null(term, du)
        ce += (g(de, "checked") or 0)
        cu += (g(du, "checked") or 0)
    dt = (time.time() - t0) / (2 * N_PAIRS)
    record(term, ku, ke, N_PAIRS, cu / N_PAIRS, ce / N_PAIRS,
           extra={"sec_per_call": dt})

# ---- goal family ------------------------------------------------------------
UNIMOD = [[1, 0, 1, 1], [1, 1, 0, 1], [2, 1, 1, 1], [1, 2, 0, 1], [0, -1, 1, 0]]
for term in ("ShapeDecode", "TransformDecode", "DimInfer", "GenInfer"):
    ku = ke = 0
    cu = ce = 0
    t0 = time.time()
    for sd in SEQ_SEEDS:
        rng = np.random.default_rng(sd + 500_000)
        if term == "TransformDecode":
            e = shift(int(rng.integers(-6, 7)), int(rng.integers(-6, 7)))
        elif term == "DimInfer":
            e = lin([0, -1, 1, 0])           # rotation90, a HELD generator
            e = shift(int(rng.integers(-3, 4)), int(rng.integers(-3, 4)), e)
        elif term == "GenInfer":
            e = lin(UNIMOD[int(rng.integers(0, len(UNIMOD)))])
        else:
            e = shift(int(rng.integers(-3, 4)), int(rng.integers(-3, 4)))
        u = rand_cells(rng)
        de = ev_goal(term, e)
        du = ev_goal(term, u)
        ke += is_null(term, de)
        ku += is_null(term, du)
        ce += (g(de, "checked") or 0)
        cu += (g(du, "checked") or 0)
    dt = (time.time() - t0) / (2 * N_PAIRS)
    record(term, ku, ke, N_PAIRS, cu / N_PAIRS, ce / N_PAIRS,
           extra={"sec_per_call": dt})

# =========================================================================== #
print("\n" + "=" * 74)
print(f"ARM P2 -- DepthInfer on the TWO-LAYER family, seeds "
      f"{DEPTH_LO}-{DEPTH_HI - 1}")
print("  Every sequence stimulus above carries ONE surface, and DepthInfer")
print("  refuses all of them with `single_velocity`. THAT IS A FACT ABOUT THE")
print("  STIMULUS. This arm is the family where the mechanism is LIVE.")
print("=" * 74)

kd_u = kd_e = 0
reasons_u = {}
for sd in DEPTH_SEEDS:
    rng = np.random.default_rng(sd)
    c0 = int(rng.integers(0, 20)); c1 = int(rng.integers(60, 90))
    v0 = int(rng.integers(1, 4)); v1 = v0 + int(rng.integers(3, 9))
    # E: two surfaces, each at its OWN CONSTANT velocity -- two layers.
    de = ev_seq("DepthInfer", depth_two_layer(c0, v0, c1, v1))
    # U: two surfaces, same count, same cells, same frames -- but the second
    # does NOT move rigidly; its velocity changes between frames. Identical in
    # every guard-visible property.
    fr = []
    for t in range(3):
        f = np.full((H, W), BG, dtype=np.uint8)
        a = c0 + v0 * t
        b = c1 + (v1 * t if t < 2 else v1 * t + 7)
        f[ROW:ROW + DOT, a:a + DOT] = FG
        f[ROW + 8:ROW + 8 + DOT, b:b + DOT] = 128
        fr.append(cells_fig(f))
    du = ev_seq("DepthInfer", fr)
    kd_e += is_null("DepthInfer", de)
    kd_u += is_null("DepthInfer", du)
    r = g(du, "reason")
    reasons_u[r] = reasons_u.get(r, 0) + 1
record("DepthInfer@2layer", kd_u, kd_e, N_PAIRS,
       extra={"refusal_reasons_U": reasons_u})
print(f"  refusal reasons on U: {reasons_u}")

# =========================================================================== #
print("\n" + "=" * 74)
print("ARM P3 -- BlinkBridge ACROSS A REAL GAP, seeds "
      f"{BLINK_LO}-{BLINK_HI - 1}")
print("  Every arm above ran at gap = 0.  THE GAP REGIME IS WHERE THIS")
print("  MECHANISM IS ACTUALLY USED, and it is the only place the")
print("  confabulate-always claim can be tested.")
print("=" * 74)

kb_u = kb_e = 0
conf_e, conf_u, corr_u = [], [], []
for sd in BLINK_SEEDS:
    rng = np.random.default_rng(sd)
    c = int(rng.integers(0, 40))
    v = int(rng.integers(2, 10))
    # E: a coherent prefix, then a gap, then the frame the prefix PREDICTS.
    e = [c, c + v, c + 2 * v, None, c + 4 * v]
    # U: the SAME prefix and the SAME gap, but the resume frame is somewhere
    # the prefix does NOT predict.  Identical arity, identical gap, identical
    # cell counts.  Only the TRUTH of the continuation differs.
    bad = c + 4 * v + int(rng.integers(13, 40))
    u = [c, c + v, c + 2 * v, None, bad]
    de = ev_seq("BlinkBridge", seq(e))
    du = ev_seq("BlinkBridge", seq(u))
    kb_e += is_null("BlinkBridge", de)
    kb_u += is_null("BlinkBridge", du)
    conf_e.append(g(de, "confidence") or 0.0)
    conf_u.append(g(du, "confidence") or 0.0)
    corr_u.append(g(du, "correction") or 0.0)
record("BlinkBridge@gap", kb_u, kb_e, N_PAIRS,
       extra={"mean_conf_E": float(np.mean(conf_e)),
              "mean_conf_U": float(np.mean(conf_u)),
              "mean_correction_U": float(np.mean(corr_u)),
              "n_correction_gt0_U": int(sum(1 for x in corr_u if x and x > 0))})
print(f"  confidence  E={np.mean(conf_e):.4f}  U={np.mean(conf_u):.4f}   "
      f"correction on U: mean={np.mean(corr_u):.2f}, "
      f">0 in {sum(1 for x in corr_u if x and x > 0)}/{N_PAIRS}")

# =========================================================================== #
print("\n" + "=" * 74)
print("ARM P9/P10/P11/P12/P13 -- THE PRIMITIVES, SELECTORS AND COUNTS")
print("=" * 74)

# --- P9: the shrug class.  Matched WELL-FORMED images; only content differs.
prim = {}
for name in ("ChangeDetect", "TemporalDiff", "Foveate"):
    ku = ke = 0
    for sd in SEQ_SEEDS:
        rng = np.random.default_rng(sd + 900_000)
        img_e = list(np.linspace(0.0, 1.0, 64))            # structured
        img_u = list(rng.random(64))                       # pure noise
        if name == "ChangeDetect":
            mk = lambda im: srs.Term(                       # noqa: E731
                "ChangeDetect", image_vals=srs.Lit(im),
                kernel_weights=srs.Lit([1.0, -1.0, -1.0, 1.0]),
                dims=srs.Lit([8, 8, 2, 2, 1]))
        elif name == "TemporalDiff":
            mk = lambda im: srs.Term(                       # noqa: E731
                "TemporalDiff", a_vals=srs.Lit(im),
                b_vals=srs.Lit(list(np.zeros(64))))
        else:
            mk = lambda im: srs.Term(                       # noqa: E731
                "Foveate", image_vals=srs.Lit(im), dims=srs.Lit([8, 8]),
                geometry=srs.Lit([4.0, 4.0, 3.0]))
        ke += S.evaluate(mk(img_e), {}) is None
        ku += S.evaluate(mk(img_u), {}) is None
    record(name, ku, ke, N_PAIRS)
    # the guard arm: a malformed dims tuple
    if name == "ChangeDetect":
        bad = srs.Term("ChangeDetect", image_vals=srs.Lit([1.0] * 64),
                       kernel_weights=srs.Lit([1.0]),
                       dims=srs.Lit([8, 8, 99, 99, 1]))
    elif name == "TemporalDiff":
        bad = srs.Term("TemporalDiff", a_vals=srs.Lit([1.0] * 64),
                       b_vals=srs.Lit([1.0] * 63))
    else:
        bad = srs.Term("Foveate", image_vals=srs.Lit([1.0] * 64),
                       dims=srs.Lit([7, 7]), geometry=srs.Lit([1.0, 1.0, 1.0]))
    prim[name] = {"guard_null": S.evaluate(bad, {}) is None}
    print(f"      {name}: guard(malformed) -> null={prim[name]['guard_null']}")

def _argmin(ty):
    return srs.Term("Argmin",
                    source=srs.Term("NodesOfType", node_type=ty),
                    var_name="x",
                    value=srs.Term("Attr", node=srs.Term("Var", name="x"),
                                   key="v"))


# --- P10: Argmin.  E = a set with a clear minimum.  U = a set of EQUAL values
#     (no candidate is better than any other -- nothing to decide).
ku = ke = 0
am_e_win, am_u_win = None, None
for sd in SEQ_SEEDS[:N_PAIRS]:
    rng = np.random.default_rng(sd + 700_000)
    s2, ag2 = boot_core()
    for i in range(5):
        s2.add_node("ArgProbeE", {"v": float(rng.random())})
        s2.add_node("ArgProbeU", {"v": 1.0})       # every candidate identical
    te = _argmin("ArgProbeE")
    tu = _argmin("ArgProbeU")
    _re, _ru = s2.evaluate(te, {}), s2.evaluate(tu, {})
    ke += _re is None
    ku += _ru is None
    am_e_win, am_u_win = _re, _ru
record("Argmin", ku, ke, N_PAIRS,
       extra={"winner_on_5_DISTINCT": repr(am_e_win),
              "winner_on_5_IDENTICAL": repr(am_u_win)})
print(f"      Argmin on 5 IDENTICAL candidates (nothing to decide) -> "
      f"returned {am_u_win!r}, NOT a null")
s3, ag3 = boot_core()
t_empty = _argmin("NoSuchType")
print(f"      Argmin: guard(EMPTY source) -> null="
      f"{s3.evaluate(t_empty, {}) is None}")

# --- P11: PickUnique.  0 -> None; 1 -> element; >1 -> ESCALATES.
s4, ag4 = boot_core()
pk = lambda ty: srs.Term("PickUnique",                       # noqa: E731
                         source=srs.Term("NodesOfType", node_type=ty))
pu = {"zero": s4.evaluate(pk("NoSuchType"), {}) is None}
s4.add_node("PUProbe", {"v": 1.0})
pu["one"] = s4.evaluate(pk("PUProbe"), {}) is not None
s4.add_node("PUProbe", {"v": 2.0})
try:
    s4.evaluate(pk("PUProbe"), {})
    pu["two"] = "returned (did NOT escalate)"
except BaseException as e:                                   # noqa: BLE001
    pu["two"] = f"ESCALATED: {type(e).__name__}"
print(f"      PickUnique: 0->null={pu['zero']}  1->value={pu['one']}  "
      f"2->{pu['two']}")

# --- P12: EnclosedCount.  E = a closed loop.  U = an open scribble.
LOOP = [[float(x), 0.0] for x in range(8)] + [[7.0, float(y)] for y in range(8)] \
     + [[float(7 - x), 7.0] for x in range(8)] + [[0.0, float(7 - y)] for y in range(8)]
ku = ke = 0
ec_e = ec_u = None
for sd in SEQ_SEEDS:
    rng = np.random.default_rng(sd + 800_000)
    open_ = [[float(x), float(rng.integers(0, 8))] for x in range(8)]
    de = as_dict(S.evaluate(srs.Term("EnclosedCount", arg=srs.Lit([LOOP])), {}))
    du = as_dict(S.evaluate(srs.Term("EnclosedCount", arg=srs.Lit([open_])), {}))
    ke += de is None
    ku += du is None
    ec_e, ec_u = de, du
record("EnclosedCount", ku, ke, N_PAIRS)
deg = as_dict(S.evaluate(srs.Term("EnclosedCount", arg=srs.Lit([[]])), {}))
print(f"      EnclosedCount: loop holes={g(ec_e,'holes')} "
      f"grid_w={g(ec_e,'grid_w')} | open holes={g(ec_u,'holes')} "
      f"grid_w={g(ec_u,'grid_w')}")
print(f"      EnclosedCount: DEGENERATE(empty) -> null={deg is None} "
      f"holes={g(deg,'holes')} grid_w={g(deg,'grid_w')}")

# --- P13: the block-matching motion sensor.
import importlib.util                                         # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "msgate", "scripts/motion_sensor_gate.py")
_ms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ms)
ku = ke = 0
ms_nan = 0
for sd in SEQ_SEEDS:
    rng = np.random.default_rng(sd + 600_000)
    a = rng.integers(0, 256, (32, 32)).astype(np.float64)
    b_e = np.roll(a, 3, axis=1)                     # a REAL translation
    b_u = rng.integers(0, 256, (32, 32)).astype(np.float64)   # INDEPENDENT
    ve = _ms._sensor(a, b_e, 8)
    vu = _ms._sensor(a, b_u, 8)
    ke += ve is None
    ku += vu is None
    ms_nan += int(np.isnan(vu).any())
record("MotionSensor", ku, ke, N_PAIRS,
       extra={"nan_on_noise": ms_nan,
              "field_shape": list(vu.shape),
              "n_vectors_emitted_on_noise": int(vu.size // 2),
              "n_zero_vectors_on_noise": int((np.abs(vu).sum(-1) == 0).sum())})
print(f"      MotionSensor on INDEPENDENT noise: emitted "
      f"{vu.size // 2} well-formed vectors, {ms_nan}/{N_PAIRS} with any NaN, "
      f"{int((np.abs(vu).sum(-1) == 0).sum())} of 16 exactly zero")

# =========================================================================== #
print("\n" + "=" * 74)
print("ARM C1 -- IS A STRUCTURED REFUSAL ERASED AT THE FIELD BOUNDARY?")
print("=" * 74)
c1 = {}
for f in ("authored", "reason", "explained", "checked", "plan"):
    t = srs.Term("ShapeDecode", goal=srs.Lit([]), codebook_type="ShapeSignature",
                 field=f, **GOAL_KW["ShapeDecode"])
    v = S.evaluate(t, {})
    c1[f] = repr(v)
    print(f"  WALLED ShapeDecode, field={f:10s} -> {v!r}")
# the same read on a NON-walled refusal, for contrast
for f in ("explained", "checked"):
    t = srs.Term("TransformDecode", goal=srs.Lit(rand_cells(
        np.random.default_rng(106000))), codebook_type="ShapeSignature",
        field=f, **GOAL_KW["TransformDecode"])
    v = S.evaluate(t, {})
    c1[f"TransformDecode.{f}"] = repr(v)
    print(f"  REFUSED TransformDecode, field={f:10s} -> {v!r}")

# =========================================================================== #
out = {"engine": _line, "n_pairs": N_PAIRS,
       "seeds": {"seq": [SEQ_LO, SEQ_HI - 1], "depth": [DEPTH_LO, DEPTH_HI - 1],
                 "blink": [BLINK_LO, BLINK_HI - 1]},
       "guard_arm": GUARD, "accept_arm": ACCEPT, "dead": DEAD,
       "delta": RESULTS, "cost": COST, "primitive_guards": prim,
       "pick_unique": pu, "c1_field_erasure": c1}
with open("results/refusal_capacity.json", "w") as fh:
    json.dump(out, fh, indent=2, default=str)
print("\nwrote results/refusal_capacity.json")
