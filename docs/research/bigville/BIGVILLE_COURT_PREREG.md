# PREREG — the council sits as court (bigville R24)

The same council that legislates also **runs court**: when the **Constable**
prosecutes a person, the council hears the charge, renders a **verdict**, and a
guilty verdict carries a **sentence** with a real effect (a fine into the same
Treasury the land_tax feeds, plus a standing hit). This composes with
`bigville_legislature` — one council body, two jobs.

## v1 → v2 CORRECTION (block 313000)

v1 (block 311000) decided each juror's vote by `charge.evidence >= c.bar`. That is
a **comparator**: the outcome is a monotone function of the evidence and the juror
brings nothing but a threshold. **Corrected** per the user: *the councillor
CHOOSES; the evidence is one input to a decision the agent makes by COLLAPSE.* The
verdict is now the council's aggregated decision-by-collapse
(`agent_judgment` / block 312000), not a threshold on evidence. This prereg
documents the v2 gates registered for that rewire.

## The mechanism (v2) — the verdict is the council's collapse

The Charge **is** a Matter: it carries `weight` (evidence) and `-about_subject->`
the defendant. Every councillor is a governed agent that `-considers->` it, so
`jc_conclude` fires: **each councillor collapses the charge against its OWN
dispositions** (credence, punitiveness, deference to the defendant's standing) into
its own conclusion — an `Argmax` over the graded stance set, subjective by
construction. Councillors **diverge**. The court then aggregates:

- `ct_hear` registers each councillor once it has concluded;
- `ct_condemn` registers those whose conclusion is **condemning** (verdict_pole>0);
- `ct_verdict_guilty` / `ct_verdict_acquit` settle once **all** councillors have
  concluded (`heard >= council size`) — **guilty** iff the condemning councillors
  reach the charge's threshold, else **acquitted**;
- `ct_sentence` fines a guilty defendant into the Treasury + a standing hit, once.

## Gates (pass/fail, pre-registered) — v2

1. **G-guilty-when-enough-condemn (HEADLINE):** against a low-standing defendant a
   condemning majority of the council convicts → the defendant is fined (coin down
   by the penalty, into the treasury) and loses standing.
2. **G-identity-shields (HEADLINE):** the **same** bench at the **same** evidence
   **acquits** a high-standing defendant (the councillors' deference shields them;
   too few condemn) — evidence is not decisive alone; who the defendant is moves it.
3. **G-verdict-is-the-collapse:** the councillors reach **more than one** distinct
   conclusion on one charge — the verdict is their collective collapse, not a
   monotone function of the evidence.
4. **G-sentence-applies-once (falsifier):** re-running the fixpoint does not
   double-fine or double-dock; an acquitted defendant is never fined.
5. **G-same-council-both-jobs:** the same Councillor nodes that pass a bill also
   sit in judgment (composition gate).
6. **G-no-python-decision (source audit):** the collapse is `jc_conclude`'s Argmax
   in `agent_judgment`; the aggregation is the `ct_*` seed rules; the adapter mints
   the constable/charge, wires who-considers-what, ticks, and reads (no rule
   engine, no Python selection).

## Scope / honesty
- The councillors' dispositions are seeded; the deliberation is a linear-lean
  collapse, the mechanism not a model of real jurisprudence. The point is that the
  verdict is the **council's own decision-by-collapse** over a data-driven stance
  set, subjective and divergent — one generic mechanism, applied to the council.
- Isolated demonstrator (`self_load_only`); composes with `bigville_legislature`
  and `agent_judgment`; no Rust; `.so` untouched (`a8a9012c`).
