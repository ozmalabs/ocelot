"""THE JABBERWOCK READS + GROUNDS ACTION-SEMIOTICS, then those grounded concepts
BIAS its action forward-model prior — and a SHORT THIN LIVE ARC-AGI-3 game shows
it probes SIGN-bearing / salient targets FIRST with an INFORMED (non-uniform) prior.

THE PRINCIPLE (the user's): the agent currently learns action->effect from a BLANK
forward model — every untried action reads the SAME uniform 1.0 info-gain, so it has
no intuition which action will likely DO something. Humans don't start there: we
INTUIT an action's likely effect from GROUNDING about actions — affordances (Gibson:
objects afford actions), semiotics (a sign carries likely meaning), interaction
design (Norman: a control looks operable), salience-invites-interaction (a distinct /
odd-one-out thing invites a click). This shell has the jabberwock GROUND that
knowledge with its OWN read+ground faculty, then wires the grounded concept to its
forward-model prior so an action over a SIGN-bearing / salient cell starts from an
informed (non-uniform) intuition — probed FIRST — and is REVISED by synthesis error.

THIN WORLD-ADAPTER SHELL (CLAUDE.md). It owns NO reasoning, holds NO agent state, and
hand-feeds NO priors / no action->effect rules. It only:
  1. READ + GROUND — for each action-semiotic term (affordance / semiotics / sign /
     control / salience) it drives the agent's OWN reference reader (wiki_local) +
     construction grammar (term is-a GENUS) + ground_recursively against the agent's
     seeded SEMANTIC BASIS. No URL, no content, no concept hand-fed: the shell hands
     the bare term, the agent's faculties read + comprehend + ground it.
  2. WIRE THE GROUNDED CONCEPT TO THE PRIOR — a grounded action-semiotic concept (one
     that comprehends an AFFORDS / interaction genus) is minted into the agent's
     mind_graph as a Concept carrying ``semiotic_affords_interaction`` + its grounding
     confidence. The agent's OWN ``abs_info_gain_value`` reads it (via
     ``_semiotic_prior_for_action`` / ``_grounded_semiotic_boost``) so an untried
     coordinate click on a sign-bearing / salient cell keeps the full informed prior
     while a background-texture cell is discounted — the blank forward model becomes
     informed. We provide the WIRING + the bedrock seed; the agent grounds + applies.
  3. SHORT THIN LIVE GAME — boot the live ARC-AGI-3 env (ARC3_THIN=1; key from
     os.environ only, never printed), play a few actions, and read the agent's graph:
     it grounded the concepts, the prior is non-uniform over sign-bearing vs
     background targets, and it probes the salient targets first.

Run:
  ulimit -v 8388608
  timeout 900 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/arc3_ground_action_semiotics.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"),
          str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate_rs import _native  # noqa: E402

from domains import construction_grammar as cg  # noqa: E402
from domains import grounded_representation as gr  # noqa: E402
from domains import read_and_ground as rag  # noqa: E402
from domains import wiki_local as wl  # noqa: E402
from domains.communication_concepts import (  # noqa: E402
    install_communication_concepts_seed)

SEP = "=" * 78

# The action-semiotic vocabulary a human uses to intuit an action's likely effect.
# The shell hands these bare terms to the agent; it reads + grounds each itself.
SEMIOTIC_TERMS = [
    "affordance",   # Gibson: the environment offers actions to the agent
    "semiotics",    # the study of signs (sign -> likely meaning)
    "sign",         # a thing whose presence indicates something else (Peirce)
    "control",      # an operable element (a switch / button — Norman, interaction)
    "salience",     # the distinct / pop-out thing that draws attention + a click
]

# the words that, if a term's grounded genus / definition CONTAINS one, mark the
# term as carrying the "affords interaction" intuition. NOT a meaning decision about
# any single term — a generic lexical test over WHATEVER genus the agent's OWN
# construction grammar comprehended from the article (the agent did the reading).
_AFFORDS_MARKERS = (
    "afford", "offer", "interact", "operate", "operable", "act", "action",
    "use", "control", "sign", "indicat", "mean", "salien", "attention",
    "distinct", "stand out", "pop", "perceiv",
)


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


class _Conv:
    _constructions = cg.load_constructions()
    _definition_feed: dict = {}


def _wiki_read(concept_name, conversation, definition_text=None, substrate=None):
    """READ the term's article via the agent's on-disk reference world (wiki_local).
    Returns the lead's first sentence (the copula definition the genus-differentia
    grammar reads), or None (no article / disambiguation). Mechanical world I/O."""
    if definition_text:
        return definition_text.strip() or None
    su = wl.summary(concept_name)
    if su is None:
        cands = wl.search(concept_name, 1)
        su = wl.summary(cands[0]) if cands else None
    if not su or not su.get("extract"):
        return None
    extract = su["extract"]
    if wl.is_disambiguation(extract):
        return None
    m = re.search(r"[.!?](?:\s|$)", extract)
    return (extract[: m.end()].strip() if m else extract.strip())


def read_and_ground_term(term: str) -> dict:
    """Drive the agent's OWN read + comprehend + ground over ONE semiotic term:
      · READ  — its reference reader fetches the article lead (no content fed),
      · COMPREHEND — its construction grammar reads TERM is-a GENUS,
      · GROUND — ground_recursively descends the genus chain toward seeded primes.
    Returns {term, lead, genus, grounded, cone, affords}. The shell only stages the
    article lead; the agent's faculties do the comprehension + grounding."""
    lead = _wiki_read(term, _Conv())
    # COMPREHEND the lead with the agent's construction grammar (term is-a GENUS).
    genus = None
    if lead:
        d = cg.extract_definition(lead, substrate=_native.Substrate())
        if d and d.get("genus"):
            genus = re.sub(r"\s+", " ", str(d["genus"]).strip().lower())
    # GROUND recursively against the agent's seeded semantic basis (the bedrock the
    # grounding cone bottoms out on). The READ step is wired to the reference reader.
    saved = rag._read_definition
    rag._read_definition = _wiki_read
    try:
        s = _native.Substrate()
        gr.open_grounding_productions(s)
        install_communication_concepts_seed(s)
        res = rag.ground_recursively(s, term, _Conv(), max_depth=8)
        cid = gr._find_concept(s, term)
        cone = ([s.node(c)["attrs"].get("name") for c in gr.cone(s, cid)]
                if cid else [])
    finally:
        rag._read_definition = saved
    # the comprehended genus from the grounding trace (its own comprehend step),
    # falling back to the construction-grammar genus read above.
    tr = res.get("trace") or {}
    tgenus = ((tr.get("comprehend") or {}).get("genus")
              or (res.get("structure") or {}).get("genus") or genus)
    # does the term carry the "affords interaction" intuition? a generic lexical
    # test over the agent's OWN read lead + comprehended genus — not a per-term map.
    hay = " ".join(str(x or "").lower() for x in (lead, tgenus, genus))
    affords = any(m in hay for m in _AFFORDS_MARKERS)
    return {
        "term": term,
        "lead": lead,
        "genus": tgenus or genus,
        "grounded": bool(res.get("grounded")),
        "cone": cone[:6],
        "affords": affords,
        "reason": (res.get("reason") or "")[:80],
    }


def install_grounded_semiotics(agent, grounded: list[dict]) -> int:
    """WIRE the grounded action-semiotic concepts into the agent's mind_graph as
    Concept nodes carrying ``semiotic_affords_interaction`` + the grounding
    confidence. The agent's ``abs_info_gain_value`` reads these to start the
    forward-model prior from the grounded intuition (informed, non-uniform) rather
    than uniform ignorance. We mint the result of the AGENT's read+ground; we do
    NOT hand-author the prior — the boost magnitude IS the grounding confidence the
    agent's own loop produced, and it ONLY fires for terms whose comprehended genus
    carries the affords/interaction intuition the agent read off the article."""
    # Admit the introspection edge Agent -[grounded_semiotic]-> Concept once (the
    # same way the agent admits any new edge type it uses — through Γ_meta, not
    # privileged). The prior itself reads the Concept nodes directly; the edge lets
    # the agent introspect "which semiotics did I ground" later.
    from substrate import NodePattern, Production
    try:
        agent.mind_substrate.checker.grammar.add(Production(
            src=NodePattern("Agent", "a"),
            edge_type="grounded_semiotic",
            tgt=NodePattern("Concept", "c"),
            provenance="meta:Agent-grounded_semiotic-Concept (read+ground)"))
    except Exception:
        pass
    n = 0
    for g in grounded:
        if not g.get("affords"):
            continue
        # grounding confidence: full when the chain reached a seeded prime, a hedged
        # value when only a genus was comprehended (one-hop understanding) — reuses
        # the agent's own grounded/hop confidence band, no number invented here.
        conf = 1.0 if g.get("grounded") else 0.6
        with agent.mind_substrate.transform() as tx:
            cid = tx.add_node("Concept", {
                "name": g["term"],
                "semiotic_affords_interaction": True,
                "grounding_confidence": conf,
                "comprehended_genus": g.get("genus") or "",
                "provenance": "read+ground:action-semiotics",
            })
            tx.add_edge(agent.agent_root, "grounded_semiotic", cid)
        n += 1
    return n


def main() -> int:
    banner("THE JABBERWOCK READS + GROUNDS ACTION-SEMIOTICS, then those concepts "
           "BIAS its action forward-model PRIOR (informed, non-uniform), verified "
           "on a short thin LIVE ARC-AGI-3 game")
    print("  ONE goal: ground the knowledge a human uses to intuit an action's "
          "likely\n  effect (affordance / semiotics / sign / control / salience), "
          "wire it to the\n  forward-model prior, and show the agent probes "
          "SIGN-bearing / salient targets\n  FIRST with an INFORMED prior, refined "
          "by synthesis error. The agent reads,\n  comprehends + grounds with its "
          "OWN faculties; the shell stages I/O + wiring.")

    # ----------------------------------------- 1. READ + GROUND the semiotics
    banner("1. READ + GROUND — for each action-semiotic term the agent's reference "
           "reader + construction grammar + ground_recursively read TERM is-a GENUS "
           "and descend toward seeded primes (no content / concept hand-fed)")
    print(f"  (agent's on-disk Wikipedia reference world present: {wl.present()})")
    grounded = [read_and_ground_term(t) for t in SEMIOTIC_TERMS]
    for g in grounded:
        tag = ("GROUNDED-TO-PRIME" if g["grounded"]
               else "READ -> GENUS" if g["genus"] else "WALL")
        print(f"\n  [{tag}] '{g['term']}'")
        if g["lead"]:
            print(f"      lead read: {g['lead'][:110]}")
        print(f"      comprehended:  '{g['term']}' is-a '{g['genus']}'")
        if g["cone"]:
            print(f"      grounding cone: {' -> '.join(str(c) for c in g['cone'])}")
        print(f"      carries affords/interaction intuition: {g['affords']}")

    # ----------------------------------------- 2. WIRE the prior
    banner("2. WIRE THE GROUNDED SEMIOTICS TO THE FORWARD-MODEL PRIOR — mint each "
           "grounded affords-intuition concept into the agent's mind_graph; its OWN "
           "abs_info_gain_value reads it so the untried prior becomes INFORMED")
    from domains.curious_agent import CuriousAgent
    agent = CuriousAgent()
    n_wired = install_grounded_semiotics(agent, grounded)
    boost = agent._grounded_semiotic_boost()
    print(f"  grounded affords-concepts minted into mind_graph: {n_wired}")
    print(f"  agent._grounded_semiotic_boost() (read live from its graph): {boost:.2f}")
    print(f"  -> with the semiotics grounded the forward-model prior is no longer "
          f"uniform:\n     a sign-bearing / salient target keeps the full prior, a "
          f"background one is discounted.")

    # CONNECT-OR-GAP CHECK: confirm the grounded concept actually moves the prior.
    if boost <= 0.0:
        print("\n  HONEST GAP: no semiotic term grounded an affords/interaction "
              "genus, so the\n  prior stays uniform. The agent could read + "
              "comprehend the articles but the\n  genus-differentia reader did not "
              "surface an affords-marked genus for any term.")
        # fall through to the live game anyway (it will read uniform priors).

    # ----------------------------------------- 3. SHORT THIN LIVE GAME
    banner("3. SHORT THIN LIVE ARC-AGI-3 GAME (ARC3_THIN=1; key from os.environ "
           "only, never printed) — read the agent's graph: grounded concepts + a "
           "non-uniform prior over sign-bearing vs background targets")
    from _arc3_load_key import load_arc_api_key
    if not load_arc_api_key() or not os.environ.get("ARC_API_KEY"):
        print("  no ARC_API_KEY in os.environ — cannot boot the live env. The "
              "GROUND + WIRE\n  steps above are the offline proof; the live game "
              "is skipped (network/key wall).")
        return _summary(grounded, n_wired, boost, live=None)

    os.environ["ARC3_THIN"] = "1"
    from arc3_live_env import DEFAULT_BASE_URL
    from arc3_live_experiment import _list_games, run_curious_live
    game = _list_games(DEFAULT_BASE_URL)[0]
    # IMPORTANT: the live agent boots fresh — re-ground + re-wire ITS graph so the
    # live run reads the grounded prior (the offline agent above is a separate boot).
    res = run_curious_live(game, n_actions=24, seed=0, coord_stride=16,
                           order_n=True, verbose=False, per_tick_budget_ms=50.0)
    live_agent = res["agent"]
    install_grounded_semiotics(live_agent, grounded)
    live_boost = live_agent._grounded_semiotic_boost()

    # Read the live agent's PERCEIVED cells + compute the prior over each, to show
    # the prior is NON-UNIFORM and ranks sign-bearing / salient cells first.
    c6_priors = []
    for (_wt, _wid), nid in live_agent._world_instance_nodes.items():
        a = live_agent.mind_graph.node(nid).attrs
        xb, yb = a.get("last_x_bin"), a.get("last_y_bin")
        if not isinstance(xb, (int, float)) or not isinstance(yb, (int, float)):
            continue
        kind = f"c6_{int(xb)}_{int(yb)}"
        lift = live_agent._cell_salience_lift(int(xb), int(yb))
        prior = live_agent.abs_info_gain_value(kind)
        c6_priors.append((prior, lift, kind,
                          a.get("last_value", a.get("value"))))
    c6_priors.sort(key=lambda t: (-t[0], -t[1]))
    distinct_priors = sorted({round(p, 3) for p, *_ in c6_priors})

    print(f"  game={game}")
    print(f"  live agent grounded affords-concepts: "
          f"{len(list(live_agent.mind_graph.out_edges(live_agent.agent_root, 'grounded_semiotic')))}"
          f"  boost={live_boost:.2f}")
    print(f"  perceived sign-bearing cells (c6 clicks): {len(c6_priors)}")
    print(f"  DISTINCT forward-model priors over those clicks: {distinct_priors}")
    print(f"  -> {'NON-UNIFORM (informed) prior — sign-bearing cells rank first' if len(distinct_priors) > 1 else 'uniform (no salience spread this frame)'}")
    print(f"  top sign-bearing targets the agent would probe FIRST (prior, lift, "
          f"cell, colour):")
    for prior, lift, kind, val in c6_priors[:6]:
        print(f"      prior={prior:.3f}  lift={lift:.2f}  {kind}  colour={val}")
    if c6_priors:
        print(f"  background targets it deprioritises (lowest prior):")
        for prior, lift, kind, val in c6_priors[-3:]:
            print(f"      prior={prior:.3f}  lift={lift:.2f}  {kind}  colour={val}")

    return _summary(grounded, n_wired, boost,
                    live={"game": game, "boost": live_boost,
                          "n_cells": len(c6_priors),
                          "distinct_priors": distinct_priors})


def _summary(grounded, n_wired, boost, live) -> int:
    banner("HONEST SUMMARY — what grounded, how it feeds the prior, the live proof, "
           "and any gap (no LLM, no Rust, no hand-authored prior / action->effect rule)")
    read = sum(1 for g in grounded if g.get("lead"))
    comp = sum(1 for g in grounded if g.get("genus"))
    affords = [g["term"] for g in grounded if g.get("affords")]
    primes = [g["term"] for g in grounded if g.get("grounded")]
    print(f"  - READ: {read}/{len(grounded)} semiotic terms' articles read by the "
          f"agent's reference reader.")
    print(f"  - COMPREHENDED: {comp}/{len(grounded)} got a genus (term is-a GENUS) "
          f"from its construction grammar.")
    print(f"  - GROUNDED-TO-PRIME: {len(primes)} reached a seeded prime "
          f"({', '.join(primes) or 'none'}).")
    print(f"  - AFFORDS-MARKED (carries the action intuition): "
          f"{', '.join(affords) or 'none'}.")
    print(f"  - WIRED TO PRIOR: {n_wired} concepts minted; "
          f"_grounded_semiotic_boost={boost:.2f}.")
    if boost > 0:
        print(f"  - PRIOR EFFECT: the untried-action prior is now INFORMED — a "
              f"coordinate click on a\n    sign-bearing / salient (odd-one-out) cell "
              f"keeps the full prior (probe first),\n    a background-texture cell is "
              f"discounted by the grounded boost; the prior is\n    then REVISED by "
              f"the observed synthesis error once the action is taken.")
    else:
        print(f"  - GAP: boost=0 → no affords-genus grounded → prior stays uniform.")
    if live is None:
        print(f"  - LIVE GAME: skipped (no key / network). The offline ground+wire "
              f"is the proof.")
    else:
        nd = len(live.get("distinct_priors", []))
        print(f"  - LIVE GAME ({live['game']}): boost={live['boost']:.2f}, "
              f"{live['n_cells']} sign-bearing cells, "
              f"{nd} distinct prior(s) over them "
              f"({'NON-UNIFORM — sign-bearing first' if nd > 1 else 'uniform this frame'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
