"""EPISTEMIC ACCESS — the "I don't know for sure, but I know how to GET it"
stance + the ask-now / bank-for-later / drop decision, built to the taught
``epistemic_access`` model (seeds/epistemic_access.json).

This EXTENDS the confidence continuum of domains/conjecture.py with a band
BETWEEN low-weight conjecture and the categorical inadmissible:

    grounded fact        conf ~1.0      HIGH               -> "X."
    order-N chain        product/hops   HIGH/MID           -> "X." / "Probably X."
    conjecture (shape)   epsilon ~0.1   LOW                -> "I think it's like X."
    --- a ROUTE exists --------------- RESOLVABLE_VIA_ROUTE -> ask / bank / drop
    no route, no shape   —              INADMISSIBLE        -> "I don't know."

The KEY point of the model: whether to SURFACE the question to the current
audience (ask now) vs BANK it for off-path resolution vs DROP it is a SOCIAL
cost-benefit over the CONVERSATION (social_capital + cumulative_question_burden
+ flow + face + materiality), NOT just "does a source exist". The headline
behavioral result: a MATERIAL, route-having question gets BANKED (not asked)
when social capital is low — the agent is a good conversational citizen.

HONEST framing (printed below):
  * VERIFIED-ACCESS half: feeling_of_findability / transactive_memory /
    knowing_where_vs_what / value-based seek control (the route-finder).
  * SCAFFOLDING social-cost half: social_capital / flow / face / cumulative
    burden / materiality / solved_class — HEURISTIC WEIGHTS (calibratable, NOT
    ground truth). The numbers used are reported.

The cases use a hybrid (same as scripts/conjecture_test.py): some run end-to-end
through ConversationWorld.turn; others construct the query frame directly + call
the epistemic_access operators, so the SOCIAL cost-benefit + the off-path banked
resolution are exercised on a real graph with full control of the discourse
state. Every datum (SocialCapital balance, PendingGap, EpistemicAccessStance) is
graph-resident and inspected.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import epistemic_access as epa
from scripts.language_test import training_bank


def _q(event=None, queried=None, **slots):
    """Build a query frame the route-finder reads (content slots + the queried
    slot marker), as the conversation world annotates it before calling
    epistemic_access."""
    f = dict(slots)
    if event is not None:
        f["event"] = event
    f["_queried_slot"] = queried
    return f


def _print_stance(label, stance):
    print(f"   query          : {label}")
    print(f"   band           : {stance['band']}")
    route = stance.get("route")
    if route:
        print(f"   route          : {route['route_type']} -> {route['source']} "
              f"(cost {route['cost']})")
        print(f"                     basis: {route['basis']}")
    else:
        print(f"   route          : NONE (no source / reference / solved-class)")
    mat = stance.get("materiality")
    if mat:
        print(f"   materiality    : material={mat['material']} "
              f"value={mat['value']:.2f}  ({mat['why']})")
    cost = stance.get("cost")
    if cost:
        print(f"   social cost    : total={cost['total']:.2f} = obtain "
              f"{cost['obtain']:.2f} + flow {cost['flow_cost']:.2f} + face "
              f"{cost['face_imposition']:.2f} + burden "
              f"{cost['cumulative_burden']:.2f}")
    bal = stance.get("balance")
    if isinstance(bal, (int, float)):
        ba = stance.get("balance_after")
        extra = (f" -> {ba:.2f} (spent {stance.get('spent', 0):.2f})"
                 if ba is not None else "")
        print(f"   social_capital : {bal:.2f}{extra}")
    print(f"   DECISION       : {stance['decision'].upper()}")
    print(f"   why            : {stance['why']}")


# ===========================================================================
# CASE 1 — RESOLVABLE + ASK (material, affordable, audience IS the source).
# ===========================================================================

def case_ask(s, cw):
    print("=" * 72)
    print("CASE 1 — RESOLVABLE + ASK: a material gap whose route is the current")
    print("interlocutor (audience IS the source), value > social cost, budget")
    print("affords it -> SURFACE the question.")
    print("=" * 72)
    # Mary is in play (introduced by a prior assertion). A where-question about
    # Mary, unresolved -> transactive route to Mary (a discourse entity); the
    # current audience is that source; material; fresh budget -> ASK.
    cw.discourse.update_from_frame({"event": "be", "agent": "Mary"})
    query = _q(event="live", queried="location", agent="Mary")
    stance = epa.decide_and_record(
        s, query, turn=1, discourse_store=cw.discourse,
        interlocutor=cw.interlocutor)
    reply = epa.reply_for_stance(stance, query, "en")
    _print_stance("where does Mary live? (no fact)", stance)
    print(f"   AGENT          : {reply!r}")
    return stance


# ===========================================================================
# CASE 2 — RESOLVABLE + BANK via a REFERENCE, resolved OFF-PATH (no question).
# ===========================================================================

def case_bank_reference(s, cw):
    print()
    print("=" * 72)
    print("CASE 2 — RESOLVABLE + BANK (reference): a word-meaning gap a REFERENCE")
    print("covers -> bank (don't burden the audience), then resolve_banked_gaps")
    print("via the reference OFF-PATH -> a later turn knows it WITHOUT a question.")
    print("=" * 72)
    # A "what does 'gavagai' mean?" gap: the reference (dictionary/Wiktionary)
    # covers it (FOF positive), but the source is NOT the present audience -> the
    # cost-benefit BANKS it (resolve off the social path).
    query = _q(event="mean", queried="patient", patient="gavagai")
    stance = epa.decide_and_record(
        s, query, turn=2, discourse_store=cw.discourse,
        interlocutor=cw.interlocutor)
    reply = epa.reply_for_stance(stance, query, "en")
    _print_stance("what does 'gavagai' mean? (a reference covers it)", stance)
    print(f"   AGENT          : {reply!r}")
    print(f"   PendingGap     : {stance.get('pending_gap')} (banked off-path)")

    # ---- resolve the banked gap OFF-PATH via the reference ----------------
    # A world-adapter-supplied reference lookup (here a stub standing in for
    # dictionary_lexicon / wiktionary_reference) — the only thing that supplies
    # the answer; nothing is faked.
    def reference_lookup(store, key):
        table = {"gavagai": "rabbit"}   # the off-path reference store
        return table.get(key)

    print()
    print("   --- off the social path: resolve_banked_gaps via the reference ---")
    traces = epa.resolve_banked_gaps(
        s, discourse_store=cw.discourse, interlocutor=cw.interlocutor,
        reference_lookup=reference_lookup)
    for t in traces:
        print(f"     {t['how']}")
    resolved = [t for t in traces if t.get("resolved")]
    # The resolved gap is now a grounded KnownFact -> a later turn can answer it
    # with NO question to the audience.
    facts = [s.node(f)["attrs"] for f in s.nodes("KnownFact")
             if s.node(f)["attrs"].get("origin") == "banked_resolution"]
    print(f"   grounded now   : {facts}")
    print("   -> the banked gap was resolved off-path; the audience was NEVER")
    print("      interrupted with a question.")
    return stance, resolved, facts


# ===========================================================================
# CASE 3 — DROP (immaterial to the exchange).
# ===========================================================================

def case_drop(s, cw):
    print()
    print("=" * 72)
    print("CASE 3 — DROP: a resolvable gap NOT relevant to the current exchange")
    print("(immaterial) -> no question, the conversation proceeds.")
    print("=" * 72)
    # A gap about an entity NOT in play (Pluto's diameter), explicitly immaterial
    # to the exchange. A route may exist (interlocutor), but materiality fails
    # -> DROP (Gricean relevance), never surfaced.
    query = _q(event="have", queried="patient", agent="Pluto",
               patient="?WHAT")
    query["_immaterial"] = True
    stance = epa.decide_and_record(
        s, query, turn=3, discourse_store=cw.discourse,
        interlocutor=cw.interlocutor)
    reply = epa.reply_for_stance(stance, query, "en")
    _print_stance("(aside) what is Pluto's diameter? (immaterial here)", stance)
    print(f"   AGENT          : {reply!r}  (proceeds; no question surfaced)")
    return stance


# ===========================================================================
# CASE 4 — SOCIAL-CAPITAL DEPLETION (the headline result): a material,
# route-having question is BANKED when capital is low; resumes after regen.
# ===========================================================================

def case_depletion(s):
    print()
    print("=" * 72)
    print("CASE 4 — SOCIAL-CAPITAL DEPLETION (the KEY demo): after several")
    print("surfaced asks, a further MATERIAL + RESOLVABLE gap is BANKED instead")
    print("of asked — the budget + cumulative burden make the ask too costly.")
    print("Then, after the budget regenerates over quiet turns, asking resumes.")
    print("Asking is COST-MANAGED, not just route-driven.")
    print("=" * 72)
    # Fresh substrate + discourse so the budget starts full and we control it.
    from domains.reference_resolution import DiscourseStore

    class _W:
        def __init__(self, s):
            self.s = s
            self._concept_nodes = {}

        def _get_or_create_concept(self, name):
            cid = self._concept_nodes.get(name)
            if cid is None:
                cid = self.s.add_node("Concept", {"name": name})
                self._concept_nodes[name] = cid
            return cid

    w = _W(s)
    store = DiscourseStore(s, w)
    # Reset the social_capital budget to FULL for a clean depletion demo (the
    # earlier cases on this shared substrate spent some). Remove + recreate.
    for nid in list(s.nodes("SocialCapital")):
        try:
            s.remove_node(nid)
        except Exception:
            pass
    epa._get_or_create_social_capital(s)
    interlocutor = "user"

    # A run of material, interlocutor-routed gaps (each about a different entity
    # in play). Each turn: tick the budget (regen), then decide.
    entities = ["Alice", "Bob", "Carol", "Dora", "Erin"]
    print(f"  weights: ask_cost(face)={epa.SC_ASK_COST} interlocutor_obtain="
          f"{epa.ROUTE_COST['interlocutor']} flow_on_topic="
          f"{epa.MATERIAL_VALUE and 0.05} regen/turn={epa.SC_REGEN_PER_TURN} "
          f"burden/recent={epa.BURDEN_PER_RECENT}  (HEURISTIC, calibratable)")
    print(f"  material value={epa.MATERIAL_VALUE}")
    print()
    decisions = []
    for i, ent in enumerate(entities):
        epa.tick_social_capital(s)
        store.update_from_frame({"event": "be", "agent": ent})
        query = _q(event="live", queried="location", agent=ent)
        snap_before = epa.social_capital_snapshot(s)
        stance = epa.decide_and_record(
            s, query, turn=i + 1, discourse_store=store,
            interlocutor=interlocutor)
        snap_after = epa.social_capital_snapshot(s)
        decisions.append(stance["decision"])
        print(f"  turn {i+1}: 'where does {ent} live?'  "
              f"balance {snap_before['balance']:.2f} "
              f"(recent_asks {snap_before['recent_asks']}) "
              f"cost {stance['cost']['total']:.2f} value {stance['value']:.2f}"
              f"  -> {stance['decision'].upper()}"
              f"  balance_now {snap_after['balance']:.2f}")
        print(f"          {stance['why']}")

    asked_then_banked = ("ask" in decisions and "bank" in decisions
                         and decisions.index("bank") > decisions.index("ask"))
    print()
    print(f"  -> decisions: {decisions}")
    print(f"  -> a material, route-having question is BANKED once capital is "
          f"low: {'YES' if asked_then_banked else 'NO'}")

    # Now several QUIET turns (no asks) -> the budget regenerates + the burden
    # cools. Then a fresh material gap ASKS again.
    print()
    print("  --- quiet turns (no asks): budget regenerates, burden cools ---")
    for q in range(4):
        snap = epa.tick_social_capital(s)
        print(f"    quiet turn: balance {snap['balance']:.2f} "
              f"recent_asks {snap['recent_asks']}")
    store.update_from_frame({"event": "be", "agent": "Frank"})
    query = _q(event="live", queried="location", agent="Frank")
    stance = epa.decide_and_record(
        s, query, turn=99, discourse_store=store, interlocutor=interlocutor)
    print(f"  resume: 'where does Frank live?'  balance "
          f"{stance['balance']:.2f} cost {stance['cost']['total']:.2f} "
          f"value {stance['value']:.2f}  -> {stance['decision'].upper()}")
    resumed = stance["decision"] == "ask"
    print(f"  -> asking RESUMES after the budget regenerates: "
          f"{'YES' if resumed else 'NO'}")
    return decisions, asked_then_banked, resumed


# ===========================================================================
# CASE 5 — INADMISSIBLE (no route, no shape) -> "I don't know".
# ===========================================================================

def case_inadmissible(s, cw):
    print()
    print("=" * 72)
    print("CASE 5 — INADMISSIBLE: no fact, no chain, no shape, NO route ->")
    print("the categorical 'I don't know'. END-TO-END through ConversationWorld.")
    print("=" * 72)
    # A bare "Why?" queries the cause slot with NO bound entity: no shape, no
    # entity in play to route to, the interlocutor is not a generic source for a
    # contentless query, a cause question is not a lookupable class -> NO route.
    r = cw.turn("Why?", "en")
    rec = cw.transcript[-1]
    print(f"   USER : Why?")
    print(f"   AGENT: {r!r}")
    print(f"   band           : {rec.get('band')}")
    print(f"   knowledge op   : {rec['knowledge_op']}")
    print("   -> the categorical no: 'I don't know' fires when there is no shape")
    print("      AND no route.")
    return rec


def main(argv):
    s = _native.Substrate()
    print("=" * 72)
    print("Setup: train comprehension (teacher ON), then converse (teacher OFF).")
    print("=" * 72)
    world = LanguageWorld(s, training_bank(), teacher_stub)
    summ = LanguageWorld.summary(world.run())
    print(f"  comprehension trained: {summ['matched']}/{summ['tasks']} matched")
    world.teacher_disabled = True
    cw = ConversationWorld(world, interlocutor="user")
    print(f"  epistemic_access weights (HEURISTIC, calibratable, NOT ground "
          f"truth):")
    print(f"    social_capital: initial={epa.SC_INITIAL} ask_cost(face)="
          f"{epa.SC_ASK_COST} regen/turn={epa.SC_REGEN_PER_TURN}")
    print(f"    burden/recent={epa.BURDEN_PER_RECENT}  route_cost={epa.ROUTE_COST}")
    print(f"    material_value={epa.MATERIAL_VALUE} immaterial_value="
          f"{epa.IMMATERIAL_VALUE}")
    print()

    r1 = case_ask(s, cw)
    r2, r2_resolved, r2_facts = case_bank_reference(s, cw)
    r3 = case_drop(s, cw)
    decisions, asked_then_banked, resumed = case_depletion(s)
    r5 = case_inadmissible(s, cw)

    # ----- graph-resident inspection --------------------------------------
    print()
    print("=" * 72)
    print("Epistemic access is graph-resident: SocialCapital / PendingGap /")
    print("EpistemicAccessStance nodes")
    print("=" * 72)
    sc = epa.social_capital_snapshot(s)
    print(f"  SocialCapital: balance={sc['balance']:.2f} "
          f"recent_asks={sc['recent_asks']} turn={sc['turn']}")
    pend = s.nodes("PendingGap")
    print(f"  {len(pend)} PendingGap node(s) banked:")
    for p in pend:
        a = s.node(p)["attrs"]
        print(f"    PendingGap {p}: queried={a.get('queried_slot')!r} "
              f"route={a.get('route_type')}->{a.get('route_source')} "
              f"resolved={a.get('resolved')} answer={a.get('answer')!r}")
    stances = s.nodes("EpistemicAccessStance")
    print(f"  {len(stances)} EpistemicAccessStance trace node(s) recorded.")

    # ----- results / checks -----------------------------------------------
    print()
    print("=" * 72)
    print("RESULTS")
    print("=" * 72)
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}  {detail}")

    chk("CASE 1 ASK: material + audience-is-source + affordable -> ask",
        r1["band"] == "RESOLVABLE_VIA_ROUTE" and r1["decision"] == "ask"
        and r1["route"]["route_type"] == "interlocutor")
    chk("CASE 2 BANK(reference): word gap banked off the social path",
        r2["band"] == "RESOLVABLE_VIA_ROUTE" and r2["decision"] == "bank"
        and r2["route"]["route_type"] == "reference")
    chk("CASE 2 resolved OFF-PATH via the reference (no question asked)",
        len(r2_resolved) >= 1 and len(r2_facts) >= 1,
        f"-> grounded {r2_facts}")
    chk("CASE 3 DROP: immaterial gap dropped (not surfaced)",
        r3["decision"] == "drop")
    chk("CASE 4 DEPLETION: a material route-having gap is BANKED when capital "
        "is low (asked earlier, banked later)", asked_then_banked,
        f"-> {decisions}")
    chk("CASE 4 RESUME: asking resumes after the budget regenerates", resumed)
    chk("CASE 5 INADMISSIBLE: no route, no shape -> 'I don't know'",
        r5.get("band") == "INADMISSIBLE"
        and "don't know" in r5["reply"].lower())

    print()
    print("  KEY RESULT: a MATERIAL, route-having question gets BANKED (not")
    print("  asked) when social capital is low -> the agent is a good")
    print("  conversational citizen, not a constant-questioner. The ask/bank")
    print("  decision is a SOCIAL cost-benefit, not just whether a source exists.")
    print()
    print("  HONEST: the VERIFIED-ACCESS half (FOF / transactive / seek-control)")
    print("  is the route-finder; the SOCIAL-COST half (social_capital / flow /")
    print("  face / cumulative burden / materiality / solved_class) is standard-")
    print("  pragmatics SCAFFOLDING with the HEURISTIC weights printed above —")
    print("  calibratable, not ground truth. A banked gap only resolves if a")
    print("  real route (the reference here) supplies it; nothing is faked.")
    print()
    print(f"EPISTEMIC ACCESS: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
