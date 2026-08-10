# A REPRESENTABLE REFUSAL — PRE-REGISTRATION

*Written and committed BEFORE any measurement number (PROTOCOL §3). The
successor to `VISION_ARGMIN_UNIQUE_RESULTS.md`, whose headline was: "`ArgminUnique`
can refuse, and no caller in the seed layer can hear it." This rung makes a
refusal HEARABLE.*

## Seed block

- **117000–117999** (mine). `check_claim` verbatim (`scripts/seed_claim.py 117000 117999`):

```
SEED CLAIM 117000-117999: CLEAN -- no collision DETECTED.
  Scope: 822 files with seed sinks; 511 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

- **Every generator argument is a LITERAL element of 117000–117999** — no
  `base + K` offset expression anywhere (the refusal-capacity rung's §11.6 lesson).
  This rung's measurement is DETERMINISTIC (no RNG in the discrimination path);
  seeds are used only where a randomised replicate is drawn, always in-block.

## The measured gap (three-way confirmed, restated in one line)

At the caller, a REFUSAL is byte-identical to three other things:
`Eq(node, sel)` returns `Bool(false)` on a refusal — the same bytes as *"you
are not the winner"* and *"the source was empty"*; `Attr(sel, key)` returns a
bare `None` — the same bytes as the empty null. `value.rs` confirms it at the
type level: `Value::None` is documented as BOTH "Python's None" AND "the default
for missing attrs", and `truthy()` collapses `None`, `0`, `0.0`, `""`, empty
collections, and `false` all to falsy. **There is no value in the language
distinct from "nothing / no / empty."**

And `argmin_or_argmax_over` (term.rs) makes it sharper than the ArgminUnique rung
recorded: the **tie-path and the empty-path BOTH return `default`** (lines
8195–8199 and 8223–8228). So even the existing `default` mechanism cannot
separate REFUSED from NOTHING — passing a sentinel as `default` conflates them.

## Hypothesis (two-sided)

**H1.** A refusal can be made distinguishable AT THE CALLER — and at the
PyO3/world-adapter boundary — from all three things it currently collapses into
(NO / NOTHING / a real value), by a purely-additive change that (a) leaves every
committed result byte-identical (§9) and (b) is reachable ONLY by a
comparison-matched-nothing, never by a selection over ordinary values (the
governing law).

**H0.** Any value that separates REFUSED from the three others is either (a) one
a SELECTION over ordinary values can silently mint (violating the governing law),
or (b) cannot be built without breaking byte-identity, or (c) still collapses to
None/false/empty at some caller shape.

## The FOUR-WAY DISCRIMINATOR — the pass condition (registered before any number)

Four cases must reach a consuming RULE (and the PyO3 boundary) DISTINCTLY:

1. **REFUSED** — a comparison matched nothing (an `ArgminRefusal` tie; a
   ShapeDecode/TransformDecode no-match lifted by a rule).
2. **NO** — a comparison came out false (`Bool(false)`).
3. **NOTHING** — an empty/absent source (`None` / missing attr).
4. **A REAL VALUE** — an ordinary result (a Node / Int).

- **CONFIRM** = a downstream rule branches DIFFERENTLY on all four, demonstrated
  by construction (feed each case; observe the rule take a distinct branch); the
  measured cases COMPOSE (an `ArgminRefusal` tie reaches a `where` as REFUSED not
  `false`; a walled ShapeDecode no-match is liftable to the SAME refusal token, not
  `None`); AND it survives PyO3 (a world adapter tells REFUSED from None/false/real).
- **FALSIFY** = REFUSED still collapses to None/false/empty at the caller, or
  cannot be built without breaking byte-identity, or the refusal value is one a
  SELECTION can silently produce.
- **GOVERNING-LAW GUARD (positive control, both directions):**
  - **direction 1** — a SELECTION over ordinary values can NEVER yield REFUSED:
    ordinary `Argmin`/`Argmax`/`Pick` never emit the refusal token, and
    `ArgminRefusal` over DISTINCT candidates returns a real winner, not the token;
    the token appears IFF the uniqueness comparison failed (a tie).
  - **direction 2** — REFUSED is distinct from `None` AND `Bool(false)` AND `0` at
    a `where`/Term boundary AND across PyO3.

## The design (chosen, with its cost stated)

The fork was weighed against the four-way discriminator + §9 + persistence + PyO3:

- **A — a `Value::Refused` variant.** Rejected as the primary: it forces the whole
  crate's exhaustive matches (~hundreds of arms), serde/jsonio/`truthy`/Eq/Ord/hash
  and the PyO3 boundary to gain a variant, to buy a distinction that a held NODE
  already gives for free. It carries a payload natively — but a minted graph node
  (C) carries the same payload AND is what the promote/ground spine reads.
- **B — a held refusal SENTINEL node**, returned by a refusing Term. This is chosen,
  BUT "zero new Rust" is FALSE for the honest four-way: `ArgminUnique`'s single
  `default` is returned on BOTH tie and empty, so a sentinel-as-default conflates
  REFUSED with NOTHING. The minimal honest fix routes the sentinel to the TIE PATH
  ONLY (empty stays `None`) — which the existing `default` cannot express.
- **C — refusal-as-minted-node** (a `Residual` node minted as a rule EFFECT) for
  persistence + the promote/ground hook.

**CHOSEN: B (made honest) + C.**

1. **Rust (additive, index 180):** a NEW Term `ArgminRefusal { source, var_name,
   value, refused: Option<TermIdx> }` — declared LAST in the enum so 175–179 do not
   move. Identical fold to `Argmin`, with ONE difference from `ArgminUnique`: on a
   tie (non-unique extremum) it returns the evaluated `refused` token (or `None` if
   unset); on an EMPTY source it returns `Value::None` — NEVER the token. This is the
   tie/empty SPLIT the existing `default` cannot make. §13: uniqueness is exact
   equality (`cmp_value == Equal`); there is no constant and nowhere to put one.
   Existing callers (`Argmin`/`Argmax`/`ArgminUnique`) are threaded with
   `refused_on_tie = None` and are byte-identical.
2. **A held `RefusalMark` node** minted by seed data (a NODE, not a reserved magic
   string — §13-clean). A rule references it via `Pick(NodesOfType("RefusalMark"))`
   and passes it as `refused`. REFUSED is then the value `Node(mark)`.
3. **A consuming rule** that branches four ways on the returned value, plus an
   effect rule that MINTS a `Residual` node on REFUSED — demonstrating a rule can
   finally HEAR a refusal and turn it into a first-class inspectable graph object.

**Cost paid:** one new Term variant wired across term.rs (enum + evaluate + remap +
child-collect), jsonio (name/to/from), reflect (to/from), and a regen of the
generated `term_variants.rs` (NUM_TERM_VARIANTS 180 → 181). NO `Value` variant, NO
`py.rs` change (a Node crosses PyO3 as a NodeID already), NO change to any existing
Term's serialization.

## Statistic / arms (exact, no sweeps)

- **BASELINE (collapse):** with the UNCHANGED engine, feed REFUSED / NO / NOTHING
  into the WTA idiom `Eq(node, ArgminUnique{...})` and the `Attr(sel, key)` idiom;
  record that all three are byte-identical (`false` / `None`). Report the bytes.
- **ARM D (four-way):** with `ArgminRefusal + RefusalMark`, feed the four cases to
  ONE consuming rule set; record which branch each takes; assert all four distinct.
- **ARM G (governing law):** direction 1 — a selection (ordinary `Argmin`, and
  `ArgminRefusal` over DISTINCT candidates) never yields the token; direction 2 —
  `Eq(token, None) == false`, `Eq(token, false) == false`, `Eq(token, 0) == false`,
  `truthy(token) == true`, all at a Term boundary.
- **ARM P (PyO3):** query the four results through the Python boundary; assert a
  world adapter distinguishes `NodeID(mark)` / `None` / `False` / `NodeID(other)`.
- **ARM C (compose):** a walled `ShapeDecode` no-match, lifted by a rule to the
  SAME `RefusalMark`, reaches the consuming rule as REFUSED (not `None`).
- **ARM R (persistence):** a graph containing a REFUSED-minted `Residual` node
  round-trips byte-identically through `graph_to_dict`/`graph_from_dict`; a graph
  WITHOUT one is byte-identical before/after.
- **ARM §9:** oracle 222/0 (`data/` symlinked) before AND after; engine hash
  re-verified after measurement; a migrated gate that is RED without the seed/Term
  and GREEN with it, and a positive control that goes RED on a foreign edit.

## Decision rule

CONFIRM iff ARM D shows four distinct branches AND ARM G passes both directions
AND ARM P distinguishes all four across PyO3 AND ARM R round-trips AND the oracle
is 222/0 before and after. A null (any arm collapses) is reported as a FALSIFY
with the collapsing case named — not rescued by changing the measure (§5).

## Prediction (stated in advance, with provisos)

I predict **CONFIRM**. Provisos I expect could break:
- (P1) I expect the new Term compiles with ~6–10 match arms flagged by the
  compiler across term.rs/jsonio/reflect; if a match I did not anticipate is
  exhaustive (e.g. in shape_decode.rs or a cost model), the blast radius is larger
  than "additive Term" implies — I will report the true count.
- (P2) I expect the `RefusalMark` node to round-trip cleanly; if `graph_to_dict`
  or a reconcile path drops an unknown-type node, ARM R fails and B is not as cheap
  as claimed.
- (P3) I expect the four-way to hold at the VALUE level (token is a Node, distinct
  from None/false/real). The one place it will NOT hold unaided is the EXISTING
  16 `Eq(node, sel)` WTA sites: there `Eq(candidate, token) == false` for every
  candidate, so REFUSED still reads `false` UNLESS the rule adds an
  `Eq(sel, RefusalMark)` guard. That is the successor's arming work, not a
  falsification of this rung — I state it here so the scope is honest in advance.
- (P4) The governing law direction 1 is the one I am least able to make airtight:
  it is true by construction (the token is emitted only on the tie branch), but a
  rule COULD put the RefusalMark node into a candidate source, and then a selection
  would "return" it. I will show this requires deliberately feeding the marker as
  DATA — it is not something a selection over ORDINARY percepts can do — and record
  the boundary.

## Scope (what is NOT shown)

- The PROMOTE (`SelfConcern → StandingConcern`) and GROUND (teacher) closure is
  NAMED as the successor, NOT built. This rung demonstrates HEAR + MINT only.
- The tie rate on real scenes is not measured (the ArgminUnique rung established it
  is unmeasured); this rung establishes REPRESENTABILITY, not an armed gate.
- Nothing is armed at the 16 existing WTA sites; the new Term is bound only by this
  rung's own demonstration seed.
