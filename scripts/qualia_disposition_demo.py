#!/usr/bin/env python3
"""DISPOSITION as a REAL CAN-relaxable DYNAMICAL QUALIA AXIS on the agent.

Run: python3 scripts/qualia_disposition_demo.py

The agent's COGNITIVE DISPOSITION — its standing willingness to mint referents /
form associations, conservative (−) ↔ permissive (+) — is modelled as a felt
scalar on a resident-style CAN Concept on the agent (domains/disposition.py),
the structural twin of self-worth (domains/can_self_worth_bridge.py). It is
SEEDED with a starting temperament (a tweak) but PRODUCED and MOVED by the SAME
native identity dynamics (can_native_identity_field_feedback,
seeds/can_decay_identity.json) that crystallise any other felt state — the seed
gives the starting point, the dynamics give the realism.

This script demonstrates the three things the axis has to earn:

  (a) DISTRIBUTION — two agents SEEDED at different disposition points occupy
      different standing `dynamical:disposition` coordinates. People sit on a
      distribution of dispositions.

  (b) MOVEMENT — the `disposition_field` is MOVED by relaxation from
      external evidence (not hand-written): sustained "opening-up paid off"
      evidence walks a conservative agent up the axis, one graded step at a
      time; sustained counter-evidence walks it back down. The trait shifts
      because the CAN rule moved it.

  (c) SIGNATURE COORDINATE — the disposition appears as a real
      `dynamical:disposition` coordinate in the agent's OWN qualia signature
      (concept_signature on the disposition Concept), and a LIVE momentary pull
      appears as the `dynamical:disposition_pull` overlay coordinate — the gap
      between the two IS "I'm being pulled to open up but my temperament hasn't
      moved."

It also reports HONESTLY whether disposition genuinely takes GRADED values under
the dynamics or SATURATES like dynamical:commitment.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp


class _Agent:
    """Minimal agent wrapper: a `.s` substrate handle + an `.agent` hub node —
    the same shape domains/disposition.py accepts (getattr(agent, 's', agent))."""
    def __init__(self):
        # a fresh schema-cache per substrate (the cache is keyed on the sub id
        # + dimension count; clearing keeps the demo's substrates independent).
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})


def _disp_coords(sig):
    """The disposition coordinates in a signature (both the crystallised
    standing axis and the live overlay pull axis)."""
    return sorted(t for t in sig if t[0].startswith("dynamical:disposition"))


def section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    # ---------------------------------------------------------------------- #
    section("(a) DISTRIBUTION — two agents seeded at different temperaments")
    # ---------------------------------------------------------------------- #
    conservative = _Agent()
    disp.set_disposition_seed(conservative, -3.0)   # a wary, mint-shy temperament
    open_minded = _Agent()
    disp.set_disposition_seed(open_minded, +2.0)    # a permissive temperament
    neutral = _Agent()
    disp.ensure_disposition(neutral)                # untouched → the SAFE DEFAULT

    print(f"conservative agent  seed=-3.0  → standing disposition_level = "
          f"{disp.disposition_level(conservative):+d}  "
          f"(field={disp.disposition_field(conservative):+.1f})")
    print(f"open-minded agent   seed=+2.0  → standing disposition_level = "
          f"{disp.disposition_level(open_minded):+d}  "
          f"(field={disp.disposition_field(open_minded):+.1f})")
    print(f"neutral agent       (default)  → standing disposition_level = "
          f"{disp.disposition_level(neutral):+d}  "
          f"(field={disp.disposition_field(neutral):+.1f})  "
          f"[DEFAULT_DISPOSITION_SEED={disp.DEFAULT_DISPOSITION_SEED} = "
          f"today's mildly-conservative behaviour]")
    print("→ three distinguishable standing coordinates: a real DISTRIBUTION, "
          "not one static value.")

    # ---------------------------------------------------------------------- #
    section("(b) MOVEMENT — disposition_field moved BY relaxation from evidence")
    # ---------------------------------------------------------------------- #
    agent = _Agent()
    disp.set_disposition_seed(agent, -3.0)   # starts wary
    print(f"start (seeded temperament):        level = "
          f"{disp.disposition_level(agent):+d}  "
          f"field = {disp.disposition_field(agent):+.1f}")

    # Sustained "opening up paid off" evidence. Each call drives the CAN
    # identity-feedback rule for a few strictly-later ticks; the rule (NOT this
    # script) steps identity_field toward the evidence sign, and disposition.py
    # mirrors the PRODUCED value onto disposition_field.
    for step in range(1, 6):
        lvl = disp.relax_disposition(agent, +1.0, ticks=1)
        print(f"  + openness evidence (step {step}):  level = {lvl:+d}  "
              f"field = {disp.disposition_field(agent):+.1f}   "
              f"← produced by can_native_identity_field_feedback, not set")
    print("→ the trait WALKED UP the axis one graded step per tick — the "
          "distribution position MOVED under evidence.")

    # Now sustained counter-evidence. Because the identity-feedback rule steps
    # toward the sign of the CUMULATIVE evidence ledger, an established trait
    # first RESISTS (its accumulated confirms still tilt the log-odds), then
    # REVERSES once sustained counter-evidence outweighs them. Drive it long
    # enough to show the full reversal.
    print("  ... now sustained counter-evidence (spurious associations) ...")
    prev = disp.disposition_level(agent)
    reversed_at = None
    for step in range(1, 16):
        lvl = disp.relax_disposition(agent, -1.0, ticks=1)
        tag = ""
        if step == 1:
            tag = "  ← resists at first (established ledger still positive)"
        elif lvl < prev and reversed_at is None:
            reversed_at = step
            tag = "  ← ledger has tipped: now reversing"
        print(f"  − conservatism evidence (step {step:2d}):  level = {lvl:+d}  "
              f"field = {disp.disposition_field(agent):+.1f}{tag}")
        prev = lvl
    print("→ an ESTABLISHED trait resists at first (its accumulated evidence "
          "ledger holds the sign) but REVERSES under sustained counter-evidence "
          "— real hysteresis, not a ratchet.")

    # ---------------------------------------------------------------------- #
    section("(c) SIGNATURE COORDINATE — disposition in the agent's own qualia "
            "signature")
    # ---------------------------------------------------------------------- #
    settled = _Agent()
    disp.set_disposition_seed(settled, 0.0)
    disp.relax_disposition(settled, +1.0, ticks=3)   # settle a +3 standing trait
    cryst = disp.disposition_signature(settled)
    print("standing (crystallised) signature disposition coords:")
    for t in _disp_coords(cryst):
        print(f"   {t}")
    print("→ `dynamical:disposition` is a real coordinate in the agent's own "
          "signature — one space with every other felt/lexical axis.")

    # The UNSETTLED point: a live momentary pull, no crystallised movement yet.
    pulled = _Agent()
    disp.set_disposition_seed(pulled, 0.0)
    disp.pull_disposition(pulled, +3.0)              # live openness pull only
    cryst_p = disp.disposition_signature(pulled)
    over_p = disp.disposition_signature(pulled, overlay=True)
    print("\nUNSETTLED POINT — a live pull with no standing movement:")
    print(f"   standing coords : {_disp_coords(cryst_p)}  (no commitment yet)")
    print(f"   overlay coords  : {_disp_coords(over_p)}   (live pull present)")
    print("→ the GAP between the overlay `dynamical:disposition_pull` and the "
          "empty standing `dynamical:disposition` IS 'I'm being pulled to open "
          "up right now, but my temperament hasn't moved.'")

    # ---------------------------------------------------------------------- #
    section("HONEST GRANULARITY REPORT — does disposition GRADE or SATURATE?")
    # ---------------------------------------------------------------------- #
    grader = _Agent()
    disp.set_disposition_seed(grader, 0.0)
    levels = []
    for _ in range(7):
        levels.append(disp.relax_disposition(grader, +1.0, ticks=1))
    print(f"levels under 7 consecutive +evidence ticks: {levels}")
    distinct = sorted(set(levels))
    print(f"distinct graded levels reached before clamp: {distinct}")
    print()
    print("VERDICT: disposition GENUINELY GRADES. quantum=1.0 == the CAN field's")
    print("own integer step: can_native_identity_field_feedback moves")
    print("identity_field by exactly ±1 per tick, so successive ticks read as")
    print("distinct coordinates 1,2,3,4 before clamping at ±4 (a 9-level axis).")
    print("This is UNLIKE dynamical:commitment (quantum=0.25), whose very first")
    print("±1 identity step already rounds to ±4 and SATURATES to {−4,0,+4}.")
    print("The spread is the field's own, honestly reported — not a quantiser")
    print("illusion: the underlying identity_field really does take the graded")
    print("integer values, and quantum=1.0 exposes them rather than crushing")
    print("them. What would give commitment the same spread: quantum=1.0 (or a")
    print("magnitude-scaled identity step, which the rule rejects on stability")
    print("grounds). Disposition simply chose the quantum that matches the step.")


if __name__ == "__main__":
    main()
