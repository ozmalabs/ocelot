# Limiting aperture per observer — what exists, and the one hole

*The ability to limit aperture is essential to social and bigville experiments.* Without limited
views there is no social dynamic at all: no belief divergence, no theory of mind, no privacy, no
deception. Every agent seeing all structure makes every agent the same agent.

This is what the substrate actually provides, measured at `aaa9fb4`.

## The good news: it is per-call, therefore per-observer, over a SHARED store

`THEORY_AS_SHAPE_RESULTS.md` established that aperture is **not stored on a held shape** — it is
applied by the matcher. That is exactly the property a social simulation wants, because per-call
means per-observer: one shared world, many partial views, rather than a private copy of the world
per agent.

Two knobs, both per-call:

**1. RANGE — `codebook_scope`.** One shared codebook `{wing, engine, proof, colour}`:

| observer | sees the wing target | sees the proof target |
|---|---|---|
| omniscient (no scope) | 2 | 2 |
| engineer `{wing, engine}` | **2** | **0** |
| mathematician `{proof}` | **0** | **2** |

**2. APERTURE — `wild_objects`.** Same observer, target of the same shape with different objects:
literal **0**, object-blind **2**.

**And the scope can come from GRAPH DATA.** A rule reading `codebook_scope: Attr(who, "knows")`
decodes each asker's own partial view — no Python decides who sees what, which is the difference
between "the engine supports partial views" and "a social simulation can be written here".
`seeds/reflex_net.json` already does exactly this, and says so: *"two nets over the SAME shared
codebook can hold DIFFERENT basins"*.

## The hole: an agent who knows NOTHING sees EVERYTHING

Measured, same codebook, same target:

| scope | covered_count |
|---|---|
| absent | 2 — omniscient, by design |
| `['wing']` | 2 |
| `['proof']` | 0 |
| **`[]` — knows nothing** | **2** |
| `['nonexistent']` | `None` |

The empty scope collapses onto omniscient. In a social experiment that is the **exact inversion you
cannot tolerate**: the least-informed agent has the most access, and it is silent.

The cause is one guard, and it is deliberate:

```rust
fn apply_scope(...) {
    let Some(sc_idx) = scope_idx else { return };     // absent -> unrestricted
    let scope = collect_part_names(&evaluate(...), ...);
    if !scope.is_empty() {                            // empty  -> ALSO unrestricted
        parts.retain(|p| scope.contains(&p.name.to_lowercase()));
    }
}
```

documented as *"A `None` scope, or one evaluating to an empty set, leaves the codebook unrestricted
— exactly mirroring `apply_exclude`'s `!excl.is_empty()` guard, so a net with no declared basin
decodes against the whole codebook."*

**This class of bug has bitten here before.** The same file records a measured inversion where every
scope element was silently dropped, the set came out empty, and a decode asking *"score this ONE
part"* returned **36 — the whole codebook's maximum** — instead of the true **0**. That was fixed at
the string-reader level. The empty-set semantics were left as intended behaviour.

## The fix is available and, on the evidence, behaviour-preserving

The two cases are distinguishable at the `Option` level and only one is load-bearing:

* `scope_idx == None` — no scope argument at all ⇒ unrestricted. Keep.
* `Some(t)` where `t` evaluates to `Value::None` — a scope was asked for but the attribute is absent
  ⇒ unrestricted. **This is the load-bearing case**: `reflex_net` passes
  `codebook_scope = Attr(rn, basin_parts)` and **no node in that seed carries a `basin_parts`
  attribute at all**, so every net takes this path.
* `Some(t)` where `t` evaluates to a present-but-EMPTY collection ⇒ *"this observer knows nothing"*
  ⇒ should restrict to nothing. Currently indistinguishable from the above.

Audited: every `codebook_scope` site in the tree — `can_native_reimplementation`,
`embodied_development`, `embodied_motor_bootstrap`, `embodied_physics_proposal`,
`humanoid_adaptation`, `somatomotor_waves`, `vision_crossframe_identity`,
`vision_invariant_comparator`, `vision_verdict_comparator`, `reflex_net` — builds its scope as
`SetT{items: [Attr(...)]}`, a singleton name read off a node, or leaves the attribute absent.
**No seed passes a literal empty list.** So separating the two cases changes nothing that currently
runs, and gives a social experiment the primitive it needs.

## FIXED

`apply_scope` now distinguishes the two cases, via a named predicate so the semantics are testable
without constructing a codebook:

```rust
fn scope_is_declared(sc_val: &Value) -> bool { !matches!(sc_val, Value::None) }
```

`Value::None` — a scope asked for but the attribute absent — stays unrestricted, preserving
`reflex_net`. Anything else, **including a present-but-empty collection**, restricts. The doc comment
that claimed the mirroring is corrected in place: scope and exclude are DUALS, so excluding an empty
set is a no-op while scoping to one is total restriction, and mirroring them was the error.

Measured after: `scope []` goes from **2 (the whole codebook)** to seeing nothing, and the
graph-native social case now reads engineer 2 / mathematician 0 / **child (knows nothing) nothing**.
Rust lib suite **792 passed, 0 failed**, including the new
`an_empty_scope_is_a_declaration_but_a_none_scope_is_not`.

The resulting distinction is meaningful rather than sloppy: `None` means *nothing is in your scope at
all* (the same as naming a part that does not exist), while `0` means *something is in scope but does
not cover this*.

## Started: graded per-observer APERTURE, as a QUOTIENT rather than a wildcard

`wild_objects` is all-or-nothing per call, and `CLAUDE.md` records the codebook-side wildcard path as
**retired** for conflating consistent substitution with incoherent novelty. The retirement is right,
and it points at the correct operation: WILD means *"matches anything"*, which discards WHICH
substitution occurred. Limited perception is not that. It is **"these are the same thing to me"** —
a quotient.

So: project a signature onto the dimensions the observer resolves, replacing unresolved slots with a
CONSTANT rather than a wildcard, and match LITERALLY. Two shapes differing only in dimensions an
observer cannot resolve become literally equal *for that observer* — an honest equivalence class,
claiming nothing about what filled the slot.

**Validated.** Four world shapes, three observers:

| observer | distinguishable things |
|---|---|
| expert (all slots) | 4 of 4 |
| layman (predicate + subject) | 4 of 4 |
| **glancer (predicate only)** | **2 of 4** — aileron/throttle/tiller collapse into one class, still distinct from `colour` |

**And it needs NO new Rust.** The vocabulary is already there: real codebooks tag every slot with
`dim_types`, populated across the corpus as `val` 789, `pred` 263, `idx` 263 — a ready-made
three-level aperture. The projection composes from existing Terms:

```
MapList(over relations,
        ZipWith(slot, dim_type,
                IfThenElse(In(dim_type, resolved), slot, marker)))
```

Measured live: expert `{pred,val}` keeps full detail; glancer `{pred}` renders
`[["controls","·","·"], ["controls","·","·"]]` — the two relations now literally identical.

### BUILT — `seeds/observer_aperture.json` v1.0.0, four rules, zero new Rust

The observer's aperture is graph data on the observer node (`resolves`, a list of
`dim_types`), and four rules do the rest — `ap_project_percept`, `ap_project_held`,
`ap_refresh_scope`, `ap_decode_percept`. No Python decides who sees what.

**Both halves are projected**, which was the second open item. Projecting only the goal would
decode a blurred observation against full-detail held parts, which is nobody's situation: what
an observer holds was itself acquired through its aperture. A projected part is named
`<observer>/<part>` so two agents' quotients of the same world part are distinct parts in the
one shared store.

**APERTURE and RANGE compose, and the composition is the mechanism.** The quotient decides what
an observer can TELL APART; `codebook_scope` decides what it HOLDS. `ap_refresh_scope` sets the
observer's scope to exactly the names of its own projected parts, so `ap_decode_percept` reads
that observer's quotient of the world and nobody else's — over the shared store, no private
copy per agent. This is also the first consumer of the empty-scope fix above: an observer that
has projected nothing now decodes against nothing rather than against everything.

Γ is declared rather than bypassed — four productions covering `perceives`, `holds_part`,
`projected`, `projected_part`. `CLAUDE.md` enumerates 159/634 rule-carrying seeds minting edges
through zero productions; this one is not among them. (The first run failed loudly with
`Γ rejects: type 'Observer' not in vocabulary`, which is the check doing its job.)

Measured, one shared store, three acuities over four world shapes:

| observer | resolves | can tell apart | percepts held |
|---|---|---|---|
| expert | `pred, val, obj` | **4 of 4** | 4 |
| glancer | `pred` | **2 of 4** | 4 |
| blind | *(nothing)* | **1 of 4** | 4 |

**Collapsing is not deleting** — the blind observer still counts four things while telling them
apart as one. The quotient is a claim about DISCRIMINATION, not about existence.

And the two results the seed exists for, both now produced by rules rather than by a probe:

| held / seen | meteorologist (`pred,val,obj`) | mystic (`pred,val`) | zealot (`val`) |
|---|---|---|---|
| barometer / **tea_leaves** | covered 1, residual `[["reads","me","leaf_pattern"]]` | covered 2, residual `[]` — **GROUNDS** | — |
| barometer / **omen** | covered 1, residual `[["senses","me","dream_image"]]` | covered 1, residual `[["senses","me","·"]]` | covered 2, residual `[]` |

The second row is the correction in `ONE_LOOP_MANY_GRAINS.md`, mechanised. The mystic's residual
is NON-EMPTY — it knows something here is unaccounted for — and its content carries the
unresolved marker, so it cannot say what. **Knowing THAT, without knowing WHAT.** The zealot,
which cannot resolve the predicate at all, sees no residual: nothing to detect, so honest
ignorance is unavailable to it rather than merely unexercised.

Gate: `tests/test_observer_aperture_migrated.py` **8/8**, including the negative control
(a full-aperture projection must alter nothing) and a fixpoint check.

## APERTURE IS A FRAME — chosen, forced, or negotiated (`seeds/aperture_frame.json` v1.0.0)

`observer_aperture` made aperture graph data, but as a single authored list: an acuity the observer
simply HAS. That is incomplete. An aperture is the FRAME you are viewing in, and a frame has
provenance — you can CHOOSE it, it can be FORCED on you, or you can NEGOTIATE it with someone else.

This is the reference-frame sense, not the Fillmore `Frame` in `seeds/design.json` (language
semantics, left alone). And it is not a metaphor here: `CLAUDE.md`'s frame/continuum invariant puts
every lossy or real-valued map in `Hom(frame, frame)` rather than inside a frame's coordinates, and
the projection above IS such a map — world frame to observer frame, with the collapse marker naming
exactly what the map discards.

**The effective aperture is a MEET.** `resolves` stops being authored and becomes derived: the
`Fold`/`Intersect` of the observer's own maximum acuity (`ap_full` — its physiology) with every
frame in force. A frame can only narrow; an aperture offering a dimension the observer's physiology
lacks does not grant it, and two frames compose by intersection regardless of provenance.

**The three modes DECODE IDENTICALLY and differ entirely in RECOURSE.** That is the whole content
of the distinction — same world, same held part, same residual, three different available moves:

| mode | recourse | measured |
|---|---|---|
| **chosen** | widen unilaterally | frame dropped, `resolves` back to full, residual re-read at full detail |
| **forced** | none — cannot lift it | stays narrow, residual `[["senses","me","·"]]`, files `SelfConcern{capability_gap}` naming the frame |
| **negotiated** | requires every bound party | 0 accepts → nothing; **1 accept → nothing**; 2 → attaches to both |

The forced row is `ONE_LOOP_MANY_GRAINS.md`'s knowing-THAT-without-knowing-WHAT one level up: not
merely unresolved, but unresolvable BY YOU — so it lands on the existing human-gated spine where
another party can act on it. An agent that can only be forced has no attention; one that can only
choose has no social constraint; one that cannot negotiate cannot establish common ground.

Gates: `tests/test_aperture_frame_migrated.py` **10/10**, `tests/test_observer_aperture_migrated.py`
**11/11**. All eight rules across both seeds mutation-tested — every single-rule drop fails at least
one test.

### Four defects this rung found, three of them in work landed the same day

Recorded because each is a reusable failure mode, not because the fixes are interesting.

**A cached projection survived a frame change.** Dedup was by projected-from name alone, so a forced
frame narrowed `resolves` while the decode went on reporting a full-detail residual from a view
taken through the *old* aperture. A view is only valid for the frame it was taken through; both the
dedup guard and the decode now carry an aperture generation. The two recourse rules needed the same
filter — before it, the forced arm filed a gap for an observer that, under the frame actually on it,
grounds cleanly with an empty residual. **A concern about a residual that no longer existed.**

**A count was held where a list had to be read.** After the generation bump, `ap_refresh_scope`
compared `Count(current-generation parts) = 1` against a **stale** `ap_scope_n = 1` left from the
previous generation — equal by coincidence, so the rule never re-fired and the scope was never
written. This is `CLAUDE.md`'s own retracted-baseline lesson at rule scope: *a count can be held; a
list has to be read.* The guard now compares the scope list itself.

**A rule is not re-armed by an attribute change on a node it only reaches at evaluation time.**
With `af_relax_chosen`'s guard reading `ap_residual` through `Neighbours` inside an `Exists`, the
rule was satisfiable and fired when applied directly by index — but **five successive full ticks
never scheduled it**. Every other seed in this tree that re-arms on state (`tr_epoch_seen`,
`codebook_epoch`) reads it off a MATCHED var, and this is why. The view is now in the match.

**And the empty-scope inversion came back through the door, at seed level.** The engine fix above
made a present-but-empty scope restrict correctly — but `ap_refresh_scope` is anchored on a
`projected_part` edge, so an observer holding NOTHING never fires it and `ap_scope` stays *absent*,
which reads as unrestricted. The agent who knows nothing sees everything, again, one level up. Fixed
by reading the scope inline at decode time, where no parts yields the empty list rather than nothing
at all. **Two related bugs fell out of the same fixture**: the re-arm guard was `Lt`, so an observer
whose part count never rises could never decode at all; and an absent `ap_seen` compares EQUAL to
the numeric `0` the counter starts at, so it silently never ran and returned a null verdict.

### And the gate that could not fail

Every test in the first version of `observer_aperture` used ONE observer — and with one observer an
unrestricted codebook is indistinguishable from a correctly scoped one, because the only parts in
the store are that observer's own. **The entire range half of the seed was inert, and the 8/8 gate
could not see it.** It took a second observer to make the difference observable, and a second
fixture after that to make it *matter*: with both observers holding the same part, an unrestricted
decode still reaches the right verdict, so the first isolation test only ever gated an assertion
about the scope attribute. The fixture that bites is asymmetric — `haver` holds a barometer,
`pauper` holds nothing and sees the same thing at the same acuity, and leakage changes the answer.

A related honest limitation, not fixed: an observer holding nothing reads `covered = None` and
`residual = null` rather than *"all of it is outstanding"*. `None` is the engine's documented
"nothing is in your scope at all" (distinct from `0`, "something is in scope and does not cover
this"), so the isolation claim holds — but the more useful reading for a social simulation would be
a full residual, and that is an engine-level semantic shared with every other scope user rather than
something this seed should decide alone.

### What remains for the full build

* ~~the observer's resolved `dim_types` as graph data on the observer node, and a rule that projects
  through it~~ — **DONE**, `resolves` + `ap_project_percept`;
* ~~projecting the CODEBOOK as well as the goal~~ — **DONE**, `ap_project_held` +
  `ap_refresh_scope`;
* **STILL OPEN — the mint.** A projected decode currently reports `ap_covered` / `ap_residual` and
  stops. It does not mint, and per the retraction below it should. What blocks it is not a decision
  but a missing attribute: `MINTING_AT_APERTURE.md` measures 182 mint sites recording no resolution,
  and until a mint carries the aperture it was formed at, *"I could not resolve this"* and *"there
  was nothing more to resolve"* are the same empty residual. That is the next rung, and it is shared
  with every other grain rather than specific to this seed;
* **PARTLY CLOSED — aperture as a learned shape.** `aperture_frame` makes the effective aperture
  DERIVED (the meet of physiology and every frame in force) and makes frames attachable, droppable
  and negotiable at runtime, so an agent's acuity now changes during a run. What is still authored
  is the vocabulary: `ap_full` and each `Aperture`'s `resolves` are hand-set lists, and nothing
  MINTS an aperture from observation. Aperture-as-a-shape, decoded and grown by the same loop as
  everything else, remains argued rather than built;
* ~~and the question this has not touched: whether a projected decode should be able to MINT. On the
  quotient reading it must not.~~ **SUPERSEDED** — `MINTING_AT_APERTURE.md` retracts this. A
  projected decode MAY mint, and must: minting from an unresolved residual is the only thing a
  limited observer can do, and theory of mind is precisely that. What the mint needs is not a
  prohibition but the aperture it was minted at, so that a coarse entity can later be REFINED rather
  than only contradicted. `ONE_LOOP_MANY_GRAINS.md` adds the further case this build has to support:
  an observer can DETECT a residual it cannot RESOLVE, so a projected decode must be able to report
  incomplete coverage without being able to name what is missing.
