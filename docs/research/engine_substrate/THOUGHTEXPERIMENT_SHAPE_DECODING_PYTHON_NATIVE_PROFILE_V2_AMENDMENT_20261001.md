# Shape-decoding Python/native attribution v2 — scope amendment

The prior profile established that concurrent cProfile activation conflicts and single-thread profiling during concurrent execution produces invalid negative C-call self time with this thread timer. This v2 keeps profiler instrumentation out of concurrent waves and uses the now-default native rule patch. Results are attributed only to sequential cells; concurrent wave CPU/wall and phase measurements remain unprofiled.
