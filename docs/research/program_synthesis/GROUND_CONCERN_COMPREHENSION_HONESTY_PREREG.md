# `ground_concern`'s comprehension composer — closing the unconditional terminal
# fallback A25 measured, or naming precisely why it can't close — PREREG

**Date:** 2026-08-11.
**Base commit:** `4563c3a` (`main`'s tip at start — verified via `git log
--oneline -1 main`), detached worktree `/home/matt/ocelot-ground-concern-honesty`,
branch `ground-concern-honesty` (created after this registration).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
(the committed `runners/dsl/python/substrate_rs/_native.abi3.so`), copied via
git checkout into this worktree and verified resolving from inside it.
Coherence probe passed before any measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Prior work this follows up:**
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_PROGREAD_SELFIMPROVE.md`
(amendment A25, merged onto `main` in the immediately-preceding commit,
`0e62166`). A25 fixed `prog_read`'s OWN promotion path by intercepting it
*before* it reaches `ground_concern` — it explicitly named the root cause
(the composer's own unconditional terminal fallback) as out of scope for that
rung. This document is that follow-up.

**Doc home, decided and justified.** CLAUDE.md names `docs/research/
agent_loop/` as the composer/driver migration's historical home, but a grep
sweep (`grep -rl "ground_concern\|composer_dispatch\|_compose_comprehension_
rule" docs/research/`) finds **zero** hits under `agent_loop/` — that
directory's ~70 files are almost entirely audio/speech/representation
iteration logs from an earlier arc, not composer-dispatch material — against
**5 hits** under `program_synthesis/` (including A25 itself and the
investigation A25 answered) and one legacy hit under the explicitly
OFF-LIMITS `engine_substrate/`. `program_synthesis/` is where this exact
mechanism's live paper trail actually lives; this doc stays there, as A25's
direct sequel.

---

## 0. The bug, exactly as A25 measured and named it

`domains/reflective_faculty.py::_compose_comprehension_rule` (starts line
1780) has three branches reached in order from `ground_concern`'s dispatch:
`"find X near Y"` (gated on `"find" in rp and "constrain" in rp`), `"find X"`
(gated on `"find" in rp`), and a **terminal block, lines 1903-1922, with NO
`if` guard at all** — it always installs a rule named
`comprehend_describe_directive_<tag>` (matching literal Mention text
`"describe"` about a `Scene` node) and returns `{"grounded": True, ...}`,
regardless of what the concern's own grounded relations (`rels`/`rp`) say.
A25 measured this installing a dead, never-firing rule for a `prog_read`
concern and reporting false success with zero record of the mismatch
anywhere.

**Task:** find the gate that lets the terminal branch fire *only* for
concerns genuinely about describing a perceived scene, mirroring the
existing `if "find" in rp:` pattern, OR determine precisely why that can't
be done safely and report the block — CLAUDE.md's own standing culture
treats a well-characterized NO-GO as a complete result, not a shortfall.

---

## 1. Bars

**AR-H-a — locate the discriminating signal, or prove none exists.**
Determine what, if anything, in the data available to
`_compose_comprehension_rule(agent, keys, rels)` (i.e. `keys` and the
grounded relations `rels`/`rp` — the SAME two arguments the `"find"` gate
already uses) distinguishes a concern genuinely about describing a
perceived scene from a `prog_read`-shaped (or any other) unrelated concern
that also grounds only to `"comprehend"`. Method: construct/find a real
fixture for (i) the canonical genuine describe-scene concern
(`scripts/arc_self_report.build_describe_faculty`'s own `induce_concern`
call — this IS the rule's origin case), (ii) at least one other real,
currently-tested caller that reaches the SAME terminal branch for a
DIFFERENT purpose (`domains/recount_faculty.py::build_recount_faculty`,
whose own module docstring already flags this branch as
content-word-independent), and (iii) a `prog_read`-shaped concern mirroring
A25's own measured `StandingConcern.relations`. Run all three live through
`induce_concern`→`ground_concern` (real `WorldAdapter`, `load_all_seeds`, no
mocks) and diff their `rels`/`rp`/`grounded_relations`/`observation`
payloads at the point `_compose_comprehension_rule` actually receives them.

**AR-H-b — GO/NO-GO on the gate, decided from AR-H-a's measurement, not
assumed.** GO iff a discriminator exists in data ALREADY available to the
function (or trivially, safely threadable to it) that separates (i)/(ii)
from (iii) without relying on caller-chosen naming (a `keys`/tag string
match would be a fragile heuristic on an arbitrary caller-supplied label,
not a held-vocabulary gate — the SAME kind of ad hoc knob CLAUDE.md's
"SHAPES, NOT NUMBERS" section already names as the standing failure mode).
NO-GO if the only available data is provably identical across (i)/(ii)/(iii)
— i.e. any gate that walls off (iii) also walls off (i) or (ii).

**AR-H-c — caller-safety survey.** For every caller of `ground_concern`
found by `grep -rl "ground_concern" domains/*.py scripts/*.py`
(pre-registered expectation: `reflective_faculty.py` itself,
`conceptualizer.py`, `consumption_quality.py`, `conversation_action.py`,
`substrate_extension.py`, `speech_enrollment.py`,
`scripts/jabberwock_daemon.py`, `scripts/arc_self_report.py`,
`domains/recount_faculty.py`), read how each handles the return value —
does it branch on `grounded`, or discard the return value and rely on the
INSTALLED-RULE side effect? This determines who is exposed to a behavior
change if AR-H-b is GO.

**AR-H-d — fix + live-demonstrate, if GO; else block precisely, if NO-GO.**
GO: implement the minimal gate (mirroring `if "find" in rp:`'s exact style),
demonstrate live that (i)/(ii) still succeed unchanged and (iii) now returns
an honest `{"grounded": False, "wall": ...}` instead of installing a dead
rule. NO-GO: name the exact mechanism blocking it (not just "it's risky") —
with live evidence, not reasoning alone (e.g. temporarily apply the most
plausible candidate gate, run the real test suite, capture the concrete
failure, then revert before final commit).

**AR-H-e — full regression, broad, node-id lists not counts.** Every test
file touching `reflective_faculty.py`/`ground_concern`/
`_compose_comprehension_rule`/`induce_concern`, found via
`grep -rl "ground_concern\|_compose_comprehension_rule\|reflective_faculty"
tests/`, run before and after (before==after if NO-GO and no code changes
land — the bar is then "the current green baseline this fix would need to
hold, and the specific tests that prove why a naive gate can't").

---

## 2. What is explicitly NOT in scope

Per the task brief: `seeds/arc_executor.json`, `seeds/arc_goals.json`,
`seeds/arc_magnitude.json`, `seeds/arc_decompose.json`,
`seeds/goal_residuals.json`, `tools/build_arc_*.py`,
`domains/prog_read_growth.py`, `scripts/jabberwock_daemon.py`'s
`_process_prog_read_standing`/`_process_code_write_standing` (A25's own
just-landed fix), `runners/dsl/src/`, and the `theory_convergence`/
`adventure_mechanics`/`engine_substrate`/`flight_control` doc trees. A
change to `induce_concern`'s own residual/coverage computation (as opposed
to the `_compose_*_rule` builders) is a DIFFERENT, larger class of change
than this rung is scoped for — CLAUDE.md sanctions the seven
`_compose_*_rule` builders as legal Python because they "only assemble Rule
JSON"; `induce_concern` is core dequantize-loop machinery, not a builder,
and touching it is out of this rung's declared shape even if AR-H-a's
measurement points there.
