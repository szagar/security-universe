"""Import and export helpers for universe members."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from security_universe.models import Security, UniverseMember

CSV_FIELDS = [
    "symbol",
    "security_type",
    "security_id",
    "short_name",
    "weight",
    "active",
    "source",
    "reason",
    "added_by",
    "tags_json",
    "metadata_json",
    "security_json",
]


def read_members(path: str | Path, universe_name: str) -> list[UniverseMember]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        return read_json_members(file_path, universe_name)
    if file_path.suffix.lower() == ".csv":
        return read_csv_members(file_path, universe_name)
    raise ValueError(f"Unsupported import format: {file_path.suffix}")


def write_members(path: str | Path, members: list[UniverseMember]) -> None:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        write_json_members(file_path, members)
        return
    if file_path.suffix.lower() == ".csv":
        write_csv_members(file_path, members)
        return
    raise ValueError(f"Unsupported export format: {file_path.suffix}")


def read_json_members(path: Path, universe_name: str) -> list[UniverseMember]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON import must contain a list of members")
    return [_member_from_mapping(item, universe_name) for item in data]


def write_json_members(path: Path, members: list[UniverseMember]) -> None:
    path.write_text(
        json.dumps(
            [member.model_dump(mode="json") for member in members],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def read_csv_members(path: Path, universe_name: str) -> list[UniverseMember]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return [
            _member_from_mapping(row, universe_name)
            for row in csv.DictReader(file)
        ]


def write_csv_members(path: Path, members: list[UniverseMember]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for member in members:
            writer.writerow(
                {
                    "symbol": member.security.symbol,
                    "security_type": member.security.security_type.value,
                    "security_id": member.security.security_id or "",
                    "short_name": member.security.short_name or "",
                    "weight": str(member.weight) if member.weight is not None else "",
                    "active": str(member.active).lower(),
                    "source": member.source or "",
                    "reason": member.reason or "",
                    "added_by": member.added_by or "",
                    "tags_json": json.dumps(sorted(member.tags)),
                    "metadata_json": json.dumps(member.metadata, sort_keys=True),
                    "security_json": member.security.model_dump_json(),
                }
            )


def _member_from_mapping(data: Any, universe_name: str) -> UniverseMember:
    if not isinstance(data, dict):
        raise ValueError("Imported member entries must be mappings")

    security_data = data.get("security")
    security_json = data.get("security_json")
    if security_data is None and security_json:
        security_data = json.loads(security_json)
    if security_data is None:
        security_data = {
            "symbol": data.get("symbol"),
            "security_type": data.get("security_type") or "unknown",
            "security_id": data.get("security_id") or None,
            "short_name": data.get("short_name") or None,
        }

    return UniverseMember(
        universe_name=universe_name,
        security=Security.model_validate(security_data),
        member_id=data.get("member_id") or None,
        weight=data.get("weight") or None,
        active=_parse_bool(data.get("active"), default=True),
        added_at=data.get("added_at") or None,
        added_by=data.get("added_by") or None,
        expires_at=data.get("expires_at") or None,
        source=data.get("source") or None,
        reason=data.get("reason") or None,
        tags=_parse_tags(data.get("tags", data.get("tags_json"))),
        metadata=_parse_mapping(data.get("metadata", data.get("metadata_json"))),
    )


def _parse_bool(value: Any, *, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _parse_tags(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    if isinstance(value, str):
        parsed = json.loads(value)
    else:
        parsed = value
    if not isinstance(parsed, list):
        raise ValueError("tags must be a list")
    return {str(item) for item in parsed}


def _parse_mapping(value: Any) -> dict[str, Any]:
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        parsed = json.loads(value)
    else:
        parsed = value
    if not isinstance(parsed, dict):
        raise ValueError("metadata must be an object")
    return parsed
