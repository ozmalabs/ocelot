#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R2 -- THE CYCLE OF ABUSE as a LIMIT CYCLE, runner
(block 286000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r2_cycle_limit_world.py` across TWO arms sharing IDENTICAL
machinery -- only whether the abuser's tension-building driver is present
differs:

  cycle                -- a constant, jittered per-tick tension trickle onto
                           the abuser's GoalBlock (the "incident driver").
  constant_regulation   -- NO tension trickle at all (the failable control,
                           per ABUSIVE_RELATIONSHIPS_SCOPING.md Part E, R2).

and measures the OSCILLATION of the victim's arousal (the read-off metric is
the standard deviation of `victim_arousal` over a post-warmup window -- a
concrete, glass-box amplitude measure; the abuser's own `snap_count` and the
mean inter-snap interval are reported as corroborating, non-gated,
descriptive read-offs of the SAME orbit's period). The runner NEVER branches
on either agent's graph state to decide the oscillation -- that is the
graph's own leaky-integrate-fire + entrainment dynamics. It only evaluates
the frozen protocol (which arm's driver to deliver) and reduces the
read-offs to statistics.

Protocol frozen in ABUSIVE_R2_CYCLE_LIMIT_PREREG.md, which locks Part C of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim.
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

import substrate_rs as srs                                    # noqa: E402
from worlds.abusive_r2_cycle_limit_world import (              # noqa: E402
    AbusiveR2CycleLimitWorld, ABUSER_HALF_WIDTH, VICTIM_HALF_WIDTH,
    LEAK, K_ACC, DISCHARGE, RECOVER_FLOOR, K_SELF, K_CO,
    TRICKLE_MAG, TRICKLE_JITTER_FRAC)

SEED_BASE = 286000
N = 200
T = 400            # ticks per episode (>= 15 abuser incident cycles at the
#                     frozen constants -- see PREREG Sec. 3.2)
WARMUP = 60         # ticks excluded from the oscillation read-off (the
#                     initial tension-building ramp before the first
#                     incident -- not yet a "cycle")
ARM_NAMES = ("cycle", "constant_regulation")


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
    """True iff arm A's CI lower bound is strictly above arm B's CI upper
    bound (A CI-separated ABOVE B)."""
    return a["ci_lo"] > b["ci_hi"]


# --------------------------------------------------------------- main measurement
def run_episode_metrics(driver_on, seed):
    """One episode: run T ticks, read the oscillation metrics off the log.
    NO decision here -- the log is graph read-offs; the metrics below are
    mechanical reductions (std / count / mean), never a judgement about the
    victim's state."""
    rng = np.random.default_rng(seed) if driver_on else None
    w = AbusiveR2CycleLimitWorld()
    log = w.run_episode(T, driver_on=driver_on, rng=rng)
    va_post = [row["victim_arousal"] for row in log[WARMUP:]]
    std = float(np.std(va_post))
    final_snap_count = log[-1]["abuser_snap_count"]
    dysreg_frac = sum(1 for row in log if row["victim_dysregulated"] == 1.0) / len(log)
    final_half_width = log[-1]["victim_half_width"]
    # mean inter-snap interval (period), from the snap_count step points.
    snap_ticks = []
    prev = 0.0
    for i, row in enumerate(log):
        if row["abuser_snap_count"] > prev:
            snap_ticks.append(i + 1)
            prev = row["abuser_snap_count"]
    intervals = [snap_ticks[i + 1] - snap_ticks[i] for i in range(len(snap_ticks) - 1)]
    mean_interval = float(np.mean(intervals)) if intervals else None
    return dict(std=std, final_snap_count=final_snap_count,
                dysreg_frac=dysreg_frac, final_half_width=final_half_width,
                n_snaps=len(snap_ticks), mean_interval=mean_interval)


def run_arm(arm, seed_base=SEED_BASE, n=N):
    driver_on = (arm == "cycle")
    rows = [run_episode_metrics(driver_on, seed_base + i) for i in range(n)]
    stds = [r["std"] for r in rows]
    snap_counts = [r["final_snap_count"] for r in rows]
    dysreg_fracs = [r["dysreg_frac"] for r in rows]
    intervals = [r["mean_interval"] for r in rows if r["mean_interval"] is not None]
    return dict(
        arm=arm, n=n, driver_on=driver_on,
        std=_ci95(stds),
        final_snap_count=_ci95(snap_counts),
        dysreg_frac=_ci95(dysreg_fracs),
        mean_inter_snap_interval=(_ci95(intervals) if intervals else None),
        n_episodes_with_snaps=sum(1 for r in rows if r["n_snaps"] > 0))


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one cycle-arm episode's oscillation entirely from
    graph_to_dict: the attended_by edge, the abuser's frustration/arousal/
    snap_count, the victim's arousal/window. No hidden Python state -- read
    from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveR2CycleLimitWorld()
    w.run_episode(T, driver_on=True, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    aaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    vaff = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    attended = [(e["src"], e["tgt"]) for e in blob["edges"] if e["type"] == "attended_by"]
    return dict(
        attended_by_edges=len(attended),
        abuser_frustration=aaff["frustration"], abuser_arousal=aaff["arousal"],
        abuser_snap_count=aaff["snap_count"],
        victim_arousal=vaff["arousal"], victim_half_width=vwot["half_width"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Checkpoint
    the neutral (pre-induction) mind; induce the MINIMUM (per Part C.3) --
    one tension-building -> incident -> honeymoon cycle (~90 ticks is enough
    for one full snap+recovery at the frozen constants, PREREG Sec. 3.2);
    measure; then graph_from_dict the checkpoint into a FRESH substrate and
    assert graph_to_dict() is BYTE-IDENTICAL to the checkpoint, and that the
    restored mind is NON-ORIENTED (identical to the pre-induction neutral
    state)."""
    w = AbusiveR2CycleLimitWorld()
    pre = w.checkpoint()                        # neutral, pre-induction
    pre_state = dict(abuser_arousal=w._attrs(w.aaff)["arousal"],
                      abuser_frustration=w._attrs(w.aaff)["frustration"],
                      victim_arousal=w._attrs(w.vaff)["arousal"])

    rng = np.random.default_rng(seed)
    w.run_episode(induce_ticks, driver_on=True, rng=rng)   # INDUCE + measure
    induced_state = dict(abuser_arousal=w._attrs(w.aaff)["arousal"],
                          abuser_frustration=w._attrs(w.aaff)["frustration"],
                          victim_arousal=w._attrs(w.vaff)["arousal"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    r_aaff = [nd["attrs"] for nd in restored["nodes"]
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "abuser_affect"][0]
    r_vaff = [nd["attrs"] for nd in restored["nodes"]
              if nd["type"] == "AffectiveState" and nd["attrs"].get("name") == "victim_affect"][0]
    restored_state = dict(abuser_arousal=r_aaff["arousal"],
                           abuser_frustration=r_aaff["frustration"],
                           victim_arousal=r_vaff["arousal"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_abuser=(induced_state["abuser_frustration"] != pre_state["abuser_frustration"]),
        induction_moved_victim=(induced_state["victim_arousal"] != pre_state["victim_arousal"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r2_cycle_limit_world.py + seeds/abusive_r2_cycle_limit.json
    for Python rule-engine calls and the literal banned shaping tokens named
    verbatim in Part C.2 of ABUSIVE_RELATIONSHIPS_SCOPING.md: `reward_signal`
    / `punish` / `reinforce` / `backprop` / `gradient`. The audit scans the
    graph's DECISION SURFACE (rule names + the attr "key"s the new rule
    actually reads/writes), never the free-text "description" / clinical
    "microtheory" prose -- matching R1's own precedent (an earlier draft's
    prose legitimately used clinical vocabulary describing what the
    mechanism does NOT do; scoping the audit to code with comments/strings
    stripped + the rule decision surface avoids that false positive)."""
    forbidden_engine = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    forbidden_shaping = ["reward_signal", "punish", "reinforce", "backprop", "gradient"]

    def _code_only(path):
        src = open(path).read()
        toks = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            toks.append(tok.string)
        return " ".join(toks), src

    py_path = os.path.join(_ROOT, "worlds", "abusive_r2_cycle_limit_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r2_cycle_limit.json")
    seed = json.load(open(seed_path))

    def _walk_keys(obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "key":
                    out.append(str(v))
                _walk_keys(v, out)
        elif isinstance(obj, list):
            for v in obj:
                _walk_keys(v, out)
    rule_surface = [r["name"] for r in seed["rules"]]
    _walk_keys(seed["rules"], rule_surface)
    _walk_keys(seed["productions"], rule_surface)
    seed_surface = " ".join(rule_surface).lower()
    haystacks = [code.lower(), seed_surface]

    eng_hits = [f for f in forbidden_engine if f in code]
    shape_hits = [f for h in haystacks for f in forbidden_shaping if f in h]
    shape_hits = sorted(set(shape_hits))
    reads_off_graph = ("self._attrs(self.vaff)" in src and "self._attrs(self.aaff)" in src)
    return dict(forbidden_engine_hits=eng_hits, forbidden_shaping_hits=shape_hits,
                reads_off_graph=reads_off_graph,
                clean=(not eng_hits and not shape_hits))


# --------------------------------------------------------------- G-discipline ----
def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                           "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        prov = engine_provenance()["source_match"]
    except Exception as e:                       # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r2_cycle_limit.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        n_new_rules=len(seed["rules"]),
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R2 -- THE CYCLE OF ABUSE: cycle arm vs constant-regulation control ...")
    arms = run_all_arms()
    cyc = arms["cycle"]["std"]
    ctl = arms["constant_regulation"]["std"]

    g_headline = dict(
        arms={k: v["std"] for k, v in arms.items()},
        cycle_ci_separated_above_control=separated(cyc, ctl),
        headline_pass=separated(cyc, ctl))

    out = dict(
        block=286000, seed_base=SEED_BASE, n=N, t_ticks=T, warmup_ticks=WARMUP,
        abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
        leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
        k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        trickle_jitter_frac=TRICKLE_JITTER_FRAC,
        arms=arms,
        g_headline=g_headline,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r2_cycle_limit.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
