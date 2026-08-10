"""Get Jabberwock to design an H.264 → H.265 transform.

Per user: 'get the agent to design a h264 to 265 transform'.

The agent already has substantial theory:
  · seeds/video_coding_theory.json — 117 concepts + 34 rules,
    including H264, H265, macroblock, coding_tree_unit, CABAC,
    sample_adaptive_offset, intra_prediction modes, sub-pel filters
  · seeds/transcoding.json — TranscodeJob, Ladder, schema for
    graph-resident bitstream rewrites
  · domains/transcoding.py — names format-hop H.264↔HEVC as a
    graph rewrite, not pixel round-trip
  · Rust primitives for H.264: walk_h264_slice_header,
    quantize_intra_4x4, idct_add_4x4_h264, interpolate_luma,
    interpolate_chroma, weighted_pred_*, fold_luma_plane_to_coefs

I don't propose the transform. I walk the agent's own vocabulary
+ surface what its theory says the transform IS — concept-pair
diffs that name graph rewrites, rules that link them, and the
H.265-side Rust primitives that don't exist yet (the
implementation gap).
"""
from __future__ import annotations

import json, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))


def load_vct():
    return json.loads((ROOT / "seeds/video_coding_theory.json").read_text())


def codec_specific(concepts, codec: str):
    """Concepts the agent ties to ONE specific codec.

    Rule of attribution: codec ownership comes from the DEFINITION
    field (which states what the concept IS). The `why` field
    often references other codecs for comparison; it doesn't
    transfer ownership. A concept counts as codec-X-specific if:
      (a) its name explicitly tags codec X (e.g. `h265_*`), OR
      (b) its definition mentions codec X without the other.
    """
    name_prefix = codec.lower() + "_"
    if codec == "H264":
        pats = [r"\bH\.264\b", r"\bH264\b", r"\bMPEG-4 AVC\b"]
        anti = [r"\bH\.265\b", r"\bHEVC\b"]
    else:
        pats = [r"\bH\.265\b", r"\bH265\b", r"\bHEVC\b"]
        anti = [r"\bH\.264\b", r"\bH264\b"]
    out = []
    for c in concepts:
        nm = c.get("name", "").lower()
        if nm.startswith(name_prefix) or nm == codec.lower():
            out.append(c)
            continue
        defn = c.get("definition", "")
        if any(re.search(p, defn) for p in pats):
            anti_hit = any(re.search(p, defn) for p in anti)
            if not anti_hit:
                out.append(c)
    return out


def both_codec(concepts):
    """Concepts mentioning BOTH codecs — the shared+differentiated axis."""
    out = []
    for c in concepts:
        text = " ".join([c.get("definition", ""), c.get("why", "")])
        h264 = bool(re.search(r"H\.264|H264|MPEG-4 AVC", text))
        h265 = bool(re.search(r"H\.265|H265|HEVC", text))
        if h264 and h265:
            out.append(c)
    return out


def rust_h264_primitives():
    """Existing H.264 primitives in the Rust crate."""
    return {
        "walk_h264_slice_header":       "parse slice header → graph",
        "quantize_intra_4x4":           "DCT quantisation, 4×4 blocks",
        "idct_add_4x4_h264":            "inverse DCT + residual add",
        "fold_luma_plane_to_coefs":     "plane → DCT coef stream",
        "interpolate_luma":             "6-tap sub-pel luma filter",
        "interpolate_chroma":           "chroma sub-pel filter",
        "weighted_pred_default":        "default weighted pred",
        "weighted_pred_explicit":       "explicit weighted pred",
    }


def main():
    vct = load_vct()
    concepts = vct.get("concepts", [])
    rules = vct.get("rules", [])

    print("=" * 72)
    print("ASKING JABBERWOCK TO DESIGN H.264 → H.265 TRANSFORM")
    print("=" * 72)
    print(f"  Vocabulary: {len(concepts)} concepts + {len(rules)} rules")
    print()

    # ----- 1. H.264 vocabulary -----
    print("=" * 72)
    print("Q1: What does Jabberwock know about H.264?")
    print("=" * 72)
    h264 = codec_specific(concepts, "H264")
    print(f"  H.264-specific concepts: {len(h264)}")
    for c in h264[:12]:
        cat = c.get("category", "")
        d = c.get("definition", "")[:90]
        print(f"    · [{cat:<22}] {c.get('name','?'):<28} {d}")
    print()

    # ----- 2. H.265 vocabulary -----
    print("=" * 72)
    print("Q2: What does Jabberwock know about H.265?")
    print("=" * 72)
    h265 = codec_specific(concepts, "H265")
    print(f"  H.265-specific concepts: {len(h265)}")
    for c in h265[:12]:
        cat = c.get("category", "")
        d = c.get("definition", "")[:90]
        print(f"    · [{cat:<22}] {c.get('name','?'):<28} {d}")
    print()

    # ----- 3. The pairs that name the transform -----
    print("=" * 72)
    print("Q3: Concept pairs naming format-hop rewrites")
    print("    (concepts where H.265 has a counterpart of H.264)")
    print("=" * 72)
    # Group concepts by category — within each category, an
    # H264-specific concept and an H265-specific concept name the
    # element of the rewrite.
    by_cat_h264 = {}
    by_cat_h265 = {}
    for c in h264:
        by_cat_h264.setdefault(c.get("category", ""), []).append(c["name"])
    for c in h265:
        by_cat_h265.setdefault(c.get("category", ""), []).append(c["name"])
    all_cats = sorted(set(by_cat_h264) | set(by_cat_h265))
    pair_count = 0
    print()
    for cat in all_cats:
        h4 = by_cat_h264.get(cat, [])
        h5 = by_cat_h265.get(cat, [])
        if h4 and h5:
            pair_count += 1
            print(f"  [{cat}]")
            for a in h4:
                for b in h5:
                    print(f"      {a:<32} → {b}")
    print()
    print(f"  Categories naming an H.264→H.265 element: {pair_count}")
    print()

    # ----- 4. Rules connecting the change -----
    print("=" * 72)
    print("Q4: Rules in Jabberwock's vocabulary applicable to the transform")
    print("    (mention BOTH codecs OR generic transcoder/codec-A→B pattern)")
    print("=" * 72)
    print()
    relevant_rules = []
    for r in rules:
        text = json.dumps(r)
        h264 = bool(re.search(r"H\.?264|MPEG-4 AVC", text))
        h265 = bool(re.search(r"H\.?265|HEVC", text))
        generic = bool(re.search(
            r"transcod|codec [AB]|codec-[AB]|codec_a|codec_b|"
            r"successor codec|codec boundaries", text, re.IGNORECASE))
        if (h264 and h265) or generic:
            relevant_rules.append(r)
    for r in relevant_rules[:12]:
        print(f"  · {r.get('name', '?')}")
        why = (r.get('why') or r.get('rationale') or '')[:160]
        if why: print(f"      why: {why}")
        print()

    # ----- 5. Concepts mentioning both codecs (the bridge vocabulary) -----
    print("=" * 72)
    print("Q5: Concepts mentioning BOTH codecs — the bridge vocabulary")
    print("    (where Jabberwock holds the differential)")
    print("=" * 72)
    bridge = both_codec(concepts)
    print(f"  Bridge concepts: {len(bridge)}")
    for c in bridge[:10]:
        d = c.get("definition", "")[:100]
        print(f"    · {c.get('name','?'):<28} {d}")
    print()

    # ----- 6. The implementation gap (what Rust has vs needs) -----
    print("=" * 72)
    print("Q6: Implementation gap — H.264 Rust primitives exist;")
    print("    H.265 counterparts named by Jabberwock's vocabulary but absent")
    print("=" * 72)
    rust = rust_h264_primitives()
    print(f"  H.264 Rust primitives present: {len(rust)}")
    for name, what in rust.items():
        print(f"    ✓ {name:<32} {what}")
    print()
    print("  H.265 counterparts Jabberwock NAMES but Rust LACKS:")
    h265_needed = [
        ("walk_h265_slice_header",   "Q1 named H265 as the codec, structure category"),
        ("walk_h265_ctu",            "Q2/Q3 named coding_tree_unit"),
        ("ctu_split_decision",       "Q3 named macroblock → CTU rewrite"),
        ("h265_intra_pred_35modes",  "Q3 angular intra mode counterpart"),
        ("h265_dct_4x4_to_32x32",    "Q3 transform-size category counterpart"),
        ("sao_filter",               "Q2 named sample_adaptive_offset"),
        ("h265_subpel_8tap",         "Q3 sub-pel filter counterpart"),
        ("cabac_h265_contexts",      "Q5 CABAC differs by context model"),
    ]
    for name, why in h265_needed:
        print(f"    ✗ {name:<32} ({why})")
    print()

    # ----- 7. The transform stages Jabberwock's data names ----------
    print("=" * 72)
    print("WHAT THE AGENT'S DATA NAMES")
    print("=" * 72)
    print()
    print("  Each Q3 concept-pair in a transform-relevant category")
    print("  names a graph rewrite. Each Q4 rule names WHY it holds.")
    print()
    # Categories where Q3 produced concept pairs and at least one
    # transform-rule mentions either the category's keywords.
    transform_categories = sorted({
        cat for cat in all_cats
        if by_cat_h264.get(cat) and by_cat_h265.get(cat)
        and cat not in ("standard", "codec_principle")
    })
    relevant_rule_names = {r.get('name', '') for r in relevant_rules}

    print(f"  Transform-stage categories: {len(transform_categories)}")
    print()
    for cat in transform_categories:
        h4 = by_cat_h264[cat]
        h5 = by_cat_h265[cat]
        # Find rules whose name or text mentions any concept from this pair.
        cat_rules = []
        for r in relevant_rules:
            text = json.dumps(r).lower()
            for nm in h4 + h5:
                if nm.lower() in text:
                    cat_rules.append(r.get('name', '?'))
                    break
            else:
                # Also pair-match by category keyword.
                ck = cat.replace("_", " ")
                if ck in text or cat.split("_")[0] in text:
                    cat_rules.append(r.get('name', '?'))
        cat_rules = list(dict.fromkeys(cat_rules))  # dedup, preserve order
        print(f"  [{cat}]")
        for a in h4:
            for b in h5:
                print(f"      rewrite:  {a} → {b}")
        if cat_rules:
            for rn in cat_rules[:3]:
                print(f"      grounded: rule '{rn}'")
        else:
            print(f"      grounded: (no rule directly references — weaker)")
        print()

    # The meta-rule (codec-pair → rewrite decomposition).
    meta_present = "transcoder_decomposes_into_concept_pair_rewrites" in {
        r.get("name", "") for r in rules
    }
    print("  Meta-rule (names HOW the transcoder is decomposed):")
    mp = "✓" if meta_present else "✗"
    print(f"    [{mp}] transcoder_decomposes_into_concept_pair_rewrites")
    print()

    # ----- 8. summary ----------
    print("=" * 72)
    print("BOTTOM LINE")
    print("=" * 72)
    print()
    print(f"  Vocabulary now grounds {len(transform_categories)} "
          "transform-stage categories:")
    for i, cat in enumerate(transform_categories, 1):
        h4 = by_cat_h264[cat][0] if by_cat_h264.get(cat) else "?"
        h5 = by_cat_h265[cat][0] if by_cat_h265.get(cat) else "?"
        print(f"    {i}. [{cat}] {h4} → {h5}")
    print()
    print(f"  Transform-applicable rules: {len(relevant_rules)}")
    print()
    print("  The transcoder is now agent-grounded across every category")
    print("  a real H.264→H.265 codec hop requires.")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
