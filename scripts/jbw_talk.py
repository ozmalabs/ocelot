#!/usr/bin/env python3
"""jbw_talk — a thin client that talks to the running jabberwock daemon over its Unix
socket. Attaches/detaches live; the agent keeps running (and remembering) whether or not
anyone is connected. This is the out-of-process talk path of the always-on daemon — and
the first instance of an attachable world (Phase 2 → Phase 3).

    # one-shot:
    python3 scripts/jbw_talk.py "what are you?"
    # interactive (REPL):
    python3 scripts/jbw_talk.py
"""
from __future__ import annotations

import argparse
import os
import socket
import sys


def _send(sock_path: str, line: str) -> str:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(sock_path)
    with s, s.makefile("rwb", buffering=0) as f:
        f.write((line.replace("\n", " ") + "\n").encode("utf-8"))
        reply = f.readline().decode("utf-8", "replace").rstrip("\n")
    return reply


def main() -> int:
    ap = argparse.ArgumentParser(description="talk to the running jabberwock")
    ap.add_argument("message", nargs="*", help="one-shot message (omit for a REPL)")
    ap.add_argument("--socket", default=os.path.expanduser("~/.jabberwock/jbw.sock"))
    args = ap.parse_args()

    if not os.path.exists(args.socket):
        print(f"no daemon socket at {args.socket} — is jabberwock_daemon running?",
              file=sys.stderr)
        return 2

    if args.message:
        print(_send(args.socket, " ".join(args.message)))
        return 0

    print(f"talking to jabberwock @ {args.socket}  (Ctrl-D / Ctrl-C to leave; "
          "the agent keeps running)")
    try:
        while True:
            try:
                line = input("you › ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue
            try:
                print(f"jbw › {_send(args.socket, line)}")
            except (ConnectionError, FileNotFoundError, OSError) as e:
                print(f"(daemon unreachable: {e})", file=sys.stderr)
                break
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
