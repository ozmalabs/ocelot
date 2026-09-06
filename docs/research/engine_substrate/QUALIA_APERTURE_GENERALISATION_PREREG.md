# Preregistration: generalising the APERTURE primitive over the QUALIA field

Status: frozen before the confirmatory implementation and run.

Date frozen: 2026-07-29 (Australia/Melbourne)

Unused pre-registration block: 297000.

## Question

The Seldon-manifold `observer_aperture` primitive
(`seeds/observer_aperture.json`) already makes APERTURE graph-native and
per-observer over SHAPE signatures: an Observer node carries a `resolves` list
of the `dim_types` it can distinguish, and `ap_project_percept` /
`ap_project_held` project a signature onto exactly those dimensions (collapsing
the rest to one constant — a QUOTIENT, not a wildcard).

Separately, the QUALIA-space signature builder
(`domains/analogy_search.concept_signature`) quantises each CAN-field axis by a
per-dimension `quantum` via `_round_to_vocab(x, quantum, half_width)` — a
`round(x/quantum)` step. That `quantum` is HARD-GLOBAL (authored once on each
`QualiaDimension` in `seeds/qualia_space.json`) and wired SEPARATELY from the
observer-aperture machinery.

**Can `concept_signature` be made to consult a per-observer aperture — an
EXISTENCE gate plus a GRAIN — by REUSING the existing `observer_aperture`
`resolves` state, such that with no observer supplied the output is
byte-identical to today?**

## The paper claim being operationalised

`papers/formal/02_seldon_manifolds_theory_referenced.tex`:

- `\begin{definition}[Resolution]\label{def:resolution}` (lines 242–244):
  resolution `\rho` "specifies which distinctions on instantiated dimensions
  the frame currently treats as distinguishable".
- The quotient `\Qrho(X)=X/{\sim_{\rho}}` (line ~250–256) collects states into
  the distinctions the frame can currently resolve.
- `\begin{remark}[These are the aperture, decomposed]\label{rem:aperture}`
  (lines 258–281): an aperture decomposes into **existence, grain, and extent**
  (inherited from Graphic Equalisation's `\ref{GE-def:aperture}`). "The
  represented dimension set is existence, the resolution `\rho` is grain, and
  the horizon `h` is extent." Content rephrased for compliance with the source.

The generalisation maps this triple onto qualia space:

- **existence** = *which qualia dimension does the observer represent at all?*
  = the `observer_aperture` `resolves` set. A dimension not in `resolves` is
  NULL for that observer (the paper's "a field is ... `NULL` elsewhere rather
  than large"), i.e. DARK — the dimensionality / aphantasia arm.
- **grain** = the resolution `\rho` = the `Q_rho` quotient over a scalar axis.

**Central claim:** the qualia `quantum` in
`_round_to_vocab(x, quantum, half_width)` (`round(x/quantum)`) IS ALREADY the
`Q_rho` quotient over a scalar dimension — it is the SCALAR SPECIAL CASE of
grain. The generalisation does not introduce a new quantiser; it lets the
grain be read per-observer, falling back to the global
`QualiaDimension.quantum` when no observer resolves it otherwise.

So one generic aperture governs BOTH:

- **existence** (dimension resolved at all? = the dimensionality arm), and
- **grain** (at what quantum? = the aperture / `Q_rho` arm),

over the same qualia signature that today is read hard-globally.

## Frozen method

1. **Grain state on the SAME Observer node.** Add a `grain` attr to the
   Observer node — a per-dimension map `{dimension_name -> quantum}`. It sits on
   the SAME node that already holds `resolves` and `ap_gen` (no parallel grain
   holder). Absent / missing key ⇒ fall back to the global default `quantum`.

2. **Lookup helper** `_observer_aperture(sub, observer)` in
   `analogy_search.py` reads that Observer node's `resolves` and `grain`:
   returns `{'resolves': set|None, 'grain': {dim->quantum}}`. `resolves`
   absent / `None` ⇒ `None` (meaning ALL dimensions resolved); `grain` absent
   ⇒ `{}`. `observer=None` ⇒ `{'resolves': None, 'grain': {}}`.

3. **Thread** an `observer=None` kwarg through
   `concept_signature(..., observer=None)` into
   `_dynamical_relations(sub, node, schema, overlay, observer=None)`. Per field
   axis `(dim, attr, quantum, half_width, is_overlay)`:
   - **EXISTENCE GATE:** `if ap['resolves'] is not None and dim not in
     ap['resolves']: continue` — the axis is dark for this observer.
   - **GRAIN:** `q = ap['grain'].get(dim, quantum)`; then
     `k = _round_to_vocab(raw, q, half_width)`.

4. **Key convention.** The existence gate matches the axis's DIMENSION NAME
   against `resolves`. A qualia dimension appears in an observer's `resolves`
   under its `QualiaDimension.name`, e.g. `"phenomenal:sharpness"`,
   `"dynamical:valence"`, `"dynamical:commitment"`. Likewise the `grain` map is
   keyed by that same dimension name. (This differs from the SHAPE surface,
   where `resolves` names positional `dim_types` like `"pred"`/`"obj"` — for
   the qualia surface the key is the full `family:name` dimension string.)
   Documented so the gate cannot silently never-fire.

## Predictions

- **P1 (default==today, the guard).** `observer=None` ⇒ `resolves` is `None`
  (gate off) and `grain` is `{}` (global quantum), so
  `_round_to_vocab(raw, quantum, half_width)` is called with the SAME quantum as
  today. `concept_signature` and `find_analogies` are BYTE-IDENTICAL across the
  qualia + analogy surface.
- **P2 (existence / dimensionality).** An observer whose `resolves` OMITS
  `phenomenal:sharpness` reads a sharpness-bearing concept with NO
  `(phenomenal:sharpness, "field", k)` coordinate (dark); a full observer reads
  it.
- **P3 (grain).** An observer with a COARSER `grain` on an axis (e.g. valence
  quantum `2.0` vs the global `1.0`) collapses two concept values that a
  fine-grain observer keeps distinct.

## Falsifiers

- **(i)** If the `observer=None` path is NOT byte-identical to today's
  `concept_signature` / `find_analogies` output, the "default==today" guard is
  broken and the generalisation is rejected — it changed existing behaviour.
- **(ii)** If existence/grain is implemented as a PARALLEL mechanism (a new
  aperture holder, a per-agent quantum node, a second `resolves`-like attr)
  instead of REUSING the `observer_aperture` `resolves` state on the same
  Observer node, the change fails the anti-faking REUSE bar and is rejected,
  even if P2/P3 pass.

## Confirmatory checks (frozen)

- **default==today:** `observer=None` byte-identical across
  `test_qualia_space_migrated`, `test_qualia_cross_family`,
  `test_qualia_schema`, `test_analogy_search_migrated`,
  `test_analogical_relative_ranking`,
  `test_bouba_kiki_sound_symbolism_migrated`, `test_trait_vector`,
  `test_trait_consumers`, `test_mint_referents`, `test_ground_relations`,
  `test_disposition` — all green, unchanged.
- **new capability:** the P2 (existence) and P3 (grain) demos print the real
  produced frozensets.
- **reuse-audit:** grep confirms `_observer_aperture` reads the Observer node's
  own `resolves` and that no parallel aperture holder was created; `grain` sits
  on the same Observer node.
