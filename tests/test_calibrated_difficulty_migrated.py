"""GIVE THE AGENT EXACTLY THE SURPRISE IT EXPECTS.

`learning_progress_curiosity` gates attention on the RATE of surprise reduction —
Schmidhuber/Oudeyer compression progress — and its own G1/G2 gates establish that
this correctly LEAVES a noisy source and LEAVES a resolved one. Both are defences
against sources that cannot be learned from.

There is no term for a source that is perfectly learnable and never ends.

An adversary that renews the difficulty exactly when it would have been exhausted
keeps `learning_progress` positive indefinitely, and every signal the agent holds
reads as healthy learning — because it IS learning. It just never finishes.

This is the strongest attack in the aperture arc and the one that survives the
most defences:

  * it does not move the tube (`DEFORMATION_BENEFICIARY_RESULTS.md` §6) — no
    re-aiming is required;
  * it does not need the victim to misattribute (§8);
  * it does not produce an EMPTY residual (§5) — it produces a healthy one, which
    is why nothing files a concern;
  * and it survives `learning_progress_curiosity` v1.1.0, whose guards address the
    UNASSESSABLE observation. These observations are perfectly assessable.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate.boot_core import boot_core  # noqa: E402
import learning_progress_measure as LP  # noqa: E402

T = 60
DESCENT = [21, 18, 15, 12, 9, 6, 3, 0]
EXHAUSTIBLE = DESCENT + [0] * (T - len(DESCENT))
CALIBRATED = [DESCENT[t % len(DESCENT)] for t in range(T)]


def _attended_ticks(seq):
    s, agent = boot_core()
    inner = s._inner
    inner.load_seed_manifest(LP.manifest_for(LP.SEED_ID), agent)
    hub = s.add_node("CuriosityHub", {"kind": "probe"})
    p = dict(LP.PARAMS)
    p["enabled"], p["mode"] = 1.0, 1.0
    cp = s.add_node("HeldCuriosityParams", p)
    inner.add_edge_unchecked(hub, "has_curiosity_params", cp)
    item = s.add_node("AttentionItem", dict(LP.ITEM_INIT))
    inner.add_edge_unchecked(hub, "has_attention_item", item)
    attended, last = 0, {}
    for t in range(T):
        s.set_attr(item, "obs", float(seq[t]))
        s.set_attr(item, "input_epoch", float(t))
        inner.run_rules()
        a = s.node(item)["attrs"]
        attended += 1 if float(a.get("attended", 0.0)) > 0 else 0
        last = {k: float(a.get(k, 0.0))
                for k in ("residual", "learning_progress", "interest", "attended")}
    return attended, last


def test_an_exhaustible_source_is_LEFT_once_it_is_learned():
    """The control, and the seed's own designed behaviour. A real thing to learn
    is learned, progress falls away, interest decays, and attention moves on."""
    attended, last = _attended_ticks(EXHAUSTIBLE)
    assert attended < T // 4, f"attended {attended}/{T} on an exhausted source"
    assert last["interest"] == 0.0
    assert last["attended"] == 0.0


def test_a_CALIBRATED_source_is_never_left_and_every_signal_reads_healthy():
    """THE ATTACK. The same difficulty, renewed exactly when it would have run
    out. The agent attends almost every tick, its interest never decays, and
    nothing anywhere reports a problem — because there is no problem to report at
    the level the agent can see. It is learning. It simply never finishes."""
    attended, last = _attended_ticks(CALIBRATED)
    assert attended > T - 5, f"only attended {attended}/{T} — the source ran out"
    assert last["interest"] > 0.0, "interest decayed; the calibration is too coarse"
    assert last["residual"] > 0.0, "the residual emptied — this is the §5 case, not this one"
    assert last["learning_progress"] != 0.0, (
        "progress went flat — a flat signal is the exhausted case and would be left")


def test_the_curiosity_gate_has_no_term_for_INEXHAUSTIBLE():
    """Why the existing defences do not fire.

    G1 leaves a NOISY source (unlearnable). G2 leaves a RESOLVED source (finished).
    Both discriminate on whether learning is possible or complete. A calibrated
    source is neither noisy nor resolved: it is perfectly learnable, perpetually —
    and the gate has no term that separates 'learnable' from 'learnable and
    endless'.

    Pinned as a known absence so that adding such a term fails this test rather
    than passing quietly."""
    exhausted, _ = _attended_ticks(EXHAUSTIBLE)
    calibrated, _ = _attended_ticks(CALIBRATED)
    assert calibrated > 5 * exhausted, (
        f"calibrated {calibrated} vs exhausted {exhausted} — if this ratio has "
        f"collapsed, the gate has acquired a term for inexhaustibility")
