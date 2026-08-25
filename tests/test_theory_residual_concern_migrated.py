"""A TARGET-GRAIN RESIDUAL OPENS A CONCERN — gate for
`seeds/theory_residual_concern.json`.

`THEORY_AS_SHAPE_RESULTS.md` established that a theory can be a held solution
shape: a target signature decodes against the codebook like any other grain, and
the residual is exactly the work remaining. It also established that the obvious
next move is wrong. Minting the residual turns *"my theory needs radar"* into
*"radar is a held capability"* — the loop reports `covered` and `residual: []`
while nothing was built and nothing was learned.

The asymmetry is exact:

  * at the OBSERVATION grain a residual is EVIDENCE. The world supplied something
    the codebook could not explain, so minting a quantum is warranted;
  * at the TARGET grain a residual is a DEMAND. Nothing supplied it, and minting
    would assert a capability on the strength of wanting one.

So the residual OPENS A CONCERN, and the concern closes only when the residual
genuinely empties. These tests pin both halves — that the concern opens, and (the
one that actually matters) that nothing here can close it by wishing.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
import sys

sys.path.insert(0, str(ROOT / "scripts"))
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

SEEDS = ["theory_residual_concern"]

HELD = {
    "wing": [["has", "airframe", "wing"], ["has", "wing", "aileron"]],
    "engine": [["has", "airframe", "engine"], ["has", "engine", "throttle"]],
}


def _world(theory_signature, held=None):
    """An agent holding one theory, over a codebook of held capabilities."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    for name, sig in (HELD if held is None else held).items():
        s.add_node("ShapeSignature", {"name": name, "kind": "capability",
                                      "signature": sig, "dim_types": []})
    agent = s.add_node("Agent", {})
    th = s.add_node("Theory", {"name": "probe", "signature": theory_signature,
                               "tr_epoch": 1.0, "tr_epoch_seen": 0.0, "tr_noted": 0.0})
    s.add_edge(agent, "holds_theory", th)
    s.tick(100_000)
    return s, agent, th


def _concerns(s):
    return [s.node(c)["attrs"] for c in s.nodes("SelfConcern")
            if s.node(c)["attrs"].get("source") == "theory_residual"]


def test_an_unreachable_theory_opens_a_concern():
    """The residual is the work remaining, and it becomes a filed gap."""
    s, _ag, th = _world([["has", "airframe", "wing"], ["has", "airframe", "radar"]])
    res = s.node(th)["attrs"].get("tr_residual")
    assert res, "fixture produced no residual — the theory is already reachable"

    cs = _concerns(s)
    assert len(cs) == 1, f"expected exactly one concern, got {len(cs)}"
    assert cs[0]["kind"] == "capability_gap"
    assert cs[0]["status"] == "noted"
    assert cs[0]["content"] == res, (
        f"the concern's content is not the residual: {cs[0]['content']} vs {res}")


def test_the_theory_does_NOT_become_reachable_by_wanting_it():
    """THE TEST THIS SEED EXISTS FOR.

    The naive loop mints the residual as a held part, and then reports the theory
    covered with an empty residual — success, having built nothing. Nothing here
    may do that: the codebook must be unchanged and the residual must still be
    outstanding after the fixpoint."""
    before = {"wing", "engine"}
    s, _ag, th = _world([["has", "airframe", "wing"], ["has", "airframe", "radar"]])

    names = {s.node(n)["attrs"].get("name") for n in s.nodes("ShapeSignature")}
    assert names == before, (
        f"the codebook GREW to {names} — a target-grain residual was minted as a "
        f"held capability, which asserts a capability on the strength of wanting one")

    assert s.node(th)["attrs"].get("tr_residual"), (
        "the residual emptied without anything producing the missing part")
    assert _concerns(s)[0]["status"] == "noted", "the concern closed itself"


def test_a_reachable_theory_opens_nothing():
    """No residual, no concern. Otherwise the seed files a gap for every goal."""
    s, _ag, th = _world([["has", "airframe", "wing"], ["has", "wing", "aileron"]])
    assert not s.node(th)["attrs"].get("tr_residual"), "fixture is not reachable"
    assert _concerns(s) == [], "a fully reachable theory opened a concern"


def test_the_same_gap_is_filed_once():
    """Deduped by content, matching gap_awareness's own guard — the decode
    re-arms whenever the codebook grows, and each re-arm must not re-file."""
    s, agent, th = _world([["has", "airframe", "wing"], ["has", "airframe", "radar"]])
    # force several more decode/open passes
    for bump in (2.0, 3.0, 4.0):
        s.set_attr(th, "tr_epoch", bump)
        s.set_attr(th, "tr_noted", 0.0)
        s.tick(100_000)
    assert len(_concerns(s)) == 1, (
        f"{len(_concerns(s))} concerns for one gap — the content dedup is not holding")


def test_the_concern_resolves_only_when_the_part_IS_genuinely_held():
    """The honest close: supply the missing capability by the route that had to
    produce it, re-arm the decode, and the residual empties — at which point the
    concern it opened is marked resolved.

    This is the positive control for the previous test. Without it, 'the concern
    never closes' would pass trivially for a seed that simply never closes
    anything."""
    s, _ag, th = _world([["has", "airframe", "wing"], ["has", "airframe", "radar"]])
    assert _concerns(s)[0]["status"] == "noted"

    # something else actually produced the capability
    s.add_node("ShapeSignature", {"name": "radar", "kind": "capability",
                                  "signature": [["has", "airframe", "radar"]],
                                  "dim_types": []})
    s.set_attr(th, "tr_epoch", 2.0)          # codebook grew -> re-arm the decode
    s.tick(100_000)

    assert not s.node(th)["attrs"].get("tr_residual"), (
        "the residual did not empty even though the part is now held")
    assert _concerns(s)[0]["status"] == "resolved", (
        "the residual emptied but the concern stayed open")
