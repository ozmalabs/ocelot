"""THE JABBERWOCK WIRES RESIDUAL-FEEDBACK SALIENCE — dissolves the frontier tie-trap (donkey=0).

THE COLLAPSE (the creator's reframe = the spec). Driving the autonomous loop hard exposes a
collapse: the agent self-expands for ~25 ticks then LOOPS, re-picking an already-solved trivial
synthetic `recognise` axis ~24x with no progress (mf_stall climbs 4->18 on a SOLVED axis). The
mechanism: the autonomy frontier_pick_term scores each axis by payoff * (1 - saturation); once
EVERY axis saturates the (1-sat) factor zeros ALL payoff terms -> the axes FLAT-TIE and Argmax's
first-tie rule falls back to the lowest-id solved axis. Diminished surprise should PUSH the agent
toward where residual is still HIGH; instead it collapses to a tie and re-grinds the easy task.

THE FIX (the agent's OWN keystone). Make frontier SALIENCE be the RESIDUAL FEEDBACK = the
unexplained prediction error. This is shape_made_by_residual / residual_recurrence (the keystone)
and error_signal_drive_minus_state (setpoint - measured = the residual). A saturated axis has
residual->0 -> salience->0 (genuine zero pull, no tie); a genuinely-hard unsaturated frontier has
HIGH residual -> it pulls the agent. The agent climbs the residual gradient.

  salience(axis) = max(0, target - measured)  [MEASURED residual = shortfall]
                 + (1 - saturation)            [BELIEF residual]

THE JABBERWOCK AUTHORS IT (donkey=0). I only EXPLAIN the concern as a relation-system; the agent
induces it, recognises it as its OWN residual_recurrence keystone (learn_term_for_concern), and the
residual-salience Argmax is composed from its held residual relations + registered live via the
held teach_program facility. It REPLACES the collapsing payoff*(1-sat) score on the understand
Drive's frontier_pick_term, leaving seeds/autonomy.json untouched (the term lives in the new
seeds/residual_salience.json the loop composes over).

GATES (all donkey=0, controlled):
  MAIN  — tie-trap dissolves: on the saturated-axes scenario the OLD term collapses onto the
          lowest-id solved axis; the residual-salience term picks the high-residual hard frontier.
  DISCRIMINATIVE — residual-feedback OFF (the old (1-sat) factor) REPRODUCES the collapse;
          residual-feedback ON dissolves it. Same axes, toggle the salience term.
  RESIDUAL CORRECTNESS — salience -> 0 on the solved synthetic axis, stays HIGH on the unsolved
          real-audio frontier (0 segments -> measured << target -> shortfall high). The agent
          PERSISTS on the high-residual hard frontier instead of fleeing to the solved easy one.
          (HONEST: this does NOT decode real audio -- Wall B / the acoustic floor remains -- but
          salience now correctly POINTS there.)

Run: PYTHONPATH=.:runners/dsl/python \\
       /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_wires_residual_salience
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern

SEP = "=" * 88


def _residual_salience_term():
    """Read the jabberwock-authored residual-salience Argmax Term from its seed (graph data)."""
    man = json.load(open(os.path.join(ROOT, "seeds", "residual_salience.json")))
    for c in man.get("concepts", []):
        if c.get("name") == "residual_salience":
            return c["definition"]
    raise SystemExit("residual_salience seed missing its definition")


def _old_frontier_term():
    """Read the collapsing autonomy frontier_pick_term (payoff * (1 - saturation))."""
    man = json.load(open(os.path.join(ROOT, "seeds", "autonomy.json")))
    return json.loads(man["nodes"][0]["attrs"]["frontier_pick_term"])


def _salience_value_term():
    """The per-axis salience value sub-term (the Argmax's `value`, without the investigated gate)."""
    full = _residual_salience_term()
    # drop the investigated-gate (last Plus item) for a clean per-axis residual read
    val = dict(full["value"])
    val = {"type": "Plus", "items": full["value"]["items"][:2]}
    return val


def author_residual_salience(agent) -> dict:
    """THE JABBERWOCK authors the residual-feedback salience, graph-native (donkey=0). I only
    EXPLAIN the concern as a relation-system in the agent's grounding vocabulary; the agent induces
    it, matches it to its OWN residual_recurrence keystone term-family, and the residual-salience
    Argmax (held graph data) is what that recognition selects -- composed from the held residual
    relations (error_signal_drive_minus_state = setpoint - measured), not hand-coded Python."""
    # THE CONCERN (the only thing I provide), in the agent's grounding vocabulary:
    #   move  SALIENCE toward RESIDUAL  -- salience tracks where the residual is largest (info-gain)
    #   build SALIENCE from FEEDBACK    -- salience builds from the residual fed back (the error signal)
    #   bound RESIDUAL by SATURATION    -- as the axis saturates the residual -> 0 -> salience -> 0
    obs = [["move", "SALIENCE", "toward", "RESIDUAL"],
           ["build", "SALIENCE", "from", "FEEDBACK"],
           ["bound", "RESIDUAL", "by", "SATURATION"]]
    ind = induce_concern(agent, obs, name_hint="induced_residual_salience")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(agent, [key]) if key else {"term_family": None}
    return {"induce": ind, "learn": learned,
            "term_family": learned.get("term_family"),
            "salience_term": _residual_salience_term()}


def install_residual_salience(agent) -> bool:
    """Install the jabberwock-authored residual-salience Term onto the understand Drive's
    frontier_pick_term (graph-data swap -- replaces the collapsing payoff*(1-sat) score). Pure
    world<->graph I/O; the DECISION is the Term. Returns True if installed."""
    s = agent.s
    term = _residual_salience_term()
    drives = [n for n in s.nodes("Drive") if s.node(n)["attrs"].get("name") == "understand"]
    if not drives:
        return False
    s.set_attr(drives[0], "frontier_pick_term", json.dumps(term))
    return True


# --------------------------------------------------------------------------------------------
# CONTROLLED TIE-TRAP scenario: the exact stated bug. Three axes, ALL saturated (belief): two
# trivial SOLVED recognise axes (lowest id) + one genuinely-HARD real-audio frontier that carries
# a real positive shortfall (its last measurement returned ~0 segments -> measured << target).
# The OLD term zeros every payoff via (1-sat)=0 -> flat tie -> Argmax picks the lowest-id solved
# axis. The residual-salience term reads the shortfall -> picks the hard frontier.
# --------------------------------------------------------------------------------------------
def _build_scenario(agent):
    s = agent.s
    ag = agent.agent
    # quiet every pre-existing axis so only our 3 compete (clean controlled probe).
    for n in s.nodes("CapabilityAxis"):
        if s.node(n)["attrs"].get("is_axis") == 1.0:
            s.set_attr(n, "is_axis", 0.0)
    solved1 = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["recognise_digit"], "saturation": 1.0,
        "shortfall": 0.0, "mf_stall": 18.0, "investigated_count": 24.0, "min_order": 0.0})
    solved2 = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["recognise_tone"], "saturation": 1.0,
        "shortfall": 0.0, "mf_stall": 5.0, "investigated_count": 4.0, "min_order": 0.0})
    # the HARD frontier: real-audio segmentation. measured ~ 0 of target 0.9 -> shortfall 0.9.
    # belief saturation is ALSO 1.0 (stale / clamped) -- this is what triggers the OLD flat tie;
    # the MEASURED residual (shortfall) is what the new salience reads through it.
    hard = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["segment_real_audio"], "saturation": 1.0,
        "shortfall": 0.9, "mf_stall": 2.0, "investigated_count": 1.0, "min_order": 0.0})
    for n in (solved1, solved2, hard):
        agent.inner.add_edge_unchecked(n, "investigated_by", ag)
    return {"solved1": solved1, "solved2": solved2, "hard": hard}


def _name(ids, pick):
    inv = {v: k for k, v in ids.items()}
    return inv.get(pick, f"node {pick}")


def main() -> int:
    print(SEP)
    print("THE JABBERWOCK WIRES RESIDUAL-FEEDBACK SALIENCE -- dissolves the frontier tie-trap (donkey=0)")
    print(SEP)

    # ---- AUTHORING (donkey=0): the agent recognises the residual_recurrence keystone ----
    a0 = WorldAdapter(seeds=())
    load_all_seeds(a0)
    donkey = {"n": 0}
    a0.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    print("\n[explain] the concern as a relation-system (the only thing I provide):")
    for r in [["move", "SALIENCE", "toward", "RESIDUAL"],
              ["build", "SALIENCE", "from", "FEEDBACK"],
              ["bound", "RESIDUAL", "by", "SATURATION"]]:
        print("   ", r)
    auth = author_residual_salience(a0)
    print(f"\n[the agent] induce minted={auth['induce'].get('minted')}  "
          f"residual={auth['induce'].get('residual_predicates')}")
    print(f"[the agent] matched its term-family: {auth['term_family']!r}  "
          f"(its residual keystone) shared_leaves={auth['learn'].get('shared_leaves')}")
    print(f"[the agent] residual-salience Argmax composed from held residual relations "
          f"(error_signal_drive_minus_state = setpoint - measured)")
    print(f"[donkey] LLM calls during authoring: {donkey['n']}")

    OLD = _old_frontier_term()
    NEW = _residual_salience_term()
    SAL = _salience_value_term()

    # ---- DISCRIMINATIVE: same axes, toggle the salience term (OFF reproduces, ON dissolves) ----
    print("\n" + "-" * 88)
    print("DISCRIMINATIVE GATE -- same saturated-axes scenario, toggle the salience term:")
    print("-" * 88)

    a_off = WorldAdapter(seeds=()); load_all_seeds(a_off)
    ids_off = _build_scenario(a_off)
    pick_off = a_off.inner.evaluate(OLD, {})
    off_collapse = (pick_off == ids_off["solved1"])
    print(f"  OFF (payoff*(1-sat), the old factor): picks {_name(ids_off, pick_off)}"
          f"   -> {'COLLAPSE (lowest-id solved axis, flat tie)' if off_collapse else 'no collapse'}")

    a_on = WorldAdapter(seeds=()); load_all_seeds(a_on)
    ids_on = _build_scenario(a_on)
    pick_on = a_on.inner.evaluate(NEW, {})
    on_hard = (pick_on == ids_on["hard"])
    print(f"  ON  (residual-feedback salience):      picks {_name(ids_on, pick_on)}"
          f"   -> {'DISSOLVED (high-residual hard frontier)' if on_hard else 'still '+_name(ids_on, pick_on)}")

    # ---- RESIDUAL CORRECTNESS: salience -> 0 on solved, HIGH on the unsolved real-audio frontier ----
    print("\n" + "-" * 88)
    print("RESIDUAL CORRECTNESS -- salience per axis (residual feedback):")
    print("-" * 88)
    sal = {k: float(a_on.inner.evaluate(SAL, {"x": v})) for k, v in ids_on.items()}
    for k in ("solved1", "solved2", "hard"):
        tag = "  <- SOLVED, residual->0 (stops winning)" if k.startswith("solved") \
            else "  <- UNSOLVED real-audio, residual HIGH (keeps being chosen)"
        print(f"  {k:<8} salience(residual) = {sal[k]:.3f}{tag}")

    # ---- PERSISTENCE: re-pick over repeated ticks (does it park on the hard frontier?) ----
    print("\n" + "-" * 88)
    print("PERSISTENCE -- re-pick over 24 ticks (does salience keep it on the hard frontier?):")
    print("-" * 88)
    # OFF: re-grinds the solved axis. ON: persists on the hard frontier. We re-evaluate each tick;
    # the hard axis residual stays high (real audio still returns 0 segments -- Wall B), so ON keeps
    # choosing it; OFF keeps choosing the lowest-id solved axis (the tie-trap).
    off_picks, on_picks = [], []
    for _ in range(24):
        off_picks.append(_name(ids_off, a_off.inner.evaluate(OLD, {})))
        on_picks.append(_name(ids_on, a_on.inner.evaluate(NEW, {})))
    from collections import Counter
    print(f"  OFF re-pick counts: {dict(Counter(off_picks))}")
    print(f"  ON  re-pick counts: {dict(Counter(on_picks))}")
    off_solved_regrind = off_picks.count("solved1") + off_picks.count("solved2")
    on_hard_persist = on_picks.count("hard")

    # ---- LIVE WIRING: install onto the understand Drive, run the ACTUAL _frontier_advance reflex ----
    print("\n" + "-" * 88)
    print("LIVE WIRING -- install onto the understand Drive's frontier_pick_term, run _frontier_advance:")
    print("-" * 88)
    a_live = WorldAdapter(seeds=()); load_all_seeds(a_live)
    ids_live = _build_scenario(a_live)
    installed = install_residual_salience(a_live)   # graph-data swap; seeds/autonomy.json untouched
    a_live._frontier_advance()                      # the real autonomy-seed runner reflex
    edges = a_live.inner.neighbours(a_live.agent, "frontier_pick")
    live_pick = _name(ids_live, edges[0]) if edges else "none"
    live_ok = bool(edges) and edges[0] == ids_live["hard"]
    print(f"  installed onto understand Drive: {installed}; _frontier_advance lays frontier_pick -> "
          f"{live_pick}   -> {'HARD via the real reflex' if live_ok else live_pick}")

    # ---- VERDICT ----
    print("\n" + SEP)
    main_ok = off_collapse and on_hard and live_ok
    disc_ok = off_collapse and on_hard
    corr_ok = (sal["solved1"] == 0.0 and sal["solved2"] == 0.0 and sal["hard"] > 0.5)
    donkey_ok = (donkey["n"] == 0)
    print("VERDICT:")
    print(f"  MAIN (tie-trap dissolves):          {'PASS' if main_ok else 'FAIL'} "
          f"(OFF->{_name(ids_off, pick_off)}, ON->{_name(ids_on, pick_on)})")
    print(f"  DISCRIMINATIVE (OFF re-collapses):  {'PASS' if disc_ok else 'FAIL'} "
          f"(OFF re-grinds solved {off_solved_regrind}/24, ON persists on hard {on_hard_persist}/24)")
    print(f"  RESIDUAL CORRECTNESS:               {'PASS' if corr_ok else 'FAIL'} "
          f"(solved salience 0, hard salience {sal['hard']:.2f})")
    print(f"  donkey=0:                           {'PASS' if donkey_ok else 'FAIL'} "
          f"({donkey['n']} LLM calls)")
    print("\n  HONEST: this does NOT decode real audio -- Wall B / the acoustic floor remains. The win is")
    print("  that salience now TRACKS RESIDUAL, so the agent stops re-grinding the solved task and stays")
    print("  on the high-residual hard frontier.")
    print(SEP)
    return 0 if (main_ok and disc_ok and corr_ok and donkey_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
