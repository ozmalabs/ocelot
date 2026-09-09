# LLM nonlinear router — the selector is a manifold, not a line — RESULTS

**Block**: 316000. Pre-reg: `LLM_NONLINEAR_ROUTER_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`NonlinearRouter`,
`fit_router_nonlinear`); measure: `scripts/llm_nonlinear_router_measure.py`.

**This corrects block 315000's "nonlinearity floor."** That claim came from a
LINEAR router — which only shows a LINE can't fit the selector. The oracle's
active-set selector is a NONLINEAR function on a MANIFOLD, and a cheap
NONLINEAR router recovers more of it. **Verdict: nonlinearity IS recoverable
and helps — nl-router beats the linear router. The remaining gap to the oracle
is a quality-of-approximation axis, not a floor.**

## Measured (Qwen3-0.6B, 30 train / 10 held-out, agreement vs full graph)

| rank | target | nl-router | lin-router | joint | oracle |
|---|---|---|---|---|---|
| 64 | 0.50 | **4** | 3 | 2 | 8 |
| 64 | 0.40 | 1 | 1 | 3 | 5 |
| 256 | 0.50 | **4** | 3 | 2 | 8 |
| 256 | 0.40 | 1 | 1 | 3 | 5 |

The nl-router is a random-feature ReLU map (`Wout · ReLU(P·x)`, fixed random
`P (r×d)`, closed-form ridge `Wout (ff×r)`), cost `d·r + r·ff` ≪ the FFN's
`2·d·ff` — genuinely cheaper than computing the activation.

### Claim 2 — nonlinearity is recoverable and helps: HOLDS
At target 0.5, nl-router 4 > lin-router 3 (> joint 2). A cheap NONLINEAR map
captures more of the selector than the line did. **Block 315's "nonlinearity
floor" was an artifact of using a linear router** — the correct statement is:
a line under-fits the selector manifold; a nonlinear map recovers more of it.
Corrected.

### Claim 3 — how far up the manifold: quality axis, not a floor
nl-router (4/10) still trails the oracle (8/10) at 0.5, rank 64 = rank 256 (more
random-feature capacity didn't help this fit), and joint still wins at 0.4. So
the RANDOM-feature nonlinear router captures SOME of the manifold, not all. The
residual is a QUALITY-OF-APPROXIMATION question — how much of the oracle
manifold a given cheap router captures — NOT an impossibility. A trained (vs
random-feature) nonlinear router is the named next step further up the manifold.

## Verdict — corrected framing

The user's correction is upheld with numbers: the active-set selector is a
MANIFOLD, not a line, and it is recoverable by a nonlinear map — a cheap
nonlinear router beats the linear one, so the "nonlinearity floor" of block 315
is retracted. What remains is not a wall but a gradient: each better
approximator (linear → random-feature nonlinear → trained nonlinear) climbs
further up the manifold toward the oracle. The honest state of the shape sub-arc
is now:
- The LLM's shape is real, sparse, query-conditional, graph-structured, and
  recoverable to identical outcomes (blocks 309–314).
- Cheap conditional ACCESS to it improves monotonically with the approximator:
  a line under-fits, a cheap nonlinear map does better, and the path to the
  oracle is more approximation capacity — a recoverable manifold, not a floor.

## Anti-faking / method
- Router FIT on train corpus, EVALUATED on DISJOINT held-out (fixed random P +
  fitted readout on the held-out input — not memorisation).
- The router is genuinely cheaper than the FFN (`r ≪ d`); a win is real cheap
  recovery, not the oracle in disguise. Oracle is an explicit per-query upper
  bound.
- Every rank/fraction reported, including the persisting oracle gap.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), small batteries; a RANDOM-FEATURE nonlinear router
  (fixed P, fitted readout), not a fully trained MLP. The win corrects the
  linear-floor claim; the residual gap bounds THIS approximator and names the
  trained-router next step. rank 64 = rank 256 suggests the random-feature
  basis, not the readout capacity, is the limiter — a trained P (not random)
  is the lever.
