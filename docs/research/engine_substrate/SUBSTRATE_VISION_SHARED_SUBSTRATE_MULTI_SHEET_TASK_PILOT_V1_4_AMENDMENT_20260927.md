# Shared-substrate multi-sheet task pilot v1.4 amendment

V1.3 found no measurable B-to-A tuning change, but it verified only B retinal input bursts and ON/OFF channel activity, not activity in B's simple-unit (SUnit) layer. V1.4 adds a B-side K=16 SUnit readout for each B context. It restores the same prepared graph snapshot before B readout, holds A's retina blank, and drives B with the phase/orientation frames used by the existing K=16 instrument. The capture records B's tuning/OSI, active-unit counts, and direct B SUnit `rate`/`act` after the paired A readout. B and A readout weights are independently captured before/after.

The A readout and the global-versus-root-scoped comparison retain the v1.3 inputs, adaptation schedule, cumulative progress bound, and exact prepared-state replay. B-only readout is a manipulation check: it tests whether the intervention travels through B's SUnit stack. It does not change the A task stimulus. Each A and B presentation reports closure status and cumulative work under the same continuation policy.

V1.3's capture was valid by independent audit, but its original driver incorrectly required a positive executable-rule count for every seed. The `vision_compose` manifest has zero executable rules. V1.4 corrects this fixture gate to require tagged-rule count to equal executable-rule count for each manifest, including the valid zero/zero case. This correction is reported separately from the new B-side measurement.

V1.4 is one seed and one two-sheet fixture. A positive B SUnit response would establish that the manipulation reaches the modeled SUnit layer in this setup; it would not establish natural-task prevalence, general scope safety, or scaling.
