"""Block 327000 — extract an LLM's KNOWLEDGE as a native CAN graph seed.

The arc so far (318-326) asked whether the LLM's MECHANISM can be re-expressed on
the CAN substrate (aperture-covariance of modes/transports). This module opens a
different, better-motivated direction: extract the LLM's CONTENT — what it knows
— as native CAN graph seeds the substrate can use for its OWN cognition. Tier 1
(this block) is KNOWLEDGE: relational facts.

The pipeline:
  ELICIT   — prompt the LLM for relational triples (is-a, capital-of, ...).
  SEED     — build a native CAN Microtheory (Concept nodes + typed edges, the
             same grammar as `seeds/can_native_reimplementation.json`).
  QUERY    — answer held-out queries by SUBSTRATE OPERATIONS ONLY (edge
             traversal / BP), NO LLM at query time.

The anti-faking bar: the seed must answer ENTAILMENT it was NOT directly told —
transitive closure (a is-a b, b is-a c ⇒ a is-a c) and composition — not just
echo stored edges (that would be a lookup table in a graph costume). Controls:
a direct-edge-only baseline (cannot do transitive ⇒ shows traversal adds real
inference) and a shuffled-graph control (entailment collapses ⇒ the real
structure, not the node set, carries it).

Protected CAN internals (`can_native_bp.py`, `model_reader.py`, `can_ops.rs`,
the seed grammar) are READ-ONLY here — built TO, never modified. torch/model
appear ONLY at ELICIT time (offline); query time is pure substrate.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# ELICIT (model side, /applications venv). Structured next-token elicitation
# of relational triples over a fixed template.
# ---------------------------------------------------------------------------

def elicit_isa(model, tokenizer, subjects, *, candidates=None, template=None):
    """Elicit `(subject, is-a, object)` for each subject by asking the LLM to
    complete a hypernym template and reading the top next token(s). Returns a
    list of (subject, object) pairs the LLM asserted. The LLM is the elicitation
    ORACLE only; it does not appear at query time.

    `candidates`: optional list of allowed object words (restrict the next-token
    argmax to these token ids) — makes the elicitation a clean choice, not free
    generation. `template`: format string with one {} for the subject."""
    template = template or "A {} is a kind of"
    pairs = []
    cand_ids = None
    if candidates is not None:
        cand_ids = {}
        for w in candidates:
            ids = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
            if ids:
                cand_ids[ids[0]] = w
    for s in subjects:
        prompt = template.format(s)
        ids = tokenizer(prompt, return_tensors="pt")["input_ids"][0].tolist()
        logits = model.forward_logits(ids)
        if cand_ids is not None:
            best = max(cand_ids, key=lambda tid: float(logits[tid]))
            obj = cand_ids[best]
        else:
            tid = int(np.argmax(logits))
            obj = tokenizer.decode([tid]).strip()
        pairs.append((s, obj))
    return pairs


def elicit_isa_batch(model, tokenizer, subjects, *, candidates=None,
                     template=None, batch_size=32):
    """Batched `elicit_isa` (block 335000): identical read (constrained
    last-token argmax over `candidates`), but amortizes the forward over
    `batch_size` subjects via `model.forward_logits_batch`. Falls back to
    per-subject `forward_logits` if the model has no batch method. Returns the
    same list of (subject, object) pairs, in subject order."""
    template = template or "A {} is a kind of"
    cand_ids = None
    if candidates is not None:
        cand_ids = {}
        for w in candidates:
            ids = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
            if ids:
                cand_ids[ids[0]] = w
    subjects = list(subjects)
    has_batch = hasattr(model, "forward_logits_batch")
    pairs = []

    def _read(logits_row, s):
        if cand_ids is not None:
            best = max(cand_ids, key=lambda tid: float(logits_row[tid]))
            return (s, cand_ids[best])
        tid = int(np.argmax(logits_row))
        return (s, tokenizer.decode([tid]).strip())

    for i in range(0, len(subjects), batch_size):
        chunk = subjects[i:i + batch_size]
        seqs = [tokenizer(template.format(s), return_tensors="pt")["input_ids"][0].tolist()
                for s in chunk]
        if has_batch:
            logits = model.forward_logits_batch(seqs)
            for row, s in zip(logits, chunk):
                pairs.append(_read(row, s))
        else:
            for seq, s in zip(seqs, chunk):
                pairs.append(_read(model.forward_logits(seq), s))
    return pairs


# ---------------------------------------------------------------------------
# SEED (substrate side, tree python3). Build a native CAN Microtheory from
# triples: a Concept node per entity, a typed edge per relation.
# ---------------------------------------------------------------------------

def build_knowledge_mt(substrate, seed_paths, triples, *, relation="isa"):
    """Build a native CAN Microtheory seed from `(subject, object)` triples of a
    single `relation`. One Concept node per distinct entity (deduped by name),
    one directed `causal_influence` edge subject->object carrying the relation
    as an edge attr. Returns (mt, name_to_node). Query time uses only the
    substrate; the LLM is not consulted here."""
    import json
    from substrate.seed_loader import engine_rules_only
    for path in seed_paths:
        substrate.load_seed_manifest(engine_rules_only(json.load(open(path))))
    mt = substrate.add_node("Microtheory",
                            {"name": "knowledge_%s" % relation,
                             "temperature": 1.0, "discrete_mode": "3state"})
    name_to_node = {}

    def node_for(name):
        if name not in name_to_node:
            c = substrate.add_node("Concept", {"name": str(name),
                                               "state": 0.0,
                                               "external_field": 0.0,
                                               "identity_field": 0.0})
            substrate.add_edge(mt, "has_concept", c, {})
            name_to_node[name] = c
        return name_to_node[name]

    for s, o in triples:
        cs, co = node_for(s), node_for(o)
        substrate.add_edge(cs, "causal_influence", co,
                           {"weight": 1.0, "relation": relation})
    return mt, name_to_node


# ---------------------------------------------------------------------------
# QUERY (substrate only). Direct-edge lookup vs transitive traversal.
# ---------------------------------------------------------------------------

def _out_neighbours(substrate, node):
    out = []
    for k in substrate.neighbours(node, "causal_influence"):
        out.append(k)
    return out


def query_direct(substrate, name_to_node, subj, obj):
    """Is there a DIRECT stored edge subj -> obj? (lookup only.)"""
    if subj not in name_to_node or obj not in name_to_node:
        return False
    target = name_to_node[obj]
    tid = target.value if hasattr(target, "value") else int(target)
    for k in _out_neighbours(substrate, name_to_node[subj]):
        if (k.value if hasattr(k, "value") else int(k)) == tid:
            return True
    return False


def query_transitive(substrate, name_to_node, subj, obj, *, max_hops=6):
    """Is `obj` reachable from `subj` by following relation edges (transitive
    closure)? This is SUBSTRATE traversal — the entailment the seed derives but
    was not directly told. Returns (reachable, hops)."""
    if subj not in name_to_node or obj not in name_to_node:
        return False, 0
    start = name_to_node[subj]
    target = name_to_node[obj]
    tid = target.value if hasattr(target, "value") else int(target)
    frontier = [(start, 0)]
    seen = {start.value if hasattr(start, "value") else int(start)}
    while frontier:
        node, d = frontier.pop(0)
        if d >= max_hops:
            continue
        for k in _out_neighbours(substrate, node):
            kid = k.value if hasattr(k, "value") else int(k)
            if kid == tid:
                return True, d + 1
            if kid not in seen:
                seen.add(kid)
                frontier.append((k, d + 1))
    return False, 0
