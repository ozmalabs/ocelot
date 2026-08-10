"""Order-N REASONING over the grounded KnownFact graph — the agent's EXISTING
order-N operator (domains/order_n_concepts.py iterate-to-N; the same lift
domains/order_n_postulates.py made for knowledge) applied to the conversation's
facts. Single-hop QA is order-1; this CHAINS facts to depth N.

What is REUSED vs NEW (honest):
  • REUSED — the iterate-to-N STRUCTURE of order_n_concepts.nth_order_terms
    ('apply one STEP `order` times'). domains/order_n_reasoning.chain_to_order
    is that loop with the step = 'compose one more entity-sharing fact'
    (order_n_concepts' step is `_minus` over a signal).
  • REUSED — order_n_postulates' compression SELECTOR (shortest coherent chain),
    its N-scaling (order rises 1 -> 2 -> … until it resolves), and its
    derivation-chain-as-graph-node (here a ReasoningChain node, like a
    SynthesizedGap / a MonitorPass trace).
  • NEW glue — the relational-composition step (entity-sharing join over
    KnownFact role slots), the slot-resolution stop, the transitive case, and
    the conversation_world wiring (a question the single-hop match misses
    escalates to onr.reason).

Cases:
  1. 2-hop relational : love(Mary,John) + live_in(John,Paris) => where Mary's
     beloved lives = Paris (chain on John). order-2.
  2. transitive       : bigger(cat,dog)+bigger(dog,mouse) => bigger(cat,mouse).
     order-2 transitive closure.
  3. N-scaling        : a 3-fact chain resolves at order-3 (1 -> 2 -> 3 passes),
     embodying 'n scales with difficulty'.
  4. honest fail      : a question with no chain -> None -> 'I don't know'
     (NOT fabricated).

HONEST PARSE BOUNDARY (reported per case): the stub teacher's lexicon covers
only the 16 bank sentences (cat/sit/mat, Mary/love/John, …). It does NOT ground
'lives/Paris/bigger/mouse', and the comprehension grammar does not mark a
location wh-gap ('Where does X live?') or comparatives ('Is A bigger than B?').
So the multi-hop QUESTION SURFACES are NOT end-to-end parseable yet; the order-N
CHAINING is demonstrated directly on the KnownFact graph (facts asserted as
graph nodes), which is the operator under test. The end-to-end conversation
path IS exercised where the surface parses: the honest-fail question runs
through ConversationWorld.turn, and the order-N escalation is wired into that
turn (a single-hop miss calls onr.reason).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import order_n_reasoning as onr
from scripts.language_test import training_bank


def _assert_fact(s, **slots):
    """Assert a fact directly as a KnownFact graph node (the order-0 datum).
    This is what conversation_world._store_fact does on a parsed assertion; we
    call it directly for the facts whose English surface the stub teacher's
    lexicon can't ground, so the order-N operator can be exercised on a real
    KnownFact graph. Returns the node id."""
    nid = s.add_node("KnownFact", dict(slots, language="en"))
    return nid


def _print_chain(res):
    if res is None:
        print("   order-N result : NONE  -> honest 'I don't know' (no chain)")
        return
    print(f"   resolved at    : ORDER-{res['order']}  "
          f"(max order reached {res['max_order_reached']})")
    print(f"   chain ({res['order']} hop"
          f"{'s' if res['order'] != 1 else ''}) : {res['chain_str']}")
    print(f"   answer         : {res['answer']}")
    print(f"   ReasoningChain : {res['node']}  (graph node, hops={res['order']})")


def case_2hop(s):
    print("=" * 72)
    print("CASE 1 — 2-hop relational chain (compose on the shared entity)")
    print("=" * 72)
    f1 = _assert_fact(s, event="love", agent="Mary", patient="John",
                      tense="present")
    f2 = _assert_fact(s, event="live_in", agent="John", location="Paris",
                      tense="present")
    print(f"   facts:  KnownFact {f1}: love(agent=Mary, patient=John)")
    print(f"           KnownFact {f2}: live_in(agent=John, location=Paris)")
    print("   question (graph level): the LOCATION of the person John (Mary's")
    print("            beloved) — anchor=John, queried relation=live_in,")
    print("            queried slot=location.")
    res = onr.reason(s, anchor_entity="John", queried_relation="live_in",
                     queried_slot="location", anchor_slot="agent")
    _print_chain(res)
    print("   PARSE BOUNDARY: 'John lives in Paris' / 'Where does Mary's")
    print("   beloved live?' are NOT end-to-end parseable (stub teacher has no")
    print("   'lives/Paris'; grammar marks no location wh-gap). Chaining shown")
    print("   on the KnownFact graph — the operator under test. The full 2-hop")
    print("   (Mary -> John -> Paris) is exercised next.")
    print()
    # the genuine 2-hop: start from Mary, chain love THEN live_in.
    print("   full 2-hop (anchor=Mary, chain love⇒live_in to a location):")
    res2 = onr.reason(s, anchor_entity="Mary", queried_relation="live_in",
                      queried_slot="location", anchor_slot="agent")
    _print_chain(res2)
    return res2


def case_transitive(s):
    print()
    print("=" * 72)
    print("CASE 2 — transitive closure (order-N of one transitive relation)")
    print("=" * 72)
    b1 = _assert_fact(s, event="bigger", agent="cat", patient="dog")
    b2 = _assert_fact(s, event="bigger", agent="dog", patient="mouse")
    print(f"   facts:  KnownFact {b1}: bigger(agent=cat, patient=dog)")
    print(f"           KnownFact {b2}: bigger(agent=dog, patient=mouse)")
    print("   question (graph level): Is the cat bigger than the mouse?")
    res = onr.reason_transitive(s, relation="bigger", subject="cat",
                                obj="mouse")
    if res is None:
        print("   order-N result : NONE")
    else:
        print(f"   resolved at    : ORDER-{res['order']} transitive")
        print(f"   chain          : {res['chain_str']}")
        print(f"   answer         : {res['answer']}  "
              f"(cat > dog > mouse  =>  cat > mouse)")
        print(f"   ReasoningChain : {res['node']}")
    print("   PARSE BOUNDARY: comparatives ('Is A bigger than B?') do NOT parse")
    print("   to a clean frame (the stub mangles it to event=sneak); transitive")
    print("   chaining shown on the KnownFact graph.")
    return res


def case_n_scaling(s):
    print()
    print("=" * 72)
    print("CASE 3 — N-scaling: a 3-fact chain resolves at ORDER-3")
    print("=" * 72)
    # A 3-hop relational chain: Alice knows Bob, Bob knows Carol, Carol live_in
    # Rome. Ask the location reachable from Alice -> order-3.
    k1 = _assert_fact(s, event="know", agent="Alice", patient="Bob")
    k2 = _assert_fact(s, event="know", agent="Bob", patient="Carol")
    k3 = _assert_fact(s, event="live_in", agent="Carol", location="Rome")
    print(f"   facts:  KnownFact {k1}: know(Alice, Bob)")
    print(f"           KnownFact {k2}: know(Bob, Carol)")
    print(f"           KnownFact {k3}: live_in(Carol, Rome)")
    print("   question (graph level): the location reachable from Alice via the")
    print("            know-chain (anchor=Alice, queried relation=live_in,")
    print("            queried slot=location).")
    print()
    print("   N scaling with difficulty — raise the order until it resolves:")
    for cap in (1, 2, 3):
        res = onr.reason(s, anchor_entity="Alice", queried_relation="live_in",
                         queried_slot="location", anchor_slot="agent",
                         max_order=cap, record=False)
        if res is None:
            print(f"     order<= {cap}: no chain resolves "
                  f"({cap} hop{'s' if cap != 1 else ''} not enough)")
        else:
            print(f"     order<= {cap}: RESOLVED at order-{res['order']} -> "
                  f"{res['answer']}   ({res['chain_str']})")
    # record the resolving one.
    res = onr.reason(s, anchor_entity="Alice", queried_relation="live_in",
                     queried_slot="location", anchor_slot="agent", max_order=4)
    print()
    _print_chain(res)
    return res


def case_honest_fail(cw, s):
    print()
    print("=" * 72)
    print("CASE 4 — order-N honest fail: NO grounded chain -> the operator")
    print("returns None (it never fabricates a chain).")
    print("=" * 72)
    print("   The order-N OPERATOR (onr.reason) is pure-grounded: a question")
    print("   with no chain returns None — no fabrication. (The conversation")
    print("   world may then ESCALATE that miss to a low-weight CONJECTURE; see")
    print("   scripts/conjecture_test.py. 'I don't know' is reserved for the")
    print("   genuinely inadmissible case — no fact, no chain, no shape.)")
    # The order-N operator directly returns None for an unreachable relation.
    direct = onr.reason(s, anchor_entity="Mary", queried_relation="break",
                        queried_slot="patient", anchor_slot="agent")
    print(f"   onr.reason(break, from Mary) = {direct}  (None — honest)")
    # END-TO-END inadmissible: a 'Why' question queries the CAUSE slot, for
    # which the agent holds no role-prior shape and no analogous fact -> the
    # categorical 'I don't know' (no shape to conjecture from).
    reply = cw.turn("Why did Mary love John?", "en")
    rec = cw.transcript[-1]
    print(f"   END-TO-END inadmissible: 'Why did Mary love John?' (CAUSE slot,")
    print(f"     no shape) -> {reply!r}  band={rec.get('band')}")
    return direct, reply


def main(argv):
    s = _native.Substrate()
    print("=" * 72)
    print("Setup: train comprehension (teacher ON), then reason (teacher OFF).")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    log = world.run()
    summ = LanguageWorld.summary(log)
    print(f"  comprehension trained: {summ['matched']}/{summ['tasks']} matched")
    world.teacher_disabled = True
    cw = ConversationWorld(world)

    # End-to-end order-1 sanity (parseable surface) BEFORE we add graph facts:
    print()
    print("-" * 72)
    print("END-TO-END order-1 (parseable): assert 'Mary loves John.' then ask")
    print("'Who does Mary love?' — single-hop, teacher OFF.")
    print("-" * 72)
    cw.turn("Mary loves John.", "en")
    r1 = cw.turn("Who does Mary love?", "en")
    print(f"   USER : Who does Mary love?")
    print(f"   AGENT: {r1!r}   (order-1 single-hop, comprehended end-to-end)")
    print()

    r_2hop = case_2hop(s)
    r_trans = case_transitive(s)
    r_nscale = case_n_scaling(s)
    r_fail = case_honest_fail(cw, s)

    # ----- graph-resident inspection: the ReasoningChain trace nodes ------
    print()
    print("=" * 72)
    print("Order-N reasoning is graph-resident: ReasoningChain trace nodes")
    print("=" * 72)
    rcs = s.nodes("ReasoningChain")
    print(f"  {len(rcs)} ReasoningChain node(s) recorded (inspectable, like a")
    print(f"  MonitorPass trace); each carries hops=order + composed_fact edges:")
    for rc in rcs:
        a = s.node(rc)["attrs"]
        hops = [str(n) for n in s.neighbours(rc, "composed_fact")]
        print(f"    ReasoningChain {rc}: order={a.get('order')} "
              f"answer={a.get('answer')!r} chain={a.get('chain')!r}")
        print(f"        composed_fact -> {hops}")

    # ----- summary / no-regression bridge ---------------------------------
    print()
    print("=" * 72)
    print("RESULTS")
    print("=" * 72)
    ok = True
    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}  {detail}")
    chk("end-to-end order-1 QA (parseable)", "john" in (r1 or "").lower(),
        f"-> {r1!r}")
    chk("2-hop relational resolves at order-2",
        r_2hop is not None and r_2hop["order"] == 2,
        f"-> {(r_2hop or {}).get('answer')!r} (graph-level)")
    chk("transitive resolves at order-2",
        r_trans is not None and r_trans["order"] == 2,
        f"-> cat bigger than mouse = {(r_trans or {}).get('answer')!r} "
        f"(graph-level)")
    chk("N-scaling: 3-fact chain resolves at order-3",
        r_nscale is not None and r_nscale["order"] == 3,
        f"-> {(r_nscale or {}).get('answer')!r} (graph-level)")
    direct_none, inadm_reply = r_fail
    chk("order-N operator returns None on no chain (not fabricated)",
        direct_none is None, "-> onr.reason = None")
    chk("inadmissible end-to-end -> 'I don't know'",
        "don't know" in (inadm_reply or "").lower(),
        f"-> {inadm_reply!r} (end-to-end)")
    chk("ReasoningChain trace nodes recorded", len(rcs) >= 3,
        f"({len(rcs)} nodes)")
    print()
    print(f"ORDER-N REASONING: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
