# Integrated Rung 3 nonlinear-map synthesis v1.1.1 — amendment

The v1.1 tuple-corrected capture is preserved as an incomplete technical attempt. The 15 workers that accepted a synthesized Program failed while serializing the returned native `NodeID`; five absolute-map workers that gapped were captured. The failure occurred after the substrate route ran and before successful worker records could be returned to the parent, so v1.1 is not complete evidence and its partial outcomes are not pooled.

V1.1.1 makes a runner-only serialization correction: convert graph `NodeID` values to strings in the raw summary. It preserves the v1.1 task tables, tuple-valued training outputs, route, scoring, repetition count, budget, and gates. It takes a fresh source/native lock and records all 20 worker outcomes. No engine, seed, or task behavior is changed.
