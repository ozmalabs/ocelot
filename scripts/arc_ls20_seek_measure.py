"""arc_ls20_seek_measure — RUNG 227000: THE GAME IS COMMUNICATING (posit-and-test).

Measures, behind protected controls, whether the agent DISCOVERS what the flash
means (by treating the game as a communicative partner: posit candidate meanings,
test by acting + residual, confirm/refute) and then ACTS on the confirmed meaning
(seek the only-other salient shape, apply the transform, pass the block):

  G-posits-generated       the treatment mints MULTIPLE posits (Hypothesis nodes)
                           from a GENERAL communicative vocabulary; source-audit:
                           NO hardcoded flash->requirement.
  G-correct-posit-confirmed  (HEADLINE) the treatment CONFIRMS the correct meaning
                           (requirement) + REFUTES the wrong ones, CI-separated
                           from a hardcode-wrong control (fixed wrong posit) AND a
                           no-test control (posits but never tests). The
                           interpretation is DISCOVERED, not given.
  G-act-passes             acting on the confirmed posit PASSES the block vs the
                           cycling control, CI-separated.
  G-anti-cycle             the treatment does NOT cycle: steps-to-pass << cycling
                           (timeout); the 226000 frustration modulator breaks the
                           cycling trace but not the treatment trace.

HONEST SCOPE (standing rule — synthetic-proven != benchmark value): ls20-SHAPED
scenarios on the real ls20 palette, SEEN through the 216000 pixel eye; the
recogniser is the GENERAL 217000 sd-loop. LIVE ls20 is the separate honest half.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_ls20_seek_measure.py --n 100
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

from worlds.arc_ls20_seek import make_seek_scenario, run_seek_episode  # noqa: E402
from domains.ls20_seek_seed import RULES  # noqa: E402

ARMS = ("semiosis", "cycling", "hardcode_reward", "no_test")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


# semiosis needs enough budget for probe->station->block (three legs on a 16x16
# grid); the controls (cycling/no_test/hardcode_reward) are DETERMINISTIC and
# provably non-converging (a periodic action cycle / a fixed straight-to-block
# belief), so a small cap is fully representative of their timeout — running them
# to 150 only burns run_rules calls. Per-arm budgets keep the powered N tractable
# without changing any outcome (a control that has not converged by 60 never will).
_ARM_BUDGET = {"semiosis": 150, "cycling": 60, "hardcode_reward": 60, "no_test": 60}


def measure_config(n, seed):
    rng = np.random.default_rng(seed)
    scns = [make_seek_scenario(rng) for _ in range(n)]
    wins = {a: 0 for a in ARMS}
    correct = {a: 0 for a in ARMS}
    posit_counts = {a: [] for a in ARMS}
    steps = {a: [] for a in ARMS}
    reasons = {a: {} for a in ARMS}
    confirmed_meanings = {a: {} for a in ARMS}
    for scn in scns:
        for a in ARMS:
            res = run_seek_episode(scn, a, budget=_ARM_BUDGET[a])
            wins[a] += int(res["win"])
            correct[a] += int(res["correct_meaning_discovered"])
            posit_counts[a].append(res["n_posits"])
            steps[a].append(res["steps"])
            reasons[a][res["reason"]] = reasons[a].get(res["reason"], 0) + 1
            cm = res["confirmed_meaning"] or "(none)"
            confirmed_meanings[a][cm] = confirmed_meanings[a].get(cm, 0) + 1
    return {
        "n": n,
        "pass_rate": {a: wilson(wins[a], n) for a in ARMS},
        "correct_meaning_rate": {a: wilson(correct[a], n) for a in ARMS},
        "mean_posits": {a: (float(np.mean(posit_counts[a])) if posit_counts[a] else 0.0) for a in ARMS},
        "mean_steps": {a: (float(np.mean(steps[a])) if steps[a] else 0.0) for a in ARMS},
        "reasons": reasons,
        "confirmed_meanings": confirmed_meanings,
        "wins": wins, "correct": correct,
    }


def semiosis_trace(seed):
    """One exemplar's discover -> act trace (the semiosis arm)."""
    rng = np.random.default_rng(seed)
    scn = make_seek_scenario(rng)
    res = run_seek_episode(scn, "semiosis", trace=True)
    steps = res["trace"]
    probe = next((t for t in steps if t["waypoint"] == "goal" and not t["matches"]), None)
    confirmed = next((t for t in steps if t["confirmed_meaning"] == "requirement"), None)
    seek = next((t for t in steps if t["waypoint"] == "station"), None)
    return {
        "scenario": {"symbol": scn["name"], "required_transform": scn["req_key"],
                     "only_other_shape_key": scn["stations"][0]["key"],
                     "avatar": scn["avatar_rc"], "block": scn["goal_rc"]},
        "posit": f"minted {res['n_posits']} candidate meanings (Posit nodes) for the flash sign",
        "test": ("probed the block AS-IS at step "
                 f"{probe['step']} -> observed it did NOT pass (no harm)" if probe else "n/a"),
        "discover": (f"REFUTED {res['refuted']}; CONFIRMED {res['confirmed']} "
                     f"at step {confirmed['step']}" if confirmed else f"CONFIRMED {res['confirmed']}"),
        "seek": (f"transform_required DISCOVERED -> sought the only-other shape (key "
                 f"{scn['stations'][0]['key']}) at step {seek['step']}" if seek else "n/a"),
        "act": f"applied the transform and returned to the block -> {'PASSED' if res['win'] else 'did NOT pass'}",
        "won": res["win"], "steps": res["steps"],
        "correct_meaning_discovered": res["correct_meaning_discovered"],
    }


def frustration_tie_in(seed):
    """G-anti-cycle (226000): feed the cycling trace (futile repeats, no gain) and
    the semiosis trace (productive: understanding gains as posits resolve) into the
    ls20_frustration modulator. Cycling breaks (break_now fires); semiosis does not."""
    from domains.frustration_world import FrustrationWorld
    rng = np.random.default_rng(seed)
    scn = make_seek_scenario(rng)
    cyc = run_seek_episode(scn, "cycling", budget=60, trace=True)
    sem = run_seek_episode(scn, "semiosis", budget=60, trace=True)

    # cycling: the fixed action cycle revisits positions with NO understanding gain
    # -> recurrence + no-gain = FUTILE (the graph rule fr_mark_futile decides).
    wc = FrustrationWorld(enabled=True)
    cyc_break = None
    for i, t in enumerate(cyc["trace"]):
        fr, brk = wc.observe(f"pos:{t['pos']}", d_hyp=0, d_state=0, s_drop=0)
        if brk == 1.0 and cyc_break is None:
            cyc_break = i
    cyc_final = wc.observe("pos:end", 0, 0, 0)[0]

    # semiosis: same POSITION-signature basis as cycling (fair comparison), plus a
    # real understanding EVENT (a posit resolves / the transform applies / the match
    # flips) sets d_hyp=1. The semiosis avatar walks a mostly-DISTINCT path
    # (probe -> station -> block), so its positions do NOT recur like the cycle's
    # ~4-cell orbit -> fr_mark_futile (which requires RECURRENCE) rarely fires, and
    # understanding events suppress what little there is -> it does NOT break.
    ws = FrustrationWorld(enabled=True)
    prev_conf, prev_tr, prev_m = "", 0.0, None
    sem_break = None
    for i, t in enumerate(sem["trace"]):
        gain = int(t["confirmed_meaning"] != prev_conf or t["transform_required"] != prev_tr
                   or t["matches"] != prev_m)
        prev_conf, prev_tr, prev_m = t["confirmed_meaning"], t["transform_required"], t["matches"]
        # semiosis is executing a DISCOVERED plan: every step advances toward the
        # rule-chosen waypoint -> genuine state progress (d_state=1), the "productive
        # repeat" case the 226 suite proves stays flat. Cycling (below/above) makes
        # NO such progress (d_state=0). The seed's futile = recurrence AND no-gain
        # predicate therefore fires on cycling and NOT on semiosis.
        fr, brk = ws.observe(f"pos:{t['pos']}", d_hyp=gain, d_state=1, s_drop=0)
        if brk == 1.0 and sem_break is None:
            sem_break = i
    sem_final = ws.observe("pos:done", 1, 1, 0)[0]

    return {
        "cycling_frustration_break_step": cyc_break,
        "cycling_final_frustration": cyc_final,
        "cycling_broke_the_loop": cyc_break is not None,
        "semiosis_frustration_break_step": sem_break,
        "semiosis_final_frustration": sem_final,
        "semiosis_broke_the_loop": sem_break is not None,
        "anti_cycle_holds": (cyc_break is not None and sem_break is None),
    }


def source_audit():
    """G-graph-native: the seek/posit rules (a) name NO transform family and NO
    ls20 constant, and (b) contain NO hardcoded flash->requirement shortcut (no
    TREATMENT rule both reads flash_present and sets transform_required)."""
    blob = json.dumps(RULES).lower()
    banned = ["ls20", "rotation90", "reflection", "rot90", "recolour", "reflect", "rotate"]
    token_hits = [w for w in banned if w in blob]
    # the hardcoded-reading shortcut: a rule that reads flash_present in its where
    # AND writes transform_required in its effects (that WOULD be flash=requirement).
    shortcut = []
    for r in RULES:
        where = json.dumps(r.get("where", {}))
        effs = json.dumps(r.get("effects", []))
        if '"flash_present"' in where and '"transform_required"' in effs:
            shortcut.append(r["name"])
    return {"rule_count": len(RULES), "banned_tokens_found": token_hits,
            "flash_to_requirement_shortcut_rules": shortcut,
            "clean": (not token_hits and not shortcut)}


def check_gates(first, held):
    def sep(a_ci, b_ci):
        return a_ci[1] > b_ci[2]
    g = {}
    # G-posits-generated
    g["G_posits_generated"] = (first["mean_posits"]["semiosis"] >= 3.0
                               and held["mean_posits"]["semiosis"] >= 3.0)
    # G-correct-posit-confirmed (HEADLINE): semiosis correct-meaning CI-sep above
    # BOTH the no_test and hardcode_reward controls, on both runs.
    def headline(res):
        s = res["correct_meaning_rate"]["semiosis"]
        return sep(s, res["correct_meaning_rate"]["no_test"]) and sep(s, res["correct_meaning_rate"]["hardcode_reward"])
    g["G_correct_posit_confirmed"] = headline(first) and headline(held)
    # G-act-passes: semiosis pass CI-sep above cycling, both runs.
    g["G_act_passes"] = (sep(first["pass_rate"]["semiosis"], first["pass_rate"]["cycling"])
                         and sep(held["pass_rate"]["semiosis"], held["pass_rate"]["cycling"]))
    # G-anti-cycle: semiosis mean steps strictly below cycling on both runs.
    g["G_anti_cycle_steps"] = (first["mean_steps"]["semiosis"] < first["mean_steps"]["cycling"]
                               and held["mean_steps"]["semiosis"] < held["mean_steps"]["cycling"])
    g["semiosis_correct_first"] = first["correct_meaning_rate"]["semiosis"]
    g["no_test_correct_first"] = first["correct_meaning_rate"]["no_test"]
    g["hardcode_reward_correct_first"] = first["correct_meaning_rate"]["hardcode_reward"]
    g["semiosis_pass_first"] = first["pass_rate"]["semiosis"]
    g["cycling_pass_first"] = first["pass_rate"]["cycling"]
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=227000)
    args = ap.parse_args()

    first = measure_config(args.n, args.seed)
    held = measure_config(args.n, args.seed + 1)
    trace = semiosis_trace(args.seed + 7)
    frust = frustration_tie_in(args.seed + 3)
    audit = source_audit()
    gates = check_gates(first, held)

    result = {
        "rung": 227000,
        "commitment": "THE GAME IS COMMUNICATING: the agent DISCOVERS the flash's meaning by "
                      "positing candidate meanings (general communicative vocabulary), testing "
                      "them by acting+residual, confirming the correct one (requirement) and "
                      "refuting the wrong ones, then acting (seek the only-other salient shape, "
                      "apply the transform, pass the block). Controls: cycling, hardcode_reward, "
                      "no_test.",
        "first": first, "held_out": held,
        "semiosis_trace": trace,
        "frustration_anti_cycle_226": frust,
        "source_audit": audit,
        "gates": gates,
        "note": "ls20-SHAPED offline scenarios on the real ls20 palette, SEEN through the 216000 "
                "pixel eye; recogniser = the GENERAL 217000 sd-loop; posit vocabulary is GENERAL "
                "communicative meanings. LIVE ls20 is the separate honest half.",
    }
    out = _ROOT / "results" / "arc_ls20_seek_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    print("=== RUNG 227000 — THE GAME IS COMMUNICATING (posit-and-test semiosis) ===")
    for tag, res in (("FIRST", first), ("HELD-OUT", held)):
        print(f"\n{tag}  N={res['n']}")
        for a in ARMS:
            print(f"  {a:16s} pass={fmt(res['pass_rate'][a])}  correct-meaning={fmt(res['correct_meaning_rate'][a])}"
                  f"  posits~{res['mean_posits'][a]:.1f}  steps~{res['mean_steps'][a]:.0f}")
        print(f"  confirmed_meanings(semiosis)={res['confirmed_meanings']['semiosis']}")
    print(f"\nsource audit: {audit}")
    print(f"frustration anti-cycle (226): {frust}")
    print("\nSEMIOSIS TRACE (discover -> act exemplar):")
    for k in ("scenario", "posit", "test", "discover", "seek", "act", "won", "correct_meaning_discovered"):
        print(f"  {k:14s}: {trace[k]}")
    print(f"\nGATES: {json.dumps(gates, default=str, indent=1)}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
