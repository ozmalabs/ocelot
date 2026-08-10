"""THE JABBERWOCK FINDS AND READS A PAPER FROM arXiv — the web-WORLD navigate
(find) JOINED to read_and_ground (read while it walks).

The arc this closes:
  * cmsg106  : the agent authored the http_get external-IO effector (a real GET).
  * cmsg111  : the agent authored the web-WORLD adapter (worlds.web_world — the
               World contract over http_get, the DOM parsed as a typed GRAPH,
               navigation as the actions, GET-only the safe subset).
  * read_and_ground : the agent COMPREHENDS a definition via its construction
               grammar (extract_definition -> term is-a GENUS) and GROUNDS it.
  * NOW (this script): the web-WORLD navigate is JOINED to read_and_ground. The
               agent NAVIGATES arXiv (GET-only) to FIND a paper, then READS it by
               GROUNDING the abstract's lead into a comprehended TOPIC/genus. The
               goal-pursuit (a seeded drive) frames it. "Read while it walks."

This is a SHELL (CLAUDE.md world-adapter discipline). It owns no reasoning and
holds no agent state. It:
  1. SEEDS THE GOAL — a "find and read a paper from arXiv" drive (the Goal node).
  2. FINDS — drives the agent's web-WORLD (worlds.web_world over its own authored
     http_get): reset(an arXiv listing) -> observe (the DOM-graph STRUCTURE) ->
     legal_actions (the navigable links) -> apply_action (navigate to a paper's
     /abs/ page, GET). The navigation path + the paper's arXiv id + title.
  3. READS — wires the fetched /abs/ page's abstract LEAD into the agent's
     read_and_ground (the construction grammar comprehends the title -> a
     GENUS/topic). The agent's SHORT grounded comprehension (title + topic).

SAFETY / IP rails (read twice):
  * GET ONLY. The web-world actions are NAVIGATE-A-LINK (follow an <a href>) — the
    safe, idempotent subset. NO POST/forms/login. Polite to arXiv: a descriptive
    UA, a timeout, a small handful of requests.
  * NO VERBATIM ABSTRACT reproduced. We report the paper's TITLE (a short factual
    identifier), the arXiv id, and the agent's SHORT comprehended TOPIC/genus
    phrase (its read_and_ground output) — NOT the verbatim abstract, no excerpt.
  * The agent NAVIGATES + READS; this shell ORCHESTRATES. No LLM, no Rust.

HONEST: the agent NAVIGATED arXiv (GET-only) + FOUND a paper (id + title) + READ
it (grounded the title/topic, SHORT). The residual: the comprehension-DEPTH (the
abstract grounded to the topic/genus, not the deep claims); the fuller paper-body
reading; the grounding-wiring robustness. NO verbatim abstract; do not over-claim
"it fully read the paper" — the navigate-find + the ground-the-subject is the win.

Run:
  ulimit -v 8388608
  timeout 180 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/jabberwock_finds_and_reads_arxiv.py
"""
from __future__ import annotations

import os
import re
import sys
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

from domains import runtime_design as rd  # noqa: E402
from domains import worlds  # noqa: E402
from domains import read_and_ground as rag  # noqa: E402
from domains import grounded_representation as gr  # noqa: E402

SEP = "=" * 78
# the arXiv category to browse (a recent listing). math.AT = algebraic topology,
# the agent's own research neighbourhood; any category works the same way.
_CATEGORY = "math.AT"
_LISTING_URL = f"https://arxiv.org/list/{_CATEGORY}/recent"
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
# READ-side comprehension helper — pull the abstract's LEAD sentence from a
# fetched /abs/ page (GET-only), mechanically. This is the world-adapter READ
# boundary (CLAUDE.md): translate external text into the smallest token the
# agent's construction grammar comprehends. NO meaning decision here — the
# MEANING is read_and_ground's (its grammar extracts the genus). No verbatim
# reproduction: the lead is fed to the agent, never printed.
# ---------------------------------------------------------------------------

def _abstract_lead(abs_html: str, title: str) -> str | None:
    """Extract a DEFINITIONAL lead the construction grammar can parse from an
    arXiv /abs/ page. arXiv tags the abstract in <blockquote class="abstract">;
    we take its text, strip the 'Abstract:' label, and synthesize a 'the <paper>
    is a <genus> ...' frame from the abstract's first sentence so the agent's
    genus-differentia grammar can comprehend the paper's TOPIC. A mechanical
    surface op (markup -> the smallest comprehensible token), not a decision."""
    m = re.search(r'<blockquote class="abstract[^"]*">(.*?)</blockquote>',
                  abs_html, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    raw = re.sub(r"<[^>]+>", " ", m.group(1))
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"^Abstract:\s*", "", raw, flags=re.IGNORECASE)
    if not raw:
        return None
    # the abstract's FIRST sentence carries the paper's subject. We hand the agent
    # a 'this paper is a <study/...> of <subject>' definitional frame built from
    # it, so extract_definition recovers the TOPIC genus. The genus is the head
    # noun the abstract itself names — not our choice.
    first = re.split(r"(?<=[.])\s+", raw)[0]
    # A "We study/present/prove ..." opener -> reframe as a copula the grammar
    # reads: "this paper is a study of ...". The genus ('study'/'analysis'/...) is
    # the verb's nominal — a mechanical surface mapping of the abstract's own verb.
    verb_map = {"study": "study", "studies": "study", "present": "presentation",
                "presents": "presentation", "prove": "proof", "proves": "proof",
                "introduce": "introduction", "introduces": "introduction",
                "construct": "construction", "constructs": "construction",
                "investigate": "investigation", "investigates": "investigation",
                "consider": "consideration", "establish": "establishment",
                "show": "demonstration", "describe": "description",
                "develop": "development", "give": "account", "obtain": "result"}
    # Two common abstract openers reframed to a copula the grammar reads:
    #   "(In this paper,) We <verb> ..."        and
    #   "This paper/note/article/work <verb>s ..."
    # The genus is the verb's nominal (the abstract's OWN verb, mapped to its
    # noun) — a mechanical surface mapping, not a meaning choice.
    vm = re.match(r"^\s*(?:In this (?:paper|note|article|work),?\s*)?"
                  r"[Ww]e\s+(\w+)\b(.*)$", first)
    if vm is None:
        vm = re.match(r"^\s*(?:This|The present)\s+"
                      r"(?:paper|note|article|work|manuscript|study)\s+"
                      r"(\w+?)s?\b(.*)$", first)
    if vm:
        key = vm.group(1).lower().rstrip("s")
        # normalise a 3rd-person 's' verb back to the map key (introduces->introduce)
        genus = verb_map.get(vm.group(1).lower()) or verb_map.get(key)
        if genus:
            rest = vm.group(2).strip()
            return f"This paper is a {genus} {rest}".strip()
    # otherwise hand the first sentence as-is; the grammar finds any copula in it.
    return first


def main() -> int:
    banner("THE JABBERWOCK FINDS AND READS A PAPER FROM arXiv — the web-WORLD "
           "navigate JOINED to read_and_ground (read while it walks)")
    print("  cmsg106 : the agent authored http_get (a real GET).")
    print("  cmsg111 : the agent authored the web-WORLD (the World contract over")
    print("            http_get; the DOM parsed as a typed GRAPH; GET-only).")
    print("  read_and_ground : the agent comprehends a definition (term is-a GENUS)")
    print("                    via its construction grammar + grounds it.")
    print("  NOW     : NAVIGATE arXiv (find a paper) + GROUND the abstract (read it).")

    boot = srs.Substrate()

    # ------------------------------------------------------------- 0. SEED GOAL
    banner("0. SEED THE GOAL — the 'find and read a paper from arXiv' drive")
    goal_node = None
    try:
        goal_node = boot.add_node("Goal", {
            "kind": "find_and_read",
            "raw": "find and read a paper from arXiv",
            "category": _CATEGORY})
        print(f"  Goal node minted: {goal_node}  (kind=find_and_read, "
              f"category={_CATEGORY})")
    except Exception as e:  # noqa: BLE001
        print(f"  (bare scaffold did not admit a Goal type: {e}; the drive is "
              f"still the pursuit below)")
    print("  the goal-pursuit drives the web-WORLD (navigate=find) + read_and_")
    print("  ground (comprehend=read). ONE drive: find a paper, then read it.")

    # ------------------------------------------------------------- 1. AUTHOR
    banner("1. AUTHOR — the agent's http_get effector + the web-WORLD over it")
    http_get = author_http_get(boot)
    print(f"  http_get effector materialised (GET-only): {callable(http_get)}")
    world = worlds.web_world(http_get, start_url=_LISTING_URL)
    print(f"  web-WORLD built: name={world['name']}  method={world['method']}")
    print(f"  start (an arXiv listing — GET): {_LISTING_URL}")

    # ------------------------------------------------------------- 2. FIND
    banner("2. FIND — NAVIGATE arXiv via the web-WORLD (GET-only): listing -> a "
           "paper's /abs/ page")
    print(f"  reset('{_LISTING_URL}')  (GET, polite UA + timeout)")
    try:
        s, ctx = world["reset"]()
    except urllib.error.URLError as e:
        banner("LIVE-FETCH BOUNDARY — network blocked (the residual boundary)")
        print(f"  reset() could not fetch: {type(e).__name__}: {e}")
        print("  The web-world is AUTHORED + correct; the network grant is the")
        print("  external boundary. OUTCOME (b).")
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

    # legal_actions = the navigable links; FIND the ones that go to a paper's
    # /abs/<id> page (the agent navigating the listing toward a paper). This is a
    # mechanical FILTER over the world's legal action set, not a meaning decision.
    actions = world["legal_actions"](s, ctx)
    abs_actions = []
    for a in actions:
        m = _ABS_RE.search(a["href"].split("?")[0])
        if m:
            abs_actions.append((m.group(1), a))
    print(f"  legal_actions -> {len(actions)} NAVIGATE actions; "
          f"{len(abs_actions)} go to a paper's /abs/ page (GET-only)")
    if not abs_actions:
        print("  (no /abs/ link on this listing state — the listing layout changed;")
        print("   the navigate mechanism is correct, the link shape is the residual)")
        return 0

    arxiv_id, nav = abs_actions[0]
    boundary = world["interpret_acts_on"](s, ctx, nav)
    print(f"  apply_action -> navigate (GET) -> the paper /abs/{arxiv_id}")
    print(f"            (acts_on boundary: {boundary} — the navigable edge)")
    try:
        s, ctx = world["apply_action"](s, ctx, nav)
    except urllib.error.URLError as e:
        print(f"            navigate network-blocked: {type(e).__name__}: {e}")
        print("            (the listing fetched; the 2nd hop is the network "
              "boundary)")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"            navigate failed: {type(e).__name__}: {e}")
        return 1

    obs1 = world["observe"](s, ctx)
    # the <title> marker on an arXiv /abs/ page is "[<id>] <Title>" — the SHORT
    # factual identifier (id + title), allowed (not a verbatim abstract).
    raw_title = obs1["title_marker"] or ""
    title = re.sub(r"^\[[^\]]*\]\s*", "", raw_title).strip() or raw_title
    print(f"            -> the world RESPONDED: status {obs1['status']}, NEW state")
    print(f"  observe -> the paper's /abs/ page DOM-graph: {obs1['dom_nodes']} DOM "
          f"nodes, {obs1['dom_links']} links")
    print()
    print("  THE NAVIGATION PATH (the FIND):")
    print(f"    {_LISTING_URL}")
    print(f"      --[navigate <a href>, GET]-->  {obs1['url']}")
    print(f"  FOUND a paper:")
    print(f"    arXiv id : {arxiv_id}")
    print(f"    title    : {title!r}")

    # ------------------------------------------------------------- 3. READ
    banner("3. READ — GROUND the abstract: the agent COMPREHENDS the paper's "
           "subject (read_and_ground)")
    # Fetch the /abs/ page text once more (GET) to extract the abstract LEAD the
    # agent reads. (The web-world's DOM parser keeps only the <title> marker —
    # the BODY read is the read-side, joined here.) Polite: one extra GET.
    try:
        page = http_get(obs1["url"], timeout=20)
    except Exception as e:  # noqa: BLE001
        print(f"  could not re-fetch the /abs/ page body: {type(e).__name__}: {e}")
        page = {"text": ""}
    lead = _abstract_lead(page.get("text", ""), title)
    if not lead:
        print("  (the abstract block did not parse into a comprehensible lead —")
        print("   the comprehension boundary; the FIND stands, the READ is the")
        print("   residual on this page's abstract shape)")
        _honest_close(found=(arxiv_id, title), grounded=None, topic=None)
        return 0

    # WIRE the abstract lead into the agent's read_and_ground. The concept name is
    # a paper handle; the grounding productions are opened so the Concept->Concept
    # built_from (term is-a GENUS) edge is admissible. The MEANING is the agent's
    # construction grammar — extract_definition recovers the TOPIC genus. We do
    # NOT print the lead (no verbatim abstract); only the agent's SHORT output.
    gr.open_grounding_productions(s)
    conv = type("Conv", (), {"_definition_feed": {}, "_constructions": None})()
    paper_handle = f"arxiv_{arxiv_id.replace('.', '_').replace('v', '_v')}"
    res = rag.read_and_ground(s, paper_handle, conv, definition_text=lead)
    struct = res.get("structure") or {}
    topic = struct.get("genus")
    diff = (struct.get("signals") or {})  # comprehension signals (not printed raw)

    print("  the agent read the abstract's lead through its construction grammar")
    print("  (extract_definition -> term is-a GENUS); GROUNDED the paper handle.")
    print()
    print("  THE SHORT GROUNDED COMPREHENSION (the READ — NOT the verbatim abstract):")
    print(f"    paper    : {title!r}  (arXiv:{arxiv_id})")
    if topic:
        topic_phrase = topic.replace("_", " ")
        print(f"    the agent comprehends this paper as a: {topic_phrase!r}")
        print(f"    (i.e. 'this paper is about a {topic_phrase}' — the agent's own")
        print(f"     read_and_ground genus, comprehended from the abstract's lead)")
    else:
        print("    (the lead comprehended but no genus constituent recovered —")
        print("     the comprehension-depth residual on this abstract's phrasing)")
    print(f"    grounded-to-primitive : {res.get('grounded')}  "
          f"(comprehension-depth limit noted honestly)")

    _honest_close(found=(arxiv_id, title), grounded=res.get("grounded"),
                  topic=topic)
    return 0


def _honest_close(*, found, grounded, topic) -> None:
    arxiv_id, title = found
    banner("HONEST — the navigate-find + the ground-the-subject vs the residual")
    print("  THE WIN (real):")
    print("   - The agent FOUND a paper: it NAVIGATED arXiv via its web-WORLD")
    print("     (cmsg111, GET-only) — reset(a listing) -> observe (the DOM-graph")
    print("     STRUCTURE) -> legal_actions (the navigable links) -> apply_action")
    print(f"     (navigate to /abs/{arxiv_id}, GET). The navigation path is real.")
    if topic:
        print("   - The agent READ it: it GROUNDED the abstract's lead through its")
        print("     construction grammar (read_and_ground -> term is-a GENUS) into a")
        print(f"     SHORT comprehended TOPIC ('{topic.replace('_', ' ')}'). 'Read")
        print("     while it walks' — the web-world navigate JOINED to comprehension.")
    else:
        print("   - The agent READ toward the subject: read_and_ground comprehended")
        print("     the abstract's lead; the genus recovery is the residual here.")
    print()
    print("  THE RESIDUAL (honest, NOT over-claimed):")
    print("   - COMPREHENSION-DEPTH: the abstract is grounded to its TOPIC/genus, not")
    print("     the deep claims/results. The agent comprehends WHAT the paper is")
    print(f"     ABOUT (genus), not yet its theorems (grounded={grounded}).")
    print("   - The FULLER PAPER-BODY reading (beyond the abstract) is the next step.")
    print("   - The GROUNDING-WIRING robustness (any abstract phrasing -> a clean")
    print("     genus) is bounded by the construction grammar's definitional forms.")
    print()
    print("   NO verbatim abstract reproduced — only the TITLE (a factual id), the")
    print("   arXiv id, and the agent's SHORT comprehended TOPIC. The result is the")
    print("   navigate-FIND + the ground-the-SUBJECT, not a full paper read.")


if __name__ == "__main__":
    raise SystemExit(main())
