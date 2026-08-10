#!/usr/bin/env python3
"""hle_nonmath_source_certify — FIRST non-math HLE measurement of the agent's
generalizable spine: RECOGNIZE the asked thing -> READ-FROM-SOURCE -> CERTIFY (or
honest MISS). UNASSISTED, key read at END ONLY, ZERO false positives the invariant.

WHY THIS SCRIPT EXISTS (the assessment, executed). The committed system scores 19 on
the HLE MATH slice from a domain-AGNOSTIC spine: recognize -> formalize -> reason/
retrieve/compute -> CERTIFY. The full HLE is 2370 text-only questions across 8
categories (Math 1061 + Bio/Med 244 + CS/AI 243 + Physics 226 + Humanities 210 +
Other 200 + Chem 108 + Eng 78). 1309 of those are NON-MATH — and the biggest breadth
lever for them is READ-FROM-SOURCE: most non-math HLE is knowledge/reasoning answerable
by reading the right source + reasoning, not by a held compute. This script points the
read-from-source + certify spine at the NON-MATH set and takes the first honest number.

TWO MEASUREMENTS, both UNASSISTED:

  (1) FLOOR — the CURRENT committed math spine (route_invariant_question +
      comprehend_asked_invariant) over the non-math set. Expected ~0 typed/numbered:
      the spine's recognizers are math-invariant-shaped (euler char, free-rank, group
      forms), so this confirms the honest floor + that nothing math-specific leaks a
      false positive onto a non-math stem.

  (2) GENERAL READ-FROM-SOURCE CERTIFIED MC ANSWERER — a domain-AGNOSTIC procedure,
      the SAME on every subject, for the multiple-choice non-math questions (the
      cleanest certifiable entry point: a single-letter key, options embedded in the
      stem). For each question:
        a. RECOGNIZE  : parse the embedded option block (A./B./... -> text); WIDENED
                        entity recognition (entity_candidates) — a RANKED list of named
                        entities for ARBITRARY subjects: quoted terms, possessives,
                        capitalised multiword proper nouns (sentence-initial noise
                        stripped), single proper nouns. Not just math possessives.
        b. READ-SOURCE: resolve the FIRST candidate that maps to a real (non-
                        disambiguation) article via the HELD local-wiki reader
                        (wiki_local.summary) — the agent's breadth engine. Returns the
                        article's LEAD (the entity's DEFINITION).
        c. CERTIFY    : the SOUND certificate. An option is certified ONLY when (i) the
                        stem is DEFINITIONAL (what-is / which-best-describes — the only
                        shape an encyclopedia lead can ENTAIL), (ii) the option's full
                        DISTINCTIVE multiword phrase is stated VERBATIM in the entity's
                        DEFINITION (lead), and (iii) it is the UNIQUE such option. Else
                        honest MISS. SOUNDNESS LESSON (measured): an earlier draft also
                        accepted a BODY sentence that co-located the option phrase with a
                        question focus word — it fired 9/9 FALSE POSITIVE (HLE answers
                        are NOT verbatim article spans, so body co-location is
                        coincidence, not entailment; the Tzotzil article's "true
                        language" matched the wrong option). The fix (fix-the-fixer):
                        restrict entailment to the source's OWN definitional predication
                        (the lead), the only span that genuinely ASSIGNS a property. This
                        fires 0 on the adversarial HLE set (answers are never the entity's
                        textbook definition) — the honest, sound MISS.

  The key (the letter) is read at END ONLY, purely to score CORRECT / FALSE-POSITIVE.
  Never fed into recognize / read / certify. No per-QID branch, no answer baking, no
  reverse-engineering. A wrong certified letter is a FALSE POSITIVE and is reported as
  such — the discipline forbids it, the count proves it.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER shell. It SEQUENCES held faculties (wiki_local
reader, certify guard) + TALLIES. It makes NO math/domain decision of its own beyond
the mechanical lexical certificate; holds NO agent state; runs NO rule engine, no LLM,
no Rust. Whether a letter comes back depends on what the SOURCE contains — an honest
MISS when the source does not uniquely support one option.
"""
from __future__ import annotations
import json, os, re, sys
from collections import Counter
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from domains import wiki_local as _wl
from domains import certify as _certify

SEP = "=" * 80
DATA = os.path.join(ROOT, "data", "hle_nonmath.json")

# light stop list for option-phrase distinctiveness; mechanical, domain-neutral.
_STOP = set("the a an of to in on for and or is are be by with as at from that this "
            "which an no not all both each any some it its their his her they these "
            "those can could would should must may might will".split())


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


# ----------------------------------------------------------------------------
# RECOGNIZE — parse the embedded option block + the stem's named entity.
# ----------------------------------------------------------------------------

def parse_options(stem: str) -> dict[str, str]:
    """Read the embedded 'A. ... B. ...' option block into {letter: text}. Mechanical
    surface->structure; the options are the question's OWN literal givens."""
    # cut to the answer-choices region if present (keeps the stem out of options).
    m = re.search(r"Answer Choices:?", stem)
    region = stem[m.end():] if m else stem
    opts: dict[str, str] = {}
    # match 'A. text' / 'A) text' up to the next 'X.'/'X)' or end.
    for mm in re.finditer(r"(?m)^\s*([A-Z])[\.\)]\s+(.*?)(?=\n\s*[A-Z][\.\)]\s|\Z)",
                          region, re.S):
        letter, text = mm.group(1), " ".join(mm.group(2).split())
        if text:
            opts[letter] = text
    return opts


# Sentence-initial / interrogative caps words that are NOT entities — they only
# look capitalised because they start a sentence or are function words. A leading
# run of these is stripped off a candidate (so "Since Gaussian" -> "Gaussian",
# "In Quantum Computing" -> "Quantum Computing"). Mechanical, domain-neutral.
_CAP_NOISE = set(
    "The This That These Those Which What When Where Who Whom Whose Why How A An "
    "In On For And Or But If Let Consider Given Suppose Question Answer Choices "
    "Other Both Each Since Imagine Assume Define Note Here There We You I It Is "
    "Are Was Were Be Do Does Did Can Could Would Should Must May Might Will Now "
    "Then Thus Hence So As At By Of To From With Without Using Below Above".split())


def entity_candidates(stem: str) -> list[str]:
    """WIDENED entity recognition: produce a RANKED list of candidate named entities
    the question may be ABOUT — for arbitrary subjects, not just math possessives.
    General, surface-driven, no per-QID. Ranked most-distinctive first so the source
    resolver tries the strongest anchor before a generic fallback:

      1. QUOTED technical terms  ('"Lalazai"', 'the "Mayer-Vietoris sequence"').
      2. POSSESSIVE proper terms ("Watterson's estimator", "Chaucer's").
      3. CAPITALISED multiword proper nouns (2-4 caps words; leading sentence-initial
         / interrogative noise words stripped — 'In Quantum Computing' -> 'Quantum
         Computing').
      4. SINGLE capitalised proper noun (>=4 letters, not a function/interrogative word).

    Each is a SURFACE read of the stem's own givens (the permitted thin boundary
    detector, CLAUDE.md) — no meaning decision, no key. The resolver then keeps the
    first that maps to a real article; if none do, the honest 'nothing to look up'.
    """
    head = stem.split("Answer Choices")[0]
    cands: list[str] = []

    def _strip_noise(phrase: str) -> str:
        ws = phrase.split()
        while ws and ws[0] in _CAP_NOISE:
            ws = ws[1:]
        return " ".join(ws)

    # 1. quoted terms — the question's own emphasised technical names.
    for m in re.findall(r"[\"“]([^\"”\n]{3,40})[\"”]", head):
        m = m.strip()
        if m and m[0].isalpha():
            cands.append(m)
    # 2. possessive proper terms: "Xxx's <kind>" and the bare proper name "Xxx".
    for full, kind in re.findall(
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})'s\s+"
            r"(?:[a-z][a-zA-Z ]*?)?\b(theorem|estimator|law|principle|effect|"
            r"equation|model|paradox|conjecture|distribution|process|criterion|"
            r"condition|sequence|notation|algorithm|transform|number)", head):
        cands.append(f"{full}'s {kind}")
    for m in re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})'s\b", head):
        cands.append(m)
    # 3. capitalised multiword proper nouns (strip leading sentence/interrogative noise).
    for m in re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})\b", head):
        m2 = _strip_noise(m)
        if len(m2.split()) >= 2:
            cands.append(m2)
    # 4. single capitalised proper noun, not a function/interrogative word.
    for m in re.findall(r"\b([A-Z][a-z]{3,})\b", head):
        if m not in _CAP_NOISE:
            cands.append(m)

    # dedup preserving order; prefer longer/multiword anchors first within their tier.
    seen: set[str] = set()
    out: list[str] = []
    for c in cands:
        k = c.lower()
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


# ----------------------------------------------------------------------------
# READ-FROM-SOURCE — the held local-wiki reader, keyed on the stem entity.
# ----------------------------------------------------------------------------

def _summary_for(entity: str):
    """The held wiki summary for an entity, trying simple surface variants. Returns the
    summary dict (with title/text/extract) or None. A DISAMBIGUATION lead is rejected
    (it is a list of senses, not the article — a near-miss that would poison the read)."""
    if not _wl.present():
        return None
    tries = [entity]
    if "'s " in entity:
        tries.append(entity.replace("'s ", " "))     # "Watterson estimator"
        tries.append(entity.split("'s ")[-1])         # the kind noun alone
    for t in tries:
        s = _wl.summary(t)
        if s and not _wl.is_disambiguation(s.get("extract", "")):
            return s
    return None


def resolve_source(stem: str):
    """WIDENED read-source: walk the ranked entity candidates and return the FIRST that
    maps to a real (non-disambiguation) article — (resolved_title, lowercased_lead), or
    (None, None) on a clean miss. The same held reader for every subject; no per-QID.

    Returns the LEAD (the entity's definition), which is the only span an encyclopedia
    genuinely ENTAILS (see _option_in_definition for why the body is not sound)."""
    for ent in entity_candidates(stem):
        s = _summary_for(ent)
        if s is None:
            continue
        lead = (s.get("extract") or "").strip()
        if not lead:
            lead = (s.get("text") or "").strip()[:600]
        if lead:
            return s.get("title") or ent, lead.lower()
    return None, None


# ----------------------------------------------------------------------------
# CERTIFY — the hard, mechanical, zero-FP source check.
# ----------------------------------------------------------------------------

def _phrase_terms(text: str) -> list[str]:
    """Distinctive content terms of a phrase (lowercased, stopworded). The mechanical
    'what words carry the meaning' read used for both the option and the stem focus."""
    toks = re.findall(r"[a-zA-Z][a-zA-Z\-]+", text.lower())
    return [t for t in toks if t not in _STOP and len(t) > 2]


# A question is DEFINITIONAL when its stem asks "what IS / which best DESCRIBES" the
# entity — the only shape an encyclopedia LEAD can genuinely entail (the lead defines the
# entity; if one option restates that definition verbatim, the source assigns it).
_DEFINITIONAL = re.compile(
    r"\bwhat (?:is|are|does|was|were)\b"
    r"|\bwhich .{0,40}?\b(?:is the|best (?:describes|defines|fits|captures))\b"
    r"|\bdefinition of\b|\bdefined as\b",
    re.IGNORECASE)


def is_definitional(stem_head: str) -> bool:
    return bool(_DEFINITIONAL.search(stem_head))


def _option_in_definition(opt_text: str, lead: str, stem_terms: set) -> bool:
    """SOUND per-option entailment, restricted to the ONE place an encyclopedia genuinely
    ENTAILS an answer: the entity's DEFINITION (its lead). True iff the option's full
    distinctive phrase is STATED VERBATIM in the lead sentence(s) — else False.

    WHY THIS IS THE ONLY SOUND LEXICAL CERTIFICATE (the lesson of the unsound run). An
    earlier draft accepted a body sentence that merely CO-LOCATED the option phrase with a
    question focus word. Measured against the keys that fired 9/9 FALSE POSITIVE: HLE MC
    answers are NOT verbatim spans of the entity's article, so any body co-location is
    COINCIDENCE, not entailment (the Tzotzil article says bats'i k'op means 'true language'
    -> wrong option F fired on the fragment). Co-location is necessary, never sufficient.
    The lead is different in KIND: it is the source's own definitional predication of the
    entity, so a verbatim option there is the source ASSIGNING that property. Guards that
    keep a wrong option from passing:
      (a) DISTINCTIVE multiword phrase (>=2 content terms the STEM does not already use) —
          rejects single common words ('France') and tautological stem-echo options.
      (b) the FULL normalised option phrase verbatim in the LEAD (not a scattered bigram in
          the body) — the source must STATE the option as the entity's definition.
    Empirically (verified on all 463 MC): this fires ZERO times — HLE answers are never the
    entity's textbook definition. So the certificate correctly MISSES the whole adversarial
    set; it would fire ONLY on a genuine 'define X' lookup, soundly, were one present."""
    terms = _phrase_terms(opt_text)
    distinctive = [t for t in terms if t not in stem_terms]
    if len(distinctive) < 2:
        return False
    norm = " ".join(opt_text.lower().split())
    return len(norm) >= 8 and norm in lead


@dataclass
class Result:
    qid: str
    entity: Optional[str] = None
    source_read: bool = False
    certified_letter: Optional[str] = None
    link: str = ""          # named link reached (recognize / read / certify / miss)
    detail: str = ""


def certify_mc(qid: str, stem: str) -> Result:
    """The full general procedure: recognize -> read-source -> SOUND certify-or-MISS."""
    r = Result(qid=qid)
    opts = parse_options(stem)
    if len(opts) < 2:
        r.link = "recognize_no_options"
        r.detail = "no embedded option block parsed"
        return r
    ents = entity_candidates(stem)
    if not ents:
        r.link = "recognize_no_entity"
        r.detail = "no named entity / technical term in stem to look up"
        return r
    title, lead = resolve_source(stem)
    r.entity = title or (ents[0] if ents else None)
    if not lead:
        r.link = "read_source_miss"
        r.detail = f"source reader resolved no article for any candidate {ents[:4]!r}"
        return r
    r.source_read = True
    stem_head = stem.split("Answer Choices")[0]
    # SOUNDNESS GATE 1: only a DEFINITIONAL question can be entailed by an encyclopedia
    # lead. A non-definitional stem (translate / compute / which-violates / strategy)
    # MISSES here regardless of any lexical match — the lead cannot answer it.
    if not is_definitional(stem_head):
        r.link = "certify_miss"
        r.detail = ("non-definitional stem -> the entity's definition cannot entail an "
                    "answer; honest MISS (lexical body match is coincidence, not entailment)")
        return r
    stem_terms = set(_phrase_terms(stem_head))
    # which options does the entity's DEFINITION (lead) STATE verbatim, distinctively?
    supported = [L for L, t in opts.items()
                 if _option_in_definition(t, lead, stem_terms)]
    # CERTIFY: exactly one option is verbatim in the definition, all others absent.
    out = type("O", (), {"detail": ""})()
    checks = [
        _certify.Check("exactly_one_option_in_definition", len(supported), 1),
        _certify.Check("supported_option_is_unique", sorted(supported),
                       supported[:1], ok=(len(supported) == 1)),
    ]
    failed = _certify.guard(out, f"mc-source[{qid}]", checks)
    if failed is not None:
        r.link = "certify_miss"
        r.detail = (f"{out.detail}  (supported={supported}; the entity's definition does "
                    f"not uniquely state one option -> honest MISS)")
        return r
    L = supported[0]
    r.certified_letter = L
    r.link = "certified"
    r.detail = f"the entity's definition (lead) states option {L!r} verbatim + uniquely"
    return r


# ----------------------------------------------------------------------------
# FLOOR — run the committed math spine over non-math (confirm ~0 + no leak).
# ----------------------------------------------------------------------------

def floor_math_spine(data) -> dict:
    from domains import presupposition_derivation as _pd
    from domains import route_invariant_question as _riq
    typed = numbered = 0
    for q in data:
        try:
            asked = _pd.comprehend_asked_invariant(q["question"])
            if asked.typed is not None:
                typed += 1
        except Exception:
            pass
        try:
            r = _riq.route_question(q["id"], q["question"])
            if r.value is not None:
                numbered += 1
        except Exception:
            pass
    return {"typed": typed, "numbered": numbered, "n": len(data)}


def main():
    data = json.load(open(DATA))
    mc = [q for q in data if q["answer_type"] == "multipleChoice"]
    n = len(data)

    banner(f"NON-MATH HLE — first measurement (N={n} non-math text-only; "
           f"{len(mc)} multipleChoice). UNASSISTED; key read END ONLY.")

    # (1) FLOOR — committed math spine over non-math.
    banner("(1) FLOOR — the committed MATH spine over the NON-MATH set")
    fl = floor_math_spine(data)
    print(f"  committed-math-spine TYPED  : {fl['typed']} / {fl['n']}")
    print(f"  committed-math-spine NUMBERED: {fl['numbered']} / {fl['n']}")
    print(f"  (expected ~0 — the spine's recognizers are math-invariant-shaped; this "
          f"confirms the honest floor + that no math faculty leaks a non-math FP)")

    # (2) GENERAL read-from-source certified MC answerer.
    banner("(2) GENERAL read-from-source CERTIFIED MC answerer over non-math MC")
    link_buckets = Counter()
    certified = []     # (qid, letter, category)
    cat_of = {q["id"]: q["category"] for q in data}
    key_of = {q["id"]: str(q["answer"]).strip() for q in data}
    for q in mc:
        r = certify_mc(q["id"], q["question"])
        link_buckets[r.link] += 1
        if r.certified_letter is not None:
            certified.append((q["id"], r.certified_letter, cat_of[q["id"]], r.detail))

    # SCORE — key read END ONLY.
    correct = fp = 0
    rows = []
    for qid, letter, cat, detail in certified:
        key = key_of[qid]
        ok = (re.fullmatch(r"[A-Z]", letter) is not None and letter == key)
        if ok:
            correct += 1
        else:
            fp += 1
        rows.append((qid, cat, letter, key, ok, detail))

    print(f"  MC questions attempted     : {len(mc)}")
    print(f"  per-LINK reach (where each MC question stopped):")
    for bk, c in sorted(link_buckets.items(), key=lambda kv: -kv[1]):
        print(f"    {bk:24s} {c}")
    print()
    print(f"  CERTIFIED (reached a letter): {len(certified)}")
    print(f"  CERTIFIED-CORRECT           : {correct}")
    print(f"  FALSE POSITIVES             : {fp}   "
          f"(MUST be 0 — certify-or-MISS discipline)")

    if rows:
        banner("CERTIFIED answers (per question, key scored END only)")
        for qid, cat, letter, key, ok, detail in rows:
            tag = "CORRECT" if ok else "*** FALSE POSITIVE ***"
            print(f"  {qid}  [{cat}]  -> {letter}  (key {key})  {tag}")
            print(f"      {detail}")

    # (3) ADVERSARIAL SOUNDNESS ASSAY — GENERAL (no per-QID, no key). Find the MC
    # questions where the resolved source MENTIONS the distinctive words of >=2 DIFFERENT
    # options (the near-miss family: the article touches multiple options, the wrong
    # option's word is present). A SOUND certificate must MISS these — co-occurrence of
    # option words is not entailment. We confirm the certificate certifies NONE of them.
    banner("(3) ADVERSARIAL SOUNDNESS ASSAY — questions whose source mentions >=2 options")
    adversarial = []
    for q in mc:
        title, lead = resolve_source(q["question"])
        if not lead:
            continue
        opts = parse_options(q["question"])
        stem_terms = set(_phrase_terms(q["question"].split("Answer Choices")[0]))
        # an option is 'mentioned' if any distinctive (non-stem) content word is in source.
        mentioned = 0
        for t in opts.values():
            dist = [w for w in _phrase_terms(t) if w not in stem_terms and len(w) > 3]
            if any(w in lead for w in dist):
                mentioned += 1
        if mentioned >= 2:
            adversarial.append(q["id"])
    leaked = []
    for qid in adversarial:
        q = next(qq for qq in mc if qq["id"] == qid)
        r = certify_mc(qid, q["question"])
        if r.certified_letter is not None:
            leaked.append(qid)
    print(f"  near-miss questions (source mentions >=2 options' words): {len(adversarial)}")
    print(f"  of those, CERTIFIED by the certificate (must be 0)       : {len(leaked)}")
    print(f"  adversarial soundness: {'HELD — all near-misses MISS' if not leaked else 'VIOLATED'}")
    if leaked:
        print(f"  LEAKED: {leaked}")

    # (4) exactMatch REACH — does the read-source-certify spine APPLY to free-form answers?
    banner("(4) exactMatch — read-source-certify reach (no sound free-form certificate yet)")
    em = [q for q in data if q["answer_type"] == "exactMatch"]
    em_read = sum(1 for q in em if resolve_source(q["question"])[1])
    em_def = sum(1 for q in em
                 if resolve_source(q["question"])[1]
                 and is_definitional(q["question"].split("Answer Choices")[0]))
    print(f"  exactMatch non-math questions          : {len(em)}")
    print(f"  ...entity resolves to a source article : {em_read}")
    print(f"  ...and the stem is definitional        : {em_def}")
    print(f"  CERTIFIED exactMatch                   : 0   (no options to SELECT among; a")
    print(f"    sound exactMatch needs CONSTRUCT-then-certify — GENERATE the answer string +")
    print(f"    verify, a larger capability than read-source-SELECT; read-source-select does")
    print(f"    not apply. FALSE POSITIVES: 0 — nothing is emitted, so none can be wrong.)")

    banner("SUMMARY LINE — non-math")
    print(f"  FLOOR (committed math spine): TYPED {fl['typed']} / NUMBERED "
          f"{fl['numbered']}  over {n} non-math")
    print(f"  GENERAL read-source MC      : CERTIFIED {len(certified)} / "
          f"CORRECT {correct} / FALSE-POSITIVE {fp}  over {len(mc)} MC")
    print(f"  ADVERSARIAL near-misses     : {len(adversarial)} (source touches >=2 options) "
          f"-> {len(leaked)} leaked (must be 0)")
    print(f"  exactMatch                  : {len(em)} Qs; {em_read} resolve a source; "
          f"CERTIFIED 0 (read-source-SELECT does not apply to free-form)")
    print(f"  zero-false-positive invariant: "
          f"{'HELD' if (fp == 0 and not leaked) else 'VIOLATED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
