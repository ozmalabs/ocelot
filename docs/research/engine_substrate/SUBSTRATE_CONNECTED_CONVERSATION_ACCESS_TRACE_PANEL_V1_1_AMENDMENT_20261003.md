# Connected-conversation access-trace panel v1.1 amendment

Date: 2026-10-03

V1.1 retains the v1 source lock and startup failure note. The failed v1 invocation stopped before starting a worker because the parent process lacked a `datetime` import; no graph was changed or measured. The v1.1 runner adds the import and uses a fresh source lock. All cases, instrumentation, baseline comparisons, measurements, and acceptance gates remain as registered in the [v1 method](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_METHOD_20261003.md).
