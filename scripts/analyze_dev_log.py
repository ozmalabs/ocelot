"""Analyze a developmental session's JSONL log + look for phase
transitions.

Usage: python scripts/analyze_dev_log.py /tmp/develop_log_100.jsonl
"""
from __future__ import annotations

import json
import sys


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/develop_log_100.jsonl"
    records = [json.loads(l) for l in open(path)]
    n = len(records)
    print(f"{n} cycles\n")

    # === Trajectory summary table — every Nth cycle ===
    step = max(1, n // 20)
    print(f"{'cyc':>4} {'stage':<22} {'mc':>5} {'Δthr':>6} "
          f"{'imp':>4} {'hyp':>4} {'phon':>4} {'signs':>5} "
          f"{'H':>5} {'bab':>4} {'invt':>5} {'acc':>4}")
    for i in range(0, n, step):
        r = records[i]
        mc = r['motor_coherence']
        mc_avg = sum(mc.values())/len(mc) if mc else 0.0
        print(f"{r['cycle']:>4} {r.get('dev_stage','?'):<22} "
              f"{mc_avg:>5.2f} {r['predicate_delta_norm']:>6.2f} "
              f"{r['impasses_raised']:>4} {r['hypotheses_minted']:>4} "
              f"{r['n_phonology_concepts']:>4} "
              f"{r['n_signs']:>5} "
              f"{r['exhibits_entropy_bits']:>5.2f} "
              f"{r.get('dev_babble_n', 0):>4} "
              f"{r.get('dev_invention_thr', 0):>5.2f} "
              f"{r['recognition_acc']:>4}")

    # === Stage transitions ===
    print("\nstage transitions:")
    prev = None
    for r in records:
        s = r.get('dev_stage')
        if s != prev:
            print(f"  c{r['cycle']:>4}  {prev or '(start)':<22}"
                  f" → {s}")
            prev = s

    # === Phase-transition detection in any metric ===
    print("\nstep-functions (Δ > 3*median |Δ|):")
    for key in ('recognition_acc', 'n_phonology_concepts',
                  'exhibits_entropy_bits', 'n_signs'):
        values = [r[key] for r in records]
        diffs = [abs(values[i+1] - values[i])
                   for i in range(n-1)]
        sorted_diffs = sorted(d for d in diffs if d > 0)
        if not sorted_diffs:
            continue
        med = sorted_diffs[len(sorted_diffs) // 2]
        steps = [(i+1, values[i], values[i+1], abs(values[i+1] - values[i]))
                   for i in range(n-1)
                   if abs(values[i+1] - values[i]) > 3 * med + 0.01]
        if steps:
            print(f"  {key}:")
            for cyc, before, after, delta in steps[:5]:
                print(f"    c{cyc}: {before} → {after} (Δ={delta:.2f})")

    # === Motor coherence ceiling ===
    mc_avgs = []
    for r in records:
        mc = r['motor_coherence']
        mc_avgs.append(sum(mc.values())/len(mc) if mc else 0.0)
    print(f"\nmotor coherence trajectory:")
    print(f"  start:  {mc_avgs[0]:.3f}")
    print(f"  c{n//4}:   {mc_avgs[n//4]:.3f}")
    print(f"  c{n//2}:   {mc_avgs[n//2]:.3f}")
    print(f"  c{3*n//4}:   {mc_avgs[3*n//4]:.3f}")
    print(f"  end:    {mc_avgs[-1]:.3f}")
    print(f"  max:    {max(mc_avgs):.3f} (cycle "
          f"{mc_avgs.index(max(mc_avgs))+1})")

    # === Predicate threshold trajectory ===
    print(f"\npredicate thresholds (initial → final):")
    init_thrs = records[0]['thresholds']
    final_thrs = records[-1]['thresholds']
    for k in init_thrs:
        print(f"  {k:<20s}  {init_thrs[k]:.3f} → "
              f"{final_thrs.get(k, 0):.3f}")

    # === Feature invention ===
    last_phon = records[-1]['n_phonology_concepts']
    init_phon = records[0]['n_phonology_concepts']
    if last_phon > init_phon:
        print(f"\n✦ FEATURE INVENTION: {init_phon} → {last_phon} "
              f"phonology concepts")
        for r in records:
            if r['n_phonology_concepts'] > init_phon:
                print(f"  first appeared c{r['cycle']}")
                break
    else:
        print(f"\nno feature invention: stayed at {init_phon} "
              f"phonology concepts")

    # === Recognition step detection ===
    accs = [r['recognition_acc'] for r in records]
    max_acc = max(accs)
    max_cyc = accs.index(max_acc) + 1
    final_acc = accs[-1]
    early_avg = sum(accs[:5]) / 5
    late_avg = sum(accs[-5:]) / 5
    print(f"\nrecognition: early avg {early_avg:.1f} → "
          f"late avg {late_avg:.1f}, "
          f"max {max_acc} (c{max_cyc})")


if __name__ == "__main__":
    main()
