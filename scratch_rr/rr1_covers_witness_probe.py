#!/usr/bin/env python3
"""RR1 — is `Covers`-with-witness genuinely needed?

Live probe against the committed engine. Reads only; writes nothing to any
graph. Answers the design spike's §10.3 question operationally: to decide
"does this candidate rule's shape already exist in the held codebook, or
must a new entry be minted", AND to recover the bindings, do the existing
Terms suffice?

Three candidate encodings of a rule's where-signature are probed, on REAL
rules drawn from the same seed corpus the rule-signature slice measured:

  A  FrozenSet of fully-concrete rows; a slot is an ABSENT row.
  B  FrozenSet with the spike's §5.3/§6.2 literal marked-SLOT row.
  C  Dict of path -> atom, with WILD as the slot marker.

For each: (a) coverage decision, (b) witness/bindings recovered,
(c) round-trip Substitute(template, sigma) == observation.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402
from domains.rule_signature import rule_signature  # noqa: E402

# The Term's `wild` FIELD is a Sym NAME (a bare string). The wild VALUE the
# engine compares against inside data is `Value::Tuple([Value::Str(sym)])`
# (`term.rs:6362`), i.e. a ONE-TUPLE containing that string. Using the bare
# string as an in-data marker silently never matches — measured, corrected.
WILD = "·?·"        # the Term field (Sym name)
WILDV = (WILD,)     # the in-DATA marker value
S = srs.Substrate()
N = S._inner  # the raw native handle takes term-JSON dicts directly


def ev(term):
    return N.evaluate(term, {})


def lit(v):
    return {"type": "Lit", "value": v}


def covers(pat, inst):
    return ev({"type": "Covers", "pattern": lit(pat), "instance": lit(inst), "wild": WILD})


def auw(vals):
    return ev({"type": "AntiUnifyWitness", "values": lit(tuple(vals)), "wild": WILD})


def idx(seq, i):
    return {"type": "IndexAt", "seq": seq, "index": lit(i)}


def roundtrip(vals, which):
    """`Substitute(AntiUnifyWitness(vals)[0], AntiUnifyWitness(vals)[1][which])`
    composed as ONE term-tree and evaluated natively.

    This composition — not a Python round trip of the sigma — is the honest
    form of the question, and it is forced: a sigma is a `Value::Dict` whose
    KEYS are position-PATH tuples, and the PyO3 term-JSON wire cannot encode
    a dict with tuple keys (`TypeError: keys must be str, int, float, bool
    or None, not tuple`). So a sigma can only ever be consumed INSIDE the
    engine, which is exactly where a graph rule would consume it."""
    auw_t = {"type": "AntiUnifyWitness", "values": lit(tuple(vals)), "wild": WILD}
    return ev({"type": "Substitute",
               "template": idx(auw_t, 0),
               "sigma": idx(idx(auw_t, 1), which),
               "wild": WILD})


# --------------------------------------------------------------------------
# Real corpus rules
# --------------------------------------------------------------------------
def load_seed_rules(names, seed_dir=os.path.join(HERE, "seeds")):
    """Find named rules across every seed manifest. Read-only."""
    found = {}
    for fn in sorted(os.listdir(seed_dir)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(seed_dir, fn)) as fh:
                blob = json.load(fh)
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and r.get("name") in names and r.get("name") not in found:
                found[r["name"]] = (fn, r)
    return found


def pool_of_where_rules(seed_dir=os.path.join(HERE, "seeds"), limit_files=None):
    """Every seed rule carrying a non-null `where`. Read-only."""
    out = []
    files = sorted(os.listdir(seed_dir))
    for fn in files:
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(seed_dir, fn)) as fh:
                blob = json.load(fh)
        except Exception:
            continue
        if not isinstance(blob, dict):
            continue
        for r in blob.get("rules", []) or []:
            if isinstance(r, dict) and isinstance(r.get("where"), dict) and r.get("name"):
                out.append((fn, r))
    return out


def main():
    print("=" * 78)
    print("RR1 — Covers-with-witness necessity probe")
    print("=" * 78)

    # The design spike's own §6 worked example, plus its sibling in the same
    # seed — the "textbook AntiUnifyWitness pair".
    named = load_seed_rules({"note_reported_gap", "note_unresolved_topic_gap",
                             "note_self_account_gap"})
    for nm, (fn, r) in sorted(named.items()):
        print(f"  corpus rule {nm!r} from seeds/{fn}: "
              f"{len(rule_signature(r.get('where')))} signature rows")
    if "note_reported_gap" not in named:
        print("!! note_reported_gap not found — aborting")
        return 1

    obs_rule = named["note_reported_gap"][1]
    obs = rule_signature(obs_rule.get("where"))

    # ----------------------------------------------------------------
    # ENCODING A — FrozenSet of concrete rows; a slot is an ABSENT row.
    # ----------------------------------------------------------------
    print("\n" + "-" * 78)
    print("ENCODING A — FrozenSet of concrete rows, slot = absent row")
    print("-" * 78)

    # A held codebook entry: the observation minus the two rows that carry
    # its two word-list literals (the design spike's own "one real
    # difference"). Those absences ARE the template's slots.
    lit_rows = frozenset(row for row in obs
                         if row[0] == "ra" and row[2] == "value"
                         and isinstance(row[3], tuple) and len(row[3]) > 3)
    entry = obs - lit_rows
    print(f"  observation rows      : {len(obs)}")
    print(f"  held entry rows       : {len(entry)}  (slot rows omitted: {len(lit_rows)})")

    print(f"  A1 Covers(entry, obs)                = {covers(entry, obs)}")
    print(f"  A2 Covers(obs, entry)  [expect False]= {covers(obs, entry)}")

    tmpl, sigmas = auw([entry, obs])
    s_entry, s_obs = sigmas[0], sigmas[1]
    print(f"  A3 AntiUnifyWitness template rows    = {len(tmpl)}  (== entry: {frozenset(tmpl) == entry})")
    print(f"  A4 sigma[entry] (pattern-side extra) = {len(s_entry)} path-entries "
          f"-> EMPTY == covers: {len(s_entry) == 0}")
    print(f"  A5 sigma[obs]   (the RESIDUAL)       = {len(s_obs)} path-entries")
    if s_obs:
        resid = list(dict(s_obs).values())[0]
        print(f"       residual member count           = {len(resid)}  "
              f"(== the {len(lit_rows)} omitted slot rows: {frozenset(resid) == lit_rows})")
    rt = roundtrip([entry, obs], 1)
    print(f"  A6 Substitute(template, sigma_obs) == obs : {frozenset(rt) == obs}")

    # Negative control: an entry that genuinely does NOT cover.
    other = None
    for fn, r in pool_of_where_rules():
        sg = rule_signature(r.get("where"))
        if sg and not sg <= obs and len(sg) > 5:
            other = (r["name"], sg)
            break
    if other:
        nm, sg = other
        t2, s2 = auw([sg, obs])
        print(f"  A7 NEGATIVE control with {nm!r}: Covers={covers(sg, obs)}, "
              f"sigma[pattern] non-empty={len(s2[0]) > 0}  "
              f"(agreement Covers<->empty-sigma: {covers(sg, obs) == (len(s2[0]) == 0)})")

    # ----------------------------------------------------------------
    # ENCODING B — the spike's literal marked-SLOT row.
    # ----------------------------------------------------------------
    print("\n" + "-" * 78)
    print("ENCODING B — FrozenSet with the spike's literal marked-SLOT row")
    print("-" * 78)
    slot_rows = frozenset(("ra", row[1], row[2], "SLOT") for row in lit_rows)
    entry_b = (obs - lit_rows) | slot_rows
    print(f"  B1 Covers(entry_B, obs)  [spike assumes True] = {covers(entry_b, obs)}")
    tb, sb = auw([entry_b, obs])
    print(f"  B2 sigma[entry_B] non-empty (pattern leaks)   = {len(sb[0]) > 0}")
    if sb[0]:
        print(f"       pattern-side extras                     = {len(list(dict(sb[0]).values())[0])} "
              f"(the SLOT rows themselves — read as pattern NOISE, not as holes)")
    # And with a real WILD in the row instead of the "SLOT" atom:
    wild_rows = frozenset(("ra", row[1], row[2], WILDV) for row in lit_rows)
    entry_bw = (obs - lit_rows) | wild_rows
    print(f"  B3 Covers(entry_B_wild, obs) [in-row WILD]    = {covers(entry_bw, obs)}")

    # ----------------------------------------------------------------
    # ENCODING C — Dict path -> atom, WILD as slot marker.
    # ----------------------------------------------------------------
    print("\n" + "-" * 78)
    print("ENCODING C — Dict of path -> atom, WILD as the slot marker")
    print("-" * 78)

    def to_dict(sig):
        return {repr(row[:-1]): row[-1] for row in sig}

    obs_d = to_dict(obs)
    entry_d = dict(obs_d)
    slot_keys = [repr(row[:-1]) for row in lit_rows]
    for k in slot_keys:
        entry_d[k] = WILDV
    print(f"  C0 marker sanity: Covers(WILDV, 'anything')      = {covers(WILDV, 'anything')}")
    print(f"  C1 Covers(entry_D, obs_D) [WILD-aware Dict arm] = {covers(entry_d, obs_d)}")
    tc, sc = auw([entry_d, obs_d])
    print(f"  C2 template keys={len(tc)}  sigma[entry]={len(sc[0])}  sigma[obs]={len(sc[1])}")
    # residual test: does the Dict arm keep obs-only keys?
    entry_d2 = {k: v for k, v in obs_d.items() if k not in slot_keys}
    td2, sd2 = auw([entry_d2, obs_d])
    print(f"  C3 entry_D2 OMITS {len(slot_keys)} keys (obs-only keys = the residual):")
    print(f"       Covers(entry_D2, obs_D)          = {covers(entry_d2, obs_d)}")
    print(f"       template keys                    = {len(td2)} (obs has {len(obs_d)})")
    print(f"       sigma[obs] captures residual?    = {len(sd2[1])} entries "
          f"-> RESIDUAL LOST: {len(sd2[1]) == 0}")
    rt_c = roundtrip([entry_d2, obs_d], 1)
    print(f"  C4 Substitute(template, sigma_obs) == obs_D : {rt_c == obs_d} "
          f"(round-trip {'INTACT' if rt_c == obs_d else 'LOSSY — cannot rebuild the observation'})")

    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
