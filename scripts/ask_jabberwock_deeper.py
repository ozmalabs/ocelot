"""Deeper jabberwock survey — find structural issues the surface survey misses.

The existing surface survey (ask_jabberwock_what_seeds_need.py) prints the
same A-D recommendations regardless of state — it can't see its own progress.
This script asks the substrate harder questions whose answers DO move as the
corpus changes:

  1. Concept duplication across seeds
  2. Definition-pattern coverage gaps (walker blind spots)
  3. Internal Mt connectivity (intra-Mt Holds references)
  4. Genuinely-circular concept pairs
  5. Shape diversity by Mt (which Mts contribute >1 shape, which only 1)
  6. Definition-length distribution (stub vs over-long)
  7. Rule dormancy (rules whose if/then keywords don't name any Concept)
  8. Cortex score axes that don't move

Each section reports verbatim numbers + examples. At the end, the script
emits three concrete refactor proposals ordered by likely impact.
"""
from __future__ import annotations

import importlib
import inspect
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


# ---------------------------------------------------------------------------
# Substrate bring-up — same pattern as the surface survey.
# ---------------------------------------------------------------------------

def fresh_substrate():
    s = _native.Substrate()
    for t in ("Microtheory", "Concept", "Rule"):
        for u in ("Microtheory", "Concept", "Rule"):
            for et in ("has_concept", "has_rule", "genlMt", "depends_on",
                       "owns_microtheory"):
                try:
                    s.add_production({
                        "src": {"type": t, "var": "a"},
                        "edge_type": et,
                        "tgt": {"type": u, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "jw_deeper",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    """Install every domains/*.py install_<name>_seed(substrate) function."""
    installed = []
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                if len([p for p in inspect.signature(fn).parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
                        and p.default is inspect.Parameter.empty]) == 1:
                    fn(s)
                    installed.append((f.stem, m.group(1)))
            except Exception:
                continue
    return installed


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _holds_refs(term):
    """Walk a Term-tree (dict or list) and collect every Holds-referenced
    concept name."""
    out = []
    if isinstance(term, dict):
        if term.get("type") == "Holds":
            c = term.get("concept")
            if isinstance(c, str):
                out.append(c)
        for v in term.values():
            if isinstance(v, (dict, list)):
                out.extend(_holds_refs(v))
    elif isinstance(term, list):
        for x in term:
            out.extend(_holds_refs(x))
    return out


def _concept_mt_owner(s, concept_nid):
    """Find the first Microtheory that owns this concept via has_concept.
    Returns the Mt name or None."""
    owners = s.in_neighbours(concept_nid, "has_concept")
    if not owners:
        return None
    return s.node(owners[0])["attrs"].get("name", "?")


def _all_concept_owners(s, concept_nid):
    """Every Mt that has_concept-edges to this concept."""
    owners = s.in_neighbours(concept_nid, "has_concept")
    return [s.node(o)["attrs"].get("name", "?") for o in owners]


def _concept_seed_provenance():
    """Walk seeds/*.json; return {concept_name: [seed_file, ...]} so we can
    flag any concept that appears in >1 seed file."""
    out: dict[str, list[str]] = defaultdict(list)
    for f in sorted((ROOT / "seeds").glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        # Seeds vary in structure; look for typed-graph nodes AND
        # the flatter "concepts": [{name, definition}, ...] form.
        if isinstance(data, dict):
            for n in data.get("nodes", []):
                if isinstance(n, dict) and n.get("type") == "Concept":
                    nm = n.get("attrs", {}).get("name")
                    if isinstance(nm, str):
                        out[nm].append(f.name)
            for c in data.get("concepts", []):
                if isinstance(c, dict):
                    nm = c.get("name")
                    if isinstance(nm, str):
                        out[nm].append(f.name)
    return out


# ---------------------------------------------------------------------------
# 1. CONCEPT DUPLICATION
# ---------------------------------------------------------------------------

def survey_duplication(s):
    print("=" * 78)
    print("1. CONCEPT DUPLICATION — same name across multiple seeds/Mts")
    print("=" * 78)
    print()
    # In-substrate duplication: same name, multiple Concept nodes.
    by_name: dict[str, list[int]] = defaultdict(list)
    for c in s.nodes("Concept"):
        nm = s.node(c)["attrs"].get("name", "")
        if nm:
            by_name[nm].append(c)
    in_graph_dupes = {nm: nids for nm, nids in by_name.items() if len(nids) > 1}

    # Also walk seeds files directly — definitive provenance.
    seed_prov = _concept_seed_provenance()
    seed_dupes = {nm: seeds for nm, seeds in seed_prov.items()
                  if len(set(seeds)) > 1}

    print(f"  In-substrate Concept-node duplicates: {len(in_graph_dupes)}")
    print(f"  Seed-file Concept duplicates:         {len(seed_dupes)}")
    print()

    if in_graph_dupes:
        print("  Top in-substrate duplicates (with inconsistent definitions):")
        ranked = sorted(in_graph_dupes.items(), key=lambda x: -len(x[1]))
        shown = 0
        for nm, nids in ranked:
            defs = set()
            for nid in nids:
                d = str(s.node(nid)["attrs"].get("definition", ""))[:80]
                defs.add(d)
            if len(defs) > 1:
                owners = []
                for nid in nids:
                    owners.extend(_all_concept_owners(s, nid))
                print(f"    · {nm}  ({len(nids)} nodes, "
                      f"{len(defs)} distinct defs)")
                print(f"      owners: {sorted(set(owners))[:5]}")
                for d in list(defs)[:2]:
                    print(f"      def: {d}")
                shown += 1
                if shown >= 8:
                    break
        print()

    if seed_dupes:
        print(f"  Concepts named in >1 seed file (top 10):")
        ranked = sorted(seed_dupes.items(),
                        key=lambda x: -len(set(x[1])))[:10]
        for nm, seeds in ranked:
            print(f"    · {nm}  in {sorted(set(seeds))}")
        print()

    return {
        "in_graph_dupes": len(in_graph_dupes),
        "seed_dupes": len(seed_dupes),
        "in_graph_dupe_names": list(in_graph_dupes.keys()),
        "seed_dupe_names": list(seed_dupes.keys()),
    }


# ---------------------------------------------------------------------------
# 2. DEFINITION-PATTERN COVERAGE
# ---------------------------------------------------------------------------

def survey_definition_patterns(s):
    print("=" * 78)
    print("2. DEFINITION-PATTERN COVERAGE — patterns walker misses")
    print("=" * 78)
    print()
    # The current walker (concept_promotion_rules) covers ONE pattern:
    # equation-identity "X = Y".  Run it first to find which concepts
    # WERE promoted; the rest are walker-misses.
    try:
        from domains.concept_promotion_rules import (
            install_concept_promotion_rules, PROMOTED_CONCEPTS,
        )
        report = install_concept_promotion_rules(s)
        promoted_names = {nm for nm, _ in PROMOTED_CONCEPTS}
    except Exception as e:
        print(f"  walker run failed: {e}")
        return {}

    print(f"  Walker promoted: {len(promoted_names)} concepts")
    print(f"  Walker missed:   {len(s.nodes('Concept')) - len(promoted_names)} concepts")
    print()

    # Tally every linguistic-shape pattern across the WALKER-MISSED
    # population.  These are the candidate patterns the walker SHOULD
    # learn next.
    patterns = [
        ("X is the process of Y",        re.compile(r"\bis the process of\b", re.I)),
        ("X is the act of Y",            re.compile(r"\bis the act of\b", re.I)),
        ("X is the study of Y",          re.compile(r"\bis the study of\b", re.I)),
        ("X is a process of Y",          re.compile(r"\bis a process of\b", re.I)),
        ("X is the ability to Y",        re.compile(r"\bis the ability to\b", re.I)),
        ("X is the measure of Y",        re.compile(r"\bis the measure of\b", re.I)),
        ("X is the property of Y",       re.compile(r"\bis the property of\b", re.I)),
        ("X consists of A, B, C",        re.compile(r"\bconsists of\b", re.I)),
        ("X is composed of A, B, C",     re.compile(r"\bis composed of\b", re.I)),
        ("X is made (up )?of A, B, C",   re.compile(r"\bis made (up )?of\b", re.I)),
        ("X involves Y",                 re.compile(r"\binvolves\b", re.I)),
        ("X depends on Y",               re.compile(r"\bdepends on\b", re.I)),
        ("X requires Y",                 re.compile(r"\brequires\b", re.I)),
        ("X causes Y",                   re.compile(r"\bcauses\b", re.I)),
        ("X produces Y",                 re.compile(r"\bproduces\b", re.I)),
        ("X enables Y",                  re.compile(r"\benables\b", re.I)),
        ("X describes Y",                re.compile(r"\bdescribes\b", re.I)),
        ("X represents Y",               re.compile(r"\brepresents\b", re.I)),
        ("X refers to Y",                re.compile(r"\brefers to\b", re.I)),
        ("X has Y",                      re.compile(r"\bhas (a|an|the)\b", re.I)),
        ("X is a type of Y",             re.compile(r"\bis a (type|kind|form|sort|class) of\b", re.I)),
        ("X is the relation(ship)? Y",   re.compile(r"\bis the relation(ship)? \b", re.I)),
        ("X means Y",                    re.compile(r"\bmeans (that|to)?\b", re.I)),
        ("X operates on Y",              re.compile(r"\boperates on\b", re.I)),
        ("X transforms Y",               re.compile(r"\btransforms\b", re.I)),
        ("X maps Y to Z",                re.compile(r"\bmaps .* to\b", re.I)),
        ("X measures Y",                 re.compile(r"\bmeasures\b", re.I)),
        ("X if Y (conditional)",         re.compile(r"\bif\b", re.I)),
        ("X when Y (conditional)",       re.compile(r"\bwhen\b", re.I)),
        ("X equals Y / =",               re.compile(r"\b(equals|=)\b")),
        ("X is greater than Y",          re.compile(r"\bis greater than\b", re.I)),
        ("X assigns Y",                  re.compile(r"\bassigns\b", re.I)),
    ]

    missed_concepts = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        nm = a.get("name", "")
        defn = a.get("definition", "")
        if nm in promoted_names:
            continue
        if isinstance(defn, str) and defn:
            missed_concepts.append((nm, defn))

    counts: Counter = Counter()
    examples: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for nm, defn in missed_concepts:
        for pat_name, pat_re in patterns:
            if pat_re.search(defn):
                counts[pat_name] += 1
                if len(examples[pat_name]) < 2:
                    examples[pat_name].append((nm, defn[:120]))

    print(f"  Patterns found across {len(missed_concepts)} walker-missed concepts:")
    print()
    for pat_name, n in counts.most_common(15):
        print(f"    {n:>4}  {pat_name}")
    print()

    # 30-concept random sample, walker-missed: show their actual
    # definitions for human-eye pattern detection.
    print(f"  30-CONCEPT RANDOM SAMPLE (walker-missed; for eye-grep):")
    rng = random.Random(42)
    sample = rng.sample(missed_concepts, min(30, len(missed_concepts)))
    for nm, defn in sample:
        print(f"    · {nm}: {defn[:140]}")
    print()

    print(f"  TOP 3 unrecognized patterns (walker should learn):")
    top3 = counts.most_common(3)
    for pat_name, n in top3:
        print(f"    [{n} matches] {pat_name}")
        for ex_nm, ex_def in examples[pat_name][:2]:
            print(f"        example: {ex_nm}: {ex_def}")
    print()

    return {
        "n_missed": len(missed_concepts),
        "n_promoted": len(promoted_names),
        "top_patterns": top3,
        "counts": dict(counts),
    }


# ---------------------------------------------------------------------------
# 3. INTERNAL Mt CONNECTIVITY
# ---------------------------------------------------------------------------

def survey_internal_connectivity(s):
    print("=" * 78)
    print("3. INTERNAL Mt CONNECTIVITY — intra-Mt Holds references")
    print("=" * 78)
    print()
    # For each Mt, gather its concept names + their Term-trees (if any).
    # Count concepts whose Term-tree has at least one Holds(name)
    # referring to a sibling concept in the same Mt.
    from domains.concept_promotion_rules import PROMOTED_CONCEPTS
    try:
        from domains.concept_grounding import GROUNDED_CONCEPTS
    except Exception:
        GROUNDED_CONCEPTS = []

    term_lookup: dict[str, dict] = {}
    for nm, term in PROMOTED_CONCEPTS:
        term_lookup[nm] = term
    for nm, term in GROUNDED_CONCEPTS:
        term_lookup[nm] = term

    mt_concepts: dict[str, set[str]] = {}
    for mt in s.nodes("Microtheory"):
        nm = s.node(mt)["attrs"].get("name", "?")
        concepts = set()
        for c in s.neighbours(mt, "has_concept"):
            cn = s.node(c)["attrs"].get("name", "")
            if cn:
                concepts.add(cn)
        mt_concepts[nm] = concepts

    mt_with_internal: list[tuple[str, int, int]] = []  # (mt, intra-conns, n_concepts)
    flat_mts = []
    for mt_name, concepts in mt_concepts.items():
        intra = 0
        for cn in concepts:
            term = term_lookup.get(cn)
            if term is None:
                continue
            refs = set(_holds_refs(term))
            siblings = refs & (concepts - {cn})
            if siblings:
                intra += 1
        mt_with_internal.append((mt_name, intra, len(concepts)))
        if len(concepts) > 0 and intra == 0:
            flat_mts.append((mt_name, len(concepts)))

    print(f"  Total Mts: {len(mt_concepts)}")
    print(f"  Mts with concepts and ZERO intra-Mt Holds: {len(flat_mts)}")
    print(f"  Mts WITH at least one intra-Mt Holds:")
    has = [(m, i, n) for m, i, n in mt_with_internal if i > 0]
    has.sort(key=lambda x: -x[1])
    for m, i, n in has[:15]:
        print(f"    {m:<40} {i:>3} concepts ref-siblings  (/ {n})")
    print()
    print(f"  Largest FLAT Mts (>=10 concepts, none reference siblings):")
    flat_mts.sort(key=lambda x: -x[1])
    for m, n in flat_mts[:12]:
        if n >= 10:
            print(f"    {m:<40} {n} concepts, all isolated")
    print()
    return {
        "n_mts": len(mt_concepts),
        "n_flat_mts": len(flat_mts),
        "n_connected_mts": len(has),
        "largest_flat_mts": [(m, n) for m, n in flat_mts if n >= 10][:10],
    }


# ---------------------------------------------------------------------------
# 4. CIRCULAR CONCEPT PAIRS
# ---------------------------------------------------------------------------

def survey_circular_pairs(s):
    print("=" * 78)
    print("4. CIRCULAR CONCEPT PAIRS — A holds B, B holds A")
    print("=" * 78)
    print()
    from domains.concept_promotion_rules import PROMOTED_CONCEPTS
    try:
        from domains.concept_grounding import GROUNDED_CONCEPTS
    except Exception:
        GROUNDED_CONCEPTS = []

    # term_lookup
    term_lookup: dict[str, dict] = {}
    for nm, term in PROMOTED_CONCEPTS:
        term_lookup[nm] = term
    for nm, term in GROUNDED_CONCEPTS:
        term_lookup[nm] = term

    # refs[a] = set of concept names a's Term-tree Holds
    refs: dict[str, set[str]] = {}
    for nm, term in term_lookup.items():
        refs[nm] = set(_holds_refs(term))

    pairs: set[tuple[str, str]] = set()
    for a, rs in refs.items():
        for b in rs:
            if b in refs and a in refs[b] and a != b:
                pairs.add(tuple(sorted((a, b))))

    print(f"  Mutually-referencing concept pairs: {len(pairs)}")
    for a, b in sorted(pairs):
        print(f"    · {a}  <->  {b}")
    print()

    # Genuine vs accidental: a pair is GENUINE if both concepts are in
    # the same Mt AND the Mt's description (or seed metadata) signals
    # intentional reciprocity. Heuristic: pairs in the same Mt are
    # candidate genuine; cross-Mt pairs are suspect.
    same_mt = 0
    cross_mt = 0
    for a, b in pairs:
        a_owners = set()
        b_owners = set()
        for c in s.nodes("Concept"):
            nm = s.node(c)["attrs"].get("name", "")
            if nm == a:
                a_owners.update(_all_concept_owners(s, c))
            if nm == b:
                b_owners.update(_all_concept_owners(s, c))
        if a_owners & b_owners:
            same_mt += 1
        else:
            cross_mt += 1
    print(f"  Same-Mt pairs (likely genuine): {same_mt}")
    print(f"  Cross-Mt pairs (likely accidental): {cross_mt}")
    print()
    print("  Detection heuristic the substrate could adopt:")
    print("    GENUINE = both concepts in same Mt + Mt explicitly tags")
    print("              the Term-tree as reciprocal_definition")
    print("    ACCIDENTAL = cross-Mt mutual reference with no signal")
    print()
    return {
        "n_pairs": len(pairs),
        "same_mt": same_mt,
        "cross_mt": cross_mt,
        "pairs": [list(p) for p in sorted(pairs)],
    }


# ---------------------------------------------------------------------------
# 5. SHAPE DIVERSITY BY Mt
# ---------------------------------------------------------------------------

def survey_shape_diversity(s):
    print("=" * 78)
    print("5. SHAPE DIVERSITY BY Mt — which Mts contribute distinct shapes")
    print("=" * 78)
    print()
    from domains.concept_promotion_rules import PROMOTED_CONCEPTS
    try:
        from domains.concept_grounding import GROUNDED_CONCEPTS
    except Exception:
        GROUNDED_CONCEPTS = []

    term_lookup: dict[str, dict] = {}
    for nm, term in PROMOTED_CONCEPTS:
        term_lookup[nm] = term
    for nm, term in GROUNDED_CONCEPTS:
        term_lookup[nm] = term

    # Shape signature: the top-level "type" of the Term tree.
    def shape_sig(term):
        if isinstance(term, dict):
            return term.get("type", "Unknown")
        return "non-dict"

    mt_shapes: dict[str, set[str]] = defaultdict(set)
    mt_donor_count: Counter = Counter()
    # Map concept name -> owning Mt(s).
    concept_to_mts: dict[str, list[str]] = defaultdict(list)
    for c in s.nodes("Concept"):
        nm = s.node(c)["attrs"].get("name", "")
        if not nm:
            continue
        for o in _all_concept_owners(s, c):
            concept_to_mts[nm].append(o)

    for nm, term in term_lookup.items():
        sig = shape_sig(term)
        for mt_name in concept_to_mts.get(nm, []):
            mt_shapes[mt_name].add(sig)
            mt_donor_count[mt_name] += 1

    print(f"  Total Mts donating shapes: {len(mt_shapes)}")
    print(f"  Total distinct shape sigs (top-level Term type):")
    all_shapes = set()
    for shapes in mt_shapes.values():
        all_shapes |= shapes
    print(f"    {sorted(all_shapes)}")
    print()
    by_diversity = sorted(mt_shapes.items(),
                          key=lambda x: -len(x[1]))
    print(f"  Mts with HIGHEST shape diversity:")
    for mt_name, shapes in by_diversity[:8]:
        n_donors = mt_donor_count[mt_name]
        print(f"    {mt_name:<40}  shapes={sorted(shapes)} "
              f"(donors={n_donors})")
    print()
    single = [(m, list(sh)[0], mt_donor_count[m])
              for m, sh in mt_shapes.items() if len(sh) == 1]
    single.sort(key=lambda x: -x[2])
    print(f"  Mts with ONLY ONE shape (count: {len(single)}; top 10 by donors):")
    for mt_name, sh, n in single[:10]:
        print(f"    {mt_name:<40}  shape={sh}  (donors={n})")
    print()
    return {
        "n_donor_mts": len(mt_shapes),
        "n_distinct_shapes": len(all_shapes),
        "top_diversity": [(m, list(s)) for m, s in by_diversity[:5]],
        "single_shape_mts": len(single),
    }


# ---------------------------------------------------------------------------
# 6. DEFINITION-LENGTH DISTRIBUTION
# ---------------------------------------------------------------------------

def survey_definition_lengths(s):
    print("=" * 78)
    print("6. DEFINITION LENGTH DISTRIBUTION — stubs and over-longs")
    print("=" * 78)
    print()
    lens: list[tuple[str, int, str]] = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        nm = a.get("name", "")
        defn = a.get("definition", "")
        if isinstance(defn, str):
            lens.append((nm, len(defn), defn))
    lens.sort(key=lambda x: x[1])

    # Buckets
    empty = [(n, d) for n, ln, d in lens if ln == 0]
    very_short = [(n, ln, d) for n, ln, d in lens if 0 < ln < 50]
    short = [(n, ln, d) for n, ln, d in lens if 50 <= ln < 100]
    medium = [(n, ln, d) for n, ln, d in lens if 100 <= ln < 250]
    long_ = [(n, ln, d) for n, ln, d in lens if 250 <= ln < 500]
    very_long = [(n, ln, d) for n, ln, d in lens if ln >= 500]

    total = max(len(lens), 1)
    print(f"  Total concepts with definition attr: {len(lens)}")
    print(f"    empty            ({len(empty):>4}) {100*len(empty)/total:.1f}%")
    print(f"    very short <50   ({len(very_short):>4}) "
          f"{100*len(very_short)/total:.1f}%")
    print(f"    short      50-99 ({len(short):>4}) "
          f"{100*len(short)/total:.1f}%")
    print(f"    medium  100-249  ({len(medium):>4}) "
          f"{100*len(medium)/total:.1f}%")
    print(f"    long    250-499  ({len(long_):>4}) "
          f"{100*len(long_)/total:.1f}%")
    print(f"    very long >=500  ({len(very_long):>4}) "
          f"{100*len(very_long)/total:.1f}%")
    print()
    if very_short[:8]:
        print(f"  STUB-CANDIDATE (very short, may be unfinished):")
        for n, ln, d in very_short[:8]:
            print(f"    [{ln:>2}c]  {n}: {d!r}")
        print()
    if very_long[:5]:
        print(f"  DECOMPOSITION-CANDIDATE (very long, may need split):")
        for n, ln, d in very_long[:5]:
            print(f"    [{ln:>4}c]  {n}: {d[:160]}...")
        print()

    return {
        "total": len(lens),
        "empty": len(empty),
        "very_short": len(very_short),
        "very_long": len(very_long),
        "stub_examples": [n for n, _, _ in very_short[:10]],
        "long_examples": [n for n, _, _ in very_long[:5]],
    }


# ---------------------------------------------------------------------------
# 7. RULE DORMANCY
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "for", "in", "on",
    "at", "to", "from", "by", "with", "and", "or", "not", "but", "as",
    "if", "then", "when", "while", "this", "that", "these", "those",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "it", "its", "their", "they", "them", "he", "she", "his", "her",
    "i", "we", "you", "us", "our", "all", "any", "some", "many",
    "more", "most", "less", "least", "much", "such", "no", "yes",
    "so", "than", "also", "only", "just", "very", "still", "still",
    "can", "may", "must", "should", "would", "could", "will", "shall",
    "node", "edge", "type", "true", "false", "value", "name", "attr",
}


def _keywords(text: str) -> set[str]:
    text = re.sub(r"[^a-z0-9_ ]", " ", text.lower())
    out = set()
    for tok in text.split():
        if len(tok) <= 2 or tok in _STOPWORDS:
            continue
        if tok.isdigit():
            continue
        out.add(tok)
    return out


def survey_rule_dormancy(s):
    print("=" * 78)
    print("7. RULE DORMANCY — rules whose if/then keywords name no Concept")
    print("=" * 78)
    print()
    concept_names = {s.node(c)["attrs"].get("name", "").lower()
                     for c in s.nodes("Concept")}
    concept_names.discard("")
    # Tokenise concept names too, for partial matches.
    concept_tokens = set()
    for nm in concept_names:
        concept_tokens |= _keywords(nm)

    dormant = []
    total_rules = 0
    rules_with_text = 0
    matched = 0
    for r in s.nodes("Rule"):
        total_rules += 1
        a = s.node(r)["attrs"]
        nm = a.get("name", "?")
        # Rules can carry head/body OR if/then OR description.
        chunks = []
        for k in ("head", "body", "if", "then", "description",
                  "rationale"):
            v = a.get(k)
            if isinstance(v, str):
                chunks.append(v)
        text = " ".join(chunks).strip()
        if not text:
            continue
        rules_with_text += 1
        kws = _keywords(text)
        if not kws:
            continue
        if kws & (concept_names | concept_tokens):
            matched += 1
        else:
            dormant.append((nm, text[:140], kws))

    print(f"  Total Rule nodes:                 {total_rules}")
    print(f"  Rule nodes with text head/body/if/then: {rules_with_text}")
    print(f"  Rule nodes referencing a Concept:       {matched}")
    print(f"  DORMANT rules (no Concept overlap):     {len(dormant)}")
    print()
    if dormant[:8]:
        print(f"  Dormant rule examples (first 8):")
        for nm, txt, kws in dormant[:8]:
            sample_kws = sorted(kws)[:6]
            print(f"    · {nm}: {txt!r}")
            print(f"      keywords none-matched: {sample_kws}")
        print()
    return {
        "total": total_rules,
        "with_text": rules_with_text,
        "matched": matched,
        "dormant": len(dormant),
        "dormant_examples": [nm for nm, _, _ in dormant[:10]],
    }


# ---------------------------------------------------------------------------
# 8. CORTEX SCORE AXES THAT DON'T MOVE
# ---------------------------------------------------------------------------

def survey_axis_movement(s):
    print("=" * 78)
    print("8. CORTEX SCORE AXES — which axes don't discriminate")
    print("=" * 78)
    print()
    # Score every Mt as if it were the subject; collect per-axis values.
    try:
        from domains.architecture_assessment import (
            score_all_qualities, install_architecture_mt,
        )
    except Exception as e:
        print(f"  could not import scorer: {e}")
        return {}
    # Need to install the architecture Mt (which adds ArchitecturalQuality nodes).
    try:
        install_architecture_mt(s)
    except Exception:
        pass

    # Score per-Mt (treat each Mt as a "subject" — owns_microtheory edge
    # would normally point here; we use the Mt itself as a stand-in).
    axes_per_mt: dict[str, list[int]] = defaultdict(list)
    n_scored = 0
    n_mts = 0
    for mt in s.nodes("Microtheory"):
        n_mts += 1
        try:
            scores = score_all_qualities(s, mt)
        except Exception:
            continue
        if not scores:
            continue
        n_scored += 1
        for sc in scores:
            axes_per_mt[sc["quality_name"]].append(sc["score"])

    print(f"  Mts: {n_mts}, scored: {n_scored}")
    print()
    print(f"  Per-axis score distribution across {n_scored} Mts:")
    print(f"    {'axis':<32} {'min':>4} {'max':>4} {'mean':>6} "
          f"{'stuck-at':>12}")
    stuck_axes = []
    for axis, vals in sorted(axes_per_mt.items()):
        if not vals:
            continue
        mn = min(vals)
        mx = max(vals)
        mean = sum(vals) / len(vals)
        stuck = ""
        if mn == mx:
            stuck = f"ALL={mn}"
            stuck_axes.append((axis, mn))
        elif mx - mn <= 1:
            stuck = "near-stuck"
            stuck_axes.append((axis, mn))
        print(f"    {axis:<32} {mn:>4} {mx:>4} {mean:>6.2f}  {stuck}")
    print()
    if stuck_axes:
        print(f"  STUCK / NEAR-STUCK axes (no discriminative power):")
        for axis, val in stuck_axes:
            print(f"    · {axis}  (sits at {val})")
        print()
    return {
        "n_mts": n_mts,
        "n_scored": n_scored,
        "stuck_axes": stuck_axes,
        "axes_per_mt": {k: v for k, v in axes_per_mt.items()},
    }


# ---------------------------------------------------------------------------
# MAIN — emit verbatim findings + 3 ordered refactor proposals.
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("JABBERWOCK DEEPER SURVEY — structural issues surface scan misses")
    print("=" * 78)
    print()

    s = fresh_substrate()
    installed = install_all(s)
    print(f"  Installed {len(installed)} seeds")
    print(f"  Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    r1 = survey_duplication(s)
    r2 = survey_definition_patterns(s)
    r3 = survey_internal_connectivity(s)
    r4 = survey_circular_pairs(s)
    r5 = survey_shape_diversity(s)
    r6 = survey_definition_lengths(s)
    r7 = survey_rule_dormancy(s)
    r8 = survey_axis_movement(s)

    # ----- Synthesise three concrete refactors -----
    print("=" * 78)
    print("JABBERWOCK'S NEXT 3 PROPOSED REFACTORS")
    print("=" * 78)
    print()

    proposals: list[tuple[str, str, str]] = []  # (title, rationale, files/specifics)

    # Candidate 1: most-common unrecognized pattern → walker extension.
    if r2.get("top_patterns"):
        pat_name, n = r2["top_patterns"][0]
        proposals.append((
            f"EXTEND THE CONCEPT WALKER WITH PATTERN: \"{pat_name}\"",
            f"{n} walker-missed concepts match this pattern. Adding "
            f"a single parser stanza to "
            f"domains/concept_promotion_rules.py "
            f"would lift them all to Term-tree definitions in one pass.",
            "files: domains/concept_promotion_rules.py "
            "(add parse_<pattern_name>() + emit_<pattern_name>_term() "
            "alongside parse_equation_identity)",
        ))

    # Candidate 2: largest FLAT Mt → priority intra-Mt wiring target.
    if r3.get("largest_flat_mts"):
        top_flat = r3["largest_flat_mts"][:3]
        mt_list = ", ".join(f"{m} ({n}c)" for m, n in top_flat)
        proposals.append((
            f"WIRE INTRA-Mt HOLDS REFERENCES IN: {top_flat[0][0]}",
            f"{len(r3['largest_flat_mts'])} Mts have >=10 concepts AND "
            f"no concept Holds-references any sibling. They read as "
            f"flat lists, not theories. Biggest targets: {mt_list}.",
            f"files: seeds/{top_flat[0][0]}.json (and similar) — add "
            f"'term' fields with Holds() pointing at sibling concepts; "
            f"this also feeds shape diversity (axis 5).",
        ))

    # Candidate 3: pick from stuck axes, dormant rules, or duplicates.
    chose_third = False
    if r8.get("stuck_axes"):
        ax = r8["stuck_axes"][0]
        proposals.append((
            f"FIX STUCK CORTEX AXIS: {ax[0]} (sits at {ax[1]})",
            f"{len(r8['stuck_axes'])} of 5 cortex axes show no "
            f"variance across {r8['n_scored']} Mts — they cannot "
            f"discriminate good Mts from bad. Either change the "
            f"scorer's input signal or delete the axis to stop "
            f"inflating the cortex's 'overall' score.",
            f"files: domains/architecture_assessment.py "
            f"(score_{ax[0]}() — read a SIGNAL that VARIES across Mts, "
            f"e.g. concept Term-tree presence / shape diversity / "
            f"intra-Mt connectivity from survey #3 or #5)",
        ))
        chose_third = True
    if not chose_third and r7.get("dormant", 0) > 0:
        proposals.append((
            f"PRUNE / RE-TARGET {r7['dormant']} DORMANT RULES",
            f"These rules' if/then text names no existing Concept. "
            f"Either the Concepts they reference are missing "
            f"(should be added) or the rules are vestigial.",
            f"files: identify owners via has_rule edges; spot-check "
            f"first 10: {r7['dormant_examples']}",
        ))
        chose_third = True
    if not chose_third and r1.get("seed_dupes", 0) > 0:
        proposals.append((
            f"DEDUPE {r1['seed_dupes']} CROSS-SEED CONCEPT NAMES",
            f"Concept names appear in multiple seed files with "
            f"potentially divergent definitions. Mark one as canonical, "
            f"others as imports (via genlMt or has_concept-edge from "
            f"a single canonical Concept node).",
            f"sample dupe names: {r1['seed_dupe_names'][:8]}",
        ))

    # Print, ordered by impact (we keep insertion order — already roughly
    # by impact: pattern coverage = biggest bulk lift; intra-Mt wiring =
    # structural; cortex axis = measurement quality).
    for i, (title, rationale, specifics) in enumerate(proposals[:3], 1):
        print(f"  {i}. {title}")
        print(f"     rationale: {rationale}")
        print(f"     {specifics}")
        print()

    print("=" * 78)
    print("END OF DEEPER SURVEY")
    print("=" * 78)


if __name__ == "__main__":
    main()
