from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PLAN_LINK_RE = re.compile(r"\((mvp-[^)#]+\.md)\)")


@dataclass(frozen=True)
class QualityCheckResult:
    checked_plan_count: int
    checked_links: list[str]


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _plan_links(index_text: str) -> list[str]:
    return sorted(set(PLAN_LINK_RE.findall(index_text)))


def _require_any(text: str, needles: Iterable[str], label: str, plan_path: Path) -> None:
    if not any(needle in text for needle in needles):
        options = ", ".join(needles)
        raise ValueError(f"{plan_path} is missing {label}; expected one of: {options}")


def _check_plan_scaffold(plan_path: Path, text: str) -> None:
    if not text.startswith("# "):
        raise ValueError(f"{plan_path} must start with a markdown H1")
    if "\nStatus:" not in text:
        raise ValueError(f"{plan_path} must contain a Status line")

    _require_any(text, ["## Goal", "## Purpose"], "goal/purpose section", plan_path)
    _require_any(text, ["## Execution Tasks", "## Implementation Tasks"], "task section", plan_path)
    _require_any(text, ["## Acceptance Evidence", "## Acceptance Criteria"], "acceptance section", plan_path)
    _require_any(text, ["## Non-Goals"], "non-goals section", plan_path)
    _require_any(text, ["## Stop Condition", "## Follow-On Gaps After This Plan"], "stop/follow-on section", plan_path)


def check_quality_surface(repo_root: Path) -> QualityCheckResult:
    plans_dir = repo_root / "docs" / "plans"
    index_path = plans_dir / "mvp-implementation-phases.md"
    index_text = _read_text(index_path)
    links = _plan_links(index_text)
    if not links:
        raise ValueError("MVP implementation index does not link any plan files")

    plan_files = sorted(path.name for path in plans_dir.glob("mvp-*.md") if path.name != index_path.name)
    missing_from_index = [name for name in plan_files if name not in links]
    if missing_from_index:
        raise ValueError(f"MVP implementation index is missing plan links: {', '.join(missing_from_index)}")

    missing_files = [link for link in links if not (plans_dir / link).exists()]
    if missing_files:
        raise ValueError(f"MVP implementation index links missing plan files: {', '.join(missing_files)}")

    for plan_name in plan_files:
        plan_path = plans_dir / plan_name
        _check_plan_scaffold(plan_path, _read_text(plan_path))

    return QualityCheckResult(checked_plan_count=len(plan_files), checked_links=links)
