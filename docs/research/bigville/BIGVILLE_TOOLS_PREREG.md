# PREREG — block 336000: tools + inventory + ownership (adventure-game mechanics)

Actions until now applied at a flat rate. Real work needs **tools**: mining with your hands
bears almost nothing at large cost; a pick actually works. The primitive is the basic
adventure-game verb — **use X on Z** (a pick on a rock, a knife on a person) and **use X with
Y** (a knife with food). A tool is an **effectiveness multiplier** on an action, held in an
**inventory**. And a tool has an owner — but **ownership is not a world fact**: it is a
recognized frame, exactly like authority (block 324000).

## The mechanism (`bigville_tools.json`)

**Fitness is data, not code.** A `Tool` carries `fit_for -> Fitness{verb, mult, effort}` children;
a new tool is a new node, never a new rule. Bare hands are a per-agent tool with tiny mult
(~0.05) and large effort (~3). A pick/rod has `mult 1, effort 1`. A knife has *two* fitnesses —
`prep` and `strike` — one node, dual-use, the verb selects.

- **`tl_gather`** — *use X on Z* (a `Deposit`): `yield = richness · fit.mult` into the matching
  inventory slot; `effort = base · fit.effort`; the deposit depletes (conservation). Gated on
  **holding** the tool, and on a fitness matching the deposit's `gather_verb` (a rod can't mine).
- **`tl_strike`** — *use X on Z* (a person): `harm = fit.mult` (a knife wounds; a fist barely);
  the victim loses health. The **same** mechanic is violence.
- **`tl_prep`** — *use X with Y* (food): a knife is a **skill multiplier**, `quality =
  cook_skill · fit.mult`. (Folds into `fs_prepare`.)
- **`oc_recognition`** — *ownership is recognition*: an `OwnershipClaim{claimant}` over an item is
  worth `Count(recognizers)` — `claim.recognition = Count(InNeighbours "recognizes")`, mirroring
  `rc_authority`. There is **no `owns` edge**. The inn "owns" its knives because the town
  **recognizes** the inn's claim.

## The fact/frame split, made concrete

- **Holding** (`agent -holds-> tool`) is a **world-fact** — physical possession. Tool use is gated
  on holding, never on owning: the cook uses the inn's knife because he *holds* it; a thief can
  wield it too.
- **Owning** is a **recognized frame** — `owner = argmax-recognized claimant`. The inn owns the
  kitchen knives while the cook holds them. **Possession never transfers recognition**: a thief who
  takes the knife holds it, but the town still recognizes the inn → that is what makes it *theft*,
  not acquisition. Split recognition = **disputed**; the substrate never adjudicates.

## Gates (pass/fail, pre-registered)

1. **G-hands-bear-almost-nothing (HEADLINE):** mining with bare hands yields ~nothing at large
   cost; a pick yields >10× at lower cost; the haul enters inventory; the deposit depletes.
2. **G-fishing-same:** hands barely catch; a rod works (>10×).
3. **G-wrong-tool-does-nothing:** a rod cannot mine (no matching fitness → no yield).
4. **G-knife-is-dual-use (HEADLINE):** the same knife multiplies prep quality (use *with* food)
   **and** wounds a person worse than a fist (use *on* a person).
5. **G-owner-is-not-a-world-fact (HEADLINE):** a bare ownership claim owns nothing; once the town
   recognizes it, the claimant is the owner; `recognition = Count(recognizers)`.
6. **G-holding-is-not-owning:** the cook *uses* the inn's knife (holding suffices) yet the **inn**,
   not the cook, is the recognized owner.
7. **G-possession-does-not-transfer-ownership:** a thief who holds *and* claims the knife owns
   nothing (nobody recognizes him); the inn remains the recognized owner → theft.
8. **G-disputed-ownership:** split recognition reads `disputed`; the substrate does not decide.
9. **G-no-python-decision (source audit):** gather/strike/prep/recognition are the seed rules;
   there is **no `owns` edge**; ownership is `Count(recognizers)`; use is gated on `holds`.

## Scope / honesty
- The recognition here is **seeded** by the adapter (who recognizes which claim). In the live town
  the per-agent recognition **decision** is the collapse in `bigville_recognition` (`rc_recognize`,
  valued by loyalty/fear/opportunism) — this seed reuses its *shape* (`Count(recognizers)`) and
  composes with it, rather than re-deriving the decision.
- Inventory is per-kind resource slots + held tools; richer per-stack inventory (each item its own
  node with weight/condition) is a refinement.
- `tl_prep` demonstrates the knife-as-multiplier self-contained; the full prep lifecycle is
  `fs_prepare` (block 335000), where the knife's `prep` fitness is the multiplier that folds in.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
