# Track 3 benchmark-issue repro artifact — independent verification

Independently re-ran `drafts/track3_sim/issue/reproduce.py` against the public repo
checkout (`.bigtmp/track3`) using the in-env `track3-abides-baseline:latest` image and
the shipped 65-scenario reference cache. Confirmed the script is self-contained and
public-only, that its per-gate results match `ISSUE.md`, and that the honest caveat is
present and accurate. One framing nit about the previous stage's provenance claim, but
nothing that undermines the artifact.

**Verdict**: APPROVED — the artifact runs clean, is portable, and its numbers match the
issue body. The issue is safe for a human to file.

## High-level view

The repro script imports only public toolkit code (`qfbench2_track_simulation.semantics`
`check_tier_a`/`check_tier_b`/`mid_price_series`/`depth_histogram`; `qfbench2_common.scoring.stylized_facts`
`stylized_fact_report`/`admissible`) and drives only the public baseline image + shipped
scenarios + reference cache. It contains no reference to `.bigtmp`, `track3_drawmap`, our
drafts, or the local `.env`. All imported signatures and default gate parameters
(Tier-A tol 1000 ns / τ-floor 0.999; Tier-B KS 0.08 / spread 10 bps; realism ceilings
KS 0.08 / ACF 0.12 / Hill 1.5 / depth-JS 0.10) were verified against the toolkit source.

My clean re-run (`--reseeds 5`, full panel) reproduced the headline **exactly**:
Tier-A fails 60/60 stochastic, Tier-B passes 59/60, KS∧ACF core 58/60, joint (Tier-A
fail ∧ tolerant pass on the same bytes) 59/60, full-4 admissible 35/60, and the
deterministic-latency control 5/5 on every gate with all four stylized facts exactly
0.000. Faithfulness (instrumented baseline == reference, exact) passed on all 13
scenarios, so every movement is attributable to the latency re-seed. Every per-scenario
row in the `ISSUE.md` table matched my output, including the single Tier-B miss
(`s001` perturb-1, KS = 0.08052 vs 0.08000).

The honest caveat is present and truthful, not scoped away: the full-4 35/60 rate is
reported in the same table as the core rates, the Hill/depth-JS attribution holds up
(s001 Hill is literally NaN; pareto Hill spread 0.71/1.95/2.05 and calm 0.78/1.67/4.94
reproduce exactly; 23 of 25 full-4 failures still pass both KS and ACF). The issue is
framed as good-faith benchmark feedback, proposes a well-posed fix (gate exactness only
on deterministic-latency scenarios / tolerate the RNG-projected order coordinate), and
explicitly bounds its claims (panel 13/65 not census, transfer conjectured, re-seed =
alternate stream not ±ε).

One provenance nit: the previous stage said the numbers "match `wellposed_results.json`."
That file exists only under `.bigtmp/track3_drawmap/out_w/` (the private harness area)
and has a richer schema than `reproduce.py` emits, so it is a private-harness artifact.
This does **not** taint the deliverables — neither `reproduce.py` nor `ISSUE.md`
references it, and the portable script independently regenerates every headline number —
but the "matches wellposed_results.json" phrasing should not be repeated to organizers as
if it were their-reproducible.

<details>
<summary>Issues (1)</summary>

1. **Private-JSON provenance phrasing** — the prior stage's "numbers match
   `wellposed_results.json`" refers to a private-harness file under
   `.bigtmp/track3_drawmap/out_w/`, not a `reproduce.py` product. Harmless (the script
   and issue body don't cite it and the numbers reproduce independently), but don't
   present that JSON to organizers as reproducible; the portable `reproduce.py --json-out`
   output is the citable artifact.

</details>

<details>
<summary>Details</summary>

### Self-contained + public-only (confirmed)

`reproduce.py` imports `qfbench2_track_simulation.semantics` and
`qfbench2_common.scoring.stylized_facts` from the repo checkout + toolkit, and inside the
container runs only `abides_fork` (public repo code). A grep for
`bigtmp|track3_drawmap|drafts|private|harness|\.env` returns only the docstring lines that
describe what it imports — no path dependency. Import smoke test in the scoring env
succeeded (`DEFAULT_TIMESTAMP_TOLERANCE_NS=1000`, `DEFAULT_KENDALL_TAU_FLOOR=0.999`).

Signature check against toolkit source:
- `check_tier_a(cand, ref, timestamp_tolerance_ns=1000, kendall_tau_floor=0.999)` — script
  calls the 2-arg form, defaults apply. Matches.
- `check_tier_b(cand, ref, ks_ceiling=0.08, spread_bps_tolerance=10.0)` — script passes
  `ks_ceiling=TIER_B_KS(0.08)`, `spread_bps_tolerance=TIER_B_SPREAD_BPS(10.0)`, equal to
  the toolkit defaults. Matches.
- `stylized_fact_report(cand_prices, ref_prices, …, cand_depth_hist=, ref_depth_hist=)` and
  `admissible(report, ceilings)` — script's call form matches; `intraday_l2` is omitted and
  `admissible` only checks ceiling keys that are present, so its absence is inert.

The in-container latency-only re-seed monkeypatches `abides_fork.config._draw_random_state`
via a temp file bind-mounted read-only (`--network none`), leaving the image and checkout
untouched. The mint-order reasoning (oracle → exchange → agents → latency → kernel;
latency index = n−2 when a latency config is present) is sound and is corroborated by the
faithfulness gate passing exactly on every scenario — the agent/oracle/kernel streams are
byte-identical to the reference, only the latency stream moves.

### Re-run reproduces the headline exactly (confirmed)

Full panel, `--reseeds 5` (60 stochastic + 5 control runs):

```
Tier-A (exact)       pass  0/60   -> fails 60/60          [ISSUE.md: 60/60 fail]  ✓
Tier-B (tolerant)    pass 59/60                            [ISSUE.md: 59/60]       ✓
realism KS&ACF core  pass 58/60                            [ISSUE.md: 58/60]       ✓
realism full-4       pass 35/60                            [ISSUE.md: 35/60]       ✓
Tier-A FAIL & (B|KS&ACF) PASS same trace: 59/60            [ISSUE.md: 59/60]       ✓
deterministic control: all gates 5/5, facts 0.000          [ISSUE.md: 5/5]         ✓
faithfulness: PASS on all 13 scenarios                     [ISSUE.md: all 13]      ✓
```

Every per-scenario row matched, e.g. `eq_uniform_tight` 0/5·5/5·4/5·5/5 KS 0.0305,
`eq_pareto_heavytail` 0/5·5/5·2/5·5/5, `s001` 0/5·4/5·0/5·4/5 KS 0.0704. The single Tier-B
miss traced to `s001` perturb-1 at KS = **0.08052** vs the 0.08000 ceiling — the exact
number and scenario `ISSUE.md` names. My run agrees with the issue body on every gate; no
disagreement to flag.

### Honest caveat is present and accurate (confirmed)

The full-4 35/60 rate is reported in the same headline table as the core rates, not
buried. Attribution verified from my JSON dump:
- `s001` Hill is NaN on all 5 reseeds (near-constant 604-row fill series) — matches the
  stated cause.
- `eq_pareto_heavytail` |α_cand−α_ref| min/med/max = 0.71 / 1.95 / 2.05; `ca_baseline_calm`
  = 0.78 / 1.67 / 4.94 — both match `ISSUE.md` to the quoted digits, confirming the Hill
  scatter is estimator noise against a fixed reference, inside a 1.5 ceiling.
- 25 full-4 failures, of which **23** still pass both KS and ACF — matches "23 of the 25."

The narrower claim (`theorem holds on the calibrated semantic core; full-4 not claimed
invariant`) is exactly what the data supports.

### No overclaim / private-env dependency (confirmed, one nit)

Framing is good-faith benchmark feedback under the rules that protect it; the proposed fix
(make `TIER_A_FAMILIES` conditional on whether the scenario declares a stochastic latency
model) is well-posed and offered as one option, not demanded. Limits are stated honestly:
panel is 13 of 65 (verified: 65 scenarios carry a `scenario_id`, one file is a
schema/index), transfer to other engines is explicitly conjectured, and the re-seed is
described as an alternate stream rather than an infinitesimal perturbation. The ABIDES pin
`f9cbe51` in the issue matches `baselines/Dockerfile` (`ARG ABIDES_COMMIT=f9cbe51342…`).

The only wrinkle is provenance, not content: the previous stage's "matches
`wellposed_results.json`" cites a file that lives under `.bigtmp/track3_drawmap/out_w/`
with a private-harness schema (`baseline_meta`, `mint_layout`, `family`, `lat_reseeds`).
The deliverables themselves are clean — no reference to it — and `reproduce.py`
regenerates every number independently, so the artifact is organizer-reproducible as
claimed. Just don't hand organizers that JSON as if it were their output; the
`reproduce.py --json-out` file is the citable one.

</details>

<details>
<summary>File map</summary>

- `drafts/track3_sim/issue/reproduce.py` — self-contained repro script; verified portable,
  public-only, and reproduces the headline.
- `drafts/track3_sim/issue/ISSUE.md` — issue body; numbers, caveat, framing, and limits all
  verified against the re-run.
- (in-env, not part of the deliverable) `.bigtmp/track3` public checkout,
  `track3-abides-baseline:latest` image, `regression_suite/reference_traces/` (65 scenarios)
  — used to drive the re-run.
- (private, not referenced by the deliverable) `.bigtmp/track3_drawmap/out_w/wellposed_results.json`
  — richer-schema harness output; provenance nit only.

Re-run command: `cd .bigtmp/track3 && <scoring-env>/python drafts/track3_sim/issue/reproduce.py --reseeds 5`

</details>
