"""Equilibrium classifier sidecar — the THIN world adapter (tracks T3 / T3b).

CLAUDE.md "the agent is a graph in Rust": this module does only
  * INGEST  — each message becomes Message/Token/CodeSpan/LinkSpan nodes + edges
              (I/O-boundary tokenisers: code fences/backticks, URLs, lowercase
              word tokens; clause index from sentence punctuation; per-token
              boundary attrs `lemma` (WordNet morphy) and `eq_class` (digit
              token -> "<num>", else first-sense WordNet noun lexname, e.g.
              "<noun.person>"); plus the speech-act SIGNALS the existing parse
              layer already computes via comprehend_text.kind_signals).
              `discourse` additionally ingests the WINDOW mechanically:
              EqWindow / EqActor nodes, authorship, reply, adjacency edges and an
              integer turn position (array order).
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
"""
from __future__ import annotations

import functools
import hashlib
import json
import re
from typing import Any, Iterable

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

PACK_VERSION = "0.3.0"
TAXONOMY_VERSION = "eq-tax-0.3.0"
PACK_IDS = ("equilibrium_tokens", "equilibrium_window", "equilibrium_lexicon",
            "equilibrium_scope", "equilibrium_msg", "equilibrium_pattern",
            "equilibrium_traits", "equilibrium_quanta", "equilibrium_competence",
            "equilibrium_episode", "equilibrium_label_status")
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


@functools.lru_cache(maxsize=65_536)
def lemma(form: str) -> str:
    """Opaque string normalisation: WordNet morphy (verb reading, then noun),
    else the form itself. Shared with the seed builder so cue words and tokens
    are normalised by the same function."""
    wn = _wordnet()
    return wn.morphy(form, "v") or wn.morphy(form, "n") or form


@functools.lru_cache(maxsize=65_536)
def noun_class(form: str) -> str | None:
    """First-sense WordNet noun lexname of the token's lemma as a class token
    ("<noun.person>"); first sense is a lookup, not a disambiguation decision."""
    syn = _wordnet().synsets(lemma(form), "n")
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


# ---- discourse windows -------------------------------------------------------
def ingest_window(substrate, agent_root, window: dict, turns: list[dict]) -> tuple[Any, list]:
    """Mechanical window ingest (design §4). Turns are taken in array order;
    `reply_to` naming an id outside the window is kept as an attr only."""
    n = _native(substrate)
    w = n.add_node("EqWindow", {"window_id": str(window["window_id"]),
                                "eq_kind": str(window["kind"])})
    n.add_edge(agent_root, "eq_window", w)
    actors: dict[str, Any] = {}  # mechanical id map (string key -> node)
    by_id: dict[str, Any] = {}
    nodes = []
    for i, t in enumerate(turns):
        extra = {"eq_turn_pos": i}
        if t.get("ts_ms") is not None:
            extra["eq_ts_ms"] = int(t["ts_ms"])
        if t.get("reply_to") is not None:
            extra["eq_reply_to_ref"] = str(t["reply_to"])
        m = _ingest(substrate, agent_root, t, extra)
        ref = str(t["actor_ref"])
        if ref not in actors:
            actors[ref] = n.add_node("EqActor", {"actor_ref": ref})
            n.add_edge(w, "eq_has_actor", actors[ref])
        n.add_edge(w, "eq_has_turn", m)
        n.add_edge(m, "eq_authored_by", actors[ref])
        if nodes:
            n.add_edge(nodes[-1], "eq_turn_next", m)
        by_id[str(t["id"])] = m
        nodes.append(m)
    for t, m in zip(turns, nodes):
        tgt = by_id.get(str(t.get("reply_to"))) if t.get("reply_to") is not None else None
        if tgt is not None:
            n.add_edge(m, "eq_reply_to", tgt)
    return w, nodes


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


def read_discourse(substrate, agent_root, w, nodes) -> dict:
    """Pure query over what the rules wrote (design §7)."""
    n = _native(substrate)
    status = _label_status(substrate, agent_root)
    messages = [_read(substrate, m, status) for m in nodes]
    quanta = []
    for a in n.neighbours(w, "eq_has_actor"):
        for q in n.neighbours(a, "eq_has_quantum"):
            qa = n.node(q)["attrs"]
            ev = set(n.neighbours(q, "eq_evidence")) | set(n.neighbours(q, "eq_hedged"))
            row = {"actor_ref": qa["q_actor"], "trait": qa["q_trait"], "polarity": qa["q_pole"],
                   "match": qa.get("eq_match"), "evidence": _refs(n, ev),
                   "counter_evidence": _refs(n, n.neighbours(q, "eq_counter")),
                   "rule_ids": _rule_ids(qa, RULE_PREFIX)}
            if qa.get("q_target"):
                row["target_ref"] = qa["q_target"]
            quanta.append(row)
    quanta.sort(key=lambda r: (r["actor_ref"], r["trait"], r["polarity"], r.get("target_ref", "")))
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
    return {"window_id": n.node(w)["attrs"]["window_id"], "messages": messages,
            "quanta": quanta, "episodes": episodes}


def discourse(substrate, agent_root, window: dict, turns: Iterable[dict]) -> dict:
    """Ingest the window -> stratified run_rules -> read. Mutates `substrate`
    (pass a fork). Returns {"window_id", "messages", "quanta", "episodes", "steps"}."""
    turns = list(turns)
    w, nodes = ingest_window(substrate, agent_root, window, turns)
    steps = run_strata(substrate, agent_root)
    out = read_discourse(substrate, agent_root, w, nodes)
    out["steps"] = steps
    return out
