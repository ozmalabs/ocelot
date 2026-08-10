"""arc_ls20_transform_measure — RUNG 217000: TRANSFORMATION RECOGNITION on ls20.

Built ON 216000 (the ls20 eye SEES: pixel-segmentation parity). This rung wires the
substrate's GENERAL shape-transform machinery — `TransformDecode` / `DimInfer`
(runners/dsl/src/shape_decode.rs) driven by the `seeds/shape_decode_loop.json`
sd_* rules — to the PIXEL-EYE Regions, and measures the RECOGNITION half of ls20's
core mechanic: "a symbol must go through various transformations (rotate / reflect /
recolour / translate) to reach the goal."

THE PIPELINE (seeing-not-oracle, honoured end to end):

  symbol shape (ls20 palette)  --_render_screen-->  RGB pixels
       --recover_grid_from_render (pixel eye, 216000)-->  SEEN grid
       --carve (4-conn per value)-->  SEEN symbol cells
       --cells_to_signature-->  [["cell", r, c, v], ...]      (the base, HELD)

  goal-form = KNOWN transform applied to the symbol, SEEN the SAME way (the
  target-form the avatar must reach)  -->  goal signature (the OBSERVATION)

  the GENERAL decode (TransformDecode/DimInfer) is asked: is the goal-form a
  transform of the held symbol?  ->  recognized_transformed + Transform{dim, delta,
  generator, k}  |  minted (refused — not a transform).

VERDICT — INTEGER-NATIVE EXACT SET EQUALITY (the "in-frame is integer" ARC path,
not a continuous comparator): the engine returns `recognized_transformed` ONLY when
the decoded transform explains EVERY cell relation exactly (a consistent functional
map per dimension; an inconsistent/partial residual MINTS instead — proven by
test_transform_decode_migrated's scrambled-null). So `recognized_transformed AND
covered_by==base` IS the exact-reconstruction verdict, performed by the engine. The
FAMILY (rotate/reflect/recolour/translate) is then read off the decoded Transform.

GROUND TRUTH BY CONSTRUCTION: each goal-form is built by applying a KNOWN transform,
so the applied family is known; recognition accuracy = fraction the general decode
recognises + attributes correctly. HONEST SCOPE (standing rule — synthetic-proven !=
benchmark value, report both): these are ls20-SHAPED symbols on the real ls20 palette,
SEEN through the pixel eye; the LIVE ls20 transformation pairs need ARC_API_KEY
(absent — the named frontier, exactly as 216000). Rotate-vs-reflect is only
DISTINGUISHABLE on CHIRAL shapes (a symmetric shape's rotation IS one of its
reflections — a mathematical fact, not a miss); the family-label accuracy is scored
on chiral shapes, and the symmetric aliasing is reported separately.

GENERALITY (the falsification bar): the decode is the SAME `TransformDecode`/`DimInfer`
that serves Omniglot / the dim_infer instrument / any domain — NO ls20-specific
transform table, NO per-task hack; the per-instance transform is DISCOVERED by decode.
`--outside-ls20` runs the identical decode on the F-pentomino corpus from
scripts/dim_infer_args to show the op is dimension/domain-arbitrary.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_ls20_transform_measure.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "runners" / "dsl" / "python"))

from worlds.arc import (  # noqa: E402
    _render_screen, recover_grid_from_render, cells_to_signature, SHAPE_DIM_TYPES,
)
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

DT = SHAPE_DIM_TYPES
BG = 0  # white background (palette 0)


# --------------------------------------------------------------------------
# THE ls20-SHAPED SYMBOL CORPUS (real ls20 palette; small polyomino symbols).
# Each symbol is a set of (dr, dc, colour) offsets from its own origin. Colours
# are ls20 palette indices (9 blue, 11 yellow, 8 red, 14 green, 6 magenta,
# 12 orange) — the same table the eye recovers (worlds/arc.py::_PALETTE).
# --------------------------------------------------------------------------
def _mono(offsets, colour):
    return [(r, c, colour) for (r, c) in offsets]


# chiral polyominoes (rotation != reflection) — the discriminating shapes.
CORPUS = {
    # F-pentomino (blue avatar-symbol): .XX / XX. / .X.
    "F_blue": _mono([(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)], 9),
    # L-tetromino (yellow): X. / X. / XX
    "L_yellow": _mono([(0, 0), (1, 0), (2, 0), (2, 1)], 11),
    # J/S-ish chiral pentomino (red): .X / .X / XX / X.
    "S_red": _mono([(0, 1), (1, 1), (2, 0), (2, 1), (3, 0)], 8),
    # Y-pentomino (green, chiral): .X / XX / .X / .X
    "Y_green": _mono([(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)], 14),
    # small chiral P (orange): XX / XX / X.
    "P_orange": _mono([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)], 12),
    # a chiral "gun" heptomino (magenta)
    "G_magenta": _mono([(0, 0), (1, 0), (2, 0), (2, 1), (0, 2), (0, 1)], 6),
}

# symmetric symbols (rotation aliases a reflection) — reported separately.
SYMMETRIC = {
    "square_blue": _mono([(0, 0), (0, 1), (1, 0), (1, 1)], 9),         # 4-fold
    "plus_red": _mono([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)], 8),    # 4-fold
    "Ltromino_yellow": _mono([(0, 0), (0, 1), (1, 0)], 11),           # diag mirror
    "Ibar_green": _mono([(0, 0), (0, 1), (0, 2), (0, 3)], 14),        # 2-fold
}

# a genuine TWO-COLOUR avatar (blue body 9 + yellow marker 11) — the 216000
# residual: it shatters into two Regions; region_signature groups them. Chiral.
AVATAR_2C = [(0, 0, 9), (1, 0, 9), (2, 0, 9), (2, 1, 11), (0, 1, 9)]


# --------------------------------------------------------------------------
# TRANSFORMS (applied to a symbol's (r, c, colour) cells — ground truth).
# --------------------------------------------------------------------------
def _reposition(cells, margin=3):
    """Shift so min row/col == margin (keep inside the canvas, non-negative)."""
    mr = min(r for r, c, v in cells)
    mc = min(c for r, c, v in cells)
    return [(r - mr + margin, c - mc + margin, v) for (r, c, v) in cells]


def t_identity(cells, _p):
    return _reposition(cells)


def t_translate(cells, p):
    dr, dc = p
    return [(r + dr, c + dc, v) for (r, c, v) in _reposition(cells)]


def t_recolour(cells, p):
    cmap = p
    return [(r, c, cmap.get(v, v)) for (r, c, v) in _reposition(cells)]


def t_rotate(cells, k):
    out = [(r, c, v) for (r, c, v) in cells]
    for _ in range(k):
        out = [(c, -r, v) for (r, c, v) in out]   # (r,c)->(c,-r) = rot90
    return _reposition(out)


def t_reflect(cells, axis):
    if axis == "c":
        out = [(r, -c, v) for (r, c, v) in cells]   # column mirror
    else:
        out = [(-r, c, v) for (r, c, v) in cells]   # row mirror
    return _reposition(out)


# recolour permutation over the symbol palette (a consistent global swap).
RECOLOUR_MAP = {9: 8, 11: 14, 8: 9, 14: 11, 12: 6, 6: 12}


# --------------------------------------------------------------------------
# SEEING — render a symbol, recover it through the pixel eye, carve it back out.
# --------------------------------------------------------------------------
def render_and_see(cells, canvas=18, noise_sigma=0.0, rng=None):
    """cells [(r,c,v)] -> place on a `canvas`x`canvas` BG grid -> _render_screen
    -> recover_grid_from_render (PIXEL EYE, pixels only) -> SEEN non-background
    cells [(r,c,v)]. This is the 216000 seeing path; the oracle grid is never read
    downstream (only used here to place pixels, exactly as a human would draw)."""
    g = [[BG] * canvas for _ in range(canvas)]
    for (r, c, v) in cells:
        if 0 <= r < canvas and 0 <= c < canvas:
            g[r][c] = int(v)
    screen = _render_screen(g, canvas, canvas).astype(np.int16)
    if noise_sigma > 0:
        nz = (rng.normal(0, noise_sigma, screen.shape) if rng is not None
              else np.random.normal(0, noise_sigma, screen.shape))
        screen = np.clip(screen + nz, 0, 255)
    seen = recover_grid_from_render(screen.astype(np.uint8))
    arr = np.asarray(seen, dtype=np.int32)
    out = []
    for r in range(arr.shape[0]):
        for c in range(arr.shape[1]):
            if int(arr[r, c]) != BG:
                out.append((r, c, int(arr[r, c])))
    return out


# --------------------------------------------------------------------------
# THE GENERAL DECODE — TransformDecode/DimInfer via the sd_* rule fixpoint.
# Identical construction to scripts/dim_infer_args.py::point_S (the shipped
# dim_infer instrument): a HELD ShapeSignature (the symbol) + a decoded
# Observation (the goal-form) + run_rules(). NOTHING ls20-specific.
# --------------------------------------------------------------------------
def decode_transform(base_sig, goal_sig):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    baseline_axes = len(list(s.nodes("CapabilityAxis")))
    s.add_node("ShapeSignature", {"name": "sym", "signature": json.dumps(base_sig),
                                  "kind": "faculty", "faculty": "sym", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal_sig, "key": ["probe"],
                                     "status": "decoded", "residual": goal_sig,
                                     "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    tr = None
    for n in s.neighbours(obs, "has_transform"):
        t = s.node(n)["attrs"]
        tr = {"dims": list(t.get("dims") or []),
              "deltas": list(t.get("deltas") or []),
              "transforms": list(t.get("transforms") or []),
              "base": t.get("base"),
              "generator": t.get("generator"),
              "k": t.get("k")}
        break
    minted = len(list(s.nodes("CapabilityAxis"))) - baseline_axes
    return {"status": at.get("status"), "covered_by": at.get("covered_by"),
            "transform": tr, "minted_axes": minted}


def classify_family(res):
    """Read the applied-transform FAMILY off the decoded Transform. Only meaningful
    when the decode recognised a transform (else None). The mapping is the general
    vocabulary's own: a rotation90 generator=>rotate, reflection_*=>reflect, a subst
    on the value dim=>recolour, shift(s) on coord dims only=>translate, empty=>id."""
    if res["status"] != "recognized_transformed" or res["transform"] is None:
        return None
    t = res["transform"]
    gen = t.get("generator")
    if gen == "rotation90":
        return "rotate"
    if gen in ("reflection_r", "reflection_c"):
        return "reflect"
    kinds = {tr.get("kind") for tr in t.get("transforms") or []}
    dims = set(t.get("dims") or [])
    if "subst" in kinds:
        return "recolour"
    if kinds and kinds <= {"shift"} and dims <= {1, 2}:
        return "translate"
    if not t.get("transforms") and gen is None:
        return "identity"
    return "other"


def _is_chiral(cells):
    def norm(cs):
        mr = min(r for r, c, v in cs); mc = min(c for r, c, v in cs)
        return frozenset((r - mr, c - mc, v) for r, c, v in cs)
    refl = [(r, -c, v) for (r, c, v) in cells]
    # chiral if no rotation of the reflection equals the original
    o = norm(cells)
    cur = refl
    for _ in range(4):
        if norm(cur) == o:
            return False
        cur = [(c, -r, v) for (r, c, v) in cur]
    return True


# --------------------------------------------------------------------------
# THE MEASUREMENT
# --------------------------------------------------------------------------
def build_pairs(corpus, translates, recolour_families=True):
    """[(base_name, family, param, base_cells, goal_cells)] — every transform pair,
    ground truth by construction. Rotate/reflect only on chiral bases."""
    pairs = []
    for name, cells in corpus.items():
        base = _reposition(cells)
        chiral = _is_chiral(cells)
        pairs.append((name, "identity", None, base, t_identity(cells, None)))
        for p in translates:
            pairs.append((name, "translate", p, base, t_translate(cells, p)))
        if recolour_families:
            pairs.append((name, "recolour", "map", base, t_recolour(cells, RECOLOUR_MAP)))
        if chiral:
            for k in (1, 2, 3):
                pairs.append((name, "rotate", k, base, t_rotate(cells, k)))
            for axis in ("c", "r"):
                pairs.append((name, "reflect", axis, base, t_reflect(cells, axis)))
    return pairs


def build_refuse_pairs(corpus):
    """Genuinely UNRELATED pairs: base X vs a DIFFERENT symbol Y (not a transform of
    X). The recogniser must REJECT (mint, no Transform) — a recogniser that can't
    refuse is not a recogniser (G-refuse)."""
    names = list(corpus.keys())
    out = []
    for i, a in enumerate(names):
        for b in names:
            if a == b:
                continue
            out.append((a, b, _reposition(corpus[a]), _reposition(corpus[b])))
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def measure(corpus, translates, noise_sigma=0.0, seed=217000):
    rng = np.random.default_rng(seed)
    pairs = build_pairs(corpus, translates)
    per_family = {}          # family -> [recognised_bool, ...]
    per_family_label = {}    # family -> [label_correct_bool, ...] (chiral only for rot/refl)
    misses = []
    for (name, family, param, base_cells, goal_cells) in pairs:
        base_seen = render_and_see(base_cells, noise_sigma=noise_sigma, rng=rng)
        goal_seen = render_and_see(goal_cells, noise_sigma=noise_sigma, rng=rng)
        base_sig = cells_to_signature(base_seen)
        goal_sig = cells_to_signature(goal_seen)
        res = decode_transform(base_sig, goal_sig)
        recognised = (res["status"] == "recognized_transformed"
                      and res["covered_by"] == "sym")
        got_family = classify_family(res)
        label_ok = recognised and (got_family == family)
        per_family.setdefault(family, []).append(recognised)
        per_family_label.setdefault(family, []).append(label_ok)
        if not recognised or not label_ok:
            misses.append({"symbol": name, "family": family, "param": str(param),
                           "status": res["status"], "got_family": got_family,
                           "generator": (res["transform"] or {}).get("generator")
                           if res["transform"] else None,
                           "n_base": len(base_seen), "n_goal": len(goal_seen)})
    fam_stats = {}
    for fam, rec in per_family.items():
        lab = per_family_label[fam]
        fam_stats[fam] = {
            "n": len(rec),
            "recognised": sum(rec),
            "recognised_frac": wilson(sum(rec), len(rec)),
            "label_correct": sum(lab),
            "label_correct_frac": wilson(sum(lab), len(lab)),
        }
    all_rec = [b for v in per_family.values() for b in v]
    # label accuracy is scored over the FOUR NAMED families only; `identity` is a
    # recognition sanity case whose label is inherently ambiguous (the trivial map
    # is expressible via many generators, exactly the symmetric-aliasing fact).
    NAMED = ("translate", "recolour", "rotate", "reflect")
    all_lab = [b for fam in NAMED for b in per_family_label.get(fam, [])]
    return {
        "noise_sigma": noise_sigma,
        "n_pairs": len(pairs),
        "overall_recognised_frac": wilson(sum(all_rec), len(all_rec)),
        "overall_label_correct_frac": wilson(sum(all_lab), len(all_lab)),
        "per_family": fam_stats,
        "misses": misses,
    }


def measure_refuse(corpus, noise_sigma=0.0, seed=217000):
    rng = np.random.default_rng(seed + 1)
    pairs = build_refuse_pairs(corpus)
    false_pos = 0
    spurious = []
    for (a, b, ac, bc) in pairs:
        a_seen = render_and_see(ac, noise_sigma=noise_sigma, rng=rng)
        b_seen = render_and_see(bc, noise_sigma=noise_sigma, rng=rng)
        res = decode_transform(cells_to_signature(a_seen), cells_to_signature(b_seen))
        recognised = (res["status"] == "recognized_transformed"
                      and res["covered_by"] == "sym")
        if recognised:
            false_pos += 1
            spurious.append({"base": a, "other": b,
                             "generator": (res["transform"] or {}).get("generator")})
    return {"n_pairs": len(pairs), "false_positives": false_pos,
            "false_positive_rate": wilson(false_pos, len(pairs)),
            "spurious": spurious[:10]}


def measure_symmetric_aliasing(noise_sigma=0.0, seed=217000):
    """The honest report: on SYMMETRIC symbols, is an applied rotate recognised as a
    transform (yes it should be), and how does the label alias to reflect?"""
    rng = np.random.default_rng(seed + 2)
    rows = []
    for name, cells in SYMMETRIC.items():
        for k in (1, 2, 3):
            base_seen = render_and_see(_reposition(cells), noise_sigma=noise_sigma, rng=rng)
            goal_seen = render_and_see(t_rotate(cells, k), noise_sigma=noise_sigma, rng=rng)
            res = decode_transform(cells_to_signature(base_seen), cells_to_signature(goal_seen))
            rows.append({"symbol": name, "applied": f"rotate_k{k}",
                         "status": res["status"],
                         "recognised": res["status"] == "recognized_transformed"
                         and res["covered_by"] == "sym",
                         "got_family": classify_family(res),
                         "generator": (res["transform"] or {}).get("generator")
                         if res["transform"] else None})
    n = len(rows)
    rec = sum(1 for r in rows if r["recognised"])
    return {"n": n, "recognised": rec, "rows": rows,
            "note": "a symmetric shape's rotation IS one of its reflections — a "
                    "reflect label here is NOT a miss, it is the same map; only "
                    "the exact-equality RECOGNITION is scored."}


def measure_multicolour(noise_sigma=0.0, seed=217000):
    """The two-colour avatar (216000 residual): grouped as ONE shape via all its
    non-background cells, then rotate/reflect/translate recognised across colours."""
    rng = np.random.default_rng(seed + 3)
    rows = []
    for family, param, fn in [("rotate", 1, lambda c: t_rotate(c, 1)),
                              ("reflect", "c", lambda c: t_reflect(c, "c")),
                              ("translate", (2, 3), lambda c: t_translate(c, (2, 3))),
                              ("recolour", "map", lambda c: t_recolour(c, RECOLOUR_MAP))]:
        base_seen = render_and_see(_reposition(AVATAR_2C), noise_sigma=noise_sigma, rng=rng)
        goal_seen = render_and_see(fn(AVATAR_2C), noise_sigma=noise_sigma, rng=rng)
        res = decode_transform(cells_to_signature(base_seen), cells_to_signature(goal_seen))
        rows.append({"family": family, "status": res["status"],
                     "recognised": res["status"] == "recognized_transformed"
                     and res["covered_by"] == "sym",
                     "got_family": classify_family(res),
                     "n_colours_base": len({v for _, _, v in base_seen})})
    return {"rows": rows}


def outside_ls20_check(seed=217000):
    """G-general: the IDENTICAL decode on a NON-ls20 corpus (the F-pentomino from
    scripts/dim_infer_args, plain 'red' string colours, no palette, no render) —
    proves the op is domain/dimension-arbitrary, not an ls20 path."""
    F = [(0, 1, "red"), (0, 2, "red"), (1, 0, "red"), (1, 1, "red"), (2, 1, "red")]
    base = cells_to_signature([(r, c, v) for r, c, v in _reposition(F)])
    out = {}
    for fam, goal_cells in [("rotate", t_rotate(F, 1)),
                            ("reflect", t_reflect(F, "c")),
                            ("translate", t_translate(F, (4, 2))),
                            ("recolour", [(r, c, "blue") for r, c, v in _reposition(F)])]:
        res = decode_transform(base, cells_to_signature(goal_cells))
        out[fam] = {"recognised": res["status"] == "recognized_transformed",
                    "got_family": classify_family(res),
                    "generator": (res["transform"] or {}).get("generator")
                    if res["transform"] else None}
    return out


# --------------------------------------------------------------------------
# GATE (threshold pre-registered in LS20_TRANSFORM_PREREG.md from a first honest run)
# --------------------------------------------------------------------------
def check_gates(headline, refuse, gate_recognise, gate_label, gate_fp):
    rec = headline["overall_recognised_frac"][0]
    lab = headline["overall_label_correct_frac"][0]
    fp = refuse["false_positive_rate"][0]
    return {
        "G_recognise": rec >= gate_recognise,
        "G_label": lab >= gate_label,
        "G_refuse": fp <= gate_fp,
        "recognised": rec, "label_correct": lab, "false_positive_rate": fp,
    }


TRANSLATES = [(2, 0), (0, 3), (3, 4), (5, 1), (1, 6)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=217000)
    ap.add_argument("--tag", default="first")
    ap.add_argument("--heldout", action="store_true",
                    help="held-out confirmation: symmetric+avatar as extra bases, fresh seed")
    ap.add_argument("--gate-recognise", type=float, default=0.0)
    ap.add_argument("--gate-label", type=float, default=0.0)
    ap.add_argument("--gate-fp", type=float, default=1.0)
    args = ap.parse_args()

    corpus = dict(CORPUS)
    if args.heldout:
        # held-out confirmation (teeth): a DIFFERENT corpus — the symmetric symbols
        # (translate/recolour only; _is_chiral gates out their rot/reflect) AND the
        # two-colour avatar as a scored chiral base — on a fresh in-block seed.
        corpus.update(SYMMETRIC)
        corpus["avatar_2c"] = AVATAR_2C
        if args.seed == 217000:
            args.seed = 217500

    # round-trip sanity: the eye is a lossless inverse on these canvases
    rt_ok = True
    for name, cells in corpus.items():
        seen = render_and_see(_reposition(cells))
        want = {(r, c, v) for r, c, v in _reposition(cells)}
        if {(r, c, v) for r, c, v in seen} != want:
            rt_ok = False

    headline = measure(corpus, TRANSLATES, noise_sigma=0.0, seed=args.seed)
    refuse = measure_refuse(corpus, noise_sigma=0.0, seed=args.seed)
    # honest envelope — the transform recognition inherits the pixel eye's noise
    # envelope (216000: clean to sigma=16, then palette-index flips). Report it.
    robustness = []
    for sig in (8.0, 16.0, 24.0):
        h = measure(corpus, TRANSLATES, noise_sigma=sig, seed=args.seed)
        r = measure_refuse(corpus, noise_sigma=sig, seed=args.seed)
        robustness.append({"noise_sigma": sig,
                           "recognised": h["overall_recognised_frac"],
                           "label_correct": h["overall_label_correct_frac"],
                           "false_positive_rate": r["false_positive_rate"]})
    symmetric = measure_symmetric_aliasing(seed=args.seed)
    multicolour = measure_multicolour(seed=args.seed)
    outside = outside_ls20_check(seed=args.seed)

    gates = check_gates(headline, refuse, args.gate_recognise, args.gate_label, args.gate_fp)

    result = {
        "rung": 217000, "tag": args.tag, "seed": args.seed,
        "commitment": "recognise ls20's transform mechanic (rotate/reflect/recolour/"
                      "translate) via the GENERAL TransformDecode/DimInfer on PIXEL-EYE "
                      "Regions; verdict = integer-native exact set equality (the engine "
                      "returns recognized_transformed only on an exact reconstruction).",
        "roundtrip_exact_inverse": rt_ok,
        "headline": headline,
        "refuse_control": refuse,
        "robustness_noise_sweep": robustness,
        "symmetric_aliasing": symmetric,
        "multicolour_avatar": multicolour,
        "outside_ls20_same_op": outside,
        "gates": gates,
        "note": "ls20-SHAPED symbols on the real ls20 palette, SEEN through the pixel "
                "eye (216000). LIVE ls20 transformation pairs need ARC_API_KEY (absent "
                "— the named frontier). rotate-vs-reflect is only distinguishable on "
                "CHIRAL shapes; symmetric aliasing reported separately, not scored as a "
                "miss.",
    }
    out = _ROOT / "results" / f"arc_ls20_transform_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    print("=== RUNG 217000 — TRANSFORMATION RECOGNITION on ls20 (pixel eye) ===")
    print(f"roundtrip exact inverse (pixel eye): {rt_ok}")
    h = headline
    print(f"\nHEADLINE  pairs={h['n_pairs']}")
    print(f"  overall recognised    : {fmt(h['overall_recognised_frac'])}")
    print(f"  overall label-correct : {fmt(h['overall_label_correct_frac'])}")
    print("  per family:")
    for fam in ("identity", "translate", "recolour", "rotate", "reflect"):
        d = h["per_family"].get(fam)
        if d:
            print(f"    {fam:10s} n={d['n']:3d} recognised={fmt(d['recognised_frac'])} "
                  f"label={fmt(d['label_correct_frac'])}")
    print(f"\nG-refuse (unrelated pairs): n={refuse['n_pairs']} "
          f"false-positives={refuse['false_positives']} "
          f"FP-rate={fmt(refuse['false_positive_rate'])}")
    print("\nROBUSTNESS (pixel-noise envelope on the render before seeing):")
    for r in robustness:
        print(f"    sigma={r['noise_sigma']:5.1f} recognised={r['recognised'][0]:.3f} "
              f"label={r['label_correct'][0]:.3f} FP={r['false_positive_rate'][0]:.3f}")
    print(f"\nSymmetric aliasing: {symmetric['recognised']}/{symmetric['n']} recognised "
          f"(reflect-label on symmetric rot is NOT a miss)")
    print("Two-colour avatar (grouped):")
    for r in multicolour["rows"]:
        print(f"    {r['family']:10s} recognised={r['recognised']} got={r['got_family']} "
              f"colours={r['n_colours_base']}")
    print("Outside-ls20 SAME op (F-pentomino, no palette/render):")
    for fam, r in outside.items():
        print(f"    {fam:10s} recognised={r['recognised']} got={r['got_family']} gen={r['generator']}")
    if h["misses"]:
        print(f"\nMISSES ({len(h['misses'])}):")
        for m in h["misses"][:20]:
            print(f"    {m['symbol']:12s} {m['family']:10s} p={m['param']:8s} "
                  f"status={m['status']} got={m['got_family']} gen={m['generator']}")
    print(f"\nGATES: {gates}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
