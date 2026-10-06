"""Equilibrium pack 0.5.0 (streams T3b + T3c): Rule JSON + codebook DATA for the
window / scope / traits / quanta / competence / episode / climate manifests.

0.5.0 (T3c, conversation tracking): turn ADJACENCY is no longer structure. The
`eq_turn_next` edge and the `eq.win.responds_to.adjacent` rule are gone; every
relational rule consumes `eq_responds_to` (declared here from platform replies,
basis "declared"; tracked inference lands as further producers of the same edge).
New window structure: `eq_thread` (thread id; O2: decided by the tracking cursor) and
`eq_answers` (per-turn answers; same shape as inquiry.answered).

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

import json

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
# 0.4.0: closed-class function words (determiners, pronouns, auxiliaries,
# prepositions, conjunctions, degree adverbs). LEXICAL by design §5.4 like the
# operators above; used only to stop a negated-echo dissent from matching on a
# function word ("not the ...", "isn't it ...").
CLOSED_CLASS = (
    "a", "an", "the", "this", "that", "these", "those", "it", "its", "it's", "i", "i'm", "me",
    "my", "we", "us", "our", "you", "your", "he", "she", "they", "them", "their", "there",
    "here", "what", "which", "who", "how", "why", "when", "where", "be", "is", "are", "was",
    "were", "been", "being", "am", "do", "does", "did", "have", "has", "had", "will", "would",
    "should", "can", "could", "must", "shall", "to", "of", "in", "on", "at", "for", "with",
    "by", "from", "as", "about", "into", "and", "or", "if", "so", "then", "than", "just",
    "really", "very", "quite", "too", "all", "any", "some", "much", "more", "even", "only",
    "sure", "yet", "really", "always", "ever", "one")
SCOPE_ITEMS = ([("EqScopeOp", {"op": "neg", "form": f}) for f in NEGATORS]
               + [("EqScopeOp", {"op": "hedge", "form": f}) for f in HEDGES]
               + [("EqScopeBoundary", {"form": f}) for f in BOUNDARIES]
               + [("EqCohMarker", {"rel": "contrast", "form": f}) for f in CONTRAST_MARKERS]
               + [("EqClosedClass", {"form": f}) for f in dict.fromkeys(CLOSED_CLASS)])
SCOPE_EDGE = {"EqScopeOp": "eq_has_scope_op", "EqScopeBoundary": "eq_has_scope_boundary",
              "EqCohMarker": "eq_has_coh_marker", "EqClosedClass": "eq_has_closed_class"}


def in_scope(op, m="m", t="t", sfx=""):
    """Head token `t` of message `m` is in the scope of an `op` operator: an
    operator token earlier in the same clause with no clause-boundary word
    between them (positions compared relationally; clause index from the
    tokeniser's sentence punctuation). `sfx` renames the inner variables so the
    shape can be used on a second (message, token) pair in the same rule (0.4.0)."""
    o, s, k, bd = (f"{v}{sfx}" for v in ("o", "s", "k", "bd"))

    def same_clause(x):
        return Eq(A(x, "eq_clause"), A(t, "eq_clause"))
    return Ex(Nb(m, "eq_has_token"), o, And(
        same_clause(o), Lt(A(o, "eq_pos"), A(t, "eq_pos")),
        Ex(Nb("agent", "eq_has_scope_op"), s,
           And(Eq(A(s, "op"), L(op)), Eq(A(s, "form"), A(o, "form")))),
        Not(Ex(Nb(m, "eq_has_token"), k, And(
            same_clause(k), Lt(A(o, "eq_pos"), A(k, "eq_pos")),
            Lt(A(k, "eq_pos"), A(t, "eq_pos")),
            Ex(Nb("agent", "eq_has_scope_boundary"), bd, Eq(A(bd, "form"), A(k, "form")))))))
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
    # explicit (platform-declared) reply to another actor's turn: basis "declared".
    # 0.5.0: adjacency is NOT structure -- a meeting turn with no declared reply
    # responds to nothing until a tracking rule (pack >= 0.6) derives the edge.
    rule("eq.win.responds_to.reply",
         [WIN, TURN, ["m", "eq_reply_to", "p"], AUTH, ["p", "eq_authored_by", "b"]],
         Not(Same("a", "b")),
         [["add_edge", "m", "eq_responds_to", "p"], ["add_edge", "m", "eq_addresses", "b"],
          ["set_attr", "m", "eq_basis", "declared"]]),
    # a platform-declared thread id names the thread directly (S0). Every other
    # thread id is decided by the tracking cursor (eq.trk.thread.*, 0.5.0 O2):
    # the earliest parent's thread, else the turn roots its own thread. (O1 ran
    # root / inherit at S1 on the scratch fork: one chain hop per pass, which cost
    # O(turns x chain length) per batch once tracked chains existed.)
    rule("eq.win.thread.platform", [WIN, TURN],
         And(Eq(A("m", "eq_thread"), L(None)), Not(Eq(A("m", "eq_platform_thread"), L(None)))),
         [["set_attr", "m", "eq_thread", T(A("m", "eq_platform_thread"))]]),
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
    ("interaction.floor", "+", False, "the unique actor with strictly the most turns (0.7.0: evidence = the "
     "holder's first turn, counter = each runner-up's first turn, match partial by construction; the "
     "turn shares are interaction.floor_share)"),
    ("interaction.floor_share", "+", False, "0.7.0: the actor's share of the floor -- evidence = every turn "
     "by the actor (monotone, never retracted)"),
    ("interaction.run", "+", False, "consecutive turns by the same actor"),
    ("interaction.responsiveness", "-", True, "question to the actor unanswered though the actor posted later"),
    ("interaction.withdrawal", "+", False, "disengagement formula; later turns by the actor are counter-evidence"),
    ("tribal.outgroup_reference", "+", False, "address + collective noun construction; no identity lexicon"),
    ("procedural.appeal", "+", False, "procedure / agenda formulae"),
]
TRAIT_SINCE = {"interaction.floor_share": "0.7.0"}  # traits added after 0.4.0
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
        # consecutive turns by the same actor; evidence = a turn that CONTINUES the
        # actor's own immediately preceding turn (0.5.0 O2: `eq_continues`, the
        # same-actor continuation edge of equilibrium_tracking -- a run is turn
        # order by definition, so it reads the ordering edge, not responds_to)
        rule("eq.quanta.interaction.run",
             [ST(1), WIN, TURN, ["m", "eq_continues", "p"], AUTH, ["p", "eq_authored_by", "a"]],
             enabled(L("interaction.run")),
             mint("q", "a", A("a", REF), L("interaction.run"), L("+"), L(""),
                  "eq.quanta.interaction.run") + [["add_edge", "q", "eq_evidence", "m"]]),
        # selective non-response: b's question responding to a's turn, a posted LATER
        # in the window, and no turn by a responds to that question
        rule("eq.quanta.interaction.responsiveness",
             [ST(1), WIN, ["w", "eq_has_turn", "qt"], ["qt", "eq_responds_to", "p"],
              ["p", "eq_authored_by", "a"], ["qt", "eq_authored_by", "b"]],
             And(enabled(L("interaction.responsiveness")), Not(Same("a", "b")), has("qt", QUESTION),
                 Ex(InNb("a", "eq_authored_by"), "x", Gt(A("x", POS), A("qt", POS))),
                 Not(Ex(InNb("qt", "eq_responds_to"), "r", _authored_by("r", "a")))),
             mint("q", "a", A("a", REF), L("interaction.responsiveness"), L("-"), A("b", REF),
                  "eq.quanta.interaction.responsiveness") + [["add_edge", "q", "eq_evidence", "qt"]]),
        # counter: b's other questions to a that a DID answer
        rule("eq.quanta.interaction.responsiveness.counter",
             [ST(2), ["a", "eq_has_quantum", "q"], ["qt", "eq_responds_to", "p"],
              ["p", "eq_authored_by", "a"], ["qt", "eq_authored_by", "b"]],
             And(Eq(A("q", "q_trait"), L("interaction.responsiveness")),
                 Eq(A("q", "q_target"), A("b", REF)), has("qt", QUESTION),
                 Ex(InNb("qt", "eq_responds_to"), "r", _authored_by("r", "a")),
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
        # question responding to a turn that already carried code / link / citation
        rule("eq.quanta.epistemic.question_demand",
             [ST(1), WIN, ["w", "eq_has_turn", "qt"], ["qt", "eq_responds_to", "p"],
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
             Not(And(Eq(A("q", "q_trait"), L("competence.claim_grounding")), Eq(A("q", "q_pole"), L("-")))),
             # 0.7.0: the floor's evidence / counter are bounded anchors (first turns), not
             # the shares; its match is set by construction (eq.quanta.match.partial_by_construction)
             Not(Eq(A("q", "q_trait"), L("interaction.floor"))))
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

# ---- space-climate traits (pack 0.4.0; voice / inquiry / response) ----------
# msg layer (S0, positive-only: every negation below is over ingest tokens or a
# seeded codebook, never over a label derived in the same stratum).
ASSERTION = lab("msg.speech_act", "assertion")
DIRECTIVE = lab("msg.speech_act", "directive")
RESP_P = [RECV, ["m", "eq_responds_to", "p"]]


def _claim_turn(p):
    """The turn makes a claim or proposal (assertion / directive); positive, so
    it is safe inside S0 where the speech-act labels are still being derived."""
    return Or(has(p, ASSERTION), has(p, DIRECTIVE))


CLIMATE_MSG_RULES = [
    # dissent is itself a claim-type turn (a contesting QUESTION is inquiry.challenge):
    # explicit disagreement formula replying to another actor's claim
    msg_rule("eq.msg.dissent.disagreement_cue", RESP_P,
             [has("m", lab("msg.disagreement")), _claim_turn("m"), _claim_turn("p")]),
    # reply OPENING with a contrast connective against another actor's claim
    msg_rule("eq.msg.dissent.contrast_claim", RESP_P,
             [has("m", lab("msg.reply_contrast")), _claim_turn("m"), _claim_turn("p")]),
    # negated echo: a negator immediately followed by a content token whose lemma
    # the prior claim carries un-negated ("the cache is cold" / "it isn't cold").
    # Two linear steps (no token x token product): (a) mark the content token
    # right after a negator in a responding turn, (b) look for its lemma in the
    # replied-to claim.
    {"name": "eq.msg.negated_token.neg_op", "batch": True,
     "match": [RECV, ["m", "eq_responds_to", "p"], ["agent", "eq_has_scope_op", "sn"],
               ["m", "eq_has_token", "o"], ["o", "eq_next", "t"]],
     "where": And(Eq(A("sn", "op"), L("neg")), Eq(A("sn", "form"), A("o", "form")),
                  Not(Ex(Nb("agent", "eq_has_closed_class"), "cc", Eq(A("cc", "form"), A("t", "form")))),
                  Not(Ex(Nb("agent", "eq_has_scope_op"), "sx", Eq(A("sx", "form"), A("t", "form"))))),
     "effects": [["add_edge", "m", "eq_neg_next", "t"]]},
    msg_rule("eq.msg.dissent.negated_echo",
             RESP_P + [["m", "eq_neg_next", "t"], ["p", "eq_has_token", "u"]],
             [Eq(A("u", "lemma"), A("t", "lemma")), _claim_turn("m"), _claim_turn("p"),
              Not(in_scope("neg", m="p", t="u", sfx="_p"))]),
    msg_rule("eq.msg.dissent_hedged.hedge_op", [RECV],
             [has("m", lab("msg.dissent")), has("m", lab("msg.hedge"))]),
    # challenge: a question opening with a contrast, or an evidence request, replying to another actor
    msg_rule("eq.msg.challenge.contrast_question", RESP_P,
             [has("m", QUESTION), has("m", lab("msg.reply_contrast"))]),
    msg_rule("eq.msg.challenge.evidence_request", RESP_P, [has("m", lab("msg.evidence_request"))]),
    msg_rule("eq.msg.challenge_hedged.hedge_op", [RECV],
             [has("m", lab("msg.challenge")), has("m", lab("msg.hedge"))]),
]

CLIMATE_TRAITS = [
    ("voice.dissent", "+", True, "disagreement toward another actor's claim: disagreement formula, "
     "reply-leading contrast, or negated echo of the prior claim; target = actor disagreed with"),
    ("voice.error_admission", "+", False, "admission of one's own error (negation-aware formulae)"),
    ("inquiry.challenge", "+", True, "question opening with a contrast, or evidence request, "
     "replying to another actor's turn"),
    ("inquiry.answered", "+", True, "on the ANSWERER: later non-question, non-dismissive, "
     "non-withdrawal reply to another actor's question; evidence = [question, answer]"),
    ("inquiry.unanswered", "+", False, "on the ASKER: question with no inquiry.answered over the "
     "completed window although another actor posted later; counter = the asker's answered questions"),
    ("response.dismissal", "+", True, "dismissal / hostility cue, or status claim without grounding, "
     "replying to a question, dissent or challenge; target = the dismissed actor"),
    ("response.engagement", "+", True, "grounding, concession or follow-up question, without a "
     "dismissive cue, replying to a question, dissent or challenge"),
]
CLIMATE_TRAIT_CUES = [
    ("voice.dissent", "+", lab("msg.dissent"), "evidence", "author"),
    ("voice.dissent", "+", lab("msg.dissent_hedged"), "hedged", "author"),
    ("voice.dissent", "+", lab("msg.disagreement_negated"), "counter", "author"),
    ("voice.error_admission", "+", lab("msg.error_admission"), "evidence", "author"),
    ("voice.error_admission", "+", lab("msg.error_admission_hedged"), "hedged", "author"),
    ("voice.error_admission", "+", lab("msg.error_admission_negated"), "counter", "author"),
    ("inquiry.challenge", "+", lab("msg.challenge"), "evidence", "author"),
    ("inquiry.challenge", "+", lab("msg.challenge_hedged"), "hedged", "author"),
    ("inquiry.challenge", "+", lab("msg.evidence_request_negated"), "counter", "author"),
]
TRAITS += CLIMATE_TRAITS
TRAIT_CUES += CLIMATE_TRAIT_CUES
_TARGETABLE.update({t: tg for t, _p, tg, _n in CLIMATE_TRAITS})
CLIMATE_TRAIT_NAMES = tuple(t for t, *_ in CLIMATE_TRAITS)

# relational reply codebook (EqClimateCue{role, lab_key}); rules read the roles
CLIMATE_CUES = (
    [("stimulus", k) for k in (QUESTION, lab("msg.dissent"), lab("msg.challenge"))]
    + [("dismiss", lab(k)) for k in ("msg.dismissal", "msg.hostility")]
    + [("status", lab("msg.status_claim"))]
    + [("ground", k) for k in GROUNDED_KEYS]
    + [("engage", k) for k in GROUNDED_KEYS + (lab("msg.concession"), QUESTION)]
    + [("nonanswer", k) for k in (QUESTION, lab("msg.withdrawal"))])


def climate_items():
    return [("EqClimateCue", {"role": r, "lab_key": k}) for r, k in CLIMATE_CUES]


CLIMATE_EDGE = {"EqClimateCue": "eq_has_climate_cue"}


def _cc(m, role):
    v = f"cc_{m}_{role}"
    return Ex(Nb("agent", "eq_has_climate_cue"), v,
              And(Eq(A(v, "role"), L(role)), Eq(ABN(m, A(v, "lab_key")), L(True))))


def _dismissive(m):
    return Or(_cc(m, "dismiss"), And(_cc(m, "status"), Not(_cc(m, "ground"))))


REPLY = [WIN, TURN, AUTH, ["m", "eq_responds_to", "p"], ["p", "eq_authored_by", "b"]]


def _reply_mint(trait, name):
    """quantum on the replier `a`, target = the replied-to actor `b`; the reply
    is evidence, the turn replied to is context (read out as evidence, not
    counted by the match shapes: one reply = one act)."""
    return (mint("q", "a", A("a", REF), L(trait), L("+"), A("b", REF), name)
            + [["add_edge", "q", "eq_evidence", "m"], ["add_edge", "q", "eq_context", "p"]])


def _answered(qt):
    v = f"qa_{qt}"
    return Ex(InNb(qt, "eq_context"), v, Eq(A(v, "q_trait"), L("inquiry.answered")))


CLIMATE_RULES = [
    # S1 (reads S0 labels, incl. their absence: S0 is at fixpoint). Conjunct
    # order is cost order only (cheapest / most selective first).
    rule("eq.quanta.response.dismissal", [ST(1)] + REPLY,
         And(_cc("p", "stimulus"), _dismissive("m"), enabled(L("response.dismissal"))),
         _reply_mint("response.dismissal", "eq.quanta.response.dismissal")),
    rule("eq.quanta.response.engagement", [ST(1)] + REPLY,
         And(_cc("p", "stimulus"), _cc("m", "engage"), Not(_dismissive("m")),
             enabled(L("response.engagement"))),
         _reply_mint("response.engagement", "eq.quanta.response.engagement")),
    # 0.5.0 (T3c O2): inquiry.answered CONSUMES the per-turn `eq_answers` edge the
    # tracking cursor writes (declared or tracked responds_to + answer-type turn);
    # the answer shape lives once, in eq.trk.answers (equilibrium_tracking).
    rule("eq.quanta.inquiry.answered",
         [ST(1), WIN, TURN, AUTH, ["m", "eq_answers", "p"], ["p", "eq_authored_by", "b"]],
         enabled(L("inquiry.answered")),
         _reply_mint("inquiry.answered", "eq.quanta.inquiry.answered")),
    # S2 (reads the ABSENCE of S1 inquiry.answered over the completed window).
    # Absence is relative: only once another actor has posted after the question.
    rule("eq.quanta.inquiry.unanswered",
         [ST(2), WIN, ["w", "eq_has_turn", "qt"], ["qt", "eq_authored_by", "b"]],
         And(has("qt", QUESTION), Not(_answered("qt")), enabled(L("inquiry.unanswered")),
             Ex(Nb("w", "eq_has_turn"), "x", And(Gt(A("x", POS), A("qt", POS)),
                                                Not(_authored_by("x", "b"))))),
         mint("q", "b", A("b", REF), L("inquiry.unanswered"), L("+"), L(""),
              "eq.quanta.inquiry.unanswered") + [["add_edge", "q", "eq_evidence", "qt"]]),
    rule("eq.quanta.inquiry.unanswered.counter",
         [ST(2), ["b", "eq_has_quantum", "q"], ["qt", "eq_authored_by", "b"]],
         And(Eq(A("q", "q_trait"), L("inquiry.unanswered")), has("qt", QUESTION), _answered("qt"),
             Not(In(V("qt"), Nb("q", "eq_evidence")))),
         [["add_edge", "q", "eq_counter", "qt"], prov("q", "eq.quanta.inquiry.unanswered.counter")]),
]

# ---- ingest / derived edge vocabulary (Γ productions) -----------------------
WINDOW_EDGE_TYPES = [
    ("Agent", "eq_window", "EqWindow"), ("EqWindow", "eq_has_actor", "EqActor"),
    ("EqWindow", "eq_has_turn", "Message"), ("Message", "eq_authored_by", "EqActor"),
    ("Message", "eq_reply_to", "Message"), ("Message", "eq_thread_parent", "Message"),
    ("Message", "eq_answers", "Message"),
    ("Message", "eq_responds_to", "Message"), ("Message", "eq_addresses", "EqActor"),
    ("Agent", "eq_has_stratum", "EqStratum"),
    *[("Agent", f"eq_stratum_{k}", "EqStratum") for k in range(1, STRATA + 1)],
]
SCOPE_EDGE_TYPES = [("Agent", e, t) for t, e in SCOPE_EDGE.items()]
TRAIT_EDGE_TYPES = [("Agent", e, t) for t, e in TRAIT_EDGE.items()]
QUANTA_EDGE_TYPES = [("EqActor", "eq_has_quantum", "EqQuantum"),
                     ("EqQuantum", "eq_evidence", "Message"), ("EqQuantum", "eq_counter", "Message"),
                     ("EqQuantum", "eq_hedged", "Message"), ("EqQuantum", "eq_component", "EqQuantum"),
                     ("EqQuantum", "eq_context", "Message")]
CLIMATE_EDGE_TYPES = [("Agent", e, t) for t, e in CLIMATE_EDGE.items()]
EPISODE_EDGE_TYPES = [("Agent", e, t) for t, e in EPISODE_EDGE.items()] + [
    ("EqWindow", "eq_has_episode", "EqEpisode"), ("EqEpisode", "eq_root", "Message"),
    ("Message", "eq_in_episode", "EqEpisode"), ("EqEpisode", "eq_has_facet", "EqEpFacet"),
    ("EqEpFacet", "eq_evidence", "Message")]


# ---- conversation TRACKING (T3c stage O2, pack 0.5.0) -----------------------
# Who responds to whom when the platform declares nothing. A seeded TURN CURSOR
# walks the conversation in turn order on the RETAINED fork: the adapter queues
# each new turn (`w -eq_trk_pending-> m`) once the S0 fixpoint is reached (that
# edge IS the "S0 done" stamp) and ticks; one turn at a time becomes current
# (`w -eq_trk_cur-> m`) and passes the phases below in rule order, all within one
# pass. Every negation in a phase reads either the current turn's completed S0
# labels or the state left by EARLIER turns, which the cursor has finalised --
# stratification by turn order, so incremental batches == one shot by construction.
# 0.8.0 (T3g): a turn's structure may be REVISED by a later turn, but only at that
# later turn's cursor step and only while the earlier turn is in its author's bounded
# held frontier (uptake, below) -- still a function of the turn sequence alone, so
# incremental == one shot holds once the revisions (turns_delta) are folded.
#
# Conversation state (graph-resident, mutated only by these rules):
#   w -eq_qud-> q               open-question set (QUD): q is a question turn not
#                               yet answered; its addressees are q's eq_addresses
#                               edges, none = the room
#   b -eq_pending-> x           x addressed actor b and b has not taken a turn since
#   b -eq_last_addressed_by-> x the most recent turn by another actor addressing b
#                               (second-person resolution)
#   a -eq_last_claim-> x        a's most recent claim (assertion / directive) turn
#   a -eq_last_turn-> x         (0.8.0) a's most recent turn
#   a -eq_trk_held-> x          (0.8.0) a's held / weak turn still revisable (frontier)
SECOND_PERSON = ("you", "your", "yours", "yourself", "yourselves", "you're", "you've",
                 "you'll", "you'd", "ya", "y'all")
# 0.7.0 closed-class BACKCHANNEL codebook (continuers / acknowledgement tokens /
# fillers, as tokenised: "mm-hmm" -> mm, hmm; "uh-huh" -> uh, huh). A turn made only of
# these tokens (and no code / link span) is a backchannel: it may respond to a
# question but does not ANSWER it. Polar answers ("yes" / "no") are not in the list.
BACKCHANNEL = ("yeah", "yeh", "yah", "yep", "yup", "okay", "ok", "right", "alright", "mm", "mmm", "mhm",
               "hmm", "hm", "huh", "uh", "um", "uhm", "er", "erm", "ah", "oh", "aha", "ooh")
TRACKING_ITEMS = ([("EqSecondPerson", {"form": f}) for f in SECOND_PERSON]
                  + [("EqBackchannel", {"form": f}) for f in BACKCHANNEL])
TRACKING_EDGE = {"EqSecondPerson": "eq_has_second_person", "EqBackchannel": "eq_has_backchannel"}
CUR = ["w", "eq_trk_cur", "m"]
CLAIM_LABS = (ASSERTION, DIRECTIVE)


def _backchannel_only(m):
    """m has at least one token, every token is a backchannel form, and no span."""
    return And(Ex(Nb(m, "eq_has_token"), "bk0"), Not(Ex(Nb(m, "eq_has_span"), "bks")),
               Not(Ex(Nb(m, "eq_has_token"), "bk1", Not(Ex(Nb("agent", "eq_has_backchannel"), "bk2",
                                                           Eq(A("bk2", "form"), A("bk1", "form")))))))


def _addressed_any(m):
    return Ex(Nb(m, "eq_addresses"), f"ad_{m}")


def _compat(m, x, b):
    """x (authored by b) is a compatible response target for m: m's explicit /
    second-person addressees (if any) include b, and m and x share the
    platform thread whenever m declares one."""
    return And(Or(Not(_addressed_any(m)), In(V(b), Nb(m, "eq_addresses"))),
               Or(Eq(A(m, "eq_platform_thread"), L(None)),
                  Eq(A(m, "eq_platform_thread"), A(x, "eq_platform_thread"))))


def _qud_for(x, a, m="m"):
    """open question x is for m's author a: addressed to a, or to the room (no
    addressees) when m is not itself a question -- a question after a ROOM
    question opens its own room question (a counter-question presupposes being
    addressed)."""
    return Or(In(V(a), Nb(x, "eq_addresses")),
              And(Not(Ex(Nb(x, "eq_addresses"), f"xa_{x}")), Not(has(m, QUESTION))))


def _open_item(y, a, m, b_same=None):
    """y is a compatible open item for m's author a: an open question for a / the
    room, or a pending address to a; by another actor; compatible with m.
    `b_same` restricts y's author to the same actor (per-addressee grouping)."""
    yb = f"au_{y}"
    by = And(Not(Same(yb, a)), _compat(m, y, yb))
    if b_same is not None:
        by = And(by, Or(Not(_addressed_any(m)), Same(yb, b_same)))
    return Ex(Nb(y, "eq_authored_by"), yb, by)


def _newer_pending(x, a, m, b):
    return Ex(Nb(a, "eq_pending"), "yp", And(Gt(A("yp", POS), A(x, POS)), _open_item("yp", a, m, b)))


def _leads_with_contrast(m):
    return Ex(Nb(m, "eq_has_token"), "lt", And(
        Not(Ex(Nb(m, "eq_has_token"), "lk", Lt(A("lk", "eq_pos"), A("lt", "eq_pos")))),
        Ex(Nb("agent", "eq_has_coh_marker"), "lc",
           And(Eq(A("lc", "rel"), L("contrast")), Eq(A("lc", "form"), A("lt", "form"))))))


UNDECLARED = Eq(A("m", "eq_reply_to_ref"), L(None))

# ---- 0.8.0 (T3g): HELD-OPEN reply attribution ---------------------------------
# A turn's parent is no longer forced. At its cursor step an undeclared turn m gets a
# bounded CANDIDATE set (`m -eq_has_cand-> c`, `c -eq_cand_ref-> x`, one fresh
# EqParentCand node per candidate), built only from bounded conversation state:
#   * the QUD top for m's author: the most recent compatible question among the latest
#     open question addressed to m's author (`a -eq_qud_for-> x`) and every actor's latest
#     open room question (`c -eq_qud_room-> x`) -- bounded by actors; older open
#     questions stay open (QUD read-out) but are no source; one per named addressee group
#                                                    (eq.trk.cand.open_question.addressed / .room)
#   * the most recent compatible pending address to m's author (eq.trk.cand.pending)
#   * the most recent compatible claim by another actor, when m leads with contrast /
#     concession / disagreement                                (eq.trk.cand.claim)
#   * the adjacent other-speaker turn `m -eq_trk_adj-> x` (the previous turn if another
#     actor wrote it, else the previous turn's own adjacent turn: one chain step over the
#     same-actor run, finalised at each turn's step)          (eq.trk.cand.adjacent)
#   * each addressee's last turn `b -eq_last_turn-> x`        (eq.trk.cand.addressee)
# Each source contributes its stack top (a maximal element of a bounded state set), never
# a ranking BETWEEN candidates. Every candidate must be compatible with m (_compat).
# Each candidate then carries CUE edges `c -eq_cue-> k` to the closed EqTrkCue codebook
# (equilibrium_tracking): every cue whose predicate holds for (m, x) -- the cue rules are
# properties of the pair, independent of which source proposed it.
# COLLAPSE is the categorical dominance shape (cf. vision_border_ownership bo_mint_owned):
#   c dominates r  <=>  cues(r) is a STRICT subset of cues(c)
#   m collapses to c <=> c dominates every rival (a sole candidate dominates vacuously);
#   confidence strong (|cues(c)| > |{pick}|, i.e. >= 2 distinct cues) else weak;
#   otherwise (>= 2 candidates, none dominating all) m is HELD -- a tie is never broken.
# A held or weak turn enters its author's HELD FRONTIER `a -eq_trk_held-> m` (at most one
# turn per actor: it is frozen -- leaves the frontier, structure unchanged -- when its
# author speaks again). UPTAKE: when a later turn y by actor B collapses to (or is a
# declared reply to, or is HELD with among its candidates) a frontier turn m and B
# authored candidate x of m, x gains the cue
# `uptake` and m's dominance is re-evaluated at y's step; strong collapses leave the
# frontier (frozen). Since a weak winner is a SOLE candidate with one cue (a strict subset
# of a singleton is empty and cues are non-empty), a weak collapse can only be upgraded to
# strong by uptake, never overturned; responds_to edges are never retracted.
# STATE (qud / pending / addressed_by / claim / rsp): updated at m's own step from m's
# immediate structure (as before); a held turn closes nothing; the parent's author is
# an addressee (hence pending / addressed_by) only of a STRONG collapse. A LATE collapse (uptake)
# applies only what is still applicable at y's step: the answer edge (same guards), the
# QUD close of the answered question, and (strong, non-question m) the parent's author as
# m's own addressee. It adds no pending address (the parent's author has just spoken in y:
# moot) and no last-addresser pointer, does not re-route a question, does not revise
# thread ids (causal), and does not touch rsp state.
# Revisions are marked for the read-out: `w -eq_trk_rev-> m` (uptake / freeze: emitted as
# a turns_delta entry), `w -eq_trk_late-> m` (a late collapse: materialised and re-layered
# through L1 / L2 so downstream facts equal a one-shot run). The adapter removes both
# marks after the batch's tracking fixpoint.
CUE_CODES = ("adjacent", "open_question", "addressed", "vocative", "second_person", "contrast",
             "answer_form", "same_thread", "uptake")
# closed-class polar-question openers (auxiliaries, as tokenised) and polar answer forms
POLAR_AUX = ("is", "are", "was", "were", "am", "do", "does", "did", "can", "could", "will", "would",
             "should", "shall", "may", "might", "must", "have", "has", "had", "isn't", "aren't",
             "wasn't", "weren't", "don't", "doesn't", "didn't", "can't", "couldn't", "won't",
             "wouldn't", "shouldn't", "haven't", "hasn't", "hadn't")
POLAR_ANSWER = ("yes", "no", "yeah", "yep", "yup", "nope", "nah", "sure", "absolutely",
                "definitely", "certainly", "correct", "exactly", "indeed")
TRACKING_ITEMS += ([("EqTrkCue", {"code": c}) for c in CUE_CODES]
                   + [("EqPolarAux", {"form": f}) for f in POLAR_AUX]
                   + [("EqPolarAnswer", {"form": f}) for f in POLAR_ANSWER])
TRACKING_EDGE.update({"EqTrkCue": "eq_has_trk_cue", "EqPolarAux": "eq_has_polar_aux",
                      "EqPolarAnswer": "eq_has_polar_answer"})

CANDS = Nb("m", "eq_has_cand")


def _open_q(x):
    """x is in the open-question set (read from x's side: O(1), never a scan of the QUD)"""
    return In(V("w"), InNb(x, "eq_qud"))


def _newer_open(x, b):
    """a strictly more recent compatible open question among the bounded QUD-top sources
    (in the same addressee group when m names addressees): x is then not the top.
    (Amendment A: an answered question stays on its pointer as a live TOPIC issue, so
    the reply-level top reads only the still-open ones.)"""
    return Or(Ex(Nb("a", "eq_qud_for"), "yf", And(Gt(A("yf", POS), A(x, POS)), _open_q("yf"),
                                                 _open_item("yf", "a", "m", b))),
              And(Not(has("m", QUESTION)), Ex(Nb("w", "eq_has_actor"), "oc", Ex(Nb("oc", "eq_qud_room"), "yr", And(
                  Gt(A("yr", POS), A(x, POS)), _open_q("yr"), _open_item("yr", "a", "m", b))))))


def _answer_form(m, x):
    """eq-tax-0.8.0 Amendment A: the TYPE-CONFORMING answer form (Raymond 2003; Schegloff
    2007): x is a question led by a polar auxiliary (after any leading vocative: "Bea, is
    ...") and m leads with a polar answer form. A free-form assertion is not an answer
    FORM -- it is a free-form contribution to the issue x raised (the topic relation
    below), so it no longer makes x a reply rival."""
    t, k, cb, v = f"qt_{x}", f"qk_{x}", f"qc_{x}", f"qv_{x}"
    polar_q = Ex(Nb(x, "eq_has_token"), t, And(
        Ex(Nb("agent", "eq_has_polar_aux"), cb, Eq(A(cb, "form"), A(t, "form"))),
        Not(Ex(Nb(x, "eq_has_token"), k, And(Lt(A(k, "eq_pos"), A(t, "eq_pos")), Not(Ex(
            Nb(x, "eq_trk_voc"), v, Eq(A(v, "eq_name_form"), A(k, "form")))))))))
    return And(has(x, QUESTION), polar_q, _leads_with(m, "eq_has_polar_answer", f"pa_{x}"))


def _thread_shared(m, x):
    """m and x are in the same sequence space: the same platform thread, or either
    declares none"""
    return Or(Eq(A(m, "eq_platform_thread"), L(None)), Eq(A(x, "eq_platform_thread"), L(None)),
              Eq(A(m, "eq_platform_thread"), A(x, "eq_platform_thread")))


def _room_slot(x, b):
    """m (by a) occupies the conditional-relevance slot of ROOM question x (by b): x's
    slot is still open (`x -eq_cr_slot-> w`: no turn by another actor in x's sequence
    space -- its platform thread, when declared -- since x; eq.trk.slot.*) and m is by
    another actor in that space"""
    return And(Not(Same("a", b)), In(V("w"), Nb(x, "eq_cr_slot")), _thread_shared("m", x))


def _reply_gate(x, b):
    """Amendment A reply relation: an open question x (by b) for m's author a is a REPLY
    rival only when m has the answer form, or m occupies x's conditional-relevance slot
    (Schegloff 2007): a selected next speaker's first turn after it (x addressed a and a
    has not spoken since: `a -eq_pending-> x`), or for a room question the first turn by
    another actor after it. The question is never classified (simple / complex): the
    replying turn's form and position decide."""
    return Or(_answer_form("m", x), In(V("a"), InNb(x, "eq_pending")), _room_slot(x, b))


def _cues(c):
    return Nb(c, "eq_cue")


def _dominates(c, r):
    """cues(r) is a strict subset of cues(c): every cue of r is a cue of c, and c has
    strictly more (two set sizes compared, no number)."""
    k = f"dk_{c}_{r}"
    return And(Not(Ex(_cues(r), k, Not(In(V(k), _cues(c))))), Gt(Count(_cues(c)), Count(_cues(r))))


def _dominates_all(m, c):
    r = f"rv_{c}"
    return Not(Ex(Nb(m, "eq_has_cand"), r, And(Not(Same(r, c)), Not(_dominates(c, r)))))


def _strong(c):
    return Gt(Count(_cues(c)), singleton(_cues(c)))


def _leads_with(m, edge, sfx):
    """m's first token is a form of the `edge` codebook"""
    t, k, cb = f"lt_{sfx}", f"lk_{sfx}", f"lc_{sfx}"
    return Ex(Nb(m, "eq_has_token"), t, And(
        Not(Ex(Nb(m, "eq_has_token"), k, Lt(A(k, "eq_pos"), A(t, "eq_pos")))),
        Ex(Nb("agent", edge), cb, Eq(A(cb, "form"), A(t, "form")))))


def _contrastive(m):
    return Or(_leads_with_contrast(m), has(m, lab("msg.concession")), has(m, lab("msg.disagreement")))


def _substantive_answer(m):
    """the existing answer guards: not a counter-question / withdrawal, not dismissive,
    not backchannel-only"""
    return And(Not(_cc(m, "nonanswer")), Not(_dismissive(m)), Not(_backchannel_only(m)))


# cue predicates over (m by a, candidate c -> x by b)
CUE_PREDICATES = {
    "adjacent": In(V("x"), Nb("m", "eq_trk_adj")),
    "open_question": And(_open_q("x"), _qud_for("x", "a"), _reply_gate("x", "b")),
    "addressed": In(V("a"), InNb("x", "eq_pending")),
    "vocative": In(V("b"), Nb("m", "eq_trk_voc")),
    "second_person": In(V("b"), Nb("m", "eq_trk_2p")),
    "contrast": And(_contrastive("m"), In(V("x"), Nb("b", "eq_last_claim"))),
    # Amendment A: the type-conforming (polar) answer form only
    "answer_form": _answer_form("m", "x"),
    "same_thread": And(Not(Eq(A("m", "eq_platform_thread"), L(None))),
                       Eq(A("m", "eq_platform_thread"), A("x", "eq_platform_thread"))),
}
CAND_FX = [["add_edge", "m", "eq_trk_cand", "x"]]
TRK_CUE = ["agent", "eq_has_trk_cue", "k"]
CAND_X = ["m", "eq_has_cand", "c"], ["c", "eq_cand_ref", "x"]
HELD_OR_WEAK = Or(Eq(A("m", "eq_trk_conf"), L("held")), Eq(A("m", "eq_trk_conf"), L("weak")))

# ---- eq-tax-0.8.0 AMENDMENT A: questions open TOPICS ---------------------------
# Two relations per turn, each held open with the same dominance shape:
#   reply (above): the local sequential prior; an open question is a reply rival only
#     under _reply_gate (answer form / conditional-relevance slot);
#   topic (here): the live issue(s) the turn is under (Roberts 1996 QUD; Ginzburg 2012:
#     a question raises an issue that stays live while people say other things).
# LIVE ISSUES (bounded, no new state): the question on m's author's addressee pointer
# (`a -eq_qud_for-> x`, one) and each other actor's latest room question
# (`b -eq_qud_room-> x`, one per asker), current on that pointer, by another actor. A
# free-form answer leaves the issue live; only a type-conforming (polar) answer resolves
# and downdates it (eq.trk.open_q.answered.*). No intervening talk retires an issue; only
# a newer question on the same pointer, that resolution, or close does. A platform-
# DECLARED reply (text) takes its parent's topic only (via_reply sources). Bound:
# |topic candidates| <= 1 (addressee pointer) + (other actors with a room question on
# their pointer) + 2 (via_reply: the one settled / declared parent -- itself when a
# question, and its decided topic) -- per turn O(actors), as the reply room source.
# A candidate is a fresh EqTopicCand (`m -eq_has_tcand-> c -eq_tcand_ref-> x`) with cue
# edges `c -eq_tcue-> k` to the closed EqTopicCue codebook; topic decided
# (`m -eq_top_to-> x`) iff one candidate's cue set strictly contains every rival's (a
# sole candidate dominates vacuously); else HELD (`m.eq_top_state = held`). FROZEN
# (`frozen`) when decided with >= 2 cues, or decided via_reply from a frozen reply
# (strong / declared); a decided-but-revisable topic is `open` (a sole 1-cue
# candidate: by the same argument as the reply relation, it can only gain cues, never
# change target). Held / open topics enter the author's TOPIC FRONTIER
# `a -eq_top_held-> m` (at most one turn per actor; frozen when the author speaks again).
# TOPIC UPTAKE: a later turn y by the asker of x or by a topic MEMBER of x
# (`x -eq_tmember-> actor`: the asker's co-participants whose turn was decided under x)
# that SETTLES a reply onto frontier turn m adds `uptake` to m's candidate x; m is
# re-evaluated at y's step (turns_delta).
# ENGAGEMENT: a turn decided under x, by an actor c other than x's asker, that is not
# backchannel-only / nonanswer / dismissive marks `x -eq_engaged_by-> c`: x is not
# unanswered (inquiry.unanswered: engaged by anyone, as answered by anyone) and c
# responded to it (interaction.responsiveness: per actor, as `eq_rsp_ans`); x stays live.
TOPIC_CUE_CODES = ("open_question", "via_reply", "vocative", "same_thread", "uptake", "answer_form")
TRACKING_ITEMS += [("EqTopicCue", {"code": c}) for c in TOPIC_CUE_CODES]
TRACKING_EDGE["EqTopicCue"] = "eq_has_top_cue"
TCANDS = Nb("m", "eq_has_tcand")
TOP_CUE = ["agent", "eq_has_top_cue", "k"]
TCAND_X = ["m", "eq_has_tcand", "c"], ["c", "eq_tcand_ref", "x"]
TOP_FX = [["add_edge", "m", "eq_top_cand", "x"]]
SETTLED = (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))
# a platform-declared reply, to another actor (eq_responds_to, declared at m's own step)
# or a declared self-continuation (eq_reply_to to the author's own turn)
NOT_DECLARED = Not(Ex(Nb("m", "eq_reply_to"), "dr_m"))
VIA = SETTLED + (("platform", "eq_reply_to"),)


def _tcues(c):
    return Nb(c, "eq_tcue")


def _tdominates(c, r):
    k = f"tk_{c}_{r}"
    return And(Not(Ex(_tcues(r), k, Not(In(V(k), _tcues(c))))), Gt(Count(_tcues(c)), Count(_tcues(r))))


def _tdominates_all(m, c):
    r = f"tr_{c}"
    return Not(Ex(Nb(m, "eq_has_tcand"), r, And(Not(Same(r, c)), Not(_tdominates(c, r)))))


def _live_issue(x):
    """x is current on a bounded QUD pointer (read from x's side: O(1))"""
    return Or(Ex(InNb(x, "eq_qud_for"), f"lf_{x}"), Ex(InNb(x, "eq_qud_room"), f"lr_{x}"))


def _issue_for(x, a):
    """x is a live issue for actor a: on a's addressee pointer, or a room question on its
    asker's pointer"""
    return Or(In(V(a), InNb(x, "eq_qud_for")), Ex(InNb(x, "eq_qud_room"), f"ir_{x}"))


def _has_tcue(c, code):
    v = f"hc_{c}_{code}"
    return Ex(_tcues(c), v, Eq(A(v, "code"), L(code)))


def _reply_frozen(m):
    """m's reply is frozen at its own step: platform-declared, or a strong collapse"""
    return Or(Ex(Nb(m, "eq_reply_to"), f"rf_{m}"), Eq(A(m, "eq_trk_conf"), L("strong")))


def _strong_t(c):
    return Gt(Count(_tcues(c)), singleton(_tcues(c)))


def _engaging(p):
    """p is a free-form contribution, not backchannel-only / nonanswer / dismissive"""
    return _substantive_answer(p)


# (x's author is read by a where-check, not a match edge: the matcher binds distinct
# variables to distinct nodes, and x may be by m's own author -- via_reply inherits the
# author's own question as the topic it is under)
def _x_by(pred):
    return Ex(Nb("x", "eq_authored_by"), "xb", pred)


TOPIC_CUE_PREDICATES = {
    "open_question": And(_x_by(Not(Same("a", "xb"))), _issue_for("x", "a")),
    # m's settled reply parent is x, or is decided under x
    "via_reply": Or(*[Or(In(V("x"), Nb("m", e)), Ex(Nb("m", e), f"vr_{bs}", In(V("x"), Nb(f"vr_{bs}", "eq_top_to"))))
                      for bs, e in VIA]),
    "vocative": _x_by(In(V("xb"), Nb("m", "eq_trk_voc"))),
    "same_thread": And(Not(Eq(A("m", "eq_platform_thread"), L(None))),
                       Eq(A("m", "eq_platform_thread"), A("x", "eq_platform_thread"))),
    "answer_form": _answer_form("m", "x"),
}

# (1) TOPIC UPTAKE of a frontier turn p by the current turn m (by a), run BEFORE m's own
# topic so that m's via_reply reads p's revised topic
TOPIC_UPTAKE_RULES = [
    *[rule(f"eq.trk.top.uptake.{basis}",
           [WIN, CUR, AUTH, ["m", edge, "p"], ["p", "eq_has_tcand", "c"], ["c", "eq_tcand_ref", "x"], TOP_CUE],
           And(Eq(A("k", "code"), L("uptake")), Not(In(V("k"), _tcues("c"))), Not(_authored_by("p", "a")),
               Or(_authored_by("x", "a"), In(V("a"), Nb("x", "eq_tmember"))),
               Ex(Nb("p", "eq_authored_by"), "tpa", In(V("p"), Nb("tpa", "eq_top_held")))),
           [["add_edge", "c", "eq_tcue", "k"], ["add_edge", "m", "eq_top_up", "p"],
            ["add_edge", "w", "eq_trk_rev", "p"]])
      for basis, edge in SETTLED],
    rule("eq.trk.top.late.decide", [WIN, CUR, ["m", "eq_top_up", "p"], ["p", "eq_has_tcand", "c"],
                                    ["c", "eq_tcand_ref", "x"]],
         And(Not(Ex(Nb("p", "eq_top_to"), "ptx")), _tdominates_all("p", "c")),
         [["add_edge", "p", "eq_top_to", "x"], ["set_attr", "p", "eq_top_state", "open"]]),
    rule("eq.trk.top.late.frozen", [WIN, CUR, ["m", "eq_top_up", "p"], ["p", "eq_top_to", "x"],
                                    ["p", "eq_has_tcand", "c"], ["c", "eq_tcand_ref", "x"]],
         _strong_t("c"), [["set_attr", "p", "eq_top_state", "frozen"]]),
    rule("eq.trk.top.late.leave", [WIN, CUR, ["m", "eq_top_up", "p"], ["p", "eq_authored_by", "pa"],
                                   ["pa", "eq_top_held", "p"]],
         Eq(A("p", "eq_top_state"), L("frozen")), [["del_edge", "pa", "eq_top_held", "p"]]),
    rule("eq.trk.top.late.member", [WIN, CUR, ["m", "eq_top_up", "p"], ["p", "eq_top_to", "x"],
                                    ["p", "eq_authored_by", "pa"]],
         L(True), [["add_edge", "x", "eq_tmember", "pa"]]),
    rule("eq.trk.top.late.engaged", [WIN, CUR, ["m", "eq_top_up", "p"], ["p", "eq_top_to", "x"],
                                     ["p", "eq_authored_by", "pa"], ["x", "eq_authored_by", "xb"]],
         And(Not(Same("pa", "xb")), _engaging("p")), [["add_edge", "x", "eq_engaged_by", "pa"]]),
]

# (2) the current turn's own topic
TOPIC_RULES = [
    # every live issue for m's author -- unless m is a platform-DECLARED reply: in text the
    # participant displays the sequence the turn continues (SSJ 1974 next-turn display), so
    # its topic is its parent's (the via_reply sources below), never an unrelated issue
    rule("eq.trk.top.cand.for", [WIN, CUR, AUTH, ["a", "eq_qud_for", "x"], ["x", "eq_authored_by", "b"]],
         And(Not(Same("a", "b")), NOT_DECLARED), TOP_FX),
    rule("eq.trk.top.cand.room", [WIN, CUR, AUTH, ["w", "eq_has_actor", "b"], ["b", "eq_qud_room", "x"]],
         And(Not(Same("a", "b")), NOT_DECLARED), TOP_FX),
    # via_reply sources: the settled parent question itself, or the parent's decided topic
    *[rule(f"eq.trk.top.via_q.{basis}", [WIN, CUR, ["m", edge, "x"]],
           And(has("x", QUESTION), _live_issue("x")), TOP_FX) for basis, edge in VIA],
    *[rule(f"eq.trk.top.via_t.{basis}", [WIN, CUR, ["m", edge, "p"], ["p", "eq_top_to", "x"]],
           _live_issue("x"), TOP_FX) for basis, edge in VIA],
    rule("eq.trk.top.cand.node", [WIN, CUR, ["m", "eq_top_cand", "x"]],
         Not(Ex(TCANDS, "t0", In(V("x"), Nb("t0", "eq_tcand_ref")))),
         [["add_node", "c", "EqTopicCand", {"eq_tcand": True}], ["add_edge", "m", "eq_has_tcand", "c"],
          ["add_edge", "c", "eq_tcand_ref", "x"]]),
    *[rule(f"eq.trk.top.cue.{code}", [WIN, CUR, AUTH, *TCAND_X, TOP_CUE],
           And(Eq(A("k", "code"), L(code)), pred), [["add_edge", "c", "eq_tcue", "k"]])
      for code, pred in TOPIC_CUE_PREDICATES.items()],
    rule("eq.trk.top.collapse", [WIN, CUR, *TCAND_X], _tdominates_all("m", "c"),
         [["add_edge", "m", "eq_top_to", "x"], ["set_attr", "m", "eq_top_state", "open"]]),
    rule("eq.trk.top.held", [WIN, CUR],
         And(Ex(TCANDS, "t0"), Not(Ex(TCANDS, "t1", _tdominates_all("m", "t1")))),
         [["set_attr", "m", "eq_top_state", "held"]]),
    rule("eq.trk.top.frozen", [WIN, CUR, ["m", "eq_top_to", "x"], *TCAND_X],
         Or(_strong_t("c"), And(_has_tcue("c", "via_reply"), _reply_frozen("m"))),
         [["set_attr", "m", "eq_top_state", "frozen"]]),
    rule("eq.trk.top.member", [WIN, CUR, AUTH, ["m", "eq_top_to", "x"]], L(True),
         [["add_edge", "x", "eq_tmember", "a"]]),
    rule("eq.trk.top.engaged", [WIN, CUR, AUTH, ["m", "eq_top_to", "x"], ["x", "eq_authored_by", "b"]],
         And(Not(Same("a", "b")), _engaging("m")), [["add_edge", "x", "eq_engaged_by", "a"]]),
]

# (3) topic frontier (with the reply frontier, at the author's next turn / close)
TOPIC_FRONTIER_RULES = [
    rule("eq.trk.top.freeze.mark", [WIN, CUR, AUTH, ["a", "eq_top_held", "z"]], Not(Same("z", "m")),
         [["add_edge", "w", "eq_trk_rev", "z"]]),
    rule("eq.trk.top.freeze.drop", [WIN, CUR, AUTH, ["a", "eq_top_held", "z"]], Not(Same("z", "m")),
         [["del_edge", "a", "eq_top_held", "z"]]),
    rule("eq.trk.top.frontier.enter", [WIN, CUR, AUTH],
         Or(Eq(A("m", "eq_top_state"), L("held")), Eq(A("m", "eq_top_state"), L("open"))),
         [["add_edge", "a", "eq_top_held", "m"]]),
]

TRACKING_RULES = [
    # ordering-only continuation: consecutive turns by the same actor (interaction.run)
    rule("eq.trk.continues", [WIN, TURN, ["m", "eq_prev_turn", "p"], AUTH, ["p", "eq_authored_by", "a"]],
         L(True), [["add_edge", "m", "eq_continues", "p"]]),
    # T0 cursor: the earliest queued turn becomes current once no turn is current
    rule("eq.trk.cursor", [WIN, ["w", "eq_trk_pending", "m"]],
         And(Not(Ex(Nb("w", "eq_trk_cur"), "c")),
             Not(Ex(Nb("m", "eq_prev_turn"), "y", In(V("y"), Nb("w", "eq_trk_pending"))))),
         [["add_edge", "w", "eq_trk_cur", "m"], ["del_edge", "w", "eq_trk_pending", "m"]]),
    # 0.8.0 adjacent other-speaker turn: the previous turn if another actor wrote it,
    # else (same-actor run) the previous turn's own adjacent turn -- one chain step
    rule("eq.trk.adj.prev", [WIN, CUR, AUTH, ["m", "eq_prev_turn", "p"], ["p", "eq_authored_by", "b"]],
         Not(Same("a", "b")), [["add_edge", "m", "eq_trk_adj", "p"]]),
    # (p's author is a where-check, not a match edge: a match edge `p -eq_authored_by-> a`
    # joined from the new authorship edge would enumerate every turn of a)
    rule("eq.trk.adj.run", [WIN, CUR, AUTH, ["m", "eq_prev_turn", "p"], ["p", "eq_trk_adj", "x"]],
         _authored_by("p", "a"), [["add_edge", "m", "eq_trk_adj", "x"]]),
    # T1 explicit address: a token equal to the name form of an actor who has
    # already spoken (actor_ref supplied by the platform; no identity guessing).
    # 0.8.0: the vocative mark `m -eq_trk_voc-> b` is the `vocative` cue's fact.
    rule("eq.trk.addressee.mention",
         [WIN, CUR, AUTH, ["m", "eq_has_token", "t"], ["w", "eq_has_actor", "b"]],
         And(Eq(A("t", "form"), A("b", "eq_name_form")), Not(Same("a", "b")),
             Lt(A("b", "eq_first_pos"), A("m", POS))),
         [["add_edge", "m", "eq_addresses", "b"], ["add_edge", "m", "eq_trk_voc", "b"]]),
    # T1' (0.7.0, participants roster) explicit address of a ROSTER participant,
    # who may not have spoken yet: the turn carries one of the participant's
    # aliases (or its actor_ref name form) as consecutive tokens -- the alias's
    # first form at token t, and every alias token at t's position plus its
    # offset. Same address edge as T1; second-person rules unchanged.
    dict(rule("eq.trk.addressee.participant",
              [WIN, CUR, AUTH, ["m", "eq_has_token", "t"], ["w", "eq_has_participant", "b"],
               ["b", "eq_has_alias", "al"]],
              And(Eq(A("al", "a_form1"), A("t", "form")), Not(Same("a", "b")),
                  Not(Ex(Nb("al", "eq_alias_tok"), "k", Not(Ex(Nb("m", "eq_has_token"), "u", And(
                      Eq(A("u", "eq_pos"), {"type": "Plus", "items": [A("t", "eq_pos"), A("k", "eq_apos")]}),
                      Eq(A("u", "form"), A("k", "form")))))))),
              [["add_edge", "m", "eq_addresses", "b"], ["add_edge", "m", "eq_trk_voc", "b"]]),
         # R10 join index (matcher traversal only): probe the alias by the token's form
         index_hints=[{"for_var": "al", "via_var": "t", "via_key": "form", "node_type": "EqAlias",
                       "this_key": "a_form1"}]),
    # T2 second-person address with no explicit addressee: the last speaker who
    # addressed this actor (0.8.0: marked `m -eq_trk_2p-> b`, the second_person cue's fact)
    rule("eq.trk.addressee.second_person",
         [WIN, CUR, AUTH, ["a", "eq_last_addressed_by", "x"], ["x", "eq_authored_by", "b"]],
         And(Not(_addressed_any("m")), Not(Same("a", "b")),
             Ex(Nb("m", "eq_has_token"), "t2", Ex(Nb("agent", "eq_has_second_person"), "sp",
                                                  Eq(A("sp", "form"), A("t2", "form"))))),
         [["add_edge", "m", "eq_addresses", "b"], ["add_edge", "m", "eq_trk_2p", "b"]]),
    # T3 (0.8.0) CANDIDATE SOURCES (only when the platform declared no reply). Each
    # source proposes its stack top; none decides the parent.
    # QUD top over BOUNDED state, never a scan of the whole open-question set: the latest
    # open question addressed to m's author (`a -eq_qud_for-> x`) and each actor's latest
    # open ROOM question (`c -eq_qud_room-> x`, when m is not itself a question)
    rule("eq.trk.cand.open_question.addressed",
         [WIN, CUR, AUTH, ["a", "eq_qud_for", "x"], ["x", "eq_authored_by", "b"]],
         And(UNDECLARED, Not(Same("a", "b")), _open_q("x"), _reply_gate("x", "b"), _compat("m", "x", "b"),
             Not(_newer_open("x", "b"))),
         CAND_FX),
    rule("eq.trk.cand.open_question.room",
         [WIN, CUR, AUTH, ["w", "eq_has_actor", "b"], ["b", "eq_qud_room", "x"]],
         And(UNDECLARED, Not(Same("a", "b")), Not(has("m", QUESTION)), _open_q("x"), _reply_gate("x", "b"),
             _compat("m", "x", "b"), Not(_newer_open("x", "b"))),
         CAND_FX),
    rule("eq.trk.cand.pending",
         [WIN, CUR, AUTH, ["a", "eq_pending", "x"], ["x", "eq_authored_by", "b"]],
         And(UNDECLARED, Not(Same("a", "b")), _compat("m", "x", "b"), Not(_newer_pending("x", "a", "m", "b"))),
         CAND_FX),
    # a claim the turn contrasts with / concedes / disagrees with: the most recent
    # compatible claim by another actor
    rule("eq.trk.cand.claim",
         [WIN, CUR, AUTH, ["w", "eq_has_actor", "b"], ["b", "eq_last_claim", "x"]],
         And(UNDECLARED, Not(Same("a", "b")), _compat("m", "x", "b"), _contrastive("m"),
             Not(Ex(Nb("w", "eq_has_actor"), "c", And(Not(Same("c", "a")), Ex(
                 Nb("c", "eq_last_claim"), "z",
                 And(Gt(A("z", POS), A("x", POS)), _compat("m", "z", "c"))))))),
         CAND_FX),
    rule("eq.trk.cand.adjacent", [WIN, CUR, AUTH, ["m", "eq_trk_adj", "x"], ["x", "eq_authored_by", "b"]],
         And(UNDECLARED, _compat("m", "x", "b")), CAND_FX),
    rule("eq.trk.cand.addressee", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"], ["b", "eq_last_turn", "x"]],
         And(UNDECLARED, Not(Same("a", "b")), _compat("m", "x", "b")), CAND_FX),
    # one fresh candidate node per proposed parent (the proposal edge dedups sources)
    rule("eq.trk.cand.node", [WIN, CUR, ["m", "eq_trk_cand", "x"]],
         Not(Ex(CANDS, "c0", In(V("x"), Nb("c0", "eq_cand_ref")))),
         [["add_node", "c", "EqParentCand", {"eq_cand": True}], ["add_edge", "m", "eq_has_cand", "c"],
          ["add_edge", "c", "eq_cand_ref", "x"]]),
    # cue producers: every codebook cue whose predicate holds for (m, x)
    *[rule(f"eq.trk.cue.{code}", [WIN, CUR, AUTH, *CAND_X, ["x", "eq_authored_by", "b"], TRK_CUE],
           And(Eq(A("k", "code"), L(code)), pred), [["add_edge", "c", "eq_cue", "k"]])
      for code, pred in CUE_PREDICATES.items()],
    # COLLAPSE (categorical dominance shape; a tie is held open, never broken)
    rule("eq.trk.collapse.strong", [WIN, CUR, *CAND_X], And(_dominates_all("m", "c"), _strong("c")),
         [["add_edge", "m", "eq_trk_to", "x"], ["set_attr", "m", "eq_trk_conf", "strong"]]),
    rule("eq.trk.collapse.weak", [WIN, CUR, *CAND_X], And(_dominates_all("m", "c"), Not(_strong("c"))),
         [["add_edge", "m", "eq_trk_to", "x"], ["set_attr", "m", "eq_trk_conf", "weak"]]),
    rule("eq.trk.collapse.held", [WIN, CUR],
         And(Ex(CANDS, "c0"), Not(Ex(CANDS, "c1", _dominates_all("m", "c1")))),
         [["set_attr", "m", "eq_trk_conf", "held"]]),
    # (the collapsed parent's author becomes an addressee only AFTER the collapse, so
    # every candidate source read the same T1/T2 addressee set). 0.8.0: only on a STRONG
    # collapse -- a weak one rests on a single cue (typically adjacency), and the address
    # it would infer feeds the `addressed` / `second_person` cues of later turns, so the
    # one cue would be counted again as independent evidence.
    rule("eq.trk.addressee.target", [WIN, CUR, AUTH, ["m", "eq_trk_to", "x"], ["x", "eq_authored_by", "b"]],
         And(Not(Same("a", "b")), Eq(A("m", "eq_trk_conf"), L("strong"))),
         [["add_edge", "m", "eq_addresses", "b"]]),
    # T4 answers (declared OR collapsed responds_to): a SUBSTANTIVE answer-type turn by
    # another actor -- counter-questions / withdrawals (nonanswer), dismissals and
    # (0.7.0) backchannel-only turns do not close. A held turn answers nothing.
    *[rule(f"eq.trk.answers.{basis}",
           [WIN, CUR, AUTH, ["m", edge, "p"], ["p", "eq_authored_by", "b"]],
           And(Not(Same("a", "b")), has("p", QUESTION), Gt(A("m", POS), A("p", POS)), _substantive_answer("m")),
           [["add_edge", "m", "eq_answers", "p"]])
      for basis, edge in (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))],
    # T4' (0.8.0) UPTAKE: m (by a) collapsed to / declared reply to a frontier turn p, and a
    # authored candidate x of p: x gains the `uptake` cue; p is re-evaluated below
    # (authorship and frontier membership are where-checks, never match edges joined from
    # an actor: those would enumerate the actor's every turn)
    *[rule(f"eq.trk.uptake.{basis}",
           [WIN, CUR, AUTH, ["m", edge, "p"], ["p", "eq_has_cand", "c"], ["c", "eq_cand_ref", "x"], TRK_CUE],
           And(Eq(A("k", "code"), L("uptake")), Not(In(V("k"), _cues("c"))), _authored_by("x", "a"),
               Ex(Nb("p", "eq_authored_by"), "pa", In(V("p"), Nb("pa", "eq_trk_held")))),
           [["add_edge", "c", "eq_cue", "k"], ["add_edge", "m", "eq_trk_up", "p"],
            ["add_edge", "w", "eq_trk_rev", "p"]])
      for basis, edge in (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))],
    # T4'' (0.8.0 rev, next-turn proof procedure, Sacks, Schegloff & Jefferson 1974): a
    # HELD later turn takes part too. Its structure does not rule out any of its
    # candidates, so each frontier turn p among them is possibly responded to by a, and
    # a's turn displays a's understanding of p: a candidate x of p authored by a gains
    # `uptake`. (A COLLAPSED m displays one target, so only that target is taken up:
    # the rules above.) Bounded: m's candidates x p's candidates x the cue codebook.
    rule("eq.trk.uptake.held",
         [WIN, CUR, AUTH, ["m", "eq_has_cand", "cm"], ["cm", "eq_cand_ref", "p"], ["p", "eq_has_cand", "c"],
          ["c", "eq_cand_ref", "x"], TRK_CUE],
         And(Eq(A("m", "eq_trk_conf"), L("held")), Eq(A("k", "code"), L("uptake")), Not(In(V("k"), _cues("c"))),
             _authored_by("x", "a"),
             Ex(Nb("p", "eq_authored_by"), "pa", In(V("p"), Nb("pa", "eq_trk_held")))),
         [["add_edge", "c", "eq_cue", "k"], ["add_edge", "m", "eq_trk_up", "p"],
          ["add_edge", "w", "eq_trk_rev", "p"]]),
    # late collapse of a taken-up frontier turn p (same dominance shape, at m's step)
    rule("eq.trk.late.mark", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_has_cand", "c"], ["c", "eq_cand_ref", "x"]],
         And(_dominates_all("p", "c"), Not(Ex(Nb("p", "eq_trk_to"), "px"))),
         [["add_edge", "w", "eq_trk_late", "p"]]),
    rule("eq.trk.late.strong", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_has_cand", "c"], ["c", "eq_cand_ref", "x"]],
         And(_dominates_all("p", "c"), _strong("c")),
         [["add_edge", "p", "eq_trk_to", "x"], ["set_attr", "p", "eq_trk_conf", "strong"]]),
    rule("eq.trk.late.weak", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_has_cand", "c"], ["c", "eq_cand_ref", "x"]],
         And(_dominates_all("p", "c"), Not(_strong("c"))),
         [["add_edge", "p", "eq_trk_to", "x"], ["set_attr", "p", "eq_trk_conf", "weak"]]),
    # a strong collapse is frozen: it leaves the frontier
    rule("eq.trk.late.frozen", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_authored_by", "pa"],
                                ["pa", "eq_trk_held", "p"]],
         Eq(A("p", "eq_trk_conf"), L("strong")), [["del_edge", "pa", "eq_trk_held", "p"]]),
    # what is still applicable of a late collapse: the answer (same guards) and its QUD close
    rule("eq.trk.late.answers",
         [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_trk_to", "x"], ["p", "eq_authored_by", "pa"],
          ["x", "eq_authored_by", "xb"]],
         And(Not(Same("pa", "xb")), has("x", QUESTION), Gt(A("p", POS), A("x", POS)), _substantive_answer("p")),
         [["add_edge", "p", "eq_answers", "x"]]),
    rule("eq.trk.late.qud_close", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_answers", "x"]],
         _open_q("x"), [["del_edge", "w", "eq_qud", "x"]]),
    # (Amendment A fix) NO late addressee: a turn's addressees are causal -- fixed at its
    # own step, like thread ids. The 0.8.0 rev added the parent's author as p's addressee
    # on a strong LATE collapse, but the per-turn evidence rules read the ABSENCE of an
    # addressee (eq.quanta.evidence.untargeted runs live on p's own batch), so a later
    # address made incremental != one shot (the untargeted quantum of p's batch stays).
    # The late collapse still shows the parent's author as the turn's reply target.
    # Amendment A: topic uptake of frontier turns, then the current turn's own topic
    # (read before m's own state updates below: m is never its own topic)
    *TOPIC_UPTAKE_RULES,
    *TOPIC_RULES,
    # T5 state update for the turns after this one
    rule("eq.trk.qud.close", [WIN, CUR, ["m", "eq_answers", "p"]], _open_q("p"),
         [["del_edge", "w", "eq_qud", "p"]]),
    rule("eq.trk.qud.open", [WIN, CUR], has("m", QUESTION), [["add_edge", "w", "eq_qud", "m"]]),
    # 0.8.0 the bounded QUD-top sources: per addressee its latest question, per asker its
    # latest room question. Amendment A: a question answered in the TYPE-CONFORMING answer
    # form (a polar answer to a polar question: the "simple" call / response, Schegloff
    # 2007; Raymond 2003) is resolved and downdated (Ginzburg 2012) -- it leaves its
    # pointer. Any other answer (a free-form contribution that closes it at reply level:
    # eq_qud / open_questions) leaves the issue LIVE on its pointer -- discussion
    # continues -- until a newer question supersedes it there, or close (Roberts 1996).
    # The relation decides, not a classification of the question. The reply sources read
    # only the still-open questions on the pointers.
    *[rule(f"eq.trk.open_q.answered.{e[7:]}", [WIN, CUR, ["m", "eq_answers", "p"], ["b", e, "p"]],
           _answer_form("m", "p"), [["del_edge", "b", e, "p"]]) for e in ("eq_qud_for", "eq_qud_room")],
    *[rule(f"eq.trk.open_q.late_answered.{e[7:]}", [WIN, CUR, ["m", "eq_trk_up", "p"], ["p", "eq_answers", "x"],
                                                     ["b", e, "x"]], _answer_form("p", "x"),
           [["del_edge", "b", e, "x"]]) for e in ("eq_qud_for", "eq_qud_room")],
    # (eval read-out only, read by no rule) a still-OPEN question leaving its bounded QUD-top
    # pointer because a newer question superseded it there: `w -eq_qud_lapsed-> x`. The
    # question itself stays open and live (eq_qud, unanswered / responsiveness state);
    # intervening talk never lapses it (a question opens a topic; answers are free form).
    rule("eq.trk.open_q.lapse_for", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"], ["b", "eq_qud_for", "x"]],
         And(has("m", QUESTION), Not(Same("a", "b")), _open_q("x")), [["add_edge", "w", "eq_qud_lapsed", "x"]]),
    rule("eq.trk.open_q.for_drop", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"], ["b", "eq_qud_for", "x"]],
         And(has("m", QUESTION), Not(Same("a", "b"))), [["del_edge", "b", "eq_qud_for", "x"]]),
    rule("eq.trk.open_q.for_set", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"]],
         And(has("m", QUESTION), Not(Same("a", "b"))), [["add_edge", "b", "eq_qud_for", "m"]]),
    rule("eq.trk.open_q.lapse_room", [WIN, CUR, AUTH, ["a", "eq_qud_room", "x"]],
         And(has("m", QUESTION), Not(_addressed_any("m")), _open_q("x")), [["add_edge", "w", "eq_qud_lapsed", "x"]]),
    rule("eq.trk.open_q.room_drop", [WIN, CUR, AUTH, ["a", "eq_qud_room", "x"]],
         And(has("m", QUESTION), Not(_addressed_any("m"))), [["del_edge", "a", "eq_qud_room", "x"]]),
    rule("eq.trk.open_q.room_set", [WIN, CUR, AUTH], And(has("m", QUESTION), Not(_addressed_any("m"))),
         [["add_edge", "a", "eq_qud_room", "m"]]),
    # Amendment A: the conditional-relevance slot of a ROOM question (Schegloff 2007; SSJ
    # 1974 rule 1b): open from the question until the first turn by another actor in its
    # sequence space (its platform thread when declared; interleaved threads keep their
    # own slots). Read only through the bounded per-asker pointer (O(actors) per turn,
    # as the room source); the current turn read it above.
    rule("eq.trk.slot.close", [WIN, CUR, AUTH, ["w", "eq_has_actor", "b"], ["b", "eq_qud_room", "x"],
                               ["x", "eq_cr_slot", "w"]],
         And(Not(Same("a", "b")), _thread_shared("m", "x")), [["del_edge", "x", "eq_cr_slot", "w"]]),
    rule("eq.trk.slot.open", [WIN, CUR], And(has("m", QUESTION), Not(_addressed_any("m"))),
         [["add_edge", "m", "eq_cr_slot", "w"]]),
    rule("eq.trk.pending.taken", [WIN, CUR, AUTH, ["a", "eq_pending", "x"]], L(True),
         [["del_edge", "a", "eq_pending", "x"]]),
    rule("eq.trk.pending.add", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"]], Not(Same("a", "b")),
         [["add_edge", "b", "eq_pending", "m"]]),
    rule("eq.trk.addressed_by.drop",
         [WIN, CUR, AUTH, ["m", "eq_addresses", "b"], ["b", "eq_last_addressed_by", "x"]],
         Not(Same("a", "b")), [["del_edge", "b", "eq_last_addressed_by", "x"]]),
    rule("eq.trk.addressed_by.set", [WIN, CUR, AUTH, ["m", "eq_addresses", "b"]], Not(Same("a", "b")),
         [["add_edge", "b", "eq_last_addressed_by", "m"]]),
    rule("eq.trk.claim.drop", [WIN, CUR, AUTH, ["a", "eq_last_claim", "x"]],
         Or(*[has("m", k) for k in CLAIM_LABS]), [["del_edge", "a", "eq_last_claim", "x"]]),
    rule("eq.trk.claim.set", [WIN, CUR, AUTH], Or(*[has("m", k) for k in CLAIM_LABS]),
         [["add_edge", "a", "eq_last_claim", "m"]]),
    # 0.8.0 the actor's last turn (the addressee source of later turns)
    rule("eq.trk.last_turn.drop", [WIN, CUR, AUTH, ["a", "eq_last_turn", "x"]], Not(Same("x", "m")),
         [["del_edge", "a", "eq_last_turn", "x"]]),
    rule("eq.trk.last_turn.set", [WIN, CUR, AUTH], L(True), [["add_edge", "a", "eq_last_turn", "m"]]),
    # 0.8.0 FREEZE: the author speaks again -- its frontier turn leaves the frontier with
    # its structure unchanged (re-emitted once as final), then this turn may enter
    rule("eq.trk.freeze.mark", [WIN, CUR, AUTH, ["a", "eq_trk_held", "z"]], Not(Same("z", "m")),
         [["add_edge", "w", "eq_trk_rev", "z"]]),
    rule("eq.trk.freeze.drop", [WIN, CUR, AUTH, ["a", "eq_trk_held", "z"]], Not(Same("z", "m")),
         [["del_edge", "a", "eq_trk_held", "z"]]),
    rule("eq.trk.frontier.enter", [WIN, CUR, AUTH], HELD_OR_WEAK, [["add_edge", "a", "eq_trk_held", "m"]]),
    *TOPIC_FRONTIER_RULES,
    # thread id: the platform thread (S0), else the thread of the EARLIEST parent
    # (declared reply_to, any author, or the immediate collapse; every earlier turn
    # already has its thread), else the turn roots its own thread (a held turn too:
    # thread ids are causal, never revised by a late collapse)
    *[rule(f"eq.trk.thread.inherit_{edge}", [WIN, CUR, ["m", edge, "p"]],
           And(Eq(A("m", "eq_thread"), L(None)), Not(Eq(A("p", "eq_thread"), L(None))),
               Not(Ex(Nb("m", "eq_reply_to"), "p1", Lt(A("p1", POS), A("p", POS)))),
               Not(Ex(Nb("m", "eq_trk_to"), "p2", Lt(A("p2", POS), A("p", POS))))),
           [["set_attr", "m", "eq_thread", T(A("p", "eq_thread"))]])
      for edge in ("eq_reply_to", "eq_trk_to")],
    rule("eq.trk.thread.root", [WIN, CUR], Eq(A("m", "eq_thread"), L(None)),
         [["set_attr", "m", "eq_thread", T(A("m", "eq_ref"))]]),
    # cursor release (last in rule order): the next queued turn starts next pass
    rule("eq.trk.release", [WIN, CUR], L(True),
         [["del_edge", "w", "eq_trk_cur", "m"]]),
    # once the queue is swept: collapsed parents become responds_to (basis tracked) --
    # the batch's own turns, and earlier turns collapsed late in this batch
    rule("eq.trk.materialise", [WIN, TURN, ["m", "eq_trk_to", "x"]],
         And(Not(Ex(Nb("w", "eq_trk_cur"), "c")), Not(Ex(Nb("w", "eq_trk_pending"), "q"))),
         [["add_edge", "m", "eq_responds_to", "x"], ["set_attr", "m", "eq_basis", "tracked"]]),
    rule("eq.trk.materialise.late", [WIN, ["w", "eq_trk_late", "m"], ["m", "eq_trk_to", "x"]],
         And(Not(Ex(Nb("w", "eq_trk_cur"), "c")), Not(Ex(Nb("w", "eq_trk_pending"), "q"))),
         [["add_edge", "m", "eq_responds_to", "x"], ["set_attr", "m", "eq_basis", "tracked"]]),
]
TRACKING_EDGE_TYPES = [
    ("Agent", "eq_has_second_person", "EqSecondPerson"), ("Agent", "eq_has_backchannel", "EqBackchannel"),
    ("Message", "eq_prev_turn", "Message"), ("Message", "eq_trk_to", "Message"), ("Message", "eq_continues", "Message"),
    ("EqWindow", "eq_trk_pending", "Message"), ("EqWindow", "eq_trk_cur", "Message"),
    ("EqWindow", "eq_qud", "Message"), ("EqActor", "eq_pending", "Message"),
    ("EqActor", "eq_last_addressed_by", "Message"), ("EqActor", "eq_last_claim", "Message"),
    # 0.7.0 participants roster (ingest; transient alias content, conversation fork only)
    ("EqWindow", "eq_has_participant", "EqActor"), ("EqActor", "eq_has_alias", "EqAlias"),
    ("EqAlias", "eq_alias_tok", "EqAliasTok"),
    # 0.8.0 held-open reply attribution
    ("Agent", "eq_has_trk_cue", "EqTrkCue"), ("Agent", "eq_has_polar_aux", "EqPolarAux"),
    ("Agent", "eq_has_polar_answer", "EqPolarAnswer"),
    ("Message", "eq_trk_adj", "Message"), ("EqActor", "eq_last_turn", "Message"),
    ("Message", "eq_trk_voc", "EqActor"), ("Message", "eq_trk_2p", "EqActor"),
    ("Message", "eq_trk_cand", "Message"), ("Message", "eq_has_cand", "EqParentCand"),
    ("EqParentCand", "eq_cand_ref", "Message"), ("EqParentCand", "eq_cue", "EqTrkCue"),
    ("EqActor", "eq_trk_held", "Message"), ("Message", "eq_trk_up", "Message"),
    ("EqWindow", "eq_trk_rev", "Message"), ("EqWindow", "eq_trk_late", "Message"),
    ("EqActor", "eq_qud_for", "Message"), ("EqActor", "eq_qud_room", "Message"),
    ("EqWindow", "eq_qud_lapsed", "Message"),
    # eq-tax-0.8.0 Amendment A: topic relation
    ("Agent", "eq_has_top_cue", "EqTopicCue"), ("Message", "eq_top_cand", "Message"),
    ("Message", "eq_has_tcand", "EqTopicCand"), ("EqTopicCand", "eq_tcand_ref", "Message"),
    ("EqTopicCand", "eq_tcue", "EqTopicCue"), ("Message", "eq_top_to", "Message"),
    ("Message", "eq_tmember", "EqActor"), ("Message", "eq_engaged_by", "EqActor"),
    ("EqActor", "eq_top_held", "Message"), ("Message", "eq_top_up", "Message"),
    ("Message", "eq_cr_slot", "EqWindow"),
]


# ---- 0.5.1 (T3d, scaling): the MONOTONE strata rules run LIVE on the retained fork -----
# A rule is monotone over an append-only conversation when every fact it reads is
# either frozen once its turn is tracked (S0 labels, eq_addresses / eq_responds_to /
# eq_answers / eq_continues, the static codebooks) or itself only ever grows (quanta,
# evidence, episode membership) and its absence tests read only frozen facts. Such
# a rule derives the same facts whether the turns arrive at once or in batches, so it
# needs no scratch fork: it runs on the retained fork, driven semi-naively by
# per-turn layer marks the adapter adds after the tracking fixpoint and removes
# again once the layer's fixpoint is reached (the marks are the batch FRONTIER, so a
# full re-match of a live rule only ever sees the batch's own turns):
#   L1  `w -eq_l1-> m`  (turn m is tracked): the per-turn S1 rules. Episode
#       extension is the exception: a root turn also enrols the OLDER turn it
#       responds to, so a reply to that older turn may join later -- eq.ep.extend
#       binds every turn, gated by `agent -eq_l1_open-> w` (open only during L1);
#   L2  `agent -eq_l2_open-> w` plus `w -eq_l2-> m` (m's L1 facts are final):
#       rules whose absence test reads an L1 fact of m (`m not evidence of q`). A cue
#       counter pairs a turn with a quantum of its author, and the quantum can first
#       appear AFTER the turn, so each counter rule has a `.newq` twin driven by
#       `w -eq_qnew-> q` (the quanta first minted in this batch) over all turns of
#       that author. Both twins carry the original rule's provenance.
# Rules that read ABSENCE over facts later turns can still change (floor, selective
# non-response, unanswered, grounding, generative outcome, match shapes) stay on the
# per-batch scratch fork, opened stratum by stratum exactly as before.
LIVE_L1 = ("eq.quanta.evidence.untargeted", "eq.quanta.evidence.targeted",
           "eq.quanta.hedged.untargeted", "eq.quanta.hedged.targeted", "eq.quanta.evidence.addressee",
           "eq.quanta.interaction.run", "eq.quanta.epistemic.question_demand",
           "eq.quanta.response.dismissal", "eq.quanta.response.engagement",
           "eq.quanta.inquiry.answered", "eq.ep.root", "eq.ep.extend", "eq.ep.facet")
LIVE_L2 = ("eq.quanta.counter.untargeted", "eq.quanta.counter.targeted",
           "eq.quanta.interaction.withdrawal.counter")
LIVE_ANCHOR = {"eq.quanta.interaction.withdrawal.counter": "m2"}
L1_OPEN, L2_OPEN = ["agent", "eq_l1_open", "w"], ["agent", "eq_l2_open", "w"]
LIVE_EDGE_TYPES = [("EqWindow", "eq_l0", "Message"), ("EqWindow", "eq_l1", "Message"), ("EqWindow", "eq_l2", "Message"),
                   ("Agent", "eq_l1_open", "EqWindow"), ("Agent", "eq_l2_open", "EqWindow"),
                   ("EqWindow", "eq_qnew", "EqQuantum")]
NEWQ = (".untargeted", ".targeted")


def _live(r):
    """Drop the stratum anchor. L1: the turn edge `w -eq_has_turn-> X` becomes the
    frontier mark `w -eq_l1-> X` (or the mark is added on the rule's turn variable).
    L2: gated by `agent -eq_l2_open-> w` (first, so a closed layer matches nothing);
    withdrawal.counter's later turn is the L2 frontier mark."""
    match = [e for e in r["match"] if not (e[0] == "agent" and e[1].startswith("eq_stratum_"))]
    if r["name"] in LIVE_L2:
        match = [L2_OPEN] + [e for e in match if e != WIN]
        if r["name"] in LIVE_ANCHOR:
            match.append(["w", "eq_l2", LIVE_ANCHOR[r["name"]]])
        return dict(r, match=match)
    if r["name"] == "eq.ep.extend":
        return dict(r, match=[L1_OPEN, ["w", "eq_has_turn", "x"]] + match)
    if r["name"] == "eq.ep.facet":  # driven by new membership; full re-match only in L1
        return dict(r, match=[L1_OPEN] + match)
    turn = [i for i, e in enumerate(match) if e[0] == "w" and e[1] == "eq_has_turn"]
    if turn:
        match[turn[0]] = ["w", "eq_l1", match[turn[0]][2]]
    elif r["name"] in LIVE_ANCHOR:
        match = ([] if WIN in match else [WIN]) + match + [["w", "eq_l1", LIVE_ANCHOR[r["name"]]]]
    return dict(r, match=match)


def _newq(r):
    """The `.newq` twin of a live cue counter: the quantum is new in this batch, the
    turn is any turn of its author (not only the frontier)."""
    match = [e for e in r["match"] if e != ["w", "eq_l2", "m"]]
    i = match.index(["a", "eq_has_quantum", "q"])
    match = [match[0], ["w", "eq_qnew", "q"], match.pop(i)] + match[1:]
    return dict(r, name=r["name"] + ".newq", match=match)


# Per-turn S0 / tracking rules bind the batch FRONTIER `w -eq_l0-> m` (added with
# the turn, removed after the batch's tracking fixpoint), so a full re-match of
# these rules sees the batch's turns, not the whole conversation.
FRONTIER_TURN = ("eq.win.responds_to.reply", "eq.win.thread.platform", "eq.trk.materialise",
                 "eq.trk.continues")


def apply_frontier(rules):
    return [dict(r, match=[e if e != TURN else ["w", "eq_l0", "m"] for e in r["match"]])
            if r["name"] in FRONTIER_TURN else r for r in rules]


def apply_live(rules):
    out = []
    for r in rules:
        if r["name"] in LIVE_L1 + LIVE_L2:
            r = _live(r)
            if r["name"].startswith("eq.quanta.counter."):
                r["match"] = [e if e != TURN else ["w", "eq_l2", "m"] for e in r["match"]]
                out += [r, _newq(r)]
                continue
        out.append(r)
    return out


# ---- 0.5.1 stage B (T3d scaling): the NON-MONOTONE families run LIVE too ---------
# The families that read ABSENCE over facts later turns can still change (floor,
# selective non-response, unanswered, claim grounding, generative outcome, match
# shapes) used to be re-derived over the whole conversation on a per-batch scratch
# fork. They now run on the retained fork with BOUNDED rolling state, the same
# one-shot meaning, and no scratch fork:
#   * per-actor turn count `a.eq_nturns`, kept by the turn cursor (one increment per
#     tracked turn, guarded by `m -eq_counted-> a`); the floor family compares
#     `a.eq_nturns_b`, the batch-final copy taken on the L1 frontier, so it sees one
#     state per batch (comparisons over ACTORS, never over turns);
#   * per-question state the cursor finalises in turn order: `w -eq_unans_wait-> q`
#     (question not yet followed by another actor) -> `q -eq_unans_due-> w`;
#     `a -eq_rsp_wait-> q` (question to a, a has not posted since) ->
#     `q -eq_rsp_due-> a`; `q -eq_rsp_ans-> a` (a responded to q);
#   * per-episode membership marks `m -eq_ep_res / eq_ep_esc-> e` (resolve /
#     escalate cue members after the root) for the generative outcome;
#   * RETRACTABLE facts live on DEDICATED edge types, so a retraction only
#     invalidates the few rules reading that type (whose candidate sets are small):
#     `a -eq_nm_quantum-> q` (a non-monotone quantum EXISTS now; the read-out reads
#     it next to `eq_has_quantum`), `q -eq_evidence_nm-> m` (open evidence of an
#     unanswered / non-responded question), `q -eq_counter_nm-> m` (runner-up turns
#     of the floor), `q -eq_floor_ru-> b` (current floor runner-up). A family's
#     quantum NODE is permanent (`a -eq_floor_node / eq_rsp_node / eq_unans_node-> q`)
#     and accrues its monotone parts (floor evidence, answered-question counters)
#     whether or not it currently exists, so re-existence reads exactly the one-shot
#     row. Retired facts leave every candidate set (a vanished quantum is no longer
#     matched by the match shapes; a followed / answered question leaves its wait set).
#   * Match shapes switch: the rule whose shape holds also clears the other shapes'
#     provenance (set to null; the read-out skips null attrs), so the quantum carries
#     exactly the provenance of its current shape. Facet-match provenance on the
#     episode is cleared when no facet of it holds that shape any more.
# Composites (eq.quanta.compose) read `eq_has_quantum` only: pack CONDITION (checked
# by check_nm_pack) -- no EqTraitCompose row requires a non-monotone trait, and no
# EqTraitCue row names one (cue rules never saw scratch quanta, and must not see
# their live successors).
NTB = "eq_nturns_b"
FLOOR_T, RSP_T, UNANS_T, CG_T = ("interaction.floor", "interaction.responsiveness",
                                 "inquiry.unanswered", "competence.claim_grounding")
NM_TRAITS = (FLOOR_T, RSP_T, UNANS_T, CG_T)


def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Union(a, b): return {"type": "Union", "a": a, "b": b}
def trait_is(q, t): return Eq(A(q, "q_trait"), L(t))


def node_nm(q, owner, actor_ref, trait, pole, target, node_edge):
    """Create a family's permanent quantum node (once): the node-creating rule is
    separate from the frequent attach / evidence rules, so those never write a
    node type (which would clear every opaque reader's cursor)."""
    key = {"q_actor": T(actor_ref), "q_trait": T(trait), "q_pole": T(pole), "q_target": T(target)}
    return [["add_node_if_absent", q, "EqQuantum", key], ["add_edge", owner, node_edge, q]]


def attach_nm(q, owner, name):
    return [["add_edge", owner, "eq_nm_quantum", q], ["set_attr", q, f"eqrule:{name}", True]]


def unset(var, name):
    return ["set_attr", var, f"eqrule:{name}", None]


# -- turn cursor (equilibrium_tracking), inserted before eq.trk.release -------------
def _resp_to_actor(x, a):
    """x responds (declared, or tracked at its own cursor step) to a turn by a."""
    return Or(Ex(Nb(x, "eq_responds_to"), "rp1", _authored_by("rp1", a)),
              Ex(Nb(x, "eq_trk_to"), "rp2", _authored_by("rp2", a)))


# the actor's turn count so far plus |{m}| (set shapes, no numeric literal: |{}| / |{m}|)
NUM_TURNS = If(Eq(A("a", "eq_nturns"), L(None)), Count({"type": "SetT", "items": []}), A("a", "eq_nturns"))
TRK_NM_RULES = [
    rule("eq.trk.nturns", [WIN, CUR, AUTH], Not(Ex(Nb("m", "eq_counted"), "cx")),
         [["set_attr", "a", "eq_nturns", T(Plus(NUM_TURNS, Count({"type": "SetT", "items": [V("m")]})))],
          ["add_edge", "m", "eq_counted", "a"]]),
    # 0.7.0: the actor's first turn (set once; the floor's bounded evidence anchor)
    rule("eq.trk.first_turn", [WIN, CUR, AUTH], Not(Ex(Nb("a", "eq_first_turn"), "ft")),
         [["add_edge", "a", "eq_first_turn", "m"]]),
    # unanswered: a question is FOLLOWED once another actor takes a later turn
    rule("eq.trk.unans.follow", [WIN, CUR, AUTH, ["w", "eq_unans_wait", "qt"], ["qt", "eq_authored_by", "b"]],
         Not(Same("a", "b")),
         [["del_edge", "w", "eq_unans_wait", "qt"], ["add_edge", "qt", "eq_unans_due", "w"]]),
    rule("eq.trk.unans.wait", [WIN, CUR], has("m", QUESTION), [["add_edge", "w", "eq_unans_wait", "m"]]),
    # selective non-response: a question to a is DUE once a posts again; a's reply to it
    rule("eq.trk.rsp.due", [WIN, CUR, AUTH, ["a", "eq_rsp_wait", "qt"]], L(True),
         [["del_edge", "a", "eq_rsp_wait", "qt"], ["add_edge", "qt", "eq_rsp_due", "a"]]),
    *[rule(f"eq.trk.rsp.ans.{basis}", [WIN, CUR, AUTH, ["m", edge, "qt"], ["qt", "eq_authored_by", "b"]],
           And(Not(Same("a", "b")), has("qt", QUESTION), _resp_to_actor("qt", "a")),
           [["add_edge", "qt", "eq_rsp_ans", "a"]])
      for basis, edge in (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))],
    *[rule(f"eq.trk.rsp.wait.{basis}", [WIN, CUR, AUTH, ["m", edge, "p"], ["p", "eq_authored_by", "b"]],
           And(Not(Same("a", "b")), has("m", QUESTION)), [["add_edge", "b", "eq_rsp_wait", "m"]])
      for basis, edge in (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))],
]


# -- floor (equilibrium_quanta) -------------------------------------------------
def _nt(x): return A(x, NTB)


COUNTED = Not(Ex(Nb("w", "eq_has_actor"), "oc", Eq(_nt("oc"), L(None))))


def _floor_holds(a):
    return And(Ex(Nb("w", "eq_has_actor"), "o", Not(Same("o", a))),
               Not(Ex(Nb("w", "eq_has_actor"), "o", And(Not(Same("o", a)), Gte(_nt("o"), _nt(a))))))


def _runner_up(a, b):
    return Not(Ex(Nb("w", "eq_has_actor"), "o", And(Not(Same("o", a)), Gt(_nt("o"), _nt(b)))))


FLOOR_RULES = [
    # batch-final turn counts (one atomic copy per batch, on the L1 frontier)
    rule("eq.quanta.interaction.floor.counts", [WIN, ["w", "eq_l1", "m"], AUTH], L(True),
         [["set_attr", "a", NTB, T(A("a", "eq_nturns"))]]),
    # held the floor: strictly more turns than every other actor (a tie mints nothing)
    rule("eq.quanta.interaction.floor.node", [WIN, ["w", "eq_has_actor", "a"]],
         And(enabled(L(FLOOR_T)), COUNTED, _floor_holds("a"), Not(Ex(Nb("a", "eq_floor_node"), "y"))),
         node_nm("q", "a", A("a", REF), L(FLOOR_T), L("+"), L(""), "eq_floor_node")),
    rule("eq.quanta.interaction.floor", [WIN, ["w", "eq_has_actor", "a"], ["a", "eq_floor_node", "q"]],
         And(enabled(L(FLOOR_T)), COUNTED, _floor_holds("a")),
         attach_nm("q", "a", "eq.quanta.interaction.floor")),
    rule("eq.quanta.interaction.floor.vanish", [WIN, ["a", "eq_nm_quantum", "q"]],
         And(trait_is("q", FLOOR_T), COUNTED, Not(_floor_holds("a"))),
         [["del_edge", "a", "eq_nm_quantum", "q"]]),
    # 0.7.0 evidence: the holder's FIRST turn (`eq_first_turn`, set once by the turn
    # cursor), on the permanent node -- a bounded anchor; the holder's turns are its
    # interaction.floor_share quantum (0.6.0: every turn of the holder)
    rule("eq.quanta.interaction.floor.evidence", [["a", "eq_floor_node", "q"], ["a", "eq_first_turn", "m"]],
         L(True), [["add_edge", "q", "eq_evidence", "m"], prov("q", "eq.quanta.interaction.floor.evidence")]),
    # counter: the turns of the runner(s)-up (no other non-holder has more turns)
    rule("eq.quanta.interaction.floor.ru", [WIN, ["a", "eq_nm_quantum", "q"], ["w", "eq_has_actor", "b"]],
         And(trait_is("q", FLOOR_T), COUNTED, Not(Same("a", "b")), _runner_up("a", "b")),
         [["add_edge", "q", "eq_floor_ru", "b"]]),
    rule("eq.quanta.interaction.floor_ru_drop", [WIN, ["a", "eq_floor_node", "q"], ["q", "eq_floor_ru", "b"]],
         And(COUNTED, Or(Not(In(V("q"), Nb("a", "eq_nm_quantum"))), Not(_runner_up("a", "b")))),
         [["del_edge", "q", "eq_floor_ru", "b"]]),
    # 0.7.0 counter: each runner-up's FIRST turn (0.6.0: every turn of every runner-up,
    # so a runner-up change rewrote O(turns) counter refs; now O(runners-up))
    rule("eq.quanta.interaction.floor.counter", [["q", "eq_floor_ru", "b"], ["b", "eq_first_turn", "m"]],
         L(True), [["add_edge", "q", "eq_counter_nm", "m"], prov("q", "eq.quanta.interaction.floor.counter")]),
    rule("eq.quanta.interaction.floor_counter_drop", [["q", "eq_counter_nm", "m"], ["m", "eq_authored_by", "b"]],
         Not(In(V("b"), Nb("q", "eq_floor_ru"))), [["del_edge", "q", "eq_counter_nm", "m"]]),
]

# -- selective non-response (equilibrium_quanta) ---------------------------------
def _engaged(qt, by=None):
    """eq-tax-0.8.0 Amendment A: qt has a decided-topic free-form contribution by another
    actor (`qt -eq_engaged_by-> c`, set by the turn cursor) -- by anyone (not
    unanswered), or by actor `by` (`by` responded to it)"""
    if by is not None:
        return In(V(by), Nb(qt, "eq_engaged_by"))
    return Ex(Nb(qt, "eq_engaged_by"), "en_" + qt)


RSP_RULES = [
    # b's question responding to a's turn, a posted LATER, and no turn by a responds to it
    # (Amendment A: nor is the question ENGAGED -- discussed under its topic)
    rule("eq.quanta.interaction.responsiveness.node", [["qt", "eq_rsp_due", "a"], ["qt", "eq_authored_by", "b"]],
         And(enabled(L(RSP_T)), Not(In(V("a"), Nb("qt", "eq_rsp_ans"))), Not(_engaged("qt", "a")),
             Not(Ex(Nb("a", "eq_rsp_node"), "y", Eq(A("y", "q_target"), A("b", REF))))),
         node_nm("q", "a", A("a", REF), L(RSP_T), L("-"), A("b", REF), "eq_rsp_node")
         + [["add_edge", "q", "eq_rsp_target", "b"]]),
    rule("eq.quanta.interaction.responsiveness",
         [["qt", "eq_rsp_due", "a"], ["qt", "eq_authored_by", "b"], ["a", "eq_rsp_node", "q"]],
         And(Eq(A("q", "q_target"), A("b", REF)), enabled(L(RSP_T)), Not(In(V("a"), Nb("qt", "eq_rsp_ans"))),
             Not(_engaged("qt", "a"))),
         attach_nm("q", "a", "eq.quanta.interaction.responsiveness") + [["add_edge", "q", "eq_evidence_nm", "qt"]]),
    # retraction, driven by the answer itself (never by a scan of the open evidence)
    rule("eq.quanta.interaction.responsiveness.retract",
         [["qt", "eq_rsp_ans", "a"], ["qt", "eq_authored_by", "b"], ["a", "eq_rsp_node", "q"],
          ["q", "eq_rsp_target", "b"]],
         L(True), [["del_edge", "q", "eq_evidence_nm", "qt"]]),
    # Amendment A: retraction driven by a's own engagement (a later topic contribution by a)
    rule("eq.quanta.interaction.responsiveness.retract_engaged",
         [["qt", "eq_engaged_by", "a"], ["qt", "eq_authored_by", "b"],
          ["a", "eq_rsp_node", "q"], ["q", "eq_rsp_target", "b"]],
         L(True), [["del_edge", "q", "eq_evidence_nm", "qt"]]),
    # counter: b's other questions to a that a DID answer (monotone, permanent node)
    rule("eq.quanta.interaction.responsiveness.counter",
         [["qt", "eq_rsp_ans", "a"], ["qt", "eq_authored_by", "b"], ["a", "eq_rsp_node", "q"]],
         Eq(A("q", "q_target"), A("b", REF)),
         [["add_edge", "q", "eq_counter", "qt"], prov("q", "eq.quanta.interaction.responsiveness.counter")]),
]
# 0.7.0 per-actor floor share (monotone, live L1): every turn is evidence of its
# author's interaction.floor_share quantum
FLOOR_SHARE_T = "interaction.floor_share"
FLOOR_SHARE_RULES = [
    rule("eq.quanta.interaction.floor_share", [WIN, ["w", "eq_l1", "m"], AUTH], enabled(L(FLOOR_SHARE_T)),
         mint("q", "a", A("a", REF), L(FLOOR_SHARE_T), L("+"), L(""), "eq.quanta.interaction.floor_share")
         + [["add_edge", "q", "eq_evidence", "m"]]),
]
# a non-monotone quantum whose open evidence emptied no longer exists
NM_VANISH = rule("eq.quanta.nm.vanish", [["a", "eq_nm_quantum", "q"]],
                 And(Or(trait_is("q", RSP_T), trait_is("q", UNANS_T)), Not(Ex(Nb("q", "eq_evidence_nm"), "xe"))),
                 [["del_edge", "a", "eq_nm_quantum", "q"]])

# -- inquiry.unanswered (equilibrium_climate) -------------------------------------
def _answered_by_edge(qt):
    """inquiry.answered mints a quantum with context qt exactly when it is enabled
    and some turn `eq_answers` qt (eq.quanta.inquiry.answered consumes that edge,
    the answer shape lives once in eq.trk.answers), so this IS `_answered(qt)` at
    the batch fixpoint -- read off the tracking edge, at the cursor step."""
    return And(enabled(L("inquiry.answered")), Ex(InNb(qt, "eq_answers"), "an_" + qt))


UNANS_RULES = [
    # S2 meaning: a question no answer closed, once another actor has posted after it
    rule("eq.quanta.inquiry.unanswered.node", [["qt", "eq_unans_due", "w"], ["qt", "eq_authored_by", "b"]],
         And(Not(_answered_by_edge("qt")), Not(_engaged("qt")), enabled(L(UNANS_T)),
             Not(Ex(Nb("b", "eq_unans_node"), "y"))),
         node_nm("q", "b", A("b", REF), L(UNANS_T), L("+"), L(""), "eq_unans_node")),
    rule("eq.quanta.inquiry.unanswered",
         [["qt", "eq_unans_due", "w"], ["qt", "eq_authored_by", "b"], ["b", "eq_unans_node", "q"]],
         And(Not(_answered_by_edge("qt")), Not(_engaged("qt")), enabled(L(UNANS_T))),
         attach_nm("q", "b", "eq.quanta.inquiry.unanswered") + [["add_edge", "q", "eq_evidence_nm", "qt"]]),
    rule("eq.quanta.inquiry.unanswered.retract",
         [["x", "eq_answers", "qt"], ["qt", "eq_authored_by", "b"], ["b", "eq_unans_node", "q"]],
         enabled(L("inquiry.answered")), [["del_edge", "q", "eq_evidence_nm", "qt"]]),
    # Amendment A: an ENGAGED question (a decided-topic contribution by another actor) is
    # not unanswered; the retraction is driven by the engagement mark
    rule("eq.quanta.inquiry.unanswered.retract_engaged",
         [["qt", "eq_engaged_by", "c"], ["qt", "eq_authored_by", "b"], ["b", "eq_unans_node", "q"]],
         L(True), [["del_edge", "q", "eq_evidence_nm", "qt"]]),
    rule("eq.quanta.inquiry.unanswered.counter", [["b", "eq_unans_node", "q"], ["qt", "eq_authored_by", "b"]],
         And(has("qt", QUESTION), _answered_by_edge("qt")),
         [["add_edge", "q", "eq_counter", "qt"], prov("q", "eq.quanta.inquiry.unanswered.counter")]),
]

# -- corroboration / contest with BOUNDED claim state (0.7.0; equilibrium_competence) ----
# 0.6.0 paired every reply with EVERY earlier claim of the addressed actor (O(claims)
# per reply). The relation is unchanged -- E(corroborated, a) = {claims of a followed
# by a later concession / deference addressed to a} + {such replies preceded by a
# claim of a}; E(contested, a, b) likewise per replier b -- but it is now derived
# from bounded per-actor / per-(actor, replier) state:
#   a -eq_claim_first-> m   a's earliest claim (replace-if-earlier: converges in-batch)
#   a -eq_corr_last-> m     the latest corroborating reply addressed to a
#   a -eq_claim_open-> m    a's claims with no later corroborating reply yet
#   q -eq_ct_last-> m       (q = contested(a, b)) b's latest contest of a
#   q -eq_ct_open-> m       a's claims not yet in q's evidence
# A reply is evidence iff it is later than a's first claim (O(1)); a claim is evidence
# iff it is earlier than the latest reply, read off the OPEN claims only, each of which
# closes once (amortised O(1) per claim and pair). Seeding a new (a, b) pair with a's
# earlier claims is O(claims) once per pair -- exactly the refs its first upsert
# carries on the wire.
CORR_CUE = (lab("msg.concession"), lab("msg.deference"))
CORR_T, CT_T = "competence.corroborated", "competence.contested"
CLAIM_E = [["a", "eq_has_quantum", "qc"], ["qc", "eq_evidence", "m1"]]
# a claim turn of THIS batch (L1 frontier): earlier claims never change the first claim
# and are already open / evidence
NEW_CLAIM = [WIN, ["w", "eq_l1", "m1"]] + CLAIM_E
REPLY_TO_A = [WIN, ["w", "eq_l1", "m2"], ["m2", "eq_addresses", "a"]]


def _contest(m):
    return And(has(m, lab("msg.reply_contrast")), _any(m, GROUNDED_KEYS))


CORR_RULES = [
    rule("eq.competence.claim_first.set", NEW_CLAIM, And(CLAIMED, Not(Ex(Nb("a", "eq_claim_first"), "cf"))),
         [["add_edge", "a", "eq_claim_first", "m1"]]),
    rule("eq.competence.claim_first.earlier", NEW_CLAIM + [["a", "eq_claim_first", "x"]],
         And(CLAIMED, Lt(A("m1", POS), A("x", POS))),
         [["del_edge", "a", "eq_claim_first", "x"], ["add_edge", "a", "eq_claim_first", "m1"]]),
    # corroborated
    rule("eq.competence.corr_last.set", REPLY_TO_A,
         And(_any("m2", CORR_CUE), Not(Ex(Nb("a", "eq_corr_last"), "cl"))),
         [["add_edge", "a", "eq_corr_last", "m2"]]),
    rule("eq.competence.corr_last.later", REPLY_TO_A + [["a", "eq_corr_last", "x"]],
         And(_any("m2", CORR_CUE), Gt(A("m2", POS), A("x", POS))),
         [["del_edge", "a", "eq_corr_last", "x"], ["add_edge", "a", "eq_corr_last", "m2"]]),
    rule("eq.competence.corroborated.reply", REPLY_TO_A + [["a", "eq_claim_first", "f"]],
         And(_any("m2", CORR_CUE), enabled(L(CORR_T)), Gt(A("m2", POS), A("f", POS))),
         mint("q", "a", A("a", REF), L(CORR_T), L("+"), L(""), "eq.competence.corroborated")
         + [["add_edge", "q", "eq_evidence", "m2"]]),
    # a new claim with no later corroborating reply (yet) is OPEN; one that already has
    # one is evidence at once; an open claim closes when a later reply arrives
    rule("eq.competence.claim_open.corr", NEW_CLAIM,
         And(CLAIMED, Not(Ex(Nb("a", "eq_corr_last"), "cx", Gt(A("cx", POS), A("m1", POS))))),
         [["add_edge", "a", "eq_claim_open", "m1"]]),
    rule("eq.competence.corroborated.claim_new", NEW_CLAIM + [["a", "eq_corr_last", "x"]],
         And(CLAIMED, Lt(A("m1", POS), A("x", POS)), enabled(L(CORR_T))),
         mint("q", "a", A("a", REF), L(CORR_T), L("+"), L(""), "eq.competence.corroborated")
         + [["add_edge", "q", "eq_evidence", "m1"]]),
    rule("eq.competence.corroborated.claim", [WIN, ["a", "eq_claim_open", "m1"], ["a", "eq_corr_last", "x"]],
         And(Lt(A("m1", POS), A("x", POS)), enabled(L(CORR_T))),
         mint("q", "a", A("a", REF), L(CORR_T), L("+"), L(""), "eq.competence.corroborated")
         + [["add_edge", "q", "eq_evidence", "m1"], ["del_edge", "a", "eq_claim_open", "m1"]]),
    # contested (per replier b = the quantum's target)
    rule("eq.competence.contested.reply", REPLY_TO_A + [["m2", "eq_authored_by", "b"], ["a", "eq_claim_first", "f"]],
         And(_contest("m2"), enabled(L(CT_T)), Gt(A("m2", POS), A("f", POS))),
         mint("q", "a", A("a", REF), L(CT_T), L("+"), A("b", REF), "eq.competence.contested")
         + [["add_edge", "q", "eq_evidence", "m2"]]),
    rule("eq.competence.ct_last.set",
         REPLY_TO_A + [["m2", "eq_authored_by", "b"], ["a", "eq_has_quantum", "q"]],
         And(trait_is("q", CT_T), Eq(A("q", "q_target"), A("b", REF)), _contest("m2"),
             Not(Ex(Nb("q", "eq_ct_last"), "cl"))),
         [["add_edge", "q", "eq_ct_last", "m2"]]),
    rule("eq.competence.ct_last.later",
         REPLY_TO_A + [["m2", "eq_authored_by", "b"], ["a", "eq_has_quantum", "q"], ["q", "eq_ct_last", "x"]],
         And(trait_is("q", CT_T), Eq(A("q", "q_target"), A("b", REF)), _contest("m2"),
             Gt(A("m2", POS), A("x", POS))),
         [["del_edge", "q", "eq_ct_last", "x"], ["add_edge", "q", "eq_ct_last", "m2"]]),
    rule("eq.competence.claim_open.ct", [["a", "eq_has_quantum", "q"]] + CLAIM_E,
         And(CLAIMED, trait_is("q", CT_T), Not(In(V("m1"), Nb("q", "eq_evidence")))),
         [["add_edge", "q", "eq_ct_open", "m1"]]),
    rule("eq.competence.contested.claim", [WIN, ["q", "eq_ct_open", "m1"], ["q", "eq_ct_last", "x"]],
         And(Lt(A("m1", POS), A("x", POS)), enabled(L(CT_T))),
         [["add_edge", "q", "eq_evidence", "m1"], prov("q", "eq.competence.contested"),
          ["del_edge", "q", "eq_ct_open", "m1"]]),
]

# -- claim grounding (equilibrium_competence) -------------------------------------
CG_RULES = [
    # a holds a grounding quantum (demonstrated / acknowledged / corroborated): permanent
    rule("eq.competence.grounded", [["a", "eq_has_quantum", "g"]], _grounding("g"),
         [["add_edge", "a", "eq_cg_grounded", "g"]]),
    # '+' (monotone): its node is created once, attached by the first evidence
    rule("eq.competence.claim_grounding.node_pos", [["a", "eq_has_quantum", "qc"], ["a", "eq_cg_grounded", "g"]],
         And(CLAIMED, enabled(L(CG_T)), Not(Ex(Nb("a", "eq_cg_pos_node"), "y"))),
         node_nm("q", "a", A("a", REF), L(CG_T), L("+"), L(""), "eq_cg_pos_node")),
    rule("eq.competence.claim_grounding.grounded_claim", CLAIM + [["a", "eq_cg_pos_node", "q"]],
         And(CLAIMED, enabled(L(CG_T)), Ex(Nb("a", "eq_cg_grounded"), "g")),
         [["add_edge", "a", "eq_has_quantum", "q"], prov("q", "eq.competence.claim_grounding.grounded_claim"),
          ["add_edge", "q", "eq_evidence", "m1"]]),
    rule("eq.competence.claim_grounding.grounding",
         [["a", "eq_has_quantum", "qc"], ["a", "eq_cg_grounded", "g"], ["g", "eq_evidence", "m2"],
          ["a", "eq_cg_pos_node", "q"]],
         And(CLAIMED, enabled(L(CG_T))),
         [["add_edge", "a", "eq_has_quantum", "q"], prov("q", "eq.competence.claim_grounding.grounding"),
          ["add_edge", "q", "eq_evidence", "m2"]]),
    # '-': claimed and NONE of demonstrated / acknowledged / corroborated (retired for good
    # once a grounding quantum appears)
    rule("eq.competence.claim_grounding.node_neg", CLAIM,
         And(CLAIMED, enabled(L(CG_T)), Not(Ex(Nb("a", "eq_cg_grounded"), "g")),
             Not(Ex(Nb("a", "eq_cg_neg_node"), "y"))),
         node_nm("q", "a", A("a", REF), L(CG_T), L("-"), L(""), "eq_cg_neg_node")),
    rule("eq.competence.claim_grounding.ungrounded", CLAIM + [["a", "eq_cg_neg_node", "q"]],
         And(CLAIMED, enabled(L(CG_T)), Not(Ex(Nb("a", "eq_cg_grounded"), "g"))),
         attach_nm("q", "a", "eq.competence.claim_grounding.ungrounded") + [["add_edge", "q", "eq_evidence", "m1"]]),
    rule("eq.competence.claim_grounding.ungrounded.vanish", [["a", "eq_nm_quantum", "q"], ["a", "eq_cg_grounded", "g"]],
         And(trait_is("q", CG_T), Eq(A("q", "q_pole"), L("-"))), [["del_edge", "a", "eq_nm_quantum", "q"]]),
]

# -- generative outcome + facet match (equilibrium_episode) ---------------------------
RES, ESC = InNb("e", "eq_ep_res"), InNb("e", "eq_ep_esc")
_RESOLVED = Ex(RES, "rm", Not(Ex(ESC, "xm", Gt(A("xm", POS), A("rm", POS)))))
GEN_LIVE = [WIN, ["w", "eq_has_episode", "e"]]
GR, GX = "eq.ep.generative.resolved", "eq.ep.generative.escalated"
FXL = [WIN, ["w", "eq_has_episode", "e"], ["e", "eq_has_facet", "fx"]]
EP_NM_RULES = [
    # episode growth + etiology facets (monotone; were live L1 rules re-driven over
    # every membership by the `eq_l1_open` gate each batch): a turn's extend role /
    # facet cues are marked once, on the L1 frontier, and the membership rules read
    # the marks (no dynamic attr look-up, no gate)
    rule("eq.ep.extend.turn", [WIN, ["w", "eq_l1", "x"]], _cue_role("x", "extend"),
         [["add_edge", "x", "eq_cue_extend", "w"]]),
    rule("eq.ep.extend", [["x", "eq_cue_extend", "w"], ["x", "eq_responds_to", "y"], ["y", "eq_in_episode", "e"]],
         L(True), [["add_edge", "x", "eq_in_episode", "e"], prov("e", "eq.ep.extend")]),
    rule("eq.ep.facet.turn", [WIN, ["w", "eq_l1", "m"], ["agent", "eq_has_facet_cue", "f"]],
         And(Eq(ABN("m", A("f", "lab_key")), L(True)), enabled(A("f", "status_label"))),
         [["add_edge", "m", "eq_fx_cue", "f"]]),
    rule("eq.ep.facet.node", [["w", "eq_has_episode", "e"], ["m", "eq_in_episode", "e"], ["m", "eq_fx_cue", "f"]],
         Not(Ex(Nb("e", "eq_has_facet"), "y", Eq(A("y", "fx_code"), A("f", "code")))),
         [["add_node_if_absent", "fx", "EqEpFacet", {"fx_ep": T(V("e")), "fx_code": T(A("f", "code"))}],
          ["add_edge", "e", "eq_has_facet", "fx"]]),
    rule("eq.ep.facet", [["w", "eq_has_episode", "e"], ["m", "eq_in_episode", "e"], ["m", "eq_fx_cue", "f"],
                         ["e", "eq_has_facet", "fx"]],
         Eq(A("fx", "fx_code"), A("f", "code")),
         [["add_edge", "fx", "eq_evidence", "m"], prov("e", "eq.ep.facet")]),
    # a turn's resolve / escalate cue role, once, on the L1 frontier (dynamic cue
    # look-up there only; the membership marks below read the mark edge)
    *[rule(f"eq.ep.gen.{role}_turn", [WIN, ["w", "eq_l1", "m"]], _cue_role("m", role),
           [["add_edge", "m", f"eq_cue_{role}", "w"]]) for role in ("resolve", "escalate")],
    *[rule(f"eq.ep.gen.{role}_member", [["e", "eq_root", "r"], ["m", "eq_in_episode", "e"], ["m", f"eq_cue_{role}", "w"]],
           Gt(A("m", POS), A("r", POS)), [["add_edge", "m", edge, "e"]])
      for role, edge in (("resolve", "eq_ep_res"), ("escalate", "eq_ep_esc"))],
    rule(GR, GEN_LIVE, _RESOLVED,
         [["set_attr", "e", "ep_generative", True], prov("e", GR), unset("e", GX)]),
    rule(GX, GEN_LIVE, And(Ex(ESC, "xm"), Not(Ex(RES, "rm"))),
         [["set_attr", "e", "ep_generative", False], prov("e", GX), unset("e", GR)]),
    # a resolution later escalated again: neither outcome (null = default)
    rule("eq.ep.generative.reopened", GEN_LIVE, And(Ex(RES, "rm"), Not(_RESOLVED)),
         [["set_attr", "e", "ep_generative", None], unset("e", GR), unset("e", GX)]),
    rule("eq.ep.facet_match.exact", FXL, _FX_EXACT, _fx_match("exact")),
    rule("eq.ep.facet_match.partial", FXL, And(Gt(Count(FX_E), Count(FX_C)), Not(_FX_EXACT)), _fx_match("partial")),
    rule("eq.ep.facet_match.weak", FXL, Not(Gt(Count(FX_E), Count(FX_C))), _fx_match("weak")),
    *[rule(f"eq.ep.facet_match.{v}.clear", GEN_LIVE,
           And(Eq(A("e", f"eqrule:eq.ep.facet_match.{v}"), L(True)),
               Not(Ex(Nb("e", "eq_has_facet"), "f", Eq(A("f", "eq_match"), L(v))))),
           [unset("e", f"eq.ep.facet_match.{v}")])
      for v in ("exact", "partial", "weak")],
]


# -- match shapes (equilibrium_quanta) --------------------------------------------
def _shape_rules(qm, ev, ctr, sfx):
    """exact / partial / weak / weak_by_construction over quanta matched by `qm`
    with evidence set `ev` and counter set `ctr`; each clears its siblings."""
    ex = And(Gt(Count(ev), singleton(ev)), Not(Ex(ctr, "x")), Not(Ex(H, "x")))
    ow = Gt(Count(ev), Count(ctr))
    plain = ("eq.quanta.match.exact", "eq.quanta.match.partial", "eq.quanta.match.weak")

    def sw(name, value):
        return [["set_attr", "q", "eq_match", value], prov("q", name)] + [unset("q", o) for o in plain if o != name]
    return [
        rule(plain[0] + sfx, qm, And(_PLAIN, ex), sw(plain[0], "exact")),
        rule(plain[1] + sfx, qm, And(_PLAIN, ow, Not(ex)), sw(plain[1], "partial")),
        rule(plain[2] + sfx, qm, And(_PLAIN, Ex(ev, "x"), Not(ow)), sw(plain[2], "weak")),
        rule("eq.quanta.match.weak_by_construction" + sfx, qm,
             And(trait_is("q", CG_T), Eq(A("q", "q_pole"), L("-"))),
             _set_match("q", "eq.quanta.match.weak_by_construction", "weak")),
        # 0.7.0: the floor holds iff the holder's share strictly outweighs every other
        # actor's (each of which is non-empty): the generic `partial` shape over the
        # shares. 0.6.0 derived exactly that from the full lists (every 0.6.0 floor
        # quantum was partial); with bounded anchors it is set by construction.
        rule("eq.quanta.match.partial_by_construction" + sfx, qm, trait_is("q", FLOOR_T),
             _set_match("q", "eq.quanta.match.partial_by_construction", "partial")),
    ]


QLIVE = [WIN, ["w", "eq_has_actor", "a"], ["a", "eq_has_quantum", "q"]]
# 0.7.0: a roster participant who has not spoken can hold a (monotone) quantum, e.g.
# competence.acknowledged from a concession addressed to it by name
QPART = [WIN, ["w", "eq_has_participant", "a"], ["a", "eq_has_quantum", "q"]]
QNM = [WIN, ["w", "eq_has_actor", "a"], ["a", "eq_nm_quantum", "q"]]
_CMP = ("eq.quanta.match.composite_exact", "eq.quanta.match.composite_weak", "eq.quanta.match.composite_partial")


def _csw(name, value):
    return _set_match("q", name, value) + [unset("q", o) for o in _CMP if o != name]


QCOMP = QLIVE + [["q", "eq_component", "x0"]]
MATCH_NM_RULES = (
    _shape_rules(QLIVE, E, C, "")
    + _shape_rules(QPART, E, C, ".participant")
    + _shape_rules(QNM, Union(E, Nb("q", "eq_evidence_nm")), Union(C, Nb("q", "eq_counter_nm")), ".nm")
    + [rule(_CMP[0], QCOMP, And(Eq(A("q", "q_composite"), L(True)),
                                Not(Ex(COMP, "x", Not(Eq(A("x", "eq_match"), L("exact")))))), _csw(_CMP[0], "exact")),
       rule(_CMP[1], QCOMP, And(Eq(A("q", "q_composite"), L(True)), Ex(COMP, "x", Eq(A("x", "eq_match"), L("weak")))),
            _csw(_CMP[1], "weak")),
       rule(_CMP[2], QCOMP, And(Eq(A("q", "q_composite"), L(True)),
                                Ex(COMP, "x", Not(Eq(A("x", "eq_match"), L("exact")))),
                                Not(Ex(COMP, "x", Eq(A("x", "eq_match"), L("weak"))))), _csw(_CMP[2], "partial"))])

# composites over the (monotone) live quanta: the same rules without a stratum anchor
COMPOSE_LIVE = [dict(r, match=[e for e in r["match"] if not e[1].startswith("eq_stratum_")])
                for r in QUANTA_RULES if r["name"] in ("eq.quanta.compose", "eq.quanta.compose.evidence")]
# the scratch-fork rules these replace (same provenance names)
NM_REPLACED = frozenset(
    {"eq.quanta.interaction.floor", "eq.quanta.interaction.floor.evidence", "eq.quanta.interaction.floor.counter",
     "eq.quanta.interaction.responsiveness", "eq.quanta.interaction.responsiveness.counter",
     "eq.quanta.inquiry.unanswered", "eq.quanta.inquiry.unanswered.counter",
     "eq.competence.claim_grounding.grounded_claim", "eq.competence.claim_grounding.grounding",
     "eq.competence.claim_grounding.ungrounded", "eq.ep.generative.resolved", "eq.ep.generative.escalated",
     "eq.ep.facet_match.exact", "eq.ep.facet_match.partial", "eq.ep.facet_match.weak",
     "eq.quanta.compose", "eq.quanta.compose.evidence", "eq.ep.extend", "eq.ep.facet",
     "eq.competence.corroborated", "eq.competence.contested"}
    | {r["name"] for r in MATCH_RULES})
NM_PACK = {"quanta": FLOOR_RULES + FLOOR_SHARE_RULES + RSP_RULES + [NM_VANISH] + COMPOSE_LIVE + MATCH_NM_RULES,
           "competence": CORR_RULES + CG_RULES,
           "episode": EP_NM_RULES, "climate": UNANS_RULES}
NM_EDGE_TYPES = [
    ("Message", "eq_counted", "EqActor"), ("EqWindow", "eq_unans_wait", "Message"),
    ("Message", "eq_unans_due", "EqWindow"), ("EqActor", "eq_rsp_wait", "Message"),
    ("Message", "eq_rsp_due", "EqActor"), ("Message", "eq_rsp_ans", "EqActor"),
    ("EqActor", "eq_nm_quantum", "EqQuantum"), ("EqActor", "eq_floor_node", "EqQuantum"),
    ("EqActor", "eq_rsp_node", "EqQuantum"), ("EqActor", "eq_unans_node", "EqQuantum"),
    ("EqActor", "eq_cg_grounded", "EqQuantum"), ("EqQuantum", "eq_evidence_nm", "Message"),
    ("EqQuantum", "eq_counter_nm", "Message"), ("EqQuantum", "eq_floor_ru", "EqActor"),
    ("Message", "eq_ep_res", "EqEpisode"), ("Message", "eq_ep_esc", "EqEpisode"),
    ("EqQuantum", "eq_rsp_target", "EqActor"), ("Message", "eq_cue_resolve", "EqWindow"),
    ("Message", "eq_cue_extend", "EqWindow"), ("Message", "eq_fx_cue", "EqFacetCue"), ("Message", "eq_cue_escalate", "EqWindow"),
    ("EqActor", "eq_cg_pos_node", "EqQuantum"), ("EqActor", "eq_cg_neg_node", "EqQuantum"),
    # 0.7.0: floor anchors; bounded corroboration / contest state
    ("EqActor", "eq_first_turn", "Message"), ("EqActor", "eq_claim_first", "Message"),
    ("EqActor", "eq_corr_last", "Message"), ("EqActor", "eq_claim_open", "Message"),
    ("EqQuantum", "eq_ct_last", "Message"), ("EqQuantum", "eq_ct_open", "Message")]


def _bind_agent(r):
    """A rule reading the agent's codebooks (cue roles, label status) binds `agent`
    through the window edge (the scratch rules bound it through the stratum anchor)."""
    bound = {v for e in r["match"] for v in (e[0], e[2])}
    if "agent" in bound or '"agent"' not in json.dumps([r["where"], r["effects"]]):
        return r
    return dict(r, match=[WIN] + r["match"])


def apply_nm(rules, pack):
    """Replace a pack's scratch-fork rules by their live non-monotone successors; the
    tracking pack gets the cursor rules inserted before `eq.trk.release`."""
    if pack == "tracking":
        i = [r["name"] for r in rules].index("eq.trk.release")
        return rules[:i] + TRK_NM_RULES + rules[i:]
    kept = [r for r in rules if r["name"] not in NM_REPLACED]
    assert not any(e[0] == "agent" and e[1].startswith("eq_stratum_") for r in kept for e in r["match"]), \
        "a scratch-stratum rule is left without a live successor"
    return kept + [_bind_agent(r) for r in NM_PACK.get(pack, [])]


def check_nm_pack():
    """Pack CONDITION of the live non-monotone families (see above)."""
    assert not any(t in NM_TRAITS for t, *_ in TRAIT_CUES), "a cue row names a non-monotone trait"
    assert not any(r[0] == "EqTraitCompose" for r in trait_items()), "compose rows need a check"
