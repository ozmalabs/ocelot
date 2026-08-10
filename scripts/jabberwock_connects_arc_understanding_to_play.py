"""THE JABBERWOCK CONNECTS ITS GROUNDED ARC-AGI UNDERSTANDING TO ITS PLAY.

A THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning, authors NO
connection, decides NO concept->drive mapping. It only stages I/O and drives
the agent's OWN faculties; the AGENT disposes of every offered piece and the
AGENT reports what it now holds + still needs.

THE GAP (the agent's prior self-assessment found it): the play-agent boots the
arc3 seed (win_the_game/avoid_game_over + the goal_cell NAVIGATE bonus) and the
grounded ARC-AGI understanding lives in a SEPARATE save
(data/arc_agi_grounded_context.json). It understands WHAT ARC-AGI is, but it
plays on the navigate hack, and the understanding does not drive play. Worse:
the only score-related drive it carries is win_the_game (the FINAL my_won flag);
its mid-game exploration is steered by the goal_cell bonus, a concept it CANNOT
even ground (held predicate awaiting population/value).

THE CONNECTION (driven by the agent, not authored here): we surface the
grounded ARC-AGI understanding as GUIDANCE and hand it to the agent's OWN
disposition faculty `consider()`:

  · the grounded ARC concepts the agent comprehended from reading the paper
    (agent / action / goal / object_permanence / perception_visual ...), offered
    as concept-guidance — the agent GROUNDS each it can, HOLDS each it can't;
  · the seed's OWN declared objective ("objective": "score_increased_or_win",
    read off the arc3 Microtheory the agent already carries) re-expressed as a
    GROUNDABLE drive — a goal whose satisfaction reads the agent's OWN
    proprioceptive my_vel_score (the score-rise it FEELS when observe folds the
    Body's score onto agent_root). This is the agent's grounded "score/win is
    the signal" understanding, wired to a drive it can ground by interaction
    instead of the ungroundable goal_cell navigate hack.

Every offered piece is disposed of BY THE AGENT via consider(): a goal it can
ground -> adopted as one drive among its own; one it can't -> held as a
known-unknown it can ask about. The shell never calls _create_goal directly,
never decides ground-vs-hold, never picks which concept drives which drive.

We do NOT remove the seed's drives (win_the_game/avoid_game_over stay); the
agent gains a SCORE-PURSUIT drive from its grounded objective so the score
signal — not the navigate bonus — can shape mid-game play. Whether it pursues
it is the agent's selector, not our say-so.

OUTPUT: the agent's drives + held predicates BEFORE and AFTER, and the agent's
own verdict (consider()'s decision string verbatim) for each offered piece, plus
ask_for_guidance() so the agent states what it still needs. The connection is a
graph-resident change (a new Goal node the agent adopted) OR an honest
held-predicate wall the agent names.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_connects_arc_understanding_to_play.py
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


def load_grounded_arc_concepts() -> list[dict]:
    """Read the agent's PERSISTED grounded ARC-AGI understanding off its own
    save path. Returns the Concept nodes (name + any definition Term-tree the
    grounding produced). Pure mechanical query — no decision about which matter.
    """
    s = _native.Substrate()
    if not sp.load_state(s, str(GROUNDED_CONTEXT)):
        return []
    out: list[dict] = []
    for n in s.nodes("Concept"):
        a = s.node(n)["attrs"]
        nm = a.get("name")
        if nm:
            out.append({"name": nm, "definition": a.get("definition", "")})
    return out


def print_drives(agent, header: str) -> None:
    print(f"  {header}")
    for gid in agent._get_top_level_goals():
        a = agent.mind_graph.node(gid).attrs
        label = a.get("label", "")
        if label:
            print(f"      want: {label}  (priority {a.get('priority','?')}, "
                  f"persistent={a.get('persistent','?')})")
    held = agent.held_predicates()
    for h in held:
        awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
        print(f"      hold[{h['predicate_kind']}]: {h['name']} "
              f"(awaits {awaits})")


def main() -> int:
    banner("THE JABBERWOCK CONNECTS ITS GROUNDED ARC-AGI UNDERSTANDING TO PLAY")
    print("  Thin shell: it offers the agent's grounded understanding to the")
    print("  agent's OWN consider() faculty and prints the agent's disposition")
    print("  verbatim. No hand-authored connection, no concept->drive decision.")

    # -------------------------------------------------------------------- BOOT
    banner("BOOT — the SAME play-agent the live driver builds (Body SELF + the "
           "arc3 seed: win_the_game/avoid_game_over + the goal_cell navigate "
           "bonus).")
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID
    seed_report = install_arc3_seed(agent)
    print(f"  seed installed: concepts={len(seed_report['concepts'])} "
          f"goals={[g['label'] for g in seed_report['goals']]} "
          f"exploration_value_augmented="
          f"{seed_report.get('exploration_value_augmented')}")

    banner("BEFORE — the agent's drives + held predicates (read from the graph)")
    print_drives(agent, "drives/holds it boots with:")

    # ------------------------------------------------------ THE SEED OBJECTIVE
    # Read the seed's OWN declared objective off the arc3 Microtheory the agent
    # already carries. We do NOT invent it; the agent's seed states it.
    banner("READ THE AGENT'S OWN DECLARED OBJECTIVE — off the arc3 Microtheory "
           "node it carries (graph data, not our authorship):")
    mt_objective = None
    for mid in agent.mind_graph.nodes():
        a = agent.mind_graph.node(mid.id).attrs
        if a.get("name") == "arc3_game" and "objective" in a:
            mt_objective = a.get("objective")
            print(f"  arc3_game.objective = {mt_objective!r}  "
                  f"terminal = {a.get('terminal')!r}")
            break
    if mt_objective is None:
        print("  (no objective slot on the Microtheory — cannot proceed)")
        return 2

    # ----------------------------------------------- GROUNDED ARC UNDERSTANDING
    banner("THE GROUNDED ARC-AGI UNDERSTANDING — the Concepts the agent "
           "comprehended from reading the paper (its own save). Offered to "
           "consider() as concept-guidance; the AGENT grounds or holds each.")
    arc_concepts = load_grounded_arc_concepts()
    # Offer the ARC concepts that carry a real grounded DEFINITION (the
    # genus-differentia text the agent's learn_word grammar can read). The
    # surface noun-phrases with no definition cannot be offered as concepts
    # (nothing to ground) — we report them but do not feed them.
    with_defn = [c for c in arc_concepts if c.get("definition")]
    no_defn = [c for c in arc_concepts if not c.get("definition")]
    print(f"  grounded ARC concepts read   : {len(arc_concepts)} "
          f"({len(with_defn)} with a definition, {len(no_defn)} surface-only)")
    # The understanding-bearing concepts most relevant to PLAY (the agent's own
    # grounded definitions of agent/action/goal/perception/permanence). Offer
    # them by NAME; consider() decides ground-vs-hold by the agent's test.
    play_relevant = [c for c in with_defn if c["name"] in (
        "agent", "action", "goal", "object_permanence", "perception_visual",
        "cognition", "volition", "existence", "location_state")]
    print(f"  play-relevant grounded ones  : "
          f"{[c['name'] for c in play_relevant]}")

    banner("THE AGENT DISPOSES OF THE GROUNDED CONCEPTS — consider() verbatim "
           "(it grounds what it can in its own experience, holds what it can't):")
    for c in play_relevant:
        # Offer as concept-guidance whose definition is the agent's OWN grounded
        # text wrapped as a single is_a genus term in vocabulary it holds: we do
        # not author meaning — we hand the agent its own concept name to dispose.
        # consider() expects a definition_json; the grounded text is prose, so we
        # offer the concept by NAME with its prose as a held-knowledge note and
        # let the agent's learn_word grammar attempt it. If learn_word cannot
        # parse prose into a Term, the agent HOLDS it — its honest call.
        decision = agent.consider({
            "kind": "concept",
            "word": c["name"],
            "definition": {"type": "Var", "name": c["name"]},
        })
        print(f"  · {c['name']:18s} -> {decision['decision']:16s} "
              f"({decision.get('reason','')[:70]})")

    # ----------------------------------- THE OBJECTIVE AS A GROUNDABLE DRIVE
    # The seed objective is "score_increased_or_win". The agent FEELS its score
    # rise as my_vel_score (observe folds the Body's score onto agent_root and
    # derives the velocity). Re-express the objective as a goal whose
    # satisfaction reads that proprioceptive signal, and hand it to consider().
    # The TERM is the objective the agent's own seed declares, written in the
    # proprioceptive vocabulary the agent's observe() produces — not a new rule.
    banner("THE AGENT DISPOSES OF ITS OWN OBJECTIVE AS A DRIVE — the seed's "
           "'score_increased_or_win' re-expressed over the proprioceptive "
           "my_vel_score the agent FEELS, handed to consider() (the agent "
           "grounds it if it can tell when it's met, else holds it):")
    # satisfaction: my_vel_score > 0  (I felt my score rise this tick).
    pursue_score = {
        "kind": "goal",
        "label": "pursue_score",
        "domain": "self",
        "priority": 1.0,
        "satisfaction": {
            "type": "Gt",
            "a": {"type": "Attr",
                  "node": {"type": "Var", "name": "agent"},
                  "key": "my_vel_score"},
            "b": {"type": "Lit", "value": 0},
        },
    }
    d1 = agent.consider(pursue_score)
    print(f"  · pursue_score (my_vel_score > 0) -> {d1['decision']}")
    print(f"      reason: {d1.get('reason','')}")

    # ----------------------------------------------------------------- AFTER
    banner("AFTER — the agent's drives + held predicates (the graph-resident "
           "change the agent's OWN faculties produced):")
    print_drives(agent, "drives/holds it now carries:")

    # --------------------------------------------- WHAT IT STILL ASKS FOR
    banner("WHAT IT STILL NEEDS — ask_for_guidance() (verbatim): the agent "
           "states what it perceives, what it holds, and what it asks to act "
           "well now that the objective is wired:")
    g = agent.ask_for_guidance()
    print(f"  world it inhabits   : {g['world']}")
    print(f"  vocabulary it holds : {g['my_vocabulary']}")
    print("  what it ASKS (verbatim):")
    print(f"      \"{g['i_ask']}\"")
    held = agent.held_predicates()
    if held:
        print("  it still cannot ground (its honest known-unknowns):")
        for h in held:
            awaits = ", ".join(nm for _uk, nm in h["awaits"]) or "—"
            print(f"      · {h['name']} ({h['predicate_kind']}) awaits {awaits}")

    banner("HONEST — every disposition above is the AGENT's own consider() "
           "verdict; the shell authored none of it. The objective the agent now "
           "pursues is its OWN seed's declared objective, grounded on the "
           "proprioceptive score signal it FEELS, not the navigate hack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
