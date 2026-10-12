"""Equilibrium pack 0.3.0 (stream T3b): Rule JSON + codebook DATA for the
window / scope / traits / quanta / competence / episode manifests.

BUILD-TIME ONLY, imported by scripts/build_equilibrium_seed_pack.py. This module
only ASSEMBLES Rule JSON and codebook rows (CLAUDE.md "_compose_*/builder scripts
are legal because they assemble Rule JSON"); every decision is a seeded rule that
runs in Rust. Codebook rows are minted through `domains.teach` by the builder.

Design: docs/research/psychology_affect/EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md

SHAPES, not numbers: every comparison below is relational between two graph
quantities (two turn positions, two evidence-set sizes, two actors' turn counts)
or presence/absence. The single literal set-size is the singleton cardinality
used to tell "one act" from "a repeated act" (design §6.2), written as
|{pick(E)}| so it reads as the set shape it is.

Strata (design §6, stratified negation): rules that read ABSENCE run in a later
stratum than the facts they negate over. A stratum's rules carry the match edge
["agent", "eq_stratum_<k>", "st"]; the adapter opens stratum k (adds that edge)
only after stratum k-1 has reached its fixpoint.
  S0 (always)  ingest-derived structure + msg cue layer
  S1           quanta evidence, interaction shapes, episode roots
  S2           counter-evidence, corroboration / contest, episode growth
  S3           claim grounding, composites, episode facets + generative
  S4           match shapes (quanta, facets), composite evidence
  S5           composite match
"""
from __future__ import annotations

# ---- Term-JSON helpers -----------------------------------------------------
def V(n): return {"type": "Var", "name": n}
def _n(x): return V(x) if isinstance(x, str) else x
def A(n, k): return {"type": "Attr", "node": _n(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Nb(n, et): return {"type": "Neighbours", "node": _n(n), "edge_type": et}
def InNb(n, et): return {"type": "InNeighbours", "node": _n(n), "edge_type": et}
def Count(src): return {"type": "Count", "source": src}
def Ex(src, var, pred=None): return {"type": "Exists", "source": src, "var_name": var,
                                     "predicate": pred if pred is not None else L(True)}
def ABN(n, name): return {"type": "AttrByName", "node": _n(n), "name": name}
def In(member, container): return {"type": "In", "member": member, "container": container}
def Diff(a, b): return {"type": "Difference", "a": a, "b": b}
def If(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Same(a, b): return Eq(V(a), V(b))
def T(t): return {"__term__": t}
def singleton(src):
    """|{pick(src)}| -- the cardinality of one element of the set (design §6.2)."""
    return Count({"type": "SetT", "items": [{"type": "Pick", "source": src}]})


def lab(label, value=True):
    """Attr key the msg layer writes on a Message when `label` fired with `value`."""
    return f"eqlab:{label}" if value is True else f"eqlab:{label}={value}"


def has(m, key):
    return Eq(A(m, key), L(True))


def rule(name, match, where, effects):
    return {"name": name, "batch": True, "match": match, "where": where, "effects": effects}


STRATA = 5
def ST(k): return ["agent", f"eq_stratum_{k}", "st"]
WIN = ["agent", "eq_window", "w"]
TURN = ["w", "eq_has_turn", "m"]
AUTH = ["m", "eq_authored_by", "a"]
POS = "eq_turn_pos"
REF = "actor_ref"


def enabled(label_term):
    """LabelStatus gate IN the graph (design §7.2): nothing is minted for a
    label whose seeded status is `disabled`."""
    return Not(Ex(Nb("agent", "eq_has_label_status"), "ls",
                  And(Eq(A("ls", "label"), label_term), Eq(A("ls", "status"), L("disabled")))))


def mint(q, owner, actor_ref, trait, pole, target, name, composite=False):
    key = {"q_actor": T(actor_ref), "q_trait": T(trait), "q_pole": T(pole), "q_target": T(target)}
    if composite:
        key["q_composite"] = True
    return [["add_node_if_absent", q, "EqQuantum", key],
            ["add_edge", owner, "eq_has_quantum", q],
            ["set_attr", q, f"eqrule:{name}", True]]


def prov(var, name):
    return ["set_attr", var, f"eqrule:{name}", True]


def turns_of(actor):
    return Count(InNb(actor, "eq_authored_by"))


# ---- scope / coherence codebook (closed-class, LEXICAL by design §5.4) ------
NEGATORS = ("not", "no", "never", "nobody", "nothing", "neither", "nor", "without", "none",
            "cannot", "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
            "won't", "wouldn't", "can't", "couldn't", "shouldn't", "hasn't", "haven't",
            "hadn't", "ain't", "mustn't")
HEDGES = ("maybe", "perhaps", "possibly", "probably", "might", "may", "could", "seems",
          "seem", "apparently", "arguably", "presumably", "somewhat", "guess", "suppose",
          "likely", "kinda", "sorta")
BOUNDARIES = ("but", "however", "although", "though", "yet", "whereas", "nevertheless",
              "nonetheless", "except")
# DISC_CONTRAST forms of seeds/coherence_relations.json (that seed is not loadable
# through load_seed_manifest: "seed node missing local_id"), plus "actually".
CONTRAST_MARKERS = ("however", "but", "yet", "although", "nevertheless", "nonetheless",
                    "whereas", "actually")
SCOPE_ITEMS = ([("EqScopeOp", {"op": "neg", "form": f}) for f in NEGATORS]
               + [("EqScopeOp", {"op": "hedge", "form": f}) for f in HEDGES]
               + [("EqScopeBoundary", {"form": f}) for f in BOUNDARIES]
               + [("EqCohMarker", {"rel": "contrast", "form": f}) for f in CONTRAST_MARKERS])
SCOPE_EDGE = {"EqScopeOp": "eq_has_scope_op", "EqScopeBoundary": "eq_has_scope_boundary",
              "EqCohMarker": "eq_has_coh_marker"}


def in_scope(op):
    """Head token `t` of message `m` is in the scope of an `op` operator: an
    operator token earlier in the same clause with no clause-boundary word
    between them (positions compared relationally; clause index from the
    tokeniser's sentence punctuation)."""
    def same_clause(x):
        return Eq(A(x, "eq_clause"), A("t", "eq_clause"))
    return Ex(Nb("m", "eq_has_token"), "o", And(
        same_clause("o"), Lt(A("o", "eq_pos"), A("t", "eq_pos")),
        Ex(Nb("agent", "eq_has_scope_op"), "s",
           And(Eq(A("s", "op"), L(op)), Eq(A("s", "form"), A("o", "form")))),
        Not(Ex(Nb("m", "eq_has_token"), "k", And(
            same_clause("k"), Lt(A("o", "eq_pos"), A("k", "eq_pos")),
            Lt(A("k", "eq_pos"), A("t", "eq_pos")),
            Ex(Nb("agent", "eq_has_scope_boundary"), "bd", Eq(A("bd", "form"), A("k", "form")))))))
    )


def msg_rule(name, match, conds, value=True):
    """A msg-layer label rule: mint-once `eqfire:<name>` + the label-level
    `eqlab:` attr the quanta layer joins on."""
    label = name[len("eq."):].rsplit(".", 1)[0]
    fire = f"eqfire:{name}"
    return {"name": name, "batch": True, "match": match,
            "where": And(Eq(A("m", fire), L(None)), *conds),
            "effects": [["set_attr", "m", fire, value], ["set_attr", "m", lab(label, value), True]]}


RECV = ["agent", "received", "m"]


def scope_label_rules(label, cue_set):
    """Negation/hedge-aware label decision over cue HITS (design §5.2). A hit is
    the head token of a matched cue, linked by `m -eq_hit_<cue_set>-> t` (so these
    rules enumerate hits only, not every token)."""
    match = [RECV, ["m", f"eq_hit_{cue_set}", "t"]]
    return [
        msg_rule(f"eq.msg.{label}.affirmed", match, [Not(in_scope("neg"))]),
        msg_rule(f"eq.msg.{label}_negated.neg_scope", match, [in_scope("neg")]),
        msg_rule(f"eq.msg.{label}_hedged.hedge_scope", match,
                 [Not(in_scope("neg")), in_scope("hedge")]),
    ]


MSG_STRUCT_RULES = [
    # any hedge operator in the turn (evidence for epistemic.hedging)
    msg_rule("eq.msg.hedge.scope_op",
             [RECV, ["agent", "eq_has_scope_op", "s"], ["m", "eq_has_token", "t"]],
             [Eq(A("s", "op"), L("hedge")), Eq(A("s", "form"), A("t", "form"))]),
    # a response that OPENS with a contrast connective (reply-pair coherence, design §5.3)
    msg_rule("eq.msg.reply_contrast.leading_marker",
             [RECV, ["m", "eq_responds_to", "p"], ["m", "eq_has_token", "t"]],
             [Not(Ex(Nb("m", "eq_has_token"), "k", Lt(A("k", "eq_pos"), A("t", "eq_pos")))),
              Ex(Nb("agent", "eq_has_coh_marker"), "c",
                 And(Eq(A("c", "rel"), L("contrast")), Eq(A("c", "form"), A("t", "form"))))]),
]

# ---- window (S0): who responds to whom -------------------------------------
WINDOW_RULES = [
    # explicit reply to another actor's turn
    rule("eq.win.responds_to.reply",
         [WIN, TURN, ["m", "eq_reply_to", "p"], AUTH, ["p", "eq_authored_by", "b"]],
         Not(Same("a", "b")),
         [["add_edge", "m", "eq_responds_to", "p"], ["add_edge", "m", "eq_addresses", "b"]]),
    # meetings carry no reply edges: an un-replied turn responds to the previous
    # turn when another actor spoke it (turn-taking adjacency, design §8.3)
    rule("eq.win.responds_to.adjacent",
         [WIN, TURN, ["p", "eq_turn_next", "m"], AUTH, ["p", "eq_authored_by", "b"]],
         And(Eq(A("w", "eq_kind"), L("meeting")), Not(Ex(Nb("m", "eq_reply_to"), "x")),
             Not(Same("a", "b"))),
         [["add_edge", "m", "eq_responds_to", "p"], ["add_edge", "m", "eq_addresses", "b"]]),
]
STRATUM_ITEMS = [("EqStratum", {"eq_stratum": k, "eq_open_edge": f"eq_stratum_{k}"})
                 for k in range(1, STRATA + 1)]

# ---- trait vocabulary v0.3.0 (open; design §8.1) -----------------------------
# (trait, poles, targetable, note). Structural traits have no EqTraitCue rows:
# their evidence is a relational shape rule below.
TRAITS = [
    ("competence.claimed", "+", False, "credential frame / experience or status assertion"),
    ("competence.demonstrated", "+", False, "code, link, citation or technical grounding in own turns"),
    ("competence.demonstrated.code", "+", False, "code span in own turns"),
    ("competence.demonstrated.citation", "+", False, "link or citation in own turns"),
    ("competence.demonstrated.technical", "+", False, "technical vocabulary (lemma-matched)"),
    ("competence.acknowledged", "+", True, "another actor concedes / defers to this actor"),
    ("competence.corroborated", "+", False, "claim, then another actor's later concession/deference to the claimant"),
    ("competence.contested", "+", True, "a claim later met by another actor's contrast reply carrying grounding"),
    ("competence.claim_grounding", "+-", False, "claimed AND (demonstrated|acknowledged|corroborated); - is weak"),
    ("epistemic.citation", "+", False, "citation or link"),
    ("epistemic.hedging", "+", False, "hedge operator in turn; NOT a competence input"),
    ("epistemic.assertion_strength", "+", False, "booster formulae"),
    ("epistemic.question_demand", "+", True, "question replying to a turn that already carried evidence"),
    ("stance.concession", "+-", True, "concession formula; '-' = negated concession"),
    ("stance.deescalation", "+", True, "apology / facilitation / reassurance formulae"),
    ("stance.hostility", "+", True, "cue displayed in window, not a hostile person"),
    ("status.claim", "+", False, "status / rank / tenure assertion (status != expertise)"),
    ("status.dismissal", "+", True, "dismissal of another's standing"),
    ("deference.to", "+", True, "deference formulae"),
    ("interaction.floor", "+", False, "the unique actor with strictly the most turns"),
    ("interaction.run", "+", False, "consecutive turns by the same actor"),
    ("interaction.responsiveness", "-", True, "question to the actor unanswered though the actor posted later"),
    ("interaction.withdrawal", "+", False, "disengagement formula; later turns by the actor are counter-evidence"),
    ("tribal.outgroup_reference", "+", False, "address + collective noun construction; no identity lexicon"),
    ("procedural.appeal", "+", False, "procedure / agenda formulae"),
]
PATTERNS = ["pattern.sealioning", "pattern.selective_non_response", "pattern.goalpost_shifting",
            "pattern.jaqing", "pattern.concern_trolling", "pattern.darvo", "pattern.motte_and_bailey"]
_TARGETABLE = {t: tg for t, _p, tg, _n in TRAITS}

SM = "msg.substantive_markers"
# (trait, pole, label key, role, owner)
TRAIT_CUES = [
    ("competence.claimed", "+", lab("msg.credential"), "evidence", "author"),
    ("competence.claimed", "+", lab("msg.status_claim"), "evidence", "author"),
    ("competence.claimed", "+", lab("msg.credential_hedged"), "hedged", "author"),
    ("competence.claimed", "+", lab("msg.status_claim_hedged"), "hedged", "author"),
    ("competence.claimed", "+", lab("msg.credential_negated"), "counter", "author"),
    ("competence.claimed", "+", lab("msg.status_claim_negated"), "counter", "author"),
    ("status.claim", "+", lab("msg.status_claim"), "evidence", "author"),
    ("status.claim", "+", lab("msg.status_claim_hedged"), "hedged", "author"),
    ("status.claim", "+", lab("msg.status_claim_negated"), "counter", "author"),
    *[("competence.demonstrated", "+", k, "evidence", "author") for k in (
        lab(SM, "code"), lab(SM, "link"), lab(SM, "citation"), lab("msg.domain", "technical"))],
    ("competence.demonstrated.code", "+", lab(SM, "code"), "evidence", "author"),
    ("competence.demonstrated.citation", "+", lab(SM, "link"), "evidence", "author"),
    ("competence.demonstrated.citation", "+", lab(SM, "citation"), "evidence", "author"),
    ("competence.demonstrated.technical", "+", lab("msg.domain", "technical"), "evidence", "author"),
    ("competence.acknowledged", "+", lab("msg.concession"), "evidence", "addressee"),
    ("competence.acknowledged", "+", lab("msg.deference"), "evidence", "addressee"),
    ("epistemic.citation", "+", lab(SM, "citation"), "evidence", "author"),
    ("epistemic.citation", "+", lab(SM, "link"), "evidence", "author"),
    ("epistemic.hedging", "+", lab("msg.hedge"), "evidence", "author"),
    ("epistemic.assertion_strength", "+", lab("msg.booster"), "evidence", "author"),
    ("epistemic.assertion_strength", "+", lab("msg.booster_hedged"), "hedged", "author"),
    ("epistemic.assertion_strength", "+", lab("msg.booster_negated"), "counter", "author"),
    ("stance.concession", "+", lab("msg.concession"), "evidence", "author"),
    ("stance.concession", "+", lab("msg.concession_hedged"), "hedged", "author"),
    ("stance.concession", "+", lab("msg.concession_negated"), "counter", "author"),
    ("stance.concession", "-", lab("msg.concession_negated"), "evidence", "author"),
    ("stance.concession", "-", lab("msg.concession"), "counter", "author"),
    ("stance.deescalation", "+", lab("msg.deescalation"), "evidence", "author"),
    ("stance.deescalation", "+", lab("msg.deescalation_hedged"), "hedged", "author"),
    ("stance.deescalation", "+", lab("msg.deescalation_negated"), "counter", "author"),
    ("stance.hostility", "+", lab("msg.hostility"), "evidence", "author"),
    ("stance.hostility", "+", lab("msg.hostility_hedged"), "hedged", "author"),
    ("stance.hostility", "+", lab("msg.hostility_negated"), "counter", "author"),
    ("status.dismissal", "+", lab("msg.dismissal"), "evidence", "author"),
    ("deference.to", "+", lab("msg.deference"), "evidence", "author"),
    ("deference.to", "+", lab("msg.deference_hedged"), "hedged", "author"),
    ("deference.to", "+", lab("msg.deference_negated"), "counter", "author"),
    ("interaction.withdrawal", "+", lab("msg.withdrawal"), "evidence", "author"),
    ("interaction.withdrawal", "+", lab("msg.withdrawal_negated"), "counter", "author"),
    ("tribal.outgroup_reference", "+", lab("msg.tribal"), "evidence", "author"),
    ("procedural.appeal", "+", lab("msg.procedural"), "evidence", "author"),
]


def trait_items():
    items = [("EqTrait", {"trait": t, "poles": p, "targetable": tg, "note": note})
             for t, p, tg, note in TRAITS]
    items += [("EqTraitCue", {"trait": t, "pole": pole, "lab_key": key, "role": role,
                              "owner": owner, "targetable": _TARGETABLE[t]})
              for t, pole, key, role, owner in TRAIT_CUES]
    return items


TRAIT_EDGE = {"EqTrait": "eq_has_trait", "EqTraitCue": "eq_has_trait_cue",
              "EqTraitCompose": "eq_has_trait_compose"}

# ---- quanta rules (generic, data-driven by EqTraitCue rows; design §6.1) -----
CUE = ["agent", "eq_has_trait_cue", "c"]


def _cue_conds(role, owner):
    return [Eq(A("c", "role"), L(role)), Eq(A("c", "owner"), L(owner)),
            Eq(ABN("m", A("c", "lab_key")), L(True)), enabled(A("c", "trait"))]


def _author_evidence(role, edge):
    out = []
    for targeted in (False, True):
        name = f"eq.quanta.{role}.{'targeted' if targeted else 'untargeted'}"
        match = [ST(1), CUE, WIN, TURN, AUTH] + ([["m", "eq_addresses", "b"]] if targeted else [])
        tgt_cond = (Eq(A("c", "targetable"), L(True)) if targeted else
                    Or(Eq(A("c", "targetable"), L(False)), Not(Ex(Nb("m", "eq_addresses"), "x"))))
        target = A("b", REF) if targeted else L("")
        out.append(rule(name, match, And(*_cue_conds(role, "author"), tgt_cond),
                        mint("q", "a", A("a", REF), A("c", "trait"), A("c", "pole"), target, name)
                        + [["add_edge", "q", edge, "m"]]))
    return out


def _counter(targeted):
    name = f"eq.quanta.counter.{'targeted' if targeted else 'untargeted'}"
    match = [ST(2), CUE, WIN, TURN, AUTH, ["a", "eq_has_quantum", "q"]]
    match += [["m", "eq_addresses", "b"]] if targeted else []
    tgt = Eq(A("q", "q_target"), A("b", REF) if targeted else L(""))
    return rule(name, match, And(
        *_cue_conds("counter", "author"), Eq(A("q", "q_trait"), A("c", "trait")),
        Eq(A("q", "q_pole"), A("c", "pole")), tgt, Not(In(V("m"), Nb("q", "eq_evidence")))),
        [["add_edge", "q", "eq_counter", "m"], prov("q", name)])


QUESTION = lab("msg.speech_act", "question")
EVIDENCE_KEYS = (lab(SM, "code"), lab(SM, "link"), lab(SM, "citation"))
GROUNDED_KEYS = EVIDENCE_KEYS + (lab("msg.domain", "technical"),)


def _any(m, keys):
    return Or(*[has(m, k) for k in keys])


def _authored_by(x, actor):
    return Ex(Nb(x, "eq_authored_by"), "y_" + x, Same("y_" + x, actor))


QUANTA_RULES = (
    _author_evidence("evidence", "eq_evidence") + _author_evidence("hedged", "eq_hedged") + [
        # acknowledgement-type cues belong to the ADDRESSEE; target = the acknowledger
        rule("eq.quanta.evidence.addressee", [ST(1), CUE, WIN, TURN, AUTH, ["m", "eq_addresses", "b"]],
             And(*_cue_conds("evidence", "addressee")),
             mint("q", "b", A("b", REF), A("c", "trait"), A("c", "pole"),
                  If(Eq(A("c", "targetable"), L(True)), A("a", REF), L("")),
                  "eq.quanta.evidence.addressee") + [["add_edge", "q", "eq_evidence", "m"]]),
        _counter(False), _counter(True),
        # ---- interaction shapes (design §6.3) ----
        # held the floor: strictly more turns than every other actor (a tie mints nothing)
        rule("eq.quanta.interaction.floor", [ST(1), WIN, ["w", "eq_has_actor", "a"]],
             And(enabled(L("interaction.floor")),
                 Ex(Nb("w", "eq_has_actor"), "o", Not(Same("o", "a"))),
                 Not(Ex(Nb("w", "eq_has_actor"), "o",
                        And(Not(Same("o", "a")), Gte(turns_of("o"), turns_of("a")))))),
             mint("q", "a", A("a", REF), L("interaction.floor"), L("+"), L(""),
                  "eq.quanta.interaction.floor")),
        rule("eq.quanta.interaction.floor.evidence",
             [ST(2), ["a", "eq_has_quantum", "q"], ["m", "eq_authored_by", "a"]],
             Eq(A("q", "q_trait"), L("interaction.floor")),
             [["add_edge", "q", "eq_evidence", "m"], prov("q", "eq.quanta.interaction.floor.evidence")]),
        # counter: the turns of the runner(s)-up (no other non-holder has more turns)
        rule("eq.quanta.interaction.floor.counter",
             [ST(2), WIN, ["w", "eq_has_actor", "a"], ["a", "eq_has_quantum", "q"],
              ["w", "eq_has_actor", "b"], ["m", "eq_authored_by", "b"]],
             And(Eq(A("q", "q_trait"), L("interaction.floor")), Not(Same("a", "b")),
                 Not(Ex(Nb("w", "eq_has_actor"), "o",
                        And(Not(Same("o", "a")), Gt(turns_of("o"), turns_of("b")))))),
             [["add_edge", "q", "eq_counter", "m"], prov("q", "eq.quanta.interaction.floor.counter")]),
        # consecutive turns by the same actor; evidence = a turn whose predecessor is theirs
        rule("eq.quanta.interaction.run",
             [ST(1), WIN, TURN, ["p", "eq_turn_next", "m"], AUTH, ["p", "eq_authored_by", "a"]],
             enabled(L("interaction.run")),
             mint("q", "a", A("a", REF), L("interaction.run"), L("+"), L(""),
                  "eq.quanta.interaction.run") + [["add_edge", "q", "eq_evidence", "m"]]),
        # selective non-response: b's question replying to a's turn, a posted LATER
        # in the window, and no turn by a replies to that question
        rule("eq.quanta.interaction.responsiveness",
             [ST(1), WIN, ["w", "eq_has_turn", "qt"], ["qt", "eq_reply_to", "p"],
              ["p", "eq_authored_by", "a"], ["qt", "eq_authored_by", "b"]],
             And(enabled(L("interaction.responsiveness")), Not(Same("a", "b")), has("qt", QUESTION),
                 Ex(InNb("a", "eq_authored_by"), "x", Gt(A("x", POS), A("qt", POS))),
                 Not(Ex(InNb("qt", "eq_reply_to"), "r", _authored_by("r", "a")))),
             mint("q", "a", A("a", REF), L("interaction.responsiveness"), L("-"), A("b", REF),
                  "eq.quanta.interaction.responsiveness") + [["add_edge", "q", "eq_evidence", "qt"]]),
        # counter: b's other questions to a that a DID answer
        rule("eq.quanta.interaction.responsiveness.counter",
             [ST(2), ["a", "eq_has_quantum", "q"], ["qt", "eq_reply_to", "p"],
              ["p", "eq_authored_by", "a"], ["qt", "eq_authored_by", "b"]],
             And(Eq(A("q", "q_trait"), L("interaction.responsiveness")),
                 Eq(A("q", "q_target"), A("b", REF)), has("qt", QUESTION),
                 Ex(InNb("qt", "eq_reply_to"), "r", _authored_by("r", "a")),
                 Not(In(V("qt"), Nb("q", "eq_evidence")))),
             [["add_edge", "q", "eq_counter", "qt"],
              prov("q", "eq.quanta.interaction.responsiveness.counter")]),
        # withdrawal: a later turn by the same actor is counter-evidence (they came back)
        rule("eq.quanta.interaction.withdrawal.counter",
             [ST(2), ["a", "eq_has_quantum", "q"], ["q", "eq_evidence", "m"],
              ["m2", "eq_authored_by", "a"]],
             And(Eq(A("q", "q_trait"), L("interaction.withdrawal")), Gt(A("m2", POS), A("m", POS)),
                 Not(In(V("m2"), Nb("q", "eq_evidence")))),
             [["add_edge", "q", "eq_counter", "m2"],
              prov("q", "eq.quanta.interaction.withdrawal.counter")]),
        # question replying to a turn that already carried code / link / citation
        rule("eq.quanta.epistemic.question_demand",
             [ST(1), WIN, ["w", "eq_has_turn", "qt"], ["qt", "eq_reply_to", "p"],
              ["qt", "eq_authored_by", "a"], ["p", "eq_authored_by", "b"]],
             And(enabled(L("epistemic.question_demand")), Not(Same("a", "b")), has("qt", QUESTION),
                 _any("p", EVIDENCE_KEYS)),
             mint("q", "a", A("a", REF), L("epistemic.question_demand"), L("+"), A("b", REF),
                  "eq.quanta.epistemic.question_demand") + [["add_edge", "q", "eq_evidence", "qt"]]),
        # ---- composites: conjunction of two component quanta (design §6.1) ----
        rule("eq.quanta.compose",
             [ST(3), ["agent", "eq_has_trait_compose", "k"], WIN, ["w", "eq_has_actor", "a"],
              ["a", "eq_has_quantum", "q1"], ["a", "eq_has_quantum", "q2"]],
             And(enabled(A("k", "trait")), Not(Same("q1", "q2")),
                 Eq(A("q1", "q_trait"), A("k", "req_a_trait")), Eq(A("q1", "q_pole"), A("k", "req_a_pole")),
                 Eq(A("q2", "q_trait"), A("k", "req_b_trait")), Eq(A("q2", "q_pole"), A("k", "req_b_pole")),
                 Or(Eq(A("k", "same_target"), L(False)), Eq(A("q1", "q_target"), A("q2", "q_target")))),
             mint("q", "a", A("a", REF), A("k", "trait"), A("k", "pole"),
                  If(Eq(A("k", "same_target"), L(True)), A("q1", "q_target"), L("")),
                  "eq.quanta.compose", composite=True)
             + [["add_edge", "q", "eq_component", "q1"], ["add_edge", "q", "eq_component", "q2"]]),
        rule("eq.quanta.compose.evidence",
             [ST(4), ["q", "eq_component", "qx"], ["qx", "eq_evidence", "m"]], L(True),
             [["add_edge", "q", "eq_evidence", "m"], prov("q", "eq.quanta.compose.evidence")]),
    ])

# ---- match shapes (S4/S5; design §6.2) -------------------------------------
E, C, H = Nb("q", "eq_evidence"), Nb("q", "eq_counter"), Nb("q", "eq_hedged")
_PLAIN = And(Eq(A("q", "q_composite"), L(None)),
             Not(And(Eq(A("q", "q_trait"), L("competence.claim_grounding")), Eq(A("q", "q_pole"), L("-")))))
_EXACT = And(Gt(Count(E), singleton(E)), Not(Ex(C, "x")), Not(Ex(H, "x")))
_OUTWEIGHS = Gt(Count(E), Count(C))
QMATCH = [ST(4), WIN, ["w", "eq_has_actor", "a"], ["a", "eq_has_quantum", "q"]]


def _set_match(var, name, value):
    return [["set_attr", var, "eq_match", value], prov(var, name)]


COMP = Nb("q", "eq_component")
MATCH_RULES = [
    rule("eq.quanta.match.exact", QMATCH, And(_PLAIN, _EXACT), _set_match("q", "eq.quanta.match.exact", "exact")),
    rule("eq.quanta.match.partial", QMATCH, And(_PLAIN, _OUTWEIGHS, Not(_EXACT)),
         _set_match("q", "eq.quanta.match.partial", "partial")),
    rule("eq.quanta.match.weak", QMATCH, And(_PLAIN, Ex(E, "x"), Not(_OUTWEIGHS)),
         _set_match("q", "eq.quanta.match.weak", "weak")),
    # absence of grounding inside ONE bounded window is weak by construction (design §8.1)
    rule("eq.quanta.match.weak_by_construction", QMATCH,
         And(Eq(A("q", "q_trait"), L("competence.claim_grounding")), Eq(A("q", "q_pole"), L("-"))),
         _set_match("q", "eq.quanta.match.weak_by_construction", "weak")),
    # composite = its weakest component
    rule("eq.quanta.match.composite_exact", [ST(5)] + QMATCH[1:],
         And(Eq(A("q", "q_composite"), L(True)),
             Not(Ex(COMP, "x", Not(Eq(A("x", "eq_match"), L("exact")))))),
         _set_match("q", "eq.quanta.match.composite_exact", "exact")),
    rule("eq.quanta.match.composite_weak", [ST(5)] + QMATCH[1:],
         And(Eq(A("q", "q_composite"), L(True)), Ex(COMP, "x", Eq(A("x", "eq_match"), L("weak")))),
         _set_match("q", "eq.quanta.match.composite_weak", "weak")),
    rule("eq.quanta.match.composite_partial", [ST(5)] + QMATCH[1:],
         And(Eq(A("q", "q_composite"), L(True)),
             Ex(COMP, "x", Not(Eq(A("x", "eq_match"), L("exact")))),
             Not(Ex(COMP, "x", Eq(A("x", "eq_match"), L("weak"))))),
         _set_match("q", "eq.quanta.match.composite_partial", "partial")),
]
QUANTA_RULES += MATCH_RULES

# ---- competence (relational; design §8.2) ----------------------------------
CLAIMED = And(Eq(A("qc", "q_trait"), L("competence.claimed")), Eq(A("qc", "q_pole"), L("+")))
GROUNDING = ("competence.demonstrated", "competence.acknowledged", "competence.corroborated")


def _grounding(var):
    return Or(*[Eq(A(var, "q_trait"), L(t)) for t in GROUNDING])


CLAIM = [["a", "eq_has_quantum", "qc"], ["qc", "eq_evidence", "m1"]]
COMPETENCE_RULES = [
    # claim followed LATER by another actor's concession / deference addressed to the claimant
    rule("eq.competence.corroborated", [ST(2)] + CLAIM + [["m2", "eq_addresses", "a"]],
         And(CLAIMED, enabled(L("competence.corroborated")), Gt(A("m2", POS), A("m1", POS)),
             _any("m2", (lab("msg.concession"), lab("msg.deference")))),
         mint("q", "a", A("a", REF), L("competence.corroborated"), L("+"), L(""),
              "eq.competence.corroborated")
         + [["add_edge", "q", "eq_evidence", "m1"], ["add_edge", "q", "eq_evidence", "m2"]]),
    # claim LATER met by another actor's contrast reply that carries grounding
    rule("eq.competence.contested",
         [ST(2)] + CLAIM + [["m2", "eq_addresses", "a"], ["m2", "eq_authored_by", "b"]],
         And(CLAIMED, enabled(L("competence.contested")), Gt(A("m2", POS), A("m1", POS)),
             has("m2", lab("msg.reply_contrast")), _any("m2", GROUNDED_KEYS)),
         mint("q", "a", A("a", REF), L("competence.contested"), L("+"), A("b", REF),
              "eq.competence.contested")
         + [["add_edge", "q", "eq_evidence", "m1"], ["add_edge", "q", "eq_evidence", "m2"]]),
    # claim_grounding '+': evidence = claim turns + grounding turns
    rule("eq.competence.claim_grounding.grounded_claim", [ST(3)] + CLAIM,
         And(CLAIMED, enabled(L("competence.claim_grounding")),
             Ex(Nb("a", "eq_has_quantum"), "g", _grounding("g"))),
         mint("q", "a", A("a", REF), L("competence.claim_grounding"), L("+"), L(""),
              "eq.competence.claim_grounding.grounded_claim") + [["add_edge", "q", "eq_evidence", "m1"]]),
    rule("eq.competence.claim_grounding.grounding",
         [ST(3), ["a", "eq_has_quantum", "qc"], ["a", "eq_has_quantum", "g"], ["g", "eq_evidence", "m2"]],
         And(CLAIMED, enabled(L("competence.claim_grounding")), _grounding("g")),
         mint("q", "a", A("a", REF), L("competence.claim_grounding"), L("+"), L(""),
              "eq.competence.claim_grounding.grounding") + [["add_edge", "q", "eq_evidence", "m2"]]),
    # claim_grounding '-': claimed and NONE of demonstrated / acknowledged / corroborated
    rule("eq.competence.claim_grounding.ungrounded", [ST(3)] + CLAIM,
         And(CLAIMED, enabled(L("competence.claim_grounding")),
             Not(Ex(Nb("a", "eq_has_quantum"), "g", _grounding("g")))),
         mint("q", "a", A("a", REF), L("competence.claim_grounding"), L("-"), L(""),
              "eq.competence.claim_grounding.ungrounded") + [["add_edge", "q", "eq_evidence", "m1"]]),
]

# ---- episodes + etiology facets (design §8.3) ------------------------------
EPISODE_CUES = (
    [("root", lab(k)) for k in ("msg.reply_contrast", "msg.hostility", "msg.concession_negated",
                                "msg.dismissal")]
    + [("extend", k) for k in (lab("msg.reply_contrast"), lab("msg.hostility"), lab("msg.concession"),
                               lab("msg.concession_negated"), lab("msg.deescalation"),
                               lab("msg.dismissal"), lab("msg.withdrawal"), QUESTION,
                               *EVIDENCE_KEYS, lab("msg.status_claim"), lab("msg.credential"),
                               lab("msg.deference"))]
    + [("resolve", lab(k)) for k in ("msg.concession", "msg.deescalation", "msg.deference")]
    + [("escalate", lab(k)) for k in ("msg.reply_contrast", "msg.hostility", "msg.dismissal")])
FACET_CUES = (
    [("epistemic", k) for k in GROUNDED_KEYS]
    + [("status", lab(k)) for k in ("msg.status_claim", "msg.credential", "msg.dismissal")]
    + [("procedural", lab("msg.procedural")), ("affective", lab("msg.hostility")),
       ("tribal", lab("msg.tribal"))])
FACET_CODES = ("epistemic", "status", "procedural", "affective", "tribal")
EPISODE_KINDS = ("dispute",)


def episode_items():
    return ([("EqEpisodeCue", {"role": r, "lab_key": k}) for r, k in EPISODE_CUES]
            + [("EqFacetCue", {"code": c, "lab_key": k, "status_label": f"facet.{c}"})
               for c, k in FACET_CUES])


EPISODE_EDGE = {"EqEpisodeCue": "eq_has_episode_cue", "EqFacetCue": "eq_has_facet_cue"}


def _cue_role(m, role):
    return Ex(Nb("agent", "eq_has_episode_cue"), "ec_" + m,
              And(Eq(A("ec_" + m, "role"), L(role)), Eq(ABN(m, A("ec_" + m, "lab_key")), L(True))))


MEMBERS = InNb("e", "eq_in_episode")
_LATER_RESOLVE = Ex(MEMBERS, "rm", And(_cue_role("rm", "resolve"), Gt(A("rm", POS), A("r", POS)),
                                       Not(Ex(MEMBERS, "xm", And(_cue_role("xm", "escalate"),
                                                                 Gt(A("xm", POS), A("rm", POS)))))))
_ANY_RESOLVE = Ex(MEMBERS, "rm", And(_cue_role("rm", "resolve"), Gt(A("rm", POS), A("r", POS))))
_LATER_ESCALATE = Ex(MEMBERS, "xm", And(_cue_role("xm", "escalate"), Gt(A("xm", POS), A("r", POS))))
FX_E = Nb("fx", "eq_evidence")
FX_C = Diff(InNb("e", "eq_in_episode"), FX_E)
_FX_EXACT = And(Gt(Count(FX_E), singleton(FX_E)), Not(Ex(FX_C, "x")))
FXMATCH = [ST(4), WIN, ["w", "eq_has_episode", "e"], ["e", "eq_has_facet", "fx"]]
GEN = [ST(3), WIN, ["w", "eq_has_episode", "e"], ["e", "eq_root", "r"]]


def _fx_match(value):
    return [["set_attr", "fx", "eq_match", value], prov("e", f"eq.ep.facet_match.{value}")]


EPISODE_RULES = [
    # root: a turn responding to another actor's turn with a root cue
    rule("eq.ep.root", [ST(1), WIN, TURN, ["m", "eq_responds_to", "p"]],
         And(enabled(L("episode.dispute")), _cue_role("m", "root")),
         [["add_node_if_absent", "e", "EqEpisode", {"ep_root": T(V("p")), "ep_kind": "dispute"}],
          ["set_attr", "e", "ep_root_ref", T(A("p", "eq_ref"))],
          ["add_edge", "w", "eq_has_episode", "e"], ["add_edge", "e", "eq_root", "p"],
          ["add_edge", "p", "eq_in_episode", "e"], ["add_edge", "m", "eq_in_episode", "e"],
          prov("e", "eq.ep.root")]),
    # growth to fixpoint: a cue-carrying turn responding to an episode turn joins it
    rule("eq.ep.extend", [ST(2), ["x", "eq_responds_to", "y"], ["y", "eq_in_episode", "e"]],
         _cue_role("x", "extend"),
         [["add_edge", "x", "eq_in_episode", "e"], prov("e", "eq.ep.extend")]),
    rule("eq.ep.facet",
         [ST(3), ["agent", "eq_has_facet_cue", "f"], WIN, ["w", "eq_has_episode", "e"],
          ["m", "eq_in_episode", "e"]],
         And(Eq(ABN("m", A("f", "lab_key")), L(True)), enabled(A("f", "status_label"))),
         [["add_node_if_absent", "fx", "EqEpFacet", {"fx_ep": T(V("e")), "fx_code": T(A("f", "code"))}],
          ["add_edge", "e", "eq_has_facet", "fx"], ["add_edge", "fx", "eq_evidence", "m"],
          prov("e", "eq.ep.facet")]),
    rule("eq.ep.generative.resolved", GEN, _LATER_RESOLVE,
         [["set_attr", "e", "ep_generative", True], prov("e", "eq.ep.generative.resolved")]),
    rule("eq.ep.generative.escalated", GEN, And(_LATER_ESCALATE, Not(_ANY_RESOLVE)),
         [["set_attr", "e", "ep_generative", False], prov("e", "eq.ep.generative.escalated")]),
    rule("eq.ep.facet_match.exact", FXMATCH, _FX_EXACT, _fx_match("exact")),
    rule("eq.ep.facet_match.partial", FXMATCH, And(Gt(Count(FX_E), Count(FX_C)), Not(_FX_EXACT)),
         _fx_match("partial")),
    rule("eq.ep.facet_match.weak", FXMATCH, Not(Gt(Count(FX_E), Count(FX_C))), _fx_match("weak")),
]

# ---- ingest / derived edge vocabulary (Γ productions) -----------------------
WINDOW_EDGE_TYPES = [
    ("Agent", "eq_window", "EqWindow"), ("EqWindow", "eq_has_actor", "EqActor"),
    ("EqWindow", "eq_has_turn", "Message"), ("Message", "eq_authored_by", "EqActor"),
    ("Message", "eq_reply_to", "Message"), ("Message", "eq_turn_next", "Message"),
    ("Message", "eq_responds_to", "Message"), ("Message", "eq_addresses", "EqActor"),
    ("Agent", "eq_has_stratum", "EqStratum"),
    *[("Agent", f"eq_stratum_{k}", "EqStratum") for k in range(1, STRATA + 1)],
]
SCOPE_EDGE_TYPES = [("Agent", e, t) for t, e in SCOPE_EDGE.items()]
TRAIT_EDGE_TYPES = [("Agent", e, t) for t, e in TRAIT_EDGE.items()]
QUANTA_EDGE_TYPES = [("EqActor", "eq_has_quantum", "EqQuantum"),
                     ("EqQuantum", "eq_evidence", "Message"), ("EqQuantum", "eq_counter", "Message"),
                     ("EqQuantum", "eq_hedged", "Message"), ("EqQuantum", "eq_component", "EqQuantum")]
EPISODE_EDGE_TYPES = [("Agent", e, t) for t, e in EPISODE_EDGE.items()] + [
    ("EqWindow", "eq_has_episode", "EqEpisode"), ("EqEpisode", "eq_root", "Message"),
    ("Message", "eq_in_episode", "EqEpisode"), ("EqEpisode", "eq_has_facet", "EqEpFacet"),
    ("EqEpFacet", "eq_evidence", "Message")]
