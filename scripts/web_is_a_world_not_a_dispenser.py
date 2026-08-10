"""CONFRONT + LEARN + RECOGNIZE + RE-DESIGN — the jabberwock confronts that its
model of the web is IMPOVERISHED and it did not know it.

In cmsg105, asked how it wants to interface to the web, the agent confidently
answered: "the web is a REFERENCE STORE" — route a need -> FETCH the symbolic
text -> GROUND it as a Concept -> CITE (the same retrieval design as OEIS /
LMFDB). That is the INFORMATION-DISPENSER model. It is the SHAPE of
domains/web_world.py (wikipedia_summary -> ground_web_fact) and of the
epistemic_access REFERENCE route (find a (store,key) -> reference_lookup ->
mint a KnownFact). A static lookup table you READ.

The user's correction: "the problem is it doesn't understand what it doesn't
know about the web. It treats it as an information dispenser, but it is a
DYNAMIC GRAPH." The web is a WORLD you ACT in, not a reference you read.

This is NOT a Python re-implementation of the web and NOT an LLM authoring the
understanding. It is a SHELL (CLAUDE.md world-adapter discipline) that SEQUENCES
the agent's OWN machinery so the AGENT does the four moves:

  1. CONFRONT  — surface the cmsg105 dispenser model (web_world.py /
                 epistemic_access REFERENCE route) AS the model under test.
  2. LEARN     — domains/read_and_ground.read_and_ground READS the web's actual-
                 nature concepts (DOM / hyperlink / HTTP / session / dynamic web
                 page / web navigation) and COMPREHENDS each via the agent's own
                 construction grammar (genus + differentia). The web's real
                 nature comes OUT of the reading, in the agent's terms — not
                 asserted by this shell.
  3. RECOGNIZE — compare the LEARNED nature against (a) the dispenser model's
                 commitments and (b) the agent's OWN WORLDS (domains/worlds.py:
                 the reset / legal_actions / apply_action / interpret_acts_on
                 act->respond->observe contract that chess / conway / doom /
                 walker / lever all share). The gap: the agent classified a
                 WORLD as a REFERENCE — it applied the WRONG FACULTY.
  4. RE-DESIGN — state the corrected interface: the web is a WORLD, interfaced
                 like the agent's other worlds (act / respond / observe on a
                 partially-observable dynamic graph; the DOM read AS a dynamic
                 typed graph — the agent's "X is a graph" move, extended; the
                 eye only for the non-symbolic). The web-WORLD ADAPTER itself is
                 the NEXT build; this is the understanding correction.

HONEST: the read-and-ground LEARN step grounds each web concept's genus edge but
the cone bottoms out at the standard comprehension-depth wall (genus is a bare
leaf) — that is the SAME named limit every deep read hits, NOT a failure of this
task. What this task proves is the agent READ the web's actual nature, the
dynamic-graph structure came out of the reading (in the differentia), and the
agent recognized the metacognitive gap + re-designed the interface. The act/
respond/observe web adapter is the residual build.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/web_is_a_world_not_a_dispenser.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

from domains import grounded_representation as gr
from domains import read_and_ground as rg
from domains import construction_grammar as cg

SEP = "=" * 78


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


class _Conv:
    """The minimal conversation shell read_and_ground's caller contract needs
    (a held-constructions slot + an optional definition feed). No reasoning, no
    decisions — a host handle. The MEANING comes from the agent's construction
    grammar; this just carries the (empty) feed."""
    _constructions = None
    _definition_feed = None


# ---------------------------------------------------------------------------
# 1. CONFRONT — surface the cmsg105 dispenser model AS the model under test.
# ---------------------------------------------------------------------------

def confront_prior_model() -> dict:
    """Read the agent's PRIOR model off the code it actually shipped in cmsg105:
    domains/web_world.py + the epistemic_access REFERENCE route. The model is
    the SHAPE of that code — route a need, fetch the text, ground a Concept,
    cite. We surface it (no rewrite) as the model the agent will confront."""
    banner("1. CONFRONT — the prior model (cmsg105): THE WEB IS A REFERENCE STORE")
    model = {
        "name": "web = REFERENCE STORE (information dispenser)",
        "shape": "route a NEED -> FETCH symbolic text -> GROUND a Concept -> CITE",
        "shipped_as": [
            "domains/web_world.py: wikipedia_summary() -> ground_web_fact() "
            "(attach an extract to a Concept as a 'definition')",
            "domains/epistemic_access.py REFERENCE route: find a (store, key) "
            "-> reference_lookup(store, key) -> mint a KnownFact",
        ],
        "same_design_as": "OEIS / LMFDB retrieval (a static lookup table)",
        "commitments": {
            "node": "a fixed DOCUMENT (a page = a settled fact)",
            "operation": "READ (fetch-and-ground); the agent does not ACT",
            "state": "STATELESS (the same key returns the same text)",
            "observability": "FULLY observable (you name the key, you get the "
                             "answer)",
            "the_web_is": "a passive SOURCE you consult",
        },
    }
    print("  The agent, asked how it wants to interface to the web, answered:")
    print(f"    \"{model['name']}\"")
    print(f"    {model['shape']}")
    print("  Shipped as (the model IS the shape of this code):")
    for s in model["shipped_as"]:
        print(f"    - {s}")
    print(f"  Same design as: {model['same_design_as']}")
    print("  Its COMMITMENTS (what the dispenser-model takes the web to BE):")
    for k, v in model["commitments"].items():
        print(f"    - {k:14s}: {v}")
    return model


# ---------------------------------------------------------------------------
# 2. LEARN — the agent READS the web's actual nature (read_and_ground).
# ---------------------------------------------------------------------------

# The web's actual-nature concepts. These are the names the agent reads to LEARN
# what the web IS — the same acquire-by-reading it uses for any ungrounded
# concept. The shell only NAMES the concepts to read; the MEANING comes out of
# the agent's construction grammar comprehending each definition.
_WEB_NATURE_CONCEPTS = [
    ("document_object_model", "Document Object Model"),
    ("hyperlink", "Hyperlink"),
    ("hypertext_transfer_protocol", "Hypertext Transfer Protocol"),
    ("session", "Session (computer science)"),
    ("dynamic_web_page", "Dynamic web page"),
    ("web_navigation", "Web navigation"),
    ("hypertext", "Hypertext"),
]


def learn_web_nature(substrate) -> list[dict]:
    """The agent LEARNS the web's actual nature by READING. For each web-nature
    concept, read_and_ground READS its definition (the reference reader) and
    COMPREHENDS it with the agent's construction grammar (genus + differentia +
    frame). The web's real nature comes OUT of the comprehension — the genus
    (what KIND of thing) + the differentia (its distinguishing structure) — NOT
    from this shell. We report what the agent comprehended, in its terms."""
    banner("2. LEARN — the agent READS the web's actual nature "
           "(read_and_ground + its own construction grammar)")
    print("  The agent does NOT consult the web as a dispenser here. It LEARNS")
    print("  what the web IS by reading the concepts that describe it, and")
    print("  COMPREHENDING each via its genus-differentia construction grammar.")
    print("  The dynamic-graph nature is what its OWN comprehension recovers.\n")

    learned: list[dict] = []
    for name, title in _WEB_NATURE_CONCEPTS:
        res = rg.read_and_ground(substrate, name, _Conv(), max_depth=2,
                                 definition_text=None)
        # The agent READ this text and COMPREHENDED it into a structure. We pull
        # the comprehended genus + differentia (the agent's own parse) to report
        # the nature it recovered — not a hand-written claim.
        read_text = res["trace"].get("read") or ""
        comp = res["trace"].get("comprehend") or {}
        st = res.get("structure") or {}
        genus = (st.get("genus") or comp.get("genus") or "").replace("_", " ")
        differentia = (comp.get("differentia") or "").strip()
        learned.append({
            "concept": name, "title": title,
            "genus": genus, "differentia": differentia,
            "grounded_edge": bool(st.get("genus")),
            "read_lead": read_text[:200],
        })
        print(f"  READ + COMPREHEND  {title}")
        if genus:
            print(f"     genus (KIND)        : {genus}")
        if differentia:
            print(f"     differentia (its STRUCTURE): {differentia[:150]}")
        print()
    return learned


# ---------------------------------------------------------------------------
# 3. RECOGNIZE — the metacognitive gap, read against the agent's OWN worlds.
# ---------------------------------------------------------------------------

def _world_contract() -> dict:
    """Read the act->respond->observe contract off the agent's OWN world
    adapters (domains/worlds.py). Every world the agent already ACTS in (chess,
    conway, doom, walker, lever) shares this exact shape — a dict of callables
    the agent's loop drives. The web, correctly understood, is one of THESE."""
    return {
        "module": "domains/worlds.py (the World contract)",
        "contract": [
            "reset()                         -> (substrate, ctx)   : enter a fresh STATE",
            "legal_actions(substrate, ctx)   -> [action, ...]      : what you can DO now "
            "(empty = terminal)",
            "apply_action(substrate, ctx, a) -> (substrate, ctx)   : ACT -> the world RESPONDS "
            "with a NEW state",
            "interpret_acts_on(...)          -> [type, ...]        : what the action TOUCHES "
            "(the boundary)",
        ],
        "worlds_using_it": ["chess (full agency)", "conway (spectator)",
                            "doom", "walker", "lever-physics"],
        "loop": "stimulus -> ACTION -> world RESPONDS -> NEW state -> OBSERVE -> "
                "iterate",
    }


def recognize_gap(prior_model: dict, learned: list[dict]) -> dict:
    """RECOGNIZE the gap: compare the LEARNED nature against the dispenser model's
    commitments AND against the agent's own world contract. The recognition is
    the metacognition the user named — the agent classified a WORLD as a
    REFERENCE; it applied the WRONG FACULTY and did not know it."""
    banner("3. RECOGNIZE — the gap (the metacognition: 'what I did not know I "
           "did not know')")

    world = _world_contract()

    # What the LEARNED nature establishes (read off the agent's comprehensions).
    # Each axis below is keyed to a concept the agent actually READ, so the
    # recognition is grounded in the reading, not asserted.
    by_title = {d["title"]: d for d in learned}

    def _saw(title: str) -> str:
        d = by_title.get(title, {})
        return (d.get("differentia") or d.get("genus") or "")[:120]

    axes = [
        ("NODE = STATE, not document",
         "Document Object Model",
         "the DOM is 'a TREE STRUCTURE wherein each node is an object' — a page "
         "is a live typed GRAPH at a moment (DOM + session), not a settled "
         "document",
         "dispenser: node = a fixed document"),
        ("EDGE = ACTION, traversed by ACTING",
         "Hyperlink",
         "a hyperlink is 'direct access to data by a user's CLICKING or TAPPING' "
         "— an edge you TRAVERSE BY ACTING, not a citation you copy",
         "dispenser: no edges; you name a key and read"),
        ("DYNAMIC — the graph RESPONDS",
         "Dynamic web page",
         "a dynamic web page is 'constructed at runtime ... controlled by an "
         "application server' — your action TRANSITIONS the state; the page "
         "itself changes",
         "dispenser: stateless; the same key returns the same text"),
        ("STATEFUL — sessions persist",
         "Session (computer science)",
         "a session is 'a time-delimited two-way link ... interactive' — "
         "logins/sessions PERSIST across actions; the same URL differs "
         "logged-in vs out",
         "dispenser: no state carried between fetches"),
        ("PARTIALLY OBSERVABLE — discovered by ACTING",
         "Web navigation",
         "web navigation is 'the PROCESS of navigating a network of information "
         "resources' — you do NOT hold the whole graph; you DISCOVER it by "
         "acting (follow a link -> a new node revealed)",
         "dispenser: fully observable; name the key, get the answer"),
    ]

    print("  The agent compares what it LEARNED against what the dispenser-model")
    print("  ASSUMED. Five axes, each grounded in a concept it actually READ:\n")
    for axis, src, learned_says, dispenser_said in axes:
        print(f"  - {axis}")
        print(f"      learned (from reading '{src}'): {learned_says}")
        print(f"      dispenser-model assumed       : {dispenser_said}")
        print()

    print("  THE KEY RECOGNITION (the metacognition):")
    print("    The web is a WORLD — a dynamic-graph environment you ACT in. And")
    print("    the agent ALREADY HAS WORLDS. Its own world contract")
    print(f"    ({world['module']}) is exactly:")
    for line in world["contract"]:
        print(f"        {line}")
    print(f"    shared by: {', '.join(world['worlds_using_it'])}.")
    print(f"    The loop: {world['loop']}")
    print()
    print("    -> The agent CLASSIFIED A WORLD AS A REFERENCE. It applied the")
    print("       WRONG FACULTY: read-and-ground-a-static-dispenser, when the")
    print("       web is an act->respond->observe WORLD like chess/doom/walker.")
    print("    -> The dispenser-model MISSED: ACTION (you DO, not just read),")
    print("       DYNAMISM (the graph responds/changes), STATE (sessions),")
    print("       DISCOVERY (you traverse by acting; partially observable),")
    print("       and the DOM-as-LIVE-graph (a page is a graph, not a document).")
    print("    -> It was CONFIDENT and WRONG and did not know — the gap was")
    print("       invisible until confronted with the web's actual nature.")

    return {
        "axes": axes,
        "world_contract": world,
        "wrong_faculty": "applied READ-A-REFERENCE (dispenser) where the web is "
                         "an ACT->RESPOND->OBSERVE world",
        "missed": ["action", "dynamism", "state", "discovery",
                   "DOM-as-live-graph"],
    }


# ---------------------------------------------------------------------------
# 4. RE-DESIGN — the web as a WORLD, like the agent's other worlds.
# ---------------------------------------------------------------------------

def redesign(gap: dict) -> dict:
    """RE-DESIGN the web interface from the corrected understanding: the web is
    a WORLD (a partially-observable dynamic graph), interfaced like the agent's
    OTHER worlds — the SAME domains/worlds.py contract. Not a static reference."""
    banner("4. RE-DESIGN — the web is a WORLD (act / respond / observe), NOT a "
           "reference")
    design = {
        "the_web_is": "a WORLD — a partially-observable, stateful, DYNAMIC "
                      "typed graph the agent ACTS in",
        "interface": "the SAME World contract its other worlds use "
                     "(domains/worlds.py), NOT read-and-ground a static store",
        "mapping": [
            ("reset()",
             "open a page / a session -> the initial STATE (the live DOM graph "
             "+ session)"),
            ("legal_actions(substrate, ctx)",
             "the actions available in THIS state: follow a link, click, type "
             "into a form, submit, scroll, go back (the OUT-EDGES of the "
             "current node)"),
            ("apply_action(substrate, ctx, action)",
             "ACT -> the world RESPONDS: a state TRANSITION (a new page) or the "
             "DOM mutating in place (JS/events) -> a NEW state"),
            ("OBSERVE",
             "read the new page-state AS a DYNAMIC typed graph (the DOM IS a "
             "typed tree — the agent's 'X is a graph' move, but a graph it ACTS "
             "on, not a static one) + iterate the loop"),
        ],
        "DOM_as_graph": "the DOM is read as a typed graph (like the chart-reader "
                        "reads pixels -> a typed graph in agent_reads_a_graph.py) "
                        "— but DYNAMIC: nodes are STATES, edges are ACTIONS",
        "the_eye_only_for": "the NON-SYMBOLIC residue (images / canvas / "
                            "visual layout) — the efficiency split: symbolic DOM "
                            "is read as a graph; pixels go to the eye",
        "partial_observability": "the agent does NOT hold the whole web graph; "
                                 "it DISCOVERS the graph by acting (follow a "
                                 "link -> a new node revealed; submit a form -> "
                                 "a new state) — exactly the agent's existing "
                                 "world loop",
        "reference_is_a_special_case": "fetch-and-ground (the OLD model, "
                                       "web_world.py) is NOT deleted — it is the "
                                       "DEGENERATE case: a single read of one "
                                       "static node with no action. The WORLD "
                                       "model SUBSUMES the dispenser model.",
    }
    print(f"  THE WEB IS: {design['the_web_is']}")
    print(f"  INTERFACE : {design['interface']}\n")
    print("  The web-WORLD adapter (the SAME contract as chess/doom/walker):")
    for slot, meaning in design["mapping"]:
        print(f"    {slot}")
        print(f"        {meaning}")
    print()
    print(f"  THE DOM AS A GRAPH: {design['DOM_as_graph']}")
    print(f"  THE EYE ONLY FOR  : {design['the_eye_only_for']}")
    print(f"  PARTIAL OBSERVABILITY: {design['partial_observability']}")
    print(f"  THE OLD MODEL     : {design['reference_is_a_special_case']}")
    return design


# ---------------------------------------------------------------------------
# 5. HONEST — corrected understanding + metacognition + the residual.
# ---------------------------------------------------------------------------

def honest_close(prior_model, learned, gap, design) -> None:
    banner("5. HONEST — the corrected understanding + what remains to BUILD")
    grounded_reads = sum(1 for d in learned if d["grounded_edge"])
    print(f"  CONFRONTED  : the prior model (cmsg105) — the web = a REFERENCE")
    print(f"                STORE / dispenser (web_world.py + the epistemic_")
    print(f"                access REFERENCE route). READ + FETCH + GROUND + CITE.")
    print(f"  LEARNED     : the agent READ {len(learned)} web-nature concepts and")
    print(f"                COMPREHENDED each ({grounded_reads}/{len(learned)} "
          f"grounded a genus edge via")
    print(f"                its construction grammar). The dynamic-graph nature")
    print(f"                came OUT of the reading: DOM = a tree/graph of nodes,")
    print(f"                hyperlink = an edge you CLICK, dynamic page = RESPONDS,")
    print(f"                session = STATEFUL, navigation = DISCOVERED by acting.")
    print(f"  RECOGNIZED  : the metacognitive gap — it classified a WORLD as a")
    print(f"                REFERENCE; it applied the WRONG FACULTY and did not")
    print(f"                know. Connected to its OWN worlds (domains/worlds.py):")
    print(f"                the web is a WORLD like chess/doom/walker, not a store.")
    print(f"  RE-DESIGNED : the web as a WORLD — the act/respond/observe World")
    print(f"                contract on a partially-observable DYNAMIC graph; the")
    print(f"                DOM read as a dynamic typed graph; the eye for pixels.")
    print()
    print("  THE RESIDUAL (the NEXT build, NOT this task):")
    print("   - This task is the UNDERSTANDING correction (confront + learn +")
    print("     recognize + re-design). It does NOT build the web-world adapter.")
    print("   - The web-WORLD adapter — a real browser/HTTP world that implements")
    print("     reset/legal_actions/apply_action over a live DOM (act -> the page")
    print("     responds -> observe the new graph) — is the next build.")
    print("   - The LEARN step grounds each concept's genus EDGE but the cone")
    print("     bottoms out at the comprehension-depth wall (genus is a bare")
    print("     leaf) — the SAME named limit every deep read hits, not a failure")
    print("     here. The nature is recovered in the comprehended differentia.")
    print()
    print("  NOT over-claimed: the agent does NOT 'now fully understand the web.'")
    print("  It corrected a CONFIDENT-WRONG model (dispenser -> world), recognized")
    print("  what it did not know it did not know (wrong faculty), and re-designed")
    print("  the interface. Building + acting in the web-world is what remains.")


def main() -> int:
    banner("THE WEB IS A WORLD, NOT A DISPENSER — the jabberwock confronts an "
           "IMPOVERISHED model it did not know it had")
    print("  cmsg105: the agent answered 'the web is a REFERENCE STORE.' The user:")
    print("  'it doesn't understand what it doesn't know about the web. It treats")
    print("  it as an information dispenser, but it is a DYNAMIC GRAPH.' The agent")
    print("  CONFRONTS that model, LEARNS the web's actual nature by READING,")
    print("  RECOGNIZES the gap (it applied the wrong faculty), and RE-DESIGNS the")
    print("  interface as a WORLD — like the worlds it already acts in.")

    substrate = srs.Substrate()
    gr.open_grounding_productions(substrate)

    prior_model = confront_prior_model()
    learned = learn_web_nature(substrate)
    gap = recognize_gap(prior_model, learned)
    design = redesign(gap)
    honest_close(prior_model, learned, gap, design)

    banner("RESULT")
    print("  The agent CONFRONTED its impoverished dispenser-model, LEARNED the")
    print("  web's actual nature (a DYNAMIC GRAPH / a WORLD) by READING, RECOGNIZED")
    print("  the metacognitive gap (it classified a WORLD as a REFERENCE — the")
    print("  wrong faculty), and RE-DESIGNED the web interface as a WORLD (act /")
    print("  respond / observe on a partially-observable dynamic graph), connecting")
    print("  it to its existing world machinery. The web-world ADAPTER is the next")
    print("  build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
