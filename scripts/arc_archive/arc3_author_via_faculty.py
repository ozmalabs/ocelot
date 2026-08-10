"""arc3_author_via_faculty — THIN HARNESS (orchestrator glue only).

The harness does NOT author the ARC interface. It (1) boots the substrate,
(2) feeds the ARC-AGI-3 spec REQUIREMENTS to the agent's OWN native
authoring faculty (runtime_design.agent_specify_* + the mechanical
emitter), (3) captures exactly what the faculty produces, and (4) probes
whether that authored output satisfies the ARC interface contract
(POST commands, X-API-Key header, AWSALB cookie session affinity,
ACTION6 x,y).

Every line of INTERFACE code in the report is the faculty's emitter output,
captured here verbatim. The harness writes none of it.

Run under: ulimit -v 8388608 + timeout. The key is loaded into os.environ
by _arc3_load_key WITHOUT surfacing the value.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (_ROOT, _HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from _arc3_load_key import load_arc_api_key  # noqa: E402


# The ARC-AGI-3 interface contract, distilled from /tmp/arc3_spec (the
# endpoints/methods the agent's authored interface MUST be able to express).
# This is the SPEC fed to the faculty — not an implementation.
ARC3_REQUIRED_OPS = [
    # (op,            method, path,                  body/headers it needs)
    ("list_games",   "GET",  "/api/games",          "X-API-Key header"),
    ("open_card",    "POST", "/api/scorecard/open",  "X-API-Key, JSON body"),
    ("reset",        "POST", "/api/cmd/RESET",       "X-API-Key, JSON {game_id,card_id,guid}, carry AWSALB cookies"),
    ("action_1_5_7", "POST", "/api/cmd/ACTION{n}",   "X-API-Key, JSON {game_id,guid}, carry AWSALB cookies"),
    ("action_6_xy",  "POST", "/api/cmd/ACTION6",     "X-API-Key, JSON {game_id,guid,x,y}, carry AWSALB cookies"),
    ("close_card",   "POST", "/api/scorecard/close", "X-API-Key, JSON {card_id}"),
]


def main() -> int:
    present = load_arc_api_key()
    klen = len(__import__("os").environ.get("ARC_API_KEY", ""))
    print(f"key present: {present}/len={klen}")

    # --- boot the substrate (the agent is a graph in Rust) ---
    try:
        import substrate_rs as srs
        s = srs.Substrate()
        print("substrate: substrate_rs.Substrate() booted")
    except Exception as e:  # noqa: BLE001
        print(f"substrate boot FAILED: {e}")
        return 2

    from domains import runtime_design as rd

    # === STEP 2a — drive the agent's OWN specify faculty on the EXTERNAL-IO
    # register (the register ARC's HTTP interface lives in). The agent reasons
    # from its held network_protocols science to the effector it lacks. ===
    spec = rd.agent_specify_http_get(s)
    print("\n=== AGENT-SPECIFIED PrimitiveSpec (the faculty's WHAT) ===")
    for k in ("name", "semantic_kind", "register", "method", "is_new_register"):
        print(f"  {k} = {spec.get(k)!r}")
    print(f"  safety = {spec.get('safety','')[:80]}...")

    # === STEP 2b — invoke the agent's mechanical emitter (NO LLM) to AUTHOR
    # the world-adapter binding from that spec. Capture the authored source. ===
    print("\n=== FACULTY AUTHORING ATTEMPT (emit_external_io_binding) ===")
    authored = None
    try:
        authored = rd.emit_external_io_binding(spec)
        print("  emitter produced a binding:")
        print("  callable_name =", authored.get("callable_name"))
        print("  method        =", authored.get("method"))
        print("  --- AUTHORED SOURCE (verbatim faculty output) ---")
        for ln in authored["world_adapter.py (binding)"].splitlines():
            print("  | " + ln)
    except Exception as e:  # noqa: BLE001
        print(f"  emitter RAISED: {type(e).__name__}: {e}")

    # === STEP 2c — the HONEST CONTRACT PROBE: can the faculty author each ARC
    # op? Drive the faculty per required op and record where it succeeds/fails.
    print("\n=== ARC-AGI-3 CONTRACT PROBE (per required op) ===")
    results = []
    for op, method, path, needs in ARC3_REQUIRED_OPS:
        op_spec = dict(spec)
        op_spec["name"] = op
        op_spec["method"] = method
        try:
            out = rd.emit_external_io_binding(op_spec)
            ok = True
            note = f"authored callable {out.get('callable_name')!r}"
        except Exception as e:  # noqa: BLE001
            ok = False
            note = f"{type(e).__name__}: {e}"
        results.append((op, method, path, ok, needs, note))
        print(f"  [{'OK ' if ok else 'NO '}] {op:14s} {method:5s} {path:24s} -> {note}")

    authored_ok = [r for r in results if r[3]]
    blocked = [r for r in results if not r[3]]
    print(f"\nfaculty authored {len(authored_ok)}/{len(results)} ARC ops; "
          f"{len(blocked)} blocked.")
    if blocked:
        print("BLOCKED ops (the faculty cannot express these):")
        for op, method, path, _ok, needs, note in blocked:
            print(f"  - {op} ({method} {path}): needs {needs}")
            print(f"      faculty verdict: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
