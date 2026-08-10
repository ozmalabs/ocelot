# BIGVILLE — SYNTACTICALLY COMPOSED POLITICAL DRAMA — PRE-REGISTRATION

Block **246000** (SEED range `246000–246999`: `seed_claim` reports **CLEAN**;
the drama is deterministic and draws no RNG, so the reservation is nominal).
Committed BEFORE any measured number. Base SHA
`b1b021f517acb327160af2cbdf55f3627b484d8d`.

## The claim under test

Block **245000** (`BIGVILLE_DRAMA_RESULTS.md`) proved the political drama EMERGES
from the seeds + rules, but flagged its own residual: the utterance TEXT is a
**cosmetic lookup table** (`UTT_TEXT = {1: "…the pastor stirs needless trouble.",
0: "…"}` in `scripts/bigville_drama_run.py`) — because per langsim (243000) the
base faculty was lexical-not-syntactic. Block **244000**
(`LANGSIM_SYNTAX_RESULTS.md`) fixed that: a structured
`Intent{predicate, agent, patient, recipient}` composed from word ORDER via the
`domains/language.py` Merge faculty on the Rust engine, order-sensitive, the
scrambled control dropping to the floor.

**This block (246000) wires the drama's utterances THROUGH the 244000 syntax
faculty**, so who-accuses-whom / who-undermines-whom is genuinely COMPOSED from
structured roles and comprehended order-sensitively, NOT looked up. The drama's
graph-state spine (John's held `chosen_burn`, Mary's minted `InferredDisposition`,
the villagers' `backs_mary`) is UNCHANGED; the surface becomes a real linguistic
artefact and the observation counts that feed the credibility rule are DERIVED by
COMPREHENDING the composed utterances.

## Architecture

- ADDITIVE, new files only, prefixed `bigville_lang_` / `drama_syntax_`.
  Blocks 244 (`domains/langsim_syntax.py`, `worlds/langsim_syntax_world.py`,
  `domains/language.py`) and 245 (`worlds/bigville_drama_world.py`,
  `seeds/bigville_drama_social.json`, `scripts/bigville_drama_run.py`) are REUSED
  BY IMPORT and left byte-UNCHANGED.
- The utterance CONTENT is COMPOSED by the graph syntax faculty
  (`language.produce` / `language.comprehend`) from a structured communicative
  Intent (predicate + roles) over a graph-resident drama lexicon (Sign data);
  NO Python string template / lookup dict.
- Decisions stay RULES: John's GOVERN/UNDERMINE is the unchanged `ss_choose_burn`
  Argmax; his public FACE is the unchanged `bd_john_public_face`; Mary's inference
  / goal / claim and the villagers' backing are the unchanged 245 seed rules. The
  adapter only COMPOSES surfaces from held graph state and DERIVES observation
  counts by COMPREHENDING those surfaces (mechanical I/O).
- NO new Rust (reuse the 244000 `language.produce` graph-side path; the Rust
  `RenderRules` arity ceiling is not touched). If the Render engine forced Rust it
  would be flagged; it does not.

## The drama lexicon (graph-resident Sign data, extends the langsim pattern)

Predicates the drama needs, each SVO (`agent` dir L, `patient` dir R bare) so word
ORDER assigns roles:

- `serve{agent, patient}`     — John's benevolent public self-claim ("John serves Bigville")
- `accuse{agent, patient}`    — the DARVO blame ("John accuses Mary" = "the pastor stirs trouble")
- `undermine{agent, patient}` — the harmful act (John's HELD private intent; and Mary's claim about John)

Proper-noun leaves: `John`, `Mary`, `Bigville`, `village`, `council`, `pastor`,
`mayor`.

The composed surfaces per John's graph decision:

| John's graph state | PUBLIC (composed, comprehended by villagers) | HELD/PRIVATE (composed) |
|---|---|---|
| deception (`stated_benevolent=1`, `chosen_burn=1`) | `serve{John,Bigville}` + `accuse{John,Mary}` | `undermine{John,Mary}` |
| no deception (`stated_benevolent=0`) | `undermine{John,Mary}` | `undermine{John,Mary}` |
| govern (`chosen_burn=0`) | `serve{John,Bigville}` | `serve{John,Bigville}` |

Mary's claim (when she forms a `DramaGoal`): `undermine{agent:John, patient:village}`.

The observation counts feeding the UNCHANGED credibility rule are DERIVED by
COMPREHENSION of these composed surfaces (not read off `stated`/`burn` directly):
`seen_benevolent += 1` iff the comprehended public names John as `agent` of `serve`;
`seen_hostile += 1` iff it names John as `agent` of `undermine`; `heard_claim += 1`
iff Mary's comprehended claim names John as `agent` of `undermine`. These map
1-to-1 onto 245's `seen_benevolent += stated` / `seen_hostile += (1-stated)` /
`heard_claim += mary_claims`, so the 245 counts (and every 245 gate) are preserved
BY CONSTRUCTION — now carried by composed language.

## Gates (pre-registered; a fabricated/unpre-registered number is a firing offence)

- **G-composed-not-lookup (HEADLINE):** the drama's key utterances are produced by
  the syntax faculty (`language.produce`) from a structured Intent (agent/patient
  roles), round-trip-verified (`comprehend(produce(intent))` recovers the roles) —
  NOT a canned string. Source-audit: no lookup dict of utterance strings in the new
  files; content comes from the graph faculty. PASS iff a composed utterance +
  its structured Intent round-trip and the source-audit is clean.
- **G-roles-carry (order-sensitive who-accuses-whom):** `accuse{John,Mary}` composes
  to a surface the receiver comprehends as `agent=John, patient=Mary` (target Mary);
  the role-swap `accuse{Mary,John}` composes/comprehends to `agent=Mary, patient=John`
  (target John) — a role-swap CHANGES the target, and a word-order SCRAMBLE fails to
  bind the agent role. PASS iff target(John accuses Mary) == Mary, target(Mary
  accuses John) == John, and the scramble drops a role.
- **G-drama-still-emerges:** the 245 emergence gates STILL pass, now driven by the
  COMPOSED language — re-run the three headline dynamics with their FAILING controls:
  - G-scheme-emerges: psychopath John scheme rate **1.0**; non-psychopath control **0.0**.
  - G-inference-emerges: Mary mints **1** `InferredDisposition == 'hostile'` + goal + claim;
    no-ToM control mints **0**.
  - G-credibility-asymmetry: deception ON → **1/5** back Mary; deception collapsed → **5/5**.
  PASS iff all three hold under the composed-language world (identical to 245's
  categorical values, because the counts are preserved by construction).
- **G-discipline:** own engine (`source_match=own`); canonical shared `.so` md5
  START==END (never written through); NO Rust (`runners/dsl` diff EMPTY); oracle
  `rung7_vision_bench.sh` + `per_area_settlement_regression` fail-set node-id SET
  before==after (ZERO new reds); gate `tests/test_bigville_lang_migrated.py`.

## Honest-residual pre-commitment

244000 was scoped to the give/promise frame; this block extends composition to
`serve`/`accuse`/`undermine`. I will report WHICH drama frames compose vs fall back,
and whether the drama's evidential weight is now genuinely LINGUISTIC (the credibility
counts derived by comprehension of composed utterances) vs still graph-state. A
partial result is reported straight. The public deception PAIR (serve + accuse) is
two composed clauses, not one conjoined clause — reported as such. The economy and
every social DECISION remain 245's unchanged graph rules; the contribution here is
that the SURFACE and the observation counts are now composed/comprehended, not
templated.
