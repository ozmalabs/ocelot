"""The agent LEARNS to classify the residue it can't ground — taught, not seeded.
It is taught a sample, INDUCES a shape-pattern per kind (no teacher needed after),
applies it to new words, and CAPTURES each as a typed node
(domains/remainder_classification). Uses a stub teacher (no live consult)."""
from __future__ import annotations

import json

from substrate.world_adapter import WorldAdapter
from domains import remainder_classification as rc


# a stub teacher: returns fixed labels for the taught sample (stands in for claude -p)
_LABELS = {
    "AAC": "acronym", "TCP": "acronym", "ALU": "acronym",
    "argmax": "code_identifier", "alloc": "code_identifier", "args": "code_identifier",
    "Ackermann": "person_name", "Amdahl": "person_name", "Bandura": "person_name",
    "Born": "person_name", "Kolmogorov": "person_name",   # varied lengths
    "allostatic": "domain_term", "aperiodic": "domain_term",
}
_CTX = {  # the prose case of each word (acronyms ALLCAPS, names Capitalized)
    "aac": "MP3/AAC/Opus codecs", "tcp": "TCP slow start", "alu": "1-5 ALU ops",
    "argmax": "argmax over the bins", "alloc": "alloc and free", "args": "the args list",
    "ackermann": "the Ackermann function", "amdahl": "Amdahl's law", "bandura": "Bandura's theory",
    "born": "the Born rule", "kolmogorov": "Kolmogorov complexity",
    "allostatic": "allostatic load rises", "aperiodic": "an aperiodic signal",
}


def _ctx(w):
    return _CTX.get(w, w)


def _ask(_q):
    return json.dumps(_LABELS)


def test_agent_learns_shape_patterns_per_kind():
    wa = WorldAdapter()
    sample = list(_CTX)
    taught = rc.teach_sample(wa.s, sample, _ctx, _ask)
    assert taught and all(k in rc.KINDS for k in taught.values())
    # a TaughtHint is recorded for each
    assert len(wa.s.nodes("TaughtHint")) >= len(taught)
    learned = rc.learn_classifier(taught, _ctx)
    # it induced the discriminative shapes
    assert learned["acronym"]["caps"] == "ALLCAPS"
    assert learned["person_name"]["caps"] == "Capitalized"
    assert learned["code_identifier"]["caps"] == "lower"


def test_applies_to_new_words_without_asking_again():
    wa = WorldAdapter()
    taught = rc.teach_sample(wa.s, list(_CTX), _ctx, _ask)
    learned = rc.learn_classifier(taught, _ctx)
    # held-out words it was NOT taught, classified by the learned shapes
    assert rc.classify("aead", "AEAD (GCM) for integrity", learned) == "acronym"
    assert rc.classify("attrs", "the node attrs dict", learned) == "code_identifier"
    assert rc.classify("borel", "the Borel set", learned) == "person_name"


def test_capture_makes_typed_nodes():
    wa = WorldAdapter()
    rc.capture(wa.s, "argmax", "code_identifier", "argmax over bins")
    rc.capture(wa.s, "ackermann", "person_name", "Ackermann function")
    assert any(wa.s.node(n)["attrs"]["surface"] == "argmax"
               for n in wa.s.nodes("CodeIdentifier"))
    assert any(wa.s.node(n)["attrs"]["surface"] == "ackermann"
               for n in wa.s.nodes("PersonName"))
