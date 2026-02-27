from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CanonicalObject(BaseModel):
    """Canonical, source-agnostic representation for normalized memory objects."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    canonical_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    source_record_type: str = Field(min_length=1)
    title: str = ""
    content: str = ""
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    people: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    domain: str = "general"
