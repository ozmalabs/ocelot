"""Gates for the PERCEPT->IDENTITY SEAM (`VISION_IDENTITY_SEAM_PREREG.md`).

Every gate here is POSITIVE-CONTROLLED: it has been seen to go RED as well as
green (protocol section 12.3 — "a gate you have only ever seen pass is not a
gate you have tested"). Three of them exist because of specific failures this
arc has already paid for:

* `test_..._writes_NO_numeric_threshold` — section 13, ported from the verdict rung.
* `test_the_floor_MOVES_as_the_codebook_grows` — the **G5 RESPONSIVENESS** gate
  the video-probe re-run earned: an instrument that is alive, deterministic and
  INSENSITIVE passes every other check and gives a confident wrong answer.
* `test_the_mint_gate_can_REFUSE` — section 1 clause 4: an arm that never mints
  and an arm that always mints both score perfectly on persistence.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

SEED_PATH = ROOT / "seeds" / "vision_identity_seam.json"
REGION = 6
#: Burned block for this rung's gates (72000-72999).
GATE_SEED = 72900


def _manifest():
    return json.loads(SEED_PATH.read_text())


def _tile(rng):
    q = rng.randint(0, 4, (REGION, REGION))
    g = rng.randint(0, 256, (REGION, REGION)).astype(float)
    return q, g


def _world(arm="ncc", manifest=None):
    from domains import identity_seam_world as sw
    if manifest is None:
        return sw.SeamWorld(arm)
    # Install a MUTATED manifest instead of the shipped one — the mutation
    # test's only route, and it never touches the file on disk.
    w = sw.SeamWorld("stock")
    w.native.load_seed_manifest(manifest, w.ag)
    w.arm = arm
    for p in w.s.nodes("IdentitySeamParams"):
        w.s.set_attr(p, "seam", 1.0)
    return w


# --------------------------------------------------------------- section 13
def test_the_seam_writes_NO_numeric_threshold():
    """No number may be chosen. The floor is measured or it is not a floor."""
    blob = json.dumps(_manifest()["rules"])
    nums = {float(m) for m in re.findall(r'"value":\s*(-?[\d.]+(?:e[+-]?\d+)?)',
                                         blob)}
    # 0/1/1.0 are structural (counts, boolean flags); 0.5 is the arming
    # discriminator on a 0.0/1.0 flag, the idiom every vision seed uses;
    # -1e18 is MaxOver's empty-source sentinel.
    assert nums <= {0.0, 1.0, 0.5, -1e18}, f"magic number in the seam: {nums}"


def test_the_seed_ships_OFF():
    """Section 9: installing this seed must change nothing until armed."""
    node = _manifest()["nodes"][0]
    assert node["type"] == "IdentitySeamParams"
    assert node["attrs"]["seam"] == 0.0


def test_the_seam_adds_no_new_Term():
    """No new Rust and no new Term (declared in the pre-registration)."""
    blob = json.dumps(_manifest()["rules"])
    used = set(re.findall(r'"type":\s*"([A-Z][A-Za-z0-9]*)"', blob))
    known = {"Var", "Attr", "Lit", "Eq", "Not", "And", "Gt", "Lt", "Count",
             "Filter", "NodesOfType", "Neighbours", "MaxOver", "Argmax", "Dot",
             "IfThenElse", "IndexAt", "Plus"}
    assert used <= known, f"unexpected Term(s): {used - known}"


# ------------------------------------------------------- section 1 clause 4
def test_the_mint_gate_can_REFUSE():
    """POSITIVE CONTROL ON THE ARM. A genuinely novel tile must mint; an
    identical re-presentation of a held tile must NOT.

    Both failure modes look like success, so both directions are asserted in
    one test: an arm that always mints passes the first half and fails the
    second, and an arm that never mints does the reverse."""
    from domains import identity_seam_world as sw
    rng = np.random.RandomState(GATE_SEED)
    w = _world("ncc")
    w.calibrate(rng, 8)
    w.run()

    q, g = _tile(rng)
    k0 = w.codebook_size()
    w.present(q, g, tag="novel_a")
    w.run()
    assert w.codebook_size() > k0, "a novel tile did not mint — the gate is inert"

    k1 = w.codebook_size()
    w.present(q, g, tag="repeat_a")          # byte-identical re-presentation
    w.run()
    assert w.read_last()["status"] == "is_held", \
        "an identical re-presentation was not recognised as already held"
    assert w.codebook_size() == k1, "an identical tile minted a second identity"


def test_distinct_tiles_do_not_collapse_to_one_identity():
    """CLAUSE 2 in miniature. An identity layer that merges everything scores
    perfectly on persistence, so distinctness gets its own gate."""
    rng = np.random.RandomState(GATE_SEED + 1)
    w = _world("ncc")
    w.calibrate(rng, 8)
    w.run()
    idents = []
    for j in range(6):
        q, g = _tile(rng)
        w.present(q, g, tag=f"d{j}")
        w.run()
        idents.append(w.read_last()["identity"])
    assert len(set(idents)) > 1, \
        f"six independent random tiles collapsed to one identity: {idents}"


# --------------------------------------------- G5 RESPONSIVENESS (the new one)
def test_the_floor_MOVES_as_the_codebook_grows():
    """G5: the floor must VARY WITH THE THING BEING VARIED, not merely be
    non-zero.

    A floor measured once against an empty codebook and never re-armed would be
    alive, deterministic, and INSENSITIVE — it would stop refusing as K grew and
    every other gate here would still pass. `is_recalib` exists for exactly this
    and this test is what proves it fires."""
    rng = np.random.RandomState(GATE_SEED + 2)
    w = _world("ncc")
    w.calibrate(rng, 8)
    w.run()
    floors = []
    for j in range(12):
        q, g = _tile(rng)
        w.present(q, g, tag=f"f{j}")
        w.run()
        floors.append(w.read_last()["is_floor"])
    seen = [f for f in floors if f is not None]
    assert len(seen) >= 6, f"the floor was never written: {floors}"
    # Section 3.1's rule: determinism pins the noise at zero, so the test is
    # simply *did it move at all* across the sweep.
    assert len(set(round(float(f), 12) for f in seen)) > 1, \
        f"the floor is CONSTANT across a growing codebook — INSENSITIVE: {seen}"


def test_the_floor_is_measured_against_the_same_codebook_not_frozen():
    """The floor must RISE as the codebook grows: more held signatures give
    noise more chances to score well. A falling or flat floor means the
    calibration probes are not being re-scored."""
    rng = np.random.RandomState(GATE_SEED + 3)
    w = _world("ncc")
    w.calibrate(rng, 8)
    w.run()
    floors = []
    for j in range(16):
        q, g = _tile(rng)
        w.present(q, g, tag=f"m{j}")
        w.run()
        f = w.read_last()["is_floor"]
        if f is not None:
            floors.append(float(f))
    assert floors[-1] > floors[0], \
        f"floor did not rise with the codebook: {floors[0]} -> {floors[-1]}"


# ------------------------------------------------------------ mutation test
def test_inverting_the_decision_turns_this_gate_RED():
    """A gate that has never failed is not a gate. Swap the IfThenElse branches
    in `is_decide` and the refusal gate must break."""
    man = copy.deepcopy(_manifest())
    dec = next(r for r in man["rules"] if r["name"] == "is_decide")
    for eff in dec["effects"]:
        t = eff[-1].get("__term__") if isinstance(eff[-1], dict) else None
        if isinstance(t, dict) and t.get("type") == "IfThenElse":
            t["then"], t["other"] = t["other"], t["then"]
    man["id"] = "vision_identity_seam_INVERTED"

    from domains import identity_seam_world as sw
    rng = np.random.RandomState(GATE_SEED + 4)
    w = _world("ncc", manifest=man)
    w.calibrate(rng, 8)
    w.run()

    # The shipped gate is a CONJUNCTION -- a novel tile mints AND an identical
    # repeat is held. The mutation must break at least one half, and the test
    # must check BOTH halves or it is only testing the half that survives.
    q, g = _tile(rng)
    k0 = w.codebook_size()
    w.present(q, g, tag="inv_a")
    w.run()
    minted_novel = w.codebook_size() > k0

    k1 = w.codebook_size()
    w.present(q, g, tag="inv_repeat")
    w.run()
    held_repeat = w.read_last()["status"] == "is_held"
    same_k = w.codebook_size() == k1

    assert not (minted_novel and held_repeat and same_k), (
        "the inverted seed still passes the refusal gate — the gate is vacuous "
        f"(minted_novel={minted_novel} held_repeat={held_repeat} "
        f"same_k={same_k})")
    # And name WHICH half died, so a future change that breaks the other half
    # cannot pass this test by accident.
    assert not minted_novel, (
        "inverting is_decide should stop novel tiles minting; it did not — "
        "the mutation is not reaching the decision")


# ------------------------------------------------- section 12.3 provenance
def test_this_rung_adds_NO_rust():
    """Pinned to THIS RUNG'S OWN COMMIT RANGE, never to a mutable tree and
    never to HEAD (section 12.3 + the endpoint guard)."""
    import subprocess
    base, tip = "212212e30b767466eca100f80e023f22365bd8d9", "a29218cc"
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{tip}", "--",
         "runners/dsl/src", "runners/dsl/Cargo.toml"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        pytest.skip(f"range not resolvable in this tree: {out.stderr.strip()}")
    assert out.stdout.strip() == "", \
        f"this rung touched Rust: {out.stdout.strip()}"
