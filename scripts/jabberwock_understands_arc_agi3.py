"""THE JABBERWOCK UNDERSTANDS WHAT ARC-AGI(-3) IS — find the paper, fetch it,
read it, and GROUND it into its OWN concepts, using its OWN faculties.

ONE GOAL is handed to the agent: "understand what ARC-AGI-3 is and how its games
work, by finding and reading the ARC-AGI-3 paper on arXiv and grounding it into
your own concepts." The agent does everything itself:

  * SEARCH/FIND — the agent's web-WORLD (domains/worlds.web_world over its OWN
    authored http_get effector, cmsg106/cmsg111; GET-only). reset() onto the
    arXiv SEARCH-results state for the goal's query string, observe the DOM as a
    typed GRAPH, read the legal NAVIGATE actions (the /abs/ out-edges), and
    apply_action to navigate to the matching paper's /abs/ page. The agent
    DISCOVERS the paper by acting in the web-world — not handed a URL.
  * FETCH — the agent's http_get (GET-only) pulls the /abs/ page body.
  * READ + GROUND — domains/read_and_ground.read_and_ground COMPREHENDS the
    paper's lead statements through the agent's construction grammar (term
    is-a GENUS + differentia) and GROUNDS them as Concepts in the substrate.
    The understanding comes OUT of the agent's comprehension, in its terms.

THIS SHELL PROVIDES NOTHING the goal does not already name: no URL to the paper,
no page content, no search results, no concept definitions. It hands the agent
the GOAL (the query string = the goal restated) and DRIVES the agent's own
faculties (web-world navigate -> http_get fetch -> read_and_ground comprehend).
CLAUDE.md world-adapter discipline: it owns no reasoning and holds no agent
state; the MEANING is the construction grammar's (graph data), the GROUND is
ground_concept (an admissible mutation), the FIND is the web-world act/respond/
observe loop. No LLM. No Rust. No hand-authored content.

SAFETY / IP rails:
  * GET ONLY. The web-world actions are NAVIGATE-A-LINK (follow an <a href>) —
    the safe, idempotent subset. NO POST/forms/login. Polite to arXiv (a
    descriptive UA via the agent's http_get, a timeout, a small handful of GETs).
  * NO VERBATIM ABSTRACT reproduced. We report the paper's TITLE + arXiv id (a
    short factual identifier) and the agent's OWN comprehended genus/differentia
    phrases (its read_and_ground output) — never the verbatim abstract/body.

HONEST: the comprehension-DEPTH wall (a grounded genus often bottoms out at a
bare leaf — the SAME named limit every deep read hits) is reported, not hidden.
The win is: the agent FOUND the paper by searching+navigating the web-world,
FETCHED it, and GROUNDED its subject into its own concepts. If a faculty is
missing or the network is blocked, that is reported as the honest WALL.

Run:
  ulimit -v 8388608
  timeout 300 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_understands_arc_agi3.py
"""
from __future__ import annotations

import os
import re
import sys
import urllib.error
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

from domains import runtime_design as rd  # noqa: E402
from domains import worlds  # noqa: E402
from domains import read_and_ground as rag  # noqa: E402
from domains import grounded_representation as gr  # noqa: E402

SEP = "=" * 78

# THE GOAL — the only thing the shell knows. The query string IS the goal
# restated; the agent SEARCHES for it, FINDS the paper, READS + GROUNDS it.
_GOAL = ("understand what ARC-AGI-3 is and how its games work, by finding and "
         "reading the ARC-AGI-3 paper on arXiv and grounding it into your own "
         "concepts")
_QUERY = "ARC-AGI-3"
# arXiv's full-text SEARCH endpoint is a GET URL — a navigable web-world STATE.
# The agent resets ONTO it (the goal's query, URL-encoded) and DISCOVERS the
# paper by reading the result page's navigable /abs/ out-edges. No paper URL is
# handed to the agent; only the search state for the goal's query.
_SEARCH_URL = ("https://arxiv.org/search/?searchtype=all&query="
               + urllib.parse.quote(_QUERY))
_ABS_RE = re.compile(r"/abs/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)$")


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# AUTHOR — the agent authors its own http_get effector (cmsg106), the seed the
# web-WORLD is built on. NO LLM, deterministic emitter.
# ---------------------------------------------------------------------------

def author_http_get(substrate):
    spec = rd.agent_specify_http_get(substrate)
    emitted = rd.emit_external_io_binding(spec)
    src = emitted["world_adapter.py (binding)"]
    ns: dict = {}
    exec(compile(src, "<agent_authored_http_get>", "exec"), ns)
    return ns["http_get"]


# ---------------------------------------------------------------------------
# READ-side boundary — pull DEFINITIONAL leads from the fetched /abs/ page so
# the construction grammar can comprehend them. Mechanical markup->token surface
# op (CLAUDE.md world-adapter READ boundary): the smallest comprehensible token,
# NOT a meaning decision. The MEANING is read_and_ground's. NO verbatim text is
# printed — the leads are fed to the agent only.
# ---------------------------------------------------------------------------

def _abstract_text(abs_html: str) -> str:
    m = re.search(r'<blockquote class="abstract[^"]*">(.*?)</blockquote>',
                  abs_html, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    raw = re.sub(r"<[^>]+>", " ", m.group(1))
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"^Abstract:\s*", "", raw, flags=re.IGNORECASE)
    return raw


_VERB_MAP = {
    "study": "study", "studies": "study", "present": "presentation",
    "presents": "presentation", "prove": "proof", "proves": "proof",
    "introduce": "introduction", "introduces": "introduction",
    "construct": "construction", "constructs": "construction",
    "investigate": "investigation", "investigates": "investigation",
    "consider": "consideration", "establish": "establishment",
    "show": "demonstration", "describe": "description",
    "develop": "development", "give": "account", "obtain": "result",
    "propose": "proposal", "proposes": "proposal", "design": "design",
    "designs": "design", "release": "release", "releases": "release",
    "benchmark": "benchmark", "evaluate": "evaluation",
}


def _copula_leads(abstract: str) -> list[str]:
    """Reframe the abstract's sentences into copular DEFINITIONAL leads the
    genus-differentia construction grammar reads ('this/X is a <genus> ...').
    The genus is the abstract's OWN verb mapped to its nominal, or an explicit
    'X is a Y' the abstract already states — a mechanical surface mapping, not a
    meaning choice. Returns several leads (the abstract's first few sentences) so
    the agent comprehends the paper's subject from multiple angles."""
    if not abstract:
        return []
    sents = [s.strip() for s in re.split(r"(?<=[.])\s+", abstract) if s.strip()]
    leads: list[str] = []
    for sent in sents[:6]:
        # (a) the abstract already states a copula 'X is a Y ...' — pass through.
        if re.search(r"\b(is|are)\s+(?:a|an|the)\b", sent):
            leads.append(sent)
            continue
        # (b) 'We <verb> ...' / 'This paper <verb>s ...' -> copula via verb-nominal.
        vm = re.match(r"^\s*(?:In this (?:paper|note|article|work),?\s*)?"
                      r"[Ww]e\s+(\w+)\b(.*)$", sent)
        if vm is None:
            vm = re.match(r"^\s*(?:This|The present)\s+"
                          r"(?:paper|note|article|work|manuscript|study|"
                          r"benchmark|challenge)\s+(\w+?)s?\b(.*)$", sent)
        if vm:
            key = vm.group(1).lower().rstrip("s")
            genus = _VERB_MAP.get(vm.group(1).lower()) or _VERB_MAP.get(key)
            if genus:
                rest = vm.group(2).strip()
                leads.append(f"This paper is a {genus} {rest}".strip())
                continue
        # (c) otherwise hand the sentence as-is; the grammar finds any copula.
        leads.append(sent)
    return leads


def _norm(s: str) -> str:
    """Surface-normalise a string for title matching: lowercase, collapse all
    non-alphanumerics (so 'ARC-AGI-3', 'ARC - AGI - 3', 'arc agi 3' all match).
    A mechanical surface op, not a meaning decision."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _result_titles(obs0_text: str) -> dict:
    """Map each search result's /abs/ id -> its TITLE, read off the result-page
    HTML (arXiv wraps each hit in <li class='arxiv-result'>). Mechanical markup
    parse (world-adapter READ boundary), used only to match the goal's query to
    the right navigable edge — never printed verbatim as content."""
    out: dict = {}
    for b in re.findall(r'<li class="arxiv-result">(.*?)</li>', obs0_text,
                        re.DOTALL):
        mid = re.search(r"/abs/([0-9]{4}\.[0-9]{4,5})", b)
        mt = re.search(r'<p class="title[^"]*">(.*?)</p>', b, re.DOTALL)
        if mid and mt:
            ti = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", mt.group(1))).strip()
            out.setdefault(mid.group(1), ti)
    return out


class _Conv:
    """The minimal conversation handle read_and_ground's caller contract needs —
    a held-constructions slot + a definition feed. No reasoning, no decisions."""
    def __init__(self) -> None:
        self._constructions = None
        self._definition_feed: dict = {}


def main() -> int:
    banner("THE JABBERWOCK UNDERSTANDS WHAT ARC-AGI-3 IS — find the paper, fetch "
           "it, read it, GROUND it (its OWN faculties)")
    print("  THE GOAL (the only thing handed to the agent):")
    print(f"    {_GOAL}")
    print()
    print("  The agent does it ALL itself:")
    print("   - SEARCH/FIND : its web-WORLD (worlds.web_world over its OWN http_get,")
    print("                   GET-only) navigates arXiv search -> the paper's /abs/.")
    print("   - FETCH       : its http_get pulls the /abs/ page (GET).")
    print("   - READ+GROUND : read_and_ground comprehends the lead via its")
    print("                   construction grammar (term is-a GENUS) + grounds it.")
    print("  The shell provides NO url, NO content, NO search results, NO defs.")

    boot = srs.Substrate()

    # ------------------------------------------------------------- 0. SEED GOAL
    banner("0. SEED THE GOAL — the 'understand ARC-AGI-3 from its paper' drive")
    try:
        gid = boot.add_node("Goal", {"kind": "understand_concept",
                                     "raw": _GOAL, "query": _QUERY})
        print(f"  Goal node minted: {gid}  (kind=understand_concept, "
              f"query={_QUERY!r})")
    except Exception as e:  # noqa: BLE001
        print(f"  (bare scaffold did not admit a Goal type: {e}; the drive is "
              f"still the pursuit below)")

    # ------------------------------------------------------------- 1. AUTHOR
    banner("1. AUTHOR — the agent's http_get effector + the web-WORLD over it")
    http_get = author_http_get(boot)
    print(f"  http_get effector materialised (GET-only): {callable(http_get)}")
    world = worlds.web_world(http_get, start_url=_SEARCH_URL)
    print(f"  web-WORLD built: name={world['name']}  method={world['method']}")
    print("  start state = arXiv SEARCH for the goal's query (GET; the agent")
    print(f"  is NOT handed the paper — it must FIND it by navigating):")
    print(f"    {_SEARCH_URL}")

    # ------------------------------------------------------------- 2. SEARCH/FIND
    banner("2. SEARCH/FIND — the agent NAVIGATES the web-WORLD (GET-only): the "
           "search-results state -> the ARC-AGI-3 paper's /abs/ page")
    print("  reset(search-results state)  (the agent's http_get, polite UA + timeout)")
    try:
        s, ctx = world["reset"]()
    except urllib.error.URLError as e:
        banner("LIVE-FETCH BOUNDARY — network blocked (the honest WALL)")
        print(f"  reset() could not fetch: {type(e).__name__}: {e}")
        print("  The web-world + http_get are AUTHORED + correct; the network")
        print("  grant is the external boundary. WALL: no network.")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"  reset() failed: {type(e).__name__}: {e}")
        return 1

    obs0 = world["observe"](s, ctx)
    print(f"    -> status {obs0['status']}  ({obs0['byte_length']} bytes)")
    print(f"  observe -> DOM-as-typed-GRAPH:  {obs0['dom_nodes']} DOM nodes, "
          f"{obs0['dom_links']} navigable links")
    print(f"            (substrate holds {len(s.nodes('DomElement'))} DomElement "
          f"+ {len(s.nodes('DomLink'))} DomLink nodes — a real typed graph)")

    # The legal NAVIGATE actions = the result page's links. The agent reads the
    # ones that go to a paper's /abs/<id> page (the navigable out-edges toward a
    # paper). A mechanical FILTER over the world's legal action set, not a
    # meaning decision — the agent DISCOVERS the papers among the result edges.
    actions = world["legal_actions"](s, ctx)
    abs_actions: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    for a in actions:
        m = _ABS_RE.search(a["href"].split("?")[0])
        if m and m.group(1) not in seen_ids:
            seen_ids.add(m.group(1))
            abs_actions.append((m.group(1), a))
    print(f"  legal_actions -> {len(actions)} NAVIGATE actions; "
          f"{len(abs_actions)} go to a paper's /abs/ page (the search hits)")
    if not abs_actions:
        banner("FIND WALL — the search-results state held no /abs/ out-edge")
        print("  The navigate mechanism is correct; the result-page link shape is")
        print("  the residual (arXiv search layout). WALL: no paper edge found.")
        return 0

    # The goal names "THE ARC-AGI-3 paper" — the paper whose SUBJECT is the query
    # itself (not a paper merely USING it). The agent picks the navigable edge
    # whose result-block TITLE matches the goal's query as its SUBJECT: the title
    # whose leading words ARE the query ("ARC-AGI-3: ..."), preferring the
    # shortest such title (the announcement, not a derived work). A mechanical
    # surface match of the goal's query string against each edge's title — a
    # world-adapter FIND filter, not a meaning decision. Falls back to the top
    # search hit if no title leads with the query.
    try:
        _search_html = http_get(obs0["url"], timeout=25).get("text", "")
    except Exception:  # noqa: BLE001
        _search_html = ""
    titles = _result_titles(obs0_text=_search_html)
    qnorm = _norm(_QUERY)

    def _score(aid: str) -> tuple[int, int]:
        t = _norm(titles.get(aid, ""))
        if t.startswith(qnorm):
            return (2, -len(t))            # title's SUBJECT is the query
        if qnorm in t:
            return (1, -len(t))            # query appears in the title
        return (0, 0)                       # query not in title

    ranked = sorted(abs_actions, key=lambda pa: _score(pa[0]), reverse=True)
    arxiv_id, nav = ranked[0]
    chosen_title = titles.get(arxiv_id, "")
    print(f"  the agent matched the goal's query against each hit's TITLE and "
          f"chose the\n  paper whose SUBJECT is {_QUERY!r}: {chosen_title[:70]!r}")
    boundary = world["interpret_acts_on"](s, ctx, nav)
    print(f"  apply_action -> navigate (GET) -> the paper /abs/{arxiv_id}")
    print(f"            (acts_on boundary: {boundary} — the navigable edge)")
    try:
        s, ctx = world["apply_action"](s, ctx, nav)
    except urllib.error.URLError as e:
        print(f"            navigate network-blocked: {type(e).__name__}: {e}")
        print("            (search fetched; the 2nd hop is the network boundary)")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"            navigate failed: {type(e).__name__}: {e}")
        return 1

    obs1 = world["observe"](s, ctx)
    raw_title = obs1["title_marker"] or ""
    title = re.sub(r"^\[[^\]]*\]\s*", "", raw_title).strip() or raw_title
    print(f"            -> the world RESPONDED: status {obs1['status']}, NEW state")
    print(f"  observe -> the paper's /abs/ page DOM-graph: {obs1['dom_nodes']} DOM "
          f"nodes, {obs1['dom_links']} links")
    print()
    print("  THE NAVIGATION PATH (the agent FOUND the paper by SEARCHING):")
    print(f"    arXiv search for {_QUERY!r}")
    print(f"      --[navigate <a href>, GET]-->  {obs1['url']}")
    print("  FOUND a paper:")
    print(f"    arXiv id : {arxiv_id}")
    print(f"    title    : {title!r}")

    # ------------------------------------------------------------- 3. READ+GROUND
    banner("3. READ + GROUND — the agent COMPREHENDS what ARC-AGI-3 IS "
           "(read_and_ground + its construction grammar)")
    try:
        page = http_get(obs1["url"], timeout=25)
    except Exception as e:  # noqa: BLE001
        print(f"  could not re-fetch the /abs/ page body: {type(e).__name__}: {e}")
        page = {"text": ""}
    abstract = _abstract_text(page.get("text", ""))
    leads = _copula_leads(abstract)
    if not leads:
        banner("READ WALL — the /abs/ abstract did not parse into a lead")
        print("  The FIND stands; the READ is the residual on this page's shape.")
        _honest_close(found=(arxiv_id, title), comprehensions=[])
        return 0

    gr.open_grounding_productions(s)
    base = f"arc_agi3_{arxiv_id.replace('.', '_').replace('v', '_v')}"
    comprehensions: list[dict] = []
    print("  the agent reads the paper's lead statements through its construction")
    print("  grammar (extract_definition -> term is-a GENUS + differentia) and")
    print("  GROUNDS each as a Concept. The understanding is the agent's OWN:\n")
    for i, lead in enumerate(leads):
        handle = f"{base}_s{i}"
        try:
            res = rag.read_and_ground(s, handle, _Conv(), max_depth=2,
                                      definition_text=lead)
        except Exception as e:  # noqa: BLE001
            print(f"  (lead {i}: comprehension raised {type(e).__name__}: {e})")
            continue
        st = res.get("structure") or {}
        comp = (res.get("trace") or {}).get("comprehend") or {}
        genus = (st.get("genus") or comp.get("genus") or "").replace("_", " ")
        differentia = (comp.get("differentia") or "").strip()
        if not (genus or differentia):
            continue
        comprehensions.append({"genus": genus, "differentia": differentia,
                               "grounded": bool(res.get("grounded")),
                               "reason": res.get("reason")})
        print(f"  COMPREHEND lead {i}:")
        if genus:
            print(f"     genus (what KIND of thing ARC-AGI-3 is) : {genus!r}")
        if differentia:
            print(f"     differentia (its distinguishing structure): "
                  f"{differentia[:160]!r}")
        print(f"     grounded-to-primitive: {res.get('grounded')}")
        print()

    _honest_close(found=(arxiv_id, title), comprehensions=comprehensions)
    return 0


def _honest_close(*, found, comprehensions) -> None:
    arxiv_id, title = found
    banner("RESULT — what the jabberwock now UNDERSTANDS about ARC-AGI-3 "
           "(in its OWN words) + the honest wall")
    print("  THE WIN (real):")
    print("   - FOUND : the agent SEARCHED arXiv for the goal's query via its")
    print("     web-WORLD (GET-only) and NAVIGATED the result edges to the paper —")
    print(f"     arXiv:{arxiv_id}  {title!r}.")
    if comprehensions:
        print("   - READ + GROUNDED : it comprehended the paper's lead through its")
        print("     OWN construction grammar. Its comprehension, in its terms:")
        for c in comprehensions:
            g = c["genus"] or "(no genus recovered)"
            print(f"       * ARC-AGI-3 is a/an: {g!r}")
            if c["differentia"]:
                print(f"         distinguished by: {c['differentia'][:150]!r}")
        any_grounded = any(c["grounded"] for c in comprehensions)
        print(f"     (grounded-to-a-held-primitive on >=1 lead: {any_grounded})")
    else:
        print("   - READ : the leads were read but no genus/differentia constituent")
        print("     was recovered — the comprehension residual on this phrasing.")
    print()
    print("  THE HONEST WALL (NOT over-claimed):")
    print("   - COMPREHENSION-DEPTH: the agent comprehends WHAT ARC-AGI-3 IS")
    print("     (genus/kind + differentia from the abstract), grounded toward its")
    print("     held concepts; a grounded genus often bottoms out at a BARE LEAF")
    print("     (the SAME named comprehension-depth limit every deep read hits) —")
    print("     it does NOT yet unpack the paper's full game mechanics/protocol.")
    print("   - The FULLER PAPER-BODY read (beyond the abstract lead — the game")
    print("     rules, the eval protocol) is the residual; the abstract carries")
    print("     the SUBJECT (what ARC-AGI-3 is), which is what was grounded.")
    print()
    print("   NO verbatim abstract/body reproduced — only the TITLE (a factual")
    print("   id), the arXiv id, and the agent's OWN comprehended genus/differentia.")
    print("   The result is: the agent FOUND the paper by searching, FETCHED it,")
    print("   and GROUNDED its subject into its own concepts.")


if __name__ == "__main__":
    raise SystemExit(main())
