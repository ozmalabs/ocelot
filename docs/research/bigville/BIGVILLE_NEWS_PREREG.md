# BIGVILLE R21 — THE NEWSPAPER & THE REPORTER: the fourth estate, a second reconstruction channel (block 269000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `59653fd443fb0e0894b5ea59a51bb39402260f4e`
Branch: `worktree-agent-a672dd60963770a51`
Block: **269000–269999** (R21 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R21 + §0 "THE ROOM WHERE IT HAPPENED").

## Seed claim (verbatim, `python scripts/seed_claim.py 269 269`)

```
SEED CLAIM 269-269: CLEAN -- no collision DETECTED.
  Scope: 977 files with seed sinks; 694 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 269000 269999` — the full block form — is likewise CLEAN.)

## What R21 adds (and how it differs from R20)

R20 gave the town the council's OFFICIAL written voice — the noticeboard minutes,
one institutional bias (the clerk protects the council). R21 gives it a SECOND,
INDEPENDENT written channel: **the paper, written by the REPORTER with the
reporter's OWN bias, which can point back AT the council.** The paper is a mass
belief-propagation channel that reaches BEYOND earshot (R19 is proximity-bound;
the paper is not), gated by literacy (R18); its freedom is a structural lever
(funding + fear); and it is a SECOND lossy reconstruction of the same events the
observer holds ground truth for — a richer case-reconstruction validation than
one channel.

## Architecture (target: ZERO new Rust)

- The reporter's writing, the capture-suppression, the printing, the literacy-and-
  earshot-gated reading, the second-channel (clerk) rendering, and the coalition-
  forms-on-quorum decision are all **graph rules over EXISTING DSL Terms**
  (`And` / `Or` / `Eq` / `Gte` / `Plus` / `Sum` / `Count` / `Neighbours` / `Attr`
  / `Var` / `Lit` + `set_attr` / `add_node` / `add_edge`). **No new Rust Term.**
  `git diff 59653fd443 -- runners/dsl` MUST be empty (incl. `term.rs`). The
  two-channel error and the coalition informed-count are READ OFF the graph as
  MEASUREMENTS — not new primitives.
- New additive files only, all prefixed `bigville_news_`:
  `seeds/bigville_news_press.json`, `seeds/bigville_news_reach.json`,
  `worlds/bigville_news_world.py`, `scripts/bigville_news_run.py`,
  `tests/test_bigville_news_migrated.py`, this file, `BIGVILLE_NEWS_RESULTS.md`,
  `results/bigville_news/summary.json`. **No existing tracked file is edited.**
  R20 (`bigville_council_*` — the noticeboard, the second-channel comparison), R18
  (literacy), R19 (`bigville_loud_*` — the reporter is occlusion-bound), R11
  (`bigville_world_*` — Giantville news via travellers) are imported READ-ONLY as
  concepts / precedents.
- Both seeds are **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load ⇒
  the rung cannot regress any other suite (per the 2026-07-29 directive).
- **The press substrate is ISOLATED** (`substrate_rs.Substrate()._inner` loading
  the two news seeds) so the fixpoint never cross-fires.
- **Every DECISION is a rule.** The adapter only: registers Town / Event /
  Reporter / Paper / Story / Minutes / Resident / Coalition graph data (ingest),
  wires edges, runs `run_rules`, and reads state. No Python `if`/`else` over agent
  state decides who writes / prints / suppresses / learns / coalesces —
  source-audit gate.

## Rules (all in the two seeds; every one a decision)

**`bigville_news_press.json` — the reporter, the paper, capture, and the two channels:**

- `np_reporter_writes` — the reporter writes a Story for the event they cover
  (`reporter -covers-> event`, `paper -employs-> reporter`, `paper -reports->
  story`, `story -about-> event`) ONLY IF `reporter.witnessed==1` (occlusion-bound,
  R19). `story.content = event.truth_value + story.reporter_bias` (the reporter's
  OWN bias — the paper's independent rendering), `written=1`. No witness ⇒ no story.
- `np_capture_suppresses` — a CAPTURED paper LAUNDERS/OMITS a damaging story:
  `story.suppressed=1` iff `paper.captured==1 AND event.damaging_to_owner==1`. A
  captured paper suppresses the story that implicates its patron (John/Scrooge);
  it does NOT suppress an ordinary story.
- `np_paper_prints` — `story.printed=1` iff `written==1 AND suppressed==0 AND
  paper.active==1 AND printed==0`. `active` is the paper-exists lever (ablate the
  paper ⇒ `active=0` ⇒ nothing prints).
- `np_clerk_records` — the SECOND channel (the noticeboard minutes, re-modelled
  locally to score both renderings in ONE substrate): `minutes.value =
  event.truth_value + minutes.clerk_bias`, `recorded=1`. The clerk PROTECTS the
  council (bias toward the favourable side); the reporter may ATTACK it — DIFFERENT
  bias profiles over the same ground truth.

**`bigville_news_reach.json` — propagation beyond earshot + collective action:**

- `np_witness_knows` — a resident who WITNESSED the event knows it DIRECTLY
  (`event -in_town-> town`, `town -has_resident-> res`, `res.witnessed==1`,
  `knows_event_flag==0`): `knows_event = event.truth_value` (the TRUE value),
  `knows_event_flag=1`. The oral/direct layer — available to literate AND
  illiterate alike (proximity, R19).
- `np_reader_learns` — a LITERATE resident who READS the paper acquires the belief
  from it BEYOND earshot (`res -reads-> paper`, `paper -reports-> story`,
  `story -about-> event`; `story.printed==1 AND res.literate==1 AND
  knows_event_flag==0`): `knows_event = story.content` (the PAPER's rendering —
  bias-shaped, NOT necessarily the truth), `knows_event_flag=1`. An ILLITERATE
  non-witness never fires (literacy gate, R18) ⇒ stays ignorant (oral layer only)
  — the informed/uninformed divide.
- `np_count_informed` — `coalition.informed = Sum_{town -has_resident-> res}
  knows_event_flag` (the count of residents who hold the shared knowledge).
- `np_coalition_forms` — `coalition.formed=1` iff `informed >= quorum AND
  formed==0`. A shared grievance becomes COMMON KNOWLEDGE via the paper ⇒ the
  coalition can form; suppress the story ⇒ the count never reaches quorum ⇒ no
  coordination (information as a precondition of collective action).

## Gates (the pre-registered claims + failing controls)

**G-paper-propagates-beliefs (mass channel) + the literacy divide:**
- `test_literate_nonwitness_learns_from_paper` — literate, `witnessed=0`, reads the
  paper ⇒ `knows_event_flag==1`, and the belief is the paper's (biased) `content`,
  NOT the truth — non-local knowledge acquired beyond earshot.
- `test_illiterate_nonwitness_stays_ignorant` — illiterate, `witnessed=0`, reads the
  paper ⇒ `knows_event_flag==0` (the oral layer only; the R18 divide).
- `test_illiterate_witness_knows_directly` — illiterate BUT `witnessed=1` ⇒ knows
  the TRUE value directly (the oral/direct layer is open to all).
- `test_ablate_paper_literate_nonwitness_ignorant` (ABLATION, load-bearing) —
  `paper.active=0` ⇒ story not printed ⇒ the literate non-witness stays
  `knows_event_flag==0`; contrast `active=1` ⇒ learns. The paper is load-bearing
  for NON-LOCAL knowledge.

**G-free-vs-captured-press (HEADLINE — a structural lever):**
- `test_independent_paper_prints_corruption` — damaging event, `captured=0` ⇒
  `printed==1`, readers learn.
- `test_captured_paper_suppresses_corruption` — damaging event, `captured=1` ⇒
  `suppressed==1`, `printed==0`, readers stay ignorant of the corruption.
- `test_ablate_capture_suppressed_story_prints` (press-freedom counterfactual) —
  flip `captured 1→0` on the SAME damaging event ⇒ the suppressed story PRINTS.
- `test_captured_paper_still_prints_nondamaging` (CONTROL) — non-damaging event,
  `captured=1` ⇒ `printed==1`. Capture LAUNDERS the story that implicates the
  patron, not the whole paper.

**G-second-reconstruction-channel (the benchmark, ties §0):**
- `test_two_channels_differ_from_truth_and_each_other` — one event, `truth=60`,
  `reporter_bias=+15` (attack), `clerk_bias=-25` (protect) ⇒ paper renders `75`,
  noticeboard renders `35`, truth is `60`; all three distinct; `error_paper=15`,
  `error_minutes=25`; the reporter overstates (content>truth), the clerk
  understates (value<truth). BOTH scoreable against the ground truth WE hold, with
  DIFFERENT bias profiles.
- `test_reader_belief_is_paper_rendering_not_truth` — a paper-only learner holds
  the biased `content` (75), a witness holds the truth (60): non-local knowledge is
  bias-shaped.
- `test_reporter_must_witness_occlusion` (R19 tie) — `reporter.witnessed=0` ⇒ no
  story written ⇒ nothing prints ⇒ readers ignorant. The reporter reports only what
  was witnessed/told.

**G-paper-feeds-collective-action:**
- `test_paper_enables_coalition` — a damaging shared grievance, independent paper, 3
  literate non-witness readers, `quorum=2` ⇒ all 3 learn ⇒ `informed==3` ⇒
  `formed==1`.
- `test_capture_suppresses_coalition` — same, `captured=1` ⇒ story suppressed ⇒
  `informed==0` ⇒ `formed==0`. Information is a precondition of collective action.
- `test_quorum_binds` (CONTROL) — only 1 informed reader, `quorum=2` ⇒ `formed==0`
  (the count, not the mere existence of the paper, is load-bearing).

**Discipline:**
- `test_no_python_news_decision_source_audit` — no `graph_rewrite` / `gr.run` /
  `gr._match` / `gr._apply` / `make_rule` in the adapter; no `if <param>` branch
  over a decision parameter; the nine decisions are the nine seed rule names.
- `test_seeds_self_load_only_and_no_new_rust` — both seeds `self_load_only`,
  `depends_on==[]`, compose only known DSL Terms; engine provenance
  `source_match in {own, shared}` (NEVER a pinned `.so` md5, lesson 7b).

## Discipline ledger (must all hold at RESULTS time)

1. **PREREG-FIRST**: this file + the seed-claim output committed BEFORE any number.
2. **Additive-only, ONE prefix `bigville_news_`**: new files only; no tracked file
   edited; R20/R18/R19/R11 imported read-only.
3. **NO new Rust**: `git diff 59653fd443 -- runners/dsl` empty.
4. **Own-engine provenance**: `source_match in {own, shared}`; no pinned `.so` md5.
5. **Canonical shared `.so` SACRED**: md5 of
   `runners/dsl/python/substrate_rs/_native.abi3.so` unchanged
   (`fd82dc2978dbb055496dd82390ac2ebe`); never commit any `.so`.
6. **Gates run INLINE**: `pytest tests/test_bigville_news_migrated.py -q` all green;
   `test_failure_baseline_migrated` 11/11; `test_engine_provenance_migrated` 7/7.
   The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` are NOT
   run — an additive `self_load_only` rung cannot regress other suites.
7. **No `git add -A`; no `git stash`; explicit paths only.**
8. **Honest residuals reported**; no fabricated / cherry-picked numbers.
9. **Two commits (prereg, build); left on the branch; NOT merged.**

## Honest scope (stated up front)

- The noticeboard's second-channel rendering (`np_clerk_records` + a `Minutes`
  node) is RE-MODELLED locally inside the news substrate so both renderings can be
  scored against ONE ground truth in ONE fixpoint. It re-uses R20's CONCEPT (the
  clerk protects the council), not R20's seed graph — the two seeds are
  self-contained. This is a deliberate isolation choice, not a claim that R20's
  seed is loaded here.
- Each scenario uses ONE event per world instance (fresh world per scenario, R20
  style); `Resident.witnessed` is the per-event proximity outcome. Multi-event
  per-resident belief is not modelled — out of scope for this rung.
- The reporter's bias is a fixed per-story parameter (ingest), not itself derived
  from a psychology sub-model. Deriving the bias magnitude endogenously (from the
  reporter's `w_supergraph` / spite, 234) is a future rung.
