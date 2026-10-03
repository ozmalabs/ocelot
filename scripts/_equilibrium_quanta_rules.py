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
# stratification by turn order, so a turn's tracked structure is causal (never
# revised by later turns) and incremental batches == one shot by construction.
#
# Conversation state (graph-resident, mutated only by these rules):
#   w -eq_qud-> q               open-question set (QUD): q is a question turn not
#                               yet answered; its addressees are q's eq_addresses
#                               edges, none = the room
#   b -eq_pending-> x           x addressed actor b and b has not taken a turn since
#   b -eq_last_addressed_by-> x the most recent turn by another actor addressing b
#                               (second-person resolution)
#   a -eq_last_claim-> x        a's most recent claim (assertion / directive) turn
SECOND_PERSON = ("you", "your", "yours", "yourself", "yourselves", "you're", "you've",
                 "you'll", "you'd", "ya", "y'all")
TRACKING_ITEMS = [("EqSecondPerson", {"form": f}) for f in SECOND_PERSON]
TRACKING_EDGE = {"EqSecondPerson": "eq_has_second_person"}
CUR = ["w", "eq_trk_cur", "m"]
CLAIM_LABS = (ASSERTION, DIRECTIVE)


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


def _newer_qud(x, a, m, b):
    """a strictly more recent compatible OPEN QUESTION exists (in the same addressee
    group when m names addressees): x is then not the target."""
    return Ex(Nb("w", "eq_qud"), "yq", And(Gt(A("yq", POS), A(x, POS)), _qud_for("yq", a),
                                          _open_item("yq", a, m, b)))


def _any_qud(a, m, b):
    """some compatible open question exists for m's author (QUD precedence: a
    pending address is a target only when no question is open for the author)."""
    return Ex(Nb("w", "eq_qud"), "zq", And(_qud_for("zq", a), _open_item("zq", a, m, b)))


def _newer_pending(x, a, m, b):
    return Ex(Nb(a, "eq_pending"), "yp", And(Gt(A("yp", POS), A(x, POS)), _open_item("yp", a, m, b)))


def _leads_with_contrast(m):
    return Ex(Nb(m, "eq_has_token"), "lt", And(
        Not(Ex(Nb(m, "eq_has_token"), "lk", Lt(A("lk", "eq_pos"), A("lt", "eq_pos")))),
        Ex(Nb("agent", "eq_has_coh_marker"), "lc",
           And(Eq(A("lc", "rel"), L("contrast")), Eq(A("lc", "form"), A("lt", "form"))))))


UNDECLARED = Eq(A("m", "eq_reply_to_ref"), L(None))
# (the target's author becomes an addressee only AFTER every T3 rule ran, so the
# three target rules all read the same T1/T2 addressee set)
# The sweep writes the target as `eq_trk_to` (read by the later phases of the same
# turn); `eq.trk.materialise` turns it into `eq_responds_to` + basis "tracked" once
# the whole queue is swept. (Engine cost, not semantics: writing eq_responds_to per
# turn re-enumerates every reply-pair msg rule on every cursor pass.)
TRACKED_FX = [["add_edge", "m", "eq_trk_to", "x"]]

TRACKING_RULES = [
    # ordering-only continuation: consecutive turns by the same actor (interaction.run)
    rule("eq.trk.continues", [WIN, TURN, ["m", "eq_prev_turn", "p"], AUTH, ["p", "eq_authored_by", "a"]],
         L(True), [["add_edge", "m", "eq_continues", "p"]]),
    # T0 cursor: the earliest queued turn becomes current once no turn is current
    rule("eq.trk.cursor", [WIN, ["w", "eq_trk_pending", "m"]],
         And(Not(Ex(Nb("w", "eq_trk_cur"), "c")),
             Not(Ex(Nb("m", "eq_prev_turn"), "y", In(V("y"), Nb("w", "eq_trk_pending"))))),
         [["add_edge", "w", "eq_trk_cur", "m"], ["del_edge", "w", "eq_trk_pending", "m"]]),
    # T1 explicit address: a token equal to the name form of an actor who has
    # already spoken (actor_ref supplied by the platform; no identity guessing)
    rule("eq.trk.addressee.mention",
         [WIN, CUR, AUTH, ["m", "eq_has_token", "t"], ["w", "eq_has_actor", "b"]],
         And(Eq(A("t", "form"), A("b", "eq_name_form")), Not(Same("a", "b")),
             Lt(A("b", "eq_first_pos"), A("m", POS))),
         [["add_edge", "m", "eq_addresses", "b"]]),
    # T2 second-person address with no explicit addressee: the last speaker who
    # addressed this actor
    rule("eq.trk.addressee.second_person",
         [WIN, CUR, AUTH, ["a", "eq_last_addressed_by", "x"], ["x", "eq_authored_by", "b"]],
         And(Not(_addressed_any("m")), Not(Same("a", "b")),
             Ex(Nb("m", "eq_has_token"), "t2", Ex(Nb("agent", "eq_has_second_person"), "sp",
                                                  Eq(A("sp", "form"), A("t2", "form"))))),
         [["add_edge", "m", "eq_addresses", "b"]]),
    # T3 tracked responds_to (only when the platform declared no reply): the most
    # recent compatible open item addressed to the author or the room -- an open
    # question (QUD first: once a counter-question closes, the question under it is
    # the top again), else the most recent pending address to the author; one per
    # named addressee, else one overall
    rule("eq.trk.responds.open_question",
         [WIN, CUR, AUTH, ["w", "eq_qud", "x"], ["x", "eq_authored_by", "b"]],
         And(UNDECLARED, Not(Same("a", "b")), _qud_for("x", "a"), _compat("m", "x", "b"),
             Not(_newer_qud("x", "a", "m", "b"))),
         TRACKED_FX),
    rule("eq.trk.responds.pending_address",
         [WIN, CUR, AUTH, ["a", "eq_pending", "x"], ["x", "eq_authored_by", "b"]],
         And(UNDECLARED, Not(Same("a", "b")), _compat("m", "x", "b"),
             Not(_any_qud("a", "m", "b")), Not(_newer_pending("x", "a", "m", "b"))),
         TRACKED_FX),
    # ... or a claim the turn contrasts with / concedes / disagrees with (existing
    # contrast-marker + concession / disagreement cue machinery): the most recent
    # claim by another actor
    rule("eq.trk.responds.claim",
         [WIN, CUR, AUTH, ["w", "eq_has_actor", "b"], ["b", "eq_last_claim", "x"]],
         And(UNDECLARED, Not(Same("a", "b")), _compat("m", "x", "b"),
             Or(_leads_with_contrast("m"), has("m", lab("msg.concession")),
                has("m", lab("msg.disagreement"))),
             Not(Ex(Nb("w", "eq_has_actor"), "c", And(Not(Same("c", "a")), Ex(
                 Nb("c", "eq_last_claim"), "z",
                 And(Gt(A("z", POS), A("x", POS)), _compat("m", "z", "c"))))))),
         TRACKED_FX),
    rule("eq.trk.addressee.target", [WIN, CUR, AUTH, ["m", "eq_trk_to", "x"], ["x", "eq_authored_by", "b"]],
         Not(Same("a", "b")),
         [["add_edge", "m", "eq_addresses", "b"]]),
    # T4 answers (declared OR tracked responds_to): an answer-type turn by another
    # actor -- counter-questions / withdrawals (nonanswer) and dismissals do not close
    *[rule(f"eq.trk.answers.{basis}",
           [WIN, CUR, AUTH, ["m", edge, "p"], ["p", "eq_authored_by", "b"]],
           And(Not(Same("a", "b")), has("p", QUESTION), Gt(A("m", POS), A("p", POS)),
               Not(_cc("m", "nonanswer")), Not(_dismissive("m"))),
           [["add_edge", "m", "eq_answers", "p"]])
      for basis, edge in (("declared", "eq_responds_to"), ("tracked", "eq_trk_to"))],
    # T5 state update for the turns after this one
    rule("eq.trk.qud.close", [WIN, CUR, ["m", "eq_answers", "p"], ["w", "eq_qud", "p"]], L(True),
         [["del_edge", "w", "eq_qud", "p"]]),
    rule("eq.trk.qud.open", [WIN, CUR], has("m", QUESTION), [["add_edge", "w", "eq_qud", "m"]]),
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
    # thread id: the platform thread (S0), else the thread of the EARLIEST parent
    # (declared reply_to, any author, or tracked target; every earlier turn already
    # has its thread), else the turn roots its own thread
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
    # once the queue is swept: tracked targets become responds_to (basis tracked)
    rule("eq.trk.materialise", [WIN, TURN, ["m", "eq_trk_to", "x"]],
         And(Not(Ex(Nb("w", "eq_trk_cur"), "c")), Not(Ex(Nb("w", "eq_trk_pending"), "q"))),
         [["add_edge", "m", "eq_responds_to", "x"], ["set_attr", "m", "eq_basis", "tracked"]]),
]
TRACKING_EDGE_TYPES = [
    ("Agent", "eq_has_second_person", "EqSecondPerson"),
    ("Message", "eq_prev_turn", "Message"), ("Message", "eq_trk_to", "Message"), ("Message", "eq_continues", "Message"),
    ("EqWindow", "eq_trk_pending", "Message"), ("EqWindow", "eq_trk_cur", "Message"),
    ("EqWindow", "eq_qud", "Message"), ("EqActor", "eq_pending", "Message"),
    ("EqActor", "eq_last_addressed_by", "Message"), ("EqActor", "eq_last_claim", "Message"),
]
