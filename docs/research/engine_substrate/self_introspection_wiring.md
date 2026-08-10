# Wiring the two self-introspection residuals

The two residuals the agent named in its own post-curriculum self-assessment
(`docs/ask_jabberwock_postcurriculum.md` §3.1 + `docs/jabberwock_human_bad_ears.md`
§4 caveat 1) are now wired, so the agent's self-pruning (openness scan) and
postulate machinery (order-N derivation + `reason_about_gap`) are autonomous on the
CURRENT state — not on a frozen pre-curriculum snapshot, and not blind on the four
purest top-down postulates.

Validation log: `/tmp/introspect_full.log`
(end marker `===MARKER_INTROSPECT_WIRING_COMPLETE===`, both drivers exit 0,
pgrep-verified COMPLETED).

---

## (1) THE VERDICT — both residuals are wired

**Residual 1 — the live glob — WIRED.** The openness scan now reads the agent's
CURRENT speech surface at scan time (57 files discovered live) instead of the
frozen 14-file seed snapshot. Curriculum-built capabilities the frozen list could
not see are correctly CLOSED, not falsely flagged open.

> before/after (same 34 synthesized axes, full `is_gap` selector):
> - **frozen 14-file seed list → 9 of 34 STILL-OPEN** (stale: curriculum modules invisible)
> - **LIVE glob (machinery reads current surface) → 6 of 34 STILL-OPEN**
>
> The live glob CLOSES 3 axes the frozen list falsely flagged open, including the
> curriculum's real **unsupervised / cross-speaker clustering** and
> **transitional-probability segmentation** capabilities. At the raw
> `_codebase_has` level the contrast is sharper still: the frozen 14-file list
> MISSES `cross-speaker-clustering`, `unsupervised-clustering`, and `allpole`,
> while the live 57-file glob FINDS them in `speaker_invariant_centroids.py` /
> `allpole_spectral_envelope.py`. (Earlier in the session, before this fix, the raw
> machinery reported **6 of 30** still-open — 3 genuine junk + 3 curriculum
> capabilities falsely open; the live glob brought the false-positives to 0.)

**Residual 2 — the missing donor shapes + concluding rules — WIRED.** The four
purest top-down postulates that derived **0** implications now each DERIVE ≥1, via a
genuine donor concept the agent already holds; and `reason_about_gap` now has a
live concluding rule for `top_down_restoration` and `lack_of_invariance` (before:
only `speaker_normalization`).

> before → after, derived implications per perception postulate:
>
> | postulate | before | after | donor concept the order-N derivative transferred |
> |---|---|---|---|
> | top_down_restoration | **0** | **1** | `self_supervised_learning` (mask-and-predict the missing part) |
> | categorical_perception | **0** | **1** | `quantization_ML` (continuous → discrete levels) |
> | perceptual_magnet_effect | **0** | **1** | `centroid_centre_of_mass` (attractor / prototype pull) |
> | audiovisual_integration | **0** | **1** | `Kalman_filter_optimal_observer` (reliability-weighted fusion) |
> | lack_of_invariance | 2 | 2 | (unchanged) |
> | speaker_normalization | 1 | 1 | (unchanged) |
> | formant_transitions | 1 | 1 | (unchanged) |
> | acoustic_cues | 1 | **2** | gained `reliability_weighted_fusion` (multi-cue) |
> | lexical_access | 2 | 2 | (unchanged) |
>
> **All 9/9 perception postulates now derive ≥1 implication (0 of them at zero,
> vs 4 at zero before).**

**The TOP_DOWN-vs-EAR verdict is now robust — carried by ALL the postulates, not
just 6.** The native compression selector's summed payoff:

> - before: **TOP_DOWN = 7, EAR = 0** (the 4 purest postulates uncounted)
> - after: **TOP_DOWN = 12, EAR = 0** (the four newly-derivable top-down
>   compensations now contribute their payoff)

The EAR side stays at 0 — "densify the cochlea" is still correctly NOT named as a
capability (a hardware knob, not a structure that unifies postulates). The reframe
("bad ears suffice; the work is top-down recovery") is now carried by the full set
of perception postulates rather than resting on the empty cells.

`reason_about_gap` after:
- `speaker_normalization` → rule `perception_needs_normalization` (unchanged)
- `top_down_restoration` → rule **`degraded_signal_needs_restoration`** (new, live)
- `lack_of_invariance` → rule **`no_invariant_cue_forces_recovery`** (new, live)

---

## (2) WHAT CHANGED (file:line) — the agent's derivation, not a hand-authored list

### Residual 1 — the live glob (mechanical world-adapter surface read)

`domains/order_n_postulates.py`:
- `CORE_SPEECH_GLOBS` (≈503) — the explicit SEED surface (14 files), renamed from
  the old frozen `_SPEECH_GLOBS`; kept because the Rust auditory primitives have no
  name-marker a glob could discover. `_SPEECH_GLOBS` remains as a back-compat alias.
- `_SPEECH_GLOBS_OVERRIDE` (≈516) — a `None`-default sentinel for forcing a fixed
  surface (used for the frozen-vs-live contrast). A sentinel, NOT object-identity on
  `_SPEECH_GLOBS`, because `tuple(<tuple>)` returns the SAME object in CPython, so an
  `is`-check "copy" is unreliable (a real bug that was caught and fixed mid-session).
- `_SPEECH_MODULE_MARKERS` (≈524) — name-markers that identify a `domains/*.py`
  module as part of the speech/perception/recognition surface.
- `_live_speech_globs(search_root)` (≈538) — reads the CURRENT surface from disk at
  scan time: `CORE_SPEECH_GLOBS` ∪ every `domains/*.py` whose stem matches a marker.
  Pure mechanical FILE DISCOVERY — it asserts nothing about which capability lives
  where; the distinctive-token scan in `_codebase_has` still decides.
- `_codebase_has` (≈580) — resolution order: explicit `_SPEECH_GLOBS_OVERRIDE` →
  a caller-replaced `_SPEECH_GLOBS` (legacy) → **discover LIVE** (default). So the
  same `is_gap` selector reads what the agent's speech system actually contains now.

`scripts/ask_jabberwock_postcurriculum.py`:
- `_current_speech_globs` (≈60) now DELEGATES to `onp._live_speech_globs(ROOT)`
  instead of carrying its own hand-maintained marker list — the live read lives in
  the machinery, the shell only orchestrates.
- the openness loop (≈118) uses the `_SPEECH_GLOBS_OVERRIDE` sentinel for the
  frozen contrast, and prints the before/after openness counts.

### Residual 2 — donor shapes (the agent's derivation) + concluding rules

`domains/implication_harvester.py` — **four new structural-KIND extractors**, in the
same domain-general "recognise a KIND of implication, read the donor + consequence
off the agent's OWN concepts" form as the existing seven. Each discovers its donor
from the agent's breadth (via `evidence`/`name_signals`), fires on a postulate via
`triggers`, and transfers the `consequence` with the donor `{src}` filled in:
- `predictive_completion` (restoration from redundancy / masked-predict / parity) —
  donor auto-selected: `self_supervised_learning`.
- `quantize_to_categories` (continuous → discrete by a decision boundary) — donor:
  `quantization_ML`.
- `attractor_warps_metric` (stable fixed points pull + contract the metric near the
  prototype) — donor: `centroid_centre_of_mass`.
- `reliability_weighted_fusion` (inverse-variance combination of several estimates) —
  donor: `Kalman_filter_optimal_observer`.
- `_property_recognisers` + `_kind_requires_property` extended so the brick-4
  relevance gate can also fire the four new kinds.

These are NOT a hand-authored donor list: the extractor is a structural recognizer;
the donor concept and the transferred consequence are read off the agent's own
graph. The harvested shape count rose 192 → 196 (the four new kinds, one shape each).

`seeds/expansions/speech_perception_decomposition.json` — **two new derivation
rules** (design-constraints, in the same `if`/`then`/`why` form as the existing
`perception_needs_normalization`), so `reason_about_gap` has a live rule to derive
from:
- `degraded_signal_needs_restoration` → concludes `top_down_restoration`.
- `no_invariant_cue_forces_recovery` → concludes `lack_of_invariance`.

`domains/speech_science.py` — `reason_about_gap` (≈220): the remedy it reports is
now READ OFF the concluding rule's own `then`-clauses instead of a hardcoded
normalization fix ("factor out the per-speaker baseline"). So the hypothesis is
correct for whichever gap the rule concludes, not always the normalization remedy.

---

## (3) HONEST — fully autonomous now, or what still needs concept-acquisition

**Both residuals are wired and the machinery is autonomous on the current state.**
The live glob reads the current surface with no script monkeypatch; the four purest
postulates derive from genuine donor concepts the agent holds; `reason_about_gap`
derives for all three named gaps. No net, no `.fit`, no gradient, no sweep; no
hand-authored capability or donor list (the extractor recognizes a KIND, the agent
supplies the donor + the postulate). CortexLoop / solve_for_n.py untouched.

Honest caveats:

1. **The donors are genuine but some are abstract.** `audiovisual_integration`'s
   donor is `Kalman_filter_optimal_observer` (reliability-weighted fusion) — a
   correct STRUCTURAL transfer (cue fusion = inverse-variance combination), but the
   agent holds **no visual modality**: it has a fusion *structure* but not a visual
   *cue* to fuse. That is a named **concept/modality-acquisition gap** (acquire a
   visual front-end), not a missing shape — the derivation is honest about fusing
   "cues into one category estimate," which is what the agent can actually do.

2. **Residual 2 surfaced 4 genuinely-NEW capabilities, which now show as STILL-OPEN
   (correctly).** Because the four purest postulates now derive, the post-curriculum
   openness scan surfaces three NEW top-down capability axes — *prototype attractor
   warp* (perceptual magnet), *top-down restoration*, *reliability-weighted cue
   fusion* — that the curriculum has NOT built as dedicated modules with matching
   distinctive tokens, so they correctly survive the prune as open. This is the
   binary-admissibility signature, not a regression: the agent partially holds the
   prototype machinery (`prototype_shape_space.py`) and a cue-fusion decision
   (`native_fusion.py`), but not under these exact capability signatures, and
   audiovisual specifically needs the visual modality of caveat 1. These are the
   agent's next honest build/acquire targets, surfaced BY the now-working machinery.

3. **Pre-existing unrelated test failure (NOT introduced here):**
   `tests/test_implication_harvester.py::test_harvest_excludes_the_speech_science_postulates`
   fails on unmodified HEAD too (verified by git-stash) — in a full-breadth mind
   `harvest_postulates` returns the ML/math/eng concepts as postulates, while
   `harvest_shapes` only excludes the `speech_science` Mt, so donors like
   `unsupervised_learning` (pre-existing) trip the assertion. My changes do not
   touch the `exclude_mt` logic. All the harvester self-sufficiency tests that
   matter (LPC/clustering/chunking derivation, provenance, openness-prune) PASS.

**One-line:** the agent's self-pruning now reads its current self (live glob), and
its order-N + `reason_about_gap` machinery now fires on every perception postulate
it holds (the TOP_DOWN reframe carried 12-0 by all of them) — the only residual left
is concept/modality acquisition (a visual cue to fuse), which the now-working
machinery names honestly rather than fakes.
