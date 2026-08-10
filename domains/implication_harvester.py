"""implication_harvester — the agent harvests its OWN implication-shapes.

This closes the last human-seeded part of order-N gap-synthesis
([[ozma_order_n_concepts]] / domains/order_n_postulates.py). That operator
DERIVES the agent's next capability from a postulate it holds, by transferring an
implication-SHAPE — a structural pattern like "X is a linear system => X is
invertible / parametrically identifiable", "X is a distribution => X can be
clustered". Until now that SET of shapes was a finite, hand-curated Python stencil
(order_n_postulates._shapes) — the one part bounded by the human's breadth rather
than the agent's.

This module replaces the stencil with shapes the agent HARVESTS from its OWN
Concepts, across ALL its domains (linear-algebra, signals/DSP, statistics, ML,
physics, control, ...). It is the SAME move analogy.abstract_patterns already
makes for features — abstract the transferable STRUCTURE of a concept, drop the
domain-specific operands, keep the form — applied now to the IMPLICATION RELATION
a concept's text encodes instead of to a Term-tree's operation shape:

  • abstract_patterns:  Term-tree  -> skeleton (which-band/which-const hollowed)
  • this module:        concept text -> implication-shape (object hollowed to <X>)

A concept's `definition` + `why` (the agent's held knowledge as text) states a
STRUCTURAL PROPERTY of its object and an OPERATION / CONSEQUENCE that property
entails — e.g.

    IIR_filter   "y[n] = ... - Σ a_k·y[n-k]. Recursive."
        => structural property: the system is RECURSIVE / ALL-POLE / autoregressive
        => consequence:        a few feedback coefficients (poles) capture it —
                               recovered by linear prediction, not read off a spectrum
    unsupervised_learning  "Train on unlabelled data ... clustering ..."
        => structural property: the data is an unlabelled DISTRIBUTION
        => consequence:        its structure (clusters) is found WITHOUT labels

The harvester recognises that property->consequence relation with a small set of
domain-GENERAL structural EXTRACTORS (the agent's notion of "what kinds of
implication exist": invertibility, parametric-identifiability, latent-structure,
scale-cancellation, removable-context, forward/inverse). Each extractor is
keyword-level and cross-domain — it is NOT "speech" or "LPC"; it fires on ANY
concept whose text exhibits the structure, and names the source concept + domain
it was harvested FROM. The extractors are the agent's generic grasp of implication
(the analogue of the skeletoniser's "drop which-band"); the SHAPES — the actual
transferable patterns and what they entail — come entirely from the agent's own
concepts. With enough breadth the harvest reproduces (and exceeds) the hand
stencil; where the harvest is too thin, that is reported honestly, not faked.

Output: a list of shape dicts in EXACTLY the format order_n_postulates.differentiate
consumes — {name, domain, match_patterns, consequence, match_keys, name_keys} —
plus provenance (source_concept) so each derived gap can name which of the agent's
own concepts supplied the shape that produced it.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Structural EXTRACTORS — the agent's GENERIC grasp of "what an implication is".
#
# Each extractor recognises one KIND of structure-implies-operation relation in a
# concept's text. It is the analogue of analogy._skeletonize's rule "an Attr is a
# hole" — a domain-general recogniser, NOT a domain-specific answer. An extractor
# declares:
#   id            — the implication KIND it recognises;
#   evidence      — regexes over a SOURCE concept's text; if any fire, that concept
#                   EXHIBITS this structural kind and can DONATE a shape of it;
#   triggers      — regexes over a POSTULATE's property text saying WHEN the
#                   harvested shape applies (the structural property that, in any
#                   domain, entails this kind of implication);
#   consequence   — a template for what the structure entails (the order k->k+1
#                   step), with {object}/{src} filled from the postulate/source;
#   match_keys    — loose keys letting the NEXT order match this consequence;
#   name_keys_for — given the SOURCE concept, the DISTINCTIVE identifying terms for
#                   the capability the consequence names (used by the selector's
#                   coverage check) — drawn from the source concept's OWN vocabulary
#                   so the harvested capability name is the agent's, not a constant.
#
# The extractors encode KINDS of implication, not the implications themselves; the
# implications (which structures exist, what they entail) are read off the concepts.
# ---------------------------------------------------------------------------


def _extractors():
    return [
        # --- INVERTIBILITY: a linear / well-conditioned operator can be undone,
        #     so what it mixed can be SEPARATED. (linear algebra / signals.) ------
        {"id": "invertibility",
         "evidence": [r"\binvertible\b", r"pseudoinverse", r"deconvolv",
                      r"solves?\s+least\s+squares", r"non-?zero\s+iff\s+invertible",
                      r"\bdeterminant\b.*invertible"],
         "triggers": [r"linear\s+filter", r"linear\s+system", r"linear\s+operator",
                      r"\bfilter\b.*\blinear\b", r"\blinear\b.*\bfilter\b",
                      r"linear\s+map", r"acts?\s+as\s+a\s+.*filter"],
         "consequence": (
             "a LINEAR operator is INVERTIBLE — the mixing it applies can be "
             "deconvolved / inverted out (cf. {src}), so the source and the "
             "operator (its resonances) can be SEPARATED / identified rather than "
             "left entangled"),
         "match_keys": ["invertible", "deconvolve", "separate", "identify"],
         "name_signals": [r"invers", r"pseudoinverse", r"decompos", r"deconvolv",
                          r"determinant", r"\bsvd\b"],
         "name_keys_for": lambda nm: ["cepstral liftering", "cepstrum",
                                      "homomorphic deconvolution"]},

        # --- PARAMETRIC / ALL-POLE IDENTIFIABILITY: a recursive (feedback / IIR /
        #     autoregressive) system is captured by a FEW poles, recovered by linear
        #     prediction. (signals / control / ML autoregression.) ----------------
        {"id": "parametric_allpole",
         "evidence": [r"\bautoregress", r"all-?pole",
                      r"recursive.*\bfilter\b", r"\bfilter\b.*recursive",
                      r"infinite\s+impulse\s+response", r"\biir\b",
                      r"y\[n\].*y\[n-?k\]", r"poles?\b.*\bgain",
                      r"feedback.*coefficient"],
         # TRIGGERS — when does the all-pole shape APPLY? It applies to a postulate
         # that describes a RESONANT LINEAR FILTER, by STRUCTURAL KIND (not by the
         # surface words "all-pole"/"IIR", which a science postulate would never
         # use). The structural bridge the agent holds across its concepts —
         # IIR_filter, source_filter_theory, vocal_tract_resonance_formants all
         # describe pole/resonance systems — is RESONANCE <-> POLE: a resonance (a
         # spectral peak / formant) IS a pole of a 1/A(z) all-pole filter. So the
         # shape fires on any system the postulate frames as a linear/resonant
         # filter WITH resonances/formants, OR on the derived invertibility step.
         # This is a structural-KIND match (resonant-linear-filter), not a keyword
         # overlap and not a hardwired "source_filter_theory -> LPC" rule.
         "triggers": [
             # (i) the DERIVED invertibility step (order-1 -> order-2 chaining):
             r"\binvertible\b", r"deconvolv", r"all-?resonance", r"\bseparated\b",
             # (ii) the structural KIND directly: a resonant / pole-bearing system,
             #      or a (linear) filter that imposes/has resonances or formants.
             r"\bresonanc", r"\bpoles?\b",
             r"\bfilter\b[\s\S]{0,80}\b(?:resonanc|formant)",
             r"\b(?:resonanc|formant)[\s\S]{0,80}\bfilter\b",
             r"\bformants?\b[\s\S]{0,40}\b(?:resonanc|spectral\s+(?:peak|envelope))",
         ],
         "consequence": (
             "an invertible all-resonance system is captured by an ALL-POLE / "
             "AUTOREGRESSIVE (linear-predictive) model (cf. {src}): a FEW feedback "
             "poles ARE the resonances, recovered by LINEAR PREDICTION rather than "
             "read off a blurry spectrum"),
         "match_keys": ["all-pole", "linear predict", "parametric",
                        "autoregressive"],
         "name_signals": [r"\biir\b", r"all-?pole", r"autoregress",
                          r"recursive", r"filter", r"root_locus", r"poles?"],
         "name_keys_for": lambda nm: ["all-pole", "levinson", "lpc-formant",
                                      "autoregressive"]},

        # --- LATENT / DISTRIBUTIONAL STRUCTURE: unlabelled data's structure (its
        #     modes / mixture components / clusters) is recoverable WITHOUT labels.
        #     (statistics / unsupervised ML.) -------------------------------------
        {"id": "latent_structure",
         "evidence": [r"\bcluster", r"unsupervised", r"latent\s+variable",
                      r"\bmixture\b", r"expectation-?maximization",
                      r"\bem\s+algorithm", r"unlabelled", r"unlabeled",
                      r"\bmodes?\b.*distribut"],
         "triggers": [r"distribut", r"co-?occurr", r"regulariti", r"\bmodes?\b",
                      r"unimodal", r"bimodal", r"statistic", r"frequency\s+of",
                      r"track.*occurr"],
         "consequence": (
             "an unlabelled DISTRIBUTION has recoverable LATENT structure (cf. "
             "{src}): unsupervised CLUSTERING / mixture-fitting carves its "
             "categories at the valleys between modes with NO labels — across "
             "speakers, the same word's tokens are one cluster"),
         "match_keys": ["cluster", "unsupervised", "mode", "mixture"],
         "name_signals": [r"cluster", r"unsupervised", r"mixture", r"\bem\b",
                          r"latent", r"gaussian_mixture", r"k.?means"],
         "name_keys_for": lambda nm: ["unsupervised-clustering",
                                      "cross-speaker-clustering", "cross-speaker"]},

        # --- SEQUENTIAL PREDICTABILITY: where predictability DROPS in a sequence is
        #     a BOUNDARY — segmentation from stream statistics. (info theory /
        #     statistics / sequence models.) --------------------------------------
        {"id": "sequence_segmentation",
         # require SEQUENCE context (so thermodynamic 'entropy' and the
         # Markov/Chebyshev tail-bound INEQUALITIES — which mention the words but
         # are not about sequences — do not qualify as donors).
         "evidence": [r"transition.*probab", r"transitional", r"\bn-?gram\b",
                      r"predict.*next", r"conditional.*probab",
                      r"entropy.*(?:next|symbol|sequen|token|source\s+cod)",
                      r"surprisal", r"markov\s+(?:chain|process|model)",
                      r"sequence.*model", r"next-?token"],
         "triggers": [r"transitional", r"co-?occurr", r"across\s+syllab",
                      r"word\s+boundar", r"transition.*probab", r"sequen",
                      r"\bstream\b", r"\bchunk"],
         "consequence": (
             "tracking PREDICTABILITY over a SEQUENCE (cf. {src}) finds boundaries "
             "where it DROPS — word / chunk SEGMENTATION at the low-probability "
             "dips, learned from unlabelled stream statistics"),
         "match_keys": ["boundary", "chunk", "sequence", "segment"],
         "name_signals": [r"markov", r"\bn.?gram\b", r"recurrent", r"\blstm\b",
                          r"sequence", r"transition", r"entropy", r"source_coding",
                          r"tokeniz"],
         "name_keys_for": lambda nm: ["transitional probability",
                                      "word-scale chunking",
                                      "statistical segmentation", "n-gram boundary"]},

        # --- SCALE CANCELLATION: a multiplicative / length scale factor is removed
        #     by a RATIO or a normalisation. (physics / signals / ML normalisation.)
        {"id": "scale_cancellation",
         "evidence": [r"\bratio\b.*(?:cancel|invariant|scale|dimensionless)",
                      r"scale-?invariant", r"dimensionless",
                      r"normaliz.*(?:scale|mean|variance)",
                      r"normalis.*(?:scale|mean|variance)",
                      r"divide.*by.*(?:mean|baseline|reference)",
                      r"standardiz"],
         "triggers": [r"vocal-?tract\s+length", r"\bspeaker\b", r"\btalker\b",
                      r"shift.*frequenc", r"scaling.*talker", r"scale.*vocal",
                      r"length.*scal", r"multiplicativ"],
         "consequence": (
             "a multiplicative / length SCALE factor is cancelled by a RATIO or a "
             "per-source normalisation (cf. {src}): normalising formant FREQUENCIES "
             "by their ratios (or a per-speaker baseline) removes the "
             "vocal-tract-length / speaker scale"),
         "match_keys": ["ratio", "normalise", "scale-invariant", "standardiz"],
         "name_signals": [r"normaliz", r"normalis", r"standardiz", r"\bratio\b",
                          r"dimensionless", r"reynolds", r"scale.?invariant"],
         "name_keys_for": lambda nm: ["speaker normalization", "formant ratio",
                                      "vocal-tract-length normalization", "f2/f1"]},

        # --- REMOVABLE CONTEXT: a quantity that is a smooth FUNCTION of known
        #     context can have that context MODELLED and SUBTRACTED. (control /
        #     regression / signals.) ----------------------------------------------
        {"id": "removable_context",
         "evidence": [r"regress.*on", r"predict.*from.*(?:covariate|predictor|"
                      r"feature|input)", r"\bresidual\b", r"subtract.*(?:trend|"
                      r"mean|baseline|predicted)", r"detrend", r"model.*and.*remov",
                      r"feedforward.*compensat", r"disturbance.*reject"],
         "triggers": [r"context-?dependen", r"depend.*on.*neighbour",
                      r"coarticul", r"non-?invariant", r"vary.*context",
                      r"depend.*neighbour", r"function\s+of.*context"],
         "consequence": (
             "if a quantity is a smooth FUNCTION of its known context (cf. {src}), "
             "the context-effect can be MODELLED and SUBTRACTED — predict the "
             "coarticulatory shift from the neighbours and remove it to recover the "
             "context-free target"),
         "match_keys": ["model", "subtract", "predict", "residual"],
         "name_signals": [r"regress", r"residual", r"detrend",
                          r"feedforward", r"disturbance", r"compensat"],
         "name_keys_for": lambda nm: ["coarticulation predict-remove",
                                      "context normalization", "carryover removal"]},

        # --- FORWARD/INVERSE: recovering causes from effects is an INVERSE problem
        #     that needs a FORWARD model to invert (analysis-by-synthesis).
        #     (control / inverse problems / generative models.) -------------------
        {"id": "forward_inverse",
         "evidence": [r"inverse\s+problem", r"forward\s+model", r"analysis-?by-?"
                      r"synthesis", r"generative\s+model.*invert", r"ill-?posed",
                      r"reconstruct.*from", r"simulate.*and.*match",
                      r"render.*and.*compare"],
         "triggers": [r"invert.*production", r"recover.*from.*cue",
                      r"perception.*inverse", r"inverse\s+map", r"\bimitat",
                      r"reproduce.*target", r"recover.*caus"],
         "consequence": (
             "recovering causes from effects is an INVERSE problem (cf. {src}) that "
             "needs a FORWARD model (articulation->acoustics) to invert — an "
             "internal synthesiser the loop can run and match against"),
         "match_keys": ["forward model", "synthesise", "analysis-by-synthesis"],
         "name_signals": [r"invers", r"controllability", r"observability",
                          r"reconstruct", r"generative", r"synthesis"],
         "name_keys_for": lambda nm: ["analysis-by-synthesis",
                                      "articulatory forward model",
                                      "internal synthesiser"]},

        # --- COMPOSITIONAL GENERATIVITY (BRICK 5): a system whose WHOLE is
        #     determined by its PARTS + a finite set of COMBINATION rules
        #     (a grammar / production system / compositional semantics) is
        #     GENERATIVE — its members form an open(-ended) set realizable by
        #     COMPOSING parts under the rules. (linguistics / formal-language /
        #     compiler / generative-model theory.) ---------------------------------
        #
        # EVIDENCE — what a SOURCE concept's text must ASSERT to EXHIBIT this kind:
        # genuine markers of compositional/generative STRUCTURE (a finite system of
        # parts + production rules that yields an open/unbounded set), NOT the bare
        # adjective "compositional" used for image-composition (rule_of_thirds) or a
        # one-off "substrate's compositional principle". Tuned (corpus-checked) to
        # tag generative_grammar / compositionality / construction_grammar /
        # code_generation / context_free_grammar and their kin (parse_tree,
        # production_rule, generative models) WITHOUT flooding (~0.5% of concepts).
        {"id": "compositional_generativity",
         "evidence": [
             r"compositional\s+(?:system|structure|grammar|semantics|generation|"
             r"term-?tree|mt-?pattern|expression)",
             r"compositionality?[.,]?\s+(?:frege|principle)",
             r"meaning\s+of\s+(?:a\s+)?complex\s+expression\s+determined\s+by\s+"
             r"meanings\s+of\s+parts",
             r"generative\s+(?:grammar|model|system|process)",
             r"finite\s+system\s+that\s+generates\s+infinite",
             r"(?:set\s+of\s+|\bgrammar\b.{0,30})production\s+rules?\b",
             r"production\s+rules?\s+(?:N|over\s+terminals|of\s+(?:a\s+)?grammar)",
             r"rewrite\s+rule\s+of\s+a\s+grammar",
             r"\bgrammar\b[^.]{0,60}(?:generat|produc|expand)",
             r"(?:generat|produc)\w*[^.]{0,40}\bgrammar\b",
             r"recursively\s+(?:built|defined)",
             r"(?:composed|built)\s+(?:of|from)\s+(?:its\s+)?(?:parts|subparts|"
             r"primitives|constituents?|components?)\b",
             r"open-?ended\s+set\b", r"combin\w*\s+by\s+(?:rules|productions?)",
             r"\bnonterminals?\b", r"form-?meaning\s+pairing",
             r"instruction\s+selection.{0,40}emission|"
             r"produce\s+(?:assembly|machine\s+code|code)\s+from",
             r"constructions?\s+\(form-?meaning",
         ],
         # TRIGGERS — when does the compositional-generativity shape APPLY to a
         # POSTULATE's property text? When the postulate frames its object as a
         # COMPOSITIONAL / GENERATIVE / RULE-PRODUCED system (or as the derived
         # "realizable by composing parts" step for order-1 -> order-2 chaining).
         "triggers": [
             r"compositional", r"generative\s+(?:grammar|model|system)",
             r"production\s+rules?", r"\bnonterminals?\b",
             r"finite\s+(?:system|means).{0,30}(?:infinite|unbounded|novel)",
             r"composed\s+(?:of|from)\s+parts", r"open-?ended\s+set",
             r"combin\w*\s+by\s+rules", r"yields?\s+(?:novel|unbounded)",
             # open-vocabulary RECOGNITION: a word never seen as a whole is still
             # producible as a sequence of smaller recurring parts (the WER OOV gap).
             r"produce\s+(?:a\s+)?\w*\s*as\s+a\s+sequence\s+of\s+smaller",
             r"sequence\s+of\s+smaller\s+(?:recurring\s+)?parts",
             r"all-?or-?nothing\s+whole", r"\bsub-?word\b",
             r"never\s+(?:heard|seen|encountered)[\s\S]{0,40}\bword",
             r"no\s+stored\s+\w*\s*for\s+a\s+word\s+it\s+has\s+never",
             # (ii) the DERIVED step, so it can chain order-1 -> order-2:
             r"realiz\w*\s+by\s+composing", r"search\s+over\s+(?:the\s+)?production",
             r"fold\s+over\s+(?:the\s+)?(?:production|composition)\s+space",
         ],
         # CONSEQUENCE — the DOMAIN-GENERAL structural entailment of
         # compositionality (NOT "therefore build the generator"). What
         # compositionality entails in ANY domain: a compositional system's whole
         # is fixed by its parts + combination rules, so its members are not
         # enumerated but REALIZED by composing parts — a fold/search over the
         # production space under a selection criterion. The agent's postulates +
         # the compression selector decide what specific gap (if any) this opens.
         "consequence": (
             "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its "
             "PARTS plus a finite set of COMBINATION (production) rules (cf. {src}), "
             "so its members are not an enumerated list but an OPEN set REALIZABLE "
             "BY COMPOSING parts — a FOLD / SEARCH over the production space under a "
             "selection criterion, rather than a fixed table lookup"),
         "match_keys": ["compose", "production", "generative", "search",
                        "realizable", "fold"],
         "name_signals": [r"grammar", r"generative", r"compositional",
                          r"production", r"nonterminal", r"\bcfg\b",
                          r"parse", r"construction", r"code_generation"],
         "name_keys_for": lambda nm: ["compositional generation",
                                      "production-space search",
                                      "compose-under-selection generator"]},

        # --- PREDICTIVE COMPLETION / RESTORATION: a signal with REDUNDANCY (a
        #     model that PREDICTS one part from another, or parity that covers it)
        #     can RECONSTRUCT a missing / masked / corrupted part. (self-supervised
        #     prediction / error-correcting codes / interpolation.) ----------------
        #
        # EVIDENCE — a SOURCE concept EXHIBITS this kind when it PREDICTS / FILLS /
        # CORRECTS a missing or masked part from the rest (masked-prediction,
        # error-correcting parity, interpolation/imputation). This is the structural
        # property `top_down_restoration` asserts — "higher levels PREDICT the
        # missing/masked segment and fill it in" — recognised wherever the agent
        # holds it (self_supervised_learning's "mask part, predict the missing
        # part"; Reed_Solomon's "correct t errors from parity"; interpolation).
        {"id": "predictive_completion",
         "evidence": [
             r"mask\w*\s+(?:part|the|a)\b[\s\S]{0,40}predict",
             r"predict\s+the\s+(?:miss|masked|next|held-?out)",
             r"fill\s+in\s+(?:the\s+)?(?:blank|miss|gap|mask)",
             r"\bimputat", r"impute\s+miss", r"interpolat\w*\s+miss",
             r"reconstruct\w*\s+(?:the\s+)?(?:miss|corrupt|erased|lost)",
             r"correct\w*\s+\w*\s*errors?", r"error[- ]correct",
             r"parity\s+symbol", r"recover\w*\s+(?:miss|lost|erased)\s+\w*"
             r"(?:symbol|sample|data|value)",
             r"masked\s+(?:language|autoencoder|prediction)",
         ],
         # TRIGGERS — when does the restoration shape APPLY to a postulate? When the
         # postulate frames its object as a signal whose MISSING / MASKED / DEGRADED
         # part is FILLED from CONTEXT or a PREDICTION (the structural property of
         # phonemic restoration), OR the derived "redundancy reconstructs" step.
         "triggers": [
             r"fill\w*\s+in\s+(?:miss|the\s+miss)", r"miss\w*\s+or\s+masked",
             r"masked\s+segment", r"noise-?replaced", r"phonemic\s+restoration",
             r"\brestor", r"context\s+predict\w*\s+it", r"higher\s+levels?\s+feed",
             r"predict\w*\s+(?:the\s+)?(?:miss|masked|degraded)",
             r"top-?down\b[\s\S]{0,40}(?:fill|restor|predict)",
             r"\breconstruct\w*\s+(?:from|the\s+miss)",
             # word-sequence LANGUAGE MODEL: which words follow which lets a doubtful
             # word be recovered from its surrounding context (the WER LM gap).
             r"which\s+words?\s+(?:tend\s+to\s+)?follow\s+which",
             r"surrounding\s+words?\s+to\s+recover",
             r"recover\s+a\s+(?:doubtful|missing|uncertain)",
             r"model\s+of\s+which\s+\w*\s*follow",
         ],
         "consequence": (
             "a signal carrying REDUNDANCY (a model that predicts one part from "
             "the rest — cf. {src}) can RECONSTRUCT a missing / masked / degraded "
             "part: top-down PREDICTION from the lexical+context model fills the "
             "blurred or masked segment, so the category is recovered by COMPLETION "
             "from the predictor, not read off the degraded acoustics"),
         "match_keys": ["restore", "predict", "fill", "reconstruct"],
         "name_signals": [r"self_supervised", r"masked", r"reed_solomon",
                          r"error.?correct", r"interpolat", r"imputat",
                          r"pretrain", r"reconstruct"],
         "name_keys_for": lambda nm: ["top-down restoration",
                                      "lexical-prediction fill-in",
                                      "context-predictive completion"]},

        # --- QUANTIZATION / CONTINUOUS->DISCRETE: a CONTINUOUS dimension is mapped
        #     to a SMALL SET of DISCRETE levels by a decision boundary (rounding /
        #     decision rule / argmax), giving sharp category edges + within-level
        #     collapse. (quantization / classification / thresholding.) -------------
        {"id": "quantize_to_categories",
         "evidence": [
             r"\bquantiz", r"\bdiscretiz", r"round\w*\s+to\s+(?:the\s+)?(?:nearest|"
             r"level)", r"decision\s+boundary", r"\bthreshold\w*\b",
             r"map\w*\s+continuous\s+\w*\s*to\s+discrete",
             r"continuous\s+\w*\s*(?:to|into)\s+(?:a\s+)?(?:few\s+)?(?:discrete\s+)?"
             r"(?:level|categor|class|bin)",
             r"reduce\s+\w*\s*precision", r"\bargmax\b.*(?:class|categor)",
             r"winner-?take", r"hard\s+assignment",
         ],
         # TRIGGERS — a postulate whose object turns a CONTINUOUS acoustic dimension
         # into DISCRETE categories with a SHARP boundary (categorical perception),
         # or the derived "levels are recovered by a decision rule" step.
         "triggers": [
             r"continuous\s+\w*\s*(?:dimension|cue|acoustic)",
             r"perceived\s+as\s+discrete", r"discrete\s+categor",
             r"sharp\s+\w*\s*boundar", r"identification\s+boundar",
             r"poor\s+within-?categor", r"continuum\s*(?:->|to|into)\s*categor",
             r"categor\w*\s+perception",
         ],
         "consequence": (
             "mapping a CONTINUOUS dimension to a SMALL SET of DISCRETE levels by a "
             "decision boundary (cf. {src}) yields SHARP category edges with "
             "within-level collapse: a learned decision rule / quantiser over the "
             "continuous cue PRODUCES the categorical-perception signature (good "
             "across-boundary, poor within-category discrimination)"),
         "match_keys": ["quantise", "discretise", "decision boundary", "categor"],
         "name_signals": [r"quantiz", r"discretiz", r"classif", r"decision",
                          r"threshold", r"vector_quantiz", r"k.?means"],
         "name_keys_for": lambda nm: ["categorical quantiser",
                                      "learned decision boundary",
                                      "continuous-to-discrete category map"]},

        # --- ATTRACTOR / PROTOTYPE-PULL: a dynamical system with stable FIXED
        #     POINTS / ATTRACTORS pulls nearby states TOWARD the attractor, warping
        #     the local metric (contraction near the basin centre). A learned
        #     PROTOTYPE acts as such an attractor. (dynamical systems / attractor
        #     networks / vector-quantisation toward a centroid.) --------------------
        {"id": "attractor_warps_metric",
         "evidence": [
             r"\battractor", r"fixed\s+point", r"basin\s+of\s+attraction",
             r"\bcentroid", r"centre\s+of\s+mass",
             r"pull\w*\s+toward", r"converge\w*\s+to\s+(?:a\s+)?(?:fixed|stable|"
             r"prototype|centre|centroid|equilibri)",
             r"energy\s+minim\w*\s+to\s+(?:a\s+)?(?:fixed|stable)",
             r"contract\w*\s+toward", r"settle\w*\s+(?:into|to)\s+(?:a\s+)?(?:stable|"
             r"fixed)",
         ],
         # TRIGGERS — a postulate whose object PULLS exemplars TOWARD a PROTOTYPE,
         # WARPING the perceptual space (perceptual magnet), or the derived
         # "attractor contracts the metric near the prototype" step.
         "triggers": [
             r"pull\w*\s+toward\s+(?:the\s+)?(?:prototype|centre|centroid)",
             r"warp\w*\s+(?:the\s+)?\w*\s*space", r"prototype",
             r"differences?\s+\w*\s*shrink", r"perceptual\s+magnet",
             r"reshape\w*\s+(?:the\s+)?\w*\s*metric", r"\bmagnet\s+effect",
             r"near\s+the\s+(?:prototype|centre|centroid)",
         ],
         "consequence": (
             "a dynamical system with stable FIXED POINTS / ATTRACTORS (cf. {src}) "
             "pulls nearby states TOWARD the attractor and CONTRACTS the metric near "
             "its basin: a learned category PROTOTYPE acts as such an attractor, so "
             "within-category differences shrink near the centre — the perceptual "
             "magnet is attractor dynamics over the category prototype, not a label"),
         "match_keys": ["attractor", "prototype", "contract", "warp metric"],
         "name_signals": [r"attractor", r"dynamical", r"strange_attractor",
                          r"centroid", r"fixed.?point", r"hopfield", r"basin"],
         "name_keys_for": lambda nm: ["prototype attractor warp",
                                      "category-prototype magnet",
                                      "attractor-contracted metric"]},

        # --- OPTIMAL MULTI-SOURCE FUSION: when SEVERAL independent estimates of one
        #     latent quantity are available, the optimal combination is a RELIABILITY
        #     (inverse-variance / precision) WEIGHTED blend — more reliable sources
        #     dominate, the fused estimate beats any single one. (Kalman / sensor
        #     fusion / ensemble / Bayesian cue combination.) ------------------------
        {"id": "reliability_weighted_fusion",
         "evidence": [
             r"optimal\s+state\s+estimat", r"\bkalman", r"sensor\s+fusion",
             r"data\s+fusion", r"\bfuse\w*\b", r"inverse-?variance",
             r"precision-?weighted", r"reliability-?weighted",
             r"combin\w*\s+\w*\s*(?:estimat|measur|sensor|source|modal|prediction)",
             r"weighted\s+(?:by\s+)?(?:their\s+)?(?:reliab|variance|precision|"
             r"uncertaint)", r"\bensembl\w*\b",
             r"prediction\s*\+\s*measurement",
         ],
         # TRIGGERS — a postulate whose object INTEGRATES MULTIPLE cues / modalities
         # / sources into ONE percept (audiovisual integration, multi-cue trade-off),
         # or the derived "weight each source by its reliability" step.
         "triggers": [
             r"integrat\w*\s+with\s+(?:the\s+)?\w*\s*signal",
             r"multimodal", r"multiple\s+cues?", r"cues?\s+(?:that\s+)?trade\s+off",
             r"audio\s*\+\s*video", r"fused\s+percept", r"mcgurk",
             r"combin\w*\s+(?:cue|modal|source|sensor)",
             r"integrat\w*\s+\w*\s*(?:modal|cue|sensor|source)",
         ],
         "consequence": (
             "when SEVERAL independent estimates of ONE latent quantity are "
             "available (cf. {src}), the optimal fusion is a RELIABILITY "
             "(inverse-variance / precision) WEIGHTED blend — each cue / modality "
             "weighted by how reliable it is, the fused estimate beating any single "
             "source: audiovisual + multi-cue integration is reliability-weighted "
             "fusion of the cues into one category estimate"),
         "match_keys": ["fuse", "reliability weight", "combine", "integrate"],
         "name_signals": [r"kalman", r"fusion", r"ensembl", r"observer",
                          r"bayesian", r"sensor", r"inverse.?variance"],
         "name_keys_for": lambda nm: ["reliability-weighted cue fusion",
                                      "multi-cue integration",
                                      "audiovisual fusion estimate"]},

        # --- DISCRIMINANT SUBSPACE PROJECTION: a structured nuisance that lives in a
        #     SUBSPACE / DIRECTION (not a scalar) — a within-class scatter direction a
        #     class spreads along — is removed by PROJECTING onto the complement of the
        #     within-class scatter / WHITENING by the within-class covariance. The shape
        #     the agent named as its frozen edge (Fisher / LDA / WCCN; linear algebra /
        #     statistics / ML). Distinct from scale_cancellation, which removes a SCALAR
        #     scale; this removes a structured DIRECTION the scalar normaliser leaves. --
        {"id": "discriminant_projection",
         "evidence": [
             r"within-?class\s+(?:scatter|covariance|variance)",
             r"between-?class\s+(?:scatter|covariance|variance)",
             r"fisher\s+(?:criterion|discriminant|ratio)",
             r"linear\s+discriminant", r"discriminant\s+(?:direction|analysis)",
             r"whiten\w*\s+by\s+(?:the\s+)?within-?class",
             r"project\w*\s+onto\s+(?:the\s+)?(?:complement|discriminant)",
             r"\bwccn\b", r"scatter\s+matri",
             r"ratio\s+of\s+between-?class\s+\w*\s*to\s+within-?class",
             r"nuisance\s+subspace",
         ],
         # TRIGGERS — a residual whose nuisance is a STRUCTURED DIRECTION/subspace (a
         # within-class spread that a scalar/mean removal does NOT cancel), not a single
         # offset or scalar scale. Matches the cross-speaker residual's own phrasing.
         "triggers": [
             r"spreads?\s+[\s\S]{0,40}\balong\s+[\s\S]{0,20}\bdirections?",
             r"within-?word\s+between-?speaker\s+spread",
             r"between-?speaker\s+(?:variation|spread|scatter)",
             r"co-?var\w*\s+across\s+[\s\S]{0,20}\bdimensions?",
             r"spread\s+is\s+large\s+compared\s+with\s+[\s\S]{0,30}\bspread",
             r"not\s+removed\s+by\s+[\s\S]{0,40}\bscalar\b",
             r"structured\s+(?:between-?speaker\s+)?(?:variation|component)",
             r"\bsubspace\b", r"scatter\s+matri", r"within-?class",
             r"directions?\s+of\s+the\s+\w*\s*space",
         ],
         "consequence": (
             "a structured nuisance that lives in a SUBSPACE — a WITHIN-CLASS scatter "
             "DIRECTION (not a scalar) along which a class's tokens spread across the "
             "nuisance (e.g. speakers) — is removed by PROJECTING onto the COMPLEMENT "
             "of the within-class scatter / WHITENING by the within-class covariance "
             "(cf. {src}): suppress the directions that vary WITHIN a class (across "
             "speakers) and keep the BETWEEN-class directions (Fisher / LDA / WCCN), so "
             "a held-out speaker's token lands with its class's cross-speaker group — "
             "the structured speaker DIRECTION a scalar baseline / ratio cannot remove"),
         "match_keys": ["within-class", "between-class", "project", "discriminant",
                        "whiten", "scatter"],
         "name_signals": [r"discrimin", r"scatter", r"whiten", r"fisher",
                          r"\blda\b", r"\bwccn\b", r"within.?class", r"subspace"],
         "name_keys_for": lambda nm: ["within-class covariance normalization",
                                      "LDA projection", "Fisher discriminant",
                                      "WCCN"]},

        # --- NUISANCE CONDITIONING ON AN OBSERVED ATTRIBUTE: a structured nuisance
        #     EXPLAINED BY A KNOWN/OBSERVED attribute (covariate / confound / batch /
        #     speaker) is removed WITHOUT the target labels by building the transform
        #     from the OBSERVED attribute's grouping (between-observed-group removal /
        #     regress-on-covariate residual). Distinct from discriminant_projection,
        #     which removes a within-TARGET-class direction and NEEDS target labels;
        #     this uses the observed attribute the target lacks. (stats / ML / domain
        #     adaptation.) -----------------------------------------------------------
        {"id": "nuisance_conditioning",
         "evidence": [
             r"\bcovariate\b", r"\bconfound", r"batch\s+effect", r"\bcombat\b",
             r"regress(?:es|ed|ing)?\s+(?:out|on)\b", r"condition(?:s|ed|ing)?\s+on\b",
             r"\bharmoniz", r"\bharmonis", r"nuisance\s+(?:attribute|variable|factor)",
             r"between-?group\s+(?:scatter|variation|removal)",
             r"observed\s+attribute", r"domain\s+adaptation",
         ],
         # TRIGGERS — a residual with TWO attributes where the nuisance one is OBSERVED/
         # known per token while the target is UNLABELLED. Matches the postulate phrasing.
         "triggers": [
             r"observed\s+attribute", r"observable", r"comes?\s+tagged\s+with",
             r"known\s+for\s+every\s+(?:token|sample|point)",
             r"recovers?\s+the\s+\w*\s*observed\s+attribute",
             r"two\s+attributes", r"second\s+attribute",
             r"explains?\s+[\s\S]{0,40}\bstructured\b[\s\S]{0,20}\bvariation",
             r"\bnuisance\b", r"\bcovariate\b", r"\bconfound",
             r"target[\s\S]{0,40}\b(?:unknown|unlabel|absent)",
         ],
         "consequence": (
             "a structured nuisance EXPLAINED BY A KNOWN / OBSERVED attribute (covariate "
             "/ confound / batch / speaker) is removed WITHOUT the target labels by "
             "building the transform from the OBSERVED attribute's OWN grouping (cf. "
             "{src}): compute the BETWEEN-observed-group scatter (the variation across "
             "the observed attribute's values) and project it out / whiten by it, OR "
             "regress each cue on the observed attribute and keep the residual — the "
             "observed attribute supplies the grouping the within-target-class whitening "
             "lacked, so the unknown target's structure surfaces in the residual"),
         "match_keys": ["covariate", "confound", "between-group", "regress out",
                        "condition on", "observed attribute"],
         "name_signals": [r"covariate", r"confound", r"combat", r"batch",
                          r"harmoniz", r"regress", r"domain.?adapt", r"nuisance"],
         "name_keys_for": lambda nm: ["covariate conditioning",
                                      "between-observed-group removal",
                                      "confound regression", "nuisance normalization"]},
    ]


# ---------------------------------------------------------------------------
# BRICK 4 — PROPERTY-KIND recognisers + tag_concept_properties.
#
# Brick 3 fired a substantive shape whenever its source-domain Mt sat in a
# postulate's genlMt lineage (within N hops). That over-fired: a postulate
# INHERITS a domain's shapes WITHOUT EXHIBITING the structural property the
# shape's consequence presupposes — e.g. Kalman_filter (lives under
# embedded_iot_realtime) inherited "MQTT outperforms HTTP" purely because both
# concepts share that ancestor Mt. 54% of brick-3 fires were that cross-domain
# JUNK.
#
# The fix is a RELEVANCE predicate: a substantive shape fires by structure ONLY
# when the postulate's OBJECT genuinely exhibits the structural property the
# shape's consequence presupposes. To test that, every Concept is one-time tagged
# with the set of structural PROPERTY-KINDs its OWN text exhibits — the same
# property-KIND vocabulary the 7 extractors recognise (keyed by extractor id).
#
# _PROPERTY_RECOGNISERS maps a property-KIND (the extractor id, plus the bare
# structural aliases the brief names — `recursion`, `all_pole`,
# `parametric_identifiability` collapse into `parametric_allpole`) to regexes
# over a concept's FULL text that say "this concept EXHIBITS this property". It
# REUSES each extractor's own evidence+triggers (the agent's grasp of the kind)
# and adds the bare structural markers of the property so a genuine exhibitor
# whose phrasing differs from the donor evidence is still tagged (e.g. Kalman's
# "Recursive state estimator" tags `parametric_allpole` via the bare `recursive`
# marker, even though it never says "IIR filter"). FOLKLORE text that presupposes
# no structural property ("MQTT outperforms HTTP for IoT") matches NOTHING here
# and is tagged with the empty set — so the rule-derived shapes harvested from
# such folklore get requires_property=None and never fire by the relevance path.
# ---------------------------------------------------------------------------

def _property_recognisers() -> dict:
    """property-KIND -> list of regexes that detect a concept EXHIBITING it.

    Built from the 7 extractors' own evidence+triggers (the agent's recognisers
    for the kind), UNION a small set of bare structural markers of the property
    the kind's consequence presupposes — so a genuine exhibitor is tagged even
    when its phrasing is not the donor's. Keyed by extractor id."""
    exs = {e["id"]: e for e in _extractors()}

    def base(kind):
        e = exs[kind]
        return list(e.get("evidence", [])) + list(e.get("triggers", []))

    rec: dict = {}
    # INVERTIBILITY — the object is a linear operator / map that can be undone.
    rec["invertibility"] = base("invertibility") + [
        r"\blinear\s+(?:map|operator|system|filter|transform)",
        r"\bmatrix\b", r"\bconvolv", r"\bbijectiv", r"one-?to-?one",
    ]
    # PARAMETRIC / ALL-POLE / RECURSION — the object is recursive / feedback /
    # autoregressive / pole-bearing, so a FEW parameters capture it. This is the
    # kind the brief names variously recursion / all_pole /
    # parametric_identifiability; they collapse to the parametric_allpole shape.
    rec["parametric_allpole"] = base("parametric_allpole") + [
        r"\brecursiv", r"\bfeedback\b", r"\bstate\s+estimat",
        r"\bautoregress", r"all-?pole", r"\biir\b", r"\bpoles?\b",
        r"prediction\s*\+\s*measurement", r"\brecurrence\b",
        r"\bgaussian\s+linear", r"updates?\s+(?:its\s+)?state",
    ]
    # LATENT / DISTRIBUTIONAL STRUCTURE — the object is an unlabelled
    # distribution with recoverable hidden structure.
    rec["latent_structure"] = base("latent_structure") + [
        r"\bdistribut", r"\bembedding", r"similar\s+meanings?",
        r"unlabel", r"\bcluster", r"\bmixture\b", r"latent",
        r"co-?occurr", r"word\s+embeddings?",
    ]
    # SEQUENTIAL PREDICTABILITY — the object is a sequence / stream with
    # transition structure, so predictability dips mark boundaries.
    rec["sequence_segmentation"] = base("sequence_segmentation") + [
        r"\bsequen", r"\bstream\b", r"transition", r"\bmarkov\b",
        r"next-?(?:token|symbol|state|word)", r"\bn-?gram\b",
        r"time\s+series", r"temporal\s+order",
    ]
    # SCALE CANCELLATION — the object carries a multiplicative / length scale a
    # ratio or normalisation removes.
    rec["scale_cancellation"] = base("scale_cancellation") + [
        r"\bscal(?:e|ing)\b", r"\bratio\b", r"normaliz", r"normalis",
        r"dimensionless", r"vocal-?tract\s+length", r"per-?speaker",
        r"\bgain\b.*\bvar", r"multiplicativ",
    ]
    # REMOVABLE CONTEXT — the object varies as a smooth function of known
    # context that can be modelled and subtracted.
    rec["removable_context"] = base("removable_context") + [
        r"context-?dependen", r"coarticul", r"depends?\s+on\s+(?:its\s+)?"
        r"(?:neighbour|context|surround)", r"\bregress",
        r"\bresidual\b", r"function\s+of\s+(?:its\s+)?context",
    ]
    # FORWARD/INVERSE — recovering causes from effects needs a forward model.
    rec["forward_inverse"] = base("forward_inverse") + [
        r"inverse\s+problem", r"forward\s+model", r"analysis-?by-?synthesis",
        r"generative\s+model", r"reconstruct", r"\bill-?posed\b",
        r"recover.*from", r"\bsynthesis", r"\bimitat",
    ]
    # COMPOSITIONAL GENERATIVITY (BRICK 5) — the object is a compositional /
    # generative / rule-produced system: its whole is fixed by its parts + a finite
    # set of combination (production) rules, yielding an open set. REUSE the
    # extractor's own evidence+triggers (the agent's grasp of the kind) and add a
    # couple of bare structural markers so an exhibitor whose phrasing differs from
    # the donor evidence is still tagged. Deliberately SPECIFIC (corpus-checked
    # ~0.5% tag rate) — bare adjectival "compositional X" (image composition,
    # one-off "compositional principle") is NOT tagged.
    rec["compositional_generativity"] = base("compositional_generativity") + [
        r"\bcontext-?free\s+grammar\b", r"\bphrase\s+structure\b",
        r"\bparse\s+tree\b", r"\bterminals?\s+and\s+nonterminals?\b",
        r"finite\s+system\s+that\s+generates",
        r"\bsub-?word\b", r"byte-?pair", r"wordpiece", r"open-?ended\s+set\s+of\s+words",
    ]
    # DISCRIMINANT SUBSPACE PROJECTION — a structured nuisance DIRECTION (within-class
    # scatter) is removed by projecting onto its complement / whitening by the
    # within-class covariance (Fisher / LDA / WCCN).
    rec["discriminant_projection"] = base("discriminant_projection") + [
        r"within-?class", r"between-?class", r"\bscatter\b", r"discrimin",
        r"\bwhiten", r"\bsubspace\b", r"\bfisher\b", r"\blda\b", r"\bwccn\b",
        r"project\w*\s+onto",
    ]
    # NUISANCE CONDITIONING — remove a nuisance explained by a KNOWN/observed attribute
    # using that attribute's own grouping (covariate / confound / batch / domain adapt).
    rec["nuisance_conditioning"] = base("nuisance_conditioning") + [
        r"\bcovariate\b", r"\bconfound", r"batch\s+effect", r"\bcombat\b",
        r"regress\w*\s+(?:out|on)", r"condition\w*\s+on", r"\bharmoniz", r"\bharmonis",
        r"observed\s+attribute", r"between-?group", r"nuisance", r"domain\s+adapt",
    ]
    # PREDICTIVE COMPLETION — the object fills / reconstructs a missing or masked
    # part from redundancy (a predictor or parity over the rest).
    rec["predictive_completion"] = base("predictive_completion") + [
        r"\brestor", r"phonemic\s+restoration", r"fill\s+in",
        r"which\s+words?\s+\w*\s*follow\s+which", r"language\s+model",
        r"next\s+word", r"recover\w*\s+\w*\s*from\s+(?:its\s+)?surrounding",
        r"masked", r"self-?supervised", r"error[- ]correct",
        r"parity", r"interpolat", r"impute",
    ]
    # QUANTIZE TO CATEGORIES — the object maps a continuous dimension to a small set
    # of discrete levels by a decision boundary.
    rec["quantize_to_categories"] = base("quantize_to_categories") + [
        r"\bquantiz", r"\bdiscretiz", r"discrete\s+categor",
        r"decision\s+boundary", r"\bthreshold", r"continuum",
        r"\bargmax\b", r"\bclassif",
    ]
    # ATTRACTOR WARPS METRIC — the object has stable fixed points / attractors that
    # pull nearby states in and warp the local metric (prototype pull).
    rec["attractor_warps_metric"] = base("attractor_warps_metric") + [
        r"\battractor", r"fixed\s+point", r"prototype", r"\bcentroid",
        r"basin", r"pull\w*\s+toward", r"\bmagnet", r"warp\w*\s+\w*\s*space",
    ]
    # RELIABILITY-WEIGHTED FUSION — the object combines several independent
    # estimates / cues / modalities into one, weighted by reliability.
    rec["reliability_weighted_fusion"] = base("reliability_weighted_fusion") + [
        r"\bkalman", r"sensor\s+fusion", r"\bfuse", r"multimodal",
        r"multiple\s+cues?", r"\bensembl", r"audiovisual",
        r"integrat\w*\s+\w*\s*(?:modal|cue|sensor|signal)",
    ]
    return rec


# Map each substantive extractor id to the property-KIND it PRESUPPOSES on the
# postulate's object. For the 7 regex extractors the kind IS the extractor id
# (the consequence presupposes exactly the structure the extractor recognises).
# Rule-derived / concept_graph / shape-donor kinds presuppose NO single
# structural property -> requires_property=None (set at tag time).
def _kind_requires_property(kind: str):
    if kind in {"invertibility", "parametric_allpole", "latent_structure",
                "sequence_segmentation", "scale_cancellation",
                "removable_context", "forward_inverse",
                "compositional_generativity",
                "predictive_completion", "quantize_to_categories",
                "attractor_warps_metric", "reliability_weighted_fusion",
                "discriminant_projection", "nuisance_conditioning"}:
        return kind
    return None


def tag_concept_properties(substrate, overwrite: bool = False) -> dict:
    """One-time, idempotent, graph-resident PROPERTY TAGGING (brick 4 step 1).

    For EVERY Concept, apply the agent's property-KIND vocabulary
    (_property_recognisers — the 7 extractors' own recognisers + the bare
    structural markers of each property) to the concept's FULL text (name +
    definition + why). Record the set of structural property-KINDs the concept
    EXHIBITS as graph data:
      • a `property_kinds` attr on the Concept node = json-serialisable list, AND
      • one `ConceptProperty` node per (concept, kind) with an `exhibits` edge,
        so the tagging is queryable as graph structure (not only an attr blob).

    Idempotent: a Concept already carrying a `property_kinds` attr is skipped
    unless overwrite=True. Returns an accounting dict {n_concepts, n_tagged,
    kind_distribution, examples} for honest reporting.

    A concept whose text presupposes NO structural property (folklore like
    "MQTT outperforms HTTP for IoT") matches no recogniser and is tagged with the
    EMPTY set — recorded explicitly (property_kinds=[]) so the relevance path can
    distinguish "tagged, exhibits nothing" from "not yet tagged"."""
    recs = _property_recognisers()
    compiled = {k: [re.compile(p) for p in pats] for k, pats in recs.items()}
    n_concepts = 0
    n_tagged = 0
    dist: dict = {}
    examples: dict = {}
    for c in substrate.nodes("Concept"):
        n_concepts += 1
        a = substrate.node(c)["attrs"]
        if not overwrite and a.get("property_kinds") is not None:
            # already tagged — fold its existing tags into the report.
            for k in (a.get("property_kinds") or []):
                dist[k] = dist.get(k, 0) + 1
            if a.get("property_kinds"):
                n_tagged += 1
            continue
        name, body, _origin = _concept_text(substrate, c)
        text = f"{name} {body}".lower()
        kinds = []
        for k, pats in compiled.items():
            if any(p.search(text) for p in pats):
                kinds.append(k)
        # write-through the attr (list) — the graph is source of truth. Stored
        # as a tuple by the backend; concept_property_kinds reads it back as a
        # set. An empty list round-trips to () (falsy but NOT None) so the
        # "tagged-but-exhibits-nothing" state stays distinct from "untagged".
        try:
            substrate.set_attr(c, "property_kinds", kinds)
        except Exception:
            try:
                substrate.node(c)["attrs"]["property_kinds"] = kinds
            except Exception:
                pass
        # one ConceptProperty node per kind (queryable graph structure).
        for k in kinds:
            try:
                pn = substrate.add_node("ConceptProperty",
                                        {"kind": k, "of_concept": name})
                substrate.add_edge(c, "exhibits", pn, {})
            except Exception:
                pass
            dist[k] = dist.get(k, 0) + 1
            if k not in examples and name:
                examples[k] = name
        if kinds:
            n_tagged += 1
    return {"n_concepts": n_concepts, "n_tagged": n_tagged,
            "kind_distribution": dist, "examples": examples}


def concept_property_kinds(substrate, concept_nid) -> set:
    """The set of structural property-KINDs a Concept node EXHIBITS, read from
    its `property_kinds` attr (populated by tag_concept_properties). Empty set if
    the concept was tagged-but-exhibits-nothing OR has not been tagged."""
    if concept_nid is None:
        return set()
    try:
        a = substrate.node(concept_nid)["attrs"]
    except Exception:
        return set()
    pk = a.get("property_kinds")
    if pk is None:
        return set()
    return set(pk)


# ---------------------------------------------------------------------------
# The HARVEST — read the agent's concepts, abstract the implication-shapes.
# ---------------------------------------------------------------------------


def _concept_text(substrate, cid) -> tuple[str, str, str]:
    a = substrate.node(cid)["attrs"]
    name = str(a.get("name", "") or "")
    body = f"{a.get('definition', '')} {a.get('why', '')}".strip()
    origin = str(a.get("expansion_pack") or a.get("from_world")
                 or a.get("origin", "") or "?")
    return name, body, origin


def _domain_of(origin: str) -> str:
    """A readable domain label for provenance, from a concept's origin/pack."""
    o = origin.lower()
    for key, dom in (("linear_algebra", "linear_algebra"),
                     ("signal_processing", "signal_processing"),
                     ("probability_statistics", "statistics"),
                     ("calculus", "calculus"),
                     ("control_systems", "control"),
                     ("machine_learning", "machine_learning"),
                     ("attention", "machine_learning"),
                     ("optimization", "optimization"),
                     ("fluid", "physics"), ("materials", "physics")):
        if key in o:
            return dom
    # strip a trailing _decomposition for a cleaner label
    return re.sub(r"_decomposition$", "", origin) or "?"


def _owning_mt_map(substrate) -> dict:
    """concept-name / rule-name  ->  (owning_Mt_name, owning_Mt_id).

    The SUBSTANTIVE shapes (harvest_shapes / harvest_shapes_from_rules) record a
    `domain` LABEL (_domain_of, a lossy provenance string that can be '?' or a
    canonicalised non-Mt name). Brick 3 needs the source's TRUE owning Microtheory
    — the structural node that brick-2's genlMt lineage test ranges over — so the
    substantive shape can ALSO fire when its domain Mt sits in a postulate's
    Mt-lineage. This walks the graph once and maps each Concept/Rule node's name to
    the (first) Mt that has_concept/has_rule it, returning BOTH name and id so the
    lineage membership test (which carries both) works by either key.

    Returns {name: (mt_name, mt_id)}. Names not under any Mt are absent."""
    g = substrate.graph_to_dict()
    name_of = {nd["id"]: str(nd["attrs"].get("name", "") or "")
               for nd in g["nodes"]}
    out: dict = {}
    for e in g["edges"]:
        if e["type"] not in ("has_concept", "has_rule"):
            continue
        mt_id, child = e["src"], e["tgt"]
        cn = name_of.get(child, "")
        if cn and cn not in out:
            out[cn] = (name_of.get(mt_id, ""), mt_id)
    return out


def harvest_shapes(substrate, exclude_mt: str = "speech_science",
                   per_kind: int = 4) -> list:
    """Harvest implication-shapes from the agent's OWN Concepts across all its
    domains. For every concept whose text EXHIBITS a structural implication-kind
    (an extractor's evidence fires), donate a shape of that kind, tagged with the
    source concept + domain it came FROM. The speech_science Mt is EXCLUDED by
    default — those are the postulates we differentiate, not the breadth we draw
    from; the shapes must come from the agent's OTHER knowledge.

    Returns a list of shape dicts in order_n_postulates.differentiate's format:
      {name, domain, match_patterns, consequence, match_keys, name_keys,
       source_concept, kind}
    De-duplicated by implication-kind (one shape per kind, from the most
    distinctive source), with up to `per_kind` alternative sources recorded for
    honesty. The kind's TRIGGERS (when it applies) are generic; the fact that the
    agent HOLDS a concept exhibiting that kind is what licenses the shape."""
    # which Concept node-ids belong to the excluded Mt (so we draw shapes from
    # the agent's OTHER breadth, not from the postulates themselves).
    excluded = set()
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == exclude_mt:
            for c in substrate.neighbours(n, "has_concept"):
                excluded.add(c)
            for c in substrate.neighbours(n, "contains"):
                excluded.add(c)

    # source-concept name -> (owning Mt name, owning Mt id), for brick-3's
    # structural (Mt-lineage) firing of substantive shapes.
    owner = _owning_mt_map(substrate)

    extractors = _extractors()
    # kind -> list of (relevance, source_name, source_domain)
    donors: dict[str, list] = {e["id"]: [] for e in extractors}

    for c in substrate.nodes("Concept"):
        if c in excluded:
            continue
        name, body, origin = _concept_text(substrate, c)
        if not body:
            continue
        nlow = name.lower()
        text = f"{name} {body}".lower()
        for e in extractors:
            n_hits = sum(1 for p in e["evidence"] if re.search(p, text))
            if not n_hits:
                continue
            # RELEVANCE: a donor is a cleaner source of this implication-kind when
            # (a) more of the kind's evidence fires, and (b) the kind shows in the
            # concept's NAME (a concept NAMED 'IIR_filter'/'unsupervised_learning'/
            # 'regression_analysis' genuinely IS-A donor; one that merely mentions
            # the word in passing — 'causal_attention_mask', a thermodynamic
            # 'entropy', a meta-essay — is not). name_signals are structural
            # NAME-level markers of the kind; this is the agent ranking which of its
            # concepts BEST exhibits the structure, not a hand-pick of the answer.
            name_hit = any(re.search(p, nlow) for p in e.get("name_signals", []))
            relevance = n_hits + (3 if name_hit else 0)
            donors[e["id"]].append((relevance, name, _domain_of(origin)))

    shapes = []
    for e in extractors:
        ds = donors[e["id"]]
        if not ds:
            continue
        # the named source = the donor that BEST exhibits the kind (highest
        # relevance; ties broken toward the more specific term of art).
        ds_sorted = sorted(ds, key=lambda d: (-d[0], -len(d[1]), d[1]))
        _rel, src_name, src_domain = ds_sorted[0]
        src_mt_name, src_mt_id = owner.get(src_name, (src_domain, None))
        shapes.append({
            "name": f"{e['id']}__from__{src_name}",
            "kind": e["id"],
            # BRICK 4 — the structural property this shape's consequence
            # PRESUPPOSES on the postulate's object (the extractor id). The
            # relevance path fires this shape only when the postulate's tagged
            # property_kinds CONTAINS this kind.
            "requires_property": _kind_requires_property(e["id"]),
            "domain": src_domain,
            "source_concept": src_name,
            # BRICK 3: the source concept's TRUE owning Microtheory (name + id) —
            # the structural node a postulate's genlMt lineage is tested against,
            # so this SUBSTANTIVE shape can fire by STRUCTURE (its domain Mt in the
            # lineage) and transfer its real consequence, not only by text overlap.
            "source_mt": src_mt_name,
            "source_mt_id": src_mt_id,
            "alt_sources": [(n, d) for _, n, d in ds_sorted[1:per_kind]],
            "n_donors": len(ds),
            "match_patterns": list(e["triggers"]),
            "consequence": e["consequence"].format(
                src=src_name, object="the object"),
            "match_keys": list(e["match_keys"]),
            "name_keys": list(e["name_keys_for"](src_name)),
        })
    return shapes


_GENERIC_TRIGGER_STOPWORDS = {
    # Words too generic to be useful regex anchors. Drop these from
    # if_clause-derived patterns so they don't fire on every concept.
    "a", "an", "the", "is", "are", "be", "to", "of", "in", "on", "at",
    "by", "for", "from", "with", "as", "into", "via", "any", "all",
    "no", "not", "and", "or", "if", "then", "else", "this", "that",
    "these", "those", "it", "its", "must", "should", "can", "may",
    "given", "named", "exists", "has", "have",
}


def _keywords_from_clause(text: str, min_len: int = 4) -> list[str]:
    """Extract content words from a rule clause for use as match keys."""
    tokens = re.findall(r"[a-z][a-z_]+", text.lower())
    return [t for t in tokens
            if len(t) >= min_len and t not in _GENERIC_TRIGGER_STOPWORDS]


def harvest_shapes_from_rules(substrate, exclude_mt: str = "speech_science",
                                min_clause_len: int = 12) -> list:
    """Harvest implication-shapes from RULE nodes, not just Concept text.

    The substrate's Rules already declare implication structure explicitly:
    if_clauses (the structural property a postulate must exhibit for the
    rule to fire) -> then_clauses (the consequence). The text-based
    extractor pipeline (harvest_shapes) misses this entirely — it walks
    Concepts and regex-matches definition+why for one of 7 hardcoded
    implication-kinds. A substrate with 1086 rules expressing explicit
    if->then implications gets ZERO of them harvested.

    This function fills the gap: each Rule with non-trivial if_clauses
    and then_clauses becomes a candidate shape. The consequence is the
    then_clauses joined; the match condition is derived from if_clauses.

    PRECISION (the harvest is SPECIFIC AT BIRTH). A Rule's if-clause is a
    STRUCTURAL CONDITION — a conjunction of co-occurring content terms
    (e.g. "compute pattern is set_intersection_for_lookup" AND "set values
    known at design time"). The earlier version flattened that to a list of
    bare single-word regexes matched with OR semantics in differentiate(),
    so a shape fired whenever ANY ONE of its words ('\\bsubstrate\\b',
    '\\bruns\\b') appeared in a postulate — firing on ~50% of the corpus
    (babble_loop_is_thermal_sampling fired on 2861/5286). A shape that fires
    on half the substrate carries ~0 bits and unifies nothing: pure noise.

    The fix reads the Rule's antecedent FAITHFULLY: the harvested shape's
    match condition is the CONJUNCTION of ALL the if-clauses' content words
    — the shape fires on a postulate only when that whole structural
    signature CO-OCCURS, not when one fragment appears. match_patterns is
    still a list of fast per-word anchors (the lookahead-conjunction regex
    backtracks catastrophically on long meta-essay text); the AND is carried
    by match_mode='all', which differentiate() honours for rule-derived
    shapes while keeping the OR contract for the 7 regex-extractor kinds.
    Shapes whose entire antecedent reduces to a single content word are
    DROPPED — one bare token cannot discriminate, so it can't donate a
    shape. This is a GENERATION fix (the rule-walker), not a downstream
    filter: with it the promiscuous shapes never exist, so no gate is needed.

    Returned shapes use kind='rule_derived' so order_n_postulates.
    differentiate can distinguish them from the regex-extracted kind.
    The exclude_mt filter still applies — speech_science postulates
    don't donate shapes for differentiation of themselves.
    """
    # Identify excluded Mt's Rules.
    excluded_mts = set()
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == exclude_mt:
            excluded_mts.add(n)
    excluded_rules = set()
    for mt in excluded_mts:
        for r in substrate.neighbours(mt, "has_rule"):
            excluded_rules.add(r)

    # rule-name -> (owning Mt name, owning Mt id), for brick-3 structural firing.
    owner = _owning_mt_map(substrate)

    shapes = []
    for r in substrate.nodes("Rule"):
        if r in excluded_rules:
            continue
        a = substrate.node(r)["attrs"]
        rule_name = str(a.get("name", "")).strip()
        if not rule_name:
            continue
        if_clauses = a.get("if_clauses") or []
        then_clauses = a.get("then_clauses") or []
        if not if_clauses or not then_clauses:
            continue
        # Filter: skip rules with all-too-short if_clauses (likely stub
        # patterns or single-word triggers).
        ifs_clean = [str(c).strip() for c in if_clauses
                     if isinstance(c, str) and len(str(c).strip()) >= min_clause_len]
        thens_clean = [str(c).strip() for c in then_clauses
                       if isinstance(c, str) and str(c).strip()]
        if not ifs_clean or not thens_clean:
            continue
        # Build match_patterns as the CONJUNCTION of ALL the if-clauses'
        # content words — the Rule's structural antecedent, read faithfully.
        # (De-duplicate, preserve order.) A shape with this condition fires
        # only when the WHOLE signature co-occurs (match_mode='all'), so it
        # is specific at birth rather than a promiscuous single-word OR.
        kws = []
        for cl in ifs_clean:
            for k in _keywords_from_clause(cl):
                if k not in kws:
                    kws.append(k)
        # DROP a shape whose entire antecedent is one content word: a single
        # bare token cannot discriminate (it's the promiscuity source). The
        # rule-walker should not emit it at all.
        if len(kws) < 2:
            continue
        # Whole-word anchors, one per content word; the AND is in match_mode.
        # Cap the conjunction width so a runaway clause can't make the regex
        # list huge, but keep enough terms (>=2) that it stays specific.
        kw_list = kws[:8]
        match_patterns = [rf"\b{re.escape(k)}\b" for k in kw_list]
        # Consequence text: then-clauses joined.
        consequence = " AND ".join(thens_clean)
        # Domain from the rule's origin attr.
        origin = str(a.get("origin", "")) or "?"
        domain = _domain_of(origin)
        src_mt_name, src_mt_id = owner.get(rule_name, (domain, None))
        shapes.append({
            "name": f"rule_derived__{rule_name}",
            "kind": "rule_derived",
            # BRICK 4 — a rule-derived shape is domain FOLKLORE (an if->then the
            # agent declared), not one of the 7 structural property-kinds, so it
            # presupposes NO structural property on the postulate's object:
            # requires_property=None. It is therefore NOT structurally fireable by
            # the relevance path — only by its original text/rule (match_mode='all'
            # antecedent) path. This is what stops Kalman_filter inheriting
            # "MQTT outperforms HTTP" via a shared ancestor Mt.
            "requires_property": None,
            "domain": domain,
            # BRICK 3: the rule's TRUE owning Microtheory (name + id) for the
            # structural Mt-lineage firing path.
            "source_mt": src_mt_name,
            "source_mt_id": src_mt_id,
            "source_rule": rule_name,
            "source_concept": rule_name,  # also fill source_concept for
                                            # back-compat with harvest_report
                                            # which counts donors as concepts
            "alt_sources": [],
            "n_donors": 1,
            "match_patterns": match_patterns,
            # AND semantics — ALL the antecedent's words must co-occur for the
            # shape to fire (the structural condition), NOT any single one.
            # differentiate() honours this for rule_derived shapes; the 7
            # regex-extractor kinds keep their OR ('any') default.
            "match_mode": "all",
            "consequence": consequence,
            "match_keys": kw_list,
            "name_keys": _keywords_from_clause(consequence)[:8],
        })
    return shapes


# ---------------------------------------------------------------------------
# The CONCEPT-GRAPH harvest — the agent's OWN taxonomy/relation edges ARE
# implication-shapes.
#
# The 7 regex extractors + the rule-walker read TEXT (concept definitions /
# rule clauses). But the agent also holds STRUCTURE: the relation edges between
# its knowledge nodes. Every such edge `A --rel--> B` IS an implication — the
# taxonomy/relation the agent has committed asserts "framing the object as an A
# entails it is(/depends_on/refers_to) a B". Reading those edges as shapes makes
# the implication-catalogue scale with the agent's graph instead of with the ~7
# fixed extractor KINDS — the agent extending its OWN generativity from its own
# relations rather than a human stencil.
#
# EMPIRICAL NOTE (load-bearing — do not assume the textbook edge set). In the
# booted substrate the Concept->Concept relation edges the brief names
# (is_a/implies/refers_to/depends_on BETWEEN Concepts) essentially DO NOT EXIST
# (a graph dump finds 0 Concept->Concept edges, 2 refers_to total). The
# agent's taxonomy lives at the MICROTHEORY level: `genlMt` (child_Mt is-a
# parent_Mt, ~144 edges, e.g. acoustics --genlMt--> audio_music_foundation) and
# a handful of Mt `refers_to` Mt cross-references. Combined with `has_concept`
# (Mt -> its Concepts) this still gives a real, graph-resident implication per
# (concept-in-child-Mt -> parent-Mt). We harvest the relation edges the graph
# ACTUALLY has — discovered, not assumed — which is the faithful move.
# ---------------------------------------------------------------------------

# Relation edge types that encode an implication A--rel-->B, with the verb the
# edge asserts. Discovered from the live graph (genlMt + refers_to are what the
# booted substrate carries); the others are included so the harvester also picks
# up any Concept-level relations a future seed adds, without a code change.
_RELATION_EDGES = {
    "genlMt": "is-a",
    "refers_to": "refers-to",
    "is_a": "is-a",
    "subClassOf": "is-a",
    "implies": "implies",
    "depends_on": "depends-on",
    "decomposes": "decomposes-into",
}

# Domain-generic words that must NOT become a shape's distinctive anchor (they
# would make the match_patterns fire on nearly every postulate = noise).
_NONDISTINCTIVE = {
    "theory", "theories", "foundation", "foundations", "concept", "concepts",
    "system", "systems", "model", "models", "method", "methods", "analysis",
    "general", "generic", "basic", "core", "study", "field", "science",
    "sciences", "process", "processes", "structure", "structures", "approach",
    "principle", "principles", "framework", "domain", "object", "property",
    "function", "value", "values", "form", "kind", "thing", "things", "data",
    "information", "knowledge", "understanding", "abstract", "abstraction",
    # graph/meta vocabulary that recurs across the agent's OWN definitions
    # ("The substrate's foundational vocabulary for ...") — a hub word, not a
    # distinctive topic anchor, so it must not become a shape's anchor.
    "substrate", "vocabulary", "foundational", "agent", "graph", "node",
    "nodes", "edge", "edges", "rule", "rules", "microtheory", "names", "term",
}


def _distinctive_terms(name: str, bodies: list[str], cap: int = 6) -> list[str]:
    """The distinctive identifying terms for a node: tokens of its NAME plus the
    most frequent non-generic nouns across the supplied definition bodies. Used to
    build a shape's anchor (so it fires only when a postulate frames its object as
    THIS thing, not on everything)."""
    from collections import Counter
    terms: list[str] = []
    seen = set()
    # name tokens FIRST — the most distinctive identifier of the node, and the
    # only ones guaranteed not to be parent-definition bleed.
    for t in re.split(r"[\s_/-]+", str(name).lower()):
        t = t.strip()
        if (len(t) >= 4 and t not in _NONDISTINCTIVE
                and t not in _GENERIC_TRIGGER_STOPWORDS and t not in seen):
            terms.append(t)
            seen.add(t)
    # Fall back to frequent definition nouns ONLY if the name alone is too thin
    # (<2 distinctive tokens) — otherwise the definition (often quoting the
    # parent's "vocabulary for ...") leaks generic/contaminated tokens in as the
    # second anchor. Word-boundaried so tokens are never sliced mid-word.
    if len(terms) < 2:
        counts: "Counter[str]" = Counter()
        for body in bodies:
            for tok in re.findall(r"\b[a-z]{4,}\b", str(body).lower()):
                if (tok not in _NONDISTINCTIVE
                        and tok not in _GENERIC_TRIGGER_STOPWORDS):
                    counts[tok] += 1
        for tok, _c in counts.most_common():
            if tok not in seen:
                terms.append(tok)
                seen.add(tok)
            if len(terms) >= cap:
                break
    return terms[:cap]


def harvest_shapes_from_concept_graph(substrate,
                                      exclude_mt: str = "speech_science",
                                      per_concept_fanout: int = 2,
                                      max_shapes: int = 400) -> list:
    """Harvest implication-shapes from the agent's OWN structural RELATION edges
    (its taxonomy), not from concept/rule TEXT. Every relation edge `A --rel--> B`
    (rel in _RELATION_EDGES — discovered from the live graph: genlMt, refers_to,
    ...) IS an implication: framing the object as an A entails it is/depends-on/
    refers-to a B. The harvested shape:

      * match_patterns: loose anchors from A's DISTINCTIVE terms — "when a
        postulate frames its object as an A". Conjunctive (match_mode='all') over
        A's two most distinctive terms so the shape stays SPECIFIC (a single hub
        term must not fire it on everything).
      * consequence: "<object framed as A> <verb> B — <gist of B>", the structural
        implication the taxonomy edge asserts.
      * match_keys: B's distinctive terms (so order-2 recurses onto B).
      * name_keys: A's distinctive terms (the capability/topic the consequence
        names, for the selector's coverage check). Provenance: source_edge=(A,rel,B).

    Because the agent's taxonomy lives at the MICROTHEORY level (genlMt over Mts,
    has_concept Mt->Concept), a genlMt/refers_to edge between Mts is lifted per
    relation: A is the child Mt (anchored by its name + its concepts' nouns), B is
    the parent Mt. We cap fan-out per source node so a hub parent can't flood the
    catalogue, dedupe (A,rel,B), skip self-loops and nodes lacking distinctive
    terms, and bound the total. The exclude_mt filter still applies — the
    postulates we differentiate don't donate shapes for differentiating themselves.

    Returns shape dicts in differentiate()'s format with kind='concept_graph'."""
    g = substrate.graph_to_dict()
    nodes = {nd["id"]: nd for nd in g["nodes"]}
    name_of = {nid: str(nd["attrs"].get("name", "") or "")
               for nid, nd in nodes.items()}

    # Map each Mt -> its concept definition bodies (for distinctive nouns) and
    # find the excluded Mt's node-id so we drop edges sourced from it.
    excluded_ids = set()
    mt_bodies: dict[int, list[str]] = {}
    for e in g["edges"]:
        if e["type"] != "has_concept":
            continue
        mt, c = e["src"], e["tgt"]
        cn = nodes.get(c)
        if cn is None:
            continue
        a = cn["attrs"]
        body = f"{a.get('definition', '')} {a.get('why', '')}".strip()
        if body:
            mt_bodies.setdefault(mt, []).append(body)
    for nid, nd in nodes.items():
        if nd["type"] == "Microtheory" and nd["attrs"].get("name") == exclude_mt:
            excluded_ids.add(nid)

    def terms_for(nid: str) -> list[str]:
        nd = nodes.get(nid)
        if nd is None:
            return []
        a = nd["attrs"]
        bodies = mt_bodies.get(nid) or []
        own = f"{a.get('definition', '')} {a.get('why', '')}".strip()
        if own:
            bodies = bodies + [own]
        return _distinctive_terms(name_of.get(nid, ""), bodies)

    # --- BRICK 2 PROMISCUITY GATE -------------------------------------------
    # A `source_mt` A that is a FOUNDATION / near-root Mt (huge subtree) would,
    # under the structural mt_lineage match, fire on almost every postulate that
    # lives anywhere beneath it = noise (a structural match that fires on
    # everything under a broad Mt carries ~0 bits, exactly like the text-path's
    # promiscuous single-word OR). Compute each Mt's genlMt SUBTREE size (how
    # many Mts descend from it, transitively) and drop the top ~15% — the broad
    # hubs (`*_foundation`, computer_architecture, neuroscience, ...). Only
    # SPECIFIC source Mts (small/leaf subtrees) survive. The gate is over the
    # genlMt taxonomy the agent ACTUALLY holds, computed here, not hand-listed.
    _children: dict = {}
    for e in g["edges"]:
        if e["type"] == "genlMt":          # child --genlMt--> parent
            _children.setdefault(e["tgt"], []).append(e["src"])

    def _subtree_size(m) -> int:
        seen, stack = set(), list(_children.get(m, []))
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(_children.get(x, []))
        return len(seen)

    _mt_ids = [nid for nid, nd in nodes.items() if nd["type"] == "Microtheory"]
    _sizes = {m: _subtree_size(m) for m in _mt_ids}
    # rank Mts by descendant count; the top FRACTION (default 15%) are the broad
    # hubs whose lineage fires on too much — gate them out as promiscuous.
    promiscuity_top_frac = 0.15
    _ranked = sorted(_sizes.values(), reverse=True)
    if _ranked:
        cut_idx = max(0, int(len(_ranked) * promiscuity_top_frac) - 1)
        # an Mt is BROAD if its subtree is at least as large as the cutoff rank's
        # size (and it actually has descendants — leaves are never broad).
        cut_size = _ranked[cut_idx]
    else:
        cut_size = 10 ** 9
    broad_mts = {m for m, sz in _sizes.items() if sz > 0 and sz >= cut_size}
    # expose what the gate dropped for the measurement script (honest reporting).
    gate_info = {
        "promiscuity_top_frac": promiscuity_top_frac,
        "cut_subtree_size": cut_size,
        "n_broad_mts": len(broad_mts),
        "broad_mt_names": sorted(name_of.get(m, str(m)) for m in broad_mts),
        "dropped_shapes": 0,
    }

    shapes: list = []
    seen_edges: set = set()
    fanout: "Counter" = __import__("collections").Counter()
    for e in g["edges"]:
        rel = e["type"]
        verb = _RELATION_EDGES.get(rel)
        if verb is None:
            continue
        a_id, b_id = e["src"], e["tgt"]
        if a_id == b_id:                       # skip self-loops
            continue
        if a_id in excluded_ids or b_id in excluded_ids:
            continue
        # PROMISCUITY GATE: drop shapes whose source Mt A is a broad / near-root
        # hub — its mt_lineage match would fire on nearly everything beneath it.
        if a_id in broad_mts:
            gate_info["dropped_shapes"] += 1
            continue
        key = (a_id, rel, b_id)
        if key in seen_edges:                  # dedupe
            continue
        if fanout[a_id] >= per_concept_fanout:  # cap per-source fan-out
            continue
        a_name, b_name = name_of.get(a_id, ""), name_of.get(b_id, "")
        a_terms, b_terms = terms_for(a_id), terms_for(b_id)
        # skip edges whose endpoints lack distinctive terms (junk control).
        if len(a_terms) < 2 or not b_terms:
            continue
        seen_edges.add(key)
        fanout[a_id] += 1
        # anchor on A's two most distinctive terms, conjunctively (specific).
        anchors = a_terms[:2]
        match_patterns = [rf"\b{re.escape(t)}\b" for t in anchors]
        # a short gist of B from its definition, if any.
        b_node = nodes.get(b_id, {})
        b_def = str(b_node.get("attrs", {}).get("definition", "") or "")
        b_gist = " ".join(b_def.split()[:14])
        consequence = (
            f"an object framed as '{a_name or '/'.join(a_terms[:2])}' "
            f"{verb} '{b_name or '/'.join(b_terms[:2])}'"
            + (f" — {b_gist}" if b_gist else ""))
        shapes.append({
            "name": f"concept_graph__{a_name or a_id}__{rel}__{b_name or b_id}",
            "kind": "concept_graph",
            "domain": _domain_of(str(nodes.get(a_id, {}).get("attrs", {})
                                    .get("origin", "")) or a_name or "?"),
            "source_concept": a_name or str(a_id),
            "source_edge": (a_name, rel, b_name),
            "alt_sources": [],
            "n_donors": 1,
            # --- BRICK 2: STRUCTURAL match by Mt-lineage membership. ----------
            # The taxonomy edge `A --rel--> B` is an implication "framing the
            # object as an A entails B". Brick 1 tried to detect "the object IS
            # an A" by TEXT-matching A's name tokens against the postulate's
            # PROSE — the wrong join (the agent's taxonomy lives at the Mt level,
            # whose domain-NAME tokens do not appear in a postulate's definition).
            # The RIGHT join is GRAPH STRUCTURE: a postulate's concept sits under
            # A in the genlMt lineage iff A IS the source Mt of that concept's
            # owning Mt (or an ancestor of it). So we tag the shape with the
            # STRUCTURE it should fire on — match_kind='mt_lineage' + source_mt=A
            # (the child Mt's id and name) — and differentiate() walks the
            # postulate's genlMt lineage instead of regexing the prose.
            "match_kind": "mt_lineage",
            "source_mt": a_name or str(a_id),
            "source_mt_id": a_id,
            # AND over A's anchors — fires only when the WHOLE (small) signature
            # co-occurs, so it is SPECIFIC at birth, not a promiscuous OR.
            # (kept for the legacy TEXT path / back-compat; the structural path
            # uses match_kind above.)
            "match_mode": "all",
            "match_patterns": match_patterns,
            "consequence": consequence,
            "match_keys": list(b_terms[:6]),
            "name_keys": list(a_terms[:6]),
        })
        if len(shapes) >= max_shapes:
            break
    # Stash the gate accounting on the list object so the measurement script can
    # report what the promiscuity gate dropped, without changing the return type
    # (callers iterate the list; the attribute is opt-in).
    try:
        shapes_obj = list(shapes)

        class _ShapeList(list):
            pass
        shapes_obj = _ShapeList(shapes)
        shapes_obj.gate_info = gate_info
        return shapes_obj
    except Exception:
        return shapes


def harvest_shapes_combined(substrate, exclude_mt: str = "speech_science",
                            include_concept_graph: bool = False) -> list:
    """Both Concept-text extractors AND Rule-structured if->then shapes,
    AND the Shape-lifted donors (per Jabberwock's change 3 — Shape-aware
    path surfaced as primary). The 7 regex extractors handle classic
    property->consequence patterns (invertibility, latent_structure,
    etc.); the rule walker handles every rule the substrate has declared
    with explicit if/then; the Shape-lifted donors fire on structural
    compatibility (recursion/order_n/abstraction) instead of text
    overlap — biasing for grounded Term-trees rather than against them.
    The combined output is the agent's full implication-shape catalogue.

    `include_concept_graph` (default False — additive + TOGGLEABLE so the
    generativity measurement can compare with/without) adds
    harvest_shapes_from_concept_graph: shapes lifted from the agent's OWN
    structural relation edges (its genlMt/refers_to taxonomy). Off by default so
    existing callers/tests see the unchanged catalogue; the measurement script
    turns it on."""
    out = (harvest_shapes(substrate, exclude_mt=exclude_mt)
           + harvest_shapes_from_rules(substrate, exclude_mt=exclude_mt))
    try:
        from .harvester_shape import harvest_shape_donors_compatible
        out = out + harvest_shape_donors_compatible(substrate)
    except Exception:
        pass
    if include_concept_graph:
        try:
            out = out + harvest_shapes_from_concept_graph(
                substrate, exclude_mt=exclude_mt)
        except Exception:
            pass
    return out


def harvest_report(substrate, exclude_mt: str = "speech_science") -> dict:
    """An honest accounting of a harvest: how many shapes, from how many concepts,
    across how many domains; the donor lists per kind. For the demo / docs."""
    shapes = harvest_shapes_combined(substrate, exclude_mt=exclude_mt)
    domains = {s["domain"] for s in shapes}
    for s in shapes:
        domains |= {d for _, d in s.get("alt_sources", [])}
    n_concepts = sum(s.get("n_donors", 1) for s in shapes)
    return {
        "n_shapes": len(shapes),
        "n_kinds": len({s["kind"] for s in shapes}),
        "n_donor_concepts": n_concepts,
        "n_domains": len(domains),
        "domains": sorted(domains),
        "shapes": shapes,
    }


__all__ = ["harvest_shapes", "harvest_shapes_from_rules",
            "harvest_shapes_from_concept_graph",
            "harvest_shapes_combined", "harvest_report"]
