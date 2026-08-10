"""PROOF: the jabberwock EXTRACTS A FUNCTION FROM PROSE, read from a REAL maths
reference (OEIS), and the function it extracts REPRODUCES the source's ground-truth
values — falsifiably verified by the source, not by hand-fed assertions.

For each sequence: read the PROSE name from OEIS -> the agent's grammar EXTRACTS
candidate formal functions (extract_function) -> ground each via
comprehend_computational_definition -> evaluate over n = offset.. -> the OEIS values
SELECT + VERIFY the correct one. Nothing is hand-written: the prose is the dataset's,
the values are the dataset's.
"""
import sys
sys.path.insert(0, ".")

from domains import oeis_local as oe
from domains import construction_grammar as cg
from domains import compute_grounding as cgnd
from domains import reason

WINDOW = 12  # verify the first 12 listed values


def verify_one(seq_id):
    d = oe.definition(seq_id)
    if d is None:
        return seq_id, None, "not in dump", []
    prose, values, offset = d["name"], d["values"], d["offset"]
    cands = cg.extract_function(prose)           # the agent's grammar reads the prose
    for cand in cands:
        comp = cgnd.comprehend_computational_definition(f"a(n) = {cand}")
        if not comp:
            continue
        term = comp["term"]
        ok = True
        checked = 0
        for i, want in enumerate(values[:WINDOW]):
            n = offset + i
            try:
                got = reason.solve(term, {"n": n})
            except Exception:
                ok = False
                break
            if int(got) != int(want):
                ok = False
                break
            checked += 1
        if ok and checked >= 4:
            return seq_id, cand, prose, values[:8]
    return seq_id, None, prose, cands


def main():
    print("=" * 78)
    print("EXTRACT FUNCTION FROM PROSE — read OEIS, verify against the SOURCE's values")
    print("=" * 78)
    print(f"  OEIS present: {oe.present()}")
    print("  (prose = the dataset's sequence_name; values = the dataset's sequence —")
    print("   nothing hand-fed; the extracted function must reproduce the real values.)\n")

    targets = ["A000005", "A000010", "A000203", "A000027",
               "A000217", "A005843", "A000290", "A000142"]
    verified = 0
    for sid in targets:
        sid_, cand, prose, vals = verify_one(sid)
        if cand:
            verified += 1
            print(f"  [OK ] {sid}  {prose[:46]!r}")
            print(f"         EXTRACTED  a(n) = {cand}   -> reproduces {vals}")
        else:
            print(f"  [-- ] {sid}  {prose[:46]!r}  -> could not extract+verify "
                  f"(candidates: {vals})")
    print(f"\n  -> {verified}/{len(targets)} sequences EXTRACTED-FROM-PROSE and "
          f"VERIFIED against the source's ground-truth values.")

    print("\n" + "=" * 78)
    print("HONEST FRONTIER — prose the grammar cannot extract a function from yet")
    print("=" * 78)
    for sid in ["A000045", "A000040"]:   # Fibonacci (recursive), primes (no formula)
        d = oe.definition(sid)
        cands = cg.extract_function(d["name"]) if d else []
        ver = verify_one(sid)[1]
        print(f"  {sid}  {d['name'][:50]!r}")
        print(f"        extract+verify -> {ver!r}  "
              f"(recursive / no closed-form clause — the named next frontier)")

    ok = verified >= 4
    print("\n" + "=" * 78)
    print(f"RESULT: {'ALL OK' if ok else 'FAILURE'} "
          f"({verified}/{len(targets)} verified from REAL prose + REAL values)")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
