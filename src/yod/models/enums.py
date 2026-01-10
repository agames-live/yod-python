"""Type definitions and enums for the Yod SDK."""

from __future__ import annotations

from typing import Literal

EntityType = Literal[
    "self",
    "person",
    "organization",
    "project",
    "location",
    "date",
    "preference",
    "topic",
    "other",
]

MemoryKind = Literal[
    "preference",
    "event",
    "profile_fact",
    "task",
    "relationship",
    "fact",
]

MemoryStatus = Literal[
    "active",
    "superseded",
    "rejected",
    "proposed",
]

MemoryType = Literal[
    "episodic",     # Events with temporal context, subject to decay
    "semantic",     # Stable facts, singleton behavior
    "procedural",   # Preferences/behaviors that strengthen with use
    "core",         # Identity facts, never superseded
]
