# iter-26 — multi-channel STACK: NO clearance, REGRESSES below the formant channel (assistant's clean re-run)

User: "keep grinding." Fourth turn. The agent DERIVED + COMPOSED a multi-channel stack from THREE of its own
shapes (redundancy_increases_reliability -> stack components; voicing_decision_routes_to_specialised_coding
-> manner/voicing channel; removable_context/smooth-function -> formant tracking) + its OWN phonology
predicates (_voicing/_sonorant/_sibilant) + the iter-24 spacing Term. NO-DONKEY verified by reading
domains/stacked_representation.py (only adapter-math DSP added). The sub-agent bailed mid-run (orphaned gates,
output lost to a dead pipe); assistant killed them and re-ran the gate + FSDD CLEANLY.

## GATE (assistant clean re-run, 12x18, 2711 gold segs)
- SURFACE  within-NN 0.204  cross-NN 0.014
- FORMANT (i25 spacing, true formants)  within-NN 0.153  cross-NN 0.043   (reproduces iter-25)
- MANNER (agent phonology channel)  within-NN 0.082  cross-NN 0.007   (weak)
- STACK (i26: formant+track ++ manner)  within-NN 0.071 (BELOW its shuffle 0.076)  cross-NN 0.000
- VERDICT: NO CLEARANCE; the STACK is WORSE than the FORMANT channel alone and below surface.

## FSDD LOSO (assistant clean re-run)
BASELINE 0.544 | FORMANT (i25, no track) 0.528 | FORMANT+TRACK 0.356 (-0.172, tracking HURTS) |
MANNER alone 0.175 | STACK (i26) 0.311 (-0.217 vs formant; -0.233 vs baseline).

## Findings
- The multi-channel STACK via naive concatenation + DTW DILUTES: the weak manner channel + channel-scale
  mismatch wash out the formant signal. Formant TRACKING HURTS (greedy mis-tracking).
- The agent derived the right KINDS (no-donkey held) but this COMBINATION regressed.
- BEST the loop has reached remains iter-25 FORMANT (gate within 0.153, FSDD 0.528 at n_spacings=4), still
  BELOW surface (gate 0.20) / baseline (FSDD 0.544).
- FSDD CONFIG-SENSITIVITY: FORMANT(i25)=0.528 here (n_spacings=4) vs 0.164 in the committed iter-25 script
  (n_spacings=6) — the formant FSDD is highly config-sensitive; treat its absolute value with caution.

## Honest state after 4 turns
The agent's loop (shift -> scale -> true-formants -> stack) derived the right KIND each turn (the META works,
autonomous, no-donkey), but has NOT cleared the OBJECT (gate/baseline), and the 4th turn REGRESSED. The
recognition co-limit is genuinely hard; the residual is the channel-COMBINATION (DTW-over-concatenation is
wrong) and the recognizer itself — beyond a single derived relation or a naive stack.
