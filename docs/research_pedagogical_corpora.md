# Pedagogical / teaching-speech corpora — what is actually downloadable with audio

Reconnaissance for wiring a **real recorded teaching voice** into the self-directed
speech world, to replace/augment the PARENT's *synthesised* child-directed speech
(`domains/parent_teacher.py`: espeak `-s`/`-p` register-gating). The goal is the
genuine pedagogical signal — hyperarticulated / slowed / clear speech with key words
stressed and hard bits simplified — as a new corpus source loader alongside
`fsdd_index` / `tts` / `piper_tts` in `domains/self_directed_speech_world.py`.

**No build. No download of large data. No commit.** Every access/format claim below
was checked against the live web (sources at the bottom); claims I could not verify
are flagged HONESTLY.

---

## (1) The corpora — VERIFIED access + format

The world's source contract (from the loaders, verified in code): a loader returns
`{word: [path, ...]}` (`fsdd_index`); clips are read by `_read_wav` (16-bit PCM WAV)
and resampled to **8 kHz mono** (`_TARGET_FS = 8000`, ffmpeg or linear interp); FSDD
encodes the speaker in the filename (`{digit}_{speaker}_{idx}.wav`) so a
**leave-one-speaker-out** held-out probe is just a filename filter (`fsdd_index_for`,
`fsdd_speakers`). A new pedagogical source must reduce to the same shape: per-word
clip lists, isolated-word audio, speaker tracked for held-out.

| Corpus | Size / speakers | Access (verified) | Format (audio? transcript? alignment? fs?) | Pedagogical features present? |
|---|---|---|---|---|
| **CHILDES / TalkBank** (incl. **Brent**, Providence) | 436 corpora, 48 languages; Brent = preverbal infants 9–15 mo, English-speaking mothers, ~14 sessions/pair; Providence = 6 children 1–3 yr, ~363 h A/V | **FREE, CC BY-NC-SA 4.0**, but **requires a (free) TalkBank account** (green Login). Transcripts: per-corpus **.zip** download. Media: **"Link to Media Folder"** → download files **one by one** (slow). **Only ~25% of CHILDES is media-linked** — most corpora are transcript-only. Brent IS audio-linked ("all transcripts completely linked to the audio"). | **Audio (.mp3/.wav/.mp4) + CHAT transcripts**, utterance-level time-linked (CHAT bullets); media fs varies (resample needed). **No isolated-word audio** — continuous spontaneous CDS; word-level isolation needs **forced alignment**. | **YES — this IS real CDS/IDS.** Brent = *infant-directed* (preverbal), the genuine motherese register. But it is **conversational/continuous**, not deliberately hyperarticulated read speech. |
| **LUCID** (London-UCL Clear speech In Dialogue, Hazan/Baker) | **40 native S. British English speakers** (20 pairs), 18–29 yr; ~170 min/speaker (110 spontaneous + read + semi-spontaneous) | **FREE for non-commercial research**, distributed via **Speechbox @ Northwestern**; contact v.hazan@ucl.ac.uk to report usage. No fee found; registration/contact, not an open direct link. | **Stereo WAV** (dialogue) + **individual per-speaker WAV**; **word-aligned orthographic transcripts (Praat TextGrids)**. Sample rate not stated on the page (lab studio → likely 44.1/48 kHz; resample to 8 kHz). | **YES — strongest clear-speech.** Explicit *"speak clearly as if to someone hearing-impaired"* + babble-barrier conditions → **hyperarticulated, reduced coarticulation, expanded vowel space**. The clear-vs-casual contrast is the corpus's whole design. |
| **ALLSSTAR / Speechbox** (Northwestern, OSCAAR) | ~90,000 audio files, many talkers/languages; L1+L2 scripted + spontaneous | Web platform **https://speechbox.linguistics.northwestern.edu/**; browsable, WAV. Per-file download terms not granular in search — **VERIFY on the interface** before relying. | **WAV** + scripted transcripts (read sentences/lists). | PARTIAL — L2 + read-list material (clear-ish), but not a *deliberate-teaching* register like LUCID; it's an archive, not a clear-speech paradigm. |
| **L2-ARCTIC** (TAMU PSI Lab) | **10+ non-native speakers** (Hindi/Korean/Mandarin/Spanish/Arabic, M+F), ~1 h each, ~1132 sentences | **FREE, CC BY-NC 4.0.** Direct download after agreeing to license + entering name/email/affiliation (https://psi.engr.tamu.edu/l2-arctic-corpus/). Clean, no ELRA. | **WAV** + **orthographic + force-aligned phone transcripts** + word-level + ~150 manually-annotated utts/speaker. | PARTIAL — *non-native read* speech, NOT teaching/clear speech. Useful as a *hard learner-accent source* (like a harder FSDD), **not** as the parent's teaching voice. |
| **ISLE** (German/Italian learners of English) | 23+23 intermediate L2 speakers, ~18 h, 250 utts | **PAID, via ELRA/ELDA** (catalogue ELRA-S0083). License + cost barrier; not free. | WAV + word- and phone-level annotation (pronunciation errors). | NO (learner errors, not teaching speech). Behind a paywall — skip. |
| **Forvo** (crowd pronunciations) | ~6M audio, 430+ languages, **isolated words** | **API**: free tier 500 req/day; **$2/yr non-commercial**. Audio licensed **CC BY-NC-SA** (license history is contested — see flags). | **Per-word audio** (MP3), already isolated — *no alignment needed*. Crowd-recorded, variable fs/quality, many speakers/word. | PARTIAL — isolated **dictionary-pronunciation** words (clear, citation-form, careful) — the *over-enunciated pronunciation-model* category. But casual crowd recordings, not a controlled clear-speech register; licensing murky. |
| **KIDS** (Konstanz prosodically-annotated IDS) | German IDS, prosodically annotated | Found only via paper/d-nb record; **no verified open download** — likely on-request from authors. | IDS audio + prosodic annotation (German). | YES (true IDS) but **access unverified** and German-only — deprioritise. |

**Honest cross-cutting facts (verified):**
- CHILDES is **mostly transcript-only**; the audio you actually need is the **~25%**
  that is media-linked. Brent (and Providence) are in that 25% — confirm per-corpus.
- **None of the CDS/IDS corpora give isolated taught words.** They are continuous
  spontaneous dyadic speech. Getting per-word clips requires **forced alignment**
  (e.g. Montreal Forced Aligner on the CHAT/TextGrid transcript) then cutting.
- **LUCID and L2-ARCTIC already ship word/phone alignment** (TextGrids / force-aligned
  phones) — so the segmentation burden there is *much* lower than CHILDES.
- The one source that is **isolated-word out of the box** is **Forvo** (per-word
  pronunciation audio), at the cost of crowd variability + a contested licence.

---

## (2) Integration plan — a pedagogical source loader

The donkey boundary is **unchanged and already correct** in `parent_teacher.py`: the
corpus is the **WORLD's teaching speech** (the parent SPEAKS, via a real recording
instead of espeak); the **agent GROUNDS** (its own `blind_guess` over its own
exemplars, its own front end). The held-out yardstick stays ungameable. A real-voice
parent only swaps *what audio the parent utters* — it touches no recognition.

### 2a. The new source, mirroring `fsdd_index`
Add a loader in `domains/self_directed_speech_world.py` that returns the same
`{word: [path, ...]}` shape, plus a speaker-scoped variant for held-out:

```
ped_index()                 -> {word: [clip_path, ...]}     # all taught clips
ped_index_for(speakers)     -> {word: [clip_path, ...]}     # LOSO train/probe split
ped_speakers()              -> [speaker, ...]               # for held-out-speaker probe
ped_available()             -> bool
load_ped_clip(path)         -> (audio float32, fs)          # _read_wav + resample to 8k
```

Reuse the existing `_read_wav` + `_resample_to_target` / ffmpeg path (the FSDD loader
already resamples non-8 kHz clips). Encode `{word}_{speaker}_{idx}.wav` filenames in
the preprocessed cache so `ped_speakers()` / `ped_index_for()` are pure filename
filters — **identical mechanic to FSDD's LOSO**, so the cross-speaker held-out probe
is free.

### 2b. The parent uses it as its teaching voice
In `parent_teacher.py`, `parent_say()` / `recast_clip()` currently call espeak (IDS)
or `W.tts` (ADS). Add a register `"REAL"` (or fold into `"IDS"`) that, **when the
taught word exists in the pedagogical corpus**, draws a *real* clear/CDS clip for that
word instead of synthesising. Keep espeak as the fallback for words the corpus lacks
(LUCID/CHILDES cover a small vocabulary, not the full lexicon). The register-gating
graph Term (`REGISTER_GATE_TERM`) is **unchanged** — it still chooses scaffold-register
vs test-register by the agent's held-out rate; only the *renderer* for the scaffold
register changes from synthetic-IDS to real-clear-speech.

### 2c. Preprocessing pipeline (the real cost)
Per source, an **offline** prep script (a world-prep tool, not agent code) that
produces the 8 kHz isolated-word cache the loader reads:
- **LUCID**: parse the **Praat TextGrid** word tier → cut each target word's interval
  from the per-speaker WAV → resample 8 kHz mono → write `{word}_{spk}_{i}.wav`. The
  alignment **already exists**; this is interval-cutting only. *Lowest burden.*
- **L2-ARCTIC**: same, from its **force-aligned** transcripts (already provided).
- **CHILDES/Brent**: the CHAT transcript has **utterance**-level time bullets, not
  word-level. To isolate words you must **force-align** (MFA) the audio to the
  transcript first, *then* cut. *Highest burden* + media is downloaded file-by-file.
- **Forvo**: per-word audio already isolated — only **resample to 8 kHz**. *Lowest
  burden of all*, but the licence/quality caveats below.

### 2d. The held-out / ungameable contract (unchanged, audited)
- The pedagogical clips are the **world's** teaching speech; the agent banks (grounds)
  them via `W.bank_exemplar`, the cookie's mechanism — **no recognition by the world.**
- **Hold out speakers**: build the cross-speaker probe with `ped_index_for(held_spk)`
  exactly as FSDD does (`fsdd_index_for`). A clear-speech corpus with many speakers
  (LUCID = 40) lets the held-out probe test **speaker-invariant** taught-word identity
  — the central perception problem the agent already flags.
- The ADS full-lexicon **held-out yardstick stays synthetic/`W.tts`** (or a held-out
  *speaker's* real clips), never the taught clips, so teaching can't inflate the
  measured number.

### 2e. Isolated taught words vs continuous CDS — the structural fork
- **LUCID / L2-ARCTIC / Forvo** → can yield **isolated taught words** (alignment or
  per-word files) → drop straight into the digit/word cell grid.
- **CHILDES/Brent IDS** → **continuous CDS**; without forced alignment it only gives
  *continuous* infant-directed speech, which fits a *future* continuous-speech world,
  not today's isolated-word cells. It is the **most authentic IDS** but the **most
  preprocessing**.

---

## (3) The highest-leverage first corpus to fetch

**LUCID** — best combination of *(accessible with audio)* × *(genuine
hyperarticulation/clear-speech pedagogy)* × *(usable format / least preprocessing,
because word alignment already ships)*.

Why LUCID over the others:
- It is the **only** verified-free corpus whose *design is the teaching register* —
  speakers explicitly clarify "as if to someone hearing-impaired" + babble-barrier
  conditions → the exact over-articulation/reduced-coarticulation/expanded-vowel
  pedagogical signal the parent should utter. (CHILDES is real IDS but conversational;
  L2-ARCTIC/ISLE are learner speech, the wrong direction; Forvo is uncontrolled.)
- **Word-aligned Praat TextGrids ship with it** → isolating taught words is
  interval-cutting, not forced alignment. Far less effort than CHILDES.
- **40 speakers** → a real cross-speaker held-out split (LOSO), matching the FSDD
  mechanic and testing speaker-invariant taught-word identity.
- **Free, non-commercial research** — fits this project; no ELRA paywall.

**Acquisition steps (do NOT run yet — recon only):**
1. Go to the **Speechbox @ Northwestern** resource (linked from
   `https://valeriehazan.com/wp/index.php/lucid-corpus-london-ucl-clear-speech-in-interaction/`)
   and the LUCID page; follow the Speechbox download for the **clear-speech** subset
   (per-speaker WAV + TextGrids).
2. **Email v.hazan@ucl.ac.uk** to report intended non-commercial research use (the
   page asks for this).
3. Offline prep: TextGrid word tier → cut target-word intervals → `ffmpeg -ar 8000
   -ac 1` → `~/.cache/ozma/lucid/{word}_{spk}_{i}.wav`. Then `ped_index()` reads it
   like FSDD.
4. License note: **non-commercial research only**, cite Baker & Hazan (LUCID); keep
   the data out of git (cache dir, like `/tmp/fsdd`).

**Fallback / fastest-to-validate-the-pipeline:** if the LUCID access email is slow,
**Forvo** (free 500 req/day API, isolated words, *zero* alignment) is the quickest way
to get real over-enunciated **isolated pronunciation-model** clips into the loader to
prove the source plumbing — accepting the licence-murkiness and crowd variability as a
throwaway-prototype, not the final teaching voice.

---

## (4) HONEST flags

- **Transcript-only vs audio:** CHILDES is *mostly transcript-only*; only ~25% is
  media-linked. The audio you want is a **subset** — confirm Brent/Providence still
  have their media folders before assuming. Most CHILDES corpora are useless here
  (no audio).
- **Alignment / segmentation burden:** real CDS (CHILDES) is **continuous** → needs
  **forced alignment (MFA)** to get isolated taught words = the single biggest effort
  item. LUCID/L2-ARCTIC **already ship alignment** (TextGrids / force-aligned phones)
  → interval-cut only. Forvo needs **no** alignment. Choose to *avoid* the MFA step
  for the first source.
- **License / registration barriers:** CHILDES = free **but account required**, CC
  BY-NC-SA; LUCID = free non-commercial via **Speechbox + a usage email** (not a
  one-click link); L2-ARCTIC = free CC BY-NC after a name/email gate; **ISLE = paid
  (ELRA)** — drop it; **Forvo = contested CC BY-NC-SA + API tiering** ($2/yr
  non-commercial) — the licence history is disputed, treat as prototype-only. All are
  **non-commercial** — fine for research, note for any productisation.
- **Are the pedagogical features genuinely present?** **LUCID: YES** (clear-speech is
  the corpus's entire design — instructed hyperarticulation + barrier conditions).
  **CHILDES/Brent: YES but different** — authentic *infant-directed* register (slower,
  higher-pitched, repetitive) yet **conversational, not deliberately hyperarticulated
  read speech**; it is the real motherese, not "clear speech." **L2-ARCTIC / ISLE:
  NO** — learner speech (errors), the opposite of a teaching voice. **Forvo:
  PARTIAL** — citation-form careful pronunciation, but uncontrolled.
- **The voice/source mismatch the parent already documents** (`parent_full.md` §5):
  the test register (espeak/FSDD) differs from the teaching register. A *real* teaching
  voice **widens** the train(real-clear)→test(espeak ADS) gap unless the held-out
  yardstick also uses **held-out real speakers**. Plan the yardstick to use a held-out
  *real* speaker (LOSO) so the bank and probe share medium, isolating the *prosodic*
  teaching effect from the *voice* mismatch.
- **Vocabulary coverage:** LUCID/CHILDES cover a **small, fixed vocabulary** (their
  scripted/spontaneous content), **not** the agent's digit + 40-word TVTropes lexicon.
  The real-voice parent can only utter **words the corpus contains**; espeak must stay
  the fallback renderer for the rest. Expect to *intersect* the corpus vocabulary with
  the curriculum, or restrict the taught cells to the covered words.
- **Realistic effort:** LUCID first source ≈ access email + a TextGrid-cutting prep
  script + the `ped_index` loader + a one-line `parent_say` branch ≈ **modest**
  (days, dominated by waiting on access and writing the cutter). CHILDES IDS is
  **weeks** (account, file-by-file media pull, MFA pipeline). Forvo is **hours** to
  prototype the plumbing (but not a keeper voice).

---

## Sources
- [CHILDES / TalkBank](https://talkbank.org/childes/) — CC BY-NC-SA 4.0, account required, browsable + zip.
- [CHILDES Brent/Siskind corpus](https://talkbank.org/childes/access/Eng-NA/Brent.html) — preverbal infants 9–15 mo, mothers, fully audio-linked.
- [CHILDES corpora list / Providence (Brown)](http://www.cog.brown.edu/research/childlanguage/corpora.html) — Providence ~363 h A/V on CHILDES.
- [LUCID corpus — Valerie Hazan](https://valeriehazan.com/wp/index.php/lucid-corpus-london-ucl-clear-speech-in-interaction/) — 40 speakers, WAV + word-aligned TextGrids, clear-speech, Speechbox access.
- [LUCID paper (Baker & Hazan)](https://www.isca-archive.org/diss_2010/baker10_diss.html)
- [Speechbox / ALLSSTAR (Northwestern)](https://speechbox.linguistics.northwestern.edu/) — ~90k WAV files archive.
- [L2-ARCTIC (TAMU PSI Lab)](https://psi.engr.tamu.edu/l2-arctic-corpus/) — CC BY-NC 4.0, WAV + force-aligned, name/email gate.
- [ISLE corpus (ELRA-S0083)](https://catalog.elra.info/en-us/repository/browse/ELRA-S0083/) — PAID via ELRA/ELDA.
- [Forvo API](https://api.forvo.com/) and [Forvo license](https://forvo.com/license/) — CC BY-NC-SA (contested), free 500 req/day, $2/yr non-commercial.
- [KIDS Konstanz IDS corpus (record)](https://d-nb.info/1187137308/34) — German IDS, access unverified.
- Ferguson & Kewley-Port clear-speech acoustics (vowel-space expansion + duration as the clear-speech levers): [PMC3370057](https://pmc.ncbi.nlm.nih.gov/articles/PMC3370057/) — confirms the *features*, but **no downloadable database**.
