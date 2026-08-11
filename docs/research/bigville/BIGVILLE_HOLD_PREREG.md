# PREREG — block 295000: the publisher HOLDS what he is told/witnessed (Rung C)

`NEWSPAPER_WRITER_PLAN.md` **Rung C**. The third faculty: the publisher integrates
what reaches him into HELD BELIEFS — ordinary `knows` edges to Facts — and holds
ONLY what he was told or witnessed. This is the second-reconstruction-channel
guarantee, over held nodes we own.

## What this delivers (graph data + rules)

Built on `BigvilleReportWorld` (so delivery is the real report + travel), with the
`bigville_hold` seed in the same substrate:

- `hold_told`: a Fact the publisher `received` (a reporter delivered it, Rung B)
  becomes a held belief — pub `knows` f — with testimony provenance.
- `hold_witnessed`: a Fact the publisher saw directly (`witnessed_fact`) becomes a
  held belief with witness provenance.

Testimony-bound and anti-confabulation are STRUCTURAL: `knows` is minted only from
`received` or `witnessed_fact`. No rule mints knowledge from nothing.

## Gates (pass/fail, pre-registered)

1. **G-holds-told:** a delivered fact becomes a held belief (pub `knows` it) with
   provenance `testimony`.
2. **G-holds-witnessed:** a fact the publisher saw directly becomes a held belief
   with provenance `witness`, without any delivery.
3. **G-anti-confabulation (HARD):** a fact that was neither delivered nor
   witnessed (a rumour that merely EXISTS in the world) is NOT known. The
   publisher does not hold what he was not given.
4. **G-held-equals-source (HARD):** the held `knows` set is EXACTLY
   (received) ∪ (witnessed) — no extra fact, none missing. Every held belief
   traces to a real event; the reconstruction channel is faithful to its sources.
5. **G-no-python-decision (source audit):** the adapter runs no rule engine and
   holds no if/else deciding what is believed; belief comes only from the hold
   rules reading `received` / `witnessed_fact`.

## Scope / honesty

- Rung C stops at HOLDING. Rendering the held beliefs as prose is Rung D; the
  bias/capture framing (which held beliefs get printed vs suppressed, and in what
  words) is Rung D's flagship.
- Isolated demonstrator + seed + test; no Rust; `.so` untouched.
- "Witnessed" here is a direct edge the adapter wires (the publisher saw it); the
  full occlusion/line-of-sight model that decides WHAT a resident witnesses is the
  town's existing R19 machinery and is out of scope for this rung — here we only
  prove that IF he witnessed or was told it, he holds it, and otherwise he does not.
