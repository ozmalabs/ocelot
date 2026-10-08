# Shape-decoding Python/native attribution v2 — preregistration

**Question:** After moving rule lookup/patch into the native branch API, where does isolated worker CPU now accrue in the shape-decoding rehearsal?

Repeat the prior 100k-node fixture, positive `dedup_identity_fix`, scoped full-copy/shared-page backends, sequential/concurrent fanout-8, and 3 fresh processes per backend/mode (12 total). Call `imagine_and_check_convergence` through its default-native patch route. Profile all eight rehearsals only in sequential cells using `cProfile.Profile(timer=time.thread_time_ns,timeunit=1e-9)`; record unprofiled concurrent thread CPU, wave wall, and phase timings. Preserve exact semantic, primary-isolation, source/native-lock, and process-uniqueness gates. Report Python/native self CPU and top sites in sequential cells, plus phase and CPU/wall comparisons for all cells.

**Limits:** cProfile's thread-CPU timer is not valid for simultaneous profilers in this environment; concurrent cells remain unprofiled. Attribution is isolated to the task/host and includes profiler overhead. It cannot show GIL wait ownership or establish workload-general tractability.
