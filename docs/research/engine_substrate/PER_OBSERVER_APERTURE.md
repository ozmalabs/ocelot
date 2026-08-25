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
* **STILL OPEN — aperture as a learned shape.** `resolves` is currently a hand-set list. The
  document above argues aperture is itself a shape, therefore decodable and mintable by the same
  loop; nothing here acquires or changes an observer's aperture, so every agent's acuity is
  authored rather than developed;
* ~~and the question this has not touched: whether a projected decode should be able to MINT. On the
  quotient reading it must not.~~ **SUPERSEDED** — `MINTING_AT_APERTURE.md` retracts this. A
  projected decode MAY mint, and must: minting from an unresolved residual is the only thing a
  limited observer can do, and theory of mind is precisely that. What the mint needs is not a
  prohibition but the aperture it was minted at, so that a coarse entity can later be REFINED rather
  than only contradicted. `ONE_LOOP_MANY_GRAINS.md` adds the further case this build has to support:
  an observer can DETECT a residual it cannot RESOLVE, so a projected decode must be able to report
  incomplete coverage without being able to name what is missing.
