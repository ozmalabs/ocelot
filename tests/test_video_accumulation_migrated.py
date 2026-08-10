"""VIDEO ACCUMULATION — the rung's own gates.

`VISION_VIDEO_ACCUMULATION_PREREG.md` (committed `f9ec8971`, base `5428104a`).

Every gate here is TWO-SIDED where it can be: it asserts the property AND
demonstrates that the check is able to go red. A gate that has never been able
to fail has not been tested.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent


def _aw():
    from domains import video_accumulation_world as aw
    return aw


# ---------------------------------------------------------------- the split
def test_the_split_is_disjoint_and_guarded():
    aw = _aw()
    train, held = aw.block_split(150)
    assert len(train) == 90 and len(held) == 50
    assert not (set(train) & set(held))
    # every training frame is >= 2 frames from every held-out frame, i.e. the
    # guard band really exists and a held-out frame is never a training
    # frame's temporal neighbour.
    for h in held:
        assert (h - 1) not in train and (h + 1) not in train
    # non-vacuity: without the guard the property FAILS.
    t2, h2 = aw.block_split(150, guard=0)
    assert any((h + 1) in t2 or (h - 1) in t2 for h in h2)


def test_held_out_frames_never_contribute_a_mint():
    """The mints recorded by the confirmatory run come only from training."""
    import json
    p = ROOT / "results/video_accum.json"
    if not p.exists():
        pytest.skip("confirmatory results absent")
    d = json.load(open(p))
    held = set(d["held"])
    train = set(d["train"])
    for cid, R in d["corpora"].items():
        assert R["mints"], f"{cid}: no mints -- vacuous gate"
        for m in R["mints"]:
            assert m["frame"] in train, f"{cid}: mint from non-training frame"
            assert m["frame"] not in held, f"{cid}: mint from a HELD-OUT frame"


# ----------------------------------------------------------- the read-out
def test_a_minted_observation_does_not_read_as_recognised():
    """THE BLIND READ-OUT THIS RUNG'S CALIBRATION CAUGHT.

    `is_decide` writes `is_held` / `is_novel`; `is_mint` then rewrites
    `is_novel` -> `is_minted`. A read-out testing `status != "is_novel"`
    scores every MINT as a recognition and reads 1.0 on a codebook of pure
    noise. The correct predicate is `status == "is_held"`.
    """
    aw = _aw()
    rng = np.random.RandomState(74910)
    w = aw.AccumWorld("ncc")
    w.calibrate(rng, 8)
    w.run()
    # An empty codebook: nothing can be recognised, so this MUST mint.
    w.present(rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
              rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float),
              tag="probe_0")
    w.run()
    st = w.read_full()["status"]
    assert st == "is_minted", f"expected a mint, got {st!r}"
    # the CORRECT predicate calls this NOT recognised ...
    assert (st == "is_held") is False
    # ... and the INCORRECT one calls it recognised, which is the bug.
    assert (st != "is_novel") is True


# ------------------------------------------------------------ the freeze
def test_the_freeze_holds_the_codebook_and_the_floor():
    aw = _aw()
    rng = np.random.RandomState(74911)
    w = aw.AccumWorld("ncc")
    w.calibrate(rng, 8)
    w.run()
    ents = [(f"e{j}",
             rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
             rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float))
            for j in range(6)]
    w.install_codebook(ents)
    k0 = w.freeze()
    f0 = w._frozen_floor
    for j in range(12):
        w.present(rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
                  rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float),
                  tag=f"ev{j}")
        w.run()
        w.refreeze()
    k1, f1 = w.assert_frozen()
    assert k1 == k0 == 6
    assert f1 == f0


def test_the_freeze_gate_is_ABLE_to_fail():
    """POSITIVE CONTROL. Without `refreeze()` the codebook grows and
    `assert_frozen()` must raise. A freeze gate that cannot go red is not a
    gate (the standing instrument rule)."""
    aw = _aw()
    rng = np.random.RandomState(74912)
    w = aw.AccumWorld("ncc")
    w.calibrate(rng, 8)
    w.run()
    w.install_codebook([("e0",
                         rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
                         rng.randint(0, 256,
                                     (aw.REGION, aw.REGION)).astype(float))])
    w.freeze()
    grew = False
    for j in range(12):
        w.present(rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
                  rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float),
                  tag=f"ev{j}")
        w.run()                      # deliberately NO refreeze()
        if w.codebook_size() > 1:
            grew = True
    assert grew, "the codebook never grew -- the positive control is vacuous"
    with pytest.raises(AssertionError):
        w.assert_frozen()


# -------------------------------------------------- installed == grown
def test_an_installed_codebook_decides_like_a_grown_one():
    """`install_codebook` must not be a different mechanism from minting.
    Grow a codebook, install the SAME tiles into a fresh world, and require
    identical identity decisions on the same observations."""
    aw = _aw()
    rng = np.random.RandomState(74913)
    tiles = [(rng.randint(0, aw.K_LEVELS, (aw.REGION, aw.REGION)),
              rng.randint(0, 256, (aw.REGION, aw.REGION)).astype(float))
             for _ in range(10)]

    a = aw.AccumWorld("ncc")
    a.calibrate(np.random.RandomState(74914), 8)
    a.run()
    grown = []
    for j, (qt, gt) in enumerate(tiles):
        k0 = a.codebook_size()
        a.present(qt, gt, tag=f"t{j}")
        a.run()
        if a.codebook_size() > k0:
            grown.append((f"t{j}", qt, gt))
    assert len(grown) >= 2, "nothing minted -- vacuous"

    b = aw.AccumWorld("ncc")
    b.calibrate(np.random.RandomState(74914), 8)
    b.run()
    b.install_codebook(grown)
    assert b.codebook_size() == a.codebook_size()

    # the same probes must land on the same identities in both worlds
    a.freeze()
    b.freeze()
    for j, (qt, gt) in enumerate(tiles):
        a.present(qt, gt, tag=f"p{j}")
        a.run()
        ra = a.read_full()
        a.refreeze()
        b.present(qt, gt, tag=f"p{j}")
        b.run()
        rb = b.read_full()
        b.refreeze()
        assert ra["status"] == rb["status"], (j, ra, rb)
        assert abs(ra["is_max"] - rb["is_max"]) < 1e-12, (j, ra, rb)


# ------------------------------------------------- section 9 / architecture
BASE = "5428104a"          # this rung's branch base, pinned (§12.3)
RUNG = "6751d03c"          # this rung's LAST OWN commit. BASE..RUNG is IMMUTABLE.


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


def test_this_rung_edits_no_seed_and_no_rust():
    """Section 9: the mechanism under test is UNCHANGED **WITHIN THIS RUNG**.

    PINNED TO `BASE..RUNG`, WHICH IS IMMUTABLE (§12.3).

    This originally compared the LIVE working tree against BASE — for both the
    seed hash and the Rust diff. The claim it makes is about THIS RUNG'S OWN
    DIFF (*this rung edited no seed and added no Rust*); tested against a
    mutable tree it tests instead **whether anyone has done any work since**,
    so it went red the moment a later rung merged Rust and then spent ~54
    commits making a FALSE ACCUSATION against landed, correct work. The Rust
    it named (`shape_decode.rs`, `scale_audit.rs`, …) belongs to rungs that
    merged afterwards; this rung's own range contains none of it.

    `test_colour_bound_k1_migrated.py` pins the same class of claim to
    `BASE_SHA..RUNG_SHA` and is green — same intent, two implementations, and
    only the mutable-tree one rotted. That is the control; this is the fix.

    The underlying FACT was verified independently BEFORE this gate was
    touched (§12.3): `git diff --name-only 5428104a 6751d03c` is 11 files,
    ZERO of them `.rs`, and it touches no `seeds/` path at all.
    """
    for path in ("seeds/vision_identity_seam.json",):
        assert _blob_at(RUNG, path) == _blob_at(BASE, path), \
            f"{path} CHANGED between {BASE} and {RUNG}"
    r = subprocess.run(["git", "diff", "--stat", BASE, RUNG, "--",
                        "runners/dsl/src"], cwd=ROOT, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "", f"Rust source moved IN THIS RUNG:\n{r.stdout}"


VERDICT_KEYS = ("is_max", "is_floor", "identified_as")


def _verdict_comparisons(path):
    """Every `ast.Compare` in `path` that touches the graph's identity verdict,
    OUTSIDE an assert.

    A SUBSTRING AUDIT IS NOT A SELECTOR (protocol section 12). The first
    version of this gate looked for the literal `"is_max >"` and PASSED a
    planted `a["is_max"] > b`, because the `"]` sits between. This walks the
    AST instead. Asserts are exempt by design: a gate comparing values is
    doing its job; the ban is on the adapter DECIDING.
    """
    import ast
    tree = ast.parse(path.read_text())
    src = path.read_text()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            for sub in ast.walk(node):
                sub._in_assert = True
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or getattr(node, "_in_assert",
                                                        False):
            continue
        seg = ast.get_source_segment(src, node) or ""
        if not any(k in seg for k in VERDICT_KEYS):
            continue
        # A PRESENCE guard (`x is None` / `x is not None`) is not a decision
        # over the verdict's VALUE. An ORDERING or EQUALITY on it is.
        if all(isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops) and \
                all(isinstance(c, ast.Constant) and c.value is None
                    for c in node.comparators):
            continue
        hits.append(seg)
    return hits


def test_the_adapter_takes_no_decision_over_graph_state():
    """Source audit, by AST. The adapter may WRITE and READ; it may not
    COMPARE the graph's identity verdict, which is what would make it the
    decider rather than `seeds/vision_identity_seam.json`.

    DECLARED: comparisons on `seam_grown` and `probe_kind` DO occur — they are
    the freeze bookkeeping (which nodes are held, which are calibration
    probes), instrument state and not an identity decision.
    """
    p = ROOT / "domains/video_accumulation_world.py"
    hits = _verdict_comparisons(p)
    assert hits == [], f"adapter decides over the verdict: {hits}"
    # non-vacuity: the walk saw real code with real comparisons in it.
    import ast
    n_cmp = sum(1 for n in ast.walk(ast.parse(p.read_text()))
                if isinstance(n, ast.Compare))
    assert n_cmp >= 5, f"audit is vacuous: only {n_cmp} comparisons parsed"


def test_the_adapter_audit_is_ABLE_to_fail(tmp_path):
    """POSITIVE CONTROL, using the EXACT mutation that defeated the substring
    version of this gate."""
    p = ROOT / "domains/video_accumulation_world.py"
    planted = tmp_path / "planted.py"
    planted.write_text(p.read_text()
                       + '\n\ndef decide(a, b):\n    return a["is_max"] > b\n')
    assert _verdict_comparisons(planted), \
        "the planted decision was NOT caught -- this gate is inert"
