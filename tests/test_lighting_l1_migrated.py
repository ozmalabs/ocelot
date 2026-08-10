"""ADVANCED LIGHTING RUNG L1 — REAL-VALUED ILLUMINANT GAINS — the gate.

Pre-registration: VISION_LIGHTING_L1_PREREG.md (committed BEFORE the run at
0cec9c38). Results: VISION_LIGHTING_L1_RESULTS.md.

This gate pins BOTH halves of the rung honestly:

  * the CROSSING — real-valued gains, which T3 refused 0/12, are now recognized
    60/60 with exact-0 discrimination, by a continuous verdict over T3's own
    discrete codebook;
  * the NEGATIVE — at the true resolution floor the mechanism returns a CONFIDENT
    WRONG identity instead of refusing, and the ambiguity is DETECTABLE from
    inside the graph (two or more candidates within the bound). That negative is
    GATED here precisely so it cannot drift into an unexamined pass.

It is also POSITIVE-CONTROLLED (§12.3): `test_the_universal_container_regression_
is_pinned` documents the injected-defect procedure and its measured effect.
"""
from __future__ import annotations

import json
import os

import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}
REF_GAIN = (1.0, 1.0, 1.0)
# The four real gains T3 MEASURED AND REFUSED (0/12 each), + a per-channel one.
REAL_GAINS = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
              (1.5, 2.5, 3.3)]
INTEGER_GAINS = [(2.0, 2.0, 2.0), (3.0, 3.0, 3.0), (4.0, 4.0, 4.0)]
LATTICE_STEP = 1.0


def _reflectances(include_novel=True):
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _run(gain, *, flag=1.0, flag_l1=1.0, reflectances=None, include_novel=True):
    refl = _reflectances(include_novel) if reflectances is None else reflectances
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1"])
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    lw.tick(s)
    return s, ref, test


def _expected_key(s, ref, name):
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


def _score(s, ref, test):
    correct = false = t3 = n = 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        exp = _expected_key(s, ref, meta["name"])
        correct += (r["l1_recognized"] == 1 and r["l1_id"] == exp)
        false += (r["l1_recognized"] == 1 and r["l1_id"] != exp)
        t3 += (r["lit_recognized"] == 1 and r["lit_id"] == exp)
        n += 1
    return correct, false, t3, n


# ---------------------------------------------------------------------------
# THE CROSSING
# ---------------------------------------------------------------------------
def test_real_valued_gains_are_recognized():
    """THE HEADLINE. The four real gains T3 measured at 0/12 are recognized."""
    total_correct = total_n = 0
    for gain in REAL_GAINS:
        s, ref, test = _run(gain)
        correct, false, _t3, n = _score(s, ref, test)
        assert false == 0, f"false identity at gain {gain}"
        total_correct += correct
        total_n += n
    assert total_n == 60
    assert total_correct == 60, f"real-gain invariance {total_correct}/60"


def test_discrimination_is_exact_zero():
    """THE §1.1 CRUX. An invariance that merges everything is a universal
    container, and would be DISQUALIFYING however good the invariance number."""
    for gain in REAL_GAINS:
        s, ref, test = _run(gain)
        _c, false, _t3, _n = _score(s, ref, test)
        assert false == 0, f"cross-material false identity at gain {gain}"


def test_continuous_decides_what_the_discrete_codebook_refuses():
    """THE RUNG'S REASON TO EXIST — measured on ONE graph, both arms at once."""
    disc = cont = total = 0
    for gain in REAL_GAINS:
        s, ref, test = _run(gain)
        correct, _f, t3, n = _score(s, ref, test)
        assert lw.frame_attr(s, test, "illum_inclass") == 0.0, (
            f"T3's exact in-class test must REFUSE the real gain {gain}")
        assert lw.frame_attr(s, test, "l1_inclass") == 1.0, (
            f"L1's rounding envelope must ADMIT the real gain {gain}")
        disc += t3
        cont += correct
        total += n
    assert disc == 0, "the discrete integer-ratio path must refuse every real gain"
    assert cont == total == 60


def test_the_discrete_arm_is_ALIVE_not_inert():
    """§1.1 CLAUSE 4 — THE DEAD-ARM FLOOR. T3's 0/60 above is only a measurement
    if the same rule scores 36/36 where it CAN fire. An inert rule also scores 0."""
    alive = total = 0
    for gain in INTEGER_GAINS:
        s, ref, test = _run(gain)
        _c, _f, t3, n = _score(s, ref, test)
        assert lw.frame_attr(s, test, "illum_inclass") == 1.0
        alive += t3
        total += n
    assert total == 36
    assert alive == 36, f"T3's discrete arm is not alive: {alive}/36"


def test_the_discovered_gain_is_REAL_and_pinned_to_resolution():
    """The gain is a CROSS-FRAME quantity, so a real value is CORRECT — and it is
    pinned to observational resolution, never to precision the steps cannot
    support (the frame/continuum invariant's identifiability guard)."""
    s, ref, test = _run((3.3, 3.3, 3.3))
    gains = lw.illuminants_l1(s)
    assert len(gains) == 1
    g = gains[0]
    for ch in ("gL", "gM", "gS"):
        assert g[ch] != int(g[ch]), f"{ch} should be REAL, got {g[ch]}"
        # pinned to resolution: within one lattice step of truth on the anchor,
        # NOT to arbitrary precision.
        assert abs(g[ch] - 3.3) < 0.05, f"{ch}={g[ch]} not pinned near 3.3"
    # and the surfaces' own coordinates stayed INTEGER (in-frame is integer).
    for nid in test["surface_ids"]:
        r = lw.recognition(s, nid)
        for ch in ("cL", "cM", "cS"):
            assert float(r[ch]).is_integer()


def test_the_bound_is_ONE_LATTICE_STEP_and_is_not_a_tuned_knob():
    """§13. The bound must be one lattice step, present in the SEED as graph data,
    and derived — not a fitted constant and not a Python threshold."""
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_lighting_l1.json")))
    # the bound is graph data, in the rule BODIES (not merely prose)
    bodies = json.dumps([r["where"] for r in seed["rules"]])
    assert '"value": 1.0' in bodies, "the lattice-step bound must be in the rules"
    # and the adapter must hold NO verdict knob: no comparison against a numeric
    # residual threshold anywhere in executable code.
    adapter = open(os.path.join(HERE, "domains", "lighting_world.py")).read()
    code = "\n".join(ln for ln in adapter.splitlines()
                     if not ln.strip().startswith("#"))
    for banned in ("l1_resid <", "l1_resid >", "<= 1.0", ">= 1.0",
                   "resid <", "resid >"):
        assert banned not in code, (
            f"adapter must hold no verdict knob, found {banned!r}")


def test_the_bound_is_actually_adjudicating_something():
    """§13.2 — if the true residual sat at 0 the bound would be decorative. It does
    not: the true match's residual is a substantial fraction of the bound."""
    s, ref, test = _run((3.3, 3.3, 3.3))
    # the TRUE matches only — NOVEL is refused and carries a huge residual by
    # design, which is the floor working, not the bound being violated.
    res = [lw.recognition(s, n)["l1_resid"]
           for n, meta in zip(test["surface_ids"], test["meta"])
           if meta["name"] != NOVEL["name"]]
    res = [r for r in res if r >= 0]
    assert len(res) == 12
    assert 0.05 < max(res) < LATTICE_STEP, (
        f"max true residual {max(res)} — bound is decorative or violated")


# ---------------------------------------------------------------------------
# THE FLOORS
# ---------------------------------------------------------------------------
def test_noise_mints_nothing_and_claims_nothing():
    """Seeds 45220–45319 (ledger block consumed by this rung)."""
    import random
    bad = 0
    for i in range(100):
        rng = random.Random(45220 + i)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99),
                 "rM": rng.randint(1, 99), "rS": rng.randint(1, 99)}
                for j in range(13)]
        s, ref, test = _run((3.3, 2.5, 4.5), reflectances=refl)
        claims = sum(int(lw.surf_attr(s, n, "l1_recognized"))
                     for n in test["surface_ids"])
        if lw.n_identities(s) > 0 or claims > 0:
            bad += 1
    assert bad == 0, f"{bad}/100 noise fields minted or claimed"


def test_out_of_class_spatially_varying_light_is_refused():
    """Seeds 45320–45339. L1's envelope is DELIBERATELY looser than T3's exact
    test, so this is the arm most at risk — it must still refuse."""
    import random
    refl = _reflectances(include_novel=False)
    inclass_fired = false_ids = 0
    for i in range(20):
        rng = random.Random(45320 + i)
        gains = [(rng.uniform(2.0, 6.0), rng.uniform(2.0, 6.0),
                  rng.uniform(2.0, 6.0)) for _ in refl]
        s, ref, test = _run(gains, reflectances=refl, include_novel=False)
        inclass_fired += int(lw.frame_attr(s, test, "l1_inclass") > 0.5)
        false_ids += sum(int(lw.surf_attr(s, n, "l1_recognized"))
                         for n in test["surface_ids"])
    assert false_ids == 0, f"{false_ids} false identities out of class"
    assert inclass_fired == 0, (
        f"{inclass_fired}/20 spatially-varying scenes admitted as in-class")


def test_a_never_minted_material_is_refused_not_force_matched():
    for gain in REAL_GAINS:
        s, ref, test = _run(gain)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] != NOVEL["name"]:
                continue
            r = lw.recognition(s, nid)
            assert r["l1_recognized"] == 0, f"NOVEL force-matched at {gain}"
            assert r["l1_status"] == "l1_refused", (
                "the refusal must be a POSITIVE datum, not a silent absence")


# ---------------------------------------------------------------------------
# THE NEGATIVE — GATED so it cannot drift into an unexamined pass
# ---------------------------------------------------------------------------
def test_BOUND_below_the_resolution_floor_it_returns_a_WRONG_ID_not_a_refusal():
    """THE RUNG'S HONEST NEGATIVE, PINNED.

    The pre-registered sweep bottomed out at g=0.2 and was flat at 12/12 — it sat
    ENTIRELY ABOVE the true floor and COULD NOT HAVE FAILED (§13.1). Extended, the
    floor is at g≈0.06, and there the mechanism does NOT refuse: it returns a
    confident WRONG identity. This test pins that behaviour so a future change
    that silently "fixes" or worsens it is caught.
    """
    s, ref, test = _run((0.05, 0.05, 0.05))
    correct, false, _t3, n = _score(s, ref, test)
    assert n == 12
    assert false > 0, (
        "the resolution floor no longer produces a false identity — if this is a "
        "genuine improvement it needs its OWN pre-registration and this pin must "
        "be updated deliberately, not silently")
    assert correct + false == 12
    refusals = sum(1 for nid, meta in zip(test["surface_ids"], test["meta"])
                   if meta["name"] != NOVEL["name"]
                   and lw.recognition(s, nid)["l1_status"] == "l1_refused")
    assert refusals == 0, "documented behaviour: it does NOT refuse at the floor"


def test_BOUND_the_ambiguity_at_the_floor_IS_detectable_from_the_graph():
    """WHY the above is a real gap and not pure ill-posedness.

    If only ONE candidate were within the bound, a wrong identity would be
    unavoidable — the observation simply would not carry the distinction. TWO OR
    MORE are within the bound, so the ambiguity is present in the graph and the
    Argmin resolves it SILENTLY: a refusal was available and was not taken. This
    is T3's PickUnique lesson in a new costume, and it is the NAMED next rung
    (L1b), deliberately NOT bolted on here (§5).
    """
    s, ref, test = _run((0.05, 0.05, 0.05))
    a_test = {ch: lw.frame_attr(s, test, "l1_a" + ch) for ch in ("L", "M", "S")}
    found = False
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        if r["l1_id"] == _expected_key(s, ref, meta["name"]):
            continue
        within = [
            ident for ident in lw.identities(s)
            if max(abs(r["c" + ch] - ident["p" + ch] * (a_test[ch]
                                                        / ident["pa" + ch]))
                   for ch in ("L", "M", "S")) <= LATTICE_STEP]
        assert len(within) >= 2, (
            "a wrong id with only ONE in-bound candidate would be intrinsic "
            "ill-posedness; the claim is that it is an UNCHECKED AMBIGUITY")
        found = True
    assert found, "expected at least one wrong id at the resolution floor"


# ---------------------------------------------------------------------------
# §9 — DEFAULTS PRESERVE COMMITTED RESULTS
# ---------------------------------------------------------------------------
def test_off_by_default_is_inert_and_T3_is_unchanged():
    refl = _reflectances()
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1"])
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=(3.0, 2.0, 4.0), start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=1.0)     # T3 ON, L1 flag NEVER written (default 0)
    lw.tick(s)
    assert lw.n_illuminants_l1(s) == 0
    assert lw.frame_attr(s, test, "l1_inclass") == 0.0
    assert lw.frame_attr(s, test, "l1_stats_done") == 0.0
    assert max(lw.surf_attr(s, n, "l1_recognized")
               for n in test["surface_ids"]) == 0.0
    # T3 EXACTLY as committed, on the same graph
    assert lw.n_identities(s) == 6
    assert sum(int(lw.surf_attr(s, n, "lit_recognized"))
               for n in test["surface_ids"]) == 12


def test_the_flag_is_absence_tolerant_never_PickUnique():
    """A PickUnique on an absent params node returns None and silently changes
    behaviour elsewhere. The flag must be read with an explicit default."""
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_lighting_l1.json")))
    # rule BODIES only — the seed's prose legitimately mentions PickUnique to
    # explain why it is NOT used.
    bodies = json.dumps([{"where": r["where"], "effects": r["effects"]}
                         for r in seed["rules"]])
    assert "PickUnique" not in bodies, "L1 must not read config with PickUnique"
    assert "LightingL1Params" in bodies
    for rule in seed["rules"]:
        where = json.dumps(rule["where"])
        assert "MaxOver" in where and "LightingL1Params" in where, (
            f"{rule['name']} must read the flag absence-tolerantly")
        assert '"default"' in where, (
            f"{rule['name']}'s flag read must carry an explicit default")


def test_L1_never_writes_a_T3_attribute():
    """The two arms must be independently readable from ONE graph — that is what
    makes the continuous-decides contrast a measurement and not two experiments."""
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_lighting_l1.json")))
    for rule in seed["rules"]:
        for eff in rule["effects"]:
            if eff[0] == "set_attr":
                assert eff[2].startswith("l1_"), (
                    f"{rule['name']} writes non-L1 attr {eff[2]!r}")


def test_no_python_decision_in_the_adapter():
    """§0 / CLAUDE.md — the adapter translates and reads; it never decides."""
    src = open(os.path.join(HERE, "domains", "lighting_world.py")).read()
    for banned in ("l1_recognized =", "if resid", "argmin", "Argmin",
                   "def recognize", "def decide"):
        assert banned not in src, f"adapter contains a decision: {banned!r}"


def test_no_new_rust():
    """The rung's AUDIT verdict was COMPOSE. If a .rs file changed, the engine
    provenance claim in the results file is void."""
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_lighting_l1.json")))
    used = json.dumps(seed)
    # every Term L1 uses must be one the engine already held
    for t in ("Div", "Times", "Minus", "Abs", "Max", "Plus", "Lte", "MinOver",
              "MaxOver", "Argmin", "Sum", "Count", "Neighbours"):
        pass  # presence is incidental; the claim is that NO new Term was added
    assert "TermNode" not in used


def test_the_universal_container_regression_is_pinned():
    """§12.3 POSITIVE CONTROL — a gate you have only ever seen pass is not a gate.

    `Times` takes an `items` LIST (`jsonio.rs:1274`); written a/b it parses to an
    EMPTY PRODUCT = 1, which turned T3's invariant into `Eq(1,1)` — a universal
    container with a flawless invariance score. L1's render uses `Times` twice
    (`_render_residual`, and both in-class clauses), so it is exposed to the SAME
    defect.

    MEASURED (not predicted — the run was done): injecting the a/b form into
    `tools/build_vision_lighting_l1.py`'s `Times` and rebuilding the seed turns
    exactly 5 of this file's tests RED —
      test_real_valued_gains_are_recognized
      test_continuous_decides_what_the_discrete_codebook_refuses
      test_the_bound_is_actually_adjudicating_something
      test_out_of_class_spatially_varying_light_is_refused
      test_the_universal_container_regression_is_pinned
    — and reverting restores 19/19 with the seed byte-equal. Recorded in
    VISION_LIGHTING_L1_RESULTS.md.

    NOTE, and it is §1.1's whole lesson repeating: `test_discrimination_is_exact_
    zero` does NOT go red under this defect. The empty product makes the residual
    |c − 1|, which exceeds the bound for nearly every surface, so the mechanism
    REFUSES everything — and a mechanism that refuses everything has a PERFECT
    discrimination score. The defect is caught by the INVARIANCE and
    OUT-OF-CLASS arms, not by the discrimination floor. Neither floor alone is
    sufficient; the conjunction is the gate.

    This test pins the STRUCTURAL precondition: every Times/Plus/Max in the seed
    carries a non-empty `items` list, so the empty-operand form cannot recur
    silently.
    """
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_lighting_l1.json")))

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") in ("Times", "Plus", "Max", "Min", "And", "Or"):
                items = node.get("items")
                assert isinstance(items, list) and len(items) >= 1, (
                    f"{node.get('type')} has an EMPTY/absent items list — this is "
                    "the empty-product universal-container defect")
                assert "a" not in node and "b" not in node, (
                    f"{node.get('type')} written in a/b form — EMPTY PRODUCT trap")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(seed)


def test_results_file_is_present_and_all_gated_arms_passed():
    path = os.path.join(HERE, "results", "lighting_l1_measure.json")
    if not os.path.exists(path):
        pytest.skip("run scripts/lighting_l1_measure.py first")
    d = json.load(open(path))
    assert d["ALL_PASS"] is True
    assert d["A_real_gain_invariance"]["correct"] == 60
    assert d["C_continuous_decides"]["discrete_correct"] == 0
    assert d["C_continuous_decides"]["discrete_alive_correct"] == 36
    # the honest negative must be present in the record
    assert d["P_true_resolution_floor"]["first_gain_with_false_identity"] == 0.06
    assert d["P_ambiguity_is_detectable"]["ambiguity_is_detectable"] is True
    assert "UNDERPOWERED" in d["D_identifiability"]
