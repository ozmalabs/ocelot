"""ARC 6 — mechanically-importable canonical sources: impedance measurement.

Answers, before anything is built: which canonical sources for advanced
mathematics/algorithms can be WALKED BY A SCRIPT (not hand-authored one
paper at a time), and what is the IMPEDANCE between each source's own
representation and this substrate's (in-frame == integer/rational/exact;
non-integer structure is cross-frame, living in a MAP applied
intensionally -- CLAUDE.md's frame/continuum invariant; and the program-
synthesis engine's `ProgEval` oracle table (`prog_eval.rs`) is explicit
that CallExtern is evaluated ONLY against a DECLARED, IN-PROCESS oracle
Dict -- "NO shelling out, ever").

THREE SEPARATE IMPORT PROBLEMS, kept separate throughout (conflating them
is the named error to avoid):
  A. KERNELS   -- computational functions registerable as ProgEval oracles.
  B. PROPERTIES/THEOREMS -- checkable assertions for Seam D.
  C. TASK->SOLUTION CONTENT -- OEIS / Rosetta Code. Flagged CONTENT: any
     import here is a preregistered bet, per the project's own six nulled
     content bets, not an assumption.

No engine/seed/adapter source is touched. This script only reads the
local repo (read-only), the network (public, read-only fetches of
canonical open sources), and writes exactly one artifact:
`results/arc6_import_impedance.json`.

Network sources fetched live, mechanically, in this run:
  - SymPy (installed, in-process): walked via `inspect`, invoked on
    canonical small-int argsets, RESULT TYPE classified exact/inexact.
  - mpmath (installed, in-process): spot-checked the same way (contrast).
  - Metamath set.mm (downloaded from GitHub, CC0): 47,625 $p theorem
    statements parsed by regex; ~2000 sampled, classified by CONFIRMED
    class-symbol tokens (grepped from the file's own "$a class TOK $."
    declarations -- not guessed) into real/complex-analysis (cross-frame)
    vs integer/finite (in-frame) vs domain-free logic.
  - Lean mathlib4 (GitHub API + raw fetch, Apache-2.0): full repo file
    tree (8302 .lean files) for the directory-level structural split,
    plus a random sample of files' theorem/lemma signatures classified
    by type token (ℝ/ℂ/... vs ℕ/ℤ/Finset/...).
  - Isabelle AFP topics page (isa-afp.org, BSD/LGPL): live-parsed topic
    taxonomy with entry counts, as published by the source itself.
  - Rosetta Code (rosettacode.org, GNU FDL 1.3): one task page fetched,
    per-language section count extracted, as a live demonstration of
    "one task, many surfaces" -- flagged CONTENT throughout.
  - GitHub license metadata for FLINT / GAP (api.github.com) -- PARI/GP's
    GPL-2.0 status is corroborated via a public mirror (no canonical
    pari-gp/pari repo exists on GitHub; upstream is a Bitbucket/hg host).

PyPI availability (installability, NOT installed -- installing packages
into the shared environment is outside this task's file-ownership scope)
checked via `pip index versions`.
"""
from __future__ import annotations

import inspect
import itertools
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import urllib.request
import warnings
from collections import Counter
from fractions import Fraction

warnings.filterwarnings("ignore")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(tempfile.gettempdir(), "arc6_import_impedance_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _curl(url, dest=None, timeout=30):
    args = ["curl", "-sL", "-m", str(timeout), "-A", "Mozilla/5.0 arc6-probe"]
    if dest:
        args += ["-o", dest]
        args += ["-w", "%{http_code}"]
        r = subprocess.run(args + [url], capture_output=True, text=True)
        return r.stdout.strip()
    else:
        r = subprocess.run(args + [url], capture_output=True, text=True)
        return r.stdout


def _github_license(owner_repo):
    try:
        out = _curl(f"https://api.github.com/repos/{owner_repo}")
        d = json.loads(out)
        lic = d.get("license") or {}
        return {
            "spdx_id": lic.get("spdx_id"), "name": lic.get("name"),
            "size_kb": d.get("size"), "stars": d.get("stargazers_count"),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# PROBLEM A (kernels) -- SymPy live walk
# ---------------------------------------------------------------------------

def probe_sympy():
    import sympy
    from sympy import Integer, Rational
    import mpmath

    modnames = [
        "sympy.ntheory", "sympy.ntheory.generate", "sympy.ntheory.factor_",
        "sympy.ntheory.primetest", "sympy.ntheory.residue_ntheory",
        "sympy.ntheory.partitions_", "sympy.ntheory.continued_fraction",
        "sympy.ntheory.multinomial",
        "sympy.functions.combinatorial.numbers",
        "sympy.functions.combinatorial.factorials",
        "sympy.combinatorics.partitions",
    ]
    mods = {}
    for m in modnames:
        mods[m] = __import__(m, fromlist=["x"])

    trial_argsets = [(12,), (2, 3), (10, 3), (2, 3, 5), (5,), (7, 2)]

    class _Timeout(Exception):
        pass

    def _handler(signum, frame):
        raise _Timeout()

    signal.signal(signal.SIGALRM, _handler)

    def call_with_timeout(obj, args, seconds=2):
        signal.alarm(seconds)
        try:
            return obj(*args)
        finally:
            signal.alarm(0)

    def is_exact(v, depth=0):
        if isinstance(v, bool):
            return True  # a decidable predicate over integers is in-frame
        if isinstance(v, int):
            return True
        if isinstance(v, (Integer, Rational, sympy.core.numbers.Rational)):
            return True
        if isinstance(v, Fraction):
            return True
        if isinstance(v, (float, complex)):
            return False
        if isinstance(v, sympy.core.numbers.Float):
            return False
        if isinstance(v, (mpmath.mpf, mpmath.mpc)):
            return False
        if depth < 2 and isinstance(v, (list, tuple, set, frozenset)):
            items = list(v)[:8]
            if not items:
                return None
            sub = [is_exact(x, depth + 1) for x in items]
            if all(s is True for s in sub):
                return True
            if any(s is False for s in sub):
                return False
            return None
        if depth < 2 and isinstance(v, dict):
            items = list(v.items())[:8]
            if not items:
                return None
            sub = [is_exact(k, depth + 1) and is_exact(val, depth + 1) for k, val in items]
            return True if all(sub) else None
        if depth < 2 and inspect.isgenerator(v):
            try:
                items = list(itertools.islice(v, 8))
            except Exception:
                return None
            return is_exact(items, depth + 1)
        return None

    rows = []
    seen = set()
    for modname, mod in mods.items():
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if not (inspect.isfunction(obj) or inspect.isbuiltin(obj)):
                continue
            mod_of_obj = getattr(obj, "__module__", "") or ""
            if not mod_of_obj.startswith("sympy"):
                continue
            key = (mod_of_obj, name)
            if key in seen:
                continue
            seen.add(key)
            try:
                sig = str(inspect.signature(obj))
            except (TypeError, ValueError):
                sig = "?"
            result_type = None
            exact = None
            called_with = None
            for args in trial_argsets:
                try:
                    v = call_with_timeout(obj, args, seconds=2)
                    result_type = type(v).__name__
                    exact = is_exact(v)
                    called_with = args
                    break
                except _Timeout:
                    continue
                except Exception:
                    continue
            rows.append({
                "module": mod_of_obj, "name": name, "signature": sig,
                "called_with": called_with, "result_type": result_type, "exact": exact,
            })

    n_total = len(rows)
    n_called = sum(1 for r in rows if r["called_with"] is not None)
    n_exact_true = sum(1 for r in rows if r["exact"] is True)
    n_exact_false = sum(1 for r in rows if r["exact"] is False)

    # mpmath contrast spot-check: same mechanism, architecturally-float library.
    mpmath_rows = []
    for name in ["sqrt", "exp", "factorial", "gamma", "pi", "log", "sin"]:
        f = getattr(mpmath, name, None)
        if f is None:
            continue
        try:
            if name == "pi":
                v = mpmath.pi
            else:
                v = call_with_timeout(f, (2,), seconds=2)
            mpmath_rows.append({"name": name, "result_type": type(v).__name__,
                                 "is_mpf_or_mpc": isinstance(v, (mpmath.mpf, mpmath.mpc))})
        except Exception as e:
            mpmath_rows.append({"name": name, "error": str(e)})

    return {
        "total_walked": n_total,
        "invoked_ok": n_called,
        "exact_true": n_exact_true,
        "exact_false": n_exact_false,
        "exact_unknown": n_called - n_exact_true - n_exact_false,
        "not_invoked_needs_bespoke_args": n_total - n_called,
        "sample_exact_kernels": [r["name"] for r in rows if r["exact"] is True][:25],
        "sample_unclassified": [r["name"] for r in rows if r["called_with"] and r["exact"] is None][:15],
        "mpmath_contrast_spotcheck": mpmath_rows,
        "sympy_version": sympy.__version__,
        "mpmath_version": mpmath.__version__,
    }


# ---------------------------------------------------------------------------
# PROBLEM B (properties/theorems) -- Metamath set.mm live sample
# ---------------------------------------------------------------------------

MM_URL = "https://raw.githubusercontent.com/metamath/set.mm/develop/set.mm"
MM_LICENSE_URL = "https://raw.githubusercontent.com/metamath/set.mm/develop/LICENSE"


def probe_metamath():
    cache = os.path.join(CACHE_DIR, "set.mm")
    if not os.path.exists(cache) or os.path.getsize(cache) < 10_000_000:
        try:
            urllib.request.urlretrieve(MM_URL, cache)
        except Exception as e:
            return {"error": f"download failed: {e}"}

    with open(cache, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    size_bytes = os.path.getsize(cache)

    lic = _curl(MM_LICENSE_URL)
    license_id = "CC0-1.0" if "CC0" in lic else "unknown (fetch failed or format changed)"

    pat = re.compile(r'\n\s*(\S+)\s+\$p\s+(.*?)\$=', re.DOTALL)
    raw_matches = pat.findall(text)
    # Two lines in the file's OWN header comment (documenting the $p syntax,
    # e.g. "<label> $p <symbollist> $= <proof> $.") match this regex but are
    # not real theorems -- a real Metamath label never contains "<"/">".
    matches = [(l, b) for (l, b) in raw_matches if "<" not in l and ">" not in l]
    doc_artifacts = len(raw_matches) - len(matches)
    total = len(matches)

    # Every token below was CONFIRMED live by grepping set.mm's own
    # "$a class <TOK> $." declarations (cr/cc/cxr/csqrt/ctopon/ccn/cmopn/
    # cds/cn0/cz/cfa/cdv/cli + df-sin/df-cos/df-tan/df-exp/df-log/df-pi/
    # df-itg) -- NOT guessed. A first pass used bare "D" and "pi" as
    # analysis markers and found "D" colliding with the generic 4th
    # class-metavariable (A,B,C,D,...); rejected once found, replaced with
    # the CONFIRMED tokens "_D" (derivative) and "_pi".
    real_tokens = {
        "RR", "CC", "RR*", "RRfld", "CCfld",
        "sin", "cos", "tan", "_e", "_pi", "log", "exp", "sqrt",
        "~~>", "S.", "S.1", "S.2", "_D",
        "TopOn", "Cn", "MetOpen", "dist",
    }
    int_tokens = {"NN", "NN0", "ZZ", "ZZ>=", "Fin", "Word", "#", "Prime", "..^", "...", "!"}

    def classify(tokens_str):
        toks = set(tokens_str.split())
        real_hit = toks & real_tokens
        int_hit = toks & int_tokens
        if real_hit:
            return "real_analysis_crossframe", real_hit
        if int_hit:
            return "integer_finite_inframe", int_hit
        return "domain_free_logic", set()

    import random
    random.seed(42)
    n_sample = 2000
    if total <= n_sample:
        sample_idx = list(range(total))
    else:
        stride = total / n_sample
        sample_idx = [int(i * stride) for i in range(n_sample)]

    counts = Counter()
    examples = {"real_analysis_crossframe": [], "integer_finite_inframe": [], "domain_free_logic": []}
    for idx in sample_idx:
        label, body = matches[idx]
        cls, hit = classify(body)
        counts[cls] += 1
        if len(examples[cls]) < 4:
            examples[cls].append({"label": label, "trigger": sorted(hit),
                                   "body_excerpt": " ".join(body.split())[:150]})

    return {
        "license": license_id,
        "size_bytes": size_bytes,
        "total_p_theorem_statements": total,
        "doc_header_artifacts_excluded": doc_artifacts,
        "sampled": len(sample_idx),
        "classification_counts": dict(counts),
        "classification_pct": {k: round(100 * v / len(sample_idx), 2) for k, v in counts.items()},
        "examples": examples,
        "note": ("'domain_free_logic' is pure propositional/set-theoretic identity "
                 "(no numeric-domain token at all, e.g. modus-ponens variants) -- "
                 "trivially in-frame as symbol manipulation but NOT itself useful "
                 "program-property content; the useful Seam-D-relevant fraction is "
                 "the smaller 'integer_finite_inframe' slice (divisibility, "
                 "primality, factorial/Bell-number identities, finite-set facts)."),
    }


# ---------------------------------------------------------------------------
# PROBLEM B (properties/theorems) -- Lean mathlib4 structural + sampled probe
# ---------------------------------------------------------------------------

def probe_mathlib4(sample_n=25):
    lic = _github_license("leanprover-community/mathlib4")

    tree_json = _curl("https://api.github.com/repos/leanprover-community/mathlib4/git/trees/master?recursive=1")
    try:
        tree = json.loads(tree_json)
    except Exception as e:
        return {"license": lic, "error": f"tree fetch failed: {e}"}

    lean_files = [t["path"] for t in tree.get("tree", [])
                  if t["path"].startswith("Mathlib/") and t["path"].endswith(".lean")]
    dir_counts = Counter(p.split("/")[1] for p in lean_files)

    # A coarse, HONEST (not authoritative) split of the top-level directories
    # into continuous/analytic (cross-frame) vs discrete/finite (in-frame)
    # vs mixed/abstract (genuinely undetermined until instantiated -- the
    # sampled probe below measures this third bucket directly instead of
    # guessing it away).
    cross_frame_dirs = {"Analysis", "Topology", "MeasureTheory", "Probability",
                         "Dynamics", "AlgebraicGeometry", "Geometry"}
    in_frame_dirs = {"Data", "NumberTheory", "Combinatorics", "Computability",
                      "Logic", "SetTheory", "Order", "Control"}
    dir_split = {"cross_frame_dirs_files": sum(dir_counts[d] for d in cross_frame_dirs),
                 "in_frame_dirs_files": sum(dir_counts[d] for d in in_frame_dirs),
                 "abstract_or_mixed_dirs_files": sum(v for k, v in dir_counts.items()
                                                      if k not in cross_frame_dirs and k not in in_frame_dirs),
                 "total_files": len(lean_files)}

    import random
    random.seed(7)
    sample = random.sample(lean_files, min(sample_n, len(lean_files)))

    real_tokens = ["ℝ", "ℂ", "NNReal", "ENNReal", "Real.", "Complex.", "MeasureTheory",
                   "TopologicalSpace", "Filter.Tendsto", "deriv ", "∫", "Continuous",
                   "IsOpen", "MetricSpace"]
    int_tokens = ["ℕ", "ℤ", "Finset", "Fintype", "Nat.", "Int.", "List ", "Multiset",
                  "ZMod", "Fin ", "DecidableEq"]

    rows = []
    for path in sample:
        url = f"https://raw.githubusercontent.com/leanprover-community/mathlib4/master/{path}"
        content = _curl(url, timeout=12)
        if not content:
            rows.append({"path": path, "error": "empty_fetch"})
            continue
        starts = [m.start() for m in re.finditer(
            r'^\s*(?:@\[[^\]]*\]\s*)?(?:protected |private |noncomputable )*(theorem|lemma)\s',
            content, re.MULTILINE)]
        chunks = []
        for s in starts:
            window = content[s:s + 400]
            cut = window.find(":=")
            chunks.append(window[:cut] if cut != -1 else window)
        sig_text = "\n".join(chunks)
        has_real = any(tok in sig_text for tok in real_tokens)
        has_int = any(tok in sig_text for tok in int_tokens)
        if has_real and not has_int:
            cls = "real_analysis_crossframe"
        elif has_int and not has_real:
            cls = "integer_finite_inframe"
        elif has_real and has_int:
            cls = "mixed"
        elif starts:
            cls = "abstract_generic_undetermined"  # theorems exist but are type-class polymorphic
        else:
            cls = "no_theorem_lemma_in_file"
        rows.append({"path": path, "n_decls": len(starts), "class": cls})

    counts = Counter(r.get("class", "error") for r in rows)
    return {
        "license": lic,
        "directory_file_counts": dict(dir_counts),
        "directory_split": dir_split,
        "sampled_files": len(sample),
        "sampled_signature_classification": dict(counts),
        "sample_rows": rows,
        "note": ("A large 'abstract_generic_undetermined' bucket is itself the "
                 "finding: much of mathlib4's mass is type-class-polymorphic "
                 "(theorems over an arbitrary CommRing/Module/Category), which is "
                 "a THIRD impedance axis beyond real-vs-integer -- dependent type "
                 "theory + typeclass abstraction is a structurally different "
                 "representation from this substrate regardless of numeric domain."),
    }


# ---------------------------------------------------------------------------
# PROBLEM B (properties/theorems) -- Isabelle AFP topic taxonomy (live)
# ---------------------------------------------------------------------------

def probe_afp():
    html = _curl("https://www.isa-afp.org/topics/")
    topic_counts = {}
    # NOTE: the leaf-topic label sits on its own line inside <a href=...>\n  Name (N)\n</a>
    # (whitespace between the '>' and the label, and between "(N)" and "</a>") --
    # a first pass without \s* on both sides silently matched only the 4 top-level
    # H2 headings (whose "(N)" is single-line and counts SUBCATEGORIES, not entries)
    # and returned 0 for every leaf; found and fixed before trusting the output.
    for m in re.finditer(r'>\s*([A-Za-z][A-Za-z0-9 /\'.-]*?)\s*\((\d+)\)\s*</a>', html):
        topic_counts[m.group(1).strip()] = int(m.group(2))
    algo_like = sum(topic_counts.get(k, 0) for k in
                    ["Algorithms", "Data structures", "Automata and formal languages"])
    discrete_math = sum(topic_counts.get(k, 0) for k in
                         ["Number theory", "Combinatorics", "Graph theory", "Order"])
    continuous_math = sum(topic_counts.get(k, 0) for k in
                           ["Analysis", "Measure and integration", "Topology", "Probability theory"])
    return {
        "license": "BSD-style OR GNU LGPL (author's choice per entry; both permissive) "
                    "-- confirmed via isa-afp.org/about, not assumed",
        "total_entries_per_source_stats_page": 1012,
        "total_authors_per_source_stats_page": 604,
        "total_lemmas_per_source_stats_page": "~323,000",
        "note_on_stats_page": ("the /statistics/ page renders its headline numbers "
                                "via client-side JS; a plain curl (used for everything "
                                "else in this script) got an empty body there. Those "
                                "three numbers were read via a full-render fetch this "
                                "session and are reported as sourced, not script-verified."),
        "topic_taxonomy_live_parsed": topic_counts,
        "algorithms_and_data_structures_entries": algo_like,
        "discrete_math_entries": discrete_math,
        "continuous_math_entries": continuous_math,
        "note": ("topic counts are the SOURCE'S OWN classification (its topics "
                 "taxonomy page), parsed live by this script -- entries may carry "
                 "more than one topic, so the leaf counts can sum to more than "
                 "1,012. A few leaf names repeat under different parents (e.g. a "
                 "'Geometry' subtopic under Computer science AND the real "
                 "'Geometry' under Mathematics) and collapse to the last-seen "
                 "value in this flat dict -- the specific names summed above "
                 "(Algorithms/Data structures/Number theory/Analysis/...) are "
                 "each unambiguous."),
    }


# ---------------------------------------------------------------------------
# PROBLEM C (content) -- OEIS (already integrated) + Rosetta Code (live demo)
# ---------------------------------------------------------------------------

def probe_oeis_status():
    import glob
    try:
        import pandas as pd
        fs = glob.glob(os.path.join(REPO_ROOT, "data/oeis/**/*.parquet"), recursive=True)
        if fs:
            df = pd.read_parquet(fs[0])
            n_rows = len(df)
            size_bytes = os.path.getsize(fs[0])
            columns = df.columns.tolist()
        else:
            n_rows = None
            size_bytes = None
            columns = None
    except Exception as e:
        n_rows, size_bytes, columns = None, None, None
        return {"error": str(e)}
    return {
        "status": "ALREADY INTEGRATED (domains/oeis_local.py, scripts/oeis_extract_verify.py)",
        "local_dump_rows": n_rows,
        "local_dump_size_bytes": size_bytes,
        "columns": columns,
        "measured_this_repo_today": ("PROGRAM_SYNTHESIS_ARC6_M0_AB.md § Ceiling B 2.1: "
                                      "8/8 target sequences extracted from prose (extract_function "
                                      "-> comprehend_computational_definition -> reason.solve) and "
                                      "verified against real downloaded ground-truth values; 2 "
                                      "documented honest non-extractions (Fibonacci, primes)."),
        "class": "CONTENT -- already a live, working, measured import (not a new bet)",
    }


def probe_rosetta_code():
    html = _curl("https://rosettacode.org/wiki/Fibonacci_sequence", timeout=20)
    n_lang_sections = len(re.findall(r'<h2[^>]*id="[A-Za-z0-9_.]+"', html))
    license_hits = re.findall(r'GNU (?:Free Documentation|Lesser General Public) License[^<]{0,20}', html)
    api_probe = _curl("https://rosettacode.org/mw/api.php?action=query&list=categorymembers&"
                       "cmtitle=Category:Programming%20Tasks&cmlimit=5&format=json", timeout=15)
    api_ok = api_probe.strip().startswith("{") and '"error"' not in api_probe[:50]
    return {
        "license": "GNU Free Documentation License 1.3 (page footer, confirmed live) "
                    "-- copyleft/attribution, NOT a no-strings-attached licence",
        "live_demo": {
            "task_fetched": "Fibonacci_sequence",
            "distinct_language_sections_found": n_lang_sections,
            "license_strings_seen": license_hits[:3],
        },
        "api_probe_at_/mw/api.php": ("worked" if api_ok else
                                      f"FAILED -- raw response head: {api_probe[:120]!r}"),
        "approx_total_tasks": "~1,200-1,400 (well-known figure; this script's live API "
                               "enumeration attempt failed -- see api_probe_at_/mw/api.php "
                               "-- reported honestly as NOT independently re-confirmed here)",
        "class": "CONTENT -- preregister as a bet if pursued; six prior content bets in "
                 "this project nulled at their ceiling",
    }


# ---------------------------------------------------------------------------
# PROBLEM A (kernels) -- other CAS candidates: PARI/GP, FLINT, GAP
# ---------------------------------------------------------------------------

def probe_cas_libraries():
    def pip_versions(pkg):
        r = subprocess.run(["pip", "index", "versions", pkg], capture_output=True, text=True, timeout=30)
        out = (r.stdout or "") + (r.stderr or "")
        return out.splitlines()[0].strip() if out.strip() else "ERROR"

    flint_gh = _github_license("flintlib/flint")
    gap_gh = _github_license("gap-system/gap")
    pari_mirror_gh = _github_license("Schaudge/pari-gp")  # canonical PARI host is
    # a Bitbucket/hg repo, not GitHub; a public mirror is used only to
    # corroborate the licence key, not as a size/activity signal.

    return {
        "sympy": {
            "install_status": "ALREADY INSTALLED (1.14.0)",
            "in_process": True, "shells_out": False,
            "license": "BSD-3-Clause (well-known; SymPy's own LICENSE file)",
            "exactness": "MIXED library -- ntheory/combinatorics submodules are exact "
                         "(measured live above); the general CAS core is symbolic and "
                         "can carry Float/complex results.",
        },
        "mpmath": {
            "install_status": "ALREADY INSTALLED (1.3.0)",
            "in_process": True, "shells_out": False,
            "license": "BSD-3-Clause",
            "exactness": "ARCHITECTURALLY INEXACT -- every result is an mpf/mpc "
                         "(arbitrary-PRECISION float, default 15 decimal digits); "
                         "confirmed live: even mpmath.factorial(5) returns an mpf, "
                         "not an exact int. Cross-frame only (a MAP/renderer/"
                         "comparator per the CLAUDE.md invariant), never an in-frame "
                         "oracle.",
        },
        "flint_via_python_flint": {
            "install_status": f"NOT installed; pip-installable: {pip_versions('python-flint')} "
                               "(not installed here -- outside this task's file-ownership "
                               "scope to modify the shared Python environment)",
            "in_process": True, "shells_out": False,
            "mechanism": "python-flint is a Cython binding directly against libflint "
                         "(an in-process C library call, not a subprocess) -- ADMISSIBLE "
                         "under prog_eval.rs's 'no shelling out' rule for ProgCallExtern.",
            "license": flint_gh,
            "exactness": "EXACT by design -- arbitrary-precision integer/rational/"
                         "polynomial/matrix arithmetic (FLINT's whole purpose).",
        },
        "pari_via_cypari2": {
            "install_status": f"NOT installed; pip-installable: {pip_versions('cypari2')} "
                               "(not installed here, same reason as above)",
            "in_process": True, "shells_out": False,
            "mechanism": "cypari2 embeds the PARI C library directly (Cython, in-process) "
                         "-- ADMISSIBLE under the same rule.",
            "license": {"declared": "GPL-2.0-or-later (PARI/GP's own documented licence; "
                                     "canonical host is Bitbucket/Mercurial, not GitHub, so "
                                     "GitHub license metadata isn't directly queryable -- "
                                     "corroborated via a public mirror)",
                        "mirror_corroboration": pari_mirror_gh},
            "exactness": "EXACT for its core domain (integers/rationals/p-adics/algebraic "
                         "numbers); has an inexact real/complex extension used only when "
                         "explicitly requested.",
            "gpl_note": "GPL-2.0: safe to call in-process from the Python world-adapter "
                        "layer (an external dependency, not linked into the compiled "
                        "substrate_rs binary); STATICALLY linking PARI into substrate_rs "
                        "itself would extend GPL obligations to that binary -- a real "
                        "question for whoever ships this, flagged not dismissed.",
        },
        "gap": {
            "install_status": "NO viable in-process Python binding found on PyPI "
                               "(checked: 'pygap' does not exist; 'gappy' (0.4.3) IS on "
                               "PyPI but is an UNRELATED project -- 'Python framework for "
                               "Gap Service API', a web-service client, not the GAP "
                               "computer-algebra system; 'gappy-system' does not exist). "
                               "GAP's real Python interface (sage.libs.gap) ships only "
                               "inside the full SageMath distribution, which is NOT "
                               "installed here (checked: `sage` not found).",
            "in_process": "NO CLEAN PATH -- the standalone GAP interpreter is normally "
                          "driven via a subprocess/pty (pexpect-style), which "
                          "prog_eval.rs's own doc comment explicitly forbids for "
                          "ProgCallExtern ('NO shelling out, ever').",
            "license": gap_gh,
            "verdict": "EXCLUDED under the current architecture, not on capability or "
                       "licence grounds -- would need a custom Rust/C FFI to libgap "
                       "(comparable in scope to building a new engine primitive), out "
                       "of this scoping task.",
        },
    }


def main():
    print("=== Problem A: SymPy / mpmath (in-process, exact-vs-inexact) ===")
    sympy_result = probe_sympy()
    print(json.dumps({k: v for k, v in sympy_result.items()
                       if k not in ("sample_exact_kernels", "sample_unclassified", "mpmath_contrast_spotcheck")},
                      indent=2))

    print("\n=== Problem A: other CAS candidates (PARI/FLINT/GAP) ===")
    cas_result = probe_cas_libraries()
    print(f"  flint license: {cas_result['flint_via_python_flint']['license']}")
    print(f"  gap license: {cas_result['gap']['license']}")
    print(f"  gap verdict: {cas_result['gap']['verdict']}")

    print("\n=== Problem B: Metamath set.mm (live download + sample) ===")
    mm_result = probe_metamath()
    print(json.dumps({k: v for k, v in mm_result.items() if k != "examples"}, indent=2))

    print("\n=== Problem B: Lean mathlib4 (live GitHub API + file sample) ===")
    mathlib_result = probe_mathlib4(sample_n=25)
    print(json.dumps({k: v for k, v in mathlib_result.items() if k != "sample_rows"}, indent=2))

    print("\n=== Problem B: Isabelle AFP (live topics page) ===")
    afp_result = probe_afp()
    print(json.dumps({k: v for k, v in afp_result.items() if k != "topic_taxonomy_live_parsed"}, indent=2))

    print("\n=== Problem C: OEIS status + Rosetta Code (live demo) ===")
    oeis_result = probe_oeis_status()
    print(json.dumps(oeis_result, indent=2))
    rosetta_result = probe_rosetta_code()
    print(json.dumps(rosetta_result, indent=2))

    out = {
        "problem_A_kernels": {
            "sympy_mpmath_live_probe": sympy_result,
            "other_cas_candidates": cas_result,
        },
        "problem_B_properties": {
            "metamath_set_mm": mm_result,
            "lean_mathlib4": mathlib_result,
            "isabelle_afp": afp_result,
        },
        "problem_C_content": {
            "oeis": oeis_result,
            "rosetta_code": rosetta_result,
        },
    }
    results_dir = os.path.join(REPO_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "arc6_import_impedance.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
