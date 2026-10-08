# Witness-margin over-fit fix + authorable linrec2 recurrence reading for the sequence domain

Two coupled changes to `tests/capability/number_qualia/runners/number_runner.py`, plus C7–C11 added to `track_j6_class_fingerprint_memory.py`. The first fixes an over-fit where short recurrences (Pell, Fibonacci) were read as high-degree polynomials: a scaled witness margin makes a degree-`k` claim credible only when `k <= len(seq) - 2 - 1`, applied to **both** `seq_felt_degree` and `seq_verify_degree` so their agreement (track_j4 S1) holds. The second adds `seq_read_linrec2`, an authorable order-2 linear-recurrence reading (exact rational 2×2 solve for `(a,b)`, then an all-terms exact check), registered after `log_degree` so it splits the `(None,None)` no-rescue bucket and gives Fibonacci its own class key. Both changes are behavior-preserving on the existing tracks and fully solver-free.

Watch for: (1) **confirmed** — the class key records only the reading *name* `'linrec2'`, not the `(a,b)` signature, so Pell `(a=2,b=1)` and Fibonacci `(a=1,b=1)` — genuinely distinct recurrences — collapse to the same key `(None,'linrec2')`; holding a Fibonacci anti-shape now repels Pell. This is a *new* merge introduced by this change (on the base branch Pell was `(5,None)` via the over-fit bug, Fibonacci was `(None,None)` — they did not share a key). It is the same class-merge defect the task set out to remove, displaced one level down, and the task spec itself calls Pell `(2,1)` a distinct class. (2) **confirmed** — the "order matters / geometric is also a linrec2" rationale in the docstrings and report is misleading: a true geometric sequence has a degenerate determinant (`x1² − x0·x2 = 0`), so `linrec2` abstains on it regardless of registration order; the ordering is harmless but is not what protects geometric. (3) **confirmed** — stale docstrings on `seq_class_key` and the track_j6 module header still describe Fibonacci as `(None,None)`.

**Verdict**: NEEDS_CHANGES

## High-level view

The witness margin is principled and correctly symmetric. Probed across the length/degree boundary, felt and verify agree on every case: genuine polynomials keep their exact degree (`n^3` from 6 points stays 3 because `3 <= 6-2-1`), and both Pell and Fibonacci go to `None`. The margin does not wrongly accept any non-polynomial, and where it rejects a real polynomial (a genuine degree-4 given only 6 points) it does so symmetrically in felt and verify — an honest "under-witnessed" abstention, not a disagreement. `margin=2` is the correct value: `margin=3` would kill legitimate `n^3` from 6 points.

`seq_read_linrec2` is genuinely composed and honest: an exact rational 2×2 solve for `(a,b)` from the first two triples, then a verification that the recurrence holds across *every* term. A Fibonacci-prefix that breaks at the last term returns `None`; sequences under 4 terms return `None`; degenerate determinants return `None`. It is solver-free (`SolverSpy.calls == 0`) — the "solve" is pure `Fraction` arithmetic, and feel-then-verify is respected (the felt claim is the `(a,b)` fit; the verification is the all-terms check).

The bucket split works for the cases the tests probe: Fibonacci `(None,'linrec2')`, geometric `(None,'log_degree')`, and primes `(None,None)` are three distinct keys, and none cross-repels the others. Fibonacci and Lucas correctly share `(None,'linrec2')` (same recurrence). Geometric stays on `log_degree` because it is claimed first *and* because `linrec2` abstains on it anyway.

The gap is that the split is coarser than the reading it is built on. `seq_authorable_claim` returns the reading *name*, so all order-2 recurrences — Fibonacci, Lucas, Pell — land in one key even though `seq_read_linrec2` distinguishes them by signature. The result is a fresh cross-class false distrust between Pell and Fibonacci that did not exist before this change. The tests pass only because C9 probes Fibonacci against geometric and primes, never against Pell.

Everything else holds: tracks j, j2, j3, j4, j5, j6 all pass; the conceptualizer audit is green; the `.so` md5 is unchanged; `seeds/` and `/applications` were not touched by this task; net_valence and the composed graph Term are untouched; no `_probe_` files remain; nothing is committed.

<details>
<summary>Issues (4)</summary>

1. **Pell/Fibonacci key merge (new false distrust)** — `seq_class_key` records only the reading name `'linrec2'`, so Pell `('linrec2',2,1)` and Fibonacci `('linrec2',1,1)` share `(None,'linrec2')` and a held Fibonacci anti-shape repels Pell. Fix by keying on the reading's full signature (namespacing `log_degree` too, since it returns a bare int) so Pell and Fibonacci get distinct keys, as the task spec intends. **confirmed**
2. **C9 coverage gap** — C9 tests Fibonacci-vs-geometric and Fibonacci-vs-primes but never Fibonacci-vs-Pell, so the merge above passes unnoticed. Add a Pell-vs-Fibonacci no-cross-repel assertion. **confirmed**
3. **Misleading "order matters / geometric is a linrec2" rationale** — geometric is degenerate for `linrec2` (`det == 0`), so it never competes; the ordering is harmless but the stated justification is wrong. Correct the docstring on `_SEQ_AUTHORABLE` and the report prose. **confirmed**
4. **Stale docstrings** — `seq_class_key` (number_runner.py:1648-1649) and the track_j6 module header (track_j6…:20-22) still describe Fibonacci as `(None,None)`. Update to `(None,'linrec2')`. **confirmed**

</details>

<details>
<summary>Details</summary>

### Witness margin: symmetric, principled, correct at the boundary

`_degree_credible(k, n)` returns `k <= n - _SEQ_WITNESS_MARGIN - 1` (margin 2), and it gates both readings — `seq_felt_degree` breaks the search once `k` stops being credible, `seq_verify_degree` returns `None` at the same threshold. Applying it to both is what preserves felt==verify. Probed across the boundary, they agree everywhere:

```
                    len  felt  verify
const                6    0     0
2n+1                 6    1     1
n^2                  6    2     2
n^3                  6    3     3     (3 <= 6-2-1, credible)
n^4                  6   None  None   (4 > 6-2-1, under-witnessed)
n^4                  7    4     4     (4 <= 7-2-1, credible)
1+n+n^2+n^3+n^4      6   None  None   (real deg-4, honestly abstained at 6 pts)
pell (7 pts)         None None         (was felt=5 on base — the over-fit)
fibonacci (8 pts)    None None
```

The one case where the margin rejects a *real* polynomial — a genuine degree-4 given exactly 6 points — is not a defect: 6 points cannot distinguish a degree-4 polynomial from a coincidence at the top difference, and the read abstains symmetrically in both felt and verify rather than disagreeing. `margin=2` is the right knob (the diff notes `margin=3` kills `n^3` from 6 points, confirmed by the boundary above), so it is scaled to the witness-count principle, not tuned to pass the specific Pell/Fibonacci inputs. No non-polynomial is wrongly accepted as a low degree in any probed case.

### linrec2 is composed, feel-then-verify, and solver-free

`seq_read_linrec2` solves the 2×2 system `[[x1,x0],[x2,x1]]·(a,b) = (x2,x3)` exactly over `Fraction`, guards the degenerate determinant, then checks `x[n] == a·x[n-1] + b·x[n-2]` for every `n >= 2`. The all-terms check is what makes it a reading rather than a Fibonacci detector — it fires on any constant-coefficient order-2 recurrence and abstains the moment a later term breaks it:

```
fibonacci -> ('linrec2', 1, 1)      lucas -> ('linrec2', 1, 1)      pell -> ('linrec2', 2, 1)
[0,1,1,2,3,5,8,99] -> None (breaks at last term)     [0,1,1] -> None (<4 terms)
geometric -> None (degenerate det)   primes/quad/cubic -> None
```

`SolverSpy.calls` stays 0 across `seq_read_linrec2`, `seq_felt_degree`, `seq_class_key`, and `seq_authorable_claim` — the solve is arithmetic, and the verify gate in `seq_extend_repertoire` pings the spy separately for its own check. The reading-specific verify gate is honest: `log_degree` is confirmed by an explicit constant-ratio check, and `linrec2`'s non-`None` return *is* the verified all-terms claim, so re-verifying would be redundant.

### The key merges what the reading distinguishes

`seq_class_key(seq) = (seq_felt_degree(seq), seq_authorable_claim(seq))`, and `seq_authorable_claim` returns the first non-`None` reading's **name**, discarding the signature:

```
              seq_read_linrec2        seq_class_key
fibonacci     ('linrec2', 1, 1)       (None, 'linrec2')
lucas         ('linrec2', 1, 1)       (None, 'linrec2')
pell          ('linrec2', 2, 1)       (None, 'linrec2')   <-- distinct recurrence, same key
```

So the memory treats Pell and Fibonacci as the same anti-shape:

```
hold fibonacci (mint anti-shape, key (None,'linrec2'))
  then pell  -> repelled_by_held_antishape      <-- FALSE DISTRUST
```

This is a *new* merge. On the base branch (06475bca) Pell keyed `(5,None)` (via the over-fit bug) and Fibonacci keyed `(None,None)`; they were separate. This change moves both to `(None,'linrec2')`, so the "split the `(None,None)` bucket" goal is achieved for Fibonacci-vs-primes but simultaneously introduces a Fibonacci-vs-Pell collision — the same category of defect, one level down. The task spec explicitly names Pell `(2,1)` as distinct from Fibonacci `(1,1)`, so this is a correctness gap against the stated intent, not merely a stylistic choice.

The reason the name-only key exists is real and worth respecting: `seq_read_log_degree` returns a bare int (geometric → 1), so a naive full-signature key would make geometric `(None, 1)`, colliding with felt-degree keys and losing the reading identity. A proper fix keys on a namespaced signature — e.g. `('log_degree', d)` and the existing `('linrec2', a, b)` — so both readings split correctly. This keeps the key solver-free (both components are arithmetic) and preserves the phase-A felt rule-out.

C9 misses this because it only holds Fibonacci and probes geometric and primes (different felt/name components, correctly not repelled). A Pell-vs-Fibonacci assertion would have caught it and should be added alongside the fix.

### "Order matters" is the wrong explanation for geometric

The `_SEQ_AUTHORABLE` docstring and the implementation report argue that geometric is "ALSO a linrec2 with a=ratio, b=0" and is protected only because `log_degree` is registered first. That is not what happens: for any true geometric sequence `x[n] = r·x[n-1]`, the determinant `x1² − x0·x2 = (r·x0)² − x0·(r²·x0) = 0`, so `seq_read_linrec2` returns `None` on geometric outright (confirmed for 2^n, 3^n, 4^n). Geometric would key `(None,'log_degree')` even if `linrec2` were tried first. The ordering is harmless, but presenting it as the safety mechanism is misleading and would mislead a future maintainer who reorders the dict thinking it is load-bearing. The genuine invariant is the degenerate-determinant guard.

</details>

<details>
<summary>File map</summary>

- `tests/capability/number_qualia/runners/number_runner.py` — adds `_SEQ_WITNESS_MARGIN`/`_degree_credible`, gates `seq_felt_degree` and `seq_verify_degree` on the margin, adds `seq_read_linrec2`, registers it in `_SEQ_AUTHORABLE` after `log_degree`, and makes `seq_extend_repertoire`'s verify gate reading-specific. `seq_class_key`/`seq_authorable_claim` unchanged in structure (name-only key — the merge origin). Stale `seq_class_key` docstring at lines 1648-1649.
- `tests/capability/number_qualia/track_j6_class_fingerprint_memory.py` — adds C7 (over-fit fixed), C8 (linrec2 signatures), C9 (bucket split — missing Pell-vs-Fibonacci), C10 (self-extension authors linrec2), C11 (solver-free); one C6 datum changed from 6 to 7 points to respect the margin. Stale module-header key description at lines 20-22.

Full diff: `git diff 06475bca -- tests/capability/number_qualia/runners/number_runner.py tests/capability/number_qualia/track_j6_class_fingerprint_memory.py`

</details>
