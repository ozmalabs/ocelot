"""AR3 harness for `ANALOGICAL_THINKING_SHAPE_MATH_PREREG.md`.

Runs BOTH scorers against the SAME graph in one process, so nothing here is a
cross-engine or cross-checkout comparison:

  * BEFORE — a read-only Python mirror of `domains/analogical_thinking.py`
    @ `d239b7c`: unanchored `StringIndexOf(name + " " + definition, kw) >= 0`
    over the SAME held vocabulary nodes, and the flat per-order set overlap
    with no structural stage.
  * AFTER  — the live module.

Sections:
  A. curated cross-Mt bridge (the real `looos_claims` × `held_writing_primitives`
     bridge the tree's own reader script builds, verbatim from that script)
  B. exhaustive vocabulary sweep over every `Concept` in a full seed boot
  C. consumer check (`shape_hits`, `metashape_realisation_counts`)

Run:  PYTHONPATH=.:runners/dsl/python python3 scripts/analogical_shape_math_probe.py
"""
from __future__ import annotations

import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs                                   # noqa: E402
import domains.analogical_thinking as at                     # noqa: E402

SEP = "=" * 96


# ---------------------------------------------------------------------------
# BEFORE — read-only mirror of the scorer at d239b7c
# ---------------------------------------------------------------------------
def before_kw_term(text):
    V = lambda n: {"type": "Var", "name": n}
    L = lambda x: {"type": "Lit", "value": x}
    return {"type": "Exists",
            "source": {"type": "Attr", "node": V("v"), "key": "keywords"},
            "var_name": "kw",
            "predicate": {"type": "Gte",
                          "a": {"type": "StringIndexOf", "haystack": L(text), "needle": V("kw")},
                          "b": L(0)}}


def before_vocab_hits(sub, native, voc_type, text):
    hits = set()
    term = before_kw_term(text)
    for n in sub.nodes(voc_type):
        if native.evaluate(term, {"v": n}):
            nm = sub.node(n)["attrs"].get("name")
            if nm:
                hits.add(nm)
    return hits


def before_reading(sub, native, c):
    a = sub.node(c)["attrs"]
    text = str(a.get("name", "")).lower() + " " + str(a.get("definition", "")).lower()
    roles = before_vocab_hits(sub, native, "FunctionalRole", text)
    prins = before_vocab_hits(sub, native, "ShapePrinciple", text)
    shapes = set()
    if prins:
        for sh in sub.nodes("MetaShape"):
            names = {sub.node(p)["attrs"].get("name")
                     for p in sub.neighbours(sh, "has_principle")}
            if prins & names:
                shapes.add(sub.node(sh)["attrs"].get("name"))
    return roles, prins, shapes


def before_compute(sub, native, sc, tc, order_n, smt, tmt):
    sa, ta = sub.node(sc)["attrs"], sub.node(tc)["attrs"]
    sn, tn = str(sa.get("name", "")).lower(), str(ta.get("name", "")).lower()
    if sn == tn:
        return None
    scat, tcat = str(sa.get("category", "")).lower(), str(ta.get("category", "")).lower()
    sdef, tdef = str(sa.get("definition", "")).lower(), str(ta.get("definition", "")).lower()
    per, why = {}, []
    ov = at._tokens(sn) & at._tokens(tn)
    if ov:
        per[0] = len(ov)
        why.append("shared name tokens: %s" % sorted(ov)[:3])
    if order_n >= 1:
        n1 = 0
        if scat and scat == tcat:
            n1 += 1
            why.append("shared category '%s'" % scat)
        common = at._tokens(sdef) & at._tokens(tdef)
        if len(common) >= 3:
            n1 += len(common)
            why.append("definition overlap (%d tokens)" % len(common))
        if n1:
            per[1] = n1
    sr, sp, sm = before_reading(sub, native, sc)
    tr, tp, tm = before_reading(sub, native, tc)
    if order_n >= 2 and (sr & tr):
        per[2] = len(sr & tr)
        why.append("shared functional role: %s" % ", ".join(sorted(sr & tr)))
    if order_n >= 3 and (sp & tp):
        per[3] = len(sp & tp)
        why.append("shared abstract principle: %s" % ", ".join(sorted(sp & tp)))
    if order_n >= 4 and (sm & tm):
        per[4] = len(sm & tm)
        why.append("shared meta-shape: %s" % ", ".join(sorted(sm & tm)))
    if not per:
        return None
    top = max(per)
    return {"source_concept": sn, "target_concept": tn, "source_mt": smt,
            "target_mt": tmt, "order_n": top, "feature_count": per[top],
            "features_total": sum(per.values()), "rationale": "; ".join(why)}


def before_find(sub, native, smt_name, tmt_names, order_n):
    def find_mt(nm):
        for m in sub.nodes("Microtheory"):
            if str(sub.node(m)["attrs"].get("name", "")) == nm:
                return m
        return None
    smt = find_mt(smt_name)
    out = []
    if smt is None:
        return out
    for tname in tmt_names:
        tmt = find_mt(tname)
        if tmt is None:
            continue
        for sc in sub.neighbours(smt, "has_concept"):
            for tc in sub.neighbours(tmt, "has_concept"):
                r = before_compute(sub, native, sc, tc, order_n, smt_name, tname)
                if r:
                    out.append(r)
    return out


# ---------------------------------------------------------------------------
# A. the curated bridge — VERBATIM from scripts/jabberwock_reads_looos.py
# ---------------------------------------------------------------------------
HELD = {
    "order_invariant_shape_distance":
        "SELECT the nearest exemplar; winner-take-all ARGMAX over an order-invariant set similarity; "
        "CHOOSE the closest; a competition that picks the best match.",
    "deformation_match":
        "TRANSFORM, warp, distort and MAP a candidate onto the mark; CONVERT one shape into another; "
        "the transform magnitude is the similarity. (agent's was a GLOBAL affine — UNDERPERFORMED.)",
    "nuisance_folding_invariance":
        "a PRIOR / EXPECTATION held before data; ANTICIPATE identity invariant to a nuisance; a "
        "FORWARD expectation / inductive bias that predicts away rotation and writer style.",
    "canonical_parse":
        "re-segment into stable PARTS at structural corners; a writer-invariant BOUNDARY and "
        "segmentation that ISOLATES parts regardless of how the character was drawn.",
    "nearest_neighbour_one_shot":
        "CLASSIFY a novel class from ONE example by SELECTING the nearest exemplar; winner-take-all "
        "ARGMAX; CHOOSE the closest; training-free, no pretraining.",
    "learned_nuisance_whitening":
        "LEARN / ADAPT / TRAIN the nuisance covariance from background data and UPDATE the metric; a "
        "learned prior. (on a holistic descriptor it did NOT help — an honest negative.)",
}

CLAIMS = {
    "innate_prior_modelling":
        "model human-INNATE PRIORS rather than learning them from data; a white-box EXPECTATION held "
        "before any example is seen.",
    "distortion_at_first_sight":
        "learn appearance similarity by mimicking how humans DISTORT an object at first sight; the "
        "distortion magnitude between two marks IS the similarity; a warp / MAP between shapes.",
    "nearest_neighbour_classifier":
        "NEAREST-NEIGHBOUR classification on that similarity space; SELECT the closest exemplar; a "
        "winner-take-all competition; no pretraining.",
    "tiny_data_regime":
        "human-level accuracy from 1-10 examples with NO pretraining; beats neural nets and classical "
        "ML in the tiny-data regime.",
    "white_box_model":
        "a WHITE-BOX model whose every step is inspectable, in place of an opaque learned embedding.",
}


def build_bridge(s):
    def mt_with(name, concepts, category):
        m = s.add_node("Microtheory", {"name": name})
        for cn, defn in concepts.items():
            c = s.add_node("Concept", {"name": cn, "definition": defn, "category": category})
            s.add_edge_unchecked(m, "has_concept", c)
        return m
    mt_with("looos_claims", CLAIMS, "paper_claim")
    mt_with("held_writing_primitives", HELD, "held_primitive")


def load_vocab(s):
    d = json.load(open(os.path.join(ROOT, "seeds", "shape_vocabulary.json")))
    local = {}
    for n in d["nodes"]:
        local[n["local_id"]] = s.add_node(n["type"], n["attrs"])
    for e in d["edges"]:
        s.add_edge_unchecked(local[e["src"]["local"]], e["type"], local[e["tgt"]["local"]])


def section_a():
    print(SEP)
    print("A. CURATED — the real looos_claims x held_writing_primitives bridge "
          "(concepts verbatim from scripts/jabberwock_reads_looos.py)")
    print(SEP)
    s = srs.Substrate()
    native = getattr(s, "_inner", s)
    load_vocab(s)
    build_bridge(s)
    at._CONCEPT_READING_CACHE.clear()
    at._VOCAB_KEYS_CACHE.clear()

    for n in (2, 3, 4):
        b = before_find(s, native, "looos_claims", ["held_writing_primitives"], n)
        a = at.find_analogies(s, "looos_claims", ["held_writing_primitives"], order_n=n)
        bk = {(r["source_concept"], r["target_concept"]): r for r in b}
        ak = {(r["source_concept"], r["target_concept"]): r for r in a}
        print("\n  order_n=%d :  BEFORE %d pairs   AFTER %d pairs   "
              "(withdrawn %d, new %d)" % (n, len(b), len(a),
                                          len(set(bk) - set(ak)), len(set(ak) - set(bk))))
        for k in sorted(set(bk) | set(ak)):
            rb, ra = bk.get(k), ak.get(k)
            ob = rb["order_n"] if rb else None
            oa = ra["order_n"] if ra else None
            flag = "  " if ob == oa else ("WITHDRAWN" if ra is None else "DEMOTED" if (oa or -1) < (ob or -1) else "CHANGED")
            print("    %-9s %-34s -> %-34s  order %s -> %s  corr=%s" %
                  (flag, k[0][:34], k[1][:34], ob, oa,
                   ra.get("corroboration") if ra else "-"))
        # the io case, explicitly
        for k, rb in sorted(bk.items()):
            if "input_output" in rb["rationale"] and k not in ak:
                print("      ^ the `io` case: BEFORE rationale = %r" % rb["rationale"][:110])
                break

    print("\n  RANKED TOP-5 at order_n=4 (BEFORE vs AFTER, each by its own key):")
    b = sorted(before_find(s, native, "looos_claims", ["held_writing_primitives"], 4),
               key=lambda r: (-r["order_n"], -r["feature_count"], -r["features_total"]))
    a = sorted(at.find_analogies(s, "looos_claims", ["held_writing_primitives"], order_n=4),
               key=at.RANK_KEY)
    for i in range(5):
        lb = "%s -> %s (n=%d)" % (b[i]["source_concept"][:26], b[i]["target_concept"][:26],
                                  b[i]["order_n"]) if i < len(b) else "-"
        la = "%s -> %s (n=%d,c=%d)" % (a[i]["source_concept"][:26], a[i]["target_concept"][:26],
                                       a[i]["order_n"], a[i].get("corroboration", 0)) if i < len(a) else "-"
        print("    %d. %-46s | %s" % (i + 1, lb, la))


# ---------------------------------------------------------------------------
# B. exhaustive sweep over a full seed boot
# ---------------------------------------------------------------------------
def section_b():
    print("\n" + SEP)
    print("B. EXHAUSTIVE — every Concept in a full load_all_seeds boot, every "
          "vocabulary entry")
    print(SEP)
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    wa = WorldAdapter()
    load_all_seeds(wa)
    s = wa.s
    native = getattr(s, "_inner", s)
    at._CONCEPT_READING_CACHE.clear()
    at._VOCAB_KEYS_CACHE.clear()

    concepts = list(s.nodes("Concept"))
    tot_b = tot_a = 0
    lost = collections.Counter()
    gained = collections.Counter()
    n_changed = 0
    for c in concepts:
        rb = before_reading(s, native, c)
        reading = at._concept_reading(s, c)
        ra = (set(reading["role"]), set(reading["principle"]), set(reading["shape"]))
        for i, axis in enumerate(("role", "principle", "shape")):
            tot_b += len(rb[i])
            tot_a += len(ra[i])
            for x in rb[i] - ra[i]:
                lost[(axis, x)] += 1
            for x in ra[i] - rb[i]:
                gained[(axis, x)] += 1
        if rb != ra:
            n_changed += 1
    print("  Concepts: %d" % len(concepts))
    print("  vocabulary readings  BEFORE %d   AFTER %d   (withdrawn %d = %.1f%%, added %d)"
          % (tot_b, tot_a, tot_b - tot_a + sum(gained.values()),
             100.0 * (tot_b - tot_a + sum(gained.values())) / max(tot_b, 1),
             sum(gained.values())))
    print("  concepts whose reading changed at all: %d (%.1f%%)"
          % (n_changed, 100.0 * n_changed / max(len(concepts), 1)))
    print("  top WITHDRAWN readings:")
    for k, v in lost.most_common(10):
        print("    %-11s %-30s %6d" % (k[0], k[1], v))
    if gained:
        print("  ADDED readings (should be empty — anchoring can only remove):")
        for k, v in gained.most_common(10):
            print("    %-11s %-30s %6d" % (k[0], k[1], v))
    else:
        print("  ADDED readings: NONE — the change is strictly a withdrawal.")

    # the biggest real bridge available: two large sibling microtheories
    sizes = []
    for m in s.nodes("Microtheory"):
        n = len(list(s.neighbours(m, "has_concept")))
        if n:
            sizes.append((n, str(s.node(m)["attrs"].get("name") or "")))
    sizes.sort(reverse=True)
    print("\n  largest concept-bearing microtheories: %s" % sizes[:4])
    if len(sizes) >= 2:
        src, tgt = sizes[0][1], sizes[1][1]
        for n in (2, 4):
            b = before_find(s, native, src, [tgt], n)
            a = at.find_analogies(s, src, [tgt], order_n=n)
            bk = {(r["source_concept"], r["target_concept"]): r for r in b}
            ak = {(r["source_concept"], r["target_concept"]): r for r in a}
            corr = sum(1 for r in a if r.get("corroboration", 0) > 0)
            demoted = sum(1 for k in set(bk) & set(ak) if ak[k]["order_n"] < bk[k]["order_n"])
            print("  bridge %s x %s @ n=%d: BEFORE %d  AFTER %d  withdrawn %d  "
                  "demoted %d  corroborated %d"
                  % (src[:26], tgt[:26], n, len(b), len(a),
                     len(set(bk) - set(ak)), demoted, corr))


# ---------------------------------------------------------------------------
# C. consumers
# ---------------------------------------------------------------------------
def section_c():
    print("\n" + SEP)
    print("C. CONSUMERS")
    print(SEP)
    s = srs.Substrate()
    load_vocab(s)
    at._CONCEPT_READING_CACHE.clear()
    at._VOCAB_KEYS_CACHE.clear()
    for text in ("gate the layer by policy",
                 "you should predict things and observe them",
                 "an operation on a satisfaction fold",
                 "aggregates of skandhas"):
        print("  shape_hits(%r) = %s" % (text[:44], sorted(at.shape_hits(s, text))))


if __name__ == "__main__":
    section_a()
    section_c()
    section_b()
