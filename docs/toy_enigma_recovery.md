# TOY-ENIGMA structure-recovery — diagnostic-ladder rung

**Claim under test.** The structure-recoverer (solve-for-N / analysis-by-synthesis
+ weighted admissibility) can reverse-engineer a toy Enigma's settings from
ciphertext + a crib + a language n-gram. And the convergence claim: the
constraint-propagation that prunes the search **is** weighted admissibility — i.e.
Turing's Bombe is the intersection of hard/soft excluders carving the inadmissible.

Memory: `ozma_structure_recoverer_and_encryption` (residual-structure detector —
classical ciphers + crib are exactly where it bites), `ozma_solve_for_n_is_general_not_speech`
(solve-for-N is domain-agnostic; the forward model is a plug-in).

## 1. Forward model + recoverer (donkey audit)

**DONKEY-CLEAN split:**
- **Enigma forward model** = owned pure logic (`domains/toy_enigma.py`). No net,
  no fit, no gradient. Exact, deterministic `f(settings, plaintext) -> ciphertext`.
- **Structure-recoverer** = the agent's cognition (`domains/enigma_recoverer.py`):
  analysis-by-synthesis (decrypt under each hypothesis = synthesise the plaintext)
  + weighted admissibility (soft excluders intersected, abstain at floor) + the
  Bombe constraint-propagation. Owned Python, no net/fit/gradient.
- **n-gram** = letter-trigram model COUNTED from a corpus (world, train-only):
  LibriSpeech dev-clean transcripts, 236,263 letters, 6,113 distinct trigrams.
  The held-out plaintexts are NOT in the corpus.
- **Ground truth** known (random settings); recoverer sees only ciphertext + crib
  + n-gram. CortexLoop untouched.

**Config (3-rotor Enigma, A..Z, N=26):** historical Enigma I rotor wirings (I/II/III)
+ reflector B (an involution -> no letter maps to itself), odometer stepping with
notch + the historical double-step anomaly, plugboard (involution). Ring = AAA
(start-only, so "recover the start positions" is well-posed for a short message).
Encryption is symmetric (decrypt = encrypt under the same settings). Self-test in
`toy_enigma.py` confirms roundtrip + no-fixed-point.

**Search-space sizes (stated):**
| quantity | size |
|---|---|
| rotor orders (3 distinct rotors) | 3! = 6 |
| start positions | 26^3 = 17,576 |
| Level-1 feasible set (order x start) | 6 x 17,576 = **105,456** |
| plugboard, p=3 pairs | C(26,2)·C(24,2)·C(22,2)/6 = **3,453,450** |
| plugboard, p=10 (historical) | ~1.5e14 |
| full key space (order x start x plug=3) | ~3.6e11 |
| full key space (order x start x plug=10) | ~2.8e26 |

## 2. Results

(filled by `scripts/toy_enigma_recovery.py`; numbers below transcribed from the run)

### Level 1 — rotor order + start positions (plugboard = 0)

Analysis-by-synthesis: for each of the 105,456 (order, start) hypotheses, decrypt
the ciphertext and score by weighted admissibility = (hard crib excluder) ∩ (soft
n-gram excluder). Argmax-admissibility = recovered settings.

- **Recovery success: 8/8 trials** — rotor order + all 3 start positions EXACT.
  Each recovery evaluates the full 105,456 feasible set in ~4.5 s.
- A 12-letter crib alone typically leaves a **single** crib-passing survivor out of
  105,456 (the no-fixed-point + crib over-determine the rotor settings).
- **Crib-length sweep (recovery rate):** crib_len 4 → 5/5, 6 → 5/5, 8 → 5/5,
  10 → 5/5, 12 → 5/5. Even a **4-letter crib over-determines the rotor settings**
  (the n-gram soft excluder carries the rest). Crib length is NOT the bottleneck
  for Level 1.

### Level 2 — plugboard via the Bombe (constraint propagation)

The crib + the rotor-only scrambler `E_i` (Enigma without plugboard) gives, at each
crib position i, the relation `c_i = S(E_i(S(p_i)))` where `S` is the plugboard
involution. The Bombe fixes the test letter's plug partner and PROPAGATES the
no-self-map + involution constraints through the crib's loops. A contradiction
(a letter forced to two partners / to itself) rejects the **entire rotor hypothesis
for all plugboards at once** — the plugboard-independent bulk prune. The few
surviving rotor hypotheses are tie-broken by n-gram admissibility, and the
plugboard is then **completed** by the same n-gram admissibility selector (the
historical "finish the Steckerbrett once the rotors are known").

**Bombe pruning curve** (survivors after plug-free constraint propagation vs crib
length, at the 105,456-rotor scope; the true hypothesis is retained at every length):

| crib length | survivors (of 105,456) | true retained | prune factor |
|---|---|---|---|
| 10 | 18,768 | yes | 5.6× |
| 14 | 1,050 | yes | 100× |
| 18 | **1** | yes | **105,456×** |
| 24 | **1** | yes | **105,456×** |

The constraint propagation alone collapses the entire rotor search to a **single
point** at crib_len ≥ 18 — without ever enumerating a plugboard. The prune is
plugboard-independent: each of the 105,456 rotor hypotheses is accepted or
rejected purely by whether a self-consistent steckering of the crib exists.

**Full Level-2 recovery (crib_len=18, plug=3 pairs, 6 trials):**

- **Recovery success: 5/6 trials** — rotor order + all 3 start positions + all 3
  plugboard pairs EXACT (trials 0–4). Each trial: 105,456 bombe tests in ~23 s,
  pruning to 1–10 survivors, then plug completion.
- **Trial 5 (the one failure, honest):** the Bombe recovered the rotors + start
  EXACTLY and all three TRUE plug pairs (ST, BH, IF) correctly — but the greedy
  plug-completion-by-admissibility added a **spurious 4th pair (XZ)** that
  marginally raised the n-gram score. The completion step does not know the true
  plug count (3), so on a marginal message it over-fits one extra pair, and the
  set-equality check fails. This is a stopping-criterion limit of the completion
  selector, NOT a failure of the Bombe constraint propagation (which retained the
  true rotors). A held-out admissibility threshold or an MDL penalty on plug count
  would close it.
- **Search cost / prune:** the full Level-2 key space (order × start × plug=3) is
  6 × 17,576 × 3,453,450 ≈ **3.64e11**. The Bombe tests only the **105,456
  rotor hypotheses** (a 3.45e6× reduction = exactly the plugboard factor it never
  enumerates), then prunes those to 1–10 survivors — an effective prune of
  ~1e10–1e11× vs brute force. (The run's printed `brute_full = 2.185e12` over-counts
  the plug space 6× from an un-normalised pair formula since fixed in the script;
  the corrected figure is 3.64e11. The *plug-independence* of the prune — the
  load-bearing claim — is unaffected.)

## 3. Convergence note — is the constraint-propagation literally weighted admissibility / the Bombe?

**Yes.** The Bombe's pruning and weighted admissibility are the same operation:
- Each crib constraint `c_i = S(E_i(S(p_i)))` is an **excluder**: given a partial
  steckering hypothesis, it either admits a value for an unknown plug letter or
  contradicts (carves it out). HARD excluder (binary admit/abstain).
- Combining the constraints = **intersection** of the per-position excluders. A
  self-consistent steckering = the intersection is non-empty (admissible). All-26
  branches contradicting = the intersection is empty for that rotor hypothesis =
  inadmissible = pruned in bulk (no plugboard enumeration).
- The n-gram is the **soft** excluder (a real-valued log-admissibility) that
  tie-breaks survivors and completes the plugboard.

So: Bombe = intersection of hard excluders carving the inadmissible; the n-gram =
the soft excluder; together = the weighted-admissibility rule graph
(`domains/weighted_admissibility`, `domains/enigma_recoverer.admissibility`). The
prune is not a heuristic bolted on — it is the admissibility intersection itself.
This is exactly the convergence the task predicted.

## 4. VERDICT

**The structure-recoverer reverse-engineers the toy Enigma.** Confirmed:

- **Level 1** (rotors + start, plug=0): **8/8 exact**; robust down to a **4-letter
  crib**. Analysis-by-synthesis + the n-gram/crib weighted-admissibility
  over-determine the rotor settings exactly, as predicted.
- **Level 2** (rotors + start + plug=3, the Bombe): **5/6 exact**. The Bombe
  constraint-propagation prunes the 105,456-rotor search to a **single survivor at
  crib_len ≥ 18, plugboard-independent** (the ~3.45e6 plugboard factor is never
  enumerated). The one miss is the plug-completion over-fitting an extra pair on a
  marginal message — a stopping-criterion issue, not a Bombe failure.
- **Scope where it works:** plugboard up to 3 pairs, crib length ≥ 18 for full
  plug recovery (≥ 4 for rotors alone), ring fixed (start-only). The prediction
  held: no-fixed-point + crib + n-gram over-determine the settings; the Bombe
  (= weighted admissibility) makes the plugboard tractable.

**Scope honesty:** the recoverer bites exactly where residual structure survives
(memory `ozma_structure_recoverer_and_encryption`): a CLASSICAL cipher with a
no-fixed-point structural weakness + a crib + English n-gram. A plug pair whose
letters the message never exercises is genuinely unrecoverable (no information in
the ciphertext) — an honest, principled limit, not a bug. This says NOTHING about
strong modern crypto (random by design = no structure to grip).
