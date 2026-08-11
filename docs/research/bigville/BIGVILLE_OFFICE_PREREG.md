# PREREG — block 358000: offices are agent-created, advertised, applied-for, appointed, delegated

*User: the scenario "starts with a Constable" but he had to be appointed by someone; his authority
is delegated from the council; if he dies/leaves he must be replaced — the same for any position.
And: a role should not be hardcoded — the council can decide it needs more police or a tax
collector (via meeting + decree, its bureaucracy); an overloaded innkeeper can create a cook role.
The concept of a job/role must exist in the minds of the agents. And filling is not magic: the role
is advertised by note or word of mouth, or the creator asks someone directly.*

Nothing about offices is intrinsic or hardcoded. An office is a concept an authority conceives in
response to need; it is made known; people choose whether to apply; the authority selects among
applicants; and the office outlives its holder.

## The mechanism (`bigville_office.json`)

- **CREATE (need → role).** `of_council_create`: the council creates a role ONLY via a `Decree`
  (its bureaucracy — the product of a convened meeting); `of_owner_create`: an OWNER creates a role
  directly for their establishment when `workload > capacity` (the overloaded innkeeper conceives a
  cook). A generic delegator (council or owner) `-delegates-> Office{title, filled, advertised}`.
- **MAKE IT KNOWN.** `of_hear_notice`: a posted `Notice` is heard by residents (no note, no
  awareness); `of_word_of_mouth`: awareness spreads through `knows` ties; the adapter's `ask` makes
  a directly-asked person aware. An opening is not magically known.
- **APPLY (the candidate's choice).** `of_apply_decide`: an aware agent collapses `{apply, pass}`
  valued by `want_work − reservation` (a job-seeker applies, a content person passes; agents
  diverge). `of_apply_grant`: an applicant is recorded (`applies_to`). **You cannot be appointed to
  a job you did not apply for.**
- **SELECT (the authority's choice).** `of_select`: the delegator chooses among the APPLICANTS
  (`Argmax` over `applies_to` by `w_competence·competence + w_loyalty·loyalty` — a merit body and a
  loyalty-prizing body diverge); `of_install` appoints the choice (one office per person).
- **DELEGATE.** `of_delegate`: the holder's authority IS the delegator's — the constable wields the
  council's authority; if the council loses recognition, the delegated authority evaporates.
- **VACATE / SUCCEED.** `of_vacate`: a holder who dies (`alive=0`) or leaves (`left=1`) vacates; the
  office outlives him and the standing opening finds a successor the same way. `of_revoke`: the
  delegator removes a holder.

## Gates (pass/fail)
1. **G-role-created-by-decree (HEADLINE):** nothing exists until decreed; the council decrees a role
   into being.
2. **G-owner-creates-directly:** an overloaded innkeeper conceives a cook role, no decree.
3. **G-not-magically-filled-must-advertise (HEADLINE):** before advertising, nobody knows and the
   office is empty; a posted note is heard, applied to, and filled.
4. **G-only-applicants-considered (HEADLINE):** the most able resident, who heard but chose not to
   apply, is NOT appointed — only applicants are considered.
5. **G-word-of-mouth:** awareness spreads through `knows`; a friend who only heard by word of mouth
   applies and is appointed.
6. **G-direct-ask:** the creator asks one person → only they become aware → appointed.
7. **G-selection-is-a-decision:** a merit council appoints the able applicant; a loyalty-prizing one
   the loyal applicant.
8. **G-delegated-authority:** the holder's authority = the council's; lose recognition → it
   evaporates.
9. **G-vacancy-and-succession (HEADLINE):** the holder falls down a well → vacant, nobody magically
   installed → a new job-seeker hears the opening and succeeds.
10. **G-no-python-decision:** create/hear/apply/select/appoint/vacate are the seed rules.

## Scope / honesty
- Self-contained demonstrator (`self_load_only`); `.so` untouched. Composes with
  `bigville_recognition` (the council's authority) and the council meeting/decree machinery; it
  reframes the constable/clerk-treasurer offices as created + advertised + appointed delegations
  (the theft seed's `con_office` is being refactored separately — this seed does not touch it).
- `apply_choice` is a single per-agent attr (fine for one focused opening at a time); an agent
  deciding per-opening across several simultaneous openings is a refinement.
- The `knows` word-of-mouth spread is one hop per settle; multi-hop propagation is the same rule
  iterated (the fixpoint already does this within a run).
