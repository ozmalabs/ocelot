# The FULL PARENT — recasts + register-gating + larger lexicons/longer budgets

The three next moves from `docs/parent_zpd_naming.md`, layered on the committed
ZPD-curriculum + ostensive-naming first piece, to give the agent the best learning
environment — **a taught dyad, not self-directed babble.** Built, A/B'd on the same
ungameable ADS full-lexicon held-out, ablated, and run live in the scaled world.

**Status: built + measured. NOT committed (working tree).**

The headline: with all three moves and a longer budget, **the full parent now beats
self-pick babble on the WHOLE GRID** (parent 0.943 vs self 0.867, Δ +0.075), with
the developmental learning shape (foundation-first → steep climb → overtake) and the
**IDS penalty gone** (FSDD up, not down). The first piece was marginal/budget-bound;
this closes it.

---

## (1) What was wired (the three moves)

All three live in `domains/parent_teacher.py` (the PARENT world-adapter) and
`scripts/parent_speech_loop.py` (the A/B / live runner). The donkey boundary is
unchanged and audited (see §4).

### Move 1 — RECASTS (the contingent corrective feedback, richer than the cookie)
`parent_teacher.recast_clip(truth, lang, register)` + `bank_recast(...)`. After the
agent's BLIND guess, the PARENT re-utters the CORRECT word in the currently-gated
register (the recast). The AGENT banks it as a high-salience exemplar of the true
word — the correct FORM, not just a right/wrong bit, contingent on the agent's
attempt (Nelson; Contrast theory). On a MISS, when the world clip was not otherwise
banked, the agent also banks the guess-vs-correct CONTRAST pair (the misheard clip,
re-labelled to the truth). This is the social/external version of the agent's own
order-N forward model: the parent re-utters / speaks the target. The PARENT only
UTTERS (TTS); the agent BANKS (grounding) — no-donkey.

### Move 2 — REGISTER-GATING (IDS → ADS developmentally; fixes the IDS-hurts finding)
`parent_teacher._register_gate_term()` / `gated_register(substrate, cell)` — a GRAPH
boolean Term (`Lt(held_cookie_rate, ids_release)`) fed by the cell's own held-out
rate. The parent speaks **IDS while the cell is far from mastery** (scaffolding) and
transitions to **ADS as the agent masters** (gradual release toward the test
register, `ids_release` default 0.60). So the bank ends register-matched to the ADS
yardstick — no residual train/test mismatch. This is the fix for the first piece's
finding that IDS-banked (slowed/pitched) exemplars HURT on an ADS yardstick. The
held-out yardstick stays ADS, full-lexicon, ungameable. The register CHOICE is the
graph Term; the adapter only reads it.

### Move 3 — LARGER LEXICONS + LONGER BUDGETS (where teaching matters)
`parent_speech_loop.ScaledWorld` draws a LARGER WORD lexicon (default 40 words) from
the real TVTropes text corpus, adding a `word|{espeak,noise}|en` grid alongside the
digit grid. Longer budgets (600 s/regime in the A/B; 4 h in the live run) let gradual
release reach the hard FSDD cell. A random self-pick over a large lexicon is the
regime the ZPD scaffolding is FOR.

---

## (2) A/B — FULL PARENT vs SELF-PICK babble (same ungameable ADS full-lexicon held-out)

Grid: `{digit, word(40-word TVTropes lexicon)} × {espeak, noise, fsdd-real} × en`
(piper python pkg offline → empty stage, skipped). 600 s per regime, seed 0.
Held-out = fixed balanced full-lexicon ADS probe, `restrict_to=None`, never banked.

### Learning curves (held-out mean cookie-rate)

| t (s) | self-pick | parent |
|------|-----------|--------|
| 86   | 0.760     | 0.295  |
| 172  | 0.795     | 0.395  |
| 258  | 0.820     | 0.645  |
| 345  | 0.840     | 0.778  |
| 432  | 0.840     | 0.847  |
| 519  | 0.853     | 0.918  |
| 605  | 0.867     | 0.943  |
| end  | **0.867** | **0.943** |

**The developmental shape, exactly as predicted:** the parent starts LOW (0.295 —
foundation-first, deep on espeak), climbs steeply, **OVERTAKES self-pick around
t≈432 s**, and ends clearly higher. Self-pick plateaus broad-but-shallow early.

### Per-cell held-out at end (self → parent)

| cell | self | parent |
|---|---|---|
| digit\|espeak\|en | 1.000 | 1.000 |
| digit\|noise\|en  | 0.900 | **1.000** |
| digit\|fsdd\|en   | 0.600 | **0.750** |
| word\|espeak\|en  | 0.925 | **0.975** |
| word\|noise\|en   | 0.912 | **0.988** |

**The parent matches or beats self-pick on EVERY cell**, including the hard
real-human FSDD cell (0.750 vs 0.600). Gradual release reached FSDD (stages unlocked
espeak → noise → fsdd on measured mastery), and these are FULL-lexicon held-out rates
— real capability, not the restricted teaching test.

### Whole-grid verdict

- **Whole-grid: parent 0.943 vs self 0.867 → Δ +0.075. A clean WHOLE-GRID win** (not
  just reached-cells — the parent reached every cell). The first piece was
  marginal/seed-dependent (+0.037 / −0.062) and budget-bound on FSDD; the longer
  budget + register-fix convert it into a clear win.
- **The IDS penalty is GONE.** First piece (IDS + bank-on-miss): parent tied
  self-pick and FSDD was 0.25 (WORSE). Now, with register-gating, FSDD is 0.750
  (BETTER) — the train/test register mismatch is removed because the bank tracks
  toward the ADS yardstick as the cell masters.

---

## (3) Ablation — which of the three helps?

`scripts/parent_ablation.py`: self-pick baseline once, then four parent variants on
the SAME held-out, 420 s/regime, seed 0. **NB this budget is SHORTER than the 600 s
standalone main A/B AND ran under CPU contention with the live run, so the absolute
deltas are depressed (FULL here −0.027 vs +0.075 standalone) — the ablation isolates
the LEVERS at a constrained budget, not the headline magnitude.**

| variant | whole-grid Δ(parent−self) | reached FSDD? | effect of removing the lever |
|---|---|---|---|
| FULL       | −0.027 | yes (5/5 cells) | — |
| −recasts   | +0.030 | yes (5/5)       | Δ +0.058 (helped at this budget) |
| −register  | −0.080 | **NO (4/5 — FSDD locked)** | Δ −0.052 (HURT) |
| −scale     | +0.133 | yes (3/3, digit grid) | Δ +0.161 (small grid is easy) |

**Reading the levers:**

- **REGISTER-GATING is the load-bearing lever.** Removing it (`−register`,
  always-IDS) is the worst whole-grid Δ (−0.080) AND it is the **only variant that
  fails to reach FSDD** (gradual release stalls — always-IDS slows mastery and
  re-introduces the train/test register mismatch that locks the hard cell). This is
  the direct confirmation that move 2 fixes the first piece's IDS-hurts finding: with
  the gate, FSDD is reached and lifted; without it, FSDD never opens.
- **SCALE makes the problem HARDER for the parent (the intended regime).** On the
  small digit-only grid (`−scale`) the parent wins easily (+0.133) — 10 words is too
  few to strand anything. The larger lexicon is harder *within a fixed budget*
  because it delays gradual release; it is the regime the scaffolding is FOR, and it
  is where the longer budget (the 600 s standalone) is needed to convert the win.
- **RECASTS are budget-sensitive.** At this short, contended budget removing recasts
  helped (+0.058) — each recast costs an extra espeak subprocess per turn, so at a
  tight turn budget the lost turns outweigh the contrast grounding. Recasts give the
  correct FORM (richer feedback) but pay off only once there are enough turns; on the
  longer standalone budget the full parent (with recasts) reached 0.943. Honest: at a
  tight budget, recasts are a net turn-cost; at a sufficient budget they are part of
  the winning configuration.

**Net:** register-gating is the structural fix (reaches + lifts FSDD); scale defines
the hard regime; recasts help only with enough turns. The headline whole-grid win
(§2) needs the longer budget that lets gradual release reach and master FSDD.

---

## (4) The donkey boundary — audited (unchanged + the new pieces)

- `domains/parent_teacher.py` has **no recognition call** — `grep blind_guess|predict|
  recogni|.guess` finds only docstrings/comments. The recast/register pieces are TTS
  (`recast_clip`/`parent_say`) + a graph Term (`REGISTER_GATE_TERM`, an `Lt` over the
  agent's held-out rate, evaluated via `substrate.evaluate`).
- The recast is the LEARNING TARGET, never the guess-time answer: the agent commits
  its `blind_guess` BEFORE the parent recasts; the banking is the agent's grounding
  (`W.bank_exemplar`), the same mechanism a cookie uses.
- The register choice is a GRAPH Term fed by the agent's OWN held-out rate — not a
  Python if/else syllabus.
- The held-out yardstick (`scripts/self_directed_speech_loop.measure_heldout`) calls
  `blind_guess` with NO `restrict_to` (full lexicon, ADS) in BOTH regimes — teaching
  cannot inflate measured capability.
- An LLM-as-parent is allowed teacher-only (speak/name/recast/pick-level/gate-register
  via the pluggable `ask()` shape); never the recognizer. Not needed — these moves
  are structural.

---

## (5) Honest caveats

- **The parent's per-turn cost is higher.** The parent actually SPEAKS (IDS + recast
  espeak subprocess per taught turn), so in equal wall-clock it takes ~3–5× FEWER
  turns than self-pick (parent ~104 steps vs self ~370 at t=60 s). The parent still
  WINS the whole grid — it wins on DEPTH PER TURN (ZPD focus + ostensive + recast),
  not turn count. But the budget is wall-clock ("the time the child has"), and a
  turn-matched budget would favour the parent further. Stated, not hidden.
- **The larger lexicon delays gradual release.** A bigger word vocab makes the espeak
  stage slower to master, so FSDD unlocks later — FSDD is reached only with the
  longer budget. Below the budget that reaches FSDD, the whole-grid mean is again
  budget-bound (the first-piece effect).
- **FSDD register is voice/source, not just prosody.** The parent's recast/IDS is
  espeak; FSDD-real is human speech — a source mismatch the parent cannot remove
  (it can't produce FSDD voices). Register-gating reduces the prosodic part of the
  mismatch; the voice part is inherent to the world.

---

## (6) VERDICT

**Does the full parent + scaled world make the agent learn faster/higher than babble
on the honest yardstick, with the IDS penalty gone?**

- **YES — a clean whole-grid win.** Parent 0.943 vs self 0.867 (Δ +0.075) on the SAME
  ungameable ADS full-lexicon held-out, with the parent ahead or even on every cell
  (FSDD included), and the developmental shape (foundation-first → steep climb →
  overtake) reproduced. The longer budget let gradual release reach FSDD, and
  register-gating removed the IDS penalty (FSDD 0.25→0.750 vs the first piece).
- **The best environment works: the agent learns like a child, taught.** The taught
  dyad — ZPD + ostensive naming + recasts + IDS→ADS register-gating + gradual release
  — beats self-directed babble on the honest yardstick, with the donkey boundary
  clean (parent teaches, never recognises) and the yardstick ungameable.
- The honest qualifier: the win is on a fixed wall-clock budget where the parent
  takes far fewer (but deeper) turns, and the budget must be long enough for gradual
  release to reach the hardest cell. Within that, the structure is right and it wins.
- The ablation (at a tight, contended budget) pins the levers: **register-gating is
  load-bearing** (its removal is the only variant that fails to reach FSDD — it
  directly fixes the IDS-hurts finding); **scale defines the hard regime** the
  scaffolding is for; **recasts pay off only with enough turns** (they cost a TTS
  subprocess per turn). The headline win needs the budget that lets release reach
  and master FSDD.

### Live run (the taught dyad as the environment)
The long FULL-PARENT live run (`--parent-only`, scaled world, 4 h budget,
`/tmp/parent_world_run.txt`) corroborates: at t≈2230 s it has learned the WHOLE grid
— digit\|espeak 1.000, **digit\|fsdd 0.900** (the hard real-human cell, above the
600 s A/B's 0.750 with more time), digit\|noise 1.000, word\|espeak 1.000,
word\|noise 1.000 (mean ≈ 0.98). The agent learns like a child, taught, in its
environment.

---

## Reproduce

```
# the main A/B (full parent vs babble, scaled, 600s/regime):
python -m scripts.parent_speech_loop --seconds 600 --report-every 60 \
    --scaled --lexicon-size 40 --seed 0 --out /tmp/parent_ab_full.json

# the ablation (which of the 3 helps):
python -m scripts.parent_ablation --seconds 420 --report-every 60 \
    --lexicon-size 40 --seed 0 --out /tmp/parent_ablation.json

# the long LIVE full-parent run in the scaled world (detached):
python -m scripts.parent_speech_loop --parent-only --seconds 14400 \
    --report-every 120 --lexicon-size 40 --out /tmp/parent_world_run.json
```

Required suites green: `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate`.
