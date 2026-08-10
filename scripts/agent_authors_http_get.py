"""PoC: the JABBERWOCK attempts to author the http_get primitive through its OWN
code-writing faculty (runtime_design specify + emit) — the bootstrap seed for the
web-as-WORLD.

THE CRUX (the question this script answers): all session the agent's code-writing
(runtime_design.agent_specify_* + emit_primitive_rust) authored primitives that
REDUCE TO HELD COMPOSITION — Rust Term-trees over held ops (ArgMax/DtwTo) or held
tower primitives over the held integer/cup ring (SNF, partition-rank, AHSS-E_2,
Steenrod). Every one is "composition inside the held basis."

http_get is a DIFFERENT REGISTER: an EXTERNAL-IO binding — code reaching OUTSIDE
the substrate to a network library, bringing bytes back from a remote host. The
agent has never authored that. This PoC tests whether its code-writing can author
ONE external-IO primitive.

Sequence (the agent does it; this script orchestrates):
  1. SPEC   — agent_specify_http_get: the agent specifies http_get as an
              EXTERNAL-IO effector (the new register), grounded in its held
              network_protocols science. It records is_new_register=True +
              reduces_to a HOST network library (NOT a held op).
  2. PROBE  — show the math-only emitter (emit_primitive_rust) CANNOT author it
              (raises) — the register gap is real, not asserted.
  3. AUTHOR — emit_external_io_binding: the agent's mechanical emitter, extended
              with an external-IO template, authors the urllib world-adapter
              binding (GET only, UA, timeout). Deterministic, NO LLM.
  4. FETCH  — execute the authored binding on a SAFE endpoint (example.com /
              httpbin GET) -> a REAL network call. Confirm by the MECHANISM
              (status 200 + byte-count + a tiny non-copyrighted marker). NO fake.

Outcome reported honestly: (a) authored + runs + FETCHES (seed works);
(b) authored but run/network blocked (run-grant boundary); (c) cannot author
external-IO (the wall).

GET only; a safe, non-copyrighted test endpoint; NO copyrighted content dumped.

Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/agent_authors_http_get.py
"""
from __future__ import annotations

import os
import sys
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native
from domains import runtime_design as rd


def main() -> int:
    s = _native.Substrate()

    # ------------------------------------------------------------------ 1. SPEC
    print("=" * 70)
    print("1. THE SPEC — the agent specifies http_get via its OWN code-writing")
    print("=" * 70)
    spec = rd.agent_specify_http_get(s)
    print(f"  name           : {spec['name']}")
    print(f"  semantic_kind  : {spec['semantic_kind']}   <- the NEW register")
    print(f"  register       : {spec['register']}")
    print(f"  method         : {spec['method']}  (GET only — safe/idempotent)")
    print(f"  is_new_register: {spec['is_new_register']}  "
          f"(NOT held-composition, unlike every math spec)")
    print(f"  why_new        : {spec['why_new']}")
    print(f"  reduces_to     : {spec['reduces_to']}")
    print(f"  category       : {spec['category']}")
    print(f"  safety         : {spec['safety']}")
    print(f"  grounded_in_science: {spec['grounded_in_science']}")
    # Confirm the spec was recorded as graph data (the agent's own record).
    specs = [n for n in s.nodes("PrimitiveSpec")
             if s.node(n)["attrs"].get("name") == "http_get"]
    print(f"  recorded as PrimitiveSpec graph node: {bool(specs)}")

    # ------------------------------------------------------------------ 2. PROBE
    print()
    print("=" * 70)
    print("2. THE REGISTER GAP — the math-only emitter CANNOT author it")
    print("=" * 70)
    # emit_primitive_rust handles only held-composition semantic_kinds
    # (index_of_reduction, trajectory_distance). Feeding it the external-IO
    # spec proves the gap: the existing code-writing path stops at the register.
    try:
        rd.emit_primitive_rust(spec)
        print("  UNEXPECTED: math emitter accepted the external-IO spec")
        math_emitter_refused = False
    except (ValueError, KeyError) as e:
        print(f"  emit_primitive_rust (held-composition only) REFUSED it:")
        print(f"    -> {type(e).__name__}: {e}")
        print("  => the external-IO register is genuinely OUTSIDE the held-math")
        print("     emitter — the gap is real, not asserted.")
        math_emitter_refused = True

    # ------------------------------------------------------------------ 3. AUTHOR
    print()
    print("=" * 70)
    print("3. THE AUTHORING — the code-writing authors the external-IO binding")
    print("=" * 70)
    emitted = rd.emit_external_io_binding(spec)
    binding_src = emitted["world_adapter.py (binding)"]
    print(f"  emitter        : emit_external_io_binding (deterministic, NO LLM)")
    print(f"  target register: {emitted['register']}")
    print(f"  callable       : {emitted['callable_name']}  (method {emitted['method']})")
    print("  authored source (a Python world-adapter, CLAUDE.md external-IO layer):")
    print("  " + "-" * 66)
    for line in binding_src.splitlines():
        print(f"    {line}")
    print("  " + "-" * 66)

    # Materialise the authored binding into a runnable callable. This is the
    # mechanical "install" of the world-adapter the agent authored — exec of the
    # emitted source, no hand-editing.
    ns: dict = {}
    exec(compile(binding_src, "<agent_authored_http_get>", "exec"), ns)
    http_get = ns["http_get"]
    print(f"  authored binding compiled + bound: {callable(http_get)}")

    # ------------------------------------------------------------------ 4. FETCH
    print()
    print("=" * 70)
    print("4. THE FETCH — run the authored http_get on a SAFE endpoint (REAL)")
    print("=" * 70)
    # SAFE, non-copyrighted, designed-for-testing endpoints (RFC 2606 reserved /
    # request-echo). GET only. We confirm by MECHANISM, never dump content.
    endpoints = [
        ("https://example.com/", "<title>Example Domain</title>"),
        ("https://httpbin.org/get", '"url"'),
    ]
    outcome = None
    detail = ""
    for url, marker in endpoints:
        print(f"  GET {url}")
        try:
            res = http_get(url, timeout=15)
        except urllib.error.URLError as e:
            print(f"    network blocked/unreachable: {type(e).__name__}: {e}")
            outcome = "b"
            detail = f"network blocked on {url}: {e}"
            continue
        except Exception as e:  # noqa: BLE001 — report any real failure honestly
            print(f"    run/network error: {type(e).__name__}: {e}")
            outcome = "b"
            detail = f"{type(e).__name__} on {url}: {e}"
            continue
        status = res["status"]
        length = res["length"]
        present = marker in res["text"]
        # NO content dump — only the mechanism: status, byte-count, marker bool.
        print(f"    status        : {status}")
        print(f"    byte-count    : {length}")
        print(f"    marker {marker!r} present: {present}")
        if status == 200 and length > 0 and present:
            outcome = "a"
            detail = (f"GET {url} -> 200, {length} bytes, "
                      f"marker {marker!r} present")
            break
        else:
            outcome = outcome or "b"
            detail = f"GET {url} -> status {status}, marker present={present}"

    # ------------------------------------------------------------------ OUTCOME
    print()
    print("=" * 70)
    print("THE HONEST OUTCOME")
    print("=" * 70)
    print(f"  spec recorded (new register)     : {bool(specs)}")
    print(f"  math emitter refused (gap real)  : {math_emitter_refused}")
    print(f"  external-IO binding authored     : {callable(http_get)}")
    if outcome == "a":
        print("  OUTCOME (a): AUTHORED + RUNS + FETCHES — the bootstrap seed WORKS.")
        print(f"    {detail}")
        print("    The code-writing CROSSED the external-IO register: the agent")
        print("    specified the new register, its emitter authored the binding,")
        print("    and the authored binding made a REAL fetch. The self-amplifying")
        print("    loop is seeded (write fetcher -> reach web -> read -> write more).")
    elif outcome == "b":
        print("  OUTCOME (b): AUTHORED but RUN/NETWORK BLOCKED — the authoring")
        print("    works; the run+network grant is the external boundary (not the")
        print("    agent's to grant).")
        print(f"    {detail}")
    else:
        print("  OUTCOME (c): could not author the external-IO register — the wall.")
        print(f"    {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
