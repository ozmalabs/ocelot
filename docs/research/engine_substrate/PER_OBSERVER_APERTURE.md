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

### What remains for the full build

* the observer's resolved `dim_types` as graph data on the observer node, and a rule that projects
  through it — the `codebook_scope = Attr(who, "knows")` pattern, one level down;
* projecting the CODEBOOK as well as the goal, so an observer decodes its own quotient of the world
  rather than a quotiented goal against full-detail parts;
* and the question this has not touched: whether a projected decode should be able to MINT. On the
  quotient reading it must not — an observer minting from what it cannot resolve is inventing
  detail, which is the target-grain wishful-thinking failure in another costume.
