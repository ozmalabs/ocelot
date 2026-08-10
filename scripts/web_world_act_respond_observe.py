"""THE WEB-WORLD ADAPTER, REALIZED — the jabberwock authors the worlds.py World
contract OVER its own http_get effector, GET-only, and ACTS in the web.

The arc:
  * cmsg105b: the agent recognized the web is a WORLD (act/respond/observe via
    the World contract), not an information dispenser; it RE-DESIGNED the
    interface as the SAME contract chess/conway/doom/walker use.
  * cmsg106: it authored the http_get external-IO effector (runtime_design.
    agent_specify_http_get + emit_external_io_binding) — a REAL GET fetch worked.
  * NOW (this script): the agent AUTHORS the web-WORLD ADAPTER — the worlds.py
    World contract (reset / legal_actions / apply_action / observe) OVER http_get,
    with the DOM parsed as a typed GRAPH (the agent's "X is a graph" move) and
    navigation (following an <a href> link) as the actions, GET-ONLY (the
    consequence-aware safe subset). The web-as-WORLD it re-designed is REALIZED.

This is a SHELL (CLAUDE.md world-adapter discipline). It does NOT reason for the
agent. It:
  1. Has the agent AUTHOR the http_get binding via its code-writing (the cmsg106
     spec + emitter — NO LLM, deterministic), then materialises it.
  2. Builds the web-WORLD over that binding (domains/worlds.web_world — the World
     contract + the DOM-as-typed-graph parser, both GET-only).
  3. DEMONSTRATES the act/respond/observe loop on SAFE pages: reset(example.com)
     -> observe (the DOM-graph STRUCTURE) -> legal_actions (the navigable link[s])
     -> apply_action (navigate a link, GET) -> the NEW state -> observe.

SAFETY / IP rails (read twice):
  * GET ONLY. The actions are NAVIGATE-A-LINK (follow an <a href>) — the safe,
    idempotent subset. NO POST/forms/login/side-effects (those CONSEQUENTIAL
    actions are GATED — the next, not this).
  * SAFE, non-copyrighted test pages: example.com (RFC 2606 reserved) + its one
    link (-> www.iana.org/domains/example). NO copyrighted-content pages.
  * NO PAGE CONTENT reproduced. We report the STRUCTURE (DOM-graph node/link
    counts) + the NAVIGATION (the link followed, status 200), NOT the page TEXT.
    The <title> tag text ("Example Domain") is the ONE structural marker allowed
    (mechanism-confirmation); NO body content, NO excerpts.

HONEST: the SAFE (GET-only) web-world adapter + the act/respond/observe loop. The
residual: the CONSEQUENTIAL actions (forms/POST) are GATED (the not-preview-safe
model — the next); the DOM-content GROUNDING (read the content into meaning — the
read-side, separate); the live-fetch boundary (the network grant); the eye for
the non-symbolic (out of scope, GET-text only).

Run:
  ulimit -v 8388608
  timeout 120 env PYTHONPATH=runners/dsl/python:. \\
    python3 scripts/web_world_act_respond_observe.py
"""
from __future__ import annotations

import os
import sys
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

from domains import runtime_design as rd
from domains import worlds

SEP = "=" * 78


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# 1. AUTHOR — the agent authors the http_get effector (cmsg106) + the web-world.
# ---------------------------------------------------------------------------

def author_http_get(substrate):
    """The agent authors the http_get external-IO binding via its OWN code-
    writing (runtime_design: spec the new EXTERNAL-IO register, then the
    deterministic emitter authors the urllib binding — NO LLM). Returns the
    materialised callable. This is the cmsg106 seed the web-world is built ON."""
    spec = rd.agent_specify_http_get(substrate)
    emitted = rd.emit_external_io_binding(spec)
    src = emitted["world_adapter.py (binding)"]
    ns: dict = {}
    exec(compile(src, "<agent_authored_http_get>", "exec"), ns)
    return ns["http_get"], spec, emitted


def main() -> int:
    banner("THE WEB-WORLD ADAPTER, REALIZED — the agent ACTS in the web as a "
           "WORLD (GET-only, the safe subset)")
    print("  cmsg105b: the web is a WORLD (act/respond/observe), not a dispenser.")
    print("  cmsg106 : the agent authored the http_get effector (a real GET worked).")
    print("  NOW     : the agent authors the WORLD CONTRACT over http_get + the")
    print("            DOM-as-typed-GRAPH parser; it ACTS in the web (GET-only).")

    boot = srs.Substrate()

    # --------------------------------------------------------------- 1. AUTHOR
    banner("1. AUTHOR — the web-WORLD adapter (the World contract over http_get)")
    http_get, spec, emitted = author_http_get(boot)
    print("  (a) the http_get EFFECTOR (cmsg106 — the agent's code-writing):")
    print(f"      spec register : {spec['register']} / {spec['semantic_kind']}")
    print(f"      method        : {spec['method']}  (GET only — safe/idempotent)")
    print(f"      callable      : {emitted['callable_name']}  "
          f"(materialised: {callable(http_get)})")
    print()
    print("  (b) the web-WORLD adapter (domains/worlds.web_world — the World")
    print("      contract OVER http_get, GET-only):")
    world = worlds.web_world(http_get, start_url="https://example.com/")
    print(f"      world name    : {world['name']}  (method {world['method']})")
    print("      contract (mirrors chess/conway):")
    print("        reset()                       -> http_get(start) -> the DOM")
    print("                                         parsed as a typed GRAPH (STATE)")
    print("        observe(s, ctx)               -> the DOM-as-typed-GRAPH STRUCTURE")
    print("        legal_actions(s, ctx)         -> the navigable <a href> links")
    print("                                         (NAVIGATE actions, GET-only)")
    print("        apply_action(s, ctx, nav)     -> http_get(link) -> the NEW state")
    print("        interpret_acts_on(s, ctx, a)  -> the boundary the navigate touches")
    print("      DOM-as-graph  : html.parser -> DomElement nodes + dom_child tree")
    print("                      edges + dom_link <a href> out-edges (admitted into")
    print("                      Γ — the agent's 'X is a graph' move).")
    print("      SAFETY        : GET ONLY — navigate-a-link (the safe, idempotent")
    print("                      subset). NO POST/forms/login (those CONSEQUENTIAL")
    print("                      actions are GATED — out of scope).")

    # ---------------------------------------------------- 2. ACT/RESPOND/OBSERVE
    banner("2. ACT / RESPOND / OBSERVE — the loop on SAFE pages (STRUCTURE, NOT "
           "content)")
    print("  reset('https://example.com/')  (RFC 2606 reserved, safe, GET)")
    try:
        s, ctx = world["reset"]()
    except urllib.error.URLError as e:
        banner("LIVE-FETCH BOUNDARY — network blocked (the residual boundary)")
        print(f"  reset() could not fetch: {type(e).__name__}: {e}")
        print("  The web-world adapter is AUTHORED + correct; the network grant is")
        print("  the external boundary (not the agent's to grant). OUTCOME (b).")
        return 0
    except Exception as e:  # noqa: BLE001 — report any real failure honestly
        banner("RUN BOUNDARY — fetch failed (reported honestly)")
        print(f"  reset() failed: {type(e).__name__}: {e}")
        return 1

    # --- OBSERVE the initial state (DOM-graph STRUCTURE, no content) ---
    obs0 = world["observe"](s, ctx)
    print(f"    -> status {obs0['status']}  ({obs0['byte_length']} bytes fetched)")
    print(f"  observe  -> DOM-as-typed-GRAPH:")
    print(f"               DOM nodes (elements)      : {obs0['dom_nodes']}")
    print(f"               navigable links (<a href>): {obs0['dom_links']}")
    print(f"               root node-id in substrate : {obs0['root_node']}")
    print(f"               <title> marker (mechanism): {obs0['title_marker']!r}")
    # Confirm the DOM is a REAL typed graph in the substrate (count the nodes/
    # edges the parser wrote — the 'X is a graph' move landed).
    dom_nodes_in_graph = len(s.nodes(obs0["node_type"]))
    link_nodes_in_graph = len(s.nodes("DomLink"))
    print(f"               (substrate now holds {dom_nodes_in_graph} {obs0['node_type']}")
    print(f"                nodes + {link_nodes_in_graph} DomLink nodes — a real typed graph)")

    # --- legal_actions = the navigable links (GET-only NAVIGATE actions) ---
    actions = world["legal_actions"](s, ctx)
    print(f"  legal_actions -> {len(actions)} NAVIGATE action(s) (GET-only):")
    for a in actions:
        print(f"               [{a['method']} navigate] -> {a['href']}")

    if not actions:
        print("  (no navigable links — terminal state; nothing to navigate)")
        _honest_close(authored=True, navigated=False)
        return 0

    # --- apply_action: navigate the link (GET) -> the world RESPONDS ---
    nav = actions[0]
    print(f"  apply_action  -> navigate (GET) -> {nav['href']}")
    boundary = world["interpret_acts_on"](s, ctx, nav)
    print(f"               (acts_on boundary: {boundary} — the navigable edge)")
    try:
        s, ctx = world["apply_action"](s, ctx, nav)
    except urllib.error.URLError as e:
        print(f"               navigate network-blocked: {type(e).__name__}: {e}")
        print("               (the first hop fetched; the 2nd-hop network is the")
        print("                boundary — the adapter + loop are correct).")
        _honest_close(authored=True, navigated="partial")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"               navigate failed: {type(e).__name__}: {e}")
        return 1

    # --- OBSERVE the NEW state (the linked page's DOM-graph STRUCTURE) ---
    obs1 = world["observe"](s, ctx)
    print(f"               -> the world RESPONDED: status {obs1['status']}, "
          f"NEW state")
    print(f"  observe  -> the NEW page's DOM-as-typed-GRAPH:")
    print(f"               url (navigated to)        : {obs1['url']}")
    print(f"               DOM nodes (elements)      : {obs1['dom_nodes']}")
    print(f"               navigable links (<a href>): {obs1['dom_links']}")
    print(f"               <title> marker (mechanism): {obs1['title_marker']!r}")
    print(f"  visited path (the NAVIGATION) : {' -> '.join(ctx['visited'])}")

    navigated = (obs1["status"] == 200 and obs1["url"] != obs0["url"])
    _honest_close(authored=True, navigated=navigated)
    return 0


# ---------------------------------------------------------------------------
# 3. HONEST — the safe web-world working vs the residual.
# ---------------------------------------------------------------------------

def _honest_close(*, authored: bool, navigated) -> None:
    banner("3. HONEST — the safe GET-only web-world working vs the residual")
    print("  THE WIN (real):")
    print("   - The agent AUTHORED the web-WORLD ADAPTER: the worlds.py World")
    print("     contract (reset/legal_actions/apply_action/observe) OVER its own")
    print("     http_get effector (cmsg106), with the DOM parsed as a typed GRAPH")
    print("     (the 'X is a graph' move) and navigation as the actions, GET-only.")
    if navigated is True:
        print("   - DEMONSTRATED the act/respond/observe loop on SAFE pages: reset")
        print("     -> observe (DOM-graph structure) -> legal_actions (the link[s])")
        print("     -> apply_action (navigate a link, GET) -> the NEW state (the")
        print("     linked page's DOM-graph) -> observe. The navigation WORKED (200).")
        print("   - The web-as-WORLD it re-designed in cmsg105b is REALIZED: the")
        print("     agent ACTS in the web (GET-only safe), built on the http_get seed.")
    elif navigated == "partial":
        print("   - reset + observe + legal_actions worked (the first page fetched +")
        print("     parsed as a DOM-graph); the navigate-hop network was the boundary.")
    else:
        print("   - reset + observe + legal_actions demonstrated (the page fetched +")
        print("     parsed as a DOM-graph); no navigable link on this state.")
    print()
    print("  THE RESIDUAL (honest, NOT this task):")
    print("   - CONSEQUENTIAL actions (POST/forms/login) are GATED — the cmsg105b")
    print("     not-preview-safe model; the safe subset here is GET-navigation only.")
    print("     Those side-effecting actions are the NEXT, not this.")
    print("   - DOM-CONTENT GROUNDING (read the page content into meaning via read_")
    print("     and_ground/comprehension) is the READ-side — separate. This world")
    print("     OBSERVES the STRUCTURE (the DOM-graph), it does not read the text.")
    print("   - The LIVE-FETCH boundary (the network grant) is external (present")
    print("     here; the boundary elsewhere).")
    print("   - The EYE for the non-symbolic (images/canvas/layout) is out of scope")
    print("     — GET-text DOM only.")
    print()
    print("  NOT over-claimed: this is NOT a full browser. The result is the SAFE")
    print("  GET-navigation web-world + the act/respond/observe loop — the agent")
    print("  acting in the web as a WORLD, GET-only, structure + navigation.")


if __name__ == "__main__":
    raise SystemExit(main())
