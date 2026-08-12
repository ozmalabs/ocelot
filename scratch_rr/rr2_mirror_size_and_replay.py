#!/usr/bin/env python3
"""RR2 — the measured size of a rule mirror, and the checkpoint-replay
amplification, both LIVE against the committed engine, with NO engine change.

Why this needs no build: `PySubstrate::add_term_subgraph` (py.rs:8551) is
already `reflect::term_to_subgraph` exposed — the *exact* operation a mirror
on `add_rule` would perform on a rule's `where` Term. So the per-rule mirror
cost is directly measurable today, on real seed rules, by calling it.

Read-only with respect to the repo; the substrates built here are throwaway.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402


def seed_rules(seed_dir):
    out = []
    for fn in sorted(os.listdir(seed_dir)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(seed_dir, fn)) as fh:
                blob = json.load(fh)
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and isinstance(r.get("where"), dict):
                out.append((fn, r.get("name"), r["where"]))
    return out


def main():
    rules = seed_rules(os.path.join(HERE, "seeds"))
    print(f"seed rules carrying a `where` Term: {len(rules)}")

    # ---- per-rule mirror size, measured -------------------------------
    per_rule = []
    failures = 0
    s = srs.Substrate()
    before_all = s.node_count()
    for fn, nm, where in rules:
        b = s.node_count()
        try:
            s._inner.add_term_subgraph(where)
        except Exception:
            failures += 1
            continue
        per_rule.append((fn, nm, s.node_count() - b))
    total = s.node_count() - before_all

    sizes = sorted(x[2] for x in per_rule)
    n = len(sizes)
    print(f"\nMirrored {n} rules ({failures} refused by add_term_subgraph)")
    print(f"  TOTAL graph nodes minted by mirroring every seed `where`: {total:,}")
    print(f"  mean per rule  : {total / max(n,1):.1f}")
    print(f"  median         : {sizes[n//2]}")
    print(f"  p90 / p99 / max: {sizes[int(n*0.90)]} / {sizes[int(n*0.99)]} / {sizes[-1]}")
    top = sorted(per_rule, key=lambda x: -x[2])[:5]
    print("  largest single-rule mirrors:")
    for fn, nm, k in top:
        print(f"    {k:>7,} nodes  {nm}  (seeds/{fn})")

    # ---- what a booted agent actually holds ---------------------------
    print("\n--- live booted agent (the spike's §12 item 5: it never booted one) ---")
    from substrate.world_adapter import WorldAdapter  # noqa: E402
    wa = WorldAdapter()
    exported = wa.inner.export_rules()
    live_where = [r for r in exported if isinstance(r.get("where"), dict)]
    print(f"  default-boot rule slots           : {len(exported)}")
    print(f"  of which carry a `where` Term     : {len(live_where)}")
    print(f"  graph nodes at boot               : {wa.s.node_count():,}")

    s2 = srs.Substrate()
    b2 = s2.node_count()
    ok = 0
    for r in live_where:
        try:
            s2._inner.add_term_subgraph(r["where"])
            ok += 1
        except Exception:
            pass
    live_mirror = s2.node_count() - b2
    print(f"  mirror nodes for the LIVE rule population ({ok} rules): {live_mirror:,}")
    print(f"  ==> mirroring would multiply this agent's graph by "
          f"{(wa.s.node_count() + live_mirror) / max(wa.s.node_count(),1):.2f}x")

    # ---- the checkpoint-replay amplification --------------------------
    # `WorldAdapter.save()` dumps `graph_to_dict()` (which WOULD include the
    # mirror nodes) AND `export_rules()`. `WorldAdapter.load()` does
    # `graph_from_dict(blob["graph"])` (restoring the mirror) and THEN
    # `import_rules(blob["rules"])`, which replays `inner.add_rule` per rule
    # (py.rs:4576). If `add_rule` mirrored, every load would re-mint on top
    # of the restored mirror — the Γ thread's own measured defect
    # (GAMMA_PYO3_REROUTE_RESULTS.md §2.5, +261 nodes/cycle, unbounded).
    #
    # Simulated here WITHOUT an engine change: mirror after each load, exactly
    # where `add_rule` would have.
    print("\n--- checkpoint-replay amplification (simulated at the exact seam) ---")
    import tempfile
    tmp = tempfile.mkdtemp()
    cur = WorldAdapter()
    for i in range(4):
        # stand in for "add_rule mirrored during import_rules"
        for r in cur.inner.export_rules():
            w = r.get("where")
            if isinstance(w, dict):
                try:
                    cur.s._inner.add_term_subgraph(w)
                except Exception:
                    pass
        p = os.path.join(tmp, f"ck_{i}.json")
        cur.save(p)
        sz = os.path.getsize(p)
        cur = WorldAdapter.load(p)
        print(f"  cycle {i}: nodes={cur.s.node_count():>9,}  "
              f"edges={cur.s.edge_count():>9,}  checkpoint={sz/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
