"""Merge legacy .strings translations into a String Catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class MergeError(Exception):
    pass


@dataclass
class MergeReport:
    language: str
    filled: int = 0
    added: int = 0
    replaced: int = 0
    unchanged: int = 0
    conflicts: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    coverage: float = 0.0

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "filled": self.filled,
            "added": self.added,
            "replaced": self.replaced,
            "unchanged": self.unchanged,
            "conflicts": self.conflicts,
            "unknown_keys": self.unknown_keys,
            "added_keys": self.added_keys,
            "coverage": round(self.coverage, 1),
        }


def load_catalog(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise MergeError("cannot read %s: %s" % (path, error))
    except json.JSONDecodeError as error:
        raise MergeError("%s is not valid JSON: %s" % (path, error))
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), dict):
        raise MergeError("%s does not look like a String Catalog" % path)
    return payload


def write_catalog(payload: dict, path: Path, sort_keys: bool = False) -> None:
    if sort_keys and isinstance(payload.get("strings"), dict):
        payload["strings"] = dict(sorted(payload["strings"].items()))
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _current_value(entry: dict, language: str) -> tuple:
    localization = (entry.get("localizations") or {}).get(language)
    if not isinstance(localization, dict):
        return None, None
    if isinstance(localization.get("stringUnit"), dict):
        unit = localization["stringUnit"]
        return unit.get("value") or "", unit.get("state") or "unknown"
    return None, "variations"


def _has_variations(entry: dict) -> bool:
    localizations = entry.get("localizations") or {}
    if not isinstance(localizations, dict):
        return False
    return any(
        isinstance(localization, dict) and "variations" in localization
        for localization in localizations.values()
    )


def _coverage(payload: dict, language: str) -> float:
    strings = payload.get("strings") or {}
    if not strings:
        return 0.0
    filled = 0
    for entry in strings.values():
        value, _ = _current_value(entry, language)
        if value:
            filled += 1
    return 100.0 * filled / len(strings)


def merge(
    payload: dict,
    translations: Dict[str, str],
    language: str,
    overwrite: bool = False,
    add_new: bool = False,
) -> MergeReport:
    strings = payload.setdefault("strings", {})
    report = MergeReport(language=language)

    for key, value in translations.items():
        value = value.strip()
        if not value:
            continue

        entry = strings.get(key)
        if entry is None:
            if not add_new:
                report.unknown_keys.append(key)
                continue
            strings[key] = {
                "localizations": {language: {"stringUnit": {"state": "translated", "value": value}}}
            }
            report.added_keys.append(key)
            report.added += 1
            continue

        if not isinstance(entry, dict):
            report.conflicts.append(key)
            continue

        if _has_variations(entry):
            report.conflicts.append(key)
            continue

        localizations = entry.setdefault("localizations", {})
        if not isinstance(localizations, dict):
            report.conflicts.append(key)
            continue

        current, state = _current_value(entry, language)

        if state == "variations":
            report.conflicts.append(key)
            continue

        if current is None:
            localizations[language] = {"stringUnit": {"state": "translated", "value": value}}
            report.added += 1
            continue

        if not current:
            localizations[language] = {"stringUnit": {"state": "translated", "value": value}}
            report.filled += 1
            continue

        if current == value:
            report.unchanged += 1
            continue

        if overwrite:
            localizations[language] = {"stringUnit": {"state": "translated", "value": value}}
            report.replaced += 1
        else:
            report.conflicts.append(key)

    report.coverage = _coverage(payload, language)
    return report
