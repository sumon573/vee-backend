"""
Shared enum definitions for Vee domain models.

All enums are string-based (str, enum.Enum) so they serialize naturally
to/from JSON and PostgreSQL native enum types.
"""

import enum


class Gender(str, enum.Enum):
    """User-declared gender identity."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
