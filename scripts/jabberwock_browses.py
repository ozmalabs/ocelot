"""THE JABBERWOCK AUTHORS ITS OWN BROWSE-AFFORDANCE-CHOICE FACULTY. I only frame the concern.

The browser world (worlds/browser.py + domains/browse_dispatch.py) perceives a live page DUALLY
(DOM + visual) but acts on nothing: `scan_and_browse`'s loop reads `chosen_action` off the mirrored
`BrowserSession` node each tick and applies it -- no rule ever WROTE one. This script drives the
agent's own self-build composer (domains/reflective_faculty.py: induce_concern -> ground_concern) to
AUTHOR the rules that (a) comprehend a "find X" instruction into a Goal carrying its wanted content,
and (b) choose WHICH affordance to click in service of that goal -- chosen_action = the affordance
whose label overlaps the most wanted words (argmax over affordances of summed word-overlap), plus a
stop condition (mark the goal satisfied once the wanted content is actually visible on the current
page, not just linked from it).

The DECISION shape (argmax over affordances of expected value) already exists as
`_compose_decision_rule` for GRID NAVIGATION (avatar_candidate/cy/cx/drow/dcol) -- this script first
tries driving that EXISTING machinery as-is on a browsing concern (stage 1) to show it fires the
WRONG composer body for this domain (BrowserSession/Element/Affordance carry none of that grid
vocabulary), which is why `_compose_browse_rule` (a twin, reached the SAME way via the held
composer_pick Program) had to be added -- machinery only, never the rule itself; the jabberwock still
authors the rule.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_browses.py
"""
from __future__ import annotations
import http.server
import json
import os
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
from domains.browse_dispatch import mint_browse_request, scan_and_browse

MAX_ACTIONS = 6

INDEX_HTML = """<!doctype html>
<html><head><title>Nature Index</title></head>
<body>
<h1>Welcome to the Nature Index</h1>
<p>This is a small site about natural landforms and features, for testing.</p>
<nav>
<a href="volcanoes.html">Learn about volcanoes</a>
<a href="rivers.html">Learn about rivers</a>
<a href="mountains.html">Learn about mountains</a>
<a href="deserts.html">Learn about deserts</a>
</nav>
</body></html>"""

PAGES = {
    "volcanoes.html": ("Volcanoes", "Volcanoes are dramatic landforms formed by erupting magma."),
    "rivers.html": ("Rivers", "Rivers are flowing bodies of water that carve valleys over time."),
    "mountains.html": ("Mountains", "Mountains are large landforms that rise above the surrounding terrain."),
    "deserts.html": ("Deserts", "Deserts are arid landscapes that receive very little rainfall."),
}


def _page_html(title: str, body: str) -> str:
    return f"<!doctype html><html><head><title>{title}</title></head><body><h1>{title}</h1><p>{body}</p></body></html>"


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def world_receive(a, instruction: str):
    """THE WORLD'S LANGUAGE RECEIVER (mirrors scripts/arc_self_report.py's world_receive) -- translate
    an external instruction into a Message + per-word Mention nodes. Mechanical ingest; no decision,
    no target extraction here -- that is the agent's OWN authored comprehension rule's job."""
    msg = a.s.add_node("Message", {"text": instruction})
    for w in instruction.lower().replace(".", "").replace("?", "").split():
        a.inner.add_edge_unchecked(msg, "has_mention", a.s.add_node("Mention", {"text": w}))
    return msg


def run_one(a, site_url: str, topic: str, label: str) -> dict:
    """world_receive the instruction for `topic` -> tick (comprehension mints the Goal) -> mint a
    BrowseRequest -> scan_and_browse (unmodified mechanism) -> report what happened."""
    S, I = a.s, a.inner
    instruction = f"Find the page about {topic}."
    print(f"\n  --- {label}: world receives {instruction!r} ---")
    world_receive(a, instruction)
    I.run_rules()

    goals_before = set(S.nodes("Goal"))
    new_goals = [g for g in goals_before if S.node(g)["attrs"].get("kind") == "find"
                 and not S.node(g)["attrs"].get("_reported")]
    for g in new_goals:
        I.set_attr(g, "_reported", 1.0)   # test-harness bookkeeping only, not a decision
        wants = [S.node(w)["attrs"].get("text") for w in I.neighbours(g, "wants")]
        print(f"      comprehended Goal {g}: wants={wants}")

    req = mint_browse_request(a, site_url + "index.html", purpose=instruction)
    log_lines = []
    touched = scan_and_browse(a, max_actions=MAX_ACTIONS, headless=True,
                               log=lambda m: log_lines.append(m))
    for ln in log_lines:
        print(f"      {ln}")

    sessions = [n for n in S.nodes("WorldInstance")
                if S.node(n)["attrs"].get("world_type") == "BrowserSession"]
    last_sess = sessions[-1] if sessions else None
    final_url = S.node(last_sess)["attrs"].get("url") if last_sess is not None else None
    goal = new_goals[0] if new_goals else None
    goal_status = S.node(goal)["attrs"].get("status") if goal is not None else None
    actions_taken = S.node(last_sess)["attrs"].get("actions_taken") if last_sess is not None else None
    return {"req": req, "final_url": final_url, "goal": goal, "goal_status": goal_status,
            "actions_taken": actions_taken, "touched": touched}


def main():
    overall = True

    # --- local fixture site (stdlib http.server, no real network) ---
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="jbw_browse_")
    with open(os.path.join(tmp_dir, "index.html"), "w") as f:
        f.write(INDEX_HTML)
    for fname, (title, body) in PAGES.items():
        with open(os.path.join(tmp_dir, fname), "w") as f:
            f.write(_page_html(title, body))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=tmp_dir, **kw)

        def log_message(self, fmt, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    site_url = f"http://127.0.0.1:{port}/"

    try:
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        donkey = {"n": 0}
        a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
        S, I = a.s, a.inner

        print("=" * 94)
        print("THE JABBERWOCK AUTHORS ITS OWN BROWSE-AFFORDANCE-CHOICE FACULTY -- I only frame the concern")
        print("=" * 94)

        # STAGE 1 -- try the EXISTING machinery as-is: frame the choice concern with the SAME
        # 'utility'/argmax vocabulary jabberwock_builds_decision_faculty.py used, and show it
        # dispatches to the (wrong-shape) grid 'decision' composer, not a browsing-specific one.
        # Driven on a THROWAWAY agent (not `a`): the wrong composer's rule ALSO writes
        # `chosen_action` (match variable named "game", but match is by EDGE TYPE only, so
        # it fires on ANY node with a has_goal edge, including our real BrowserSession) --
        # installing it into `a` would race with the correct rule stage 2 authors below and
        # clobber chosen_action back to '' every tick. Keeping the probe on a throwaway agent
        # is itself the honest finding: the existing composer's OUTPUT is not just unhelpful
        # here, it is actively WRONG if installed alongside a real session.
        probe = WorldAdapter(seeds=())
        load_all_seeds(probe)
        ind_u = induce_concern(probe, [["utility", "ARGMAX", "over", "AFFORDANCE"]],
                                name_hint="stage1_existing_utility_probe")
        g_u = ground_concern(probe, [ind_u["capability_key"]]) if ind_u.get("capability_key") else {}
        print(f"\n  [stage1] existing 'utility' vocabulary alone -> path={g_u.get('path')!r} "
              f"form={g_u.get('form')!r}")
        ok1 = _pass(g_u.get("path") == "compose_decision_rule",
                    "confirmed: 'utility' alone fires the EXISTING grid-navigation 'decision' composer "
                    "(wrong shape for this domain -- game/avatar_candidate/cy,cx/drow,dcol, none of which "
                    "BrowserSession/Element/Affordance have; its Term would even clobber a real session's "
                    "chosen_action back to empty if installed alongside it) -- this is why a twin composer "
                    "was needed")
        overall &= ok1

        # STAGE 2 -- DRIVE THE CONCERNS: comprehension ('find X' directive -> Goal) and choice
        # ('match' affordance to goal). Each clause LEADS with the cue word induce_concern keys the
        # residual on (the FIRST WORD of each clause).
        ind_c = induce_concern(a, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"]],
                                name_hint="browse_find_directive")
        print(f"\n  [stage2a induce_concern] minted={ind_c.get('minted')} "
              f"key={ind_c.get('capability_key')!r} residual={ind_c.get('residual_predicates')}")
        before = I.rule_count()
        g_c = ground_concern(a, [ind_c["capability_key"]]) if ind_c.get("capability_key") else {}
        after = I.rule_count()
        print(f"  [stage2a ground_concern] grounded={g_c.get('grounded')} path={g_c.get('path')!r} "
              f"form={g_c.get('form')!r}  rule_count {before} -> {after}")
        print(f"     grounded_relations={g_c.get('grounded_relations')}")
        if g_c.get("wall"):
            print(f"     WALL: {g_c['wall']}")
        for r in (g_c.get("rules") or []):
            print(f"\n     ---- authored rule {r['name']!r} ----")
            print("     match:", r["match"])
            print("     where:", json.dumps(r["where"])[:300])
            print("     effects:", json.dumps(r["effects"])[:400])
        ok2 = _pass(g_c.get("grounded") is True and g_c.get("path") == "compose_comprehension_rule"
                    and g_c.get("form") == "find_directive_rule",
                    "the comprehension composer authored the 'find X' -> Goal rules")
        overall &= ok2

        ind_m = induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"]],
                                name_hint="browse_choice_relevance")
        print(f"\n  [stage2b induce_concern] minted={ind_m.get('minted')} "
              f"key={ind_m.get('capability_key')!r} residual={ind_m.get('residual_predicates')}")
        before = I.rule_count()
        g_m = ground_concern(a, [ind_m["capability_key"]]) if ind_m.get("capability_key") else {}
        after = I.rule_count()
        print(f"  [stage2b ground_concern] grounded={g_m.get('grounded')} path={g_m.get('path')!r} "
              f"form={g_m.get('form')!r}  rule_count {before} -> {after}")
        print(f"     grounded_relations={g_m.get('grounded_relations')}")
        if g_m.get("wall"):
            print(f"     WALL: {g_m['wall']}")
        for r in (g_m.get("rules") or []):
            print(f"\n     ---- authored rule {r['name']!r} ----")
            print("     match:", r["match"])
            print("     where:", json.dumps(r["where"])[:300])
            print("     effects:", json.dumps(r["effects"])[:600])
        ok3 = _pass(g_m.get("grounded") is True and g_m.get("path") == "compose_browse_rule",
                    "the browse composer authored the affordance-choice rules")
        overall &= ok3

        # STAGE 3 -- live run: instruction -> comprehension -> mint_browse_request -> scan_and_browse.
        r1 = run_one(a, site_url, "volcanoes", "run 1 (volcanoes)")
        print(f"\n  [stage3] final_url={r1['final_url']!r} goal_status={r1['goal_status']!r} "
              f"actions_taken={r1['actions_taken']}")
        ok4 = _pass(bool(r1["final_url"]) and r1["final_url"].endswith("volcanoes.html"),
                    "the agent's OWN rule navigated to the volcanoes page (chosen_action was written "
                    "by run_rules -- zero host choice of which link to click)")
        overall &= ok4
        ok5 = _pass(r1["goal_status"] == "satisfied", "the stop-condition rule marked the goal satisfied "
                    "once the wanted content was visible on the arrived page")
        overall &= ok5
        ok6 = _pass((r1["actions_taken"] or 0) <= MAX_ACTIONS and (r1["actions_taken"] or 0) >= 1,
                     f"reached the target within max_actions ({r1['actions_taken']} <= {MAX_ACTIONS})")
        overall &= ok6

        # STAGE 4 -- DISCRIMINATIVE CONTROL: a DIFFERENT goal must choose DIFFERENTLY (not luck/hardcoding).
        r2 = run_one(a, site_url, "deserts", "run 2 (deserts, control)")
        print(f"\n  [stage4] final_url={r2['final_url']!r} goal_status={r2['goal_status']!r}")
        ok7 = _pass(bool(r2["final_url"]) and r2["final_url"].endswith("deserts.html"),
                    "the control run (different goal) navigated to the DIFFERENT target page")
        overall &= ok7
        ok8 = _pass(r1["final_url"] != r2["final_url"],
                    "discriminative: the two runs' goals produced DIFFERENT chosen affordances "
                    "(not a fixed/lucky choice)")
        overall &= ok8

        print(f"\n  [donkey] LLM calls: {donkey['n']}")
        ok9 = _pass(donkey["n"] == 0, "donkey == 0 (no LLM calls anywhere in the loop)")
        overall &= ok9

        print("\n" + "=" * 94)
        if overall:
            print("  ALL STAGES PASS. The jabberwock authored its OWN comprehension + affordance-choice "
                  "rules from framed concerns; scan_and_browse (unmodified) read chosen_action each tick "
                  "and applied it; two different goals chose two different links; donkey=0.")
        else:
            print("  Some stages FAILED (see [FAIL] lines above) -- honest report, not papered over.")
        return 0 if overall else 1
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
