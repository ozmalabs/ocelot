"""ADVANCED LIGHTING RUNG L4 — SHADOW vs REFLECTANCE EDGES — the GATE.

Written INDEPENDENTLY of `scripts/lighting_l4_measure.py`: every test below
BUILDS ITS OWN SCENE and reads the graph, rather than asserting over the
runner's output file. That is not stylistic — in rung L2 the gate disagreeing
with the runner is what caught an arm that could not vary (a shuffled scene that
was never passed), and an assertion over a runner's JSON would have agreed with
the bug.

PROTOCOL: §1 (gate the measure), §1.1 (a dead arm scores a perfect floor), §9
(defaults preserve committed results), §12.3 (a provenance claim is pinned to
its DIFF, never to a mutable tree), §13 (magic numbers fall OUT).
"""
from __future__ import annotations

import ast
import json
import os
import random
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: E402  (registers vision_lighting_l4)
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_l4_world as l4w  # noqa: E402
from domains import border_ownership_world as bow  # noqa: E402

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402


SEED_PATH = os.path.join(ROOT, "seeds", "vision_lighting_l4.json")

# THE BASE COMMIT this rung is measured against (§12.3: pinned to a DIFF, never
# to a mutable tree). The provenance claims below are about THIS RUNG'S OWN
# COMMITS, so they are tested over an immutable commit range.
BASE_SHA = "07eeda24"
RUNG_SHA = "2ff2a95e"          # this rung's own commit. The provenance diffs below MUST
                               # use BASE_SHA..RUNG_SHA, never BASE_SHA..HEAD: HEAD is a
                               # MOVING target, so once any later rung merges its files
                               # appear in this rung's "own diff" and the ownership
                               # assertions fail falsely. Third instance of this defect
                               # in the arc (§12.3).

MATERIALS = {"a": (10, 20, 30), "b": (40, 15, 25), "c": (12, 44, 8),
             "d": (33, 9, 41), "e": (21, 37, 14), "f": (6, 28, 36)}
NAMES = ["a", "b", "c", "d", "e", "f"]
G0 = 2.3          # NON-INTEGER on purpose: integer gains make D_XY exactly 0.
H = W = 12


def NEU(reflectance, g):
    """Render under a spectrally NEUTRAL illuminant of scalar strength `g`.
    The adapter takes a 3-vector gain always; this names the flat case."""
    return l4w.render(reflectance, l4w.neutral(g))


# --- helpers (build a scene, tick, read back) ---------------------------------
def _row(cones, flag=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting_l4"])
    h = l4w.add_field(s, [cones])
    l4w.set_flag(s, lighting_l4=flag)
    l4w.tick(s)
    return s, h


def _kind_of(cR, cQ):
    s, h = _row([cR, cQ])
    return l4w.kind(s, h, 0, 0)


def _seed():
    with open(SEED_PATH) as f:
        return json.load(f)


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args],
                          capture_output=True, text=True).stdout


# =============================================================================
# ARM A — a NEUTRAL cast-shadow boundary reads l4_illuminant.
# DECLARED ENTAILED BY THE DERIVATION (prereg §6). Gated as CONSISTENCY.
# =============================================================================
@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("jump", [1.5, 1.7, 2.0, 2.6, 3.0, 5.0])
def test_A_a_neutral_shadow_edge_reads_ILLUMINANT(name, jump):
    r = MATERIALS[name]
    assert _kind_of(NEU(r, G0), NEU(r, G0 * jump)) == "l4_illuminant"


def test_A_the_shadow_arm_is_genuinely_ROUNDING_not_a_degenerate_zero():
    """§1: a test that cannot round is a test that cannot fail.

    On INTEGER gains the cross-product deviation is EXACTLY 0 for every material
    and the arm is unexercised. The confirmatory base gain is NON-INTEGER, and
    this pins that at least one headline row has a STRICTLY POSITIVE margin.
    """
    margins = []
    for name in NAMES:
        r = MATERIALS[name]
        s, h = _row([NEU(r, G0), NEU(r, G0 * 1.5)])
        margins.append(l4w.margin(s, h, 0, 0))
    assert max(margins) > 0.0, "no rounding anywhere — the arm is degenerate"
    assert max(margins) <= 1.0


# =============================================================================
# ARM B — a genuine MATERIAL boundary reads l4_reflectance. THE DISCRIMINATION.
# =============================================================================
def test_B_every_material_pair_reads_REFLECTANCE():
    bad = []
    for i in range(len(NAMES)):
        for j in range(i + 1, len(NAMES)):
            k = _kind_of(NEU(MATERIALS[NAMES[i]], G0),
                         NEU(MATERIALS[NAMES[j]], G0))
            if k != "l4_reflectance":
                bad.append((NAMES[i], NAMES[j], k))
    assert len(bad) == 0, f"misclassified material pairs: {bad}"


# =============================================================================
# ARM C — a SHADOW boundary must NOT become an OBJECT boundary.
# =============================================================================
def _scene_2d():
    grid = []
    for r in range(H):
        row = []
        for c in range(W):
            mat = "c" if (2 <= r < 6 and 2 <= c < 6) else "a"
            g = G0 * 0.4 if (7 <= r < 11 and 7 <= c < 11) else G0
            row.append(NEU(MATERIALS[mat], g))
        grid.append(row)
    return grid


def _l4_graph_2d():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting_l4"])
    h = l4w.add_field(s, _scene_2d())
    l4w.set_flag(s, lighting_l4=1.0)
    l4w.tick(s)
    return s, h


def _protos(grid):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow.add_field(s, grid)
    bow.set_flag(s, bown=1.0)
    bow.tick(s)
    return bow.protos(s)


PATCH_ROOT = 2 * W + 2       # 26
SHADOW_ROOT = 7 * W + 7      # 91


def test_C1_the_defect_is_REAL_raw_luminance_mints_a_SPURIOUS_shadow_object():
    """THE POSITIVE CONTROL FOR C2. If the shadow rectangle did not mint under
    RAW luminance, C2 would be demonstrating nothing at all."""
    s, h = _l4_graph_2d()
    protos = _protos(l4w.luminance_grid(s, h))
    roots = sorted(p["root"] for p in protos)
    assert roots == [PATCH_ROOT, SHADOW_ROOT], (
        f"RAW must mint BOTH the patch and the SPURIOUS shadow object; got {protos}")


def test_C2_the_shadow_is_NOT_an_object_boundary_and_the_material_STILL_IS():
    """THE HEADLINE. Both halves are required: a build that merged EVERYTHING
    would mint 0 (patch absorbed) and a build that merged NOTHING would mint 0
    by the other route (no component singly surrounded)."""
    s, h = _l4_graph_2d()
    protos = _protos(l4w.val_grid(s, h))
    roots = sorted(p["root"] for p in protos)
    assert SHADOW_ROOT not in roots, "the SHADOW minted a proto-object"
    assert roots == [PATCH_ROOT], f"expected exactly the material patch; got {protos}"
    assert protos[0]["members"] == 16


def test_C_the_two_rectangle_boundaries_are_classified_OPPOSITELY():
    s, h = _l4_graph_2d()
    patch = set([l4w.kind(s, h, r, 1, "h") for r in range(2, 6)]
                + [l4w.kind(s, h, 1, c, "v") for c in range(2, 6)])
    shadow = set([l4w.kind(s, h, r, 6, "h") for r in range(7, 11)]
                 + [l4w.kind(s, h, 6, c, "v") for c in range(7, 11)])
    assert patch == {"l4_reflectance"}, patch
    assert shadow == {"l4_illuminant"}, shadow


def test_C_border_ownership_is_shown_a_DIFFERENT_field_not_a_DIFFERENT_seed():
    """L4 changes what border-ownership is SHOWN, never how it decides."""
    s, h = _l4_graph_2d()
    raw, l4 = l4w.luminance_grid(s, h), l4w.val_grid(s, h)
    assert raw != l4
    assert len({v for r in raw for v in r}) == 3     # lit bg / shadow bg / patch
    assert len({v for r in l4 for v in r}) == 2      # bg+shadow merged / patch


# =============================================================================
# ARM D′ — DISAGREEMENT. Both classes non-empty in ONE graph, ONE tick.
# =============================================================================
def _combined_row():
    mats = ["a"] * 6 + ["c"] * 7
    gains = [G0] * 9 + [G0 * 0.4] * 4
    return [NEU(MATERIALS[mats[i]], gains[i]) for i in range(13)]


def test_Dprime_one_scene_one_tick_yields_BOTH_classes():
    """The arm a refuse-everything build AND an accept-everything build both
    fail — each empties one side (§1.1, confirmed four times in this arc)."""
    s, h = _row(_combined_row())
    kinds = [l4w.kind(s, h, 0, c) for c in range(12)]
    assert kinds.count("l4_illuminant") >= 1, kinds
    assert kinds.count("l4_reflectance") >= 1, kinds


def test_Dprime_the_edges_are_at_the_PRE_REGISTERED_positions():
    s, h = _row(_combined_row())
    kinds = [l4w.kind(s, h, 0, c) for c in range(12)]
    assert kinds[5] == "l4_reflectance"      # material a -> c
    assert kinds[8] == "l4_illuminant"       # gain x0.4, same material
    assert all(kinds[c] == "l4_flat" for c in (0, 1, 2, 3, 4, 6, 7, 9, 10, 11))


def test_Dprime_the_SHADOW_does_not_split_the_component_and_the_MATERIAL_does():
    s, h = _row(_combined_row())
    vals = l4w.val_grid(s, h)[0]
    assert len(set(vals)) == 2, vals
    assert len(set(vals[0:6])) == 1          # material a, one component
    assert len(set(vals[6:13])) == 1         # material c ACROSS the shadow
    assert vals[5] != vals[6]                # split exactly at the material edge


# =============================================================================
# ARM E — PENUMBRA.
# =============================================================================
@pytest.mark.parametrize("rho", [1.15, 1.3])
def test_E_a_soft_shadow_ramp_reads_ILLUMINANT_wherever_it_is_an_edge(rho):
    r = MATERIALS["a"]
    s, h = _row([NEU(r, G0 * rho ** k) for k in range(8)])
    kinds = [l4w.kind(s, h, 0, c) for c in range(7)]
    edges = [k for k in kinds if k != "l4_flat"]
    assert edges, "the ramp produced no edge at all"
    assert all(k == "l4_illuminant" for k in edges), kinds


# =============================================================================
# ARM F — the NOISE FLOOR, and its ALIVENESS (§1.1 clause 4).
# =============================================================================
def _noise_tally(seeds):
    illum = classified = tot = 0
    for sd in seeds:
        rng = random.Random(sd)
        row = [tuple(rng.randint(0, 120) for _ in range(3)) for _ in range(13)]
        s, h = _row(row)
        for c in range(12):
            k = l4w.kind(s, h, 0, c)
            tot += 1
            illum += (k == "l4_illuminant")
            classified += (k != "")
    return illum, classified, tot


def test_F_alive_the_noise_classifier_is_NOT_SILENT():
    """§1.1 clause 4, FIRST — a classifier that fires on nothing scores a
    FLAWLESS floor while measuring nothing. Run this BEFORE believing the floor."""
    illum, classified, tot = _noise_tally(range(45680, 45700))
    assert classified == tot, f"only {classified}/{tot} adjacencies classified"


def test_F_BOUND_the_noise_floor_FAILS_its_pre_registered_exact_zero_rule():
    """THE PRE-REGISTERED RULE IS EXACTLY 0. IT FAILS AT 2/1200.

    I predicted the failure in advance (prereg §5 proviso 1, "0–5 of 1200") with
    its mechanism. Pinned at the MEASURED value AND at the failure — `== 2` and
    `> 0` — so it can neither drift into an unexamined pass nor be quietly
    re-read as a success. A refuse-everything build scores this floor PERFECTLY
    (0/1200), which is exactly why it reddens here: the assertion is the measured
    value, not the inequality.
    """
    illum, classified, tot = _noise_tally(range(45680, 45780))
    assert tot == 1200
    assert classified == tot
    assert illum == 2, f"the floor moved: {illum}/1200"
    assert illum > 0, "the pre-registered rule was exactly 0; this must record a FAIL"


def test_F_BOUND_the_noise_leaks_ARE_arm_H_arising_BY_CHANCE():
    """THE DIAGNOSIS, and it is architectural rather than statistical: both
    surviving leaks are random triples that happen to be NEAR-PROPORTIONAL —
    i.e. arm H's constructed ambiguity occurring by accident. The floor's
    residual is not a separate defect; it is the SAME irreducible failure mode,
    measured a second way.
    """
    leaks = []
    for sd in range(45680, 45780):
        rng = random.Random(sd)
        row = [tuple(rng.randint(0, 120) for _ in range(3)) for _ in range(13)]
        s, h = _row(row)
        for c in range(12):
            if l4w.kind(s, h, 0, c) == "l4_illuminant":
                leaks.append((row[c], row[c + 1]))
    assert len(leaks) == 2
    for cR, cQ in leaks:
        ratios = [cQ[k] / max(cR[k], 1e-9) for k in range(3)]
        spread = max(ratios) / min(ratios)
        assert spread < 1.05, (
            f"leak {cR}->{cQ} is NOT near-proportional (spread {spread:.3f}) — "
            "the diagnosis is wrong and the residual has another cause")


# =============================================================================
# ARMS G, H — the PREDICTED NEGATIVES. These are the rung's real bound.
# =============================================================================
@pytest.mark.parametrize("name", NAMES)
def test_G_a_CHROMATIC_shadow_is_MISCLASSIFIED_as_reflectance(name):
    """PREDICTED NEGATIVE, and physically the common case (blue skylight in
    shade vs yellow sun in light). The ratio cue is simply WRONG here."""
    r = MATERIALS[name]
    assert _kind_of(NEU(r, G0), l4w.render(r, (4.0, 4.4, 5.2))) \
        == "l4_reflectance"


@pytest.mark.parametrize("r1,r2", [((10, 20, 30), (20, 40, 60)),
                                   ((10, 20, 30), (15, 30, 45))])
def test_H_PROPORTIONAL_materials_are_MISREAD_as_a_shadow(r1, r2):
    """PREDICTED NEGATIVE. Irreducible to ANY local ratio cue: a material change
    that IS a scalar multiple is indistinguishable from an illuminant change."""
    assert _kind_of(NEU(r1, G0), NEU(r2, G0)) == "l4_illuminant"


# =============================================================================
# ARM I — BOUND OCCUPANCY (process rule 7).
# =============================================================================
def test_I_the_bound_is_HUGGED_on_the_illuminant_side_and_the_classes_SEPARATE():
    """L1b's hazard: a bound that never binds, invisible because only the winner
    was reported. Report BOTH sides. If the illuminant side sat at 0 and the
    reflectance side at 0.001, the classes would be separated by something other
    than this bound — and the numbers would say so."""
    illum, refl = [], []
    for name in NAMES:
        for jump in (1.5, 1.7, 2.0, 2.6, 3.0, 5.0):
            r = MATERIALS[name]
            s, h = _row([NEU(r, G0), NEU(r, G0 * jump)])
            illum.append(l4w.margin(s, h, 0, 0))
    for i in range(len(NAMES)):
        for j in range(i + 1, len(NAMES)):
            s, h = _row([NEU(MATERIALS[NAMES[i]], G0),
                         NEU(MATERIALS[NAMES[j]], G0)])
            refl.append(l4w.margin(s, h, 0, 0))
    assert max(illum) <= 1.0
    assert max(illum) > 0.5, "the bound is not hugged — it may never bind"
    assert min(refl) > 1.0
    assert min(refl) / max(illum) > 5.0, "the two classes are not separated"


def test_I_the_channel_pair_COUNT_inside_the_bound_is_recorded():
    """The literal count process rule 7 asks for, computed IN-GRAPH."""
    r = MATERIALS["a"]
    s, h = _row([NEU(r, G0), NEU(r, G0 * 2.0)])
    assert l4w.npairs(s, h, 0, 0) == 3
    s, h = _row([NEU(MATERIALS["a"], G0), NEU(MATERIALS["c"], G0)])
    assert 0 <= l4w.npairs(s, h, 0, 0) < 3


# =============================================================================
# ARM J — randomised layouts.
# =============================================================================
def test_J_randomised_material_layouts_read_REFLECTANCE_at_their_boundaries():
    tot = ok = 0
    for sd in range(45780, 45800):
        rng = random.Random(sd)
        mats = [rng.choice(NAMES) for _ in range(13)]
        s, h = _row([NEU(MATERIALS[m], G0) for m in mats])
        for c in range(12):
            if mats[c] != mats[c + 1]:
                tot += 1
                ok += (l4w.kind(s, h, 0, c) == "l4_reflectance")
    assert tot > 0
    assert ok / tot >= 0.95, f"{ok}/{tot}"


# =============================================================================
# ARM X / §9 — the flag OFF by default, and the seed inert.
# =============================================================================
def test_X_the_flag_ships_OFF_and_the_seed_is_NOT_boot_loaded():
    seed = _seed()
    params = [n for n in seed["nodes"] if n["type"] == "LightingL4Params"]
    assert len(params) == 1
    assert params[0]["attrs"]["lighting_l4"] == 0.0
    s, ag = boot_core()
    assert len(list(s.nodes("LightingL4Params"))) == 0


def test_X_with_the_flag_OFF_NO_l4_attribute_is_written_anywhere():
    s, h = _row(_combined_row(), flag=0.0)
    assert l4w.written_l4_attrs(s, h) == []
    assert all(l4w.kind(s, h, 0, c) == "" for c in range(12))
    assert l4w.n_components(s, h) == 13      # nothing merged: every cell its own


# =============================================================================
# §13 / §12.3 / CLAUDE.md — the structural gates.
# =============================================================================
def test_this_rung_adds_NO_new_constant():
    """The seed's ENTIRE numeric literal set must be {0.0, 0.5, 1.0} — a STRICT
    SUBSET of L2's and L3's {0.0, 0.5, 1.0, 1.0e9}."""
    lits = set(re.findall(r'"value": ([-0-9.eE+]+)',
                          json.dumps(_seed()["rules"])))
    assert lits == {"0.0", "0.5", "1.0"}, sorted(lits)


def test_this_rung_adds_NO_RUST():
    """§12.3: pinned to THIS RUNG'S OWN DIFF (an immutable commit range), never
    to a mutable tree — a gate that diffs the live tree tests whether anyone has
    done any work since, which is a different (and false) claim."""
    diff = _git("diff", "--name-only", f"{BASE_SHA}..{RUNG_SHA}",
                "--", "runners/dsl/src", "runners/dsl/Cargo.toml")
    assert diff.strip() == "", f"this rung touched Rust:\n{diff}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_this_rung_EDITS_NO_COMMITTED_SEED():
    """T3, L1, L1b, L2, L3 and border-ownership stay byte-identical. The only
    admissible edit to a committed file is the ADDITIVE seed_registry entry.

    `--relative` so the paths are reported against the gamma-substrate tree
    rather than the repo root — the claim is about THIS tree's seeds.
    """
    changed = [p for p in _git("diff", "--name-only", "--relative",
                               f"{BASE_SHA}..{RUNG_SHA}", "--", "seeds/").split() if p]
    assert changed == ["seeds/vision_lighting_l4.json"], changed


def test_PROVENANCE_the_rungs_whole_diff_is_only_files_it_OWNS():
    """Process rule 8 / §12.3: the self-audit diffs an IMMUTABLE COMMIT RANGE,
    TRACKED FILES ONLY — never base→worktree, never a repo-wide untracked scan.

    Every path this rung's commits touch must be a file this rung owns. A single
    foreign path here means another agent's in-flight work has been swept in
    (§11 rule 3), and the answer is to revert, not to widen this list.
    """
    owned = {
        "VISION_LIGHTING_L4_PREREG.md",
        "VISION_LIGHTING_L4_RESULTS.md",
        "VISION_PROTOCOL.md",                  # ledger + ladder rows only
        "tools/build_vision_lighting_l4.py",
        "seeds/vision_lighting_l4.json",
        "domains/lighting_l4_world.py",
        "domains/seed_registry.py",            # ADDITIVE registration only
        "scripts/lighting_l4_measure.py",
        "results/lighting_l4_measure.json",
        "tests/test_lighting_l4_migrated.py",
    }
    changed = {p for p in _git("diff", "--name-only", "--relative",
                               f"{BASE_SHA}..{RUNG_SHA}").split() if p}
    assert changed <= owned, f"FOREIGN paths in this rung's diff: {changed - owned}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_PROVENANCE_the_seed_registry_edit_is_PURELY_ADDITIVE():
    """The one committed file this rung edits. It must only ADD lines — a
    deletion there would mean another rung's registration was disturbed."""
    diff = _git("diff", "--relative", f"{BASE_SHA}..{RUNG_SHA}",
                "--", "domains/seed_registry.py")
    removed = [ln for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    assert removed == [], f"the registry edit removed lines: {removed}"
    assert "vision_lighting_l4" in diff


def test_every_TERM_used_by_this_seed_already_EXISTS_in_the_engine():
    types = set(re.findall(r'"type": "([A-Za-z_]+)"', json.dumps(_seed()["rules"])))
    with open(os.path.join(ROOT, "runners", "dsl", "src", "jsonio.rs")) as f:
        src = f.read()
    missing = [t for t in types if f'"{t}" =>' not in src]
    assert missing == [], missing


def test_the_flag_is_absence_tolerant_and_never_PickUnique():
    """Process rule 3. PickUnique on a params node returns None when absent,
    which silently CHANGES behaviour instead of reading as OFF."""
    body = json.dumps(_seed()["rules"])
    assert "PickUnique" not in body
    assert '"type": "MaxOver"' in body
    # and it must be inert in a graph that never loaded the params node
    s, ag = boot_core()
    h = l4w.add_field(s, [_combined_row()])
    l4w.tick(s)
    assert l4w.written_l4_attrs(s, h) == []


def test_the_predicate_is_L2s_slowvar_clause_with_the_QUANTIFIER_MOVED():
    """The audit's central claim, gated structurally: L4's core predicate is the
    SAME cross-multiplied ratio-agreement shape L2's `_slowvar_clause` uses,
    with the index pair (locale,locale) replaced by (channel,channel)."""
    with open(os.path.join(ROOT, "tools", "build_vision_lighting_l2.py")) as f:
        l2 = f.read()
    assert "_slowvar_clause" in l2
    # L2's shape: Lte(Abs(Minus(Times([..]), Times([..]))), Plus([Times([..]), ..]))
    rules = {r["name"]: r for r in _seed()["rules"]}
    body = json.dumps(rules["l4_classify_illuminant"]["where"])
    for t in ("Lte", "Abs", "Minus", "Times", "Plus"):
        assert f'"type": "{t}"' in body, t
    # cross-multiplied, never divided, in the DECISION path
    assert '"type": "Div"' not in body, "a ratio was divided into a float"


def test_Times_is_never_written_in_the_a_b_EMPTY_PRODUCT_form():
    """Process rule 4. An empty product is 1, so the a/b form would collapse
    every D_XY to |1-1| = 0 and call EVERY adjacency a shadow."""
    for t in re.finditer(r'\{"type": "Times"[^}]*', json.dumps(_seed()["rules"])):
        assert '"items"' in t.group(0), t.group(0)


def test_no_python_decision_in_the_adapter():
    """CLAUDE.md §0, on the AST rather than on a grep: no `if`/`else` expression
    or statement anywhere in the world adapter."""
    path = os.path.join(ROOT, "domains", "lighting_l4_world.py")
    with open(path) as f:
        tree = ast.parse(f.read())
    bad = [type(n).__name__ for n in ast.walk(tree)
           if isinstance(n, (ast.If, ast.IfExp))]
    assert bad == [], f"{path} contains Python decisions: {bad}"


def test_the_seed_declares_its_own_BOUNDS():
    """§8. The predicted negatives must be named in the seed itself, not only in
    the write-up — a bound that lives only in prose is a bound that gets lost."""
    d = _seed()["description"]
    for phrase in ("CHROMATIC", "PROPORTIONAL", "MULTI-ILLUMINANT",
                   "NOT transitive", "DOES NOT RECOVER REFLECTANCE"):
        assert phrase in d, phrase
