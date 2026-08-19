"""Generic resident-held rules for documents, observations, and writing.

Reading a law, proclamation, charter, notice, contract, recipe, or game
rulebook creates a private interpretation.  Observations activate that
interpretation and produce candidates; only an explicit backend commitment
can turn a candidate into a goal or communication input.  No function here
enforces a rule or mutates a world object.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Optional

import substrate_rs as srs

from substrate.seed_loader import manifest_for

_SEED_FLAG = "cognitive_rule_frames_loaded"
_TERMINALS = frozenset(".!?")


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None) or getattr(sub, "_inner", sub)
    root = getattr(agent, "agent", None)
    if root is None:
        root = next((n for n in sub.nodes("Agent")
                     if not sub.node(n)["attrs"].get("is_class")), None)
    if root is None:
        raise ValueError("cognitive rule frames require an Agent root")
    return sub, native, root


def _nid(value):
    return value if hasattr(value, "value") else srs.NodeID(int(value))


def _edge(native, source, kind, target):
    try:
        native.add_edge_unchecked(source, kind, target)
    except TypeError:
        native.add_edge_unchecked(source, kind, target, {})


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _key(*parts):
    return hashlib.sha256("\x1f".join(map(str, parts)).encode()).hexdigest()


def _node(agent, surface):
    sub, _, _ = _resolve(agent)
    surface = str(surface).strip().lower()
    # Occurrences stay distinct.  Rule and observation cues are joined by the
    # surface attribute; aliasing them to one node loses provenance and native
    # graph matching intentionally rejects that alias.
    return sub.add_node("CognitiveCue", {
        "surface": surface, "normal_form": surface,
        "provenance": "resident_lexical_cue"})


def ensure_seed(agent):
    sub, native, root = _resolve(agent)
    if sub.node(root)["attrs"].get(_SEED_FLAG) == 1.0:
        return
    native.load_seed_manifest(manifest_for("cognitive_rule_frames"), root)
    native.set_attr(root, _SEED_FLAG, 1.0)


def _sentences(text):
    out, buf = [], []
    text = str(text or "")
    for i, char in enumerate(text):
        buf.append(char)
        if char in _TERMINALS and (i + 1 == len(text) or text[i + 1].isspace()):
            value = "".join(buf).strip()
            if value:
                out.append(value)
            buf = []
    value = "".join(buf).strip()
    if value:
        out.append(value)
    return out


def _tokens(agent, text):
    try:
        from domains.instruction_comprehension import tokenize
        return tokenize(agent, str(text or ""))
    except Exception:
        return []


def _cues(agent, text, tokens=None):
    sub, _, _ = _resolve(agent)
    tokens = _tokens(agent, text) if tokens is None else tokens
    out = []
    for token in tokens:
        attrs = sub.node(token)["attrs"]
        word = str(attrs.get("text") or "").strip().lower()
        if (not word or word in _TERMINALS or
                not any(char.isalnum() for char in word) or
                float(attrs.get("fn") or 0.0) > 0.5):
            continue
        if word not in out:
            out.append(word)
    return out


def _instruction(agent, text):
    try:
        from domains.instruction_comprehension import comprehend
        return comprehend(agent, text)
    except Exception as exc:
        return {"tokens": [], "units": [], "error": str(exc)}


def _prose(agent, text):
    try:
        from domains.reading_collapse import read_clause
        return read_clause(agent, text, write=False, learn=True)
    except Exception as exc:
        return {"clause": text, "predications": [],
                "residual_before": [text], "error": str(exc)}


def _interpret(sentence, instruction, prose):
    units = list(instruction.get("units") or [])
    kind, condition, consequence, procedure = "statement", "", sentence, ""
    if units:
        unit = units[0]
        unit_kind = str(unit.get("kind") or "act")
        if unit_kind == "ifthen":
            kind = "conditional"
            condition = str(unit.get("cond_text") or "")
            consequence = " ".join(str(x.get("text") or "")
                                    for x in (unit.get("body") or [])).strip()
            consequence = consequence or str(unit.get("text") or sentence)
        elif unit_kind == "foreach":
            kind = "procedure"
            condition = str(unit.get("source_text") or "")
            procedure = " ".join(str(x.get("text") or "")
                                  for x in (unit.get("body") or [])).strip()
            consequence = procedure or str(unit.get("text") or sentence)
        elif unit_kind == "stop":
            kind = "termination"
            condition = str(unit.get("cond_text") or "")
            consequence = str(unit.get("text") or sentence)
        else:
            kind = "procedure"
            procedure = " ".join(str(x.get("text") or "") for x in units).strip()
            consequence = procedure or sentence
    speech_act = str(prose.get("speech_act") or "statement")
    if speech_act == "instruction" and kind == "statement":
        kind, procedure, consequence = "procedure", sentence, sentence
    residual = list(prose.get("residual_before") or [])
    confidence = 1.0 if (units or prose.get("predications") or prose.get("construction")) else 0.45
    if residual:
        confidence *= 0.75
    return {
        "kind": kind, "condition_text": condition,
        "consequence_text": consequence, "procedure_text": procedure,
        "norm_text": "", "confidence": float(confidence),
        "speech_act": speech_act, "instruction_units": units,
        "prose_reading": prose, "residual": residual}


def _private_doc(agent, source_key):
    sub, _, root = _resolve(agent)
    for node in sub.nodes("CognitiveRuleDocument"):
        if (sub.node(node)["attrs"].get("source_key") == source_key and
                node in sub.neighbours(root, "holds_rule_document")):
            return node
    return None


def _result(agent, document, source=None, evidence=None):
    sub, _, _ = _resolve(agent)
    rules = list(sub.neighbours(document, "has_rule"))
    cues = []
    for rule in rules:
        for cue in sub.neighbours(rule, "has_cue"):
            if cue not in cues:
                cues.append(cue)
    return {"status": "held", "rule_document": document,
            "source_document": source, "rules": rules, "cues": cues,
            "evidence": evidence or {},
            "source_key": sub.node(document)["attrs"].get("source_key")}


def read_rule_document(agent, source_document, text, *, name="document",
                       kind="document", author=None, version=None):
    """Read a rule-like physical document into this resident's private graph."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    text, name, kind = str(text or ""), str(name), str(kind)
    source_key = _key(name, kind, version, text)
    existing = _private_doc(agent, source_key)
    if existing is not None:
        return _result(agent, existing, source_document, {"idempotent": True})
    document = sub.add_node("CognitiveRuleDocument", {
        "name": name, "title": name, "document_kind": kind,
        "author": "" if author is None else str(author),
        "version": "" if version is None else str(version),
        "source_key": source_key, "status": "held",
        "text_hash": hashlib.sha256(text.encode()).hexdigest(),
        "sentence_count": 0.0, "provenance": "resident_read_document"})
    _edge(native, root, "holds_rule_document", document)
    if source_document is not None:
        _edge(native, document, "from_document", _nid(source_document))
    sentences, instruction_reads, prose_reads = _sentences(text), [], []
    cue_count = 0
    for order, sentence in enumerate(sentences):
        instruction, prose = _instruction(agent, sentence), _prose(agent, sentence)
        interpretation = _interpret(sentence, instruction, prose)
        instruction_reads.append(instruction)
        prose_reads.append(prose)
        rule = sub.add_node("HeldRule", {
            "rule_key": f"{source_key}:{order}", "source_key": source_key,
            "source_order": float(order), "surface": sentence,
            "kind": interpretation["kind"], "status": "held",
            "condition_text": interpretation["condition_text"],
            "consequence_text": interpretation["consequence_text"],
            "procedure_text": interpretation["procedure_text"],
            "norm_text": interpretation["norm_text"],
            "confidence": interpretation["confidence"],
            "interpretation_json": _json(interpretation),
            "provenance": "resident_read_document"})
        _edge(native, document, "has_rule", rule)
        _edge(native, root, "holds_rule", rule)
        surfaces = _cues(agent, sentence)
        cue_count += len(surfaces)
        for surface in surfaces:
            _edge(native, rule, "has_cue", _node(agent, surface))
    native.set_attr(document, "sentence_count", float(len(sentences)))
    native.set_attr(document, "cue_count", float(cue_count))
    native.run_rules()
    return _result(agent, document, source_document, {
        "sentences": sentences, "instruction_reads": instruction_reads,
        "prose_reads": prose_reads,
        "reader": "instruction_comprehension+reading_collapse"})


def _next_sequence(agent):
    sub, _, root = _resolve(agent)
    values = [int(sub.node(node)["attrs"].get("sequence", -1) or -1)
              for node in sub.neighbours(root, "has_cognitive_observation")]
    return max(values + [-1]) + 1


def observe_situation(agent, text="", *, cues=None, kind="world_observation",
                      source=None, attributes=None):
    """Add an observation and return graph-created activations/predictions."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    text, sequence = str(text or ""), _next_sequence(agent)
    surfaces = [str(x).strip().lower() for x in (cues or []) if str(x).strip()]
    if not surfaces and text:
        surfaces = _cues(agent, text)
    surfaces = list(dict.fromkeys(surfaces))
    observation_key = _key(kind, sequence, text, surfaces)
    observation = sub.add_node("CognitiveObservation", {
        "observation_key": observation_key, "sequence": float(sequence),
        "kind": str(kind), "status": "current", "surface": text,
        "source": "" if source is None else str(source),
        "attributes_json": _json(attributes or {}),
        "provenance": "world_observation"})
    _edge(native, root, "has_cognitive_observation", observation)
    cue_nodes = []
    for surface in surfaces:
        cue = _node(agent, surface)
        cue_nodes.append(cue)
        _edge(native, observation, "has_cue", cue)
    native.run_rules()
    activations = []
    for node in sub.neighbours(root, "has_rule_activation"):
        if (sub.node(node)["attrs"].get("observation_key") == observation_key
                and node not in activations):
            activations.append(node)
    predictions = []
    for activation in activations:
        for prediction in sub.neighbours(activation, "has_prediction"):
            if prediction not in predictions:
                predictions.append(prediction)
    return {"status": "observed", "observation": observation,
            "cues": cue_nodes, "activations": activations,
            "predictions": predictions}


def commit_prediction(agent, prediction, *, mode="goal", meaning=None,
                      target=None, priority=1.0):
    """Record explicit backend use of a prediction, without enacting it."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    prediction = _nid(prediction)
    if not sub.has_node(prediction):
        raise KeyError(f"unknown RulePrediction {prediction}")
    if sub.node(prediction)["type"] != "RulePrediction":
        raise TypeError("commit_prediction expects a RulePrediction node")
    mode = str(mode)
    if mode not in {"goal", "plan", "action_input", "utterance", "communication"}:
        raise ValueError(f"unsupported cognitive commitment mode: {mode!r}")
    attrs = sub.node(prediction)["attrs"]
    commitment = sub.add_node("CognitiveCommitment", {
        "mode": mode, "status": "committed",
        "prediction_key": attrs.get("key", ""),
        "meaning_json": _json(meaning if meaning is not None else
                               {"rule_prediction": attrs.get("surface", "")}),
        "priority": float(priority),
        "target": "" if target is None else str(target),
        "provenance": "resident_backend_decision"})
    _edge(native, root, "has_cognitive_commitment", commitment)
    _edge(native, commitment, "for_prediction", prediction)
    native.set_attr(prediction, "status", "committed")
    result = {"commitment": commitment, "prediction": prediction, "mode": mode}
    if mode in {"goal", "plan", "action_input"}:
        goal = sub.add_node("Goal", {
            "goal_kind": "cognitive_rule_prediction", "status": "candidate",
            "prediction_key": attrs.get("key", ""),
            "meaning_json": sub.node(commitment)["attrs"]["meaning_json"],
            "priority": float(priority)})
        _edge(native, root, "has_goal", goal)
        _edge(native, commitment, "produces_goal", goal)
        result["goal"] = goal
    elif mode in {"utterance", "communication"}:
        intent = sub.add_node("CognitiveCommunicationIntent", {
            "status": "candidate",
            "meaning_json": sub.node(commitment)["attrs"]["meaning_json"],
            "priority": float(priority),
            "target": "" if target is None else str(target)})
        _edge(native, root, "has_communication_intent", intent)
        _edge(native, commitment, "produces_communication_intent", intent)
        result["communication_intent"] = intent
    native.run_rules()
    return result


def draft_document(agent, text, *, name="document", kind="document",
                   audience=None, source_prediction=None):
    """Compose a private draft for a law, proclamation, notice, or rule."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    name, kind = str(name), str(kind)
    revisions = [int(sub.node(n)["attrs"].get("revision", 0) or 0)
                 for n in sub.neighbours(root, "authored_document")
                 if sub.node(n)["type"] == "DocumentDraft"
                 and sub.node(n)["attrs"].get("name") == name]
    revision = max(revisions + [0])
    draft = sub.add_node("DocumentDraft", {
        "name": name, "title": name, "kind": kind, "text": str(text or ""),
        "revision": float(revision), "status": "draft",
        "audience_json": _json(list(audience or [])),
        "provenance": "resident_composition"})
    _edge(native, root, "authored_document", draft)
    if source_prediction is not None:
        prediction = _nid(source_prediction)
        if not sub.has_node(prediction):
            raise KeyError(f"unknown source RulePrediction {prediction}")
        _edge(native, draft, "based_on_prediction", prediction)
    native.run_rules()
    return {"status": "drafted", "draft": draft, "revision": revision}


def revise_document_draft(agent, draft, text):
    """Revise a private draft without publishing or notifying anyone."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    draft = _nid(draft)
    if not sub.has_node(draft) or sub.node(draft)["type"] != "DocumentDraft":
        raise KeyError(f"unknown DocumentDraft {draft}")
    if draft not in sub.neighbours(root, "authored_document"):
        raise PermissionError("a resident can only revise its own private draft")
    next_revision = int(sub.node(draft)["attrs"].get("revision", 0) or 0) + 1
    native.set_attr(draft, "text", str(text or ""))
    native.set_attr(draft, "revision", float(next_revision))
    native.set_attr(draft, "status", "draft")
    return {"status": "revised", "draft": draft, "revision": next_revision}


def propose_document_write(agent, draft, *, destination=None, priority=1.0):
    """Return a world-facing write proposal without publishing the document."""
    ensure_seed(agent)
    sub, native, root = _resolve(agent)
    draft = _nid(draft)
    if not sub.has_node(draft) or sub.node(draft)["type"] != "DocumentDraft":
        raise KeyError(f"unknown DocumentDraft {draft}")
    if draft not in sub.neighbours(root, "authored_document"):
        raise PermissionError("a resident can only propose its own private draft")
    attrs = sub.node(draft)["attrs"]
    proposal = sub.add_node("DocumentWriteIntent", {
        "status": "candidate", "name": attrs.get("name", "document"),
        "kind": attrs.get("kind", "document"), "text": attrs.get("text", ""),
        "revision": attrs.get("revision", 0.0),
        "destination": "" if destination is None else str(destination),
        "priority": float(priority), "provenance": "resident_backend_decision"})
    _edge(native, root, "proposed_document_write", proposal)
    _edge(native, proposal, "for_draft", draft)
    return {"status": "candidate", "proposal": proposal,
            "name": attrs.get("name", "document"),
            "kind": attrs.get("kind", "document"),
            "text": attrs.get("text", ""),
            "revision": attrs.get("revision", 0.0), "destination": destination}


def held_rule_state(agent):
    """Return resident-owned rule state for reverse APIs and debugging."""
    sub, _, root = _resolve(agent)

    def connected(edge, type_name):
        out = []
        for node in sub.neighbours(root, edge):
            if sub.node(node)["type"] == type_name and node not in out:
                out.append(node)
        return out

    return {
        "rule_documents": connected("holds_rule_document", "CognitiveRuleDocument"),
        "rules": connected("holds_rule", "HeldRule"),
        "observations": connected("has_cognitive_observation", "CognitiveObservation"),
        "activations": connected("has_rule_activation", "RuleActivation"),
        "predictions": connected("has_rule_prediction", "RulePrediction"),
        "commitments": connected("has_cognitive_commitment", "CognitiveCommitment"),
        "communication_intents": connected("has_communication_intent", "CognitiveCommunicationIntent"),
        "goals": connected("has_goal", "Goal"),
    }


__all__ = [
    "commit_prediction", "draft_document", "ensure_seed", "held_rule_state",
    "observe_situation", "propose_document_write", "read_rule_document",
    "revise_document_draft",
]
