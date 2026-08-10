"""APPERCEPTIVE / ASSOCIATIVE AGNOSIA (FRONTIER T9) — the migrated gate
(VISION_AGNOSIA_PREREG.md).

Deterministic except the noise floor (seeds 48000–48099). A VALIDATION gate for
the FORM<->RECOGNITION seam — failure-mode gate #1 of
VISION_VENTRAL_GROUNDING.md, "the sharpest architectural tell". The classic
double dissociation, both ablations being FLAGS on `AgnosiaParams` (OFF by
default = intact, §9):

  * ASSOCIATIVE (`associative=1` guards the three sd_recognize* rules — the sole
    writers of covered_by) — the percept still FORMS (COPY survives, byte-identical
    to intact, including the occluded cells the sensor never carried) but is NOT
    NAMED. Recognition dies DOWNSTREAM of an intact percept.
  * APPERCEPTIVE (`apperceptive=1` guards gr_fill — percept COMPLETION) — the form
    cannot be built (COPY fails by exactly the occluded cells) so naming fails with
    it. The failure is UPSTREAM.
  * DOUBLE DISSOCIATION — the two ablations hit DIFFERENT stages and COPY is what
    discriminates: copy survives the identity lesion and fails the render lesion,
    while naming fails under both.
  * §1.1 — neither arm is a dead instrument: the associative copy is a REAL
    reconstruction (the 3 no-data cells per object are rendered) and the
    apperceptive percept is non-empty with the identity layer still running on it.
  * FLOOR — 100 random stimuli name NOTHING in EVERY arm; the lesions are not
    confounded with noise.
  * §13.2 — each flag MOVES its claimed target and only its target.
"""
import json
import os

from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts import agnosia_measure as am  # noqa: E402

_RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "agnosia_measure.json")


def test_intact_control_validity_both_copy_and_name_succeed():
    """A INTACT (§1.1): neither readout is a dead instrument to begin with."""
    a = am.arm("A_INTACT")
    assert a["n_copy_ok"] == a["n"] == 6, a
    assert a["n_name_ok"] == a["n"], a
    assert a["covered"] == am.NAMES, a          # each names its OWN object
    assert a["symdiffs"] == [0] * 6, a


def test_associative_copy_survives_but_naming_dies():
    """B ASSOCIATIVE (headline): recognition dies downstream of an intact percept."""
    b = am.arm("B_ASSOCIATIVE", associative=1.0)
    assert b["n_copy_ok"] == b["n"] == 6, b     # the form is still FORMED
    assert b["n_named_anything"] == 0, b        # and nothing is NAMED
    assert b["symdiffs"] == [0] * 6, b


def test_apperceptive_copy_fails_and_naming_fails_with_it():
    """C APPERCEPTIVE (headline): the failure is UPSTREAM — no form, no name."""
    c = am.arm("C_APPERCEPTIVE", apperceptive=1.0)
    assert c["n_copy_ok"] == 0, c
    assert c["n_named_anything"] == 0, c
    # exactly the 3 occluded on-form cells per object — the lesion removes
    # COMPLETION and nothing else
    assert c["symdiffs"] == [3] * 6, c
    # §1.1: the percept is non-empty and the identity layer still ran on it
    assert c["n_percept_nonempty"] == c["n"], c
    assert c["statuses"] == ["minted"], c


def test_apperceptive_second_render_corruption_agrees():
    """C2: the pre-registered second render corruption (interp blur) reproduces C."""
    c2 = am.arm("C2_APPERCEPTIVE_INTERP", interp=1.0)
    assert c2["n_copy_ok"] == 0 and c2["n_named_anything"] == 0, c2


def test_the_double_dissociation_copy_discriminates_the_two_stages():
    """D: two ablations, DIFFERENT stages — the seam is real, not one blob."""
    a = am.arm("A_INTACT")
    b = am.arm("B_ASSOCIATIVE", associative=1.0)
    c = am.arm("C_APPERCEPTIVE", apperceptive=1.0)
    assert a["n_copy_ok"] == a["n"] and a["n_name_ok"] == a["n"]
    # copy SURVIVES the identity lesion and FAILS the render lesion ...
    assert b["n_copy_ok"] == b["n"] and c["n_copy_ok"] == 0
    # ... while naming fails under BOTH
    assert b["n_named_anything"] == 0 and c["n_named_anything"] == 0


def test_copy_is_genuinely_alive_not_a_trivial_pass():
    """E (§1.1): the surviving copy is a REAL reconstruction across no data, and
    is byte-identical to the intact arm's."""
    a = am.arm("A_INTACT")
    b = am.arm("B_ASSOCIATIVE", associative=1.0)
    for ra, rb in zip(a["rows"], b["rows"]):
        assert ra["percept"] == rb["percept"], (ra["object"], "percept moved")
        # the occluded on-form cells carry NO sensor data in any arm, and the
        # render puts every one of them into the percept
        assert len(rb["occ_on_form"]) == 3, rb
        assert rb["occ_rendered"] == rb["occ_on_form"], rb


def test_floor_noise_names_nothing_in_every_arm():
    """G: 100 random stimuli (seeds 48000–48099) — 0 false names, every arm."""
    for kw in ({}, {"associative": 1.0}, {"apperceptive": 1.0}):
        f = am.floor_arm("floor", **kw)
        assert f["n_named"] == 0, (kw, f)
        assert f["n"] == 100, f


def test_each_flag_is_load_bearing_on_its_own_target():
    """H (§13.2): `associative` moves NAME and NOT copy; `apperceptive` moves COPY."""
    a = am.arm("A_INTACT")
    b = am.arm("B_ASSOCIATIVE", associative=1.0)
    c = am.arm("C_APPERCEPTIVE", apperceptive=1.0)
    assert abs(a["n_name_ok"] - b["n_name_ok"]) > 0      # moves naming
    assert abs(a["n_copy_ok"] - b["n_copy_ok"]) == 0     # ... and NOT the percept
    assert abs(a["n_copy_ok"] - c["n_copy_ok"]) > 0      # moves the percept


def test_offday_defaults_are_intact():
    """X (§9): both flags at their shipped default reproduce the intact arm exactly."""
    a = am.arm("A_INTACT")
    x = am.arm("X_OFFDAY_DEFAULTS")
    assert [r["percept"] for r in x["rows"]] == [r["percept"] for r in a["rows"]]
    assert x["n_copy_ok"] == x["n"] and x["n_name_ok"] == x["n"]


def test_the_ablations_are_flags_not_python_decisions():
    """§0/CLAUDE.md: an ablation is a FLAG on a params node. Source-grep gate —
    neither the adapter nor the runner may branch on a lesion flag."""
    import io
    import tokenize
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("domains/agnosia_world.py", "scripts/agnosia_measure.py"):
        src = open(os.path.join(here, rel)).read()
        # Scan CODE only: drop comments and string literals (docstrings included),
        # so the gate cannot be satisfied — or tripped — by prose ABOUT the rule.
        code_lines = {}
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            code_lines.setdefault(tok.start[0], []).append(tok.string)
        for lineno, toks in code_lines.items():
            code = " ".join(toks)
            assert not ("if" in toks and ("associative" in code or "apperceptive" in code)), \
                f"{rel}:{lineno}: a lesion flag is BRANCHED ON in Python: {code!r}"
    # and the guards live in the rules they lesion, as graph data
    sd = json.load(open(os.path.join(here, "seeds", "shape_decode_loop.json")))
    guarded = [r["name"] for r in sd["rules"]
               if json.dumps(r.get("where", {})).find('"associative"') >= 0]
    assert sorted(guarded) == ["sd_recognize", "sd_recognize_dim",
                               "sd_recognize_transformed"], guarded
    gr = json.load(open(os.path.join(here, "seeds", "vision_ground.json")))
    guarded_g = [r["name"] for r in gr["rules"]
                 if json.dumps(r.get("where", {})).find('"apperceptive"') >= 0]
    assert guarded_g == ["gr_fill"], guarded_g


def test_flags_ship_off_by_default():
    """§9: the seed's shipped defaults are INTACT."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seed = json.load(open(os.path.join(here, "seeds", "vision_agnosia.json")))
    (node,) = seed["nodes"]
    assert node["type"] == "AgnosiaParams"
    assert node["attrs"] == {"associative": 0.0, "apperceptive": 0.0}, node


def test_pinned_results_reproduce_the_committed_verdict():
    """§10: the committed results file records ALL_PASS under a named engine."""
    d = json.load(open(_RESULTS))
    assert d["verdict"]["ALL_PASS"] is True, d["verdict"]
    assert d["seeds_consumed"] == [48000, 48099], d["seeds_consumed"]
    assert "engine" in d["provenance"], d["provenance"]
