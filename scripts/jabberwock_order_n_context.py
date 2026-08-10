#!/usr/bin/env python3
"""jabberwock_order_n_context — ORDER-N CONTEXT as the agent's OWN COLLAPSE FACULTY at the context
timescale, with an OPEN-ENDED codebook that MINTS a new context dimension on a residual that fits
none (dynamic quantization). Creator (2026-07-04): "there is also order N context ... which need
salience to identify the relevance. the context should include ARBITRARY context — and critically it
should include the ability to ADD NEW CONTEXTS."

Prints, all donkey=0, all through scripts/collapse_engine.run_collapse:
  1. the SEEDED dims (cadence/place/time-on-BOTH-ends/duration/gap) consolidating over turns;
  2. the HEADLINE — an arbitrary cue MINTS a new context dimension, the codebook GROWS, a re-decode
     RECOGNIZES it (sd_mint_quantum -> codebook grows -> sd_redecode, one level up);
  3. SALIENCE -> RELEVANCE — a shifted dim is salient (the residual), a steady dim is not;
  4. the FEED — a richer context shift tips the interlocutor re-attribution more decisively.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_order_n_context.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.context_model as cm
import domains.interlocutor_model as im


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def _hr(t): print("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


def main() -> int:
    ok = True
    a = _agent()
    STEADY = dict(place="chat", time_self=14, time_other=9, gap=0)

    _hr("1. SEEDED DIMS consolidate over turns (cadence / place / time on BOTH ends / duration / gap)")
    for i, t in enumerate(["Hi there, how are you today?",
                           "I wanted to ask about the timeline please.",
                           "Thanks, that is helpful indeed."]):
        cm.observe_turn(a, t, context=dict(STEADY, duration=i + 1))
    snap = cm.model_snapshot(a)
    print("  codebook :", snap["codebook"])
    for d in cm.SEEDED_DIMS:
        print(f"    {d:11s} -> {snap['feat_counts'].get(d)}")
    print("  time on BOTH ends is modeled separately: self=afternoon, other=morning")
    ok &= all(d in snap["codebook"] for d in cm.SEEDED_DIMS)
    ok &= snap["feat_counts"]["place"] == {"chat": 3}

    _hr("2. HEADLINE — an ARBITRARY cue MINTS a new context dimension (dynamic quantization)")
    before = list(cm.model_snapshot(a)["codebook"])
    r = cm.observe_turn(a, "typing from my phone now", context=dict(STEADY, device="phone"))
    print("  codebook BEFORE :", before)
    print("  arbitrary cue   : device=phone  (a dimension the codebook has NEVER held)")
    print("  residual['mint']:", r["minted"], "  <- fit no held dimension -> MINT a new quantum")
    print("  codebook AFTER  :", r["codebook_after"], "  <- GREW by exactly the minted dim")
    print("  re-decode       :", r["recognized_after_mint"], "  <- now HELD -> recognized (loop closed)")
    ok &= r["minted"] == ["device"] and "device" in r["codebook_after"]
    ok &= r["recognized_after_mint"] == ["device"]
    r2 = cm.observe_turn(a, "still on my phone", context=dict(STEADY, device="phone"))
    print("  next turn device=phone mints:", r2["minted"], "  <- a held dimension never re-mints")
    ok &= r2["minted"] == []

    _hr("3. SALIENCE -> RELEVANCE — the shifted dim is salient (residual), the steady dim is not")
    b = _agent()
    cm.observe_turn(b, "hi", context=dict(STEADY)); cm.observe_turn(b, "hey", context=dict(STEADY))
    r = cm.observe_turn(b, "calling you now", context=dict(STEADY, place="voice"))
    print("  place: chat->voice (shift),  time_self: afternoon (steady)")
    print("  salient_dims :", r["salient_dims"], "  <- the RELEVANT context this turn (the residual)")
    print("  salience     :", r["salience"], "  <- salience IS the residual, not a payoff")
    print("  salient_context(agent):", cm.salient_context(b))
    ok &= r["salient_dims"] == ["place"] and ("place", "voice") in r["salient"]

    _hr("4. FEED — a richer context shift tips the interlocutor re-attribution more decisively")
    persona = ["Please kindly consider, indeed, the disposition toward virtue.",
               "Certainly, morality could, perhaps, be examined carefully.",
               "Pardon, would you consider consequences, thoughtfully weighed?"]
    brk = "Please could you kindly clarify that point for me now"
    a0 = _agent(); [im.observe_turn(a0, t) for t in persona]
    d0 = im.observe_turn(a0, brk, context={})
    a1 = _agent(); [im.observe_turn(a1, t) for t in persona]
    d1 = im.observe_turn(a1, brk, context={"channel_changed": True})
    a2 = _agent(); [im.observe_turn(a2, t) for t in persona]
    d2 = im.observe_turn(a2, brk, context={"place_changed": True, "channel_changed": True})
    print(f"  no context          -> {d0['decision']:12s} context_gaps={d0['context_gaps']}")
    print(f"  channel (new dim)   -> {d1['decision']:12s} context_gaps={d1['context_gaps']}")
    print(f"  place + channel     -> {d2['decision']:12s} context_gaps={d2['context_gaps']}")
    print("  the new dim (channel, beyond time_gap/place) tips identity; a richer shift is a bigger")
    print("  residual -> more decisive. context_model.interlocutor_context() supplies these flags.")
    ok &= d0["decision"] != "identity" and d1["decision"] == "identity"
    ok &= len(d2["context_gaps"]) > len(d1["context_gaps"])

    donkey = a._donkey["n"] + b._donkey["n"] + a0._donkey["n"] + a1._donkey["n"] + a2._donkey["n"]
    _hr(f"{'PASS' if ok and donkey == 0 else 'FAIL'} — order-N context is the collapse faculty at the "
        f"context timescale; ADD-NEW-CONTEXT is dynamic quantization (mint-on-residual via "
        f"run_collapse); salience=residual=relevance; donkey={donkey}")
    return 0 if ok and donkey == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
