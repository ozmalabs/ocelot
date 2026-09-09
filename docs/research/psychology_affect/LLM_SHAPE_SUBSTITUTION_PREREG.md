# LLM shape substitution — is the outcome in the shape? — PREREG

**Block**: 311000

**Task**: The user's framing — *"the recovery is of the TRUE SHAPE that is
encoded in the substrate of the LLM."* Test it directly: SUBSTITUTE the dense
FFN op in the recovered Qwen3-0.6B graph (block 309000) with a SHAPE-NATIVE
operation — retrieve the active memories by geometry — and measure whether the
outcome survives. If it does, the outcome is carried by the SHAPE (which
memories fire), not the specific dense arithmetic.

## 1. Why the FFN is the shape carrier

Geva et al.: a transformer FFN is a bank of KEY-VALUE MEMORIES — `gate_proj`
rows are keys the input queries, `down_proj` columns are the values written.
FFN(x) is thus a RETRIEVAL over a learned dictionary. So the shape-native
substitution is: retrieve the top memories by QUERY-KEY GEOMETRY (the
coherence/kNN primitive this whole arc built) and compute only those — instead
of the dense sum over all neurons.

## 2. The substitution + the honest comparison

`domains/llm_structure_recovery.SparseConfig`:
- **SHAPE-RETRIEVE** (`ffn_retrieve_frac`): select neurons by query-key
  geometry `|x·gate_key|`, retrieve top-k, compute only their up+down. This is
  the shape substitution — a kNN retrieval standing in for the dense FFN.
- **EXACT-TOPK** (`ffn_keep_frac`, block 310000): select neurons by the TRUE
  activation `|silu(gate)·up|`. This is the shape WITH the full descriptor — an
  ORACLE upper bound on which memories matter.

Both keep the same FRACTION of neurons; the GAP between their agreement is how
much of the shape the query-key descriptor MISSES. Agreement measured vs the
full recovered graph (= 100% vs torch).

## 3. Falsifiable claims

1. **Off is bit-exact** (`ffn_retrieve_frac=1.0` => full forward).
2. **The outcome is in the shape**: EXACT-TOPK holds high agreement at a SMALL
   fraction of neurons — i.e. the outcome depends on WHICH sparse memory-set
   fires, not the full dense sum. (Registered threshold: agreement stays high
   at 50% of neurons.)
3. **The gap identifies the missing shape**: SHAPE-RETRIEVE (gate-key only) is
   MEASURABLY WORSE than EXACT-TOPK at the same fraction — the gap localises
   exactly what shape the single query-key direction fails to capture (the
   up-projection's contribution). Reported as the shape-gap curve.

Reported with measured outcomes; whichever way each falls.

## 4. What each outcome means for the framing

- EXACT-TOPK holds at low fraction → the outcome IS in the shape (the sparse
  active-memory set), supporting "the true shape carries the computation."
- SHAPE-RETRIEVE < EXACT-TOPK → the query-key geometry is an INCOMPLETE shape
  descriptor; the still-missing shape is named precisely (joint gate+up key
  structure / coactivation), which is the next thing to recover.
- If EXACT-TOPK ALSO broke at low fraction → the outcome would NOT be in a
  sparse shape (it would need the full dense sum); reported as a failure of the
  framing.

## 5. Anti-faking / bounds

- SHAPE-RETRIEVE really skips the up+down arithmetic for unretrieved neurons
  (real FLOP cut on those); the gate-scoring `x·gate_key` to RANK is itself a
  full matmul, so the FLOP floor is ~0.64–0.81 — reported honestly (a better
  retrieval index would remove that; not built here).
- EXACT-TOPK is explicitly an ORACLE (it peeks at the true activation to
  select) — used to UPPER-BOUND how much the shape can carry, not as a
  deployable cheap op. Stated plainly.
- Agreement on HELD-OUT prompts vs the full graph.
- **default == today**: off is bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.
- One small model, next-token / greedy agreement, theoretical FLOPs.
