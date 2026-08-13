"""
SPIKE / PROOF-OF-CONCEPT ONLY -- NOT PRODUCTION CODE.

Part of CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md Sec 3.3 / Sec 6 (revised).
Pure Python, standalone, no Rust, no PyO3, no seeds, no substrate import.

Tests the OUTCOME-equivalence bar for "polarization," not formal fidelity
to a Curie-Weiss phase transition: does a discrete CODEBOOK-DECODE
mechanism, with an "attention"/scrutiny analog implemented as the
EXISTING ShapeDecode-style notion of how much agreement is required before
a match is accepted (a stand-in for the beam/max_steps/cand_k/budget
parameters ShapeDecode already exposes, term.rs's TermNode::ShapeDecode),
reproduce the qualitative PHENOMENON polarization is actually about: a
population with a smooth, uniform, continuum-valued TRUE underlying
position clusters into a small number of mutually-incompatible, internally
-consistent, EXTREME resolved stances as scrutiny increases, rather than
resolving smoothly across the middle -- with a sharpening/threshold
character as scrutiny (the native "attention" analog) increases.

Does NOT touch runners/dsl/src/shape_decode.rs or any production path.
"""

import random

N = 8
PROTO_PRO = [1] * N
PROTO_ANTI = [-1] * N
TRIALS_PER_ALPHA = 40


def individual_components(alpha, rng):
    """One individual's TRUE, per-component-INDEPENDENT position: each of
    the N components independently leans PRO with probability alpha, ANTI
    otherwise (Binomial-style heterogeneity, not a lock-step blend -- a
    real individual's own N belief components need not all move together).
    alpha is each individual's own latent "true" leaning, drawn uniformly
    over [0,1] across the population -- the smooth-continuum null input
    this check tries to falsify."""
    return [1 if rng.random() < alpha else -1 for _ in range(N)]


def classify(components, scrutiny_T):
    """Decode this individual's observed (already-quantized, {-1,+1})
    position against the two held prototypes. scrutiny_T is the coverage
    threshold -- how many of the N components must agree with a prototype
    before it counts as a recognized match, the native stand-in for
    ShapeDecode's own beam/max_steps/cand_k/budget knobs (how hard the
    decode looks / how much it demands before accepting a candidate)."""
    agree_pro = sum(1 for x, p in zip(components, PROTO_PRO) if x == p)
    agree_anti = N - agree_pro
    matches_pro = agree_pro >= scrutiny_T
    matches_anti = agree_anti >= scrutiny_T
    if matches_pro and not matches_anti:
        return "pro"
    if matches_anti and not matches_pro:
        return "anti"
    if matches_pro and matches_anti:
        return "ambiguous"
    return "unresolved"


def run(scrutiny_T, n_alpha=41, seed=2026):
    rng = random.Random(seed)
    counts = {"pro": 0, "anti": 0, "ambiguous": 0, "unresolved": 0}
    resolved_alphas = []
    for k in range(n_alpha):
        alpha = k / (n_alpha - 1)
        for _ in range(TRIALS_PER_ALPHA):
            comps = individual_components(alpha, rng)
            c = classify(comps, scrutiny_T)
            counts[c] += 1
            if c in ("pro", "anti"):
                resolved_alphas.append(alpha)
    if resolved_alphas:
        near_extreme = sum(1 for a in resolved_alphas if a < 0.2 or a > 0.8)
        frac_extreme = near_extreme / len(resolved_alphas)
    else:
        frac_extreme = float("nan")
    return counts, frac_extreme, len(resolved_alphas)


def main():
    print("A population with a uniform, smooth, continuum-valued latent "
          "leaning (alpha in [0,1], 41 levels x 40 independent individuals "
          "each, per-component-independent, N=8 components) decoded "
          "against two fixed prototype configurations, at increasing "
          "decode SCRUTINY (the native attention/engagement analog -- how "
          "many of N=8 components must agree before a match is accepted).")
    print()
    print(f"{'scrutiny_T':>10}  {'pro':>6} {'anti':>6} {'ambig':>6} "
          f"{'unresolved':>10}  {'frac_resolved_near_extreme':>28}")
    for T in range(1, N + 1):
        counts, frac_extreme, n_resolved = run(T)
        fe = f"{frac_extreme:.3f}" if n_resolved else "n/a"
        print(f"{T:>10}  {counts['pro']:>6} {counts['anti']:>6} "
              f"{counts['ambiguous']:>6} {counts['unresolved']:>10}  {fe:>28}")

    print()
    print("Registered prediction, checked against the table above: as "
          "scrutiny_T rises, the RESOLVED population should not merely "
          "shrink -- it should become MORE concentrated near the extremes "
          "(frac_resolved_near_extreme should rise toward 1.0), i.e. those "
          "who do resolve, resolve to a pole, not to the middle -- the "
          "qualitative polarization/clustering outcome, produced by a "
          "static coverage-threshold decode with NO Boltzmann ensemble, "
          "NO continuous inverse temperature, and no iteration at all.")


if __name__ == "__main__":
    main()
