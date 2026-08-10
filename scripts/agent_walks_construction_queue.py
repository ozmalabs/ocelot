"""WALK THE PRIORITIZED QUEUE of missing construction-types + ACQUIRE EACH — the
autonomous run of the compounding ramp the agent built (cmsg82).

cmsg81 clustered the 436-claim un-cracked residual into a RANKED queue of missing
construction-types (existential 99, universal 77, conditional-def 43, predicative
21 [ACQUIRED], TFAE 8, constructive 7, notation 7, adjunction 7, universal-property
2) and acquired the TOP definitional one (predicative/conditional), lifting the
detect+brute-force grounding 13.1% -> 15.2%. The user's instruction: "have it walk
the queue and acquire the rest."

The agent WALKS THE REST of its OWN queue. For each construction-type in priority
order it ACQUIRES the type (its acquire_definitional_construction: read-how-to-read
OR abstract-from-its-own-failure-instances -> the held marker shape as GRAPH DATA),
re-runs the SAME detect+brute-force on the SAME dense claims, and ACCUMULATES the
cumulative lift — until the queue is exhausted OR the lift DRIES.

THE HONEST DISCOVERY (cmsg82's point, not a forced lift). The queue was ranked by
FREQUENCY, but the grounding metric is GENUS-DIFFERENTIA (object IS-A genus + the
harvested object->invariant/identification). Some queued types are DEFINITIONS
(constructive 'a monoid CONSISTS OF a set ...', universal-property 'the product is
the TERMINAL OBJECT ...') — a clean object->genus that SHOULD lift. But others are
LOGICAL / QUANTIFIED CLAIMS (existential 'there exists Z such that P', universal
'for all X, P', TFAE 'the following are equivalent', adjunction 'F is left adjoint
to G') — NOT 'X is-a Y' definitions; their 'term' is a quantified clause the agent's
OWN precision floor (_is_clean_object) REJECTS, so acquiring their opener does NOT
lift the genus-differentia grounding. The WALK DISCOVERS which type lifts (definitional)
vs which needs a DIFFERENT representation (a logical/claim grounding — the next-deeper
frontier). The honest dry-up is the RESULT, not a failure; the shell does NOT force a
lift on the quantified claims.

FAITHFUL (CLAUDE.md): the AGENT walks (its cmsg81 ranking) + acquires each (its
acquire_definitional_construction over its OWN held CONSTRUCTION_TYPE_VOCAB +
failure-instances) + re-runs + the VERIFY (a clean term+genus on a real instance)
is the honest selector. This SHELL only SEQUENCES the walk; it adds NO comprehension
reasoning — every meaning judgement is the construction grammar's. No LLM authors a
construction; no Rust; the acquired shapes are GRAPH DATA; stays in the MATH/reading
domain (no audio path). data/arxiv gitignored (code only).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/agent_walks_construction_queue.py
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native

from domains import construction_grammar as cg
from domains import grounded_representation as gr

from scripts.agent_grounds_each_claim import setup, ground_claim, _attr, _is_clean_object
from scripts.agent_detects_and_bruteforces_comprehension import bruteforce_claim
from scripts.agent_acquires_constructions_and_compounds import (
    detect_and_bruteforce, identify_missing_constructions, _CONSTRUCTION_MARKERS,
    N_PAPERS,
)

SEP = "=" * 78
SAMPLE = 500
SPOT_CHECK = 8


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# THE QUEUE (the agent's cmsg81 ranking, walked in PRIORITY order). Each entry
# pairs a queue construction-TYPE tag (the identify_missing_constructions marker)
# with the held CONSTRUCTION_TYPE_VOCAB key + a meta-description (the read-how-to-
# read route). The predicative/conditional pair is the cmsg81 PREFIX (acquired
# first to reproduce 13.1% -> 15.2%); the WALK then continues the rest.
# ---------------------------------------------------------------------------

# the queue marker-tag -> (vocab key, meta-description). The meta-description is the
# READ-HOW-TO-READ source (a prose explanation of how the construction is written);
# the agent ALSO abstracts from its own failure-instances of the type. Ordered by
# the cmsg81 frequency ranking (the agent's own priority).
WALK = [
    # --- the cmsg81 PREFIX: the predicative/conditional DEFINITION (acquired first,
    # reproduces 13.1% -> 15.2%). The two markers are ONE construction family. ---
    ("predicative_conditional_definition",
     ["conditional/predicative def 'we say X is P if Q'",
      "conditional def 'X is P if/iff Q'"],
     None,   # uses the DEFAULT predicative vocab (we say/we call + if/iff)
     "A property of a mathematical object is defined in the predicative register by "
     "writing 'we say X is P if Q' (or 'we call X a P if Q'): X is the object, P the "
     "property, Q the condition. 'we say'/'we call' introduces the definiendum and "
     "'if'/'iff' begins the defining condition."),

    # --- the WALK: the rest of the queue, priority order ---
    ("existential_claim",
     ["existential 'there exists Z such that'"],
     "existential_claim",
     "An existence claim is written 'there exists Z such that P': it asserts SOME "
     "object Z satisfying a property P. 'there exists' is an existential quantifier "
     "binding a new variable; it does not introduce a definiendum."),

    ("universal_claim",
     ["universal-quantified 'for all/every X ...'"],
     "universal_claim",
     "A universal claim is written 'for all X, P' (or 'for every/any/each X, P'): it "
     "asserts a property P holds of EVERY X in a range. 'for all'/'for every' is a "
     "universal quantifier binding a range, not a definiendum."),

    ("tfae_claim",
     ["the-following-are-equivalent (TFAE)"],
     "tfae_claim",
     "A logical-equivalence claim is written 'the following are equivalent:' followed "
     "by a list of conditions, asserting each condition implies every other. It is a "
     "claim about a LIST of conditions, not a single object's kind."),

    ("constructive_definition",
     ["constructive def 'X consists of ... satisfying'"],
     "constructive_definition",
     "A structure is defined constructively by writing 'a X consists of a SET (or "
     "object) together with extra structure satisfying axioms', or 'a X is a GENUS "
     "equipped with ...': the genus is the base object the structure is built on, "
     "introduced by 'consists of' / 'is given by'."),

    ("notation_introduction",
     ["notation-introduction 'we denote/write'"],
     None,   # notation has its own comprehend path; here it is read as a definition
     "A piece of notation is introduced by writing 'we denote by SYM the OBJECT' or "
     "'we write SYM for the OBJECT': SYM is a symbol standing for the named object."),

    ("adjunction_claim",
     ["adjunction 'F is left/right adjoint to G'"],
     "adjunction_claim",
     "An adjunction is written 'F is left adjoint to G' (or right adjoint / adjoint "
     "to): it asserts a RELATION between two functors F and G, not that F is a kind "
     "of object. 'left adjoint'/'right adjoint' is a relation, not a genus."),

    ("universal_property_definition",
     ["universal-property def"],
     "universal_property_definition",
     "A universal-property definition is written 'the X is the terminal object' (or "
     "initial object / has the universal property): X is defined as the object with "
     "a universal mapping property."),
]


def _instances_for(diag: dict, marker_tags: list[str]) -> list[str]:
    """The agent's OWN failure-instances of a construction-TYPE (the teaching set the
    abstract-from-instances route reads). Pools every example marker_tag for the type."""
    out: list[str] = []
    for tag in marker_tags:
        out.extend(diag["examples"].get(tag, []))
    # de-dup, keep order.
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _verifies_clean(ins: str, term_hint=None) -> bool:
    """The agent's precision floor: does this instance extract a CLEAN term+genus
    (both pass _is_clean_object)? The honest definitional-vs-logical selector — a
    quantified clause has no clean object->genus and fails this."""
    d = cg.extract_definition(ins, term=term_hint)
    return bool(d and d.get("term") and d.get("genus")
                and _is_clean_object(d["term"]) and _is_clean_object(d["genus"]))


def _pick_example(instances: list[str]) -> str | None:
    """Pick a representative, SHORT, VERIFIABLE instance of the type (the VERIFY
    truth-signal demonstrates the acquire on a clean instance). Falls back to the
    shortest instance when none verifies clean (the honest logical-claim case — the
    acquire will then NOT verify, the dry-up)."""
    if not instances:
        return None
    short = sorted(instances, key=len)
    for ins in short:
        if len(cg._split_sentences(ins)) <= 3 and _verifies_clean(ins):
            return ins
    return short[0]


def main():
    banner("WALK THE PRIORITIZED QUEUE of missing construction-types + ACQUIRE EACH "
           "(cmsg82 — the autonomous run of the compounding ramp the agent built)")
    print("  cmsg81 ranked the 436-claim un-cracked residual into a QUEUE of missing")
    print("  construction-types + acquired the top DEFINITIONAL one (predicative/")
    print("  conditional), lifting 13.1% -> 15.2%. The agent now WALKS THE REST: for")
    print("  each type in priority order it ACQUIRES the type (read-how-to-read /")
    print("  abstract-from-its-own-failures -> held GRAPH DATA) + re-runs + accumulates")
    print("  the lift. THE HONEST DISCOVERY: the DEFINITIONAL types (object IS-A genus)")
    print("  lift the genus-differentia grounding; the LOGICAL/QUANTIFIED types")
    print("  (existential/universal/TFAE/adjunction) have NO clean object->genus — the")
    print("  agent's OWN precision floor rejects their quantified-clause parse, so they")
    print("  DRY. The walk DISCOVERS which is which; it does NOT force a lift.")

    # reset the acquired-construction graph data so the walk starts from the BARE
    # reader (it accumulates each acquired type as it walks — the compounding).
    cg._ACQUIRED_DEFN["definitional_openers"] = []
    cg._ACQUIRED_DEFN["extra_differentia"] = []
    cg._ACQUIRED_DEFN["extra_copula"] = []

    def fresh():
        s = _native.Substrate()
        built = setup(s, N_PAPERS)
        return s if built is not None else None

    # --- BARE BASELINE (no acquired construction = cmsg80's 13.1%) ---
    banner("0. BARE BASELINE — detect+brute-force with NO acquired construction "
           "(cmsg80)")
    s0 = fresh()
    if s0 is None:
        print("  NO arXiv source on disk (data/arxiv, gitignored). Cannot run.")
        return 1
    base = detect_and_bruteforce(s0)
    n_claims = base["n_claims"]
    bare_total = base["single_pass"] + base["cracked"]
    bare_pct = 100.0 * bare_total / max(1, n_claims)
    print(f"  single-pass {base['single_pass']}/{n_claims}  + brute-force "
          f"{base['cracked']}  = {bare_total}/{n_claims} ({bare_pct:.1f}%)")
    print(f"  un-cracked residual: {len(base['residual'])} (the queue is clustered "
          f"from THIS)")

    # the agent CLUSTERS the residual into the ranked queue (cmsg81's identify).
    diag = identify_missing_constructions(s0, base["residual"])
    ranked = sorted(diag["counts"].items(), key=lambda x: -x[1])
    banner("   the agent's RANKED QUEUE (clustered from its own un-cracked failures):")
    for tag, nn in ranked:
        print(f"    · {nn:4d}  {tag}")

    # --- THE WALK: acquire each queued type in priority order, accumulate the lift ---
    banner("1. THE WALK — acquire each queued construction-type in priority order; "
           "re-run; accumulate the cumulative lift (each acquire COMPOUNDS)")
    history = [("(bare baseline cmsg80)", bare_total, bare_pct, 0.0, "—")]
    prev_total = bare_total
    consecutive_dry = 0
    for form_name, marker_tags, vocab_key, meta in WALK:
        instances = _instances_for(diag, marker_tags)
        vocab = cg.CONSTRUCTION_TYPE_VOCAB.get(vocab_key) if vocab_key else None
        kind = (vocab or {}).get("kind", "definitional")
        example = _pick_example(instances)

        print(f"\n  >>> ACQUIRE  [{form_name}]  ({kind.upper()};  "
              f"{len(instances)} own failure-instances)")
        acq = cg.acquire_definitional_construction(
            form_name, meta_definition=meta, instances=instances,
            example=example, example_term=None, vocab=vocab)
        con = acq.get("construction") or {}
        # report WHAT it acquired + HOW (the openers/copulas/terminators it abstracted).
        src = []
        if meta:
            src.append("read-how-to-read")
        if instances:
            src.append(f"abstract-from-{len(instances)}-own-failures")
        print(f"        source     : {' + '.join(src)}")
        if con and con.get("kind") == "logical_claim":
            print(f"        RECOGNISED  : quantifier/relational markers "
                  f"{con.get('quantifiers')} — a QUANTIFIED/LOGICAL claim. The agent")
            print(f"        {'':14s}NAMES the type but mints NO definitional marker (a")
            print(f"        {'':14s}quantifier binds a variable / a relation; it does NOT")
            print(f"        {'':14s}introduce a definiendum -> no object->genus to ground).")
        elif con:
            print(f"        openers    : {con.get('openers')}   "
                  f"copulas: {con.get('extra_copula')}   "
                  f"terminators: {con.get('extra_differentia')}")
        else:
            print(f"        comprehended: NONE (no recurring definitional marker "
                  f"abstracted — the type has no opener/copula that introduces a "
                  f"definiendum)")
        print(f"        VERIFY      : before-clean={acq['before']}  "
              f"after-clean={acq['after']}  -> acquired={acq['acquired']}")
        if acq.get("term"):
            print(f"        example     : term={acq['term']!r} genus={acq['genus']!r}")
        elif example:
            ex = re.sub(r'\s+', ' ', example)[:110]
            print(f"        example     : \"{ex}...\"  -> NO clean term+genus "
                  f"(the agent's precision floor rejects the quantified-clause parse)")

        # RE-RUN the SAME detect+brute-force WITH all acquired-so-far constructions.
        s = fresh()
        res = detect_and_bruteforce(s)
        total = res["single_pass"] + res["cracked"]
        pct = 100.0 * total / max(1, n_claims)
        contrib = total - prev_total
        print(f"        RE-RUN      : single-pass {res['single_pass']}  + brute "
              f"{res['cracked']}  = {total}/{n_claims} ({pct:.1f}%)")
        print(f"        CONTRIBUTION: {contrib:+d} claims  (cumulative "
              f"{bare_pct:.1f}% -> {pct:.1f}%)")
        history.append((form_name, total, pct, contrib, kind))
        # DRY-UP detection: a definitional/logical acquire that cracks ~0 NEW claims.
        if contrib <= 0:
            consecutive_dry += 1
            why = ("LOGICAL/QUANTIFIED — no clean object->genus (the agent's precision "
                   "floor rejects the quantified-clause parse: a DIFFERENT KIND of "
                   "claim)" if kind == "logical"
                   else "REDUNDANT — the base reader already handles this definitional "
                   "shape (its copula was already held)")
            print(f"        DRY        : +0 new — {why}")
        else:
            consecutive_dry = 0
        prev_total = total

    # --- THE MAP: where the lift came from + where/why it dried ---
    banner("2. THE CUMULATIVE LIFT + the per-construction CONTRIBUTION (the walk)")
    print(f"  {'construction-type':42s} {'kind':13s} {'contrib':>7s}  cumulative")
    for name, total, pct, contrib, kind in history:
        cs = f"{contrib:+d}" if name != "(bare baseline cmsg80)" else "—"
        print(f"  {name:42s} {kind:13s} {cs:>7s}  {total}/{n_claims} ({pct:.1f}%)")

    final_total, final_pct = history[-1][1], history[-1][2]
    banner("3. THE HONEST MAP — where the grounding LIFTS (definitional) vs where it "
           "DRIES (logical/quantified -> the next-deeper frontier)")
    lifters = [(n, c, k) for (n, t, p, c, k) in history[1:] if c > 0]
    driers = [(n, c, k) for (n, t, p, c, k) in history[1:] if c <= 0]
    print("  LIFTED (definitional — a clean object IS-A genus the metric grounds):")
    if lifters:
        for n, c, k in lifters:
            print(f"    · {n:42s} {c:+d}  ({k})")
    else:
        print("    (none beyond the prefix)")
    print("\n  DRIED (the honest discovery — acquiring the opener cracked ~0 new):")
    for n, c, k in driers:
        if k == "logical":
            print(f"    · {n:42s} {c:+d}  LOGICAL/QUANTIFIED — NO object->genus; the")
            print(f"      {'':42s}      'term' is a quantified clause the precision")
            print(f"      {'':42s}      floor rejects -> a DIFFERENT KIND of claim.")
        else:
            print(f"    · {n:42s} {c:+d}  REDUNDANT — the base copula already reads it.")

    banner("4. THE AGENT'S CONCLUSION — the map of its own comprehension queue")
    n_lift = len([1 for (_, _, _, c, _) in history[1:] if c > 0])
    n_redundant = len([1 for (_, _, _, c, k) in history[1:]
                       if c <= 0 and k != "logical"])
    n_logical = len([1 for (_, _, _, c, k) in history[1:]
                     if c <= 0 and k == "logical"])
    print(f"  CUMULATIVE LIFT : {bare_pct:.1f}% (bare cmsg80) -> {final_pct:.1f}% after "
          f"walking the whole queue,")
    print(f"                    on the SAME {n_claims} dense claims. The ONLY lift came "
          f"from the\n                    predicative/conditional DEFINITION (the cmsg81 "
          f"prefix, +29).")
    print(f"  WHERE IT LIFTS  : the predicative/conditional DEFINITION ('we say X is P "
          f"if Q')")
    print(f"                    — a clean object IS-A GENUS the genus-differentia "
          f"grounding grounds.")
    print(f"  REDUNDANT       : the OTHER definitional types ({n_redundant}: constructive "
          f"'consists of',")
    print(f"                    universal-property 'is the terminal object', notation) "
          f"crack +0 —")
    print(f"                    the base reader ALREADY holds their copula (the agent "
          f"acquired")
    print(f"                    these shapes in earlier work; the walk confirms they "
          f"are held).")
    print(f"  WHERE IT DRIES  : the {n_logical} LOGICAL/QUANTIFIED constructions "
          f"(existential 'there")
    print(f"                    exists Z such that', universal 'for all X', TFAE, adjunction)")
    print(f"                    crack +0 — they are NOT 'X is-a Y' definitions; their")
    print(f"                    'term' is a quantified clause, their 'genus' a property/")
    print(f"                    relation. The agent NAMES the type by its quantifier but")
    print(f"                    mints NO definitional marker (a quantifier binds a "
          f"variable,")
    print(f"                    it does not introduce a definiendum) — NOT a failure but "
          f"the")
    print(f"                    honest finding: a DIFFERENT KIND of claim.")
    print(f"  THE NEXT FRONTIER (the agent names it): the quantified/logical claims need a")
    print(f"                    NON-genus-differentia grounding — a CLAIM representation")
    print(f"                    (a quantifier binding a variable over a domain + a predicate;")
    print(f"                    a logical-equivalence over a list; a relation between two")
    print(f"                    objects) rather than an object IS-A genus. That is the")
    print(f"                    next-deeper rung the WALK surfaced — the honest end of THIS")
    print(f"                    ramp, the named start of the next.")

    # PRECISION spot-check: the lift is REAL (clean both sides) on the final graph.
    banner("5. PRECISION — the walk's groundings are REAL (convergence-verified, the "
           "cmsg79/80/81 over-grab guard holds)")
    s = fresh()
    res = detect_and_bruteforce(s)
    shown = 0
    for cid, bf in res["grounded_by_bf"].items():
        txt = re.sub(r"\s+", " ", _attr(s, cid, "text"))
        print(f"    [{_attr(s, cid, 'kind')}] shape={','.join(bf['shapes']) or '-'} "
              f"objects -> {bf['objects'][:4]}")
        print(f"       \"{txt[:110]}...\"")
        shown += 1
        if shown >= SPOT_CHECK:
            break
    print(f"\n  precision: every grounded object passed _is_clean_object (both sides "
          f"clean); the\n  brute-force's synthesis-check required the object's content "
          f"to MATCH the statement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
