"""RUNG L1b — THE UNIQUENESS GATE for the SILENT-ARGMIN HAZARD.

Gates VISION_UNIQUENESS_PREREG.md / VISION_UNIQUENESS_RESULTS.md.

The finding acted on (VISION_LIGHTING_L1_RESULTS.md): below the resolution floor L1's
recognizer returns a CONFIDENT WRONG IDENTITY while ≥2 candidates lie INSIDE the
verdict bound — the ambiguity is visible in the graph and `Argmin` resolves it
silently. These tests gate BOTH halves of the rung: the AUDIT of where that hazard
exists across the merged codebook rungs, and the GATE that refuses instead.

§1.1's conjunction is the design constraint throughout: a build that REFUSES
EVERYTHING scores a perfect floor on the discrimination and noise arms, so those
arms alone are NOT a gate. `test_the_gate_does_NOT_regress_the_unambiguous_regime`
is the arm a refuse-everything build FAILS, and it is what makes the rest mean
something.
"""
from __future__ import annotations
import json
import math
import os
import random

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402
from domains import uniqueness_world as uw  # noqa: E402
# The AST structural auditor. Five assertions in this file used to pattern-match a
# SERIALIZED seed blob and were evadable by re-spelling / negating / nesting /
# reversing / relocating an equivalent composition — see
# `VISION_TRIPWIRE_REPAIR_PREREG.md` (inventory S1-S5) and its results file.
from tools.term_ast_audit import (  # noqa: E402
    audit_seed_file, legacy_string_test, walk_terms,
)

LATTICE_STEP = 1.0
REF_GAIN = (1.0, 1.0, 1.0)
MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}
REAL_GAINS = [(1.5, 1.5, 1.5), (2.5, 2.5, 2.5), (3.3, 3.3, 3.3), (7.5, 7.5, 7.5),
              (1.5, 2.5, 3.3)]
FLOOR_GAINS = [0.06, 0.05, 0.04]


def _refl(include_novel=True):
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _run(gain, *, reflectances=None, include_novel=True, uniqueness=1.0):
    refl = _refl(include_novel) if reflectances is None else reflectances
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_uniqueness"])
    ref = lw.add_frame(s, reflectances=refl, gain=REF_GAIN, is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=1.0)
    lw.set_flag_l1(s, lighting_l1=1.0)
    uw.set_flag(s, uniqueness=uniqueness)
    lw.tick(s)
    return s, ref, test


def _expected(s, ref, name):
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


def _rows(s, ref, test):
    out = []
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        v = uw.verdict(s, nid)
        out.append({"name": meta["name"], "exp": _expected(s, ref, meta["name"]),
                    **r, **v})
    return out


# ---------------- PART B — THE GATE -------------------------------------------

@pytest.mark.parametrize("g", FLOOR_GAINS)
def test_HAZARD_the_pregate_build_returns_a_confident_wrong_identity(g):
    """ARM A — THE PREMISE. With the gate OFF the floor mis-identifies and NEVER
    refuses. If this stops reproducing, the rung's premise is gone and the gate is
    solving a problem that no longer exists."""
    s, ref, test = _run((g, g, g), uniqueness=0.0)
    rows = _rows(s, ref, test)
    false_ids = sum(1 for r in rows if r["l1_recognized"] == 1 and r["l1_id"] != r["exp"])
    refused = sum(1 for r in rows if r["l1_recognized"] != 1)
    assert false_ids > 0, f"g={g}: the hazard did not reproduce"
    assert refused == 0, f"g={g}: expected CONFIDENT wrong ids, got {refused} refusals"


@pytest.mark.parametrize("g", FLOOR_GAINS)
def test_GATE_the_ambiguous_regime_REFUSES_instead_of_misidentifying(g):
    """ARM B — the rung's reason to exist. With the gate ON, not one false identity
    survives the ambiguous regime, and the refusals are EXPLICIT (`uq_ambiguous`),
    never a silent absence (§1.1's dead-arm lesson)."""
    s, ref, test = _run((g, g, g), uniqueness=1.0)
    rows = _rows(s, ref, test)
    uq_false = sum(1 for r in rows if r["uq_recognized"] == 1 and r["uq_id"] != r["exp"])
    l1_false = sum(1 for r in rows if r["l1_recognized"] == 1 and r["l1_id"] != r["exp"])
    assert l1_false > 0, "the ungated arm on the SAME graph must still be hazardous"
    assert uq_false == 0, f"g={g}: gate let {uq_false} false identities through"
    assert any(r["uq_status"] == "uq_ambiguous" for r in rows)
    for r in rows:
        if r["uq_status"] == "uq_ambiguous":
            assert r["uq_ncand"] >= 2, "a refusal must record ≥2 tied candidates"


def test_the_gate_does_NOT_regress_the_unambiguous_regime():
    """ARM C — THE §1.1 CONJUNCTION, AND THE ARM A REFUSE-EVERYTHING BUILD FAILS.

    L1's committed headline is 60/60 at the five real gains. The gate must leave it
    exactly there. This is the test that makes the discrimination and noise floors
    mean something: both of those are satisfied by a mechanism that refuses
    everything, and this one is not."""
    correct = refused = total = 0
    for g in REAL_GAINS:
        s, ref, test = _run(g, uniqueness=1.0)
        for r in _rows(s, ref, test):
            total += 1
            correct += int(r["uq_recognized"] == 1 and r["uq_id"] == r["exp"])
            refused += int(r["uq_status"] == "uq_ambiguous")
    assert total == 60
    assert correct == 60, f"REGRESSION: {correct}/60 (a refuse-everything build lands here)"
    assert refused == 0


def test_an_admitted_row_is_byte_identical_to_L1s_own_answer():
    """The gate SUBTRACTS ambiguous claims and adds nothing: where it admits, the
    identity is L1's own Argmin winner, unchanged."""
    for g in REAL_GAINS:
        s, ref, test = _run(g, uniqueness=1.0)
        for r in _rows(s, ref, test):
            if r["uq_recognized"] == 1:
                assert r["uq_id"] == r["l1_id"]


def test_discrimination_is_exact_zero():
    """ARM D. NOTE (§1.1): a refuse-everything build ALSO passes this — which is
    exactly why it is not the gate. See the no-regression test."""
    false_ids = 0
    for g in REAL_GAINS:
        s, ref, test = _run(g, uniqueness=1.0)
        false_ids += sum(1 for r in _rows(s, ref, test)
                         if r["uq_recognized"] == 1 and r["uq_id"] != r["exp"])
    assert false_ids == 0


def test_noise_is_refused_with_the_gate_on():
    """ARM E (subset of the confirmatory 100; seeds from the rung's own block)."""
    for seed in range(45340, 45360):
        rng = random.Random(seed)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99), "rM": rng.randint(1, 99),
                 "rS": rng.randint(1, 99)} for j in range(13)]
        s, ref, test = _run((3.3, 2.5, 4.5), reflectances=refl, uniqueness=1.0)
        assert lw.n_identities(s) == 0
        assert sum(uw.verdict(s, n)["uq_recognized"] for n in test["surface_ids"]) == 0


def test_a_novel_material_is_never_force_matched():
    """ARM F."""
    for gain in REAL_GAINS:
        s, ref, test = _run(gain, uniqueness=1.0)
        for nid, meta in zip(test["surface_ids"], test["meta"]):
            if meta["name"] == NOVEL["name"]:
                assert uw.verdict(s, nid)["uq_recognized"] == 0


def test_the_declared_ambiguity_COST_is_pinned():
    """ARM G — the PRE-REGISTERED COST, pinned so it cannot drift into an unexamined
    pass. At the floor the gate refuses CORRECT rows too, because they are genuinely
    ambiguous. It buys honesty with recall, and the price is recorded, not hidden.

    The prereg predicted 0/12 retained at EVERY floor gain; at g=0.04 TWO rows were
    retained (they had exactly one candidate in bound). That broken proviso is
    pinned here rather than smoothed over (§3.7)."""
    retained = {}
    for g in FLOOR_GAINS:
        s, ref, test = _run((g, g, g), uniqueness=1.0)
        rows = _rows(s, ref, test)
        retained[g] = sum(1 for r in rows if r["uq_recognized"] == 1)
    assert retained[0.06] == 0
    assert retained[0.05] == 0
    assert retained[0.04] == 2, "the prereg's proviso broke HERE — pinned, not hidden"


def test_the_flag_is_OFF_by_default_and_absence_tolerant():
    """§9 + process rule 3. With the params node ABSENT the MaxOver default (0.0)
    turns the gate off — it must NOT be a PickUnique on a params node.

    REPAIRED (inventory S3, `VISION_TRIPWIRE_REPAIR_PREREG.md`). The previous form
    was `'"type": "MaxOver"' in blob` — satisfied by a `MaxOver` ANYWHERE in the seed,
    so it never actually checked that the FLAG READ is the tolerant one. This walks
    the parsed tree and inspects the read of `uniqueness` ITSELF.
    """
    seed = json.load(open(os.path.join(_ROOT, "seeds", "vision_uniqueness.json")))
    reads = [n for n, _p, _d in walk_terms(seed["rules"])
             if n.get("type") in ("MaxOver", "PickUnique", "Pick")
             and '"uniqueness"' in json.dumps(n.get("term", n))]
    assert reads, "no read of the `uniqueness` flag found at all"
    assert all(n["type"] == "MaxOver" for n in reads), (
        "the flag read must be absence-tolerant (MaxOver with a default), never a "
        f"Pick/PickUnique on a params node: {[n['type'] for n in reads]}")
    assert not [n for n, _p, _d in walk_terms(seed["rules"])
                if n.get("type") == "PickUnique"], "no PickUnique anywhere"
    assert seed["nodes"][0]["attrs"]["uniqueness"] == 0.0


def test_OFFDAY_the_gate_writes_nothing_at_the_default_flag():
    """§9: at the default the seed is INERT — no `uq_*` attribute exists anywhere,
    including in the regime where the gate would otherwise fire hardest."""
    for g in [REAL_GAINS[0], (0.04, 0.04, 0.04)]:
        s, ref, test = _run(g, uniqueness=0.0)
        for r in _rows(s, ref, test):
            assert r["uq_status"] == ""
            assert r["uq_recognized"] == 0


def test_the_gate_never_writes_an_L1_attribute():
    """The namespace split that makes the two-arm comparison ONE measurement — and
    that makes the fixpoint terminate (§2.1). No effect may target `l1_*`."""
    seed = json.load(open(os.path.join(_ROOT, "seeds", "vision_uniqueness.json")))
    for rule in seed["rules"]:
        for eff in rule["effects"]:
            assert eff[0] == "set_attr"
            assert eff[2].startswith("uq_"), f"{rule['name']} writes {eff[2]}"


def test_this_rung_adds_NO_new_constant():
    """§13. The only numbers in the gate are L1's inherited ONE-LATTICE-STEP bound,
    the count 2 (the definition of 'more than one'), the flag's 0.5 comparison and
    the literals 0.0/1.0. Nothing was fitted to make an output look right."""
    seed = json.load(open(os.path.join(_ROOT, "seeds", "vision_uniqueness.json")))
    lits = set()

    def walk(t):
        if isinstance(t, dict):
            if t.get("type") == "Lit" and isinstance(t.get("value"), (int, float)):
                lits.add(float(t["value"]))
            for v in t.values():
                walk(v)
        elif isinstance(t, list):
            for v in t:
                walk(v)

    walk(seed["rules"])
    assert lits <= {0.0, 0.5, 1.0, 2.0}, f"unexpected constant(s): {lits}"


def test_no_python_decision_in_the_adapter():
    """§0 / CLAUDE.md: the adapter blind-writes a flag and reads attrs. It must not
    branch on graph state — in particular it must not COMBINE l1_recognized with an
    ambiguity marker to derive a verdict; the rules partition and write uq_status.

    A substring scan is NOT a selector here (§12): `->` in a type annotation
    contains `>`. This parses the module and asserts on the AST — no branch node
    (`If`/`IfExp`), no comparison, no boolean operator anywhere in the adapter.
    """
    import ast
    src = open(os.path.join(_ROOT, "domains", "uniqueness_world.py")).read()
    tree = ast.parse(src)
    banned = [n for n in ast.walk(tree)
              if isinstance(n, (ast.If, ast.IfExp, ast.Compare, ast.BoolOp))]
    assert not banned, (
        "adapter branches on state: "
        + ", ".join(f"{type(n).__name__}@line{n.lineno}" for n in banned))
    # And it must not re-derive the verdict from L1's attributes — that is the rules'
    # job (uq_admit / uq_refuse_ambiguous partition and write uq_status). Checked on
    # the CODE, not the prose: the module docstring legitimately DISCUSSES
    # `l1_recognized` in order to say why the adapter does not read it.
    # Docstring nodes are excluded BY IDENTITY, not by value — `get_docstring`
    # returns a cleaned/dedented copy that no longer equals the source constant.
    doc_nodes = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = getattr(n, "body", None)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                doc_nodes.add(id(body[0].value))
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in doc_nodes]
    bad = [s for s in literals if s.startswith("l1_")]
    assert not bad, f"adapter reads an L1 attribute: {bad}"
    allowed = {"attrs", "UniquenessParams", "uniqueness", ""}
    assert all(s.startswith("uq_") or s in allowed for s in literals), literals


# ---------------- PART A — THE AUDIT ------------------------------------------

def test_AUDIT_L1_is_exposed_and_the_ambiguity_is_visible_in_the_graph():
    """The hazard, and the proof it is not intrinsic ill-posedness: at the floor ≥2
    candidates lie INSIDE the bound, so a refusal was available and was not taken."""
    s, ref, test = _run((0.04, 0.04, 0.04), uniqueness=0.0)
    ids = lw.identities(s)
    a = {k: float(s.node(test["frame"])["attrs"].get(k, 0.0))
         for k in ("l1_aL", "l1_aM", "l1_aS")}
    worst = 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        r = lw.recognition(s, nid)
        k = sum(1 for c in ids
                if max(abs(r["c" + ch] - c["p" + ch] * (a["l1_a" + ch] / c["pa" + ch]))
                       for ch in "LMS") <= LATTICE_STEP)
        worst = max(worst, k)
    assert worst >= 2, "the ambiguity must be detectable from inside the graph"
    assert worst == 6, "six of six candidates inside the bound — pinned"


def test_AUDIT_T2_category_is_NOT_exposed_BY_CONSTRUCTION():
    """`cat_recognize` is an Exists over a region box with an EXACT signature
    equality and assigns NO identity from a codebook; `cat_mint` dedups per
    signature, so the matching-candidate set has cardinality ≤1 ALWAYS. The
    degenerate stimulus (two kinds sharing a signature, overlapping boxes) MERGES
    into one category rather than producing two rival candidates."""
    from domains import category_world as cw
    items = [dict(d0=1, d1=1, v0=a, v1=b, kind=nm)
             for v0s, v1s, nm in [((10, 20), (30, 40), "P"), ((15, 25), (35, 45), "Q")]
             for a in v0s for b in v1s]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_category"])
    h = cw.add_field(s, items=items)
    cw.set_flag(s, identity=1.0)
    cw.tick(s)
    assert len(list(s.nodes("ObjCategory"))) == 1, "shared signature must not mint two"


def test_AUDIT_colour_identity_bound_CORRECTED_a_bound_was_added_and_is_now_SEEN():
    """**CORRECTED — this assertion's POLARITY IS INVERTED, and that is the finding.**

    L1b recorded: *"`ci_assign` contains ZERO `Lte` nodes, so it can NEVER refuse"*,
    asserted as `'"type": "Lte"' not in blob` with the note *"if a bound was added,
    re-run the audit"*. **A bound WAS added** (`VISION_COLOUR_BOUND_RESULTS.md` +
    `..._K1_RESULTS.md`) and it was composed as **`Lt` inside `Not(Exists(...))`** —
    so the tripwire never tripped. That is the defect this rung repairs
    (`VISION_TRIPWIRE_REPAIR_PREREG.md`, inventory S1).

    The audit's MEASURED numbers are unaffected: the k=1 rung pinned `bound=0.0` in
    `audit_colour_identity`, so that row measures the UNBOUNDED behaviour its prose
    always claimed. What changes is the STRUCTURAL claim, corrected here rather than
    edited into L1b's results (§7).
    """
    path = os.path.join(_ROOT, "seeds", "vision_colour_identity.json")
    a = audit_seed_file(path, "ci_assign")
    rule = [r for r in json.load(open(path))["rules"] if r["name"] == "ci_assign"][0]
    assert [n for n, _p, _d in walk_terms(rule) if n.get("type") == "Argmin"]
    # THE CORRECTION: a bound is present, and it is negated and nested.
    assert a["T1_bound_like"] >= 1, (
        "`ci_assign` now HAS an admission bound — if it is ever removed, this "
        "assertion must flip back and the audit must be re-run")
    assert any(d["not_depth"] > 0 for d in a["T1_detail"]), (
        "the landed bound sits inside Not(Exists(...)); polarity is part of the claim")
    # and the old instrument is STILL blind to it — kept as the standing evidence
    assert legacy_string_test(rule, "Lte") is True


def test_AUDIT_similarity_path_has_no_verdict_bound_so_the_gate_is_NA():
    """`shape_decode_loop` admits by EXACT equality, so 'two candidates inside the
    bound' is undefined there. Pinned so that adding a bound forces an audit re-run.

    REPAIRED (inventory S2). The previous form asserted `Lte`/`Gte` absent from the
    serialized seed — and the seed DOES contain 19 comparators (`Lt`/`Gt`), so the
    assertion's premise was never what its prose claimed; a bound spelled `Lt` would
    have evaded it entirely. The AST detector classifies by OPERAND SHAPE: those 19
    are all cardinality tests (`Count(...)`) or flag/epoch reads, none is a bound.

    **The verdict is UNCHANGED — and that is a result, not a formality.** A naive
    any-comparator detector flips this row the WRONG way; the row survives precisely
    because `Count`-rooted comparisons are excluded, which is L1b's own published
    semantics for this path (*"admission is exact equality"*) applied structurally.
    """
    a = audit_seed_file(os.path.join(_ROOT, "seeds", "shape_decode_loop.json"))
    assert a["T0_any_comparator"] > 0, "non-vacuous: there ARE comparators here"
    assert a["T1_bound_like"] == 0, "no VERDICT BOUND — re-run the audit if this fails"
    assert {d["reason"] for d in a["T0_non_bound_detail"]} <= {
        "cardinality", "atomic-vs-atomic (flag/epoch read)"}
