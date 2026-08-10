# Native fusion — the NEW hearing path's FUSION DECISION as a graph-resident Rust Term

Rank-1 of the migration audit (`a87613a4df1e5e200`). Per `CLAUDE.md` the agent IS a typed
graph in Rust; the recognition DECISION must be a graph-resident Term, not a Python dict
comprehension. This migrates the new/SOTA multi-pronged fusion decision off Python and into
a native `Term` evaluated by `substrate.evaluate` (native Rust eval), faithfully.

## The fusion that was ported (read-only — scoring files NOT modified)

`scripts/articulatory_gamma.py` ~600–611 and `scripts/perception_composition.py` ~384–390,
per held-out token:

```
log_a_h_c[w] = log_a_h[w] - max_w' log_a_h[w']          # formant prong, top-centred
log_a_a_c[w] = log_a_a[w] - max_w' log_a_a[w']          # articulatory prong, top-centred
logA[w]      = log_a_h_c[w] + w_art * log_a_a_c[w] + ng_logp[w]
predict      = argmax_w logA[w]
```

`log_a_h` / `log_a_a` are the per-prong RAW log-admissibilities, `w_art` is the
train-measured reliability weight (inner-LOSO on TRAIN speakers only), `ng_logp` is the
train-only n-gram log-prior (already top-centred).

## (1) The native Term-tree wired

`domains/native_fusion.py`. Per candidate word `w`, the top-centring is done IN the graph
(a `MaxOver` over the SAME candidate-word set, fresh inner var so it does not shadow the
outer `Argmax` var):

```
score(w) = Plus([
    Minus( Attr(w, log_a_h),  MaxOver_w'( Attr(w', log_a_h) ) ),                 # formant, top-centred
    Times([ Lit(w_art),  Minus( Attr(w, log_a_a), MaxOver_w'( Attr(w', log_a_a) ) ) ]),  # articulatory, weighted
    Attr(w, ng_logp),                                                            # n-gram log-prior
])
predict = Argmax over { Concept : is_word == 1 } of score(w)
```

This mirrors `domains/weighted_admissibility.predict_weighted_term` (Argmax over a graph
score). The Python wrapper feeds the RAW (un-centred) prong channels as graph attrs and
reads back the argmax word — the centring + weighting + summing + argmax are all the native
evaluator.

### Donkey audit — every primitive verified to exist in `runners/dsl/src/term.rs`

| Term      | term.rs | jsonio.rs parse tag |
|-----------|---------|---------------------|
| `Argmax`  | L146    | L778                |
| `Plus`    | L262    | L859                |
| `Minus`   | L263    | L860                |
| `Times`   | L264    | L864                |
| `MaxOver` | L71     | L771                |
| `Attr`    | L35     | L651                |
| `Var`     | L32     | L648                |
| `Lit`     | L33     | L649                |
| `NodesWhere` | L367 | L1016               |

ZERO new primitives. Native eval via `substrate.evaluate`. No net, no `.fit`, no gradient,
no sweep, no learned weight — `w_art` is the train-measured reliability constant, entered as
a `Lit`. The scoring files `articulatory_gamma.py` and `perception_composition.py` are
NOT modified (verified via `git diff --stat`: no diff). `CortexLoop` / `solve_for_n`
untouched.

## (2) Native vs Python accuracy + per-token agreement (FSDD LOSO, n=3000)

Driver: `scripts/native_fusion_accept.py` (re-runs the new-path LOSO loop with read-only
helpers, computes BOTH fusions per token). Full log: `/tmp/native_fusion_full.log`.

| metric                              | value          |
|-------------------------------------|----------------|
| n (held-out tokens, never banked)   | 3000           |
| chance                              | 0.1000         |
| PYTHON-fusion accuracy              | **0.5940**     |
| NATIVE-fusion accuracy              | **0.5940**     |
| per-token AGREEMENT                  | **1.0000** (3000/3000, disagree=0) |

Identical to the 59.4% gap-dropped baseline class. (Quick `--quick` smoke run: n=360, both
0.5889, agreement 1.0000.)

## (3) VERDICT

FAITHFUL. The new path's fusion DECISION is now a graph-resident Rust `Term` — the same
arithmetic, evaluated by `substrate.evaluate`, reproducing the Python decision EXACTLY
(identical accuracy, 100% per-token agreement, zero disagreements over 3000 tokens). This
brings the NEW hearing path's fusion to parity with the OLD path
(`weighted_admissibility.predict_weighted_term`), which was already native. No discrepancy
to root-cause. The `-1e18` sentinel for non-finite formant distances is handled identically
in both: a sentinel word never wins the `MaxOver` top-centring nor the `Argmax`, matching
the Python guard.
