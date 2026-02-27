from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from core.canonical_schema import CanonicalObject
from storage.sqlite_store import SQLiteStore

SAME_DAY = "SAME_DAY"
SAME_PERSON = "SAME_PERSON"
SAME_DOMAIN = "SAME_DOMAIN"
FOLLOW_UP = "FOLLOW_UP"


@dataclass(frozen=True)
class Relation:
    relation_id: str
    from_canonical_id: str
    to_canonical_id: str
    relation_type: str
    reason: str
    confidence: float = 1.0

    def to_record(self) -> Dict[str, object]:
        return {
            "relation_id": self.relation_id,
            "from_canonical_id": self.from_canonical_id,
            "to_canonical_id": self.to_canonical_id,
            "relation_type": self.relation_type,
            "reason": self.reason,
            "confidence": self.confidence,
        }


def _make_relation_id(from_id: str, to_id: str, relation_type: str, reason: str) -> str:
    payload = {
        "from_canonical_id": from_id,
        "to_canonical_id": to_id,
        "relation_type": relation_type,
        "reason": reason,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return f"rel_{digest[:24]}"


def _ordered_pair(id_a: str, id_b: str) -> Tuple[str, str]:
    return (id_a, id_b) if id_a < id_b else (id_b, id_a)


def _anchor_datetime(obj: CanonicalObject) -> Optional[datetime]:
    candidate = obj.start_at or obj.due_at or obj.created_at or obj.updated_at or obj.end_at
    if candidate is None:
        return None
    if candidate.tzinfo is None:
        return candidate.replace(tzinfo=timezone.utc)
    return candidate.astimezone(timezone.utc)


def _anchor_day(obj: CanonicalObject) -> Optional[str]:
    anchor = _anchor_datetime(obj)
    return anchor.date().isoformat() if anchor else None


def _people_set(obj: CanonicalObject) -> Set[str]:
    return {person.strip().lower() for person in obj.people if person and person.strip()}


def _domain_value(obj: CanonicalObject) -> str:
    return (obj.domain or "").strip().lower()


def _shared_people(obj_a: CanonicalObject, obj_b: CanonicalObject) -> Set[str]:
    return _people_set(obj_a).intersection(_people_set(obj_b))


def _build_pair_relations(obj_a: CanonicalObject, obj_b: CanonicalObject) -> List[Relation]:
    relations: List[Relation] = []

    day_a = _anchor_day(obj_a)
    day_b = _anchor_day(obj_b)
    if day_a and day_b and day_a == day_b:
        from_id, to_id = _ordered_pair(obj_a.canonical_id, obj_b.canonical_id)
        reason = f"anchor_day={day_a}"
        relations.append(
            Relation(
                relation_id=_make_relation_id(from_id, to_id, SAME_DAY, reason),
                from_canonical_id=from_id,
                to_canonical_id=to_id,
                relation_type=SAME_DAY,
                reason=reason,
            )
        )

    people_overlap = _shared_people(obj_a, obj_b)
    if people_overlap:
        from_id, to_id = _ordered_pair(obj_a.canonical_id, obj_b.canonical_id)
        reason = f"people={','.join(sorted(people_overlap))}"
        relations.append(
            Relation(
                relation_id=_make_relation_id(from_id, to_id, SAME_PERSON, reason),
                from_canonical_id=from_id,
                to_canonical_id=to_id,
                relation_type=SAME_PERSON,
                reason=reason,
            )
        )

    domain_a = _domain_value(obj_a)
    domain_b = _domain_value(obj_b)
    if domain_a and domain_b and domain_a == domain_b:
        from_id, to_id = _ordered_pair(obj_a.canonical_id, obj_b.canonical_id)
        reason = f"domain={domain_a}"
        relations.append(
            Relation(
                relation_id=_make_relation_id(from_id, to_id, SAME_DOMAIN, reason),
                from_canonical_id=from_id,
                to_canonical_id=to_id,
                relation_type=SAME_DOMAIN,
                reason=reason,
            )
        )

    time_a = _anchor_datetime(obj_a)
    time_b = _anchor_datetime(obj_b)
    if time_a and time_b:
        earlier_obj, earlier_time, later_obj, later_time = (
            (obj_a, time_a, obj_b, time_b) if time_a <= time_b else (obj_b, time_b, obj_a, time_a)
        )
        delta = later_time - earlier_time
        shared_context = bool(_shared_people(obj_a, obj_b)) or (
            _domain_value(obj_a) and _domain_value(obj_a) == _domain_value(obj_b)
        )
        if timedelta(0) < delta <= timedelta(days=7) and shared_context:
            reason = f"delta_hours={delta.total_seconds() / 3600:.2f}"
            relations.append(
                Relation(
                    relation_id=_make_relation_id(
                        earlier_obj.canonical_id, later_obj.canonical_id, FOLLOW_UP, reason
                    ),
                    from_canonical_id=earlier_obj.canonical_id,
                    to_canonical_id=later_obj.canonical_id,
                    relation_type=FOLLOW_UP,
                    reason=reason,
                )
            )

    return relations


def build_relations(objects: Sequence[CanonicalObject]) -> List[Relation]:
    dedup: Dict[Tuple[str, str, str], Relation] = {}
    object_count = len(objects)
    for idx in range(object_count):
        for jdx in range(idx + 1, object_count):
            pair_relations = _build_pair_relations(objects[idx], objects[jdx])
            for relation in pair_relations:
                key = (
                    relation.from_canonical_id,
                    relation.to_canonical_id,
                    relation.relation_type,
                )
                dedup[key] = relation
    return sorted(
        dedup.values(),
        key=lambda rel: (rel.from_canonical_id, rel.to_canonical_id, rel.relation_type),
    )


def build_relations_from_store(store: SQLiteStore) -> List[Relation]:
    return build_relations(store.fetch_canonical_objects())


def rebuild_and_store_relations(store: SQLiteStore, objects: Optional[Iterable[CanonicalObject]] = None) -> int:
    if objects is None:
        source_objects = store.fetch_canonical_objects()
    else:
        source_objects = list(objects)
    relations = build_relations(source_objects)
    store.replace_relations([relation.to_record() for relation in relations])
    return len(relations)
