"""global_monitoring -- STEP 5: GLOBAL comprehension monitoring.

domains/reading_review.py is a strong LOCAL (within-clause) standards-of-
coherence monitor: `combined_incoherence` catches an ungroundable or
selectionally-mismatched clause ('I could of done that', 'the report
infers ...'). But it is LOCAL -- it scores one clause's own predications and
cannot see a contradiction between two facts FAR APART in the text:

    'The lawyer had no children. She was busy. His daughter arrived home.'

Each clause is individually coherent (reading_review passes all three), yet
the THIRD entails the lawyer HAS a child, contradicting the FIRST. This is
Glenberg, Meyer & Lindem 1982's illusion-of-knowing shape, and exactly the
gap O'Brien & Cook 2016's RI-Val model assigns to its VALIDATION stage: a new
proposition is checked against the WHOLE situation model (not the current
clause), and a failed check escalates to reprocessing.

THE MECHANISM (a thin driver; every DECISION is a graph Program/Term):

  1. READ. Each sentence is read via the HELD reading_scope.read_scope (with
     the SAME read_clause fallback situation_model_reader.py/coref_entities.py
     already use) -- reused, unchanged. Its LOCAL incoherence is
     reading_review.combined_incoherence -- REUSED verbatim, not re-derived --
     over that clause's own predications (this is the "each ~0, passes" half
     of the headline: the local monitor genuinely cannot see the problem).

  2. ENTAIL. A predication argument that decomposes (mechanical `str.split
     ("_")` -- no regex, the SAME boundary op reading_review._head /
     reading_scope._swallows_predication use) into a KINSHIP noun
     (daughter/son/child/children -- the seeded `KINSHIP` MarkerClass,
     seeds/global_monitoring.json, membership read the SAME way
     situation_model_reader.cos_membership reads its `COS` class) entails a
     `has_child` fact on the predication's POSSESSOR: the clause's own
     subject when the kinship noun is a plain object ('lawyer had no
     children' -> lawyer), or the antecedent of a possessive determiner
     ('his daughter' -> whoever 'his' resolves to) found by REUSING
     coref_entities.antecedent_argmax_term (the SAME graph-native Argmax the
     conversation/reading coref path already runs -- not a new resolver). A
     seeded NEGATOR prefix ('no'/'zero'/'none') entails 0; otherwise 1.

  3. VALIDATE. The entailed value is checked against the situation model's
     CURRENTLY ESTABLISHED value for that attr on that entity -- the
     `global_contradiction` Program (seeds/global_monitoring.json: `established
     != unset AND established != new`, the Var/Eq/Not/And vocabulary
     seeds/reading_review.json's `review_license` Program already proves
     sufficient), evaluated by `native.evaluate` in Rust. Python only READS
     the established attr and hands it in as a bound value -- exactly the
     `_licensed` idiom reading_review.py already uses for its own Program
     (`best`/`runnerup`/`self` read then handed to `review_license`). This is
     the GRAPH-NATIVE gate: no Python conditional comparing the two
     values decides the contradiction -- `native.evaluate` on the Program does.

  4. ESCALATE. A fired contradiction is NOT silently accepted: it flags a
     `GlobalIncoherence` node and calls reading_scope's EXISTING retained-
     trace / cold re-read path (`reading_scope._reanalyse`, reused AS-IS,
     unmodified) on the sentence that established the now-contradicted fact
     versus the one that just broke it -- reactivate-then-cold-reread, the
     same mechanism `read_paragraph` already runs on a non-sequitur, now
     ALSO reachable from a global state contradiction, matching RI-Val's
     Validation -> (failure) -> reprocess.

ARCHITECTURE (CLAUDE.md). Steps 1/4 call HELD faculties (reading_scope,
reading_review, situation_model_reader, coref_entities) AS-IS, unmodified.
Step 2's entailment reads a seeded MarkerClass exactly like an existing one.
Step 3's DECISION is a graph Program; Python only marshals values (mechanical
adapter I/O), never compares them itself. NO regex, NO `import re`, no new
Rust Term (Var/Lit/Attr/Eq/Not/And is already sufficient, per
seeds/reading_review.json's own `review_license`).

HONEST SCOPE. This catches exactly two contradiction TYPES: (a) a DIRECT
attr conflict already stated as such by the codebook's own canon (has_child
0 vs 1), and (b) an ENTAILED conflict where a stated surface term (daughter/
son/child) supplies the conflicting attr via the seeded KINSHIP class. It
MISSES any contradiction whose entailment is not derivable from this small,
FINITE codebook (a term the KINSHIP class does not name -- 'grandchild',
'niece'; a possessive whose antecedent does not resolve; a conflict along an
attribute this seed does not model) -- an honest residual, not hidden,
exactly as seeds/inference_knowledge.json documents for its own knowledge
codebook.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import coref_entities as ce
from domains import reading_collapse as rc
from domains import reading_review as rr
from domains import reading_scope as rs
from domains import reflective_faculty as rf
from domains import situation_model_reader as smr

_SEED_ID = "global_monitoring"
_UNSET = "__unset__"

# Possessive determiners -- a closed function-word class (the SAME status
# reading_review._PRONOUNS documents for its own set: "A function-word list,
# NOT a correction map"). reference_resolution._PRONOUNS has no possessive
# case at all (it, he, she, him, her, they, them only), so this is genuinely
# new coverage, not a duplicate of an existing table -- but the RESOLUTION
# mechanism it feeds (coref_entities.antecedent_argmax_term) is 100% reused.
_POSSESSIVE = {
    "his": {"number": "singular", "agree": "person"},
    "her": {"number": "singular", "agree": "person"},
    "their": {"number": "plural", "agree": "any"},
    "its": {"number": "singular", "agree": "non_person"},
}

# A negated-quantity prefix ('no children', 'zero children', 'none') entails
# the absence (0); any other prefix (a number, or none at all) entails
# presence (1). Closed, small, honest -- the SAME status as _POSSESSIVE.
_NEGATORS = frozenset({"no", "zero", "none"})


# --------------------------------------------------------------------------- #
#  resolution + idempotent seed load (mechanical adapter I/O).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def ensure_seeds(agent) -> None:
    """Idempotently install seeds/global_monitoring.json (the KINSHIP
    MarkerClass + the global_contradiction Program) plus its dependency
    (situation_model / event_reasoning, via smr.ensure_seeds -- reused).
    Guard is the sentinel Concept 'global_monitoring', the SAME idiom every
    other domains/*.py ensure_seeds uses."""
    smr.ensure_seeds(agent)
    sub, native, ag_node = _resolve(agent)
    if _has_concept(sub, _SEED_ID):
        return
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)


# --------------------------------------------------------------------------- #
#  KINSHIP membership -- the SAME member-lookup shape
#  situation_model_reader.cos_membership reads for its COS class, applied to
#  a NOUN class. HONEST: unlike COS (a verb class where reading_collapse's
#  _wordnet_nearness meaningfully extends membership by verb-sense
#  adjacency), that helper is VERB-scoped (wn.synsets(word, pos="v")) and
#  does not apply to nouns -- so membership here is EXACT-FORM only, over a
#  small finite seed list. An unseen kinship noun is a genuine residual.
# --------------------------------------------------------------------------- #
def _kinship_node(sub):
    for n in sub.nodes("MarkerClass"):
        if sub.node(n)["attrs"].get("cls") == "KINSHIP":
            return n
    return None


def kinship_membership(agent, noun: str) -> dict:
    """Is `noun` a member of the seeded KINSHIP class? Returns {noun, kin,
    canon}. `canon` is the bridge attribute name (always 'has_child' in the
    current codebook) the member's `canon` map supplies -- read off the seed,
    never guessed. Exact-form only (see module docstring for why the COS
    adjacency-join mechanism does not transplant onto a noun class)."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    node = _kinship_node(sub)
    noun = str(noun).lower()
    if node is None:
        return {"noun": noun, "kin": False, "canon": None}
    at = sub.node(node)["attrs"]
    forms = [str(f).lower() for f in (at.get("forms") or [])]
    canon = dict(at.get("canon") or {})
    if noun in forms:
        return {"noun": noun, "kin": True, "canon": canon.get(noun, noun)}
    return {"noun": noun, "kin": False, "canon": None}


# --------------------------------------------------------------------------- #
#  DECOMPOSE a compound argument token -- mechanical string ops, no regex
#  (the SAME `str(span).split("_")` boundary op reading_review._head /
#  reading_scope._swallows_predication already use on the identical
#  underscore-joined argument shape reading_collapse._norm produces).
# --------------------------------------------------------------------------- #
def _decompose_kin_arg(token) -> Optional[dict]:
    toks = [t for t in str(token).lower().split("_") if t]
    if not toks:
        return None
    return {"noun": toks[-1], "prefix": (toks[0] if len(toks) > 1 else None)}


# --------------------------------------------------------------------------- #
#  POSSESSIVE RESOLUTION -- 100% reuse of coref_entities' graph-native Argmax
#  (antecedent_argmax_term over the resident SmEntity pool). The ONLY new
#  content is the _POSSESSIVE agreement-spec table above; the DECISION
#  (which resident entity wins) is unchanged coref_entities machinery.
# --------------------------------------------------------------------------- #
def _resolve_possessive(agent, prefix: str, turn: int, unit=None) -> Optional[str]:
    sub, native, _ = _resolve(agent)
    spec = _POSSESSIVE.get(prefix)
    if spec is None:
        return None
    cb_name = ce._current_cb(agent)
    term = ce.antecedent_argmax_term(spec, cb_name, unit)
    winner = native.evaluate(term, {})
    if winner is None:
        return None
    return sub.node(winner)["attrs"].get("name")


# --------------------------------------------------------------------------- #
#  KIN SIGNAL -- scan a predication's arguments for a kinship-noun entailment.
# --------------------------------------------------------------------------- #
def kin_signal(agent, pred: list, turn: int, unit=None) -> Optional[dict]:
    """Does this predication entail a `has_child`-shaped fact? Scans every
    argument (mechanical): the first one that decomposes to a seeded KINSHIP
    noun supplies the entailment. The POSSESSOR is either (a) the antecedent
    of a possessive-determiner prefix ('his daughter' -- resolved via the
    reused coref Argmax), or (b) the clause's own subject, when the kinship
    noun is a plain (optionally negated/quantified) object ('lawyer had no
    children' -> lawyer). A bare kinship subject with NO possessive ('Daughter
    arrived.') has no determinable possessor -- an honest unresolved residual,
    not guessed. Returns None when no argument names a kinship noun at all
    (the discriminative case: an unrelated clause never triggers a check)."""
    if not pred or len(pred) < 2:
        return None
    subject = str(pred[1])
    for idx, raw in enumerate(pred[1:]):
        decomp = _decompose_kin_arg(raw)
        if decomp is None:
            continue
        mem = kinship_membership(agent, decomp["noun"])
        if not mem["kin"]:
            continue
        prefix = decomp["prefix"]
        if prefix in _POSSESSIVE:
            possessor = _resolve_possessive(agent, prefix, turn, unit=unit)
            if possessor is None:
                return {"kin": True, "resolved": False, "arg": raw,
                        "noun": decomp["noun"], "prefix": prefix,
                        "reason": ("possessive %r held open -- no agreeing resident "
                                   "antecedent (RI-Val: not force-bound)" % prefix)}
        elif idx == 0:
            return {"kin": True, "resolved": False, "arg": raw,
                    "noun": decomp["noun"], "prefix": prefix,
                    "reason": ("bare kinship subject %r with no possessive -- possessor "
                               "undeterminable, honest residual" % raw)}
        else:
            possessor = subject
        return {"kin": True, "resolved": True, "possessor": possessor,
                "entailed_attr": mem["canon"],
                "entailed_value": 0 if prefix in _NEGATORS else 1,
                "noun": decomp["noun"], "prefix": prefix, "arg": raw}
    return None


# --------------------------------------------------------------------------- #
#  VALIDATE + APPLY -- the graph-native contradiction gate.
# --------------------------------------------------------------------------- #
def validate_against_model(agent, entity_name: str, attr: str, new_value,
                           *, sentence: str, turn: int, unit=None,
                           sentence_order=None, trace_node=None) -> dict:
    """THE GATE. Read the sm_entity's CURRENTLY ESTABLISHED value for `attr`
    (mechanical graph read); evaluate the seeded `global_contradiction`
    Program (native.evaluate -- the DECISION) over {established, new, unset};
    if it fires, mint a `GlobalIncoherence` flag (never silently accepted).
    Then advance the model (`set_attr`) regardless -- the text's claim
    becomes the new state, same as any other ingested fact; the contradiction
    is FLAGGED, not suppressed or force-corrected. Returns {entity, attr,
    established, new, contradiction, incoherence, salience, flag_node,
    prior_establisher}.

    `sentence_order`/`trace_node` (Wave: dynamic-thresholds/reopen, 2026-07-11):
    mechanical PROVENANCE bookkeeping -- WHO (which SentenceParse order/ring-
    buffer trace) established the PRIOR value of this (entity, attr), read back
    BEFORE it is overwritten and returned as `prior_establisher` (None on a
    first establishment). This is the SAME provenance `read_and_monitor`'s
    Python `established_by` dict already keeps ephemerally for its own call;
    persisting it on the SmEntity (`establish_meta`, one JSON dict per entity)
    lets the LIVE `_shim_monitoring` driver (which processes SentenceParse rows
    across MANY cognitive_tick calls, not one Python stack frame) call
    `escalate_reread` against the RIGHT prior sentence's retained trace without
    re-deriving it. A caller that never passes `sentence_order` gets the
    byte-identical pre-wave behaviour (no bookkeeping write)."""
    ensure_seeds(agent)
    sub, native, _ = _resolve(agent)
    ent = smr._entity(agent, entity_name, unit=unit)       # mint-or-fetch, reused as-is
    established = sub.node(ent)["attrs"].get(attr, _UNSET)
    prog = rf._load_program(sub, "global_contradiction")
    env = {"established": established, "new": new_value, "unset": _UNSET}
    fired = bool(native.evaluate(prog, env)) if prog is not None else False
    incoh = 1.0 if fired else 0.0
    salience = rr._salience(incoh)                        # REUSED verbatim
    prior_establisher = None
    if sentence_order is not None:
        try:
            meta = json.loads(sub.node(ent)["attrs"].get("establish_meta") or "{}")
        except Exception:
            meta = {}
        prior_establisher = meta.get(attr)
    sub.set_attr(ent, attr, new_value)
    if sentence_order is not None:
        meta[attr] = {"sentence": sentence, "order": sentence_order, "trace_node": trace_node}
        sub.set_attr(ent, "establish_meta", json.dumps(meta))
    node = None
    if fired:
        gi_attrs = {"entity": entity_name, "attr": attr, "established": established,
                    "new": new_value, "sentence": sentence, "t": float(turn),
                    "salience": salience, "flagged": 1.0}
        if unit is not None:
            gi_attrs["unit"] = unit
        node = sub.add_node("GlobalIncoherence", gi_attrs)
    return {"entity": entity_name, "attr": attr, "established": established,
            "new": new_value, "contradiction": fired, "incoherence": incoh,
            "salience": salience, "flag_node": node, "prior_establisher": prior_establisher}


# --------------------------------------------------------------------------- #
#  ESCALATE -- the existing reading_scope retained-trace / cold re-read path,
#  reused AS-IS. A contradiction is never silently accepted: it forces a
#  reanalysis of the sentence that established the now-broken fact.
# --------------------------------------------------------------------------- #
def escalate_reread(agent, established_entry: Optional[dict], trigger_entry: dict,
                    trigger_pred: list, *, max_revisits: int = 8) -> dict:
    """RI-Val: Validation -> (failure) -> reprocess. Reuses
    `reading_scope._reanalyse` UNCHANGED -- the SAME reactivate-then-cold-
    re-read path `read_paragraph` runs on a referent non-sequitur, now ALSO
    driven by a global state contradiction. `established_entry["trace_node"]`
    is passed through honestly: None when the establishing sentence never
    committed a retained trace (e.g. it resolved via the read_clause
    fallback) -- `reactivate` then correctly reports a cold miss and
    `_reanalyse` falls through to `_reread_from_source`, exactly as it does
    for a genuinely evicted trace."""
    if established_entry is None:
        return {"escalated": False,
                "reason": "no prior sentence on record established this attr"}
    est_preds = established_entry.get("predications") or []
    prior = {"sentence": established_entry["sentence"], "predications": est_preds,
             "referents": sorted(rs._referents(est_preds)),
             "trace_node": established_entry.get("trace_node")}
    trigger = {"sentence": trigger_entry["sentence"], "predications": [trigger_pred]}
    result = rs._reanalyse(agent, prior, trigger, max_revisits)
    result["escalated"] = True
    return result


# --------------------------------------------------------------------------- #
#  THE DRIVER -- read the text sentence by sentence; local review passes;
#  global validation catches the far-apart contradiction.
# --------------------------------------------------------------------------- #
def read_and_monitor(agent, text: str, *, max_sentences: int = 40,
                     max_revisits: int = 8) -> dict:
    """THE WIRE for step 5. For each sentence: read it (reading_scope.read_scope,
    the SAME read_clause fallback situation_model_reader/coref_entities use);
    score its LOCAL incoherence (reading_review.combined_incoherence, REUSED
    verbatim -- this is the "local passes" half of the headline). For each
    predication: a kinship entailment (`kin_signal`) is VALIDATED against the
    accumulated situation model (`validate_against_model` -- the graph-native
    gate); a fired contradiction ESCALATES to the existing cold re-read path
    (`escalate_reread`) and is never silently accepted. A non-kinship
    predication is handed to `coref_entities.resolve_and_ingest` unchanged (the
    ordinary situation-model wire, reused as-is). Returns {textbase, checks,
    escalations, situation_model}."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    sentences = rc._split_sentences(text)
    textbase: list = []
    checks: list = []
    escalations: list = []
    established_by: dict = {}                              # (entity, attr) -> textbase entry
    turn = 0
    for s in sentences[:max_sentences]:
        if not s.strip():
            continue
        rec = rs.read_scope(agent, s)
        preds = rec.get("predications") or []
        source = "read_scope"
        trace_node = rec.get("trace_node") if rec.get("committed") else None
        if not preds:
            fb = rc.read_clause(agent, s, write=False)
            preds = fb.get("predications") or []
            source = "read_clause_fallback"
            trace_node = None
        local_incoherence = rr.combined_incoherence(agent, {"predications": preds})
        entry = {"sentence": s, "predications": preds, "source": source,
                 "local_incoherence": local_incoherence, "trace_node": trace_node}
        textbase.append(entry)
        for p in preds:
            turn += 1
            kin = kin_signal(agent, p, turn)
            if kin is None:
                ce.resolve_and_ingest(agent, p, s, turn)
                continue
            if not kin.get("resolved"):
                checks.append({"predication": p, "sentence": s, "kin": kin,
                               "contradiction": False, "note": kin["reason"]})
                continue
            ce._touch_entity(agent, s, kin["possessor"], "agent", turn)
            chk = validate_against_model(agent, kin["possessor"], kin["entailed_attr"],
                                          kin["entailed_value"], sentence=s, turn=turn)
            key = (kin["possessor"], kin["entailed_attr"])
            prior_entry = established_by.get(key)
            chk.update({"predication": p, "sentence": s, "kin": kin})
            checks.append(chk)
            if chk["contradiction"]:
                esc = escalate_reread(agent, prior_entry, entry, p, max_revisits=max_revisits)
                esc["for_check"] = chk
                escalations.append(esc)
            established_by[key] = entry

    model: dict[str, dict] = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if nm:
            model[nm] = {k: v for k, v in at.items() if k != "name"}
    return {"text": text, "sentences": sentences, "textbase": textbase,
            "checks": checks, "escalations": escalations, "situation_model": model}


__all__ = [
    "ensure_seeds", "kinship_membership", "kin_signal", "validate_against_model",
    "escalate_reread", "read_and_monitor",
]
