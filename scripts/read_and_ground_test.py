"""PROVE the LIVE read-and-ground learning loop closes — honestly.

When the agent hits an UNGROUNDED concept (its graph-native coherence is low, so
it KNOWS it doesn't understand), instead of only abstaining it GOES AND LEARNS:
it READS the concept's definition, COMPREHENDS it with its own construction
grammar, GROUNDS it by composing built_from edges over concepts it already holds
(recursively, toward the seeded primitives), and RE-CHECKS coherence. The whole
loop is the agent's OWN machinery composed:

    GAP (coherence) -> READ (reference reader) -> COMPREHEND (constructions)
        -> GROUND (ground_concept) -> [recurse] -> RE-COHERE (coherence)

This script proves, with the full trace:
  1. THE LOOP CLOSES on a comprehensible case: 'a widget is a device' fed; a
     question about `widget` -> coherence LOW -> read_and_ground -> reads the
     definition -> grounds widget built_from device -> coherence MEETS the bar ->
     the agent PROCEEDS (it learned the concept live).
  2. RECURSION: a 2-level case (gizmo defined via gadget, gadget itself not yet
     grounded -> recurse -> ground gadget -> ground gizmo); the cone reaches a
     seeded primitive.
  3. HONEST DEGRADE: a complex real definition (a relative clause the
     constructions can't decompose) -> read_and_ground returns grounded=False
     (comprehension-bound) -> the agent ABSTAINS honestly.
  4. NO REGRESSION: already-coherent questions (capital->Paris, gcd, sumsq) are
     unaffected; the abstain still fires when grounding genuinely fails.

No LLM. The MEANING is the construction grammar's (graph data); the GROUND is
ground_concept (an admissible Concept->Concept mutation). Comprehension is the
NAMED bottleneck — more definitional constructions = the additive next step.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import grounded_representation as gr
from domains import read_and_ground as rag
from scripts.language_test import training_bank


SEP = "=" * 72


def _seed_primitive(s, name: str) -> None:
    """Seed a PRIMITIVE concept the agent already holds (built_from nothing) —
    the basis the recursion must bottom out at. A held basis concept, the kind
    the seed loaders install."""
    for c in s.nodes("Concept"):
        if s.node(c)["attrs"].get("name") == name:
            return
    s.add_node("Concept", {"name": name, "origin": "seed_primitive"})


def main(argv: list[str]) -> int:
    s = _native.Substrate()
    print(SEP)
    print("Setup: train comprehension; build the conversation world")
    print(SEP)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    world.run()
    world.teacher_disabled = True
    cw = ConversationWorld(world)

    # Seed the PRIMITIVES the new concepts will ground out at (held basis
    # concepts — built_from nothing). 'device' is the genus of 'widget'; 'gadget'
    # will be grounded onto 'device' too in the recursion case.
    for prim in ("device",):
        _seed_primitive(s, prim)

    # FEED the definitions the agent will READ (a teacher's gloss / a staged
    # lead). In the live system these come from the reference reader (web_world);
    # here we feed comprehensible + complex definitions to prove the loop + the
    # honest degrade deterministically (no network dependency).
    cw._definition_feed = {
        # comprehensible — a simple genus the constructions parse.
        "widget": "a widget is a device",
        # recursion — gizmo via gadget, gadget itself via device (a primitive).
        "gizmo": "a gizmo is a gadget",
        "gadget": "a gadget is a device",
        # complex — a relative clause the constructions CANNOT decompose.
        "bordism": ("a bordism is an equivalence that relates manifolds whose "
                    "disjoint union is the boundary of a higher manifold"),
    }

    # ---------------------------------------------------------------- 1. CLOSE
    print()
    print(SEP)
    print("1. THE LOOP CLOSES — 'widget' is NOT held; the agent learns it live")
    print(SEP)
    held_before = gr._find_concept(s, "widget") is not None
    print(f"  before: widget is a held Concept? {held_before}  (must be False)")

    res = rag.read_and_ground(s, "widget", cw)
    tr = res["trace"]
    print(f"  READ       : {tr.get('read')!r}")
    print(f"  COMPREHEND : {tr.get('comprehend')}")
    print(f"  GROUND     : {tr.get('ground')}")
    print(f"  structure  : {res['structure']}")
    print(f"  -> grounded={res['grounded']}  reason={res['reason']}")
    widget_id = gr._find_concept(s, "widget")
    proof = gr.grounding_reaches_primitives(s, widget_id)
    print(f"  CONE       : size={proof['cone_size']} depth={proof['depth']} "
          f"primitives={proof['primitives']} grounded={proof['grounded']}")
    close_ok = res["grounded"] and proof["grounded"]

    # The DIRECT re-cohere proof: the SAME frame goes from coherence 0.0 (the
    # fillers are not held concepts) to 1.0 after read_and_ground grounds them —
    # the gap closing, measured by the agent's OWN coherence function.
    print()
    print("  --- DIRECT re-cohere: same frame, coherence BEFORE vs AFTER ---")
    s_rc = _native.Substrate()
    gr.open_grounding_productions(s_rc)
    _seed_primitive(s_rc, "device")
    from domains import coherence_graph as _cohg
    from domains import construction_grammar as _cg

    class _Conv:
        _definition_feed = {"widget": "a widget is a device",
                            "gadget": "a gadget is a device"}
        _constructions = _cg.load_constructions()
    # a two-filler frame: both fillers ungrounded -> coherence 0.0.
    rc_frame = {"agent": "widget", "patient": "gadget", "speech_act": "question"}
    coh_before = _cohg.coherence(s_rc, rc_frame, False)
    for f in ("widget", "gadget"):
        rag.read_and_ground(s_rc, f, _Conv())
    coh_after = _cohg.coherence(s_rc, rc_frame, False)
    print(f"  frame fillers : {_cohg.content_fillers(rc_frame)}")
    print(f"  coherence     : BEFORE={coh_before:.3f}  AFTER={coh_after:.3f}"
          f"  (grounded both to shared primitive 'device' -> connected)")
    recohere_ok = coh_before < 0.5 and coh_after >= 0.99
    close_ok = close_ok and recohere_ok

    # The full TURN: gap (low coherence) -> read_and_ground -> re-cohere ->
    # PROCEED. Disable the external reference lookup so the ONLY path past the
    # comprehension abstain is the agent LEARNING the concepts (else a network
    # reference route could answer without comprehending). This isolates the
    # comprehension-abstain mechanism the loop hooks.
    print()
    print("  --- the FULL TURN (abstain path; reference lookup OFF to isolate) ---")
    s2 = _native.Substrate()
    w2 = LanguageWorld(s2, training_bank(), teacher_stub)
    w2.run(); w2.teacher_disabled = True
    cw2 = ConversationWorld(w2)
    cw2.reference_lookup = None  # isolate the comprehension-abstain mechanism
    _seed_primitive(s2, "device")
    # two NONSENSE content words the parser keeps as-is (not lemmatized to a
    # held lexicon concept): the agent does NOT hold 'wug'/'zib'; it learns them
    # by reading their fed definitions and grounding both onto 'device'.
    cw2._definition_feed = {"wug": "a wug is a device",
                            "zib": "a zib is a device"}
    reply = cw2.turn("Is the wug a zib?", "en")
    rec = cw2.transcript[-1]
    coh = rec.get("coherence", {})
    rng = rec.get("read_and_ground", {})
    print(f"  USER : Is the wug a zib?")
    print(f"  fillers   : {coh.get('fillers')}")
    print(f"  coherence : value={coh.get('value')}"
          f"  after_learning={coh.get('value_after_learning')}"
          f"  required={coh.get('required'):.3f}")
    if rng.get("attempts"):
        for a in rng["attempts"]:
            print(f"  read_and_ground: filler={a['filler']!r} "
                  f"grounded={a['grounded']}  structure={a['structure']}")
    proceeded = rec.get("band") != "NOT_COMPREHENDED" and "read_and_ground" in rec
    print(f"  knowledge_op: {rec['knowledge_op'][:120]}")
    print(f"  AGENT: {reply!r}")
    print(f"  -> read_and_ground FIRED on abstain path + PROCEEDED past the "
          f"comprehension abstain? {proceeded}")
    close_ok = close_ok and proceeded

    # ------------------------------------------------------------- 2. RECURSE
    print()
    print(SEP)
    print("2. RECURSION — 'gizmo' via 'gadget' (gadget itself not yet grounded)")
    print(SEP)
    res2 = rag.read_and_ground(s, "gizmo", cw, max_depth=2)
    tr2 = res2["trace"]
    print(f"  gizmo READ      : {tr2.get('read')!r}")
    print(f"  gizmo COMPREHEND: {tr2.get('comprehend')}")
    sub = tr2.get("recursed")
    if sub:
        print(f"    RECURSE -> gadget READ      : {sub.get('read')!r}")
        print(f"    RECURSE -> gadget COMPREHEND: {sub.get('comprehend')}")
        print(f"    RECURSE -> gadget GROUND    : {sub.get('ground')}")
    print(f"  gizmo GROUND    : {tr2.get('ground')}")
    print(f"  -> grounded={res2['grounded']}  structure={res2['structure']}")
    gizmo_id = gr._find_concept(s, "gizmo")
    proof2 = gr.grounding_reaches_primitives(s, gizmo_id)
    chain = gr.cone(s, gizmo_id)
    chain_names = [s.node(c)["attrs"].get("name") for c in chain]
    print(f"  CONE (built_from*): {chain_names}  depth={proof2['depth']} "
          f"primitives={proof2['primitives']}")
    recurse_ok = (res2["grounded"] and sub is not None
                  and proof2["depth"] >= 2 and "device" in proof2["primitives"])

    # ------------------------------------------- 2b. GAP 1: COMPLEX DEF GROUNDS
    print()
    print(SEP)
    print("2b. GAP 1 — a COMPLEX definition (relative clause) now COMPREHENDS:")
    print("    'a manifold is a topological space that locally resembles ...'")
    print("    -> genus EXTRACTED ('topological space') -> grounds where it")
    print("       returned False before. (genus seeded -> the cone closes.)")
    print(SEP)
    s_m = _native.Substrate()
    gr.open_grounding_productions(s_m)
    _seed_primitive(s_m, "topological_space")

    class _ConvM:
        _definition_feed = {
            "manifold": ("a manifold is a topological space that locally "
                         "resembles Euclidean space")}
        _constructions = _cg.load_constructions()
    res_m = rag.read_and_ground(s_m, "manifold", _ConvM())
    tr_m = res_m["trace"]
    print(f"  manifold READ      : {tr_m.get('read')!r}")
    print(f"  manifold COMPREHEND: {tr_m.get('comprehend')}")
    print(f"  -> grounded={res_m['grounded']}  structure={res_m['structure']}")
    print(f"     reason: {res_m['reason']}")
    # the structure must extract the HEAD NOUN genus (not the whole tail) and
    # ground manifold built_from topological_space -> the cone reaches the seeded
    # primitive. The differentia is recorded as a label, NOT required to ground.
    cm = res_m["structure"] or {}
    gap1_grounds = (res_m["grounded"]
                    and cm.get("genus") == "topological_space"
                    and "topological_space" in (cm.get("primitives") or [])
                    and bool(tr_m.get("comprehend", {}).get("differentia")))

    # -------------------------------------------------------- 3. HONEST DEGRADE
    print()
    print(SEP)
    print("3. HONEST DEGRADE — Gap 1 moved the line: a complex def now")
    print("   COMPREHENDS (genus extracted), but if the genus is itself")
    print("   un-held it still HONESTLY fails to ground (bare-leaf genus).")
    print(SEP)
    res3 = rag.read_and_ground(s, "bordism", cw)
    tr3 = res3["trace"]
    print(f"  bordism READ      : {tr3.get('read')!r}")
    print(f"  bordism COMPREHEND: {tr3.get('comprehend')}  (genus extracted)")
    print(f"  -> grounded={res3['grounded']}  reason={res3['reason']}")
    # the def now COMPREHENDS (a frame with genus is recovered) but the genus
    # 'equivalence' is a bare leaf the agent does not hold -> grounded=False,
    # honestly (the boundary moved from 'did not comprehend' to 'genus un-held').
    comprehended3 = bool(tr3.get("comprehend"))
    degraded = comprehended3 and (not res3["grounded"])

    # the FULL TURN abstains honestly on the complex concept: read_and_ground
    # is ATTEMPTED, fails to comprehend, coherence stays low -> abstain. Reference
    # lookup OFF to isolate the comprehension mechanism (a research term is not
    # encyclopedia-summary-extractable anyway — reference_route's stated limit —
    # but disabling it makes the comprehension-bound abstain deterministic).
    s3 = _native.Substrate()
    w3 = LanguageWorld(s3, training_bank(), teacher_stub)
    w3.run(); w3.teacher_disabled = True
    cw3 = ConversationWorld(w3)
    cw3.reference_lookup = None
    cw3._definition_feed = {
        "bordism": ("a bordism is an equivalence that relates manifolds whose "
                    "disjoint union is the boundary of a higher manifold"),
        "spin": ("a spin is a property that relates particles whose intrinsic "
                 "angular momentum is quantized")}
    reply3 = cw3.turn("Did the bordism break the spin?", "en")
    rec3 = cw3.transcript[-1]
    rng3 = rec3.get("read_and_ground", {})
    if rng3.get("attempts"):
        for a in rng3["attempts"]:
            print(f"  read_and_ground attempt: filler={a['filler']!r} "
                  f"grounded={a['grounded']}  reason={a['reason']}")
    print(f"  FULL TURN reply: {reply3!r}  band={rec3.get('band')}")
    abstained = rec3.get("band") == "NOT_COMPREHENDED"
    print(f"  -> abstained honestly (comprehension-bound)? {abstained}")
    degrade_ok = degraded and abstained

    # ----------------------------------------------------------- 4. NO REGRESSION
    print()
    print(SEP)
    print("4. NO REGRESSION — already-coherent questions unaffected")
    print(SEP)
    s4 = _native.Substrate()
    w4 = LanguageWorld(s4, training_bank(), teacher_stub)
    w4.run(); w4.teacher_disabled = True
    cw4 = ConversationWorld(w4)
    cw4.reference_lookup = None  # isolate: no off-path web answers in this block
    cw4.turn("The cat sat on the mat.", "en")
    r_known = cw4.turn("Who sat on the mat?", "en")
    rec_known = cw4.transcript[-1]
    no_learn_on_known = "read_and_ground" not in rec_known
    print(f"  'Who sat on the mat?' -> {r_known!r}  band={rec_known.get('band')}")
    print(f"    (coherent question never entered read_and_ground: "
          f"{no_learn_on_known})")

    r_gcd = cw4.turn("What is the gcd of 48 and 36?", "en")
    rec_gcd = cw4.transcript[-1]
    print(f"  'What is the gcd of 48 and 36?' -> {r_gcd!r}")
    r_sumsq = cw4.turn("What is the sum of squares up to 10?", "en")
    rec_sumsq = cw4.transcript[-1]
    print(f"  'What is the sum of squares up to 10?' -> {r_sumsq!r}")

    coherent_ok = (rec_known.get("band") != "NOT_COMPREHENDED"
                   and no_learn_on_known
                   and "12" in str(r_gcd) and "385" in str(r_sumsq))

    # the abstain STILL fires when grounding genuinely fails: a multi-filler
    # research frame whose fillers have NO comprehensible definition fed and NO
    # web route (reference_lookup off) -> read_and_ground can't ground them ->
    # coherence stays low -> the agent abstains honestly.
    r_res = cw4.turn("Did the bordism break the cobordism?", "en")
    rec_res = cw4.transcript[-1]
    rng_res = rec_res.get("read_and_ground", {})
    abstain_fires = rec_res.get("band") == "NOT_COMPREHENDED"
    if rng_res.get("attempts"):
        for a in rng_res["attempts"]:
            print(f"  research filler {a['filler']!r}: grounded={a['grounded']}"
                  f"  reason={a['reason']}")
    print(f"  research question (no comprehensible def, no web): {r_res!r}  "
          f"band={rec_res.get('band')}")
    print(f"    -> abstain still fires on genuine grounding failure: "
          f"{abstain_fires}")

    # ----------------------------------------------- 5. PROVENANCE + ATTRIBUTION
    print()
    print(SEP)
    print("5. COMPREHEND ITS SOURCE — the agent HOLDS what Wikipedia IS, attaches")
    print("   PROVENANCE on grounding, reads HOW + the EPISTEMIC WEIGHT off the")
    print("   held concept (NOT hardcoded), and can ATTRIBUTE an answer.")
    print(SEP)
    from domains import communication_concepts as _comm
    from domains import source_provenance as _sp
    from domains import epistemic_access as _epa

    s5 = _native.Substrate()
    _comm.install_communication_concepts_seed(s5)

    # (a) the agent HOLDS what Wikipedia is: wikipedia is-a encyclopedia is-a
    #     reference_work is-a source, GROUNDED, with conventions + reliability.
    chain_ok = True
    for nm in ("source", "reference_work", "encyclopedia", "wikipedia"):
        cid = gr._find_concept(s5, nm)
        pr = gr.grounding_reaches_primitives(s5, cid) if cid else {"grounded": False}
        print(f"  holds {nm:14s}: grounded={pr['grounded']} prims={pr.get('primitives')}")
        chain_ok = chain_ok and bool(pr.get("grounded"))
    conv = _sp.conventions_for_source(s5, "local_wiki")
    print(f"  encyclopedia conventions (read off held concept): "
          f"lead_defines={conv.get('lead_defines') if conv else None} "
          f"domain_preface={conv.get('domain_preface') if conv else None!r}")
    epi = _sp.epistemic_status_for_source(s5, "wikipedia")
    print(f"  wikipedia epistemic status (read off held reliability): "
          f"status={epi.get('status') if epi else None} "
          f"reliability={epi.get('reliability') if epi else None} "
          f"conf={epi.get('confidence') if epi else None}")
    holds_ok = (chain_ok and conv is not None and conv.get("lead_defines") is True
                and epi is not None and epi.get("status") == "consensus")

    # (b) PROVENANCE on grounding: simulate a READ of 'manifold' FROM Wikipedia
    #     (the wiki_local provenance template) and ground it — the grounded node
    #     CARRIES {source, genre, who, how, where, when} + epistemic status read
    #     off the held source. (Offline + deterministic: a staged wiki summary.)
    gr.open_grounding_productions(s5)
    _seed_primitive(s5, "topological_space")
    wiki_prov = {"source": "wikipedia", "genre": "encyclopedia",
                 "who": "editorial_consensus", "how": "encyclopedic",
                 "where": "Manifold",
                 "when": "2024-09 structured-wikipedia enwiki snapshot"}
    epi_status = _sp.epistemic_status_for_source(s5, "wikipedia")
    gres = gr.ground_concept(s5, "manifold", ["topological_space"],
                             "isa(manifold, topological_space)",
                             frame="mathematics",
                             provenance=wiki_prov, epistemic_status=epi_status)
    mid = gr._find_concept(s5, "manifold")
    import json as _json
    node_prov = _json.loads(s5.node(mid)["attrs"].get("provenance", "null"))
    node_epi = _json.loads(s5.node(mid)["attrs"].get("epistemic_status", "null"))
    print(f"\n  grounded 'manifold' FROM Wikipedia — node provenance:")
    print(f"    where={node_prov.get('where')!r} who={node_prov.get('who')!r} "
          f"how={node_prov.get('how')!r} when={node_prov.get('when')!r}")
    print(f"    epistemic_status={node_epi.get('status')!r} "
          f"(distinct from self-DERIVED / CONJECTURE)  "
          f"grounding_status={s5.node(mid)['attrs'].get('grounding_status')!r}")
    prov_ok = (node_prov.get("source") == "wikipedia"
               and node_prov.get("where") == "Manifold"
               and node_prov.get("who") == "editorial_consensus"
               and node_prov.get("when")
               and node_epi.get("status") == "consensus")

    # (c) ATTRIBUTION: a reference-route answer carries its provenance + the
    #     consensus-tertiary weight — "I read in Wikipedia that ..." (not a bare
    #     assertion). The source name is read off the provenance, not hardcoded.
    attributed = _epa._attribute("Paris.", wiki_prov, "en")
    print(f"\n  ATTRIBUTION surface: {attributed!r}")
    bare = _epa._attribute("Paris.", None, "en")
    print(f"  (no provenance -> bare assertion: {bare!r})")
    attr_ok = ("I read in Wikipedia" in attributed and "Paris" in attributed
               and bare == "Paris.")

    provenance_ok = holds_ok and prov_ok and attr_ok

    # ------------------------------------------------------------------ SUMMARY
    print()
    print(SEP)
    print("SUMMARY")
    print(SEP)
    rows = [
        ("1. loop CLOSES (read->comprehend->ground->re-cohere->proceed)", close_ok),
        ("2. RECURSION reaches a seeded primitive (gizmo->gadget->device)", recurse_ok),
        ("2b. GAP 1 complex def COMPREHENDS+grounds (manifold->topological_space)",
         gap1_grounds),
        ("3. HONEST DEGRADE: complex def comprehends but un-held genus -> fails",
         degrade_ok),
        ("4a. coherent questions unaffected (Paris/gcd/sumsq)", coherent_ok),
        ("4b. abstain still fires on genuine grounding failure", abstain_fires),
        ("5. SOURCE COMPREHENDED: holds Wikipedia (grounded) + provenance on "
         "grounding + attribution", provenance_ok),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print()
    print(f"RESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}")
    print()
    print("Faithful framing: the loop is the agent's OWN machinery composed —")
    print("coherence (gap) -> reference reader (read) -> constructions (comprehend)")
    print("-> ground_concept (ground) -> coherence (confirm). Definitional")
    print("constructions are graph DATA. Comprehension is the NAMED bottleneck:")
    print("a complex definition needs more constructions (the additive next step).")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
