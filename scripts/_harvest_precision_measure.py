"""Measure harvest precision: firing-breadth distribution, artifact rate, and
corroborated-axis count over a fixed sample of postulates. Run on BEFORE (stashed)
and AFTER (fixed) states with identical sampling for an apples-to-apples compare."""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from scripts.iter5_frontier import fresh_substrate, install_all
from domains.order_n_postulates import harvest_postulates, synthesize_gaps
from domains.implication_harvester import harvest_shapes_combined
from domains.gap_prioritiser import shape_firing_breadth


def main():
    n_sample = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    s = fresh_substrate(); install_all(s)
    lib = harvest_shapes_combined(s)
    posts = harvest_postulates(s, mt_name=None)
    N = len(posts)
    print(f"shapes={len(lib)} corpus_N={N}")

    # 1) firing breadth distribution (honours match_mode)
    b = shape_firing_breadth(s, lib)
    bv = sorted(b.values())
    over10 = sum(1 for x in bv if x > N * 0.10)
    over5 = sum(1 for x in bv if x > N * 0.05)
    print(f"FIRING_BREADTH median={bv[len(bv)//2]} p90={bv[int(len(bv)*.9)]} "
          f"max={bv[-1]} >10%={over10} >5%={over5}")
    top = sorted(b.items(), key=lambda x: -x[1])[:5]
    print("FIRING_TOP5 " + " | ".join(f"{c}:{nm}" for nm, c in top))

    # 2) synthesize OPEN gaps over the SAME deterministic sample as iter5
    top_productive = [
        "universal_coordination_pattern", "pre_computed_lookup_table",
        "cached_shape", "second_order_scheduler_state_as_graph",
        "reflection_tower_smith_1982", "shape_keyed_lookup",
        "second_order_observability_compounds", "function_shape",
        "memo_function_michie_1968", "hippocampus",
        "drives_estimation_control_pattern", "SIMT_GPU_execution",
        "seven_meta_shape_subsystems_pattern", "meta_shape",
        "epoch_based_reclamation", "lyapunov_stability_check",
        "training_paradigm_brute_force",
        "function_shape_is_cognitive_layer_of_l6_coordination",
        "negative_problem_space_pruning", "DPDK",
    ]
    by_name = {nm: 1 for _, nm, _ in posts}
    stride = max(1, N // max(1, (n_sample - len(top_productive))))
    sample = [posts[i][1] for i in range(0, N, stride)]
    chosen = [c for c in dict.fromkeys(top_productive + sample) if c in by_name][:n_sample]

    total_open = 0
    for nm in chosen:
        try:
            gaps = synthesize_gaps(s, nm, max_order=1, record=True,
                                   prune=True, shapes=lib)
            total_open += len(gaps)
        except Exception:
            continue

    # 3) artifact rate + corroboration: group recorded gaps by capability sig,
    #    count distinct via_shapes per capability axis.
    sig_shapes = {}   # capability-sig -> set(via_shapes)
    sig_count = Counter()
    for nid in s.nodes("SynthesizedGap"):
        a = s.node(nid)["attrs"]
        sig = frozenset(str(k).lower() for k in a.get("capability_keys", []))
        if not sig:
            continue
        sig_shapes.setdefault(sig, set()).update(a.get("via_shapes", []))
        sig_count[sig] += 1
    n_axes = len(sig_shapes)
    single_shape_axes = sum(1 for v in sig_shapes.values() if len(v) == 1)
    corroborated_axes = sum(1 for v in sig_shapes.values() if len(v) >= 2)
    # single-shape-artifact FRACTION of recorded gaps (a gap whose capability is
    # produced by exactly one shape — the iter5 ARTIFACT definition).
    artifact_gaps = sum(c for sig, c in sig_count.items()
                        if len(sig_shapes[sig]) == 1)
    print(f"OPEN_GAPS recorded={len(s.nodes('SynthesizedGap'))} total_open={total_open}")
    print(f"AXES distinct={n_axes} single_shape={single_shape_axes} "
          f"corroborated(>=2)={corroborated_axes}")
    if total_open:
        frac = artifact_gaps / max(1, sum(sig_count.values()))
        print(f"ARTIFACT_FRACTION single_shape_gaps/total={artifact_gaps}/"
              f"{sum(sig_count.values())} = {frac:.1%}")


if __name__ == "__main__":
    main()
