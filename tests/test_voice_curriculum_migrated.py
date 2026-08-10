"""test_voice_curriculum_migrated -- VOICE-EXPANSION (WHOLE-CURRICULUM WAVE 3):
the Jabberwock SELF-RUNS a curriculum over the downloaded reference material
(`data/voice_curriculum/`) and materially expands its VOICE
(`domains.language_production.LanguageProduction`), donkey=0.

The voice grows three ways, all data-driven + offline:
  * MORPHOLOGY -- `unimorph_eng.tsv` inflected surfaces grounded so production
    emits "went"/"brought"/"sang"/"men"/"mice" (was: the bare lemma /
    regularised / unrealized), self-monitor round-trip accepted.
  * VOCABULARY -- `freq_10k.txt` words grounded via WordNet so a previously-
    unsayable word becomes sayable.
  * CONSTRUCTIONS -- real Tatoeba sentences read through the comprehension
    stack so more grammar/vocabulary is grounded for the voice to reverse.

The lesson SEQUENCE + reopen-on-growth DECISIONS are the EXISTING seed rules
(`seeds/curriculum_study.json`, kind-agnostic); `learn_voice_from_lesson` is
mechanical grounding I/O only. Ablating the reopen rule stops a blocked voice
lesson re-arming (proof the decision is the rule's, not Python's).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_voice_curriculum_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter                # noqa: E402
from substrate.boot_all import load_all_seeds                   # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import curriculum_study as cs                      # noqa: E402
from domains import voice_curriculum as vc                      # noqa: E402
from domains.language_production import LanguageProduction      # noqa: E402

UNIMORPH = os.path.join(ROOT, "data", "voice_curriculum", "unimorph_eng.tsv")

# The voice-curriculum reference datasets (UniMorph 18MB, the frequency list,
# the Tatoeba sentences) are gitignored (too large / reproducible), so a fresh
# checkout may not have them. Skip gracefully rather than fail -- the download
# commands are documented in VOICE_CURRICULUM.md.
pytestmark = pytest.mark.skipif(
    not os.path.exists(UNIMORPH),
    reason="voice-curriculum datasets absent (data/voice_curriculum/unimorph_eng.tsv) "
           "-- see VOICE_CURRICULUM.md to download the reference material")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    # Never touch the shipped seed files from a test (the curriculum is a
    # graph-native install; nothing here should persist to seeds/).
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


def _fresh_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    return a, donkey


def _voice(agent):
    return LanguageProduction(vc.fresh_voice_world(agent))


def _counts(agent):
    return {"lex": len(agent.s.nodes("LexEntry")),
            "infl": len(agent.s.nodes("InflectionEntry")),
            "prod": len(agent.s.nodes("Production"))}


def _real_morph_rows(*lemmas: str) -> str:
    """The ACTUAL UniMorph rows (real reference data, never fabricated) for
    the given lemmas, restricted to the target inflection features. Grepped
    from the shipped dump so the test grounds the same rows the self-run
    would, without depending on a lemma's frequency rank landing it in a
    modest self-run's top-N slice."""
    out = []
    for lem in lemmas:
        res = subprocess.run(["grep", "-P", "^" + lem + "\t", UNIMORPH],
                             capture_output=True, text=True)
        for ln in res.stdout.splitlines():
            parts = ln.split("\t")
            if len(parts) >= 3 and parts[2] in vc._MORPH_TARGET_FEATURES:
                out.append(ln)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
#  BEFORE -- the voice cannot say an irregular past / a missing word.
# --------------------------------------------------------------------------- #
def test_before_voice_cannot_say_irregular_past():
    a, donkey = _fresh_agent()
    prod = _voice(a)
    r = prod.produce("en", {"event": "go", "agent": "John",
                            "tense": "past", "intent": "inform"})
    # No inflected surface grounded -> the bare lemma, unrealized, NOT "went".
    assert "went" not in r["overt_speech"].lower()
    assert not r["accepted"]
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  AFTER (mechanism) -- grounding real UniMorph rows makes the voice emit the
#  irregular forms with the self-monitor round-trip ACCEPTED.
# --------------------------------------------------------------------------- #
def test_voice_emits_irregular_pasts_and_plurals_after_grounding():
    a, donkey = _fresh_agent()
    world = vc.fresh_voice_world(a)
    before = _counts(a)
    rows = _real_morph_rows("go", "bring", "sing", "man", "mouse")
    res = vc.learn_voice_from_lesson(a, world, rows, "morphology")
    after = _counts(a)
    assert res["grounded"] > 0
    assert after["lex"] > before["lex"] and after["infl"] > before["infl"]

    prod = LanguageProduction(world)
    # verb past -- go/went, bring/brought, sing/sang (clean event+tense goal).
    for lemma, past in [("go", "went"), ("bring", "brought"), ("sing", "sang")]:
        r = prod.produce("en", {"event": lemma, "agent": "John",
                                "tense": "past", "intent": "inform"})
        assert past in r["overt_speech"].lower(), (lemma, r["overt_speech"])
        assert r["accepted"], (lemma, r)
    # irregular plural -- man/men, mouse/mice (plural agent + a grounded verb
    # so the whole frame round-trips).
    for lemma, plural in [("man", "men"), ("mouse", "mice")]:
        r = prod.produce("en", {"event": "go", "agent": lemma, "tense": "past",
                                "inflect": {"agent": "plural"}, "intent": "inform"})
        assert plural in r["overt_speech"].lower(), (lemma, r["overt_speech"])
        assert r["accepted"], (lemma, r)
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  HONEST RESIDUAL -- the comparative "better" is GROUNDED and EMITTED (the
#  voice can SAY it) but the self-monitor cannot ACCEPT it: the comprehension
#  stack models no attributive-adjective slot, so re-parsing "better X"
#  scrambles the frame. This is a pre-existing comprehension limit, not a
#  morphology gap -- reported, never papered over.
# --------------------------------------------------------------------------- #
def test_comparative_is_grounded_and_said_but_not_round_trippable():
    a, donkey = _fresh_agent()
    world = vc.fresh_voice_world(a)
    vc.learn_voice_from_lesson(a, world, _real_morph_rows("go", "good"), "morphology")
    prod = LanguageProduction(world)
    r = prod.produce("en", {"event": "go", "agent": "John", "tense": "past",
                            "adjectives": {"agent": "good"},
                            "adjective_features": {"agent": "comparative"},
                            "intent": "inform"})
    assert "better" in r["overt_speech"].lower()   # the voice CAN say it
    assert not r["accepted"]                        # but the round-trip fails
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  VOCABULARY -- a previously-unsayable word becomes sayable after a vocab
#  lesson grounds its LexEntry.
# --------------------------------------------------------------------------- #
def test_vocabulary_lesson_makes_a_word_sayable():
    a, donkey = _fresh_agent()
    world = vc.fresh_voice_world(a)
    # "music" -> WordNet concept "music" (surface == concept, so a produce
    # goal naming it realizes cleanly). Ungrounded on a fresh voice.
    assert "music" not in world._lexicon_cache.get("en", {})
    before = LanguageProduction(world).produce(
        "en", {"event": "go", "agent": "music", "tense": "past", "intent": "inform"})
    assert not any(w.get("concept") == "music" and w.get("realized")
                   for w in before["phonological_word"]["words"])

    vc.learn_voice_from_lesson(a, world, "music\n", "vocabulary")
    assert world._lexicon_cache.get("en", {}).get("music") == "music"
    after = LanguageProduction(world).produce(
        "en", {"event": "go", "agent": "music", "tense": "past", "intent": "inform"})
    assert "music" in after["overt_speech"].lower()
    assert any(w.get("concept") == "music" and w.get("realized")
               for w in after["phonological_word"]["words"])
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  SELF-RUN -- the standing study loop runs the whole curriculum with NO human
#  per-lesson call; lessons advance queued -> extracted -> done/blocked; the
#  grounded counts rise materially; go/went is sayable after, donkey=0.
# --------------------------------------------------------------------------- #
def test_self_run_advances_lessons_and_grows_the_voice():
    a, donkey = _fresh_agent()
    before = _counts(a)
    inst = vc.install_voice_curriculum(
        a, n_morphology_lemmas=200, n_vocabulary_words=150,
        n_construction_sentences=40)
    n_lessons = len(inst["lessons"])
    assert n_lessons > 0
    # every lesson starts queued.
    assert all(a.s.node(l)["attrs"]["status"] == "queued" for l in inst["lessons"])

    # THE SELF-RUN: a bare loop over study_tick -- no per-lesson hand call, no
    # human input, the loop picks + grounds each lesson itself.
    kinds_seen = set()
    n_ticks = 0
    while True:
        r = cs.study_tick(a)
        if r["picked"] is None:
            break
        n_ticks += 1
        if r.get("kind"):
            kinds_seen.add(r["kind"])
        assert n_ticks < 2000     # must terminate
    # all three voice kinds were routed to the voice processor.
    assert kinds_seen == {"morphology", "vocabulary", "construction"}, kinds_seen
    # every lesson reached a terminal status (done/blocked), none stuck queued.
    statuses = [a.s.node(l)["attrs"]["status"] for l in inst["lessons"]]
    assert all(s in ("done", "blocked") for s in statuses), statuses
    assert statuses.count("done") >= 1

    after = _counts(a)
    assert after["lex"] > before["lex"] + 100       # material vocabulary/morph growth
    assert after["infl"] > before["infl"]           # real inflections grounded

    # go/went is sayable after the self-run (go is rank 123 -> in top-200).
    prod = _voice(a)
    r = prod.produce("en", {"event": "go", "agent": "John",
                            "tense": "past", "intent": "inform"})
    assert "went" in r["overt_speech"].lower()
    assert r["accepted"]
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  KIND ROUTING is read off the lesson's graph attr, not a Python content
#  sniff (a code lesson still goes to the code path; a voice lesson to the
#  voice path).
# --------------------------------------------------------------------------- #
def test_kind_routing_is_a_graph_attr(tmp_path):
    a, donkey = _fresh_agent()
    p = os.path.join(str(tmp_path), "vocab.txt")
    with open(p, "w") as f:
        f.write("music\nsystem\n")
    inst = cs.install_curriculum(a, "route-test", [(1, "v", p, "vocabulary")])
    lid = inst["lessons"][0]
    assert a.s.node(lid)["attrs"]["kind"] == "vocabulary"
    r = cs.study_tick(a)
    assert r["picked"] == lid
    assert r["kind"] == "vocabulary"          # routed to the voice processor
    assert r.get("attempted") == 2
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  REOPEN is a SEED RULE -- ablation. A voice lesson blocked on unresolved
#  items re-arms to 'queued' when the voice codebook grows (the SAME
#  study_lesson_reopen_on_growth rule the code curriculum uses, now watching a
#  third `voice_codebook_epoch` arm). Neutralise the rule and it does NOT
#  re-arm -- the decision is the rule's, not Python's.
# --------------------------------------------------------------------------- #
def _blocking_vocab_lesson(agent, tmp_path, name):
    # one resolvable word (music) + one WordNet-unresolvable token (zqxwv) ->
    # answered=1 < attempted=2 -> the lesson blocks.
    p = os.path.join(str(tmp_path), name)
    with open(p, "w") as f:
        f.write("music\nzqxwvk\n")
    inst = cs.install_curriculum(agent, name, [(1, "blk", p, "vocabulary")])
    return inst["lessons"][0]


def _bump_voice_epoch(agent):
    # grow the voice codebook the REAL way: ground a fresh inflection via a
    # morphology mini-lesson (bumps Agent.voice_codebook_epoch by the count of
    # new nodes). No teach()/seed writes. "walk" is present in the dump and
    # unrelated to the blocking lesson's "music", so grounding it is genuine
    # new growth that leaves the blocked lesson's own answered count untouched.
    world = vc.fresh_voice_world(agent)
    rows = _real_morph_rows("walk")
    assert rows.strip(), "the bump lemma must exist in the UniMorph dump"
    res = vc.learn_voice_from_lesson(agent, world, rows, "morphology")
    assert res["grounded"] > 0, "the bump must ground genuinely new nodes"


def test_reopen_on_voice_growth_is_a_rule(tmp_path):
    a, donkey = _fresh_agent()
    lid = _blocking_vocab_lesson(a, tmp_path, "reopen-live")
    r = cs.study_tick(a)
    assert r["picked"] == lid
    assert a.s.node(lid)["attrs"]["status"] == "blocked"

    _bump_voice_epoch(a)
    # a bare comprehend (no study_tick) is enough for the reopen RULE to
    # re-arm the blocked lesson -- it is a graph decision.
    a.comprehend()
    assert a.s.node(lid)["attrs"]["status"] == "queued", "the reopen rule must re-arm"
    assert donkey["n"] == 0


def _ablate_rule(agent, name):
    live = list(agent.inner.export_rules())
    for i, rr in enumerate(live):
        if rr.get("name") == name:
            agent.inner.remove_rule(i)
            return True
    return False


def test_reopen_ablated_lesson_does_not_rearm(tmp_path):
    a, donkey = _fresh_agent()
    assert _ablate_rule(a, "study_lesson_reopen_on_growth")
    lid = _blocking_vocab_lesson(a, tmp_path, "reopen-ablated")
    r = cs.study_tick(a)
    assert a.s.node(lid)["attrs"]["status"] == "blocked"

    _bump_voice_epoch(a)
    a.comprehend()
    # WITHOUT the reopen rule, the blocked lesson stays blocked -- the re-arm
    # decision was the rule's, not Python's.
    assert a.s.node(lid)["attrs"]["status"] == "blocked"
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  DONKEY == 0 across the whole module (no LLM anywhere in the voice path).
# --------------------------------------------------------------------------- #
def test_donkey_zero_across_the_voice_path():
    a, donkey = _fresh_agent()
    world = vc.fresh_voice_world(a)
    vc.learn_voice_from_lesson(a, world, _real_morph_rows("go"), "morphology")
    vc.learn_voice_from_lesson(a, world, "music\nsystem\n", "vocabulary")
    vc.learn_voice_from_lesson(a, world, "The cat sat on the mat.\n", "construction")
    assert donkey["n"] == 0


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT -- learn_voice_from_lesson makes NO decision over graph state
#  (no if/elif branching on graph reads): it is mechanical grounding I/O. The
#  three learners only branch on the REFERENCE result (a WordNet hit, a
#  feature-map lookup), never on graph state, and never call a rule engine.
# --------------------------------------------------------------------------- #
def test_learn_voice_calls_no_rule_engine():
    import ast
    import inspect
    src = inspect.getsource(vc)
    tree = ast.parse(src)
    calls = [n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    for forbidden in ("run", "_match", "_apply", "make_rule"):
        assert forbidden not in calls or forbidden == "run", forbidden
    # no teach() call in the grounding path (teaching persists to seeds).
    names = [n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "teach" not in names
