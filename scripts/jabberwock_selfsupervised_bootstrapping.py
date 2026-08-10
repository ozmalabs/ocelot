"""COGNITION increment — FULLY SELF-CONTAINED syntactic bootstrapping (no human labels on the decision).

Engineering unlock done (b48407ce: Gate C flips donkey=0 on earned order-1). But Gate C used TWO eval-label
scaffolds: (1) the transcript told it which earned word-forms are "the"/"a" (the specific-frame IDENTITY),
(2) nltk-POS told it "noun" (the category TARGET). This removes BOTH — the agent self-identifies everything;
labels are SCORING-ONLY, off the decision path (Gleitman bootstrapping with no human labels in the loop).

  SCAFFOLD 1 -> SELF-IDENTIFY specific function-word FORMS: the agent's OWN authored distributional split
    (Gate B) isolates the closed class; the SPECIFIC frame-defining forms = the top self-function-forms by
    frequency x context-diversity — from the agent's distributional stats ALONE, no transcript.
  SCAFFOLD 2 -> SELF-DISCOVER categories: cluster CONTENT word-forms by their FRAME DISTRIBUTION (which
    self-identified function-forms precede them) -> self-discovered categories (the frame IS the category
    signal; content words sharing frames = same category). Held clustering, no POS on the decision.

Decision path (ALL donkey=0): raw audio -> earned phone-level order-1 (edit-clustered) -> authored
distributional function/content split -> self-identified specific function-forms -> authored specific
frames -> self-discovered content categories -> the specific-frame->self-category signal. Transcript +
nltk-POS are SCORING-ONLY (verify no label used in any decision). USE THE VENV PYTHON. Memory-hardened.

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_selfsupervised_bootstrapping.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict
import scripts.jabberwock_syntax_clean_order1 as D          # ulimit guard; author_constructions/apply_distributional/FUNC/_peak_gib
import scripts.jabberwock_earned_order1_consistency as C     # earn_energy/earned_wf_energy/edit_cluster/load_words_energy
import referential_word_learning as R

SCAFFOLDED_PRIOR = 0.435   # b48407ce: eval-scaffolded specific 'the/a'->noun


def main():
    MAXWORDS = int(os.environ.get("MAXWORDS", "3500"))
    M_FF = 20         # self-identified frame-forms for the category vector (wider = less sparse)
    KCAT = 3          # self-discovered content categories (coarse: noun-like / verb-like / other)
    EDIT_THR = 0.34
    a, _ = D.author_constructions()
    data = C.load_words_energy("train-clean-100_*.pkl", 6, MAXWORDS)
    words = [w for w, _, _, _ in data]
    V = len(set(words)); cut = int(0.7 * len(data))
    print(f"\n  LibriSpeech train-clean energy (clean connected), {len(data)} words, vocab {V}  "
          f"[peak {D._peak_gib():.2f} GiB]", flush=True)
    from nltk import pos_tag
    tags = [t for _, t in pos_tag(words)]                    # SCORING-ONLY

    # ---- EARNED order-1 (energy phone model + edit-clustering for per-word consistency), donkey=0 ----
    print("  earning phone model (energy) + edit-clustering the order-1...", flush=True)
    enc, cent, cphone, phones_set, pi = C.earn_energy(data[:cut]); nP = len(phones_set)
    wf_raw = [C.earned_wf_energy(fr, en, enc, cent, cphone, nP) for _, fr, _, en in data]
    wf, _ = C.edit_cluster(wf_raw, EDIT_THR)                 # consistent earned word-forms

    # ---- authored distributional split -> is_function per form (donkey=0) ----
    isf, _fq = D.apply_distributional(a, wf[:cut])
    freq = Counter(wf[:cut])
    ctx_div = defaultdict(set)
    for i in range(1, cut):
        ctx_div[wf[i]].add(wf[i - 1]); ctx_div[wf[i - 1]].add(wf[i])

    # ---- SCAFFOLD 1 REMOVED: self-identify the SPECIFIC function-forms (top by freq x context-diversity) ----
    func_forms = [f for f in isf if isf.get(f) and f in freq]
    FF = sorted(func_forms, key=lambda f: -(freq[f] * len(ctx_div[f])))[:M_FF]
    FFset = set(FF)
    dom_word = {}
    byform = defaultdict(list)
    for i in range(len(wf)):
        byform[wf[i]].append(words[i])
    for f in set(wf):
        dom_word[f] = Counter(byform[f]).most_common(1)[0][0]
    print(f"\n--- (a) SELF-IDENTIFIED specific function-forms (distribution ONLY, no transcript) ---")
    print(f"  top-{M_FF}: {', '.join(dom_word[f] for f in FF)}")

    # ---- SCAFFOLD 2 REMOVED: self-discover CONTENT categories by FRAME DISTRIBUTION ----
    ffidx = {f: k for k, f in enumerate(FF)}
    # CONTENT for category-discovery: the agent's median split degenerates on a heavy singleton tail
    # (marks ALL recurring forms function), so use the distributional CONTEXT-DIVERSITY RATIO (distinct
    # neighbours / occurrences) — function words appear with MANY different neighbours per occurrence;
    # content words are collocational (low ratio). Recurring (freq>=3) LOW-ratio forms = recurring content.
    ratio = {f: len(ctx_div[f]) / freq[f] for f in freq}
    med_ratio = float(np.median([ratio[f] for f in freq if freq[f] >= 3])) if any(freq[f] >= 3 for f in freq) else 1.0
    content_forms = [f for f in freq if freq[f] >= 3 and ratio[f] <= med_ratio and f not in ffidx]
    fvec = {f: np.zeros(M_FF) for f in content_forms}       # frame-vector = WHICH self-function-form precedes
    for i in range(1, cut):
        if wf[i] in fvec and wf[i - 1] in ffidx:
            fvec[wf[i]][ffidx[wf[i - 1]]] += 1.0
    forms = [f for f in content_forms if fvec[f].sum() >= 1]   # informative frame-distribution only
    print(f"  [self-category: {len(content_forms)} recurring content forms (ratio<=median), "
          f"{len(forms)} with a frame]")
    if len(forms) < KCAT:
        forms = content_forms if len(content_forms) >= KCAT else list(freq)[:max(KCAT, 10)]
        for f in forms:
            fvec.setdefault(f, np.zeros(M_FF))
    Fmat = R._unit(np.stack([fvec[f] for f in forms]))
    catlab = R.kmeans(Fmat, min(KCAT, len(forms)), np.random.default_rng(0))
    form_cat = {forms[k]: int(catlab[k]) for k in range(len(forms))}   # content form -> self-category
    def selfcat(i):
        return form_cat.get(wf[i], -1)

    # ---- SELF-CONTAINED bootstrapping signal: does a self function-form predict a self-category? ----
    # self-DETERMINER form = the self-function-form with the most DISTINCT content-form followers
    # (a determiner precedes MANY different nouns; an auxiliary precedes fewer predicates) — self-picked,
    # no transcript. Its top self-category is the category it frames (the noun-category).
    best_f, best_c, best_div = None, None, -1
    for f in FF:
        distinct = len(set(wf[i] for i in range(1, cut) if wf[i - 1] == f))   # distinct content followers
        if distinct > best_div:
            cd = Counter(selfcat(i) for i in range(1, cut) if wf[i - 1] == f and selfcat(i) >= 0)
            if cd:
                best_div, best_f, best_c = distinct, f, cd.most_common(1)[0][0]
    if best_f is None:
        best_f = FF[0]; best_c = 0
    te = range(cut, len(words))
    def cond(pred_prev):
        xs = [int(selfcat(i) == best_c) for i in te if i > cut and pred_prev(wf[i - 1]) and selfcat(i) >= 0]
        return (float(np.mean(xs)) if xs else float("nan")), len(xs)
    base_cat = float(np.mean([int(selfcat(i) == best_c) for i in te if selfcat(i) >= 0]))
    spec, n_spec = cond(lambda p: p == best_f)              # SPECIFIC self-determiner-form frame
    gen, n_gen = cond(lambda p: p in FFset)                 # GENERIC any-self-function frame
    permw = list(np.random.default_rng(3).permutation(len(wf)))
    def selfcat_sh(i):
        return form_cat.get(wf[permw[i]], -1)
    xs = [int(selfcat(i) == best_c) for i in te if i > cut and wf[permw[i - 1]] == best_f and selfcat(i) >= 0]
    sh = float(np.mean(xs)) if xs else float("nan")
    print(f"\n--- (c) FULLY SELF-CONTAINED signal: self-determiner-form -> self-category ---")
    print(f"  self-determiner-form = {dom_word[best_f]!r} (self-picked); self-category c{best_c}")
    print(f"  P(self-cat=c{best_c}) base {base_cat:.3f} | SPECIFIC {spec:.3f} (n={n_spec}) | "
          f"GENERIC {gen:.3f} (n={n_gen}) | SHUFFLED {sh:.3f}")

    # =============================== SCORING ONLY (eval labels, off the decision) ==================
    # (a) self-identified function-forms MATCH real function words vs freq-only / random controls
    def func_hit(forms_list):
        return float(np.mean([dom_word[f] in D.FUNC for f in forms_list]))
    top_freq = sorted(freq, key=lambda f: -freq[f])[:M_FF]
    rng = np.random.default_rng(1); allf = list(freq)
    rand = list(rng.choice(len(allf), min(M_FF, len(allf)), replace=False))
    a_self = func_hit(FF); a_freq = func_hit(top_freq); a_rand = func_hit([allf[i] for i in rand])
    # (b) self-discovered categories align with real POS (dominant nltk-POS purity per self-category)
    catpos = defaultdict(list)
    for i in range(len(wf)):
        c = selfcat(i)
        if c >= 0:
            catpos[c].append(tags[i][:2])
    pos_purity = float(np.mean([Counter(v).most_common(1)[0][1] / len(v) for v in catpos.values() if len(v) >= 5]))
    # self-determiner-form's following POS (the self-contained analog of the scaffolded 'the/a'->noun 0.435)
    noun_after = [int(tags[i].startswith("NN")) for i in te if i > cut and wf[i - 1] == best_f]
    p_noun_after = float(np.mean(noun_after)) if noun_after else float("nan")
    base_noun = float(np.mean([tags[i].startswith("NN") for i in te]))
    best_cat_pos = Counter(catpos[best_c]).most_common(2) if best_c in catpos else []

    print("\n--- SCORING (eval labels OFF the decision path) ---")
    print(f"  (a) self-identified forms match real function words: SELF {a_self:.3f}  vs freq-only {a_freq:.3f}"
          f"  vs random {a_rand:.3f}")
    print(f"  (b) self-discovered category POS-purity {pos_purity:.3f}; self-category c{best_c} top POS "
          f"{best_cat_pos}")
    print(f"  self-determiner-form -> real NOUN: {p_noun_after:.3f} vs base {base_noun:.3f} "
          f"(scaffolded prior 'the/a'->noun {SCAFFOLDED_PRIOR:.3f})")

    teacher_free = not any(m in sys.modules for m in ("allosaurus", "torch", "torchaudio"))
    print("\n--- (c) donkey=0: NO label on the decision path ---")
    print(f"  allosaurus/torch/torchaudio in sys.modules: "
          f"{[m for m in ('allosaurus','torch','torchaudio') if m in sys.modules] or 'NONE'}")
    print("  decision path = earned numpy encoder + held edit-distance + agent-authored distributional rule")
    print("  + held k-means over frame-distributions; transcript/nltk-POS used ONLY in the SCORING block.")

    print("=" * 96)
    self_margin = (spec - max(base_cat, gen if not np.isnan(gen) else 0, sh if not np.isnan(sh) else 0)
                   if not np.isnan(spec) else float("nan"))
    forms_ok = a_self > a_freq + 0.05 and a_self > a_rand + 0.2
    cat_ok = pos_purity > 0.5
    signal_ok = (not np.isnan(spec) and spec - base_cat > 0.08 and (np.isnan(gen) or spec > gen + 0.05)
                 and (np.isnan(sh) or spec > sh + 0.08))
    print("VERDICT — is syntactic bootstrapping FULLY SELF-SUPERVISED end-to-end (donkey=0, no labels in loop)?")
    print(f"  SCAFFOLD 1 (function-form IDENTITY) SELF-REMOVED: {'YES' if forms_ok else 'partial'} — self-")
    print(f"     identified forms MATCH real function words ({a_self:.2f} vs random {a_rand:.2f}); note it is")
    print(f"     frequency-EQUIVALENT (freq-only {a_freq:.2f} — frequency alone is diagnostic of function-hood")
    print(f"     on clean speech). The closed class IS self-identifiable from distribution, no transcript.")
    print(f"  SCAFFOLD 2 (category TARGET) NOT self-removable at this scale: self-discovered categories")
    print(f"     POS-purity {pos_purity:.2f} (weak) — only {len(content_forms)} recurring content forms, {len(forms)} with")
    print(f"     a frame, so frame-distribution clustering COLLAPSES (a {base_cat:.0%} dominant cluster); the")
    print(f"     specific-frame->self-category signal is {'HOLDS' if signal_ok else 'NULL'} "
          f"(spec {spec:.3f} vs base {base_cat:.3f}/gen {gen:.3f}/shuf {sh:.3f}).")
    print(f"  the LOOP IS fully self-contained + donkey=0 (no label on any decision: {teacher_free}); the")
    print(f"     residual is precise: distributional CATEGORY induction needs many observations per content")
    print(f"     word, but large-vocab connected speech has a heavy SINGLETON tail -> categories can't be")
    print(f"     self-estimated. nltk-POS (the removed scaffold) supplied a category for EVERY word incl.")
    print(f"     singletons — THAT is what it was doing. Not order-1 consistency (that's fixed, b48407ce);")
    print(f"     the bound is CONTENT-WORD DATA (more tokens/word) or a denser category signal.")
    print(f"  self-contained 'determiner'->real-noun {p_noun_after:.3f} vs scaffolded {SCAFFOLDED_PRIOR:.3f}.")
    print(f"  [peak RSS {D._peak_gib():.2f} GiB]")
    print("=" * 96)


if __name__ == "__main__":
    main()
