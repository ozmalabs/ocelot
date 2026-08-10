"""arc3_live_env — the LIVE HTTP transport for ARC-AGI-3, a drop-in replacement
for the offline ``arc3_env.Arc3Env`` that talks to the real public-preview API
at https://three.arcprize.org instead of a re-implemented rule set.

WHY THIS FILE EXISTS. ``arc3_env.py`` is a FAITHFUL OFFLINE re-implementation of
the published ARC-3 interaction contract (64x64 grids, RESET / ACTION1..7 /
ACTION6(x,y), GameState NOT_PLAYED/NOT_FINISHED/WIN/GAME_OVER). The agent and the
world ADAPTER (``domains/arc3_world.py``) only ever see that contract. This module
swaps the env BEHIND step() for a live HTTP client — the rules now live on the
server, and the agent must infer them from real interaction. The adapter and the
CuriousAgent are UNCHANGED; only the transport differs (exactly as the offline
files always promised: "the SAME agent code would drive the real API by swapping
this Env for an HTTP client").

THE LIVE PROTOCOL (confirmed against the running API + the official `arc_agi`
SDK's RemoteEnvironmentWrapper, June 2026):

  · AUTH         — header ``X-Api-Key: <ARC_API_KEY>`` on every request. The key
                   is read ONLY from os.environ['ARC_API_KEY']; it is never
                   written to disk or hardcoded.
  · SESSION      — ``POST /api/scorecard/open`` sets AWS ALB affinity cookies
                   (``AWSALBAPP-*``). Those cookies MUST be carried on the
                   subsequent /api/cmd/* calls (a requests.Session does this),
                   or the command lands on a backend that returns
                   ``{"error":"SERVER_ERROR","message":"game ... not found"}``.
                   This is the one non-obvious wire detail.
  · RESET        — ``POST /api/cmd/RESET`` with body
                   {"card_id": <scorecard>, "game_id": <full game_id>}; returns
                   the first frame + a ``guid`` identifying the episode.
  · ACTIONn      — ``POST /api/cmd/ACTION{1..7}`` with body
                   {"game_id": ..., "guid": ...}; ACTION6 additionally carries
                   integer "x" and "y" (0..63).
  · FRAME        — JSON {game_id, guid, state, frame:[64x64 grid], levels_completed,
                   win_levels, available_actions, action_input, full_reset}.
                   NOTE the two differences from the offline re-impl:
                     (a) there is NO ``score`` field — progress is
                         ``levels_completed`` (we map it onto Frame.score so the
                         adapter is byte-for-byte unchanged);
                     (b) the server reports ``available_actions`` (e.g. [6] means
                         only ACTION6 is currently legal). We expose it so the
                         driver can honour it.

The grid VALUES are opaque colour indices 0..15 exactly as offline; 0 is
background. The real frames are DENSE (vc33: ~2880 non-empty cells of 4096) —
far richer than the offline toy games — which is the honest difficulty gap.

NO substrate dependency here — this is purely the WORLD/transport, like
arc3_env. All reasoning lives in the CuriousAgent (a graph).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import requests

# Reuse the protocol symbols (Frame / GameState / ACTION names) from the offline
# env so the adapter import in domains/arc3_world.py needs ZERO changes — the
# live env is the same contract, different transport.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from arc3_env import (  # noqa: E402
    Frame,
    GameState,
    RESET,
    ACTION1, ACTION2, ACTION3, ACTION4, ACTION5, ACTION6, ACTION7,
)

DEFAULT_BASE_URL = "https://three.arcprize.org"

# action-name -> ACTION{n} endpoint suffix the server expects.
_ACTION_ENDPOINT = {
    RESET: "RESET",
    ACTION1: "ACTION1", ACTION2: "ACTION2", ACTION3: "ACTION3",
    ACTION4: "ACTION4", ACTION5: "ACTION5", ACTION6: "ACTION6",
    ACTION7: "ACTION7",
}

# server's integer action ids -> our action-name constants (for available_actions).
_ID_TO_ACTION = {
    1: ACTION1, 2: ACTION2, 3: ACTION3, 4: ACTION4,
    5: ACTION5, 6: ACTION6, 7: ACTION7,
}


class Arc3ApiError(RuntimeError):
    pass


class Arc3LiveEnv:
    """Live analogue of ``arc3_env.Arc3Env`` backed by the real HTTP API.

    Exposes the same surface the adapter uses: ``game_id``, ``reset()`` and
    ``step(action, coord)`` returning a ``Frame`` with ``.grid`` / ``.score`` /
    ``.state``. Additionally surfaces ``available_actions`` (the server-legal
    action set for the current frame), which the offline env did not have.

    The scorecard is opened lazily on first reset(). The AWS ALB session cookie
    set by scorecard/open is carried automatically via the requests.Session.
    """

    def __init__(
        self,
        game_id: str,
        base_url: str = DEFAULT_BASE_URL,
        tags: Optional[List[str]] = None,
        timeout: float = 30.0,
    ) -> None:
        api_key = os.environ.get("ARC_API_KEY")
        if not api_key:
            raise Arc3ApiError(
                "ARC_API_KEY is not set in the environment. "
                "Export it (export ARC_API_KEY=...) before running; it is never "
                "read from disk."
            )
        self.game_id = game_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._tags = tags or ["jabberwock"]
        self._session = requests.Session()
        self._session.headers.update({
            "X-Api-Key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self._card_id: Optional[str] = None
        self._guid: Optional[str] = None
        self.available_actions: List[str] = []

    # -- HTTP helpers -----------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        try:
            data = resp.json()
        except ValueError:
            raise Arc3ApiError(f"{path}: non-JSON response ({resp.status_code}): "
                               f"{resp.text[:200]}")
        if isinstance(data, dict) and data.get("error"):
            raise Arc3ApiError(f"{path}: {data.get('error')}: {data.get('message')}")
        resp.raise_for_status()
        return data

    def _open_scorecard(self) -> str:
        data = self._post("/api/scorecard/open", {"tags": self._tags})
        card = data.get("card_id")
        if not card:
            raise Arc3ApiError(f"scorecard/open returned no card_id: {data}")
        return card

    # -- Frame construction ----------------------------------------------
    def _to_frame(self, data: dict, action_input) -> Frame:
        """Translate the live JSON response into the offline ``Frame`` shape.

        ``levels_completed`` -> Frame.score so the adapter (which reads
        frame.score) needs no change. ``available_actions`` (ints) is decoded
        and cached on the env for the driver to honour."""
        grids = data.get("frame") or [[]]
        state = GameState(data.get("state", GameState.NOT_FINISHED.value))
        self._guid = data.get("guid", self._guid)
        avail_ids = data.get("available_actions") or []
        self.available_actions = [
            _ID_TO_ACTION[i] for i in avail_ids if i in _ID_TO_ACTION
        ]
        return Frame(
            game_id=data.get("game_id", self.game_id),
            guid=self._guid or "",
            state=state,
            score=int(data.get("levels_completed", 0) or 0),
            frame=grids,
            action_input=action_input,
        )

    # -- the protocol (live) ---------------------------------------------
    def reset(self) -> Frame:
        if self._card_id is None:
            self._card_id = self._open_scorecard()
        payload = {"card_id": self._card_id, "game_id": self.game_id}
        if self._guid:
            payload["guid"] = self._guid
        data = self._post("/api/cmd/RESET", payload)
        return self._to_frame(data, action_input=(RESET, None))

    def step(self, action: str, coord: Optional[Tuple[int, int]] = None,
             reasoning=None) -> Frame:
        if action == RESET:
            return self.reset()
        if self._guid is None:
            # Mirror the offline env: a step before reset just resets.
            return self.reset()
        endpoint = _ACTION_ENDPOINT.get(action)
        if endpoint is None:
            raise Arc3ApiError(f"unknown action {action!r}")
        payload = {"game_id": self.game_id, "guid": self._guid}
        # The agent's own words for what it is doing + why — routed to the API's
        # `reasoning` field (the "thinking" surfaced in replays). A string is wrapped;
        # a dict passes through. Omitted when None so nothing changes for callers
        # that don't narrate.
        if reasoning is not None:
            payload["reasoning"] = ({"thought": reasoning} if isinstance(reasoning, str)
                                    else reasoning)
        if action == ACTION6:
            # The server requires x,y for ACTION6 (a bare ACTION6 returns HTTP
            # 500). The adapter always supplies a coordinate; guard anyway.
            if coord is None:
                raise Arc3ApiError("ACTION6 requires a coordinate (x, y)")
            x, y = coord
            payload["x"] = int(x)
            payload["y"] = int(y)
        data = self._post(f"/api/cmd/{endpoint}", payload)
        return self._to_frame(data, action_input=(action, coord))

    def close_scorecard(self) -> Optional[dict]:
        """Best-effort scorecard close — reports the server-side tally."""
        if self._card_id is None:
            return None
        try:
            return self._post("/api/scorecard/close", {"card_id": self._card_id})
        except Exception:
            return None


if __name__ == "__main__":
    # Smoke test: reset a public game and step ACTION6 a few times. Requires
    # ARC_API_KEY in the environment. Prints the live frame shape + transitions.
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="vc33-5430563c")
    ap.add_argument("--steps", type=int, default=3)
    args = ap.parse_args()

    env = Arc3LiveEnv(args.game)
    f = env.reset()
    g = f.grid
    nz = sum(1 for row in g for v in row if v != 0)
    print(f"reset: state={f.state.value} score={f.score} "
          f"grid={len(g)}x{len(g[0])} non_empty={nz} "
          f"available={env.available_actions}")
    for i in range(args.steps):
        f = env.step(ACTION6, (32, 32))
        nz = sum(1 for row in f.grid for v in row if v != 0)
        print(f"step{i}: state={f.state.value} score={f.score} "
              f"non_empty={nz} available={env.available_actions}")
    print("scorecard:", env.close_scorecard())
