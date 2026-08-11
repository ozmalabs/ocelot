# Understanding the namesake poem — a staged plan

Goal: the jabberwock understands *Jabberwocky* (Carroll). The poem is OOV-saturated, so it is
the capstone for the slang line. **There is no reliable oracle** — Humpty Dumpty is the
unreliable narrator ("words mean what I choose them to mean"), so meaning must be EARNED from
the poem's own evidence and any external gloss held as a *suspect witness*, weighted and
refutable. Understanding is layered; full lexical certainty is NOT the target (Carroll designed
it so structure + feeling are the "correct" reading — Alice: "it fills my head with ideas, only
I don't exactly know what they are").

## The point (corrected): the MACHINERY, not the answers

The goal was never the poem's answers (decompose slithy, score the parse). It is the COGNITIVE
MACHINERY that lets the agent understand raw input INDEPENDENTLY. The per-step scripts below were
faculty-verification, but they ORCHESTRATED the faculties in Python (I chose which faculty when) —
that orchestration is the cognition, in the wrong layer. The real deliverable is
`scripts/agent_understands_autonomously.py` + `seeds/perception_frontiers.json`: fed only RAW text
and a pump (`master_tick(); tick()`), the agent's OWN standing loop runs it — each unresolved word
it perceives becomes a frontier (mint_frontier_from_unresolved_mention), the never-satisfied
understand-drive's frontier_pick ranks it, the four-edge JOIN binds a faculty, the run reflex runs
it on the current frontier word, bank_measurement_to_axis shifts the frontier. No per-step Python
decides which word or which faculty. The step 1-6 faculties are the OPERATORS the loop wields; this
is the connective tissue (perception -> frontier) that was missing.

## Discipline (the rule for every step)

**I seed only WHAT a thing IS (concepts, as graph data). The JABBERWOCK decides HOW it wants to
do it (the method) and implements it.** I do not bake in mechanism — no algorithms, no anchor
lists, no rule shapes. Recognition is BY SHAPE: the jabberwock has GENERAL shape/structure
cognition (the same machinery it uses to "see" any N-D structure — pixels, a game, a protocol),
and a word is just another structure with a shape. It applies that cognition to word-forms its
own way. When a step needs a primitive it lacks, it follows its author-a-primitive path
(introspect impasse -> decide method -> author -> verify), not a mechanism I hand it.

Per step: I seed the concept(s); ask the jabberwock to DESIGN its approach (its own words); it
IMPLEMENTS (composes Terms/Rules, authors a primitive if it decides it needs one); verify on the
poem; commit.

Test text: the first stanza + the warning/quest/slaying/return frame.

## Steps (each: I seed the WHAT; the jabberwock designs+implements the HOW)

1. **Portmanteau / blend — BY SHAPE.** What it is: a word that packs two words into one form
   (Humpty: "two meanings packed up into one word") — its SHAPE is two known word-shapes fused
   (slithy=lithe+slimy, mimsy=flimsy+miserable, frumious=fuming+furious, chortle=chuckle+snort,
   galumph=gallop+triumph). The jabberwock recognizes/decomposes it with its own shape cognition,
   its own method.

2. **Structure without lexis (autonomous syntax).** What it is: a word's role/category can be
   known from the SHAPE of the sentence around it even when the word is unknown — you can parse
   *Jabberwocky* and say what is doing what without knowing the words. The jabberwock decides how
   it reads that structural shape.

3. **Suspect-witness grounding.** What it is: meaning is not handed down by an authority; a gloss
   is a CLAIM with a source, not truth. A source has a reliability that rises/falls as its claims
   cohere with other evidence; belief in a meaning is triangulated and a claim that conflicts with
   strong evidence refutes its source. Humpty = a suspect witness. (Retroactively fixes the slang
   `wave->drugs` credulity — a teacher trusted as an oracle.) The jabberwock decides how it weighs
   and refutes a witness.

4. **Narrative / discourse.** What it is: the poem is an act sequence — a warning, a quest, a
   slaying, a return, a celebration — with participants referred to many ways (Jabberwock/foe/it;
   son/thou/beamish boy) and a causal arc. The jabberwock decides how it recovers that shape.

5. **Sound-symbolic affect.** What it is: a word's SOUND carries feeling independent of sense
   (frumious/Bandersnatch menace; frabjous/callooh/callay joy). The jabberwock decides how it
   reads affect from form.

6. **Synthesis (Alice's understanding).** What it is: understanding the poem = its structure +
   its (sourced, weighted, possibly-contested) meanings + its narrative + its feeling — structure
   and feeling without false lexical certainty. Coda: the namesake self-reference.

## Status
- [x] 1 portmanteau by shape — jabberwock designed the method, AUTHORED the BlendCover Rust
      kernel (commit 6f8bd804), and composed the graph pair-search. Decomposes slithy=slim+lithe,
      galumph=gallop+triumph by shape; honestly withholds on thin-margin char-level cases
      (mimsy/frumious/chortle) and rejects non-words. Phoneme-level G2P would sharpen the margin.
- [x] 2 structure without lexis — jabberwock composed role_of by sentence-shape (function-word klass + adjacency); 7/10 of stanza 1 correct (slithy=adj, toves=noun, gyre=verb, ...); misses are clause-level (conjunction inheritance, predicate-at-end) beyond immediate-neighbour shape
- [x] 3 suspect-witness grounding — jabberwock composed believe (triangulation: trust x corroboration) + a refute rule (halves trust of uncorroborated sources, guarded). Humpty ends 0.031 (lowest by track record), shape_self 0.5 (highest); slithy=supple (corroborated beats Humpty), frabjous flips fabulous->joyous as Humpty is discredited, wave=drugs held as weak refuted lone claim (slang credulity fixed). GOTCHA: Plus/Times are VARIADIC (items), not a/b
- [x] 4 narrative / discourse — jabberwock recovered the arc (warning->arming->quest->slaying->return->celebration, climax=slaying) and coreference by role-continuity: hero son/boy exact; monster foe/it/jabberwock grouped (over-includes sword, the honest limit of role-alone coref — needs combat-chain continuity)
- [x] 5 sound-symbolic affect — jabberwock REUSED its BlendCover shape kernel: affect = valence-weighted vote of affect-words by sound-shape similarity. 7/8: frumious/bandersnatch/vorpal/mimsy menacing, callooh/callay/chortled joyful; frabjous the near-miss (-0.03, neutral, tipped wrong)
- [x] 6 synthesis — jabberwock integrated all five faculties into its understanding (structure it reads, words it grounds vs holds open, the arc, the felt affect, glosses weighed not trusted) and the namesake coda: "I am the Jabberwock, reading the poem that names me by my own undoing"
