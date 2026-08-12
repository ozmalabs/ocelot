#!/usr/bin/env python3
"""AR3 — does the meta-shape growth loop actually CLOSE?

residual → (recurrence) → mint → epoch bump → re-decode → recognize,
driven entirely by the `run_rules` fixpoint. Plus the NEGATIVE control: an
observation that already has a home must recognise and mint nothing.
"""
from __future__ import annotations

import json
import os
import sys

TREE = os.environ.get("OZMA_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (TREE, os.path.join(TREE, "runners", "dsl", "python")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.seed_loader import manifest_for            # noqa: E402
from domains.meta_shape import observe                    # noqa: E402


def boot():
    wa = WorldAdapter()
    for seed in ("shape_vocabulary", "meta_shape_growth"):
        wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
    return wa


def shapes(wa):
    return sorted(str(wa.s.node(n)["attrs"].get("name")) for n in wa.s.nodes("MetaShape"))


def obs_rows(wa):
    out = []
    for n in wa.s.nodes("ShapeObservation"):
        a = wa.s.node(n)["attrs"]
        out.append({"item_type": a.get("item_type"), "status": a.get("status"),
                    "covered_by": a.get("covered_by")})
    return out


def main():
    wa = boot()
    rules = [r for r in wa.inner.rule_names()] if hasattr(wa.inner, "rule_names") else []
    installed = [r for r in rules if r.startswith("msg_")]
    log = {"installed_msg_rules": installed, "codebook_before": shapes(wa)}

    # ---- a genuinely NOVEL slot skeleton, seen ONCE -------------------------
    observe(wa, "TradeRecord", {"buyer": "alice", "seller": "bob", "lot": "7"})
    log["after_first"] = {"observations": obs_rows(wa), "codebook": shapes(wa)}

    # ---- the SAME skeleton, different content: RECURRENCE ------------------
    observe(wa, "TradeRecord", {"buyer": "carol", "seller": "dave", "lot": "9"})
    log["after_second"] = {"observations": obs_rows(wa), "codebook": shapes(wa)}

    minted = [n for n in shapes(wa) if n.startswith("ms_")]
    log["minted"] = minted
    for n in wa.s.nodes("MetaShape"):
        a = wa.s.node(n)["attrs"]
        if str(a.get("name", "")).startswith("ms_"):
            log["minted_entry"] = {"name": a.get("name"), "support": a.get("support"),
                                   "signature": a.get("signature")}
    for n in wa.s.nodes("ShapePrinciple"):
        a = wa.s.node(n)["attrs"]
        if a.get("minted"):
            log["minted_principle"] = {"name": a.get("name"), "keywords": a.get("keywords")}

    # ---- a NEAR-VARIANT: must recognise against the MINTED entry, no mint ---
    observe(wa, "TradeRecord", {"buyer": "erin", "seller": "frank", "lot": "11"})
    log["after_variant"] = {"observations": obs_rows(wa), "codebook": shapes(wa)}

    # ---- NEGATIVE CONTROL: an item that already has a home -----------------
    observe(wa, "Note", {"text": "gate the layer by policy"})
    log["after_negative_control"] = {"observations": obs_rows(wa), "codebook": shapes(wa)}

    print(json.dumps(log, indent=1, default=str))


if __name__ == "__main__":
    main()
