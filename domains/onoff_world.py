"""onoff_world — RUNG 6 world adapter: the ON/OFF retinal split's ANATOMY, a
REAL freeze, and the signed layer's read-out.

ARCHITECTURE (CLAUDE.md). WORLD ADAPTER and pure READ-OUT only. It does exactly
four mechanical things:

  1. LAY OUT the bipolar layer — mint an ON and an OFF `Bipolar` per retinal
     location, each `drives`-wired from the SAME `RetinaCell`. Anatomy, exactly
     like `cortex_sheet.add_cortex` wiring retinotopy.
  2. LAY OUT the signed simple layer — mint `SUnit`s and wire `OOSynapse`s from
     both channels inside an rf x rf window. Positional geometry.
  3. FREEZE — set the graph-data flags that make every learning rule inert.
  4. READ the response back out. Pure query.

No decisions: no conditional over graph state chooses what the agent does. The
ON/OFF *pathway* is anatomy (it is genetically specified in real retinas, not
learned) and is named as such in the claim — exactly as rung 4 named retinotopy.
What must be GROWN, and what the rung measures, is the SUBREGION STRUCTURE: which
ON and which OFF cells a given SUnit comes to weight, i.e. the spatially aligned
adjacent ON/OFF subregions that make a simple cell orientation-selective.

WHAT IS DELIBERATELY *NOT* REUSED, AND WHY (VISION_PRIOR_ART.md flagged the
duplication risk, so this is answered explicitly rather than silently):

  `substrate_rs/vision.py` already ships `lgn_pair(sigma_on, sigma_off)` / `dog`
  / `v1_bank` / `oja_update`. None of them is fit for this rung:

    * `lgn_pair`/`dog` are HAND-DESIGNED difference-of-Gaussian convolution
      kernels computed in numpy (`origin="dog"`). That is a hand-built retina —
      precisely the bolt-on error PROTOCOL 0 names (`preprocess_patches`) and
      that Stage 1's six `designed:1.0` kernels were retracted for.
    * They are not an ON/OFF *split* at all. A DoG's OUTPUT is signed. Feeding a
      signed channel in would ASSUME AWAY the very thing rung 5 identified (our
      channel is non-negative) and would break Dale's law rather than model it.
      The whole point is TWO NON-NEGATIVE channels whose DIFFERENCE is signed.
    * `oja_update` is numpy over Image/Kernel nodes — a learning rule in Python
      (forbidden), batch-averaged over patches, with no Synapse, no plasticity
      per connection, and no WTA. The graph-native Oja already exists as
      `oja_learn` (`seeds/vision_waves.json`) and `vg_learn_kernel_oja`.

  So `vision.py` is REJECTED for the mechanism. It is REUSED where it is
  genuinely right: nowhere in this file, because the instrument this rung must
  reuse is rung 5's calibrated probe (`domains/complex_cells.py`), whose Gabor
  reference, rectification and period-4 anti-aliasing were themselves calibrated
  against three instrument bugs. Swapping in a second Gabor implementation would
  silently re-open that calibration.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np

from domains.wave_world import WaveWorld, _add_edge


# --------------------------------------------------------------------------- #
#  1 + 2. ANATOMY (mechanical wiring, no decisions)
# --------------------------------------------------------------------------- #
def add_onoff_retina(world: WaveWorld) -> dict:
    """Mint an ON and an OFF `Bipolar` for every `RetinaCell`, each driven by
    that same cell. Returns {(row, col, polarity): nid}.

    ONE wave field, TWO channels. The Bipolars share the retina they read, so
    stage II waves drive ON and OFF alike — segregation is an OUTCOME the Units
    must grow, never an input. `oo_bipolar_burst` (a RULE) decides what each
    polarity does with the shared signal; this function only states which cell
    drives which bipolar, which is anatomy."""
    s = world.s
    out: dict[tuple[int, int, int], Any] = {}
    for (r, c), cell in world.cells.items():
        for pol in (1, -1):
            b = s.add_node("Bipolar", {
                "row": float(r), "col": float(c), "polarity": float(pol),
                "bursting": 0.0, "bstep": -1.0})
            _add_edge(s, world.retina, "has_bipolar", b)
            _add_edge(s, cell, "drives", b)
            out[(r, c, pol)] = b
    return out


def add_signed_units(world: WaveWorld, bipolars: dict, n_units: int, *,
                     rf: int = 7, w0: float = 1.0, jitter: float = 0.05,
                     centres: Optional[list] = None, seed: int = 0) -> list:
    """Mint `n_units` `SUnit`s, each wired to BOTH polarities of every location
    in a centred rf x rf window.

    Initial weights are uniform `w0` with a small symmetry-breaking jitter — NOT
    structure, just a tie-break (a perfectly uniform population would have no WTA
    winner), exactly as `WaveWorld.add_units` does. Because ON and OFF start at
    the SAME uniform value, the initial effective RF (w+ - w-) is ~0 everywhere:
    the layer begins with NO orientation and NO subregions. Whatever segregation
    appears was grown by the rules.

    `n_syn` is written as an attr because `oo_sunit_xbar` needs the synapse count
    to take a mean — positional anatomy the adapter already knows, the same kind
    of mechanical fact as the RF geometry."""
    rng = np.random.default_rng(seed)
    s = world.s
    half = rf // 2
    units = []
    for i in range(n_units):
        if centres is None:
            cy = half + int(rng.integers(0, max(1, world.h - rf + 1)))
            cx = half + int(rng.integers(0, max(1, world.w - rf + 1)))
        else:
            cy, cx = int(centres[i][0]), int(centres[i][1])
        u = s.add_node("SUnit", {
            "name": f"s{i}", "act": 0.0, "act_step": -1.0, "bursting": 0.0,
            "burst_step": -1.0, "last_burst": -999.0, "xbar": 0.0,
            "xbar_step": -1.0, "cy": float(cy), "cx": float(cx),
            "rf": float(rf), "n_syn": 0.0, "xbar_on": 0.0, "xbar_off": 0.0,
            "n_on": 0.0, "n_off": 0.0, "theta": 0.0, "theta_step": -1.0,
            "rate": 0.0, "rate_step": -1.0})
        _add_edge(s, world.retina, "has_sunit", u)
        n_syn = n_on = n_off = 0
        for dr in range(-half, half + 1):
            for dc in range(-half, half + 1):
                for pol in (1, -1):
                    b = bipolars.get((cy + dr, cx + dc, pol))
                    if b is None:
                        continue
                    w = float(max(w0 * (1.0 + jitter * rng.normal()), 1e-3))
                    syn = s.add_node("OOSynapse", {
                        "weight": w, "touched": -1.0, "drow": float(dr),
                        "dcol": float(dc), "polarity": float(pol)})
                    _add_edge(s, b, "oo_pre", syn)
                    _add_edge(s, syn, "oo_post", u)
                    n_syn += 1
                    if pol > 0:
                        n_on += 1
                    else:
                        n_off += 1
        s.set_attr(u, "n_syn", float(n_syn))
        s.set_attr(u, "n_on", float(n_on))
        s.set_attr(u, "n_off", float(n_off))
        units.append(u)
    return units


# --------------------------------------------------------------------------- #
#  3. THE FREEZE — the bug rung 5 found, fixed properly
# --------------------------------------------------------------------------- #
def freeze(world: WaveWorld) -> None:
    """A REAL freeze: every learning rule that could touch this world is made
    inert, as GRAPH DATA.

    THIS IS NOT `oja = 0`, AND THAT IS THE WHOLE POINT. `bh_potentiate`,
    `bh_depress` and `bh_scale` are each gated on `WaveParams.oja == 0.0`, so
    setting oja=0 to "switch learning off" instead switches the OTHER learning
    rule ON. Rung 5 measured the damage: a single `cell_stats` probe moved the
    simple layer's weights by up to 47.9 and trained three DIFFERENT hand-set
    poolings to one attractor, so the instrument was measuring its own learning.
    `test_oja_zero_is_not_a_freeze_*` pins the defect; the gate FAILS on the
    defective freeze and PASSES on this one.

    `OnOffParams.frozen` is the honest fix for this seed: a single flag that
    every learning rule in `vision_onoff.json` carries in its `where`, so no
    rule can learn while it is set — regardless of which OTHER rule is selected.
    The legacy layer's rates are additionally zeroed (with oja kept SELECTED, so
    the `bh_*` rules stay gated off) — that combination is an exact identity, and
    is verified, not assumed."""
    for p in world.s.nodes("OnOffParams"):
        world.s.set_attr(p, "frozen", 1.0)
    for p in world.s.nodes("WaveParams"):
        world.s.set_attr(p, "oja", 1.0)      # keep bh_* gated OFF ...
        world.s.set_attr(p, "oja_eta", 0.0)  # ... and make oja_learn an identity
        world.s.set_attr(p, "bcm", 0.0)
    for p in world.s.nodes("ComplexParams"):
        world.s.set_attr(p, "cx_eta", 0.0)


def thaw(world: WaveWorld) -> None:
    """Undo `freeze`'s OnOffParams flag. Mechanical."""
    for p in world.s.nodes("OnOffParams"):
        world.s.set_attr(p, "frozen", 0.0)


def set_params(world: WaveWorld, **kw) -> None:
    """Write OnOffParams knobs. Every arm of every experiment is expressed
    through this — the ablation is the agent's own configuration (PROTOCOL 0),
    never a Python branch."""
    for p in world.s.nodes("OnOffParams"):
        for k, v in kw.items():
            world.s.set_attr(p, k, float(v))


# --------------------------------------------------------------------------- #
#  4. READ-OUT (pure query)
# --------------------------------------------------------------------------- #
def signed_rf(world: WaveWorld, u) -> np.ndarray:
    """THE EFFECTIVE RECEPTIVE FIELD: w_ON - w_OFF, laid out by (drow, dcol).

    This is what the cell actually filters with — the quantity rung 5 showed the
    unsigned layer could never make negative. Pure query."""
    rf = int(world.s.node(u)["attrs"]["rf"])
    half = rf // 2
    a = np.zeros((rf, rf), np.float32)
    for syn in world.s.in_neighbours(u, "oo_post"):
        at = world.s.node(syn)["attrs"]
        a[int(at["drow"]) + half, int(at["dcol"]) + half] += (
            float(at["weight"]) * float(at["polarity"]))
    return a


def channel_rf(world: WaveWorld, u, polarity: int) -> np.ndarray:
    """One channel's weights alone (ON or OFF), laid out by (drow, dcol)."""
    rf = int(world.s.node(u)["attrs"]["rf"])
    half = rf // 2
    a = np.zeros((rf, rf), np.float32)
    for syn in world.s.in_neighbours(u, "oo_post"):
        at = world.s.node(syn)["attrs"]
        if int(at["polarity"]) == polarity:
            a[int(at["drow"]) + half, int(at["dcol"]) + half] = float(at["weight"])
    return a


def weights(world: WaveWorld, units) -> np.ndarray:
    """Every OOSynapse weight over `units`, in a stable order. For drift."""
    out = []
    for u in units:
        syns = sorted(world.s.in_neighbours(u, "oo_post"),
                      key=lambda s: (world.s.node(s)["attrs"]["drow"],
                                     world.s.node(s)["attrs"]["dcol"],
                                     world.s.node(s)["attrs"]["polarity"]))
        out.extend(float(world.s.node(s)["attrs"]["weight"]) for s in syns)
    return np.array(out, float)


def install_signed_rf(world: WaveWorld, u, G: np.ndarray) -> None:
    """Write a known SIGNED effective RF onto an SUnit by SPLITTING it across the
    two non-negative channels: w_ON = [G]+, w_OFF = [-G]+ .

    This is the exact inverse of `signed_rf` (w_ON - w_OFF == G) and is how the
    ideal reference cell is built for calibration: it is what a PERFECT signed
    simple cell looks like in this architecture, under Dale (both weights >= 0).
    Calibration/positive-control only — never in an arm."""
    rf = int(world.s.node(u)["attrs"]["rf"])
    half = rf // 2
    for syn in world.s.in_neighbours(u, "oo_post"):
        at = world.s.node(syn)["attrs"]
        g = float(G[int(at["drow"]) + half, int(at["dcol"]) + half])
        pol = int(at["polarity"])
        world.s.set_attr(syn, "weight", max(g, 0.0) if pol > 0 else max(-g, 0.0))


def segregation(world: WaveWorld, u) -> dict:
    """H1c's read-out: are the ON and OFF subregions SPATIALLY SEGREGATED and
    ADJACENT (the Hubel & Wiesel structure), or intermixed?

    `seg` is the |correlation| between the ON-minus-OFF sign map and its own
    best-fitting single spatial axis... deliberately NOT that: instead we report
    two model-free descriptives —

      `frac_on`   : fraction of RF locations where w_ON - w_OFF > 0
      `clumpiness`: the fraction of 4-neighbour location pairs inside the RF that
                    share the SIGN of (w_ON - w_OFF). 0.5 = intermixed (a
                    salt-and-pepper RF); ->1.0 = contiguous subregions.

    Pure query. A random sign map gives clumpiness ~0.5, which is the floor the
    calibration states; an ideal Gabor's is measured, not assumed."""
    d = signed_rf(world, u)
    sgn = np.sign(d)
    same = tot = 0
    for r in range(d.shape[0]):
        for c in range(d.shape[1]):
            for dr, dc in ((0, 1), (1, 0)):
                r2, c2 = r + dr, c + dc
                if r2 < d.shape[0] and c2 < d.shape[1]:
                    if sgn[r, c] != 0 and sgn[r2, c2] != 0:
                        tot += 1
                        same += int(sgn[r, c] == sgn[r2, c2])
    return {"frac_on": float((d > 0).mean()),
            "clumpiness": float(same / tot) if tot else float("nan")}


def merge_bipolars(by_eye: dict) -> dict:
    """Merge several eyes' bipolar maps into ONE map keyed (eye, row, col, pol).

    THE TRAP THIS EXISTS TO KILL, measured before it could bite
    (`scripts/two_eyes_binocular_probe.py`): `add_onoff_retina` returns a map
    keyed `(row, col, polarity)`, and two eyes share a coordinate frame. So the
    obvious `merged = {**left, **right}` SILENTLY DROPS AN ENTIRE EYE — 512
    entries where 1024 were expected — and the "binocular" unit it wires reads
    100%% monocular. That is not a crash and not a warning: it is a beautiful,
    publishable, entirely fake ocular-dominance result that passes every
    PROTOCOL §1 check, because the surviving eye really is the only input and
    the cell really is perfectly dominated by it.

    An absence produced by a key collision is evidence of a LOOKUP, not of a
    measurement (§1.1, §12) — the same disease as `.get('Name','')` and a
    guarded division returning 0.0, in dict form.

    So: the eye is part of the key, and the count is ASSERTED. Raises rather
    than returning a short map, because the whole failure mode is that a short
    map looks exactly like a correct one.
    """
    merged: dict = {}
    for eye, bip in by_eye.items():
        for (r, c, pol), nid in bip.items():
            key = (eye, r, c, pol)
            if key in merged:                      # cannot happen; assert anyway
                raise ValueError(
                    f"merge_bipolars: duplicate key {key} — an eye's own map "
                    f"collided with itself.")
            merged[key] = nid
    expected = sum(len(b) for b in by_eye.values())
    if len(merged) != expected:
        raise ValueError(
            f"merge_bipolars: COLLISION — {len(merged)} entries from "
            f"{len(by_eye)} eyes where {expected} were expected. An eye has "
            f"been silently dropped; any ocular-dominance measure taken on "
            f"this map would report dominance that is a key collision.")
    return merged


def bipolars_of_eye(merged: dict, eye) -> dict:
    """Project a merged (eye,row,col,pol) map back to one eye's
    (row,col,pol) map — the shape `add_signed_units` consumes. Mechanical."""
    return {(r, c, p): n for (e, r, c, p), n in merged.items() if e == eye}


__all__ = ["add_onoff_retina", "add_signed_units", "freeze", "thaw",
           "set_params", "signed_rf", "channel_rf", "weights",
           "install_signed_rf", "segregation", "merge_bipolars",
           "bipolars_of_eye"]
