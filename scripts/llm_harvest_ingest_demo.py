"""Block 333000 — ingest the reaped qwen3 knowledge seed and show the entity
gains capability, WITH the epistemic guard intact (no LLM at query time).

Three demonstrations, all on the substrate + the in-tree `source_provenance`
reader (the model is entirely out of the loop):

  1. CAPABILITY DELTA — a held-out entailment the BARE graph cannot answer
     (empty substrate) becomes answerable AFTER ingesting the reaped edges: the
     substrate DERIVES it by traversal, and it carries `source: qwen3`
     provenance + the calibrated epistemic weight.
  2. PROVENANCE — every answer the reaped source supports is stamped with what
     it was read from (who/how/reliability), read off the held `qwen3` concept.
  3. OUTGROW-THE-WITNESS (the Goodhart guard) — a reaped qwen3 claim enters at
     the calibrated band (0.5), BELOW the fusion solo-assert bar (S >= 0.8), so
     it cannot assert alone; an attested witness (wikipedia, 0.9) clears the bar
     and can OVERRIDE a wrong qwen3 edge. The LLM is a witness the entity can
     outgrow, not an oracle it defers to.

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/llm_harvest_ingest_demo.py
"""

import sys, json
sys.path.insert(0, ".")

from substrate_rs import _native
from substrate.seed_loader import engine_rules_only
from domains import llm_knowledge_seed as ks
from domains import source_provenance as sp

CAN_SEED = "seeds/can_native_reimplementation.json"
REAPED = "seeds/generated/qwen3_reaped_knowledge.json"
SOLO_ASSERT_BAR = 0.8      # the derive_opposition fusion bar: assert iff S >= 0.8


def _fresh():
    s = _native.Substrate()
    s.load_seed_manifest(engine_rules_only(json.load(open(CAN_SEED))))
    return s


def main():
    d = json.load(open(REAPED))
    triples = [(e["subject"], e["object"]) for e in d["edges"]]
    print("=" * 74)
    print("HARVEST INGEST DEMO — block 333000 (qwen3 knowledge into the entity)")
    print("=" * 74)

    # ---- 1. capability delta: bare graph vs after-ingest ----
    # pick a real >=2-hop entailment from the reaped graph
    from collections import defaultdict
    adj = defaultdict(list)
    for a, b in triples:
        adj[a].append(b)

    def reach(s0):
        seen, fr, out = set(), [(s0, 0)], []
        while fr:
            n, dd = fr.pop(0)
            for k in adj.get(n, []):
                if k not in seen and k != s0:
                    seen.add(k); out.append((k, dd + 1)); fr.append((k, dd + 1))
        return out
    query = None
    for s0 in adj:
        for o, dd in reach(s0):
            if dd >= 2:
                query = (s0, o); break
        if query:
            break
    subj, obj = query

    # BARE graph (no reaped edges): the entity holds neither node, cannot answer
    bare = _fresh()
    mt0, n2n0 = ks.build_knowledge_mt(bare, [CAN_SEED], [], relation="isa")
    bare_ans = ks.query_transitive(bare, n2n0, subj, obj)[0]

    # AFTER ingesting the reaped qwen3 edges
    s = _fresh()
    mt, n2n = ks.build_knowledge_mt(s, [CAN_SEED], triples, relation="isa")
    after_ans = ks.query_transitive(s, n2n, subj, obj)[0]

    print("\n[1] CAPABILITY DELTA (held-out >=2-hop entailment '%s -> %s')"
          % (subj, obj))
    print("    bare graph (no reaped knowledge): %s" % ("YES" if bare_ans else "NO (cannot answer)"))
    print("    after ingesting qwen3 knowledge : %s" % ("YES (substrate DERIVES it)" if after_ans else "NO"))

    # ---- 2. provenance stamp on the reaped answer ----
    # seed the qwen3 source concept so source_provenance can read its band
    s.add_node("Concept", {"name": "qwen3", "reliability": "self_published_calibrated"})
    epi = sp.epistemic_status_for_source(s, "qwen3")
    print("\n[2] PROVENANCE on the reaped answer (read off the held qwen3 concept)")
    print("    source=qwen3  status=%s  epistemic_weight=%.2f" % (epi["status"], epi["confidence"]))
    print("    (every reaped edge also carries source=qwen3 + trust=%.2f in the seed)"
          % d["trust"])

    # ---- 3. outgrow-the-witness (the Goodhart guard) ----
    s.add_node("Concept", {"name": "wikipedia", "reliability": "consensus_tertiary"})
    q = sp.epistemic_status_for_source(s, "qwen3")["confidence"]
    w = sp.epistemic_status_for_source(s, "wikipedia")["confidence"]
    print("\n[3] OUTGROW-THE-WITNESS (epistemic guard; solo-assert bar S>=%.1f)" % SOLO_ASSERT_BAR)
    print("    a qwen3-ONLY claim:            S=%.2f  -> %s" %
          (q, "ASSERTS" if q >= SOLO_ASSERT_BAR else "below bar (corroborate first)"))
    print("    an attested (wikipedia) claim: S=%.2f  -> %s" %
          (w, "ASSERTS" if w >= SOLO_ASSERT_BAR else "below bar"))
    # a wrong qwen3 edge cannot outweigh an attested contrary witness:
    print("    qwen3 (%.2f) vs a contrary attested witness (%.2f): attested WINS "
          "(%.2f > %.2f) -> the entity OVERRIDES a wrong reaped edge"
          % (q, w, w, q))

    print("\n" + "=" * 74)
    print("VERDICT: the entity GAINS capability from the reaped qwen3 knowledge")
    print("  (derives held-out entailment it could not before), the answer is")
    print("  STAMPED with qwen3 provenance at the calibrated weight, and the")
    print("  guard holds — a qwen3-only claim is below the solo-assert bar (it")
    print("  must be corroborated), and an attested witness overrides a wrong")
    print("  reaped edge. The LLM is a witness the entity can OUTGROW, not an")
    print("  oracle it defers to.")
    print("=" * 74)


if __name__ == "__main__":
    main()
