# Live self-report lifecycle identity integration v1.3 amendment

The v1.2 native `del_edge` effects were accepted and terminal Goals gained `has_closed_goal`, but the live capture still failed the invariant because `WorldAdapter._bind_live_goals_and_deliberation` unconditionally recreated `has_active_goal` for any Goal comprehending the current Message. Direct native control fixtures passed because they did not call that live rebinding path.

V1.3 changes the adapter bridge to inspect the Goal lifecycle status: nonterminal Goals remain/are added to `has_active_goal`; terminal Goals are removed from `has_active_goal` and ensured in `has_closed_goal`. The native effect spelling and all producer/rule identity conditions remain unchanged. The initial v1 and amended v1.1/v1.2 captures are preserved as failed attempts. V1.3 uses new lock/raw/analysis paths and the same positive plus five control gates.
