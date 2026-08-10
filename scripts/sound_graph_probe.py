"""sound_graph_probe — the ONE load-bearing test for the sound-as-a-graph reframe.

Claim under test: invariance is FREE in the graph. The FILTER subgraph (formant
RELATIONS — ratios) should make the same digit cluster across speakers BETTER
than the absolute spectrum does, because vocal-tract length is a multiplicative
scale that cancels in the ratios but shifts every spectral bin.

Honest probe, not a tuned pipeline. The extraction (finding formants) still runs
on the spectrum, so the graph is only as clean as that — we report whether the
RELATIONAL structure is nonetheless more invariant, or just inherits the noise.

Metric (LOSO-comparable to the session's numbers raw 0.32 / CMVN 0.60):
For a held-out speaker, classify each of their digit utterances by
nearest-class-prototype, where prototypes are built ONLY from the OTHER
speakers. Accuracy averaged over all held-out speakers = leave-one-speaker-out
accuracy. Run the SAME LOSO classifier on (a) the filter-graph signature and
(b) the spectrum signature. Higher LOSO accuracy = more speaker-invariant.
We also report a Fisher-style same/across separation ratio.
"""
import os
import sys

sys.path.insert(0, os.getcwd())

import numpy as np

import scripts.fsdd_learner_world as fl
from domains.sound_graph import (build_sound_graph, filter_signature,
                                 filter_signature_rich, spectrum_signature,
                                 spectrum_signature_traj, surface_schema)

DIGITS = fl._DIGITS
PER = int(os.environ.get("SG_PER", "12"))      # utterances per (digit,speaker)


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def euclid_sim(a, b):
    return -float(np.linalg.norm(a - b))


def loso_accuracy(samples_by, speakers, sim_fn):
    """Leave-one-speaker-out nearest-prototype accuracy.
    samples_by[(digit, speaker)] = list of feature vectors."""
    accs = []
    for held in speakers:
        # Prototypes per digit from all OTHER speakers.
        protos = {}
        for d in range(len(DIGITS)):
            vecs = []
            for sp in speakers:
                if sp == held:
                    continue
                vecs += samples_by.get((d, sp), [])
            if vecs:
                protos[d] = np.mean(vecs, axis=0)
        # Classify held-out speaker's utterances.
        correct = total = 0
        for d in range(len(DIGITS)):
            for v in samples_by.get((d, held), []):
                best, best_s = None, -1e18
                for pd, pv in protos.items():
                    s = sim_fn(v, pv)
                    if s > best_s:
                        best_s, best = s, pd
                total += 1
                correct += int(best == d)
        if total:
            accs.append(correct / total)
    return float(np.mean(accs)) if accs else 0.0


def separation(samples_by, speakers, sim_fn):
    """Mean same-content-across-speaker similarity vs mean across-content
    similarity. Returns (same, across, ratio)."""
    same, across = [], []
    items = []   # (digit, speaker, vec)
    for (d, sp), vs in samples_by.items():
        for v in vs:
            items.append((d, sp, v))
    for i in range(len(items)):
        di, spi, vi = items[i]
        for j in range(i + 1, len(items)):
            dj, spj, vj = items[j]
            if spi == spj:
                continue   # cross-speaker only (the invariance question)
            s = sim_fn(vi, vj)
            (same if di == dj else across).append(s)
    sm = float(np.mean(same)) if same else 0.0
    ac = float(np.mean(across)) if across else 0.0
    ratio = (sm - ac)
    return sm, ac, ratio


def main():
    print("=" * 70)
    print("SOUND-AS-A-GRAPH probe — filter (relations) vs spectrum, LOSO")
    print("=" * 70)

    # (1) The schema the agent specified (surfaced from its science).
    sch = surface_schema()
    print("\n[1] Sound-graph schema (surfaced from the agent's source-filter "
          "science)")
    print("    NODES:", ", ".join(sch["nodes"]))
    print("    EDGES:", ", ".join(sch["edges"]))
    print("    invariant subgraph =", sch["invariant_subgraph"],
          "| speaker subgraph =", sch["speaker_subgraph"])
    print("    grounded in:")
    for k, v in sch["grounded_in"].items():
        print(f"      - {k}: {v[:110]}...")

    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})
    print(f"\n    speakers: {speakers}  (LOSO over {len(speakers)})")
    print(f"    {PER} utterances per (digit, speaker)")

    # (2) Build features. Four representations, two matched pairs:
    #   collapsed: filter ratios (2 nums)  vs  spectrum envelope (24 bins)
    #   trajectory: filter-ratio traj      vs  spectrum traj (matched dims)
    reps = {
        "filter_collapsed": ({}, euclid_sim),
        "filter_traj":      ({}, euclid_sim),
        "spectrum_flat":    ({}, cosine),
        "spectrum_traj":    ({}, cosine),
    }
    n_empty = 0
    for d in range(len(DIGITS)):
        for sp in speakers:
            files = [p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER]
            for p in files:
                s, fs = fl.load_wav(p)
                sg = build_sound_graph(s, fs)
                fc = filter_signature(sg)
                if not np.any(fc):
                    n_empty += 1
                reps["filter_collapsed"][0].setdefault((d, sp), []).append(fc)
                reps["filter_traj"][0].setdefault((d, sp), []).append(
                    filter_signature_rich(sg))
                reps["spectrum_flat"][0].setdefault((d, sp), []).append(
                    spectrum_signature(s, fs))
                reps["spectrum_traj"][0].setdefault((d, sp), []).append(
                    spectrum_signature_traj(s, fs))
    print(f"    built features; empty filter-sigs: {n_empty}")

    # (3) The numbers.
    print("\n[2] Invariance (cross-speaker), LOSO nearest-prototype accuracy")
    print(f"    chance = {1/len(DIGITS):.2f}  (session refs: raw 0.32, CMVN 0.60)")
    results = {}
    for name, (by, sim) in reps.items():
        acc = loso_accuracy(by, speakers, sim)
        sm, ac, sep = separation(by, speakers, sim)
        dim = len(next(iter(by.values()))[0])
        results[name] = {"loso": acc, "sep": sep, "same": sm, "across": ac,
                         "dim": dim}
        print(f"    {name:18s} dim={dim:3d}  LOSO acc={acc:.3f}  "
              f"sep(same-across)={sep:+.3f}")

    # (4) Verdict — compare the matched-dimensionality trajectory pair, the
    #     fair head-to-head (filter relations vs absolute spectrum, same dims).
    g = results["filter_traj"]["loso"]
    sp_acc = results["spectrum_traj"]["loso"]
    print("\n[3] VERDICT (matched-dimensionality: filter_traj vs spectrum_traj)")
    print(f"    filter (relations) LOSO={g:.3f}  vs  spectrum (abs) LOSO={sp_acc:.3f}")
    if g > sp_acc + 0.03:
        print("    -> The FILTER GRAPH is MORE speaker-invariant by construction.")
        print("       The ratio relations cancel vocal-tract length; would")
        print("       reduce the need for the CMVN/VTLN/predict-remove chain.")
    elif g < sp_acc - 0.03:
        print("    -> The filter graph is LESS invariant: the formant extraction")
        print("       is noisy enough that the relational structure INHERITS the")
        print("       spectral problem rather than dissolving it. The graph is")
        print("       only as clean as the spectral peak-picking it rests on.")
    else:
        print("    -> No clean win: relational structure neither clearly")
        print("       dissolves nor clearly inherits the invariance problem at")
        print("       this extraction quality.")
    return results


if __name__ == "__main__":
    main()
