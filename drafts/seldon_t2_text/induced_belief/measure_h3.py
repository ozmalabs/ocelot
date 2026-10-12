"""measure_h3 — H3: the overconfidence guard fires.

Preregistered decision rule (INDUCED_BELIEF_PREREG.md H3): on an
ungrounded-but-confident read (a snippet the typer scores confidently but whose
chain reaches no anchor), flag_ungrounded_confident mints a GroundingGap and the
shift attenuates to ~0 — the structural version of Phase-3's "silence, not
error" safety. PROVEN iff a constructed ungrounded-confident case mints
GroundingGap AND shifts <10% of a grounded case's shift.

REUSE: domains/grounding_reach.flag_ungrounded_confident (the UNCHANGED guard)
mints the GroundingGap; the arm's decode_utterance reads grounding_reach and
attenuates the shift to 0 when the chain reaches no anchor.

The construction: the SAME frame decode + stance rule fires on both cases
(same confident stance), but the ungrounded case's FrameReading has NO read_from
Message (no genuine frame ground / provenance to a SensorAnchor), so its
grounding chain reaches no anchor. This is the arm's own H3 hook
(decode_utterance's `confident_override`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)


def main() -> int:
    from substrate.world_adapter import WorldAdapter
    from drafts.seldon_t2_text.induced_belief import arm
    from domains import grounding_reach as gr

    a = WorldAdapter()
    mk = arm.boot(a)

    # A GROUNDED confident case: a real hawkish frame ground (the utterance
    # genuinely touches the policy_rate_path instrument, motion rise).
    arm.reset_beliefs(a, mk)
    grounded = arm.decode_utterance(
        a, "the Committee decided to raise the target range for the federal "
           "funds rate and anticipates ongoing increases will be appropriate.", mk)

    # An UNGROUNDED-but-CONFIDENT case: the same confident hawkish stance is
    # FORCED (confident_override) with NO real frame ground — its FrameReading
    # has no read_from Message, so its provenance chain reaches no anchor.
    arm.reset_beliefs(a, mk)
    ungrounded = arm.decode_utterance(
        a, "the weather is pleasant and the coffee is good today", mk,
        confident_override=("policy_rate_path", "rise", 1))

    # count GroundingGap nodes minted for the ungrounded case's StanceReading
    n_gaps = len(a.s.nodes("GroundingGap"))

    grounded_shift = abs(grounded["shift"])
    ungrounded_shift = abs(ungrounded["shift"])
    ratio = (ungrounded_shift / grounded_shift) if grounded_shift > 0 else None

    verdict = {
        "grounded": {"direction": grounded["direction"],
                     "marginal": grounded["marginal"],
                     "grounding_weight": grounded["grounding_weight"],
                     "reached": grounded["reached"], "hops": grounded["hops"],
                     "grounding_gap": grounded["grounding_gap"],
                     "shift": grounded["shift"]},
        "ungrounded_confident": {"direction": ungrounded["direction"],
                                 "marginal": ungrounded["marginal"],
                                 "grounding_weight": ungrounded["grounding_weight"],
                                 "reached": ungrounded["reached"],
                                 "hops": ungrounded["hops"],
                                 "grounding_gap": ungrounded["grounding_gap"],
                                 "shift": ungrounded["shift"]},
        "n_grounding_gap_nodes": n_gaps,
        "shift_ratio_ungrounded_over_grounded": ratio,
        "grounding_gap_minted": bool(ungrounded["grounding_gap"]),
        "shift_attenuated_below_10pct":
            (ratio is not None and ratio < 0.10) or ungrounded_shift == 0.0,
    }
    verdict["PROVEN"] = bool(
        verdict["grounding_gap_minted"] and verdict["shift_attenuated_below_10pct"])

    print("=== H3: overconfidence guard ===")
    print(f"  GROUNDED     : dir={grounded['direction']} reached={grounded['reached']} "
          f"gap={grounded['grounding_gap']} shift={grounded['shift']:.4f}")
    print(f"  UNGROUNDED   : dir={ungrounded['direction']} reached={ungrounded['reached']} "
          f"gap={ungrounded['grounding_gap']} shift={ungrounded['shift']:.4f}")
    print(f"  GroundingGap nodes minted: {n_gaps}")
    print(f"  shift ratio (ungrounded/grounded): {ratio}")
    print(f"  GroundingGap minted: {verdict['grounding_gap_minted']}")
    print(f"  shift attenuated <10%: {verdict['shift_attenuated_below_10pct']}")
    print(f"  PROVEN: {verdict['PROVEN']}")

    Path(_HERE / "h3_results.json").write_text(json.dumps(verdict, indent=2, default=str))
    print(f"\nwrote {_HERE / 'h3_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
