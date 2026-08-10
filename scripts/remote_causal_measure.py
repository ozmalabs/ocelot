"""remote_causal_measure — RUNG 228000: REMOTE CAUSATION (interventional causal
discovery across space).

Measures, behind protected controls, whether the agent:
  G-exhaustion-drives-exploration  navigates to the only-remaining-salient object
                        after exhausting known options, WITH NO prior causal model,
                        CI-separated above `causal_prior` (only moves toward an
                        already-hypothesised object -> never goes).
  G-remote-attribution  (HEADLINE) correctly attributes the remote effect at B to the
                        interaction at A ACROSS SPACE, CI-separated above a LOCAL-ONLY
                        control (attributes only at B's location) AND a NO-INTERVENTION
                        control (passive co-occurrence -> confabulates). Pair-scored
                        (Family A ∧ Family B both correct: needs spatial reach AND
                        interventional discipline). Two configs (first + held-out).
  G-action-furthers-posit  the action to further the posit is INTERACT-WITH-THE-CROSS +
                        observe the remote effect (measured on a trace) — not a local
                        block-probe.
  G-pass-via-remote     the full loop PASSES on a genuinely-remote board vs the 227-style
                        local_only model which CANNOT (non-local effect), CI-separated.
  G-general             the SAME rules work on ls20-shaped (cross->shape) AND Doom-shaped
                        (lever->door) boards — domain-agnostic by construction.

HONEST SCOPE (standing rule — synthetic-proven != benchmark value): a clean confounded
causal-discovery world; the interventional facts are OBSERVED by running the probe
world-model (act vs no-op), the RULES produce the verdict. LIVE ls20 is the separate
honest half.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/remote_causal_measure.py --n 24
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.remote_causal import (  # noqa: E402
    make_attribution_scenario, run_attribution_vignette, correct_verdict,
    make_remote_board, run_grid_episode,
)
from domains.remote_causal_seed import RULES  # noqa: E402

ATTR_ARMS = ("remote", "local_only", "no_intervention")
GRID_ARMS = ("remote", "local_only", "no_intervention", "causal_prior")
FLAVOURS = ("ls20", "doom")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def sep(a_ci, b_ci):
    return a_ci[1] > b_ci[2]


# ===========================================================================
# G-remote-attribution (HEADLINE) — pair-scored across Families A + B.
# ===========================================================================
def measure_attribution(n, seed):
    rng = np.random.default_rng(seed)
    # per flavour + combined
    per_flav = {}
    pair_hits = {a: 0 for a in ATTR_ARMS}
    famA_hits = {a: 0 for a in ATTR_ARMS}
    famB_hits = {a: 0 for a in ATTR_ARMS}
    total_pairs = 0
    for flavour in FLAVOURS:
        fa = {a: 0 for a in ATTR_ARMS}
        fb = {a: 0 for a in ATTR_ARMS}
        pr = {a: 0 for a in ATTR_ARMS}
        for _ in range(n):
            scnA = make_attribution_scenario(rng, "A", flavour=flavour)
            scnB = make_attribution_scenario(rng, "B", flavour=flavour)
            for a in ATTR_ARMS:
                okA = correct_verdict(run_attribution_vignette(scnA["truth"], scnA["objects"], a),
                                      "A", scnA["truth"], scnA["objects"])
                okB = correct_verdict(run_attribution_vignette(scnB["truth"], scnB["objects"], a),
                                      "B", scnB["truth"], scnB["objects"])
                fa[a] += int(okA); fb[a] += int(okB); pr[a] += int(okA and okB)
                famA_hits[a] += int(okA); famB_hits[a] += int(okB); pair_hits[a] += int(okA and okB)
            total_pairs += 1
        per_flav[flavour] = {
            "n": n,
            "famA_rate": {a: wilson(fa[a], n) for a in ATTR_ARMS},
            "famB_rate": {a: wilson(fb[a], n) for a in ATTR_ARMS},
            "pair_rate": {a: wilson(pr[a], n) for a in ATTR_ARMS},
        }
    return {
        "per_flavour": per_flav,
        "combined_pair_rate": {a: wilson(pair_hits[a], total_pairs) for a in ATTR_ARMS},
        "combined_famA_rate": {a: wilson(famA_hits[a], total_pairs) for a in ATTR_ARMS},
        "combined_famB_rate": {a: wilson(famB_hits[a], total_pairs) for a in ATTR_ARMS},
        "total_pairs": total_pairs,
    }


# ===========================================================================
# G-exhaustion + G-pass-via-remote — grid boards, both flavours.
# ===========================================================================
def measure_grid(n, seed):
    rng = np.random.default_rng(seed)
    per_flav = {}
    reach = {a: 0 for a in GRID_ARMS}
    passed = {a: 0 for a in GRID_ARMS}
    total = 0
    for flavour in FLAVOURS:
        rc = {a: 0 for a in GRID_ARMS}
        pa = {a: 0 for a in GRID_ARMS}
        for _ in range(n):
            scn = make_remote_board(rng, flavour=flavour)
            for a in GRID_ARMS:
                res = run_grid_episode(scn, a, budget=200)
                rc[a] += int(res["reached_cross"]); pa[a] += int(res["win"])
                reach[a] += int(res["reached_cross"]); passed[a] += int(res["win"])
            total += 1
        per_flav[flavour] = {
            "n": n,
            "reach_cross_rate": {a: wilson(rc[a], n) for a in GRID_ARMS},
            "pass_rate": {a: wilson(pa[a], n) for a in GRID_ARMS},
        }
    return {
        "per_flavour": per_flav,
        "combined_reach_cross_rate": {a: wilson(reach[a], total) for a in GRID_ARMS},
        "combined_pass_rate": {a: wilson(passed[a], total) for a in GRID_ARMS},
        "total": total,
    }


# ===========================================================================
# G-action-furthers-posit — the action trace of the `remote` arm.
# ===========================================================================
def action_trace(seed):
    rng = np.random.default_rng(seed)
    scn = make_remote_board(rng, flavour="ls20")
    res = run_grid_episode(scn, "remote", budget=200, trace=True)
    tr = res["trace"]
    known_probe = next((t for t in tr if t["waypoint"] == "goal" and not t["b_matches"]), None)
    exhaust = next((t for t in tr if t["explore_mode"] == 1.0), None)
    seek_cross = next((t for t in tr if t["waypoint"] == "object"), None)
    attributed = next((t for t in tr if t["attributed_remote"] == 1.0), None)
    passed = next((t for t in tr if t["waypoint"] == "goal" and t["b_matches"]), None)
    return {
        "board": {"avatar": scn["avatar_rc"], "block": scn["block_rc"],
                  "remote_switch": scn["remote_obj_rc"]},
        "known_probe": (f"probed the block AS-IS at step {known_probe['step']} -> did NOT pass"
                        if known_probe else "n/a"),
        "exhaust": (f"exhausted known option -> explore_mode at step {exhaust['step']}"
                    if exhaust else "n/a"),
        "action_to_further_posit": (
            f"navigated toward the ONLY un-visited salient object (the remote switch) "
            f"at step {seek_cross['step']} -> interacted (NOT a local block-probe)"
            if seek_cross else "n/a"),
        "attributed_across_space": (
            f"attributed B's change to the remote switch across space at step "
            f"{attributed['step']}" if attributed else "n/a"),
        "passed_via_remote": (f"operated the switch -> B matched -> passed at step {passed['step']}"
                              if passed else "did NOT pass"),
        "reached_cross": res["reached_cross"], "attributed_remote": res["attributed_remote"],
        "won": res["win"], "confirmed": res["confirmed"],
        "action_is_interact_not_local_probe": bool(seek_cross is not None
                                                    and res["attributed_remote"] == 1.0),
    }


# ===========================================================================
# 226 frustration tie-in — the futile causal_prior cycle is broken; the remote
# exhaustion->explore->discover trajectory is not.
# ===========================================================================
def frustration_tie_in(seed):
    from domains.frustration_world import FrustrationWorld
    rng = np.random.default_rng(seed)
    scn = make_remote_board(rng, flavour="ls20")
    cyc = run_grid_episode(scn, "causal_prior", budget=60, trace=True)
    rem = run_grid_episode(scn, "remote", budget=60, trace=True)

    # causal_prior: never explores -> blind cycle, recurrent positions, no gain.
    wc = FrustrationWorld(enabled=True)
    cyc_break = None
    for i, t in enumerate(cyc["trace"]):
        _, brk = wc.observe(f"pos:{t['pos']}", d_hyp=0, d_state=0, s_drop=0)
        if brk == 1.0 and cyc_break is None:
            cyc_break = i
    cyc_final = wc.observe("pos:end", 0, 0, 0)[0]

    # remote: exhaustion->explore->discovery makes genuine progress (d_state=1) and
    # understanding gains (posit resolves / attribution / match flips = d_hyp=1).
    ws = FrustrationWorld(enabled=True)
    prev = (0.0, False)
    rem_break = None
    for i, t in enumerate(rem["trace"]):
        gain = int(t["explore_mode"] != prev[0] or t["b_matches"] != prev[1]
                   or t["attributed_remote"] == 1.0)
        prev = (t["explore_mode"], t["b_matches"])
        _, brk = ws.observe(f"pos:{t['pos']}", d_hyp=gain, d_state=1, s_drop=0)
        if brk == 1.0 and rem_break is None:
            rem_break = i
    rem_final = ws.observe("pos:done", 1, 1, 0)[0]
    return {
        "causal_prior_break_step": cyc_break,
        "causal_prior_final_frustration": cyc_final,
        "causal_prior_broke_the_loop": cyc_break is not None,
        "remote_break_step": rem_break,
        "remote_final_frustration": rem_final,
        "remote_broke_the_loop": rem_break is not None,
        "anti_cycle_holds": (cyc_break is not None and rem_break is None),
    }


# ===========================================================================
# G-graph-native / source-audit.
# ===========================================================================
def source_audit():
    # scan ONLY the executable parts (match/where/effects) — the LOGIC must be
    # domain-agnostic. Comments are prose (a reviewer reads them, the engine does not).
    exec_blob = json.dumps([{"match": r.get("match"), "where": r.get("where"),
                             "effects": r.get("effects")} for r in RULES]).lower()
    banned = ["ls20", "cross", "lever", "door", "switch", "rotation", "rotation90",
              "reflection", "rotate", "recolour", "shape"]
    token_hits = [w for w in banned if w in exec_blob]
    blob = exec_blob
    # the go-to-cross (exploration) decision must read ONLY visited/salience/exhaustion —
    # never a hardcoded causal attr. Check rc_seek_novel_salient's where.
    explore = next((r for r in RULES if r["name"] == "rc_seek_novel_salient"), None)
    ew = json.dumps(explore.get("where", {})) if explore else ""
    explore_reads = sorted(set(
        w for w in ("visited", "salient", "explore_mode", "symbol_matches_goal",
                    "eff_act", "eff_noop", "passive_cooccur", "is_local", "link_status",
                    "obj_id", "status")
        if f'"{w}"' in ew))
    explore_clean = set(explore_reads) <= {"visited", "salient", "explore_mode",
                                           "symbol_matches_goal"}
    # NO rule sets a confirmed link directly from flash/perception without the
    # interventional facts: confirm reads eff_act/eff_noop (interventional) or
    # passive_cooccur (the labelled control). A hardcoded-shortcut = a rule that
    # sets link status "confirmed" without reading eff_* or passive_cooccur.
    shortcut = []
    for r in RULES:
        effs = json.dumps(r.get("effects", []))
        where = json.dumps(r.get("where", {}))
        if '"confirmed"' in effs and not (
                "eff_act" in where or "eff_noop" in where or "passive_cooccur" in where):
            shortcut.append(r["name"])
    return {"rule_count": len(RULES), "banned_tokens_found": token_hits,
            "explore_rule_reads": explore_reads, "explore_reads_only_visited_salience": explore_clean,
            "confirm_without_intervention_shortcut": shortcut,
            "clean": (not token_hits and explore_clean and not shortcut)}


def source_match():
    """seed builder -> json round-trips byte-stable."""
    from domains.remote_causal_seed import manifest
    p = _ROOT / "seeds" / "remote_causal.json"
    on_disk = p.read_text() if p.exists() else ""
    fresh = json.dumps(manifest(), indent=1)
    return on_disk == fresh


def check_gates(attr_first, attr_held, grid):
    g = {}
    # G-exhaustion: remote reach-cross CI-sep above causal_prior (combined).
    rcr = grid["combined_reach_cross_rate"]
    g["G_exhaustion_drives_exploration"] = sep(rcr["remote"], rcr["causal_prior"])
    # G-remote-attribution (HEADLINE): remote pair-rate CI-sep above BOTH controls, both configs.
    def headline(res):
        pr = res["combined_pair_rate"]
        return sep(pr["remote"], pr["local_only"]) and sep(pr["remote"], pr["no_intervention"])
    g["G_remote_attribution"] = headline(attr_first) and headline(attr_held)
    # G-pass-via-remote: remote pass CI-sep above local_only (combined).
    pr = grid["combined_pass_rate"]
    g["G_pass_via_remote"] = sep(pr["remote"], pr["local_only"])
    # G-general: the doom flavour reproduces the pattern (remote confirms across space;
    # local_only/no_int fail) in BOTH attribution and grid.
    df = attr_first["per_flavour"]["doom"]
    dg = grid["per_flavour"]["doom"]
    g["G_general_doom"] = (sep(df["pair_rate"]["remote"], df["pair_rate"]["local_only"])
                           and sep(df["pair_rate"]["remote"], df["pair_rate"]["no_intervention"])
                           and sep(dg["pass_rate"]["remote"], dg["pass_rate"]["local_only"])
                           and sep(dg["reach_cross_rate"]["remote"], dg["reach_cross_rate"]["causal_prior"]))
    # numbers for the report
    g["remote_pair_first"] = attr_first["combined_pair_rate"]["remote"]
    g["local_only_pair_first"] = attr_first["combined_pair_rate"]["local_only"]
    g["no_intervention_pair_first"] = attr_first["combined_pair_rate"]["no_intervention"]
    g["remote_reach_combined"] = rcr["remote"]
    g["causal_prior_reach_combined"] = rcr["causal_prior"]
    g["remote_pass_combined"] = pr["remote"]
    g["local_only_pass_combined"] = pr["local_only"]
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed", type=int, default=228000)
    args = ap.parse_args()

    attr_first = measure_attribution(args.n, args.seed)
    attr_held = measure_attribution(args.n, args.seed + 1)
    grid = measure_grid(args.n, args.seed + 5)
    trace = action_trace(args.seed + 7)
    frust = frustration_tie_in(args.seed + 3)
    audit = source_audit()
    smatch = source_match()
    gates = check_gates(attr_first, attr_held, grid)

    result = {
        "rung": 228000,
        "commitment": "REMOTE CAUSATION: exhaustion-first exploration (reach the only un-visited "
                      "salient object with NO prior causal model) -> intervene -> DISCOVER the "
                      "remote-causal link by the interventional do-contrast (act->effect vs "
                      "no-op->no-effect), attributing B's change ACROSS SPACE -> act -> pass. "
                      "Controls: causal_prior (no exploration), local_only (attributes only at "
                      "B's location), no_intervention (passive co-occurrence -> confabulates). "
                      "Same rules on ls20 (cross->shape) AND Doom (lever->door).",
        "attribution_first": attr_first, "attribution_held_out": attr_held,
        "grid": grid, "action_trace": trace, "frustration_anti_cycle_226": frust,
        "source_audit": audit, "source_match": smatch, "gates": gates,
        "note": "A clean confounded causal-discovery world; interventional facts OBSERVED by the "
                "probe world-model (do vs no-op), the RULES produce the verdict. LIVE ls20 is the "
                "separate honest half.",
    }
    out = _ROOT / "results" / "remote_causal_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    def fmt(ci):
        return f"{ci[0]:.3f} [{ci[1]:.3f}, {ci[2]:.3f}]"

    print("=== RUNG 228000 — REMOTE CAUSATION (interventional causal discovery across space) ===")
    print(f"\nG-remote-attribution (HEADLINE, pair-scored A∧B) — combined over both flavours, N pairs={attr_first['total_pairs']}")
    for tag, res in (("FIRST", attr_first), ("HELD-OUT", attr_held)):
        print(f"  {tag}")
        for a in ATTR_ARMS:
            print(f"    {a:16s} pair={fmt(res['combined_pair_rate'][a])}  "
                  f"famA={fmt(res['combined_famA_rate'][a])}  famB={fmt(res['combined_famB_rate'][a])}")
    print(f"\nG-exhaustion-drives-exploration + G-pass-via-remote — grid, N boards={grid['total']}")
    for a in GRID_ARMS:
        print(f"  {a:16s} reach_cross={fmt(grid['combined_reach_cross_rate'][a])}  "
              f"pass={fmt(grid['combined_pass_rate'][a])}")
    print(f"\nG-general (Doom flavour lever->door):")
    df = attr_first["per_flavour"]["doom"]; dg = grid["per_flavour"]["doom"]
    for a in ATTR_ARMS:
        print(f"  {a:16s} doom-pair={fmt(df['pair_rate'][a])}")
    for a in GRID_ARMS:
        print(f"  {a:16s} doom-reach={fmt(dg['reach_cross_rate'][a])} doom-pass={fmt(dg['pass_rate'][a])}")
    print(f"\nsource audit: {audit}")
    print(f"source_match (seed round-trips): {smatch}")
    print(f"frustration anti-cycle (226): {frust}")
    print("\nACTION TRACE (the action that furthers the posit):")
    for k in ("board", "known_probe", "exhaust", "action_to_further_posit",
              "attributed_across_space", "passed_via_remote", "action_is_interact_not_local_probe"):
        print(f"  {k:30s}: {trace[k]}")
    print(f"\nGATES: {json.dumps(gates, default=str, indent=1)}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
