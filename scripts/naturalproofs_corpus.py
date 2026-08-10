"""PROVE the NaturalProofs corpus is CONNECTED into the agent's reference reader,
and the agent ACQUIRES a lower-tower operation FROM it — with the HONEST combined
coverage map across the reading STACK (Wikipedia + OEIS + NaturalProofs).

NaturalProofs (ProofWiki + Stacks + textbooks, 14,698 entries) adds two things
the agent needs to keep climbing:
  · the LOWER-TOWER OPERATIONS *with proofs* — kernel / image / quotient / rank /
    boundary (operations the agent HAS), now sourced WITH the derivation.
  · the genuinely-new PROOFS (the `target` field — the derivation material).

HONEST (the named gap): NaturalProofs is ProofWiki-heavy and does NOT cover the
research-topology tier (homology / cohomology / spectral sequence / classifying
space / cobordism / spin = ~0 entries). Those DEFINITIONS are in Wikipedia; the
research-tier PROOFS are the residual -> nLab / Stacks / arXiv, NOT connected.

No LLM. naturalproofs_local is a WORLD ADAPTER (mirrors oeis_local / wiki_local);
the reference reader (read_and_ground) now sources the STACK; the comprehension +
grounding are the agent's OWN machinery.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains import naturalproofs_local as npl
from domains import read_and_ground as rag
from domains import grounded_representation as gr

SEP = "=" * 74


def _seed_primitive(s, name: str) -> None:
    for c in s.nodes("Concept"):
        if s.node(c)["attrs"].get("name") == name:
            return
    s.add_node("Concept", {"name": name, "origin": "seed_primitive"})


class _Conv:
    """A bare conversation host — NO fed definition feed (the agent must SOURCE
    the definition from the corpus, not a handed string)."""
    _definition_feed = None
    _constructions = None


def main() -> int:
    print(SEP)
    print("THE READING STACK — Wikipedia (broad) + OEIS (sequences) +")
    print("                    NaturalProofs (foundational defs + PROOFS)")
    print(SEP)

    # ---------------------------------------------------------- 0. CONNECTED
    print()
    print("0. THE CORPUS IS CONNECTED")
    print(f"   naturalproofs_local.present() = {npl.present()}  (must be True)")
    if not npl.present():
        print("   corpus not on disk — abort"); return 1

    # a DEFINITION read from the corpus (a lower-tower operation it HAS).
    kdef = npl.definition("kernel")
    print()
    print("   --- a DEFINITION read from NaturalProofs (the operation 'kernel') ---")
    print(f"   title: {kdef['title']}")
    print(f"   text : {kdef['text'][:200].replace(chr(10),' ')} ...")
    print(f"   refs : {kdef['refs'][:4]}")

    # a PROOF read from the corpus (the derivation material — the `target`).
    kproof = npl.proof_for("Kernel of Group Homomorphism")
    print()
    print("   --- a PROOF read from NaturalProofs (the derivation material) ---")
    print(f"   theorem: {kproof['title']}")
    print(f"   states : {kproof['text'][:140].replace(chr(10),' ')} ...")
    print(f"   PROOF  : {kproof['proof'][:240].replace(chr(10),' ')} ...")

    # ------------------------------------------------ 1. THE READER SOURCES IT
    print()
    print(SEP)
    print("1. THE REFERENCE READER SOURCES NaturalProofs (the stack, most-specific")
    print("   first): a concept name -> its NaturalProofs definition lead")
    print(SEP)
    for op in ("kernel", "quotient", "rank"):
        lead = rag._read_naturalproofs_definition(op)
        print(f"   read({op!r}) -> {lead!r}")

    # ------------------------------------------- 2. THE AGENT ACQUIRES FROM IT
    print()
    print(SEP)
    print("2. THE AGENT ACQUIRES A LOWER-TOWER OPERATION FROM NaturalProofs")
    print("   before(not held) -> read-FROM-NaturalProofs -> grounded")
    print(SEP)
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    # seed the genus PRIMITIVES the corpus's definitions bottom out at (held basis
    # concepts the agent already has — set / subset / ordinal are foundational).
    for prim in ("set", "subset", "ordinal", "object"):
        _seed_primitive(s, prim)
    cw = _Conv()

    acquired_ok = True
    for op, genus in (("quotient", "set"), ("kernel", "subset"),
                      ("rank", "ordinal")):
        held_before = rag._is_held(s, op)
        print()
        print(f"   '{op}': held BEFORE? {held_before}  (must be False)")
        # NO fed feed -> the SOURCE is the corpus (read_and_ground -> the reader ->
        # naturalproofs_local). The agent reads the real corpus definition.
        res = rag.read_and_ground(s, op, cw)
        tr = res["trace"]
        print(f"     READ (from corpus): {str(tr.get('read'))[:90]!r}")
        comp = tr.get("comprehend") or {}
        print(f"     COMPREHEND        : term={comp.get('term')!r} "
              f"genus={comp.get('genus')!r}")
        st = res.get("structure") or {}
        print(f"     GROUNDED          : {res['grounded']}  "
              f"cone={st.get('cone_size')} primitives={st.get('primitives')}")
        print(f"     reason            : {res['reason'][:90]}")
        held_after = rag._is_held(s, res.get("structure", {}).get(
            "grounded_name") or op)
        print(f"   '{op}': held AFTER?  {held_after}")
        acquired_ok = acquired_ok and res["grounded"]

    # --------------------------------------- 3. THE COMBINED COVERAGE MAP
    print()
    print(SEP)
    print("3. THE COMBINED COVERAGE MAP (honest, MEASURED) — which corpus has each")
    print(SEP)
    try:
        from domains import wiki_local as wl
        wiki_present = wl.present()
    except Exception:
        wiki_present = False
    try:
        from domains import oeis_local as oel
        oeis_present = oel.present()
    except Exception:
        oeis_present = False

    # the lower-tower operations: NaturalProofs (with proofs!).
    print()
    print("   LOWER-TOWER OPERATIONS  ->  NaturalProofs (definition + PROOF):")
    print(f"   {'operation':<12}{'def?':<6}{'proof?':<8}{'top-level titles':<18}")
    for op in ("kernel", "image", "quotient", "rank", "boundary"):
        has_def = npl.definition(op) is not None
        hits = npl.search(op, limit=400)
        n_proof = sum(1 for (_t, hp) in hits if hp)
        # count top-level theorem titles (a coarse 'how many entries' proxy).
        n_top = len(hits)
        print(f"   {op:<12}{('Y' if has_def else 'N'):<6}"
              f"{('Y x'+str(n_proof)):<8}{n_top:<18}")

    # the research-topology tier: NOT in NaturalProofs -> Wikipedia (def only).
    print()
    print("   RESEARCH-TOPOLOGY TIER  ->  Wikipedia (definition/prose) / NOT in NP:")
    print(f"   {'concept':<20}{'in NaturalProofs?':<20}{'in Wikipedia?':<14}")
    for c in ("homology", "cohomology", "classifying space", "cobordism",
              "spin"):
        n_hits = len(npl.search(c, limit=400))
        has_real_def = npl.definition(c) is not None
        # HONEST: a bare substring hit (cohomology stub matched by 'homology') is
        # NOT coverage — only a resolvable DEFINITION counts. The research tier has
        # ~0 real definitions here; report the count, not a bare Y.
        if has_real_def:
            np_cell = f"~def-only ({n_hits} hit)"
        elif n_hits:
            np_cell = f"N (incidental x{n_hits})"
        else:
            np_cell = "N (0 entries)"
        in_wiki = "Y" if (wiki_present and _wiki_has(c)) else \
            ("?" if not wiki_present else "N")
        print(f"   {c:<20}{np_cell:<20}{in_wiki:<14}")

    print()
    print("   NUMBER-THEORY SEQUENCES ->  OEIS (prose + ground-truth values):")
    print(f"   oeis_local present? {oeis_present}  "
          f"(e.g. A000005 divisor count -> values to verify against)")

    # --------------------------------------- 4. THE NAMED GAP
    print()
    print(SEP)
    print("4. THE NAMED GAP (honest, not over-claimed)")
    print(SEP)
    print("""   COVERED (connected, read + acquired from):
     · foundational + intermediate DEFINITIONS, WITH PROOFS  -> NaturalProofs
     · broad + research-tier DEFINITIONS (prose)             -> Wikipedia
     · number-theory sequences + ground-truth VALUES         -> OEIS

   THE RESIDUAL (the named gap — NOT connected, do NOT over-claim):
     · the research-tier PROOFS / DERIVATIONS — the spectral sequence AS A
       PROCEDURE, the bordism computation, the classifying-space construction —
       are sparse-to-absent in ALL three connected corpora.
     -> nLab / Stacks (the deeper proof source) / arXiv — the deeper residual,
        NOT connected. The win is the connected stack + the honest map, NOT
        solved research math.""")

    print()
    print(SEP)
    ok = acquired_ok
    print(f"RESULT: corpus connected + agent acquired lower-tower ops = "
          f"{'ALL OK' if ok else 'INCOMPLETE'}")
    print(SEP)
    return 0 if ok else 1


def _wiki_has(title: str) -> bool:
    try:
        from domains import wiki_local as wl
        return wl.summary(title) is not None
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
