"""CAS EC-15 RS-232 중량 문자열 파서."""

from __future__ import annotations

import re
from dataclasses import dataclass


WEIGHT_PATTERN = re.compile(
    r"^(?P<label>NET|net)\s*:?\s*(?P<value>[+-]?\d+(?:\.\d+)?)\s*(?P<unit>g|kg)?\s*$"
)


@dataclass(frozen=True)
class ScaleWeight:
    value: float
    unit: str
    stable: bool


def parse_weight(line: str) -> ScaleWeight | None:
    """EC-15의 NET/net 한 줄을 중량 데이터로 변환한다."""
    match = WEIGHT_PATTERN.match(line.strip())
    if match is None:
        return None

    return ScaleWeight(
        value=float(match.group("value")),
        unit=match.group("unit") or "g",
        stable=match.group("label") == "NET",
    )
