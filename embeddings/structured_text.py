from __future__ import annotations

from typing import Iterable, List

from core.canonical_schema import CanonicalObject


def _normalize_people(people: Iterable[str]) -> List[str]:
    seen = set()
    normalized: List[str] = []
    for person in people:
        entry = person.strip()
        if not entry:
            continue
        key = entry.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(entry)
    return sorted(normalized, key=str.lower)


def build_structured_embedding_text(obj: CanonicalObject) -> str:
    """Build the only allowed embedding input: title+content+people+domain."""
    people = _normalize_people(obj.people)
    people_blob = ", ".join(people) if people else ""
    return "\n".join(
        [
            f"title: {obj.title.strip()}",
            f"content: {obj.content.strip()}",
            f"people: {people_blob}",
            f"domain: {obj.domain.strip()}",
        ]
    )
