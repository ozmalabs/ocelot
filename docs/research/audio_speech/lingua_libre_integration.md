# Lingua Libre — gateless multilingual pedagogical teaching voice (integration)

Wiring **Lingua Libre** (lingualibre.org, the Wikimedia project of recorded
isolated-word/phrase pronunciations — free, CC, many languages, many speakers,
**no access gate**) into the self-directed speech world as a REAL pedagogical /
L2-teaching-voice source. It is the gateless, multilingual version of the clear
pronunciation-model register (the "second-language-learning material") that the
PARENT can utter instead of synthetic espeak.

This complements `docs/research_pedagogical_corpora.md` (which surveyed
gated/aligned corpora — LUCID, CHILDES, L2-ARCTIC). Lingua Libre wins on the one
axis those lose: **no gate, isolated-words out of the box, many languages**.

---

## (1) Access path — VERIFIED LIVE + subset FETCHED

**Endpoint (verified working, 2026-06):** `https://lingualibre.org/sparql`
(Blazegraph, ~78.9M triples; the documented `lingualibre.org/wiki/...` pages now
301-redirect to an archived read-only mirror, but the **SPARQL service and the
Commons audio are fully live**).

**Data model (verified by probing records):** each Record item has
- `prop:P4` → language entity (`Q22`=English, `Q21`=French, `Q24`=German, `Q386`=Spanish)
- `prop:P7` → transcription (the spoken word, a literal string)
- `prop:P5` → speaker (an entity; the person who voiced it)
- `prop:P3` → audio file: a **Commons `Special:FilePath` URL**, real **16-bit PCM
  WAV** (mono, 44.1 kHz). **Not ogg** — no transcode-from-ogg needed, just resample.

The audio is fetched by plain HTTP from `commons.wikimedia.org/.../Special:FilePath/...`
(HTTP 200, `audio/x-wav`). No API key, no login, no rate-gate hit at this volume.

**Fetched subset** (`scripts/fetch_lingua_libre.py`, the offline world-prep tool):
the digit words `zero..nine` per language, in en/fr/de/es, resampled to 8 kHz mono
16-bit and written `{word}_{speaker}_{idx}.wav` into
`~/.cache/ozma/lingualibre/<lang>/` (out of git, like `/tmp/fsdd`).

| lang | clips | distinct speakers | notes |
|---|---|---|---|
| en (Q22) | 88 | 19 | `one`/`two` 15 spk; `zero` only 2 |
| fr (Q21) | 285 | 57 | richest — `deux`/`trois`/`quatre`/`cinq` 44–45 spk; **no `zero`** (French uses "zéro"; LL has it under a different transcription, not fetched) |
| de (Q24) | 71 | 13 | `eins`..`vier`/`fünf` ~10 spk; `null` only 1 |
| es (Q386) | 35 | 11 | thinnest — most words 2–7 spk; `cero` only 1 |
| **total** | **479** | — | ~5.1 MB on disk |

Full per-word coverage is in `/tmp/ll_coverage_run.txt`
(`python3 scripts/fetch_lingua_libre.py --report`).

---

## (2) Loader + pedagogical render branch (donkey-clean)

### Loader (mirrors `fsdd_index`), in `domains/self_directed_speech_world.py`:
- `ll_index(lang)` → `{word: [path, ...]}` (covered words only)
- `ll_index_for(speakers, lang)` → LOSO-scoped `{word: [path]}` (filename filter)
- `ll_speakers(lang)` → `[speaker, ...]` for the held-out split
- `ll_available(lang)` → bool
- `load_ll_clip(path)` → `(audio float32, fs)` (8 kHz; defensive resample)

The speaker is encoded in the filename (`{word}_{speaker}_{idx}.wav`, speaker =
the LL entity Q-id lowercased), so `ll_speakers`/`ll_index_for` are **pure filename
filters — the IDENTICAL LOSO mechanic to FSDD**. All five are mechanical I/O reads.

### Render branch, in `domains/parent_teacher.py`:
- `ped_clip(word, lang, held_speakers=None, rng=None)` → a REAL Lingua Libre
  clear-speech clip for the word (excluding held-out speakers), or `None` if the
  corpus lacks the word.
- `parent_say(word, lang, register="IDS", held_speakers=None, use_real=True)` — for
  the **scaffold (IDS) register**, draws a real LL clip when the word is covered;
  **espeak IDS is the fallback** for uncovered words. `recast_clip` / `bank_recast`
  thread `held_speakers` / `use_real` through.

**The `REGISTER_GATE_TERM` graph decision is UNCHANGED** — it still chooses
scaffold (IDS) vs test (ADS) register by the agent's held-out rate. Only the
*renderer for the scaffold register* swaps from synthetic-IDS to real-clear-speech.

### Donkey boundary (audited clean):
- The corpus is the **WORLD's teaching speech** — the parent SPEAKS a real
  recording (world I/O); the agent grounds + recognises it, never inverts it.
- **Held-out speakers are excluded from `ped_clip`** (the `held_speakers` filter),
  so teaching clips never leak the cross-speaker held-out probe's speakers.
- No recognition, no decision-over-graph-state, no rule-engine call was added to
  Python. The render branch is a mechanical "covered? real : espeak" at the I/O
  boundary (the same shape as the existing espeak/Piper renderer selection).
- Multilingual = the polyglot: en/fr/de/es teaching voices in one cache.

---

## (3) Quick end-to-end verify (real clips → teach → held-out recognise)

`/tmp/ll_e2e_run.txt` (re-run: `PYTHONPATH=. python3 /tmp/ll_e2e.py`):
- **Loader** returns real clips for all 4 languages (8 kHz, non-empty).
- **Render branch**: `parent_say("four","en",IDS)` returns a **real** LL clip
  (8288 samples) not espeak; an uncovered token falls back to espeak; `ped_clip`
  returns `None` for uncovered, a clip for covered.
- **Real multilingual LOSO** (French, the agent's cochlear front end + 1-NN over
  banked exemplars, **held-out speakers never banked**): 57 speakers split
  46 train / 11 held → **23/49 = 46.9% on 8 words (chance 12.5%)**. A genuine
  cross-speaker held-out result on real recordings, far above chance.

Required suites green: `test_stt_pipeline` (verified), `test_gap_guidance`
(verified) — 10 passed.

---

## (4) HONEST assessment

- **Coverage.** All four languages have most digit words with multiple speakers.
  **French is genuinely LOSO-grade** (57 speakers, 44–45 per common word). English
  and German are usable (13–19 speakers) but thinner per word. **Spanish is thin**
  (11 speakers, several words at 2–3) — enough to prototype, marginal for a clean
  Spanish-only LOSO. Two gaps: French `zero` (LL stores "zéro"/other transcription,
  not fetched here) and several languages' `zero`/`null`/`cero` have only 1–2
  speakers. So **espeak must stay the fallback** for uncovered/thin words — wired.
- **Format / quality.** Real 16-bit PCM WAV, mono, originally 44.1 kHz, resampled
  to 8 kHz mono — exactly the FSDD format, drops straight into the cell grid. These
  are **citation-form clear pronunciations** (volunteers reading words), i.e. the
  over-enunciated dictionary register — the clear pronunciation-model the
  doc's §1 catalogued, NOT instructed-hyperarticulation (LUCID) nor conversational
  IDS (CHILDES). Crowd-recorded → some channel/level variability (real, useful).
- **Speaker counts / multilingual LOSO.** French alone supports a real
  speaker-invariant held-out probe (the central perception problem). en/de support
  a weaker LOSO; es is prototype-grade. **Aggregate, it IS enough for a real
  multilingual teaching-voice + a French-grade cross-speaker held-out yardstick**;
  to scale, widen the fetched vocabulary beyond digits (LL has large word lists per
  language) — the loader + render branch already generalise to any word the cache
  contains (`ll_index` keys are whatever was fetched).
- **vs the §1 survey.** Lingua Libre beats LUCID/CHILDES/L2-ARCTIC on access
  (gateless SPARQL + Commons, no email, no ELRA, no MFA), isolation (per-word files,
  zero forced alignment), and language breadth — at the cost of register (citation
  pronunciation, not instructed clear-speech) and per-word depth.

**License:** CC (Lingua Libre recordings are CC-BY-SA / CC0 per speaker on
Commons); non-commercial-safe for research; keep the cache out of git (it is, in
`~/.cache/ozma/lingualibre`). Cite Lingua Libre / Wikimedia France.

---

## Files

- `scripts/fetch_lingua_libre.py` — offline world-prep: SPARQL query + Commons
  fetch + 8 kHz resample → `{word}_{speaker}_{idx}.wav` cache. `--report` for
  coverage, `--limit-per-word N` for a smaller subset.
- `domains/self_directed_speech_world.py` — `ll_index` / `ll_index_for` /
  `ll_speakers` / `ll_available` / `load_ll_clip` (+ `__all__`).
- `domains/parent_teacher.py` — `ped_clip` + the real/pedagogical render branch in
  `parent_say` / `recast_clip` / `bank_recast`.

Captured runs: `/tmp/ll_coverage_run.txt`, `/tmp/ll_e2e_run.txt`, `/tmp/ll_fetch.log`.
