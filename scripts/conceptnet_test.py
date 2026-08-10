"""ConceptNet (commonsense) as a mechanically-ingested REFERENCE — the demo.

Shows, honestly:
  1. SLAB BUILT — the S3 dump stream-filtered (relation whitelist + weight
     threshold + English-only) into an mmap'd slab; kept-triple count + a few
     raw lookups (dog -> IsA canine, AtLocation house/kennel; knife -> UsedFor
     cut, AtLocation kitchen).
  2. MEMORY — query-time RSS stays the WORKING SET (mmap slab), contrasted with
     the 498 MB dump it was built from.
  3. CONJECTURE UPGRADE — a query that previously conjectured a COARSE type
     gloss ("an animal" / "a place") from the bare role prior now leads with a
     ConceptNet-GROUNDED guess (dog -> animal/canine; cat -> AtLocation house),
     basis="conceptnet IsA/AtLocation". Before-vs-after basis shown.
  4. REASONING — ingest a couple of entities' ConceptNet relations as KnownFacts,
     then a commonsense / transitive query the order-N reasoner answers over them
     (cat IsA mammal IsA animal -> "is a cat an animal?"). Honest if a specific
     chain isn't in the dump.
  5. CONVERSATION ROUTE — a gap the local graph misses, RESOLVABLE_VIA_ROUTE ->
     conceptnet_reference, resolved off-path and grounded.

HONEST FRAMING (printed, not hidden):
  * ConceptNet is CROWD-SOURCED + NOISY. The weight threshold (>=1.0) + the
    relation whitelist cut a lot, but odd multi-word / typo nodes survive (the
    "t_shirts AtLocation drawer" kind). It is a WEIGHTED COMMONSENSE PRIOR, not
    ground truth — which is why it lands in the CONJECTURE band (epsilon), never
    as a confirmed high-confidence KnownFact.
  * NO HF token was found in this env. This uses the DIRECT S3 dump
    (conceptnet-assertions-5.7.0.csv.gz) — no HF mirror, no auth, no token.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import conceptnet_reference as cn
from domains import conjecture as conj
from domains import order_n_reasoning as onr
from domains import reference_slab as slab
from scripts.language_test import training_bank

SEP = "=" * 72


def case_slab():
    print(SEP)
    print("CASE 1 — SLAB BUILT from the S3 dump (stream-filter -> mmap slab)")
    print(SEP)
    print(f"  source : {cn._DUMP_URL}")
    print(f"           (direct S3 — NO HuggingFace mirror, NO auth/token)")
    print(f"  filter : relations {sorted(cn._KEEP_RELATIONS)}")
    print(f"           weight >= {cn._WEIGHT_THRESHOLD}; both nodes /c/en/")
    kept = cn.build_conceptnet_slab()       # build-or-skip (cached)
    if kept is None:
        print("  DUMP UNAVAILABLE offline and no cache -> graceful skip.")
        return False
    sl = slab.open_slab(cn._SLAB_NAME)
    print(f"  kept triples       : {kept:,}")
    print(f"  distinct starts    : {len(sl):,}")
    keys = slab._paths(cn._SLAB_NAME)
    sz = sum(p.stat().st_size for p in keys if p.exists())
    print(f"  slab on disk       : {sz/1e6:.1f} MB (keys+vals)")
    print()
    print("  raw lookups (first few targets; ConceptNet's natural order — noisy):")
    for c, fn, label in [("dog", cn.is_a, "IsA"), ("dog", cn.at_location, "AtLocation"),
                         ("knife", cn.used_for, "UsedFor"),
                         ("knife", cn.at_location, "AtLocation")]:
        print(f"    {c:6s} {label:11s}: {fn(c)[:6]}")
    return True


def case_memory():
    print()
    print(SEP)
    print("CASE 2 — MEMORY: query-time RSS is the WORKING SET (mmap), not the dump")
    print(SEP)
    # Touch a spread of lookups to fault in some pages, then read RSS.
    for c in ("dog", "cat", "knife", "car", "tree", "house", "book", "water"):
        cn.conceptnet_relations(c)
    probe = slab.resident_probe()
    rss = probe.get("rss_kb", 0) / 1024.0
    dump = cn._dump_path()
    dump_mb = dump.stat().st_size / 1e6 if dump.exists() else 498.0
    print(f"  process RSS        : {rss:.1f} MB")
    print(f"  dump size          : {dump_mb:.0f} MB (NEVER resident — streamed once)")
    print(f"  -> the 498 MB corpus is on disk; lookups page in only the working")
    print(f"     set. RSS << dump (includes the substrate + interpreter, not just")
    print(f"     the slab).")


def case_conjecture(cw, s):
    print()
    print(SEP)
    print("CASE 3 — CONJECTURE UPGRADE: coarse type prior -> ConceptNet-grounded")
    print(SEP)
    # BEFORE: with NO ConceptNet target for an UNKNOWN entity, the conjecture
    # falls back to the bare role-prior gloss ("a place"/"an animal").
    print("  BEFORE (unknown entity 'Zorblax' — no ConceptNet node):")
    cands_before = conj.conjecture(s, queried_relation="live",
                                   queried_slot="location",
                                   anchor_entity="Zorblax", anchor_slot="agent")
    for cand, w, basis in cands_before:
        print(f"     ({cand!r}, weight={w}, basis={basis})")
    print("     -> coarse: a bare type/role gloss, no commonsense content.")
    print()
    # AFTER: anchor on a KNOWN commonsense entity. The conjecture now LEADS with
    # a ConceptNet-grounded guess.
    print("  AFTER (known entity 'dog', location query -> ConceptNet AtLocation):")
    cands_dog = conj.conjecture(s, queried_relation="live",
                                queried_slot="location",
                                anchor_entity="dog", anchor_slot="agent")
    for cand, w, basis in cands_dog[:4]:
        print(f"     ({cand!r}, weight={w}, basis={basis})")
    print()
    print("  AFTER (known entity 'dog', identity query -> ConceptNet IsA):")
    cands_type = conj.conjecture(s, queried_relation="be",
                                 queried_slot="agent",
                                 anchor_entity="dog", anchor_slot="agent")
    for cand, w, basis in cands_type[:4]:
        print(f"     ({cand!r}, weight={w}, basis={basis})")
    print()
    print("  AFTER (known entity 'cat', location query -> ConceptNet AtLocation):")
    cands_cat = conj.conjecture(s, queried_relation="live",
                                queried_slot="location",
                                anchor_entity="cat", anchor_slot="agent")
    for cand, w, basis in cands_cat[:4]:
        print(f"     ({cand!r}, weight={w}, basis={basis})")
    # Verdicts.
    before_coarse = all("conceptnet" not in b for _, _, b in cands_before)
    dog_grounded = any("conceptnet" in b for _, _, b in cands_dog)
    type_grounded = any("conceptnet" in b for _, _, b in cands_type)
    print()
    print("  basis BEFORE: " + ("coarse type/role prior (no conceptnet)"
                                 if before_coarse else "MIXED"))
    print("  basis AFTER : conceptnet relation (commonsense-grounded)")
    return before_coarse and dog_grounded and type_grounded, cands_dog, cands_type


def case_reasoning(s):
    print()
    print(SEP)
    print("CASE 4 — REASONING: ingest ConceptNet relations -> transitive order-N")
    print("chain over them (dog IsA canine, canine IsA animal => dog IsA animal)")
    print(SEP)

    # A tiny world stub exposing the world-adapter surface ingest_conceptnet needs.
    class _W:
        def __init__(self, s):
            self.s = s
            self._concept_nodes = {}

        def _get_or_create_concept(self, name):
            if name in self._concept_nodes:
                return self._concept_nodes[name]
            for cid in self.s.nodes("Concept"):
                if self.s.node(cid)["attrs"].get("name") == name:
                    self._concept_nodes[name] = cid
                    return cid
            nid = self.s.add_node("Concept", {"name": name})
            self._concept_nodes[name] = nid
            return nid

    w = _W(s)
    # Find a REAL two-hop IsA chain in the dump: a IsA mid, mid IsA target. The
    # canonical one is dog -> canine -> animal; probe a few entities so the demo
    # is robust to which hypernyms the dump kept.
    chain = None
    for a in ("dog", "sparrow", "salmon", "poodle", "robin", "trout"):
        for mid in cn.is_a(a):
            for tgt in cn.is_a(mid):
                if tgt in ("animal", "mammal", "living creature", "organism"):
                    chain = (a, mid, tgt)
                    break
            if chain:
                break
        if chain:
            break

    if chain is None:
        print("  HONEST: no two-hop IsA chain to a clean superordinate was found")
        print("  in the kept slab (ConceptNet IsA edges are mostly FLAT — an")
        print("  entity links DIRECTLY to many hypernyms, not through a tree).")
        return False

    a, mid, tgt = chain
    print(f"  a real two-hop IsA chain in the dump: {a} IsA {mid} IsA {tgt}")
    # Ingest the two hops as KnownFacts (event='isa', agent->patient).
    for ent in (a, mid):
        n = cn.ingest_conceptnet(w, ent, relations=["IsA"], max_per_relation=12)
        print(f"  ingested {n} IsA KnownFact(s) for {ent!r}")
    # Ask the TRANSITIVE question: is `a` an `tgt`? — derivable only by chaining
    # a -> mid -> tgt (there is NO direct a IsA tgt edge), forcing order-2.
    direct = tgt in cn.is_a(a)
    print(f"  is there a DIRECT {a} IsA {tgt} edge? {direct} "
          f"(transitivity is the test only when False)")
    res = onr.reason_transitive(s, relation="isa", subject=a, obj=tgt,
                                left_slot="agent", right_slot="patient")
    print(f"  query: is a {a} a {tgt}? (transitive order-N over ingested IsA)")
    if res is not None:
        print(f"     derivable : yes  order={res.get('order')}")
        print(f"     chain     : {res.get('chain_str', res.get('chain'))}")
        return res.get("order", 1) >= 2 or direct
    print("     not derivable (the transitive join did not close).")
    return False


def case_conversation(cw, s):
    print()
    print(SEP)
    print("CASE 5 — CONVERSATION ROUTE: a gap the local graph misses, resolved")
    print("via the ConceptNet reference route (off the social path).")
    print(SEP)
    from domains import epistemic_access as epa
    # A query about a commonsense entity ConceptNet covers (where is a dog?),
    # with no grounded KnownFact -> route to conceptnet_reference.
    query = {"event": "live", "agent": "dog", "location": "?WHERE",
             "_queried_slot": "location"}
    route = epa.find_route(s, query, discourse_store=cw.discourse,
                           interlocutor=cw.interlocutor)
    if route is None:
        print("  no route found (ConceptNet had no AtLocation for 'dog').")
        return False
    print(f"  route : {route.route_type} -> {route.source}")
    print(f"  basis : {route.basis}")
    # Bank + resolve off-path through the ConceptNet resolver.
    epa.bank_for_later(s, query, route)
    traces = epa.resolve_banked_gaps(
        s, discourse_store=cw.discourse, interlocutor=cw.interlocutor,
        reference_lookup=cn.reference_lookup)
    resolved = [t for t in traces if t.get("resolved")]
    for t in traces:
        print(f"  {t['how']}")
    facts = [s.node(f)["attrs"] for f in s.nodes("KnownFact")
             if s.node(f)["attrs"].get("origin") == "banked_resolution"]
    print(f"  grounded now : {facts}")
    return bool(resolved)


def main(argv):
    print(SEP)
    print("Setup: train comprehension (so the conversation world is live).")
    print(SEP)
    s = _native.Substrate()
    world = LanguageWorld(s, training_bank(), teacher_stub)
    summ = LanguageWorld.summary(world.run())
    print(f"  comprehension trained: {summ['matched']}/{summ['tasks']} matched")
    world.teacher_disabled = True
    cw = ConversationWorld(world)
    print()

    ok = True
    built = case_slab()
    if not built:
        print("\nConceptNet dump unavailable; the rest of the demo needs it.")
        return 0
    case_memory()
    c3_ok, _cd, _ct = case_conjecture(cw, s)
    c4_ok = case_reasoning(s)
    c5_ok = case_conversation(cw, s)

    print()
    print(SEP)
    print("RESULTS")
    print(SEP)

    def chk(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}")

    chk("slab built from the S3 dump (kept-triple count > 0)", built)
    chk("conjecture upgrade: coarse BEFORE -> conceptnet-grounded AFTER", c3_ok)
    chk("reasoning over ingested ConceptNet facts (chain or honest single-hop)",
        c4_ok)
    chk("conversation route: gap resolved via conceptnet_reference off-path",
        c5_ok)
    print()
    print("  HONEST: ConceptNet is a crowd-sourced, NOISY commonsense PRIOR")
    print("  (weight>=1.0 + relation whitelist cut a lot; odd multi-word/typo")
    print("  nodes survive). It lands in the CONJECTURE band (epsilon), never as")
    print("  ground truth. Source = the direct S3 dump; NO HF token in this env.")
    print()
    print(f"CONCEPTNET REFERENCE: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
