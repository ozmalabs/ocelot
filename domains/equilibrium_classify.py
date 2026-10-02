"""Equilibrium classifier sidecar v0 — the THIN world adapter (track T3).

CLAUDE.md "the agent is a graph in Rust": this module does only
  * INGEST  — each message becomes Message/Token/CodeSpan/LinkSpan nodes + edges
              (I/O-boundary tokenisers: code fences/backticks, URLs, lowercase
              word tokens + a digit-token shape class `eq_class`; plus the
              speech-act SIGNALS the existing parse layer
              already computes via comprehend_text.kind_signals);
  * TICK    — run_rules: the seeded rules (seeds/speech_act_classify.json +
              seeds/equilibrium_*.json) decide every label;
  * EMIT    — a mechanical read of the `eqfire:<rule name>` attrs those rules
              wrote, joined to the seeded LabelStatus nodes.
No label is decided here. OZMA_NO_LLM=1 is expected; nothing here reaches an LLM.

Usage (caller owns isolation — classify a FORK, never the frozen base):
    s, root = boot()
    snap = s.snapshot(); branch = snap.fork()
    labels = classify(branch, root, [{"id": "m1", "text": "how?"}])
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

PACK_VERSION = "0.2.0"
TAXONOMY_VERSION = "eq-tax-0.2.0"
PACK_IDS = ("equilibrium_tokens", "equilibrium_lexicon", "equilibrium_msg",
            "equilibrium_pattern", "equilibrium_label_status")
FIRE_PREFIX = "eqfire:"
RULE_STEP_BUDGET = 10_000

# I/O-boundary tokenisers (emit tokens, never labels).
_FENCE = re.compile(r"```.*?(?:```|$)", re.S)
_INLINE = re.compile(r"`[^`\n]+`")
_URL = re.compile(r"\b(https?)://\S+", re.I)
_WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
# Token shape class (I/O-boundary lexing, not a label): seeded cue slots such as
# "<num>" match it; "<" can never occur in a `form`, so classes and forms never collide.
NUM_CLASS = "<num>"


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
    """Fresh substrate with the pack and its whole dependency closure."""
    return boot_core(PACK_IDS)


def _spans(text: str) -> tuple[list[tuple[str, dict]], str]:
    """Code/link spans as (node type, attrs) + the residual prose for word tokens."""
    spans: list[tuple[str, dict]] = []
    for rx, form in ((_FENCE, "fence"), (_INLINE, "inline")):
        spans += [("CodeSpan", {"eq_span": "code", "form": form}) for _ in rx.findall(text)]
        text = rx.sub(" ", text)
    spans += [("LinkSpan", {"eq_span": "link", "scheme": sch.lower()}) for sch in _URL.findall(text)]
    return spans, _URL.sub(" ", text)


def _ingest(s, root, msg: dict) -> Any:
    from domains.comprehend_text import kind_signals
    n = _native(s)
    text = str(msg.get("text") or "")
    sig = kind_signals(s, text)
    attrs = {"eq_ref": str(msg["id"]), "sak_pending": 1.0,
             "sak_ends_q": 1.0 if sig["ends_q"] else 0.0}
    attrs.update({f"sak_{k}": sig[k] for k in ("first_role", "first_pos") if sig.get(k)})
    m = n.add_node("Message", attrs)
    n.add_edge(root, "received", m)
    spans, prose = _spans(text)
    for typ, sattrs in spans:
        n.add_edge(m, "eq_has_span", n.add_node(typ, sattrs))
    prev = None
    for i, w in enumerate(_WORD.findall(prose.replace("\u2019", "'").lower())):
        tattrs = {"form": w, "eq_pos": i}
        if w.isdigit():
            tattrs["eq_class"] = NUM_CLASS
        t = n.add_node("Token", tattrs)
        n.add_edge(m, "eq_has_token", t)
        if prev is not None:
            n.add_edge(prev, "eq_next", t)
        prev = t
    return m


def _label_status(s, root) -> dict[str, dict]:
    n = _native(s)
    rows = [n.node(x)["attrs"] for x in n.neighbours(root, "eq_has_label_status")]
    return {r["label"]: r for r in rows}


def _read(s, m, status: dict[str, dict]) -> dict:
    """Mechanical read-out: every `eqfire:<rule>` attr -> (label, value, rule_id).
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
        out["rule_ids"].append(rid)
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
