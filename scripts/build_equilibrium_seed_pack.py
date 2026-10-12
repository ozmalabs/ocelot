#!/usr/bin/env python3
"""Build the Equilibrium seed pack (0.8.0, tracks T3 + T3b + T3c + T3d + T3e + T3f + T3g) as flat seed manifests.

    PYTHONPATH=.:runners/dsl/python OZMA_NO_LLM=1 python3 scripts/build_equilibrium_seed_pack.py

Writes seeds/equilibrium_{tokens,window,lexicon,scope,msg,pattern,traits,quanta,
competence,episode,climate,label_status}.json.
BUILD-TIME ONLY: this script authors graph data; it is not on the request path.

* Codebook nodes (EqCue, EqScopeOp/EqScopeBoundary/EqCohMarker, EqStratum,
  EqTrait/EqTraitCue, EqEpisodeCue/EqFacetCue) are minted through the `teach`
  facility (CLAUDE.md "Teaching the agent -> seeds") on a scratch substrate into
  a temp seeds_dir; the export step stamps the pack header (version /
  self_load_only / depends_on) and wires each taught node to the agent root so
  seeded rules can reach the vocabulary by a match edge.
* Rules decide every label; each msg rule writes `eqfire:<rule name>` = <label
  value> on the Message (mint-once guard: that attr is null) plus the label-level
  `eqlab:<label>[=<value>]` attr the quanta layer joins on. The adapter reads the
  eqfire attrs back mechanically and appends `@<pack_version>`.
* 0.3.0 cue recognition (design §5): formula cue sets match token `form`,
  technical vocabulary matches token `lemma` (cue words normalised by the SAME
  adapter function), class slots (`<num>`, `<noun.person>`, `<noun.group>`)
  match the token class. Negation-sensitive ("scoped") cue sets no longer decide
  the label directly: the n-gram rule marks a HIT on the head token, and the
  scope rules (seeds/equilibrium_scope.json codebook) decide affirmed /
  negated / hedged.
"""
from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SEEDS = ROOT / "seeds"
PACK_VERSION = "0.8.0"
TAXONOMY_VERSION = "eq-tax-0.8.0"
NUM = "<num>"            # token class slot: any all-digit prose token
PERSON = "<noun.person>"  # token class slot: first-sense WordNet noun lexname
GROUP = "<noun.group>"
TOKEN_CLASSES = (NUM, PERSON, GROUP)

import _equilibrium_quanta_rules as qr  # noqa: E402  (build-time Rule JSON assembly)
from _equilibrium_quanta_rules import A, L, Eq, Not, And, Or, lab  # noqa: E402


def rule(name, match, conds, value):
    """Direct label rule (v0 shape): mint-once eqfire + label-level eqlab attr."""
    fire = f"eqfire:{name}"
    label = name[len("eq."):].rsplit(".", 1)[0]
    return {"name": name, "match": match,
            "where": And(Eq(A("m", fire), L(None)), *conds),
            "effects": [["set_attr", "m", fire, value], ["set_attr", "m", lab(label, value), True]]}


RECV = ["agent", "received", "m"]
MSG = "eq.msg"

# ---- equilibrium_msg rules -------------------------------------------------
# speech_act: Ocelot sak_kind (seeds/speech_act_classify.json) -> Equilibrium act
# (design §1.1): question->question, statement->assertion, instruction->directive.
SAK_MAP = [("question", "question"), ("statement", "assertion"), ("instruction", "directive")]
# T3h: a clause the syntax marks interrogative (qr.interrogative_rule: subject-aux
# inversion, wh + inverted auxiliary, tag; `m.eq_interrogative`) is a question even when the
# ladder (typed '?' / first parsed element) did not call it one -- speech transcripts carry
# no '?'. The ladder's assertion / directive then do not fire (one speech act per turn).
# The mark rule runs FIRST in the pass (rules apply in order), so every speech-act rule
# reads its final value. Only where the ladder did not already call it a question: a typed
# / ladder question keeps exactly its 0.8.0 provenance.
INTERROGATIVE = Eq(A("m", qr.INTERROG_ATTR), L(True))
RULES = [qr.interrogative_rule(f"{MSG}.speech_act.interrogative_mark")]
RULES += [rule(f"{MSG}.speech_act.sak_{k}", [RECV],
               [Eq(A("m", "sak_kind"), L(k))] + ([] if k == "question" else [Not(INTERROGATIVE)]), act)
          for k, act in SAK_MAP]
RULES += [rule(f"{MSG}.speech_act.interrogative", [RECV],
               [Not(Eq(A("m", "sak_kind"), L("question"))), INTERROGATIVE], "question")]
RULES += [
    rule(f"{MSG}.substantive_markers.question_act", [RECV],
         [Or(Eq(A("m", f"eqfire:{MSG}.speech_act.sak_question"), L("question")), INTERROGATIVE)], "question"),
    rule(f"{MSG}.substantive_markers.code_fence", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("code")), Eq(A("sp", "form"), L("fence"))], "code"),
    rule(f"{MSG}.substantive_markers.code_inline", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("code")), Eq(A("sp", "form"), L("inline"))], "code"),
    rule(f"{MSG}.substantive_markers.link_url", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("link"))], "link"),
]


MAX_N = 5  # longest cue (tokens); EqCue slots are w1..w5
NGRAM = {1: "cue_unigram", 2: "cue_bigram", 3: "cue_trigram", 4: "cue_4gram", 5: "cue_5gram"}
TVARS = ("t", "u", "t3", "t4", "t5")  # v0 rule bodies used t/u; kept for n<=2

# cue set -> (label, value, mode, match_on). mode "scoped": negation/hedge-aware
# (hit + scope rules); "direct": the n-gram rule decides the label itself.
CUE_SETS = {
    "deescalation": ("deescalation", True, "scoped", "form"),
    "concession": ("concession", True, "scoped", "form"),
    "status_claim": ("status_claim", True, "scoped", "form"),
    "hostility": ("hostility", True, "scoped", "form"),
    "credential": ("credential", True, "scoped", "form"),
    "deference": ("deference", True, "scoped", "form"),
    "booster": ("booster", True, "scoped", "form"),
    "withdrawal": ("withdrawal", True, "scoped", "form"),
    "citation": ("substantive_markers", "citation", "direct", "form"),
    "domain_technical": ("domain", "technical", "direct", "lemma"),
    "credential_denial": ("credential_negated", True, "direct", "form"),
    "dismissal": ("dismissal", True, "direct", "form"),
    "tribal": ("tribal", True, "direct", "form"),
    "procedural": ("procedural", True, "direct", "form"),
    # 0.4.0 (space climate)
    "disagreement": ("disagreement", True, "scoped", "form"),
    "error_admission": ("error_admission", True, "scoped", "form"),
    "evidence_request": ("evidence_request", True, "scoped", "form"),
    "error_denial": ("error_admission_negated", True, "direct", "form"),
}
SCOPED_LABELS = [lbl for lbl, _v, mode, _m in CUE_SETS.values() if mode == "scoped"]


def _slot(tv, k, classed, attr):
    # A cue slot matches a token by its `form` (formulae) or `lemma` (technical
    # vocabulary) OR, where the bucket has a class slot at position k, by its
    # ingest token class (`eq_class`, e.g. "<num>"; a class string can never be
    # a form or lemma). Plain Eq elsewhere keeps the rule pass cheap.
    w = A("c", f"w{k}")
    return Or(Eq(A(tv, attr), w), Eq(A(tv, "eq_class"), w)) if classed else Eq(A(tv, attr), w)


def cue_edge(cue, n):
    """Bucket edge agent -> EqCue by (cue set, length). Rules join tokens only
    against their own bucket, so the rule pass costs ~tokens x |bucket| instead of
    tokens x |lexicon| per rule (0.2.0 perf fix; see SLICE2 RESULTS)."""
    return f"eq_cue_{cue}_n{n}"


def cue_rules(cue):
    """One rule per cue length n (1..MAX_N): a run of n consecutive prose tokens
    (one clause) equal to an EqCue{cue} whose slots w1..wn are set and w(n+1) unset.
    direct: decides the label. scoped: marks a hit on the head token `t`."""
    label, value, mode, attr = CUE_SETS[cue]
    prefix = "citation_" if cue == "citation" else ("technical_" if cue == "domain_technical" else "")
    out = []
    for n in sorted({len(w) for c, _v, *w in LEXICON if c == cue}):
        match = [RECV, ["m", "eq_has_token", "t"], ["agent", cue_edge(cue, n), "c"]]
        match += [[TVARS[k - 1], "eq_next", TVARS[k]] for k in range(1, n)]
        conds = [Eq(A("c", "cue"), L(cue))]
        if n > 1:
            conds.append(Not(Eq(A("c", f"w{n}"), L(None))))
        if n < MAX_N:
            conds.append(Eq(A("c", f"w{n + 1}"), L(None)))
        bucket = [w for c, _v, *w in LEXICON if c == cue and len(w) == n]
        conds += [_slot(TVARS[k - 1], k, any(w[k - 1] in TOKEN_CLASSES for w in bucket), attr)
                  for k in range(1, n + 1)]
        name = f"{MSG}.{label}.{prefix}{NGRAM[n]}"
        if mode == "direct":
            r = rule(name, match, conds, value)
        else:
            hit = f"eqhit:{cue}"
            r = {"name": name, "match": match,
                 "where": And(Eq(A("t", hit), L(None)), *conds),
                 "effects": [["set_attr", "t", hit, True],
                             ["add_edge", "m", f"eq_hit_{cue}", "t"],
                             ["set_attr", "m", f"eqcue:{name}", True]]}
        if not any(w[0] in TOKEN_CLASSES for w in bucket):
            # R10 join index (matcher traversal only; same match/where/effects):
            # probe EqCue.w1 by the head token's form/lemma instead of scanning
            # the whole bucket per token. Not used where slot 1 is a class slot.
            r["index_hints"] = [{"for_var": "c", "via_var": "t", "via_key": attr,
                                 "node_type": "EqCue", "this_key": "w1"}]
        out.append(r)
    return out


# ---- lexicon (taught) ------------------------------------------------------
LEXICON = [  # (cue, variant, w1[, w2 .. w5]) -- v0 entries first, order preserved
    ("deescalation", "apology", "sorry"),
    ("deescalation", "apology", "apologies"),
    ("deescalation", "apology", "apologize"),
    ("deescalation", "apology", "apologise"),
    ("deescalation", "apology", "my", "bad"),
    ("deescalation", "apology", "my", "mistake"),
    ("deescalation", "concession", "fair", "point"),
    ("deescalation", "concession", "good", "point"),
    ("deescalation", "concession", "you're", "right"),
    ("deescalation", "reassurance", "no", "worries"),
    ("deescalation", "acknowledgement", "i", "understand"),
    ("citation", "attribution", "according", "to"),
    ("citation", "attribution", "cited", "in"),
    ("citation", "reference", "cf"),
    ("citation", "reference", "see", "section"),
]
# ---- 0.2.0 additions -------------------------------------------------------
LEXICON += [("deescalation", "facilitation", *p.split()) for p in (
    "let's step back", "let's pause", "both points are valid", "can we align on",
    "let's focus on the data", "how do we test this", "let's find common ground",
    "let's hear from everyone", "to synthesize")]
LEXICON += [("concession", "concession", *p.split()) for p in (
    "good point", "fair point", "valid point", "you're right", "you are right",
    "fair enough", "i stand corrected", "good catch", "that makes sense", "my mistake",
    "i hadn't considered that")]
LEXICON += [("status_claim", v, *p.split()) for v, p in (
    ("tenure", f"in my {NUM} years"), ("tenure", f"{NUM} years of experience"),
    ("tenure", "decades of experience"),
    ("ownership", "my team"), ("ownership", "i run"), ("ownership", "i built"),
    *(("role", f"as the {r}") for r in ("lead", "vp", "director", "manager", "architect")),
    ("authority", "trust me"), ("authority", "i know what i'm doing"))]
LEXICON += [("hostility", "hostility", *p.split()) for p in (
    "ridiculous", "nonsense", "clueless", "stupid", "obviously wrong", "bad idea",
    "stop interrupting", "waste of time", "are you serious", "you don't understand",
    "you do not understand")]
LEXICON += [("domain_technical", "technical", *p.split()) for p in (
    "latency", "p99", "p95", "throughput", "rfc", "memory leak", "deadlock", "concurrency",
    "mutex", "cache", "database", "index", "benchmark", "profiler", "flamegraph",
    "flame graph", "tcp", "socket", "heap", "cpu", "scaling", "failover", "redundancy",
    "api", "payload", "deserialization", "connection pool", "query")]
# ---- 0.3.0 additions (T3b): class-slot frames + new formula sets -----------
LEXICON += [("credential", "frame", *p.split()) for p in (
    f"i'm a {PERSON}", f"i'm an {PERSON}", f"i am a {PERSON}", f"i am an {PERSON}",
    f"as a {PERSON}", f"as an {PERSON}", f"i work as a {PERSON}")]
LEXICON += [("credential_denial", "frame", *p.split()) for p in (
    f"i'm not a {PERSON}", f"i'm not an {PERSON}", f"i am not a {PERSON}", f"i am not an {PERSON}")]
LEXICON += [("deference", "deference", *p.split()) for p in (
    "you know best", "i defer to you", "you're the expert", "over to you", "happy to defer")]
LEXICON += [("booster", "booster", *p.split()) for p in (
    "clearly", "obviously", "definitely", "certainly", "undeniably", "without a doubt",
    "of course")]
LEXICON += [("withdrawal", "disengage", *p.split()) for p in (
    "never mind", "i'll leave it there", "forget it", "i give up", "count me out", "i'm out",
    "i'm done here")]
LEXICON += [("dismissal", "dismissal", *p.split()) for p in (
    "you wouldn't understand", "not your area", "stay in your lane", "leave it to the experts",
    "you're not qualified", "with all due respect")]
LEXICON += [("tribal", "outgroup_address", *p.split()) for p in (
    f"you {GROUP}", f"those {GROUP}", "people like you", "you lot", "your lot", "your kind")]
LEXICON += [("procedural", "procedure", *p.split()) for p in (
    "point of order", "back to the agenda", "per the agenda", "out of scope", "time check",
    "for the record", "follow the process")]
# ---- 0.4.0 additions (space climate): disagreement / error admission / evidence request
# All scoped (negation / hedge aware on the head token) except error_denial, which
# names the negated constructions a contiguous cue cannot reach ("i was not wrong").
LEXICON += [("disagreement", "disagreement", *p.split()) for p in (
    "disagree", "that's wrong",
    "that is wrong", "that's incorrect", "that is incorrect", "that's not true", "that is not true",
    "that isn't true", "that's not right", "that isn't right", "i don't agree", "i do not agree",
    "i'm not convinced", "i am not convinced", "not convinced", "i don't buy it", "i don't buy that",
    "that's not the case", "that is not the case", "i'd push back", "i would push back",
    "push back on that", "i object")]
LEXICON += [("error_admission", "admission", *p.split()) for p in (
    "i was wrong", "i was mistaken", "i was incorrect", "my mistake", "my bad", "my error",
    "my fault", "i stand corrected", "i got that wrong", "i got it wrong", "i misread",
    "i misspoke", "i made a mistake", "i messed up", "that's on me", "i retract that",
    "i take that back", "i take it back")]
LEXICON += [("error_denial", "denial", *p.split()) for p in (
    "i was not wrong", "i wasn't wrong", "i was never wrong", "i'm not wrong", "i am not wrong",
    "i was not mistaken", "i wasn't mistaken", "i didn't make a mistake")]
LEXICON += [("evidence_request", "request", *p.split()) for p in (
    "what's the evidence", "what is the evidence", "where's the evidence", "where is the evidence",
    "any evidence", "what evidence", "evidence for that", "evidence for this", "is there data",
    "what data", "can you back that up", "can you back this up", "back that up",
    "how do you know", "what makes you think", "why do you think", "says who", "how so",
    "prove it", "any proof", "what proof", "citation needed", "do you have a source",
    "any source", "any sources", "your source", "source please", "sources please",
    "need a source")]
assert all(3 <= len(e) <= 2 + MAX_N for e in LEXICON), "cue length must be 1..MAX_N tokens"
assert {c for c, *_ in LEXICON} == set(CUE_SETS)


def normalised_lexicon():
    """lemma-matched sets store each cue word through the adapter's own `lemma`
    (so token and cue are normalised by one function); class slots untouched."""
    from domains.equilibrium_classify import lemma
    out = []
    for cue, variant, *words in LEXICON:
        if CUE_SETS[cue][3] == "lemma":
            words = [w if w in TOKEN_CLASSES else lemma(w) for w in words]
        out.append((cue, variant, *words))
    return out


# ---- cue rules (only for cue lengths the lexicon actually has) --------------
for _cue in ("citation", "deescalation", "concession", "status_claim", "hostility",
             "domain_technical", "credential", "credential_denial", "deference", "booster",
             "withdrawal", "dismissal", "tribal", "procedural", "disagreement", "error_admission",
             "error_denial", "evidence_request"):
    RULES += cue_rules(_cue)
for _lbl in SCOPED_LABELS:
    RULES += qr.scope_label_rules(_lbl, next(c for c, v in CUE_SETS.items() if v[0] == _lbl))
RULES += qr.MSG_STRUCT_RULES
RULES += qr.CLIMATE_MSG_RULES


# ---- label status (design §9) ----------------------------------------------
SUPPORTED = [  # (label, values, match_class, since_pack)
    ("msg.speech_act", ["question", "assertion", "directive"], "exact", "0.1.0"),
    ("msg.substantive_markers", ["question", "code", "link", "citation"], "exact", "0.1.0"),
    ("msg.deescalation", [True], "exact", "0.1.0"),
    ("msg.concession", [True], "exact", "0.2.0"),
    ("msg.status_claim", [True], "exact", "0.2.0"),
    ("msg.hostility", [True], "exact", "0.2.0"),
    ("msg.domain", ["technical"], "exact", "0.2.0"),
]
_V4_SCOPED = ("disagreement", "error_admission", "evidence_request")
_v3 = [f"msg.{lbl}" for lbl in ("credential", "deference", "booster", "withdrawal")]
_v3 += [f"msg.{lbl}{sfx}" for lbl in SCOPED_LABELS if lbl not in _V4_SCOPED
        for sfx in ("_negated", "_hedged")]
_v3 += ["msg.dismissal", "msg.tribal", "msg.procedural", "msg.hedge", "msg.reply_contrast"]
SUPPORTED += [(lbl, [True], "exact", "0.3.0") for lbl in dict.fromkeys(_v3)]
_v4 = [f"msg.{lbl}{sfx}" for lbl in _V4_SCOPED for sfx in ("", "_negated", "_hedged")]
_v4 += ["msg.dissent", "msg.dissent_hedged", "msg.challenge", "msg.challenge_hedged"]
SUPPORTED += [(lbl, [True], "exact", "0.4.0") for lbl in _v4]

EDGE_TYPES = [("Agent", "received", "Message"), ("Message", "eq_has_token", "Token"),
              ("Token", "eq_next", "Token"), ("Message", "eq_has_span", "CodeSpan"),
              ("Message", "eq_has_span", "LinkSpan"), ("Agent", "eq_has_cue", "EqCue"),
              ("Agent", "eq_has_label_status", "LabelStatus"),
              ("Message", "eq_neg_next", "Token")]  # 0.4.0: content token right after a negator
EDGE_TYPES += sorted({("Agent", cue_edge(c, len(w)), "EqCue") for c, _v, *w in LEXICON})
EDGE_TYPES += [("Message", f"eq_hit_{c}", "Token") for c, v in CUE_SETS.items() if v[2] == "scoped"]


def header(sid, deps, desc):
    return {"id": sid, "version": PACK_VERSION, "self_load_only": True, "depends_on": deps,
            "taxonomy_version": TAXONOMY_VERSION, "description": desc}


def productions(sid, triples):
    return [{"provenance": f"{sid}:{s}_{e}_{t}", "src": {"type": s, "var": "a"}, "edge_type": e,
             "tgt": {"type": t, "var": "b"}} for s, e, t in triples]


def root_edges(nodes, etype):
    return [{"src": {"role": "agent_root"}, "tgt": {"local": n["local_id"]},
             "type": etype, "attrs": {}} for n in nodes]


def taught(category, deps, items):
    """Mint codebook rows through `teach` on a scratch substrate; return the
    taught nodes exactly as teach filed them."""
    from substrate.boot_core import boot_core
    from domains.teach import teach
    s, ag = boot_core(("speech_act_classify",))
    scratch = types.SimpleNamespace(s=s, agent_root=ag)
    with tempfile.TemporaryDirectory() as d:
        for typ, attrs in items:
            teach(scratch, typ, attrs, category=category, depends_on=deps, seeds_dir=Path(d))
        return json.loads((Path(d) / f"{category}.json").read_text())["nodes"]


def codebook(sid, deps, desc, items, edge_of, extra_edges=()):
    nodes = taught(sid, deps, items)
    edges = [e for n in nodes for e in root_edges([n], edge_of[n["type"]])]
    m = header(sid, deps, desc)
    m.update(nodes=nodes, edges=edges, productions=productions(sid, extra_edges), rules=[])
    return m


def build_lexicon() -> dict:
    lexicon = normalised_lexicon()
    items = []
    for cue, variant, *words in lexicon:
        attrs = {"cue": cue, "variant": variant}
        attrs.update({f"w{k}": w for k, w in enumerate(words, 1)})
        items.append(("EqCue", attrs))
    nodes = taught("equilibrium_lexicon", ["equilibrium_tokens"], items)
    m = header("equilibrium_lexicon", ["equilibrium_tokens"],
               "Equilibrium cue vocabulary (EqCue{cue,variant,w1[..w5]}; class slots '<num>', "
               "'<noun.person>', '<noun.group>'; domain_technical words stored as lemmas), minted "
               "via domains.teach on a scratch substrate; wired to agent root by eq_has_cue.")
    edges = root_edges(nodes, "eq_has_cue")
    edges += [{"src": {"role": "agent_root"}, "tgt": {"local": n["local_id"]},
               "type": cue_edge(n["attrs"]["cue"], sum(f"w{k}" in n["attrs"] for k in range(1, MAX_N + 1))),
               "attrs": {}} for n in nodes]
    m.update(nodes=nodes, edges=edges, productions=[], rules=[])
    return m


def label_status_rows():
    rows = [{"label": lbl, "kind": "msg", "values": vals, "status": "shadow", "since_pack": since,
             "match_class": mc} for lbl, vals, mc, since in SUPPORTED]
    rows += [{"label": t, "kind": "trait", "values": list(p), "status": "shadow",
              "since_pack": qr.TRAIT_SINCE.get(t, "0.4.0" if t in qr.CLIMATE_TRAIT_NAMES else "0.3.0"),
              "match_class": None}
             for t, p, _tg, _n in qr.TRAITS]
    rows += [{"label": p, "kind": "trait", "values": ["+"], "status": "disabled",
              "since_pack": "0.3.0", "match_class": None} for p in qr.PATTERNS]
    rows += [{"label": f"episode.{k}", "kind": "episode_kind", "values": [], "status": "shadow",
              "since_pack": "0.3.0", "match_class": None} for k in qr.EPISODE_KINDS]
    rows += [{"label": f"facet.{c}", "kind": "facet", "values": [], "status": "shadow",
              "since_pack": "0.3.0", "match_class": None} for c in qr.FACET_CODES]
    return rows


def build() -> dict[str, dict]:
    qr.check_nm_pack()
    out = {}
    out["equilibrium_tokens"] = dict(
        header("equilibrium_tokens", ["speech_act_classify"],
               "Ingest vocabulary: Message/Token/CodeSpan/LinkSpan tokens the adapter mints."),
        nodes=[], edges=[], rules=[], productions=productions("equilibrium_tokens", EDGE_TYPES))
    win = codebook("equilibrium_window", ["equilibrium_tokens"],
                   "Window / conversation ingest vocabulary (EqWindow/EqActor, authorship, declared reply, "
                   "turn position; no adjacency edge since 0.5.0), the EqStratum clock the adapter "
                   "opens in order, and the rules deriving responds_to / addresses (basis declared) "
                   "and thread structure.",
                   qr.STRATUM_ITEMS, {"EqStratum": "eq_has_stratum"}, qr.WINDOW_EDGE_TYPES)
    win["rules"] = qr.apply_frontier(qr.WINDOW_RULES)
    out["equilibrium_window"] = win
    out["equilibrium_lexicon"] = build_lexicon()
    out["equilibrium_scope"] = codebook(
        "equilibrium_scope", ["equilibrium_tokens"],
        "Closed-class scope codebook (LEXICAL by design §5.4): negators / hedges (EqScopeOp), "
        "clause-boundary words (EqScopeBoundary), reply-leading contrast connectives (EqCohMarker), "
        "function words (EqClosedClass, 0.4.0: negated-echo dissent).",
        qr.SCOPE_ITEMS, qr.SCOPE_EDGE, qr.SCOPE_EDGE_TYPES)
    out["equilibrium_msg"] = dict(
        header("equilibrium_msg", ["equilibrium_lexicon", "equilibrium_scope", "equilibrium_window",
                                   "speech_act_classify"],
               "msg-layer rules: speech_act (from sak_kind), substantive_markers, cue hits, "
               "negation/hedge-scoped cue labels, domain (technical, lemma), hedge, reply_contrast, "
               "0.4.0 dissent / challenge (reply-pair shapes)."),
        nodes=[], edges=[], productions=[], rules=RULES)
    out["equilibrium_pattern"] = dict(
        header("equilibrium_pattern", ["equilibrium_msg"],
               "pat-layer stub: superseded by behavioural quanta (equilibrium_quanta); ships NO rules."),
        nodes=[], edges=[], productions=[], rules=[])
    out["equilibrium_traits"] = codebook(
        "equilibrium_traits", ["equilibrium_msg"],
        "Open trait vocabulary v0.4.0: EqTrait{trait,poles,targetable} + EqTraitCue{trait,pole,"
        "lab_key,role,owner}; generic eq.quanta.* rules read these rows (new trait = new rows).",
        qr.trait_items(), qr.TRAIT_EDGE, qr.TRAIT_EDGE_TYPES)
    out["equilibrium_quanta"] = dict(
        header("equilibrium_quanta", ["equilibrium_traits", "equilibrium_window"],
               "Generic quanta rules: evidence / hedged / counter from EqTraitCue rows, interaction "
               "shapes (floor, run, responsiveness, withdrawal), question_demand, composites, match shapes."),
        nodes=[], edges=[], productions=productions("equilibrium_quanta", qr.QUANTA_EDGE_TYPES),
        rules=qr.apply_nm(qr.apply_live(qr.QUANTA_RULES), "quanta"))
    out["equilibrium_competence"] = dict(
        header("equilibrium_competence", ["equilibrium_quanta"],
               "Relational competence: corroborated, contested, claim_grounding (+ / - capped weak)."),
        nodes=[], edges=[], productions=[], rules=qr.apply_nm(qr.apply_live(qr.COMPETENCE_RULES), "competence"))
    ep = codebook("equilibrium_episode", ["equilibrium_quanta"],
                  "Episodes (dispute root / growth over responds_to), etiology facets (EqFacetCue), "
                  "generative true/false (null = default), facet match shapes.",
                  qr.episode_items(), qr.EPISODE_EDGE, qr.EPISODE_EDGE_TYPES)
    ep["rules"] = qr.apply_nm(qr.apply_live(qr.EPISODE_RULES), "episode")
    out["equilibrium_episode"] = ep
    cl = codebook("equilibrium_climate", ["equilibrium_quanta"],
                  "Space-climate relational traits (0.4.0): EqClimateCue{role,lab_key} reply codebook "
                  "(stimulus / dismiss / status / ground / engage / nonanswer) and the S1/S2 rules for "
                  "response.dismissal, response.engagement, inquiry.answered, inquiry.unanswered.",
                  qr.climate_items(), qr.CLIMATE_EDGE, qr.CLIMATE_EDGE_TYPES)
    cl["rules"] = qr.apply_nm(qr.apply_live(qr.CLIMATE_RULES), "climate")
    out["equilibrium_climate"] = cl
    trk = codebook("equilibrium_tracking", ["equilibrium_climate", "equilibrium_window", "equilibrium_scope"],
                   "Conversation tracking (T3c O2; 0.8.0 T3g held-open collapse): a seeded turn cursor "
                   "over the retained conversation fork derives addressees (name mention of a known "
                   "actor_ref, second person to the last addresser), a bounded CANDIDATE parent set per "
                   "undeclared turn (QUD top / latest pending address / latest contrasted claim / adjacent "
                   "other-speaker turn / addressee's last turn) with cue edges to the closed EqTrkCue "
                   "codebook, collapse only on strict cue-set dominance (strong >= 2 cues, weak 1; else "
                   "HELD, never tiebroken), uptake revision over a per-actor held frontier, eq_answers, the "
                   "open-question set (eq_qud) and same-actor continuation. EqSecondPerson / EqBackchannel "
                   "/ EqPolarAux / EqPolarAnswer closed-class codebooks.",
                   qr.TRACKING_ITEMS, qr.TRACKING_EDGE,
                   qr.TRACKING_EDGE_TYPES + qr.LIVE_EDGE_TYPES + qr.NM_EDGE_TYPES)
    trk["rules"] = qr.apply_nm(qr.apply_frontier(qr.TRACKING_RULES), "tracking")
    out["equilibrium_tracking"] = trk
    nodes = [{"local_id": i, "type": "LabelStatus", "attrs": a} for i, a in enumerate(label_status_rows())]
    out["equilibrium_label_status"] = dict(
        header("equilibrium_label_status", ["equilibrium_msg", "equilibrium_pattern", "equilibrium_traits",
                                            "equilibrium_episode", "equilibrium_climate",
                                            "equilibrium_tracking"],
               "One LabelStatus{label,kind,values,status,since_pack,match_class} per msg label, "
               "trait, episode kind and facet."),
        nodes=nodes, edges=root_edges(nodes, "eq_has_label_status"), productions=[], rules=[])
    return out


if __name__ == "__main__":
    for sid, m in build().items():
        (SEEDS / f"{sid}.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
        print(f"wrote seeds/{sid}.json nodes={len(m['nodes'])} rules={len(m['rules'])}")
