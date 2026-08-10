"""The jabberwock REVIEWS itself — a critical self-assessment, not an inventory.

An audit counts what's there; a review hunts for what's WRONG: frames that
recognise a question but route to a capability that can't answer it; concepts /
microtheories referenced but never defined; signs that collide or denote
nothing; dangling Term-subgraph edges; dead scopes; broken boundary invariants.
The agent's whole self is graph data now, so it can run these invariant checks
over itself and report findings with severity — like a code review of its own
structure.

Each check returns FINDINGS (the problems), not just a tally. Mechanical graph
queries; the driver decides nothing — it surfaces what the graph says about
itself, honestly (a review that finds nothing is a review that wasn't looking).
"""
from __future__ import annotations

from collections import Counter

import domains.seed_registry  # noqa: F401 — populates REGISTRY
from substrate.boot_core import CORE_SEEDS, load_seeds_into
from substrate.seeds import REGISTRY
from substrate.world_adapter import WorldAdapter

FINDINGS = []   # (severity, check, detail)


def finding(sev, check, detail):
    FINDINGS.append((sev, check, detail))


def _agent():
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent, ["frames", "relations", "psychology"])
    return wa


def review():
    print("=" * 72)
    print("  THE JABBERWOCK REVIEWS ITSELF")
    print("=" * 72)
    wa = _agent()
    node_ids = list(wa.s.nodes())
    nodes = {n: wa.s.node(n) for n in node_ids}
    idset = set(node_ids)
    edges = wa.s.graph_to_dict()["edges"]
    name_of = {}
    for n, d in nodes.items():
        nm = d["attrs"].get("name")
        if nm:
            name_of.setdefault((d["type"], nm), n)
    concept = {nm: n for (t, nm), n in name_of.items() if t == "Concept"}
    mt = {nm: n for (t, nm), n in name_of.items() if t == "Microtheory"}

    # --- the full capability set a frame could route to -------------------
    from domains.reason import CAPABILITIES
    caps = set(CAPABILITIES) | set(wa.taught_capabilities()) | set(wa.runtime_capabilities())

    # CHECK 1 — every Frame routes to a Concept that has a capability -------
    for f in wa.frames():
        fn = nodes[f]["attrs"].get("name")
        rb = list(wa.inner.neighbours(f, "realised_by"))
        if not rb:
            finding("FAIL", "frame-routing", f"{fn}: no realised_by edge")
            continue
        cname = nodes[rb[0]]["attrs"].get("name")
        if cname not in caps:
            finding("WARN", "frame-routing",
                    f"{fn} -> {cname}: recognises but no capability can answer it")
        if not list(wa.inner.neighbours(f, "holds_in")):
            finding("WARN", "frame-scope", f"{fn}: no holds_in Microtheory (always in scope)")

    # CHECK 2 — every Frame's holds_in Mt is in the agent's competence scope
    scope = wa._agent_scope_mts()
    for f in wa.frames():
        held = list(wa.inner.neighbours(f, "holds_in"))
        if held and not any(h in scope for h in held):
            finding("WARN", "frame-scope",
                    f"{nodes[f]['attrs'].get('name')}: holds_in an Mt outside the agent's scope (unreachable)")

    # CHECK 3 — genlMt targets resolve + no self-loops ---------------------
    for n, d in nodes.items():
        if d["type"] != "Microtheory":
            continue
        for parent in wa.inner.neighbours(n, "genlMt"):
            if parent not in idset:
                finding("FAIL", "mt-genlMt", f"{d['attrs'].get('name')}: genlMt -> missing node")
            if parent == n:
                finding("FAIL", "mt-genlMt", f"{d['attrs'].get('name')}: genlMt self-loop")

    # CHECK 4 — dangling edges (src or tgt node missing) -------------------
    dangling = [e for e in edges if e["src"] not in
                {int(str(x).lstrip('#')) for x in idset} or e["tgt"] not in
                {int(str(x).lstrip('#')) for x in idset}]
    if dangling:
        finding("FAIL", "graph-integrity", f"{len(dangling)} dangling edges")

    # CHECK 5 — lexicon: duplicate sign forms + signs denoting nothing -----
    forms = Counter(s["form"] for s in wa.taught_signs())
    dups = [f for f, c in forms.items() if c > 1]
    if dups:
        finding("WARN", "lexicon-dup", f"{len(dups)} duplicate sign forms: {dups[:5]}")

    # CHECK 6 — semiotic definitions reference resolvable concepts ---------
    for cname in getattr(wa, "_semiotic_definitions", {}):
        if cname not in concept:
            finding("WARN", "semiotic", f"semiotic def for '{cname}' has no Concept node")

    # CHECK 7 — empty microtheories (no Concept/Frame holds_in them) -------
    held_in_tgts = {e["tgt"] for e in edges if e["type"] == "holds_in"}
    empty_mts = [nm for nm, n in mt.items()
                 if int(str(n).lstrip('#')) not in held_in_tgts]
    if empty_mts:
        finding("INFO", "empty-mt",
                f"{len(empty_mts)} microtheories with no holds_in content "
                f"(by-design scope structure, filled by teaching): {empty_mts[:6]}")

    # CHECK 8 — boundary invariants after a growth run ---------------------
    g = WorldAdapter(); g.boot_gamma_meta()
    g.live_gamma(n_games=3, max_plies=40, grow_every_game=1)
    s_, m_, a_ = g.senses(), g.models_set(), g.acts_on_set()
    if not (m_ <= s_):
        finding("FAIL", "boundary", f"models NOT subset of senses: {m_ - s_}")
    if not (a_ <= s_):
        finding("FAIL", "boundary", f"acts_on NOT subset of senses: {a_ - s_}")
    bad_prod = [p for p in g.gamma_dynamic.productions
                if not p.src.type or not p.tgt.type or not p.edge_type]
    if bad_prod:
        finding("FAIL", "gamma", f"{len(bad_prod)} malformed Γ productions")

    # CHECK 9 — every registered seed's dependency closure resolves --------
    unresolved = []
    for sid in REGISTRY.known():
        try:
            REGISTRY.resolve([sid])
        except Exception as e:
            unresolved.append(f"{sid}: {type(e).__name__}")
    if unresolved:
        finding("FAIL", "seed-closure", f"{len(unresolved)} seeds fail to resolve: {unresolved[:4]}")

    # CHECK 10 — the architecture invariant (the hull is gone) -------------
    import importlib
    try:
        importlib.import_module("domains.curious_agent")
        finding("FAIL", "architecture", "domains.curious_agent STILL EXISTS")
    except ModuleNotFoundError:
        pass

    # === CLOSING THE BLIND SPOTS the meta-review found ====================
    # Materialise the grounding / residue-capture / decomposition vocabulary via
    # the faculties' LIGHT paths (no teacher), then check each type's invariant —
    # so these checks are LIVE (real nodes) and verify the faculties emit
    # well-formed graph data.
    from domains import remainder_classification as rc
    from domains import morpheme_decomposition as md
    for w, k in (("tcp", "acronym"), ("argmax", "code_identifier"),
                 ("amdahl", "person_name"), ("aperiodic", "domain_term")):
        try:
            rc.capture(wa.s, w, k, context=f"… {w} …")
        except Exception:
            pass
    try:
        md.agent_decide_decomposition_mechanism(wa.s)
        _code, _held = md.corpus_morpheme_code()
        for _w in ("actionspace", "hashmap"):
            md.decompose(wa.s, _w, _code, _held)
    except Exception:
        pass

    # CHECK 11 — captured residue nodes are well-formed (surface + a valid KIND) --
    for nt in ("Acronym", "CodeIdentifier", "PersonName", "DomainTerm"):
        for n in wa.s.nodes(nt):
            a = wa.s.node(n)["attrs"]
            if not a.get("surface"):
                finding("FAIL", "capture", f"{nt} #{n} has no surface")
            elif a.get("kind") not in rc.KINDS:
                finding("WARN", "capture", f"{nt} #{n} kind {a.get('kind')!r} not a known KIND")

    # CHECK 12 — decomposition structure: morphemes hang off a compound; candidates scored
    cf = set(wa.s.nodes("CompoundForm"))
    for m in wa.s.nodes("Morpheme"):
        if not any(m in wa.inner.neighbours(c, "has_part") for c in cf):
            finding("WARN", "decomposition",
                    f"orphan Morpheme '{wa.s.node(m)['attrs'].get('surface')}' not has_part of a CompoundForm")
    for c in cf:
        if not list(wa.inner.neighbours(c, "has_part")):
            finding("WARN", "decomposition",
                    f"CompoundForm '{wa.s.node(c)['attrs'].get('surface')}' has no Morpheme parts")
    for d in wa.s.nodes("DecompCandidate"):
        if not isinstance(wa.s.node(d)["attrs"].get("bits"), (int, float)):
            finding("WARN", "decomposition", "DecompCandidate without a numeric 'bits' score")

    # CHECK 13 — the agent's SPEC / HINT records carry their identifying content --
    for nt, key in (("PrimitiveSpec", "name"), ("DecompositionSpec", "name"),
                    ("TaughtHint", "answer")):
        for n in wa.s.nodes(nt):
            if not wa.s.node(n)["attrs"].get(key):
                finding("WARN", "record-integrity", f"{nt} #{n} missing '{key}'")

    # CHECK 14 — every other semantic type the review now covers must carry an
    # IDENTIFYING attribute (a typed node with none is corrupt): the older blind
    # spots the meta-review named — Lexeme / Lexicon / LexSlot / Reflex / Seed /
    # Theorem. The Agent root is identified by ROLE (agent_root), not an attr, so
    # it is checked structurally instead — the agent must HAVE a root.
    if not wa.s.nodes("Agent"):
        finding("FAIL", "node-integrity", "no Agent root node — the agent has no self")
    _ID = ("name", "id", "surface", "answer", "form", "title", "kind")
    for nt in ("Lexeme", "Lexicon", "LexSlot", "Reflex", "Seed", "Theorem"):
        for n in wa.s.nodes(nt):
            a = wa.s.node(n)["attrs"]
            if not any(a.get(k) for k in _ID):
                finding("WARN", "node-integrity", f"{nt} #{n} has no identifying attribute")

    # --- META: the review reviews the REVIEW PROCESS ----------------------
    review_the_review(wa)

    # --- report -----------------------------------------------------------
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    FINDINGS.sort(key=lambda x: order.get(x[0], 9))
    by_sev = Counter(s for s, _, _ in FINDINGS)
    print(f"\n  ran 14 invariant checks + a META-review of the review process, "
          f"over {len(node_ids)} nodes / {len(edges)} edges")
    print(f"  findings: {by_sev.get('FAIL',0)} FAIL · {by_sev.get('WARN',0)} WARN · "
          f"{by_sev.get('INFO',0)} INFO\n")
    for sev, chk, detail in FINDINGS:
        print(f"  [{sev:4s}] {chk:16s} {detail}")
    print("\n" + "=" * 72)
    if by_sev.get("FAIL", 0):
        print("  VERDICT: structural FAILs found — the agent is not internally sound.")
    elif by_sev.get("WARN", 0):
        print("  VERDICT: sound, with warnings worth addressing (see WARN).")
    else:
        print("  VERDICT: internally sound — no broken invariants.")
    print("=" * 72)


def review_the_review(wa):
    """The review turns its critical eye on ITSELF: a review that doesn't review
    what the agent now IS has gone stale. Two meta-checks:

      1. COVERAGE — of the node TYPES the agent actually mints in operation, how
         many does any check touch? Types no check names are review BLIND SPOTS.
      2. SHAPE — are the checks only structural-integrity (edges/scope), with no
         invariant over the agent's newer CAPTURE faculties? A review that grew a
         vocabulary it never checks is the finding.
    """
    import re

    # Materialise the agent's RECENT type vocabulary (the grounding + residue-
    # capture faculties mint these in operation; bring them into the graph so the
    # audit sees the agent as it actually is, not just the seed-boot skeleton).
    try:
        from domains import remainder_classification as rc
        for w, k in (("tcp", "acronym"), ("argmax", "code_identifier"),
                     ("amdahl", "person_name"), ("aperiodic", "domain_term")):
            rc.capture(wa.s, w, k)
    except Exception:
        pass
    for t, a in (("CompoundForm", {"surface": "actionspace"}),
                 ("Morpheme", {"surface": "action"}),
                 ("DecompCandidate", {"active": 0.0, "bits": 0.0}),
                 ("DecompositionSpec", {"name": "morpheme_decomposition"}),
                 ("PrimitiveSpec", {"name": "MorphHead"}),
                 ("TaughtHint", {"answer": "acronym"})):
        try:
            wa.s.add_node(t, a)
        except Exception:
            pass

    present = Counter(wa.s.node(n)["type"] for n in wa.s.nodes())
    # the CHECKS' source only — NOT this meta function (else its own type mentions
    # would falsely count as 'reviewed', the review flattering itself).
    src = open(__file__).read().split("def review_the_review")[0]
    reviewed = {t for t in present if re.search(r"\b" + re.escape(t) + r"\b", src)}
    # internal DSL term-tree nodes (Term.*) are plumbing — reviewed collectively by
    # the integrity checks, not per type; separate them from the SEMANTIC vocab.
    sem = {t for t in present if not t.startswith("Term.")}
    sem_blind = sorted(t for t in sem if t not in reviewed)
    n_term = sum(1 for t in present if t.startswith("Term."))

    finding("INFO", "review-coverage",
            f"the checks name {len(reviewed & sem)}/{len(sem)} of the agent's SEMANTIC "
            f"node types ({len(reviewed & sem) / max(1, len(sem)):.0%}); "
            f"{n_term} internal Term.* types are reviewed only collectively")
    if sem_blind:
        finding("WARN", "review-coverage",
                f"{len(sem_blind)} semantic node types NO check reviews — blind "
                f"spots: {sem_blind}")

    # SHAPE: the checks are integrity-only; flag the un-checked capture invariants
    # the newer faculties introduced (the review should grow these).
    cap = [t for t in ("Acronym", "CodeIdentifier", "PersonName", "DomainTerm",
                       "CompoundForm", "Morpheme") if t in sem_blind]
    if cap:
        finding("WARN", "review-shape",
                "no check verifies the newer CAPTURE faculties' invariants — e.g. "
                "every Acronym/PersonName/DomainTerm has a surface + kind; every "
                "Morpheme is has_part of a CompoundForm; every PersonName grounds as "
                "a person. The review grew structural checks, not faculty-invariant "
                f"ones (uncovered: {cap})")


if __name__ == "__main__":
    review()
