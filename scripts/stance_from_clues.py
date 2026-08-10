"""PROVE author STANCE toward a venue is a SHAPE read off the artifact's own
CHEAP SURFACE CLUES — to a TIGHT confidence window, with NO posting history and
NO held per-author tag.

THE MOVE (the cheap-shape / shape-matching efficiency, one level up). Stance is a
recognizable SHAPE, not a dossier: you read it off the artifact's surface (does it
speak the venue's in-group vocabulary? frame the owner/politics approvingly or
avoid them? promotional-to-an-audience or aligned-and-amplifying?) and MATCH that
clue vector against the venue's KNOWN alignment (already in the deep cone). A few
strong, agreeing clues pin the stance to high confidence. Recognize the pattern,
don't retrieve the person.

PROVEN here (no LLM, no Rust, no per-case Python decision, NO history lookup —
the stance shapes are graph data; the clue read is a cheap surface scan; the
match is the analogical/prototype overlap; the reweight is composition over the
venue cone):

  1. STANCE FROM CLUES, NO HISTORY:
     · an artifact that SPEAKS the in-group vocabulary + frames the owner/politics
       APPROVINGLY + amplifies  -> ENDORSES at HIGH confidence — inferred from the
       ARTIFACT ALONE (no author node, no history accessed).
     · a PROMOTIONAL / audience-directed artifact that AVOIDS the politics
       -> STAYED_FOR_AUDIENCE.
     · a NEUTRAL topical artifact -> INDIFFERENT (or abstain when clues are thin).
  2. TIGHT WINDOW, CHEAP: a few strong agreeing clues -> high confidence; the
     window is TIGHT when clues agree and DROPS / ABSTAINS when clues are
     mixed/absent. The clue read is a surface scan with NO history call
     (instrumented: history_accessed stays False on every inferred path).
  3. SAME ARTIFACT-TEXT, the inferred stance drives the venue×author reweighting:
     endorses -> AMPLIFY the venue alignment as the author's signal;
     stayed_for_audience -> DISCOUNT it. Driven by the INFERRED stance, not a tag.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.communication_concepts import install_communication_concepts_seed
from domains import contextualization_depth as cd
from domains import source_provenance as sp


def main() -> int:
    s = _native.Substrate()
    install_communication_concepts_seed(s)

    ok = True

    # the venue cone @2024 — its alignment web IS the in-group vocabulary the
    # clues are matched against (musk / politics / content_moderation / ...).
    cone = sp.context_for(s, "X post", "2024-03-01")
    alignment = tuple(c for c in (cone.get("implied") or [])
                      if c in cd._ALIGNMENT_CONCEPTS)
    print("=" * 76)
    print("THE VENUE ALIGNMENT (the in-group vocabulary the clues match against)")
    print("=" * 76)
    print(f"  venue cone @2024 alignment concepts: {sorted(alignment)}")
    print(f"  stance SHAPES (graph data, NOT per-author tags):")
    for st, shape in cd._STANCE_SHAPES.items():
        print(f"    {st:<20} {shape}")

    # ======================================================================
    # 1. STANCE FROM CLUES, NO HISTORY — three artifacts, NO author node.
    # ======================================================================
    print("\n" + "=" * 76)
    print("1 — STANCE INFERRED FROM THE ARTIFACT ALONE (no author, no history)")
    print("=" * 76)

    # an ENDORSER artifact: speaks in-group vocab + approving framing + amplifies.
    endorse_art = {
        "surface": ("finally a free speech town square — thank you Elon, no more "
                    "censorship, this is the way. real conversation is back."),
        "source": "X post", "when": "2024-03-01",
        "stake": 0.9, "surprise": 0.8, "relevance": 0.7}
    # a STAYED-FOR-AUDIENCE artifact: promotional / audience-directed, avoids
    # politics entirely.
    audience_art = {
        "surface": ("new drop is out now! check out our latest — link in bio. "
                    "still here for you, follow us for more. use code SPRING."),
        "source": "X post", "when": "2024-03-01",
        "stake": 0.9, "surprise": 0.8, "relevance": 0.7}
    # an INDIFFERENT / topical artifact: a neutral fact, no engagement either way.
    topical_art = {
        "surface": ("a manifold is a topological space that locally resembles "
                    "euclidean space near each point."),
        "source": "X post", "when": "2024-03-01",
        "stake": 0.9, "surprise": 0.8, "relevance": 0.7}

    # the TOPICAL case carries NO stance clues -> stance is NOT A SALIENT/RELEVANT
    # dimension for it. ABSTAINING IS SALIENCE, not an epistemic hedge: the agent
    # does not guess 'indifferent' and does not retrieve a dossier — it returns a
    # NOT-RELEVANT verdict (stance None, source 'not_salient'). That is the correct
    # read: a bare neutral fact has no stance, so the dimension does not apply.
    cases = [("ENDORSER", endorse_art, "endorses", {"inferred"}),
             ("STAYED_FOR_AUDIENCE", audience_art, "stayed_for_audience",
              {"inferred"}),
             ("TOPICAL (no stance clues)", topical_art, None, {"not_salient"})]

    inferred = {}
    for tag, art, expect, ok_srcs in cases:
        # author=None -> there is NO author node and NO history that COULD be read.
        st = cd.author_stance(s, None, "X post", artifact=art,
                              alignment_vocab=alignment)
        inferred[tag] = st
        print(f"\n  {tag}: {art['surface'][:60]!r}...")
        print(f"    clues  = {cd._clue_brief(st['clues'])}")
        print(f"    in-group hits = {st['clues'].get('in_group_hits')}")
        print(f"    -> stance={st['stance']!r}  confidence={st['confidence']}  "
              f"source={st['source']!r}")
        print(f"    history_accessed = {st['history_accessed']}")
        good = (st["stance"] == expect and st["source"] in ok_srcs
                and st["history_accessed"] is False)
        print(f"  [{'OK ' if good else 'XX '}] read {expect!r} from the "
              f"artifact alone, no history (source={st['source']!r})")
        ok = ok and good

    # the ENDORSER read must be HIGH confidence (a few strong agreeing clues).
    endo = inferred["ENDORSER"]
    high_conf = endo["confidence"] >= 0.6 and endo["match"]["margin"] >= 2
    print(f"\n  [{'OK ' if high_conf else 'XX '}] ENDORSER pinned at HIGH "
          f"confidence {endo['confidence']} (clean margin "
          f"{endo['match']['margin']}) — a few strong clues -> a tight window")
    ok = ok and high_conf

    # ======================================================================
    # 2. TIGHT WINDOW vs ABSTAIN — strong-agreeing clues are tight; a MIXED
    #    read is lower; a NO-CLUE artifact abstains (honest thin read).
    # ======================================================================
    print("\n" + "=" * 76)
    print("2 — TIGHT when clues agree; LOWER when mixed; ABSTAIN when thin")
    print("=" * 76)

    # a MIXED artifact: promotional markers AND an in-group/approving phrase —
    # the clues pull toward two shapes, so the margin shrinks and confidence drops.
    mixed_art = {
        "surface": ("free speech is back — also check out our new drop, link in "
                    "bio! follow us."),
        "source": "X post", "when": "2024-03-01"}
    st_mixed = cd.author_stance(s, None, "X post", artifact=mixed_art,
                                alignment_vocab=alignment)
    # a NO-CLUE artifact: a bare claim, no surface markers at all -> abstain.
    thin_art = {"surface": "a claim about the world", "source": "X post"}
    st_thin = cd.author_stance(s, None, "X post", artifact=thin_art,
                               alignment_vocab=alignment)

    print(f"\n  STRONG (endorser) : conf={endo['confidence']}  "
          f"margin={endo['match']['margin']}  overlaps={endo['match']['overlaps']}")
    print(f"  MIXED             : conf={st_mixed['confidence']}  "
          f"margin={st_mixed['match']['margin']}  "
          f"overlaps={st_mixed['match']['overlaps']}  stance={st_mixed['stance']!r}")
    print(f"  THIN (no clues)   : source={st_thin['source']!r}  "
          f"stance={st_thin['stance']!r}  relevant={st_thin.get('relevant')}")
    tight_drops = st_mixed["confidence"] < endo["confidence"]
    # ABSTAIN IS SALIENCE: no clues -> stance NOT RELEVANT (None / 'not_salient'),
    # a decisive verdict — NOT a low-conf guess, NOT a held-tag dossier fallback.
    thin_not_relevant = (st_thin["source"] == "not_salient"
                         and st_thin["stance"] is None
                         and st_thin.get("relevant") is False)
    print(f"\n  [{'OK ' if tight_drops else 'XX '}] the window is TIGHT on agreeing "
          f"clues and DROPS when clues are mixed")
    print(f"  [{'OK ' if thin_not_relevant else 'XX '}] a no-clue artifact -> stance "
          f"NOT RELEVANT (abstaining IS salience: a verdict, not a guess/dossier)")
    ok = ok and tight_drops and thin_not_relevant

    # CHEAP / NO HISTORY on every inferred path (instrumented).
    no_hist = all(v["history_accessed"] is False for v in inferred.values()) \
        and st_mixed["history_accessed"] is False
    print(f"  [{'OK ' if no_hist else 'XX '}] NO author history accessed on any "
          f"inferred path (the read is the cheap surface scan only)")
    ok = ok and no_hist

    # ======================================================================
    # 3. THE INFERRED STANCE DRIVES THE VENUE×AUTHOR REWEIGHTING (not a tag).
    # ======================================================================
    print("\n" + "=" * 76)
    print("3 — the INFERRED stance drives the venue×author reweighting")
    print("=" * 76)

    # SAME venue@when; the stance comes from the ARTIFACT TEXT, no held tag, no
    # author node -> different deep context purely from the inferred shape.
    d_endo = cd.deep_context_for_author(
        s, "X post", "2024-03-01", author=None, artifact=endorse_art)
    d_aud = cd.deep_context_for_author(
        s, "X post", "2024-03-01", author=None, artifact=audience_art)

    print(f"\n  venue cone @2024 (SAME for both): name={d_endo['name']!r} "
          f"owner={d_endo['owner']!r}")
    print(f"\n  ENDORSER artifact -> stance={d_endo['stance']!r} "
          f"(conf {d_endo['stance_confidence']}, src {d_endo['stance_source']!r})")
    print(f"    AMPLIFIED  = {d_endo.get('amplified')}")
    print(f"    author_signal = {d_endo['author_signal']}")
    print(f"\n  AUDIENCE artifact -> stance={d_aud['stance']!r} "
          f"(conf {d_aud['stance_confidence']}, src {d_aud['stance_source']!r})")
    print(f"    DISCOUNTED  = {d_aud['discounted']}")
    print(f"    author_signal = {d_aud['author_signal']}")

    same_cone = (d_endo["implied"] == d_aud["implied"]
                 and d_endo["name"] == d_aud["name"])
    align_set = set(c for c in d_endo["implied"] if c in cd._ALIGNMENT_CONCEPTS)
    endo_amplifies = (set(d_endo.get("amplified") or []) == align_set
                      and align_set <= set(d_endo["author_signal"]))
    aud_discounts = (set(d_aud["discounted"]) == align_set and len(align_set) > 0
                     and not (align_set & set(d_aud["author_signal"])))
    inferred_src = (d_endo["stance_source"] == "inferred"
                    and d_aud["stance_source"] == "inferred"
                    and d_endo["history_accessed"] is False)
    print()
    print(f"  [{'OK ' if same_cone else 'XX '}] the VENUE cone is identical for both "
          f"artifacts")
    print(f"  [{'OK ' if endo_amplifies else 'XX '}] the INFERRED endorser AMPLIFIES "
          f"the alignment {sorted(align_set)} as the author's signal")
    print(f"  [{'OK ' if aud_discounts else 'XX '}] the INFERRED audience-stayer "
          f"DISCOUNTS the alignment (venue=noise)")
    print(f"  [{'OK ' if inferred_src else 'XX '}] BOTH stances are INFERRED from "
          f"the artifact (source='inferred'), NO history accessed")
    ok = ok and same_cone and endo_amplifies and aud_discounts and inferred_src

    print("\n" + "=" * 76)
    print("RESULT:", "ALL OK" if ok else "FAILURE")
    print("=" * 76)
    print("""
The LEARNING: AUTHOR STANCE toward a venue is now a SHAPE read off the artifact's
own CHEAP SURFACE CLUES — to a TIGHT confidence window — with NO posting history
and NO held per-author tag. The clue read (in-group vocabulary, framing polarity,
register, engagement) is a surface scan matched against the venue cone's KNOWN
alignment; the clue vector is shape-matched against three held stance SHAPES
(graph data) -> stance + confidence. A few strong, agreeing clues pin a TIGHT
window (endorses, high conf); mixed clues lower it; a no-clue artifact ABSTAINS
(falling to a weak held prior / neutral default — NOT a confident guess). The
inferred stance then drives the venue×author reweighting. This is the cheap-shape
/ shape-matching efficiency one level up: recognize the pattern, don't retrieve
the person.

FAITHFUL: the stance shapes are graph data; the clue extraction is a cheap
surface scan; the match reuses the analogical/prototype overlap; the reweight is
composition over the venue cone. No LLM, no Rust, no per-case Python decision,
NO history lookup (instrumented: history_accessed=False on every inferred path).

HONEST / coarse: the clue set is a small surface-marker vocabulary; the in-group
vocabulary is SEEDED from the venue cone's alignment concepts; the confidence is
the shape-match overlap, NOT a calibrated probability. A held tag survives only
as an optional fallback PRIOR when the artifact carries zero clues.""")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
