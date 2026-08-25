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

## Not done

The change alters documented, intentional engine semantics on `ShapeDecode`'s path, so it is
recorded here rather than made. What is needed to make it is small; what is needed to make it
*safely* is the both-modes comparison this tree already expects of an engine default, and a decision
that `[]` ≠ absent is the contract you want.

Also unmeasured: whether `wild_objects` is the right aperture knob for social use at all. It is
all-or-nothing per call, and `CLAUDE.md` records the codebook-side wildcard path as **retired** for
conflating consistent substitution with incoherent novelty — so a graded per-observer aperture, as
opposed to a graded per-observer RANGE, has no mechanism here yet.
