"""browse_dispatch — the web-BROWSE dispatch MECHANISM (host I/O only, CLAUDE.md).

Mirrors `domains/fetch_dispatch.py`'s shape exactly, one level up: fetch
reads a URL's TEXT once; browse opens a live, dual-level (native DOM +
human-equivalent visual) `BrowserWorld` (`worlds/browser.py`) session and
runs a BOUNDED interaction loop.

The DECISION to browse a URL is the agent's: it mints a `BrowseRequest`
node (`status="requested"`) via its own rules when it wants to visit a
page. This module does not decide THAT, does not decide WHICH url, and
does not decide what to click — it only:

  1. **sees** a requested `BrowseRequest` node,
  2. **opens** a `BrowserWorld` and does the first full ingest (DOM +
     screenshot, both grounded levels),
  3. **loops** up to `max_actions` times: `agent.tick()` (let the agent's
     own seeded rules react to what it now perceives), then read
     `chosen_action` off the mirrored `BrowserSession` node — if a rule
     wrote one, apply it (host I/O) and incrementally re-ingest; if none
     was written, STOP. An agent with no browsing rules seeded yet simply
     perceives the first page and the loop ends after zero actions — that
     is the honest, correct behaviour, not a bug to paper over.
  4. **closes** the session (prunes the raw percept subgraph, keeps the
     `BrowserSession` root as the durable record) and marks the request
     done/failed.

Node vocabulary (fixed contract — do not deviate):
    BrowseRequest{url, status, purpose?, error?}
      -> (side effect) a BrowserWorld session: BrowserSession + Element /
         Affordance / GridCell / Region / ChangeEvent, pruned at close();
         see `worlds/browser.py` for that vocabulary.

REQUIRES the agent to have the `region_grouping` seed loaded (see
`worlds/browser.py`'s module docstring for why: `segment`'s `has_region`/
`within` edges are Γ-checked and `region_grouping` is what admits them).

Node-id caution (CLAUDE.md): ids recycle from a freelist with no generation
counter — every raw id held across a call boundary is `has_node`-guarded.
"""
from __future__ import annotations

from worlds.browser import BrowserWorld
from domains import construction_grammar as _cg

_MAX_ACTIONS_DEFAULT = 5


def ingest_directive(agent, text: str):
    """Mint a Message + one POS-TYPED Mention per token — the mechanical I/O-boundary
    ingest for a browse directive ("Find the page about volcanoes near the diagram.").
    Reuses the agent's OWN POS faculty (`construction_grammar.parse_directive_elements`
    -> `parse_with_gaps`'s `_pos_token`: function-word reference + Wiktionary POS slabs,
    left-context disambiguated — the SAME classifier the gap-as-part-of-speech
    comprehension path uses) plus its GOVERNANCE walk (which preposition, if any,
    introduces a content noun). Each Mention carries `text`/`pos`/`role`/`idx`/
    `gov_prep` — a mechanical reference lookup + positional fact, like tokenisation.
    STRUCTURING what a governing preposition MEANS (names the TARGET vs a CONSTRAINT)
    is NOT decided here — that is the agent's own authored comprehension rule, reading
    these typed Mentions (domains/reflective_faculty.py's `_compose_comprehension_rule`
    structured-find branch)."""
    msg = agent.s.add_node("Message", {"text": text})
    for i, el in enumerate(_cg.parse_directive_elements(text)):
        surf = el["surface"].strip(".,?!;:").lower()
        if not surf:
            continue
        attrs = {"text": surf, "pos": el.get("pos") or "", "role": el.get("role") or "",
                 "idx": float(i)}
        gp = el.get("gov_prep")
        if gp:
            attrs["gov_prep"] = gp
        mn = agent.s.add_node("Mention", attrs)
        agent.inner.add_edge_unchecked(msg, "has_mention", mn)
    return msg


def mint_browse_request(agent, url: str, purpose: str = ""):
    """Hand-mint a BrowseRequest node. A test/authoring helper — the agent
    will mint these itself via its own rules (not this function's concern);
    mirrors `domains.fetch_dispatch.mint_fetch_request` /
    `domains.experiment_dispatch.mint_experiment`."""
    return agent.s.add_node("BrowseRequest", {
        "url": str(url), "status": "requested", "purpose": str(purpose or ""),
    })


def scan_and_browse(agent, *, max_actions: int = _MAX_ACTIONS_DEFAULT,
                     headless: bool = True, log=lambda *a: None) -> list:
    """Find every REQUESTED BrowseRequest, open a BrowserWorld session,
    ingest the first page, and run the bounded tick/apply loop above.
    Returns the node-id list of every BrowseRequest touched this call.
    Safe to call repeatedly; does nothing when there is nothing to do."""
    S, I = agent.s, agent.inner
    touched: list = []
    for req in list(S.nodes("BrowseRequest")):
        if not I.has_node(req):
            continue
        a = S.node(req)["attrs"]
        if a.get("status") != "requested":
            continue
        url = a.get("url") or ""
        I.set_attr(req, "status", "running")
        touched.append(req)

        from domains.information_commitment import assess
        from domains.shape_tube import goal_manifold, goal_projection
        gate = assess(
            agent,
            commit={
                "name": "browser_apply",
                "expected_goal_work": float(a.get("expected_goal_work", 1.0)),
                "expected_information_gain": float(a.get("expected_information_gain", 0.5)),
                "projection": goal_projection("browser_apply_goal", active=True, action_count=1, intervention_magnitude=1.0),
            },
            wait={"delay_cost": float(a.get("delay_cost", 0.1)),
                  "projection": goal_projection("browser_apply_goal", active=False, action_count=0, intervention_magnitude=0.0)},
            refine={"refinement_cost": 1.0, "projection": goal_projection("browser_apply_goal", active=False, action_count=1, intervention_magnitude=0.5)},
            manifold=goal_manifold("browser_apply_goal"),
            retain_trace=False,
        )
        I.set_attr(req, "commit_decision", gate["decision"] or "undetermined")
        if gate["decision"] != "commit" or not gate["authorized"]:
            I.set_attr(req, "status", "deferred")
            continue

        world = BrowserWorld(agent, headless=headless)
        steps = 0
        try:
            world.reset(url)
            while steps < max_actions:
                agent.tick()
                sess_wi = world.session_node()
                if sess_wi is None or not S.has_node(sess_wi):
                    break
                chosen = S.node(sess_wi)["attrs"].get("chosen_action") or ""
                if not chosen:
                    break
                I.set_attr(sess_wi, "chosen_action", "")   # cleared; a rule writes it, the host reads it
                world.apply((chosen,))
                steps += 1
            I.set_attr(req, "status", "done")
            log(f"browsed {url!r}: {steps} action(s)")
        except Exception as e:  # noqa: BLE001 -- network/host failure -> failed, not a crash
            I.set_attr(req, "status", "failed")
            I.set_attr(req, "error", f"{type(e).__name__}: {e}")
            log(f"browse failed ({url}): {type(e).__name__}: {e}")
        finally:
            try:
                world.close()
            except Exception as e:  # noqa: BLE001 -- close is best-effort teardown
                log(f"browse close error ({url}, continuing): {type(e).__name__}: {e}")
    return touched
