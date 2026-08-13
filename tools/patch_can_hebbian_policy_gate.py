"""Patch seeds/can_native_reimplementation.json (1.1.0 -> 1.2.0): add the
Blocker-B policy gate to can_native_hebbian_mint / can_native_hebbian_reweight,
AND fix a genuine, pre-existing (NOT introduced by this patch -- reproduced
on an untouched v1.1.0 checkout before this script existed,
CAN_HEBBIAN_MATERIALIZATION_RESULTS.md Sec2.x) dedup-guard defect in
can_native_note_coactivation, found while building/testing the policy gate.

CAN_HEBBIAN_MATERIALIZATION_PREREG.md / _RESULTS.md. The continuous
mechanism's Hebbian update is always policy-gated (self_improvement_loop.py's
mt_allows("allow_Hebbian_J"), OR'd with a transient plasticity_override>0
rescue); the native mint/reweight rules fired unconditionally through
v1.1.0. This script ANDs a Term-composed policy predicate into both rules'
existing `where` clause -- zero new Rust, zero new Term kinds (Eq/IfThenElse/
Or/Gt/Not/Attr all pre-exist and are reused verbatim).

Registered, deliberate divergence from mt_allows' own Python default
(PREREG Sec2 item 2): an Mt with NO `update_policy` attr at all is treated
as ALLOWED here (legacy/opt-in), not DENIED (mt_allows' conservative
"frozen" default) -- because the existing regression file
(tests/test_can_native_reimplementation.py) builds its Hebbian-test Mts
without ever setting update_policy, and that file must stay green,
unmodified. An Mt carrying an EXPLICIT update_policy attr
(frozen/adaptive/hybrid) is gated identically to mt_allows.

THE DEDUP-GUARD FIX: can_native_note_coactivation's own "already noted"
guard compared a coactivated_with edge's TARGET (a Coactivation node) directly
against `b` (a Concept node) -- `Eq(Nth(e2,2), Var("b"))` -- a type mismatch
that can never be true, so the guard was vacuous. Within one run_rules() cold-
path pass, note_coactivation could therefore re-fire for a pair that had
ALREADY been noted on an earlier tick (the moment the causal_influence edge
guard's own window was still open, i.e. exactly the tick can_native_hebbian_
mint mints the edge in the SAME pass), minting a SECOND, independent
Coactivation ledger for the same (a,b) direction -- which can_native_hebbian_
reweight then advances in parallel, silently inflating the evidence count
this rung's own materialization claim depends on. Fixed to the correct
TWO-HOP existence check (the same a-coactivated_with->co-coactivation_of->b
walk can_native_hebbian_mint's own MATCH pattern already uses, just
expressed as a where-guard): zero new Rust, zero new Term kinds (nested
Exists/Edges/Nth/Eq, all pre-existing and already used elsewhere in this
exact rule).

Run once: `python3 tools/patch_can_hebbian_policy_gate.py`. Idempotent guard:
refuses to re-patch a rule that already carries the gate marker comment.
"""
from __future__ import annotations
import json
import os

SEED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "seeds", "can_native_reimplementation.json",
)

def V(n):        return {"type": "Var", "name": n}
def A(node, k):  return {"type": "Attr", "node": node, "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def Gt(a, b):    return {"type": "Gt", "a": a, "b": b}
def Not(a):      return {"type": "Not", "arg": a}
def Or(*it):     return {"type": "Or", "items": list(it)}
def Nth(items, index): return {"type": "Nth", "items": items, "index": index}
def Edges(node, edge_type):
    return {"type": "Edges", "node": node, "edge_type": edge_type}
def Exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name, "predicate": predicate}
def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


# The EXACT buggy guard, as it exists in v1.1.0 -- matched structurally
# before replacement so this script refuses to touch anything it doesn't
# recognise byte-for-byte.
_BUGGY_DEDUP_GUARD = {
    "type": "Not",
    "arg": {
        "type": "Exists",
        "source": {"type": "Edges", "node": {"type": "Var", "name": "a"},
                   "edge_type": "coactivated_with"},
        "var_name": "e2",
        "predicate": {
            "type": "Eq",
            "a": {"type": "Nth", "items": {"type": "Var", "name": "e2"}, "index": 2},
            "b": {"type": "Var", "name": "b"},
        },
    },
}


def _correct_dedup_guard() -> dict:
    """Not(Exists(a.coactivated_with as e2, Exists(Nth(e2,2).coactivation_of
    as e3, Nth(e3,2) == b))) -- the real two-hop "already noted" check,
    matching can_native_hebbian_mint's own match pattern
    ([a,coactivated_with,coact],[coact,coactivation_of,b]) exactly, just
    expressed as a where-guard instead of a match clause."""
    e2 = V("e2")
    e3 = V("e3")
    inner_exists = Exists(
        Edges(Nth(e2, 2), "coactivation_of"), "e3",
        Eq(Nth(e3, 2), V("b")),
    )
    return Not(Exists(Edges(V("a"), "coactivated_with"), "e2", inner_exists))


def hebbian_policy_gate(mt_var: str = "mt") -> dict:
    """Or(mt_allows_equivalent, plasticity_override > 0).

    mt_allows_equivalent mirrors self_improvement_loop.py::mt_allows's
    three-way switch (frozen -> False; adaptive -> True; hybrid -> the
    allow_Hebbian_J axis attr, default True when absent -- Not(Eq(attr,
    False)) reads as default-True) with ONE registered divergence: the
    final fallback (no update_policy attr present at all) is True, not
    mt_allows' own False/frozen default -- see module docstring.
    """
    mt = V(mt_var)
    policy = A(mt, "update_policy")
    axis_default_true = Not(Eq(A(mt, "allow_Hebbian_J"), L(False)))
    mt_allows_equiv = IfThenElse(
        Eq(policy, L("frozen")), L(False),
        IfThenElse(
            Eq(policy, L("adaptive")), L(True),
            IfThenElse(
                Eq(policy, L("hybrid")), axis_default_true,
                L(True),  # no explicit policy -> legacy/opt-in allow
            ),
        ),
    )
    override_active = Gt(A(mt, "plasticity_override"), L(0.0))
    return Or(mt_allows_equiv, override_active)


def _fix_note_coactivation_dedup(seed: dict) -> None:
    rule = next(r for r in seed["rules"] if r["name"] == "can_native_note_coactivation")
    items = rule["where"]["items"]
    matches = [i for i, it in enumerate(items) if it == _BUGGY_DEDUP_GUARD]
    if not matches:
        raise SystemExit(
            "can_native_note_coactivation: buggy dedup guard not found "
            "byte-for-byte -- refusing to patch blind (either already fixed, "
            "or the rule changed shape and this script needs updating)"
        )
    if len(matches) > 1:
        raise SystemExit("can_native_note_coactivation: ambiguous match, more than one identical item")
    items[matches[0]] = _correct_dedup_guard()


def patch(seed: dict) -> dict:
    if seed.get("version") == "1.2.0":
        raise SystemExit("already at 1.2.0 -- refusing to re-patch")
    targets = {"can_native_hebbian_mint", "can_native_hebbian_reweight"}
    patched = set()
    for rule in seed["rules"]:
        if rule["name"] not in targets:
            continue
        where = rule["where"]
        assert where["type"] == "And", f"{rule['name']}: expected And where, got {where['type']}"
        where["items"].append(hebbian_policy_gate("mt"))
        patched.add(rule["name"])
    missing = targets - patched
    if missing:
        raise SystemExit(f"rules not found: {missing}")
    _fix_note_coactivation_dedup(seed)
    seed["version"] = "1.2.0"
    seed["description"] = seed["description"] + (
        " v1.2.0 (CAN_HEBBIAN_MATERIALIZATION_RESULTS.md) adds the "
        "Blocker-B POLICY GATE to can_native_hebbian_mint/"
        "can_native_hebbian_reweight: both now defer to an Or(mt_allows-"
        "equivalent-three-way-switch, plasticity_override>0) predicate "
        "before minting/reweighting, mirroring self_improvement_loop.py's "
        "mt_allows(\"allow_Hebbian_J\")+plasticity_override transient "
        "path exactly, with ONE registered divergence: an Mt carrying NO "
        "update_policy attr at all is treated as allowed (legacy/opt-in, "
        "preserving the pre-gate unconditional behaviour the existing "
        "regression file's Hebbian tests depend on) rather than "
        "mt_allows' own conservative frozen-default. can_native_note_"
        "coactivation is NOT gated -- it is pure observation/bookkeeping "
        "(mints a Coactivation ledger record, no causal_influence edge, "
        "no evidence-count mutation), matching self_improvement_loop.py's "
        "own relax()-is-never-policy-gated precedent (\"Reading "
        "equilibrium isn't policy-gated; only J/h mutations are\"). Zero "
        "new Rust, zero new Term kinds -- Eq/IfThenElse/Or/Gt/Not/Attr all "
        "pre-exist. ALSO fixes a genuine, pre-existing (confirmed present "
        "on an untouched v1.1.0 checkout, not introduced by this patch) "
        "dedup-guard defect in can_native_note_coactivation: its "
        "\"already noted\" guard compared a coactivated_with edge's target "
        "(a Coactivation node) directly against the Concept b -- a type "
        "mismatch that was always false, so a pair could get a SECOND, "
        "independent Coactivation ledger minted on the tick its edge was "
        "minted, silently inflating subsequent evidence counts. Replaced "
        "with the correct two-hop existence check "
        "(a-coactivated_with->co-coactivation_of->b), matching can_native_"
        "hebbian_mint's own match pattern -- zero new Rust, zero new Term "
        "kinds (nested Exists/Edges/Nth/Eq, all pre-existing)."
    )
    return seed


def main():
    with open(SEED_PATH) as f:
        seed = json.load(f)
    seed = patch(seed)
    with open(SEED_PATH, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    print(f"patched {SEED_PATH} -> version {seed['version']}")


if __name__ == "__main__":
    main()
