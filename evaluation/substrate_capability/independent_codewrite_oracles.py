"""Small independent executable oracles for the code-write adequacy panel.

This file contains only task definitions used to label probe and held-out
inputs. The runner hashes it separately from each candidate source.
"""
from __future__ import annotations


def label(task: str, inputs: dict):
    if task == "parity":
        if set(inputs) != {"value"}:
            raise ValueError("parity input must contain exactly value")
        return int(inputs["value"]) % 2 == 0
    if task == "clamp":
        if set(inputs) != {"value", "lower", "upper"}:
            raise ValueError("clamp input must contain value, lower, and upper")
        value, lower, upper = (inputs["value"], inputs["lower"], inputs["upper"])
        return lower if value < lower else upper if value > upper else value
    if task == "square":
        if set(inputs) != {"x"}:
            raise ValueError("square input must contain exactly x")
        return int(inputs["x"]) ** 2
    raise ValueError(f"unknown oracle task: {task}")
