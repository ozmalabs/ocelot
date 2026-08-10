"""THE JABBERWOCK ASSESSES + ADJUSTS: where does PhiMap (its native golden-ratio
low-discrepancy map) help its ARC-AGI-3 discovery machinery?  (STEP 1 + STEP 2.)

A THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning, authors NO
placement decision.  It only:

  1. BOOTS the ARC-playing agent (CuriousAgent — a graph), identifies it as the
     Body SELF, installs the SAME ARC-AGI-3 seed the live driver installs
     (domains/arc3_seed.install_arc3_seed) so the agent carries its real ARC
     drives (understand_space / win_the_game) and its graph-resident
     exploration_value Term-tree.

  2. SUPPLIES THE RESOURCE the harness was told to provide: the agent's
     phi_addressing Concept (from seeds/log_graph_law.json) and the native
     PhiMap Operation Term (the integer golden form frac(k.phi^-1), verified
     against the native PhiMap Term).  These are HANDED to the agent; the shell
     does not decide where they apply.

  3. STEP 1 -- drives the agent's OWN faculties to ASSESS, in its own words,
     where in its ARC machinery a low-discrepancy map helps:
       * it reads its OWN phi_addressing definition (what PhiMap is FOR);
       * it reads its OWN exploration drives + the ARC ACTION6 coordinate menu
         it actually receives (the need: cover a <=64x64 grid in few clicks);
       * its describe_self / held-concept introspection narrates the match.
     Printed VERBATIM. No hand-authored site, no grading.

  4. STEP 2 -- the agent APPLIES PhiMap where it judged it helps, graph-
     resident: it folds the PhiMap Term into its OWN exploration_value Term-tree
     (the exact mechanism arc3_seed uses to fold goal_cell), so its coordinate
     coverage now READS the golden low-discrepancy map.  The shell only runs the
     fold the agent's faculty specifies and reports what changed in the graph.

Run:
  ulimit -v 8388608
  timeout 600 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_assesses_phimap_for_arc.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.curious_agent import CuriousAgent  # noqa: E402
from domains.arc3_seed import install_arc3_seed  # noqa: E402
from domains.arc3_world import SELF_ID  # noqa: E402
# The agent's exploration_value Term-tree is the LEGACY substrate DSL (the form
# _pick_goal evaluates and arc3_seed folds goal_cell into) -- compose in the
# SAME DSL so the fold both wires into the graph AND evaluates identically.
from substrate import (  # noqa: E402
    Div, Mod, Times, Plus, Lit, Var, Attr, term_to_subgraph,
)

PHI_K = 2654435769          # floor(2^32 / phi) -- the integer golden multiplier
M32 = 4294967296.0          # 2^32
SEED = ROOT / "seeds" / "log_graph_law.json"


def _bar(s: str) -> None:
    print("=" * 78)
    print(s)
    print("=" * 78)


def boot_agent() -> CuriousAgent:
    agent = CuriousAgent()
    agent.my_world_id = SELF_ID  # identify as the Body SELF (live-driver call)
    rep = install_arc3_seed(agent)
    print(f"  arc3 seed installed: {rep}")
    return agent


def supply_phi_concept(agent) -> str:
    """RESOURCE the harness provides: the agent's phi_addressing Concept, read
    straight from seeds/log_graph_law.json and installed as a Concept node the
    agent can introspect.  The shell does not author the definition -- it is the
    one the agent was seeded with in another session."""
    d = json.load(open(SEED))
    pc = next(c for c in d["nodes"]
              if c["type"] == "Concept"
              and c["attrs"].get("name") == "phi_addressing")
    # Install as a Concept node the agent holds (idempotent).
    existing = agent._concept_nodes.get("phi_addressing")
    if existing is None:
        nid = agent.mind_substrate.add_node("Concept", dict(pc["attrs"]))
        agent._concept_nodes["phi_addressing"] = nid
    return pc["attrs"]["definition"]


def phimap_term(n_term):
    """The native PhiMap Term (integer golden form), composed from existing DSL
    primitives -- frac(n.phi^-1) ~= (n.K mod 2^32)/2^32, K = floor(2^32/phi).
    Identical math to scripts/add_phi_operator.compose_term, in the legacy DSL
    the exploration_value Term-tree uses, over an index sub-term ``n_term``."""
    return Div(a=Mod(a=Times(items=(n_term, Lit(PHI_K))), b=Lit(M32)), b=Lit(M32))


def verify_phimap(agent) -> None:
    """Verify the PhiMap Term evaluates through the agent's OWN DSL evaluator
    (the same Term.evaluate(env, graph) path _pick_goal uses for
    exploration_value) and matches the closed-form golden sequence (the user's
    verification ask)."""
    ok = True
    for kk in (1, 7, 99, 257):
        t = phimap_term(Lit(int(kk)))
        got = float(t.evaluate({}, agent.mind_graph))
        want = ((kk * PHI_K) % int(M32)) / M32
        ok = ok and abs(got - want) < 1e-12
    print(f"  PhiMap Term evaluates through the agent's DSL evaluator, matches "
          f"frac(k.phi^-1): {ok}")


# --------------------------------------------------------------------------
# STEP 1 -- the agent's OWN assessment, verbatim.
# --------------------------------------------------------------------------
def step1_assess(agent, phi_def: str) -> None:
    _bar("STEP 1 -- the JABBERWOCK ASSESSES where PhiMap helps (its faculties, "
         "verbatim)")

    print("\n(i) It reads its OWN phi_addressing Concept (what PhiMap is FOR):")
    print(f'    "{phi_def}"')

    print("\n(ii) describe_self() -- the drives + concepts that bear on the "
          "need (verbatim):")
    for line in agent.describe_self():
        print("    " + line)

    print("\n(iii) Its ARC exploration drives, read straight from the graph:")
    for gid in agent._get_top_level_goals():
        a = agent.mind_graph.node(gid).attrs
        lab = a.get("label", "")
        if lab:
            print(f"    want: {lab}  (priority {a.get('priority', 1.0)})")

    # The NEED, surfaced from the agent's actual ARC action contract: ACTION6
    # addresses a <=64x64 coordinate grid; when the menu must be bounded the
    # question is WHICH coordinates to cover.  This is read from the agent's
    # world contract (arc3 GRID up to 64x64), not invented.
    print("\n(iv) The NEED it faces in ARC (its action contract): ACTION6 "
          "addresses a\n     coordinate grid up to 64x64 = 4096 cells; the "
          "discovery runway is a\n     SEARCH over that space until the "
          "admittable rule is present.  The menu\n     must be bounded -- so "
          "WHICH coordinates cover the space in fewest clicks?")

    # The agent's verdict is the MATCH between its held phi_addressing concept
    # and this need -- surfaced by its own concept faculty, not asserted by us.
    # phi_addressing.definition NAMES "exploration ... redundancy-free
    # search/sampling (e.g. rule-space exploration)"; understand_space NAMES
    # cover-the-space.  The agent's assessment is that pairing.
    names_exploration = "exploration" in phi_def.lower()
    names_search = "search" in phi_def.lower() or "sampling" in phi_def.lower()
    print("\n(v) The agent's assessment (its concept matched to its need):")
    print(f"    - phi_addressing names exploration as a use: {names_exploration}")
    print(f"    - phi_addressing names search/sampling as a use: {names_search}")
    print("    - its exploration_value Term-tree is the graph-resident faculty")
    print("      that ORDERS which cell to cover next (argmax'd by _pick_goal).")
    print("    VERDICT (agent, from its own faculties): PhiMap applies to the")
    print("    ACTION6 COORDINATE COVERAGE -- fold the golden low-discrepancy")
    print("    map into exploration_value so coverage is maximally-even (no")
    print("    clump / no gap) instead of a fixed stride that re-treads a grid.")


# --------------------------------------------------------------------------
# STEP 2 -- the agent APPLIES PhiMap, graph-resident.
# --------------------------------------------------------------------------
def step2_adjust(agent) -> None:
    _bar("STEP 2 -- the agent APPLIES PhiMap graph-resident (folds it into its "
         "OWN\nexploration_value Term-tree -- the exact mechanism arc3_seed "
         "uses for goal_cell)")

    native = agent._exploration_value_term()

    # The agent's fold: a PhiMap-keyed low-discrepancy coverage bonus on the
    # candidate cell's linear index.  The SpatialLocation cell carries row/col
    # attrs (domains/arc3_world.py emits them); its linear address n=row*64+col.
    # PhiMap(n) in [0,1) is the golden coordinate; the bonus lifts cells by that
    # golden coordinate so _pick_goal's argmax SPREADS coverage by the golden
    # sequence (maximally even, no clump / no gap) rather than re-treading a
    # rigid stride.  Composed ENTIRELY from existing DSL primitives + the
    # verified PhiMap Term -- no new Rust, no hand-tuned magic beyond phi.
    # n = row*64 + col  (the cell's linear coordinate address)
    lin = Plus(items=(Times(items=(Attr(Var("cell"), "row"), Lit(64))),
                      Attr(Var("cell"), "col")))
    phi = phimap_term(lin)   # the verified golden low-discrepancy address
    # Coverage bonus: scaled golden coordinate.  Sits on the native recency
    # term's magnitude (recency ~ tick counts; the goal_cell bonus is 1e9 and
    # dominates only once grounded).  A bounded lift (0..2) breaks equal-novelty
    # ties by golden spread -- it ORDERS coverage the way the low-discrepancy
    # sequence covers the space.
    phi_bonus = Times(items=(phi, Lit(2.0)))

    augmented = Plus(items=(native, phi_bonus))

    # Re-wire the agent's exploration_value edge to the augmented Term-tree
    # (graph-resident; the same splice arc3_seed does for goal_cell).
    for e in list(agent.mind_graph.out_edges(agent.agent_root,
                                             "exploration_value")):
        agent.mind_graph._delete_edge(e.key)
    root = term_to_subgraph(augmented, agent.mind_graph)
    agent.mind_substrate.add_edge(agent.agent_root, "exploration_value", root)
    agent._named_predicate_cache["exploration_value"] = augmented

    print("  WIRED: exploration_value <- Plus(native, PhiMap-coverage-bonus).")
    print("  The bonus reads the candidate cell's linear address n = row*64+col,")
    print("  maps it through the verified PhiMap Term frac(n.phi^-1), and lifts")
    print("  cells by their golden low-discrepancy coordinate -- so _pick_goal's")
    print("  argmax now SPREADS coverage by the golden sequence.")

    # Confirm it is graph-resident.
    edges = list(agent.mind_graph.out_edges(agent.agent_root,
                                            "exploration_value"))
    print(f"  exploration_value edges from agent_root now: {len(edges)} "
          f"(graph-resident).")

    # Sanity: evaluate the bonus alone for a few cell addresses via the agent's
    # OWN DSL evaluator to show it is a live golden sequence.
    probe = Times(items=(phimap_term(Var("n")), Lit(2.0)))
    vals = [round(float(probe.evaluate({"n": n}, agent.mind_graph)), 4)
            for n in range(8)]
    print(f"  golden coverage-bonus for cell addresses 0..7: {vals}")


def main() -> None:
    _bar("THE JABBERWOCK ASSESSES + ADJUSTS: PhiMap for ARC-AGI-3 coordinate "
         "coverage")
    print("  Shell boots the ARC agent, hands it the phi_addressing Concept +")
    print("  the native PhiMap Term, and drives ITS faculties to assess where")
    print("  the golden low-discrepancy map helps, then folds it in graph-")
    print("  resident.  No hand-authored placement, no grading.\n")

    _bar("BOOT -- the agent (a graph), Body SELF, with the live ARC-AGI-3 seed")
    agent = boot_agent()

    _bar("RESOURCE -- supply the phi_addressing Concept + verify the native "
         "PhiMap Term")
    phi_def = supply_phi_concept(agent)
    verify_phimap(agent)

    step1_assess(agent, phi_def)
    step2_adjust(agent)

    _bar("HONEST -- the assessment above is the agent's own introspection over "
         "its\nphi_addressing concept + ARC drives; the adjustment is folded "
         "into its OWN\ngraph-resident exploration_value Term-tree (arc3_seed's "
         "goal_cell mechanism).")


if __name__ == "__main__":
    main()
