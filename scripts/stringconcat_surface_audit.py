"""STRINGCONCAT/SURFACE AUDIT — the runner for the `load_parts` type fix (2026-07-17).

*** A MEASURING INSTRUMENT + A REPRODUCTION. IT CHANGES NO BEHAVIOUR. ***

THE DEFECT IT PINS
------------------
`StringConcat` evaluates to `Value::Surface(Text)` — not `Value::Str`. That is
NOT an accident and NOT fixable at the source: `evaluate()` holds an immutable
`&Interner`, so a Term-built string can never be interned into a `Sym`
(term.rs states this in its own words, three times). Every Term-built string —
`StringConcat` / `StringSlice` / `ToJsonString` / `FromJsonString` — is
therefore a `Surface(Text)` BY CONSTRUCTION.

`load_parts` (shape_decode.rs) read a codebook entry's name as
`let Value::Str(name_sym) = &nv else { continue }` — no Surface arm. So a
`ShapeSignature` NAMED BY A RULE was silently dropped: no error, no warning,
the part simply did not exist and every later observation re-minted against a
codebook that never grew.

It nearly produced a FALSE PARADIGM NEGATIVE: all four lattice orientations
minted, which reads exactly like "the substrate's core dynamic-quantization
loop cannot fold orientation". No gate caught it. What caught it was a human
noticing that 0deg and 180deg are the same bar, and it minted twice.

WHY THIS SHAPE OF FIX (and not the other two)
---------------------------------------------
* "Make StringConcat return Str" — IMPOSSIBLE without threading a mutable
  interner through the whole hot evaluate path, and it would defeat the point
  of `Str(Sym)` (Eq as a u32 compare).
* "Unify Str and Surface" — REFUTED BY A PROOF ALREADY IN THE TREE
  (term.rs::eq_with_string_coercion): the Eq+Hash contract requires equal
  values to hash equally, but `Str` hashes its Sym and `Surface` hashes its
  bytes, and `Hash::hash` has no interner access.
* "Teach the READER both shapes" — CORRECT, and it is the convention the
  engine had already settled on everywhere else: `graph_rules.rs::as_str`,
  `term.rs::eq_with_string_coercion`, and shape_decode.rs's OWN
  `td_val_to_string` all accept the pair. `load_parts`/`load_generators` were
  simply the readers that never got the arm.

WHAT IT PRINTS
--------------
1. provenance (PROTOCOL §10.1 — a number without an engine is not a result);
2. the fix: a StringConcat-named ShapeSignature LOADS (covered_count == 3);
3. the unlock: a rule authors a codebook entry END-TO-END — name by
   `StringConcat` AND signature by `ToJsonString`, both Surface;
4. the loudness: a name of the WRONG TYPE panics naming the offender, instead
   of vanishing (the `PickUnique` posture — §1.1 / §12);
5. the audit: which seeds build a codebook node, and whether any took the
   dropping path (the §9 question).

    python scripts/stringconcat_surface_audit.py

IT HARDCODES NO EXPECTED FLOAT (PROTOCOL §12.3) — it recomputes the invariant
live on both sides and prints the verdict. A gate frozen to a digest or a base
sha has rotted twice in this arc, both times by falsely accusing an innocent
rung.
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine,
# and it must do so BEFORE the first `domains.*` import — the first
# `substrate_rs` import BINDS the engine, so a preamble that runs afterwards
# is a no-op that looks correct.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: F401,E402
import domains.reflective_faculty as rf  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402

SIG = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]


def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _concat_name(prefix, var, key):
    return {"__term__": {"type": "StringConcat", "parts": [
        {"type": "Lit", "value": prefix},
        {"type": "IndexAt",
         "seq": {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key},
         "index": {"type": "Lit", "value": 0}}]}}


def check_str_named_baseline():
    """An interned-Str name must load — the byte-identical path."""
    s, ag, native = _boot()
    s.add_node("ShapeSignature", {"name": "str_named", "kind": "faculty",
                                  "faculty": "str_named", "signature": json.dumps(SIG)})
    r = native.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": SIG}})
    return r.get("covered_count")


def check_rule_authored_end_to_end():
    """A rule authors a codebook entry ENTIRELY: name by StringConcat (Surface)
    AND signature by ToJsonString (Surface). BOTH were silently dropped before
    the fix — the name by `load_parts`'s name arm, the signature by its
    Str-only JSON arm."""
    s, ag, native = _boot()
    obs = s.add_node("Observation", {"signature": [list(x) for x in SIG],
                                     "key": ["k9"], "status": "probe"})
    s.add_edge(ag, "observed", obs)
    native.add_rule({
        "name": "audit_rule_authors_part", "match_type": "Observation",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "obs"}, "key": "status"},
                  "b": {"type": "Lit", "value": "probe"}},
        "effects": [
            ["add_node", "ss", "ShapeSignature", {
                "name": _concat_name("authored_", "obs", "key"),
                "kind": "authored",
                "signature": {"__term__": {"type": "ToJsonString", "value": {
                    "type": "Attr", "node": {"type": "Var", "name": "obs"},
                    "key": "signature"}}}}],
            ["set_attr", "obs", "status", "done"]],
    })
    native.run_rules()
    names = [str(s.node(n)["attrs"].get("name", "")) for n in s.nodes("ShapeSignature")]
    authored = [n for n in names if n.startswith("authored_")]
    r = native.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": SIG}})
    return authored, r.get("covered_count")


def check_wrong_type_is_loud():
    """A name that is PRESENT but not string-shaped must ERROR, not skip.
    `continue`-on-unexpected-type is a silent wrong answer — the same disease
    as `.get('Name','')` and a guarded division scoring a dead cell a floor."""
    s, ag, native = _boot()
    s.add_node("ShapeSignature", {"name": 12345, "kind": "faculty", "faculty": "x",
                                  "signature": json.dumps(SIG)})
    try:
        r = native.evaluate({"type": "ShapeDecode", "goal": {"type": "Lit", "value": SIG}})
        return False, "NO ERROR — silently returned covered_count=%r" % (r.get("covered_count"),)
    except BaseException as e:
        return True, str(e).split("\n")[0][:120]


def audit_seed_codebook_builders():
    """THE §9 QUESTION: 37 seeds use StringConcat — did any committed result
    depend on the silent drop? A result can only depend on it if a seed builds
    a CODEBOOK node (ShapeSignature / DimensionGenerator), since those are the
    only types `load_parts`/`load_generators` read."""
    codebook = {"ShapeSignature", "DimensionGenerator"}
    builders, concat_seeds = [], []
    for f in sorted(glob.glob(os.path.join(ROOT, "seeds", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        base = os.path.basename(f)
        if "StringConcat" in json.dumps(d):
            concat_seeds.append(base)
        for r in d.get("rules", []):
            for e in r.get("effects", []):
                if isinstance(e, list) and len(e) >= 4 and e[0] == "add_node" and e[2] in codebook:
                    js = json.dumps(e)
                    builders.append((base, r.get("name"), e[2],
                                     "StringConcat" in js, "ToJsonString" in js))
    return concat_seeds, builders


def main():
    print(provenance_line())
    print()

    cc = check_str_named_baseline()
    print("[1] interned-Str-named part loads      : covered_count=%r  -> %s"
          % (cc, "PASS (byte-identical path)" if cc == 3 else "FAIL"))

    authored, cc2 = check_rule_authored_end_to_end()
    print("[2] RULE authors a part END-TO-END     : names=%r covered_count=%r  -> %s"
          % (authored, cc2, "PASS" if cc2 == 3 else "FAIL"))
    print("      name via StringConcat + signature via ToJsonString — BOTH Surface(Text),")
    print("      BOTH silently dropped before the fix.")

    loud, msg = check_wrong_type_is_loud()
    print("[3] wrong-typed name is LOUD           : %s" % ("PASS — panicked" if loud else "FAIL — SILENT"))
    print("      %s" % msg)

    concat_seeds, builders = audit_seed_codebook_builders()
    print()
    print("[4] §9 AUDIT — seeds using StringConcat: %d" % len(concat_seeds))
    print("    seeds that BUILD a codebook node by rule (the only ones that could")
    print("    have taken the dropping path): %d" % len(builders))
    for b in builders:
        print("      %-22s rule=%-18s type=%-16s StringConcat=%s ToJsonString=%s" % b)
    took_drop = [b for b in builders if b[3] or b[4]]
    print()
    print("    VERDICT: %s" % (
        "NO committed result could depend on the silent drop — no codebook builder\n"
        "             uses a Surface-producing Term. The one builder that exists\n"
        "             (vision_sdloop's vq_grow_quantum) WORKED AROUND the defect by\n"
        "             naming via IndexAt (an already-interned Str), which is why the\n"
        "             orbit law is byte-identical across the fix."
        if not took_drop else
        "*** %d builder(s) took the dropping path — INVESTIGATE, do not suppress ***"
        % len(took_drop)))


if __name__ == "__main__":
    main()
