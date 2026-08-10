#!/usr/bin/env python3
"""FRUSTRATED / ANGRY SNAPPING runner (block 242000).

mint -> ingest -> run_rules -> read-off. Drives ``worlds/snap_goal_block_world.py``
to measure the explosive episode (Ross Greene: "kids do well if they can"):

  G-snap-is-threshold (HEADLINE): arousal/frustration builds GRADUALLY but the
    snap OUTPUT is ABRUPT (all-or-none) at the window's UPPER bound; AND -- the
    DISPROPORTION TEETH -- the SAME small trigger produces NO snap at LOW
    accumulated residual but a SNAP at HIGH residual (the "last straw"; the
    glass-box dissolution of "why blow up over THAT"). The snap MAGNITUDE is read
    from the ACCUMULATED residual, NOT the trigger.

  G-window-gates-snapping: narrow window -> snaps SOONER (fewer blocks); monotone
    across >=3 widths, CI-separated. Failable control: at MAX width the same block
    sequence never reaches threshold.

  G-anger-is-directed: an attributable blocking AGENT -> DIRECTED discharge at it
    (anger); an impersonal obstacle -> UNDIRECTED distress (no target).

  G-coreg-interrupts: a regulated caregiver holds arousal below threshold ->
    FEWER/NO snaps vs alone. Failable control: absent/dysregulated caregiver ->
    snaps.

The runner NEVER branches on arousal to decide a snap -- that is the rule set in
``seeds/snap_frustration.json``, riding the REAL AffectiveState.arousal + 239000's
WindowOfTolerance. Protocol frozen in SNAP_PREREG.md.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import tokenize

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.snap_goal_block_world import (          # noqa: E402
    SnapGoalBlockWorld, TRIGGER_MAG, SNAP_CAP)

SEED_BASE = 242000
N = 60

# G-window: half-width levels (the WIDTH knob) -> blocks_to_snap {5, 8, 12}.
WIDTH_LEVELS = [40.0, 70.0, 100.0]
WIDTH_JITTER = 3.0
CONTROL_WIDTH = 400.0            # failable control: never reaches threshold

# G-teeth: prior-block residual levels at half_width = 100.
TEETH_WIDTH = 100.0
LOW_PRIOR = 2                    # F ~= 19.4  -> trigger does NOT snap
HIGH_PRIOR = 11                 # F ~= 97.6  -> the identical trigger DOES snap


def _ci95(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return dict(mean=m, sd=0.0, ci_lo=m, ci_hi=m, n=n)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return dict(mean=m, sd=sd, ci_lo=m - half, ci_hi=m + half, n=n)


def separated(a, b):
    """A's CI lower bound strictly above B's CI upper bound."""
    return a["ci_lo"] > b["ci_hi"]


def overlap(a, b):
    return not (a["ci_lo"] > b["ci_hi"] or b["ci_lo"] > a["ci_hi"])


# -------------------------------------- G-snap (HEADLINE): teeth + abruptness ----
def teeth_arm(n_prior, seed0, n=N, width=TEETH_WIDTH):
    """For each seed deliver n_prior identical blocks then ONE identical trigger;
    read whether THAT trigger fired a snap (the GRAPH decides). The trigger
    magnitude is the SAME in every arm and at every residual -- only the prior
    residual differs. Per SNAP_PREREG.md the window WIDTH is FIXED (=100) for the
    teeth so the mechanism is deterministic (the straw is the trigger, not a
    jittered-narrow window snapping early); the seed varies nothing here, which is
    the correct outcome for a deterministic threshold -- all seeds agree (0 vs 1).
    """
    rows = []
    for _ in range(n):
        w = SnapGoalBlockWorld(half_width=width, trigger_mag=TRIGGER_MAG)
        rows.append(w.snapped_after_prior_blocks(n_prior))
    return dict(
        snapped_on_trigger=_ci95([r["snapped_on_trigger"] for r in rows]),
        snap_magnitude=_ci95([r["snap_magnitude"] for r in rows
                              if r["snapped_on_trigger"]]) if any(
            r["snapped_on_trigger"] for r in rows) else _ci95([0.0]),
        last_trigger_mag=_ci95([r["last_trigger_mag"] for r in rows]),
        rows=rows)


def abruptness_probe(seed=SEED_BASE, width=TEETH_WIDTH):
    """One run: arousal ramps GRADUALLY (max per-tick increment small) while
    snap_count steps 0->1 in a SINGLE tick (all-or-none). The snap magnitude
    (residual) exceeds the window's hi -- arousal crossed the upper bound."""
    w = SnapGoalBlockWorld(half_width=width, trigger_mag=TRIGGER_MAG)
    res = w.run_until_snap()
    traj = w.arousal_trajectory()
    # max per-tick arousal increment BEFORE the snap tick (the gradual ramp).
    incs = []
    for i in range(1, len(traj)):
        prev_count = traj[i - 1][2]
        if traj[i][2] > prev_count:          # the snap tick -- stop measuring ramp
            break
        incs.append(traj[i][1] - traj[i - 1][1])
    max_ramp_inc = max(incs) if incs else 0.0
    # snap_count is integer-valued at every tick (all-or-none, never fractional).
    counts = [c for (_, _, c) in traj]
    all_integer_steps = all(float(c).is_integer() for c in counts)
    return dict(
        blocks_to_snap=res["blocks_to_snap"], snapped=res["snapped"],
        max_ramp_increment=max_ramp_inc, trigger_mag=TRIGGER_MAG,
        snap_magnitude=res["snap_magnitude"], window_hi=width,
        magnitude_exceeds_hi=res["snap_magnitude"] > width,
        magnitude_to_trigger_ratio=(res["snap_magnitude"] / res["last_trigger_mag"]
                                    if res["last_trigger_mag"] else 0.0),
        snap_count_integer_steps=all_integer_steps,
        gradual_build_abrupt_output=(max_ramp_inc <= TRIGGER_MAG + 1e-9
                                     and res["snapped"]))


# ------------------------------------------------ G-window: blocks_to_snap ----
def width_arm(level_mu, seed0, n=N):
    rng = np.random.default_rng(seed0)
    bts = []
    snapped = []
    for _ in range(n):
        w = SnapGoalBlockWorld(
            half_width=float(rng.normal(level_mu, WIDTH_JITTER)),
            trigger_mag=TRIGGER_MAG)
        r = w.run_until_snap()
        bts.append(r["blocks_to_snap"])
        snapped.append(int(r["snapped"]))
    return dict(blocks_to_snap=_ci95(bts), snap_frac=sum(snapped) / len(snapped))


def control_arm(seed0, n=N):
    """FAILABLE CONTROL: at MAX width the same block sequence NEVER snaps."""
    rng = np.random.default_rng(seed0)
    snapped = []
    for _ in range(n):
        w = SnapGoalBlockWorld(half_width=CONTROL_WIDTH, trigger_mag=TRIGGER_MAG)
        snapped.append(int(w.run_until_snap()["snapped"]))
    return dict(snap_frac=sum(snapped) / len(snapped), n=n)


# ------------------------------------------------ G-anger: directed vs not ----
def anger_arm(blocker_present, seed0, n=N):
    rng = np.random.default_rng(seed0)
    directed = []
    undirected = []
    edges = []
    for _ in range(n):
        w = SnapGoalBlockWorld(
            half_width=float(rng.normal(TEETH_WIDTH, WIDTH_JITTER)),
            trigger_mag=TRIGGER_MAG, blocker_present=blocker_present)
        w.run_until_snap()
        a = w.readout()
        directed.append(a["snap_directed"])
        undirected.append(a["snap_undirected"])
        edges.append(len(w.directed_at_edges()))
    return dict(directed_frac=_ci95(directed), undirected_frac=_ci95(undirected),
                directed_at_edge_frac=_ci95([1.0 if e else 0.0 for e in edges]))


# ------------------------------------------------ G-coreg: interrupts snap ----
def coreg_arm(caregiver_present, caregiver_regulated, seed0, n=N):
    rng = np.random.default_rng(seed0)
    snapped = []
    for _ in range(n):
        w = SnapGoalBlockWorld(
            half_width=float(rng.normal(TEETH_WIDTH, WIDTH_JITTER)),
            trigger_mag=TRIGGER_MAG, caregiver_present=caregiver_present,
            caregiver_regulated=caregiver_regulated)
        snapped.append(int(w.run_until_snap()["snapped"]))
    return dict(snap_frac=_ci95(snapped))


# ---------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct a snap episode from graph_to_dict alone: the accumulated
    residual, arousal, window bounds, the small trigger magnitude, the snap
    magnitude (residual, NOT trigger), and the attribution target -- the
    disproportion is READABLE (trigger small, residual at threshold)."""
    w = SnapGoalBlockWorld(half_width=TEETH_WIDTH, trigger_mag=TRIGGER_MAG,
                           blocker_present=True)
    res = w.run_until_snap()
    blob = w.checkpoint()
    nodes = {n["id"]: n for n in blob["nodes"]}
    aff = next(nodes[i]["attrs"] for i in nodes
               if nodes[i]["type"] == "AffectiveState"
               and nodes[i]["attrs"].get("name") == "agent_affect")
    win = next(nodes[i]["attrs"] for i in nodes
               if nodes[i]["type"] == "WindowOfTolerance")
    directed = [(e["src"], e["tgt"]) for e in blob["edges"]
                if e["type"] == "directed_at"]
    return dict(
        frustration_residual=aff["frustration"], arousal=aff["arousal"],
        window_lo=win["lo"], window_hi=win["hi"],
        last_trigger_mag=aff["last_trigger_mag"],
        snap_magnitude=aff["snap_magnitude"], snap_count=aff["snap_count"],
        snap_directed=aff["snap_directed"],
        directed_at_target_edges=len(directed),
        disproportion_readable=(aff["last_trigger_mag"] <= TRIGGER_MAG + 1e-9
                                and aff["snap_magnitude"] > win["hi"]),
        magnitude_from_residual_not_trigger=(
            aff["snap_magnitude"] > 5.0 * aff["last_trigger_mag"]),
        blocks_to_snap=res["blocks_to_snap"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------ source audit ----
def source_audit():
    """No Python decides a snap / attribution / co-regulation. Forbidden: Python
    rule-engine calls, and any reward/punishment token (the snap is a STATE,
    never a badness -- Greene). The adapter's conditionals are over WORLD state."""
    path = os.path.join(_ROOT, "worlds", "snap_goal_block_world.py")
    src = open(path).read()
    code_toks = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        code_toks.append(tok.string)
    code = " ".join(code_toks)
    forbidden_engine = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    forbidden_reward = ["reward", "punish", "penalty", "penalis", "penaliz"]
    eng_hits = [f for f in forbidden_engine if f in code]
    rew_hits = [f for f in forbidden_reward if f in code.lower()]
    return dict(forbidden_engine_hits=eng_hits, forbidden_reward_hits=rew_hits,
                reads_arousal_off_graph=("arousal" in code),
                clean=(not eng_hits and not rew_hits))


# --------------------------------------------------------------- G-discipline ----
def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                          "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        prov = engine_provenance()["source_match"]
    except Exception as e:                      # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "snap_frustration.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("G-snap (headline): disproportion teeth + abruptness ...")
    low = teeth_arm(LOW_PRIOR, SEED_BASE + 10)
    high = teeth_arm(HIGH_PRIOR, SEED_BASE + 20)
    abrupt = abruptness_probe()

    print("G-window: blocks_to_snap vs window WIDTH ...")
    widths = {int(mu): width_arm(mu, SEED_BASE + 100 * (i + 1))
              for i, mu in enumerate(WIDTH_LEVELS)}
    control = control_arm(SEED_BASE + 900)

    print("G-anger: attributable blocker -> directed ...")
    blocker = anger_arm(True, SEED_BASE + 2000)
    obstacle = anger_arm(False, SEED_BASE + 2100)

    print("G-coreg: regulated caregiver interrupts ...")
    alone = coreg_arm(False, 1.0, SEED_BASE + 3000)
    dysreg = coreg_arm(True, 0.0, SEED_BASE + 3100)
    regulated = coreg_arm(True, 1.0, SEED_BASE + 3200)

    lvls = sorted(widths.keys())
    g_snap = dict(
        teeth_low=low["snapped_on_trigger"], teeth_high=high["snapped_on_trigger"],
        teeth_separated=separated(high["snapped_on_trigger"], low["snapped_on_trigger"]),
        high_snap_magnitude=high["snap_magnitude"],
        trigger_mag=low["last_trigger_mag"], abruptness=abrupt)
    g_window = dict(
        widths={str(k): widths[k]["blocks_to_snap"] for k in lvls},
        snap_frac={str(k): widths[k]["snap_frac"] for k in lvls},
        monotone_ci_separated=all(
            separated(widths[lvls[j + 1]]["blocks_to_snap"],
                      widths[lvls[j]]["blocks_to_snap"])
            for j in range(len(lvls) - 1)),
        control_max_width=control,
        control_never_snaps=(control["snap_frac"] == 0.0))
    g_anger = dict(
        blocker=blocker, obstacle=obstacle,
        directed_separated=separated(blocker["directed_frac"], obstacle["directed_frac"]),
        blocker_directs=(blocker["directed_frac"]["mean"] >= 0.95),
        obstacle_undirected=(obstacle["undirected_frac"]["mean"] >= 0.95),
        obstacle_not_directed=(obstacle["directed_frac"]["mean"] <= 0.05))
    g_coreg = dict(
        alone=alone["snap_frac"], dysregulated=dysreg["snap_frac"],
        regulated=regulated["snap_frac"],
        regulated_interrupts_ci_separated=separated(
            alone["snap_frac"], regulated["snap_frac"]),
        dysregulated_still_snaps=overlap(dysreg["snap_frac"], alone["snap_frac"]),
        dysregulated_not_interrupting=separated(
            dysreg["snap_frac"], regulated["snap_frac"]))

    out = dict(
        block=242000, base_sha="bd6af1cbee4f148b4ded201d7e19d3b1ac657b98",
        seed_base=SEED_BASE, n=N, snap_cap=SNAP_CAP, trigger_mag=TRIGGER_MAG,
        width_levels=WIDTH_LEVELS, teeth_low_prior=LOW_PRIOR, teeth_high_prior=HIGH_PRIOR,
        g_snap_is_threshold=g_snap, g_window_gates_snapping=g_window,
        g_anger_is_directed=g_anger, g_coreg_interrupts=g_coreg,
        g_glass_box=glass_box_reconstruct(), source_audit=source_audit(),
        discipline=discipline(),
        prior_art=(
            "SYNTHETIC model of the explosive-episode / window-of-tolerance / "
            "frustration-aggression frameworks. CONCEDES as prior art (NOT "
            "claimed): appraisal-theory anger (OCC; EMA/Gratch-Marsella), the "
            "frustration-aggression hypothesis (Dollard 1939; Berkowitz), "
            "RL-frustration (blocked-reward RPE). CLAIMS ONLY: the snap as a "
            "THRESHOLD-crossing of the ACCUMULATED residual against a SETTABLE "
            "window, unified on ONE substrate with co-regulation (239000) that "
            "interrupts it, the window WIDTH (241000) that gates it, and the "
            "glass-box disproportion-readable dissolution of 'why blow up over "
            "THAT' -- Greene's explosive child mechanised. Mechanism-proven, NOT "
            "a clinical-outcome number."))
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "snap.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
