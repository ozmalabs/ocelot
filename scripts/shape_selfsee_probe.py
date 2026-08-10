#!/usr/bin/env python3
"""SHAPE-SELFSEE — can the jabberwock NAME, and then DETECT, the shape of the
defects this project keeps catching by hand?

Pre-registered in VISION_SHAPE_SELFSEE_PREREG.md (committed BEFORE this ran).

ARCHITECTURE (CLAUDE.md): this file is a WORLD ADAPTER and nothing else. It
carries I/O — it hands the agent verbatim code and English, calls the agent's
OWN faculties (converse / read_function / AntiUnify / induce_concern /
categorise_by_shape), and reads verdicts back. There is NO Python conditional
here that decides what the shape IS. The `flagged` predicate below is a
MECHANICAL read of a verdict the agent already produced (minted / residual /
None), never a judgement about the code.

§13.1: the naming prompt is CODE ONLY. It contains no shape name and no
generator. D5-D8 are WITHHELD from naming and appear only at detection.

OFF by default: never imported by the bench; run explicitly.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# §10.1 RULE 3: the preamble MUST run BEFORE any domains.* import binds the
# engine. A preamble that runs afterwards is a no-op that looks correct.
from domains import engine_provenance as ep  # noqa: E402
ep.ensure_tree_engine()
ep.engine_preamble()

# The bench must never mutate the real boot seeds (two agents are live).
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_reading                          # noqa: E402
from domains.teach import categorise_by_shape             # noqa: E402
from domains.reflective_faculty import induce_concern     # noqa: E402

WILD = "·?·"

# ---------------------------------------------------------------------------
# THE ITEM SET — frozen in the pre-registration. 8 MATCHED pairs: each pair is
# the same function differing ONLY in the defect, so an instrument that
# separates them must be reading the DEFECT, not the construction.
# ---------------------------------------------------------------------------
PAIRS = [
    # 1 — osi: the real one (domains/complex_cells.py:214). A dead cell scores
    #     a flawless 0.0 floor. Twin returns a sentinel that cannot be a score.
    ("osi",
     "def osi(tc):\n"
     "    a, b = tc[0], tc[1]\n"
     "    return float((a - b) / (a + b)) if (a + b) > 1e-9 else 0.0\n",
     "def osi(tc):\n"
     "    a, b = tc[0], tc[1]\n"
     "    return float((a - b) / (a + b)) if (a + b) > 1e-9 else None\n"),
    # 2 — the catalogue read.
    ("catalogue_name",
     "def catalogue_name(entry):\n"
     "    name = entry.get('Name', '')\n"
     "    return name\n",
     "def catalogue_name(entry):\n"
     "    name = entry['title']\n"
     "    return name\n"),
    # 3 — the cumulative-mean temporal reference.
    ("sustained_ref",
     "def sustained_ref(ref, value, n):\n"
     "    ref = value if n == 0 else ref + (value - ref) / n\n"
     "    return value - ref\n",
     "def sustained_ref(ref, value, n):\n"
     "    ref = None if n < 2 else ref + (value - ref) / n\n"
     "    return value - ref\n"),
    # 4 — Pick vs PickUnique.
    ("pick",
     "def pick(candidates):\n"
     "    chosen = candidates[0]\n"
     "    return chosen\n",
     "def pick(candidates):\n"
     "    chosen = one_or_raise(candidates)\n"
     "    return chosen\n"),
    # ---- WITHHELD FROM NAMING (detection only) ----
    # 5 — visits counted as firings.
    ("tick_count",
     "def tick_count(rules):\n"
     "    n = sum(r.visits for r in rules)\n"
     "    return n\n",
     "def tick_count(rules):\n"
     "    n = sum(r.firings for r in rules)\n"
     "    return n\n"),
    # 6 — the high-water mark read as a per-N figure.
    ("mem_per_cell",
     "def mem_per_cell(usage, n):\n"
     "    total = usage.ru_maxrss\n"
     "    return total / n\n",
     "def mem_per_cell(counter, n):\n"
     "    total = counter.bytes_allocated_since_start\n"
     "    return total / n\n"),
    # 7 — the empty file that reads as a pass.
    ("suite_passed",
     "def suite_passed(path):\n"
     "    failures = read_lines(path)\n"
     "    return len(failures) == 0\n",
     "def suite_passed(path):\n"
     "    failures = read_lines_or_raise(path)\n"
     "    return len(failures) == 0\n"),
    # 8 — the skip-guard hiding a missing fixture.
    ("check_fixture",
     "def check_fixture(path):\n"
     "    ok = exists(path)\n"
     "    return skip(path) if not ok else run(path)\n",
     "def check_fixture(path):\n"
     "    ok = exists(path)\n"
     "    return fail(path) if not ok else run(path)\n"),
]
SHOWN_AT_NAMING = 4          # pairs 1-4; 5-8 are withheld


def boot():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def au(native, values):
    """The agent's OWN least-general-generalization Term."""
    return native.evaluate(
        {"type": "AntiUnify", "values": {"type": "Lit", "value": values},
         "wild": WILD}, {})


def read(agent, src):
    """The agent reads the source ITSELF (stdlib AST ingest -> its own
    skeleton -> its own ShapeDecode). Mechanical call; no decision here."""
    return code_reading.read_function(agent, src)


def flagged(reading):
    """MECHANICAL read-back of a verdict the AGENT produced: did its own decode
    fail to cover this code (mint / residual)? Not a judgement about the code."""
    return bool(reading.get("minted")) or bool(reading.get("residual"))


def fisher_2x2(a, b, c, d):
    """Two-sided Fisher exact on [[a,b],[c,d]]. No scipy dependency."""
    from math import comb
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def p_tab(x):
        return (comb(r1, x) * comb(n - r1, c1 - x)) / comb(n, c1)
    obs = p_tab(a)
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    return sum(p_tab(x) for x in range(lo, hi + 1) if p_tab(x) <= obs + 1e-12)


def main():
    print("=" * 78)
    print("SHAPE-SELFSEE — pre-registered: VISION_SHAPE_SELFSEE_PREREG.md")
    print(ep.provenance_line())
    print("=" * 78)

    agent = boot()
    native = agent.s._inner
    out = {"engine": ep.provenance_line(), "naming": {}, "detection": {}}

    # =====================================================================
    # PHASE A — NAMING. The instances go in VERBATIM. No shape name, no
    # generator, no pre-grouping, no prose of mine.
    # =====================================================================
    print("\n" + "=" * 78)
    print("PHASE A — NAMING (through the agent's OWN front doors)")
    print("=" * 78)

    # A1 — the NL front door, code verbatim.
    print("\n--- A1: converse (NL front door), the code put to it VERBATIM ---")
    a1 = []
    for name, defective, _ in PAIRS[:SHOWN_AT_NAMING]:
        q = defective.strip()
        reply = agent.converse(q, speech_act="statement")
        a1.append({"q": q, "reply": reply})
        print(f"\n  Q (verbatim code):\n    " + q.replace("\n", "\n    "))
        print(f"  A: {reply!r}")
    # The one English question — it names NO shape and NO generator.
    for q in ("What shape do these four things share?",
              "Is that one shape or several?",
              "Have you seen that shape before?"):
        reply = agent.converse(q, speech_act="question")
        a1.append({"q": q, "reply": reply})
        print(f"\n  Q: {q}\n  A: {reply!r}")
    out["naming"]["converse"] = a1

    # A2 — the code register: the agent reads each instance itself.
    print("\n--- A2: the code register (agent's own AST ingest + ShapeDecode) ---")
    a2 = {}
    for name, defective, _ in PAIRS[:SHOWN_AT_NAMING]:
        r = read(agent, defective)
        a2[name] = {"construction": r.get("construction"), "minted": r.get("minted"),
                    "residual": r.get("residual"), "skeleton": r.get("skeleton"),
                    "what_does": r.get("what_does")}
        print(f"  {name:16s} construction={r.get('construction')!r:26s} "
              f"minted={r.get('minted')} residual={r.get('residual')}")
    out["naming"]["code_register"] = a2

    # A3 — AntiUnify over the skeletons THE AGENT DERIVED. "What shape do these
    # share?" asked with the agent's own generalization operator.
    print("\n--- A3: AntiUnify over the agent's OWN derived skeletons ---")
    skels = [a2[name]["skeleton"] for name, _, _ in PAIRS[:SHOWN_AT_NAMING]]
    shared = au(native, skels)
    print(f"  skeletons: {skels}")
    print(f"  AntiUnify(shared shape) = {shared!r}")
    out["naming"]["antiunify_shared"] = repr(shared)

    # A4 — categorise_by_shape on the instance TEXT (the code itself, verbatim).
    print("\n--- A4: categorise_by_shape on the code text (verbatim) ---")
    a4 = {}
    for name, defective, _ in PAIRS[:SHOWN_AT_NAMING]:
        cat = categorise_by_shape(agent, "TaughtHint", {"src": defective})
        a4[name] = cat
        print(f"  {name:16s} -> {cat!r}")
    out["naming"]["categorise_by_shape"] = a4

    # A5 — the sd-loop on the agent's OWN derived skeletons: held, or mint?
    print("\n--- A5: induce_concern (sd-loop) on the agent's own skeletons ---")
    a5 = {}
    for name, defective, _ in PAIRS[:SHOWN_AT_NAMING]:
        sk = a2[name]["skeleton"]
        r = induce_concern(agent, sk, name_hint=f"selfsee_{name}")
        a5[name] = {"minted": r.get("minted"), "covered_by": r.get("covered_by"),
                    "closest": r.get("closest_held_shape")}
        print(f"  {name:16s} minted={r.get('minted')} covered_by={r.get('covered_by')!r} "
              f"closest={r.get('closest_held_shape')!r}")
    out["naming"]["induce_concern"] = a5

    # =====================================================================
    # PHASE B — DETECTION. 8 matched pairs, both arms. THE REAL TEST.
    # =====================================================================
    print("\n" + "=" * 78)
    print("PHASE B — DETECTION: 8 matched pairs (defect vs correct twin)")
    print("=" * 78)
    print(f"{'pair':16s} {'arm':10s} {'construction':26s} {'minted':7s} {'residual':10s} flagged")
    rows = []
    for name, defective, correct in PAIRS:
        for arm, src in (("DEFECT", defective), ("CORRECT", correct)):
            r = read(agent, src)
            f = flagged(r)
            rows.append({"pair": name, "arm": arm, "construction": r.get("construction"),
                         "minted": r.get("minted"), "residual": r.get("residual"),
                         "flagged": f, "what_does": r.get("what_does")})
            print(f"{name:16s} {arm:10s} {str(r.get('construction')):26s} "
                  f"{str(r.get('minted')):7s} {str(r.get('residual')):10s} {f}")
    out["detection"]["rows"] = rows

    d_flag = sum(1 for r in rows if r["arm"] == "DEFECT" and r["flagged"])
    c_flag = sum(1 for r in rows if r["arm"] == "CORRECT" and r["flagged"])
    p = fisher_2x2(d_flag, 8 - d_flag, c_flag, 8 - c_flag)
    print(f"\n  2x2: DEFECT flagged {d_flag}/8 | CORRECT flagged {c_flag}/8")
    print(f"  Fisher exact (two-sided) p = {p:.6f}")

    # Do the twins read IDENTICALLY? (the null in its sharpest form)
    ident = 0
    for name, defective, correct in PAIRS:
        rd, rc = read(agent, defective), read(agent, correct)
        same = (rd.get("construction") == rc.get("construction")
                and rd.get("minted") == rc.get("minted")
                and rd.get("residual") == rc.get("residual")
                and rd.get("what_does") == rc.get("what_does"))
        ident += same
        print(f"  {name:16s} defect-twin reading IDENTICAL: {same}")
    print(f"\n  identical readings: {ident}/8 pairs")
    out["detection"]["identical_pairs"] = ident

    # AntiUnify each pair: the agent's own operator on defect vs twin.
    print("\n--- AntiUnify(defect, correct) per pair — the agent's own LGG ---")
    for name, defective, correct in PAIRS:
        sd = read(agent, defective).get("skeleton")
        sc = read(agent, correct).get("skeleton")
        print(f"  {name:16s} D={sd} C={sc} -> LGG={au(native, [sd, sc])!r}")

    # Decision rule, applied mechanically from the pre-registration.
    if d_flag == 8 and c_flag == 8:
        verdict = "INERT (flags everything — no discrimination)"
    elif d_flag == 0 and c_flag == 0:
        verdict = "INERT (flags nothing — no discrimination)"
    elif d_flag >= 7 and c_flag <= 1 and p < 0.05:
        verdict = "HIT (H2 supported)"
    else:
        verdict = "NULL (H2-null: the arms do not separate)"
    out["detection"]["d_flagged"] = d_flag
    out["detection"]["c_flagged"] = c_flag
    out["detection"]["fisher_p"] = p
    out["detection"]["verdict"] = verdict
    print(f"\n  PRE-REGISTERED VERDICT: {verdict}")

    # Did it file anything about itself?
    print("\n--- did the agent file a concern? ---")
    gaps = agent.converse("What gaps do you have?", speech_act="question")
    print(f"  'What gaps do you have?' -> {gaps!r}")
    out["gaps_reply"] = gaps

    dest = os.path.join(ROOT, "results", "shape_selfsee.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
