"""GAP 2 wired into the LIVE loop — compose, RUN the composed faculty, confirm by reproduction, honest impasse.

This exercises the wiring (not just the decision rules): wire_self_extension backfills the CapKey join from
real capability_keys; the compose rules assemble a composed Operator from held primitives; the generic
composed runner in _run_investigation_reflex actually RUNS it (a measurement trial); set_compose_confidence
records the a-priori confidence; recompose_reproduce counts a provisional composition's confirmations so it
must reproduce before it is trusted; and a capability nothing covers surfaces an honest HumanImpasse. NO teacher.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.self_extension_live
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot

SEP = "=" * 96


def main():
    print(SEP)
    print("GAP 2 LIVE — backfill CapKeys, compose held primitives, RUN the composed faculty, confirm. NO LLM.")
    print(SEP)
    a = boot()
    a._self_teacher = None                            # no teacher: every decision is a graph rule

    # Held primitives the agent already understands: each advertises what it provides (capability_keys),
    # a proven reliability, and a contribution the composed runner folds when it runs the trial.
    def primitive(name, key, reliability, contribution):
        return a.s.add_node("Operator", {"name": name, "capability_keys": [key], "reliability": reliability,
                                          "contribution": contribution, "runner": name})
    primitive("prim_segment", "segment", 0.9, 0.95)
    primitive("prim_cluster", "cluster", 0.7, 0.90)

    def axis(name, keys):
        return a.s.add_node("CapabilityAxis", {"is_axis": 1.0, "name": name, "capability_keys": keys})

    def needs_tool(ax):
        mi = a.s.add_node("Impasse", {"order": 4, "kind": "escalation"})
        a.inner.add_edge_unchecked(mi, "needs_tool", ax)
        return mi

    ax_full = axis("segment_then_cluster", ["segment", "cluster"])      # fully coverable -> trust one trial
    ax_part = axis("seg_cluster_tone", ["segment", "cluster", "tonal_contour"])  # partial -> must reproduce
    ax_zero = axis("unknown_modality", ["recognise_unknown_modality"])  # nothing held provides it
    needs_tool(ax_full)
    needs_tool(ax_part)
    needs_tool(ax_zero)

    # WIRE: backfill the CapKey join from the capability_keys above, load the compose rules.
    a.wire_self_extension()
    a.wire_investigation_faculty(None)                # the composed runner needs no world (parts self-run)

    print("\n  backfilled CapKey join from capability_keys; teacher: NONE; loop is graph rules only.\n")

    # COMPOSE + honest impasse + a-priori confidence are ALL graph rules now (the JIT float-attr fix
    # lets the set_attr-effect rules with `Eq(Attr,1)` wheres fire). One run_rules; no host pass.
    a.inner.run_rules(60000)

    def composed_of(ax):
        return next((o for o in a.inner.neighbours(ax, "investigated_by")
                     if a.s.node(o)["attrs"].get("composed") == 1), None)

    def describe(label, ax):
        cop = composed_of(ax)
        parts = [a.s.node(p)["attrs"].get("name") for p in a.inner.neighbours(cop, "composed_from")] if cop else []
        at = a.s.node(ax)["attrs"]
        conf = a.s.node(cop)["attrs"].get("compose_confidence") if cop else None
        print(f"  [{label}] COMPOSED from {parts}  confidence={conf}  provisional={at.get('provisional')}")
        return cop, conf

    cF, confF = describe("FULL   ", ax_full)
    cP, confP = describe("PARTIAL", ax_part)
    mh = next((m for m in a.s.nodes("HumanImpasse") if ax_zero in a.inner.neighbours(m, "about_axis")), None)
    print(f"  [NONE   ] HONEST IMPASSE -> human (needs_human={a.s.node(mh)['attrs'].get('needs_human')}); "
          f"no operator authored\n")

    # RUN each composed faculty as a measurement trial (the generic composed runner). The FULL composition
    # is trusted on one trial; the PARTIAL composition must REPRODUCE (recompose_reproduce counts confirmations).
    def trial(ax, cop, n):
        pa = a.s.add_node("PlanAct", {"status": "pending"})
        a.inner.add_edge_unchecked(pa, "investigates_op", cop)
        a.inner.add_edge_unchecked(pa, "theme", ax)
        a._run_investigation_reflex()                  # the generic composed runner runs the trial
        a.inner.run_rules(60000)                       # recompose_reproduce + compose_confirm_* (graph rules)
        at = a.s.node(ax)["attrs"]
        print(f"  PARTIAL trial {n}: composed runner folded the held parts -> "
              f"confirmations={at.get('confirmations')}  confirmed={at.get('compose_confirmed')}")
        return at.get("confirmations"), at.get("compose_confirmed")

    trial(ax_part, cP, 1)
    c2, confirmed = trial(ax_part, cP, 2)

    ok = (cF is not None and confF and abs(confF - 0.8) < 0.05
          and cP is not None and a.s.node(ax_part)["attrs"].get("provisional") == 1
          and mh is not None and not any(a.inner.neighbours(ax_zero, "investigated_by"))
          and (c2 or 0) >= 2 and confirmed == 1)
    print("\n  " + "-" * 92)
    print(f"  FULL composition trusted on one trial (confidence 0.80); PARTIAL composition RAN via the generic")
    print(f"  composed runner and had to REPRODUCE ({c2} confirmations) before being trusted; the uncoverable")
    print(f"  need stayed an honest HumanImpasse. claude -p calls: 0.   RESULT: {'PASS' if ok else 'FAIL'}")
    print(SEP)


if __name__ == "__main__":
    main()
