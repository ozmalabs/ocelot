"""Symbolic perception handlers — the figure judge's world-knowledge by LOOKUP, not an LLM oracle.

Each handler is registered under a tool name (`register_tool_handler`) so a graph Rule can ground a
figure perception with a native `UseTool` Term: the Term is graph-resident; its lookup body reuses the
on-disk corpus loader the rest of the agent already uses (`domains.dict_teacher._wordnet`). This is the
move the jabberwock chose in its plan — "replacing a guess with a lookup" — and it retires the
`claude -p` call from the figure path. Boundary I/O per CLAUDE.md: no decision lives in a handler; the
grounding decision is the Rule that reads the handler's value.

Three-valued by convention, since `UseTool` carries ints cleanly:
    1  = definite yes      0 = definite no       -1 = unknown (out of vocabulary) -> the rule ABSTAINS.
The grounding rule asserts a perception ONLY on +1; on 0/-1 it asserts nothing (abstain-don't-guess).
"""
from __future__ import annotations

_WN = None


def _wn():
    global _WN
    if _WN is None:
        from domains.dict_teacher import _wordnet
        _WN = _wordnet()
    return _WN


def _antonyms_direct(word):
    """Lemma-level antonyms across every synset of `word`."""
    wn = _wn()
    out = set()
    for syn in wn.synsets(word):
        for lem in syn.lemmas():
            for ant in lem.antonyms():
                out.add(ant.name().lower())
    return out


def _antonyms_indirect(word):
    """Adjective-antonym closure: `word`'s synset (or a similar_to head) carries an antonym; collect
    that antonym's whole satellite family. This is the standard WordNet route to lexicalised adjective
    opposition (the agent's 'property-hop'). It recovers general pairs (hot/cold, light/dark); it does
    NOT manufacture opposition where WordNet has none (bitter/sweet, deafening/silence) — those abstain."""
    wn = _wn()
    out = set()
    for sa in wn.synsets(word):
        for head in [sa] + list(sa.similar_tos()):
            for lem in head.lemmas():
                for ant in lem.antonyms():
                    fam = [ant.synset()] + list(ant.synset().similar_tos())
                    for s in fam:
                        for ll in s.lemmas():
                            out.add(ll.name().lower())
    return out


def wn_antonym(a, b):
    """+1 if a,b are WordNet antonyms (direct or via the adjective closure); 0 if both are in WordNet
    and no antonym link exists; -1 if either word is out of vocabulary (abstain). Same word -> 0
    (so a figure's self has_part pairs never fire an opposes edge)."""
    a = str(a).lower().strip()
    b = str(b).lower().strip()
    if not a or not b:
        return -1
    if a == b:
        return 0
    wn = _wn()
    if not wn.synsets(a) or not wn.synsets(b):
        return -1                                   # OOV -> abstain
    A = _antonyms_direct(a) | _antonyms_indirect(a)
    B = _antonyms_direct(b) | _antonyms_indirect(b)
    return 1 if (b in A or a in B) else 0


def wikt_antonym(a, b):
    """English Wiktionary opposition witness (curated, per-sense, trust 0.8). +1 if Wiktionary lists
    a,b as antonyms; 0 if both are en entries with no antonym link; -1 if either is out of vocabulary."""
    a = str(a).lower().strip()
    b = str(b).lower().strip()
    if not a or not b or a == b:
        return 0 if (a and b) else -1
    from domains.wiktionary_reference import wiktionary_antonym, wiktionary_has_en
    if wiktionary_antonym(a, b):
        return 1
    if wiktionary_has_en(a) and wiktionary_has_en(b):
        return 0
    return -1                                        # OOV -> abstain


def cn_antonym(a, b):
    """ConceptNet opposition witness (crowd-sourced, trust 0.4, corroborates only). +1 if the
    weight-filtered Antonym slab links a,b; 0 if both concepts are present with no Antonym edge;
    -1 if either is absent. Membership is boolean — the weight floor was applied at slab build."""
    a = str(a).lower().strip()
    b = str(b).lower().strip()
    if not a or not b or a == b:
        return 0 if (a and b) else -1
    from domains.conceptnet_reference import conceptnet_antonym, conceptnet_relations
    if conceptnet_antonym(a, b):
        return 1
    if conceptnet_relations(a) and conceptnet_relations(b):
        return 0
    return -1                                        # OOV -> abstain


# ---------------------------------------------------------------------------
# derive_opposes — the fourth witness: REASON opposition from definition + context when the
# lexicons are silent. Returns the trust CONTRIBUTION directly (0.8 HARD / 0.5 SOFT / 0.0 abstain),
# so the fused rule just adds it. Layers tried in order, first non-abstain wins (the agent's spec):
#   A: definitional negation/absence over a shared genus (near-deductive; resolves silence/deafening)
#   B: property-hop then antonym-test the properties via the lexicons (resolves polar-property pairs)
#   C: meaning-vector / semantic-tension contrast (STAGED — needs the meaning_vector faculty)
# ---------------------------------------------------------------------------
import re

# Negation/absence cues a gloss uses to assert the ABSENCE of a genus (Layer A).
_NEG_CUES = ("absence of", "lack of", "lacking", "without", "devoid of", "free of",
             "absence", "not ", "no ")
# Generic gloss scaffolding + function words that are never a discriminating genus.
_STOP = {
    "the", "a", "an", "of", "or", "and", "to", "in", "on", "as", "by", "for", "with", "that",
    "is", "are", "be", "being", "been", "when", "which", "who", "etc", "esp", "especially",
    "state", "quality", "person", "persons", "people", "thing", "things", "someone", "something",
    "able", "disposed", "having", "showing", "marked", "used", "make", "made", "render", "producing",
    "produced", "characterized", "category", "common", "characteristic", "kind", "nature", "way",
    "one", "any", "some", "such", "this", "these", "those", "their", "its", "from", "into", "than",
    "absence", "lack", "lacking", "without", "devoid", "free", "not", "no", "very", "great", "more",
}


def _wn_glosses(word, k=4):
    wn = _wn()
    return [s.definition() for s in wn.synsets(word)[:k]]


def _content_terms(gloss):
    """Discriminating content lemmas of a gloss (drop scaffolding/function words)."""
    return {t for t in re.findall(r"[a-z]+", (gloss or "").lower())
            if len(t) > 2 and t not in _STOP}


def _absented_terms(word, k=4):
    """Terms a word's glosses assert the ABSENCE of: the content word right after a negation cue
    (silence: 'the absence of sound' -> {'sound'}). Scans top-k senses (sense-1 alone misses it)."""
    out = set()
    for gloss in _wn_glosses(word, k):
        low = (gloss or "").lower()
        for cue in _NEG_CUES:
            i = low.find(cue)
            while i >= 0:
                for t in re.findall(r"[a-z]+", low[i + len(cue):]):
                    if len(t) > 2 and t not in _STOP:
                        out.add(t)
                        break
                i = low.find(cue, i + 1)
    return out


def _genus(word, hop=True, k=4):
    """The genus terms a word affirms: content lemmas of its glosses, optionally expanded by one
    property-hop (deafening -> 'loud' -> 'producing sound...' yields 'sound')."""
    g = set()
    for gloss in _wn_glosses(word, k):
        g |= _content_terms(gloss)
    if hop:
        for t in list(g)[:6]:
            for g2 in _wn_glosses(t, 1):
                g |= _content_terms(g2)
    return g


def _hop(word):
    """A word's core property: the first salient content lemma of its primary gloss
    (deafening -> 'loud')."""
    gls = _wn_glosses(word, 1)
    if not gls:
        return None
    terms = sorted(_content_terms(gls[0]))
    return terms[0] if terms else None


def _layer_a(a, b):
    """One gloss negates a genus the other affirms (shared, property-hop-expanded). Near-deductive."""
    for x, y in ((a, b), (b, a)):
        neg = _absented_terms(x)
        if neg and (neg & _genus(y, hop=True)):
            return True
    return False


def _layer_b(a, b):
    """Hop each word to its core property, then antonym-test the properties via the lexicons only.
    Returns 0.8 (HARD) / 0.5 (SOFT) / 0.0."""
    pa, pb = _hop(a), _hop(b)
    if not pa or not pb or pa == a or pb == b or pa == pb:
        return 0.0
    S = ((1.0 if wn_antonym(pa, pb) == 1 else 0.0)
         + (0.8 if wikt_antonym(pa, pb) == 1 else 0.0)
         + (0.4 if cn_antonym(pa, pb) == 1 else 0.0))
    if S >= 0.8:
        return 0.8
    if S >= 0.4:
        return 0.5
    return 0.0


_SWN = None


def _swn():
    global _SWN
    if _SWN is None:
        import nltk
        try:
            from nltk.corpus import sentiwordnet as swn
            swn.senti_synset("good.a.01")
        except LookupError:
            nltk.download("sentiwordnet", quiet=True)
            from nltk.corpus import sentiwordnet as swn
        _SWN = swn
    return _SWN


def _adj_valence(word):
    """Sense-aware valence over a word's ADJECTIVE senses (SentiWordNet pos-neg). Aggregating over
    adjective senses fixes the sense-1 trap (wn.synsets('kind')[0] is the NOUN 'category' -> 0.0)."""
    wn = _wn()
    swn = _swn()
    vs = []
    for s in wn.synsets(word, pos=wn.ADJ) + wn.synsets(word, pos=wn.ADJ_SAT):
        try:
            ss = swn.senti_synset(s.name())
            vs.append(ss.pos_score() - ss.neg_score())
        except Exception:
            pass
    return (sum(vs) / len(vs)) if vs else None


# Universal noun roots that do NOT discriminate a semantic field (every quality-noun reaches them).
_FIELD_ROOTS = {"entity.n.01", "abstraction.n.06", "attribute.n.02", "psychological_feature.n.01",
                "state.n.02", "cognition.n.01"}


def _dnoun_synsets(word):
    """The noun synsets a word's adjective senses derive to (cruel -> cruelty; kind -> kindness)."""
    wn = _wn()
    out = set()
    for s in wn.synsets(word, pos=wn.ADJ) + wn.synsets(word, pos=wn.ADJ_SAT):
        for l in s.lemmas():
            for d in l.derivationally_related_forms():
                if d.synset().pos() == "n":
                    out.add(d.synset())
    return out


def _same_field(a, b, depth=3):
    """True iff a,b's derivational attribute-nouns share a DISCRIMINATING hypernym within `depth`
    (cruelty/kindness both reach quality.n.01; deliciousness/ugliness diverge before it). This is the
    'same field' guard that stops Layer C firing on opposite-valence DIFFERENT-field pairs (delicious/ugly)."""
    def hyps(word):
        h = set()
        for syn in _dnoun_synsets(word):
            for path in syn.hypernym_paths():
                for n in path[-depth - 1:]:
                    h.add(n.name())
        return h
    return bool((hyps(a) & hyps(b)) - _FIELD_ROOTS)


def _layer_c(a, b):
    """Meaning contrast: same field AND flipped valence pole. Resolves pure-semantic opposition the
    lexicons and Layers A/B miss (cruel/kind). Never distance alone — requires the field guard."""
    va, vb = _adj_valence(a), _adj_valence(b)
    if va is None or vb is None:
        return 0.0
    if not _same_field(a, b):                         # different field -> abstain (no false positive)
        return 0.0
    margin = abs(va - vb)
    pole_flip = (va > 0.15 and vb < -0.15) or (va < -0.15 and vb > 0.15)
    if pole_flip and margin >= 0.8:
        return 0.8                                    # HARD
    if pole_flip and margin >= 0.4:
        return 0.5                                    # SOFT
    return 0.0


def derive_opposes(a, b):
    """Fourth witness: reason opposition from glosses when the lexicons are silent. Returns the trust
    contribution (0.8 HARD / 0.5 SOFT / 0.0 abstain). Abstain-don't-guess: no layer firing -> 0.0.
      A: definitional negation over a shared genus (deafening/silence)
      B: property-hop then lexical antonym on the properties
      C: meaning contrast — same field AND flipped valence pole (cruel/kind)"""
    try:
        a = str(a).lower().strip()
        b = str(b).lower().strip()
        if not a or not b or a == b:
            return 0.0
        if not _wn_glosses(a) or not _wn_glosses(b):
            return 0.0                                # no glosses to reason over -> abstain
        if _layer_a(a, b):                            # Layer A: HARD
            return 0.8
        sb = _layer_b(a, b)                           # Layer B: HARD/SOFT/abstain
        if sb:
            return sb
        return _layer_c(a, b)                         # Layer C: meaning contrast (valence + same field)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Animacy (Phase 2): personification = an INANIMATE SUBJECT performing an ANIMATE-AGENT action.
# wn_animate grounds the subject from the WordNet noun taxonomy; wn_verb_agentive grounds the verb
# from its lexname + selectional FRAMES ("Somebody ----s" vs "Something ----s"). Comprehension over
# the taxonomy, not a lookup. The grounding rule requires the inanimate noun to be the SUBJECT.
# ---------------------------------------------------------------------------

_ANIMATE_HYPERNYMS = {"living_thing.n.01", "organism.n.01", "person.n.01", "animal.n.01",
                      "causal_agent.n.01"}
_AGENT_VLEX = {"verb.communication", "verb.cognition", "verb.emotion", "verb.perception", "verb.social"}


def wn_animate(word):
    """+1 if the word's primary noun sense is animate (a living thing / person / animal / agent);
    0 if a clean inanimate noun; -1 if it has no noun sense (out of vocabulary)."""
    w = str(word).lower().strip()
    if not w:
        return -1
    wn = _wn()
    ns = wn.synsets(w, pos=wn.NOUN)
    if not ns:
        return -1
    s = ns[0]
    if s.lexname() in ("noun.person", "noun.animal", "noun.plant"):
        return 1
    hyper = {h.name() for path in s.hypernym_paths() for h in path}
    return 1 if (_ANIMATE_HYPERNYMS & hyper) else 0


def wn_verb_agentive(verb):
    """+1 if a verb's core sense takes an ANIMATE agent (lexname in the animate classes, OR its
    WordNet frames lean 'Somebody' over 'Something'); 0 if it leans inanimate; -1 if not a verb.
    The frame ratio separates 'knock'/'whisper' (agentive) from 'run'/'shine'/'fall' (ambiguous/
    inanimate) where the lexname alone (verb.contact) cannot."""
    w = str(verb).lower().strip()
    if not w:
        return -1
    wn = _wn()
    lemma = wn.morphy(w, wn.VERB) or w
    syns = wn.synsets(lemma, pos=wn.VERB)
    if not syns:
        return -1
    if any(s.lexname() in _AGENT_VLEX for s in syns[:3]):
        return 1
    sb = st = 0
    for s in syns[:5]:
        for l in s.lemmas():
            if l.name() == lemma:
                for f in l.frame_strings():
                    if f.startswith("Somebody"):
                        sb += 1
                    elif f.startswith("Something"):
                        st += 1
    if st == 0 and sb >= 1:
        return 1                                       # purely animate frames (whisper, weep)
    if sb >= 2 and sb >= 3 * st:
        return 1                                       # strong animate lean (knock 7:1)
    if st >= sb:
        return 0                                       # inanimate lean (shine, rust, fall)
    return -1


# ---------------------------------------------------------------------------
# Valence (Phase 3): irony = a literal phrase whose sincere valence OPPOSES the situation's valence.
# text_valence scores a phrase's sentiment SIGN from the curated Bing Liu opinion lexicon (no per-sense
# WSD noise — neutral topic nouns like 'weather'/'job' simply aren't in the lexicon). The ground_irony
# rule asserts opposes(literal_reading, context) when their valence signs are opposite.
# ---------------------------------------------------------------------------

_OPINION = None


def _opinion():
    global _OPINION
    if _OPINION is None:
        import nltk
        try:
            from nltk.corpus import opinion_lexicon
            opinion_lexicon.positive()
        except LookupError:
            nltk.download("opinion_lexicon", quiet=True)
            from nltk.corpus import opinion_lexicon
        _OPINION = (set(opinion_lexicon.positive()), set(opinion_lexicon.negative()))
    return _OPINION


def text_valence(text):
    """Sentiment SIGN of a phrase from the curated opinion lexicon: +1 net-positive, -1 net-negative,
    0 neutral. Sign (not raw count) so an opposite-valence pair multiplies to exactly -1."""
    pos, neg = _opinion()
    s = 0
    for t in re.findall(r"[a-z]+", str(text).lower()):
        if t in pos:
            s += 1
        elif t in neg:
            s -= 1
    return 1 if s > 0 else (-1 if s < 0 else 0)


# ---------------------------------------------------------------------------
# Shape (Phase 5): metaphor vs metonymy. The governing asymmetry — metonymy is a LINK with no shared
# property; metaphor is a SHARED PROPERTY across far domains with NO link. So find the link FIRST; only
# its absence licenses resemblance. The strongest link-finder is Wiktionary's OWN sense tags: a word's
# conventional metonymy is one Wiktionary records as a 'metonymically'/'figuratively'/'broadly' sense.
# ---------------------------------------------------------------------------

_CN_CONTIG = {"PartOf", "AtLocation", "UsedFor", "MadeOf", "SymbolOf", "HasA"}
_FIG_TAGS = {"metonymically", "figuratively", "broadly"}


def _head_noun(gloss):
    """First content noun in a figurative gloss ('the monarch, the monarchy...' -> 'monarch')."""
    wn = _wn()
    for t in re.findall(r"[a-z]+", str(gloss).lower()):
        if len(t) > 2 and t not in _STOP and wn.synsets(t, pos=wn.NOUN):
            return t
    return None


def _meronym_linked(a, b):
    """b is a part/member/substance (or holonym) of a, either direction (synecdoche)."""
    wn = _wn()

    def mero(w):
        out = set()
        for s in wn.synsets(w, pos=wn.NOUN):
            for rel in (s.part_meronyms(), s.member_meronyms(), s.substance_meronyms(),
                        s.part_holonyms(), s.member_holonyms(), s.substance_holonyms()):
                for x in rel:
                    for l in x.lemmas():
                        out.add(l.name().lower())
        return out
    return b in mero(a) or a in mero(b)


def _noun_related(a, b, depth=3):
    """True if two nouns share a non-root hypernym within `depth` (executive~boss~person related;
    detail~gunman not). The semantic match that beats bare lexical overlap (gloss 'boss' vs 'executive')."""
    wn = _wn()
    if not a or not b:
        return False
    a = wn.morphy(a, wn.NOUN) or a
    b = wn.morphy(b, wn.NOUN) or b
    if a == b:
        return True
    sa, sb = wn.synsets(a, pos=wn.NOUN), wn.synsets(b, pos=wn.NOUN)
    if not sa or not sb:
        return False

    def hyps(s):
        return {n.name() for path in s.hypernym_paths() for n in path[-depth - 1:]}
    overlap = hyps(sa[0]) & hyps(sb[0])
    return bool(overlap - {"entity.n.01", "abstraction.n.06", "physical_entity.n.01"})


def wikt_metonymic(literal, fig_gloss):
    """+1 if the literal word has a conventional metonymic/figurative Wiktionary sense whose target
    MATCHES the figurative meaning (the sense's gloss head is lexically or semantically related to the
    figurative head — so suit->'boss' matches 'executive', but gun->'gunman' does NOT match 'planted
    detail'); 0 if it has English entries but no matching sense; -1 if out of vocabulary."""
    from domains.wiktionary_reference import wiktionary_fig_senses, wiktionary_has_en
    lit = str(literal).lower().strip()
    fg_terms = _content_terms(str(fig_gloss))
    fg_head = _head_noun(fig_gloss)
    for tags, gloss in wiktionary_fig_senses(lit):
        if not (_FIG_TAGS & tags):
            continue
        g_terms = _content_terms(gloss)
        if g_terms & fg_terms:                                # lexical overlap (crown->'monarchy')
            return 1
        if "metonymically" in tags and any(
                _noun_related(fn, gn) for fn in fg_terms for gn in g_terms):
            return 1                                          # strong tag + semantic target match (executives->boss)
    return 0 if wiktionary_has_en(lit) else -1


def cn_contiguity(literal, fig_gloss):
    """+1 if a DIRECT contiguity link connects the literal and the figurative head: a whitelisted
    ConceptNet relation (PartOf/AtLocation/UsedFor/MadeOf/SymbolOf/HasA) or WordNet meronymy. 0 if both
    known and no link; -1 if the head can't be resolved."""
    from domains.conceptnet_reference import conceptnet_relations
    lit = str(literal).lower().strip()
    head = _head_noun(fig_gloss)
    if not head:
        return -1
    for a, b in ((lit, head), (head, lit)):
        for r, t in conceptnet_relations(a):
            if r in _CN_CONTIG and (t == b or b in t.split()):
                return 1
    return 1 if _meronym_linked(lit, head) else 0


def shape_cross_domain(literal, fig_gloss):
    """+1 if the literal and the figurative head are in DIFFERENT WordNet noun domains (different lexname,
    or no shared non-root hypernym); 0 if the same domain; -1 if either is OOV. The resemblance guard:
    a metaphor crosses domains, a same-domain figurative is more likely metonymy/literal."""
    wn = _wn()
    lit = str(literal).lower().strip()
    head = _head_noun(fig_gloss)
    if not head:
        return -1
    la = wn.synsets(lit, pos=wn.NOUN)
    lb = wn.synsets(head, pos=wn.NOUN)
    if not la or not lb:
        return -1
    if la[0].lexname() != lb[0].lexname():
        return 1
    ha = {h.name() for p in la[0].hypernym_paths() for h in p}
    hb = {h.name() for p in lb[0].hypernym_paths() for h in p}
    return 0 if ((ha & hb) - {"entity.n.01", "abstraction.n.06"}) else 1


# ---------------------------------------------------------------------------
# Magnitude (Phase 4): hyperbole / understatement / sarcasm-spike. Curated magnitude/intensity lexicons
# (small, principled — no WSD). scalar_violation = a magnitude far beyond the literal (hyperbole);
# understates = a minimizer over a severe reality (understatement/litotes); scalar_spike = an over-the-top
# intensifier (with the irony opposes edge -> sarcasm).
# ---------------------------------------------------------------------------

_EXTREME = {
    "million", "millions", "billion", "billions", "trillion", "zillion", "gazillion", "bazillion",
    "ton", "tons", "forever", "eternity", "infinite", "infinity", "endless", "endlessly", "countless",
    "thousand", "thousands", "hundred", "dozens", "ages", "dying", "starving", "starved", "freezing",
    "boiling", "everything", "nothing", "always", "never",
}
_MINIMIZER = {
    "just", "merely", "only", "slightly", "bit", "touch", "somewhat", "mere", "tad", "hardly",
    "barely", "little", "scratch", "not",
}
# strong positive intensifiers — the over-the-top marker that turns irony into sarcasm. Deliberately
# NOT the mild evaluatives (lovely / great / nice) so plain irony stays irony.
_SPIKE = {
    "wonderful", "fantastic", "marvelous", "marvellous", "fabulous", "spectacular", "brilliant",
    "magnificent", "splendid", "superb", "perfect", "stupendous", "phenomenal", "tremendous",
}
_SEVERE = _EXTREME | {
    "severe", "severely", "deep", "deeply", "threatening", "fatal", "lethal", "excellent",
    "outstanding", "terrible", "brutal", "bitterly", "extreme", "extremely", "devastating",
    "catastrophic", "disaster", "awful", "horrible", "freezing", "scorching", "agony", "agonizing",
    "exceptional", "superb", "magnificent", "appalling", "dreadful", "grave", "critical",
}


def wikt_idiomatic(phrase):
    """1 if the phrase has a Wiktionary sense tagged 'idiomatic' — a fixed, noncompositional multi-word
    phrase (kick the bucket, bite the bullet). The idiom signal, curated, no LLM."""
    from domains.wiktionary_reference import wiktionary_fig_senses
    for tags, _gloss in wiktionary_fig_senses(str(phrase).lower().strip()):
        if "idiomatic" in tags:
            return 1
    return 0


def is_extreme(word):
    """1 if the word is an extreme/hyperbolic magnitude term (million / ton / forever)."""
    return 1 if str(word).lower().strip() in _EXTREME else 0


def is_minimizer(word):
    """1 if the word minimizes (just / a bit / merely / not) — the understatement/litotes marker."""
    return 1 if str(word).lower().strip() in _MINIMIZER else 0


def is_intensifier_spike(word):
    """1 if the word is an over-the-top positive intensifier (wonderful / fantastic) — the sarcasm marker."""
    return 1 if str(word).lower().strip() in _SPIKE else 0


def text_severe(text):
    """1 if a phrase contains a severe/extreme term — the reality an understatement downplays."""
    toks = set(re.findall(r"[a-z]+", str(text).lower()))
    return 1 if (toks & _SEVERE) else 0


# tool-name -> handler. Registered once at boot; the native UseTool dispatch looks them up by name.
HANDLERS = {
    "wn_antonym": wn_antonym,
    "wikt_antonym": wikt_antonym,
    "cn_antonym": cn_antonym,
    "derive_opposes": derive_opposes,
    "wn_animate": wn_animate,
    "wn_verb_agentive": wn_verb_agentive,
    "text_valence": text_valence,
    "wikt_metonymic": wikt_metonymic,
    "cn_contiguity": cn_contiguity,
    "shape_cross_domain": shape_cross_domain,
    "wikt_idiomatic": wikt_idiomatic,
    "is_extreme": is_extreme,
    "is_minimizer": is_minimizer,
    "is_intensifier_spike": is_intensifier_spike,
    "text_severe": text_severe,
}


def register_symbolic_handlers(native):
    """Register every symbolic-perception handler on the native substrate module (idempotent)."""
    for name, fn in HANDLERS.items():
        native.register_tool_handler(name, fn)
    return sorted(HANDLERS)
