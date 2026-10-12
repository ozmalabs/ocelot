# Direct native-access serialization v1 results

## Result

Three source-stable workers passed. In each, a live `converse()` paused after selection while four separate threads attempted calls through the adapter's public graph surfaces: `tick()`, `inner.node(agent)`, `s.node(agent)`, and `s._inner.node(agent)`. The observed shared RLock recorded every acquisition attempt and confirmed none entered before the conversation released it. All four operations then completed. The conversation retained exact Goal/message/origin identity, emitted selection → execution → result, closed its Goal, and returned the baseline reply. No threads raised or remained alive.

`WorldAdapter.inner` and the underlying native handle reachable as `WorldAdapter.s._inner` now use a lightweight facade that serializes each native call on the same adapter RLock. Calls through `WorldAdapter.s` reach that same facade. The earlier `converse`/`tick` capture also passed. This closes the tested common handle paths and one public-method path; it does not protect a raw PyO3 handle retained before wrapping, code that reaches the facade's private `_native`, a second adapter with a distinct lock around the same native object, or arbitrary third-party native callers.

## Evidence and limits

- Protocol: [`SUBSTRATE_DIRECT_NATIVE_ACCESS_SERIALIZATION_V1_20260926.md`](SUBSTRATE_DIRECT_NATIVE_ACCESS_SERIALIZATION_V1_20260926.md)
- Runner: [`substrate_direct_native_access_serialization_v1.py`](../../../scripts/substrate_direct_native_access_serialization_v1.py)
- Independent analyzer: [`analyze_substrate_direct_native_access_serialization_v1.py`](../../../scripts/analyze_substrate_direct_native_access_serialization_v1.py)
- Lock: [`direct_native_access_serialization_v1_lock_20260926.json`](../../../evaluation/substrate_capability/direct_native_access_serialization_v1_lock_20260926.json)
- Raw capture: [`substrate_direct_native_access_serialization_v1_20260926.json`](../../../evaluation/reports/substrate_direct_native_access_serialization_v1_20260926.json)
- Analysis: [`substrate_direct_native_access_serialization_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_direct_native_access_serialization_v1_analysis_20260926.json)
