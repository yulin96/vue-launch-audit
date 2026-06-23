#!/usr/bin/env python3
"""
Scan Vue projects for code shapes that often hide stale state or async-flow bugs.

Exit codes:
0 = no matches
1 = one or more review leads found
2 = invalid usage
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
}

SKIP_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "coverage",
    ".output",
    ".nuxt",
    ".next",
    "playwright-report",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    column: int
    severity: str
    code: str
    message: str
    snippet: str


@dataclass(frozen=True)
class LineRule:
    code: str
    severity: str
    pattern: re.Pattern[str]
    message: str


LINE_RULES = [
    LineRule(
        code="STATE_MERGE_OBJECT_ASSIGN",
        severity="HIGH",
        pattern=re.compile(r"\bObject\.assign\s*\("),
        message="对象合并更新，确认是否应该整体替换，避免保留上一次数据里的旧字段。",
    ),
    LineRule(
        code="STATE_MERGE_SPREAD",
        severity="HIGH",
        pattern=re.compile(r"=\s*\{[^}\n]*\.\.\.[^}\n]+,\s*\.\.\.[^}\n]+\}"),
        message="对象 spread 合并更新，确认新数据是否可能缺字段并残留旧信息。",
    ),
    LineRule(
        code="STATE_FIELD_MUTATION_AFTER_ASYNC",
        severity="LEAD",
        pattern=re.compile(r"\b\w+\.value\.[\w$]+\s*="),
        message="ref 对象字段级更新，确认这里不是在写入一个新的页面/接口实体。",
    ),
    LineRule(
        code="ASYNC_NOT_AWAITED",
        severity="LEAD",
        pattern=re.compile(r"(?<!await\s)(?<!return\s)\b(?:api|post|get|fetch|request)[\w$]*\s*\("),
        message="请求或异步调用没有 await/return，确认后续 UI、跳转或计时不依赖它完成。",
    ),
    LineRule(
        code="WATCH_SIDE_EFFECT",
        severity="LEAD",
        pattern=re.compile(r"\bwatch(?:Effect)?\s*\("),
        message="watch/watchEffect 入口，检查内部是否会重复触发请求、跳转、计时或刷新。",
    ),
    LineRule(
        code="ROUTE_GUARD_SIDE_EFFECT",
        severity="LEAD",
        pattern=re.compile(r"\brouter\.(?:push|replace)\s*\("),
        message="路由跳转，确认它不会被初始化、watcher 或接口回调重复触发。",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Vue source files for stale-state and async-flow risk patterns.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--include-ext",
        action="append",
        default=[],
        help="Extra file extension to scan, for example .mts.",
    )
    return parser.parse_args()


def should_scan_file(path: Path, extensions: set[str]) -> bool:
    return path.is_file() and path.suffix.lower() in extensions


def iter_files(root: Path, extensions: set[str]):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if should_scan_file(path, extensions):
            yield path


def find_empty_catches(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", text, re.DOTALL):
        line = text.count("\n", 0, match.start()) + 1
        line_start = text.rfind("\n", 0, match.start()) + 1
        column = match.start() - line_start + 1
        snippet = text[match.start() : match.end()].replace("\n", " ").strip()
        findings.append(
            Finding(
                path=path,
                line=line,
                column=column,
                severity="HIGH",
                code="EMPTY_CATCH",
                message="空 catch 会吞掉真实失败，确认用户是否能看到失败原因并重试。",
                snippet=snippet,
            )
        )
    return findings


def scan_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    findings = find_empty_catches(path, text)
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        for rule in LINE_RULES:
            match = rule.pattern.search(line)
            if match:
                findings.append(
                    Finding(
                        path=path,
                        line=line_number,
                        column=match.start() + 1,
                        severity=rule.severity,
                        code=rule.code,
                        message=rule.message,
                        snippet=stripped,
                    )
                )
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        return 2

    extensions = set(TEXT_EXTENSIONS)
    for ext in args.include_ext:
        normalized = ext if ext.startswith(".") else f".{ext}"
        extensions.add(normalized.lower())

    findings: list[Finding] = []
    for file_path in iter_files(root, extensions):
        findings.extend(scan_file(file_path))

    if not findings:
        print(f"No Vue state risk patterns found under {root}")
        return 0

    for item in findings:
        rel_path = item.path.relative_to(root)
        print(f"{rel_path}:{item.line}:{item.column} [{item.severity}] [{item.code}] {item.message}")
        print(f"  {item.snippet}")

    high_count = sum(1 for item in findings if item.severity == "HIGH")
    lead_count = len(findings) - high_count
    print(f"\nFound {len(findings)} Vue state/async review lead(s): {high_count} high, {lead_count} lead.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
