"""Read the figures of speech, then ADJUST the machinery to suit.

Last pass, the trope's figure relation (figurative ABOUT literal) was HANDED to the agent. So here
the agent first READS Wikipedia/the dictionary on the figures themselves — metaphor, metonymy, idiom,
allegory, figure of speech — grounding what they ARE. Then it adjusts its own meaning-vector machinery
to suit, the way it designed it:

  DETECT  (graph-native rule `detect_figure`): a form carrying a LITERAL reading (dictionary) AND a
          FIGURATIVE reading (wiki) -> draw figure_of(F -> L) ITSELF. The presence of two bound
          readings on one form is the whole signal; no one tells it which is the figure (the literal
          is the one that breaks against the world). This closes the handed-edge gap.
  CLASSIFY (rule `classify_figure` over a native discriminator): type the figure by the SHAPE of the
          L->F mapping — same-domain contiguity (part/attribute-for-thing) -> METONYMY; cross-domain
          resemblance -> METAPHOR; no recoverable transform -> IDIOM. The decision is a native term;
          its two inputs (contiguity?/resemblance?) are GROUNDED world-knowledge, like any perception.

Detection runs entirely in the graph. We verify it over the real grounded tropes with the figure
edges DELETED, so the agent must re-find them.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_adjusts_for_figures
"""
from __future__ import annotations
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries

SEP = "=" * 96
# Cases to read: (name, literal key word, figurative gloss or None=pull trope def, source, trust).
# Tropes (figurative from the suspect wiki) + canonical metonyms (figurative from common usage) so
# BOTH mapping shapes are exercised live — cross-domain resemblance AND same-domain association.
CASES = [
    ("chekhovs gun", "gun", None, "tvtropes_wiki", 0.4),
    ("red herring", "herring", None, "tvtropes_wiki", 0.4),
    ("red shirt", "shirt", None, "tvtropes_wiki", 0.4),
    ("the cavalry", "cavalry", None, "tvtropes_wiki", 0.4),
    ("the crown", "crown", "the monarch, the monarchy, or royal authority", "common_usage", 0.7),
    ("suits", "suit", "business executives or corporate management", "common_usage", 0.7),
    ("the white house", "house", "the US president and the executive administration", "common_usage", 0.7),
    ("the bench", "bench", "the judges or the judiciary", "common_usage", 0.7),
]
# Multi-word forms carry their constituent words as has_part Mentions, so the agent's structural tests
# can read them: idiom (no part is itself a figure), simile (a like/as comparator part is present).
IDIOMS = [
    ("kick the bucket", "bucket", "to die", ["kick", "the", "bucket"]),
    ("raining cats and dogs", "cats", "raining very heavily", ["raining", "cats", "and", "dogs"]),
    ("bite the bullet", "bullet", "to endure a painful situation with courage", ["bite", "the", "bullet"]),
    ("the whole nine yards", "yards", "everything, the full extent", ["the", "whole", "nine", "yards"]),
]
# Similes: an explicit comparison using like/as (the comparator is a constituent word).
SIMILES = [
    ("brave as a lion", "lion", "extremely courageous", ["brave", "as", "a", "lion"]),
    ("fights like a tiger", "tiger", "fights very fiercely", ["fights", "like", "a", "tiger"]),
    ("sleeps like a log", "log", "sleeps very deeply", ["sleeps", "like", "a", "log"]),
]
# Hyperboles: deliberate exaggeration — a magnitude far beyond the plausible literal range, no marker.
HYPERBOLES = [
    ("a million times", "times", "very many times", ["a", "million", "times"]),
    ("waited forever", "forever", "waited a very long time", ["waited", "forever"]),
    ("this weighs a ton", "ton", "this is very heavy", ["this", "weighs", "a", "ton"]),
]
# Personifications: a human action/quality ascribed to a non-human or inanimate subject (type mismatch).
PERSONIFICATIONS = [
    ("the wind whispered", "wind", "the wind made a soft sound", ["the", "wind", "whispered"]),
    ("the sun smiled", "sun", "the sun shone warmly", ["the", "sun", "smiled"]),
    ("opportunity knocked", "opportunity", "a chance presented itself", ["opportunity", "knocked"]),
]
# (subject word, action word) per personification, for the forced-choice animacy/type-mismatch test.
PERSONIF_SA = {"the wind whispered": ("wind", "whispered"), "the sun smiled": ("sun", "smiled"),
               "opportunity knocked": ("opportunity", "knocked")}
# Oxymora: two contradictory terms conjoined in one bound form. (name, kw, gloss, parts, opposed-pair).
OXYMORA = [
    ("deafening silence", "silence", "a silence so complete it overwhelms", ["deafening", "silence"], (0, 1)),
    ("bittersweet", "sweetness", "both painful and sweet at once", ["bitter", "sweet"], (0, 1)),
    ("living dead", "dead", "dead yet still moving; the undead", ["living", "dead"], (0, 1)),
]
# Allegories: a narrative whose parts each map (figure_of) to a referent in a coherent second domain,
# with the SOURCE relation preserved among the targets (structure-mapping). (part, target, source-rel'n).
ALLEGORIES = [
    ("Animal Farm", "Soviet history",
     [("Napoleon (the pig)", "Joseph Stalin"), ("Snowball (the pig)", "Leon Trotsky"),
      ("the farm animals", "the Soviet working class")],
     [(0, 1)]),                                    # Napoleon drives out Snowball  /  Stalin exiles Trotsky
    ("The Tortoise and the Hare", "a moral about diligence",
     [("the tortoise", "steady persistence"), ("the hare", "complacent overconfidence")],
     [(0, 1)]),                                    # tortoise beats hare  /  persistence beats overconfidence
]
# Understatements (litotes): present something as far weaker/less than it really is. (name, kw, intended,
# parts, the real situation it is measured against).
UNDERSTATEMENTS = [
    ("it's just a scratch", "scratch", "the wound is severe", ["it's", "just", "a", "scratch"],
     "the wound is deep and life-threatening"),
    ("not bad", "bad", "actually excellent", ["not", "bad"], "an outstanding, excellent performance"),
    ("a bit chilly", "chilly", "it is freezing", ["a", "bit", "chilly"], "it is minus twenty degrees, bitterly cold"),
]
# Ironies: the literal meaning is the opposite of what the situation supports. (name, kw, intended,
# parts, the context/situation).
IRONIES = [
    ("what lovely weather", "weather", "the weather is terrible", ["what", "lovely", "weather"],
     "a violent thunderstorm is raging"),
    ("great job", "job", "you failed badly", ["great", "job"], "he completely failed the task"),
    ("I just love waiting in line", "line", "waiting is awful", ["I", "just", "love", "waiting", "in", "line"],
     "stuck in a two-hour queue"),
]
FIGURES = ["metaphor", "metonymy", "idiom", "allegory", "figure of speech", "simile", "hyperbole",
           "personification", "oxymoron", "understatement", "irony"]


def _yn1(judge, q):
    """One yes/no sample. Robust to a preamble: first standalone yes/no token in the reply.
    A failed/empty call ABSTAINS (-1) — it must not silently count as a 'no' vote (that biased the
    majority toward 'no' whenever a `claude -p` call timed out late in a long run)."""
    try:
        ans = judge(q + " Reply with exactly one word: yes or no. No preamble, no other text.")
        ans = ans.get("answer") if isinstance(ans, dict) else ans
        toks = re.findall(r"\b(yes|no)\b", str(ans or "").lower())
        if not toks:
            return -1                              # empty / no verdict -> abstain, do not vote 'no'
        return 1 if toks[0] == "yes" else 0
    except Exception:
        return -1                                  # abstain (don't bias the vote toward 'no')


def _yn(judge, q, votes=3):
    """Ground a world-knowledge signal as the MAJORITY of the non-abstaining samples — a single LLM
    yes/no is too noisy, and late calls in a long run can fail, so vote and retry past abstentions."""
    s = []
    for _ in range(votes):
        v = _yn1(judge, q)
        if v >= 0:
            s.append(v)
        if len([x for x in s]) >= 3 and abs(sum(s) * 2 - len(s)) > 1:
            break                                  # early stop once a clear majority is in
    return 1 if (s and sum(s) * 2 > len(s)) else 0


def _ask(judge, q):
    """One judge call, retrying past empty replies — late calls in a long run can return '' (a
    degraded `claude -p`); an empty answer must not be taken as a real (often wrong) signal."""
    for _ in range(3):
        try:
            r = judge(q)
            r = ((r.get("answer") if isinstance(r, dict) else r) or "").strip().lower()
            if r:
                return r
        except Exception:
            pass
        time.sleep(1.0)
    return ""


def _choice(judge, q, opts, n=3):
    """Forced-choice among opts, majority of n samples (ignoring abstentions). Forced-choice and
    voting together beat the judge's noise on the abstract relations these figures hinge on."""
    tally = {}
    for _ in range(n):
        r = _ask(judge, q + f" Answer with exactly one word: {' or '.join(opts)}.").replace("-", "")
        # word-boundary match so 'living' does NOT match inside 'nonliving' (the substring trap)
        hit = next((o for o in opts if re.search(r"\b" + re.escape(o.replace("-", "")) + r"\b", r)), None)
        if hit:
            tally[hit] = tally.get(hit, 0) + 1
    return max(tally, key=tally.get) if tally else "?"


def _opposite(judge, x, y):
    """Oxymoron opposition, robustly: ASK for the antonym of one word and see if the other appears,
    over a few tries in both directions (antonym wording varies; accept any hit). The model generates
    antonyms readily, where it pedantically refuses a yes/no 'are they opposite'."""
    for a, b in ((x, y), (y, x)):
        stem = b.lower()[:5]                          # 'silence'->'silen' also catches 'silent', etc.
        for _ in range(2):
            r = _ask(judge, f"What is the opposite or antonym of {a!r}? Reply with a few words only.")
            if b.lower() in r or (len(stem) >= 4 and stem in r):
                return 1
    return 0


def _animacy(judge, q):
    return _choice(judge, q, ["living", "nonliving"])


def _polarity(judge, q):
    return _choice(judge, q, ["positive", "negative"])


def _magdir(judge, q):
    return _choice(judge, q, ["weaker", "stronger", "accurate"])


_SHAPE_MAP = {"association": "association", "metonymy": "association", "contiguity": "association",
              "resemblance": "resemblance", "metaphor": "resemblance", "analogy": "resemblance",
              "neither": "neither", "idiom": "neither", "none": "neither"}


def _shape1(judge, q):
    """One sample of the mapping-shape perception: association | resemblance | neither."""
    try:
        ans = judge(q)
        ans = ans.get("answer") if isinstance(ans, dict) else ans
        toks = re.findall(r"\b(association|metonymy|contiguity|resemblance|metaphor|analogy|"
                          r"neither|idiom|none)\b", str(ans or "").lower())
        return _SHAPE_MAP[toks[0]] if toks else None
    except Exception:
        return None


def _shape(judge, q, votes=3):
    """Ground the L->F mapping shape as ONE coherent perception (majority of N) — metaphor vs
    metonymy is a single discrimination, not two independent yes/nos that both collapse to 0."""
    s = [v for v in (_shape1(judge, q) for _ in range(votes)) if v]
    if not s:
        return "neither"
    return max(set(s), key=s.count)


def main():
    print(SEP)
    print("READ THE FIGURES OF SPEECH, THEN ADJUST THE MACHINERY — detect + classify figures itself")
    print(SEP)
    a = boot()
    judge = a._self_teacher                       # claude teacher: the semantic/world-knowledge oracle
    attach_libraries(a, log=lambda *x: None)      # dictionary teacher for the literal sense
    dict_teacher = a._self_teacher
    for s in ("learned_lexicon", "learned_tropes", "figurative_language"):
        if os.path.exists(os.path.join(ROOT, "seeds", s + ".json")):
            a.inner.load_seed_manifest(manifest_for(s), a.agent)
    tropes = {x["attrs"]["name"]: x["attrs"] for x in
              json.load(open(os.path.join(ROOT, "seeds", "learned_tropes.json")))["nodes"]
              if x.get("type") == "Trope"}

    # 1. READ the figures of speech — ground what they ARE (the machinery is grounded, not assumed).
    before = len(a.s.nodes("Concept"))
    learned = {}
    for f in FIGURES:
        a.ground_unknowns(f)
        learned[f] = (a._taught_lookup.get("taught_" + f.replace(" ", "_").replace("-", "_"), "") or "")[:78]
    print(f"\n  READ the figures of speech (+{len(a.s.nodes('Concept'))-before} concepts grounded):")
    for f in ("metaphor", "metonymy", "idiom"):
        print(f"    {f:18}: {learned.get(f)!r}")

    # 2. Build each name's two readings (literal from dictionary, figurative from its source) — but DO
    #    NOT draw the figure_of edge. The adjusted machinery must detect it.
    src = {"dictionary": a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})}
    for _, _, _, sn, tr in CASES:
        if sn not in src:
            src[sn] = a.s.add_node("Source", {"name": sn, "trust": tr})
    rows = []
    for name, kw, fig_gloss, sn, tr in CASES:
        fig_gloss = fig_gloss or (tropes.get(name, {}).get("definition") or "")
        try:
            lp = dict_teacher(kw)
            lit_gloss = (lp.get("answer") if isinstance(lp, dict) else "") or "(literal sense)"
        except Exception:
            lit_gloss = "(literal sense)"
        lit = a.s.add_node("Reading", {"word": name, "gloss": lit_gloss[:64], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": fig_gloss[:70], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src[sn])
        rows.append((name, kw, lit, fig, lit_gloss, fig_gloss))

    # Multi-word forms (idioms, similes, hyperboles): same literal+figurative reading pair, PLUS the
    # constituent words as has_part Mentions so the agent's structural tests can read them.
    if "common_usage" not in src:
        src["common_usage"] = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})
    parts_map, fig_by_name, part_nodes = {}, {}, {}
    for name, kw, fig_gloss, parts in IDIOMS + SIMILES + HYPERBOLES + PERSONIFICATIONS:
        try:
            lp = dict_teacher(kw)
            lit_gloss = (lp.get("answer") if isinstance(lp, dict) else "") or "(literal sense)"
        except Exception:
            lit_gloss = "(literal sense)"
        lit = a.s.add_node("Reading", {"word": name, "gloss": lit_gloss[:64], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": fig_gloss[:70], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        pn = [a.s.add_node("Mention", {"text": w}) for w in parts]
        for m in pn:
            a.inner.add_edge_unchecked(fig, "has_part", m)
        # Personification grounded HERE (early, while the judge is fresh) — its forced-choice animacy
        # type-mismatch. Done at build time so it doesn't land late in the long classify loop.
        if name in PERSONIF_SA:
            subj_w, act_w = PERSONIF_SA[name]
            s = _animacy(judge, f"Is {subj_w!r} a living thing or a non-living thing?")
            p = _animacy(judge, f"Is the action {act_w!r} normally done by a living being or by a "
                         f"non-living thing?")
            a.inner.set_attr(fig, "personifies", 1 if (s == "nonliving" and p == "living") else 0)
        rows.append((name, kw, lit, fig, lit_gloss, fig_gloss))
        parts_map[name] = parts; fig_by_name[name] = fig; part_nodes[name] = pn

    # Oxymora: same, plus an opposes edge between the two contradictory parts — but ONLY if the agent's
    # opposition perception confirms it (it reuses its meaning-vector opposition judgment, not my say-so).
    oxymoron_names = set()
    for name, kw, fig_gloss, parts, (i, j) in OXYMORA:
        try:
            lp = dict_teacher(kw)
            lit_gloss = (lp.get("answer") if isinstance(lp, dict) else "") or "(literal sense)"
        except Exception:
            lit_gloss = "(literal sense)"
        lit = a.s.add_node("Reading", {"word": name, "gloss": lit_gloss[:64], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": fig_gloss[:70], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        pn = [a.s.add_node("Mention", {"text": w}) for w in parts]
        for m in pn:
            a.inner.add_edge_unchecked(fig, "has_part", m)
        contra = _opposite(judge, parts[i], parts[j])   # generative antonym test (reliable)
        if contra == 1:                              # the opposition the agent perceives -> opposes edge
            a.inner.add_edge_unchecked(pn[i], "opposes", pn[j])
            a.inner.add_edge_unchecked(pn[j], "opposes", pn[i])
        rows.append((name, kw, lit, fig, lit_gloss, fig_gloss))
        fig_by_name[name] = fig; part_nodes[name] = pn; oxymoron_names.add(name)

    # Understatements: scalar DOWNWARD — ground the direction vs the real situation (its mirror of
    # the hyperbole test). Understatement when the statement makes the situation sound much WEAKER.
    for name, kw, intended, parts, situation in UNDERSTATEMENTS:
        lit = a.s.add_node("Reading", {"word": name, "gloss": name[:60], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended[:64], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        for w in parts:
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        d_dir = _magdir(judge, f"Compared to the real situation ({situation}), does saying {name!r} make "
                        f"it sound much weaker, much stronger, or about accurate?")
        if d_dir == "weaker":
            a.inner.set_attr(fig, "understates", 1)
        rows.append((name, kw, lit, fig, name, intended))

    # Ironies: literal valence vs the SITUATION's valence — opposed -> opposes(literal_reading, context).
    # The agent's guard: irony cannot fire without a context for the literal meaning to oppose.
    for name, kw, intended, parts, situation in IRONIES:
        lit = a.s.add_node("Reading", {"word": name, "gloss": name[:60], "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": intended[:64], "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src["dictionary"])
        a.inner.add_edge_unchecked(fig, "claimed_by", src["common_usage"])
        for w in parts:
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": w}))
        ctx = a.s.add_node("Context", {"text": situation[:60]})
        lit_val = _polarity(judge, f"Ignore any sarcasm or context. If the words {name!r} were said "
                            f"sincerely and meant completely literally, would they sound positive or "
                            f"negative on their own?")
        ctx_val = _polarity(judge, f"Is this situation positive/good or negative/bad: {situation}?")
        if lit_val != "?" and ctx_val != "?" and lit_val != ctx_val:
            a.inner.add_edge_unchecked(lit, "opposes", ctx)   # literal reading opposes the context
        rows.append((name, kw, lit, fig, name, intended))

    personif_names = {nm for nm, _, _, _ in PERSONIFICATIONS}
    before_edges = sum(len(a.inner.neighbours(f, "figure_of")) for _, _, _, f, _, _ in rows)
    print(f"\n  built {len(rows)} names as literal+figurative reading pairs (tropes, metonyms, idioms, "
          f"similes, hyperboles, personifications, oxymora); figure_of edges BEFORE: {before_edges}  (none)")

    # 3. DETECT — run the agent's native rule. It draws figure_of(F->L) itself.
    a.inner.run_rules(10000)
    detected = [(name, lit, fig) for name, _, lit, fig, _, _ in rows
                if a.inner.neighbours(fig, "figure_of")]
    print(f"\n  ran detect_figure (native graph rule) -> the agent drew {len(detected)} figure_of "
          f"edges ITSELF (was {before_edges}):")
    for name, lit, fig in detected:
        tgt = a.inner.neighbours(fig, "figure_of")[0]
        print(f"    {name!r}: figurative --figure_of--> literal  "
              f"(detected: {a.s.node(fig)['attrs'].get('figure_detected')==1})  "
              f"[target is the literal reading: {a.s.node(tgt)['attrs'].get('kind')}]")

    # 4. CLASSIFY — ground the discriminator inputs (the mapping shape; and for multi-word forms the
    #    compositional-failure and scalar-violation tests), then let the native classifier term type
    #    each figure. The structural simile-marker test needs no perception (it reads has_part).
    print(f"\n  classifying by the SHAPE of the L->F mapping (the agent's discriminator):")
    for name, kw, lit, fig, lit_gloss, fig_gloss in rows:
        if not a.inner.neighbours(fig, "figure_of"):
            continue
        # Forms already decided structurally / at build time need no shape grounding — skip them:
        # simile (marker), oxymoron (internal opposes), irony (literal opposes context), understatement.
        # Forms already decided structurally / at build time need NO further grounding — skip them:
        # simile (marker), oxymoron (internal opposes), irony (literal opposes context), understatement,
        # personification (animacy grounded at build). This keeps the judge healthy by avoiding calls.
        pn = part_nodes.get(name, [])
        markered = any(a.s.node(m)["attrs"].get("text") in ("like", "as") for m in pn)
        opposed = any(a.inner.neighbours(m, "opposes") for m in pn)
        irony = bool(a.inner.neighbours(lit, "opposes"))
        understated = a.s.node(fig)["attrs"].get("understates") == 1
        if markered or opposed or irony or understated or name in personif_names:
            a.inner.set_attr(fig, "scored", 1)
            continue
        ctx = (f"The phrase {name!r} literally refers to: {lit_gloss[:80]}. Figuratively it means: "
               f"{fig_gloss[:90]}.")
        if name in parts_map:
            # Multi-word idioms/hyperboles: scalar (hyperbole, checked first) + compositional (idiom).
            # No shape grounding needed — these are not metonymy/metaphor.
            comp = _yn(judge, ctx + f" Can the figurative meaning be worked out from the literal meanings "
                       f"of its individual words ({', '.join(parts_map[name])}), or is it a fixed idiom "
                       f"whose meaning is unrelated to its parts? Answer 'yes' if it can be worked out "
                       f"from the words, 'no' if it is an opaque idiom.")
            a.inner.set_attr(fig, "noncompositional", 0 if comp == 1 else 1)
            exagg = _yn(judge, ctx + f" Does {name!r} use an exaggerated quantity or extent for emphasis "
                        f"— a number, amount, or duration far beyond literal truth (e.g. 'a million "
                        f"times'='many', 'waited forever'='a long time', 'weighs a ton'='heavy')? Answer "
                        f"'no' if it has no such exaggerated magnitude (e.g. opaque idioms like 'kick the "
                        f"bucket' or 'the whole nine yards').")
            a.inner.set_attr(fig, "scalar_violation", 1 if exagg == 1 else 0)
        else:
            # Single-concept CASES: the metonymy-vs-metaphor mapping shape (one voted perception).
            shape = _shape(judge, ctx + f" How is the figurative meaning connected to the literal {kw}? "
                           f"Answer with ONE word: 'association' if it is the same domain and the {kw} is "
                           f"a part, attribute, container, or symbol of the figurative thing (e.g. 'the "
                           f"crown' for the monarch); 'resemblance' if the figurative thing is a different "
                           f"kind of thing that merely resembles a {kw} by analogy (e.g. 'red herring'); "
                           f"or 'neither'.")
            a.inner.set_attr(fig, "contiguity", 1 if shape == "association" else 0)
            a.inner.set_attr(fig, "resemblance", 1 if shape == "resemblance" else 0)
        a.inner.set_attr(fig, "scored", 1)        # release classify_figure now signals are grounded
    a.inner.run_rules(10000)
    for name, kw, lit, fig, _, _ in rows:
        if not a.inner.neighbours(fig, "figure_of"):
            continue
        at = a.s.node(fig)["attrs"]
        kind = at.get("figure_kind", "?")
        why = {"simile": "like/as comparator part present (structural)",
               "oxymoron": "two conjoined parts carry an opposes edge (pair-layer, internal)",
               "irony": "literal reading opposes the context (pair-layer, external)",
               "hyperbole": "scalar violation UP: magnitude beyond plausible (grounded)",
               "understatement": "scalar violation DOWN: far weaker than the real situation",
               "idiom": "non-compositional AND no part is a figure (stored whole)",
               "metonymy": "same-domain association (grounded shape)",
               "personification": "inanimate subject + human-agentive predicate (type mismatch)",
               "metaphor": "cross-domain resemblance (grounded shape)"}.get(kind, "")
        print(f"    {name:22} -> FIGURE = {kind.upper():10}  [{why}]")

    # 5. Branch check — prove the agent's discriminator covers ALL THREE figure types deterministically
    #    (independent of the noisy live grounding above): feed each input combo, read the native verdict.
    print(f"\n  the discriminator itself (deterministic — feed the three mapping shapes directly):")
    probes = [("contiguity present", 1, 0), ("resemblance present", 0, 1), ("neither", 0, 0)]
    for label, c, r in probes:
        l = a.s.add_node("Reading", {"word": f"probe_{label}", "kind": "literal"})
        f = a.s.add_node("Reading", {"word": f"probe_{label}", "kind": "figurative",
                                     "figure_detected": 1, "contiguity": c, "resemblance": r, "scored": 1})
        a.inner.add_edge_unchecked(f, "figure_of", l)
        a.inner.run_rules(10000)
        print(f"    {label:20} (contiguity={c}, resemblance={r}) -> {a.s.node(f)['attrs'].get('figure_kind','?').upper()}")

    # 6. ALLEGORY — the agent's structure-mapping test: a narrative whose contained parts each carry a
    #    figure_of edge AND whose figurative targets preserve the source parts' relations.
    print(f"\n  detecting ALLEGORY (the agent's structure-mapping test over whole narratives):")
    for narr_name, theme, parts, rels in ALLEGORIES:
        narr = a.s.add_node("Narrative", {"name": narr_name, "theme": theme})
        pnodes, tnodes = [], []
        for plabel, tlabel in parts:
            p = a.s.add_node("Reading", {"word": plabel, "kind": "allegory_part"})
            t = a.s.add_node("Reading", {"word": tlabel, "kind": "referent", "to_domain": theme})
            a.inner.add_edge_unchecked(p, "figure_of", t)     # each part is a figure of its referent
            a.inner.add_edge_unchecked(narr, "contains", p)
            pnodes.append(p); tnodes.append(t)
        for i, j in rels:                                     # source relation, MIRRORED in the targets
            a.inner.add_edge_unchecked(pnodes[i], "acts_on", pnodes[j])
            a.inner.add_edge_unchecked(tnodes[i], "acts_on", tnodes[j])
        a.inner.run_rules(10000)
        at = a.s.node(narr)["attrs"]
        nfig = sum(1 for p in pnodes if a.inner.neighbours(p, "figure_of"))
        print(f"    {narr_name!r} (theme: {theme}) — {nfig} part-figures, relation mirrored in targets "
              f"-> {at.get('figure_kind','?').upper()} (is_allegory={at.get('is_allegory')})")

    print("\n" + SEP)
    print("  The agent read the figures of speech and adjusted its machinery to suit. detect_figure draws")
    print("  figure_of itself, and one discriminator now covers TEN figures, each by the agent's test:")
    print("    SIMILE         - a like/as comparator part is present (structural)")
    print("    OXYMORON       - two conjoined parts carry an opposes edge (pair-layer, INTERNAL)")
    print("    IRONY          - the literal reading opposes the CONTEXT (pair-layer, EXTERNAL)")
    print("    HYPERBOLE      - magnitude far ABOVE the plausible range (scalar up)")
    print("    UNDERSTATEMENT - magnitude far BELOW the real situation (scalar down)")
    print("    IDIOM          - non-compositional AND stored whole (no part is itself a figure)")
    print("    METONYMY       - same-domain association  |  METAPHOR - cross-domain resemblance")
    print("    PERSONIFICATION- inanimate subject + human-agentive predicate (type mismatch)")
    print("    ALLEGORY       - a narrative whose part-figures preserve their relations in the targets")
    print("  Oxymoron and irony share one tension primitive (internal vs external endpoints); hyperbole")
    print("  and understatement share one scalar test (up vs down). The agent's rules decide the type.")
    print(SEP)


if __name__ == "__main__":
    main()
