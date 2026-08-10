# ADVANCED LIGHTING — RUNG L1: REAL-VALUED ILLUMINANT GAINS — PRE-REGISTRATION

*Authored and committed **BEFORE** the run (§3). Extends `VISION_LIGHTING_RESULTS.md`
(T3, the integer-ratio diagonal illuminant class) with the mechanism
`VISION_CONTINUOUS_POSE_RESULTS.md` (T1) established for real-angle rotation.
Base `main` HEAD **7cbf1962** (`git merge-base --is-ancestor 7cbf1962 HEAD` verified).
Branch `gamma-substrate/vision-lighting-l1`.*

---

## 0. THE RUNG, IN ONE SENTENCE

T3 crossed lighting-invariance for the **EXACT-RENDERING (integer-ratio)** diagonal
illuminant class and **REFUSED real-valued gains** (measured **0/12** at gains
1.5 / 2.5 / 3.3 / 7.5 against **12/12** at 2.0 / 3.0 / 4.0), deliberately adding **no
tolerance** to widen it (§5) and **NAMING** the resolution-derived identifiability
bound rather than building it. **L1 builds that bound**, by T1's mechanism transposed
from rotation to gain: the gain is a **continuous parameter in the CROSS-FRAME map**,
the candidate is **RENDERED at that continuous gain onto the stepped integer lattice**,
and recognition is decided by a **CONTINUOUS VERDICT** over a proposal from the
discrete codebook — *bins propose, continuous decides* — with the admission threshold
**FALLING OUT of observational resolution**, never tuned.

---

## 1. AUDIT (§12.4) — VERDICT: **COMPOSE. NO NEW RUST.**

### 1.1 What T3 already gives L1

| T3 asset | file:line | what L1 does with it |
|---|---|---|
| `li_frame_stats` — per-channel `MaxOver` anchor `a_ch` + `Sum` `s_ch`, hub-scoped via `Neighbours(frame,"has_surface")` | `tools/build_vision_lighting.py:113–150` | **pattern reused**, not called. L1 computes its OWN stats into its OWN attr namespace (`l1_a*`, `l1_s*`, `l1_m*`, `l1_n`) so L1 is self-contained and T3's attrs are never written by L1. |
| `li_inclass` — EXACT integer cross-multiplication `a_ch·ref.s_ch == s_ch·ref.a_ch` on all 3 channels; mints `Illuminant{g*_num,g*_den}` | `:171–210`, predicate `:153–165` | **THIS is the rule that refuses a real gain** (a rounded real gain breaks the exact order-statistic equality ⇒ `illum_inclass` stays 0 ⇒ `li_recognize` cannot fire). L1 adds a **continuous-envelope** sibling `l1_inclass`; T3's rule is **untouched**. |
| `li_mint` — MDL mint of `SurfaceIdentity{pL,pM,pS, paL,paM,paS, sid_key}` at `m_min=2` (falls out of `d=3`), in the **reference** frame | `:232–276` | **REUSED AS-IS.** The mint happens in the reference frame at **unit gain**, so it is entirely unaffected by the test frame's real gain. L1 **depends on** `vision_lighting` being loaded with `lighting=1` for the codebook to exist. Declared. |
| `li_recognize` — the exact invariant `c_ch·pa_ch == p_ch·a_ch` | `:295–335`, predicate `:279–289` | **the DISCRETE arm of L1's crux measurement.** Read from the SAME graph as L1's continuous arm, in the same run. Untouched. |
| `li_raw_recognize` — the no-discounting RAW baseline | `:341–367` | reported unchanged. |
| the exact `(numer,denom)` gain pair | `:200–206` | L1's contrast: T3 holds the gain as an **exact integer ratio**; L1 holds it as the **REAL** number `Div(a_ch, pa_ch)` — legitimate precisely because it is a **cross-frame** quantity (the frame/continuum invariant). |
| adapter `add_frame` / `add_surface` (integer render `int(r)·int(g)`) | `domains/lighting_world.py:29–72` | needs a **real-gain render** `round(r·g)`. T3's own probe already does this inline (`scripts/lighting_measure.py:292–320`); L1 lifts it into the adapter as `add_frame(..., gain=<float tuple>)` — **world physics, mechanical, no decision**. |

### 1.2 The continuous machinery for the verdict — ALL Terms already exist

T1 used held `Rotate` (the cross-frame render) + `PointSetDist` (the held continuous
verdict) + `MinOver`/`Argmin`/`Lte` (bins-propose-continuous-decides). The **gain**
analogue needs a scalar render and a scalar distance, and every Term is held:

| Term | `runners/dsl/src/jsonio.rs` | role in L1 |
|---|---|---|
| `Div {a,b}` | `:1275` | **the continuous gain** `ĝ_ch = a_ch / pa_ch` — a REAL number in the cross-frame map |
| `Times {items}` | `:1274` | **the render** `p_ch · ĝ_ch` (⚠ `items` LIST — see §6) |
| `Minus {a,b}` | `:1270` | observed − rendered |
| `Abs {arg}` | `:1267` | the per-channel residual |
| `Max {items}` | `:1403` | **the verdict** = L∞ over the 3 channels (correct metric: each channel rounds INDEPENDENTLY) |
| `Plus {items}` | `:1269` | the in-class envelope |
| `Lte {a,b}` / `Gte {a,b}` | `:1094` / `:1102` | the falls-out admission bound |
| `MinOver {source,var_name,value,default}` | `:1174` | the best residual over the codebook (absence-tolerant via `default`) |
| `Argmin {source,var_name,value,default}` | `:1194` | names the winner — **exactly T1's `cp_recognize` effect** (`seeds/continuous_pose.json`) |
| `MaxOver` / `MinOver` / `Sum` / `Count` / `Neighbours` / `Filter` / `Not` / `Exists` | T3's set | frame statistics, hub-scoped |

**VERDICT: L1 COMPOSES with ZERO new Rust.** One new seed (`vision_lighting_l1`),
flag-gated on its own `LightingL1Params.lighting_l1`, **OFF by default** (§9).
There is **no DSL gap**, so no Rust is justified and none is written; the engine hash
is therefore unchanged (shared build, Rust source byte-identical, §10.1 rule 4).

**Can a real gain be pinned to resolution without a tuned tolerance?** **YES** — §2
derives it. This is *not* the honest negative the task allowed for; the bound falls out
of the lattice step and the anchor's defining property, with no free parameter.

---

## 2. THE BOUND — IT FALLS OUT (§13). NOTHING IS TUNED.

**Protocol** (T3's own, `scripts/lighting_measure.py:47`): the **reference frame is
rendered at unit gain**, so the prototype and reference anchor are exact integers. The
test frame is rendered at a real per-channel gain `g_ch` through `round()` — the
observation is stepped **by construction**, which is what grounding IS.

Write, per channel (subscript dropped):

- `p = r` — the prototype (ref at unit gain, exact)
- `pa = M := max_i r_i` — the reference anchor (exact; `round` is monotone so the max
  commutes with rendering)
- `c = round(r·g) = r·g + ε_c`, **`|ε_c| ≤ ½`**
- `a = round(M·g) = M·g + ε_a`, **`|ε_a| ≤ ½`**

### 2.1 The RECOGNITION bound = **1.0 = ONE LATTICE STEP**

The continuous gain estimate is the cross-frame ratio `ĝ = a / pa` (a **REAL** number —
correct, it lives in the map, not in a frame). The candidate is **rendered** at it:

```
residual = | c  −  p · ĝ |
         = | (r·g + ε_c)  −  r·(M·g + ε_a)/M |
         = | ε_c  −  ε_a · (r/M) |
         ≤  ½  +  ½ · (r/M)
         ≤  ½  +  ½                 because r ≤ M = the anchor, BY DEFINITION
         =  1
```

**The bound is ONE lattice step, per channel — the sum of exactly TWO half-step
rounding displacements:** the observation's own rounding (`½`), and the anchor
estimate's rounding **attenuated by `r/a ≤ 1`, which holds because the anchor IS the
frame's maximum**. Nothing is fitted. This is the exact analogue of T1's `√2/2` (there:
ONE rounding, 2-D Euclidean half-diagonal; here: TWO roundings, per-channel L∞).

The verdict aggregates the three channels by **`Max`** (L∞), because each channel is
rounded independently — so the per-channel bound is also the vector bound. Admission is
`Lte(verdict, 1.0)`.

### 2.2 The IN-CLASS envelope — also falls out, and is DECLARED LOOSE

T3's in-class test is the exact order-statistic identity `a·ref_s == s·ref_a`. Under
rounding, with `n` surfaces, `S := Σ_i r_i`, `E := Σ_i ε_i` so `|E| ≤ n/2`:

```
| a·ref_s − s·ref_a | = | (M·g+ε_a)·S − (S·g+E)·M | = | ε_a·S − E·M |
                      ≤ ½·S + (n/2)·M  =  ½·( ref_s + n·ref_a )
```

**`n = Count(frame's surfaces)`, read from the data.** Every term is one half-step
rounding scaled by its own cross-multiplier. **Not tuned — but honestly LOOSE**, because
the sum accumulates `n` roundings. So L1 adds a **second, tighter necessary clause on
the MIN order statistic** (which accumulates only TWO roundings, exactly like §2.1):

```
| a·ref_m − m·ref_a | ≤ ½·( ref_m + ref_a )      m := MinOver(frame's surfaces, c_ch)
```

**Both clauses must hold, on all three channels.** This is declared **in advance** and
on a principled ground (fewer accumulated roundings ⇒ a tighter falls-out envelope) —
it is a design choice, not §5 metric surgery, and it is pre-registered before any L1
number is seen.

### 2.3 IDENTIFIABILITY — what the bound CANNOT buy

The bound is pinned to observational **resolution** and to nothing else. It therefore
**must** fail when the resolution is inadequate: at a **dimming** gain `g < 1`, distinct
materials render onto the **same or adjacent lattice points** (`round(r·0.2)` collapses
`r=10` and `r=12` onto `2`), and no verdict can separate what the steps did not record.
**We predict a low-gain floor and we do not know where it is** — the curve is the
measurement (§4 arm D). *"You can apply π, but any given circle is stepped."*

---

## 3. WHAT IS BUILT

**ONE new seed `seeds/vision_lighting_l1.json`** (builder
`tools/build_vision_lighting_l1.py`), depending on `vision_lighting`, gated on
`LightingL1Params.lighting_l1`, **default 0.0 = OFF** (§9). Flag read
**absence-tolerantly** — `Gt(MaxOver(NodesOfType("LightingL1Params"), p, p.lighting_l1,
default 0), 0.5)` — **never `PickUnique`**, which returns `None` on an absent params
node and silently changes behaviour elsewhere.

Four rules, all writing to an **L1-only attribute namespace** so **no T3 attribute is
ever written by L1** and both arms are readable from one graph:

1. **`l1_frame_stats`** — the frame's own per-channel `MaxOver` anchor `l1_a*`, `Sum`
   `l1_s*`, `MinOver` `l1_m*`, and `Count` `l1_n`, hub-scoped through
   `Neighbours(frame,"has_surface")` (§12.1 — never a global `NodesOfType` grab).
   Idempotent under an `l1_stats_done` guard.
2. **`l1_inclass`** — the §2.2 **continuous envelope** on BOTH the sum and the min
   statistics, all three channels. Holds ⇒ mint `IlluminantL1` carrying the **REAL**
   per-channel gain `Div(l1_a, ref.l1_a)` and set `l1_inclass=1`. Fails ⇒ nothing minted,
   the frame is **REFUSED**.
3. **`l1_recognize`** — **THE CONTINUOUS VERDICT.** Guard:
   `Lte( MinOver(Neighbours(ref,"has_identity"), c, verdict(c), default 1e9), 1.0 )`;
   effect: `l1_id = Attr(Argmin(same source, same value), "sid_key")`, `l1_recognized=1`
   — T1's `cp_recognize` shape exactly. The codebook **proposes** (`SurfaceIdentity`
   nodes minted by T3's integer `li_mint`); the **continuous** rendered residual
   **decides**. Hub-scoped to the reference frame's own `has_identity` population.
4. **`l1_refuse`** — marks `l1_status="l1_refused"` when in-class but no candidate is
   within the bound, so a refusal is a positive datum and the arm can be shown ALIVE
   rather than merely silent (§1.1 clause 4).

**Adapter change** (`domains/lighting_world.py`): `add_surface` renders
`round(r · g)` and accepts float gains — mechanical world physics, the agent never sees
`r` or `g`, only the product. Source-audited by a no-Python-decision test.

**T3 is NOT modified.** `seeds/vision_lighting.json` and
`tools/build_vision_lighting.py` are byte-identical; `tests/test_lighting_migrated.py`
must still be **27/27**.

---

## 4. ARMS, PREDICTIONS, AND GATES (stated BEFORE the run)

Materials: T3's six (`a`–`f`), two patches each ⇒ 12 surfaces; plus T3's single-patch
`NOVEL`. Reference frame at unit gain.

| arm | statistic | PREDICTION | gated |
|---|---|---|---|
| **A REAL-GAIN INVARIANCE** *(headline)* | correct id / 12, at the four gains T3 REFUSED: **1.5, 2.5, 3.3, 7.5**, + the per-channel real gain **(1.5, 2.5, 3.3)** | **60/60** — every surface recognized as its own identity | ✅ ≥ 58/60 |
| **B DISCRIMINATION exact-0** *(§1.1 CRUX)* | cross-material false identities over all arm-A conditions | **0** | ✅ == 0 |
| **C CONTINUOUS-DECIDES** *(the rung's reason to exist)* | on the SAME graph: T3 `lit_recognized` vs L1 `l1_recognized`, at real gains | discrete **0/60**, continuous **60/60** | ✅ discrete == 0 **and** continuous ≥ 58 |
| **C-alive** *(§1.1 clause 4 — the DEAD-ARM FLOOR)* | T3's discrete arm at INTEGER gains 2/3/4 | **36/36** — the discrete arm is ALIVE, it refuses real gains because they moved the values, not because it is inert | ✅ == 36 |
| **D IDENTIFIABILITY / RESOLUTION** | correct id / 12 across the gain sweep **0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.5, 3.3, 7.5, 20.0** | clean at `g ≥ 1`; **DEGRADES at low `g`** as the lattice loses resolution. The break point is **UNKNOWN and is the measurement.** | ✅ `g ≥ 1` all 12/12; low-`g` **REPORTED**, and **discrimination must stay 0 everywhere** (a resolution failure must be a REFUSAL, never a false identity) |
| **E NOISE floor** (n=100, seeds **45220–45319**) | random cone fields minting or claiming anything | **0/100** | ✅ == 0 |
| **F OUT-OF-CLASS floor** (n=20 spatially-varying, seeds **45320–45339**) | false identities | **0** | ✅ == 0 |
| **F-inclass** | whether the looser envelope ADMITS out-of-class frames | **RISKED — the envelope is looser than T3's exact test and MAY admit.** If it admits, the refusal must come from the recognition bound instead, and F must still be 0. | ✅ reported; **F gates** |
| **G NOVEL-material floor** | the single-patch material (never minted) force-matched | **0** | ✅ == 0 |
| **X OFF-DAY** (§9) | `lighting_l1=0` | L1 fully inert; T3 gate **27/27** unchanged; vision bench **200/0** with `data/`; sd orbit law **{2:1,3:2,4:2,6:2,12:4}** unmoved; sibling gates green | ✅ |

**Seed ledger:** the block **45220–45999** was CLEAN
(`VISION_PROTOCOL.md:973` — *"45100–45199 + 45220–45999 CLEAN"*). L1 consumes
**45220–45319** (noise floor) and **45320–45339** (out-of-class). **45100–45199 and
45340–45999 remain CLEAN.**

---

## 5. §13.1 — ENTAILED vs RISKED, DECLARED IN ADVANCE

**The test §13.1 demands: *could this model have produced the opposite result?***
**YES, and in a specific, nameable way.** The bound `1.0` is a whole lattice step, while
the six materials' cone triples differ by as little as **2** in some channel (e.g.
`a=(10,20,30)` vs `e=(21,37,14)` differ by 11 in L but material pairs come within 2 in
individual channels). At a **dimming** gain the rendered separation shrinks below the
bound and the argmin **will** merge. **A universal container is a live outcome of this
build, not a hypothetical** — which is exactly the T3 failure mode, and why B and D's
discrimination clause are the real gates.

**ENTAILED by construction — reported as CONSISTENCY, NOT banked as discovery:**

- **Arm A's ADMISSION half.** Given the §2.1 algebra, a correct implementation *must*
  admit the true identity (its residual is `≤ 1` by derivation). Reported because a
  **broken** build fails it — as T3's positive control proved — not because it is a
  result.
- **Arm C's DIRECTION.** T3 has already measured that exact cross-multiplication refuses
  a rounded real gain. Only the **magnitude** (a total 0/60 → 60/60 flip) is informative.

**RISKED — this is the result:**

- **Arm A's CORRECTNESS half.** That the admitted candidate is the *right* one is a
  property of the argmin over a codebook whose members sit within a lattice step of one
  another at low gain. Nothing entails it.
- **Arm B (exact-0)** — the universal-container crux. A blind normaliser passes A and
  fails B.
- **Arm D's break point** — genuinely unknown; the curve is the finding.
- **Arms E, F, G** — the refusals. A nearest-assignment mechanism force-assigns and
  fails all three. F is doubly risked because L1's envelope is *deliberately looser*
  than the exact test that delivered T3's 0/20.

**§13.2 load-bearing:** L1 must be shown to *do* something — `D = |on − off|` on the
recognition count at a real gain must be **12**, and the T3 arm on the same graph must
be **0**. If L1 changed nothing, it would not be a mechanism.

---

## 6. THE KNOWN TRAP, AND THE POSITIVE CONTROL (§12.3)

**`Times` takes an `items` LIST** (`runners/dsl/src/jsonio.rs:1274`). Written `a`/`b` it
parses to an **EMPTY PRODUCT = 1**, which turned T3's invariant into `Eq(1,1)` — a
**universal container with a flawless invariance score**. `Max` and `Plus` take `items`
too (`:1403`, `:1269`); `Div`, `Minus`, `Lte`, `Gte` take `a`/`b`; `Abs` takes `arg`.
Every constructor in L1's builder carries the list/scalar form in its own docstring.

**The gate is POSITIVE-CONTROLLED before the result is believed.** We inject the
empty-product defect into L1's render and verify the gate goes **RED**, then revert and
verify it returns to green. *A gate you have only ever seen pass is not a gate you have
tested.* The count of tests that go red on the injected defect is reported.

---

## 7. BOUNDS — WHAT L1 DOES NOT DO (§8)

L1 widens the **GLOBAL diagonal illuminant** class from integer ratios to **real
values**. It does **NOT** attempt, and these remain the **NAMED FRONTIER**:

- **L2 — spatially-varying illuminant / Retinex.** Refused, not solved.
- **L3 — global illuminant inference** (recovering the light without a reference frame).
- **L4 — shadow-vs-reflectance edge attribution.**
- **Multi-illuminant scenes** — unsolved even computationally.
- The **abstract cone-triple grain**: integer `(cL,cM,cS)` per surface, **reflectance
  GIVEN**, not pixels, not images, not spectra; the axes are not learned.
- The **white-patch (anchor) assumption** — inherited from T3 and still load-bearing:
  the two frames must share the surface SET. Land's assumption, imported as a mechanism.
- The **intrinsic global-scale ambiguity** (T3's bound L1-of-T3) is untouched and
  remains correct behaviour.
- Inherited and unchanged: deformation, style, the learned axis-codebook at natural-image
  scale.

---

## 8. PROVENANCE (§10)

Engine hash, `provenance_line()`, base HEAD **7cbf1962**, branch, `data/` symlinked
(§10.2) so the bench number is the **200/0** condition, and the exact seed block consumed
are all recorded in `VISION_LIGHTING_L1_RESULTS.md`. **NO new Rust ⇒ no new engine hash**
(§10.1 rule 4). Every number in the results file comes from
`results/lighting_l1_measure.json`, written by `scripts/lighting_l1_measure.py`.

**§7: the outcome is reported whatever it is.** A low-gain merge, an out-of-class
admission, or a failure of the bound to fall out cleanly are all first-class results and
will be stated as the headline if that is what the run says.
