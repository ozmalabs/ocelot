# PREREG — block 293000: the publisher role is a PORTABLE held goal + affordance

Newspaper-writer plan (`NEWSPAPER_WRITER_PLAN.md`), **Rung A**. The newspaper is
not a subsystem; it is the fixed point of four general faculties. This rung
delivers the FIRST: the "gather information and write" role is a GENERAL, held,
PORTABLE thing a resident carries — not a hardcoded reporter.

## The defect this removes

`bigville_integ3_world.py::_install_press` picks the reporter in PYTHON:

```python
for nm in self.people:
    if self.roles2.get(nm) == "fishmonger":   # <-- a Python decision
        rep_nm = nm
```

That is an agent decision in Python (which resident is the writer), and it bakes
the role into one node type (`Reporter`). Both violate the architecture rule and
the plan's principle (the role must be general and portable).

## What replaces it (graph data + rules)

A resident HOLDS the role as two ordinary, general things:
- a gather goal — `Goal{kind:"know"}`, the SAME general goal any curious agent
  holds (not newspaper-specific);
- a publish capability — an `affords` edge to an `Affordance{name:"makes_known"}`
  (Gibsonian: the resident who affords making-things-known).

And the town's paper finds its writer by a RULE, not a Python pick:
- `pub_employ_afforder`: a Resident in the town who `affords` a `makes_known`
  Affordance is employed by the town's Paper (`Paper -employs-> Resident`).
- `pub_unemploy_non_afforder`: the Paper stops employing a resident who no longer
  affords makes_known (so the edge FOLLOWS the affordance, not accretes).
- `pub_role_gathers`: a resident who affords makes_known acquires the general
  gather goal `Goal{kind:know}` if it holds none — the role BUNDLES the goal.

The world adapter (`bigville_publisher_world.py`) only wires nodes/edges and moves
the `affords` edge; every "who is the publisher" decision is the rule reading the
affordance.

## Gates (pass/fail, pre-registered)

1. **G-role-derives (foundation):** give resident A `affords makes_known`, run
   rules → the Paper employs A (and A holds a `Goal{kind:know}`). No Python
   selected A.
2. **G-portable (HEADLINE):** move the `affords makes_known` edge from A to B, run
   rules → the Paper now employs B and NOT A; B acquires the gather goal. The
   publish role FOLLOWS the affordance. Swapping the holder swaps the writer, with
   zero code change — the proof the role is general, not bespoke.
3. **G-no-python-pick (source audit):** the world adapter contains no role-string
   / name test that selects the publisher (no `== "fishmonger"`, no `roles`
   lookup deciding the writer); the `employs` edge is produced only by the rule.
4. **G-two-afforders (generality):** two residents affording makes_known → the
   Paper employs BOTH (nothing hardcodes a single reporter); removing one leaves
   the other. (The town CHOOSING one lead writer among several is a later rung's
   concern — here we prove the role is not singular-by-construction.)

## Scope / honesty

- This rung delivers the PORTABLE ROLE only. It does NOT yet make townspeople go
  report to him (Rung B), hold what he is told (Rung C), or render prose from held
  nodes (Rung D). The weekly f-string headline in `integ3` is untouched by this
  rung and remains the thing Rung D deletes.
- Built as an ISOLATED demonstrator + seed first (the conduct-spine precedent:
  demonstrate + gate, fold into `integ3` later), so nothing in the live town moves
  until the fold-in rung, and the `.so` is not rebuilt (pure seed/adapter/test).
- Graph-native: the role is nodes + edges; every decision is a rule; the adapter
  is mechanical I/O.
