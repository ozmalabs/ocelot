# PREREG — block 319000: the church — congregation + Mary's private counsel room

Record correction: **the church already exists** (`bigville_fisc_church`, block
257000, R9): the third voluntary institution, funded by donation/tithe, paying
Mary's stipend, giving charity, with `fc_counsel` (Mary co-regulates a distressed
resident). **Mary the pastor is a main named character** (`bigville_cast100`:
`role: pastor`, `workplace_kind: church`, `role_identity 0.81`). What was missing —
and what the user specified — is: the church is **non-denominational**, it has a
**private room where Mary does counselling**, and it holds a **public congregation**
(the attendance question). This rung adds those three, on top of the existing
funded institution.

## The mechanism (`bigville_church.json`)

The town `has_church` a **non-denominational** `Church`, `staffed_by` the pastor
(Mary), with a private `Room{private:1}`.

- **`ch_hold_service`** — on the Sunday cadence the pastor holds a public
  `Service{open, draw}`; `draw` is her own pull (charm / role-identity).
- **`ch_decide`** — each resident DECIDES to attend by a collapse over `{go, stay}`:
  `church_choice = Attr(Argmax valued by attend_sign · (piety·draw − worldly_pull),
  "label")`. **Non-denominational** ⇒ the pull is faith only; a resident's creed
  never gates attendance. Once per resident per service.
- **`ch_enter`** — a "go" resident joins the public congregation (`attends`);
  congregation size = `Count(attendees)`, emergent, never hardcoded.
- **`ch_counsel_private`** — in the private room Mary counsels a resident who came
  for it: their **distress is eased**, and what they confided becomes a
  `ConfidentialDisclosure{private:1, public:0}` Mary **holds privately** — never
  made public. This is **the-room-where-it-happened** occlusion: the observer reads
  the confession, the town cannot.

The church has two faces of one institution: the **public** service (attendance,
reportable in the paper) and the **private** counsel (sealed, confidential).

## Gates (pass/fail, pre-registered)

1. **G-service-held / pastor-is-Mary (HEADLINE):** on Sunday a service is held; the
   pastor is **Mary**; the church is non-denominational.
2. **G-emergent-congregation (HEADLINE):** attendance is a COUNT emerging from
   residents' own piety — the devout attend, the faithless stay away — never a
   hardcoded number.
3. **G-private-counsel-is-confidential (HEADLINE):** counselling eases the
   resident's distress AND Mary holds the disclosure privately (`private=1,
   public=0`); it is never made public — the observer reads it, the town cannot.
4. **G-non-denominational:** a pious resident of a minority creed attends
   (attendance is gated by faith, never creed); `non_denominational == 1`.
5. **G-pastor-draw-is-load-bearing:** the same residents yield a larger congregation
   under a more charismatic/committed pastor (higher draw) than a lesser one.
6. **G-attendance-is-the-residents-decision:** two residents with different piety
   reach different attend decisions on the same service (it is their collapse).
7. **G-no-python-decision (source audit):** hold/decide/enter/counsel are the seed
   rules; the attend decision is an Argmax collapse in the seed; the adapter mints
   the church/Mary/room/residents, arms Sunday and counsel, ticks, and reads.

## Scope / honesty
- Attendance is a genuine per-resident collapse (Argmax over {go, stay}) — the
  congregation is emergent and divergent, consistent with the session's principle
  that a decision is a collapse over the agent's own held params.
- This rung is a self-contained demonstrator of the congregation + private room +
  non-denominational marker; it does NOT re-implement the existing funding/tithe/
  stipend/charity (`bigville_fisc_church`) — those stand. Composing the two (a
  service whose collection funds the stipend) is a natural next rung, deferred.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
