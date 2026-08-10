"""RUNG 8C — STEP 1: IS RUNG 8's PROBE STILL BLIND, AND IS `mu_endo` EVEN IN THIS PATHWAY?

This is the cheap gate that decides whether anything else in rung 8C may run.
It answers TWO questions, both by MEASUREMENT rather than by reading the ladder:

  Q1  THE PREMISE.  The brief says: "re-run rung 8's §1 calibration WITH `mu_endo`
      IN PLACE." So: is `mu_endo` in rung 8's pathway at all? This is asked
      POSITIVELY -- boot the pathway, enumerate the node types that actually
      exist, and look for the population `mu_endo` lives on -- and NOT by
      grepping seed files and inferring what they select. PROTOCOL §12.1: *a
      claim about what code SELECTS is not established by counting the tokens
      that select it. Read one.* The same section records a supervisor's grep
      producing a confident, false premise ("76 population grabs"), which is
      exactly the shape of the claim under test here.

  Q2  THE NUMBER.  Rung 8's §1 calibration gate, through rung 8's OWN harness,
      verbatim (`rung8b_calibrate.reproduction`, which rung 8B already used as
      its reproduction control and which returned rung 8's numbers to the digit
      on a different binary). Rung 8 reported, at engine `95167c01b7b3`:

          lateral (composed)   floor 0.0205 | IDEAL 0.1290 | peak/base 0.89
          degenerate (rung 6)  floor 0.3105 | IDEAL 1.0000 | peak/base 6.94

      The IDEAL on the composed pathway is the gate: PROTOCOL §1 says *"run it on
      an ideal exemplar of the structure -- it must score high."* 0.1290 is what
      stopped rung 8, and 1.0000 is what the same probe returns on rung 6's own
      channels.

**`peak/base` is REPORTED but NOT READ as a criterion** -- it is an unbounded
ratio that has blown up in two independent rungs (1.6e6; 7.1e7 / 2.4e8) and
PROTOCOL §1.1 says it should be bounded or retired. It is printed only because
rung 8 and rung 8B both printed it, so it is part of the reproduction control.

Seeds: 0 / 3000 -- ALREADY BURNED (the ledger's rung-8 calibration row). **No
confirmatory seed is touched.** This script trains nothing and asserts nothing;
it is a gate reader.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PROTOCOL §10.1 rule 3: "Any non-pytest entrypoint (a rung script) must call
# `engine_preamble()` ITSELF." It must run BEFORE any `domains.*` import, because
# the FIRST import of `substrate_rs` binds the engine for the whole process — a
# preamble that runs afterwards is a no-op that LOOKS correct. Caught live: this
# rung's scripts imported `domains.complex_cells` first and silently loaded the
# CANONICAL tree's engine via the `.pth`, which went RED mid-session when a
# concurrent agent rebuilt it from ITS Rust source (§11.5: "long-running
# measurement is not a lock").
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8b_calibrate import reproduction  # noqa: E402
from scripts.rung8_lib import build  # noqa: E402


def pathway_node_types(channels: str) -> dict:
    """Q1, POSITIVELY: boot rung 8's pathway and enumerate what is REALLY there.

    Returns the node-type histogram of the live graph plus a direct check for the
    EyeCell population `mu_endo` is latched onto (`ey_endo_latch` matches
    `["e","has_eyecell","c"]`) and for the attribute itself, wherever it may sit.
    """
    w, _us, _a, _b = build(seed=0, n_units=6, channels=channels)
    g = w.s.graph_to_dict()
    types: dict[str, int] = {}
    has_mu_endo = 0
    for n in g["nodes"].values() if isinstance(g["nodes"], dict) else g["nodes"]:
        t = n["type"]
        types[t] = types.get(t, 0) + 1
        if "mu_endo" in (n.get("attrs") or {}):
            has_mu_endo += 1
    return {"types": types, "n_eyecell": types.get("EyeCell", 0),
            "n_nodes_with_mu_endo": has_mu_endo}


def main() -> int:
    print("=" * 78)
    print("RUNG 8C — STEP 1: IS THE PROBE STILL BLIND?  IS `mu_endo` IN THIS PATHWAY?")
    print(provenance_line())
    print("=" * 78)

    # ---------------------------------------------------------------- #
    # Q1 — THE PREMISE, measured. `mu_endo` lives on the EYE's EyeCell
    #      population (`vision_eye.json`). Rung 8's pathway loads
    #      vision_waves + vision_onoff [+ vision_lateral + vision_compose].
    #      `vision_eye` depends only on `vision_waves` -- it is a SIBLING of
    #      `vision_onoff`, not an ancestor -- so if it is absent, no
    #      dependency closure drags it in. Do not infer that: look.
    # ---------------------------------------------------------------- #
    print("\n--- Q1. IS `mu_endo` IN RUNG 8's PATHWAY? (booted and enumerated) ---")
    for chan in ("lateral", "degenerate"):
        info = pathway_node_types(chan)
        print(f"  [{chan}] node types present: "
              f"{sorted(info['types'].items(), key=lambda kv: -kv[1])}")
        print(f"  [{chan}] EyeCell nodes (the population `mu_endo` sits on): "
              f"{info['n_eyecell']}")
        print(f"  [{chan}] nodes carrying a `mu_endo` attribute AT ALL: "
              f"{info['n_nodes_with_mu_endo']}")

    # ---------------------------------------------------------------- #
    # Q2 — THE NUMBER. Rung 8's own harness, verbatim.
    # ---------------------------------------------------------------- #
    print("\n--- Q2. RUNG 8's §1 CALIBRATION GATE (rung 8's harness, verbatim) ---")
    print("        rung 8 @ 95167c01b7b3:  lateral 0.0205 / 0.1290 / 0.89")
    print("                                degenerate 0.3105 / 1.0000 / 6.94")
    out = {}
    for chan in ("lateral", "degenerate"):
        fl, id_, pb, th = reproduction(chan)
        out[chan] = (fl, id_, pb, th)
        print(f"  [{chan:11s}] floor {fl:.4f} | IDEAL {id_:.4f} | "
              f"peak/base {pb:.2f} (NOT a criterion) | theta {th:.4f}")

    lat_ideal = out["lateral"][1]
    deg_ideal = out["degenerate"][1]
    print("\n--- VERDICT ---")
    print(f"  IDEAL split-Gabor on the COMPOSED pathway: {lat_ideal:.4f}")
    print(f"  IDEAL split-Gabor on RUNG 6's OWN channels: {deg_ideal:.4f}")
    blind = lat_ideal < 0.80
    print(f"  PROBE BLIND ON THE COMPOSED PATHWAY? {'YES' if blind else 'NO'}"
          f"   (§1 needs the ideal exemplar to score HIGH)")
    print("\n  If Q1 reports 0 EyeCell nodes and 0 nodes carrying `mu_endo`, then"
          "\n  `mu_endo` was never in this pathway, the brief's premise is FALSE,"
          "\n  and Q2's number is UNCHANGED for the most boring possible reason:"
          "\n  nothing in rung 8's pathway changed. STEP 2 is entered on the"
          "\n  ORIGINAL rung-8/8B diagnosis, not on a rescued one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
