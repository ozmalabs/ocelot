"""VISION CURRICULUM (Stage 2) — the agent SELF-RUNS a developmental vision
curriculum and grows its own visual codebook.

The shape mirrors `test_voice_curriculum_migrated.py`: install a Curriculum of
real lessons, then drive `curriculum_study.study_tick` in a loop with NO
per-lesson human call and NO teacher, and assert the agent's codebook actually
grew. donkey=0: the source is real BSDS300 photographs on disk; the self-teacher
is asserted never to be called.

SCOPE, STATED HONESTLY. This wave implements the ladder's FIRST level only --
`babble` (L0: grow receptive fields from image statistics). The plan's
remaining levels (tracking / permanence / transform-invariance / composition)
are NOT built, and `learn_vision_from_lesson` reports an unbuilt kind as
attempted=0/answered=0 rather than faking a pass. `test_unbuilt_levels_are_not_
faked` pins that, so a level cannot quietly appear to work before it exists.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
from domains import curriculum_study as cs  # noqa: E402
from domains import vision_curriculum as vis  # noqa: E402
from domains import vision_corpus as vcorp  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_seed_writes(monkeypatch):
    monkeypatch.setenv("OZMA_SEED_PERSIST_DISABLED", "1")


@pytest.fixture(scope="module", autouse=True)
def _need_corpus():
    if len(vcorp.bsds_paths("train")) < 10:
        pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")


def _fresh_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    return a, donkey


def _grown(a):
    return len([k for k in a.s.nodes("Kernel")
                if a.s.node(k)["attrs"].get("grown") == 1.0])


def _agent_node(a):
    return [x for x in a.s.nodes("Agent")
            if not a.s.node(x)["attrs"].get("is_class")][0]


def test_agent_self_runs_the_vision_curriculum_and_grows_its_codebook(tmp_path):
    """THE HEADLINE GATE. BEFORE: the agent holds ZERO grown kernels. Then the
    standing study loop advances every queued lesson autonomously -- no human
    per-lesson call, no teacher. AFTER: the codebook has materially grown, and
    every lesson settled through the EXISTING kind-agnostic lifecycle rules."""
    a, donkey = _fresh_agent()
    plan = vis.prepare_babble_lessons(n_patches=90, chunk=30, source="bsds",
                                      lesson_dir=str(tmp_path))
    assert len(plan) == 3
    cs.install_curriculum(a, "Vision Development", plan, source="test")

    assert _grown(a) == 0, "BEFORE: agent must hold no grown kernels"

    ticks = 0
    kinds = set()
    while True:
        r = cs.study_tick(a)
        if r["picked"] is None:
            break
        ticks += 1
        kinds.add(r.get("kind"))
        assert ticks < 100, "study loop did not terminate"

    assert ticks == 3, f"expected one tick per lesson, got {ticks}"
    assert kinds == {"babble"}
    after = _grown(a)
    assert after > 5, f"AFTER: codebook barely grew ({after} kernels)"
    # Growth was recorded as the agent's own epoch counter, which is what
    # re-arms study_lesson_reopen_on_growth's vision arm.
    ep = a.s.node(_agent_node(a))["attrs"].get("vision_codebook_epoch")
    assert ep and ep > 0, f"vision_codebook_epoch not bumped ({ep})"
    # donkey=0: real photographs on disk, never an LLM.
    assert donkey["n"] == 0, f"the self-teacher was called {donkey['n']}x"

    lessons = [n for n in a.s.nodes("StudyLesson")]
    assert all(a.s.node(n)["attrs"].get("status") in ("done", "blocked")
               for n in lessons)


def test_every_grown_kernel_came_from_image_data_not_a_template(tmp_path):
    """The point of the whole L0 rebuild: a grown kernel's weights come from a
    real image patch (designed:0.0, minted by the rule), never from the six
    hand-designed seed kernels. Those are detached before growth so they cannot
    win the winner-take-all competition and re-plant the answer."""
    a, _d = _fresh_agent()
    plan = vis.prepare_babble_lessons(n_patches=60, chunk=60, source="bsds",
                                      lesson_dir=str(tmp_path))
    cs.install_curriculum(a, "Vision Development", plan, source="test")
    cs.study_tick(a)

    fac = a.s.nodes("ConvFaculty")[0]
    pool = a.s.neighbours(fac, "has_kernel")
    assert pool, "pool empty"
    for k in pool:
        at = a.s.node(k)["attrs"]
        assert at.get("grown") == 1.0, "a designed kernel is still in the pool"
        assert at.get("designed") == 0.0
        assert at.get("source") == "vg_mint_kernel_from_patch"
        assert np.all(np.isfinite(np.array(at["weights"], float)))


def test_lesson_routing_is_by_the_lessons_own_kind_attr(tmp_path):
    """study_tick routes on the lesson's OWN `kind` graph attr -- a mechanical
    read, never a Python sniff of the lesson's content."""
    p = tmp_path / "l.txt"
    p.write_text("# empty babble lesson\n")
    a, _d = _fresh_agent()
    cs.install_curriculum(a, "route-test", [(1, "v", str(p), "babble")])
    r = cs.study_tick(a)
    assert r.get("kind") == "babble"
    assert r["picked"] is not None


def test_unbuilt_levels_are_not_faked():
    """The plan's ladder is L0-L6; this wave built L0 only. An unbuilt level
    must report attempted=0/answered=0 -- never a silent pass that would make
    a level look implemented."""
    assert vis.VISION_KINDS == ("babble",), (
        "VISION_KINDS grew — if a level was implemented, extend this gate; "
        "if not, it must not be routable")
    a, _d = _fresh_agent()
    world = vis.fresh_vision_world(a)
    for unbuilt in ("constancy", "invariance", "composition", "recognition"):
        r = vis.learn_vision_from_lesson(a, world, "whatever", unbuilt)
        assert r["attempted"] == 0 and r["answered"] == 0 and r["grounded"] == 0


def test_reopen_on_vision_growth_is_a_seed_rule_not_python():
    """The reopen DECISION is the existing kind-agnostic seed rule, extended
    with a fourth `vision_codebook_epoch` Or-arm — the same single edit the
    voice wave needed. Python only writes the facts it reads."""
    import json
    with open(os.path.join(ROOT, "seeds", "curriculum_study.json")) as f:
        seed = json.load(f)
    rule = [r for r in seed["rules"]
            if r["name"] == "study_lesson_reopen_on_growth"][0]
    blob = json.dumps(rule)
    assert "vision_codebook_epoch" in blob and "vision_decoded_epoch" in blob
    arms = rule["where"]["items"][1]["items"]
    assert len(arms) == 4, f"expected 4 growth arms, got {len(arms)}"
