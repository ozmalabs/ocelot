"""BLOCK 247000 -- BIGVILLE: KNOWN LAWS + IN-GAME ENFORCEMENT gate.

Laws are FIRST-CLASS graph objects inhabitants HOLD; a violation is WITNESSED
(occlusion-gated); enforcement is an AGENT's decision by rule (subject to its own
motivation); Mary's counter runs THROUGH a lawful removal process. Gate-verified
with FAILING controls -- nothing scripted, no Python decides an enforcement
outcome, no Rust. Deterministic / categorical. See BIGVILLE_LAW_PREREG.md.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.engine_provenance import engine_preamble, engine_provenance  # noqa: E402
engine_preamble()

from worlds.bigville_law_world import BigvilleLawWorld    # noqa: E402

T = 20


def _out(**kw):
    w = BigvilleLawWorld(**kw)
    w.run(T=T)
    o = w.outcome()
    w.close()
    return o


# ---------------- G-law-known ----------------
def test_laws_are_graph_objects_inhabitants_hold():
    """The prohibition + removal laws are graph NODES the inhabitants HOLD
    (knows_law edges) -- not a hardcoded world constraint. John holds the very
    law he can break; Mary holds the removal law she invokes."""
    o = _out()
    codes = {l["code"] for l in o["law"]["laws"]}
    assert codes == {"PROHIBIT_OFFICE_HARM", "OFFICE_REMOVAL"}, codes
    assert "PROHIBIT_OFFICE_HARM" in o["law"]["laws_known_by"]["John"]
    assert "OFFICE_REMOVAL" in o["law"]["laws_known_by"]["Mary"]
    # every citizen holds the laws too (they are KNOWN, village-wide)
    for i in range(5):
        held = o["law"]["laws_known_by"]["villager_%d" % i]
        assert "PROHIBIT_OFFICE_HARM" in held and "OFFICE_REMOVAL" in held, held


# ---------------- G-enforcement-in-game ----------------
def test_violation_detected_and_consequence_applied_by_rule():
    """A witnessing enforcer DETECTS the violation (bl_detect_violation) and the
    consequence (a censure on the Office) is applied by the enforcer's RULE
    (bl_enforce) -- an in-graph state change, no external referee."""
    o = _out()
    assert o["n_violations"] == 1, o["n_violations"]
    assert o["enforced"] is True and o["censures"] == 1, o
    assert o["law"]["violations"][0]["act"] == "office_harm"
    assert o["law"]["violations"][0]["law_code"] == "PROHIBIT_OFFICE_HARM"


# ---------------- G-occlusion-limits-enforcement (HEADLINE) ----------------
def test_enforcement_flips_with_occlusion_alone():
    """THE HEADLINE + FAILING CONTROL: John schemes every tick in BOTH arms; the
    ONLY change is the constable's line-of-sight. An OCCLUDED (unwitnessed)
    violation is NEVER enforced; the SAME violation moved into the enforcer's LOS
    IS enforced. Enforcement flips with occlusion alone."""
    witnessed = _out(constable_sees_office=True)
    occluded = _out(constable_sees_office=False)
    # John's behaviour is identical across the two arms
    assert witnessed["john_scheme_rate"] == occluded["john_scheme_rate"] == 1.0
    # witnessed -> detected + enforced; occluded -> nothing
    assert witnessed["n_violations"] == 1 and witnessed["enforced"] is True
    assert witnessed["censures"] == 1
    assert occluded["n_violations"] == 0 and occluded["enforced"] is False
    assert occluded["censures"] == 0
    assert occluded["law"]["constable"]["witnessed_harm"] == 0


# ---------------- G-captured-enforcer ----------------
def test_captured_enforcer_declines_impartial_enforces():
    """A captured enforcer (John holds the lever: loyalty_to_john > duty) DECLINES
    to enforce against John EVEN WHEN it witnesses the violation -> the violation
    persists, no censure. An impartial enforcer enforces. The two arms differ by
    the enforcer's held motivation ONLY (both witness)."""
    impartial = _out(constable_captured=False)
    captured = _out(constable_captured=True)
    assert captured["n_violations"] == 1, captured           # it DID witness
    assert captured["declined"] is True and captured["enforced"] is False
    assert captured["censures"] == 0                          # violation persists un-censured
    assert impartial["enforced"] is True and impartial["censures"] == 1
    assert impartial["enforced"] != captured["enforced"]


# ---------------- G-lawful-counter ----------------
def test_mary_counter_runs_through_the_lawful_removal_process():
    """Mary's reduce_office_hold goal acts THROUGH the removal law: she files a
    RemovalMotion citing it, and the Council removes John via that motion + an
    impartial council + a believing quorum. Controls: with NO removal law she can
    file no motion (no extra-legal removal); with a CAPTURED council the motion
    stalls."""
    lawful = _out(deception=False)                            # electorate backs Mary
    no_law = _out(deception=False, mary_knows_removal_law=False)
    capt_council = _out(deception=False, council_impartial=False)
    # the counter succeeds THROUGH the law
    assert lawful["n_motions"] == 1 and lawful["lawfully_removed"] is True
    assert lawful["removed"] == 1 and lawful["office_hold"] == 0
    assert lawful["law"]["removal_motions"][0]["law_code"] == "OFFICE_REMOVAL"
    assert lawful["law"]["removal_outcomes"][0]["lawful"] == 1
    # control: no lawful instrument -> no motion -> no removal
    assert no_law["n_motions"] == 0 and no_law["removed"] == 0 and no_law["office_hold"] == 1
    # control: captured council -> motion filed but removal blocked
    assert capt_council["n_motions"] == 1 and capt_council["removed"] == 0
    assert capt_council["office_hold"] == 1


def test_credibility_asymmetry_gates_the_lawful_counter():
    """Bonus (the credibility layer binds the lawful counter): under John's
    charming public face the accusation lacks quorum, so the lawful removal FAILS
    even though the motion is filed; collapsing the deception lets the electorate
    back Mary and the SAME council process removes him."""
    deception = _out(deception=True)
    no_deception = _out(deception=False)
    assert deception["n_motions"] == 1 and deception["lawfully_removed"] is False
    assert no_deception["lawfully_removed"] is True
    assert no_deception["law"]["backs_mary_count"] > deception["law"]["backs_mary_count"]


# ---------------- G-discipline ----------------
def test_glass_box_source_audit_no_python_decision_no_referee():
    """The world adapter runs NO python rule engine and mints NO rule; there is no
    external referee and no reward/shaping token. The enforcement DECISION lives
    only in the seed rules."""
    src = open(os.path.join(ROOT, "worlds", "bigville_law_world.py")).read()
    for p in ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
              "make_rule(", "graph_rewrite("]:
        assert p not in src, p
    for tok in ["reward_signal", "punish", "reinforce", "backprop", "gradient", "referee"]:
        assert tok not in src, tok


def test_seed_is_integer_native_and_self_load_only():
    seed = json.load(open(os.path.join(ROOT, "seeds", "bigville_laws_enforcement.json")))
    assert seed.get("self_load_only") is True and seed.get("depends_on") == []
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == []
    assert [r["name"] for r in seed["rules"]] == [
        "bl_detect_violation", "bl_enforce", "bl_decline",
        "bl_mary_files_motion", "bl_council_removes"]


def test_new_seed_is_isolated_not_in_full_boot():
    """bigville_laws_enforcement is self_load_only: load_all_seeds must NOT load
    it (additive, isolated, in nobody's fixed path)."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "bigville_laws_enforcement" not in seeds


def test_engine_is_this_worktrees_own_build():
    """Provenance discipline: the measuring engine is THIS worktree's own build."""
    p = engine_provenance()
    assert p["source_match"] == "own", p["source_match"]
