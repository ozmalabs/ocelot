# Converting a TRAINED model to SELF-LEARNING — research grounding for the jabberwock

Research spike (web + literature) for: "can we take a TRAINED model and CONVERT it to self-learning —
even as a strong BOOTSTRAP/teacher?" This doc is REFERENCE (the operator's web/lit work); the PLAN is
the jabberwock's (driven separately, PHASE 3).

## The framing (savant 3a -> 3b)
A trained model = CAPABILITY without UNDERSTANDING (savant 3a — data crystallized into weights; runs
the program, can't introspect/teach/extend it). SELF-LEARNING = the UNDERSTANDING axis (3b — generates
its own supervision, re-derives its representation, can TEACH + EXTEND). CONVERSION = distill the
trained model's CAPABILITY into self-learning STRUCTURE, with the trained model as a TEACHER/SCAFFOLD
that ACCELERATES the earning — the student still EARNS (the bootstrap speeds the cost, does not skip it,
[[ozma_two_metaskills]] pay-the-real-cost). VALIDATION of 3b = the student can TEACH + EXTEND, NOT just
re-execute (the savant-3b test, [[ozma_savant_3a_3b]]).

For EACH mechanism: how the trained model teaches/proposes + does the student EARN understanding
(teach/extend) or merely COPY.

## Mechanisms (web/lit)

### Knowledge DISTILLATION (Hinton soft targets) + BORN-AGAIN nets
- HOW: the teacher's SOFT targets (temperature-scaled logits) carry "dark knowledge" — inter-class
  similarity the hard label lacks. The student trains to match the teacher's distribution.
- EARN vs COPY: **COPY.** The student learns the same INPUT->OUTPUT FUNCTION (often more accurately
  than from hard labels), but it does NOT acquire a re-runnable STRUCTURE it can teach/extend — it's a
  smaller savant. (Born-again = same arch student sometimes beats teacher, but still a function copy.)
- USE for us: distillation gives the SOFT-TARGET SIGNAL (a richer-than-label teacher) — useful as the
  teacher's PROPOSAL, not as the conversion itself.

### WAKE-SLEEP / Helmholtz machine
- HOW: a RECOGNITION net (bottom-up, data->latents) + a GENERATIVE net (top-down, latents->data). WAKE:
  recognition proposes latents, the generative model is updated to explain the data. SLEEP: the
  generative model DREAMS (samples latents+data), the recognition net trains on its own dreams.
- EARN vs COPY: **EARN (the generative side).** The recognition net is a fast PROPOSAL; the generative
  model is the earned structure that explains the data. The proposal accelerates inference; the
  understanding lives in the generative model. THE template for "teacher accelerates, student earns."

### DREAMCODER / amortized program inference  ★ the keystone
- HOW: a neural RECOGNITION model proposes programs to seed search; a LIBRARY of reusable abstractions
  is learned by refactoring discovered solutions (E-graph common-subexpression). The two BOOTSTRAP each
  other in a wake-sleep loop: a richer library -> richer dreams -> a better recognition net -> solves
  more tasks -> a richer library.
- EARN vs COPY: **EARN.** The neural net is ONLY the amortized proposal (a fast guesser); the earned
  understanding is the symbolic LIBRARY + the discovered PROGRAMS — interpretable, teachable, EXTENSIBLE
  (new abstractions compose old ones). The net bootstraps search; the structure is earned and grows.
  EXACTLY "trained model as teacher that accelerates earning of structure."

### NEURAL -> SYMBOLIC program/rule EXTRACTION (symbolic distillation)
- HOW: extract a closed-form / rule / program description of the function a trained net learned
  (pedagogical: I/O behaviour; decompositional: read the units; symbolic regression on the net).
  "Distillability" can be improved by regularizing the teacher to learn smoother functions.
- EARN vs COPY: **EARN (partial).** The extracted SYMBOLIC structure IS re-representable/teachable —
  the savant 3a->3b move (the program survives extraction from the substrate, [[ozma_savant_3a_3b]]).
  The risk: extraction can be low-fidelity if the net's function is not structured.

### SELF-TRAINING / NOISY-STUDENT / self-distillation
- HOW: the teacher labels unlabelled data (pseudo-labels); the student trains on them (often with noise/
  augmentation), then becomes the next teacher. Iterate.
- EARN vs COPY: **COPY+amplify.** Expands the teacher's reach to more data but stays a function copy; no
  structure earned. Useful as a LABEL-GENERATOR (the teacher generates supervision the student would
  otherwise need data for) — a bootstrap of the COST, not of understanding.

### MODEL INVERSION (discriminative -> generative = analysis-by-synthesis)
- HOW: invert a discriminative/trained model into a generative one; recognize by generation
  (the AbS move, our 2eb45a1a).
- EARN vs COPY: **EARN.** Inverting into a generative model that recognizes-by-generation IS the earned,
  teachable structure. The trained discriminative model can SEED/score the inversion (teacher), the
  generative structure is earned.

## CRUX (convergent): how a trained model TEACHES so an earned structured student bootstraps FAST
The wake-sleep / DreamCoder pattern is the answer and it is what "trained->self-learning" means:
**the trained model is the fast PROPOSAL/RECOGNITION/LABEL-GENERATOR; the EARNED structure (generative
model + library + programs) is the understanding; they bootstrap each other; the net accelerates the
search/inference the student would otherwise pay in full, but the student still EARNS the structure
(which it can teach + extend).** Validation of the earned side = TEACH + EXTEND (savant-3b), not
re-execution.

## MAPPED to the jabberwock (held structure to distill INTO + teachers to distill FROM)
The jabberwock is unusually ready for this — it HOLDS the structured-student side AND has trained
models available as teachers:

| Conversion role | what the jabberwock HOLDS | status |
|---|---|---|
| EARNED STRUCTURE to distill into (the generative model) | AbS generator (2eb45a1a), residual-recurrence generation, writer-physics motor (eae5048b), allographic Substitute (ea55902d), the 5 components + shape-math (AntiUnify/StructSim/Covers) | HELD |
| The amortized PROPOSAL/recognition net (the teacher's role) | the trained scattering+learned head (63%), borrowed Gemma (91%), the speech nets — usable as PROPOSALS/scorers (read-only) | HELD (as teachers) |
| LIBRARY-learning (earned abstractions that grow) | the rung-2 COMPOSER (0f05f957) assembles held parts; grow_part_library AUTHORS new shape-signatures; teach_program registers held Terms | HELD |
| TEACH + EXTEND (the savant-3b validation) | teach_program, parent_teacher/universal-ask, self-extension ladder (dynamic_extend rung-3), the composer | HELD |
| The DREAM (sleep phase) | the held generator can DREAM (render variants — physics-aug eae5048b) to train/seed the proposal | HELD |

**The convergent CONVERSION recipe for the jabberwock (ranked cheap teacher-bootstrap first):**
1. **TEACHER-AS-PROPOSAL bootstrap (cheapest, wake-sleep-faithful).** Use a trained model (Gemma 91% /
   the learned head 63% / a speech net) as the fast RECOGNITION PROPOSAL that seeds the agent's AbS
   program search (2eb45a1a): the teacher narrows the candidate set / scores a prior; the agent's
   held generator EARNS the program that explains the query. Teacher accelerates; student earns.
2. **TEACHER-LABELS -> earned structure (self-training of the structure, not the function).** The
   teacher pseudo-labels unlabelled traces; the agent INDUCES the held PROGRAM/library that generates
   each labelled class (induce_concern / AntiUnifyWitness over the teacher-grouped examples) — the
   library is earned, the teacher only supplied the grouping the agent would have paid data for.
3. **SYMBOLIC EXTRACTION (savant 3a->3b).** Probe the trained net to extract the STRUCTURE it encodes
   (which strokes/parts it keys on) and re-represent it as held shape-signatures/programs — the
   extracted structure is teachable + extensible (the 3a->3b conversion proper).
4. **LIBRARY BOOTSTRAP loop (DreamCoder-faithful, the full thing).** Wake: teacher-proposal + AbS
   solve traces -> discovered programs. Sleep: refactor common sub-programs into NEW held parts
   (grow_part_library) + DREAM variants (physics-aug) to sharpen the proposal. Iterate -> the library
   grows, the proposal sharpens, the student's earned structure deepens.

**Validation (the win is real only if the student EARNS):** the converted student must TEACH (emit a
re-runnable held program a 2nd agent executes) + EXTEND (compose a NEW class/program from the earned
library) — NOT merely re-execute the teacher's function. A strong teacher-bootstrap that demonstrably
SPEEDS the earning while the student still teaches+extends = the massive win the steer names.

## Sources
- Knowledge distillation / dark knowledge / born-again: https://openreview.net/pdf?id=BJxA924YvS ;
  https://www.sciencedirect.com/topics/computer-science/knowledge-distillation
- Wake-sleep / Helmholtz machine: https://en.wikipedia.org/wiki/Wake-sleep_algorithm ;
  http://www.gatsby.ucl.ac.uk/~dayan/papers/d2000a.pdf ; https://arxiv.org/pdf/2007.03132 (Memoised W-S)
- DreamCoder (wake-sleep library learning, neural proposal bootstraps program search):
  https://dl.acm.org/doi/10.1145/3453483.3454080 ; https://ml4code.github.io/publications/ellis2021dreamcoder/ ;
  https://arxiv.org/html/2306.07856v3 (decompiling amortized knowledge)
- Neural->symbolic extraction / symbolic distillation: https://arxiv.org/html/2507.22767v1 ;
  https://arxiv.org/html/2602.21307 (SymTorch) ; https://openreview.net/forum?id=qy024FMO1L (rule distillation)
- Self-training / noisy-student / self-distillation: https://arxiv.org/pdf/2009.07032
