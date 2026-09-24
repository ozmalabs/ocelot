"""media_analysis — AGENT DELETION, the rhetorical move where an agentless
passive omits the responsible actor (Halliday transitivity / critical
discourse analysis: "Shots were fired." backgrounds WHO fired them; "Police
fired shots." does not). ALSO: UNSAID ROLE, the same shape one level up —
what is NOT being said via a RELATIONAL NOUN's absent complement ("states'
rights" — a right is always a right TO something; the residual is "a right
to what?"). See this module's UNSAID ROLE section below for the second
capability's own docstring; the two share one architecture, mirrored exactly.

`reading_collapse._ground`'s passive_event mode already grounds a passive
clause as `[verb, '_', patient]` — the '_' agent slot IS the raw agent-absence
signal (see reading_collapse.py's PASSIVE docstring). This module does not
touch that byte-parity-frozen predication. It mirrors domains/meaning_inference.py's
architecture exactly:

ARCHITECTURE BOUNDARY (CLAUDE.md) — ZERO Python decisions:
  · PYTHON (this module) is PURE ANNOTATION. For every "passive"-construction
    reading it writes ONE `PassivePredication{verb, patient, agent,
    agent_filled}` fact, unconditionally, whenever `read_clause` grounds a
    passive (write=True only — off the byte-parity path, exactly like
    meaning_inference's annotators). `agent`/`agent_filled` are a MECHANICAL
    read of the clause's own marker sequence — the SAME facts
    `reading_collapse._det_agent_by_phrase` and `_arg_head` already compute —
    tightly gated to the unambiguous single-clause shape [COP, PPART, BY]
    ('X was V-ed by Y', nothing else in the clause): a real corpus probe
    (tests/fixtures/reading_parity's Aesop/Grimm CORPUS group) found cases
    where a trailing BY belongs to an EMBEDDED reduced-relative participle
    ("...occasioned BY its fall...", "...forced to sing...BY themselves...")
    rather than the clause's own passive predicate; filling those would
    misattribute agency, so the gate is exact-shape, not "BY appears
    somewhere". Outside that gate, `agent_filled` stays 0.0 (honest — no
    agent claimed) exactly as the frozen `[verb, '_', patient]` predication
    already reads. There is no `if verb in AGENTIVE_VERBS` anywhere here —
    that join is the rule's, below.
  · GRAPH RULE (seeds/media_analysis.json, Rust `run_rules`) makes the WHOLE
    decision: `mint_agent_deletion` JOINS a `PassivePredication` to a held
    `AgentiveVerb{verb}` row by `Eq(pp.verb, av.verb)` — the SAME
    SelectionalClassPair join pattern meaning_inference uses — gated on
    `Eq(pp.agent_filled, 0.0)` (a by-phrase agent, when the mechanical read
    found one, is decisive: NO deletion) and deduped by a `Not Exists` guard
    on an existing `FramingObservation` for the same (verb, patient). Mints a
    REVISABLE `FramingObservation{device:'agent_deletion', verb, patient,
    confidence, revisable:1.0, note}` — the same ReadingBelief-shaped layer
    `reading_collapse._record_reading_belief` already uses for the
    passive/stative collapse. `AgentiveVerb` is TEACHABLE
    (`domains.teach.teach(agent, "AgentiveVerb", {"verb": "evict"})`) — a
    newly taught row extends coverage with NO code change, the same way
    meaning_inference's `SelectionalClassPair` rows do.
  · MECHANICAL READER: `held_framing_observations` queries the held
    `FramingObservation` nodes back out — a pure graph read, no decision.

Wired ADDITIVELY off the byte-parity path, in the SAME `if write and preds:`
block in `reading_collapse.read_clause` that already calls
`meaning_inference`'s annotators (a sibling `try/except`, so a failure here
can never mask or be masked by meaning_inference's own). Only NEW node types
(`PassivePredication`, `AgentiveVerb`, `FramingObservation`); no existing
predication/event/decompose/read_clause/heads field is read or written.
"""
from __future__ import annotations

from typing import Optional

from domains import reading_collapse as rc
from domains import reflective_faculty as rf

_SEED_ID = "media_analysis"


# --------------------------------------------------------------------------- #
#  resolution + idempotent seed load (mirrors meaning_inference's).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


def _wire_agentive_verbs_to_agent(sub, ag_node) -> None:
    """Reconcile-by-presence (the SAME idiom `meaning_inference._wire_class_pairs_to_agent`
    uses): every held `AgentiveVerb` row — seeded, or minted later by `teach()`
    — is wired to `agent` via `has_agentive_verb` so `mint_agent_deletion`'s
    join sees it without a fresh boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_agentive_verb"))
    for av in sub.nodes("AgentiveVerb"):
        if av not in wired:
            sub.add_edge(ag_node, "has_agentive_verb", av)


def _wire_relational_nouns_to_agent(sub, ag_node) -> None:
    """Reconcile-by-presence (the SAME idiom as `_wire_agentive_verbs_to_agent`):
    every held `RelationalNoun` row — seeded, or minted later by `teach()` — is
    wired to `agent` via `has_relational_noun` so `mint_unsaid_role`'s reader
    (`annotate_relational_noun`) sees it without a fresh boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_relational_noun"))
    for rn in sub.nodes("RelationalNoun"):
        if rn not in wired:
            sub.add_edge(ag_node, "has_relational_noun", rn)


def _wire_strategic_registers_to_agent(sub, ag_node) -> None:
    """Reconcile-by-presence (the SAME idiom as `_wire_agentive_verbs_to_agent`):
    every held `StrategicRegister` row — seeded, or minted later by `teach()` —
    is wired to `agent` via `has_strategic_register` so the intent-attribution
    rules' join sees it without a fresh boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_strategic_register"))
    for sr in sub.nodes("StrategicRegister"):
        if sr not in wired:
            sub.add_edge(ag_node, "has_strategic_register", sr)


def _wire_relevance_weights_to_agent(sub, ag_node) -> None:
    """Reconcile-by-presence (the SAME idiom as `_wire_agentive_verbs_to_agent`):
    every held `RelevanceWeight` row — seeded, or minted later by `teach()` — is
    wired to `agent` via `has_relevance_weight` so the intent-attribution rules'
    join sees it without a fresh boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_relevance_weight"))
    for rw in sub.nodes("RelevanceWeight"):
        if rw not in wired:
            sub.add_edge(ag_node, "has_relevance_weight", rw)


_OFFICIAL_STATEMENT_TOKENS = ["dense", "norefs", "nodefn", "impersonal",
                              "charlight", "nocontr", "flat", "proselayout"]


def _ensure_official_statement_register(agent) -> None:
    """Additively register ONE new register, `official_statement`, into
    `register_source`'s OWN dynamic codebook via its documented, public
    `add_register` ('added by hint' — an explicit named shape) extension path —
    the SAME path that module's own test suite exercises for its 'legalese'
    precedent (`tests/test_register_source.py::test_f2_new_register_addable_by_
    hint`). `register_source.py` itself is never touched. This gives POSIT
    INTENTIONALITY a REAL, non-fabricated register signal: an impersonal,
    no-contraction, no-reference-marker institutional shape (a press release /
    official announcement reads this way) is DISTINCT, by ShapeDecode's own
    verdict, from generic third-person reference prose ('encyclopedic', which
    additionally requires reference markers — dates/parentheticals) and from
    personal/contracted/punchy prose ('casual'). Idempotent (`add_register`
    itself no-ops when the name is already present)."""
    from domains import register_source as rs
    rs.add_register(agent, "official_statement", _OFFICIAL_STATEMENT_TOKENS,
                    family="institutional", read_approach="subject_by_salience",
                    source_specific="press_release")


def ensure_media_analysis_seed(agent) -> None:
    """Idempotently install the agent_deletion + unsaid_role + intent-attribution
    rules + seeded `AgentiveVerb`/`RelationalNoun`/`StrategicRegister`/
    `RelevanceWeight` join rows (seeds/media_analysis.json), register the
    `official_statement` register into register_source's own codebook, and
    reconcile-wire every held codebook row (seeded or taught since) to the
    agent root. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    if ("mint_agent_deletion" not in names or "mint_unsaid_role" not in names
            or "mint_intent_attribution_strategic" not in names):
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
    _wire_agentive_verbs_to_agent(sub, ag_node)
    _wire_relational_nouns_to_agent(sub, ag_node)
    _wire_strategic_registers_to_agent(sub, ag_node)
    _wire_relevance_weights_to_agent(sub, ag_node)
    _ensure_official_statement_register(agent)


# --------------------------------------------------------------------------- #
#  PURE ANNOTATION — facts only, no decision.
# --------------------------------------------------------------------------- #
def _existing_passive_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("PassivePredication"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("verb")), str(at.get("patient"))))
    return out


def _by_agent_head(agent, marker_seq: list, roles: list) -> str:
    """The by-phrase agent's clean head, MECHANICALLY read, iff the clause's
    WHOLE marker sequence is the unambiguous single-clause shape
    [COP, PPART, BY] — 'X was V-ed by Y' with no other marker anywhere in the
    clause. By construction of `reading_collapse._skeleton_from_words`, the
    LAST role (the final flush after the last marker) is then exactly the
    by-phrase's object; its head is read via the SAME `_arg_head` faculty
    every other role uses. Returns '' (no agent read) outside that exact
    shape — deliberately NOT triggered by "BY appears somewhere": real prose
    has BY deep inside multi-clause blobs attached to an embedded
    reduced-relative participle, not this predicate (measured against the
    frozen parity corpus's Aesop/Grimm CORPUS group — see this module's
    docstring)."""
    marker_classes = [c for c, _w in marker_seq]
    if marker_classes != ["COP", "PPART", "BY"]:
        return ""
    role_ids = [rc._norm(r) for r in roles if r.strip()]
    if len(role_ids) < 2:
        return ""
    return rc._arg_head(agent, role_ids[-1]) or ""


def annotate_passive_predication(agent, read: dict, marker_seq: list, roles: list) -> list:
    """For the ONE passive predication `read_clause` just grounded (construction
    'passive'), write a `PassivePredication{verb, patient, agent, agent_filled}`
    fact — unconditionally, whenever the reading is a passive, whether or not
    any `AgentiveVerb`/deletion rule will ever match it. `agent`/`agent_filled`
    are the mechanical by-phrase read (`_by_agent_head`); WHETHER an agentless
    reading with an agentive verb counts as rhetorical deletion is entirely
    `mint_agent_deletion`'s join, never decided here. Linked
    `agent -has_passive_predication-> pp`. Idempotent by (verb, patient).
    Returns the newly-added PassivePredication node ids."""
    sub, native, ag_node = _resolve(agent)
    if read.get("construction") != "passive" or ag_node is None:
        return []
    preds = read.get("predications") or []
    if not preds:
        return []
    ensure_media_analysis_seed(agent)
    existing = _existing_passive_keys(sub)
    by_agent = _by_agent_head(agent, marker_seq, roles)
    created: list = []
    for p in preds:
        if len(p) < 3:
            continue
        verb, patient = str(p[0]), str(p[2])
        key = (verb, patient)
        if key in existing:
            continue
        pp = sub.add_node("PassivePredication", {
            "verb": verb, "patient": patient,
            "agent": by_agent, "agent_filled": 1.0 if by_agent else 0.0,
        })
        sub.add_edge(ag_node, "has_passive_predication", pp)
        existing.add(key)
        created.append(pp)
    if created:
        native_steps = native.run_rules()
        receipt = sub.add_node("NativeMediaAnalysisReceipt", {
            "schema": "native_media_analysis_receipt.v1",
            "cluster": "media_analysis.passive_settlement",
            "provenance": "native_rule_readback:passive_analysis",
            "native_rule": "media_analysis_passive_rules",
            "passive_count": len(created),
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        native.add_edge_unchecked(
            ag_node, "has_native_media_analysis_receipt", receipt)
    # POSIT INTENTIONALITY (additive) — any FramingObservation this call's
    # run_rules() just minted (or one already held from an earlier call) now
    # gets its signals annotated, keyed to THIS clause's own text. See
    # `annotate_intent_signals`'s docstring below.
    annotate_intent_signals(agent, read.get("clause"))
    return created


# --------------------------------------------------------------------------- #
#  MECHANICAL READER — query the held FramingObservation beliefs back out
#  (mirrors meaning_inference.held_inferred_senses).
# --------------------------------------------------------------------------- #
def held_framing_observations(agent, device: Optional[str] = None) -> list:
    """The agent's held `FramingObservation` beliefs, optionally filtered to
    one `device` ('agent_deletion'). Pure graph read — no decision."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("FramingObservation"):
        at = sub.node(nd)["attrs"]
        if device is not None and at.get("device") != device:
            continue
        out.append({"device": at.get("device"), "verb": at.get("verb"),
                    "patient": at.get("patient"), "confidence": at.get("confidence"),
                    "revisable": at.get("revisable"), "note": at.get("note")})
    return out


# =========================================================================== #
#  UNSAID ROLE — the residual of a RELATIONAL NOUN / nominalization.
#
#  Generalises agent-deletion (there, the verb's AGENT role is the residual)
#  to NOMINAL hosts: a relational noun's shape is REL(holder, complement:?),
#  and an unfilled complement slot is a residual — "a right to WHAT?", "the
#  killing OF WHOM?", "killed BY WHOM?". DETECT, DO NOT FILL: the output is
#  the FORMULATED QUESTION, never an answer. Detecting the shape needs only
#  the noun (a held codebook row) and whether its expected complement marker
#  sits immediately after it in the clause's own recognised tokens — zero
#  world knowledge. Filling it (-> "slavery") needs the world and is
#  explicitly out of scope.
#
#  ZERO PYTHON DECISIONS: `annotate_relational_noun` only writes a MECHANICAL,
#  CODEBOOK-INDEPENDENT structural fact — one `NominalMention{noun, next_word}`
#  per distinct (regular-plural-normalised) content-word lemma in the clause,
#  UNCONDITIONALLY, for every clause read, regardless of whether that lemma is
#  CURRENTLY a held RelationalNoun. This is deliberate, and mirrors WHY
#  `PassivePredication` is written unconditionally over every passive
#  (never gated on AgentiveVerb membership): an EARLIER design gated
#  NominalMention-writing on "does this word already match a held
#  RelationalNoun row" and precomputed `complement_present` right there in
#  Python — it passed every gate EXCEPT teach-extends, because a lemma taught
#  AFTER the clause was read had produced no fact to join against. Recording
#  the (lemma, next_word) pair unconditionally, and pushing the
#  codebook-relative comparison into the RULE, fixes that: the SAME
#  `NominalMention` fact stays there, and re-running rules after teaching a
#  new `RelationalNoun` row (`test_agent_teaches_new_relational_noun`, mirror
#  of `test_agent_teaches_new_agentive_verb`) finds and joins it with no
#  re-read, no code change.
#
#  `RelationalNoun{noun, complement_role, theme, question}` is the scalar-row
#  codebook (a noun with several expected complements — 'killing'->of/by — is
#  several rows), TEACHABLE via domains.teach.teach(agent, 'RelationalNoun',
#  {...}) with NO code change. The rule (`mint_unsaid_role`,
#  seeds/media_analysis.json) makes the WHOLE decision: JOINS a
#  `NominalMention` to a `RelationalNoun` row by Eq(nm.noun, rn.noun), gated on
#  Not(Eq(nm.next_word, rn.complement_role)) — the token immediately following
#  the noun is NOT the row's expected marker, i.e. the complement is absent —
#  the exact-adjacency counterpart of `_by_agent_head`'s by-phrase read (not
#  "the marker appears somewhere in the clause"; see the residual note below).
#  Deduped by a Not-Exists guard on an existing UnsaidRole for the same (host,
#  role). Mints a REVISABLE `UnsaidRole{host, role, theme, question,
#  filled:0.0, revisable:1.0, note}` — the QUESTION, never a filled value.
#  There is no `if complement_present == 0`, and no `if word in
#  relational_nouns`, anywhere in this module.
#
#  WIRING: `annotate_relational_noun` is called from a WRITE-GATED hook in
#  `reading_collapse.read_clause`, placed BEFORE the `if not skeleton:` /
#  `if write and preds:` gates (not reusing the existing preds-gated
#  media_analysis hook) — a relational noun's own local complement is a
#  property of ITS neighbourhood, not of whether the surrounding clause
#  happened to ground a full predication ("The crackdown continued." has no
#  VERB/COP the reader can construct at all, yet 'crackdown' still needs its
#  'on'-complement checked). It receives `words`, the SAME already-recognised
#  token list `read_clause` computed for this clause (the reader's own
#  tokenisation — no fresh parse, no regex).
#
#  HONEST RESIDUAL: exact-adjacency means a complement realised NON-adjacently
#  (e.g. "the killing of the civilians BY the soldiers" — 'by' present but not
#  immediately after 'killing') is mis-read as absent. Scanning further would
#  need a principled clause-boundary signal (e.g. stop at the next verb) this
#  module does not attempt — gated, not faked, and not exercised by any
#  required test. Plural matching is a REGULAR (-s) strip only
#  (`_regular_singular`), not a lemmatizer — an irregular plural is a
#  documented gap, not silently mishandled. `NominalMention` records only the
#  FIRST occurrence of a given lemma per agent (cross-clause, like
#  `PassivePredication`'s (verb,patient) key) — a second clause introducing
#  the same noun word on the same agent will not get a fresh adjacency read;
#  every gate below uses a fresh single-clause agent (the project's own
#  documented isolation-testing lesson), so this never bites here.
# --------------------------------------------------------------------------- #
def _regular_singular(word: str) -> str:
    """The word's regular (-s) singular via plain string slicing — NOT a
    lemmatizer, NOT regex. Covers the common case the seeded RelationalNoun
    rows need ('rights'->'right', 'deaths'->'death'); an irregular plural is
    an honest, documented residual (see module docstring above)."""
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _existing_nominal_lemmas(sub) -> set:
    out = set()
    for nd in sub.nodes("NominalMention"):
        at = sub.node(nd)["attrs"]
        out.add(str(at.get("noun")))
    return out


def annotate_relational_noun(agent, out: dict, words: list) -> list:
    """For the clause `read_clause` just recognised, write ONE
    `NominalMention{noun, next_word}` fact per distinct content-word lemma —
    UNCONDITIONALLY, regardless of whether that lemma is currently a held
    RelationalNoun (see the module docstring above for why: gating here would
    break TEACH-EXTENDS), and regardless of whether the clause grounded any
    predication at all. `words` is the SAME already-recognised token list
    `read_clause` computed for this clause. `noun` is the token's REGULAR
    (-s) singular (`_regular_singular`); `next_word` is the immediately
    following recognised token, or `''` if the lemma is clause-final — a
    purely MECHANICAL structural read, no codebook lookup. Closed-class glue
    (determiner/preposition/aux, via the SAME `reading_collapse` tables the
    reader itself consults) is skipped — never a candidate noun host. Only
    the FIRST occurrence of a given lemma is recorded. Returns the newly-
    added NominalMention node ids."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None or not words:
        return []
    ensure_media_analysis_seed(agent)
    lw = [str(w).lower() for w in words]
    existing = _existing_nominal_lemmas(sub)
    created: list = []
    seen: set = set()
    for i, w in enumerate(lw):
        if w in rc._DETERMINERS or w in rc._PP_PREPS or w in rc._AUX:
            continue
        lemma = _regular_singular(w)
        if lemma in seen or lemma in existing:
            continue
        seen.add(lemma)
        nxt = lw[i + 1] if i + 1 < len(lw) else ""
        nm = sub.add_node("NominalMention", {"noun": lemma, "next_word": nxt})
        sub.add_edge(ag_node, "has_nominal_mention", nm)
        existing.add(lemma)
        created.append(nm)
    if created:
        native_steps = native.run_rules()
        receipt = sub.add_node("NativeMediaAnalysisReceipt", {
            "schema": "native_media_analysis_receipt.v1",
            "cluster": "media_analysis.relational_noun_settlement",
            "provenance": "native_rule_readback:relational_noun_analysis",
            "native_rule": "media_analysis_relational_noun_rules",
            "mention_count": len(created),
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        native.add_edge_unchecked(
            ag_node, "has_native_media_analysis_receipt", receipt)
    # POSIT INTENTIONALITY (additive) — any UnsaidRole this call's run_rules()
    # just minted (or one already held from an earlier call) now gets its
    # signals annotated, keyed to THIS clause's own text.
    annotate_intent_signals(agent, out.get("clause"))
    return created


def held_unsaid_roles(agent) -> list:
    """The agent's held `UnsaidRole` beliefs — the formulated questions for
    every detected residual, never an answer. Pure graph read — no
    decision."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("UnsaidRole"):
        at = sub.node(nd)["attrs"]
        out.append({"host": at.get("host"), "role": at.get("role"), "theme": at.get("theme"),
                    "question": at.get("question"), "filled": at.get("filled"),
                    "revisable": at.get("revisable"), "note": at.get("note")})
    return out


# =========================================================================== #
#  POSIT INTENTIONALITY — given a residual (a FramingObservation agent_deletion
#  OR an UnsaidRole), POSIT whether the omission is STRATEGIC (a rhetorical
#  euphemism/agency-hiding move) or INCIDENTAL, GRADED and DEFEASIBLE, honestly
#  UNDETERMINED when the signal is thin. The canonical case: "states' rights"
#  in a political/official register posits STRATEGIC; the bare phrase with no
#  register context posits UNDETERMINED — the SAME residual, a different
#  context, a different (revisable) judgment.
#
#  THREE SIGNAL FAMILIES, combined (mirrors reading_collapse's passive-lean
#  Σ-weight/threshold shape, but the combine + the three-way posit DECISION
#  live in the seed rules below, not in Python — this module only writes
#  mechanical facts, exactly like PassivePredication/NominalMention):
#
#   1. REGISTER — `register_source.decode_register`'s own verdict, gated on
#      ITS OWN `confident` flag: a bare, short residual clause is honestly
#      NOT confident (`register_source._MIN_CONFIDENT_WORDS` — no fabrication),
#      so `register` is written as '' (the codebook's own zero-weight row).
#      `ensure_media_analysis_seed` additively teaches `register_source` ONE
#      new register, `official_statement` (impersonal / no contraction / no
#      reference marker — a press-release/official-announcement shape), via
#      that module's own public, documented `add_register` extension path
#      (mirrors its test suite's 'legalese' precedent) — so a REAL ShapeDecode
#      verdict, not a Python register table, drives the strategic signal.
#   2. RELEVANCE (Gricean) — a competent speaker's omission of a HIGH-
#      relevance role (the AGENT of an agentive/violent verb; a relational
#      noun's DEFINING complement — 'to' on 'right', 'of'/'by' on 'killing')
#      is a MARKED omission (a quantity-maxim flout); a routinely-omitted role
#      (e.g. 'growth OF what' in casual mention) is LOW-relevance. Looked up
#      via `relevance_key`, a MECHANICAL structural key built from the
#      residual's own fields — 'verb:<verb>' or 'role:<host>:<role>' — no
#      weight, no lookup, just the join key the rule uses.
#   3. SOURCE — GATED. `source_provenance.py` requires an explicit `source`
#      label a bare-clause residual simply does not carry;
#      wiring it here for a residual with no attached source would be
#      fabrication, not signal. `source_weight` is a Lit 0.0 on every mint
#      rule, and `basis` says so honestly. Register + relevance alone is a
#      legitimate first posit.
#
#  `IntentSignal{residual_type, residual_ref, verb, host, role, register,
#  relevance_key}` is written UNCONDITIONALLY, once per held residual (deduped
#  by `residual_ref`) — the same "write the fact regardless of whether a rule
#  will ever join it" discipline `PassivePredication`/`NominalMention` use.
#  `StrategicRegister{register, strategic_weight}` and `RelevanceWeight{key,
#  relevance_weight}` are the two TEACHABLE codebooks
#  (`domains.teach.teach(agent, 'StrategicRegister'/'RelevanceWeight', {...})`)
#  the three seed rules (`mint_intent_attribution_strategic`/`_incidental`/
#  `_undetermined`, seeds/media_analysis.json) JOIN against and Gte/Lte/Gt+Lt-
#  gate a `Plus(sr.strategic_weight, rw.relevance_weight)` against the SAME two
#  held thresholds (0.7 strategic, 0.15 incidental) to mint a REVISABLE
#  `IntentAttribution{residual_ref, residual_type, posit, confidence, register,
#  register_weight, relevance_weight, source_weight, basis, revisable:1.0,
#  note}` — `posit`/`basis` are Lit values on the MATCHING rule; there is no
#  `if confidence >= X: posit = 'strategic'` anywhere in this file.
# --------------------------------------------------------------------------- #
def _relevance_key(residual_type: str, verb: str, host: str, role: str) -> str:
    """The MECHANICAL structural join key for `RelevanceWeight` — built from
    the residual's own fields, never a weight or a decision. String shaping
    only (the same status as `NominalMention.next_word` or `_by_agent_head`'s
    structural read), not a semantic judgment."""
    if residual_type == "agent_deletion":
        return "verb:%s" % verb
    return "role:%s:%s" % (host, role)


def _confident_register(agent, text: Optional[str]) -> str:
    """The register `register_source.decode_register` (no hint — the pure
    by-shape read) verdicts for `text`, gated on ITS OWN `confident` flag.
    Returns '' (the codebook's honest zero-weight row) when there is no text,
    or the shape evidence is not confident — a short bare clause never
    fabricates a register. Local import (this module's established idiom for
    cross-domain calls): register_source is not otherwise on media_analysis's
    load path, so this keeps it that way."""
    if not text:
        return ""
    from domains import register_source as rs
    d = rs.decode_register(agent, str(text))
    return str(d.get("register") or "") if d.get("confident") else ""


def _existing_intent_signal_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("IntentSignal"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("residual_type")), str(at.get("residual_ref"))))
    return out


def annotate_intent_signals(agent, text: Optional[str]) -> list:
    """For every held residual (FramingObservation{device:'agent_deletion'} OR
    UnsaidRole) that does not yet have an `IntentSignal`, write ONE —
    UNCONDITIONALLY, register/relevance-key only, no weight, no posit. `text`
    is THIS call's own clause text (`read.get('clause')` / `out.get('clause')`)
    — the register is read ONCE, at the moment a residual first becomes
    available, and is never re-read for an already-signalled residual (the
    SAME "record it once" idiom `PassivePredication`/`NominalMention` use for
    their own dedup keys). Runs `native.run_rules()` when it wrote anything, so
    the intent-attribution rules see the new facts immediately. Returns the
    newly-added IntentSignal node ids."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    register = _confident_register(agent, text)
    existing = _existing_intent_signal_keys(sub)
    created: list = []
    for nd in sub.nodes("FramingObservation"):
        at = sub.node(nd)["attrs"]
        if at.get("device") != "agent_deletion":
            continue
        verb = str(at.get("verb"))
        ref = "%s|%s" % (verb, at.get("patient"))
        key = ("agent_deletion", ref)
        if key in existing:
            continue
        sig = sub.add_node("IntentSignal", {
            "residual_type": "agent_deletion", "residual_ref": ref,
            "verb": verb, "host": "", "role": "",
            "relevance_key": _relevance_key("agent_deletion", verb, "", ""),
            "register": register,
        })
        sub.add_edge(ag_node, "has_intent_signal", sig)
        existing.add(key)
        created.append(sig)
    for nd in sub.nodes("UnsaidRole"):
        at = sub.node(nd)["attrs"]
        host, role = str(at.get("host")), str(at.get("role"))
        ref = "%s|%s" % (host, role)
        key = ("unsaid_role", ref)
        if key in existing:
            continue
        sig = sub.add_node("IntentSignal", {
            "residual_type": "unsaid_role", "residual_ref": ref,
            "verb": "", "host": host, "role": role,
            "relevance_key": _relevance_key("unsaid_role", "", host, role),
            "register": register,
        })
        sub.add_edge(ag_node, "has_intent_signal", sig)
        existing.add(key)
        created.append(sig)
    if created:
        native_steps = native.run_rules()
        receipt = sub.add_node("NativeMediaAnalysisReceipt", {
            "schema": "native_media_analysis_receipt.v1",
            "cluster": "media_analysis.intent_signal_settlement",
            "provenance": "native_rule_readback:intent_signal_analysis",
            "native_rule": "media_analysis_intent_signal_rules",
            "signal_count": len(created),
            "native_steps": int(native_steps),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        native.add_edge_unchecked(
            ag_node, "has_native_media_analysis_receipt", receipt)
    return created


def held_intent_attributions(agent, posit: Optional[str] = None) -> list:
    """The agent's held `IntentAttribution` beliefs, optionally filtered to one
    `posit` ('strategic' | 'incidental' | 'undetermined'). Pure graph read —
    no decision."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("IntentAttribution"):
        at = sub.node(nd)["attrs"]
        if posit is not None and at.get("posit") != posit:
            continue
        out.append({
            "residual_ref": at.get("residual_ref"), "residual_type": at.get("residual_type"),
            "posit": at.get("posit"), "confidence": at.get("confidence"),
            "register": at.get("register"), "register_weight": at.get("register_weight"),
            "relevance_weight": at.get("relevance_weight"), "source_weight": at.get("source_weight"),
            "basis": at.get("basis"), "revisable": at.get("revisable"), "note": at.get("note"),
        })
    return out
