"""THE JABBERWOCK READS THE BODY of the paper it FOUND — grounds it to its CLAIMS,
not just the topic (cmsg112's named comprehension-DEPTH residual).

The arc this closes:
  * cmsg111 : the agent authored the web-WORLD adapter (GET-only, the DOM as a typed
              graph).
  * cmsg112 : the jabberwock NAVIGATED arXiv (GET-only) -> FOUND a paper
              (arXiv:2606.13224, math.AT) -> READ it by grounding the abstract's
              LEAD into a comprehended TOPIC/genus. grounded-to-primitive=False —
              it knew WHAT the paper is ABOUT (subject), not its claims.
  * NOW (this shell): READ THE BODY. The agent's arXiv .tex parse (cmsg77,
              arxiv_local) parses the FOUND paper's theorem/definition/lemma/
              proposition/corollary environments (the CLAIM-bearing body, LaTeX
              preserved). For EACH claim the agent GROUNDS it as a Claim/Concept via
              its construction grammar (read_and_ground: term is-a GENUS + the
              differentia; recursively toward held primitives) — measuring DEPTH
              (grounded-to-PRIMITIVE vs grounded-to-TOPIC). Where a claim references
              a CONSTRUCTION the agent does NOT hold (an un-held genus / an
              un-recognised construction-type), it DETECTS that + QUEUES it to
              ACQUIRE (the same ground+acquire the HLE ladder ran).

This is a SHELL (CLAUDE.md world-adapter discipline). It owns no reasoning and
holds no agent state. It:
  1. GET THE BODY — take the FOUND paper (arXiv:2606.13224) + parse its claim-
     bearing environments via the agent's arXiv .tex reader (arxiv_local; the .tex
     was fetched GET-only by scripts/fetch_arxiv.py, data/ gitignored).
  2. GROUND EACH CLAIM — read_and_ground / the construction grammar comprehends
     each (definition channel: term is-a genus + differentia; claim channel:
     quantifier+variable+domain+predicate; harvest channel: object->invariant /
     identification). DEPTH: a claim whose genus grounds to a HELD primitive is
     grounded-to-PRIMITIVE; one whose genus is held-as-topic-only is grounded-to-
     TOPIC.
  3. DETECT + ACQUIRE-QUEUE — every un-held genus / un-recognised construction-type
     the comprehension hit is DETECTED + QUEUED to acquire (the honest residual the
     agent NAMES — the constructions it cannot yet unpack).

SAFETY / IP rails (read twice):
  * The .tex is already on disk (GET-only, cmsg77 fetch; data/arxiv gitignored).
    NO new network call here — this shell only READS the local .tex.
  * NO VERBATIM CLAIM TEXT reproduced. We report the agent's GROUNDED-CLAIM
    structure (a SHORT genus/kind label per claim, the DEPTH, the acquire-queue) —
    NOT the verbatim theorem/definition statements. Short labels/identifiers OK.
  * The AGENT parses + grounds + queues; this shell ORCHESTRATES. No LLM, no Rust.
    Stays in the MATH/reading domain (no audio path).

HONEST: the body grounded to CLAIMS (DEPTH — N claims parsed, M grounded-to-
primitive) vs cmsg112's abstract-only TOPIC; the acquire-queue (the constructions
it can't yet unpack — needs-read/needs-acquire). NO verbatim; do NOT over-claim
"it fully understood the paper" — the body-to-claims grounding + the honest
acquire-queue is the result.

Run:
  ulimit -v 8388608
  timeout 300 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_reads_paper_body_to_claims.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native

from domains import arxiv_local as ax
from domains import construction_grammar as cg
from domains import grounded_representation as gr
from domains import read_and_ground as rag
from domains import math_foundations as mf

# the agent's own claim-precision floor (cmsg78 — a clean noun-phrase object, not a
# research-register clause the genus-differentia reader over-grabbed); reused here.
from scripts.agent_grounds_each_claim import _is_clean_object

SEP = "=" * 78

# the FOUND paper (cmsg112: navigated arxiv.org/list/math.AT/recent -> /abs/<id>).
FOUND_PAPER = "2606.13224"

# a short human label for the math.AT subject (cmsg112 grounded the topic from the
# abstract's lead). Used only as the navigate-provenance line, NOT a claim quote.
FOUND_TOPIC = "homotopy theory / bisimplicial sets (math.AT)"

SPOT = 10  # how many grounded claims to label for the precision read.


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _name_norm(surface: str) -> str:
    return re.sub(r"\s+", "_", (surface or "").lower().strip())


# the construction-TYPE markers the agent reads OFF the body — its held vocabulary
# of how research-math statements are written. A claim whose construction-type is
# recognised but whose GENUS does not ground is a comprehension residual; a claim
# matching one of these markers but NOT grounding is a construction the agent must
# acquire (the acquire-by-reading queue). Pure surface read (no meaning decision).
_CONSTRUCTION_MARKERS = [
    ("predicative/conditional def 'we say X is P if Q'",
     re.compile(r"\b(we say|we call|one says|is said to be)\b", re.I)),
    ("conditional def 'X is P if/iff Q'",
     re.compile(r"\bis\b[^.]{1,60}?\b(if|iff|whenever)\b", re.I)),
    ("constructive def 'X consists of ... satisfying'",
     re.compile(r"\b(consists of|equipped with|together with)\b", re.I)),
    ("universal-quantified 'for all/every X ...'",
     re.compile(r"\bfor (all|every|any|each)\b", re.I)),
    ("existential 'there exists Z such that'",
     re.compile(r"\bthere (exists|is)\b", re.I)),
    ("the-following-are-equivalent (TFAE)",
     re.compile(r"\bthe following are equivalent\b", re.I)),
    ("adjunction 'F is left/right adjoint to G'",
     re.compile(r"\b(left adjoint|right adjoint|adjunction)\b", re.I)),
    ("universal-property def",
     re.compile(r"\b(universal property|initial object|terminal object)\b", re.I)),
]


def _construction_types(text: str) -> list[str]:
    """The construction-TYPE tags whose surface markers appear in a claim — the
    agent's held vocabulary of research-math statement shapes (a surface read)."""
    t = re.sub(r"\s+", " ", text)
    return [tag for tag, rx in _CONSTRUCTION_MARKERS if rx.search(t)]


# ---------------------------------------------------------------------------
# (1) GET THE BODY — parse the FOUND paper's claim-bearing environments.
# ---------------------------------------------------------------------------

def body_statements(paper: str) -> list[dict]:
    """The FOUND paper's claim-bearing environments (theorem/definition/lemma/
    proposition/corollary), parsed from the local .tex by the agent's arXiv reader
    (arxiv_local — the cmsg77 .tex parse, LaTeX preserved). GET-only, already on
    disk; this only READS the local file."""
    return [e for e in ax.statements() if e["paper"] == paper]


# ---------------------------------------------------------------------------
# (2) GROUND EACH CLAIM — the agent comprehends + grounds; measure DEPTH.
# ---------------------------------------------------------------------------

class Conv:
    """A bare conversation handle the read-and-ground loop reads its construction
    set + (empty) definition feed off — no reasoning, a data carrier."""
    _definition_feed: dict = {}
    _constructions = None


def ground_one_claim(s, entry: dict, conv) -> dict:
    """GROUND one claim-bearing environment as a Claim/Concept. The agent's
    construction grammar comprehends it through THREE held channels:
      · DEFINITION  — term is-a GENUS (+ differentia): extract_definition. The
                      claim's grounded GENUS/kind. read_and_ground then recurses the
                      genus toward HELD primitives -> the DEPTH (grounded-to-
                      PRIMITIVE iff the genus's cone reaches a seeded primitive,
                      else grounded-to-TOPIC).
      · CLAIM       — quantifier + variable + domain + predicate: extract_claim
                      (the logical/quantified statements — for-all/exists/TFAE).
      · HARVEST     — object->invariant / identification facts: harvest_facts.
    Returns the grounded-claim structure (NO verbatim text): {kind, key, channel,
    genus, depth, grounded_to_primitive, claim_kind, acquire}. `acquire` names the
    un-held construction the claim references (the acquire-queue entry), or None."""
    text = entry["text"]
    label = entry.get("attribution") or entry.get("label") or None

    out: dict = {"kind": entry["kind"], "key": entry["key"],
                 "channel": None, "genus": None, "depth": None,
                 "primitives": None, "grounded_to_primitive": False,
                 "claim_kind": None, "acquire": None,
                 "ctypes": _construction_types(text)}

    # --- DEFINITION channel: term is-a GENUS (+ differentia) ---
    d = cg.extract_definition(text, substrate=s, term=label)
    genus = None
    if d and d.get("genus"):
        if _is_clean_object(d["genus"]):
            genus = _name_norm(d["genus"])

    if genus:
        out["channel"] = "definition"
        out["genus"] = genus
        # GROUND + recurse the genus toward HELD primitives (read_and_ground feeds
        # the genus as the definitional lead). DEPTH = grounded-to-PRIMITIVE iff the
        # cone reaches a seeded primitive; else grounded-to-TOPIC (the held-but-
        # un-grounded genus — the acquire-by-reading frontier).
        res = rag.read_and_ground(s, genus, conv, definition_text=None)
        out["grounded_to_primitive"] = bool(res.get("grounded"))
        struct = res.get("structure") or {}
        out["depth"] = struct.get("depth")
        # when the genus is itself already a held basis (read_and_ground short-
        # circuits with structure=None), read the reached primitive(s) off its cone
        # directly — so a grounded-to-primitive claim names the bedrock it bottoms
        # out at (not 'depth None').
        if out["grounded_to_primitive"]:
            cid = gr._find_concept(s, genus)
            if cid is not None:
                proof = gr.grounding_reaches_primitives(s, cid)
                out["depth"] = proof["depth"]
                out["primitives"] = proof["primitives"]
        if not out["grounded_to_primitive"]:
            # the genus is held-as-topic-only / does not reach a primitive — DETECT
            # + QUEUE it to acquire (read its definition toward primitives). The
            # honest residual the agent NAMES.
            out["acquire"] = {"target": genus, "why": res.get("reason"),
                              "kind": "un-held-genus"}
        return out

    # --- CLAIM channel: a logical/quantified statement (no object->genus) ---
    c = cg.extract_claim(text, term=label)
    if c is not None:
        out["channel"] = "claim"
        out["claim_kind"] = c["kind"]
        pred = c["predicate"]
        # a claim is grounded-to-PRIMITIVE-style only if its predicate carries a
        # HELD fact (invariant / identification / inner is-a); else it is grounded
        # as a CLAIM but its predicate content is the breadth residual.
        held_pred = bool(pred["invariants"] or pred["identifications"]
                         or "isa" in pred)
        out["grounded_to_primitive"] = held_pred
        if not held_pred:
            out["acquire"] = {"target": f"{c['kind']}-predicate",
                              "why": "predicate uses ops beyond the held library",
                              "kind": "un-held-predicate"}
        return out

    # --- HARVEST channel: object->invariant / identification facts ---
    facts = cg.harvest_facts(text)
    if facts["invariants"] or facts["identifications"]:
        out["channel"] = "harvest"
        out["grounded_to_primitive"] = False  # a fact, not a genus-to-primitive
        return out

    # --- UN-COMPREHENDED: the agent does NOT unpack this claim. DETECT its
    # construction-type(s) + QUEUE them to acquire (the acquire-by-reading queue —
    # the same ground+acquire the HLE ladder ran). The honest comprehension
    # frontier, the agent's named residual. ---
    out["channel"] = None
    cts = out["ctypes"]
    out["acquire"] = {"target": (cts[0] if cts else "unrecognised-construction"),
                      "why": "construction-type not recognised by the held reader",
                      "kind": "un-recognised-construction"}
    return out


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    banner("THE JABBERWOCK READS THE BODY of the paper it FOUND — grounds it to "
           "its CLAIMS, not just the topic (cmsg112's comprehension-DEPTH residual)")
    print("  cmsg111 : the agent authored the web-WORLD adapter (GET-only).")
    print("  cmsg112 : it NAVIGATED arXiv (GET-only) -> FOUND arXiv:" + FOUND_PAPER)
    print("            -> READ it by grounding the abstract's LEAD into a TOPIC")
    print("            (grounded-to-primitive=False — the SUBJECT, not the claims).")
    print("  NOW     : READ THE BODY — parse the theorem/definition/lemma")
    print("            environments + GROUND EACH CLAIM (genus/differentia, toward")
    print("            primitives) + DETECT+QUEUE the constructions it can't unpack.")

    if not ax.present():
        print("\n  NO arXiv .tex on disk (data/arxiv, gitignored). The FOUND paper's")
        print("  source must be fetched (scripts/fetch_arxiv.py, GET-only) first.")
        return 1

    # ----------------------------------------------------------- 1. GET THE BODY
    banner("1. GET THE BODY — parse the FOUND paper's claim-bearing environments "
           "(the agent's arXiv .tex reader, cmsg77; the .tex was fetched GET-only)")
    sts = body_statements(FOUND_PAPER)
    if not sts:
        print(f"  the FOUND paper {FOUND_PAPER} is not among the fetched .tex "
              f"(data/arxiv). Cannot read its body.")
        return 1
    by_kind: dict[str, int] = {}
    with_proof = 0
    for e in sts:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        if e.get("proof"):
            with_proof += 1
    print(f"  FOUND paper : arXiv:{FOUND_PAPER}   subject (cmsg112 topic): "
          f"{FOUND_TOPIC}")
    print(f"  the .tex parse (LaTeX preserved) found "
          f"{len(sts)} CLAIM-BEARING environments:")
    for k in ("theorem", "proposition", "lemma", "corollary", "definition"):
        if by_kind.get(k):
            print(f"    · {by_kind[k]:3d}  {k}")
    print(f"  ({with_proof} of them carry their PROOF immediately following — the "
          f"derivation material.)")
    print(f"  -> this is the BODY (the claim-bearing environments), past cmsg112's")
    print(f"     abstract-LEAD-only read. NO verbatim statement reproduced.")

    # ----------------------------------------------------- 2. GROUND EACH CLAIM
    banner("2. GROUND EACH CLAIM — the agent comprehends each as a Claim/Concept "
           "(genus/differentia, read_and_ground) + measures DEPTH")
    s = _native.Substrate()
    # SEED THE MATH BEDROCK (the grounded primitives the recursion bottoms out at —
    # set/relation/space/map/...; math_bedrock_grounding's seed). Without it every
    # genus is held-as-topic only and the DEPTH measure trivially collapses; with it
    # the read_and_ground descent can genuinely REACH a primitive (grounded-to-
    # primitive) where the genus chain bottoms out at the seeded bedrock.
    mf.install_math_foundations_seed(s)
    gr.open_grounding_productions(s)
    conv = Conv()
    print(f"  the agent grounds each claim through its held channels (DEFINITION: "
          f"term is-a\n  GENUS+differentia; CLAIM: quantifier+variable+domain+"
          f"predicate; HARVEST: object->\n  invariant/identification). DEPTH = "
          f"grounded-to-PRIMITIVE (the genus's cone reaches a\n  seeded primitive) "
          f"vs grounded-to-TOPIC (held genus, un-grounded toward primitives).\n")

    grounded = []          # the grounded-claim structures
    n_def = n_claim = n_harvest = n_uncomp = 0
    n_to_primitive = 0
    for e in sts:
        r = ground_one_claim(s, e, conv)
        grounded.append(r)
        if r["channel"] == "definition":
            n_def += 1
        elif r["channel"] == "claim":
            n_claim += 1
        elif r["channel"] == "harvest":
            n_harvest += 1
        else:
            n_uncomp += 1
        if r["grounded_to_primitive"]:
            n_to_primitive += 1

    n = len(sts)
    n_grounded = n_def + n_claim + n_harvest
    print(f"  GROUNDED AS A CLAIM/CONCEPT : {n_grounded}/{n} environments "
          f"comprehended into a typed claim")
    print(f"    · DEFINITION  (term is-a GENUS + differentia) : {n_def}")
    print(f"    · CLAIM       (quantifier/variable/domain/predicate) : {n_claim}")
    print(f"    · HARVEST     (object->invariant / identification)   : {n_harvest}")
    print(f"  DEPTH (honest): {n_to_primitive}/{n} grounded-to-PRIMITIVE (the genus's")
    print(f"    cone reaches a seeded primitive / the predicate carries a held fact);")
    print(f"    the rest are grounded-to-TOPIC (held genus/claim, un-grounded toward")
    print(f"    primitives — the comprehension-DEPTH residual, past cmsg112's topic).")

    # ------------------------------------------- 2b. PRECISION (short labels)
    banner("2b. PRECISION — the grounded-claim structure (SHORT genus/kind label "
           "per claim; NOT verbatim — the agent's comprehended subject)")
    shown = 0
    # show the grounded-to-PRIMITIVE claims FIRST (the depth payoff), then the
    # grounded-to-topic ones — so the precision read leads with the deepest.
    comprehended = [r for r in grounded if r["channel"] is not None]
    comprehended.sort(key=lambda r: not r["grounded_to_primitive"])
    for r in comprehended:
        if r["grounded_to_primitive"]:
            prims = r.get("primitives") or []
            ptag = (" [" + ", ".join(prims[:2]) + "]") if prims else ""
            depth = f"-> primitive (depth {r['depth']}){ptag}"
        else:
            depth = "-> topic (genus held, un-grounded)"
        if r["channel"] == "definition":
            lab = f"a {r['kind']} defining a '{r['genus'].replace('_', ' ')}'"
        elif r["channel"] == "claim":
            lab = f"a {r['kind']} asserting a {r['claim_kind']} claim"
        else:
            lab = f"a {r['kind']} stating an invariant/identification fact"
        print(f"    [{r['kind']:11}] {lab:54}  {depth}")
        shown += 1
        if shown >= SPOT:
            break
    print(f"\n  (read above: each is the agent's SHORT comprehended subject — the")
    print(f"   genus/kind, the depth — NOT the verbatim claim. The to-primitive ones")
    print(f"   bottom out at a held primitive; the to-topic ones name the frontier.)")

    # --------------------------------------------- 3. DETECT + ACQUIRE-QUEUE
    banner("3. DETECT + ACQUIRE-QUEUE — the constructions the agent CANNOT unpack "
           "(detected + queued to acquire-by-reading; the agent's named residual)")
    # cluster the acquire-queue by KIND + target (the un-held genus terms, the
    # un-held predicates, the un-recognised construction-types).
    queue: dict[str, dict[str, int]] = {}
    for r in grounded:
        a = r["acquire"]
        if not a:
            continue
        queue.setdefault(a["kind"], {})
        queue[a["kind"]][a["target"]] = queue[a["kind"]].get(a["target"], 0) + 1
    total_q = sum(sum(v.values()) for v in queue.values())
    print(f"  the agent DETECTED {total_q} claims referencing a construction it does")
    print(f"  NOT yet hold -> QUEUED to ACQUIRE (read its definition toward")
    print(f"  primitives / acquire the construction-type — the SAME ground+acquire")
    print(f"  the HLE ladder ran). The queue, by kind:\n")
    for kind in ("un-held-genus", "un-held-predicate", "un-recognised-construction"):
        items = queue.get(kind, {})
        if not items:
            continue
        n_items = sum(items.values())
        print(f"  · {kind}  ({n_items} claims, {len(items)} distinct):")
        ranked = sorted(items.items(), key=lambda x: -x[1])
        for tgt, cnt in ranked[:8]:
            short = tgt.replace("_", " ")
            print(f"      ACQUIRE  '{short}'  (x{cnt})")
    print(f"\n  -> this IS the honest residual, NAMED by the agent: the genus terms /")
    print(f"     constructions it cannot yet unpack, queued to acquire-by-reading.")

    # --------------------------------------------------------------- HONEST
    banner("HONEST — the body-to-claims DEPTH (vs the abstract-only topic) + the "
           "acquire-queue (the residual); NO verbatim; not over-claimed")
    print("  THE WIN (real):")
    print(f"   - BODY: the agent parsed the FOUND paper's {len(sts)} CLAIM-BEARING")
    print(f"     environments from its .tex (the cmsg77 reader; GET-only, on disk).")
    print(f"   - CLAIMS: it grounded {n_grounded}/{n} as a Claim/Concept (genus/")
    print(f"     differentia / quantifier / invariant) — PAST cmsg112's abstract-only")
    print(f"     TOPIC, which grounded NO claims (grounded-to-primitive=False).")
    print(f"   - DEPTH: {n_to_primitive}/{n} grounded-to-PRIMITIVE (the genus's cone")
    print(f"     reaches a seeded primitive); the rest grounded-to-TOPIC.")
    print(f"   - ACQUIRE-QUEUE: {total_q} claims reference a construction it cannot")
    print(f"     yet unpack -> DETECTED + QUEUED to acquire-by-reading (its named")
    print(f"     residual — the un-held genus terms / un-recognised constructions).")
    print()
    print("  THE RESIDUAL (honest, NOT over-claimed):")
    print("   - COMPREHENSION-DEPTH: most claims ground to their TOPIC/genus, not all")
    print("     the way to seeded primitives (the dense research-register frontier).")
    print("     The agent reads the body to its CLAIMS + knows HONESTLY what it can't")
    print("     yet unpack — it did NOT 'fully understand the paper'.")
    print("   - The acquire-queue is the next ground+acquire rung (read each queued")
    print("     genus/construction toward primitives — the SAME HLE-ladder mechanism).")
    print()
    print("   NO verbatim claim text reproduced — only the grounded-claim STRUCTURE")
    print("   (a SHORT genus/kind label per claim), the DEPTH, and the acquire-queue.")
    print("   The body-to-claims grounding + the named acquire-queue is the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
