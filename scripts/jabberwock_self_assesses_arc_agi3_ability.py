"""THE JABBERWOCK SELF-ASSESSES ITS OWN ABILITY TO DO ARC-AGI v3.

A THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning, holds NO agent
state, and authors NO assessment. It only:

  1. BOOTS the agent (CuriousAgent — a graph), identifies it as the Body SELF,
     and installs the SAME ARC-AGI-3 seed the live driver installs
     (domains/arc3_seed.install_arc3_seed) — so the agent's self-model carries
     the ARC win goal, the action-meaning Microtheory, and the goal_cell genus
     it would play with. This is the agent's ARC-playing competence, graph-
     resident, exactly as the live experiment boots it.

  2. LOADS, as CONTEXT, the agent's persisted GROUNDED ARC-AGI understanding
     (data/arc_agi_grounded_context.json via self_persistence.load_state, the
     agent's own save path) into a SEPARATE substrate and reads back the ARC
     concepts it grounded — so the report shows the assessment is grounded in
     what the agent actually comprehended about what ARC-AGI IS. (Loaded
     separately, not merged, so the live seeded agent is not clobbered.)

  3. DRIVES the agent's OWN self-assessment faculties and prints their output
     VERBATIM — no hand-authored capability list, no grading:
       · describe_self()        — its reflective self-report (what it is /
                                  knows / wants / holds-but-cannot-ground).
       · ask_for_guidance()     — what it perceives, the actions it has tried,
                                  its vocabulary, and what it ASKS to act well.
       · held_predicates() +
         ask_about()            — its KNOWN-UNKNOWNS: the words/goals it holds
                                  but cannot yet ground (its honest gaps), and
                                  exactly what it still needs to perceive.
       · compute_pressure() +
         runtime_capabilities() — its resource self-report (op_mean_cost /
                                  op_count over its ARC-bearing ops; spent/limit).

The shell stages I/O and prints the agent's verdicts. The MEANING is the
agent's graph (its self-model, drives, held predicates); the ASSESSMENT is the
agent's own introspection faculties; no LLM, no Rust, no Python decision about
how able the agent is.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_self_assesses_arc_agi3_ability.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate_rs import _native  # noqa: E402

from domains import self_persistence as sp  # noqa: E402
from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_seed import install_arc3_seed  # noqa: E402
from domains.arc3_world import SELF_ID  # noqa: E402

SEP = "=" * 78
GROUNDED_CONTEXT = ROOT / "data" / "arc_agi_grounded_context.json"


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# (2) CONTEXT — the agent's persisted GROUNDED understanding of WHAT ARC-AGI IS,
# read back from its own save path. Surfaced as context so the self-assessment
# is grounded in what the agent actually comprehended. Loaded into its OWN
# substrate (not merged into the live agent), then read mechanically.
# ---------------------------------------------------------------------------

def load_grounded_arc_context() -> list[str]:
    s = _native.Substrate()
    if not sp.load_state(s, str(GROUNDED_CONTEXT)):
        return []
    names = []
    for n in s.nodes("Concept"):
        nm = s.node(n)["attrs"].get("name")
        if nm:
            names.append(nm)
    return sorted(names)


# ---------------------------------------------------------------------------
# (1) BOOT — the SAME ARC-playing agent the live driver builds.
# ---------------------------------------------------------------------------

def boot_arc_agent() -> tuple[CuriousAgent, dict]:
    agent = CuriousAgent()
    # Identify as the Body SELF (so observe() would fold game score/won/over into
    # the agent's my_* proprioception the seeded WIN goal reads) and install the
    # arc3 meta-rules seed — the EXACT calls scripts/arc3_live_experiment.py makes.
    agent.my_world_id = SELF_ID
    report = install_arc3_seed(agent)
    return agent, report


# ---------------------------------------------------------------------------
# MAIN — boot, load context, drive the agent's own self-assessment, print
# everything VERBATIM.
# ---------------------------------------------------------------------------

def main() -> int:
    banner("THE JABBERWOCK SELF-ASSESSES ITS OWN ABILITY TO DO ARC-AGI v3")
    print("  The shell boots the ARC-playing agent (same seed as the live driver),")
    print("  loads its grounded ARC-AGI understanding as context, and prints the")
    print("  agent's OWN self-assessment faculties VERBATIM. No hand-authored")
    print("  assessment, no grading — the agent's introspection is the verdict.")

    # ---------------------------------------------------------------- BOOT
    banner("BOOT — the agent (a graph), identified as the Body SELF, with the "
           "ARC-AGI-3 seed installed (win goal + action Microtheory + goal_cell)")
    agent, seed = boot_arc_agent()
    print(f"  arc3 seed installed: "
          f"{ {k: (len(v) if hasattr(v, '__len__') else v) for k, v in seed.items()} }")

    # -------------------------------------------------------------- CONTEXT
    banner("CONTEXT — the agent's PERSISTED grounded understanding of WHAT "
           "ARC-AGI IS (data/arc_agi_grounded_context.json, its own save path)")
    arc_concepts = load_grounded_arc_context()
    print(f"  the agent holds {len(arc_concepts)} grounded Concepts from reading "
          f"ARC-AGI-3; the ARC-relevant ones it would reason WITH:")
    arc_relevant = [c for c in arc_concepts
                    if any(k in c.lower() for k in (
                        "arc", "agent", "action", "goal", "scor", "object",
                        "interact", "explor", "effic", "skill", "game", "play",
                        "reward", "win", "state", "frame", "grid", "benchmark"))]
    for c in arc_relevant:
        print(f"    · {c}")

    # ============================================================ ASSESSMENT
    # The agent's OWN faculties. Everything below is printed VERBATIM from the
    # agent's introspection — the shell adds no judgement.

    banner("(a) WHAT IT CAN DO — describe_self(): the agent's reflective "
           "self-report (verbatim). What it IS, the concepts it can evaluate, "
           "and the drives that bear on play.")
    for line in agent.describe_self():
        print(f"  {line}")

    banner("(a) WHAT IT CAN DO — its DRIVES/GOALS for ARC (the goals the seed "
           "wired, read straight from the graph, verbatim):")
    for gid in agent._get_top_level_goals():
        a = agent.mind_graph.node(gid).attrs
        label = a.get("label", "")
        if label:
            print(f"    want: {label}  "
                  f"(priority {a.get('priority', '?')}, "
                  f"persistent={a.get('persistent', '?')})")

    banner("(a) WHAT IT CAN DO — ask_for_guidance(): in its own words, where it "
           "is, what it perceives, the actions it has tried, the vocabulary it "
           "holds, and what it ASKS to act well (verbatim):")
    g = agent.ask_for_guidance()
    print(f"  world it inhabits        : {g['world']}")
    print(f"  kinds it perceives       : {g['i_perceive_kinds']}")
    print(f"  actions it has tried     : {g['actions_i_have_tried']}")
    print(f"  vocabulary it holds      : {g['my_vocabulary']}")
    print("  its self-report (describe()):")
    for line in g["my_report"]:
        print(f"      {line}")
    print("  what it ASKS (verbatim):")
    print(f"      \"{g['i_ask']}\"")

    banner("(b) WHERE IT IS WEAK / BLOCKED — held_predicates(): the words/goals "
           "it holds but CANNOT yet ground (its honest known-unknowns), each "
           "with exactly what it still AWAITS (verbatim):")
    held = agent.held_predicates()
    if not held:
        print("  (none — it grounds everything it holds)")
    for h in held:
        awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
        print(f"    [CANNOT GROUND] {h['name']} "
              f"({h['predicate_kind']}) — awaits: {awaits}")

    banner("(c) WHAT IT JUDGES IT WOULD NEED — ask_about(): for each held "
           "predicate, the agent NAMES what it must perceive/meet/understand to "
           "ground it, and asks for it by a genus it holds (verbatim):")
    for h in held:
        q = agent.ask_about(h["name"])
        if q is None:
            continue
        print(f"  · about '{q['i_cannot_ground']}':")
        for need in q["because_i_lack"]:
            print(f"      it lacks: {need}")
        print(f"      it asks: \"{q['i_ask']}\"")

    banner("RESOURCE SELF-REPORT — compute_pressure() + runtime_capabilities() "
           "(op_mean_cost / op_count over its ARC-bearing ops; verbatim):")
    cp = agent.compute_pressure()
    print(f"  compute_pressure (spent/limit): {cp}  "
          f"(None = no budget/spend recorded yet — it has not yet PLAYED in "
          f"this session, so no op cost has accrued)")
    caps = agent.runtime_capabilities()
    print("  runtime_capabilities exposed (the agent answers these about its own "
          "runtime):")
    for cap in sorted(caps.keys()):
        print(f"    · {cap}")
    print("  op_mean_cost / op_count for the ops that bear on ARC play "
          "(observe / choose_action / quality_of_position / recognise_frame):")
    for op in ("observe", "choose_action", "quality_of_position",
               "recognise_frame", "grow", "discover"):
        try:
            mean = caps["op_mean_cost"]({"of": op})
            cnt = caps["op_count"]({"of": op})
        except Exception as exc:  # honest: report the faculty error, don't fake
            print(f"    {op:22}  (faculty error: {exc})")
            continue
        print(f"    {op:22}  mean_cost={mean:.4f} ms  count={cnt}")

    # ----------------------------------------------------------------- HONEST
    banner("HONEST — the verdict above is the AGENT's own introspection; the "
           "shell authored none of it.")
    print("  · The agent's CAN-DO is read from its describe_self + drives + the")
    print("    vocabulary/kinds it reports it can evaluate and act with.")
    print("  · The agent's WEAK/BLOCKED is its OWN held_predicates — the concepts")
    print("    it holds but cannot ground until it perceives a missing percept.")
    print("  · The agent's WOULD-NEED is its OWN ask_about — naming exactly the")
    print("    percept/kind/concept it still lacks, asked for by a held genus.")
    print("  · compute_pressure is None because no op cost has accrued in this")
    print("    introspection-only session (no live play was run here).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
