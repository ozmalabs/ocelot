"""Gates for block 208000 — MODULATOR-DRIVEN DOOM AGENT THAT NARRATES ITS
EMOTIONS. Fuses 205000 active exploration with 207000 emergent-emotion regions:
live play observables feed the drive system, the modulators shift, a 207000
region fires an emotion, and the agent narrates it via a template lexicon.

The emotion is the GRAPH'S (an emergent 207000 region); the wording is a lexicon.
No Python / new seed rule writes a hit_*/emotion attr. NO Rust.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

import scripts.doom_emotion_narration_report as REP          # noqa: E402
import scripts.modulator_emergence_measure as M              # noqa: E402
from substrate.seed_loader import manifest_for               # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "doom_emotion_narration.json")


# ---- ensure the seed is present (emit if a fresh worktree) ----
@pytest.fixture(scope="module", autouse=True)
def _seed():
    if not os.path.exists(SEED_PATH):
        import scripts.build_doom_emotion_narration_seed as B
        B.main()
    return json.load(open(SEED_PATH))


# ---- a unit rig: one config -> exactly one 207000 region, via play_fed drive ----
def _emotion_for(**ev):
    eye, inner = M._eye(load_authored=False)
    inner.load_seed_manifest(json.load(open(SEED_PATH)), eye._agent)
    hub, ms = M._hub_ms(eye, inner, residual_thresh=7)
    over = dict(play_fed=1, novel_hi=8, ev_novel=0, ev_arrived=0, ev_switched=0,
                ev_committed=0, ev_unreach=0, now_epoch=0, last_tend=0)
    over.update(ev)
    d = M._drive(eye, inner, ms, **over)
    # two-pass settle (regions are sticky): converge, clear read-off, fire once
    inner.run_rules()
    for k in (["hit_" + n for n in ("surprise", "fear", "anxiety", "anger",
              "frustration", "disgust", "joy", "sadness", "curiosity", "boredom",
              "fulfilment", "bliss", "angst", "grief")]
              + ["emotion", "action_tendency", "n_fired", "n_blend"]):
        inner.set_attr(ms, k, 0.0)
    inner.run_rules()
    a = dict(M._ms_attrs(eye, ms))
    fired = M._fired_all(eye, ms)
    eye.stop()
    return fired, int(a["emotion"]), int(a["n_fired"]), int(a["arousal_band"])


# ============================ G-emerge (headline) ==========================
# Each raw-observable configuration lands in EXACTLY ONE 207000 region — the six
# exploration emotions PLUS joy (a coverage-achievement milestone) and sadness
# (an un-re-groundable frontier), the two that the connected-map episode does not
# exercise live but which are WIRED and here proven synthetically.
CONFIGS = {
    "surprise":    (dict(ev_novel=11),                                 1, 2),   # HIGH? band irrelevant, appraised=0
    "curiosity":   (dict(ev_novel=3),                                  9, 1),
    "frustration": (dict(ev_novel=0, ev_committed=1),                  5, 2),   # HIGH arousal
    "boredom":     (dict(ev_novel=0, ev_switched=1, ev_committed=1),  10, 0),   # LOW arousal
    "joy":         (dict(ev_arrived=1),                                7, 1),
    "sadness":     (dict(ev_unreach=1),                                8, 0),
    "neutral":     (dict(ev_novel=0),                                  0, 0),
}


@pytest.mark.parametrize("name", list(CONFIGS))
def test_each_config_fires_exactly_one_intended_region(name):
    ev, exp_code, exp_band = CONFIGS[name]
    fired, code, nfired, band = _emotion_for(**ev)
    if name == "neutral":
        assert fired == [] and code == 0 and nfired == 0
    else:
        assert fired == [name], f"{name}: fired {fired}"
        assert code == exp_code and nfired == 1
        if name in ("frustration", "boredom"):
            assert band == exp_band     # the graph's arousal BAND discriminates


# ============================ the live episode ============================
@pytest.fixture(scope="module")
def episode():
    import scripts.doom_emotion_narration_run as RUN
    return RUN.run_episode(budget=60, view_radius=5)


def test_g_emerge_chain_fires_from_live_play(episode):
    """Over a real 205000 play episode the emotion at each tick is produced by
    the 207000 regions from live drive/modulator state; exactly one region per
    non-neutral tick; the ladder config always yields its intended emotion."""
    tr = episode["trace"]
    gt = REP.g_track(tr)
    assert gt["one_fire_each"]
    assert gt["no_cfg_emotion_mismatch"]
    non_neutral = sum(v for k, v in gt["distribution"].items() if k != "neutral")
    assert non_neutral > 0
    # the exploration palette actually EMERGES from real play (not scripted)
    assert {"surprise", "curiosity", "frustration"} <= set(gt["distribution"])


def test_g_track_alignment_and_graph_discriminator(episode):
    """Emotions TRACK play events (confusion diagonal, agreement >= 0.90), and
    the frustration(HIGH)/boredom(LOW) split is the GRAPH's arousal band."""
    gt = REP.g_track(episode["trace"])
    assert gt["agreement_frac"] >= 0.90
    disc = gt["discriminator"]
    if disc["frustration_band"] and disc["boredom_band"]:
        assert disc["frustration_band"] == ["HIGH"]
        assert disc["boredom_band"] == ["LOW"]
        assert disc["discriminator_is_graph_band"]


def test_play_is_byte_identical_to_205000_curiosity(episode):
    """The emotion layer is an orthogonal consumer: coverage matches the 205000
    curiosity arm exactly (60-tick budget -> 307 cells)."""
    assert episode["final_coverage"] == 307


def test_narration_transcript_present(episode):
    tr = episode["trace"]
    narrated = [r["narration"] for r in tr if r["narration"]]
    assert len(narrated) > 0
    # every narration is a template read-off carrying the fired emotion name
    for r in tr:
        if r["narration"]:
            assert r["emotion"] in r["narration"]
            assert r["tendency"] in r["narration"]


# ============================ source / discipline audits ============================
def test_g_emerge_source_audit():
    ge = REP.g_emerge_audit()
    assert ge["one_new_rule"]
    assert ge["new_seed_rule_writes_no_hit_or_emotion"]
    assert ge["python_never_writes_emotion"]
    assert ge["depends_on_207000"]


def test_g_narrate_read_off_audit():
    gn = REP.g_narrate_audit()
    assert gn["no_forbidden_engine_call"]
    assert gn["lexicon_is_graph_data"]
    assert set(gn["lexicon_codes"]) == {1, 5, 7, 8, 9, 10}


def test_integer_native_and_canonical_so_untouched():
    gd = REP.g_discipline()
    assert gd["integer_native"], gd["seed_terms"]
    assert gd["canonical_untouched"], gd["canonical_so_md5"]


def test_term_rs_and_runners_dsl_diff_empty():
    """208000 adds NO Rust: the whole runners/dsl tree is unchanged vs main."""
    import subprocess
    out = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "runners/dsl"],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    assert out == "", f"runners/dsl changed:\n{out}"


def test_207000_canonical_table_unchanged_with_208_loaded():
    """Default-OFF: with the 208000 seed ALSO loaded, the 207000 canonical
    emergence table reproduces byte-identically (dem_drive_feed is inert without
    a play_fed drive)."""
    doff = REP.default_off_207000()
    assert doff["all_207000_cases_unchanged"], doff["rows"]


def test_default_off_no_emotion_nodes_without_opt_in():
    """Loading the seed creates NO ModulatorState / EmotionHub by default; the
    emotion path exists only on explicit adapter opt-in."""
    eye, inner = M._eye(load_authored=False)
    inner.load_seed_manifest(json.load(open(SEED_PATH)), eye._agent)
    n_ms = len(eye.substrate.nodes("ModulatorState"))
    n_hub = len(eye.substrate.nodes("EmotionHub"))
    # the lexicon nodes DO load (they are inert data), but no live emotion state
    n_lex = len(eye.substrate.nodes("EmotionNarration"))
    eye.stop()
    assert n_ms == 0 and n_hub == 0
    assert n_lex == 6
