# Live self-report lifecycle producer probe preregistration

**Question:** when the production conversation path selects and runs an existing held self-report faculty twice for the same recipient, does it emit Goal-specific lifecycle events, or only the inbound instruction and reply?

**Protocol:** run three fresh Python worker processes. Each creates `WorldAdapter(seeds=())`, loads all seeds with external language-model and seed-persistence paths disabled, then submits two identical `report your organisation` instructions from `alice` in one session. This is the existing `conversation_action.act_on_instruction` self-report route exercised by the live converse path, not the earlier `goal_only` route. The probe records process/build/source identity, per-turn time, inbound Message and DiscourseEvent IDs and attributes, recipient, `communication_route`, reply presence/target evidence, all Goals comprehending that Message, `originated_in` links, transitions, associated Deliberations, and event-kind counts.

**Positive route gates:** both turns return a non-empty reply with organisation evidence; both messages report `communication_route=self_report`; each produces exactly one `source=conversation`, `kind=report_self`, `self_target=self_organisation` Goal that comprehends its own Message and originates in its own inbound event; two turns have distinct Message/event/Goal IDs and the same non-empty recipient.

**Lifecycle gap gates:** the shared discourse state contains exactly two `instruction` events and zero `selection`, `execution`, or `action_result` events; neither Goal has a transition event; no event has a `for_goal` edge. The repeated producer record shape must agree across the three fresh processes after excluding process-local numeric IDs and timings.

The capture is a positive check of live held-faculty routing and origin provenance, and a negative check for lifecycle event production on this route. It does not claim the reply is a durable execution receipt, nor that no other action path can emit lifecycle events. Do not pool the preceding goal-only instruction probe.
