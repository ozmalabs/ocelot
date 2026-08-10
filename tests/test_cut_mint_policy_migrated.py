"""CUT-MINT POLICY — the gates.

`VISION_CUT_MINT_POLICY_PREREG.md`. Every gate here is one a green run could
FAIL, and the two that guard the mechanism are POSITIVE-CONTROLLED with the
exact mutation that would defeat them — because the incumbent rung found its
own adapter audit was INERT and found it only by mutating a green gate.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "17cb3f3d"          # this rung's branch base, pinned (§12.3)
RUNG = "f8c4d904"          # this rung's LAST OWN commit (the results commit;
                           # dbc8dc82 is the merge). BASE..RUNG is IMMUTABLE.
ADAPTER = "domains/cut_mint_world.py"
SEED = "seeds/vision_cut_mint_policy.json"


# --------------------------------------------------------------- provenance
def _blob_at(rev, path):
    """The bytes of `path` at `rev`, from either repo layout."""
    r = subprocess.run(["git", "show", f"{rev}:research/experiments/"
                        f"gamma-substrate/{path}"],
                       cwd=ROOT.parents[2], capture_output=True)
    if r.returncode != 0:
        r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                           capture_output=True)
    assert r.returncode == 0, f"cannot read {path} at {rev}"
    return r.stdout


def test_this_rung_adds_no_rust():
    """The claim: THIS RUNG adds NO Rust.

    PINNED TO `BASE..RUNG`, WHICH IS IMMUTABLE (§12.3).

    This originally diffed BASE against the **live working tree**. That is not
    a test of this rung's claim at all — it is a test of whether ANYONE has
    done any work since, so it goes red the moment any later rung merges Rust,
    and then it is a FALSE ACCUSATION of landed, correct work. It broke at
    `1214b7c6` and was red ~54 commits while this rung's claim stayed true the
    whole time. `test_colour_bound_k1_migrated.py` makes the same class of
    claim against `BASE_SHA..RUNG_SHA` and did not rot; that is the natural
    control, and this is the same fix.

    The underlying FACT was verified independently before this gate was
    touched (§12.3 — *verify the fact, then fix the gate, never the reverse*):
    `git diff --name-only 17cb3f3d f8c4d904` is 11 files, ZERO of them `.rs`
    and none under `runners/dsl/src`.
    """
    r = subprocess.run(["git", "diff", "--stat", BASE, RUNG, "--",
                        "runners/dsl/src"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", f"Rust source moved IN THIS RUNG:\n{r.stdout}"


@pytest.mark.parametrize("path", ["seeds/vision_identity_seam.json",
                                  "seeds/vision_cut_abstention.json"])
def test_the_seeds_this_rung_reuses_are_byte_unchanged(path):
    """The mechanism is *the incumbent seeds, unedited* plus one new rule. If
    either moved WITHIN THIS RUNG, every number here is attributable to
    something else.

    Pinned to `BASE..RUNG` for the same reason as the gate above: this
    compared the LIVE file against BASE, so a later rung legitimately editing
    either seed would have reddened this rung's provenance gate and accused it
    of an edit it never made. It is green today only because nobody has
    touched those two seeds yet — a latent instance of the same defect, fixed
    here rather than left armed.
    """
    assert _blob_at(RUNG, path) == _blob_at(BASE, path), \
        f"{path} CHANGED between {BASE} and {RUNG}"


# ------------------------------------------------------------- §13: no knob
def _literals(term, out):
    if isinstance(term, dict):
        if term.get("type") == "Lit":
            out.append(term.get("value"))
        for v in term.values():
            _literals(v, out)
    elif isinstance(term, list):
        for v in term:
            _literals(v, out)


def test_the_policy_seed_contains_no_tuned_number():
    """§13. The policy reads a FLAG another rule wrote; it must not carry a
    threshold, a window or a magnitude of its own. The only numerals allowed
    are structural: 0.5 (the seam's own arming midpoint idiom), 1 (the
    `is_cut` flag / the `mint_abstained` mark), 0 (a count)."""
    seed = json.loads((ROOT / SEED).read_text())
    lits = []
    _literals(seed["rules"], lits)
    nums = {v for v in lits if isinstance(v, (int, float))
            and not isinstance(v, bool)}
    assert nums <= {0, 0.5, 1}, f"a tuned number is in the seed: {nums}"
    # NON-VACUITY: the walk must have SEEN literals, or it proves nothing.
    assert len(lits) >= 5, f"literal walk is vacuous: {lits}"


def test_the_policy_seed_ships_disarmed():
    """§9. Every committed accumulation number must reproduce."""
    seed = json.loads((ROOT / SEED).read_text())
    armed = [n["attrs"]["armed"] for n in seed["nodes"]
             if n["type"] == "CutMintParams"]
    assert armed == [0.0], armed


# ------------------------------------------------- the adapter takes no branch
VERDICT_KEYS = ("is_max", "is_floor", "identified_as", "is_cut",
                "mint_abstained", "status")
WRITE_PATH = ("__init__", "hold_sequence", "present_at", "_split_at_mint")


def _verdict_comparisons_in_write_path(path):
    """Every `ast.Compare` touching a verdict key inside a WRITE-PATH function.

    A SUBSTRING AUDIT IS NOT A SELECTOR (§12): the incumbent's first version of
    this gate looked for the literal `"is_max >"` and PASSED a planted
    `a["is_max"] > b`, because the `"]` sits between. This walks the AST.

    Read-back methods are exempt BY NAME and the exemption is declared: a
    reader that reports which steps the graph marked must compare `is_cut`, and
    that is reporting, not deciding. Asserts are exempt for the same reason the
    incumbent exempts them — a gate comparing values is doing its job.
    """
    src = path.read_text()
    tree = ast.parse(src)
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fn.name not in WRITE_PATH:
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Assert):
                for sub in ast.walk(node):
                    sub._in_assert = True
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare) or \
                    getattr(node, "_in_assert", False):
                continue
            seg = ast.get_source_segment(src, node) or ""
            if not any(k in seg for k in VERDICT_KEYS):
                continue
            # A PRESENCE guard (`x is None` / `x is not None`) is not a
            # decision over the verdict's VALUE. Ordering or equality is.
            if all(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops) \
                    and all(isinstance(c, ast.Constant) and c.value is None
                            for c in node.comparators):
                continue
            hits.append((fn.name, seg))
    return hits


def test_the_adapter_takes_no_decision_over_graph_state():
    p = ROOT / ADAPTER
    hits = _verdict_comparisons_in_write_path(p)
    assert hits == [], f"the adapter decides in its write path: {hits}"
    n_cmp = sum(1 for n in ast.walk(ast.parse(p.read_text()))
                if isinstance(n, ast.Compare))
    assert n_cmp >= 3, f"audit is vacuous: only {n_cmp} comparisons parsed"


def test_the_adapter_audit_is_ABLE_to_fail(tmp_path):
    """POSITIVE CONTROL, with the EXACT mutation that defeated the substring
    version of this gate — planted INSIDE the write path."""
    p = ROOT / ADAPTER
    src = p.read_text()
    marker = "    def present_at(self, qtile, gtile, *, tag, frame):\n"
    assert marker in src, "the write-path anchor moved; the control is blind"
    planted = tmp_path / "planted.py"
    planted.write_text(src.replace(
        marker, marker + '        if self.s.node(0)["is_max"] > 0.5:\n'
                         '            pass\n'))
    assert _verdict_comparisons_in_write_path(planted), \
        "the planted decision was NOT caught -- this gate is inert"


# --------------------------------------------------- the split is verbatim
def test_the_split_seam_is_the_seam_verbatim():
    """The policy interposes by INSTALL ORDER, not by re-authoring. The two
    halves must reconstitute the seam file's rule list exactly."""
    from substrate.seed_loader import manifest_for
    from domains.cut_mint_world import _split_at_mint

    seam = manifest_for("vision_identity_seam")
    pre, mint = _split_at_mint(seam)
    assert [r["name"] for r in mint["rules"]] == ["is_mint"]
    rebuilt = {r["name"]: r for r in pre["rules"] + mint["rules"]}
    original = {r["name"]: r for r in seam["rules"]}
    assert set(rebuilt) == set(original)
    for n in original:
        assert json.dumps(rebuilt[n], sort_keys=True) == \
            json.dumps(original[n], sort_keys=True), f"{n} was re-authored"
    # and the split half installs no duplicate nodes/productions
    assert mint["nodes"] == [] and mint["productions"] == []


# ------------------------------------------------------------ the mechanism
def _synthetic(n_pre=5, n_post=5, seed=75900):
    """Two shots with a hard cut between them. INPUT CONSTRUCTION."""
    rng = np.random.RandomState(seed)
    a = rng.randint(0, 256, (24, 24)).astype(float)
    b = rng.randint(0, 256, (24, 24)).astype(float)
    f = [np.clip(a + rng.randint(0, 3, (24, 24)), 0, 255)
         for _ in range(n_pre)]
    f += [np.clip(b + rng.randint(0, 3, (24, 24)), 0, 255)
          for _ in range(n_post)]
    return f


def _grow(policy, frames, *, seed=75901):
    from domains.cut_mint_world import CutMintWorld
    import domains.video_accumulation_world as aw
    w = CutMintWorld(policy=policy)
    w.calibrate(np.random.RandomState(seed), 8)
    w.run()
    w.hold_sequence(frames)
    q = [aw.quantize(f) for f in frames]
    qr = [aw.regions_of(x) for x in q]
    gr = [aw.grey_regions_of(f) for f in frames]
    mints = []
    for t in range(len(frames)):
        for i in range(16):
            k = w.codebook_size()
            w.present_at(qr[t][i], gr[t][i], tag=f"{t}_{i}", frame=t)
            w.run()
            if w.codebook_size() > k:
                mints.append((t, i))
    return w, mints


def test_the_policy_rule_is_installed_between_decide_and_mint():
    """Load order is the mechanism (`Substrate::run_rules` schedules every
    dirty rule in ONE pass in index order), so the position is a gate."""
    from domains.cut_mint_world import CutMintWorld
    w = CutMintWorld(policy=False)
    names = [r["name"] for r in w.native.export_rules()]
    assert names.index("is_decide") < names.index("cm_abstain_mint") \
        < names.index("is_mint"), names[-8:]


def test_disarmed_growth_is_identical_to_the_incumbent():
    """§9 AND the check that makes the duplicated boot trustworthy: with the
    policy DISARMED this world must grow the incumbent `AccumWorld`'s codebook
    exactly — same K, same mints, same frames and regions."""
    import domains.video_accumulation_world as aw
    frames = _synthetic()
    w, mints = _grow(False, frames)

    ref = aw.AccumWorld("ncc")
    ref.calibrate(np.random.RandomState(75901), 8)
    ref.run()
    q = [aw.quantize(f) for f in frames]
    qr = [aw.regions_of(x) for x in q]
    gr = [aw.grey_regions_of(f) for f in frames]
    rmints = []
    for t in range(len(frames)):
        for i in range(16):
            k = ref.codebook_size()
            ref.present(qr[t][i], gr[t][i], tag=f"{t}_{i}")
            ref.run()
            if ref.codebook_size() > k:
                rmints.append((t, i))
    assert w.codebook_size() == ref.codebook_size()
    assert mints == rmints, "the load-order split moved the disarmed result"


def test_armed_policy_declines_to_mint_at_the_marked_frames():
    """The headline mechanism. The graph marks the cut step itself, and every
    observation of the two frames incident on it is declined."""
    frames = _synthetic()
    w, mints = _grow(True, frames)
    assert w.marked_steps() == [4], w.step_mags()
    # frames 4 and 5 are the ones incident on step 4
    assert not [t for t, _ in mints if t in (4, 5)], mints
    # and it left a trace a reader can find. EXACTLY 16 — one per region of
    # frame 5. Frame 4 contributes NONE, and that is the policy behaving
    # correctly rather than a shortfall: by frame 4 the shot is already held,
    # so those observations are RECOGNISED, never novel, and there is no mint
    # to decline. The rule declines mints, not recognitions.
    ab = w.abstentions()
    assert len(ab) == 16, ab[:3]
    assert {a["obs_key"].split("_")[0] for a in ab} == {"5"}
    assert {a["reason"] for a in ab} == {"cut_marked"}


def test_the_abstention_gate_is_ABLE_to_fail():
    """POSITIVE CONTROL for the gate above: with the SAME frames and the SAME
    seed, the DISARMED world DOES mint at those frames. If it did not, the
    test above would pass on a world where nothing happens."""
    frames = _synthetic()
    w, mints = _grow(False, frames)
    assert [t for t, _ in mints if t in (4, 5)], \
        "the disarmed world mints nothing there -- the armed gate is vacuous"
    assert w.marked_steps() == [], "a disarmed world must mark nothing"
    assert w.abstentions() == []


def test_the_policy_does_not_touch_the_seam_verdict():
    """`identified_as` is deliberately left intact, so the graph still holds
    what it WOULD have done and the cost stays measurable."""
    frames = _synthetic()
    w, _ = _grow(True, frames)
    declined = [w.s.node(n)["attrs"] for n, _ in w._obs
                if w.s.node(n)["attrs"].get("mint_abstained") == 1]
    assert declined, "nothing was declined -- gate is vacuous"
    assert all(a.get("identified_as") is not None for a in declined)
    assert all(a.get("status") == "cm_abstained" for a in declined)
