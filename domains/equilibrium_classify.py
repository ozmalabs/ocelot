"""Equilibrium classifier sidecar — the THIN world adapter (tracks T3 / T3b / T3c, pack 0.5.0).

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
    conversation_ingest(conv, root, st, turns)   # per batch (caller ran conversation_check)
    conversation_close(conv, root, st)           # complete final quanta / episodes
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

PACK_VERSION = "0.5.1"
TAXONOMY_VERSION = "eq-tax-0.5.1"
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
#     Only the non-monotone rules remain on the scratch fork (see
#     scripts/_equilibrium_quanta_rules.py LIVE_L1 / LIVE_L2).
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
# only bindings driven by the batch's new edges. These are evaluation-strategy
# flags; the fixpoint they reach is the same (golden-checked, RESULTS T3d).
CONVERSATION_KINDS = ("meeting", "thread", "channel")
QUESTION_KEY = "eqlab:msg.speech_act=question"
EMIT_PREFIX = "eqemit:"


class Conversation:
    """Adapter handle for one retained conversation fork: the EqWindow node id
    and its (edge-less) EqLedger bookkeeping node id."""
    __slots__ = ("w", "ledger")

    def __init__(self, w, ledger) -> None:
        self.w, self.ledger = w, ledger


def incremental_engine(n) -> None:
    """Turn on semi-naive evaluation for every rule of this substrate (and of
    forks taken from it): an engine evaluation strategy, not a decision."""
    n.set_incremental_match(True)
    n.set_precise_dirty(True)
    n.set_fresh_node_exempt(True)
    n.set_batch_incremental(True)
    n.set_empty_match_proof(True)  # a closed live layer (no frontier mark) matches nothing


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
    return {"conversation_id": a["conversation_id"], "seq": n.node(state.ledger)["attrs"]["eq_seq"],
            "kind": a["eq_kind"]}


def conversation_check(substrate, state: Conversation, turns: list[dict]) -> str | None:
    """Ordering preconditions of a batch (no mutation): 'duplicate_turn' if an id
    repeats in the batch or already exists in the conversation, 'out_of_order'
    if a ts_ms is earlier than the latest ts_ms seen (ties keep array order)."""
    n = _native(substrate)
    last = n.node(state.ledger)["attrs"].get("eq_last_ts")
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


def conversation_ingest(substrate, agent_root, state: Conversation, turns: list[dict]) -> dict:
    """Append one batch to the retained conversation fork and read it out.
    The caller has run conversation_check. Returns
      {"conversation_id", "seq", "turns": [...], "quanta": [new/changed],
       "episodes": [new/changed], "open_questions": [...], "steps": [...]}"""
    n = _native(substrate)
    w = state.w
    book = n.node(state.ledger)["attrs"]
    pos, last_ref, last_ts = book["eq_next_pos"], book.get("eq_last_ref"), None
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
    s0 = n.run_rules(DISCOURSE_FUEL)  # S0 on the retained fork
    if s0 >= DISCOURSE_FUEL:
        raise BudgetExhausted("rule fuel exhausted")
    # S0 is at fixpoint for the new turns: queue them for the seeded turn cursor
    # (equilibrium_tracking) and tick again on the retained fork
    for m in nodes:
        n.add_edge(w, "eq_trk_pending", m)
    trk = n.run_rules(DISCOURSE_FUEL)
    if trk >= DISCOURSE_FUEL:
        raise BudgetExhausted("rule fuel exhausted")
    # the batch's turns are final for the per-turn window / tracking rules:
    # retire them from that frontier, so later batches never re-match them
    for m in nodes:
        n.remove_edge(w, "eq_l0", m)
    # the tracked turns enter the LIVE (monotone) strata layers in order -- L1
    # per-turn rules, then L2 (rules whose absence test reads an L1 fact) -- as
    # the layer's frontier marks, which are removed once its fixpoint is reached
    live = []
    for layer in ("eq_l1", "eq_l2"):
        for m in nodes:
            n.add_edge(w, layer, m)
        if layer == "eq_l1":
            n.add_edge(agent_root, "eq_l1_open", w)
        if layer == "eq_l2":
            qnew = _new_quanta(n, state)
            for q in qnew:
                n.add_edge(w, "eq_qnew", q)
            n.add_edge(agent_root, "eq_l2_open", w)
        live.append(n.run_rules(DISCOURSE_FUEL))
        if live[-1] >= DISCOURSE_FUEL:
            raise BudgetExhausted("rule fuel exhausted")
        for m in nodes:
            n.remove_edge(w, layer, m)
        if layer == "eq_l1":
            n.remove_edge(agent_root, "eq_l1_open", w)
        if layer == "eq_l2":
            n.remove_edge(agent_root, "eq_l2_open", w)
            for q in qnew:
                n.remove_edge(w, "eq_qnew", q)
    seq = book["eq_seq"] + 1
    n.set_attr(state.ledger, "eq_seq", seq)
    out = _emit(substrate, agent_root, state, nodes, full=False)
    out["steps"] = [s0, trk] + live + out["steps"]
    return out


def _new_quanta(n, state: Conversation) -> list:
    """Quanta first minted on the retained fork in this batch (mechanical set
    difference against the ledger's `eqq:` marks; bounded by actors x quanta,
    not by conversation length)."""
    seen = n.node(state.ledger)["attrs"]
    new = []
    for a in n.neighbours(state.w, "eq_has_actor"):
        for q in n.neighbours(a, "eq_has_quantum"):
            qa = n.node(q)["attrs"]
            k = f"eqq:{qa['q_actor']}|{qa['q_trait']}|{qa['q_pole']}|{qa.get('q_target', '')}"
            if k not in seen:
                n.set_attr(state.ledger, k, True)
                new.append(q)
    return new


def conversation_close(substrate, agent_root, state: Conversation) -> dict:
    """Final read-out: every quantum / episode of the conversation, no turns.
    The caller drops the retained fork afterwards."""
    return _emit(substrate, agent_root, state, [], full=True)


def run_strata(substrate, agent_root) -> list[int]:
    """Tick to fixpoint, then open each seeded EqStratum in its seeded order and
    tick again. Returns the step count of every tick."""
    n = _native(substrate)
    strata = sorted(n.neighbours(agent_root, "eq_has_stratum"),
                    key=lambda x: n.node(x)["attrs"]["eq_stratum"])
    steps = [n.run_rules(DISCOURSE_FUEL)]
    for st in strata:
        n.add_edge(agent_root, n.node(st)["attrs"]["eq_open_edge"], st)
        steps.append(n.run_rules(DISCOURSE_FUEL))
    if any(k >= DISCOURSE_FUEL for k in steps):
        raise BudgetExhausted("rule fuel exhausted")
    return steps


def _refs(n, nodes) -> list[str]:
    rows = [n.node(x)["attrs"] for x in nodes]
    return [r["eq_ref"] for r in sorted(rows, key=lambda r: r["eq_turn_pos"])]


def _read_turn(f, m, status) -> dict:
    n = _native(f)
    a = n.node(m)["attrs"]
    responds = _refs(n, n.neighbours(m, "eq_responds_to"))
    return {"id": a["eq_ref"], "read": _read(f, m, status), "responds_to": responds,
            "basis": a.get("eq_basis") if responds else "none",
            "addressees": sorted({n.node(x)["attrs"]["actor_ref"]
                                  for x in n.neighbours(m, "eq_addresses")}),
            "thread_id": a.get("eq_thread"), "topic_id": a.get("eq_topic"),
            "answers": _refs(n, n.neighbours(m, "eq_answers"))}


def _read_quanta(n, w) -> list[dict]:
    quanta = []
    for a in n.neighbours(w, "eq_has_actor"):
        for q in n.neighbours(a, "eq_has_quantum"):
            qa = n.node(q)["attrs"]
            # eq_context (0.4.0): the turn a relational quantum replies to (e.g. the
            # question of inquiry.answered) -- evidence on the wire, not counted by
            # the seeded match shapes
            ev = (set(n.neighbours(q, "eq_evidence")) | set(n.neighbours(q, "eq_hedged"))
                  | set(n.neighbours(q, "eq_context")))
            row = {"actor_ref": qa["q_actor"], "trait": qa["q_trait"], "polarity": qa["q_pole"],
                   "match": qa.get("eq_match"), "evidence": _refs(n, ev),
                   "counter_evidence": _refs(n, n.neighbours(q, "eq_counter")),
                   "rule_ids": _rule_ids(qa, RULE_PREFIX)}
            if qa.get("q_target"):
                row["target_ref"] = qa["q_target"]
            quanta.append(row)
    quanta.sort(key=lambda r: (r["actor_ref"], r["trait"], r["polarity"], r.get("target_ref", "")))
    return quanta


def _read_episodes(n, w) -> list[dict]:
    episodes = []
    for e in n.neighbours(w, "eq_has_episode"):
        ea = n.node(e)["attrs"]
        turns = n.in_neighbours(e, "eq_in_episode")
        members = sorted((n.node(x)["attrs"] for x in turns), key=lambda r: r["eq_turn_pos"])
        actor_refs = sorted({n.node(a)["attrs"]["actor_ref"] for x in turns
                             for a in n.neighbours(x, "eq_authored_by")})
        facets = sorted(({"code": n.node(f)["attrs"]["fx_code"],
                          "match": n.node(f)["attrs"].get("eq_match")}
                         for f in n.neighbours(e, "eq_has_facet")), key=lambda r: r["code"])
        episodes.append({"episode_id": f"ep:{ea['ep_root_ref']}", "kind": ea["ep_kind"],
                         "actor_refs": actor_refs, "turns": [r["eq_ref"] for r in members],
                         "facets": facets, "generative": ea.get("ep_generative"),
                         "rule_ids": _rule_ids(ea, RULE_PREFIX),
                         "_first_pos": members[0]["eq_turn_pos"] if members else -1})
    episodes.sort(key=lambda r: (r.pop("_first_pos"), r["episode_id"]))
    return episodes


def _open_questions(n, w) -> list[str]:
    qs = [x for x in n.neighbours(w, "eq_has_turn")
          if n.node(x)["attrs"].get(QUESTION_KEY) is True and not n.in_neighbours(x, "eq_answers")]
    return _refs(n, qs)


def _sig(row: dict) -> str:
    blob = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def _delta(n, ledger, kind: str, rows: list[dict], key, seq: int, full: bool) -> list[dict]:
    """Mechanical emitted-mark comparison: a row is emitted when its signature
    differs from the `eqemit:` mark on the conversation's ledger (or when `full`)."""
    out = []
    marks = n.node(ledger)["attrs"]
    for r in rows:
        k = f"{EMIT_PREFIX}{kind}:{json.dumps(key(r), separators=(',', ':'))}"
        sig = _sig(r)
        prev = marks.get(k)
        if full or prev is None or prev.split(":", 1)[1] != sig:
            out.append(r)
        if prev is None or prev.split(":", 1)[1] != sig:
            n.set_attr(ledger, k, f"{seq}:{sig}")
    return out


def _emit(substrate, agent_root, state: Conversation, nodes: list, full: bool) -> dict:
    n = _native(substrate)
    w = state.w
    snap = substrate.snapshot()
    scratch = snap.fork()  # strata run here; dropped below
    del snap
    # the scratch strata re-derive over the whole prefix with the committed
    # full batch pass (their rules read absence; nothing is carried over)
    _native(scratch).set_batch_incremental(False)
    try:
        steps = run_strata(scratch, agent_root)[1:]
        f = _native(scratch)
        status = _label_status(scratch, agent_root)
        turns = [_read_turn(scratch, m, status) for m in nodes]
        quanta, episodes = _read_quanta(f, w), _read_episodes(f, w)
        open_q = _open_questions(f, w)
    finally:
        del scratch
    seq = n.node(state.ledger)["attrs"]["eq_seq"]
    qkey = lambda r: [r["actor_ref"], r["trait"], r["polarity"], r.get("target_ref", "")]  # noqa: E731
    return {"conversation_id": n.node(w)["attrs"]["conversation_id"], "seq": seq,
            "turns": turns,
            "quanta": _delta(n, state.ledger, "q", quanta, qkey, seq, full),
            "episodes": _delta(n, state.ledger, "e", episodes, lambda r: [r["episode_id"]], seq, full),
            "open_questions": open_q, "steps": steps}


def discourse(substrate, agent_root, window: dict, turns: Iterable[dict]) -> dict:
    """/v1/discourse = open + one ingest + close on `substrate` (pass a fork).
    Returns {"window_id", "messages", "quanta", "episodes", "steps"}."""
    turns = list(turns)
    st = conversation_open(substrate, agent_root, window["window_id"], window["kind"])
    got = conversation_ingest(substrate, agent_root, st, turns)
    fin = conversation_close(substrate, agent_root, st)
    return {"window_id": str(window["window_id"]), "messages": [t["read"] for t in got["turns"]],
            "turns": got["turns"], "quanta": fin["quanta"], "episodes": fin["episodes"],
            "open_questions": fin["open_questions"], "steps": got["steps"]}
