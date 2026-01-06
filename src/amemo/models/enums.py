"""Type definitions and enums for the Amemo SDK."""

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
