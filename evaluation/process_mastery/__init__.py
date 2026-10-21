"""Process Mastery Battery (PMB) v1 — Track I evaluation (see PMB_V1_SPEC.md).

Python here is mechanical: it generates task instances (the world), boots
agents, hands the world's actions and tasks to the graph, ticks, and reads
results. Every decision (what to invent, keep, try, explain) is a graph rule.
"""
