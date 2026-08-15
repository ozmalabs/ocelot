# Nature mining (non-cognition) — investigation plan

Companion to `NATURE_MINING_RESULTS.md` (read that for the findings; this
file registers scope and method before the findings existed).

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/nature-mining`, branch
`nature-mining-investigation`, detached from `main` at `fff8555` (checked
fresh immediately before worktree creation — `git log --oneline -1 main`
returned `fff8555` both at task start and at worktree creation, no drift).

## Why this rung exists

A same-day sibling conversation connected DNA/RNA/protein biology to this
project's architecture and found several load-bearing parallels (codebook
vs. decode = archive vs. execution; wobble-position redundancy = a real bug
in `CapabilityAxis` identity; frameshift catastrophe = the already-central
"in-frame is integer" invariant; alternative splicing = "transform in the
existing basis"; folding/chaperones = `run_rules()`'s fixpoint +
`multi_start_settle_and_pick_best`; layered proofreading = the
gap-awareness → self-improvement pipeline) — and ONE explicitly REJECTED
parallel (junk DNA / exaptation does not transfer, because biological
deletion has a cost `git log` does not have). That conversation is the
calibration for THIS rung, not a lower bar: every finding here must name a
specific file/function/mechanism it connects to, not a thematic resonance,
and a well-localized null is exactly as valuable as a hit.

This rung's scope is everything else in nature — immune systems, stigmergy,
mycorrhizal networks, homeostasis/allostasis, morphogenesis, symbiosis — per
the orchestrator's brief. Cognition/genetics is out of scope (already
covered). `runners/dsl/src/shape_decode.rs` / `CapabilityAxis` identity and
`domains/solver_dispatch.py` are OUT OF SCOPE regardless of relevance — two
sibling agents own those files this session.

## Method

For each candidate system:

1. State the biological mechanism precisely (what it actually does, not the
   popular-science gloss), with a real citation where one is easy to hand.
2. Read the actual current code/seed for the analogous mechanism in this
   repo — not assumed from memory, not from `CLAUDE.md`'s summary alone.
3. Ask directly: does the biological version suggest something CONCRETELY
   DIFFERENT from what's there — a real design correction — or is it a
   poetic label for something already correct? Or does it fail to transfer
   at all, and why (name the real constraint that breaks it, the way the
   junk-DNA/exaptation rejection did for the sibling rung)?
4. Check `/home/matt/ozmadev/internal` (the private companion repo carrying
   the user's own prior theory) for whether this connection already exists
   in the theory papers, so novelty is measured against the right target.

Rank findings by consequence × confidence / cost, `SHAPE_AUDIT.md` §8's own
method. Report rejected parallels with the same weight as hits.

## Candidates surveyed

- Immune systems (clonal selection / affinity maturation / memory cells) vs.
  the gap-awareness → `experiment_dispatch.py` → adopt loop and the sd-loop
  codebook's recognize/mint split.
- Stigmergy (pheromone deposit + evaporation) vs. this project's own
  surprise-gated decay primitive (`seeds/staleness_decay.json`) and vs. the
  session's own concurrent-background-agent coordination pattern (shared
  `main`/docs, no direct messaging).
- Mycorrhizal resource-sharing networks vs. `domains/gap_prioritiser.py`'s
  frontier-guided axis selection and the quanta-navigation flood
  (`runners/dsl/src/space_quantize.rs`).
- Homeostasis vs. allostasis vs. the `feedback_control` /
  `prediction_minus_observation` meta-shape pair already named in
  `seeds/seven_meta_shape_subsystems.json`, checked against a real
  consumer (`seeds/staleness_decay.json`'s surprise-gated half-life).
- Embryonic morphogenesis (positional information, reaction-diffusion) vs.
  `run_rules()`'s local-rule-to-global-fixpoint shape and the quanta flood.
- Symbiosis/endosymbiosis (when do two organisms fuse vs. stay coupled-but-
  separate) vs. the "same pattern, own cache — no cross-import" convention
  used verbatim in `domains/analogical_thinking.py`,
  `domains/reflective_faculty.py`, `domains/solver_dispatch.py`.

## Build bar

This is primarily an ideation/investigation task. A build is warranted only
if a finding is clear-cut, cheap, narrow, and low-risk — the same bar the
sibling wobble-position finding cleared. A finding that requires touching
Γ-production generation, the composer/experiment dispatch decision surface,
or anything resembling a new scalar knob (explicitly disallowed by
`CLAUDE.md`'s "SHAPES, NOT NUMBERS" rule) is named, not built, regardless of
how compelling the analogy is. A purely analytical result with nothing built
is a complete, valid outcome.
