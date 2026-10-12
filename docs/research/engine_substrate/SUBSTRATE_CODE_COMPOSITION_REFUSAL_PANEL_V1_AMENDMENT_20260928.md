# Code-composition refusal panel v1 amendment

Date: 2026-09-28  
Status: pre-replay source-drift disclosure.

The first two-worker execution completed its schedule, but the full lock gate failed: `seeds/communication_intent_arbitration.json` changed during worker 1. That run is excluded from analysis and supplies no valid result. The first candidate lock had seed SHA-256 `a8de8e3999bf1f24c95364451bfa387f9f00b59775320647dee4a597a0e06e06`; after that failed run the seed was `418570f12e9c58c3d7e12c51c1d13070c18cd04729cc324663d383b28b298c7e`. A second pre-run lock recorded `domains/comprehend_text.py` as `cb0d5a3224552867aabe961689ff0d9798a4fc82793e4ae13fc40cde6b5e73b2`, while both workers observed `d578e5a49250495ab310efdc534b6c10c90d788a12de3900642326ea0ab33aad`. Both workers were internally stable against that changed snapshot, but it did not match the parent pre-run lock. Both executions are excluded from scoring. No probe inputs or scoring criteria change. A fresh full lock is required before the next candidate execution; only a run with every parent and worker lock gate passing will be scored.
