# Shared native facade serialization v1 results

## Result

The repeated source-locked capture passed in three fresh processes. A second `_AdapterNativeFacade` constructed around the same PyO3 `Substrate` obtained the identical RLock. While a live `converse()` paused after selection, five contenders attempted public `tick()`, `adapter.inner.node()`, `adapter.s.node()`, `adapter.s._inner.node()`, and `second_facade.node()`. Every call was observed attempting the shared lock; none entered before A released it. All five then completed, the conversation retained Goal/message/origin identity and terminal lifecycle, the baseline reply matched, and all threads joined without errors.

The source now uses a native-object-identity registry to share locks across facades. A separate live lifecycle check confirms the two-facade owner count decrements and the registry entry is removed after both facades are released. This avoids retaining the non-weakrefable native object after the last facade disappears.

An earlier capture attempt is excluded because one worker detected a source hash change. The repeated capture regenerated its lock from the current source; all three workers then matched source fingerprints at start and end. The first independent analyzer invocation also rejected the raw capture because it compared operation names to thread names; the analyzer was corrected and now passes without changing the capture.

## Evidence and limits

- Protocol: [`SUBSTRATE_SHARED_NATIVE_FACADE_SERIALIZATION_V1_20260926.md`](SUBSTRATE_SHARED_NATIVE_FACADE_SERIALIZATION_V1_20260926.md)
- Runner: [`substrate_shared_native_facade_serialization_v1.py`](../../../scripts/substrate_shared_native_facade_serialization_v1.py)
- Independent analyzer: [`analyze_substrate_shared_native_facade_serialization_v1.py`](../../../scripts/analyze_substrate_shared_native_facade_serialization_v1.py)
- Lock: [`shared_native_facade_serialization_v1_lock_20260926.json`](../../../evaluation/substrate_capability/shared_native_facade_serialization_v1_lock_20260926.json)
- Raw capture: [`substrate_shared_native_facade_serialization_v1_20260926.json`](../../../evaluation/reports/substrate_shared_native_facade_serialization_v1_20260926.json)
- Analysis: [`substrate_shared_native_facade_serialization_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_shared_native_facade_serialization_v1_analysis_20260926.json)

This covers two facades and one controlled schedule over one shared PyO3 object. It does not establish safety for complete `WorldAdapter` instances sharing all Python-side indexes, retained raw handles, direct `_native` access, external callers, autonomous native workers, other schedules, or throughput.
