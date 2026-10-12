# Dirty-rule entry audit v1.1 analysis amendment

This independent amendment aligns each `scheduler_selected_rules` counter with the same operation's `scheduler_pass` count and the dirty-rule count observed immediately before the call. The original v1 capture, source lock, and raw audit remain unchanged.

Acceptance distinguishes the first scheduler pass from later passes. When a call has one pass, entry dirty count must equal total selected rules. When it has two passes, selected rules may exceed the entry dirty count because effects during pass one can dirty additional rules; the excess is reported explicitly as later-pass selections. Dirty-name mapping ambiguities remain visible and are not treated as zero.
