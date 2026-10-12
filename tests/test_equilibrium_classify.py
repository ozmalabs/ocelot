"""Equilibrium classifier sidecar v0 (T3): seed pack subset + thin adapter.

Synthetic golden set only (pseudonyms actor_a / expert_e). OZMA_NO_LLM=1.
Pack 0.2.0 adds cue labels concession / status_claim / hostility / domain(technical).
Pack 0.3.0 (T3b): scoped cue sets (deescalation / concession / status_claim /
hostility / ...) mark a HIT with their n-gram rule (`eqcue:` provenance) and the
negation/hedge scope rule `<label>.affirmed` decides the label; technical
vocabulary is lemma-matched. Rule-id expectations below are the v0.2 n-gram
rules plus the `.affirmed` label rule (see `_expand`).
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
RULE_NAME = re.compile(r"^eq\.((msg|rel|emo|pat)\.[a-z_]+\.[a-z0-9_]+"
                       r"|(win|quanta|competence|ep)(\.[a-z_]+){1,3})$")
SCOPED = {"deescalation", "concession", "status_claim", "hostility"}


def _expand(rules):
    """v0.2 rule names -> 0.3.0 rule ids: a scoped n-gram hit adds `<label>.affirmed`."""
    return set(rules) | {f"{r.split('.')[0]}.affirmed" for r in rules if r.split(".")[0] in SCOPED}

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
    ("actor_a_03", "Sorry, I misread your answer.",  # 0.4.0: also an error admission
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True], "msg.error_admission": [True]},
     {"speech_act.sak_statement", "deescalation.cue_unigram", "error_admission.cue_bigram",
      "error_admission.affirmed"}),
    ("actor_a_04", "Fair point, that works.",  # 0.2.0: also a concession cue
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True], "msg.concession": [True]},
     {"speech_act.sak_statement", "deescalation.cue_bigram", "concession.cue_bigram"}),
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
    ("actor_a_07", "My bad, you\u2019re right.",  # two bigram cues, one rule fire; 0.4.0 error admission
     {"msg.speech_act": ["assertion"], "msg.deescalation": [True], "msg.concession": [True],
      "msg.error_admission": [True]},
     {"speech_act.sak_statement", "deescalation.cue_bigram", "concession.cue_bigram",
      "error_admission.cue_bigram", "error_admission.affirmed"}),
    ("expert_e_08", "Here is a fix: `sorted(xs, reverse=True)` and more at https://example.org/sorting",
     {"msg.speech_act": ["assertion"], "msg.substantive_markers": ["code", "link"]},
     {"speech_act.sak_statement", "substantive_markers.code_inline", "substantive_markers.link_url"}),
    ("actor_a_08", "Why does `xs.reverse()` return None?",
     {"msg.speech_act": ["question"], "msg.substantive_markers": ["code", "question"]},
     {"speech_act.sak_question", "substantive_markers.code_inline", "substantive_markers.question_act"}),
    ("actor_a_09", "Thanks, it works now.",  # gratitude is NOT supported in this slice
     {"msg.speech_act": ["assertion"]}, {"speech_act.sak_statement"}),
    ("expert_e_09", "That is wrong and you know it.",  # no hostility cue; 0.4.0 disagreement formula
     {"msg.speech_act": ["assertion"], "msg.disagreement": [True]},
     {"speech_act.sak_statement", "disagreement.cue_trigram", "disagreement.affirmed"}),
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

# ---- 0.2.0 cue labels: positives + near-miss negatives (synthetic, pseudonyms) --
A_ = "assertion"
GOLDEN_V2 = [
    # concession
    ("actor_a_12", "Good catch, I stand corrected.", A_, {"msg.concession": [True]},
     {"concession.cue_bigram", "concession.cue_trigram"}),
    ("expert_e_11", "That makes sense to me.", A_, {"msg.concession": [True]},
     {"concession.cue_trigram"}),
    ("actor_a_13", "I hadn\u2019t considered that edge case.", A_, {"msg.concession": [True]},
     {"concession.cue_4gram"}),
    ("expert_e_12", "Fair enough.", A_, {"msg.concession": [True]}, {"concession.cue_bigram"}),
    ("actor_a_14", "That makes no sense.", A_, {}, set()),                     # near miss
    ("expert_e_13", "Good points were raised on the right side.", A_, {}, set()),  # near miss
    # status_claim (incl. the <num> token-class slot)
    ("expert_e_14", "In my 15 years of doing this it never failed.", A_,
     {"msg.status_claim": [True]}, {"status_claim.cue_4gram"}),
    ("expert_e_15", "As the lead on this, trust me.", A_, {"msg.status_claim": [True]},
     {"status_claim.cue_trigram", "status_claim.cue_bigram"}),
    ("expert_e_16", "I know what I'm doing here.", A_, {"msg.status_claim": [True]},
     {"status_claim.cue_5gram"}),
    ("expert_e_17", "Decades of experience say otherwise.", A_, {"msg.status_claim": [True]},
     {"status_claim.cue_trigram"}),
    ("expert_e_18", "I have 12 years of experience with this.", A_, {"msg.status_claim": [True]},
     {"status_claim.cue_4gram"}),
    ("actor_a_15", "In my years here nothing changed.", A_, {}, set()),        # near miss: no number
    ("actor_a_16", "In my fifteen years here nothing changed.", A_, {}, set()),  # limit: number word
    ("actor_a_17", "As the deadline nears we ship.", A_, {}, set()),            # near miss
    # hostility (cue-level only)
    ("actor_a_18", "This is ridiculous.", A_, {"msg.hostility": [True]}, {"hostility.cue_unigram"}),
    ("expert_e_19", "You don't understand the problem.", A_, {"msg.hostility": [True]},
     {"hostility.cue_trigram"}),
    ("actor_a_19", "That was a waste of time and a bad idea.", A_, {"msg.hostility": [True]},
     {"hostility.cue_trigram", "hostility.cue_bigram"}),
    ("actor_a_20", "I am serious about the deadline.", A_, {}, set()),         # near miss
    ("expert_e_20", "Set `stupid_mode=false` in the config.", None,
     {"msg.substantive_markers": ["code"]}, {"substantive_markers.code_inline"}),  # cue in code
    ("actor_a_21", "That is not obviously correct.", A_, {}, set()),           # near miss
    # domain: technical
    ("expert_e_21", "The p99 latency doubled after the deploy.", A_, {"msg.domain": ["technical"]},
     {"domain.technical_cue_unigram"}),
    ("expert_e_22", "We found a memory leak in the connection pool.", A_,
     {"msg.domain": ["technical"]}, {"domain.technical_cue_bigram"}),
    # 0.3.0: technical vocabulary is lemma-matched (indexes -> index), was a near miss in 0.2.0
    ("actor_a_22", "The indexes look fine to me.", A_, {"msg.domain": ["technical"]},
     {"domain.technical_cue_unigram"}),
    ("actor_a_23", "Read `tcp_dump.txt` and the socketed notes.", None,  # lemma limit: WordNet
     {"msg.substantive_markers": ["code"]}, {"substantive_markers.code_inline"}),  # has no 'socketed'
    # de-escalation: meeting facilitation
    ("expert_e_23", "Let\u2019s step back for a moment.", None, {"msg.deescalation": [True]},
     {"deescalation.cue_trigram"}),
    ("actor_a_24", "Both points are valid.", A_, {"msg.deescalation": [True]},
     {"deescalation.cue_4gram"}),
    ("expert_e_24", "Let's focus on the data.", None, {"msg.deescalation": [True]},
     {"deescalation.cue_5gram"}),
    ("actor_a_25", "To synthesize, we ship on Friday.", A_, {"msg.deescalation": [True]},
     {"deescalation.cue_bigram"}),
    ("expert_e_25", "Let's hear from everyone first.", None, {"msg.deescalation": [True]},
     {"deescalation.cue_4gram"}),
    ("actor_a_26", "Let's step forward.", None, {}, set()),                    # near miss
    ("expert_e_26", "Run `let's pause` in the shell.", None,
     {"msg.substantive_markers": ["code"]}, {"substantive_markers.code_inline"}),  # cue in code
]
CUE_FAMILIES = {"concession", "status_claim", "hostility", "domain", "deescalation",
                "substantive_markers"}
CUE_LABELS = {"msg.concession", "msg.status_claim", "msg.hostility", "msg.domain",
              "msg.deescalation", "msg.substantive_markers"}


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
        assert set(o["rule_ids"]) == {f"eq.msg.{r}@{eq.PACK_VERSION}" for r in _expand(rules)}, mid
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
    """0.3.0: v0 `pat.*` person labels are replaced by `pattern.*` composite
    traits, all disabled; every msg label, trait, episode kind and facet is shadow."""
    _, root, snap = base
    st = eq._label_status(snap.fork(), root)
    assert not any(k.startswith("pat.") for k in st)
    pats = {k: v for k, v in st.items() if k.startswith("pattern.")}
    assert len(pats) == 7 and all(v["status"] == "disabled" and v["kind"] == "trait"
                                  for v in pats.values())
    assert {k for k, v in st.items() if v["status"] != "shadow"} == set(pats)
    assert {"msg.speech_act", "msg.substantive_markers", "msg.deescalation", "msg.concession",
            "msg.status_claim", "msg.hostility", "msg.domain"} <= set(st)
    assert all(st[k]["match_class"] == "exact" for k in CUE_LABELS)
    assert {k for k, v in st.items() if v["since_pack"] == "0.2.0"} == {
        "msg.concession", "msg.status_claim", "msg.hostility", "msg.domain"}
    assert {v["kind"] for v in st.values()} == {"msg", "trait", "episode_kind", "facet"}


def test_v2_cue_labels_golden(base):
    """0.2.0 cue labels: positives fire the expected n-gram rule; near misses and
    cues inside code spans fire nothing. Speech act checked only where given."""
    _, root, snap = base
    out = eq.classify(snap.fork(), root, [{"id": g[0], "text": g[1]} for g in GOLDEN_V2])
    assert [o["id"] for o in out] == [g[0] for g in GOLDEN_V2]
    for o, (mid, _text, act, labels, rules) in zip(out, GOLDEN_V2):
        got = {k: sorted(v["values"], key=str) for k, v in o["labels"].items() if k in CUE_LABELS}
        assert got == labels, mid
        cue_rids = {r for r in o["rule_ids"] if r.split(".")[2] in CUE_FAMILIES}
        assert cue_rids == {f"eq.msg.{r}@{eq.PACK_VERSION}" for r in _expand(rules)}, mid
        if act is not None:
            assert o["labels"]["msg.speech_act"]["values"] == [act], mid
        for lab in got:
            assert o["labels"][lab]["status"] == "shadow", (mid, lab)


def test_lexicon_cues_are_contiguous_and_num_slot_is_scoped():
    lex = next(m for m in eq.pack_manifests() if m["id"] == "equilibrium_lexicon")
    cues = [n["attrs"] for n in lex["nodes"]]
    assert all(n["type"] == "EqCue" for n in lex["nodes"])
    by_tgt: dict = {}
    for e in lex["edges"]:
        by_tgt.setdefault(e["tgt"]["local"], []).append(e["type"])
    for n in lex["nodes"]:  # one reachability edge + exactly its own (cue, length) bucket edge
        a = n["attrs"]
        size = sum(f"w{k}" in a for k in range(1, 6))
        assert sorted(by_tgt[n["local_id"]]) == sorted(
            ["eq_has_cue", f"eq_cue_{a['cue']}_n{size}"]), a
    for c in cues:
        slots = [k for k in ("w1", "w2", "w3", "w4", "w5") if k in c]
        assert slots == ["w1", "w2", "w3", "w4", "w5"][:len(slots)] and slots, c
        assert set(c) <= {"cue", "variant", *slots}, c
        assert all(re.fullmatch(r"[a-z0-9]+(?:'[a-z]+)?|<num>|<noun\.(person|group)>", c[k])
                   for k in slots), c
        classes = {c[k] for k in slots if c[k].startswith("<")}
        if eq.NUM_CLASS in classes:
            assert c["cue"] == "status_claim", c
        if "<noun.person>" in classes:
            assert c["cue"] in ("credential", "credential_denial"), c
        if "<noun.group>" in classes:
            assert c["cue"] == "tribal", c
    assert {c["cue"] for c in cues} == {
        "deescalation", "citation", "concession", "status_claim", "hostility", "domain_technical",
        "credential", "credential_denial", "deference", "booster", "withdrawal", "dismissal",
        "tribal", "procedural", "disagreement", "error_admission", "error_denial", "evidence_request"}


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
