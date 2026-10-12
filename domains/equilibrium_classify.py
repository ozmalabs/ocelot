"""Equilibrium classifier sidecar — the THIN world adapter (tracks T3 / T3b / T3c / T3e / T3f / T3g, pack 0.8.0).

CLAUDE.md "the agent is a graph in Rust": this module does only
  * INGEST  — each message becomes Message/Token/CodeSpan/LinkSpan nodes + edges
              (I/O-boundary tokenisers: code fences/backticks, URLs, lowercase
              word tokens; clause index from sentence punctuation; per-token
              boundary attrs `lemma` (WordNet morphy) and `eq_class` (digit
              token -> "<num>", else first-sense WordNet noun lexname, e.g.
              "<noun.person>"); plus the speech-act SIGNALS the existing parse
              layer already computes via comprehend_text.kind_signals).
              Conversations (T3c) additionally ingest turns INCREMENTALLY onto a
              retained fork: one EqWindow conversation node, EqActor authorship,
              declared reply edges to earlier turns, integer turn position / ts
              (no adjacency edge: turn order is not structure since 0.5.0).
              `discourse` = open + one ingest + close.
  * TICK    — run_rules: the seeded rules (seeds/speech_act_classify.json +
              seeds/equilibrium_*.json) decide every label, quantum and episode.
              Discourse ticks the rule fixpoint once per seeded STRATUM: the
              strata are EqStratum nodes in seeds/equilibrium_window.json, and
              the adapter opens them in their seeded order by adding one marker
              edge each (a fixed clock schedule, never a branch on graph state),
              so rules that read ABSENCE only run after what they negate over
              has reached its fixpoint (stratified negation).
  * EMIT    — a mechanical read of the attrs/edges those rules wrote, joined to
              the seeded LabelStatus nodes.
No label, trait or episode is decided here. OZMA_NO_LLM=1 is expected; nothing
here reaches an LLM (WordNet is a local corpus lookup; it is never downloaded).

Usage (caller owns isolation — run on a FORK, never the frozen base):
    s, root = boot()
    snap = s.snapshot(); branch = snap.fork()
    labels = classify(branch, root, [{"id": "m1", "text": "how?"}])
    out = discourse(snap.fork(), root, {"window_id": "w1", "kind": "thread"},
                    [{"id": "t1", "actor_ref": "actor_a", "text": "..."}])
    conv = snap.fork(); st = conversation_open(conv, root, "c1", "meeting")
    conversation_ingest(conv, root, st, turns, participants)  # per batch: turns (+ roster, 0.7.0) + EVIDENCE DELTAS
    conversation_close(conv, root, st)           # final read-out (deltas: empty, no ticks)
    conversation_full(conv, root, st)            # complete quanta / episodes (discourse)
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
import threading
from typing import Any, Iterable

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

PACK_VERSION = "0.8.0"
TAXONOMY_VERSION = "eq-tax-0.8.0"
PACK_IDS = ("equilibrium_tokens", "equilibrium_window", "equilibrium_lexicon",
            "equilibrium_scope", "equilibrium_msg", "equilibrium_pattern",
            "equilibrium_traits", "equilibrium_quanta", "equilibrium_competence",
            "equilibrium_episode", "equilibrium_climate", "equilibrium_tracking",
            "equilibrium_label_status")
FIRE_PREFIX = "eqfire:"   # label-deciding rule fired on a Message
CUE_PREFIX = "eqcue:"     # cue-recognition rule fired on a Message (provenance only)
RULE_PREFIX = "eqrule:"   # quanta/episode rule contributed to a node (provenance)
RULE_STEP_BUDGET = 10_000
# Fuel cap per stratum tick (an engine resource bound, not a decision parameter):
# if a tick spends it all, the fixpoint is incomplete and the request errors.
# Same cap as classify; synthetic 500-turn windows use <= 37 steps per tick
# (SLICE RESULTS), i.e. > 2x headroom (PREREG P6).
DISCOURSE_FUEL = RULE_STEP_BUDGET

# I/O-boundary tokenisers (emit tokens, never labels).
_FENCE = re.compile(r"```.*?(?:```|$)", re.S)
_INLINE = re.compile(r"`[^`\n]+`")
_URL = re.compile(r"\b(https?)://\S+", re.I)
_WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_CLAUSE = re.compile(r"[.!?;:,\n]+")
# Token shape classes (I/O-boundary lexing, not labels): seeded cue slots such as
# "<num>" / "<noun.person>" match them; "<" can never occur in a `form`.
NUM_CLASS = "<num>"


class BudgetExhausted(RuntimeError):
    """A stratum tick spent its whole fuel cap: the fixpoint is not complete."""


def _native(s):
    return getattr(s, "_inner", s)


def pack_manifests() -> list[dict]:
    return [manifest_for(sid) for sid in PACK_IDS]


def pack_digest() -> str:
    """sha256 over the pack manifests' canonical JSON bytes, in PACK_IDS order."""
    blob = json.dumps(pack_manifests(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def load_pack(substrate, agent_root) -> None:
    """Install the pack manifests (in dependency order) onto a substrate whose
    out-of-pack deps (speech_act_classify and its closure) are already loaded."""
    for m in pack_manifests():
        _native(substrate).load_seed_manifest(m, agent_root)


def boot():
    """Fresh substrate with the pack and its whole dependency closure.
    Warms the WordNet boundary lookups so the first request does not pay for them."""
    _wordnet()
    return boot_core(PACK_IDS)


# ---- boundary tokens: lemma + noun class (WordNet, local corpus only) -------
@functools.lru_cache(maxsize=1)
def _wordnet():
    """Local WordNet only: a missing corpus is an error, never a download."""
    from nltk.corpus import wordnet as wn
    wn.ensure_loaded()
    return wn


# NLTK's WordNet reader is not thread-safe (lazily opened, shared data-file
# handles); conversations are ingested on parallel worker threads, so every
# WordNet lookup is serialised (the lru caches below make repeats lock-free).
_WN_LOCK = threading.Lock()


@functools.lru_cache(maxsize=65_536)
def lemma(form: str) -> str:
    """Opaque string normalisation: WordNet morphy (verb reading, then noun),
    else the form itself. Shared with the seed builder so cue words and tokens
    are normalised by the same function."""
    wn = _wordnet()
    with _WN_LOCK:
        return wn.morphy(form, "v") or wn.morphy(form, "n") or form


@functools.lru_cache(maxsize=65_536)
def noun_class(form: str) -> str | None:
    """First-sense WordNet noun lexname of the token's lemma as a class token
    ("<noun.person>"); first sense is a lookup, not a disambiguation decision."""
    lem = lemma(form)
    with _WN_LOCK:
        syn = _wordnet().synsets(lem, "n")
    return f"<{syn[0].lexname()}>" if syn else None


def token_class(form: str) -> str | None:
    return NUM_CLASS if form.isdigit() else noun_class(form)


def _spans(text: str) -> tuple[list[tuple[str, dict]], str]:
    """Code/link spans as (node type, attrs) + the residual prose for word tokens."""
    spans: list[tuple[str, dict]] = []
    for rx, form in ((_FENCE, "fence"), (_INLINE, "inline")):
        spans += [("CodeSpan", {"eq_span": "code", "form": form}) for _ in rx.findall(text)]
        text = rx.sub(" ", text)
    spans += [("LinkSpan", {"eq_span": "link", "scheme": sch.lower()}) for sch in _URL.findall(text)]
    return spans, _URL.sub(" ", text)


def _ingest(s, root, msg: dict, extra: dict | None = None) -> Any:
    from domains.comprehend_text import kind_signals
    n = _native(s)
    text = str(msg.get("text") or "")
    sig = kind_signals(s, text)
    attrs = {"eq_ref": str(msg["id"]), "sak_pending": 1.0,
             "sak_ends_q": 1.0 if sig["ends_q"] else 0.0}
    attrs.update({f"sak_{k}": sig[k] for k in ("first_role", "first_pos") if sig.get(k)})
    attrs.update(extra or {})
    m = n.add_node("Message", attrs)
    n.add_edge(root, "received", m)
    spans, prose = _spans(text)
    for typ, sattrs in spans:
        n.add_edge(m, "eq_has_span", n.add_node(typ, sattrs))
    pos = 0
    clauses = _CLAUSE.split(prose.replace("\u2019", "'").lower())
    for ci, clause in enumerate(clauses):
        prev = None  # the token chain does not cross a clause boundary
        for w in _WORD.findall(clause):
            tattrs = {"form": w, "lemma": lemma(w), "eq_pos": pos, "eq_clause": ci}
            cls = token_class(w)
            if cls is not None:
                tattrs["eq_class"] = cls
            t = n.add_node("Token", tattrs)
            n.add_edge(m, "eq_has_token", t)
            if prev is not None:
                n.add_edge(prev, "eq_next", t)
            prev = t
            pos += 1
    return m


def _label_status(s, root) -> dict[str, dict]:
    n = _native(s)
    rows = [n.node(x)["attrs"] for x in n.neighbours(root, "eq_has_label_status")]
    return {r["label"]: r for r in rows}


def _rule_ids(attrs: dict, *prefixes: str) -> list[str]:
    return [f"{k.split(':', 1)[1]}@{PACK_VERSION}"
            for k in sorted(attrs) if k.startswith(prefixes) and attrs[k] is not None]


def _read(s, m, status: dict[str, dict]) -> dict:
    """Mechanical read-out: every `eqfire:<rule>` attr -> (label, value, rule_id);
    `eqcue:<rule>` attrs are cue-recognition provenance (rule ids only).
    The label is the rule name minus the `eq.` prefix and its variant segment."""
    attrs = _native(s).node(m)["attrs"]
    out: dict = {"id": attrs["eq_ref"], "labels": {}, "rule_ids": []}
    for key in sorted(k for k in attrs if k.startswith(FIRE_PREFIX)):
        rule_name = key[len(FIRE_PREFIX):]
        label = rule_name[len("eq."):].rsplit(".", 1)[0]
        rid = f"{rule_name}@{PACK_VERSION}"
        st = status.get(label, {})
        row = out["labels"].setdefault(label, {
            "values": [], "rule_ids": [], "status": st.get("status"),
            "match_class": st.get("match_class")})
        if attrs[key] not in row["values"]:
            row["values"].append(attrs[key])
        row["rule_ids"].append(rid)
    out["rule_ids"] = _rule_ids(attrs, FIRE_PREFIX, CUE_PREFIX)
    return out


def classify(substrate, agent_root, messages: Iterable[dict]) -> list[dict]:
    """Ingest -> run_rules -> read. Mutates `substrate` (pass a fork).
    Returns one dict per message, in input order:
      {"id", "labels": {label: {values, rule_ids, status, match_class}}, "rule_ids"}"""
    msgs = list(messages)
    nodes = [_ingest(substrate, agent_root, m) for m in msgs]
    _native(substrate).run_rules(RULE_STEP_BUDGET)
    status = _label_status(substrate, agent_root)
    return [_read(substrate, m, status) for m in nodes]


# ---- conversations (track T3c, pack 0.5.0) -----------------------------------
# One conversation = one RETAINED fork of the frozen base (the caller owns it).
#   * INGEST is incremental: each batch adds its turns to the retained fork
#     (Message/Token nodes, EqActor authorship, declared `eq_reply_to` to an
#     EARLIER turn of the conversation, integer `eq_turn_pos` / `eq_ts_ms`;
#     no adjacency edge), then ticks S0 there (the positive msg / cue / declared
#     structure layer), so every turn is tokenised and labelled exactly once.
#   * The strata S1..S5 read ABSENCE over the conversation so far (unanswered,
#     floor, match shapes, generative, ...). Ticked in place they would leave
#     stale facts behind as turns arrive (the rules mint, never retract), so each
#     batch ticks them on a SCRATCH fork of the retained fork, reads out, and
#     drops it: the read-out after every batch equals a one-shot run over the
#     same prefix.
#   * 0.5.1 (T3d): the MONOTONE strata rules (per-turn evidence / hedged /
#     counter cues, run, question demand, response type, answered, episode
#     root / extend / facet, competence corroboration) run LIVE on the retained
#     fork instead, driven by per-turn layer marks (L1 `eq_l1` + `eq_l1_open`,
#     then L2 `eq_l2` + `eq_l2_open` + `eq_qnew`) added after the tracking fixpoint and removed after
#     the layer's fixpoint (the batch frontier) -- each turn is evaluated once.
#     (scripts/_equilibrium_quanta_rules.py LIVE_L1 / LIVE_L2).
#   * 0.5.1 stage B: the NON-MONOTONE families (floor, selective non-response,
#     unanswered, claim grounding, generative outcome, match shapes) run live too,
#     with bounded rolling state the turn cursor finalises and dedicated retraction
#     edges (`eq_nm_quantum`, `eq_evidence_nm`, `eq_counter_nm`, ...). There is no
#     scratch fork; the read-out after every batch still equals a one-shot run over
#     the same prefix (golden- and per-prefix-checked, RESULTS T3d §5).
#   * EMIT reads per-turn structure for the batch's turns, the quanta/episodes
#     that are new or changed since they were last emitted (emitted marks are
#     `eqemit:` attrs on the conversation node, compared mechanically), and the
#     open questions. close() emits the complete final set.
# Turn / actor lookup is the substrate's attr index (Message.eq_ref,
# EqActor.actor_ref) on the retained fork. Per-conversation bookkeeping (seq,
# next turn position, last ts / ref, emitted marks) lives on an EqLedger node in
# the same fork that has NO edges: no rule binds or reaches it, so writing it
# never invalidates a rule's incremental cursor (isolated-node exemption). The
# handle below holds only the two node ids.
#
# Incremental evaluation (track T3d): conversation forks run the engine's
# semi-naive matching for every rule (incremental_match + precise_dirty +
# isolated-node exemption + batch_incremental): a batch's run_rules enumerates
# only bindings driven by the batch's new edges. Stage A (T3d scaling) adds four
# more evaluation-strategy flags that remove the remaining whole-prefix re-matches
# of the S0 / tracking / live layers: own_write_exempt (an effect's own dedup
# look-up never clears a cursor), precise_rule_deletes (the tracking cursor's
# DelEdge no longer clears EVERY rule's cursor), seeded_join_order (semi-naive
# sub-matches join outward from the seed with index hints + pushdown) and
# write_frontier (a local attr / edge write re-checks only the bindings of the
# written node). These are evaluation-strategy flags; the fixpoint they reach is
# the same (golden-checked, RESULTS T3d stage A).
# Stage B adds hop_frontier (one-hop local attr reads) and delete_frontier (a
# retraction edge's delete re-checks only its endpoints' bindings).
# Read-out is a DELTA (see _emit): only quanta / episodes the batch's ticks changed
# are re-read; open questions are the tracking rules' graph-resident QUD set
# `w -eq_qud-> q`.
# 0.6.0 (T3e) EVIDENCE DELTAS: the wire carries `quanta_delta` / `episodes_delta`
# instead of re-emitting whole rows. Every tick is the engine's exact-edge-delta
# run (run_rules_edge_delta): the NET existence change of every edge of the
# read-out's edge types (evidence / counter / quantum-existence / episode
# membership / facet) and the touched quantum / episode / facet nodes. An
# evidence pair's previous state is the engine's first-seen edge state, so the
# add / remove sets are read from the change alone (no list is re-read). The
# ledger keeps one mark per emitted quantum / episode (its id, sort key and
# scalar fields), so retraction (an existing quantum whose existence edges are
# gone) and field changes are mechanical comparisons. Folding every delta in
# seq order gives exactly the full rows a full read gives at that point
# (conversation_full; RESULTS T3e).
CONVERSATION_KINDS = ("meeting", "thread", "channel")
QUESTION_KEY = "eqlab:msg.speech_act=question"
EMIT_PREFIX = "eqemit:"
# a conversation's quanta: monotone (`eq_has_quantum`) and the non-monotone families'
# currently EXISTING ones (`eq_nm_quantum`); evidence / counter edges likewise include
# the families' retractable types (pack 0.5.1 stage B, scripts/_equilibrium_quanta_rules.py)
QUANTUM_EDGES = ("eq_has_quantum", "eq_nm_quantum")
EVIDENCE_EDGES = ("eq_evidence", "eq_hedged", "eq_context", "eq_evidence_nm")
COUNTER_EDGES = ("eq_counter", "eq_counter_nm")
EPISODE_EDGES = ("eq_has_episode", "eq_in_episode", "eq_has_facet")
# what the engine's exact-edge-delta run reports (edge types / node types)
DELTA_EDGE_TYPES = list(QUANTUM_EDGES + EVIDENCE_EDGES + COUNTER_EDGES + EPISODE_EDGES)
DELTA_NODE_TYPES = ["EqQuantum", "EqEpisode", "EqEpFacet"]


class Conversation:
    """Adapter handle for one retained conversation fork: the EqWindow node id
    and its (edge-less) EqLedger bookkeeping node id."""
    __slots__ = ("w", "ledger")

    def __init__(self, w, ledger) -> None:
        self.w, self.ledger = w, ledger


class Changes:
    """What one call's ticks changed, accumulated from the engine's
    exact-edge-delta reports (mechanical bookkeeping): touched node ids by type,
    and per edge key (src, type, tgt) [exists at the call's start, exists now]."""
    __slots__ = ("nodes", "edges")

    def __init__(self) -> None:
        self.nodes: dict[str, set] = {}
        self.edges: dict[tuple, list] = {}

    def add(self, rep: dict) -> None:
        for typ, ids in rep["affected_nodes"].items():
            self.nodes.setdefault(typ, set()).update(ids)
        for s, et, t, now in rep["edges_changed"]:
            k = (s, et, t)
            if k in self.edges:
                self.edges[k][1] = now
            else:
                self.edges[k] = [not now, now]

    def net(self) -> dict:
        """edge key -> exists now, for the edges whose existence changed"""
        return {k: now for k, (before, now) in self.edges.items() if before != now}


def _led(n, ledger, key: str):
    """one ledger attr (never the whole ledger: its marks grow with the conversation)"""
    return n.get_attr_many([ledger], key)[0]


def incremental_engine(n) -> None:
    """Turn on semi-naive evaluation for every rule of this substrate (and of
    forks taken from it): an engine evaluation strategy, not a decision."""
    n.set_incremental_match(True)
    n.set_precise_dirty(True)
    n.set_fresh_node_exempt(True)
    n.set_batch_incremental(True)
    n.set_own_write_exempt(True)  # an effect's own dedup look-up never clears a cursor
    n.set_precise_rule_deletes(True)  # a DelEdge-only rule invalidates per deleted type
    n.set_seeded_join_order(True)  # seeded sub-matches join outward from the seed
    n.set_write_frontier(True)  # a local attr write re-checks only bindings of the written node
    n.set_empty_match_proof(True)  # a closed live layer (no frontier mark) matches nothing
    n.set_hop_frontier(True)  # a one-hop local attr write re-checks only its E-neighbours' bindings
    n.set_delete_frontier(True)  # a retraction edge's delete re-checks only its endpoints' bindings


def _actors(n, w) -> list:
    """the conversation's actors: speakers (`eq_has_actor`), then roster participants
    who have not spoken (`eq_has_participant`); a quantum may be on either (e.g. an
    acknowledgement addressed to a named participant)"""
    sp = n.neighbours(w, "eq_has_actor")
    part = n.neighbours(w, "eq_has_participant")
    if not part:
        return sp
    seen = {a.value for a in sp}
    return sp + [a for a in part if a.value not in seen]


def _lookup(n, typ: str, key: str, value: str):
    hit = n.nodes_where(typ, key, value)
    return hit[0] if hit else None


def conversation_open(substrate, agent_root, conversation_id: str, kind: str) -> Conversation:
    n = _native(substrate)
    incremental_engine(n)
    for typ, key in (("Message", "eq_ref"), ("EqActor", "actor_ref")):
        if not n.has_attr_index(typ, key):
            n.declare_attr_index(typ, key)
    w = n.add_node("EqWindow", {"window_id": str(conversation_id),
                                "conversation_id": str(conversation_id),
                                "eq_kind": str(kind)})
    ledger = n.add_node("EqLedger", {"eq_seq": 0, "eq_next_pos": 0})  # never gets an edge
    n.add_edge(agent_root, "eq_window", w)
    return Conversation(w, ledger)


def conversation_info(substrate, state: Conversation) -> dict:
    n = _native(substrate)
    a = n.node(state.w)["attrs"]
    return {"conversation_id": a["conversation_id"], "seq": _led(n, state.ledger, "eq_seq"),
            "kind": a["eq_kind"]}


def conversation_check(substrate, state: Conversation, turns: list[dict]) -> str | None:
    """Ordering preconditions of a batch (no mutation): 'duplicate_turn' if an id
    repeats in the batch or already exists in the conversation, 'out_of_order'
    if a ts_ms is earlier than the latest ts_ms seen (ties keep array order)."""
    n = _native(substrate)
    last = _led(n, state.ledger, "eq_last_ts")
    seen: set[str] = set()
    for t in turns:
        tid = str(t["id"])
        if tid in seen or _lookup(n, "Message", "eq_ref", tid) is not None:
            return "duplicate_turn"
        seen.add(tid)
        ts = t.get("ts_ms")
        if ts is not None:
            if last is not None and int(ts) < last:
                return "out_of_order"
            last = int(ts)
    return None


def _alias_forms(text: str) -> list[str]:
    """An alias / name as the token forms the ingest tokeniser gives it in a turn
    (same normaliser and word pattern; clause punctuation is ignored, an alias is
    matched over consecutive token positions)."""
    return _WORD.findall(_CLAUSE.sub(" ", text.replace("\u2019", "'").lower()))


def _name_form(ref: str) -> str | None:
    name = ref.replace("\u2019", "'").lower()
    return name if _WORD.fullmatch(name) else None


def _roster(n, w, participants: list[dict]) -> None:
    """Participants roster (cumulative): each entry becomes / reuses the EqActor of
    its actor_ref, linked `w -eq_has_participant-> a` (NOT `eq_has_actor`: an actor
    joins the speakers -- floor, turn counts -- only with its first turn), plus one
    EqAlias per distinct alias token sequence (`a -eq_has_alias-> al`, its first
    form `a_form1`, its tokens `al -eq_alias_tok-> EqAliasTok{form, eq_apos}`). The
    actor_ref's own name form is one more alias. Ingest only: the tracking rule
    eq.trk.addressee.participant decides addressing. Aliases are transient: they
    exist only in this retained fork (dropped on close / eviction) and no read-out
    reads them."""
    for p in participants:
        ref = str(p["actor_ref"])
        actor = _lookup(n, "EqActor", "actor_ref", ref)
        if actor is None:
            attrs = {"actor_ref": ref}
            if _name_form(ref) is not None:
                attrs["eq_name_form"] = _name_form(ref)
            actor = n.add_node("EqActor", attrs)
        if not n.has_edge(w, "eq_has_participant", actor):
            n.add_edge(w, "eq_has_participant", actor)
        held = set(n.get_attr_many(n.neighbours(actor, "eq_has_alias"), "a_key")) \
            if n.neighbours(actor, "eq_has_alias") else set()
        names = ([ref] if _name_form(ref) is not None else []) + list(p.get("aliases") or ())
        for text in names:
            forms = _alias_forms(str(text))
            key = " ".join(forms)
            if not forms or key in held:
                continue  # no word token (cannot occur in a turn's tokens) / already held
            held.add(key)
            al = n.add_node("EqAlias", {"a_form1": forms[0], "a_key": key})
            n.add_edge(actor, "eq_has_alias", al)
            for i, f in enumerate(forms):
                n.add_edge(al, "eq_alias_tok", n.add_node("EqAliasTok", {"form": f, "eq_apos": i}))


def conversation_ingest(substrate, agent_root, state: Conversation, turns: list[dict],
                        participants: list[dict] | None = None) -> dict:
    """Append one batch (and optionally roster entries, which apply from this
    batch's turns on) to the retained conversation fork and read it out.
    The caller has run conversation_check. Returns
      {"conversation_id", "seq", "turns": [...], "turns_delta": [...], "quanta_delta": [...],
       "episodes_delta": [...], "open_questions": [...], "steps": [...]}"""
    n = _native(substrate)
    w = state.w
    if participants:
        _roster(n, w, participants)
    pos, last_ref, last_ts = _led(n, state.ledger, "eq_next_pos"), _led(n, state.ledger, "eq_last_ref"), None
    prev = _lookup(n, "Message", "eq_ref", last_ref) if last_ref is not None else None
    nodes = []
    for t in turns:
        rt = t.get("reply_to")
        tgt = _lookup(n, "Message", "eq_ref", str(rt)) if rt is not None else None
        extra: dict = {"eq_turn_pos": pos}
        pos += 1
        if t.get("ts_ms") is not None:
            extra["eq_ts_ms"] = int(t["ts_ms"])
        if rt is not None:
            extra["eq_reply_to_ref"] = str(rt)  # kept even when it names no earlier turn
        if t.get("platform_thread") is not None:
            extra["eq_platform_thread"] = str(t["platform_thread"])
        m = _ingest(substrate, agent_root, t, extra)
        ref = str(t["actor_ref"])
        actor = _lookup(n, "EqActor", "actor_ref", ref)
        if actor is None:
            # eq_name_form: the actor_ref under the SAME token normaliser (a token
            # equal to it is an explicit mention); eq_first_pos: ordering stamp so
            # a mention only resolves to an actor who has already spoken
            name = ref.replace("\u2019", "'").lower()
            aattrs = {"actor_ref": ref, "eq_first_pos": extra["eq_turn_pos"]}
            if _WORD.fullmatch(name):
                aattrs["eq_name_form"] = name
            actor = n.add_node("EqActor", aattrs)
            n.add_edge(w, "eq_has_actor", actor)
        elif not n.has_edge(w, "eq_has_actor", actor):
            # a roster participant's first turn: it joins the speakers now
            n.set_attr(actor, "eq_first_pos", extra["eq_turn_pos"])
            n.add_edge(w, "eq_has_actor", actor)
        n.add_edge(w, "eq_has_turn", m)
        n.add_edge(w, "eq_l0", m)  # S0 / tracking frontier mark (removed after tracking)
        n.add_edge(m, "eq_authored_by", actor)
        if prev is not None:
            n.add_edge(m, "eq_prev_turn", prev)  # turn ORDER (cursor + continuation only)
        prev = m
        if tgt is not None:
            n.add_edge(m, "eq_reply_to", tgt)
        if t.get("ts_ms") is not None:
            last_ts = int(t["ts_ms"])
        nodes.append(m)
    if turns:
        n.set_attr(state.ledger, "eq_last_ref", str(turns[-1]["id"]))
        n.set_attr(state.ledger, "eq_next_pos", pos)
    if last_ts is not None:
        n.set_attr(state.ledger, "eq_last_ts", last_ts)
    touched = Changes()  # what this batch's ticks changed (engine reports; delta read-out)
    s0 = _tick(n, touched)  # S0 on the retained fork
    if s0 >= DISCOURSE_FUEL:
        raise BudgetExhausted("rule fuel exhausted")
    # S0 is at fixpoint for the new turns: queue them for the seeded turn cursor
    # (equilibrium_tracking) and tick again on the retained fork
    for m in nodes:
        n.add_edge(w, "eq_trk_pending", m)
    trk = _tick(n, touched)
    if trk >= DISCOURSE_FUEL:
        raise BudgetExhausted("rule fuel exhausted")
    # the batch's turns are final for the per-turn window / tracking rules:
    # retire them from that frontier, so later batches never re-match them
    for m in nodes:
        n.remove_edge(w, "eq_l0", m)
    # 0.8.0: earlier turns the cursor REVISED in this batch (uptake / freeze:
    # `w -eq_trk_rev-> m`) are re-read as turns_delta; those collapsed late
    # (`w -eq_trk_late-> m`, already materialised) re-enter the live layers below
    # with the batch's turns. Both are frontier marks: removed once read.
    rev, late = n.neighbours(w, "eq_trk_rev"), n.neighbours(w, "eq_trk_late")
    for m in rev:
        n.remove_edge(w, "eq_trk_rev", m)
    for m in late:
        n.remove_edge(w, "eq_trk_late", m)
    batch = {m.value for m in nodes}
    layered = nodes + [m for m in late if m.value not in batch]
    # the tracked turns enter the LIVE (monotone) strata layers in order -- L1
    # per-turn rules, then L2 (rules whose absence test reads an L1 fact) -- as
    # the layer's frontier marks, which are removed once its fixpoint is reached
    live = []
    for layer in ("eq_l1", "eq_l2"):
        for m in layered:
            n.add_edge(w, layer, m)
        if layer == "eq_l1":
            n.add_edge(agent_root, "eq_l1_open", w)
        if layer == "eq_l2":
            qnew = _new_quanta(n, state)
            for q in qnew:
                n.add_edge(w, "eq_qnew", q)
            n.add_edge(agent_root, "eq_l2_open", w)
        live.append(_tick(n, touched))
        if live[-1] >= DISCOURSE_FUEL:
            raise BudgetExhausted("rule fuel exhausted")
        for m in layered:
            n.remove_edge(w, layer, m)
        if layer == "eq_l1":
            n.remove_edge(agent_root, "eq_l1_open", w)
        if layer == "eq_l2":
            n.remove_edge(agent_root, "eq_l2_open", w)
            for q in qnew:
                n.remove_edge(w, "eq_qnew", q)
    seq = _led(n, state.ledger, "eq_seq") + 1
    n.set_attr(state.ledger, "eq_seq", seq)
    out = _emit(substrate, agent_root, state, nodes, touched,
                [m for m in rev if m.value not in batch])
    out["steps"] = [s0, trk] + live + out["steps"]
    return out


def _new_quanta(n, state: Conversation) -> list:
    """Quanta first minted on the retained fork in this batch (mechanical set
    difference against the ledger's `eqq:` marks; bounded by actors x quanta,
    not by conversation length; the quantum keys are read in bulk)."""
    qs = list(dict.fromkeys(q for a in _actors(n, state.w) for q in n.neighbours(a, "eq_has_quantum")))
    if not qs:
        return []
    cols = [n.get_attr_many(qs, k) for k in ("q_actor", "q_trait", "q_pole", "q_target")]
    new = []
    for q, actor, trait, pole, target in zip(qs, *cols):
        k = f"eqq:{actor}|{trait}|{pole}|{'' if target is None else target}"
        if _led(n, state.ledger, k) is None:
            n.set_attr(state.ledger, k, True)
            new.append(q)
    return new


def _frontier(n, w) -> list:
    """0.8.0: the held frontier (every actor's still-revisable held / weak turn, and
    Amendment A: its still-revisable held / open topic turn)"""
    return [m for a in _actors(n, w) for e in ("eq_trk_held", "eq_top_held") for m in n.neighbours(a, e)]


def conversation_close(substrate, agent_root, state: Conversation) -> dict:
    """Final read-out: no turns, and no ticks, so the evidence deltas are empty
    (every change was emitted by the batch that made it). 0.8.0: the held frontier
    is frozen at close, so its turns are re-emitted once as final turns_delta
    entries (structure unchanged: freezing never changes a field). The caller
    drops the retained fork afterwards."""
    n = _native(substrate)
    return _emit(substrate, agent_root, state, [], Changes(), _frontier(n, state.w))


def conversation_full(substrate, agent_root, state: Conversation) -> dict:
    """Every quantum / episode of the conversation as full rows (/v1/discourse,
    and the reference a folded delta stream must equal)."""
    n = _native(substrate)
    return {"quanta": _read_quanta(n, state.w), "episodes": _read_episodes(n, state.w),
            "open_questions": _open_questions(n, state.w)}


def run_strata(substrate, agent_root, touched: Changes | None = None) -> list[int]:
    """Tick to fixpoint, then open each seeded EqStratum in its seeded order and
    tick again. Returns the step count of every tick. With `touched`, every tick
    is the engine's exact-edge-delta run, accumulated into `touched`."""
    n = _native(substrate)
    strata = sorted(n.neighbours(agent_root, "eq_has_stratum"),
                    key=lambda x: n.node(x)["attrs"]["eq_stratum"])
    steps = [_tick(n, touched)]
    for st in strata:
        n.add_edge(agent_root, n.node(st)["attrs"]["eq_open_edge"], st)
        steps.append(_tick(n, touched))
    if any(k >= DISCOURSE_FUEL for k in steps):
        raise BudgetExhausted("rule fuel exhausted")
    return steps


def _tick(n, touched: Changes | None) -> int:
    """One run_rules fixpoint; with `touched`, the engine's exact-edge-delta
    variant (same fixpoint) whose report is accumulated into `touched`."""
    if touched is None:
        return n.run_rules(DISCOURSE_FUEL)
    rep = n.run_rules_edge_delta(DISCOURSE_FUEL, DELTA_EDGE_TYPES, DELTA_NODE_TYPES)
    touched.add(rep)
    return rep["progress_steps"]


def _refs(n, nodes) -> list[str]:
    """turn refs in turn order (two bulk attr reads; positions are unique)"""
    nodes = list(nodes)
    if not nodes:
        return []
    pos, ref = n.get_attr_many(nodes, "eq_turn_pos"), n.get_attr_many(nodes, "eq_ref")
    return [r for _, r in sorted(zip(pos, ref))]


def _candidates(n, m, has="eq_has_cand", ref="eq_cand_ref", cue="eq_cue") -> list[dict]:
    """0.8.0: the turn's candidate parents (EqParentCand nodes) with their cue codes,
    in turn order of the candidate; cues sorted (a set on the wire). Amendment A: the
    same read-out over the topic candidates (EqTopicCand: eq_has_tcand / eq_tcand_ref /
    eq_tcue)."""
    rows = []
    for c in n.neighbours(m, has):
        x = n.neighbours(c, ref)[0]
        xa = n.node(x)["attrs"]
        rows.append((xa["eq_turn_pos"], {"ref": xa["eq_ref"], "cues": sorted(
            n.node(k)["attrs"]["code"] for k in n.neighbours(c, cue))}))
    return [r for _, r in sorted(rows, key=lambda r: r[0])]


def _structure(n, m) -> dict:
    """The turn's revisable structure fields (the turns_delta row). Mechanical: basis
    and confidence are the rules' own marks (`eq_basis`, `eq_trk_conf`)."""
    a = n.node(m)["attrs"]
    responds = _refs(n, n.neighbours(m, "eq_responds_to"))
    conf = a.get("eq_trk_conf")
    if responds:
        basis = a.get("eq_basis")
        conf = "declared" if basis == "declared" else conf
    else:
        basis = "held" if conf == "held" else "none"
        conf = "held" if conf == "held" else None
    return {"id": a["eq_ref"], "responds_to": responds, "basis": basis, "confidence": conf,
            "candidates": _candidates(n, m),
            "addressees": sorted({n.node(x)["attrs"]["actor_ref"]
                                  for x in n.neighbours(m, "eq_addresses")}),
            "thread_id": a.get("eq_thread"), "answers": _refs(n, n.neighbours(m, "eq_answers")),
            # Amendment A: the topic relation (the rules' decided `eq_top_to`, else null)
            "topic_id": next(iter(_refs(n, n.neighbours(m, "eq_top_to"))), None),
            "topic_candidates": _candidates(n, m, "eq_has_tcand", "eq_tcand_ref", "eq_tcue")}


def _read_turn(f, m, status) -> dict:
    row = _structure(_native(f), m)
    row["read"] = _read(f, m, status)
    return row


def _turns_delta(n, revised) -> list[dict]:
    """0.8.0: full structure rows of earlier turns this call revised (one per id, turn order)."""
    revised = list({m.value: m for m in revised}.values())
    pos = n.get_attr_many(revised, "eq_turn_pos") if revised else []
    return [_structure(n, m) for _, m in sorted(zip(pos, revised), key=lambda r: r[0])]


def _quantum_row(n, q, qa: dict) -> dict:
    """One quantum's full row (the 0.5.x wire row; /v1/discourse)."""
    # eq_context (0.4.0): the turn a relational quantum replies to (e.g. the
    # question of inquiry.answered) -- evidence on the wire, not counted by
    # the seeded match shapes
    ev = {x for et in EVIDENCE_EDGES for x in n.neighbours(q, et)}
    row = {"actor_ref": qa["q_actor"], "trait": qa["q_trait"], "polarity": qa["q_pole"],
           "match": qa.get("eq_match"), "evidence": _refs(n, ev),
           "counter_evidence": _refs(n, {x for et in COUNTER_EDGES for x in n.neighbours(q, et)}),
           "rule_ids": _rule_ids(qa, RULE_PREFIX)}
    if qa.get("q_target"):
        row["target_ref"] = qa["q_target"]
    return row


def _read_quanta(n, w, only: list | None = None) -> list[dict]:
    """Every quantum of the conversation, or only the quanta in `only`."""
    if only is None:
        only = list(dict.fromkeys(q for a in _actors(n, w) for et in QUANTUM_EDGES
                                  for q in n.neighbours(a, et)))
    quanta = [_quantum_row(n, q, n.node(q)["attrs"]) for q in only]
    quanta.sort(key=lambda r: (r["actor_ref"], r["trait"], r["polarity"], r.get("target_ref", "")))
    return quanta


def _facets(n, e) -> list[dict]:
    return sorted(({"code": n.node(f)["attrs"]["fx_code"], "match": n.node(f)["attrs"].get("eq_match")}
                   for f in n.neighbours(e, "eq_has_facet")), key=lambda r: r["code"])


def _episode_row(n, e, ea: dict) -> tuple[dict, int]:
    """One episode's full row and its first member's turn position."""
    turns = n.in_neighbours(e, "eq_in_episode")
    members = sorted((n.node(x)["attrs"] for x in turns), key=lambda r: r["eq_turn_pos"])
    actor_refs = sorted({n.node(a)["attrs"]["actor_ref"] for x in turns
                         for a in n.neighbours(x, "eq_authored_by")})
    return ({"episode_id": f"ep:{ea['ep_root_ref']}", "kind": ea["ep_kind"],
             "actor_refs": actor_refs, "turns": [r["eq_ref"] for r in members],
             "facets": _facets(n, e), "generative": ea.get("ep_generative"),
             "rule_ids": _rule_ids(ea, RULE_PREFIX)},
            members[0]["eq_turn_pos"] if members else -1)


def _read_episodes(n, w, only: list | None = None) -> list[dict]:
    """Every episode of the conversation, or only the episodes in `only`."""
    rows = [_episode_row(n, e, n.node(e)["attrs"])
            for e in (n.neighbours(w, "eq_has_episode") if only is None else only)]
    rows.sort(key=lambda r: (r[1], r[0]["episode_id"]))
    return [r for r, _ in rows]


def _open_questions(n, w) -> list[str]:
    """The open-question set is graph-resident: the tracking rules keep
    `w -eq_qud-> q` for every question turn not yet answered (opened when the
    question is tracked, closed by the tracked `eq_answers` edge, the only source
    of that edge), so the read-out is O(open questions), not a scan of the turns."""
    return _refs(n, n.neighbours(w, "eq_qud"))


# ---- evidence deltas (track T3e, pack 0.6.0) ----------------------------------
# A delta is relative to everything emitted earlier for the conversation. Every
# change is emitted by the call that made it, so "previously emitted" is the graph
# at the start of the call: an edge's previous state is the engine's first-seen
# state (Changes.net), a quantum's / episode's previous existence and scalar
# fields are its ledger mark (written when emitted, cleared on retract).

def _srs():
    import substrate_rs
    return substrate_rs


def _quantum_id(key: list) -> str:
    """Stable within the conversation: a digest of the permanent quantum node's
    identity key (the add_node_if_absent key the rules mint it under)."""
    blob = json.dumps(key, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "q:" + hashlib.sha256(blob).hexdigest()[:16]


def _was(n, net: dict, s, et: str, t) -> bool:
    """An edge's existence at the start of the call."""
    k = (s.value, et, t.value)
    return (not net[k]) if k in net else n.has_edge(s, et, t)


def _pairs(n, net: dict, q, ms, types) -> tuple[list, list]:
    """Turns added to / removed from q's union over `types` edges, among the
    turns `ms` one of whose `types` edges from q changed existence."""
    add, rem = [], []
    for m in ms:
        now = any(n.has_edge(q, et, m) for et in types)
        was = any(_was(n, net, q, et, m) for et in types)
        if now != was:
            (add if now else rem).append(m)
    return _refs(n, add), _refs(n, rem)


def _mark(n, ledger, key: str):
    raw = _led(n, ledger, key)
    return json.loads(raw) if raw else None


def _quanta_delta(n, state: Conversation, ch: Changes, net: dict) -> list[dict]:
    srs = _srs()
    actors = {a.value for a in _actors(n, state.w)}
    cand: dict[int, tuple[set, set]] = {}
    for (s, et, t) in net:
        if et in QUANTUM_EDGES:
            cand.setdefault(t, (set(), set()))
        elif et in EVIDENCE_EDGES:
            cand.setdefault(s, (set(), set()))[0].add(srs.NodeID(t))
        elif et in COUNTER_EDGES:
            cand.setdefault(s, (set(), set()))[1].add(srs.NodeID(t))
    for qi in ch.nodes.get("EqQuantum", ()):
        cand.setdefault(qi, (set(), set()))
    out = []
    for qi, (ev, co) in cand.items():
        q, mk = srs.NodeID(qi), f"{EMIT_PREFIX}q:{qi}"
        mark = _mark(n, state.ledger, mk)
        node = n.node(q) if n.has_node(q) else None
        exists = (node is not None and node["type"] == "EqQuantum"
                  and any(a.value in actors for et in QUANTUM_EDGES for a in n.in_neighbours(q, et)))
        if not exists:
            if mark is not None:  # it no longer holds
                out.append((mark["k"], {"quantum_id": mark["id"], "op": "retract"}))
                n.set_attr(state.ledger, mk, None)
            continue
        qa = node["attrs"]
        key = [qa["q_actor"], qa["q_trait"], qa["q_pole"], qa.get("q_target") or ""]
        fields = {"match": qa.get("eq_match"), "rule_ids": _rule_ids(qa, RULE_PREFIX)}
        if mark is None:  # first appearance (or re-appearance): full lists
            row = _quantum_row(n, q, qa)
            d = {"quantum_id": _quantum_id(key), "op": "upsert", "actor_ref": row["actor_ref"],
                 "trait": row["trait"], "polarity": row["polarity"], "match": row["match"],
                 "target_ref": row.get("target_ref"),
                 "evidence_add": row["evidence"], "evidence_remove": [],
                 "counter_add": row["counter_evidence"], "counter_remove": [],
                 "rule_ids": row["rule_ids"]}
        else:
            ea, er = _pairs(n, net, q, ev, EVIDENCE_EDGES)
            ca, cr = _pairs(n, net, q, co, COUNTER_EDGES)
            d = {"quantum_id": mark["id"], "op": "upsert"}
            if fields["match"] != mark["match"]:
                d["match"] = fields["match"]
            d.update(evidence_add=ea, evidence_remove=er, counter_add=ca, counter_remove=cr)
            if fields["rule_ids"] != mark["rule_ids"]:
                d["rule_ids"] = fields["rule_ids"]
            if len(d) == 6 and not (ea or er or ca or cr):
                continue  # touched, unchanged
        if mark is None or any(fields[f] != mark[f] for f in fields):
            n.set_attr(state.ledger, mk, json.dumps({"id": d["quantum_id"], "k": key, **fields},
                                                    separators=(",", ":"), ensure_ascii=False))
        out.append((key, d))
    out.sort(key=lambda r: r[0])
    return [d for _, d in out]


def _episodes_delta(n, state: Conversation, ch: Changes, net: dict) -> list[dict]:
    srs = _srs()
    w = state.w
    cand: dict[int, list] = {}
    for (s, et, t) in net:
        if et == "eq_has_episode" and s == w.value:
            cand.setdefault(t, [])
        elif et == "eq_in_episode":
            cand.setdefault(t, []).append(s)
        elif et == "eq_has_facet":
            cand.setdefault(s, [])
    for ei in ch.nodes.get("EqEpisode", ()):
        cand.setdefault(ei, [])
    for fi in ch.nodes.get("EqEpFacet", ()):
        f = srs.NodeID(fi)
        if n.has_node(f):
            for e in n.in_neighbours(f, "eq_has_facet"):
                cand.setdefault(e.value, [])
    out = []
    for ei, ms in cand.items():
        e, mk = srs.NodeID(ei), f"{EMIT_PREFIX}e:{ei}"
        mark = _mark(n, state.ledger, mk)
        if not (n.has_node(e) and n.has_edge(w, "eq_has_episode", e)):
            if mark is not None:
                out.append((mark["s"], {"episode_id": mark["id"], "op": "retract"}))
                n.set_attr(state.ledger, mk, None)
            continue
        ea = n.node(e)["attrs"]
        fields = {"kind": ea["ep_kind"], "facets": _facets(n, e),
                  "generative": ea.get("ep_generative"), "rule_ids": _rule_ids(ea, RULE_PREFIX)}
        if mark is None:  # first appearance: full lists
            row, first = _episode_row(n, e, ea)
            counts: dict[str, int] = {}
            for x in n.in_neighbours(e, "eq_in_episode"):
                for a in n.neighbours(x, "eq_authored_by"):
                    r = n.node(a)["attrs"]["actor_ref"]
                    counts[r] = counts.get(r, 0) + 1
            sort = [first, row["episode_id"]]
            d = {"episode_id": row["episode_id"], "op": "upsert", "kind": row["kind"],
                 "actor_refs": row["actor_refs"], "turns_add": row["turns"], "turns_remove": [],
                 "facets": row["facets"], "generative": row["generative"], "rule_ids": row["rule_ids"]}
        else:
            add = [srs.NodeID(m) for m in ms if net[(m, "eq_in_episode", ei)]]
            rem = [srs.NodeID(m) for m in ms if not net[(m, "eq_in_episode", ei)]]
            counts = dict(mark["n"])
            for m, step in [(m, 1) for m in add] + [(m, -1) for m in rem]:
                for a in n.neighbours(m, "eq_authored_by"):
                    r = n.node(a)["attrs"]["actor_ref"]
                    counts[r] = counts.get(r, 0) + step
                    if counts[r] == 0:
                        del counts[r]
            sort = mark["s"]
            d = {"episode_id": mark["id"], "op": "upsert"}
            if fields["kind"] != mark["kind"]:
                d["kind"] = fields["kind"]
            if sorted(counts) != sorted(mark["n"]):
                d["actor_refs"] = sorted(counts)
            d["turns_add"], d["turns_remove"] = _refs(n, add), _refs(n, rem)
            for f in ("facets", "generative", "rule_ids"):
                if fields[f] != mark[f]:
                    d[f] = fields[f]
            if len(d) == 4 and not (add or rem):
                continue  # touched, unchanged
        n.set_attr(state.ledger, mk, json.dumps({"id": d["episode_id"], "s": sort, "n": counts, **fields},
                                                separators=(",", ":"), ensure_ascii=False))
        out.append((sort, d))
    out.sort(key=lambda r: r[0])
    return [d for _, d in out]


def _emit(substrate, agent_root, state: Conversation, nodes: list, changes: Changes,
          revised: list = ()) -> dict:
    """Read-out of the retained fork: the batch's turns, the earlier turns this call
    revised (`turns_delta`, 0.8.0), the quanta / episodes deltas of what this call's
    ticks changed (`changes`), the open questions."""
    n = _native(substrate)
    w = state.w
    status = _label_status(substrate, agent_root)
    turns = [_read_turn(substrate, m, status) for m in nodes]
    net = changes.net()
    return {"conversation_id": n.node(w)["attrs"]["conversation_id"],
            "seq": _led(n, state.ledger, "eq_seq"), "turns": turns,
            "turns_delta": _turns_delta(n, revised),
            "quanta_delta": _quanta_delta(n, state, changes, net),
            "episodes_delta": _episodes_delta(n, state, changes, net),
            "open_questions": _open_questions(n, w), "steps": []}


def discourse(substrate, agent_root, window: dict, turns: Iterable[dict]) -> dict:
    """/v1/discourse = open + one ingest + full read-out on `substrate` (pass a fork).
    Returns {"window_id", "messages", "quanta", "episodes", "steps"} (full rows)."""
    turns = list(turns)
    st = conversation_open(substrate, agent_root, window["window_id"], window["kind"])
    got = conversation_ingest(substrate, agent_root, st, turns)
    fin = conversation_full(substrate, agent_root, st)
    return {"window_id": str(window["window_id"]), "messages": [t["read"] for t in got["turns"]],
            "turns": got["turns"], "quanta": fin["quanta"], "episodes": fin["episodes"],
            "open_questions": fin["open_questions"], "steps": got["steps"]}
