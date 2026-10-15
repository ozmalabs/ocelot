# A vocabulary base: sufficiency before criteria (2026-10-10)

This follows [P6](OPEN_ENDED_P6_CRITERION_PROPOSALS_RESULTS_20261010.md). The human observation: part of the problem is sufficiency, and a proper vocabulary base is required.

**Outcome:** with an English vocabulary base held as graph data, the agent stops misreading ordinary words. On two production streams, every ask-back about a function word disappeared (2 and 4 before, 0 after). Spurious goal-takes fell from 7 to 4 and from 14 to 4, and error-or-none replies from 28 to 21 and from 23 to 19. Post-run ReplyQuality rose from 0.708 to 0.817 and from 0.683 to 0.858.

The base also showed that the P6 preferred criterion proposal rested on a vocabulary artifact.

## What was insufficient

**The POS faculty** (`construction_grammar._pos_token`) had no class for contractions or interjections:
- Wiktionary types "i'm", "what's" and "i've" as `contraction` and "wow" and "hmm" as `intj`. Neither tag was mapped, so each token became an untyped by-position gap.
- An untyped head makes the agent ask back: "what's 'I'm'?", "I'm not familiar with 'Wow'".
- Worse, "I'm …" statements were read as possible instructions. That produced "I am checking whether this is an instruction before acting." and "I took on the goal to …".
- On a fresh checkout the Wiktionary POS slab is gitignored and absent, so almost every word was untyped.

**The criterion** (`ReplyQuality`) decides on-topic overlap with a hand-chosen 107-word stoplist that includes "fun" and "like". So "Fun is defined by the Oxford English Dictionary …" counted as off-topic to "What do you do for fun?".

## What changed

**`seeds/vocabulary_base_en.json`** (from `scripts/gen_vocabulary_base.py`) holds 7,203 `VocabEntry{form, pos, klass, share, rank, expands}` nodes, derived mechanically. No hand word lists:
- **Source.** The Brown corpus: 1.16M POS-tagged tokens. Brown tags map to a part of speech.
- **Closed or open class.** A form is closed-class when at least 90% of its tokens carry a closed-class tag: determiner, pronoun, preposition, conjunction, auxiliary, modal, particle, qualifier, interjection or contraction. It is open at 90% open-class, and mixed otherwise.
- **Contractions** are Brown's compound tags, for example `PPSS+BEM` "i'm" → [pronoun, auxiliary], or a negated auxiliary such as `DO*` "don't". The parts are kept in `expands`.
- **Counts.** 651 closed, 114 mixed and 6,438 open entries. Every closed form is kept; open and mixed forms are kept to the top 6,000 by Brown frequency.
- **Conversational supplement.** 784 forms from persona_chat_8938 dialogues 300+ (never an evaluation stream) were typed by Wiktionary, for example "haha" and "awesome".

The base is in the conversation profile anchors. Boot time is unchanged (1.2 s with or without it).

**`domains/vocabulary_base.py`** reads the agent's own `VocabEntry` nodes, so a taught entry counts. With no graph it falls back to the same seed file. `OZMA_VOCABULARY_BASE=0` disables it, for measurement arms only.

**Readers:**
- **`_pos_token`.** A token no other source typed is typed from the base before it becomes a gap.
  - A contraction is typed by its first part: "i'm" and "it's" are subject pronouns. A wh-contraction is a wh-focus: "what's" is the focus "thing".
  - An auxiliary-first contraction ("don't", "can't") is a `negated_auxiliary`, deliberately not the bare `auxiliary` that `speech_act_classify` reads as polar-question inversion. A first version used `auxiliary` and turned every "I'm …" statement into a question, which was caught in this tranche's own measurement.
  - A closed-class interjection ("oh", "hey") is typed before Wiktionary, whose first-listed sense of "Oh" is a proper name. That had made "Oh, cool. I've …" read as the command "cool".
- **`WorldAdapter.classify_speech_act`.**
  - A turn made only of interjections ("hmm", "haha", "wow!") is the acknowledgment act.
  - An interjection head is not verb-headed evidence, so "hmm" is no longer an instruction.
- **`ReplyQuality` (criterion edit op `vocabulary`).** It can take its function words from the base, unioned with or replacing the hand stoplist. It is inert until a human adopts it.

## Production: base on vs off

Setup:
- `endemic_rsi_daemon_v1.py <stream> shadow 120`, with the P5b authored family installed.
- The off arm sets `OZMA_VOCABULARY_BASE=0` and is otherwise identical code.

| | persona off | persona on | persona50_40_49 off | persona50_40_49 on |
|---|---|---|---|---|
| Ask-backs about a function word (first pass / post-run) | 2 / 2 | 0 / 0 | 4 / 4 | 0 / 0 |
| Spurious goal-takes, post-run | 7 | 4 | 14 | 4 |
| Error or none, post-run | 28 | 21 | 23 | 19 |
| ReplyQuality mean, post-run | 0.708 | 0.817 | 0.683 | 0.858 |
| Same, with `question → definition` scored 0 | 0.617 | 0.683 | 0.633 | 0.775 |
| Quality drops vs fresh boot | 0 | 0 | 0 | 0 |
| Adoptions | 3 | 3 | 3 | 3 |

**Where the changed turns went.** In the post-run retests, persona50_40_49's changed turns broke down as follows:
- 10 goal-takes, 7 "checking whether this is an instruction" replies, 4 ask-backs and 1 none all became neutral receipts;
- 3 nones and 1 clarification became dictionary definitions.

Persona followed the same pattern. Its "none → definition" changes (5 + 1) are non-answers that the current criterion credits. The row with definitions scored 0 removes that credit, and the gain remains: +0.067 and +0.142.

**What the base exposes next:**
- Preference questions still get dictionary definitions or nothing. That is the missing self-account faculty from P5.
- "I've never been much of a puzzle game person, but …" still becomes a goal-take: "never" is read as the predicate.
- Backchannels ("hmm", "haha") now get no reply. Statement → none scores 0, against 1 for the old "what's 'hmm'?". This is the typed-acknowledgement reply-rule gap from P5.

## The criterion, measured again

`criterion_proposals_c6_v1.py --vocabulary` and `--given vocab:closed+mixed/replace`:
- **The vocabulary edits** (closed or closed+mixed, union or replace) leave κ on the labelled set unchanged: DEV 0.9574, TEST 0.9192. The labels cannot tell the hand stoplist from the base. On-topic overlap rarely decides a label's score.
- **The P6 preferred proposal depended on the stoplist.** Under the base, "fun" is an open noun, so "Fun is defined …" is *on-topic*. `cap question→definition | off_topic` no longer catches it and is no longer recommended.
- **The new preferred proposal** is `cell question→definition = 0`: TEST gain 0.0177, precision0 0.9926. The `addressed_to_agent` cap is equivalent on these labels.

So the narrower proposal I put to you in P6 was an artifact of the hand vocabulary. The decision now has two parts, both yours:
1. Adopt the vocabulary edit `vocab:closed+mixed/replace`, a sufficiency change, κ-neutral.
2. Adopt `cell question→definition = 0` on top of it.

## Verification

- **`tests/test_vocabulary_base_migrated.py`** (4 tests):
  - the derived entries;
  - the base types only otherwise-untyped tokens: "Wow" is an interjection, "I'm" a subject pronoun, "What's" a wh-focus, and an already-typed parse is unchanged with the base off;
  - a taught `VocabEntry` in the graph is consulted;
  - the criterion reads the base only when the edit is held.
- **`tests/test_speech_act_parity_migrated.py`.** Five social fragments ("hello", "Hello.", "hey, what's up?", "hmm", "thanks") were untyped in the historical capture and are now typed. They are adjudicated in the test's override table, and their kinds are unchanged.
- **Comprehension scope** (14 files, base on and off): identical results. The 5 failures in `comprehension_cutover`, `deep_comprehension` and `wordplay` fail in both arms.
- **Targeted regression:** see the commit message.
