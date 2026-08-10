"""GAP 2 — self-extension by composing held primitives, with a known confidence and an honest impasse. NO LLM.

The agent's order-4 self-extend used to ask a hosted teacher (claude -p) to name a new approach. Now, when a
frontier needs a capability, the agent COMPOSES a new operator from the held primitives whose advertised
CapKeys cover the need (a graph join), carries an a-priori confidence = coverage x mean reliability of the
parts, and lets the trial confirm it. When NOTHING it holds touches the need, it surfaces an honest
HumanImpasse naming the gap — it does not fabricate a placeholder that falsely saturates the axis.

This demo sets up held primitives + three capability needs (fully covered / partially covered / not covered
at all) and runs ONLY the self_extension graph rules with NO teacher attached.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.self_extension_demo
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96


def main():
    print(SEP)
    print("GAP 2 — compose held primitives on a capability need; honest impasse when nothing covers it. NO LLM.")
    print(SEP)
    a = boot()
    a._self_teacher = None                            # detach the teacher: the compose/impasse decisions are graph rules
    a.inner.load_seed_manifest(manifest_for("self_extension"), a.agent)

    # Held primitives the agent already understands, each advertising a CapKey + a proven reliability.
    def capkey(name):
        return a.s.add_node("CapKey", {"name": name})

    def primitive(name, key, reliability):
        p = a.s.add_node("OperationPrimitive", {"name": name, "reliability": reliability})
        a.inner.add_edge_unchecked(p, "provides_key", key)
        return p

    k_seg = capkey("segment")
    k_clu = capkey("cluster")
    k_tone = capkey("tonal_contour")                 # a substantive need nothing held provides
    k_novel = capkey("recognise_unknown_modality")   # an entirely uncovered capability
    primitive("prim_segment", k_seg, 0.9)
    primitive("prim_cluster", k_clu, 0.7)

    def axis(name, keys):
        ax = a.s.add_node("CapabilityAxis", {"is_axis": 1.0, "name": name})
        for k in keys:
            a.inner.add_edge_unchecked(ax, "requires_key", k)
        return ax

    def needs_tool(ax):
        mi = a.s.add_node("Impasse", {"order": 4, "kind": "escalation"})
        a.inner.add_edge_unchecked(mi, "needs_tool", ax)
        return mi

    ax_full = axis("segment_and_cluster", [k_seg, k_clu])           # fully covered
    ax_partial = axis("seg_cluster_and_tone", [k_seg, k_clu, k_tone])  # partially covered (tone unprovided)
    ax_zero = axis("unknown_modality", [k_novel])                  # nothing covers it
    for ax in (ax_full, ax_partial, ax_zero):
        needs_tool(ax)

    print("\n  held primitives: prim_segment(provides segment, reliability 0.9), "
          "prim_cluster(provides cluster, 0.7)")
    print("  capability needs: [segment+cluster] FULL | [segment+cluster+tonal_contour] PARTIAL | "
          "[unknown_modality] NONE")
    print("  teacher attached: NONE — every decision below is a graph rule.\n")

    # compose / wire / honest-impasse AND set_compose_confidence are all GRAPH RULES now (the JIT
    # float-attr fix lets the confidence rule's `Eq(Attr(cop,'composed'),1)` where fire). No host pass.
    a.inner.run_rules(60000)

    def composed_of(ax):
        for o in a.inner.neighbours(ax, "investigated_by"):
            if a.s.node(o)["attrs"].get("composed") == 1:
                return o
        return None

    def report(label, ax):
        cop = composed_of(ax)
        at = a.s.node(ax)["attrs"]
        if cop is not None:
            parts = [a.s.node(p)["attrs"].get("name") for p in a.inner.neighbours(cop, "composed_from")]
            conf = a.s.node(cop)["attrs"].get("compose_confidence")
            cov = at.get("compose_confidence")
            prov = at.get("provisional")
            print(f"  [{label}] COMPOSED from {parts}  coverage={cov}  "
                  f"confidence={conf}  provisional={prov}")
            return cop, None
        mh = next((m for m in a.s.nodes("HumanImpasse") if ax in a.inner.neighbours(m, "about_axis")), None)
        if mh is not None:
            mat = a.s.node(mh)["attrs"]
            print(f"  [{label}] HONEST IMPASSE -> human (needs_human={mat.get('needs_human')}, "
                  f"kind={mat.get('kind')}); NO operator authored, axis NOT saturated")
            return None, mh
        print(f"  [{label}] (nothing happened)")
        return None, None

    cF, _ = report("FULL   ", ax_full)
    cP, _ = report("PARTIAL", ax_partial)
    cZ, hZ = report("NONE   ", ax_zero)

    # checks
    ok = (cF is not None and cP is not None and cZ is None and hZ is not None
          and abs(a.s.node(cF)["attrs"]["compose_confidence"] - 0.8) < 0.01
          and a.s.node(ax_partial)["attrs"].get("provisional") == 1
          and not composed_of(ax_zero))
    teacher_calls = 0  # no teacher attached; the compose/impasse decisions are graph rules

    print("\n  " + "-" * 92)
    print(f"  FULL composed (conf 1.0x0.8=0.80, trust one trial); PARTIAL composed (provisional, must be")
    print(f"  confirmed/reproduced); NONE surfaced as an honest HumanImpasse with no placeholder. "
          f"claude -p calls: {teacher_calls}.")
    print(f"  RESULT: {'PASS' if ok else 'FAIL'} — the agent extends itself from what it holds, with a known")
    print(f"  confidence, and names the gap it cannot compose instead of papering over it.")
    print(SEP)


if __name__ == "__main__":
    main()
