#!/usr/bin/env python3
"""STYLE AS A DISCOVERED DIMENSION (FRONTIER T5) — a style as a per-SOURCE COHERENT
offset on a DISCOVERED continuous axis (confirmatory run).

Pre-registration: VISION_STYLE_PREREG.md (committed BEFORE this run at a08b2a97, §3).
The within-category projection, the per-source coherence test, THE AXIS DISCOVERY, the
minting, the source-blind recognition and the memorization control are the
vision_style RULES (sty_project / sty_mint_a0 / sty_mint_a1 / sty_recognize_a0 /
sty_recognize_a1 / sty_memorize). This runner only CONSTRUCTS sourced ObjItem
axis-coordinate fields, builds a real TRAIN/TEST split, and READS the minted styles /
per-item readouts back (mechanical I/O, §0), TALLYING metrics over them. The
ground-truth `kind` and the source's TRUE styled axis are used ONLY here, for the
split and the scoring — NEVER read by a seed rule.

Seeds 47000–47999: 47000–47099 = the noise floor (arm E); 47100–47199 = the
incoherent-source draws (arm X1). 47200–47999 remain CLEAN.

Run from the gamma-substrate dir:
    python scripts/style_measure.py
"""
from __future__ import annotations
import json
import math
import os
import random
import sys
import time

# TREE-RELATIVE resolution (§10.1 rule 3): this tree's root first, so the runner can
# be invoked as `python scripts/style_measure.py` from any cwd and still import THIS
# worktree's domains/ and substrate/ (never another tree's).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import style_world as sw  # noqa: E402

# m_min = 3 FALLS OUT of d_style = 2 (VISION_STYLE_PREREG §1.4) — a style is an
# (axis, delta) PAIR and membership is FREE because the source is OBSERVED, so the
# style pays iff m > d_style = 2. NOT tuned.
D_STYLE = 2
M_MIN = 3

# --- the corpus, fixed in advance (VISION_STYLE_PREREG §3) ---------------------
KINDS = {
    "A": {"sig": (1, 1), "base": (10, 30)},
    "B": {"sig": (2, 1), "base": (50, 30)},
    "C": {"sig": (1, 2), "base": (10, 70)},
}
# instance index -> kind (2 instances per kind, per source)
KIND_ORDER = ["A", "A", "B", "B", "C", "C"]

# Three STYLED sources. Each is CONSTANT on ONE axis (its style) and takes ALL-DISTINCT
# values on the other (its free axis) so no accidental agreement can arise there. The
# free axes never collide with a held delta ({0,6} on axis 0, {0} on axis 1).
SOURCES = {
    1: {"axis": 0, "delta": 0, "r0": [0] * 6,
        "r1": [5, 10, 15, 20, 25, 30]},
    2: {"axis": 0, "delta": 6, "r0": [6] * 6,
        "r1": [5, 10, 15, 20, 25, 30]},
    3: {"axis": 1, "delta": 0, "r0": [3, 9, 12, 15, 18, 21],
        "r1": [0] * 6},
}

# Held-out instances, added AFTER minting (boxes fixed). Each raw coordinate is
# asserted absent from training by the runner.
HELD_OUT = {
    1: {"kind": "A", "r0": 0, "r1": 7},
    2: {"kind": "B", "r0": 6, "r1": 17},
    3: {"kind": "C", "r0": 13, "r1": 0},
}

INCOHERENT_SRC = 4
INCOHERENT_LO, INCOHERENT_HI = 1, 40   # iid Uniform{1..40} on BOTH axes


def _item(sid: int, kind: str, r0: int, r1: int) -> dict:
    k = KINDS[kind]
    return dict(d0=k["sig"][0], d1=k["sig"][1],
                v0=k["base"][0] + r0, v1=k["base"][1] + r1,
                src=sid, kind=kind, r0=r0, r1=r1)


def _train_items(only_kinds: dict | None = None) -> list[dict]:
    """The training instances of every styled source (6 each, 2 per kind).
    `only_kinds` optionally restricts a source to a subset of kinds (arm L)."""
    items = []
    for sid, sp in SOURCES.items():
        allowed = None if only_kinds is None else only_kinds.get(sid)
        for i, kn in enumerate(KIND_ORDER):
            if allowed is not None and kn not in allowed:
                continue
            items.append(_item(sid, kn, sp["r0"][i], sp["r1"][i]))
    return items


def _train_coords() -> set:
    return {(it["v0"], it["v1"]) for it in _train_items()}


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_category", "vision_style"])
    return s, ag


def _mint_scene(items=None):
    """Boot, add TRAINING items, tick to mint categories AND styles."""
    s, ag = _boot()
    h = sw.add_field(s, items=items if items is not None else _train_items())
    sw.set_flag(s, style=1.0, identity=1.0)
    sw.tick(s)
    return s, h


def _expected_styles():
    return sorted((sid, sp["axis"], sp["delta"]) for sid, sp in SOURCES.items())


# ---- H: STYLE DISCOVERED (headline) ------------------------------------------
def arm_style_discovered():
    s, h = _mint_scene()
    got = sw.styles(s)
    observed = sorted((g["src"], g["axis"], g["delta"]) for g in got)
    per_source = {}
    for sid, sp in SOURCES.items():
        mine = [g for g in got if g["src"] == sid]
        on_true_axis = [g for g in mine if g["axis"] == sp["axis"]]
        on_free_axis = [g for g in mine if g["axis"] != sp["axis"]]
        per_source[str(sid)] = {
            "n_styles": len(mine),
            "true_axis": sp["axis"], "true_delta": sp["delta"],
            "discovered": [{"axis": g["axis"], "delta": g["delta"],
                            "members": g["members"]} for g in mine],
            "axis_correct": (len(on_true_axis) == 1
                             and on_true_axis[0]["delta"] == sp["delta"]),
            "n_on_free_axis": len(on_free_axis),
        }
    passed = (len(got) == len(SOURCES)
              and observed == _expected_styles()
              and all(v["n_styles"] == 1 and v["axis_correct"]
                      and v["n_on_free_axis"] == 0 for v in per_source.values()))
    return {"n_styles": len(got), "styles": got, "per_source": per_source,
            "expected": [list(t) for t in _expected_styles()],
            "observed": [list(t) for t in observed],
            "n_categories": sw.n_categories(s), "pass": passed}


# ---- G: GENERALIZATION --------------------------------------------------------
def _with_held_out():
    s, h = _mint_scene()
    trained = _train_coords()
    held = {}
    for sid, ho in HELD_OUT.items():
        nid = sw.add_obj(s, h, _item(sid, ho["kind"], ho["r0"], ho["r1"]))
        held[sid] = nid
    sw.tick(s)
    return s, h, held, trained


def arm_generalization():
    s, h, held, trained = _with_held_out()
    per = {}
    correct = 0
    for sid, nid in held.items():
        r = sw.readout(s, nid)
        sp = SOURCES[sid]
        ho = HELD_OUT[sid]
        coord_unseen = (r["v0"], r["v1"]) not in trained
        ok = (r["sty_recognized"] == 1
              and r["sty_src"] == sid
              and r["sty_axis"] == sp["axis"]
              and r["cat_recognized"] == 1
              and r["cat_sig"] == KINDS[ho["kind"]]["sig"]
              and coord_unseen)
        if ok:
            correct += 1
        per[str(sid)] = {**r, "coord_unseen": coord_unseen, "kind": ho["kind"],
                         "correct": ok}
    return {"held_out": per, "gen_correct": correct, "K": len(HELD_OUT),
            "pass": correct == len(HELD_OUT)}


# ---- B: DISCRIMINATION --------------------------------------------------------
def arm_discrimination():
    """Every item's SOURCE-BLIND recognized style must name its OWN source. The
    recognition rules never read the `produced` edge, so pollution is mechanically
    possible — this is a RISKED test (§13.1)."""
    s, h, held, _ = _with_held_out()
    cross_false = 0
    n_checked = 0
    detail = []
    for nid, meta in zip(h["item_ids"], h["meta"]):
        r = sw.readout(s, nid)
        if r["sty_recognized"] != 1:
            continue
        n_checked += 1
        if r["sty_src"] != meta["src"]:
            cross_false += 1
            detail.append({"true_src": meta["src"], "recognized_src": r["sty_src"],
                           "coord": [r["v0"], r["v1"]], "dv": [r["dv0"], r["dv1"]]})
    styles = sw.styles(s)
    distinct = len({(g["axis"], g["delta"]) for g in styles}) == len(styles)
    both_axes = sum(sw.readout(s, n)["sty_both_axes"] for n in h["item_ids"])
    return {"n_recognized_items": n_checked, "cross_false": cross_false,
            "detail": detail, "styles_distinct": distinct,
            "items_matching_both_axes": both_axes,
            "pass": cross_false == 0 and distinct}


# ---- X1: THE COHERENCE CRUX (§1.1, RISKED) ------------------------------------
def _p_max_mult_ge3(n: int, m: int) -> float:
    """EXACT probability that some value occurs >= 3 times among n iid draws from m
    equiprobable values (n = 6 here). Counted by complement over multiplicity
    patterns with every bin <= 2: choose j bins holding 2 and (n-2j) bins holding 1,
    then assign the labelled draws (n! / 2!^j ways). Pure arithmetic — no seeds
    burned, no simulation."""
    total = m ** n
    safe = 0
    for j in range(0, n // 2 + 1):
        singles = n - 2 * j
        if singles < 0 or j + singles > m:
            continue
        ways_bins = math.comb(m, j) * math.comb(m - j, singles)
        ways_assign = math.factorial(n) // (2 ** j)
        safe += ways_bins * ways_assign
    return 1.0 - safe / total


def _binom_crit(n: int, p: float, alpha: float = 0.05) -> int:
    """Smallest k with P(Binom(n,p) >= k) <= alpha. Observed < k ⇒ within chance."""
    tail = 1.0
    for k in range(0, n + 1):
        if tail <= alpha:
            return k
        tail -= math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    return n + 1


def arm_coherence_crux(n_seeds=100, base_seed=47100):
    """An INCOHERENT source (both axes iid Uniform{1..40}) gets the SAME instance
    count, the SAME kinds and a comparable spread, in the SAME scene as the three
    styled sources. A mechanism that mints a 'style' for ANY source is a UNIVERSAL
    CONTAINER and is disqualified. Paired positive controls in the same scene
    (§1.1): the styled sources must STILL mint 3/3, and the incoherent source's
    items must be ALIVE (dv_set = 1) — a silent arm is a failed gate, never a good
    floor."""
    p_axis = _p_max_mult_ge3(6, INCOHERENT_HI - INCOHERENT_LO + 1)
    p_chance = 1.0 - (1.0 - p_axis) ** 2          # either axis may coincide
    crit = _binom_crit(n_seeds, p_chance)

    false_mints = 0
    styled_ok = 0
    alive_all = 0
    n_alive_items = 0
    per_seed = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        items = _train_items()
        inc_ids = []
        for j, kn in enumerate(KIND_ORDER):
            items.append(_item(INCOHERENT_SRC, kn,
                               rng.randint(INCOHERENT_LO, INCOHERENT_HI),
                               rng.randint(INCOHERENT_LO, INCOHERENT_HI)))
        s, h = _mint_scene(items)
        got = sw.styles(s)
        inc_styles = [g for g in got if g["src"] == INCOHERENT_SRC]
        styled = sorted((g["src"], g["axis"], g["delta"])
                        for g in got if g["src"] != INCOHERENT_SRC)
        if styled == _expected_styles():
            styled_ok += 1
        inc_items = [n for n, m in zip(h["item_ids"], h["meta"])
                     if m["src"] == INCOHERENT_SRC]
        alive = [sw.readout(s, n)["dv_set"] for n in inc_items]
        n_alive_items += sum(alive)
        if all(a == 1 for a in alive):
            alive_all += 1
        if inc_styles:
            false_mints += 1
            per_seed.append({"seed": seed, "false_styles": inc_styles})
    return {
        "n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
        "incoherent_range": [INCOHERENT_LO, INCOHERENT_HI],
        "false_mint_scenes": false_mints,
        "false_mint_frac": round(false_mints / n_seeds, 4),
        "p_chance_analytic": round(p_chance, 6),
        "expected_false_mints": round(p_chance * n_seeds, 3),
        "binom_crit_95": crit,
        "styled_mint_ok": styled_ok,
        "incoherent_items_alive_scenes": alive_all,
        "incoherent_items_alive_total": n_alive_items,
        "incoherent_items_expected": 6 * n_seeds,
        "detail": per_seed,
        "universal_container": false_mints >= n_seeds,
        "pass": (false_mints < crit and styled_ok == n_seeds
                 and alive_all == n_seeds),
    }


# ---- C: MEMORIZATION CONTROL (declared ENTAILED) ------------------------------
def arm_memorization():
    s, h, held, trained = _with_held_out()
    sum_mem = 0
    sum_sty = 0
    per = {}
    for sid, nid in held.items():
        r = sw.readout(s, nid)
        sum_mem += r["sty_mem_recognized"]
        sum_sty += r["sty_recognized"]
        per[str(sid)] = {"sty_mem_recognized": r["sty_mem_recognized"],
                         "sty_recognized": r["sty_recognized"]}
    return {"per_source": per, "sum_mem_recognized": sum_mem,
            "sum_sty_recognized": sum_sty, "K": len(HELD_OUT),
            "entailed": True,
            "pass": sum_mem == 0 and sum_sty == len(HELD_OUT)}


# ---- E: FLOOR / noise (declared ENTAILED via T2's floor) ----------------------
def arm_floor_noise(n_seeds=100, base_seed=47000):
    false_mints = 0
    false_cats = 0
    per_seed = []
    for i in range(n_seeds):
        seed = base_seed + i
        rng = random.Random(seed)
        items = []
        for _ in range(36):
            items.append(dict(d0=rng.randint(0, 99), d1=rng.randint(0, 99),
                              v0=rng.randint(0, 99), v1=rng.randint(0, 99),
                              src=rng.randint(1, 4)))
        s, h = _mint_scene(items)
        k = sw.n_styles(s)
        c = sw.n_categories(s)
        if k > 0:
            false_mints += 1
            per_seed.append({"seed": seed, "n_styles": k, "styles": sw.styles(s)})
        if c > 0:
            false_cats += 1
    return {"n_seeds": n_seeds, "seed_range": [base_seed, base_seed + n_seeds - 1],
            "false_style_fields": false_mints, "false_category_fields": false_cats,
            "detail": per_seed, "entailed": True, "pass": false_mints == 0}


# ---- L: BOUND PROBE / anchor coverage (PREDICTED REFUSAL) ---------------------
def arm_bound_anchor_coverage():
    """The pre-registered demonstration that cross-kind coherence is a PROPERTY OF
    THE DATA, not of the rule. Train S1 in kinds A,B ONLY. Kind C's box origin on
    axis 0 is then set by S2 (r0 = 6) instead of S1 (r0 = 0), so S1's offset in kind
    C is no longer 0. PREDICTED: S1's held-out in kind C is NOT recognized as S1's
    style. Reported with the diagnosis, NOT patched with a tolerance (§5)."""
    items = _train_items(only_kinds={1: {"A", "B"}})
    s, h = _mint_scene(items)
    styles = sw.styles(s)
    s1_styles = [g for g in styles if g["src"] == 1]
    # (a) the naive held-out: S1's own offset r0 = 0 in kind C
    n_a = sw.add_obj(s, h, _item(1, "C", 0, 12))
    # (b) a held-out INSIDE kind C's (shifted) box, so the failure is the OFFSET and
    #     not merely T2's containment floor
    n_b = sw.add_obj(s, h, _item(1, "C", 8, 12))
    sw.tick(s)
    ra, rb = sw.readout(s, n_a), sw.readout(s, n_b)
    cats = {(c["d0"], c["d1"]): c for c in _categories(s)}
    cbox = cats.get(KINDS["C"]["sig"])
    refused = (ra["sty_src"] != 1) and (rb["sty_src"] != 1)
    return {
        "s1_styles": s1_styles,
        "kind_C_box": cbox,
        "held_out_a_outside_box": {**ra, "note": "r0=0: below the shifted box origin"},
        "held_out_b_inside_box": {**rb, "note": "r0=8: contained, offset shifted to 2"},
        "predicted": "REFUSAL",
        "refused": refused,
        "pass": refused and len(s1_styles) == 1,
    }


def _categories(s) -> list[dict]:
    out = []
    for c in s.nodes("ObjCategory"):
        a = s.node(c)["attrs"]
        out.append({k: int(round(float(a.get(k, 0.0))))
                    for k in ("d0", "d1", "members", "v0lo", "v0hi", "v1lo", "v1hi")})
    out.sort(key=lambda d: (d["d0"], d["d1"]))
    return out


# ---- D: MDL -------------------------------------------------------------------
def arm_mdl():
    s, h = _mint_scene()
    got = sw.styles(s)
    k = len(got)
    m_total = sum(g["members"] for g in got)
    mdl_raw = m_total                 # each member stores its own value on that axis
    mdl_styled = D_STYLE * k          # (axis, delta) per style; membership is FREE
    return {"n_styles": k, "members_total": m_total,
            "mdl_raw": mdl_raw, "mdl_styled": mdl_styled,
            "mdl_ratio": round(mdl_raw / mdl_styled, 4) if mdl_styled else None,
            "m_min": M_MIN, "d_style": D_STYLE,
            "derivation": "m > d_style = 2  <=>  m >= 3 (membership FREE: source observed)",
            "pass": k == len(SOURCES) and mdl_styled < mdl_raw and M_MIN == D_STYLE + 1}


# ---- F: DOWNSTREAM / LOAD-BEARING (§1 clause 5) -------------------------------
def arm_downstream():
    train = _train_items()
    s, ag = _boot(); h = sw.add_field(s, items=train)
    sw.set_flag(s, style=1.0, identity=1.0); sw.tick(s)
    on_styles = sw.n_styles(s)
    on_rec = [sw.obj_attr(s, n, "sty_recognized_a0") + sw.obj_attr(s, n, "sty_recognized_a1")
              for n in h["item_ids"]]
    on_dv = [sw.obj_attr(s, n, "dv_set") for n in h["item_ids"]]
    s, ag = _boot(); h = sw.add_field(s, items=train)
    sw.set_flag(s, style=0.0, identity=1.0); sw.tick(s)
    off_styles = sw.n_styles(s)
    off_rec = [sw.obj_attr(s, n, "sty_recognized_a0") + sw.obj_attr(s, n, "sty_recognized_a1")
               for n in h["item_ids"]]
    off_dv = [sw.obj_attr(s, n, "dv_set") for n in h["item_ids"]]
    d_styles = abs(on_styles - off_styles)
    d_rec = max(abs(a - b) for a, b in zip(on_rec, off_rec))
    d_dv = max(abs(a - b) for a, b in zip(on_dv, off_dv))
    return {"on_styles": on_styles, "off_styles": off_styles,
            "d_styles": d_styles, "d_recognized_max": d_rec, "d_projected_max": d_dv,
            "pass": d_styles > 0 and d_rec > 0 and d_dv > 0}


# ---- X: OFF-DAY (§9) ----------------------------------------------------------
def arm_offday():
    s, ag = _boot()
    h = sw.add_field(s, items=_train_items())
    sw.tick(s)   # BOTH flags left at their defaults (style=0, identity=0)
    k = sw.n_styles(s)
    max_rec = max(sw.obj_attr(s, n, "sty_recognized_a0")
                  + sw.obj_attr(s, n, "sty_recognized_a1") for n in h["item_ids"])
    max_dv = max(sw.obj_attr(s, n, "dv_set") for n in h["item_ids"])
    max_mem = max(sw.obj_attr(s, n, "sty_mem_recognized") for n in h["item_ids"])
    # And with T2 ON but style OFF: the style seed must remain inert on a live scene.
    s2, ag2 = _boot()
    h2 = sw.add_field(s2, items=_train_items())
    sw.set_flag(s2, style=0.0, identity=1.0); sw.tick(s2)
    k2 = sw.n_styles(s2)
    max_dv2 = max(sw.obj_attr(s2, n, "dv_set") for n in h2["item_ids"])
    return {"n_styles": k, "max_sty_recognized": max_rec, "max_dv_set": max_dv,
            "max_mem_recognized": max_mem,
            "categories_live_styles_off": sw.n_categories(s2),
            "n_styles_with_categories_on": k2, "max_dv_set_with_categories_on": max_dv2,
            "pass": (k == 0 and max_rec == 0.0 and max_dv == 0.0 and max_mem == 0.0
                     and k2 == 0 and max_dv2 == 0.0)}


def main():
    t0 = time.time()
    prov = provenance_line()
    results = {
        "provenance": prov,
        "prereg": "VISION_STYLE_PREREG.md (committed a08b2a97, BEFORE this run)",
        "seed_block": [47000, 47999],
        "d_style": D_STYLE, "m_min": M_MIN,
        "H_style_discovered": arm_style_discovered(),
        "G_generalization": arm_generalization(),
        "B_discrimination": arm_discrimination(),
        "C_memorization_entailed": arm_memorization(),
        "D_mdl": arm_mdl(),
        "F_downstream": arm_downstream(),
        "X_offday": arm_offday(),
        "L_bound_anchor_coverage": arm_bound_anchor_coverage(),
        "X1_coherence_crux": arm_coherence_crux(),
        "E_floor_noise_entailed": arm_floor_noise(),
    }
    arm_keys = [k for k in results
                if isinstance(results.get(k), dict) and "pass" in results[k]]
    results["ALL_PASS"] = all(results[k]["pass"] for k in arm_keys)
    results["elapsed_s"] = round(time.time() - t0, 2)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "results", "style_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(prov)
    for k in arm_keys:
        print(f"  {k:28s} pass={results[k]['pass']}")
    print("ALL_PASS:", results["ALL_PASS"], "| wrote", out,
          "|", results["elapsed_s"], "s")


if __name__ == "__main__":
    main()
