"""test_context_model — ORDER-N CONTEXT as the agent's OWN COLLAPSE FACULTY at the context
timescale, with an OPEN-ENDED codebook that MINTS a new context dimension on a residual that fits
none (dynamic quantization). Discriminative, donkey=0. Gates:

  1. SEEDED DIMS — cadence, place, and time-on-BOTH-ends (each party's local time, duration/gap) are
     modeled and CONSOLIDATE over turns. Print the model.
  2. ADD-NEW-CONTEXT (headline) — a cue that fits no seeded dimension MINTS a new context dimension:
     the codebook GROWS and a re-decode RECOGNIZES it. Dynamic quantization at the context timescale,
     via the sd-loop's mint-on-residual (run_collapse's on_gap), not a hand-added enum entry.
  3. SALIENCE -> RELEVANCE — a turn where one dim shifts (place changes) makes THAT dim salient (the
     residual) and a steady dim not; salience IS the residual and picks the relevant context.
  4. FEEDS IDENTITY — a richer context shift (beyond time_gap/place) strengthens the interlocutor
     re-attribution (a bigger context residual tips identity more decisively); salient context is
     available to the Conceptualizer.
  5. COLLAPSE/SD-NATIVE — the decode+mint route through run_collapse (the DomainPlug); source audit:
     no bespoke residual/quantizer, no fixed-enum context.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter                # noqa: E402
from substrate.boot_all import load_all_seeds                   # noqa: E402
import domains.context_model as cm                              # noqa: E402
import domains.interlocutor_model as im                         # noqa: E402


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


# A steady conversation: same place, same local times on both ends, growing duration.
STEADY = dict(place="chat", time_self=14, time_other=9, duration=1, gap=0)


# ===========================================================================
# 1. SEEDED DIMS — cadence / place / time-on-both-ends consolidate over turns
# ===========================================================================
def test_seeded_dims_model_and_consolidate():
    a = _agent()
    for i, t in enumerate(["Hi there, how are you doing today?",
                           "I wanted to ask about the project timeline please.",
                           "Thanks, that is very helpful indeed."]):
        ctx = dict(STEADY); ctx["duration"] = i + 1
        cm.observe_turn(a, t, context=ctx)
    snap = cm.model_snapshot(a)
    print("CONTEXT MODEL:", snap)
    # the seeded dims are all present in the codebook and carry accumulated value counts.
    for d in cm.SEEDED_DIMS:
        assert d in snap["codebook"], f"seeded dim {d} not registered"
        assert d in snap["feat_counts"] and sum(snap["feat_counts"][d].values()) >= 1
    # time on BOTH ends is modeled distinctly (self afternoon, other morning) — not one clock.
    assert "afternoon" in snap["feat_counts"]["time_self"]
    assert "morning" in snap["feat_counts"]["time_other"]
    # consolidation: place is steady across 3 turns -> one value, counted 3x.
    assert snap["feat_counts"]["place"] == {"chat": 3}
    assert snap["turns"] == 3
    assert a._donkey["n"] == 0


# ===========================================================================
# 2. ADD-NEW-CONTEXT (headline) — an arbitrary cue MINTS a new dimension
# ===========================================================================
def test_arbitrary_cue_mints_a_new_context_dimension():
    a = _agent()
    cm.observe_turn(a, "hello", context=dict(STEADY))
    before = set(cm.model_snapshot(a)["codebook"])
    assert "device" not in before, "the novel dimension must not be pre-registered"

    # a context cue on a dimension the codebook has never held: which DEVICE the party is on.
    r = cm.observe_turn(a, "typing from my phone now", context=dict(STEADY, device="phone"))
    print("MINT:", "minted=", r["minted"], "recognized_after=", r["recognized_after_mint"],
          "\n  codebook_before=", r["codebook_before"],
          "\n  codebook_after =", r["codebook_after"])

    # the residual that fit no held dimension MINTED a new context dimension (codebook GREW).
    assert "device" in r["minted"], "an unfitted cue must mint a new context dimension"
    after = set(cm.model_snapshot(a)["codebook"])
    assert "device" in after and after == before | {"device"}, "the codebook must grow by exactly it"
    # RE-DECODE against the grown codebook recognizes it (dynamic quantization closes the loop).
    assert "device" in r["recognized_after_mint"], "re-decode must recognize the minted dimension"

    # ...and a SECOND turn on the now-held dimension no longer mints (it is part of the codebook).
    r2 = cm.observe_turn(a, "still on my phone", context=dict(STEADY, device="phone"))
    assert "device" not in r2["minted"], "a held dimension never re-mints"
    assert a._donkey["n"] == 0


# ===========================================================================
# 3. SALIENCE -> RELEVANCE — the shifted dim is salient, the steady dim is not
# ===========================================================================
def test_salience_is_the_residual_and_picks_the_relevant_dim():
    a = _agent()
    # establish an expectation: same place ("chat") over two turns.
    cm.observe_turn(a, "hi", context=dict(STEADY))
    cm.observe_turn(a, "how are you", context=dict(STEADY))

    # now the PLACE shifts (chat -> voice) while time_self stays steady (afternoon).
    r = cm.observe_turn(a, "calling you now", context=dict(STEADY, place="voice"))
    print("SALIENCE:", "salient_dims=", r["salient_dims"], "salience=", r["salience"])

    # the shifted dim is SALIENT (a residual); the steady dim is not.
    assert "place" in r["salient_dims"], "the shifted dim must be salient (residual)"
    assert "time_self" not in r["salient_dims"], "a steady dim must NOT be salient"
    # salience IS the residual — the (dim, value) the model could not collapse this turn.
    assert ("place", "voice") in r["salient"]
    assert r["salience"]["place"] == 1.0
    # and the Conceptualizer-facing read exposes exactly the relevant dims + their values.
    rel = cm.salient_context(a)
    assert rel["salient_dims"] == ["place"] and rel["values"]["place"] == "voice"
    assert a._donkey["n"] == 0


# ===========================================================================
# 4. FEEDS IDENTITY — a richer context shift tips re-attribution more decisively
# ===========================================================================
def _build_persona(a):
    for t in ["Please kindly consider, indeed, the disposition toward virtue.",
              "Certainly, morality could, perhaps, be examined carefully.",
              "Pardon, would you consider consequences, thoughtfully weighed?"]:
        im.observe_turn(a, t)


def test_richer_context_shift_feeds_and_sharpens_identity():
    break_text = "Please could you kindly clarify that point for me now"  # a single style break

    # (a) no context shift -> the sub-coherent single style break does NOT re-attribute.
    a0 = _agent(); _build_persona(a0)
    r0 = im.observe_turn(a0, break_text, context={})
    assert r0["decision"] != "identity" and not r0["context_gaps"]

    # (b) the NEW context dim (channel, beyond time_gap/place) — fed from context_model's salient
    #     read — tips the SAME style break into re-attribution.
    a1 = _agent(); _build_persona(a1)
    r1 = im.observe_turn(a1, break_text, context={"channel_changed": True})
    print("CHANNEL-ONLY:", r1["decision"], "context_gaps=", r1["context_gaps"])
    assert r1["decision"] == "identity", "a context dim beyond time_gap/place must feed identity"
    assert any(g[0] == "channel" for g in r1["context_gaps"])

    # (c) a RICHER shift (place + channel) is a BIGGER context residual -> more decisive.
    a2 = _agent(); _build_persona(a2)
    r2 = im.observe_turn(a2, break_text, context={"place_changed": True, "channel_changed": True})
    print("PLACE+CHANNEL:", r2["decision"], "context_gaps=", r2["context_gaps"])
    assert r2["decision"] == "identity"
    assert len(r2["context_gaps"]) > len(r1["context_gaps"]), "richer context = bigger residual"

    # the feed is REAL: context_model.interlocutor_context turns a salient shift into these flags.
    ca = _agent()
    cm.observe_turn(ca, "hi", context=dict(STEADY))
    cm.observe_turn(ca, "hi", context=dict(STEADY))
    shift = cm.observe_turn(ca, "hi", context=dict(STEADY, place="voice"))
    fed = cm.interlocutor_context(shift)
    assert fed.get("place_changed") is True, "a salient place shift feeds place_changed to identity"
    assert a0._donkey["n"] == 0 and a1._donkey["n"] == 0 and a2._donkey["n"] == 0


# ===========================================================================
# 5. COLLAPSE / SD-NATIVE — decode+mint route through run_collapse; source audit
# ===========================================================================
def test_decode_and_mint_route_through_the_collapse_engine():
    import domains.context_collapse_plug as plug
    import collapse_engine as ce
    assert plug.run_collapse is ce.run_collapse, "residual comes from the agent's collapse loop"

    # a novel-DIMENSION cue is a mint residual; a novel-VALUE on a held dim is a salient residual;
    # a value the model expects collapses (no residual). One run_collapse pass produces all three.
    codebook = ["place"]
    model = {"place": {"chat": 3}}
    r = plug.collapse_context(codebook, model, {"place": "voice", "device": "phone"})
    assert r["mint"] == ["device"], "the un-held dimension is the mint residual"
    assert r["salient"] == [("place", "voice")], "the un-expected value on a held dim is salience"
    steady = plug.collapse_context(codebook, model, {"place": "chat"})
    assert steady["mint"] == [] and steady["salient"] == [], "an expected value collapses (no residual)"

    # SOURCE AUDIT: context_model has no bespoke quantizer / fixed context enum — the mint is the
    # collapse residual (collapse_context), the codebook grows by _mint_dim, and no numeric engine.
    src = open(os.path.join(ROOT, "domains", "context_model.py")).read()
    assert "collapse_context(" in src
    for fn in ("context_model.py", "context_collapse_plug.py"):
        code = [ln for ln in open(os.path.join(ROOT, "domains", fn)).read().splitlines()
                if not ln.lstrip().startswith("#")]
        code = "\n".join(code)
        for bad in ("import numpy", "import math", "math.exp(", ".fit(", ".backward("):
            assert bad not in code, f"{fn} smells like a parallel engine: {bad}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
