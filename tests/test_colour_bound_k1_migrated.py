"""Gate for THE k=1 HOLE IN THE COLOUR REFUSAL BOUND
(VISION_COLOUR_BOUND_K1_PREREG.md / VISION_COLOUR_BOUND_K1_RESULTS.md).

PART A is a NEGATIVE: no finite k=1 bound falls out, and none CAN — the packing
radius is non-increasing under codebook growth, so the k=1 radius upper-bounds every
radius reachable by growth, and that supremum is unbounded. This gate pins the
derivation, the five rejected rivals, and the caveat that ships with the flip.

THE CONJUNCTION IS THE GATE (process rule 5). The landed rung MEASURED that a
refuse-everything build leaves the refusal/ambiguity/floor arms GREEN. So the arms
that can catch it here are `test_NOREG_*` (which now includes the k=1 field) and
`test_DISAGREE_*` (pointwise agreement, non-degenerate both ways at k>=2). Both are
positive-controlled in the results file against injected defects.
"""
from __future__ import annotations

import json
import math
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_SHA = "41a3158c"          # base `main` HEAD this rung branched from (§11)
RUNG_SHA = "bb548ac3"          # this rung's own commit — BASE_SHA..RUNG_SHA is immutable,
                               # so the provenance claims stay true regardless of what
                               # merges on top afterwards (§12.3)

from scripts.colour_bound_k1_measure import (  # noqa: E402
    arm_A, arm_MONO, arm_NONLOCAL, arm_UNDEF, arm_EXTENT, arm_NOREG,
    arm_DISAGREE, arm_FLOOR, delta_on_flipped, _r3_bound, _r4_gap,
    _seed_default_bound, SEEDS_DISAGREE, SEEDS_FLOOR,
)


# --- PART A: the derivation ----------------------------------------------------
def test_A_the_k1_hole_is_REAL_on_the_ARMED_build():
    """RISKED, the premise. With the bound ARMED and a single-quantum codebook, a
    probe 276 units away is STILL admitted. If this passed, there would be no hole."""
    a = arm_A()
    assert a["PASS"], a
    assert a["k"] == 1
    assert a["packing_radius"] == {"(0, 0)": None}      # undefined at k=1
    assert a["probe"]["ci_refused"] == 0.0              # ADMITTED
    assert a["probe_dist"] == pytest.approx(276.4797, abs=1e-3)


def test_MONO_the_packing_radius_is_NON_INCREASING_under_codebook_growth():
    """THE DERIVATION (§13). `r_i(S') <= r_i(S)` for `S` subset `S'`, because a min
    over a superset cannot increase. Measured along a growth chain: undefined -> 50.0
    -> 10.0."""
    m = arm_MONO()
    assert m["PASS"], m
    assert m["radii_of_c1"] == [None, 50.0, 10.0]
    assert m["monotone_non_increasing"] is True
    assert m["k1_radius_is_undefined"] is True


def test_MONO_every_FINITE_k1_candidate_is_EXCEEDED_by_an_exhibited_extension():
    """Why NO finite k=1 bound can be consistent: for any candidate `r0`, place a
    second prototype at `4*r0+1` and the packing radius becomes `2*r0+0.5 > r0`. The
    k=1 radius must upper-bound every reachable radius, and that supremum is
    UNBOUNDED — so `r(k=1) = +inf` (admit everything) is this derivation's OWN LIMIT,
    not a missing piece."""
    m = arm_MONO()
    assert m["all_finite_candidates_exceeded"] is True
    # the four candidates the rival audit puts forward, each killed by construction
    for r0 in ("0.0", "0.7071", "1.0", "138.24"):
        row = m["finite_candidates_exceeded"][r0]
        assert row["exceeds_candidate"] is True, (r0, row)
        assert row["extension_radius"] > float(r0)


def test_MONO_the_GRAPH_shows_the_shrink_not_merely_the_algebra():
    """§13.2 / §1 clause 5: the seed's OWN decision must move, not just my Python
    re-derivation. The SAME probe is admitted at k=1 and refused at k=3."""
    m = arm_MONO()
    assert m["graph_k1_admits"] == 1
    assert m["graph_k3_refuses"] == 1
    assert m["graph_shows_the_shrink"] is True


# --- PART A: the rivals, rejected ----------------------------------------------
def test_R1_the_mint_has_ZERO_intrinsic_extent_the_structural_root():
    """ENTAILED (§13.1), reported NOT banked: `ci_mint_category` clusters by EXACT
    value, so every member sits at distance 0. This is the ROOT of the null — every
    length scale in this seed lives BETWEEN prototypes, and at k=1 there is no
    between."""
    e = arm_EXTENT()
    assert e["max_cluster_extent"] == 0.0
    assert e["ENTAILED_not_banked"] is True
    assert len(e["per_scene"]) == 5


def test_R1prime_the_sqrt2_over_2_floor_is_INDISTINGUISHABLE_from_zero():
    """The observational-resolution floor is not an independent candidate: every
    observed opponent coordinate is an INTEGER, so no probe can ever lie in the open
    interval (0, sqrt(2)/2) where it would differ from a bound of 0."""
    u = arm_UNDEF()
    assert u["integer_opponent_coords"] == "100/100"
    assert u["r1prime_sqrt2_over_2_indistinguishable_from_0"] is True


def test_R3_the_scene_dynamic_range_DEGENERATES_at_k1():
    """T3's anchor idiom ("the frame's own measured ceiling") is 0.0 in BOTH landed
    k=1 scenes — it collapses to R1 exactly where the hole is."""
    n = arm_NONLOCAL()
    assert n["PASS"], n
    assert n["r3_degenerates_to_zero_at_k1"] is True
    for name in ("achromatopsia_SPLIT_CLEAN", "achromatopsia_FLOOR"):
        row = n["r3_on_landed_k1_scenes"][name]
        assert row["k"] == 1 and row["n_distinct_obs"] == 1
        assert row["r3_bound"] == 0.0


def test_R3_is_NON_LOCAL_the_measured_rejection():
    """THE decisive measurement against the strongest rival. Same codebook, same
    observation — and the verdict FLIPS from refused to admitted because an UNRELATED
    patch was added elsewhere in the field. A bound whose verdict depends on a patch
    the observation has nothing to do with is not a property of the decode."""
    nl = arm_NONLOCAL()["nonlocality"]
    assert nl["scene_without_patch"]["admits"] is False
    assert nl["scene_with_unrelated_patch"]["admits"] is True
    assert nl["verdict_flips"] is True
    assert nl["scene_without_patch"]["r3_bound"] == 15.0
    assert nl["scene_with_unrelated_patch"]["r3_bound"] == 200.0


def test_R4_is_CONSISTENT_at_k_ge_2_but_UNDEFINED_at_k1_THE_CRUX():
    """THE CRUX. Observed-separation is the ONLY rival consistent with the landed
    bound — 0 disagreements over 100 already-burned probes — and it is UNDEFINED in
    every k=1 case, including the defect scene where the only competitor IS the
    winner. The rivals DEFINED at k=1 are INCONSISTENT; the CONSISTENT one is
    UNDEFINED."""
    u = arm_UNDEF()
    assert u["PASS"], u
    assert u["agreement_with_packing_at_k_ge_2"]["disagreements"] == 0
    assert u["agreement_with_packing_at_k_ge_2"]["n"] == 100
    assert u["r4_undefined_everywhere_at_k1"] is True
    for name, row in u["undefined_at_k1"].items():
        assert row["r4_gap"] is None, (name, row)


def test_PART_A_IS_A_NEGATIVE_and_names_its_own_unblocking_change():
    """§7 — the negative is first-class, and it names the precise change that would
    unblock it: a mint with INTRINSIC EXTENT (colour identity's own NAMED FRONTIER,
    perceptual NEARNESS in minting). Pinned in the seed so it cannot be lost."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    d = seed["description"]
    assert "NONE DOES" in d
    assert "NON-INCREASING under codebook growth" in d
    assert "INTRINSIC EXTENT" in d and "NEARNESS in minting" in d


# --- PART B: the flip ----------------------------------------------------------
def test_the_default_IS_FLIPPED():
    assert _seed_default_bound() == 1.0


def test_NOREG_no_regression_THE_CONJUNCTION():
    """RISKED, and THE arm that catches a refuse-everything build (process rule 5).
    Everything here runs on the SEED DEFAULT, so it exercises the flip itself."""
    c = arm_NOREG()
    assert c["PASS"], c
    assert c["seed_default_bound_in_force"] == 1.0
    assert c["a_k3_field"]["n_assigned"] == 36 and c["a_k3_field"]["n_refused"] == 0
    assert c["a_k3_field"]["signs_correct"] is True
    assert c["c_recognize_not_remint"]["n_cats_before"] == 3
    assert c["c_recognize_not_remint"]["n_cats_after"] == 3


def test_NOREG_the_landed_dist4_probe_is_STILL_assigned_on_the_flipped_default():
    """The landed off-prototype probe sits at 4.0 against a bound of 7.8102 — 3.81
    INSIDE the region where a tighter bound would refuse it. A refuse-everything
    build, the exact-extent bound (0), the lattice-step bound (1.0) and the `Times`
    a/b empty-product trap ALL fail here."""
    b = arm_NOREG()["b_off_prototype_probe"]
    assert b["ci_refused"] == 0.0
    assert b["sign_dist"] == pytest.approx(4.0)
    assert (b["sign_rg"], b["sign_by"]) == (10.0, 0.0)
    assert 4.0 < 7.8102


def test_NOREG_the_k1_field_still_assigns_all_36():
    """The regime the bound does not reach must be untouched by the flip."""
    d = arm_NOREG()["d_k1_field"]
    assert d["k"] == 1
    assert d["n_assigned"] == 36 and d["n_refused"] == 0
    assert d["all_dist_zero"] is True


def test_DISAGREE_the_graph_IS_the_derived_predicate_at_k1_AND_k_ge_2():
    """RISKED, n=100 per regime, seeds 50200-50299. Non-degenerate BOTH ways at
    k>=2, so neither a refuse-everything nor an admit-everything build passes."""
    d = arm_DISAGREE()
    assert d["PASS"], d
    assert d["seeds"] == [50200, 50299]
    assert d["k3"]["disagreements"] == 0 and d["k1"]["disagreements"] == 0
    assert d["k3"]["n"] == 100 and d["k1"]["n"] == 100
    assert d["k3"]["n_admitted"] >= 1 and d["k3"]["n_refused"] >= 1


def test_DISAGREE_the_k1_DEAD_ZONE_is_reported_not_hidden():
    """HONEST: at k=1 the graph admits 100/100 — a degenerate split, and it is the
    FINDING, not a passing floor. The bound reaches k>=2 only."""
    d = arm_DISAGREE()
    assert d["k1"]["k"] == 1
    assert d["k1"]["n_admitted"] == 100 and d["k1"]["n_refused"] == 0


def test_FLOOR_noise_mints_and_signs_nothing():
    f = arm_FLOOR()
    assert f["PASS"], f
    assert f["fields_minting"] == 0 and f["fields_with_signs"] == 0
    assert f["seeds"] == [50300, 50399]


def test_DELTA_ON_FLIPPED_is_EMPTY_across_every_landed_scene():
    """PART B condition 2, and the measurement the flip was gated on."""
    d = delta_on_flipped()
    assert d["PASS"], d
    assert d["n_changed_fields_across_landed_scenes"] == 0
    assert len(d["scenes"]) == 5
    for name, row in d["scenes"].items():
        assert row["changed"] == {}, (name, row["changed"])


def test_DELTA_the_k1_dead_zone_is_BYTE_IDENTICAL_on_vs_off():
    """PART B condition 3 — the flip is a STRICT improvement: refusal gained at
    k>=2, NOTHING lost at k=1. It cannot regress the regime it does not reach."""
    d = delta_on_flipped()["k1_dead_zone"]
    assert d["scene_stats_identical_on_vs_off"] is True
    assert d["far_probe_identical_on_vs_off"] is True
    assert d["probe_on"] == d["probe_off"]


def test_L1b_defect_record_still_reproduces_its_COMMITTED_numbers():
    """§6 item 5 / the declared carve-out. L1b's audit is a RECORD OF THE DEFECT; it
    now pins `bound=0.0` explicitly, so its committed numbers reproduce exactly even
    though the seed default is ARMED."""
    from scripts.uniqueness_measure import audit_colour_identity
    a = audit_colour_identity()
    assert a["probes"]["far_out_of_gamut"]["sign_dist"] == pytest.approx(269.5199)
    assert a["probes"]["far_out_of_gamut"]["refused"] == 0
    assert a["probes"]["equidistant"]["sign_dist"] == pytest.approx(10.0)
    assert a["probes"]["equidistant"]["margin"] == 0.0


# --- composition / no-new-Rust / no-new-rule -----------------------------------
def _rung_diff_names():
    """Pinned to THIS RUNG'S OWN IMMUTABLE COMMIT RANGE (§12.3).

    This originally diffed BASE_SHA against the WORKING TREE and scanned every
    untracked file repo-wide — correct only while the rung sits alone on its branch.
    Once anything else merges, that diff legitimately contains the other rung's files
    and the untracked scan sweeps up `var/pytest_tmp/**` scratch artifacts (including
    stray `*.rs` from other tests' temp dirs), producing FALSE provenance failures.
    The same defect was fixed in the prior colour-bound gate; it propagated here by
    copy. The claims are unchanged — only the scope: `BASE_SHA..RUNG_SHA` is immutable
    and cannot be polluted by later merges or a dirty tree."""
    out = subprocess.run(["git", "diff", "--name-only", BASE_SHA, RUNG_SHA],
                         cwd=HERE, capture_output=True, text=True).stdout
    return sorted({ln for ln in out.splitlines() if ln.strip()})


def test_this_rung_adds_NO_Rust():
    changed = _rung_diff_names()
    assert changed, "expected a non-empty rung diff"
    rs = [f for f in changed if f.endswith(".rs")]
    assert rs == [], f"this rung claims NO new Rust but touched: {rs}"


def test_this_rung_adds_NO_new_RULE_and_changes_no_rule_body():
    """PART A is a NEGATIVE, so there is nothing to build: the ONLY seed change is
    the default attribute. Every rule's `match`, `where` and `effects` is BYTE-EQUAL
    to the landed v1.2.0 — verified against git, not by eye."""
    blob = subprocess.run(["git", "show", f"{BASE_SHA}:research/experiments/"
                           "gamma-substrate/seeds/vision_colour_identity.json"],
                          cwd=HERE, capture_output=True, text=True).stdout
    before = json.loads(blob)
    after = json.load(open(os.path.join(HERE, "seeds",
                                        "vision_colour_identity.json")))
    assert [r["name"] for r in before["rules"]] == [r["name"] for r in after["rules"]]
    for rb, ra in zip(before["rules"], after["rules"]):
        for key in ("match", "where", "effects"):
            assert rb[key] == ra[key], f"{rb['name']}.{key} moved"
    # the ONLY node-attr change is `bound`
    assert before["nodes"][0]["attrs"]["bound"] == 0.0
    assert after["nodes"][0]["attrs"]["bound"] == 1.0
    for k in ("identity", "achromatopsia"):
        assert before["nodes"][0]["attrs"][k] == after["nodes"][0]["attrs"][k]


def test_this_rung_introduces_no_tuned_constant():
    """§13. PART A adds no bound, so it adds no literal. The seed's executable
    literal set is UNCHANGED from v1.2.0, and the derived radii (7.8102, 10.0, 50.0)
    appear in no executable term."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    for rule in seed["rules"]:
        blob = json.dumps(rule.get("where", {})) + json.dumps(rule.get("effects", []))
        for forbidden in ("7.8102", "10.0", "50.0", "276.4797", "0.7071"):
            assert forbidden not in blob, (rule["name"], forbidden)


def test_the_Times_items_list_form_is_used_throughout():
    """Process rule 4 — the `a`/`b` form is an EMPTY PRODUCT (=1) and would silently
    turn the bound into the constant 1.0. This rung changes NO composition, so the
    inherited guard must still use the items-list form everywhere."""
    seed = json.load(open(os.path.join(HERE, "seeds",
                                       "vision_colour_identity.json")))
    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Times":
                assert "items" in o and isinstance(o["items"], list) and o["items"], o
                assert "a" not in o and "b" not in o, o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)


def test_no_python_decision_in_the_runner_predicates():
    """§0 / CLAUDE.md. The admit/refuse decision belongs to the SEED. This runner's
    rival predicates exist only to MEASURE and to evaluate rejected candidates — they
    are never written back into the graph."""
    src = open(os.path.join(HERE, "scripts",
                            "colour_bound_k1_measure.py")).read()
    for banned in ("set_attr(", "add_edge(", "s.add_node("):
        assert banned not in src, banned
