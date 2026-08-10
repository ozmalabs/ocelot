#!/usr/bin/env python3
"""Non-cognitive runtime status and read-only graph inspection client."""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request


def _get(base: str, path: str, query: dict | None = None) -> dict:
    url = base.rstrip("/") + path
    if query:
        query = {key: value for key, value in query.items() if value is not None}
        url += "?" + urllib.parse.urlencode(query)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="inspect a running Jabberwock without invoking cognition")
    parser.add_argument("--base", default="http://127.0.0.1:8787")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="constant-time host runtime status")
    commands.add_parser("summary", help="read-only graph summary")

    nodes = commands.add_parser("nodes", help="page through raw graph nodes")
    nodes.add_argument("--type")
    nodes.add_argument("--offset", type=int, default=0)
    nodes.add_argument("--limit", type=int, default=100)

    node = commands.add_parser("node", help="show one node and its incident edges")
    node.add_argument("id")

    edges = commands.add_parser("edges", help="page through raw graph edges")
    edges.add_argument("--type")
    edges.add_argument("--source", type=int)
    edges.add_argument("--target", type=int)
    edges.add_argument("--offset", type=int, default=0)
    edges.add_argument("--limit", type=int, default=100)

    rules = commands.add_parser("rules", help="page through executable rules")
    rules.add_argument("--name")
    rules.add_argument("--offset", type=int, default=0)
    rules.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if args.command == "status":
        result = _get(args.base, "/api/runtime/status")
    elif args.command == "summary":
        result = _get(args.base, "/api/debug/graph")
    elif args.command == "nodes":
        result = _get(args.base, "/api/debug/graph/nodes", {
            "type": args.type, "offset": args.offset, "limit": args.limit})
    elif args.command == "node":
        result = _get(args.base, "/api/debug/graph/nodes/" + urllib.parse.quote(args.id))
    elif args.command == "edges":
        result = _get(args.base, "/api/debug/graph/edges", {
            "type": args.type, "source": args.source, "target": args.target,
            "offset": args.offset, "limit": args.limit})
    else:
        result = _get(args.base, "/api/debug/graph/rules", {
            "name": args.name, "offset": args.offset, "limit": args.limit})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
