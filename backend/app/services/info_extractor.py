import re
from datetime import UTC, datetime
from typing import Any

from app.utils.skills_keywords import (
    ALL_SECTION_HEADERS,
    DEGREE_KEYWORDS,
    SECTION_HEADERS,
    SKILLS_KEYWORDS,
)
from app.utils.text_cleaning import clean_text

MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
DATE_RANGE_PATTERN = re.compile(
    rf"({MONTH_PATTERN})\s*(\d{{4}})\s*[-–—]\s*({MONTH_PATTERN}|present|current|\d{{4}})",
    re.IGNORECASE,
)
YEAR_RANGE_PATTERN = re.compile(
    r"(\d{4})\s*[-–—]\s*(\d{4}|present|current)",
    re.IGNORECASE,
)
EXPLICIT_YEARS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?experience",
    re.IGNORECASE,
)


def _normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for skill in SKILLS_KEYWORDS:
        pattern = re.escape(skill)
        if re.search(rf"\b{pattern}\b", lowered):
            found.append(skill)
    return sorted(set(found), key=lambda s: lowered.find(s))


def _parse_month_year(month: str, year: str) -> datetime | None:
    try:
        month_num = datetime.strptime(month[:3].title(), "%b").month
        return datetime(int(year), month_num, 1)
    except ValueError:
        return None


def _years_between(start: datetime, end: datetime) -> float:
    return max(0.0, (end - start).days / 365.25)


def extract_years_of_experience(text: str) -> float:
    explicit = EXPLICIT_YEARS_PATTERN.findall(text)
    if explicit:
        return max(float(y) for y in explicit)

    total_years = 0.0
    now = datetime.now(UTC).replace(tzinfo=None)

    for match in DATE_RANGE_PATTERN.finditer(text):
        start = _parse_month_year(match.group(1), match.group(2))
        end_token = match.group(3)
        if not start:
            continue
        if re.fullmatch(r"\d{4}", end_token, re.IGNORECASE):
            end = datetime(int(end_token), start.month, 1)
        else:
            end = now
        total_years += _years_between(start, end)

    for match in YEAR_RANGE_PATTERN.finditer(text):
        start_year = int(match.group(1))
        end_token = match.group(2)
        start = datetime(start_year, 1, 1)
        if re.fullmatch(r"\d{4}", end_token, re.IGNORECASE):
            end = datetime(int(end_token), 12, 31)
        else:
            end = now
        total_years += _years_between(start, end)

    return round(total_years, 1)


def _is_section_header(line: str) -> bool:
    stripped = line.strip().rstrip(":")
    return any(
        re.fullmatch(rf"{re.escape(header)}", stripped, re.IGNORECASE)
        for header in ALL_SECTION_HEADERS
    )


def _find_section_lines(text: str, headers: list[str]) -> list[str]:
    lines = text.splitlines()
    capture = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if capture and collected:
                break
            continue

        header_hit = any(
            re.fullmatch(rf"{re.escape(h)}:?", stripped, re.IGNORECASE) for h in headers
        )
        if header_hit:
            capture = True
            continue

        if capture:
            if _is_section_header(stripped):
                break
            collected.append(stripped)

    return collected


def extract_education(text: str) -> list[str]:
    section_lines = _find_section_lines(text, SECTION_HEADERS["education"])
    entries: list[str] = []

    for line in section_lines:
        lowered = line.lower()
        if any(degree in lowered for degree in DEGREE_KEYWORDS):
            entries.append(line)

    if not entries:
        for line in text.splitlines():
            lowered = line.lower()
            if any(degree in lowered for degree in DEGREE_KEYWORDS):
                entries.append(line.strip())

    return entries[:5]


def extract_projects(text: str) -> list[str]:
    return _find_section_lines(text, SECTION_HEADERS["projects"])[:10]


def extract_certifications(text: str) -> list[str]:
    return _find_section_lines(text, SECTION_HEADERS["certifications"])[:10]


def extract_recent_experience_end(text: str) -> str | None:
    latest: datetime | None = None
    latest_label: str | None = None
    now = datetime.now(UTC).replace(tzinfo=None)

    for match in DATE_RANGE_PATTERN.finditer(text):
        end_token = match.group(3)
        if re.fullmatch(rf"{MONTH_PATTERN}", end_token, re.IGNORECASE):
            end = _parse_month_year(end_token, match.group(2))
            if end and (latest is None or end > latest):
                latest = end
                latest_label = f"{match.group(3).title()} {match.group(2)}"
        elif re.search(r"present|current", end_token, re.IGNORECASE):
            return "Present"

    for match in YEAR_RANGE_PATTERN.finditer(text):
        end_token = match.group(2)
        if re.search(r"present|current", end_token, re.IGNORECASE):
            return "Present"
        if re.fullmatch(r"\d{4}", end_token):
            end = datetime(int(end_token), 12, 31)
            if latest is None or end > latest:
                latest = end
                latest_label = end_token

    return latest_label


def extract_structured_fields(raw_text: str) -> dict[str, Any]:
    text = clean_text(raw_text)
    return {
        "skills": extract_skills(text),
        "years_of_experience": extract_years_of_experience(text),
        "education": extract_education(text),
        "projects": extract_projects(text),
        "certifications": extract_certifications(text),
        "recent_experience_end": extract_recent_experience_end(text),
    }
