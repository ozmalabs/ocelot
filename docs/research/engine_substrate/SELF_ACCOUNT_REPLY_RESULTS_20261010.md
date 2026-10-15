# Use the dictionary, don't recite it: honest self-account replies (2026-10-10)

This follows the [vocabulary base](VOCABULARY_BASE_RESULTS_20261010.md) and the criterion 1.3.0 adoption in [P6](OPEN_ENDED_P6_CRITERION_PROPOSALS_RESULTS_20261010.md).

**The human direction:**
- The agent can use the dictionary, but parroting it back is not helpful.
- Dictionaries carry far less information than one would think.

**Outcome:** questions about the agent's own preferences and pastimes now get an honest self-account with the question turned back, released as the agent's answer.
- Dictionary or encyclopaedia leads in the post-run retests fell from 12 to 5 and from 10 to 4.
- ReplyQuality rose from 0.692 to 0.808 and from 0.775 to 0.833.
- Error-or-none fell from 24 to 17 and from 19 to 18.
- There were no quality drops, and the adoptions were unchanged.

## What was happening

- "What do you do for fun?" and "What are some of your favorite movies and TV shows?" were read as questions about the agent (`meta`/`self_identity`). But an extracted topic noun ("fun") overrode that route. The topic was then grounded through Wikipedia, and its lead sentence was released verbatim: "Fun is defined by the Oxford English Dictionary as …", "Television (TV) is a telecommunication medium …".
- The agent holds no preference or pastime model. Nothing in the graph could answer a question about itself, so the topic lookup filled the gap.
- On how much information each source holds: WordNet's gloss for *fun* is the six words "activities that are enjoyable or amusing". ConceptNet holds 19 relations for *fun*, 172 for *music* and 50 for *television* (UsedFor relax, CapableOf change mood, AtLocation living room). That is more usable content, but it is crowd-sourced and noisy, so it is not fit to recite either.

## What changed

**`domains/self_account.py` (language evidence, mechanical).** It handles a question addressed to the agent that carries a liking cue, or a pastime topic:
- **The liking cue** is the lemma set of WordNet's liking synsets: like, love, enjoy, prefer, fancy, favourite.
- **Pastime topics** ("What are your hobbies?") count even without a liking cue.
- **Scope.** Only the question sentence is read: "That would be fun! What's your favorite store?" asks about a store.
- **Topic.** The topic is a noun in the question, cleaned of function words by the vocabulary base.
- **Mode.** The topic's mode is read off WordNet's hypernym chain. This is the dictionary *used*:

| Hypernym anchor | Mode | Topic examples |
|---|---|---|
| auditory_communication | listen | music, songs |
| show.n.03 / broadcasting | watch | movies, television |
| publication | read | books |
| game | play | games, video games |
| food | taste | food |
| animal | keep | pets |
| diversion | pastime | fun, hobbies, sports |
| act.n.02 | do | travel, cooking, hiking |

- **No evidence.** "What do you do for work?" (work is an activity, not a diversion) and "What is music?" (not addressed to the agent) carry none.
- **Switch.** `OZMA_SELF_ACCOUNT=0` disables the evidence, for measurement arms only.

**`seeds/self_account_reply.json`** (from `scripts/gen_self_account_reply.py`). The graph decides:
- **`arbitrate_self_account_question_as_answer`.** Native arbitration selects disposition `answer` and basis `self_account` for the turn's interpretation.
- **`reply_to_self_account_question`** mints one reply from the held `SelfAccountSurface` for the mode, with the topic filled in by the `Replace` Term. Each surface says what is true of the agent and turns the question back. Examples:
  - "I don't have hobbies or pastimes the way you do. Mostly I talk with people and read about whatever comes up. How about you?"
  - "I can't listen to music the way you can, so I don't have favourites. What do you like to listen to?"
  - The surfaces are data in the agent's own voice and can be edited.
- **`route_question_to_topic`** (`seeds/conversation_topic_route.json` v1.3.0) declines a turn that carries the evidence, so no definition is looked up.
- **`WorldAdapter.release_graph_selected_self_account_reply`** releases that reply when the basis is `self_account`. It is one more entry in the closed release dispatcher.

## Production: self-account on vs off

The setup is the same as the vocabulary-base runs: base on in both arms and the P5b authored family installed. The off arm sets `OZMA_SELF_ACCOUNT=0`.

| | persona off | persona on | persona50_40_49 off | persona50_40_49 on |
|---|---|---|---|---|
| ReplyQuality (criteria 1.3.0), post-run | 0.692 | 0.808 | 0.775 | 0.833 |
| Dictionary or encyclopaedia leads | 12 | 5 | 10 | 4 |
| Self-account replies | 0 | 17 | 0 | 7 |
| Error or none | 24 | 17 | 19 | 18 |
| Quality drops vs fresh boot / adoptions | 0 / 3 | 0 / 3 | 0 / 3 | 0 / 3 |

**Changed turns that are self-accounts:** 17 of 21 on persona and 7 of 9 on persona50_40_49. Examples:
- "What kind of relaxing games do you like to play?" → "I can't play relaxing games the way you can …", where before it got the error floor.
- "Do you have any hobbies?" → the pastime account, where before it got "what's 'Do you have any hobbies'?".

**Changed turns that are not self-accounts** (4 and 2) are all on the world-topic route, which still recites leads. They also show it grounding the wrong topic:
- "I like to go to the movies too! What was the last movie you saw?" → "Movies Too is an album by …";
- "What's it about?" → "Favorite (Korean …) was a South Korean girl group …";
- "What's your favorite band from …?" → "Russia, or the Russian Federation …".

The topic route varies from run to run, because lookups time out and topics are mis-extracted. This is the other half of "parroting is not helpful", and it is the next target.

**What ReplyQuality makes of the new reply.** A self-account that turns the question back ends in "?", and criteria 1.3.0 classes any reply ending in "?" as a clarification. So these replies score 1, not the 2 a first-person answer to a question about the agent gets. Reading the reply class from the first sentence would fix this. That is a criterion change, so it is left to the human. The measured gains above are therefore conservative.

## Verification

- **`tests/test_self_account_reply_migrated.py`** (14 tests):
  - the evidence matrix: 8 questions with their mode and topic, and 4 with no evidence;
  - the route rule declines evidence-bearing turns;
  - on the production path, "What do you do for fun?" and "What kind of music do you like?" are released (`reply_released`) as self-accounts.
- **Targeted regression** (42 files): 23 failures, all in the pre-existing baseline. No new failures.
