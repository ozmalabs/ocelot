# PREREG — block 296000: the publisher WRITES prose from held beliefs (Rung D)

`NEWSPAPER_WRITER_PLAN.md` **Rung D** — the flagship, and the close of the chain.
The publisher writes the newspaper by RENDERING his held beliefs as prose, and
bias/capture become WORD choices. This replaces the Python f-string headline with
graph-native prose, and makes the free-vs-captured result legible as words.

## What this delivers (graph data + rules)

Built on the full chain (report → hold), with the `bigville_write` seed:

- For each Fact the publisher `knows` (Rung C), a `Story` is minted whose `text`
  is a `StringConcat` term over the fact's structured fields
  (subject / event / place / patron) — the engine renders the sentence; no Python
  f-string builds it.
- Framing is capture-gated: `write_free` and `write_captured_ordinary` render the
  FULL sentence (naming the patron — the cause clause); `write_laundered` (a
  captured paper on a `damaging` story) renders the SAME held fact WITHOUT the
  patron clause.

## Gates (pass/fail, pre-registered)

1. **G-rendered-not-fstring (source audit):** the story `text` is produced by a
   `StringConcat` in the seed; the world adapter contains no f-string / `%`/
   `.format`/`join` building a headline. Python supplies the held meaning; the
   surface is the engine's.
2. **G-names-held-actors:** the rendered prose contains the subject (and, when
   free, the patron) taken from the HELD fact — it writes about what it holds.
3. **G-free-vs-captured (HEADLINE / flagship):** over the SAME held fact, a free
   paper and a captured paper produce DIFFERENT prose — the free text contains the
   patron's name (the cause clause); the captured text does NOT — while
   subject/event/place are identical. The bias is in the WORDS, not a scalar.
4. **G-capture-is-targeted:** a captured paper still prints a NON-damaging story in
   full (patron clause present) — capture launders only the damaging story.
5. **G-only-what-is-held:** the paper prints stories ONLY about facts the publisher
   KNOWS. A fact never delivered and never witnessed (a rumour) is never printed —
   no confabulation reaches the page (inherits Rung C's anti-confabulation).
6. **G-falsifier:** if the laundered render still named the patron, G-free-vs-
   captured would fail — the gate is non-vacuous (asserts the captured text
   OMITS the exact patron string the free text contains).

## Scope / honesty

- This is the demonstrator chain (report→hold→write), gated end to end. Folding it
  into the live `integ3` town — deleting the `_print_paper` scalar crush and the
  f-string headline there, and driving the weekly paper from the reporter's
  actually-held beliefs — is the fold-in rung (the 289000 precedent), NOT this
  block. The integ3 f-string still exists until then; this block proves the
  replacement works.
- Isolated demonstrator + seed + test; no Rust; `.so` untouched. The render is
  the existing `StringConcat` Term (no new primitive).
- The fact's structured fields (subject/event/place/patron) are ingested by the
  adapter here; in the fold-in they will be read off the town's real conduct spine
  (who evicted whom, from the Conduct nodes) rather than hand-supplied.
