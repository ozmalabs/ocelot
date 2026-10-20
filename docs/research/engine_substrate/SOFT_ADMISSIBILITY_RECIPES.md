# Soft Admissibility and Soft Exclusion Recipes (`SoftWeights`)

Phase 2 (`COGNITION_BUILD_P2_GRADED_PRIMITIVES_PLAN.md` §P2.C1.5) provides graded candidate weighting via a single binder Term, `SoftWeights`, without introducing a separate `SoftExclude` primitive.

## 1. `SoftWeights` Contract

```json
{
  "type": "SoftWeights",
  "source": <collection-term>,
  "var_name": "c",
  "value": <numeric-term-over-c>,
  "temperature": <numeric-term>,
  "default": <optional-fallback-term>
}
```

- Evaluates `value` for each element `c` in `source.snapshot()` (skipping non-numeric or non-finite values).
- For temperature $T > 0$, returns a `List` of 2-tuples `(c, w_c)` where
  $$w_c = \frac{\exp((v_c - v_{\max}) / T)}{\sum_j \exp((v_j - v_{\max}) / T)}.$$
- For $T \le 0$, splits weight $1/k$ equally across the $k$ tied maxima and assigns $0.0$ to all other surviving candidates.
- Tuple slots are read with `Nth`:
  - Candidate element: `{"type": "Nth", "items": {"type": "Var", "name": "pair"}, "index": 0}`
  - Candidate weight: `{"type": "Nth", "items": {"type": "Var", "name": "pair"}, "index": 1}`

## 2. Soft Exclusion Recipe (`score - penalty * excluded`)

Hard `Filter` predicates discard any candidate with `excluded == 1`, leaving an empty set when every candidate has been pruned at a tight tolerance. To down-weight excluded candidates while keeping them reachable when no unexcluded candidate dominates, compose `value` as `Minus(score, Times(penalty, excluded))`:

```json
{
  "type": "SoftWeights",
  "source": {
    "type": "Neighbours",
    "node": {"type": "Var", "name": "ctx"},
    "edge_type": "has_candidate"
  },
  "var_name": "c",
  "value": {
    "type": "Minus",
    "a": {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "score"},
    "b": {
      "type": "Times",
      "items": [
        {"type": "Attr", "node": {"type": "Var", "name": "policy"}, "key": "exclusion_penalty"},
        {"type": "Attr", "node": {"type": "Var", "name": "c"}, "key": "excluded"}
      ]
    }
  },
  "temperature": {"type": "Attr", "node": {"type": "Var", "name": "policy"}, "key": "temperature"}
}
```

### Properties
1. **Nonzero survival:** For any finite `exclusion_penalty` and $T > 0$, an excluded candidate retains weight $w_c > 0$ and can still be recovered if all unexcluded candidates fail downstream verification.
2. **Monotone suppression:** Increasing `exclusion_penalty` strictly decreases the excluded candidate's Boltzmann weight relative to unexcluded candidates (`tests/test_soft_weights_term.py::test_soft_exclusion_recipe_retains_nonzero_weight_that_falls_with_penalty`).
3. **Hard-filter limit:** As `exclusion_penalty` $\to \infty$ (or $T \to 0^+$ with an unexcluded candidate exceeding `score - penalty`), the excluded candidate's weight approaches $0$.
