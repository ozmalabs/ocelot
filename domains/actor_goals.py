"""actor_goals — ABDUCTIVE EXPLANATION of a THIRD-PARTY actor's behaviour, the
opening slice of the "reverse-engineer the actor's goal" arc. This is about an
actor DESCRIBED IN TEXT (e.g. "the oil company" in a news sentence) — NEVER
the conversation partner (that is domains/interlocutor_model.py's business;
this module does not touch it, import it, or read from it).

Mirrors domains/media_analysis.py's architecture exactly (studied as the
template): a MECHANICAL annotator writes facts unconditionally from what
`reading_collapse.read_clause` already grounds; TEACHABLE codebooks hold the
world knowledge; SEED RULES (Eq-joins + guards) make every decision; a
MECHANICAL reader queries the result back out. Zero Python decisions.

THREE THINGS, for a third-party actor:

  1. AGENCY — is the actor the action's AUTHOR (its agent/subject) or its
     RECIPIENT (its patient/beneficiary)? `annotate_actor_action` writes ONE
     `ActorAction{actor, verb, object, object_domain, actor_role}` fact per
     actor-bearing predication `read_clause` just grounded — `actor_role` is
     the RAW STRUCTURAL read ('agent' — the predication's subject-position
     argument; see the PASSIVE note below for the by-phrase case). `verb` is
     ALWAYS run through `reading_collapse._participle_lemma` (a held WordNet
     morphy read, mechanical — the SAME faculty the passive path already uses
     to reduce 'evicted'->'evict') so an active-voice inflected surface
     ('funded') and a passive-voice already-lemmatised base ('fund') key the
     SAME codebook row. There is no `if verb in ...` anywhere in this file —
     the codebook join is the rule's.

     The FINAL semantic label (author vs recipient) is NOT decided here: a
     verb whose grammatical subject conventionally names the RECEIVING
     participant rather than the causer (Levin's experiencer/goal-subject
     class — receive/get/accept/obtain) is a SEPARATE teachable codebook,
     `RecipientVerb{verb}`, and it is the matching RULE
     (`mint_actor_goal_recipient`, seeds/actor_goals.json) that relabels the
     resulting `ActorGoal.agency` to 'recipient' via Eq(aa.verb, rv.verb) —
     never a Python `if verb == "received"`. "The company received a grant."
     structurally reads 'company' as the predication's subject-position
     argument (actor_role stays the honest structural fact, 'agent') exactly
     like any other subject; the codebook JOIN is what tells the rule this
     particular verb's subject is semantically a recipient, not the Python
     annotator guessing verb semantics.

  2. SURFACE GOAL — `ActionGoal{verb, goal}` is the teachable codebook
     (fund/sponsor/donate/back/finance -> 'support'); `mint_actor_goal`
     (seeds/actor_goals.json) JOINS an author-role ActorAction to it by
     Eq(verb) and mints a candidate `ActorGoal{actor, surface_goal, object,
     agency:'author'}` — `object` is the action's own object DOMAIN (see
     `_object_domain` below), never a fabricated goal value.

  3. THE LAYERED-GOAL SIGNAL (the headline case — "oil company funds
     renewables"). `ActorProfile{actor, core_interest, opposes}` is the
     second teachable codebook (a HANDFUL, illustrative: oil_company ->
     fossil_fuels vs renewable_energy; cigarette_company -> smoking vs
     quit-smoking). `flag_conflicting_meta_goal` JOINS an author ActorGoal to
     an ActorProfile by Eq(actor), gated on Eq(profile.opposes,
     goal.object) — the actor's DECLARED core interest conflicts with THIS
     action's own object domain — and mints `serves_conflicting_meta_goal:
     1.0` + the raw conflict fields, never a fabricated hidden-goal VALUE
     (DETECT, DO NOT FILL — see the module-level semantics note below).

  SEMANTICS OF THE FLAG — READ THIS BEFORE USING IT. This is NOT "the
  surface action is fake" and it is NOT "the funded engineers/recipients are
  complicit." The project's governing principle is that MANY THINGS ARE TRUE
  AT THE SAME TIME: an oil company's funded renewable-energy project can be
  entirely genuine, competently run, and produce real good — AND the funder
  can simultaneously hold a higher-level goal that conflicts with the
  project's own object domain. Both are true at once; the flag asserts only
  the SECOND thing, about the FUNDER's own goal layer, never about the
  funded object or its recipients/beneficiaries. `serves_conflicting_meta_
  goal` means "this actor's action ALSO plausibly serves a higher-level goal
  that conflicts with the action's surface object" — it is a claim about
  ONE MORE layer coexisting with the genuine one, not a claim that the
  genuine layer is false. No rule in this seed ever attributes anything to
  the object/beneficiary of the action (the renewable-energy project, its
  engineers, the quit-smoking program) — every mint/set effect below is
  scoped to the FUNDER's own ActorGoal node.

  THE FLAG IS ALSO MECHANISM-AGNOSTIC. A surface-goal-vs-actor-interest
  conflict is consistent with at least TWO DISTINCT mechanisms a single act
  cannot discriminate between: (a) DECEPTION — the actor knows the
  divergent goal and does not state it (deliberate); (b) an INTROSPECTION
  GAP — the actor sincerely believes the stated reason, and it is not
  deliberately hidden, but it is not the actual driver either
  (Nisbett-Wilson confabulation — NOT deliberate, NOT culpable). Neither
  this module nor its seed rule ever picks between them: `mechanism`
  is written literally as `'undetermined'` on every flagged ActorGoal, and
  no basis string anywhere below uses a word ("strategic", "deliberate",
  "deceptive", "insincere", ...) that would assert one mechanism over the
  other. What is detected is the STRUCTURAL conflict only.

  HONEST RESIDUAL — SINGLE-ACT vs PATTERN. A single funding act only makes
  the conflicting meta-goal a DEFEASIBLE POSSIBILITY — `revisable:1.0`,
  never a conclusion. Stronger evidence of an actual divergent goal (of
  either mechanism above) is a PATTERN ACROSS ACTIONS OVER TIME (fund the
  design, then lobby against its adoption; publicise the fund, stay silent
  on outcomes) — named schemas for that cross-action pattern (Trojan Horse,
  Guilt-Based Action, ...) live at that temporal/cross-action grain and are
  an explicit LATER SLICE, out of scope here. This slice detects the
  single-act STRUCTURAL conflict only.

ARCHITECTURE BOUNDARY (CLAUDE.md) — ZERO Python decisions: this module only
WRITES FACTS (`ActorAction`, mechanically, from the predication + marker
structure `read_clause` already computed) and READS beliefs back out
(`held_actor_goals`). The seed rules in seeds/actor_goals.json make every
decision: which verb counts as author-goal-bearing (`mint_actor_goal`),
which verb's subject is a recipient (`mint_actor_goal_recipient`), and
whether an actor's declared interest conflicts with an action's object
(`flag_conflicting_meta_goal`). All three codebooks (`ActionGoal`,
`RecipientVerb`, `ActorProfile`) are TEACHABLE via `domains.teach.teach`
with no code change.

WIRED via ONE additive, write-gated hook in `reading_collapse.read_clause`'s
existing `if write and preds:` block (a sibling try/except alongside the
meaning_inference / media_analysis calls already there — a failure here can
never mask or be masked by theirs). Only NEW node types (`ActorAction`,
`ActionGoal`, `RecipientVerb`, `ActorProfile`, `ActorGoal`); no existing
predication/event/decompose/read_clause/heads field is read or written, and
this module never imports or touches domains/interlocutor_model.py,
domains/reflective_faculty.py, domains/world_adapter.py, or any
conversation/intent seed.

THE COMPOUND-ACTOR PARSE RESIDUAL (measured, not assumed — see the probe
this module's test suite documents). `reading_collapse`'s bare-active-voice
S-V-O fallback (`_skeleton_from_words`'s trailing loop) picks the FIRST
content word (starting at index 1) that WordNet marks verb-headed as the
clause's VERB marker; for a two-word premodified actor compound whose HEAD
NOUN itself has a rare verb sense in WordNet ('company' — archaic "to
company with"), that head noun wins the marker slot instead of the real verb
('funded'), and the whole predication mis-splits ("The oil company funded a
renewable energy project." grounds as `['company', 'oil',
'funded_renewable_energy_project']` — verb='company', not 'fund'; actor=
'oil', not 'oil_company'). This is a documented, PRE-EXISTING reading-layer
limitation this module builds ON, not around (fixing `_skeleton_from_words`'s
verb-selection ladder is out of this slice's scope, and reading_collapse.py
is not this slice's file to rewrite). The workaround this module's own test
corpus uses for a compound actor is the SAME passive-with-by-phrase route
domains/media_analysis.py already exploits for exactly this reason: a
passive clause's by-phrase agent is read via the clause's OWN marker
sequence, not the buggy bare-SVO fallback, so "A renewable energy project
was funded by the oil company." parses cleanly (verb='fund', patient=
'renewable_energy_project', by-phrase='oil company'). Unlike
`media_analysis._by_agent_head` (which reduces the by-phrase through
`reading_collapse._arg_head`'s WordNet-compound-preferring head extraction —
correct for 'oil company', a real WordNet compound, but LOSSY for
'cigarette company'/'coal company', which are not held compounds and reduce
to the bare head 'company', erasing the very modifier that distinguishes one
profiled actor from another), `_by_phrase_actor_raw` below reads the RAW
un-reduced by-phrase role span instead — the SAME `reading_collapse._norm`
underscore-join every other role span uses, deliberately WITHOUT the
head-reduction step, so 'cigarette company' and 'coal company' keep their
distinguishing modifier and can be looked up in `ActorProfile` by their own
surface name. Single-word active-voice actors ("The charity funded...",
"The company received...") need no such route — the bare-SVO fallback never
tests the clause-initial word, so a one-word actor is byte-clean already.
A genuinely mangled multi-word ACTIVE-voice actor phrase (no passive
rephrasing available) is an honest, undetected residual: this module writes
no ActorAction from an unrecoverable predication rather than fabricate one
from a glued verb+object blob.
"""
from __future__ import annotations

from typing import Optional

from domains import reading_collapse as rc

_SEED_ID = "actor_goals"


# --------------------------------------------------------------------------- #
#  resolution + idempotent seed load (mirrors media_analysis.py's).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        from domains import reflective_faculty as rf
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


def _wire_by_type(sub, ag_node, node_type: str, edge_type: str) -> None:
    """Reconcile-by-presence (the SAME idiom
    `media_analysis._wire_agentive_verbs_to_agent` uses): every held row of
    `node_type` — seeded, or minted later by `teach()` — is wired to `agent`
    via `edge_type` so the matching rule's join sees it without a fresh
    boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, edge_type))
    for n in sub.nodes(node_type):
        if n not in wired:
            sub.add_edge(ag_node, edge_type, n)


def ensure_actor_goals_seed(agent) -> None:
    """Idempotently install the actor-goals rules + seeded `ActionGoal`/
    `RecipientVerb`/`ActorProfile` codebook rows (seeds/actor_goals.json),
    and reconcile-wire every held codebook row (seeded or taught since) to
    the agent root. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    if ("mint_actor_goal" not in names or "mint_actor_goal_recipient" not in names
            or "flag_conflicting_meta_goal" not in names):
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
    _wire_by_type(sub, ag_node, "ActionGoal", "has_action_goal")
    _wire_by_type(sub, ag_node, "RecipientVerb", "has_recipient_verb")
    _wire_by_type(sub, ag_node, "ActorProfile", "has_actor_profile")


# --------------------------------------------------------------------------- #
#  PURE ANNOTATION — facts only, no decision.
# --------------------------------------------------------------------------- #
def _object_domain(object_span: str) -> str:
    """The object's DOMAIN category — a MECHANICAL, position-based token
    drop: the object role span's already-underscore-joined surface
    ('renewable_energy_project') with its FINAL token (assumed the head
    noun — 'project'/'startup'/'program') removed, keeping the premodifier
    run ('renewable_energy') that carries the domain content an
    `ActorProfile.opposes` row is written against. A single-token object
    ('grant') has no premodifier to keep and reads as '' — honest absence,
    never a guess. Pure string-shape (no `import re`, no lexicon lookup, no
    decision about what the domain MEANS) — the same status as
    `media_analysis._regular_singular`'s plain slicing."""
    s = str(object_span)
    if "_" not in s:
        return ""
    return s.rsplit("_", 1)[0]


def _by_phrase_actor_raw(marker_seq: list, roles: list) -> str:
    """The RAW (un-head-reduced) by-phrase actor span, MECHANICALLY read,
    under the SAME tightly-gated single-clause shape
    `media_analysis._by_agent_head` uses ([COP, PPART, BY], nothing else in
    the clause) — duplicated here deliberately rather than called into,
    because this module needs the UN-REDUCED span (`reading_collapse._norm`
    only) rather than `_by_agent_head`'s `_arg_head`-reduced head, to keep a
    non-WordNet-compound actor's distinguishing modifier ('coal company' ->
    'coal_company', not the bare head 'company') — see the module docstring's
    COMPOUND-ACTOR PARSE RESIDUAL note. Returns '' outside the exact gate —
    no by-phrase agent named, honestly nothing to report."""
    marker_classes = [c for c, _w in marker_seq]
    if marker_classes != ["COP", "PPART", "BY"]:
        return ""
    if len(roles) < 2:
        return ""
    last = roles[-1]
    if not str(last).strip():
        return ""
    return rc._norm(last)


def _existing_actor_action_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("ActorAction"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("actor")), str(at.get("verb")), str(at.get("object"))))
    return out


def annotate_actor_action(agent, out: dict, marker_seq: list, roles: list) -> list:
    """For every actor-bearing predication `read_clause` just grounded, write
    ONE `ActorAction{actor, verb, object, object_domain, actor_role}` fact —
    UNCONDITIONALLY, no codebook check, no decision about whether the verb
    or actor will ever match anything. Two structural shapes:

      · a PASSIVE clause's by-phrase agent (predication `[verb, '_',
        patient]`, `construction=='passive'`): actor is the RAW by-phrase
        span (`_by_phrase_actor_raw`) — a by-phrase names the semantic
        AGENT by construction, so `actor_role='agent'`. No by-phrase found
        (the exact-shape gate declines, or the passive is agentless) ->
        nothing written for that predication — honest, no fabrication (the
        SAME discipline `PassivePredication.agent_filled==0.0` already
        uses one layer down).
      · any other predication `[pred, a, b]` (len>=3) whose first argument
        is a real span (not the passive placeholder '_'): `a` is the
        predication's SUBJECT-position argument -- the mechanical
        structural read this module treats as `actor_role='agent'`
        (subject vs object/oblique; see the module docstring's AGENCY
        section for why the SEMANTIC author/recipient label is a separate,
        rule-decided question from this raw structural fact).

    `verb` is always run through `reading_collapse._participle_lemma` (a
    held WordNet morphy read) so an inflected active surface ('funded') and
    an already-lemmatised passive surface ('fund') key the same codebook
    row. Idempotent by (actor, verb, object). Returns the newly-added
    ActorAction node ids."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    preds = out.get("predications") or []
    if not preds:
        return []
    ensure_actor_goals_seed(agent)
    construction = out.get("construction")
    existing = _existing_actor_action_keys(sub)
    created: list = []
    for p in preds:
        if len(p) < 3:
            continue
        verb_raw, a, b = p[0], p[1], p[2]
        if construction == "passive" and a == "_":
            actor = _by_phrase_actor_raw(marker_seq, roles)
            if not actor:
                continue
            object_ = str(b)
        elif a and a != "_":
            actor = str(a)
            object_ = str(b)
        else:
            continue
        verb = rc._participle_lemma(verb_raw)
        key = (actor, verb, object_)
        if key in existing:
            continue
        node = sub.add_node("ActorAction", {
            "actor": actor, "verb": verb, "object": object_,
            "object_domain": _object_domain(object_), "actor_role": "agent",
        })
        sub.add_edge(ag_node, "has_actor_action", node)
        existing.add(key)
        created.append(node)
    if created:
        native.run_rules()
    return created


# --------------------------------------------------------------------------- #
#  MECHANICAL READER — query the held ActorGoal beliefs back out.
# --------------------------------------------------------------------------- #
def held_actor_goals(agent, agency: Optional[str] = None) -> list:
    """The agent's held `ActorGoal` beliefs, optionally filtered to one
    `agency` ('author' | 'recipient'). Pure graph read — no decision. `basis`
    is a MECHANICAL string rendering (never a decision) of the raw
    `meta_goal_core_interest`/`meta_goal_opposes`/`mechanism` fields the
    `flag_conflicting_meta_goal` rule set — see the module docstring's
    SEMANTICS note: this describes a conflict in the actor's OWN goal layer,
    never a claim about the funded object or its recipients, and it is
    MECHANISM-AGNOSTIC — the rendering never asserts deception/deliberateness
    (the rule only ever writes `mechanism:'undetermined'`; this reader only
    ever echoes that literal value, never picks a mechanism itself)."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("ActorGoal"):
        at = sub.node(nd)["attrs"]
        if agency is not None and at.get("agency") != agency:
            continue
        basis = ""
        if at.get("serves_conflicting_meta_goal"):
            basis = ("this action's surface object (%r) conflicts with the actor's "
                      "declared core interest (%r); the actor's action may ALSO serve "
                      "a divergent higher-level goal -- mechanism (deliberate vs "
                      "sincere-but-self-opaque) %s at single-act grain, a defeasible "
                      "possibility only, about the ACTOR's own goal layer, never a "
                      "claim about this action's object or its recipients"
                      % (at.get("meta_goal_opposes"), at.get("meta_goal_core_interest"),
                         str(at.get("mechanism") or "undetermined").upper()))
        out.append({
            "actor": at.get("actor"), "verb": at.get("verb"), "agency": at.get("agency"),
            "surface_goal": at.get("surface_goal"), "object": at.get("object"),
            "serves_conflicting_meta_goal": at.get("serves_conflicting_meta_goal"),
            "meta_goal_core_interest": at.get("meta_goal_core_interest"),
            "meta_goal_opposes": at.get("meta_goal_opposes"),
            "mechanism": at.get("mechanism"),
            "basis": basis,
            "revisable": at.get("revisable"),
        })
    return out


# --------------------------------------------------------------------------- #
#  CONFLICTING / MULTIPLE GOALS — the first "climb" layer.
#
#  A DISCLAIMER/hedge ("I'm not racist, but ...", "no offense, but ...",
#  "with all due respect, ...") signals TWO goals in tension: goal-A (express
#  the content) AND goal-B (avoid its social cost). This slice detects it as a
#  classify-by-codebook-JOIN — the SAME architecture as media_analysis's
#  AffixCandidate morphology (a MECHANICAL annotator emits candidates
#  UNCONDITIONALLY; a TEACHABLE codebook holds the world knowledge; an
#  AGENT-AUTHORED seed rule makes the decision by an Eq-join; a MECHANICAL
#  reader queries it back out).
#
#  The rule itself is NOT hand-written here: the agent AUTHORS it from a plain
#  method + the taught codebook via procedural_reader.read_method ->
#  binding_resolver.derive_binding -> method_synthesis.synthesise_rule_from_method.
#  This file contributes ONLY (1) a mechanical n-gram annotator (no decision —
#  emits EVERY contiguous word n-gram), (2) codebook wiring (reconcile-by-
#  presence, so teach()-ed cue rows reach the rule's join), and (3) a reader.
# --------------------------------------------------------------------------- #
_DISCLAIMER_MIN_N = 2
_DISCLAIMER_MAX_N = 6
_DISCLAIMER_PUNCT = ".,?!;:\"'()[]{}"


def _utterance_ngrams(utterance: str,
                      min_n: int = _DISCLAIMER_MIN_N,
                      max_n: int = _DISCLAIMER_MAX_N) -> list:
    """EVERY contiguous lowercased word n-gram (len min_n..max_n) of the
    utterance — pure mechanical `str` work (lower + split + per-word
    punctuation strip + space-join), NO `import re`, NO decision about which
    n-grams could be a disclaimer. The codebook JOIN in the AGENT-AUTHORED
    rule decides which phrase matters; this only enumerates. Deduped by phrase
    (a repeated phrase yields one candidate)."""
    words: list = []
    for raw in str(utterance).lower().split():
        w = raw.strip(_DISCLAIMER_PUNCT)
        if w:
            words.append(w)
    out: list = []
    seen: set = set()
    for n in range(min_n, max_n + 1):
        for i in range(0, len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            if phrase not in seen:
                seen.add(phrase)
                out.append(phrase)
    return out


def _wire_codebook_by_key(agent, node_type: str, edge_type: str, key: str) -> None:
    """Reconcile-wire every held `node_type` codebook row to the agent root via
    `edge_type`, ONE row per distinct `key` value. A default-seeded row and a
    later teach() of the SAME key are two nodes, and wiring both would make the
    classify-by-join fire twice for one fact (duplicate reading); the key is the
    codebook's join key, so key-uniqueness at the wiring is the correct dedup.
    The shared reconcile-by-presence idiom every goal-layer codebook uses.
    Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, edge_type))
    seen = {str(sub.node(n)["attrs"].get(key)) for n in wired}
    for n in sub.nodes(node_type):
        if n in wired:
            continue
        k = str(sub.node(n)["attrs"].get(key))
        if k in seen:
            continue
        native.add_edge_unchecked(ag_node, edge_type, n)
        seen.add(k)


def _held_method_text(sub, method_name: str):
    for n in sub.nodes("MethodSpec"):
        at = sub.node(n)["attrs"]
        if at.get("name") == method_name:
            return at.get("text")
    return None


def _author_layer_rule(agent, *, method_name: str, rule_name: str,
                       fact_type: str, codebook_type: str) -> bool:
    """AUTHOR a goal-layer classify-by-join rule ONCE (idempotent), from the
    `MethodSpec{name:method_name}` the agent holds -- via its OWN rule-authoring
    faculty (`procedural_reader` -> `binding_resolver` -> `method_synthesis`).
    The rule is NEVER seeded (each layer's _no_shipped guard forbids it); this
    runs the faculty at read time and installs the authored rule to the LIVE
    graph. Requires >=1 `fact_type` node + >=1 `codebook_type` node present so
    `derive_binding` can ground the fact/codebook collections. Returns True iff
    it authored+installed this call. NO decision here: the held method text +
    the faculty do the authoring; this only sequences the calls and guards
    idempotency -- the crown-jewel self-authoring, run automatically."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return False
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    if rule_name in names:
        return False
    if not list(sub.nodes(fact_type)) or not list(sub.nodes(codebook_type)):
        return False
    method_text = _held_method_text(sub, method_name)
    if not method_text:
        return False
    from domains import procedural_reader as pr
    from domains import binding_resolver as br
    from domains import method_synthesis as ms
    model = pr.read_method(agent, method_text, name=method_name)
    gb = br.derive_binding(agent, model)
    res = ms.synthesise_rule_from_method(agent, model, gb.get("binding"), install=True)
    if res.get("installed"):
        native.run_rules()
        return True
    return False


def ensure_disclaimer_codebook(agent) -> None:
    """Reconcile-wire every held `DisclaimerCue` row — seeded, or minted by a
    later `teach()` — to the agent root via `has_disclaimer_cue`, so the
    AGENT-AUTHORED join rule sees it without a fresh boot (the SAME
    reconcile-by-presence idiom `ensure_actor_goals_seed` uses for its
    codebooks). Mechanical seed I/O, not a decision. Teaching a new cue row +
    calling this is all the growth the join needs — no rule/code change."""
    _wire_codebook_by_key(agent, "DisclaimerCue", "has_disclaimer_cue", "phrase")


_CONFLICTING_GOALS_DEFAULT_SEED = "conflicting_goals_default"


def ensure_conflicting_goals_defaults(agent) -> None:
    """Idempotently self-load the DEFAULT conflicting-goals DATA
    (seeds/conflicting_goals_default.json): the starter `DisclaimerCue` codebook
    + the `MethodSpec` the agent authors its rule from. DATA ONLY -- no rule
    ships there (the rule is agent-authored; see `ensure_conflicting_goals_rule`
    and test_agent_authors_conflicting_goals_rule's _no_shipped guard). Same
    self-load idiom as `media_analysis.ensure_media_analysis_seed`, so the
    reading pipeline (booted via boot_core, which does not list this seed) still
    gets the default codebook. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    have_method = any(sub.node(n)["attrs"].get("name") == "conflicting_goals"
                      for n in sub.nodes("MethodSpec"))
    if not have_method:
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_CONFLICTING_GOALS_DEFAULT_SEED), ag_node)
    ensure_disclaimer_codebook(agent)


def ensure_conflicting_goals_rule(agent) -> bool:
    """AUTHOR the conflicting-goals classify-by-join rule ONCE (idempotent).
    The caller annotates DisclaimerCandidates first so derive_binding can ground
    the fact collection. See `_author_layer_rule`."""
    return _author_layer_rule(
        agent, method_name="conflicting_goals",
        rule_name="synth_classify_conflicting_goals",
        fact_type="DisclaimerCandidate", codebook_type="DisclaimerCue")


# --------------------------------------------------------------------------- #
#  THE OTHER THREE GOAL LAYERS -- auto-fire on an article read via the SAME
#  template (default DATA seed + agent-AUTHORED rule + annotator in the stage).
#  The rules are NEVER seeded (each layer's _no_shipped guard). One combined
#  default seed carries all three MethodSpecs + starter codebooks.
# --------------------------------------------------------------------------- #
_GOAL_LAYERS_DEFAULT_SEED = "goal_layers_default"


def ensure_goal_layers_defaults(agent) -> None:
    """Idempotently self-load the DEFAULT DATA for the surface-inversion /
    temporal / named-trope layers (seeds/goal_layers_default.json): their
    `MethodSpec`s + starter `DistancingCue` / `OpposingActionPair` /
    `TropeSignature` codebooks. DATA ONLY -- no rule ships (each rule is
    agent-authored). Same self-load idiom as `ensure_conflicting_goals_defaults`,
    so the reading pipeline (boot_core) still gets the codebooks. Mechanical."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    have = any(sub.node(n)["attrs"].get("name") == "surface_inversion"
               for n in sub.nodes("MethodSpec"))
    if not have:
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_GOAL_LAYERS_DEFAULT_SEED), ag_node)
    ensure_distancing_codebook(agent)
    ensure_opposing_pair_codebook(agent)
    ensure_trope_codebook(agent)


def ensure_surface_inversion_rule(agent) -> bool:
    """AUTHOR the surface-inversion classify-by-join rule ONCE (idempotent).
    Caller annotates UtterancePhrases first. See `_author_layer_rule`."""
    return _author_layer_rule(
        agent, method_name="surface_inversion",
        rule_name="synth_classify_surface_inversion",
        fact_type="UtterancePhrase", codebook_type="DistancingCue")


def ensure_temporal_conflict_rule(agent) -> bool:
    """AUTHOR the temporal-conflict classify-by-join rule ONCE (idempotent).
    Caller annotates ActionPairFacts first (which need ActorAction facts, minted
    by annotate_actor_action in the clause reads). See `_author_layer_rule`."""
    return _author_layer_rule(
        agent, method_name="temporal_conflict",
        rule_name="synth_classify_temporal_conflict",
        fact_type="ActionPairFact", codebook_type="OpposingActionPair")


def ensure_named_trope_rule(agent) -> bool:
    """AUTHOR the named-trope classify-by-join rule ONCE (idempotent). Depends on
    the temporal layer having minted >=1 TemporalConflictReading (the fact it
    joins) + the TropeSignature codebook. See `_author_layer_rule`."""
    return _author_layer_rule(
        agent, method_name="named_trope",
        rule_name="synth_classify_named_trope",
        fact_type="TemporalConflictReading", codebook_type="TropeSignature")


# --------------------------------------------------------------------------- #
#  THE FIFTH LAYER -- EPISTEMIC GAP (deception vs introspection-gap humility).
#  Structurally different: not a text-cue join but STRUCTURAL signal-detectors
#  over the actor-action / temporal beliefs the reads produce, an agent-AUTHORED
#  evidence classify-by-join, and the context-dependent assess_epistemic_lean
#  COMBINE. The VERDICT needs world-supplied context (the actor's class/type via
#  annotate_actor_class -- "a better model of the actor's environment than the
#  actor's self-model"); the reading stage auto-produces the EVIDENCE.
# --------------------------------------------------------------------------- #
_EPISTEMIC_DEFAULT_SEED = "epistemic_default"


def ensure_epistemic_defaults(agent) -> None:
    """Idempotently self-load the DEFAULT epistemic DATA
    (seeds/epistemic_default.json): the `MethodSpec` + the `EpistemicSignal` /
    `ForcedChoiceExpectation` / `ClassBaseline` codebooks. DATA ONLY -- no rule
    ships (the rule is agent-authored). Same self-load idiom as the other goal
    layers. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    have = any(sub.node(n)["attrs"].get("name") == "epistemic_evidence"
               for n in sub.nodes("MethodSpec"))
    if not have:
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_EPISTEMIC_DEFAULT_SEED), ag_node)
    ensure_epistemic_codebook(agent)
    ensure_class_baseline_codebook(agent)


def ensure_epistemic_evidence_rule(agent) -> bool:
    """AUTHOR the epistemic-evidence classify-by-join rule ONCE (idempotent).
    Caller runs the signal detectors first (so >=1 EvidenceCandidate exists to
    ground). See `_author_layer_rule`."""
    return _author_layer_rule(
        agent, method_name="epistemic_evidence",
        rule_name="synth_classify_epistemic_evidence",
        fact_type="EvidenceCandidate", codebook_type="EpistemicSignal")


def run_epistemic_signal_detectors(agent) -> None:
    """Run every STRUCTURAL epistemic signal-detector over the held beliefs the
    reads produced -- each a pure structural read (a count / presence test), no
    decision: coordination-proxy (from a TemporalConflictReading), directional-
    asymmetry (repeated same-direction ActionPairFacts), isolated-act (a single
    conflicting ActorGoal), forced-choice probes (per ActorAction, the fact side
    of the structural-forcing join). Mechanical orchestration; the lean/weight of
    each emitted candidate is the codebook's, and the verdict is the combine's."""
    annotate_coordination_proxy(agent)
    annotate_directional_asymmetry(agent)
    annotate_isolated_act(agent)
    annotate_forced_choice_probes(agent)


def _existing_disclaimer_candidate_phrases(sub) -> set:
    out = set()
    for nd in sub.nodes("DisclaimerCandidate"):
        out.add(str(sub.node(nd)["attrs"].get("phrase")))
    return out


def annotate_disclaimer_candidates(agent, utterance: str) -> list:
    """For an utterance, write ONE `DisclaimerCandidate{phrase}` fact per
    contiguous word n-gram — UNCONDITIONALLY, no codebook check, no decision
    (the SAME "emit candidates, the rule joins" pattern as
    `meaning_inference.annotate_affix_candidates`). Each is wired to the agent
    hub via `has_disclaimer_candidate`, a DEDICATED edge type. Idempotent by
    phrase. The DECISION about which candidate is a real disclaimer is entirely
    the AGENT-AUTHORED seed rule's Eq-join against the taught `DisclaimerCue`
    codebook — never here. Returns the newly-added node ids."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    ensure_disclaimer_codebook(agent)
    existing = _existing_disclaimer_candidate_phrases(sub)
    created: list = []
    for phrase in _utterance_ngrams(utterance):
        if phrase in existing:
            continue
        node = sub.add_node("DisclaimerCandidate", {"phrase": phrase})
        native.add_edge_unchecked(ag_node, "has_disclaimer_candidate", node)
        existing.add(phrase)
        created.append(node)
    if created:
        native.run_rules()
    return created


def held_conflicting_goals(agent) -> list:
    """The agent's held `ConflictingGoalsReading` beliefs — the disclaimer
    phrase that fired + the tension the taught cue named. Pure graph read, no
    decision."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("ConflictingGoalsReading"):
        at = sub.node(nd)["attrs"]
        out.append({"phrase": at.get("phrase"), "tension": at.get("tension")})
    return out


# --------------------------------------------------------------------------- #
#  GENERIC PHRASE ANNOTATOR — the ONE mechanical n-gram emitter EVERY future
#  phrase-cue layer reuses (same-surface inversion is its FIRST client).
#
#  A phrase-cue layer classifies an utterance by JOINING its word n-grams
#  against a TEACHABLE codebook of cue phrases, via an AGENT-AUTHORED seed rule.
#  This function is the layer's ONLY Python: it emits ONE `UtterancePhrase{phrase}`
#  fact per contiguous 2..6-word n-gram — UNCONDITIONALLY, codebook-independent,
#  NO decision, NO `import re` (the SAME mechanical `str` enumeration
#  `annotate_disclaimer_candidates` uses, but on a GENERIC node type). A NEW
#  phrase-cue layer therefore needs ZERO new Python: teach a new cue codebook +
#  have the agent AUTHOR a join rule against `UtterancePhrase` — that is all.
#
#  The DECISION about which n-gram matters is entirely the AGENT-AUTHORED seed
#  rule's Eq-join against the taught cue codebook — never here.
# --------------------------------------------------------------------------- #
def _existing_utterance_phrases(sub) -> set:
    out = set()
    for nd in sub.nodes("UtterancePhrase"):
        out.add(str(sub.node(nd)["attrs"].get("phrase")))
    return out


def annotate_utterance_phrases(agent, utterance: str) -> list:
    """GENERIC mechanical n-gram annotator (world-adapter I/O). For an utterance,
    write ONE `UtterancePhrase{phrase}` fact per contiguous 2..6-word lowercased
    n-gram — UNCONDITIONALLY, no codebook check, no decision (the SAME "emit
    every candidate, the rule joins" pattern as `annotate_disclaimer_candidates`,
    but on a GENERIC node type any phrase-cue layer can join against). Each is
    wired to the agent hub via `has_utterance_phrase`, a DEDICATED edge type.
    Idempotent by phrase. Returns the newly-added node ids.

    This ONE annotator serves same-surface inversion AND every future phrase-cue
    layer, so subsequent layers = teach a codebook + AUTHOR a join rule, with NO
    new Python. `_utterance_ngrams` (defined above for the disclaimer layer) is
    the shared mechanical enumerator — no `import re`, pure `str` work."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    existing = _existing_utterance_phrases(sub)
    created: list = []
    for phrase in _utterance_ngrams(utterance):
        if phrase in existing:
            continue
        node = sub.add_node("UtterancePhrase", {"phrase": phrase})
        native.add_edge_unchecked(ag_node, "has_utterance_phrase", node)
        existing.add(phrase)
        created.append(node)
    if created:
        native.run_rules()
    return created


def ensure_distancing_codebook(agent) -> None:
    """Reconcile-wire every held `DistancingCue` row — seeded, or minted by a
    later `teach()` — to the agent root via `has_distancing_cue`, so the
    AGENT-AUTHORED join rule sees it without a fresh boot (the SAME
    reconcile-by-presence idiom `ensure_disclaimer_codebook` uses). Mechanical
    seed I/O, not a decision. Teaching a new cue row + calling this is all the
    growth the join needs — no rule/code change."""
    _wire_codebook_by_key(agent, "DistancingCue", "has_distancing_cue", "phrase")


def held_surface_inversions(agent) -> list:
    """The agent's held `SurfaceInversionReading` beliefs — the utterance phrase
    that fired (from f) + the distancing reading the taught cue named (from c).
    Pure graph read, no decision. A SurfaceInversionReading means the speaker is
    voicing the surface content at a DISTANCE (quotation/attribution/condemnation)
    — the goal is INVERTED (call-out/report), not endorsement of the content."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("SurfaceInversionReading"):
        at = sub.node(nd)["attrs"]
        out.append({"phrase": at.get("phrase"), "reading": at.get("reading")})
    return out


# --------------------------------------------------------------------------- #
#  TEMPORAL CROSS-ACTION PATTERN — two acts by the SAME actor on the SAME object,
#  opposing in valence ACROSS TIME, reveal a layered/temporal meta-goal neither
#  act shows alone ("the oil company FUNDED the technology, then LOBBIED AGAINST
#  its adoption"). This is the "revealed only across actions" layer (the explicit
#  LATER slice the single-act flag_conflicting_meta_goal docstring names).
#
#  It is realised as the SAME classify-by-codebook-JOIN the conflicting-goals and
#  surface-inversion layers use, reshaped to fit the agent's CURRENT 1-key
#  Eq-join: a MECHANICAL pairing annotator emits ONE `ActionPairFact` per ordered
#  same-actor-same-object pair, keyed by a COMPOSITE `pair_key` (first_verb +
#  '|' + second_verb, order-preserving); a TEACHABLE `OpposingActionPair` codebook
#  names the meaningful support-then-undermine composite keys; and the AGENT
#  AUTHORS the join rule (procedural_reader -> binding_resolver -> method_synthesis)
#  against the SINGLE `pair_key` field. The pairing annotator makes NO valence
#  decision — it enumerates EVERY same-actor-same-object ordered pair; the
#  DECISION of which composite keys are opposing is entirely the AGENT-AUTHORED
#  rule's Eq-join against the taught codebook. NO `import re`.
# --------------------------------------------------------------------------- #
def _node_id_int(nd) -> int:
    """The integer id of a node handle, for CREATION-order (== graph/sentence
    order) sorting. Mirrors binding_resolver._node_int — mechanical, no decision."""
    v = getattr(nd, "value", None)
    if isinstance(v, int):
        return v
    try:
        return int(str(nd).lstrip("#"))
    except ValueError:
        return 0


def _held_actor_actions_ordered(sub) -> list:
    """Held `ActorAction` facts as (actor, verb, object) tuples in CREATION order
    (graph/sentence order). Pure graph read, no decision."""
    rows = []
    for nd in sub.nodes("ActorAction"):
        at = sub.node(nd)["attrs"]
        rows.append((nd, str(at.get("actor")), str(at.get("verb")), str(at.get("object"))))
    rows.sort(key=lambda t: _node_id_int(t[0]))
    return [(a, v, o) for (_nd, a, v, o) in rows]


def _existing_action_pair_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("ActionPairFact"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("actor")), str(at.get("object")), str(at.get("pair_key"))))
    return out


def annotate_action_pairs(agent) -> list:
    """For every ORDERED pair of held `ActorAction` facts with the SAME actor AND
    the SAME object (in graph/creation == sentence order), write ONE
    `ActionPairFact{actor, object, pair_key}` fact — UNCONDITIONALLY, no codebook
    check, no valence judgement — where `pair_key = first_verb + '|' + second_verb`
    (a composite, order-preserving string, so 'fund|oppose' != 'oppose|fund').

    This is the SAME "emit every candidate, the rule joins" discipline as
    `annotate_disclaimer_candidates` / `annotate_utterance_phrases`, lifted to a
    SELF-JOIN over the held actions: the enumeration of same-actor-same-object
    ordered pairs is purely structural (a nested loop over held facts + a string
    concat — no `import re`, no lexicon lookup); the OPPOSING-ness of a pair is
    decided ENTIRELY by the AGENT-AUTHORED rule's Eq-join against the taught
    `OpposingActionPair` codebook, never here. Each fact is wired to the agent hub
    via `has_action_pair`, a DEDICATED edge type. Idempotent by
    (actor, object, pair_key). Returns the newly-added node ids.

    `verb` comes straight off the held ActorAction, which `annotate_actor_action`
    already ran through `reading_collapse._participle_lemma` ('funded'->'fund',
    'opposed'->'oppose'), so a pair_key is built from lemmas on both sides and keys
    the taught codebook row consistently regardless of surface inflection."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    actions = _held_actor_actions_ordered(sub)
    if len(actions) < 2:
        return []
    existing = _existing_action_pair_keys(sub)
    created: list = []
    for i in range(len(actions)):
        a_actor, a_verb, a_obj = actions[i]
        for j in range(i + 1, len(actions)):
            b_actor, b_verb, b_obj = actions[j]
            if a_actor != b_actor or a_obj != b_obj:
                continue
            pair_key = a_verb + "|" + b_verb
            key = (a_actor, a_obj, pair_key)
            if key in existing:
                continue
            node = sub.add_node("ActionPairFact", {
                "actor": a_actor, "object": a_obj, "pair_key": pair_key,
            })
            native.add_edge_unchecked(ag_node, "has_action_pair", node)
            existing.add(key)
            created.append(node)
    if created:
        native.run_rules()
    return created


def ensure_opposing_pair_codebook(agent) -> None:
    """Reconcile-wire every held `OpposingActionPair` row — seeded, or minted by a
    later `teach()` — to the agent root via `has_opposing_action_pair`, so the
    AGENT-AUTHORED join rule sees it without a fresh boot (the SAME
    reconcile-by-presence idiom `ensure_distancing_codebook` uses). Mechanical seed
    I/O, not a decision. Teaching a new opposing-pair row + calling this is all the
    growth the join needs — no rule/code change."""
    _wire_codebook_by_key(agent, "OpposingActionPair", "has_opposing_action_pair", "pair_key")


def held_temporal_conflicts(agent) -> list:
    """The agent's held `TemporalConflictReading` beliefs — the actor + object +
    composite pair_key that fired (from f) + the note the taught codebook row named
    (from c). Pure graph read, no decision. A TemporalConflictReading means the
    SAME actor acted on the SAME object with an opposing valence ACROSS actions
    (support then undermine) — a layered/temporal meta-goal neither act shows
    alone, revealed only across the pair."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("TemporalConflictReading"):
        at = sub.node(nd)["attrs"]
        out.append({"actor": at.get("actor"), "object": at.get("object"),
                    "pair_key": at.get("pair_key"), "note": at.get("note")})
    return out


# --------------------------------------------------------------------------- #
#  NAMED STRATEGIC SCHEMAS — the TVTropes capstone. Give the cross-action goal
#  pattern a NAME: "fund the design, then oppose its adoption" IS the Trojan-Horse
#  schema (a gift carrying a hidden hostile payload); other support-then-undermine
#  composite keys map to Bait and Switch, False Flag Operation, etc. — names drawn
#  from the real TVTropes strategic-schema vocabulary.
#
#  This is a META-classification over an EXISTING reading: it JOINS a held
#  `TemporalConflictReading`'s `pair_key` (the FACT — already minted by the
#  cross-action temporal layer above, already hub-wired via
#  `has_temporal_conflict_reading`, already carrying `pair_key`) against a TEACHABLE
#  `TropeSignature{pair_key, trope, gloss}` codebook keyed by the SAME `pair_key`,
#  and mints a NAMED `TropeReading{actor, object, pair_key, trope, gloss}`.
#
#  ZERO new annotator: the TemporalConflictReading IS the fact, so nothing new is
#  emitted here — this slice contributes ONLY codebook wiring (reconcile-by-
#  presence, so teach()-ed TropeSignature rows reach the join) + a reader. Fits the
#  agent's CURRENT 1-key classify-by-codebook-join exactly (one Eq on `pair_key`),
#  so the agent AUTHORS the rule ITSELF from a plain method + the taught codebook
#  via procedural_reader.read_method -> binding_resolver.derive_binding ->
#  method_synthesis.synthesise_rule_from_method. NO hand-written rule. The DECISION
#  of which pattern is which named schema is entirely the AGENT-AUTHORED rule's
#  Eq-join against the taught codebook, never Python (no `import re`).
# --------------------------------------------------------------------------- #
def ensure_trope_codebook(agent) -> None:
    """Reconcile-wire every held `TropeSignature` row — seeded, or minted by a
    later `teach()` — to the agent root via `has_trope_signature`, so the
    AGENT-AUTHORED join rule (and derive_binding's codebook grounding) sees it
    without a fresh boot (the SAME reconcile-by-presence idiom
    `ensure_opposing_pair_codebook` uses). Mechanical seed I/O, not a decision.
    Teaching a new TropeSignature row + calling this is all the growth the join
    needs — no rule/code change."""
    _wire_codebook_by_key(agent, "TropeSignature", "has_trope_signature", "pair_key")


def held_trope_readings(agent) -> list:
    """The agent's held `TropeReading` beliefs — the actor + object + composite
    pair_key that fired (from f, the TemporalConflictReading fact) + the NAMED
    trope + its gloss the taught codebook row supplied (from c). Pure graph read,
    no decision. A TropeReading NAMES the strategic schema an already-detected
    temporal-conflict pattern instantiates ('fund|oppose' -> 'Trojan Horse')."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("TropeReading"):
        at = sub.node(nd)["attrs"]
        out.append({"actor": at.get("actor"), "object": at.get("object"),
                    "pair_key": at.get("pair_key"), "trope": at.get("trope"),
                    "gloss": at.get("gloss")})
    return out


# =========================================================================== #
#  THE EPISTEMIC-GAP HUMILITY LAYER — deception (stated!=held, deliberate,
#  culpable) vs introspection-gap (held!=actual, sincere, not culpable) behind a
#  stated-goal/behaviour mismatch.
#
#  BOTTOM LINE that governs every design choice below (research-derived): the
#  honest DEFAULT is UNDETERMINED and MUST stay the majority outcome. Human
#  peer-to-peer lie-detection runs ~54% (Bond & DePaulo) and a competent
#  self-deceiver is textually IDENTICAL to a sincere actor. So ONLY STRUCTURAL /
#  DOCUMENTARY signals move a verdict off UNDETERMINED; stylistic cues NEVER can.
#
#  THE ONE PLACE THAT CEILING LIFTS — the agent's MODEL ADVANTAGE. Bond & DePaulo
#  is SYMMETRIC-information peer judgement (a stranger judging a stranger, no
#  model edge). The agent is not in that position: it can hold a BETTER MODEL of
#  the actor than the actor's own self-model — in particular a model of the wider
#  socioeconomic system that predicts FORCED / STRUCTURAL choices. Against such a
#  model, locating deception/rationalisation is OFTEN TRACTABLE, not undetermined:
#  compare the actor's STATED reason against the STRUCTURALLY-PREDICTED (forced)
#  one; the divergence locates the hidden driver with NO documentary confession.
#  That is the `structural_forcing` signal + the model-asymmetry mechanism
#  discriminator (`ForcedChoiceExpectation.actor_can_introspect`) below. For
#  POLITICAL / COMPANY / INSTITUTIONAL actors the model is EASY because the
#  forced-choice driver reduces to MONEY and POWER — a strong reusable prior, so
#  a sophisticated actor's stated altruistic reason that cuts against its own
#  profit/power interest routes to DECEPTION (it knows its own interest), while an
#  INDIVIDUAL rationalising a structurally-forced choice as principle routes to
#  the INTROSPECTION-GAP.
#
#  ARCHITECTURE (identical discipline to every slice above): MECHANICAL
#  annotators emit behaviour-record FACTS + `EvidenceCandidate`s UNCONDITIONALLY
#  (no lean/weight decision — the weight lives in the codebook); a TEACHABLE
#  `EpistemicSignal` codebook holds the world knowledge (lean/weight/
#  evidence_kind); the AGENT AUTHORS the signal-DETECTION rule (classify-by-join,
#  its current faculty); and the COMBINE/BAND — the humility core — is a
#  hand-authored graph rule (an HONESTLY-REPORTED capability rung above the
#  agent's current authoring; see `ensure_epistemic_combine_rule`). Every verdict
#  is a REVISABLE belief that carries its `residual_other_mass` (never 0) and its
#  model-defeasibility caveat. NO `import re`.
# =========================================================================== #

# --- the TEACHABLE codebook rows (the agent's OWN teach()) ------------------- #
#  Each row: {name, lean ('deception'|'opacity'), weight (float), evidence_kind
#  ('documentary'|'structural'|'behavioural'|'stylistic')}. `internal_knowledge_
#  trace` is the only near-decisive (documentary) cue; the stylistic rows are
#  RECORDED but their weight is 0.0 or they are guarded out of moving the verdict
#  (the debunked-cue guard — stylistic can NEVER move off UNDETERMINED).
EPISTEMIC_SIGNAL_CODEBOOK = [
    {"name": "internal_knowledge_trace", "lean": "deception", "weight": 0.8,
     "evidence_kind": "documentary",
     "note": "a documentary trace that the actor PRIVATELY acknowledged the true "
             "goal (an ingested statement / explicit marker) -- the only near-decisive cue; "
             "never inferred from stylistic text."},
    {"name": "consistent_directional_asymmetry", "lean": "deception", "weight": 0.35,
     "evidence_kind": "structural",
     "note": "the actor's acts lean the same divergent direction across N independent "
             "observations -- a pattern, not one act."},
    {"name": "scrutiny_contingent_competence", "lean": "deception", "weight": 0.35,
     "evidence_kind": "structural",
     "note": "the stated goal is pursued competently only when observed/scrutinised -- "
             "an awareness-implying structural signal."},
    {"name": "coordination_requires_dual_goal", "lean": "deception", "weight": 0.4,
     "evidence_kind": "structural",
     "note": "the trajectory needs a joint stated+hidden goal to cohere. PROXY-CAPPED: "
             "the honest inverse-planning model is UNBUILT, so this rests on the "
             "TemporalConflictReading proxy and can NEVER reach strong_deception."},
    {"name": "clear_served_interest", "lean": "deception", "weight": 0.15,
     "evidence_kind": "behavioural",
     "note": "a divergent interest is visibly served by the act -- weak, behavioural."},
    {"name": "isolated_incoherent_act", "lean": "opacity", "weight": 0.35,
     "evidence_kind": "structural",
     "note": "one act that does not cohere with the stated goal, no pattern -- leans "
             "confusion/self-opacity, not deliberate deception."},
    {"name": "no_served_interest_visible", "lean": "opacity", "weight": 0.25,
     "evidence_kind": "behavioural",
     "note": "no divergent interest is visibly served -- leans introspection-gap."},
    {"name": "fluent_sincere_rationalisation", "lean": "opacity", "weight": 0.15,
     "evidence_kind": "stylistic",
     "note": "a fluent, sincere-sounding account -- STYLISTIC: recorded, must never "
             "move the verdict off UNDETERMINED on its own."},
    {"name": "hedging_distancing", "lean": "opacity", "weight": 0.0,
     "evidence_kind": "stylistic",
     "note": "hedges / distancing language -- a DEBUNKED cue: recorded, weight 0.0, "
             "NEVER weighted."},
    # structural_forcing has NO fixed lean row here: its lean is ROUTED by the
    # model-asymmetry (actor_can_introspect) in the two structural-forcing rules,
    # which mint EpistemicEvidence directly. Its weight (0.55) lives in those
    # rules as codebook-grade data. See ForcedChoiceExpectation below.
]
_STRUCTURAL_FORCING_WEIGHT = 0.55

# --- the socioeconomic / forced-choice model (teachable, grow-by-teaching) --- #
#  {actor_type, structural_interest, forced_against, actor_can_introspect}. The
#  MONEY/POWER institutional prior makes this model EASY for company/political
#  actors (they KNOW their profit/power incentive -> can_introspect 1.0 -> a
#  stated reason that cuts against it routes to DECEPTION). An INDIVIDUAL
#  rationalising a structurally-forced choice as principle is can_introspect 0.0
#  -> INTROSPECTION-GAP. This is the SEED of the socioeconomic model; the full
#  structural graph is a later component, but the signal works off taught
#  expectations now. (No bespoke row per company is NEEDED for the prior itself --
#  the reusable structural_interest is 'profit_and_market_power' /
#  'power_retention'; each row still names the specific threat it is forced
#  against. A single actor_type='company' row matching EVERY company by category
#  needs an actor->category classifier -- an HONEST later component.)
#  STAKES ARE THE MISSING VARIABLE the lab lie-detection studies (Bond & DePaulo
#  ~54%) threw away: those studies were STAKES-FREE (a subject told to lie, nothing
#  at risk) and so hit chance. REAL institutional deception has MEASURABLE stakes
#  (the money/power at risk when the stated reason diverges from the forced
#  choice), and stakes ESTABLISH PRIORS. So each row carries `stakes` (0..1): a
#  fossil-fuel co opposing its own core business = high (~1.0); a trivial PR choice
#  = low (~0.2). The structural_forcing WEIGHT is SCALED BY stakes, so the
#  resulting lean's CONFIDENCE (and the interval WIDTH) scale with the measured
#  stakes: high stakes -> a confident, narrower-interval lean; low stakes -> a wide
#  interval that stays UNDETERMINED. UNDETERMINED is thus the LOW-STAKES / no-model
#  case, NOT an over-cautious default -- with a matched expectation AND non-trivial
#  stakes the layer COMMITS to a bounded-but-informative estimate.
FORCED_CHOICE_CODEBOOK = [
    {"actor_type": "oil_company", "structural_interest": "protect_fossil_fuels",
     "forced_against": "renewable_energy", "actor_can_introspect": 1.0, "stakes": 1.0,
     "note": "sector instantiation of the company money/power prior: an oil company's "
             "profit/market position is threatened by renewables adoption; it KNOWS this. "
             "HIGH stakes -- its core business is at risk."},
    {"actor_type": "pharma_company", "structural_interest": "profit_and_market_power",
     "forced_against": "generic_medicine", "actor_can_introspect": 1.0, "stakes": 1.0,
     "note": "the SAME money/power prior in a DIFFERENT sector -- generalises beyond oil: "
             "a pharma company's profit is threatened by cheap generics; it KNOWS this. "
             "HIGH stakes."},
    {"actor_type": "political_actor", "structural_interest": "power_retention",
     "forced_against": "donor_reform", "actor_can_introspect": 1.0, "stakes": 0.9,
     "note": "the political money/power prior: a stated principled reason that cuts against "
             "re-election/funder relations is strategic; the actor KNOWS its power incentive."},
    {"actor_type": "factory_worker", "structural_interest": "job_security",
     "forced_against": "automation_support", "actor_can_introspect": 0.0, "stakes": 0.8,
     "note": "the INDIVIDUAL case: a person can genuinely rationalise a structurally-forced "
             "choice as free principle -- can_introspect 0.0 routes to INTROSPECTION-GAP, "
             "not deception (no bad faith). Real but personal stakes (their job)."},
    {"actor_type": "pr_agency", "structural_interest": "profit_and_market_power",
     "forced_against": "logo_colour", "actor_can_introspect": 1.0, "stakes": 0.2,
     "note": "a TRIVIAL-stakes divergence: little money/power rides on the choice, so the "
             "structural prior is weak -- stays UNDETERMINED. Shows UNDETERMINED is the "
             "low-stakes case, not over-caution."},
]


# --------------------------------------------------------------------------- #
#  codebook wiring (reconcile-by-presence — the SAME idiom every slice uses)
# --------------------------------------------------------------------------- #
def ensure_epistemic_codebook(agent) -> None:
    """Reconcile-wire every held `EpistemicSignal` / `ForcedChoiceExpectation`
    row (seeded, or minted by a later `teach()`) to the agent root, so the
    detection / forcing rules see them without a fresh boot. Mechanical seed
    I/O, not a decision."""
    _wire_codebook_by_key(agent, "EpistemicSignal", "has_epistemic_signal", "name")
    _wire_codebook_by_key(agent, "ForcedChoiceExpectation",
                          "has_forced_choice_expectation", "actor_type")


def seed_epistemic_codebook(agent, *, signals=EPISTEMIC_SIGNAL_CODEBOOK,
                            forced_choices=FORCED_CHOICE_CODEBOOK) -> None:
    """Teach the whole `EpistemicSignal` + `ForcedChoiceExpectation` codebook via
    the agent's OWN `teach()` facility, then reconcile-wire it. Mechanical: teach
    adds the row to the live graph (and, when persistence is enabled, to a seed);
    WHICH seed is the agent's own call. Re-teaching is a no-op (idempotent)."""
    from domains.teach import teach
    for row in signals:
        teach(agent, "EpistemicSignal", dict(row))
    for row in forced_choices:
        teach(agent, "ForcedChoiceExpectation", dict(row))
    ensure_epistemic_codebook(agent)


# --------------------------------------------------------------------------- #
#  MECHANICAL ANNOTATORS — emit behaviour-record FACTS + EvidenceCandidates,
#  UNCONDITIONALLY, with NO lean/weight decision (the weight is the codebook's).
# --------------------------------------------------------------------------- #
def _existing_attr_keys(sub, node_type: str, key: str) -> set:
    return {str(sub.node(nd)["attrs"].get(key)) for nd in sub.nodes(node_type)}


def annotate_evidence_candidate(agent, signal_name: str) -> Optional[int]:
    """The MINIMAL mechanical annotator: record that a behaviour-record of
    category `signal_name` was OBSERVED, as ONE `EvidenceCandidate{signal_name}`
    fact — UNCONDITIONALLY, no codebook check, no lean/weight judgement (the SAME
    'emit a candidate, the rule joins' discipline as `annotate_action_pairs`). The
    world supplies WHICH behaviour-record fired; the DECISION about its lean/weight
    is entirely the AGENT-AUTHORED detection rule's Eq-join against the taught
    `EpistemicSignal` codebook. Wired via `has_evidence_candidate`. Idempotent by
    signal_name. Returns the node id (or None if already present)."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return None
    if str(signal_name) in _existing_attr_keys(sub, "EvidenceCandidate", "signal_name"):
        return None
    node = sub.add_node("EvidenceCandidate", {"signal_name": str(signal_name)})
    native.add_edge_unchecked(ag_node, "has_evidence_candidate", node)
    return node


def _has_single_observation_fact(sub) -> bool:
    return bool(sub.nodes("SingleObservationFact"))


def annotate_single_observation(agent) -> Optional[int]:
    """Record the behaviour-record FACT that only ONE observation is available (no
    behaviour history) as a singleton `SingleObservationFact{present:1.0}`. Pure
    mechanical fact-write, no decision. The COMBINE reads this as the
    SINGLE-OBSERVATION CLAMP (deception is not concludable from one act).
    Idempotent (singleton)."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None or _has_single_observation_fact(sub):
        return None
    node = sub.add_node("SingleObservationFact", {"present": 1.0})
    native.add_edge_unchecked(ag_node, "has_single_observation", node)
    return node


def annotate_coordination_proxy(agent) -> list:
    """For every held `TemporalConflictReading` (the shipped fund->oppose
    cross-action pattern — the COORDINATION PROXY), emit ONE
    `EvidenceCandidate{signal_name:'coordination_requires_dual_goal'}` — a
    mechanical read of an already-minted reading into a candidate, no decision. The
    reading IS the proxy for the (unbuilt) inverse-planning model; the combine
    PROXY-CAPS any verdict resting on it at weak_deception."""
    sub, _, _ = _resolve(agent)
    created = []
    if sub.nodes("TemporalConflictReading"):
        nid = annotate_evidence_candidate(agent, "coordination_requires_dual_goal")
        if nid is not None:
            created.append(nid)
    return created


def annotate_directional_asymmetry(agent, *, min_repeats: int = 2) -> list:
    """If the SAME (actor, pair_key) recurs across >= `min_repeats` held
    `ActionPairFact`s (N independent same-direction observations), emit ONE
    `EvidenceCandidate{signal_name:'consistent_directional_asymmetry'}`. Pure
    structural COUNT over held facts (a nested tally, no lexicon, no valence
    judgement, no `import re`); `min_repeats` is the structural minimum for 'a
    pattern' (the SAME status as the disclaimer n-gram's min_n), never a lean
    decision. The lean/weight is the codebook's."""
    sub, _, _ = _resolve(agent)
    counts: dict = {}
    for nd in sub.nodes("ActionPairFact"):
        at = sub.node(nd)["attrs"]
        k = (str(at.get("actor")), str(at.get("pair_key")))
        counts[k] = counts.get(k, 0) + 1
    created = []
    if any(c >= min_repeats for c in counts.values()):
        nid = annotate_evidence_candidate(agent, "consistent_directional_asymmetry")
        if nid is not None:
            created.append(nid)
    return created


def annotate_isolated_act(agent) -> list:
    """If EXACTLY ONE `ActorGoal` carries `serves_conflicting_meta_goal==1.0` AND
    there is NO `TemporalConflictReading` (a single conflicting act, no cross-action
    pattern), emit an `EvidenceCandidate{signal_name:'isolated_incoherent_act'}` +
    a `SingleObservationFact`. Pure structural read of held beliefs (a count + a
    presence test), no decision about the lean (that is the codebook's)."""
    sub, _, _ = _resolve(agent)
    conflicting = [nd for nd in sub.nodes("ActorGoal")
                   if float(sub.node(nd)["attrs"].get("serves_conflicting_meta_goal") or 0.0) == 1.0]
    created = []
    if len(conflicting) == 1 and not sub.nodes("TemporalConflictReading"):
        nid = annotate_evidence_candidate(agent, "isolated_incoherent_act")
        if nid is not None:
            created.append(nid)
        so = annotate_single_observation(agent)
        if so is not None:
            created.append(so)
    return created


def annotate_internal_knowledge_trace(agent, acknowledged: bool) -> Optional[int]:
    """Emit `EvidenceCandidate{signal_name:'internal_knowledge_trace'}` ONLY when
    an EXPLICIT input marker (`acknowledged`) says the actor PRIVATELY acknowledged
    the true goal — an ingested statement / documentary flag the WORLD supplies,
    NEVER inferred from stylistic text. Mechanical: the world hands over the
    documentary fact; the annotator only records it. Returns None when no marker."""
    if not acknowledged:
        return None
    return annotate_evidence_candidate(agent, "internal_knowledge_trace")


def _existing_probe_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("ForcedChoiceProbe"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("actor")), str(at.get("object"))))
    return out


def annotate_forced_choice_probes(agent) -> list:
    """For every held `ActorAction`, emit ONE `ForcedChoiceProbe{actor, object}`
    (object = the action's OBJECT DOMAIN, the same premodifier-keeping token
    `ActorGoal.object` carries) — UNCONDITIONALLY, no codebook check, no decision.
    This is the FACT side of the structural-forcing join: it enumerates every
    actor+stated-object the reader grounded; the DECISION about whether that stated
    direction DIVERGES from the structurally-forced one (and how the mechanism
    routes) is entirely the structural-forcing RULES' Eq-join against the taught
    `ForcedChoiceExpectation` model. Wired via `has_forced_choice_probe`.
    Idempotent by (actor, object). No `import re`."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    existing = _existing_probe_keys(sub)
    created = []
    for nd in sub.nodes("ActorAction"):
        at = sub.node(nd)["attrs"]
        actor = str(at.get("actor"))
        obj = str(at.get("object_domain") or "")
        if not obj or (actor, obj) in existing:
            continue
        node = sub.add_node("ForcedChoiceProbe", {"actor": actor, "object": obj})
        native.add_edge_unchecked(ag_node, "has_forced_choice_probe", node)
        existing.add((actor, obj))
        created.append(node)
    return created


# --------------------------------------------------------------------------- #
#  DSL term builders (the SAME helpers method_synthesis / the seed rules use)
# --------------------------------------------------------------------------- #
def _V(n): return {"type": "Var", "name": n}
def _L(v): return {"type": "Lit", "value": v}
def _A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _And(*xs): return {"type": "And", "items": list(xs)}
def _Or(*xs): return {"type": "Or", "items": list(xs)}
def _Not(x): return {"type": "Not", "arg": x}
def _NodesOf(t): return {"type": "NodesOfType", "node_type": t}
def _Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def _Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def _Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
def _Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def _Plus(*xs): return {"type": "Plus", "items": list(xs)}
def _Min(*xs): return {"type": "Min", "items": list(xs)}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(*xs): return {"type": "Times", "items": list(xs)}
def _Abs(x): return {"type": "Abs", "arg": x}
def _Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


# --------------------------------------------------------------------------- #
#  STRUCTURAL FORCING — the model-advantage detection, with model-asymmetry
#  routing of the mechanism. CAPABILITY RUNG (reported honestly): these two rules
#  are HAND-AUTHORED (a rule-JSON builder, the SAME legal category as
#  method_synthesis's _compose_* builders). The agent's CURRENT classify-by-join
#  authoring (derive_binding) emits a SINGLE-key join with NO scalar guard and NO
#  lean-routing, so the TWO-key join (actor==actor_type AND object==forced_against)
#  + the `actor_can_introspect` guard that ROUTES the mint's lean EXCEEDS what the
#  agent authors today. The SHAPE is squarely within the engine's classify
#  vocabulary (the agent EXECUTES it in run_rules); only the AUTHORING (binding
#  derivation of multi-key joins + guards + lean-routing) is the rung above.
# --------------------------------------------------------------------------- #
def _structural_forcing_rule(introspect_value: float, lean: str) -> dict:
    """One structural-forcing routing rule: JOIN a ForcedChoiceProbe to a
    ForcedChoiceExpectation on actor==actor_type AND object==forced_against, GUARD
    on actor_can_introspect==`introspect_value`, and mint an
    `EpistemicEvidence{signal_name:'structural_forcing', lean, weight:0.55,
    evidence_kind:'structural', ...}` (the model-asymmetry routes the lean:
    can_introspect 1.0 -> deception; 0.0 -> introspection-gap/opacity). Dedup by
    (signal_name, actor). NOT proxy-capped: this is a legitimate model-based
    structural signal, not the inverse-planning proxy."""
    return {
        "name": "structural_forcing_%s" % ("deception" if introspect_value == 1.0 else "gap"),
        "batch": False,
        "match": [["agent", "has_forced_choice_probe", "p"],
                  ["agent", "has_forced_choice_expectation", "x"]],
        "where": _And(
            _Eq(_A(_V("p"), "actor"), _A(_V("x"), "actor_type")),
            _Eq(_A(_V("p"), "object"), _A(_V("x"), "forced_against")),
            _Eq(_A(_V("x"), "actor_can_introspect"), _L(introspect_value)),
            _Not(_Exists(_NodesOf("EpistemicEvidence"), "e2",
                         _And(_Eq(_A(_V("e2"), "signal_name"), _L("structural_forcing")),
                              _Eq(_A(_V("e2"), "actor"), _A(_V("p"), "actor"))))),
        ),
        "effects": [
            ["add_node", "ev", "EpistemicEvidence", {
                "signal_name": "structural_forcing",
                "lean": lean,
                # WEIGHT SCALED BY MEASURED STAKES: base 0.55 * ForcedChoiceExpectation.stakes
                # (money/power at risk). High stakes -> full-weight confident lean; low stakes
                # -> a weight below the band threshold, so it stays UNDETERMINED.
                "weight": {"__term__": _Times(_L(_STRUCTURAL_FORCING_WEIGHT),
                                              _A(_V("x"), "stakes"))},
                "evidence_kind": "structural",
                "proxy_based": 0.0,
                "model_based": 1.0,
                "stakes": {"__term__": _A(_V("x"), "stakes")},
                "actor": {"__term__": _A(_V("p"), "actor")},
                "structural_interest": {"__term__": _A(_V("x"), "structural_interest")},
                "forced_against": {"__term__": _A(_V("x"), "forced_against")},
                "actor_can_introspect": introspect_value,
            }],
            ["add_edge", "agent", "has_epistemic_evidence", "ev"],
        ],
    }


def ensure_structural_forcing_rules(agent) -> dict:
    """Install the two structural-forcing routing rules (idempotent by name).
    Returns a small report naming the capability rung."""
    sub, native, ag_node = _resolve(agent)
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    installed = []
    for introspect_value, lean in ((1.0, "deception"), (0.0, "opacity")):
        r = _structural_forcing_rule(introspect_value, lean)
        if r["name"] not in names:
            native.add_rule(r)
            installed.append(r["name"])
    return {"installed": installed,
            "rung": "hand-authored (multi-key join + can_introspect guard + lean-routing "
                    "exceed derive_binding's single-key/no-guard classify authoring)"}


# --------------------------------------------------------------------------- #
#  THE COMBINE / BAND — the humility core. CAPABILITY RUNG (reported honestly):
#  a global masses-and-gates BANDING over ALL held EpistemicEvidence is NOT a
#  classify-by-join, so it is BEYOND the agent's current authoring faculty. It is
#  built here as ONE hand-authored graph RULE whose entire banding decision is a
#  nested `IfThenElse` Term tree EVALUATED BY RUST (the decision lives in the
#  graph, not in Python) + a mechanical reader. The guardrails are NON-NEGOTIABLE:
#    · DEFAULT UNDETERMINED unless a structural/documentary signal fired
#      (stylistic/behavioural-alone can NEVER move off UNDETERMINED).
#    · SINGLE-OBSERVATION CLAMP: a SingleObservationFact forces the deception side
#      to UNDETERMINED (you cannot conclude deliberate deception from one act; the
#      humble opacity direction stays reachable).
#    · ASYMMETRIC / MORAL thresholds: a deception band needs strictly MORE
#      accumulated weight (>= 0.50) than the mirror opacity band (>= 0.35).
#    · COORDINATION GATE: strong_deception is UNREACHABLE without a NON-proxy
#      awareness signal (internal_knowledge_trace / scrutiny_contingent_competence);
#      the coordination PROXY can never reach it.
#    · NO band is 'certain'; residual_other_mass is NEVER 0.
# --------------------------------------------------------------------------- #
# thresholds (research-derived; deception strictly harder than opacity)
_OPACITY_WEAK_MIN = 0.35
_OPACITY_STRONG_MIN = 0.70
_DECEPTION_WEAK_MIN = 0.50
_DECEPTION_STRONG_MIN = 0.70
_RESIDUAL_FLOOR = 0.46          # ~ (1 - human peer lie-detection ceiling ~0.54)
_AWARENESS_SIGNALS = ("internal_knowledge_trace", "scrutiny_contingent_competence")


def _mass(lean: str):
    """Sum of `weight` over held EpistemicEvidence of the given lean (a Term)."""
    return _Sum(_Filter(_NodesOf("EpistemicEvidence"), "e",
                        _Eq(_A(_V("e"), "lean"), _L(lean))),
                "d", _A(_V("d"), "weight"))


def _exists_ev(pred_builder):
    return _Exists(_NodesOf("EpistemicEvidence"), "e", pred_builder("e"))


def _combine_rule() -> dict:
    """The single banding rule. Matches the singleton assessment anchor, dedups on
    EpistemicLeanReading, and mints ONE reading whose verdict/score/confidence/
    residual are all Terms the Rust evaluator computes over the held evidence."""
    D = _mass("deception")
    O = _mass("opacity")
    struct_doc = _exists_ev(lambda e: _Or(_Eq(_A(_V(e), "evidence_kind"), _L("structural")),
                                          _Eq(_A(_V(e), "evidence_kind"), _L("documentary"))))
    awareness_real = _exists_ev(lambda e: _Or(*[_Eq(_A(_V(e), "signal_name"), _L(s))
                                               for s in _AWARENESS_SIGNALS]))
    single_obs = _Exists(_NodesOf("SingleObservationFact"), "so",
                         _Eq(_A(_V("so"), "present"), _L(1.0)))
    proxy = _exists_ev(lambda e: _Eq(_A(_V(e), "signal_name"),
                                     _L("coordination_requires_dual_goal")))
    model_based = _exists_ev(lambda e: _Eq(_A(_V(e), "signal_name"), _L("structural_forcing")))

    # --- FOLLOW-ON A: the class-level BASELINE-DECEPTION PRIOR (calibrated, class-
    # level, PRIOR-not-conviction). `apply_class_baseline` (a hand-authored plumbing
    # JOIN, see ensure_class_baseline_apply_rule) has already minted ONE
    # AppliedClassBaseline{baseline_prior} per matched actor_class; `baseline` sums
    # their small priors. The COMBINE adds it to the STARTING deception mass (D_eff),
    # shifting the point estimate / interval START toward deception. THE MORAL-
    # ASYMMETRY GUARDRAIL is STRUCTURAL, not a magnitude cap: (i) the prior is NOT
    # EpistemicEvidence, so it never sets `struct_doc` -> baseline ALONE (no
    # structural/documentary signal) falls to the `_Not(struct_doc)` branch and can
    # NEVER reach any deception band; (ii) strong_deception additionally needs
    # `awareness_real`, which a prior can never supply. So the prior can only shift
    # the undetermined<->weak boundary WHEN a real structural signal is already
    # present, and can NEVER alone flip a genuinely-undetermined case to a confident
    # (strong) deception verdict.
    baseline = _Sum(_NodesOf("AppliedClassBaseline"), "ab", _A(_V("ab"), "baseline_prior"))
    D_eff = _Plus(D, baseline)

    # --- FOLLOW-ON B: a LEGAL-HEDGING reading present (the agent-authored
    # UtterancePhrase X LegalHedgingCue join minted a LegalHedgingReading). Its
    # forcing is LEGAL and MUTUALLY UNDERSTOOD, so it routes to its OWN band
    # `legal_hedging` (NOT on the deception<->opacity axis) -- but ONLY when the
    # divergence is EXPLAINED by it, i.e. NO competing structural_forcing money/power
    # signal (model_based). A real structural_forcing divergence DOMINATES: a hedge
    # phrase co-occurring does NOT downgrade it to legal_hedging.
    has_legal_hedge = _Exists(_NodesOf("LegalHedgingReading"), "lh",
                              _Eq(_A(_V("lh"), "phrase"), _A(_V("lh"), "phrase")))

    # --- FOLLOW-ON C: a DIVERGENCE (a detected mismatch / explicit falsehood) is
    # present. Deception-shaped by construction. When it has NO structural/documentary
    # explanation (`_Not(struct_doc)` -> no ForcedChoiceExpectation match, no measurable
    # stakes) AND no legal-hedge explanation, the ABSENCE of a stakes-fit is itself the
    # signal: it routes to `non_instrumental` (a non-strategic cause -- compulsion /
    # identity), which is DISTINCT from a bare no-model UNDETERMINED (which has no
    # divergence at all) and is NEVER labelled deception.
    divergence = _Exists(_NodesOf("DivergenceFact"), "df",
                         _Eq(_A(_V("df"), "present"), _L(1.0)))

    # verdict = nested IfThenElse (the WHOLE banding decision, one Term tree).
    verdict = _Ite(
        _And(has_legal_hedge, _Not(model_based)),         # B: legal register, no rival forcing
        _L("legal_hedging"),
        _Ite(
            _Not(struct_doc),                             # no structural/documentary signal
            _Ite(divergence,                              # C: deception-shaped but unexplained
                 _L("non_instrumental"), _L("undetermined")),
            _Ite(_Gt(D_eff, O),                           # deception leaning (D_eff = D + prior)
                 _Ite(single_obs, _L("undetermined"),     # single-observation clamp
                      _Ite(_And(_Gte(D_eff, _L(_DECEPTION_STRONG_MIN)), awareness_real),
                           _L("strong_deception"),
                           _Ite(_Gte(D_eff, _L(_DECEPTION_WEAK_MIN)),
                                _L("weak_deception"), _L("undetermined")))),
                 _Ite(_Gte(O, _L(_OPACITY_STRONG_MIN)), _L("strong_opacity"),  # opacity leaning
                      _Ite(_Gte(O, _L(_OPACITY_WEAK_MIN)),
                           _L("weak_opacity"), _L("undetermined"))))))

    # THE OUTPUT IS A CONFIDENCE INTERVAL, not a coarse band. `lean_score` is the
    # POINT ESTIMATE (deception mass minus opacity mass; stakes already scaled into
    # each structural_forcing weight). `residual_other_mass` is the interval
    # HALF-WIDTH (uncertainty): a floor that SHRINKS with decisiveness (|score|) but
    # NEVER reaches 0 -- being certain is impossible, but a reasonable bounded
    # estimate is not -- PLUS the genuine opposing mass present. So high-stakes /
    # decisive evidence -> a narrower interval that need not cross 0 (a committed
    # lean); low-stakes / weak evidence -> a wide interval straddling 0
    # (UNDETERMINED). interval = [lean_score - residual, lean_score + residual].
    lean_score = _Minus(D_eff, O)
    abs_score = _Abs(_Minus(D_eff, O))
    # confidence in [0,1) — NEVER 1.0 (no certainty): |score| / (|score| + 1).
    confidence = _Div(abs_score, _Plus(abs_score, _L(1.0)))
    residual = _Plus(_Div(_L(_RESIDUAL_FLOOR), _Plus(_L(1.0), abs_score)), _Min(D_eff, O))
    interval_low = _Minus(lean_score, residual)
    interval_high = _Plus(lean_score, residual)
    proxy_flag = _Ite(proxy, _L(1.0), _L(0.0))
    model_flag = _Ite(model_based, _L(1.0), _L(0.0))

    return {
        "name": "epistemic_combine_band",
        "batch": False,
        "match": [["agent", "has_epistemic_anchor", "anchor"]],
        "where": _Not(_Exists(_NodesOf("EpistemicLeanReading"), "r2",
                              _Eq(_A(_V("r2"), "kind"), _L("epistemic_lean")))),
        "effects": [
            ["add_node", "reading", "EpistemicLeanReading", {
                "kind": "epistemic_lean",
                "verdict": {"__term__": verdict},
                "lean_score": {"__term__": lean_score},
                "confidence": {"__term__": confidence},
                "residual_other_mass": {"__term__": residual},
                "interval_low": {"__term__": interval_low},
                "interval_high": {"__term__": interval_high},
                "deception_mass": {"__term__": D},
                "opacity_mass": {"__term__": O},
                "baseline_prior": {"__term__": baseline},
                "proxy_based": {"__term__": proxy_flag},
                "model_based": {"__term__": model_flag},
                "revisable": 1.0,
            }],
            ["add_edge", "agent", "has_epistemic_lean_reading", "reading"],
        ],
    }


def ensure_epistemic_combine_rule(agent) -> dict:
    """Install the combine rule + the singleton assessment anchor (both idempotent).
    Returns a report naming the capability rung."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is not None and not sub.nodes("EpistemicAssessmentAnchor"):
        anchor = sub.add_node("EpistemicAssessmentAnchor", {"present": 1.0})
        native.add_edge_unchecked(ag_node, "has_epistemic_anchor", anchor)
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    installed = False
    if "epistemic_combine_band" not in names:
        native.add_rule(_combine_rule())
        installed = True
    return {"installed": installed,
            "rung": "hand-authored graph rule -- a global masses-and-gates banding is NOT a "
                    "classify-by-join, so it is beyond the agent's current authoring faculty; "
                    "the DECISION still lives in the graph (a nested IfThenElse Term tree run "
                    "by Rust), Python only assembles the rule JSON."}


# --------------------------------------------------------------------------- #
#  MECHANICAL READERS — query the held beliefs back out.
# --------------------------------------------------------------------------- #
def held_epistemic_evidence(agent) -> list:
    """Held `EpistemicEvidence` beliefs (the classified signals). Pure graph read."""
    sub, _, _ = _resolve(agent)
    out = []
    for nd in sub.nodes("EpistemicEvidence"):
        at = sub.node(nd)["attrs"]
        out.append({"signal_name": at.get("signal_name"), "lean": at.get("lean"),
                    "weight": at.get("weight"), "evidence_kind": at.get("evidence_kind"),
                    "actor": at.get("actor"), "model_based": at.get("model_based"),
                    "proxy_based": at.get("proxy_based")})
    return out


def held_epistemic_readings(agent) -> list:
    """Held `EpistemicLeanReading` verdicts, each rendered with its BASIS (which
    signals fired, read mechanically off the held evidence) + the humility caveat.
    Pure graph read + mechanical string rendering (no decision): NO band is
    'certain', residual_other_mass is echoed (never 0), and when a
    `structural_forcing` signal is in the basis the rendering NAMES the held
    structural model as itself defeasible/revisable and records that the mechanism
    was routed by model-asymmetry, not by a documentary confession."""
    sub, _, _ = _resolve(agent)
    basis = sorted({str(sub.node(nd)["attrs"].get("signal_name"))
                    for nd in sub.nodes("EpistemicEvidence")})
    # measured stakes behind any structural_forcing evidence (the money/power at
    # risk that anchors the interval) — read mechanically off the evidence.
    stakes_vals = [sub.node(nd)["attrs"].get("stakes")
                   for nd in sub.nodes("EpistemicEvidence")
                   if sub.node(nd)["attrs"].get("signal_name") == "structural_forcing"]
    out = []
    for nd in sub.nodes("EpistemicLeanReading"):
        at = sub.node(nd)["attrs"]
        residual = at.get("residual_other_mass")
        interval = [at.get("interval_low"), at.get("interval_high")]
        model_note = ""
        verdict = at.get("verdict")
        if verdict == "legal_hedging":
            # FOLLOW-ON B: a DISTINCT band off the deception<->opacity axis.
            model_note = ("liability-forced register (lawyer-approved weasel-words), MUTUALLY "
                          "UNDERSTOOD as such -- not a claim about the actual state, so NOT "
                          "deception and NOT an introspection gap; a forced choice whose forcing "
                          "is LEGAL")
        elif verdict == "non_instrumental":
            # FOLLOW-ON C: deception-shaped, but the ABSENCE of a stakes-fit is the signal.
            model_note = ("deception-shaped, but NO ForcedChoiceExpectation match and NO measurable "
                          "stakes explain it -> points to a NON-STRATEGIC cause (compulsion / "
                          "identity), NOT strategic concealment; the absence of a stakes explanation "
                          "is itself the signal")
        elif "structural_forcing" in basis:
            model_note = ("this verdict rests on a HELD structural (socioeconomic / "
                          "forced-choice money-power) model that is itself DEFEASIBLE and "
                          "REVISABLE; the mechanism (deception vs introspection-gap) was "
                          "ROUTED by the actor_can_introspect field of that held model, and "
                          "its CONFIDENCE is anchored by the MEASURED STAKES %s (the "
                          "money/power at risk) -- the agent's model-advantage over "
                          "symmetric, stakes-free peer judgement, NOT a documentary "
                          "confession" % (stakes_vals or "n/a"))
        # FOLLOW-ON A: surface the class-level prior (a PRIOR, never per-act evidence)
        # if one shifted the start toward deception.
        if float(at.get("baseline_prior") or 0.0) > 0.0:
            model_note = (model_note + "  " if model_note else "") + (
                "a class-level BASELINE-DECEPTION PRIOR (%r) shifted the starting lean toward "
                "deception -- a calibrated class prior, NOT per-act evidence: it can never alone "
                "reach a confident (strong) deception verdict" % at.get("baseline_prior"))
        caveat = ("NEVER certain (revisable:%s); residual_other_mass=%r is never 0 and is "
                  "the interval half-width -- a competent self-deceiver is textually "
                  "identical to a sincere actor, and any held structural model is imperfect, "
                  "so the OTHER mechanism always keeps mass. lean is a bounded estimate "
                  "[%s, %s], not a certainty" % (at.get("revisable"), residual,
                                                 interval[0], interval[1]))
        out.append({
            "verdict": at.get("verdict"),
            "lean_score": at.get("lean_score"),
            "confidence": at.get("confidence"),
            "residual_other_mass": residual,
            "interval": interval,
            "deception_mass": at.get("deception_mass"),
            "opacity_mass": at.get("opacity_mass"),
            "baseline_prior": at.get("baseline_prior"),
            "proxy_based": at.get("proxy_based"),
            "model_based": at.get("model_based"),
            "stakes": stakes_vals,
            "basis": basis,
            "model_note": model_note,
            "caveat": caveat,
            "revisable": at.get("revisable"),
        })
    return out


def assess_epistemic_lean(agent) -> list:
    """Mechanical driver: settle the DETECTION + structural-forcing rules to
    fixpoint, THEN install + run the COMBINE band, and read the verdict out. The
    combine is installed only AFTER detection has settled, so the single minted
    reading reflects ALL the evidence. Pure world-adapter orchestration (tick and
    read) — no decision over graph state."""
    sub, native, ag_node = _resolve(agent)
    ensure_structural_forcing_rules(agent)
    ensure_class_baseline_apply_rule(agent)    # FOLLOW-ON A: mint AppliedClassBaseline
    native.run_rules(10000)                    # detection + structural forcing + baseline apply
    ensure_epistemic_combine_rule(agent)
    native.run_rules(10000)                    # the banding fires once
    return held_epistemic_readings(agent)


# =========================================================================== #
#  FOLLOW-ON A — BASELINE-DECEPTION PRIOR (calibrated, class-level, PRIOR-not-
#  conviction). Deception is the ASSUMED NORM for some actor classes (advertiser /
#  politician / pr / corporation): a small class-level prior that shifts the
#  STARTING lean toward deception, WITHOUT ever becoming per-act evidence. The
#  moral asymmetry is enforced STRUCTURALLY in the combine (a prior is not
#  EpistemicEvidence, so it never sets struct_doc and can never supply awareness)
#  -- see the combine's FOLLOW-ON A note. This section supplies ONLY: the teachable
#  codebook, a MECHANICAL class annotator (the WORLD supplies the class, exactly as
#  annotate_internal_knowledge_trace takes a world-supplied documentary flag), the
#  hand-authored plumbing JOIN that applies the prior, and a reader.
#
#  CAPABILITY RUNG (reported honestly): the baseline ADD lives in the combine Term
#  (a global masses-and-gates banding, beyond the agent's classify-by-join
#  authoring); the ActorClassFact X ClassBaseline JOIN is a trivial single-key
#  plumbing rule hand-authored here (the same legal category as the structural-
#  forcing builders) -- the DECISION stays in graph Terms, Python only assembles
#  the JSON.
# =========================================================================== #
CLASS_BASELINE_CODEBOOK = [
    {"actor_class": "advertiser", "baseline_prior": 0.2,
     "note": "advertising is a persuasion register everyone already discounts -- a small "
             "class-level prior toward deception, never a per-act conclusion."},
    {"actor_class": "politician", "baseline_prior": 0.2,
     "note": "campaign speech is read with a standing discount; a class-level prior only."},
    {"actor_class": "pr", "baseline_prior": 0.25,
     "note": "public-relations output is liability/interest-shaped by trade -- a slightly "
             "higher class prior, still never per-act evidence."},
    {"actor_class": "corporation", "baseline_prior": 0.15,
     "note": "a corporate voice serves a fiduciary interest; a modest class-level prior."},
]


def ensure_class_baseline_codebook(agent) -> None:
    """Reconcile-wire every held `ClassBaseline` row (seeded, or minted by a later
    `teach()`) to the agent root via `has_class_baseline`, so the baseline-apply
    JOIN sees it without a fresh boot. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    _wire_codebook_by_key(agent, "ClassBaseline", "has_class_baseline", "actor_class")


def seed_class_baseline_codebook(agent, *, rows=CLASS_BASELINE_CODEBOOK) -> None:
    """Teach the whole `ClassBaseline` codebook via the agent's OWN `teach()`, then
    reconcile-wire it. Idempotent (re-teaching is a no-op)."""
    from domains.teach import teach
    for row in rows:
        teach(agent, "ClassBaseline", dict(row))
    ensure_class_baseline_codebook(agent)


def _existing_actor_class_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("ActorClassFact"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("actor")), str(at.get("actor_class"))))
    return out


def annotate_actor_class(agent, actor: str, actor_class: str) -> Optional[int]:
    """Record the WORLD-SUPPLIED class of an actor as ONE `ActorClassFact{actor,
    actor_class}` fact -- UNCONDITIONALLY, no codebook check, no decision (the SAME
    'the world hands over the fact, the annotator only records it' discipline as
    annotate_internal_knowledge_trace). WHICH class an actor belongs to is an
    external datum, never inferred here from stylistic text. Wired via
    `has_actor_class_fact`. Idempotent by (actor, actor_class). Returns the node id
    (or None if already present)."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return None
    if (str(actor), str(actor_class)) in _existing_actor_class_keys(sub):
        return None
    node = sub.add_node("ActorClassFact", {"actor": str(actor), "actor_class": str(actor_class)})
    native.add_edge_unchecked(ag_node, "has_actor_class_fact", node)
    return node


def _class_baseline_apply_rule() -> dict:
    """JOIN `ActorClassFact` to `ClassBaseline` on actor_class and mint ONE
    `AppliedClassBaseline{actor_class, baseline_prior}` per matched class (dedup by
    actor_class). This is the plumbing that carries the taught class prior into the
    graph so the combine can sum it; the ADD itself is the combine Term's."""
    return {
        "name": "apply_class_baseline",
        "batch": False,
        "match": [["agent", "has_actor_class_fact", "acf"],
                  ["agent", "has_class_baseline", "cb"]],
        "where": _And(
            _Eq(_A(_V("acf"), "actor_class"), _A(_V("cb"), "actor_class")),
            _Not(_Exists(_NodesOf("AppliedClassBaseline"), "a2",
                         _Eq(_A(_V("a2"), "actor_class"), _A(_V("acf"), "actor_class")))),
        ),
        "effects": [
            ["add_node", "ab", "AppliedClassBaseline", {
                "actor_class": {"__term__": _A(_V("acf"), "actor_class")},
                "baseline_prior": {"__term__": _A(_V("cb"), "baseline_prior")},
            }],
            ["add_edge", "agent", "has_applied_class_baseline", "ab"],
        ],
    }


def ensure_class_baseline_apply_rule(agent) -> dict:
    """Reconcile-wire the ClassBaseline codebook + install the baseline-apply JOIN
    (idempotent by name). Returns a report naming the capability rung."""
    sub, native, ag_node = _resolve(agent)
    ensure_class_baseline_codebook(agent)
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    installed = False
    if "apply_class_baseline" not in names:
        native.add_rule(_class_baseline_apply_rule())
        installed = True
    return {"installed": installed,
            "rung": "hand-authored plumbing JOIN (single-key) -- the DECISION (adding the "
                    "prior to the starting lean) lives in the combine Term; Python only "
                    "assembles the JSON."}


# =========================================================================== #
#  FOLLOW-ON B — LEGAL_HEDGING is NOT deception (a distinct verdict). Lawyer-
#  approved weasel-words ("may contribute to", "results not typical", "helps
#  support", "up to X", "may help", "is designed to") are a LIABILITY-MINIMISING
#  REGISTER everyone reads as such -- a FORCED CHOICE whose forcing is LEGAL and
#  MUTUALLY UNDERSTOOD. It must NOT route to deception (nor introspection-gap): it
#  gets its OWN band `legal_hedging`.
#
#  AGENT-AUTHORED: recognition REUSES the GENERIC `annotate_utterance_phrases`
#  n-gram annotator and a TEACHABLE `LegalHedgingCue{phrase, register}` codebook,
#  and the AGENT AUTHORS the classify-by-join rule ITSELF ("When an utterance
#  phrase's phrase matches a legal hedging cue's phrase, classify a legal hedging
#  reading.") via procedural_reader.read_method -> binding_resolver.derive_binding
#  -> method_synthesis.synthesise_rule_from_method -> synth_classify_legal_hedging_
#  reading. NO hand-written detection rule, NO shipped rule. This section supplies
#  ONLY the codebook + wiring + a reader; the ROUTING to the `legal_hedging` band is
#  the combine Term's (see the combine's FOLLOW-ON B note).
# =========================================================================== #
LEGAL_HEDGING_CUE_CODEBOOK = [
    {"phrase": "may contribute to", "register": "liability-forced-register"},
    {"phrase": "results not typical", "register": "liability-forced-register"},
    {"phrase": "helps support", "register": "liability-forced-register"},
    {"phrase": "up to", "register": "liability-forced-register"},
    {"phrase": "may help", "register": "liability-forced-register"},
    {"phrase": "is designed to", "register": "liability-forced-register"},
]


def ensure_legal_hedging_codebook(agent) -> None:
    """Reconcile-wire every held `LegalHedgingCue` row (seeded, or minted by a later
    `teach()`) to the agent root via `has_legal_hedging_cue`, so the AGENT-AUTHORED
    join rule (and derive_binding's codebook grounding) sees it without a fresh
    boot. Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_legal_hedging_cue"))
    for n in sub.nodes("LegalHedgingCue"):
        if n not in wired:
            native.add_edge_unchecked(ag_node, "has_legal_hedging_cue", n)


def seed_legal_hedging_codebook(agent, *, rows=LEGAL_HEDGING_CUE_CODEBOOK) -> None:
    """Teach the whole `LegalHedgingCue` codebook via the agent's OWN `teach()`,
    then reconcile-wire it. Idempotent (re-teaching is a no-op)."""
    from domains.teach import teach
    for row in rows:
        teach(agent, "LegalHedgingCue", dict(row))
    ensure_legal_hedging_codebook(agent)


def held_legal_hedging_readings(agent) -> list:
    """The agent's held `LegalHedgingReading` beliefs -- the weasel-word phrase that
    fired (from f) + the register the taught cue named (from c). Pure graph read, no
    decision."""
    sub, _, _ = _resolve(agent)
    out: list = []
    for nd in sub.nodes("LegalHedgingReading"):
        at = sub.node(nd)["attrs"]
        out.append({"phrase": at.get("phrase"), "register": at.get("register")})
    return out


# =========================================================================== #
#  FOLLOW-ON C — NON_INSTRUMENTAL_DECEPTION (the compulsive anomaly). A DIVERGENCE
#  (a detected mismatch -- a conflicting-meta-goal ActorGoal, or an explicit
#  falsehood marker the world supplies) with NO ForcedChoiceExpectation match AND
#  NO measurable stakes AND no legal-hedge explanation is "deception-shaped but has
#  NO instrumental explanation" -- the compulsive / anomalous case. This section
#  supplies ONLY the mechanical DivergenceFact annotator; the ROUTING to the
#  `non_instrumental` band is the combine Term's (see the combine's FOLLOW-ON C
#  note).
# =========================================================================== #
def _has_divergence_fact(sub) -> bool:
    return bool(sub.nodes("DivergenceFact"))


def annotate_divergence(agent, *, detected: bool = False) -> Optional[int]:
    """Record that a DIVERGENCE (a detected surface/actor mismatch or an explicit
    falsehood marker) is present, as a singleton `DivergenceFact{present:1.0}`. The
    fact is written when EITHER the world hands over an explicit `detected` marker
    (an ingested falsehood flag, exactly like annotate_internal_knowledge_trace's
    documentary flag) OR a held `ActorGoal` already carries
    `serves_conflicting_meta_goal==1.0` (a mechanical presence read of an
    already-minted belief -- no decision). Idempotent (singleton). Returns the node
    id (or None)."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None or _has_divergence_fact(sub):
        return None
    from_belief = any(
        float(sub.node(nd)["attrs"].get("serves_conflicting_meta_goal") or 0.0) == 1.0
        for nd in sub.nodes("ActorGoal"))
    if not (detected or from_belief):
        return None
    node = sub.add_node("DivergenceFact", {"present": 1.0})
    native.add_edge_unchecked(ag_node, "has_divergence_fact", node)
    return node
