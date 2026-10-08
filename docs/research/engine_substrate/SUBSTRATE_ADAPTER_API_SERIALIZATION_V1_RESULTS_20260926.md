# Adapter public API serialization v1 results

## Result

The source-current capture passed in three fresh workers. While A was paused after its live describe-scene selection event, B attempted public `WorldAdapter.tick()` and was observed at the common transaction lock before acquisition. It did not enter the protected call until A's `converse` returned. A then retained its exact inbound Message and origin event, completed selection → execution → result, closed its Goal, and returned the established baseline reply. B's tick completed with an integer result. No worker thread raised or remained alive.

This supports serialization across the tested `converse`/`tick` pair. The implementation now wraps every public `WorldAdapter` function with the per-instance RLock, so reentrant public calls within an adapter share the same boundary. The source audit and capture do not cover direct `s`/`inner` access, multiple adapter objects over the same native substrate, autonomous workers, external callbacks, every public method, or every thread schedule. The PyO3 borrow model itself is unchanged.

## Evidence and limits

- Protocol: [`SUBSTRATE_ADAPTER_API_SERIALIZATION_V1_20260926.md`](SUBSTRATE_ADAPTER_API_SERIALIZATION_V1_20260926.md)
- Runner: [`substrate_adapter_api_serialization_v1.py`](../../../scripts/substrate_adapter_api_serialization_v1.py)
- Independent analyzer: [`analyze_substrate_adapter_api_serialization_v1.py`](../../../scripts/analyze_substrate_adapter_api_serialization_v1.py)
- Lock: [`live_describe_scene_adapter_api_serialization_v1_lock_20260926.json`](../../../evaluation/substrate_capability/live_describe_scene_adapter_api_serialization_v1_lock_20260926.json)
- Raw capture: [`substrate_live_describe_scene_adapter_api_serialization_v1_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_adapter_api_serialization_v1_20260926.json)
- Analysis: [`substrate_adapter_api_serialization_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_adapter_api_serialization_v1_analysis_20260926.json)
