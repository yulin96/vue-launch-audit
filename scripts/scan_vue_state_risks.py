#!/usr/bin/env python3
"""Scan Vue source for stale-state and async-flow review leads.

Exit codes:
0 = no matches
1 = one or more review leads found
2 = invalid usage
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".vue", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
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
    priority: str
    code: str
    message: str
    snippet: str


@dataclass(frozen=True)
class LineRule:
    code: str
    priority: str
    pattern: re.Pattern[str]
    message: str
    scan_strings: bool = False


LINE_RULES = [
    LineRule(
        "STATE_MERGE_OBJECT_ASSIGN",
        "REVIEW_FIRST",
        re.compile(r"\bObject\.assign\s*\(\s*(?!\{\s*\})"),
        "向已有对象合并数据，确认是否应该整体替换，避免保留上一次数据里的旧字段。",
    ),
    LineRule(
        "STATE_FIELD_MUTATION_AFTER_ASYNC",
        "LEAD",
        re.compile(r"\b\w+\.value\.[\w$]+\s*="),
        "ref 对象字段级更新，确认这里不是在写入一个新的页面或接口实体。",
    ),
    LineRule(
        "WATCH_SIDE_EFFECT",
        "LEAD",
        re.compile(r"\bwatch(?:Effect)?\s*\("),
        "watch/watchEffect 入口，检查内部是否会重复触发请求、跳转、计时或刷新。",
    ),
    LineRule(
        "ROUTE_GUARD_SIDE_EFFECT",
        "LEAD",
        re.compile(r"\brouter\.(?:push|replace)\s*\("),
        "路由跳转，确认它不会被初始化、watcher 或接口回调重复触发。",
    ),
    LineRule(
        "PROMISE_BRANCH_CLOSURE",
        "LEAD",
        re.compile(r"\bnew\s+Promise\s*\("),
        "手写 Promise 包装，确认所有业务分支都会结束，并释放 loading 或 lock。",
    ),
    LineRule(
        "LOCK_SET_TRUE",
        "REVIEW_FIRST",
        re.compile(
            r"\b[\w$]*(?:lock|Lock|locked|Locked|loading|Loading|submitting|Submitting)[\w$]*"
            r"(?:\.value)?\s*=\s*true\b"
        ),
        "锁或 loading 被置为 true，确认成功、失败、取消和配置失败分支都会恢复。",
    ),
    LineRule(
        "TOAST_OBJECT_PAYLOAD",
        "LEAD",
        re.compile(r"\b(?:toast\.\w+|Toast|showToast|showFailToast|showSuccessToast)\s*\(\s*\{"),
        "toast/modal 首参是对象，确认当前库的参数约定和实际可见输出。",
    ),
    LineRule(
        "DYNAMIC_SCRIPT_LOAD",
        "LEAD",
        re.compile(
            r"\bcreateElement\s*\(\s*['\"]script['\"]\s*\)|"
            r"\.appendChild\s*\(\s*\w*script",
            re.IGNORECASE,
        ),
        "动态脚本加载，确认加载失败时用户动作不会表现为成功或无响应。",
        scan_strings=True,
    ),
    LineRule(
        "DIRECT_STORAGE_ACCESS",
        "LEAD",
        re.compile(r"\b(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\s*\("),
        "直接读写浏览器存储，确认 key 包含必要的用户、活动、语言或渠道身份。",
    ),
]

SPECIAL_RULES = {"EMPTY_CATCH", "STATE_MERGE_SPREAD"}
AVAILABLE_RULES = SPECIAL_RULES | {rule.code for rule in LINE_RULES}
SENSITIVE_VALUE = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key)(\s*[:=]\s*)(['\"]).*?\3"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan Vue source for stale-state and async-flow review leads.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--include-ext", action="append", default=[], help="Extra extension, for example .mts.")
    parser.add_argument(
        "--include-path",
        action="append",
        default=[],
        help="Relative path or glob to include. Repeat as needed.",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        help="Relative path or glob to exclude. Repeat as needed.",
    )
    parser.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Run only the named rule code. Repeat as needed.",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Scan tracked and untracked working-tree changes only.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--max-results",
        type=int,
        default=200,
        help="Maximum findings to emit; 0 means unlimited.",
    )
    return parser.parse_args()


def mask_non_code(text: str, preserve_strings: bool = False) -> str:
    """Mask comments and optionally strings while preserving offsets and newlines."""
    chars = list(text)
    index = 0
    state = "code"
    quote = ""

    while index < len(chars):
        current = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""

        if state == "code":
            if current == "/" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if current == "/" and next_char == "*":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if text.startswith("<!--", index):
                for offset in range(4):
                    chars[index + offset] = " "
                index += 4
                state = "html_comment"
                continue
            if current in {"'", '"', "`"}:
                quote = current
                if not preserve_strings:
                    chars[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if current == "\n":
                state = "code"
            else:
                chars[index] = " "
        elif state == "block_comment":
            if current == "*" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "code"
                continue
            if current != "\n":
                chars[index] = " "
        elif state == "html_comment":
            if text.startswith("-->", index):
                for offset in range(3):
                    chars[index + offset] = " "
                index += 3
                state = "code"
                continue
            if current != "\n":
                chars[index] = " "
        elif state == "string":
            if current == "\\" and next_char:
                if not preserve_strings:
                    chars[index] = " "
                    if next_char != "\n":
                        chars[index + 1] = " "
                index += 2
                continue
            if current == quote:
                if not preserve_strings:
                    chars[index] = " "
                state = "code"
            elif not preserve_strings and current != "\n":
                chars[index] = " "
        index += 1

    return "".join(chars)


def normalize_pattern(pattern: str) -> str:
    value = pattern.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def matches_path(relative_path: str, patterns: list[str]) -> bool:
    for raw_pattern in patterns:
        pattern = normalize_pattern(raw_pattern)
        if (
            relative_path == pattern
            or relative_path.startswith(f"{pattern}/")
            or fnmatch.fnmatchcase(relative_path, pattern)
        ):
            return True
    return False


def changed_paths(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "not a Git working tree"
        raise ValueError(f"--changed-only requires Git status: {detail}")

    records = result.stdout.split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status = record[:2]
        path = record[3:]
        if path:
            paths.add(path)
        if ("R" in status or "C" in status) and index < len(records):
            renamed_from = records[index]
            index += 1
            if renamed_from:
                paths.add(renamed_from)
    return paths


def iter_files(
    root: Path,
    extensions: set[str],
    include_paths: list[str],
    exclude_paths: list[str],
    changed: set[str] | None,
):
    candidates = (
        (root / relative for relative in sorted(changed))
        if changed is not None
        else root.rglob("*")
    )
    selected: list[Path] = []
    for path in candidates:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in Path(relative).parts):
            continue
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if include_paths and not matches_path(relative, include_paths):
            continue
        if exclude_paths and matches_path(relative, exclude_paths):
            continue
        selected.append(path)
    yield from sorted(set(selected), key=lambda item: item.relative_to(root).as_posix())


def redact_snippet(snippet: str) -> str:
    return SENSITIVE_VALUE.sub(lambda match: f"{match.group(1)}{match.group(2)}<redacted>", snippet)


def finding_from_match(
    path: Path,
    source_text: str,
    match: re.Match[str],
    priority: str,
    code: str,
    message: str,
) -> Finding:
    line = source_text.count("\n", 0, match.start()) + 1
    line_start = source_text.rfind("\n", 0, match.start()) + 1
    line_end = source_text.find("\n", match.start())
    if line_end == -1:
        line_end = len(source_text)
    return Finding(
        path,
        line,
        match.start() - line_start + 1,
        priority,
        code,
        message,
        redact_snippet(source_text[line_start:line_end].strip()),
    )


def scan_file(path: Path, enabled_rules: set[str] | None = None) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    enabled = enabled_rules or AVAILABLE_RULES
    code_text = mask_non_code(text)
    code_with_strings = mask_non_code(text, preserve_strings=True)
    findings: list[Finding] = []

    if "EMPTY_CATCH" in enabled:
        for match in re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", code_text, re.DOTALL):
            findings.append(
                finding_from_match(
                    path,
                    text,
                    match,
                    "REVIEW_FIRST",
                    "EMPTY_CATCH",
                    "空 catch 会吞掉失败，确认用户是否能看到原因并重试。",
                )
            )

    if "STATE_MERGE_SPREAD" in enabled:
        spread_pattern = re.compile(
            r"=\s*\{(?=[^{}]{0,500}\.\.\.[^{}]{0,500}\.\.\.)[^{}]{0,500}\}",
            re.DOTALL,
        )
        for match in spread_pattern.finditer(code_text):
            findings.append(
                finding_from_match(
                    path,
                    text,
                    match,
                    "REVIEW_FIRST",
                    "STATE_MERGE_SPREAD",
                    "对象 spread 合并更新，确认新数据缺字段时是否会残留旧信息。",
                )
            )

    source_lines = text.splitlines()
    code_lines = code_text.splitlines()
    string_lines = code_with_strings.splitlines()
    for line_number, source_line in enumerate(source_lines, start=1):
        if not source_line.strip():
            continue
        for rule in LINE_RULES:
            if rule.code not in enabled:
                continue
            candidate = string_lines[line_number - 1] if rule.scan_strings else code_lines[line_number - 1]
            match = rule.pattern.search(candidate)
            if match:
                findings.append(
                    Finding(
                        path,
                        line_number,
                        match.start() + 1,
                        rule.priority,
                        rule.code,
                        rule.message,
                        redact_snippet(source_line.strip()),
                    )
                )
    return findings


def finding_payload(finding: Finding, root: Path) -> dict[str, object]:
    return {
        "path": finding.path.relative_to(root).as_posix(),
        "line": finding.line,
        "column": finding.column,
        "priority": finding.priority,
        "code": finding.code,
        "message": finding.message,
        "snippet": finding.snippet,
        "evidence_state": "Lead",
    }


def emit_json(root: Path, findings: list[Finding], emitted: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "schema_version": 1,
                "scanner": "vue-state-risks",
                "root": str(root),
                "total": len(findings),
                "returned": len(emitted),
                "truncated": len(emitted) < len(findings),
                "summary": {
                    "review_first": sum(item.priority == "REVIEW_FIRST" for item in findings),
                    "lead": sum(item.priority == "LEAD" for item in findings),
                },
                "findings": [finding_payload(item, root) for item in emitted],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def emit_text(root: Path, findings: list[Finding], emitted: list[Finding]) -> None:
    if not findings:
        print(f"No Vue state risk patterns found under {root}")
        return
    for item in emitted:
        rel_path = item.path.relative_to(root)
        print(f"{rel_path}:{item.line}:{item.column} [{item.priority}] [{item.code}] {item.message}")
        print(f"  {item.snippet}")
    review_first = sum(item.priority == "REVIEW_FIRST" for item in findings)
    leads = len(findings) - review_first
    suffix = f"; showing {len(emitted)}" if len(emitted) < len(findings) else ""
    print(f"\nFound {len(findings)} review lead(s): {review_first} review first, {leads} lead{suffix}.")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Root not found: {root}", file=sys.stderr)
        return 2
    if args.max_results < 0:
        print("--max-results must be 0 or greater.", file=sys.stderr)
        return 2

    enabled_rules = set(args.rule) if args.rule else AVAILABLE_RULES
    unknown_rules = enabled_rules - AVAILABLE_RULES
    if unknown_rules:
        print(
            f"Unknown rule(s): {', '.join(sorted(unknown_rules))}. "
            f"Available: {', '.join(sorted(AVAILABLE_RULES))}",
            file=sys.stderr,
        )
        return 2

    extensions = set(TEXT_EXTENSIONS)
    for extension in args.include_ext:
        normalized = extension if extension.startswith(".") else f".{extension}"
        extensions.add(normalized.lower())

    try:
        changed = changed_paths(root) if args.changed_only else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for file_path in iter_files(root, extensions, args.include_path, args.exclude_path, changed):
        findings.extend(scan_file(file_path, enabled_rules))
    findings.sort(key=lambda item: (item.path.relative_to(root).as_posix(), item.line, item.column, item.code))

    emitted = findings if args.max_results == 0 else findings[: args.max_results]
    if args.format == "json":
        emit_json(root, findings, emitted)
    else:
        emit_text(root, findings, emitted)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
