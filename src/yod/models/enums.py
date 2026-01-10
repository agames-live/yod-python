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
    "semantic",  # Consolidated memories abstracted from episodic clusters
]

MemoryStatus = Literal[
    "active",
    "superseded",
    "rejected",
    "proposed",
    "consolidated",  # Episodic memories merged into semantic facts
    "archived",      # Decayed memories pruned during consolidation
]

MemoryType = Literal[
    "episodic",     # Events with temporal context, subject to decay
    "semantic",     # Stable facts, singleton behavior
    "procedural",   # Preferences/behaviors that strengthen with use
    "core",         # Identity facts, never superseded
]
