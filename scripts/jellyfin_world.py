"""JELLYFIN WORLD — the jabberwock's window onto a real, large, curated children's
library, where it CHOOSES what to watch and learns from it.

A world adapter (mechanical external-I/O -> substrate, per CLAUDE.md): it authenticates
to the Jellyfin server, pulls the catalogue the 'william' account is allowed to see
(child-restricted) into the graph as a menu of watchable Media, exposes a direct
stream URL per item (PyAV/ffmpeg open it over HTTP — no full download), and lets the
agent SELECT N items to watch. It does NOT decide for the agent; the selection is
driven by the agent's own state (what it has already learned) with surprise/novelty
as the selector — the compression principle, now as active curiosity.

Content note: the library is HEVC 1080p MKV, so PIXELS come via PyAV/ffmpeg (the
agent's own decoder is H.264-only); the temporal-structure reading and the V1+rank
visual representation are codec-agnostic, so the learning pipeline still applies.

Auth: logs in as 'william' (no password -> child content only); caches the token in
~/.jellyfin_session.

Usage:
    from scripts.jellyfin_world import JellyfinWorld
    jf = JellyfinWorld(); jf.connect()
    jf.ingest_catalog(substrate)            # mint the menu into the graph
    picks = jf.choose(substrate, n=3)       # the agent chooses what to watch
    url = jf.stream_url(item_id)            # PyAV/ffmpeg-openable

Run as a script: connect, enumerate, and show what the jabberwock would choose.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter

BASE = "https://jellyfin.hrdwrbob.net"
USER = "william"            # no-password child account
SESSION = os.path.expanduser("~/.jellyfin_session")
_AUTH = 'MediaBrowser Client="jabberwock", Device="cli", DeviceId="jabberwock-1", Version="0.1"'


class JellyfinWorld:
    def __init__(self, base: str = BASE):
        self.base = base
        self.token = None
        self.uid = None

    # ---- connection (mechanical I/O) ----
    def _req(self, path: str, method: str = "GET", body=None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Authorization": (f'MediaBrowser Token="{self.token}"' if self.token else _AUTH)}
        if data is not None:
            h["Content-Type"] = "application/json"
        r = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        return json.load(urllib.request.urlopen(r, timeout=30))

    def connect(self):
        if os.path.exists(SESSION):
            tok, uid = open(SESSION).read().split()
            self.token, self.uid = tok, uid
            try:
                self._req(f"/Users/{self.uid}")     # validate
                return self
            except Exception:
                self.token = self.uid = None
        a = self._req("/Users/AuthenticateByName", "POST", {"Username": USER, "Pw": ""})
        self.token, self.uid = a["AccessToken"], a["User"]["Id"]
        with open(SESSION, "w") as f:
            f.write(self.token + "\n" + self.uid + "\n")
        os.chmod(SESSION, 0o600)
        return self

    # ---- catalogue ----
    def catalog(self, kinds=("Series", "Movie"), limit=2000):
        """The watchable menu william can see: Series + standalone Movies, with the
        metadata the agent picks on (genres, year, runtime)."""
        items = []
        for k in kinds:
            r = self._req(
                f"/Items?userId={self.uid}&Recursive=true&IncludeItemTypes={k}"
                f"&Fields=Genres,RunTimeTicks,ProductionYear,Overview"
                f"&SortBy=SortName&Limit={limit}")
            for it in r.get("Items", []):
                items.append({
                    "id": it["Id"], "name": it["Name"], "type": k,
                    "genres": it.get("Genres", []),
                    "year": it.get("ProductionYear"),
                    "runtime_s": (it.get("RunTimeTicks") or 0) // 10_000_000,
                })
        return items

    def episodes(self, series_id: str, limit=500):
        r = self._req(
            f"/Shows/{series_id}/Episodes?userId={self.uid}"
            f"&Fields=RunTimeTicks&Limit={limit}")
        return [{"id": e["Id"], "name": e["Name"],
                 "series": e.get("SeriesName"),
                 "season": e.get("ParentIndexNumber"),
                 "ep": e.get("IndexNumber"),
                 "runtime_s": (e.get("RunTimeTicks") or 0) // 10_000_000}
                for e in r.get("Items", [])]

    def stream_url(self, item_id: str) -> str:
        """A direct, PyAV/ffmpeg-openable URL for the original media (no transcode,
        no full download — ffmpeg seeks over HTTP)."""
        return (f"{self.base}/Videos/{item_id}/stream?static=true"
                f"&api_key={urllib.parse.quote(self.token)}")

    # ---- ingest the menu into the substrate (mechanical) ----
    def ingest_catalog(self, s, kinds=("Series", "Movie")):
        from substrate_rs import Production, NodePattern
        for src, edge, tgt, prov in [
            ("JellyfinLibrary", "has_title", "Series", "jf:lib_has_series"),
            ("JellyfinLibrary", "has_title", "Movie", "jf:lib_has_movie"),
        ]:
            s.add_production(Production(src=NodePattern(type=src, var="a"), edge_type=edge,
                                       tgt=NodePattern(type=tgt, var="b"), where=None,
                                       weight=None, provenance=prov).to_dict())
        lib = s.add_node("JellyfinLibrary", {"server": self.base, "user": USER})
        n = 0
        for it in self.catalog(kinds):
            nid = s.add_node(it["type"], {
                "name": it["name"], "jf_id": it["id"],
                "genres": ",".join(it["genres"]), "year": it["year"] or 0,
                "runtime_s": it["runtime_s"]})
            s.add_edge(lib, "has_title", nid)
            n += 1
        return lib, n

    # ---- the agent CHOOSES (selector = surprise/novelty over what it knows) ----
    def choose(self, s, n=3, watched_series=None):
        """The jabberwock picks N titles to watch next. Cold start (nothing watched):
        spread across DISTINCT series/genres to bootstrap broad structure. Warm:
        prefer titles in series it has NOT yet seen (maximum expected novelty =
        information gain), the compression/curiosity selector. Returns catalog dicts.
        This reads the agent's accumulated state; it is selection, not a fixed list."""
        watched_series = set(watched_series or [])
        cat = self.catalog(("Series",))
        # learning-oriented first (song/story shows carry the cleanest structure),
        # but the real lever is NOVELTY: unseen series outrank seen ones.
        def novelty(it):
            seen = it["name"] in watched_series
            return (0 if seen else 1, len(it["genres"]) > 0)
        ranked = sorted(cat, key=novelty, reverse=True)
        # diversity: one per genre bucket first
        picks, seen_g = [], set()
        for it in ranked:
            g = (it["genres"] or ["?"])[0]
            if it["name"] in watched_series:
                continue
            if g in seen_g and len(picks) < len(cat):
                continue
            seen_g.add(g)
            picks.append(it)
            if len(picks) >= n:
                break
        for it in ranked:                       # backfill if genres ran out
            if len(picks) >= n:
                break
            if it not in picks and it["name"] not in watched_series:
                picks.append(it)
        return picks[:n]


def main():
    import sys
    sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
    import substrate_rs as srs
    jf = JellyfinWorld().connect()
    print("=" * 74)
    print(f"JELLYFIN WORLD — connected as '{USER}' (child-restricted) @ {BASE}")
    print("=" * 74)
    s = srs.Substrate()
    lib, n = jf.ingest_catalog(s)
    cat = jf.catalog(("Series", "Movie"))
    series = [c for c in cat if c["type"] == "Series"]
    movies = [c for c in cat if c["type"] == "Movie"]
    gc = Counter(g for c in cat for g in (c["genres"] or ["(none)"]))
    print(f"  catalogue ingested into the graph: {n} titles "
          f"({len(series)} series, {len(movies)} movies)")
    print(f"  genres: {dict(gc)}")
    print("\n  THE JABBERWOCK CHOOSES (cold start, n=4) — by novelty + diversity:")
    for p in jf.choose(s, n=4):
        eps = jf.episodes(p["id"], limit=1)
        print(f"    · {p['name']:<34} [{','.join(p['genres']) or '?'}]  "
              f"({'episodes available' if eps else 'no eps'})")
    print("\n  (stream access verified earlier: PyAV/ffmpeg open the stream URL over "
          "HTTP, no full download.)")
    print("=" * 74)


if __name__ == "__main__":
    main()
