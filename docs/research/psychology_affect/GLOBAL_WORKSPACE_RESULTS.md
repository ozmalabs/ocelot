# Global Workspace — seriality PRODUCED by competition/broadcast (block 350000)

## What this closes

The consciousness / inner-speech literature review's **must-have #2** for the train of
thought (block 346) was, at the time, still open: **produce seriality via broadcast/competition with an ignition threshold (Global Workspace Theory — Baars; Dehaene), rather than ASSERT it via the FIFO agenda queue.** (The item was tracked as still-open in the earlier `ATTENTION_WIDTH_AXIS_RESULTS.md` and `APERTURE_GRAIN_TUBE_RESULTS.md`; block 350 later addressed the local mechanism.)

### The honest diagnosis of what was wrong

The block-346 train of thought **asserts** seriality by construction: the next thought is
`agenda.pop(0)` — a FIFO queue. There is exactly one thought per turn only because the
list hands them out one at a time in insertion order. There is no contest, no salience
read, no threshold. "One thought at a time" was a property of the DATA STRUCTURE, not a
produced bottleneck. Global Workspace Theory says the opposite: many unconscious candidate
coalitions run in parallel; each moment exactly ONE wins access to a single BROADCAST slot
(the workspace) via a WINNER-TAKE-ALL contest over SALIENCE; below an IGNITION THRESHOLD
nothing is broadcast (the coalition stays unconscious). **Seriality is the OUTPUT of the
contest, not an axiom of the plumbing.**

## What this block replaced

The next-thought selection changed from **agenda FIFO** to **salience competition for a
single broadcast slot**:

- **before (block 346, still the default):** `cur = agenda.pop(0)` — queue-order pick.
- **after (block 350, when the workspace strategy is wired in):** score every un-thought
  candidate by a teacher-free salience → **argmax = the broadcast winner** (the single
  serial bottleneck) → **ignition gate:** broadcast only if the winner clears the ignition
  threshold, else **NO broadcast this turn** (honest silence — the train yields rather than
  force a sub-threshold pick). **Losers stay in the candidate set** for the next turn's
  contest.

## The teacher-free salience source (why the competition is PRINCIPLED, not arbitrary)

The verify stage's mandate was explicit: if there is no teacher-free salience signal to
make the competition principled, report the negative rather than fake an arbitrary contest.
There **is** a real signal, so this block reports a positive honestly. Per candidate topic
the coalition score is a held `Plus` over these channels:

- **Learning-progress / interest (block 202000 — the principled primary).** The curiosity
  `AttentionItem`'s integer progress signal, keyed by the same topic string the agenda
  uses. Prefers the raw learning-progress RATE (`smoothed_progress`, else
  `learning_progress` — Oudeyer/Schmidhuber compression-progress, noisy-TV-resistant),
  falling back to the sustained `interest` attr. Present only for ingested topics; for a
  topic with no item the LP channel is **0** (honest absence, not a fabricated score).
- **Is-a proximity to the current focus (block 346 — the always-available floor).**
  Closeness to the focus on the is-a spine via a bidirectional BFS hop count (1 hop = most
  proximate, decaying per further hop). This keeps the competition principled even for
  candidates that have no curiosity item, because the plain is-a seed always carries it.
- **Tube membership / deviation (block 348/349 — optional).** When a `ThoughtManifold` tube
  is active, a candidate inside the tube (deviation 0) is more salient than one off it; the
  per-candidate deviation is subtracted as an inverse-salience penalty.

Where a candidate has **neither** a curiosity item **nor** any is-a relation to the focus,
its salience is 0 (honest absence) — it simply waits sub-threshold; the module never
invents a score to force a pick.

## Discrete quanta throughout (the substrate's premise — no floats decide)

Every salience channel and the ignition threshold are INTEGER QUANTA. Each channel is
snapped `k = round(x/quantum)` (clamped) via the substrate's OWN quantiser
(`analogy_search._round_to_vocab` — the same one `observer_aperture` / `attention_width`
use). The WINNER is a held `Argmax` Term over `[topic, salience_quantum]` pairs
(reusing `predictive_reading._argmax_pairs_term`) — a GRAPH-NATIVE decision, not a Python
`max()`/`sort()`. The IGNITION gate is an integer comparison of the winner's quantum
against the ignition-threshold quantum. A raw float only ever appears as an INPUT snapped
on entry; it never leaks a continuum into the decision.

The LP salience quantum is `4.0` — chosen honestly to sit at the substrate's calibrated
native resolution (`progress_floor=10`, `surprise_floor=4`) so the real single/double-digit
progress rate is visible rather than rounding to 0 (a coarse grain of 64 made
`round(6/64)=0` and silently discarded a genuine signal). The default ignition threshold is
`1` quantum ("any positive salience ignites" — the loosest honest gate); callers raise it
to demand a stronger coalition.

## Results (measured, pure graph, teacher-free) — VERBATIM

Seed: an is-a DAG (`poodle→dog→mammal→animal→organism`, `sparrow→bird→animal`). A
teacher-call spy counts external-answerer invocations. Focus `dog`; `cat` and `poodle` are
**equal-proximity siblings** (both is-a `dog`-line at proximity 3), so any salience
difference between them is the CONFIRMED learning-progress signal alone, not graph
position:

```
teacher-free salience, focus='dog' (cat & poodle are EQUAL-proximity siblings):
  cat:     LP progress=0  is-a proximity=3  =>  salience_quanta=3
  poodle:  LP progress=8  is-a proximity=3  =>  salience_quanta=5
  (equal proximity, so poodle's higher salience is the CONFIRMED LP signal)
```

| claim | statement | result |
|---|---|---|
| W1 | competition ≠ FIFO (workspace broadcasts argmax, not queue front) | **PASS** |
| W2 | ignition threshold ⇒ honest silence (sub-threshold ⇒ no broadcast) | **PASS** |
| W3 | seriality PRODUCED (one winner into the single slot; losers remain) | **PASS** |
| W4 | teacher-free held workspace path (ask-spy 0) | **PASS** |
| W5 | backward-compat (`select=None` == block-346 FIFO, identical) | **PASS** |

Verbatim experiment output (`scripts/gen_rung3_global_workspace.py`, OVERALL: **PASS**):

```
[W1] COMPETITION != FIFO
  candidate set (agenda order): ['cat', 'poodle']
  FIFO would take front:        'cat'
  workspace broadcasts argmax:  'poodle'  (quanta={'cat': 3, 'poodle': 5})
  equal proximity (3==3) => difference is the LP signal
  DIFFER: True   => W1 PASS

[W2] IGNITION THRESHOLD => honest silence
  top salience quanta=5, ignition demanded=6 -> broadcast=None (reason=sub_threshold)
  barren set ['zqvorn', 'fluxbaz'] (no LP, unrelated to focus) -> broadcast=None
  => W2 PASS

[W3] SERIALITY PRODUCED (single broadcast slot; bottleneck)
  candidates competing: ['cat', 'poodle', 'sparrow'] (scores={'cat': 3, 'poodle': 5, 'sparrow': 0})
  ONE winner into the slot: 'poodle' ; losers remain: ['cat', 'sparrow']
  => W3 PASS

[W4] TEACHER-FREE held workspace path
  workspace train topics_thought: ['poodle', 'dog', 'mammal']
  stop_reason=novelty_stalled  ask_spy=0  => W4 PASS

[W5] BACKWARD-COMPAT (select=None == block-346 FIFO)
  default    topics=['poodle', 'mammal', 'animal'] stop=novelty_stalled
  select=None topics=['poodle', 'mammal', 'animal'] stop=novelty_stalled
  identical: True   => W5 PASS
```

### The ignition-threshold = honest-silence behaviour (W2)

The ignition gate is the load-bearing honesty of GWT here. When the top salience is below
the demanded ignition quantum, or when the candidate set is barren (unrelated, no
curiosity signal — e.g. `['zqvorn','fluxbaz']`), the workspace broadcasts **None**. In the
train, `select` returning None ends the train with `stop_reason='sub_threshold_silence'`:
the workspace declined to broadcast rather than forcing a pick. This is the direct analogue
of a sub-threshold coalition failing to ignite — the substrate stays silent instead of
fabricating a "conscious" thought. (In the W4 path above the ignition is loose enough that
the train proceeds and disengages instead on the pre-existing `novelty_stalled` dynamic;
the sub-threshold-silence branch is what W2 exercises directly.)

## Backward-compatibility (byte-for-byte)

The only wiring is an additive `select=None` kwarg on `run_inner_conversation`. With the
default (`select=None`) the exact block-346 FIFO `agenda.pop(0)` path runs byte-for-byte;
the workspace competition only engages when a strategy is passed. W5 confirms identical
topics and stop-reason. The block 346/347/348/349 experiments were re-run and produce
**byte-for-byte identical** output with the `select=` hook present vs. HEAD (same
`SUMMARY_JSON`, same stop-reasons, same exit codes, ask-spy 0) — the hook introduces no
regression on the default path. (Those experiments' own pre-existing partial/deferred
verdicts — e.g. block 346 C4/C6 deferred, the regulated-manifold and aperture-grain claims
awaiting their richer seeds — are unchanged by this block and are documented in their own
results files; they are not regressions from block 350.)

## Remaining plan — historical note

The original “next block” wording below is superseded by the landed block-351 work. The global-workspace result remains a local, opt-in mechanism result; gated dimension-minting is documented in `GATED_MINTING_RESULTS.md` and evaluated in the capability suite. Neither result establishes graph-native production ownership, general agency, P5 transfer, or trusted custody. The next production-facing work is governed by `THOUGHT_MANIFOLD_PRODUCTION_PLAN.md`, especially its Python-control-loop architecture gate.

## Guardrails (all green)

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only — no Rust rebuild).
- Protected READ-ONLY files untouched (`runners/dsl/src/can_ops.rs`,
  `domains/can_junction_tree.py`, `domains/can_native_bp.py`, `domains/model_reader.py`).
- `domains/conceptualizer.py` untouched — the no-Python-decision audit
  (`tests/test_conceptualizer.py::test_no_python_decision_source_audit`) stays green.
- Teacher-free (no LLM; ask-spy 0 on the held path). Additive only. Discrete quanta
  throughout (held `Argmax` Term + `_round_to_vocab`). Nothing under `/applications`.
- Committed block-350 files only, staged by name (`git diff --cached --stat` confirmed).

## Artifacts

- `domains/global_workspace.py` — the Global Workspace: `salience_quanta` (teacher-free
  coalition score, held `Plus` over LP + is-a proximity − tube deviation, snapped to
  integer quanta), `broadcast_winner` (held `Argmax` over `[topic, salience_quantum]` pairs
  + ignition gate → honest silence), `workspace_select` (the `select=`-compatible strategy).
- `domains/train_of_thought.py` — the additive `select=None` kwarg on
  `run_inner_conversation` (default preserves the block-346 FIFO byte-for-byte; a strategy
  drives competition/broadcast, None ⇒ `stop_reason='sub_threshold_silence'`).
- `scripts/gen_rung3_global_workspace.py` — the experiment (W1–W5, teacher-call spy).
