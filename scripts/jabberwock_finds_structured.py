"""THE JABBERWOCK AUTHORS A STRUCTURED "find X near Y" COMPREHENSION. I only frame the concern.

commit c0288920 named the residual: the browse "find X" comprehension (domains/reflective_
faculty.py's `_compose_comprehension_rule`) used a small CLOSED STOPWORD LIST to decide what a
directive wants -- fine for a single-target directive, but a MULTI-CONSTRAINT one ("find the page
about volcanoes near the diagram") needs the full POS/gap grammar to separate the TARGET
("volcanoes", the thing named) from the CONSTRAINT ("diagram", what it must be found near) instead
of flattening both into one undifferentiated word bag.

This script drives the SAME self-build composer (induce_concern -> ground_concern) one register
further:

  (a) POS AT THE BOUNDARY -- domains/browse_dispatch.ingest_directive mechanically POS-types +
      GOVERNANCE-stamps every Mention of a directive, reusing the agent's OWN POS faculty
      (construction_grammar.parse_directive_elements -> parse_with_gaps' _pos_token, the SAME
      classifier the gap-as-part-of-speech comprehension path uses). This surfaced a real,
      narrowly-scoped wall in that shared faculty (fixed here): 'near' 's Wiktionary DOMINANT
      sense lists a content reading (adj) before its preposition reading, so _pos_token mis-typed
      it as content; the fix trusts function_word_reference's role-bearing preposition
      classification (which already resolves the polysemy correctly) over the raw dominant sense,
      for prepositions specifically -- an ordering fix to the existing faculty, not a new tagger.

  (b) STRUCTURED COMPREHENSION -- a NEW `constrain_target_directive` RelationCue (seeds/
      relation_vocabulary.json) grounds a 'constrain' relation head alongside 'find'/'comprehend';
      `_compose_comprehension_rule`'s structured branch (gated on BOTH grounding) authors rules
      that bind a content-noun Mention to the Goal's TARGET (`wants`) unless its governing
      preposition is in a held CONSTRAINT-class set, in which case it binds to `constrained_by` --
      a POSITIVE held-vocabulary class test over POS + governance, not a stopword list.

  (c) STRUCTURED BROWSING -- `_compose_browse_rule`'s structured twin (gated the same way via
      'match'+'constrain') requires BOTH a target word AND a constraint word visible on the
      arrived page before marking the goal satisfied, and weights constraint-word overlap as
      SECONDARY evidence in the affordance choice.

Local fixture site: an index with two links about the SAME headline topic -- a DECOY page that
mentions the target but not the constraint, and a CORRECT page that mentions both. donkey=0
throughout.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_finds_structured.py
"""
from __future__ import annotations
import http.server
import json
import os
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern
from domains.browse_dispatch import mint_browse_request, scan_and_browse, ingest_directive
from domains import construction_grammar as cg

MAX_ACTIONS = 8
DIRECTIVE = "Find the page about volcanoes near the diagram."

INDEX_HTML = """<!doctype html>
<html><head><title>Nature Index</title></head>
<body>
<h1>Welcome to the Nature Index</h1>
<p>This is a small site about natural landforms and features, for testing.</p>
<nav>
<a href="decoy.html">Learn about volcanoes</a>
<a href="correct.html">Volcanoes diagram guide</a>
<a href="mountains.html">Learn about mountains</a>
</nav>
</body></html>"""

DECOY_HTML = ("<!doctype html><html><head><title>Volcanoes</title></head><body>"
              "<h1>Volcanoes</h1><p>Volcanoes are dramatic landforms formed by erupting magma.</p>"
              "</body></html>")
CORRECT_HTML = ("<!doctype html><html><head><title>Volcano Diagram</title></head><body>"
                "<h1>Volcano Diagram</h1><p>This diagram explains how volcanoes erupt, "
                "showing the magma chamber below.</p></body></html>")
MOUNTAINS_HTML = ("<!doctype html><html><head><title>Mountains</title></head><body>"
                   "<h1>Mountains</h1><p>Mountains are large landforms that rise above the "
                   "surrounding terrain.</p></body></html>")


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def main():
    overall = True

    tmp_dir = tempfile.mkdtemp(prefix="jbw_find_")
    with open(os.path.join(tmp_dir, "index.html"), "w") as f:
        f.write(INDEX_HTML)
    with open(os.path.join(tmp_dir, "decoy.html"), "w") as f:
        f.write(DECOY_HTML)
    with open(os.path.join(tmp_dir, "correct.html"), "w") as f:
        f.write(CORRECT_HTML)
    with open(os.path.join(tmp_dir, "mountains.html"), "w") as f:
        f.write(MOUNTAINS_HTML)

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

        print("=" * 96)
        print("THE JABBERWOCK AUTHORS A STRUCTURED 'find X near Y' COMPREHENSION -- I only frame the concern")
        print("=" * 96)

        # STAGE 0 -- POS AT THE BOUNDARY: the reused faculty types + governs the directive's tokens.
        els = cg.parse_directive_elements(DIRECTIVE)
        print(f"\n  [stage0] parse_directive_elements({DIRECTIVE!r}):")
        for e in els:
            extra = f" gov_prep={e['gov_prep']!r}" if "gov_prep" in e else ""
            print(f"      {e['surface']!r:16s} role={e['role']:9s} pos={e['pos']!s:12s}{extra}")
        near_el = next(e for e in els if e["surface"].lower() == "near")
        ok0 = _pass(near_el["role"] == "function" and near_el["pos"] == "preposition",
                    "'near' types as a PREPOSITION (the _pos_token ordering fix: function_word_"
                    "reference's role-bearing reading now wins over Wiktionary's ambiguous dominant "
                    "sense for this word)")
        overall &= ok0

        # STAGE 1 -- DISCRIMINATIVE CONTRAST: the OLD flat/stopword parse mis-binds this directive.
        probe = WorldAdapter(seeds=())
        load_all_seeds(probe)
        ind_old = induce_concern(probe, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"]],
                                  name_hint="old_flat_find_directive")
        g_old = ground_concern(probe, [ind_old["capability_key"]])
        ingest_directive(probe, DIRECTIVE)
        probe.inner.run_rules()
        old_goal = next(n for n in probe.s.nodes("Goal") if probe.s.node(n)["attrs"].get("kind") == "find")
        old_wants = sorted(probe.s.node(w)["attrs"].get("text")
                            for w in probe.inner.neighbours(old_goal, "wants"))
        print(f"\n  [stage1] OLD stopword-based parse (form={g_old.get('form')!r}) -> "
              f"wants={old_wants}")
        ok1 = _pass(g_old.get("form") == "find_directive_rule" and old_wants == ["diagram", "near", "volcanoes"],
                    "confirmed the residual: the OLD parse flattens the TARGET ('volcanoes'), the "
                    "CONSTRAINT ('diagram'), and even the bare preposition ('near', not in its "
                    "closed stoplist) into ONE undifferentiated 'wants' bag -- no target/constraint "
                    "distinction is possible downstream")
        overall &= ok1

        # STAGE 2 -- DRIVE THE STRUCTURED CONCERNS.
        ind_c = induce_concern(a, [["comprehend", "a", "DIRECTIVE"], ["find", "the", "TARGET"],
                                    ["constrain", "near", "CONSTRAINT"]],
                                name_hint="browse_find_constrained_directive")
        print(f"\n  [stage2a induce_concern] minted={ind_c.get('minted')} "
              f"residual={ind_c.get('residual_predicates')}")
        g_c = ground_concern(a, [ind_c["capability_key"]]) if ind_c.get("capability_key") else {}
        print(f"  [stage2a ground_concern] path={g_c.get('path')!r} form={g_c.get('form')!r}")
        for r in (g_c.get("rules") or []):
            print(f"\n     ---- authored rule {r['name']!r} ----")
            print("     match:", r["match"])
            print("     where:", json.dumps(r["where"])[:300])
            print("     effects:", json.dumps(r["effects"])[:300])
        ok2 = _pass(g_c.get("grounded") is True and g_c.get("path") == "compose_comprehension_rule"
                    and g_c.get("form") == "find_directive_structured_rule",
                    "the structured comprehension composer authored the POS-driven target/"
                    "constraint-binding rules")
        overall &= ok2

        ind_m = induce_concern(a, [["match", "the", "AFFORDANCE", "to", "the", "GOAL"],
                                    ["constrain", "near", "CONSTRAINT"]],
                                name_hint="browse_choice_relevance_constrained")
        print(f"\n  [stage2b induce_concern] minted={ind_m.get('minted')} "
              f"residual={ind_m.get('residual_predicates')}")
        g_m = ground_concern(a, [ind_m["capability_key"]]) if ind_m.get("capability_key") else {}
        print(f"  [stage2b ground_concern] path={g_m.get('path')!r} form={g_m.get('form')!r}")
        ok3 = _pass(g_m.get("grounded") is True and g_m.get("path") == "compose_browse_rule"
                    and g_m.get("form") == "browse_structured_rule",
                    "the structured browse composer authored the weighted-choice + both-required-"
                    "stop rules")
        overall &= ok3

        # STAGE 3 -- world_receive the directive; the agent's own rules parse it.
        ingest_directive(a, DIRECTIVE)
        I.run_rules()
        goal = next(g for g in S.nodes("Goal") if S.node(g)["attrs"].get("kind") == "find")
        wants = sorted(S.node(w)["attrs"].get("text") for w in I.neighbours(goal, "wants"))
        constrained = sorted(S.node(w)["attrs"].get("text") for w in I.neighbours(goal, "constrained_by"))
        print(f"\n  [stage3] NEW structured parse -> wants(target)={wants} constrained_by={constrained}")
        ok4 = _pass(wants == ["page", "volcanoes"] and constrained == ["diagram"],
                    "the NEW parse cleanly separates TARGET ('page', 'volcanoes') from CONSTRAINT "
                    "('diagram') -- the discriminative contrast with stage1's flat bag")
        overall &= ok4

        # STAGE 4 -- live navigation: reach the CORRECT page (target+constraint), not the DECOY.
        mint_browse_request(a, site_url + "index.html", purpose=DIRECTIVE)
        scan_and_browse(a, max_actions=MAX_ACTIONS, headless=True, log=lambda m: print(f"      {m}"))
        sessions = [n for n in S.nodes("WorldInstance") if S.node(n)["attrs"].get("world_type") == "BrowserSession"]
        sess = sessions[-1]
        sess_attrs = S.node(sess)["attrs"]
        print(f"\n  [stage4] final_url={sess_attrs.get('url')!r} "
              f"goal_status={S.node(goal)['attrs'].get('status')!r} "
              f"actions_taken={sess_attrs.get('actions_taken')}")
        ok5 = _pass(bool(sess_attrs.get("url")) and sess_attrs["url"].endswith("correct.html"),
                    "the agent's OWN structured rule navigated to the page satisfying BOTH the "
                    "target AND the constraint")
        overall &= ok5
        ok6 = _pass(not sess_attrs.get("url", "").endswith("decoy.html"),
                    "did NOT stop on the decoy page (which only mentions the target)")
        overall &= ok6
        ok7 = _pass(S.node(goal)["attrs"].get("status") == "satisfied",
                    "the structured stop-condition rule marked the goal satisfied")
        overall &= ok7
        ok8 = _pass(1 <= (sess_attrs.get("actions_taken") or 0) <= MAX_ACTIONS,
                    f"reached the target within max_actions "
                    f"({sess_attrs.get('actions_taken')} <= {MAX_ACTIONS})")
        overall &= ok8

        print(f"\n  [donkey] LLM calls: {donkey['n']}")
        ok9 = _pass(donkey["n"] == 0, "donkey == 0 (no LLM calls anywhere in the loop)")
        overall &= ok9

        print("\n" + "=" * 96)
        if overall:
            print("  ALL STAGES PASS. The jabberwock authored its OWN POS-driven target/constraint "
                  "comprehension + constraint-honoring browse-choice rules from framed concerns; "
                  "the old stopword parse's mis-bind is pinned as the discriminative contrast; "
                  "donkey=0.")
        else:
            print("  Some stages FAILED (see [FAIL] lines above) -- honest report, not papered over.")
        return 0 if overall else 1
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
