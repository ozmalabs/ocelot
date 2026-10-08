# Python source coverage audit v1.2 amendment

Date: 2026-09-28  
Status: preregistered deterministic census refresh; execution has not started.

V1.1 remains preserved as the historical 32/833 direct-link census. V1.2 reruns the same scanner on the current Python source and seed-manifest state after a reviewed source adjudication added capability-map links for modules observed in the conversation task activation panel. The updated capability map now has 26 capability rows. The conversation module activation panel was repeated under a fresh current-source lock (v1.2); its linked task oracles and source/cache integrity gates pass.

The scan scope and static/dynamic reachability rules do not change. V1.2 must hash the capability map before and after the census as well as Python/seed inputs, and abort on any input drift. Its purpose is to report the updated mapping baseline, not to claim increased substrate capability: changing links affects source inventory coverage only. The directly linked file count and activated-module join must be reported separately from import reachability and task outcomes.
