# Registered seed-root admission census v1.2 amendment

V1.1 corrected the empty-profile comparison but its analyzer imported the v1 runner's lock context. The replay was therefore checking v1 fingerprints rather than v1.1 inputs; the source-stability check caught this as an analyzer-hash mismatch. Preserve v1.1 capture and analysis as a failed integrity iteration.

V1.2 changes no population or measurement design. It binds the independent analyzer to the v1.2 runner/lock and retains the nonempty-profile condition. A fresh source lock and capture are required so all provenance references the exact analyzer under review.
