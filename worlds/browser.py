"""worlds/browser — a Playwright-backed BROWSER world (host-layer I/O only, CLAUDE.md).

Lets the agent interact with a live webpage at TWO GROUNDED LEVELS, the same
page seen two ways:

  NATIVE      — the DOM, mirrored as a typed graph: `Element` nodes for
                significant tags (interactive controls, structural landmarks,
                substantial text leaves) + `Affordance` nodes for the ones
                that can be acted on, wired `contains` (structure) /
                `follows` (document order) / `affords` (element -> action).

  HUMAN-EQUIVALENT — a LIVE pixel feed: a CDP screencast writes JPEG
                frames into a JBWF shared-memory buffer (`scripts/fb_pipe.py`'s
                `FbWriter`), and the Rust eye (`fb_attach`/`fb_sample`) reads
                that buffer directly and segments it -> persistent `Region`
                nodes, the SAME `segment_and_track` primitive `segment()`
                (and the ARC eye) use. Falls back to a one-shot
                `page.screenshot()` + `substrate_rs.Substrate.segment` when
                the live screencast can't be set up (known-flaky under some
                headless Chromium configs) or `use_live_eye=False`.

  CROSS-LEVEL — for every kept `Element`, the grid cells its bounding box
                overlaps are looked up for the `Region`(s) they are
                `within`, and an `element -renders_as-> region` edge is
                added: the DOM node and the visual region are the same
                thing, seen two ways.

This is the ArcWorld contract (`worlds/arc.py`): reset / legal_actions /
apply. Unlike ArcWorld (whose caller does the ingest, e.g. `arc_run.py`
calling `agent.perceive_frame(sub)`), a `BrowserWorld` is handed the live
`WorldAdapter` up front and does its own ingest inside `reset`/`apply` —
there is no browser-specific "perceive_frame" on `WorldAdapter` (out of
scope to add: `substrate/world_adapter.py` is owned by other in-flight
work), so this module reproduces that ORCHESTRATION (mirror -> segment ->
ground -> tick) itself, calling only public `WorldAdapter`/`Substrate`
primitives — no new agent decision logic, exactly the ArcWorld division of
labor.

REQUIRES the agent to have the `region_grouping` seed loaded. `segment`'s
`has_region`/`within` edges are written through the CHECKED (Γ-admissible)
Rust `add_edge`, and `region_grouping`'s productions (generic
`WorldInstance -> Region`) are what admit them; without it `segment` still
mints `Region` nodes but every edge silently fails admissibility and the
regions are unreachable from the session (found by hand while building this
module — see the test file for the reproduction). `worlds/arc.py` gets this
for free because every ARC-playing agent's seed set already includes it;
a `BrowserWorld` caller must include it explicitly.

ALSO REQUIRES the `browser_affordance_reach` seed loaded (same reason:
`load_all_seeds` picks it up for free, an explicit seed list must name it).
It ships the two graph-resident rules that keep `session -has_affordance->
affordance` in sync with the DOM `contains*` tree via the agent-authored
`ReachableFrom` Term — see `_ingest`'s comment at the affordance mirror for
the mechanism.

Node-id caution (CLAUDE.md): ids recycle from a freelist with no generation
counter — every raw id held across a call boundary is `has_node`-guarded.
"""
from __future__ import annotations

import base64
import io
import re
from uuid import uuid4

import numpy as np
from PIL import Image

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from scripts.fb_pipe import FbWriter

# --- human-equivalent-level tuning --------------------------------------------
GRID_W, GRID_H = 80, 60          # coarse colour grid the Rust eye segments
VIEWPORT_W, VIEWPORT_H = 800, 600  # -> exactly 10px/cell, deterministic mapping
COLOR_BINS = 4                    # quantisation levels per RGB channel

# A ChangeEvent minted THIS ingest must survive every `run_rules`/`tick`
# fixpoint the ingest drives -- including `agent.observe`'s internal tick,
# the live-eye look-rule's own `run_rules` firing, and the trailing
# `agent.tick()` -- all of which (now that the WHEN-TO-SAMPLE decision is the
# agent's own rule, not a one-shot host `fb_sample`) can advance the session's
# `frame` (the framebuffer frame_seq the look-rule's `fb_sample` effect
# stamps). `region_grouping`'s `prune_consumed_changes` rule deletes any CE
# whose `frame` < the session's `frame`; a CE minted with the pre-sample frame
# would therefore be pruned MID-ingest, before `_ingest` can read it back.
# Minting with this sentinel (>> any realistic frame_seq) makes `prune` leave
# the live CE alone for the whole ingest; `_ingest` then re-tags it (after the
# final `agent.tick()`) with the session's TRUE final frame, so the NEXT
# ingest's first tick advances `frame` past it and `prune` retires it -- the
# rule's own "survive this tick, pruned next frame" semantics, just no longer
# fragile to a one-shot-host-bump assumption. (region_grouping's prune rule is
# effectively browser-only: only a BrowserWorld mints `has_change` edges, so
# this sentinel touches no other world.)
_CE_LIVE_SENTINEL = 1e18

# --- native-level tuning -------------------------------------------------------
INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea"}
LANDMARK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "nav", "main",
                  "header", "footer", "form", "article", "section"}
TEXT_MIN_LEN = 15
TEXT_MAX_LEN = 200

# One page.evaluate() call extracts the whole significant-element tree in
# document order: mechanical DOM->data translation (host I/O), no decisions
# ("significant" is a fixed, hand-authored membership test, the same kind of
# thin I/O-boundary classifier CLAUDE.md permits — there is no Rust DOM
# primitive to defer to). Each record's `id` is a structural path (tag +
# nth-of-type-among-siblings at every ancestor level) — POSITION-stable
# across re-ingests the way ARC's cell id="{r}_{c}" is, so unchanged
# elements dedup instead of re-minting (see the module docstring's
# `region_grouping` note for the other place stability matters).
_WALK_JS = r"""
() => {
  const INTERACTIVE = new Set(['a','button','input','select','textarea']);
  const LANDMARK = new Set(['h1','h2','h3','h4','h5','h6','nav','main',
                             'header','footer','form','article','section']);
  const TEXT_MIN = 15;
  const results = [];
  const tagCounters = new Map();
  let order = 0;

  function directText(el) {
    let t = '';
    for (const n of el.childNodes) if (n.nodeType === 3) t += n.textContent;
    return t.replace(/\s+/g, ' ').trim();
  }

  function walk(el, pathPrefix, keptParentPath) {
    const tag = el.tagName ? el.tagName.toLowerCase() : '';
    if (!tag || tag === 'script' || tag === 'style' || tag === 'noscript') return;
    const counters = tagCounters.get(pathPrefix) || {};
    const idx = counters[tag] || 0;
    counters[tag] = idx + 1;
    tagCounters.set(pathPrefix, counters);
    const myPath = pathPrefix + '/' + tag + '[' + idx + ']';

    const txt = directText(el);
    const significant = INTERACTIVE.has(tag) || LANDMARK.has(tag) || txt.length >= TEXT_MIN;
    let myKeptParent = keptParentPath;
    if (significant) {
      const rect = el.getBoundingClientRect();
      results.push({
        id: myPath, tag: tag, text: txt,
        href: el.getAttribute('href') || '',
        name: el.getAttribute('name') || '',
        itype: el.getAttribute('type') || '',
        value: ('value' in el) ? String(el.value) : '',
        x: rect.x, y: rect.y, w: rect.width, h: rect.height,
        parent: keptParentPath, order: order++,
      });
      myKeptParent = myPath;
    }
    for (const child of el.children) walk(child, myPath, myKeptParent);
  }
  walk(document.documentElement, '', null);
  return results;
}
"""


def _affordance_kind(rec: dict) -> str | None:
    tag = rec["tag"]
    if tag == "a":
        return "navigate" if rec.get("href") else None
    if tag == "button":
        return "click"
    if tag == "input":
        itype = (rec.get("itype") or "text").lower()
        if itype in ("submit", "button", "reset", "checkbox", "radio"):
            return "click"
        return "type"
    if tag == "textarea":
        return "type"
    if tag == "select":
        return "select"
    return None


def _to_xpath(path_id: str) -> str:
    """Structural path "/html[0]/body[0]/p[1]" -> 1-indexed XPath, so a
    kept Element can be re-located on the live page from its stable id
    alone (no persisted Playwright object needed)."""
    return re.sub(r"\[(\d+)\]", lambda m: f"[{int(m.group(1)) + 1}]", path_id)


def _record_key(rec: dict) -> tuple:
    """The comparable projection of a DOM record — changes here are what
    `apply`'s incremental re-ingest treats as "this element changed"."""
    return (rec["tag"], rec["text"][:TEXT_MAX_LEN], rec.get("href", ""),
            rec.get("name", ""), rec.get("value", ""), rec.get("itype", ""),
            round(rec["x"]), round(rec["y"]), round(rec["w"]), round(rec["h"]))


def _quantize_screenshot(png_bytes: bytes):
    """Screenshot bytes -> (H, W, flat values, (viewport_w, viewport_h)).
    Mechanical downsample (PIL BOX = block-average, "dominant colour per
    cell") + per-channel quantisation to a small integer value the Rust
    `segment` primitive can flood on (equal-value = same region), exactly
    the role `_render_screen`'s colour blocks play for ARC's palette."""
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    vw, vh = img.size
    resample = getattr(getattr(Image, "Resampling", Image), "BOX", Image.BOX)
    small = img.resize((GRID_W, GRID_H), resample)
    arr = np.asarray(small, dtype=np.int32)
    step = 256 // COLOR_BINS
    levels = np.clip(arr // step, 0, COLOR_BINS - 1)
    values = (levels[..., 0] * COLOR_BINS * COLOR_BINS
              + levels[..., 1] * COLOR_BINS + levels[..., 2]).astype(np.int32)
    return GRID_H, GRID_W, values.reshape(-1).tolist(), (vw, vh)


class BrowserWorld:
    """A 3-call world (reset / legal_actions / apply) over a live Playwright
    page, wired into an already-booted `WorldAdapter`. See module docstring."""

    def __init__(self, agent, headless: bool = True, use_live_eye: bool = True):
        self.agent = agent
        self.headless = headless
        self.use_live_eye = use_live_eye
        self._pw = None
        self._browser = None
        self._page = None
        self.session_wid: str | None = None
        self._prev_keys: dict[str, tuple] = {}
        self._prev_grid_values: list | None = None
        self._grid_wh = (VIEWPORT_W, VIEWPORT_H)
        self._pages_visited = 0
        self._actions_taken = 0
        self._change_seq = 0
        self._locator_map: dict[str, dict] = {}     # affordance world-id -> {kind, xpath}
        self._all_element_wids: set[str] = set()      # cumulative, for close()-time pruning
        self._all_affordance_wids: set[str] = set()
        self._all_changeevent_wids: set[str] = set()
        self._current_affordance_wids: list[str] = []  # this-frame legal actions
        # --- live-eye state (CDP screencast -> JBWF shm -> Rust fb_sample) ---
        self._live_eye_fb_id: int | None = None
        self._eye_writer: FbWriter | None = None
        self._cdp = None
        self._cell_wids: dict[tuple[int, int], object] = {}   # (row,col) -> raw Cell NodeID
        self._cell_grid_wh: tuple[int, int] | None = None
        # --- rule-driven-look state (CLAUDE.md: WHEN to sample is the agent's ---
        # --- own rule, not a host fb_sample call; mirror worlds/fb_eye.py) ----
        self._look_trigger_nid: object | None = None   # LookTrigger node id (-wants_look-> session)
        self._look_rule_installed: bool = False        # idempotent guard for the look-rule

    # --- Playwright plumbing (host I/O only) ------------------------------

    def _launch(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        self._page.set_viewport_size({"width": VIEWPORT_W, "height": VIEWPORT_H})
        if self.use_live_eye:
            self._start_live_eye()

    def _on_screencast_frame(self, params: dict) -> None:
        """CDP `Page.screencastFrame` handler: decode the JPEG frame,
        resize to the fixed viewport, channel-swap to BGRA8888, and
        write it into the shm buffer the Rust eye samples. Mechanical
        byte translation, no decisions. ALWAYS acks in `finally` — a
        missed ack just stalls new screencast frames, not fatal, and an
        ack failure must not crash the CDP event thread."""
        try:
            if self._eye_writer is not None:
                data = base64.b64decode(params["data"])
                img = Image.open(io.BytesIO(data)).convert("RGB")
                if img.size != (VIEWPORT_W, VIEWPORT_H):
                    img = img.resize((VIEWPORT_W, VIEWPORT_H))
                rgb = np.asarray(img, dtype=np.uint8)
                bgra = np.empty((VIEWPORT_H, VIEWPORT_W, 4), dtype=np.uint8)
                bgra[..., 0] = rgb[..., 2]
                bgra[..., 1] = rgb[..., 1]
                bgra[..., 2] = rgb[..., 0]
                bgra[..., 3] = 255
                self._eye_writer.write_frame(bgra.tobytes())
        except Exception:  # noqa: BLE001 -- best-effort; a dropped frame just waits for the next
            pass
        finally:
            try:
                if self._cdp is not None:
                    self._cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
            except Exception:  # noqa: BLE001 -- ack failure must not crash the CDP event thread
                pass

    def _start_live_eye(self) -> None:
        """Start a live CDP screencast writing into a fresh JBWF shm
        buffer, and attach the Rust eye to it. Best-effort end to end:
        CDP screencast is known-flaky under some headless Chromium
        configs, so ANY failure here cleans up whatever partial state
        got created and falls back to the screenshot path (`_ingest`
        branches on `self._live_eye_fb_id is None`)."""
        name = f"/jbw_fb_browser_{uuid4().hex[:8]}"
        writer = None
        try:
            writer = FbWriter(name, VIEWPORT_W, VIEWPORT_H, create=True, keep=False)
            self._eye_writer = writer
            cdp = self._page.context.new_cdp_session(self._page)
            self._cdp = cdp
            cdp.on("Page.screencastFrame", self._on_screencast_frame)
            cdp.send("Page.startScreencast", {
                "format": "jpeg", "quality": 80,
                "maxWidth": VIEWPORT_W, "maxHeight": VIEWPORT_H, "everyNthFrame": 1})

            # Don't fb_attach + first-sample a buffer with zero real pixels
            # in it -- poll (short timeout) for the first screencast frame.
            waited_ms, deadline_ms, step_ms = 0, 2000, 20
            while writer.frame_seq() == 0 and waited_ms < deadline_ms:
                self._page.wait_for_timeout(step_ms)
                waited_ms += step_ms
            if writer.frame_seq() == 0:
                raise RuntimeError("live eye: no screencast frame arrived within timeout")

            self._live_eye_fb_id = self.agent.inner.fb_attach(name)
        except Exception:  # noqa: BLE001 -- fall back to the screenshot path, cleanly
            try:
                if self._cdp is not None:
                    self._cdp.send("Page.stopScreencast")
            except Exception:  # noqa: BLE001
                pass
            self._cdp = None
            if writer is not None:
                try:
                    writer.close()
                except Exception:  # noqa: BLE001
                    pass
            self._eye_writer = None
            self._live_eye_fb_id = None
            self.use_live_eye = False

    # --- the 3-call contract ------------------------------------------------

    def reset(self, url: str) -> dict:
        """Launch (or reuse) the browser, navigate to `url`, full ingest at
        both levels. Returns a context dict (session node id + counts)."""
        try:
            from evaluation.p0a.legacy_io_guard import deny_direct_io
            deny_direct_io("browser.launch_apply")
        except ImportError:
            pass
        if self._page is None:
            self._launch()
        self.session_wid = f"session_{uuid4().hex[:8]}"
        self._prev_keys = {}
        self._prev_grid_values = None
        self._pages_visited = 0
        self._actions_taken = 0
        self._page.goto(url, wait_until="load")
        self._pages_visited += 1
        return self._ingest(cold=True)

    def legal_actions(self) -> list:
        """Every currently-afforded action, as `(affordance_world_id,)` —
        the same tuple shape ArcWorld's actions use."""
        return [(wid,) for wid in self._current_affordance_wids]

    def apply(self, action) -> dict:
        """Perform `action` (an affordance world-id, optionally with a
        value to type/select) via Playwright, then incremental re-ingest."""
        try:
            from evaluation.p0a.legacy_io_guard import deny_direct_io
            deny_direct_io("browser.launch_apply")
        except ImportError:
            pass
        name = action[0]
        value = action[1] if len(action) > 1 else None
        if name.startswith("scroll"):
            self._page.mouse.wheel(0, 400)
        else:
            info = self._locator_map.get(name)
            if info is not None:
                loc = self._page.locator(f"xpath={info['xpath']}")
                kind = info["kind"]
                try:
                    if kind == "type":
                        loc.fill(str(value) if value is not None else "")
                    elif kind == "select":
                        if value is not None:
                            loc.select_option(str(value))
                        else:
                            loc.click()
                    else:  # click / navigate
                        loc.click()
                except Exception:  # noqa: BLE001 -- element may have detached under us
                    pass
        try:
            self._page.wait_for_load_state("load", timeout=3000)
        except Exception:  # noqa: BLE001 -- no navigation occurred; that's fine
            pass
        self._page.wait_for_timeout(80)   # let inline-JS DOM mutation settle
        self._actions_taken += 1

        navigated = self._page.url != getattr(self, "_current_url", self._page.url)
        cold = navigated
        if navigated:
            self._pages_visited += 1
            self._prune_session_percepts(keep_session=True)
            self._prev_keys = {}
            self._prev_grid_values = None
        return self._ingest(cold=cold)

    # --- ingest: DOM (native) + screenshot/segment (human-equivalent) + ground -----

    def _walk_dom(self) -> list[dict]:
        return self._page.evaluate(_WALK_JS)

    def _ingest(self, cold: bool) -> dict:
        agent = self.agent
        self._current_url = self._page.url
        records = self._walk_dom()
        new_map = {r["id"]: r for r in records}

        # `region_grouping`'s `prune_consumed_changes` rule deletes any
        # ChangeEvent whose `frame` < its session's `frame`. The live eye's
        # look-rule (the agent's own `fb_sample`-as-effect) stamps the session's
        # `frame` with the shm buffer's frame_seq on every fire -- and now that
        # the WHEN-TO-SAMPLE decision is the agent's rule (not a one-shot host
        # `fb_sample`), that fire happens DURING `agent.observe`'s tick, the
        # live-eye `run_rules`, AND the trailing `agent.tick()`. So a CE minted
        # with the pre-sample frame would be pruned mid-ingest before `_ingest`
        # can read it back. Minting it with the `_CE_LIVE_SENTINEL` (>> any
        # frame_seq) keeps `prune`'s hands off it for the whole ingest; the
        # final-frame re-tag after `agent.tick()` (below) hands it the session's
        # TRUE final frame so the NEXT ingest's first tick retires it -- the
        # rule's "survive this tick, pruned next frame" semantics, robustly.
        g = TypedGraph()
        sess = g._insert_node("BrowserSession", {
            "id": self.session_wid, "url": self._current_url, "status": "open",
            "pages_visited": self._pages_visited, "actions_taken": self._actions_taken})

        changed_ids = [eid for eid, r in new_map.items()
                       if cold or eid not in self._prev_keys
                       or self._prev_keys[eid] != _record_key(r)]
        disappeared = [] if cold else [eid for eid in self._prev_keys if eid not in new_map]

        # sibling order (ALL currently-kept elements, not just changed ones) ->
        # `follows` needs the full doc-order neighbourhood.
        siblings: dict[str | None, list[str]] = {}
        for eid, r in sorted(new_map.items(), key=lambda kv: kv[1]["order"]):
            siblings.setdefault(r.get("parent") or None, []).append(eid)

        touched_affordances: list[str] = []
        new_ce_wids: list[str] = []   # ChangeEvent wids minted THIS ingest (frame re-tagged below)
        for eid in changed_ids:
            r = new_map[eid]
            el_wid = f"el_{eid}"
            eln = g._insert_node("Element", {
                "id": el_wid, "tag": r["tag"], "text": r["text"][:TEXT_MAX_LEN],
                # mechanical lower-case mirror of `text` (host I/O, no decision) — lets a graph rule
                # do CASE-INSENSITIVE substring matching via StringIndexOf, which has no case-fold of
                # its own; see the browse-affordance-choice composer (reflective_faculty.py).
                "text_lc": r["text"][:TEXT_MAX_LEN].lower(),
                "href": r.get("href", ""), "name": r.get("name", ""),
                "value": r.get("value", ""), "itype": r.get("itype", ""),
                "bbox_x": float(r["x"]), "bbox_y": float(r["y"]),
                "bbox_w": float(r["w"]), "bbox_h": float(r["h"]), "present": 1.0})
            parent_eid = r.get("parent")
            if parent_eid:
                pstub = g._insert_node("Element", {"id": f"el_{parent_eid}"})
                g._insert_edge(pstub, "contains", eln)
            else:
                g._insert_edge(sess, "contains", eln)
            sibs = siblings.get(parent_eid or None, [])
            pos = sibs.index(eid) if eid in sibs else -1
            if pos > 0:
                prev_eid = sibs[pos - 1]
                pstub2 = g._insert_node("Element", {"id": f"el_{prev_eid}"})
                g._insert_edge(eln, "follows", pstub2)
            kind = _affordance_kind(r)
            if kind:
                aff_wid = f"aff_{eid}"
                label = (r["text"][:60] or r.get("name") or r.get("href") or r["tag"])
                # mechanical lower-case mirror of `label` — same reason as Element.text_lc above.
                an = g._insert_node("Affordance", {"id": aff_wid, "kind": kind, "label": label,
                                                    "label_lc": label.lower()})
                g._insert_edge(eln, "affords", an)
                self._locator_map[aff_wid] = {"kind": kind, "xpath": _to_xpath(eid)}
                self._all_affordance_wids.add(aff_wid)
                touched_affordances.append(aff_wid)
            self._all_element_wids.add(el_wid)
            if not cold:
                ce_wid = f"chg_{self._change_seq}"
                self._change_seq += 1
                kind_ce = "appeared" if eid not in self._prev_keys else "changed"
                cen = g._insert_node("ChangeEvent", {
                    "id": ce_wid, "kind": kind_ce, "element_id": eid,
                    "seq": self._change_seq, "frame": _CE_LIVE_SENTINEL})
                g._insert_edge(sess, "has_change", cen)
                estub = g._insert_node("Element", {"id": el_wid})
                g._insert_edge(cen, "at_element", estub)
                self._all_changeevent_wids.add(ce_wid)
                new_ce_wids.append(ce_wid)

        for eid in disappeared:
            ce_wid = f"chg_{self._change_seq}"
            self._change_seq += 1
            cen = g._insert_node("ChangeEvent", {
                "id": ce_wid, "kind": "disappeared", "element_id": eid,
                "seq": self._change_seq, "frame": _CE_LIVE_SENTINEL})
            g._insert_edge(sess, "has_change", cen)
            self._all_changeevent_wids.add(ce_wid)
            new_ce_wids.append(ce_wid)

        live_eye = self._live_eye_fb_id is not None
        if live_eye:
            # Pixels flow through the shm buffer the CDP screencast writes
            # (see _start_live_eye/_on_screencast_frame); no GridCell nodes
            # go through the TypedGraph mirror at all -- fb_sample mints/
            # reuses its own Cell WorldInstance nodes directly on the Rust
            # side.
            self._grid_wh = (VIEWPORT_W, VIEWPORT_H)
        else:
            H, W, flat_values, (vw, vh) = _quantize_screenshot(self._page.screenshot())
            self._grid_wh = (vw, vh)
            prev_vals = self._prev_grid_values
            for idx in range(H * W):
                v = flat_values[idx]
                pv = prev_vals[idx] if prev_vals is not None else None
                if cold or pv != v:
                    r, c = idx // W, idx % W
                    gcn = g._insert_node("GridCell", {"id": f"gc_{r}_{c}", "row": r,
                                                       "col": c, "value": int(v)})
                    g._insert_edge(sess, "has_cell", gcn)
            self._prev_grid_values = flat_values

        sub = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
        agent.observe(sub)   # mirror -> WorldInstance nodes + edges, ticks once

        S, I = agent.s, agent.inner
        for eid in disappeared:
            wi = agent._instances.get(("Element", f"el_{eid}"))
            if wi is not None and S.has_node(wi):
                I.set_attr(wi, "present", 0.0)

        sess_wi = agent._instances[("BrowserSession", self.session_wid)]

        # Mirror the agent's own active Goals onto THIS session (mechanical graph mirror,
        # CLAUDE.md-admissible host I/O -- not a decision: a Goal only ever gets minted by
        # the agent's OWN rules, e.g. the browse-affordance-choice composer's comprehension
        # twin; this only makes an already-decided Goal reachable from the session node via
        # `has_goal`, the same edge type a decision rule matches on, so a graph rule can bind
        # BOTH "which session am I choosing an action in" and "what do I want" together).
        # Filtered on status != 'satisfied' only (no kind check) so it stays domain-general.
        for gwi in S.nodes("Goal"):
            if not S.has_node(gwi):
                continue
            if S.node(gwi)["attrs"].get("status") == "satisfied":
                continue
            if not I.has_edge(sess_wi, "has_goal", gwi):
                I.add_edge_unchecked(sess_wi, "has_goal", gwi)

        # `sess -has_affordance-> affordance` is now GRAPH-NATIVE, not a Python flattening loop.
        # The DOM `contains` tree nests affordances at arbitrary depth (a `<nav>` wraps links, a
        # `<form>` wraps inputs) and `-affords->` only ever fires on the AFFORDING element itself.
        # This USED to require a hand-rolled Python mirror because the DSL had no transitive-closure
        # Term to walk `contains*` from a rule; the agent has since authored and the creator installed
        # `ReachableFrom(node, edge_type)` (BFS-to-fixpoint over `Neighbours`, returns a frozenset of
        # NodeIDs), which closes exactly that gap. The `browser_affordance_reach` seed (REQUIRED --
        # see the module docstring) ships two graph-resident rules, registered into the SAME rule
        # store `agent.tick()` drives (`add_rule`, not a graph-resident `Rule` node -- those need the
        # native `Substrate.tick()`, which `WorldAdapter.tick()` does not call):
        #   mint: [sess contains el0] [el affords aff], where el ∈ ReachableFrom(sess, "contains")
        #         AND el.present > 0  ->  add_edge sess has_affordance aff
        #   drop: [sess has_affordance aff] [el affords aff], where NOT el.present > 0
        #         ->  del_edge sess has_affordance aff
        # (`el0` only anchors the `sess` var to a real node via a one-hop `contains` edge -- every
        # ingested page has at least one top-level significant element -- the same var-binding idiom
        # `reflective_faculty.py`'s browse rules already use for a second contained element.) Both
        # rules fire to a full run_rules() fixpoint, so unlike the old Python code there is no
        # "must run before tick()" ordering hazard: whichever tick sees the correct `present` flags
        # (set by the disappeared-handling loop above, before `agent.tick()` below) converges to the
        # correct `has_affordance` edge set, and the browse decision rule (which also lives in that
        # same store) re-fires off the corrected edges within the SAME fixpoint. `present` is checked
        # only on the AFFORDING element itself, matching the OLD code's exact semantics -- when an
        # ancestor disappears from the DOM, `_walk_dom` never re-emits any of its descendants either,
        # so the affording element's OWN record lands in `disappeared` and gets `present=0` too (see
        # the loop above); no ancestor-presence check is needed.
        #
        # `current_affordances` below is UNRELATED host I/O: it is not the graph mirror, it is the
        # world's own external action list (`legal_actions()`'s `apply()` targets), read back out of
        # the same `present` bookkeeping for the CLAUDE.md-admissible "emit" half of this adapter.
        def _element_present(el_wid: str) -> bool:
            wi = agent._instances.get(("Element", el_wid))
            if wi is None or not S.has_node(wi):
                return False
            return float(S.node(wi)["attrs"].get("present", 1.0)) > 0.0

        current_affordances = [aff_wid for aff_wid in self._all_affordance_wids
                                if _element_present("el_" + aff_wid[len("aff_"):])]
        self._current_affordance_wids = current_affordances

        if live_eye:
            # THE WHEN-TO-SAMPLE DECISION IS THE AGENT'S OWN RULE, not a host
            # fb_sample call (CLAUDE.md: perception timing is the agent's, never
            # the host's). The live eye is wired via a LookTrigger node
            # (-wants_look-> this session) carrying (fb_id, grid_w, grid_h), and
            # the agent's look-rule (browser_look_when_frame_advances, installed
            # once by _ensure_look_wiring -- the composed _compose_attention_rule
            # shape, reading its own wiring off graph context, no host-supplied
            # literals) fires fb_sample as an EFFECT, gated by
            # FbFrameSeq(fb_id) > sess.last_looked_seq. run_rules drives it to
            # fixpoint: exactly one sample per genuinely-new frame, zero host
            # fb_sample calls (the closed loop tests/test_rule_driven_look.py
            # proves end to end). fb_sample mints/reuses the same Cell
            # WorldInstance nodes + Regions + bumps sess.frame, so everything
            # downstream (cell-wid cache, ChangeEvent frame re-tag, renders_as)
            # reads graph state the RULE produced -- this branch never calls
            # I.fb_sample itself.
            self._ensure_look_wiring(sess_wi)
            I.run_rules(1000)
            dims = (GRID_W, GRID_H)
            if not self._cell_wids or self._cell_grid_wh != dims:
                self._rebuild_cell_wids(*dims)
        else:
            cell_ids = []
            for r in range(H):
                for c in range(W):
                    wi = agent._instances.get(("GridCell", f"gc_{r}_{c}"))
                    cell_ids.append(int(str(wi).lstrip("#")) if wi is not None else -1)
            I.segment(sess_wi, H, W, flat_values, cell_ids)

        # No pre-`agent.tick()` ChangeEvent re-tag: the CE was minted with
        # `_CE_LIVE_SENTINEL`, so `prune_consumed_changes` (which fires during
        # `agent.tick()` alongside the look-rule) leaves it alone for the whole
        # ingest -- a pre-tick re-tag to the current `frame` would be stale
        # again the moment the look-rule fires inside that same tick. The TRUE
        # final-frame re-tag happens AFTER `agent.tick()` below.
        self._refresh_renders_as(new_map)
        agent.tick()

        if new_ce_wids:
            # Re-tag this ingest's ChangeEvents with the session's TRUE final
            # frame (after the look-rule's last `fb_sample` effect this tick
            # stamped it) so the NEXT ingest's first look-rule firing advances
            # `frame` past them and `prune_consumed_changes` retires them --
            # the rule's own "survive this tick, pruned next frame" semantics.
            # (The sentinel kept `prune` off them DURING this tick; without it
            # the CE would be deleted before this call returns it to the caller.)
            final_frame = float(S.node(sess_wi)["attrs"].get("frame", 0.0))
            for wid in new_ce_wids:
                wi = agent._instances.get(("ChangeEvent", wid))
                if wi is not None and S.has_node(wi):
                    I.set_attr(wi, "frame", final_frame)

        self._prev_keys = {eid: _record_key(r) for eid, r in new_map.items()}

        n_elements = sum(1 for wid in self._all_element_wids if _element_present(wid))
        n_regions = sum(1 for _ in I.neighbours(sess_wi, "has_region"))
        return {"session": sess_wi, "url": self._current_url, "cold": cold,
                "elements": n_elements, "affordances": len(self._current_affordance_wids),
                "regions": n_regions, "changed": len(changed_ids),
                "disappeared": len(disappeared)}

    def _rebuild_cell_wids(self, grid_w: int, grid_h: int) -> None:
        """Scan the agent's own WorldInstance nodes for the Cell nodes
        `fb_sample` mints/reuses (`world_type == "Cell"`, `world_id ==
        "{row}_{col}"`), building a `(row, col) -> raw NodeID` cache.
        `fb_sample` mints these ONCE per (fb_id, grid dims, game) triple
        and reuses the same node ids on every later call -- this cache
        mirrors that lifetime, so it's cheap to rebuild only the first
        time (empty cache) or if the grid dims ever change (defensive;
        GRID_W/GRID_H are fixed module constants so in practice never)."""
        agent = self.agent
        S, I = agent.s, agent.inner
        cache: dict[tuple[int, int], object] = {}
        for nid in I.nodes("WorldInstance"):
            if not S.has_node(nid):
                continue
            attrs = I.node(nid)["attrs"]
            if attrs.get("world_type") != "Cell":
                continue
            cache[(int(attrs["row"]), int(attrs["col"]))] = nid
        self._cell_wids = cache
        self._cell_grid_wh = (grid_w, grid_h)

    def _ensure_look_rule_installed(self) -> None:
        """Install the canonical look-rule ONCE into the Rust rule store
        `agent.tick()`/`run_rules` drive (the SAME store the
        `browser_affordance_reach` seed's rules live in -- registering a
        rule here is mechanical host setup, NOT running the Python rule
        engine and NOT an agent decision; the WHEN-to-sample decision is
        the rule's own where-clause, made at fixpoint time). This is the
        composed `domains.reflective_faculty._compose_attention_rule`
        shape generalised to read its own wiring off graph context -- no
        host-supplied literal fb_id/grid dims (those come from the
        LookTrigger a world adapter stamps). If the agent has already
        self-composed an equivalent rule (the fb_eye contract), this
        idempotently coexists: the where-clause watermark makes a
        duplicate harmless -- one rule fires per new frame, the gate
        closes, the second sees the advanced watermark and stays silent."""
        if self._look_rule_installed:
            return
        V = lambda n: {"type": "Var", "name": n}
        Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
        Gt = lambda a, b: {"type": "Gt", "a": a, "b": b}
        FbSeq = lambda fb: {"type": "FbFrameSeq", "fb": fb}
        fb_id_t = Attr(V("t"), "fb_id")
        rule = {
            "name": "browser_look_when_frame_advances",
            "match": [["t", "wants_look", "g"]],
            "where": Gt(FbSeq(fb_id_t), Attr(V("g"), "last_looked_seq")),
            "effects": [
                ["fb_sample", {"__term__": fb_id_t}, "g",
                 {"__term__": Attr(V("t"), "grid_w")},
                 {"__term__": Attr(V("t"), "grid_h")}],
                ["set_attr", "g", "last_looked_seq", {"__term__": FbSeq(fb_id_t)}],
            ],
        }
        try:
            self.agent.inner.add_rule(rule)
        except Exception:  # noqa: BLE001 -- best-effort: an equivalent self-composed rule may already exist
            pass
        self._look_rule_installed = True

    def _ensure_look_wiring(self, sess_wi) -> None:
        """Stamp the LookTrigger graph context the agent's look-rule reads
        (mirror ``worlds/fb_eye.py::attach_eye``): a ``LookTrigger`` carrying
        ``(fb_id, grid_w, grid_h)`` wired ``-wants_look->`` this session,
        plus the session's ``last_looked_seq`` watermark (set to -1.0 ONLY
        when absent, so it persists across ingests within one session; a
        fresh session has none -> -1.0 -> the rule fires on the first new
        framebuffer frame). Mechanical host I/O -- no decision about WHEN
        to sample lives here; the rule's where-clause decides."""
        agent = self.agent
        S, I = agent.s, agent.inner
        self._ensure_look_rule_installed()
        trig = self._look_trigger_nid
        if trig is None or not S.has_node(trig):
            trig = S.add_node("LookTrigger", {
                "fb_id": float(self._live_eye_fb_id),
                "grid_w": float(GRID_W), "grid_h": float(GRID_H),
            })
            self._look_trigger_nid = trig
        else:
            I.set_attr(trig, "fb_id", float(self._live_eye_fb_id))
            I.set_attr(trig, "grid_w", float(GRID_W))
            I.set_attr(trig, "grid_h", float(GRID_H))
        # Re-point wants_look at the current session: drop any stale edge to a
        # prior session (a reset mints a new session_wid) so the rule matches
        # exactly THIS session, then add the edge if absent (idempotent).
        for prev in list(I.neighbours(trig, "wants_look")):
            if prev != sess_wi:
                try:
                    I.remove_edge(trig, "wants_look", prev)
                except Exception:  # noqa: BLE001 -- stale target, best-effort drop
                    pass
        if not I.has_edge(trig, "wants_look", sess_wi):
            I.add_edge_unchecked(trig, "wants_look", sess_wi)
        # Watermark: set only if absent so it survives across this session's
        # later ingests (the rule advances it itself after each sample).
        if S.has_node(sess_wi):
            if S.node(sess_wi)["attrs"].get("last_looked_seq") is None:
                I.set_attr(sess_wi, "last_looked_seq", -1.0)

    def _refresh_renders_as(self, new_map: dict) -> None:
        """Cross-level grounding: element bbox -> covered grid cells ->
        the Region(s) those cells are `within` -> `element -renders_as->
        region`, added directly on the agent's live substrate (Region only
        exists there, post-`segment`/`fb_sample`). Pure geometry, no
        decision. Cell lookup branches on which pixel source is live:
        the live eye's `(row, col) -> NodeID` cache, or the old TypedGraph-
        mirrored `("GridCell", "gc_{r}_{c}")` instance index."""
        agent = self.agent
        S, I = agent.s, agent.inner
        vw, vh = self._grid_wh
        live_eye = self._live_eye_fb_id is not None
        for eid, r in new_map.items():
            el_wi = agent._instances.get(("Element", f"el_{eid}"))
            if el_wi is None or not S.has_node(el_wi):
                continue
            x0 = max(0, min(GRID_W - 1, int(r["x"] / max(vw, 1) * GRID_W)))
            y0 = max(0, min(GRID_H - 1, int(r["y"] / max(vh, 1) * GRID_H)))
            x1 = max(0, min(GRID_W - 1, int((r["x"] + max(r["w"], 1)) / max(vw, 1) * GRID_W)))
            y1 = max(0, min(GRID_H - 1, int((r["y"] + max(r["h"], 1)) / max(vh, 1) * GRID_H)))
            regions: set = set()
            for rr in range(y0, y1 + 1):
                for cc in range(x0, x1 + 1):
                    if live_eye:
                        gc_wi = self._cell_wids.get((rr, cc))
                    else:
                        gc_wi = agent._instances.get(("GridCell", f"gc_{rr}_{cc}"))
                    if gc_wi is None or not S.has_node(gc_wi):
                        continue
                    for reg in I.neighbours(gc_wi, "within"):
                        regions.add(reg)
            for reg in list(I.neighbours(el_wi, "renders_as")):
                if reg not in regions:
                    try:
                        I.remove_edge(el_wi, "renders_as", reg)
                    except Exception:  # noqa: BLE001 -- stale target, best-effort drop
                        pass
            for reg in regions:
                if S.has_node(reg) and not I.has_edge(el_wi, "renders_as", reg):
                    I.add_edge_unchecked(el_wi, "renders_as", reg)

    # --- episodic lifecycle ---------------------------------------------------

    def session_node(self):
        """The mirrored BrowserSession WorldInstance node id, or None."""
        if self.session_wid is None:
            return None
        return self.agent._instances.get(("BrowserSession", self.session_wid))

    def _prune_session_percepts(self, keep_session: bool = True, closing: bool = False) -> None:
        """Remove the raw sensory subgraph (Element / Affordance / GridCell
        or Cell / ChangeEvent / Region) minted under this session.
        Mechanical cleanup — what the agent LEARNED (concepts/rules/taught
        nodes) lives elsewhere in the graph and is untouched.

        `closing`: True only from `close()` (true session teardown), False
        from `apply()`'s mid-session navigation prune. This matters ONLY
        for the live-eye Cell nodes: `fb_sample`'s Rust-side cache is keyed
        by (fb_id, grid dims, game) and `game` (`sess_wi`) is STABLE across
        navigation within one session (only `reset()` changes
        `session_wid`) — so `fb_sample` expects to keep reusing the SAME
        Cell node ids on every later call for the life of the session.
        Deleting them out from under it mid-session panics the next
        `fb_sample` ("node id refers to a freed slot"); it's only safe once
        `close()` has also `fb_detach`ed (no further `fb_sample` calls for
        this fb_id will ever happen)."""
        agent = self.agent
        S, I = agent.s, agent.inner
        sess_wi = self.session_node()
        if sess_wi is not None and S.has_node(sess_wi):
            for reg in list(I.neighbours(sess_wi, "has_region")):
                if S.has_node(reg):
                    I.remove_node(reg)
        for wid in list(self._all_element_wids):
            wi = agent._instances.pop(("Element", wid), None)
            if wi is not None and S.has_node(wi):
                I.remove_node(wi)
        for wid in list(self._all_affordance_wids):
            wi = agent._instances.pop(("Affordance", wid), None)
            if wi is not None and S.has_node(wi):
                I.remove_node(wi)
        for wid in list(self._all_changeevent_wids):
            wi = agent._instances.pop(("ChangeEvent", wid), None)
            if wi is not None and S.has_node(wi):
                I.remove_node(wi)
        if self._live_eye_fb_id is not None:
            if closing:
                for wi in list(self._cell_wids.values()):
                    if S.has_node(wi):
                        I.remove_node(wi)
                self._cell_wids = {}
                # The LookTrigger control node lives for the session and is
                # re-pointed across navigations; only a true close() (which
                # also fb_detach'es) removes it -- the rule's wants_look edge
                # would otherwise dangle off a detached framebuffer.
                if self._look_trigger_nid is not None and S.has_node(self._look_trigger_nid):
                    I.remove_node(self._look_trigger_nid)
                self._look_trigger_nid = None
            # else: leave the live-eye Cell nodes (and cache) alone -- see
            # docstring above.
        else:
            for r in range(GRID_H):
                for c in range(GRID_W):
                    key = ("GridCell", f"gc_{r}_{c}")
                    wi = agent._instances.pop(key, None)
                    if wi is not None and S.has_node(wi):
                        I.remove_node(wi)
        self._all_element_wids.clear()
        self._all_affordance_wids.clear()
        self._all_changeevent_wids.clear()
        self._current_affordance_wids = []
        self._locator_map.clear()
        if not keep_session and sess_wi is not None:
            agent._instances.pop(("BrowserSession", self.session_wid), None)
            if S.has_node(sess_wi):
                I.remove_node(sess_wi)

    def close(self) -> None:
        """Prune the raw sensory subgraph, leave the BrowserSession root as
        the durable episodic record, and release Playwright resources."""
        agent = self.agent
        S, I = agent.s, agent.inner
        sess_wi = self.session_node()
        self._prune_session_percepts(keep_session=True, closing=True)
        if sess_wi is not None and S.has_node(sess_wi):
            I.set_attr(sess_wi, "status", "closed")
            I.set_attr(sess_wi, "pages_visited", self._pages_visited)
            I.set_attr(sess_wi, "actions_taken", self._actions_taken)
        if self._cdp is not None:
            try:
                self._cdp.send("Page.stopScreencast")
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
            self._cdp = None
        if self._live_eye_fb_id is not None:
            try:
                self.agent.inner.fb_detach(self._live_eye_fb_id)
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
            self._live_eye_fb_id = None
        if self._eye_writer is not None:
            try:
                self._eye_writer.close()
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
            self._eye_writer = None
        if self._page is not None:
            try:
                self._page.close()
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:  # noqa: BLE001
                pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:  # noqa: BLE001
                pass
        self._page = self._browser = self._pw = None
