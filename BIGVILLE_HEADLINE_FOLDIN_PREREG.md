# PREREG — block 297000: fold the rendered headline into the LIVE town

`NEWSPAPER_WRITER_PLAN.md` fold-in. The demonstrator chain (Rungs A–D, blocks
293000–296000) proved the writer end to end in isolation. This block lands the
core of it in the LIVE `integ3` town: the weekly newspaper HEADLINE is now
RENDERED from the week's REAL event's structured fields (StringConcat), replacing
the Python f-string `"week %d: %d passings, %d without a roof"`.

## The defect removed

`bigville_integ3_world.py` built the weekly headline as a Python f-string over
counts. The prose was authored in Python, not by the graph — the plan's headline
defect, in the live town.

## What replaces it (additive; existing behaviour preserved)

- New seed `bigville_headline.json` (self_load_only, loaded explicitly in
  `_install_press`): 3 render rules that set the Story's `text` via `StringConcat`
  over the story's structured fields (subject / event_verb / place / patron).
  `hl_render_full` names the patron; `hl_render_plain` renders a story with no
  patron (a death); `hl_render_laundered` drops the patron for a CAPTURED paper on
  a DAMAGING story.
- `_print_paper` gains an optional `story_fields` dict; it sets the fields on the
  Story, `_run()` renders the text, and the paper record's `headline` becomes the
  RENDERED text (read off the graph). Absent `story_fields`, the legacy string
  path is byte-unchanged.
- The weekly call site derives ATOMIC held tokens from the REAL event: a death
  leads with the dead resident's real `name` (from `death_log`) and a
  kind-selected verb; else a homelessness story that names the council as patron.
  The SENTENCE is assembled by the render rules, never in Python.

## Gates (pass/fail, pre-registered)

1. **G-headline-rendered (HEADLINE):** after a live run, the weekly `headline` is
   rendered prose — a full sentence ending in ".", NOT the old
   `"week N: … passings …"` template. The `%`-format headline string never
   appears.
2. **G-real-name:** when a death occurred that week, the headline contains the
   dead resident's real name from `death_log` (the paper writes about a real held
   event, by name).
3. **G-free-vs-captured (flagship, live):** on the same damaging (homelessness)
   story, a free paper NAMES the patron ("the council") and a captured paper
   OMITS it — different prose, same event, in the live town.
4. **G-no-python-prose (source audit):** the weekly call site builds no
   sentence — no `"week %d…" %` f-string, no `.format` assembling the headline;
   the headline is the graph-rendered `text`.
5. **G-existing-green (regression):** every existing integ3 / news / integ
   migrated gate stays green (the fold-in is additive; the scalar `content` /
   printed / suppressed / informed propagation is byte-unchanged).

## Scope / honesty

- This lands the RENDERED HEADLINE from real content + the free-vs-captured
  launder in the live town. It does NOT yet route the reporter's TRAVEL + HOLD
  (Rungs B/C) into integ3 — the live paper's fields are read mechanically off
  `death_log`/homelessness (a sensor read), not yet delivered by a walking
  reporter and held as a belief. That deeper fold-in (reporter walks, holds,
  writes only what he holds) is a further step; this block replaces the f-string,
  which was the plan's headline defect.
- Honest residual: the homelessness story says "Several families" (not the exact
  count) because rendering a NUMBER as prose in the graph is a further step (and
  is exactly the column-writer's territory); the death story carries the exact
  real name. No number is Python-formatted into the prose.
- No Rust; `.so` untouched. Additive to a load-bearing world; all prior gates
  verified green before and after.
