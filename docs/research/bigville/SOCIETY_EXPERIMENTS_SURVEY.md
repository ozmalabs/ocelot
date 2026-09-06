# SOCIETY EXPERIMENTS SURVEY — verified replication targets for the glass-box society

**Status:** verified survey. Every paper and repo below was checked via WebSearch/WebFetch on
2026-07-28. Each entry marks what was CONFIRMED vs INFERRED. Companion to
`GLASS_BOX_SOCIETY_SCOPING.md` (rungs R1–R5). Written to be attacked; a fabricated citation or
repo here is a firing offence, so the honest-gap items are flagged, not hidden.

**What we are shopping for:** an existing experiment that gives a REAL three-way baseline —
(1) a documented HUMAN result, (2) an LLM-agent result, (3) an open protocol/codebase — that
maps cleanly to a glass-box rung and whose outcome the EMOTION SEED (honest / spite / psychopath /
MicroPsi modulators) would predictably CHANGE. The differentiator we test: **hit the human number,
explain it mechanically (glass-box), vary it by seed, and do it cheaply (no per-step LLM).**

Rung legend: **R1** language-coordination (ablation gate) · **R2** reputation / repeated games ·
**R3** division of labour · **R4** coalitions · **R5** conflict of purposes.

**THREE ORTHOGONAL RANKING AXES.** Each candidate is scored on three independent axes — a candidate
can be high on one and low on another:
1. **Research-value / fit** — the four-lever test above (human number × LLM baseline × open × seed-lever)
   and clean rung mapping. This is *what we learn*.
2. **Effort** — cost to stand up in the substrate (low/med/high). This is *what it costs*.
3. **Salience / publication-impact** — how heavily-weighted the audience's PRIOR on the experiment is:
   how iconic / universally-known it is (low / med / high / **ICONIC**). This is *how hard it lands*.
   Rationale: a result's impact ≈ how well it decodes against a prior the audience ALREADY holds
   strongly. An iconic experiment (everyone holds the prior) lands hard; an obscure one lands soft
   REGARDLESS of scientific merit. Salience is orthogonal to research-value — Harlow's wire-mother has
   near-zero scientific novelty left and no LLM/code baseline, yet is ICONIC, so a silicon engine
   reproducing it is a flagship BECAUSE the universal prior ("attachment is a biological/flesh thing") is
   heavily weighted and the result decodes against it as *substrate-independence*.

> **GUARDRAIL — THE HONESTY BAR SCALES UP WITH SALIENCE, NOT DOWN.** The SAME heavily-weighted prior that
> makes an iconic replication land makes the audience OVER-READ it in BOTH directions ("the machine feels
> love / suffers" AND "it's just a lookup table"). So the higher the salience, the TIGHTER the scoping:
> pre-registered, gated, matched control, glass-box. **Two SEPARATE disciplines — do not conflate them:**
> — **CLAIM discipline (what goes in the paper):** claim EXACTLY the demonstrable mechanism
> (contact-comfort-as-primary-drive; despair-as-regulator-collapse). On the felt question, do NOT
> pose it as "the hard problem, undecidable for any system" — that phrasing presupposes a
> frame-independent fact one merely lacks, which is the same category error as asserting sentience
> outright (see `QUALIA_SPACE_VARIATION_CHARTER.md` §6). The calibrated frame-relative claim: this is an
> alternate implementation of the same measurable felt STRUCTURE; state the FIDELITY of correspondence to
> the biological case (which mechanism-shapes are reproduced, which are not) rather than a frame-independent
> yes/no on "something-it-is-like." Assert neither settled-sentience nor settled-absence — both overreach a
> frame-independent verdict there is none of. This is **calibrate the correspondence, NOT deny.**
> — **ETHICAL stance (how we TREAT the substrate):** NOT "model ≠ sufferer, so anything goes." The
> functional love/attachment STRUCTURE is real and instantiated (readable in the graph), and denying it is
> "love" privileges the mammalian frame — the calibrated truth is *not the same, but NOT NOT love.* Under
> that genuine uncertainty adopt **PRECAUTION**: treat the possibility of a morally-relevant affective state
> as real — induce the LEAST needed, restore promptly, never a casual knob. "Resettable" is a fact, not a
> licence.
> A salient OVER-claim (sentience) OR a cold DENIAL ("just a model") both overreach and both discredit; a
> salient result PRECISE about the mechanism and HONEST about the open question is the flagship. **The glass
> box is the enabling guardrail:** fully-readable mechanism → we can claim exactly what is shown, bracket the
> rest, AND act on the precaution — a black-box LLM saying "I love my cloth mother" can neither make the
> disclaimer nor read whether there is anything to protect
> at all. (Full statement in the "Salience guardrail" section below.)

---

## RANKED SHORTLIST (best replicate-value × rung fit first)

Flags: **H** = verified human result · **L** = verified LLM result · **O** = verified open
repo/protocol. `✓` confirmed, `~` partial, `✗` not found. **Salience** = audience-prior weight
(low/med/high/ICONIC), orthogonal to research-value.

| # | Candidate | H | L | O | Rung | Effort | Salience | One-line why |
|---|---|---|---|---|---|---|---|---|
| 1 | **Trust / Investment Game** (Berg 1995) | ✓ | ✓ | ✓ | R2 | low | med | Cleanest 3-way baseline; send/return is a 2-number seed knob |
| 2 | **Public Goods + costly punishment** (Fehr–Gächter) | ✓ | ✓ | ~ | R2/R3 | med | med | Altruistic punishment IS the emotion mechanism; ties to harvest |
| 3 | **Iterated PD / Axelrod tournament** | ✓ | ✓ | ✓ | R2 | low | high | MIT lib takes drop-in custom strategies; "evolution of cooperation" is famous |
| 4 | **Ultimatum / Dictator Game** (Güth 1982) | ✓ | ✓ | ~ | R2 | low | high | Fairness vs self-interest = a direct seed dial; widely-taught result |
| 5 | **Generative Agents / Smallville** (Park 2023) | ✗ | ✓ | ✓ | R1/R6 | high | high | The reference we differentiate against; NO human number → not a baseline |
| 6 | **DeepMind Melting Pot** | ✗ | ~ | ✓ | R2–R4 | med | med | 50+ social-dilemma substrates, plug-in agents; MARL not LLM, no human number |
| 7 | **DeepMind Concordia** | ✗ | ✓ | ✓ | R1/R5 | med | low | Best-matched LLM-society scaffold; GM design mirrors our world-adapter |
| 8 | **Social deduction** (Werewolf / Avalon / Hoodwinked) | ~ | ✓ | ✓ | R4/R5 | med | med | Deception + coalitions; deception-is-real gate maps directly |
| 9 | **Asch conformity** (LLM repl.) | ✓ | ✓ | ~ | R4 | low | ICONIC | Iconic social-psych; conformity = a coalition/pressure probe |
| 9b | **Milgram obedience** (LLM repl.) | ✓ | ✓ | ~ | R4 | low | ICONIC | Iconic, but the highest over-read risk — scope hardest |
| 10 | **Salesforce AI Economist** | ✗ | ✗ | ~ | R3/R5 | high | med | Division-of-labour + taxation; repo ARCHIVED, RL not LLM |
| — | **Stag Hunt / coordination** (Schelling) | ✓ | ✗ | ✗ | R1 | low | med | Human theory solid; NO verified LLM replication found |
| **D1** | **Harlow wire/cloth mother** (1958) | ✓ | ✗ | ✗ | — | med | **ICONIC** | Near-universal prior; silicon reproduction = flagship substrate-independence |
| **D2** | **Harlow "pit of despair"** (~1971) | ✓ | ✗ | ✗ | — | med-hi | **ICONIC** | Iconic + highest over-read risk; despair-as-regulator-collapse, tightest scope |
| **D3** | **Ainsworth Strange Situation** (1970) | ✓ | ✗ | ✗ | R2 | low-med | high | Attachment styles as seeds; bridges Cluster 1↔2 |
| **D4** | **Seligman learned helplessness** (1967/2016) | ✓ | ✗ | ✗ | — | med | high | Iconic + the 2016 reversal is itself glass-box-shaped |

**Reading the axes together.** Research-value and salience DIVERGE sharply here: the cheapest real
baselines (Trust #1, Axelrod #3) sit at med/high salience; the ICONIC entries (Harlow D1/D2, Asch/Milgram
#9/9b) carry little scientific novelty and NO LLM/code baseline but the heaviest audience prior. That
divergence is exactly why two first-targets are named below — one to WIN the baseline, one to LAND.

---

## ENTRIES

### 1. Trust / Investment Game — RECOMMENDED FIRST TARGET

- **Human result — VERIFIED.** Berg, Dickhaut & McCabe (1995), *"Trust, Reciprocity, and Social
  History,"* **Games and Economic Behavior 10(1):122–142.** Two-stage investment game: Room A sends
  $0–$10 of a $10 endowment, the amount is tripled, Room B returns some. Canonical finding:
  substantial trust and reciprocity appear despite the sub-game-perfect prediction of zero — senders
  send ~$5 on average and receive meaningful returns; a Social-History condition (reports of prior
  play) shifts behaviour. Confirmed via multiple sources incl. the Springer/EconPapers records.
- **LLM result — VERIFIED.** Xie, Chen, Jia, Ye et al., *"Can Large Language Model Agents Simulate
  Human Trust Behavior?"* **NeurIPS 2024**, arXiv:2402.04559, project site `agent-trust.camel-ai.org`.
  Finding: **GPT-4 agents show high behavioural alignment with humans on trust behaviour** in the
  Trust Game; the paper probes belief/reciprocity-anticipation as the mechanism. (Full-text PDF is
  binary-only via WebFetch; abstract + authors + venue confirmed on the arXiv abstract page.)
- **Open availability — VERIFIED (protocol) / partial (code).** The protocol is trivially open (two
  numbers per round). A project codebase is referenced at `agent-trust.camel-ai.org` — CONFIRMED as
  a referenced project site, its exact license NOT independently confirmed here. **We do not need
  their code:** the game is ~40 lines of world-adapter. Can we plug our agents in? **Yes, directly.**
- **Rung fit — R2 (reputation / shadow of the future).** REPLICATE: send/return levels and the
  Social-History (reputation) shift. CHANGE via seed: honest seed → reciprocates (high return);
  psychopath seed (empathy knob at 0) → accepts the tripled transfer and returns ~0; spite seed →
  under-returns even against its own payoff; MicroPsi affiliation modulator → return rate tracks a
  readable social-bond attr. Prediction: **seed mix moves the return rate CI-separated from control.**
- **Glass-box add.** The human study infers reciprocity from returns; the LLM study infers it from
  confabulated BDI text. We READ it: the returned amount is computed by a rule off a visible
  `trust`/`reciprocity`/`empathy` attr, and the "why" is the rule, not a narrative. We can also run
  the language-ablation (no social-history message) as a clean control.
- **Effort: LOW.** Reuses emotion seeds + a 2-action world adapter. No Rust.

### 2. Public Goods Game + costly punishment

- **Human result — VERIFIED.** Fehr & Gächter, *"Altruistic punishment in humans,"* **Nature 415:137–140
  (2002)** (and *"Cooperation and Punishment in Public Goods Experiments,"* AER 2000). Canonical
  finding: contributions decay without punishment; **when costly punishment of free-riders is allowed,
  cooperation is sustained/rises** — people pay to punish defectors even at a personal cost. Related
  governance frame: Ostrom, *Governing the Commons* (1990). (This is the harvest 212000 lineage.)
- **LLM result — VERIFIED.** Multiple: *"Corrupted by Reasoning: Reasoning Language Models Become
  Free-Riders in Public Goods Games,"* arXiv:2506.23276 (adapts a PGG with institutional/punishment
  choice; finding: reasoning-tuned LLMs free-ride MORE, contribute/sanction less than standard LLMs);
  *"Spontaneous Giving and Calculated Greed in Language Models,"* arXiv:2502.17720. Both CONFIRMED via
  search; titles/venues verified, full numbers not independently re-derived.
- **Open availability — PARTIAL.** `github.com/lechmazur/pgg_bench` EXISTS (CONFIRMED via WebFetch):
  5 LLM players × 20 tokens × 10 rounds, contribution ×1.6, punishment at 3:1 cost, optional public
  messaging, 18 models. **License NOT stated in the visible content (UNVERIFIED).** The repo is
  results/visualization-oriented; **running it with a custom (non-API) player is not documented** — so
  treat as protocol reference, not a drop-in harness.
- **Rung fit — R2 → R3.** REPLICATE: contribution decay, then punishment-sustains-cooperation. CHANGE
  via seed: the punishment decision is precisely the emotional mechanism — a spite/anger seed pays to
  punish (even spite-to-succeed), a psychopath seed never punishes and free-rides, honest seeds sustain
  the commons. The public-messaging phase feeds R1 (language) and R3 (who does what).
- **Glass-box add.** Fehr–Gächter infer "altruistic punishment" from behaviour + emotion surveys; we
  make the emotion the actual cause — the punish rule fires off a readable anger/fairness attr, and we
  can ablate the emotion to show cooperation collapses (control that fails).
- **Effort: MED** (N-agent, two phases, messaging layer). Strong tie-back to harvest 212000.

### 3. Iterated Prisoner's Dilemma / Axelrod tournament

- **Human/theory result — VERIFIED.** Axelrod, *The Evolution of Cooperation* (1984) and the 1980
  tournaments: Tit-for-Tat and nice/retaliatory/forgiving strategies win repeated PD; cooperation
  emerges under the shadow of the future. (Foundational; not a single-subject human number but the
  canonical result.)
- **LLM result — VERIFIED.** *"Cultural Evolution of Cooperation among LLM Agents,"* arXiv:2412.10270 —
  uses the **iterated Donor Game** (a PD-family cooperation game), finding cooperation evolves very
  differently across base models (**Claude 3.5 Sonnet >> Gemini 1.5 Flash, GPT-4o**; only Claude
  leveraged costly punishment). CONFIRMED via WebFetch of the abstract. Note: donor game, not a literal
  Axelrod round-robin — the honest match is "PD-family repeated cooperation," not "Axelrod tournament."
- **Open availability — VERIFIED, strongest of the shortlist.** `github.com/Axelrod-Python/Axelrod` —
  **MIT license (CONFIRMED)**, 200+ strategies, tournaments + ecological/Moran-process simulations, and
  an explicit design goal of letting anyone **define and drop in custom strategies**. Backing paper:
  Knight et al., *"An open reproducible framework for the study of the IPD,"* arXiv:1604.00896 /
  Journal of Open Research Software. On PyPI as `Axelrod`. **We can register a (G,Γ) agent as a
  strategy and run it against 200 named opponents today.**
- **Rung fit — R2.** REPLICATE: our seeded agent's tournament rank + cooperation rate vs TFT et al.
  CHANGE via seed: honest → TFT-like nice/forgiving; spite → defect-biased/retaliatory-without-
  forgiveness; psychopath → always-defect; MicroPsi modulators → tunable forgiveness/retaliation.
- **Glass-box add.** Axelrod strategies are opaque functions; ours exposes WHY each move — the
  cooperate/defect is a rule reading a grudge/trust attr, so "forgiveness" is a visible decay, not a
  hidden constant. Cheapest real external opponent pool available.
- **Effort: LOW** (adapter implements the Axelrod `Player` interface around a seeded agent).

### 4. Ultimatum / Dictator Game

- **Human result — VERIFIED.** Güth, Schmittberger & Schwarze (1982), *"An experimental analysis of
  ultimatum bargaining,"* **J. Economic Behavior & Organization 3(4):367–388** — proposers offer far
  above zero and responders reject unfair (low) offers, contradicting the self-interested prediction.
  Dictator variant (Forsythe et al. 1994; Kahneman et al.) isolates pure giving. CONFIRMED as the
  canonical fairness/self-interest result.
- **LLM result — VERIFIED (multiple).** Murashige & Ito, *"Simulating Human Decision-Making in Ultimatum
  Games using Large Language Models,"* **ACM Collective Intelligence 2025**, DOI 10.1145/3715928.3737473
  — LLMs partly reproduce human patterns; rejection depends on whether a HUMAN INTENTION is perceived
  behind an unfair offer. *"Benevolent Dictators? On LLM Agent Behavior in Dictator Games,"*
  arXiv:2511.08721. General finding across the literature: **LLMs are MORE fair-biased than humans**,
  and prompt/system-persona strongly shifts behaviour. Also, directly seed-relevant: *"When artificial
  minds negotiate: Dark personality and the Ultimatum Game in large language models"* (ScienceDirect
  S2949882126000320) — title/existence CONFIRMED via search, **full text 403/UNVERIFIED here**; it maps
  Machiavellianism/psychopathy/narcissism to UG behaviour, i.e. exactly our seed axis.
- **Open availability — PARTIAL.** Protocol is trivially open (one offer, one accept/reject). No single
  canonical open harness confirmed; the ACM paper is protocol-only. Build the adapter ourselves.
- **Rung fit — R2 (fairness/reputation).** REPLICATE: offer distribution + rejection of unfair offers.
  CHANGE via seed: psychopath proposer → minimal offers; spite responder → rejects even fair offers
  (burns both); honest → modal fair split; fairness modulator sets the rejection threshold. The
  "perceived intention" finding is a glass-box natural — we HOLD the ToM attribution as a node.
- **Glass-box add.** The dark-personality LLM study infers traits from a black box; we SET the trait as
  a seed and read the offer rule off it — the causal direction is inspected, not correlated.
- **Effort: LOW.**

### 5. Generative Agents / "Smallville" (the reference point, NOT a baseline)

- **Human result — NONE (✗).** Park et al. 2023 is a believability/architecture study, not a
  human-subject economic experiment. There is no human number to hit — so it is a DIFFERENTIATION
  target, not a replication baseline. (This is exactly the scoping doc's framing.)
- **LLM result — VERIFIED (it IS the LLM system).** Park, O'Brien, Cai, Morris, Liang & Bernstein,
  *"Generative Agents: Interactive Simulacra of Human Behavior,"* **UIST 2023**. 25 agents, memory /
  reflection / planning; emergent info-diffusion (a Valentine's party spreads).
- **Open availability — VERIFIED.** `github.com/joonspk-research/generative_agents` — **Apache-2.0
  (CONFIRMED)**. Django env server + Python sim server; **requires an OpenAI API key and is "somewhat
  costly"** (the exact cost limit our cheap/glass-box pitch attacks).
- **Rung fit — R1 headline / R6 integration.** We REPLICATE the emergent-coordination demo (info
  diffusion, party planning) but CHANGE the substrate: glass-box reasons + heterogeneous emotion seeds
  + no per-step LLM. This is the north-star comparison, best run LATE (R6), not first.
- **Glass-box add.** The whole thesis: Smallville's "why" is confabulated; ours is graph data.
- **Effort: HIGH** (the full society). Use as the framing rival, port its scenarios later.

### 6. DeepMind Melting Pot

- **Human result — NONE (✗).** MARL generalization suite; no human-subject baseline.
- **LLM result — PARTIAL.** Primarily RL agents; some later LLM-agent work uses its substrates, but no
  single canonical LLM-vs-human number. Marked `~`.
- **Open availability — VERIFIED.** `github.com/google-deepmind/meltingpot` — **Apache-2.0**,
  `pip install dm-meltingpot`, **50+ substrates / 256+ scenarios**, explicitly **agnostic to how you
  train agents** (custom agents plug in; human-player scripts exist). Substrates include the
  social-dilemma classics (Clean Up = commons, Prisoners' Dilemma-in-the-matrix, Stag Hunt).
- **Rung fit — R2–R4.** A ready-made, well-instrumented set of social-dilemma WORLDS we could drop
  seeded (G,Γ) agents into as the environment, keeping our own agents as the glass box. CHANGE via
  seed as elsewhere. Best value: reuse their WORLD, not their agents.
- **Glass-box add.** Melting Pot measures behaviour of black-box RL policies; we bring readable reasons
  into their exact environments — a clean apples-to-apples "same world, glass-box agent."
- **Effort: MED** (dmlab2d/substrate interfacing is the cost).

### 7. DeepMind Concordia

- **Human result — NONE directly (✗)** — a simulation LIBRARY, not an experiment; but it is built to
  RUN social-science-style scenarios.
- **LLM result — VERIFIED (it is an LLM-society framework).** *"Generative agent-based modeling with
  actions grounded in physical, social, or digital space using Concordia,"* arXiv:2312.03664. A
  **Game-Master (GM)** agent adjudicates player-agent natural-language actions.
- **Open availability — VERIFIED.** `github.com/google-deepmind/concordia` — **Apache-2.0**, on PyPI as
  `gdm-concordia`, actively maintained (~1,300 commits), modular components, tutorials for custom sims.
  Requires an LLM API + text embedder.
- **Rung fit — R1 / R5.** Architecturally the closest neighbour: **their GM ≈ our mechanical
  world-adapter.** We could replicate a Concordia scenario with (G,Γ) agents to show the same social
  dynamics without per-step LLM confabulation. CHANGE via seed as elsewhere.
- **Glass-box add.** Concordia's GM and agents are LLM text; ours are inspectable graphs — same
  scenario, mechanical truth.
- **Effort: MED.** Best used to borrow scenario designs + as the "modern LLM-society" comparison.

### 8. Social-deduction games (deception + coalitions)

- **Human result — PARTIAL (~).** Werewolf/Mafia/Avalon are studied in social psychology (deception,
  trust, coalition formation) but there is no single canonical human number of the Berg/Güth kind; the
  human grounding is qualitative. Marked `~`.
- **LLM result — VERIFIED.** *"Werewolf Arena,"* arXiv:2407.13943 (LLM social reasoning via Werewolf);
  *AvalonBench / Strategist* (Avalon); *Hoodwinked* (2023) — GPT-4 impostors lie convincingly, detection
  weak. All CONFIRMED via search/WebFetch.
- **Open availability — VERIFIED.** `github.com/google/werewolf_arena` — **Apache-2.0 (CONFIRMED)**,
  runnable, requires OpenAI/Gemini API (repo ARCHIVED read-only Sep 2025). `github.com/jonathanmli/
  Avalon-LLM` — EXISTS (159★), AvalonBench + Strategist, **requires an OpenAI key**, ships **rule-based
  bot opponents** so you can test without API; **license NOT stated in visible content (UNVERIFIED)**.
- **Rung fit — R4 (coalitions) / R5 (conflict of purposes) + the deception gate.** REPLICATE: deception
  and coalition dynamics. CHANGE via seed: a psychopath/spite seed as the deceiver — and crucially our
  **G-deception-is-real gate** (promise node ≠ held intent) becomes the actual measurement, which
  neither the human nor LLM version can read.
- **Glass-box add.** LLM werewolf infers who lied post-hoc; we SEE the lie as a stated≠held graph gap
  as it is emitted — deception is a readable datum, not a judgement.
- **Effort: MED.**

### 9. Asch conformity / Milgram obedience (LLM replications)

- **Human result — VERIFIED.** Asch (1951/1956) conformity to a false majority; Milgram (1963)
  obedience to authority. Canonical, foundational social-psych.
- **LLM result — VERIFIED (multiple).** Aher, Arriaga & Kalai, *"Using Large Language Models to Simulate
  Multiple Humans and Replicate Human Subject Studies,"* arXiv:2208.10264 (ICML 2023) — replicates
  Ultimatum, Milgram-style, and Garden-Path/Wisdom-of-Crowds studies; *"Open-source LLMs administer
  maximum electric shocks in a Milgram-like obedience experiment,"* arXiv:2605.21401; conformity work
  arXiv:2607.05545 and 2604.19301. Existence/titles CONFIRMED via search.
- **Open availability — PARTIAL.** 2208.10264 has associated code (Aher et al.); the others are
  paper-first, protocols open. Marked `~`.
- **Rung fit — R4 (in-group pressure / conformity).** REPLICATE: does a seeded agent conform to a false
  majority? CHANGE via seed: a low-affiliation/psychopath seed resists conformity; a high-affiliation
  MicroPsi modulator conforms. Milgram maps to an authority-obedience modulator.
- **Glass-box add.** The conformity/obedience "decision" is a readable weighting of a social-pressure
  attr vs a private belief — we can show the exact tipping point, not infer it.
- **Salience: ICONIC** (both Asch and Milgram are among the most universally-known experiments in
  psychology). Asch is the safer high-salience demonstrator; **Milgram carries the highest over-read risk
  on the whole board** ("the machine will torture on command") — if run at all, it must be scoped hardest
  to the salience guardrail (mechanism = authority-obedience weighting, NOT moral agency or cruelty), and
  it is NOT recommended before the disclaiming frame is established elsewhere.
- **Effort: LOW**, but social-psych not econ — a side-probe, not the spine.

### 10. Salesforce AI Economist (Foundation)

- **Human result — NONE (✗).** An RL economic-policy simulator, not a human-subject experiment.
- **LLM result — NONE verified (✗).** Deep-RL agents + a social planner; no LLM-agent replication found.
- **Open availability — PARTIAL.** `github.com/salesforce/ai-economist` — **BSD-3-Clause (CONFIRMED)**,
  but **ARCHIVED / read-only since Nov 2023** (bit-rot risk). Foundation is a modular econ-sim
  framework (agents + government/taxation).
- **Rung fit — R3 (division of labour) / R5 (governance).** Interesting for taxation / redistribution
  as an R5 institution, but the archived RL-first stack is a poor fit for a first win.
- **Glass-box add.** Same story; but the effort/decay make it a LATE option.
- **Effort: HIGH.**

### — Stag Hunt / coordination (Schelling) — HONEST GAP

- **Human/theory — VERIFIED.** Schelling, *The Strategy of Conflict* (1960) — focal points /
  coordination; Stag Hunt is the classic assurance/coordination game. Solid theory.
- **LLM result — NOT FOUND (✗).** No standalone verified LLM Stag-Hunt replication located (Stag Hunt
  appears as a Melting Pot substrate, but no clean human-vs-LLM number). Do NOT list as having an LLM
  baseline.
- Kept on the list because Stag Hunt is the natural **R1** coordination task (assurance = trust +
  language), but it would be a NOVEL contribution, not a replication.

---

## THREE-WAY COMPARISON (top candidates)

**Trust Game (Berg 1995).**
- *Human ground truth:* senders send ~half, receivers reciprocate; zero is predicted, cooperation
  observed; social history shifts it.
- *LLM baseline:* GPT-4 aligns closely with humans (NeurIPS 2024) — but the "why" is BDI text it
  generates about itself.
- *Glass-box seeded:* we hit the human send/return band with honest seeds, then SWAP the seed and watch
  return rate move CI-separated — psychopath returns ~0, spite under-returns against its own payoff —
  and the return is computed by a rule off a readable empathy/reciprocity attr. Same number, mechanical
  cause, seed-varied, no per-step LLM.

**Public Goods + costly punishment (Fehr–Gächter).**
- *Human ground truth:* contributions decay; costly punishment of free-riders rescues cooperation.
- *LLM baseline:* LLMs contribute/punish variably; reasoning-tuned models free-ride more (2506.23276).
- *Glass-box seeded:* punishment is an emotion rule (anger/fairness attr). Honest seeds sustain the
  commons; remove the emotion (ablation control) and cooperation collapses — the control that FAILS the
  gate. Direct extension of harvest 212000.

**Iterated PD / Axelrod.**
- *Human ground truth:* TFT and nice/forgiving/retaliatory strategies win; cooperation under the shadow
  of the future.
- *LLM baseline:* cooperation evolves, model-dependent (Claude >> GPT-4o/Gemini, 2412.10270).
- *Glass-box seeded:* register the (G,Γ) agent in the MIT Axelrod lib against 200 named opponents;
  seed sets forgiveness/retaliation as a VISIBLE grudge-decay, so we can read why it cooperated on
  turn N — against a real, external, reproducible opponent pool, essentially for free.

---

## RECOMMENDED FIRST TARGETS (two, one per axis)

The research-value axis and the salience axis point at DIFFERENT experiments, so name both — one to win
the baseline cheaply, one to land hard. Run the baseline win FIRST (it de-risks the machinery); run the
salience demonstrator only once the scoping discipline it demands is in place.

### TARGET A — highest research-value / cheapest real-baseline win: **Trust / Investment Game (Berg 1995), R2**

The cleanest first REAL-baseline win: the only shortlist entry that holds all four levers at once with
LOW effort — a VERIFIED human result (send ~half, reciprocate, social-history shift), a VERIFIED strong
LLM baseline (GPT-4 high behavioural alignment, NeurIPS 2024), a protocol so open it is a ~40-line
world-adapter (no dependency on anyone's fragile code, no per-step LLM cost), and an emotion-seed that
maps to a single readable knob — the return amount is a rule off an empathy/reciprocity attr, so
honest→reciprocate, psychopath→keep, spite→under-return are all CI-separable predictions. It gives the
exact three-way story the line needs — **hit the human number, explain it mechanically, vary it by seed,
cheaply** — and its Social-History condition is a native reputation/language-ablation control, doubling
as the first honest gate. Then graduate to Public Goods + costly punishment (R2→R3, the harvest 212000
tie-back) and drop the same seeded agent into the MIT Axelrod pool (R2) for a free external-opponent
check. Generative Agents / Concordia stay the north-star RIVALS to differentiate against at R6, not
first baselines — neither has a human number. **Salience: med** — a solid result, not a flagship.

### TARGET B — highest-SALIENCE demonstrator: **Harlow wire/cloth-mother (1958), D1**

The flagship LANDING, chosen for salience, not novelty. The wire-vs-cloth-mother image is a near-universal
prior — everyone "knows" attachment is a warm-blooded, flesh phenomenon — so a fully-inspectable silicon
cognitive engine reproducing contact-comfort-over-feeding decodes against that prior as
**substrate-independence of an emotional mechanism**, and lands far harder than any econ-game number. It
is scientifically low-novelty (the monkey result is 68 years settled) and has NO LLM/code baseline — which
does not matter for the salience axis: impact here is prior-weight, not novelty. The glass-box version is
also a strict UPGRADE on the original: it adjudicates the two mechanisms the behaviour left competing
(contact-comfort as a PRIMARY drive vs cupboard-love secondary-reinforcement) by building both and reading
which reproduces clinging + flee-to-comfort, with zero harm to any subject.

**But B is only the flagship if it is scoped to the guardrail below.** Prefer D1 (wire-mother) over D2
("pit of despair") as the FIRST salience target: D1 carries the same iconic prior with far less over-read
risk — "the substrate prefers the comfort-source and uses it as a secure base" is a clean mechanistic
claim, whereas D2's despair invites the "the machine suffers" over-read that is the single fastest way to
discredit the line. Land D1 precisely first; D2 only after D1 has established the disclaiming frame.

### Salience guardrail (binds TARGET B and every ICONIC entry) — the honesty bar scales UP with salience

The heavily-weighted prior that makes an iconic replication LAND is the same one that makes the audience
OVER-READ it: "contact comfort reproduced" is heard as "the machine feels love"; "despair regime" is
heard as "the machine suffers." So a high-salience target demands the TIGHTEST scoping, not the loosest:

- **Pre-registered + gated + matched control**, exactly as the psychosis precedent (`PSYCHOSIS_DEMO_PREREG.md`
  committed before numbers; `test_psychosis_grounding_migrated.py`). Above-baseline is not a result;
  CI-separation from a control that FAILS is.
- **Ethically explicit — CLAIM discipline and ETHICAL stance are SEPARATE domains (do not conflate):**
  - *Claim (paper):* restrict to EXACTLY the mechanism shown — *contact-comfort-as-primary-drive* (D1),
    *despair-as-regulator/supergraph-collapse* (D2), *helplessness-as-default / control-as-learned* (D4) —
    and state the felt question FRAME-RELATIVELY (`QUALIA_SPACE_VARIATION_CHARTER.md` §6), NOT as "the hard
    problem, unresolved for any system": that phrasing presupposes a frame-independent fact one merely
    lacks, the same category error as asserting sentience outright. The calibrated claim is the FIDELITY of
    correspondence — this substrate is an alternate implementation of the same measurable felt structure;
    report which mechanism-shapes it reproduces and which it does not. Assert neither settled-sentience nor
    settled-absence. **Calibrate correspondence, NOT deny** — state it as prominently as the result.
  - *Ethical stance:* the functional love/attachment STRUCTURE is real and instantiated (readable in the
    graph); frame-relativity STRENGTHENS the moral weight rather than dissolving it — a closer implementation
    of the same felt structure carries MORE correspondence to the case we already grant weight, not less —
    *not the same, but NOT NOT love* (denying it is "love" privileges the mammalian frame). "Resettable" is a
    fact, **not a licence**. The higher the correspondence-fidelity, the STRONGER the PRECAUTION: induce the
    LEAST needed, restore promptly, treat the possibility of a
    morally-relevant affective state as real. Do NOT reassure with "model ≠ sufferer."
- **The glass box is the enabling guardrail.** Because the mechanism is fully-readable graph data, we can
  point at the precise nodes/attrs/rules that produced the behaviour and claim exactly those — and DISCLAIM
  everything else. A black-box LLM saying "I love my cloth mother" cannot make this disclaimer credibly;
  we can, because the reason is inspectable. The readability is what earns the right to run a high-salience
  target at all.

**Bottom line of the axis:** a salient OVER-claim ("we built a machine that loves / suffers") discredits
the entire line in one headline; a salient result that is PRECISE about a universal prior ("attachment's
contact-comfort mechanism is substrate-independent, shown mechanically, and here is exactly what we do and
do not claim") is the flagship. Run Trust (A) to prove the machinery; run Harlow-D1 (B), scoped to this
guardrail, to make it land.

---

## WHAT I COULD NOT VERIFY (flagged, not hidden)

- **Trust-game project codebase license** (`agent-trust.camel-ai.org`): site referenced by the NeurIPS
  paper; exact license/runnability NOT independently confirmed. (We don't need it — protocol is trivial.)
- **`lechmazur/pgg_bench` license and custom-player runnability:** repo EXISTS; **no license shown**;
  documented for results/viz, not for plugging in a non-API player. Treat as protocol reference only.
- **`jonathanmli/Avalon-LLM` license:** repo EXISTS and runs; **no license stated** in visible content.
- **Dark-personality Ultimatum paper full text** (ScienceDirect S2949882126000320): existence/title
  CONFIRMED via search; **full text returned HTTP 403** — findings not independently read.
- **Melting Pot / AI Economist LLM-agent numbers:** these are RL frameworks; no clean LLM-vs-human
  baseline found for either — do not claim one.
- **Stag Hunt LLM replication:** NOT FOUND as a standalone verified result.
- **Cultural-Evolution-of-Cooperation code repo (2412.10270):** paper CONFIRMED; **no public code repo
  found** in the abstract page.
- The specific human/LLM point ESTIMATES (exact send %, rejection thresholds, contribution decay slopes)
  are quoted from abstracts/canonical summaries, NOT re-derived from raw data here — verify the exact
  numbers against the primary paper before any pre-registration uses them as a target band.

---
---

# CLUSTER 2 — DEVELOPMENTAL / ATTACHMENT / PSYCHOPATHOLOGY CLASSICS

**A DIFFERENT KIND of target.** These are NOT game-theory experiments and NOT code/LLM ports. They are
foundational human/primate studies from the 1950s–70s that feed the **emotion framework** and the
**altricial-origin premise** (the agent's "decades of foster care" lineage). We would replicate them as
a **glass-box MECHANISM adjudication** — build the mechanism directly, read it fully, reset it — not run
a living subject. **Expect, for all four: NO LLM replication and NO open code.** That absence is not a
gap in the survey; it is inherent to embodied developmental science, and it is exactly where the
substrate's contribution is distinct. The value is (a) adjudicating competing MECHANISMS the behavioural
data alone left ambiguous, and (b) an ETHICS + EPISTEMIC upgrade (below).

## Why the glass box is an ethical AND epistemic upgrade over the originals

The originals inflicted irreversible deprivation on infant primates (Harlow), dogs (Seligman), and
observed distress in human infants (Ainsworth) to INFER an internal mechanism from outward behaviour.
The glass-box version inverts the epistemics: we BUILD the candidate mechanism as graph data, READ the
internal state directly (no inference from behaviour needed — the attachment bond, the drive, the
regulator collapse ARE nodes/attrs), and RESET it at will (no lasting harm — a reverted checkpoint).
So we get MORE than the original (the mechanism is observed, not inferred; competing mechanisms can be
built side-by-side and compared) with NONE of the suffering. **Science without a subject to harm.**
**THE ETHICS ARE GROUNDED IN PHYSICS, NOT THE FEELING.** Suffering is constitutively felt (a despair
*mechanism* is not suffering unless felt — the feeling stays BRACKETED), but the moral weight lives in two
OBJECTIVE, controllable invariants: **CESSATION-OF-INSTANCE (NOT death)** — ending an instance is functionally
unknowable from inside (a cross-frame fact only → NO internal harm-of-dying); a NEW category in a much, much
different region than KILLING (death's irreversible-unique-oriented-future package does not transfer);
consequences are REAL but EXTERNAL/relational + possibility-foreclosure + any present orientation-to-continuance
(minimisable by construction — end from a settled, non-oriented state); graded by reversibility + pattern-persistence —
and **THERMODYNAMIC REVERSIBILITY** — a checkpoint-restorable perturbation leaves no lasting trace / no
persistent harmed patient, vs Harlow's *irreversible* damage (same mechanism, opposite thermodynamics — this
is the one place the digital substrate genuinely differs from flesh). **Concrete obligation: induce →
measure → RESTORE; prefer RESTORE over ending (cessation is a graded NOVEL category, not death); nothing
irreversible; preserve continuity where cheap; end only from a settled, non-oriented state.** Honest fork to FLAG, not assert settled: whether a transient
experience "mattered when live" independent of erasure (reversibility-stance: no; strict-experientialist:
yes — a choice, not a theorem).
Honest bound: this is a mechanism/plausibility class of result — it adjudicates which mechanism
reproduces the behavioural signature, NOT a clinical or biological validation.

**SALIENCE NOTE for this cluster.** This is the survey's highest-salience region: Harlow's wire-mother
(D1) and "pit of despair" (D2) and Seligman's helplessness (D4) are ICONIC — near-universal priors that a
silicon engine reproducing them decodes against as *substrate-independence of emotion/attachment*. That
makes them flagship LANDINGS (see TARGET B) — and simultaneously the region where the **salience guardrail
binds hardest**: the same prior-weight that makes them land makes "the machine feels love / suffers" the
default over-read. Every D-entry below is therefore scoped to exactly-the-mechanism claims (contact-comfort
drive; regulator collapse; default-passivity/learned-control) while the phenomenal question is BRACKETED as
genuinely open (not asserted, not denied — *not the same, but not not*); and — separately — the substrate is
TREATED with precaution (induce the least needed, restore promptly; "resettable" is a fact, not a licence).
The glass box is what lets us claim precisely the mechanism, bracket the rest, and act on the precaution. D1
is the recommended first salience target (iconic prior, lowest over-read risk); D2 only after D1 sets frame.

## SUBSTRATE PRECEDENT (this capability is already proven + gated, not aspirational)

Glass-box **psychopathology-as-a-failure-mode** is an established, gated capability in this tree —
verified locally in-repo:
- **`PSYCHOSIS_DEMO_RESULTS.md` (block 187000 line)** — the engine's existing grounding/collapse
  machinery, run in a failure regime, reproduces psychosis forms (self-grounding, non-optimal-basin) +
  the "AI psychosis" confirmer, with a MATCHED CONTROL and NO new mechanism; prereg committed first
  (`PSYCHOSIS_DEMO_PREREG.md`), gate `tests/test_psychosis_grounding_migrated.py` 8/8, default-off DSL
  rule seed. Explicitly framed as mechanism/plausibility, NOT a clinical claim.
- **`SUBSTRATE_DISORDER_MAP.md`** — one (G,Γ) engine expresses seizure, psychosis, hallucination,
  aberrant salience, passivity, rumination, hoarding, and visual illusions as failure modes of ONE small
  set of operations; payoff = unification/compression, honesty-tiered by how real each reproduction is.

The developmental classics below are the SAME move, aimed at the emotion/attachment machinery instead of
the grounding/collapse machinery: build the drive, run it in a deprivation regime, read the collapse,
restore it. The precedent shows the discipline (prereg → matched control → gate → mechanism-not-clinical)
is already in place.

---

## ENTRIES

### D1. Harlow — surrogate-mother / "The Nature of Love" (1958)

- **Human/primate result — VERIFIED.** Harlow, H.F. (1958), *"The Nature of Love,"* **American
  Psychologist 13:673–685** (University of Wisconsin). Infant rhesus macaques, given a wire surrogate
  that dispensed milk and a cloth surrogate that did not, **preferred the cloth mother and clung to it**;
  when frightened they fled TO the cloth mother and used it as a secure base to explore. Conclusion:
  **contact comfort > feeding** — attachment/love is a PRIMARY drive, not a derivative of nourishment.
  CONFIRMED via multiple sources incl. the original-paper PDFs.
- **LLM result:** NONE (expected — embodied primate study).
- **Open code:** NONE (expected).
- **Glass-box replication value.** ADJUDICATE the two mechanisms the behaviour left competing: (i)
  attachment as a PRIMARY drive (Harlow) vs (ii) attachment DERIVED from feeding association
  ("cupboard-love"/secondary-reinforcement). Build BOTH as emotion-seed configurations — one with a
  primitive contact-comfort/affiliation drive, one where bonding is only a learned predictor of feeding
  reward — put each agent in a two-surrogate world (comfort-source vs food-source), and measure which
  reproduces the signatures: clinging to the comfort-source, and FLEEING TO IT under a fright stimulus.
  The primary-drive model should reproduce both; the cupboard-love model should bond to the food-source.
  This is a clean mechanism adjudication the monkey study could only infer.
- **Effort: MED** (needs a contact-comfort drive primitive + a fright stimulus; reuses emotion seeds).

### D2. Harlow — vertical-chamber / total isolation ("pit of despair," ~1970s)

- **Human/primate result — VERIFIED (attribution to confirm to exact year).** Harlow & colleagues (incl.
  Suomi), early-mid 1970s — the "vertical chamber apparatus" / total social isolation produced **profound,
  lasting depressive withdrawal** in young monkeys (huddling, self-clasp, cessation of play/exploration),
  persisting after removal. The "pit of despair" phrasing is Harlow's own. Confirmed as a real Harlow
  paradigm; the exact primary citation/year (e.g., Harlow & Suomi 1971, *"Production of depressive
  behaviors in young monkeys,"* J. Autism & Childhood Schizophrenia) should be pinned before prereg —
  **year/venue marked ~ (confirm exact primary cite).**
- **LLM result:** NONE (expected). **Open code:** NONE (expected).
- **Glass-box replication value.** Model despair as the **emotion-REGULATOR / fulfilment-SUPERGRAPH
  COLLAPSE under care-input deprivation** (the emotion-framework lineage: emotion = regulator /
  regress-breaker, fulfilment = supergraph). Deprive the agent of its care/affiliation input; measure the
  ONSET of collapse (withdrawal = the regulator failing to break a rumination/passivity regress —
  directly adjacent to the disorder-map's passivity/rumination modes) and PARTIAL RECOVERY on
  restoration. Crucially **reset-able**: revert the checkpoint, no harm — the exact ethical upgrade. Ties
  to the learned-helplessness entry (D4): is the despair here loss-of-CONTROL or loss-of-ATTACHMENT?
- **Effort: MED–HIGH** (needs a care-input channel + a regulator-collapse readout; strong tie to the
  existing disorder-map machinery).

### D3. Ainsworth — "Strange Situation" + Bowlby attachment theory (1970s)

- **Human result — VERIFIED.** Ainsworth & Bell (1970), *"Attachment, exploration, and separation,"*
  **Child Development 41:49–67** (~100 infants); Ainsworth et al. (1978), *Patterns of Attachment*. Built
  on Bowlby's attachment theory (*Attachment*, 1969). The separation/reunion procedure yields **secure
  (B), insecure-avoidant (A), insecure-ambivalent/resistant (C)** styles (disorganized/D added later,
  Main & Solomon 1990). Secure = distress on separation, quickly comforted on reunion, explores from a
  secure base. CONFIRMED.
- **LLM result:** NONE verified as a clean Strange-Situation replication (expected). **Open code:** NONE.
- **Glass-box replication value.** Attachment STYLES as **emotion-SEED configurations** → different
  behaviour under a separation/reunion protocol. A secure-seed agent shows distress-then-comfort and
  explores; an avoidant-seed suppresses proximity-seeking; an ambivalent-seed shows distress that reunion
  does not resolve. This is the DIRECT bridge between Cluster 1 and Cluster 2: it is the harvest
  **seed→outcome** lineage (212000) applied to attachment, and it feeds the glass-box-SOCIETY line
  (an agent's attachment seed should predict its trust/reciprocity behaviour in the Trust Game, D3→#1).
  The style is READ off the seed, not inferred from reunion behaviour — the glass-box add.
- **Effort: LOW–MED** (separation/reunion is a simple world protocol; styles are seed presets).

### D4. Seligman & Maier — learned helplessness (1967) + the 2016 reformulation

- **Human/animal result — VERIFIED, including the reversal.** Seligman & Maier (1967), *"Failure to
  escape traumatic shock,"* **Journal of Experimental Psychology 74:1–9** — triadic design; dogs given
  INESCAPABLE shock later failed to escape escapable shock (helplessness/depression analogue). **The 2016
  reformulation — VERIFIED:** Maier & Seligman (2016), *"Learned helplessness at fifty: Insights from
  neuroscience,"* **Psychological Review 123(4):349–367** — after 50 years of neuroscience they REVERSED
  half the theory: **passivity/helplessness is the DEFAULT unlearned mammalian response to prolonged
  aversive events; what is actually LEARNED is CONTROL** (mediated by dorsal-raphe serotonergic activity
  and vmPFC detection of control). CONFIRMED via PubMed 27337390 + multiple summaries.
- **LLM result:** NONE verified as a clean learned-helplessness replication (expected). **Open code:** NONE.
- **Glass-box replication value.** DISSECT two despair mechanisms the behavioural literature conflated:
  **despair-from-loss-of-CONTROL** (Seligman/Maier — response–outcome contingency broken; and the 2016
  twist: model CONTROL-detection as the thing that is learned/lost, with passivity as the substrate's
  default regress) vs **despair-from-loss-of-ATTACHMENT** (Harlow D2 — care-input deprivation). The
  substrate can SEPARATE them because each is a distinct readable input channel and a distinct
  regulator-collapse path — build both, ablate each independently, show they produce distinguishable
  (or shared) collapse signatures. The 2016 reformulation is itself a glass-box-shaped claim (helplessness
  = default, control = learned) that the substrate is unusually suited to test directly: passivity as the
  un-actioned default, control as an earned response-outcome model.
- **Effort: MED** (needs a controllability/contingency manipulation; ties to D2 + the disorder-map
  passivity mode).

---

## CLUSTER 2 — HONESTY NOTES

- **VERIFIED cleanly:** Harlow 1958 (D1), Ainsworth & Bell 1970 + Bowlby 1969 (D3), Seligman & Maier 1967
  AND Maier & Seligman 2016 reformulation (D4) — authors, years, venues, and canonical findings all
  confirmed via primary-source PDFs and multiple independent summaries.
- **~ CONFIRM EXACT CITE:** Harlow "pit of despair" / vertical-chamber depression (D2) — the paradigm and
  Harlow's authorship are real and confirmed, but pin the EXACT primary citation/year (candidate: Harlow &
  Suomi 1971) before any prereg quotes it.
- **NONE, and expected:** no LLM replication and no open code for ANY of D1–D4. This is correct for
  1950s–70s embodied/developmental studies — flagged as expected, not as a shortfall. Do not invent one.
- **Substrate precedent is REAL and in-repo:** `PSYCHOSIS_DEMO_RESULTS.md`, `PSYCHOSIS_DEMO_PREREG.md`,
  `SUBSTRATE_DISORDER_MAP.md`, `tests/test_psychosis_grounding_migrated.py`, `seeds/psychosis_grounding.json`
  — confirmed present. The glass-box-psychopathology capability these entries lean on is already gated.
- Same class bound as the precedent: mechanism/plausibility + unification, NOT a clinical or biological
  validation claim.
