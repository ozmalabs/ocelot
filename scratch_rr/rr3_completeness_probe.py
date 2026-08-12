#!/usr/bin/env python3
"""RR3 — does any reasoning path need a rule-shape mirror to be COMPLETE?

The design spike's §10.4 rates lazy mirroring "medium" confidence with a
precisely named gap: *"I have not checked whether anything in the reasoning
path would need the mirror to be complete."*

The decisive evidence is empirical and already in the tree: `RuleSummary` is
a **deliberately partial** mirror of the rule store, and has been since it
was built. If the reasoning paths that consume it work correctly today over
a partial mirror, incompleteness is not a new hazard.

Boots a real agent (`load_all_seeds`) and measures the ratio.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))


def main():
    from domains.engine_provenance import engine_preamble
    engine_preamble(strict=False)
    from substrate.boot_core import boot_core
    from substrate.boot_all import load_all_seeds

    print("booting a full agent (boot_core + load_all_seeds) ...", flush=True)
    s_, agent = boot_core()

    class _Agent:
        def __init__(self, s, agent_node):
            self.s = s
            self.inner = s._inner
            self.agent = agent_node

    wa = _Agent(s_, agent)
    load_all_seeds(wa)

    n_rules = wa.inner.rule_count()
    exported = wa.inner.export_rules()
    n_where = sum(1 for r in exported if isinstance(r.get("where"), dict))

    summaries = list(wa.s.nodes("RuleSummary"))
    print(f"\n  installed rule slots (rule_count)   : {n_rules}")
    print(f"  of which carry a `where` Term       : {n_where}")
    print(f"  RuleSummary nodes in the graph      : {len(summaries)}")
    print(f"  ==> RuleSummary mirrors {len(summaries)}/{n_rules} "
          f"= {100.0*len(summaries)/max(n_rules,1):.1f}% of the rule store")

    # Now let the three provenance minters run and re-measure — the point is
    # that even AFTER they run, the mirror is still deliberately partial.
    try:
        import domains.reflective_faculty as rf
        for fn in ("_ensure_acting_rule_provenance", "_ensure_reply_rule_provenance"):
            f = getattr(rf, fn, None)
            if f:
                try:
                    f(wa, wa.inner)
                except Exception as e:
                    print(f"  ({fn} raised {e!r})")
    except Exception as e:
        print(f"  (reflective_faculty unavailable: {e!r})")

    summaries2 = list(wa.s.nodes("RuleSummary"))
    print(f"  RuleSummary after the provenance minters run: {len(summaries2)}")
    print(f"  ==> still {100.0*len(summaries2)/max(n_rules,1):.1f}% of the rule store")

    # And what the flags say about WHY it is partial (a deliberate filter,
    # not an accident).
    flags = {}
    for nid in summaries2:
        a = wa.s.node(nid)["attrs"]
        for k in ("writes_chosen_action", "writes_reply", "skippable"):
            if a.get(k) is not None:
                flags[k] = flags.get(k, 0) + 1
    print(f"  flag population on RuleSummary nodes: {flags}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
