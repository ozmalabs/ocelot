#!/usr/bin/env python3
"""THE CODEC DECISION PROBE — read the GRAPH STATE, not the return value.

`test_codec_graph_resident` has been red since the file was born (~48 d), failing
"expected 10 rule firings, got 0". The pre-registered decision rule
(`VISION_BASELINE_LIST_PREREG.md` §3):

  decoded EMPTY    -> (A) the mechanism never engages; RETRACT the claim.
  decoded CORRECT  -> (B) the COUNT is what is mis-stated; correct the gate + positive control.
  decoded PARTIAL  -> (A) with the partial extent reported.

DO NOT "fix" the assertion before running this. Verify the fact, then decide (protocol 12.3).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
sys.path.insert(0, str(ROOT / "tests"))

from domains import engine_provenance  # noqa: E402
print("PROVENANCE:", engine_provenance.provenance_line())
print("LOADAVG:", os.getloadavg())

import test_codec_graph_resident as T  # noqa: E402
from substrate_rs import Substrate  # noqa: E402


def probe():
    s = Substrate()
    T.seed_codec_vocabulary(s)
    head = T.seed_pps_grammar(s)
    rules = T.seed_pps_decode_rules(s)
    print(f"rules seeded: {len(rules) if rules is not None else 'None'}")

    pps_rbsp = b"\xce\x0f\xc8"
    buf = s._inner.add_node("Buffer", {"bytes": pps_rbsp})
    state = s._inner.add_node("DecodeState", {"bp": 0})
    s._inner.add_edge(state, "current", head)
    s._inner.add_edge(state, "buffer", buf)

    steps = s._inner.run_rules(max_steps=1000)
    print(f"run_rules returned: {steps}   (gate expects {len(T.H264_PPS_FIELDS)})")

    decoded = {}
    for v in s._inner.neighbours(state, "decoded"):
        a = s._inner.node(v)["attrs"]
        decoded[a["name"]] = a["val"]
    print(f"decoded node count: {len(decoded)}")
    for k, v in sorted(decoded.items()):
        print(f"   {k} = {v}")

    expected = {
        "pic_parameter_set_id": 0, "seq_parameter_set_id": 0,
        "entropy_coding_mode_flag": 0,
        "bottom_field_pic_order_in_frame_present_flag": 0,
        "num_slice_groups_minus1": 0,
        "num_ref_idx_l0_default_active_minus1": 0,
        "num_ref_idx_l1_default_active_minus1": 0,
        "weighted_pred_flag": 0, "weighted_bipred_idc": 0,
        "pic_init_qp_minus26": -3,
    }
    ok = {k: decoded.get(k) == v for k, v in expected.items()}
    print(f"fields correct: {sum(ok.values())}/{len(expected)}")
    print(f"final bp attr: {s._inner.node(state)['attrs'].get('bp')}")
    # where did `current` end up?
    cur = list(s._inner.neighbours(state, "current"))
    if cur:
        print(f"current -> {s._inner.node(cur[0])['attrs']}")
    else:
        print("current -> (no edge)")

    if not decoded:
        print("\nVERDICT: (A) EMPTY — the mechanism never engaged.")
    elif all(ok.values()):
        print("\nVERDICT: (B) COMPLETE AND CORRECT — the COUNT is what is mis-stated.")
    else:
        print(f"\nVERDICT: (A/partial) — {sum(ok.values())}/{len(expected)} fields.")


if __name__ == "__main__":
    probe()
