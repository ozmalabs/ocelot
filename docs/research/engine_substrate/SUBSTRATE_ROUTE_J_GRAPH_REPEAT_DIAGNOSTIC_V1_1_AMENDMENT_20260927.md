# Route panel J graph-repeat diagnostic v1.1 amendment

Date: 2026-09-27

The v1 analyzer compared each composite worker lock against the inner study lock, so it falsely reported a source-lock mismatch. Its captured driver and worker study-lock payloads are available for direct comparison and show stable files. V1 also retained node attribute hashes but not the actual values; it identified one changed attribute hash on the same `Interlocutor` node in one worker.

V1.1 corrects the lock-shape check and records full attributes for `Interlocutor` nodes so the difference can be classified as volatile metadata or semantic state. It repeats three fresh processes on the same frozen full-runtime snapshot and does not change the route or graph.
