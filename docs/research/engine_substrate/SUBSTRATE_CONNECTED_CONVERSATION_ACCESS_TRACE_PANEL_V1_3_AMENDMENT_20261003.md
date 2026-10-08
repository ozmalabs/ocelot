# Connected-conversation access-trace panel v1.3 amendment

Date: 2026-10-03

V1.2's paired capture passed all runner gates. Its independent analysis then failed only because the analyzer expected 36 historical comparison rows; the design contains 12 replicate/case pairs (three workers × four cases). V1.3 corrects this analyzer coverage expectation to 12, retaining the v1.2 runner, lock, capture, analysis, and amendment as provenance. Workload selection, paired trace-off/trace-on execution, measurements, and acceptance gates are unchanged. A fresh lock covers the corrected analyzer.
