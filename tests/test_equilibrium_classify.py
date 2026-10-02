"""Equilibrium classifier sidecar v0 (T3): seed pack subset + thin adapter.

Synthetic golden set only (pseudonyms actor_a / expert_e). OZMA_NO_LLM=1.
Run: OZMA_NO_LLM=1 python3 -m pytest tests/test_equilibrium_classify.py -q
"""
import importlib.util
import json
import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from domains import equilibrium_classify as eq  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RULE_NAME = re.compile(r"^eq\.(msg|rel|emo|pat)\.[a-z_]+\.[a-z0-9_]+$")

# (id, text, {label: values}, {rule names without "eq.msg." / "@ver"})
GOLDEN = [
    ("actor_a_01", "How do I reverse a list in Python?",
     {"msg.speech_act": ["question"], "msg.substantive_markers": ["question"]},
     {"speech_act.sak_question", "substantive_markers.question_act"}),
    ("expert_e_01", "Use `reversed(xs)` or slice it with `xs[::-1]`.",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["code"]},
     {"speech_act.sak_statement", "substantive_markers.code_inline"}),
    ("actor_a_02", "Is that faster",  # subject-aux inversion, no '?'
     {"msg.speech_act": ["question"], "msg.substantive_markers": ["question"]},
     {"speech_act.sak_question", "substantive_markers.question_act"}),
    ("expert_e_02", "```python\nxs.reverse()\n```",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["code"]},
     {"speech_act.sak_statement", "substantive_markers.code_fence"}),
    ("expert_e_03", "See https://docs.example.org/tutorial/lists.html for details.",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["link"]},
     {"speech_act.sak_statement", "substantive_markers.link_url"}),
    ("actor_a_03", "Sorry, I misread your answer.",
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True]},
     {"speech_act.sak_statement", "deescalation.cue_unigram"}),
    ("actor_a_04", "Fair point, that works.",
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True]},
     {"speech_act.sak_statement", "deescalation.cue_bigram"}),
    ("expert_e_04", "No worries!",
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True]},
     {"speech_act.sak_statement", "deescalation.cue_bigram"}),
    ("expert_e_05", "According to the docs, reverse() mutates in place.",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["citation"]},
     {"speech_act.sak_statement", "substantive_markers.citation_cue_bigram"}),
    ("actor_a_05", "Compare the two outputs.",
     {"msg.speech_act": ["directive"]}, {"speech_act.sak_instruction"}),
    ("expert_e_06", "Notice the trailing comma.",
     {"msg.speech_act": ["directive"]}, {"speech_act.sak_instruction"}),
    ("actor_a_06", "What about tuples?",
     {"msg.speech_act": ["question"], "msg.substantive_markers": ["question"]},
     {"speech_act.sak_question", "substantive_markers.question_act"}),
    ("expert_e_07", "Tuples are immutable, cf. the data model docs.",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["citation"]},
     {"speech_act.sak_statement", "substantive_markers.citation_cue_unigram"}),
    ("actor_a_07", "My bad, you\u2019re right.",  # two bigram cues, one rule fire
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True]},
     {"speech_act.sak_statement", "deescalation.cue_bigram"}),
    ("expert_e_08", "Here is a fix: `sorted(xs, reverse=True)` and more at https://example.org/sorting",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["code", "link"]},
     {"speech_act.sak_statement", "substantive_markers.code_inline", "substantive_markers.link_url"}),
    ("actor_a_08", "Why does `xs.reverse()` return None?",
     {"msg.speech_act": ["question"], "msg.substantive_markers": ["code", "question"]},
     {"speech_act.sak_question", "substantive_markers.code_inline", "substantive_markers.question_act"}),
    ("actor_a_09", "Thanks, it works now.",  # gratitude is NOT supported in this slice
     {"msg.speech_act": ["assertion"]}, {"speech_act.sak_statement"}),
    ("expert_e_09", "That is wrong and you know it.",  # hostility NOT supported in this slice
     {"msg.speech_act": ["assertion"]}, {"speech_act.sak_statement"}),
    ("actor_a_10", "Run `echo sorry` again.",  # cue inside code is not a cue
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["code"]},
     {"speech_act.sak_statement", "substantive_markers.code_inline"}),
    ("expert_e_10", "I understand the confusion; see section 5.1 of the tutorial.",
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True],
      "msg.substantive_markers": ["citation"]},
     {"speech_act.sak_statement", "deescalation.cue_bigram",
      "substantive_markers.citation_cue_bigram"}),
    ("actor_a_11", "", {"msg.speech_act": ["assertion"]}, {"speech_act.sak_statement"}),
]


@pytest.fixture(scope="module")
def base():
    s, root = eq.boot()
    snap = s.snapshot()
    return s, root, snap


def _run(base):
    _, root, snap = base
    branch = snap.fork()
    return eq.classify(branch, root, [{"id": i, "text": t} for i, t, _, _ in GOLDEN])


def test_golden_labels_and_rule_ids(base):
    out = _run(base)
    assert [o["id"] for o in out] == [g[0] for g in GOLDEN]
    for o, (mid, _text, labels, rules) in zip(out, GOLDEN):
        got = {k: sorted(v["values"], key=str) for k, v in o["labels"].items()}
        assert got == {k: sorted(v, key=str) for k, v in labels.items()}, mid
        assert set(o["rule_ids"]) == {f"eq.msg.{r}@{eq.PACK_VERSION}" for r in rules}, mid
        for lab, row in o["labels"].items():
            assert row["status"] == "shadow" and row["match_class"] == "exact", (mid, lab)
            assert all(r.startswith(f"eq.{lab}.") for r in row["rule_ids"]), (mid, lab)


def test_fork_isolation_and_determinism(base):
    s, root, snap = base
    rev0 = snap.source_revision
    n0 = len(s._inner.nodes())
    a, b = _run(base), _run(base)
    assert a == b
    assert snap.source_revision == rev0
    assert len(s._inner.nodes()) == n0


def test_pack_manifests_shape():
    seen = set()
    for m in eq.pack_manifests():
        assert m["self_load_only"] is True and m["version"] == eq.PACK_VERSION
        assert m["taxonomy_version"] == eq.TAXONOMY_VERSION
        assert isinstance(m["depends_on"], list) and m["depends_on"]
        assert all(d in seen or not d.startswith("equilibrium_") for d in m["depends_on"])
        seen.add(m["id"])
        for r in m.get("rules", []):
            assert RULE_NAME.match(r["name"]), r["name"]
            assert not r["name"].startswith("eq.pat."), "v0 slice ships no pattern rules"


def test_pattern_labels_are_disabled_stubs(base):
    _, root, snap = base
    st = eq._label_status(snap.fork(), root)
    pats = {k: v for k, v in st.items() if k.startswith("pat.")}
    assert len(pats) == 7 and all(v["status"] == "disabled" for v in pats.values())
    assert {k for k, v in st.items() if v["status"] == "shadow"} == {
        "msg.speech_act", "msg.substantive_markers", "msg.deescalation"}


def test_builder_reproduces_checked_in_seeds():
    spec = importlib.util.spec_from_file_location(
        "build_eq_pack", ROOT / "scripts" / "build_equilibrium_seed_pack.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    built = mod.build()
    for sid in eq.PACK_IDS:
        on_disk = json.loads((ROOT / "seeds" / f"{sid}.json").read_text())
        assert json.loads(json.dumps(built[sid])) == on_disk, sid


def test_pack_digest_is_stable_hex():
    d = eq.pack_digest()
    assert re.fullmatch(r"[0-9a-f]{64}", d) and d == eq.pack_digest()
