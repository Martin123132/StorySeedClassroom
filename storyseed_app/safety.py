from __future__ import annotations

import re
from typing import Any


AGE_BANDS = ["5-7", "8-11", "12-14", "15+"]
REQUIRED_LISTS = ["characters", "settings", "objects", "topics"]
RISKY_TERMS = [
    "blood",
    "drug",
    "gun",
    "hate speech",
    "knife",
    "kill",
    "murder",
    "racist",
    "self harm",
    "self-harm",
    "sex",
    "slur",
    "suicide",
    "weapon",
]


def check_state(state: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    counts = {
        "characters": _count_list(state.get("characters")),
        "settings": _count_list(state.get("settings")),
        "objects": _count_list(state.get("objects")),
        "topics": _count_list(state.get("topics")),
        "vocabulary_bands": len(state.get("vocabulary", {}) if isinstance(state.get("vocabulary"), dict) else {}),
        "subject_packs": len(state.get("subject_packs", {}) if isinstance(state.get("subject_packs"), dict) else {}),
    }

    _check_required_lists(state, issues)
    _check_structured_entries(state, issues)
    _check_vocabulary(state, issues)
    _check_subject_packs(state, issues)
    _check_risky_terms(state, issues)

    status = _overall_status(issues)
    return {
        "status": status,
        "label": _status_label(status),
        "summary": _summary(status, issues),
        "issues": issues,
        "counts": counts,
    }


def _check_required_lists(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    for key in REQUIRED_LISTS:
        value = state.get(key)
        if not isinstance(value, list) or not value:
            issues.append(_issue("red", key.title(), f"{key.replace('_', ' ').title()} has no usable entries."))
        elif len(value) < 3:
            issues.append(_issue("amber", key.title(), f"{key.replace('_', ' ').title()} has only {len(value)} entries. Add a few more for variety."))


def _check_structured_entries(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    specs = {
        "characters": ["name", "trait", "wish"],
        "settings": ["name", "texture"],
        "objects": ["name", "twist"],
    }
    for key, fields in specs.items():
        values = state.get(key)
        if not isinstance(values, list):
            continue
        seen: set[str] = set()
        for index, item in enumerate(values, start=1):
            if not isinstance(item, dict):
                issues.append(_issue("red", key.title(), f"Entry {index} is not in the expected format."))
                continue
            missing = [field for field in fields if not str(item.get(field) or "").strip()]
            if "name" in missing:
                issues.append(_issue("red", key.title(), f"Entry {index} is missing a name."))
            elif missing:
                issues.append(_issue("amber", key.title(), f"{item.get('name')} is missing {', '.join(missing)}."))
            name_key = str(item.get("name") or "").strip().lower()
            if name_key:
                if name_key in seen:
                    issues.append(_issue("amber", key.title(), f"Duplicate name found: {item.get('name')}."))
                seen.add(name_key)


def _check_vocabulary(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    vocab = state.get("vocabulary")
    if not isinstance(vocab, dict):
        issues.append(_issue("red", "Vocabulary", "Vocabulary should be grouped by age band."))
        return
    for age in AGE_BANDS:
        words = vocab.get(age)
        if not isinstance(words, list) or not [word for word in words if str(word).strip()]:
            issues.append(_issue("red", "Vocabulary", f"Missing vocabulary for age {age}."))
            continue
        if len(words) < 4:
            issues.append(_issue("amber", "Vocabulary", f"Age {age} has fewer than four vocabulary words."))
        duplicates = _duplicates(words)
        if duplicates:
            issues.append(_issue("amber", "Vocabulary", f"Age {age} repeats: {', '.join(duplicates[:3])}."))


def _check_subject_packs(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    packs = state.get("subject_packs")
    if not isinstance(packs, dict) or not packs:
        issues.append(_issue("amber", "Subject Packs", "Subject packs are missing, so prompts will be less tailored."))
        return
    for subject, pack in packs.items():
        if not isinstance(pack, dict):
            issues.append(_issue("amber", "Subject Packs", f"{subject} is not a valid subject pack."))
            continue
        for field in ["focus", "topics", "constraints", "extensions"]:
            value = pack.get(field)
            if not isinstance(value, list) or not value:
                issues.append(_issue("amber", "Subject Packs", f"{subject} is missing {field}."))
        vocabulary = pack.get("vocabulary")
        if not isinstance(vocabulary, dict):
            issues.append(_issue("amber", "Subject Packs", f"{subject} is missing age-band vocabulary."))
            continue
        missing_ages = [age for age in AGE_BANDS if not vocabulary.get(age)]
        if missing_ages:
            issues.append(_issue("amber", "Subject Packs", f"{subject} has no vocabulary for {', '.join(missing_ages)}."))


def _check_risky_terms(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    haystack = _flatten_text(state)
    for term in RISKY_TERMS:
        if _contains_term(haystack, term):
            issues.append(_issue("amber", "Teacher Review", f"Review edited seed banks for the word '{term}'."))


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value or "")


def _contains_term(text: str, term: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term).replace(r"\ ", r"[\s-]+") + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _duplicates(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    repeated: list[str] = []
    for value in values:
        key = str(value).strip().lower()
        if not key:
            continue
        if key in seen and key not in repeated:
            repeated.append(key)
        seen.add(key)
    return repeated


def _count_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _overall_status(issues: list[dict[str, str]]) -> str:
    levels = {issue["level"] for issue in issues}
    if "red" in levels:
        return "red"
    if "amber" in levels:
        return "amber"
    return "green"


def _status_label(status: str) -> str:
    return {
        "green": "Seed Bank Safety Green",
        "amber": "Teacher Review Amber",
        "red": "Seed Bank Needs Attention",
    }[status]


def _summary(status: str, issues: list[dict[str, str]]) -> str:
    if status == "green":
        return "Seed banks look ready for classroom use."
    if status == "amber":
        return f"{len(issues)} thing needs teacher review before sharing widely."
    return f"{len(issues)} thing needs fixing before the seed bank is reliable."


def _issue(level: str, area: str, message: str) -> dict[str, str]:
    target = "seeds" if area not in {"Vocabulary"} else "seeds"
    return {"level": level, "area": area, "message": message, "target": target}
