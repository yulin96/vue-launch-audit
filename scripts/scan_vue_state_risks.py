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
        code="STATE_MERGE_OBJECT_ASSIGN",
        priority="REVIEW_FIRST",
        pattern=re.compile(r"\bObject\.assign\s*\(\s*(?!\{\s*\})"),
        message="向已有对象合并数据，确认是否应该整体替换，避免保留上一次数据里的旧字段。",
    ),
    LineRule(
        code="STATE_FIELD_MUTATION_AFTER_ASYNC",
        priority="LEAD",
        pattern=re.compile(r"\b\w+\.value\.[\w$]+\s*="),
        message="ref 对象字段级更新，确认这里不是在写入一个新的页面/接口实体。",
    ),
    LineRule(
        code="WATCH_SIDE_EFFECT",
        priority="LEAD",
        pattern=re.compile(r"\bwatch(?:Effect)?\s*\("),
        message="watch/watchEffect 入口，检查内部是否会重复触发请求、跳转、计时或刷新。",
    ),
    LineRule(
        code="ROUTE_GUARD_SIDE_EFFECT",
        priority="LEAD",
        pattern=re.compile(r"\brouter\.(?:push|replace)\s*\("),
        message="路由跳转，确认它不会被初始化、watcher 或接口回调重复触发。",
    ),
    LineRule(
        code="PROMISE_BRANCH_CLOSURE",
        priority="LEAD",
        pattern=re.compile(r"\bnew\s+Promise\s*\("),
        message="手写 Promise 包装，确认所有业务分支都会 return/resolve/reject，并释放 loading 或 lock。",
    ),
    LineRule(
        code="LOCK_SET_TRUE",
        priority="REVIEW_FIRST",
        pattern=re.compile(
            r"\b[\w$]*(?:lock|Lock|locked|Locked|loading|Loading|submitting|Submitting)[\w$]*"
            r"(?:\.value)?\s*=\s*true\b"
        ),
        message="锁或 loading 被置为 true，确认成功、失败、取消、SDK 配置失败分支都会恢复。",
    ),
    LineRule(
        code="TOAST_OBJECT_PAYLOAD",
        priority="LEAD",
        pattern=re.compile(r"\b(?:toast\.\w+|Toast|showToast|showFailToast|showSuccessToast)\s*\(\s*\{"),
        message="toast/modal 首参是对象，确认当前库是否会把对象渲染成 [object Object] 或丢失 message。",
    ),
    LineRule(
        code="DYNAMIC_SCRIPT_LOAD",
        priority="LEAD",
        pattern=re.compile(r"\bcreateElement\s*\(\s*['\"]script['\"]\s*\)|\.appendChild\s*\(\s*\w*script", re.IGNORECASE),
        message="动态脚本加载，确认加载失败时用户动作不会表现为成功或无响应。",
        scan_strings=True,
    ),
    LineRule(
        code="DIRECT_STORAGE_ACCESS",
        priority="LEAD",
        pattern=re.compile(r"\b(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\s*\("),
        message="直接读写浏览器存储，确认 key 包含必要的用户、活动、语言或渠道身份。",
    ),
]


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
        path=path,
        line=line,
        column=match.start() - line_start + 1,
        priority=priority,
        code=code,
        message=message,
        snippet=source_text[line_start:line_end].strip(),
    )


def find_empty_catches(path: Path, source_text: str, code_text: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", code_text, re.DOTALL):
        findings.append(
            finding_from_match(
                path,
                source_text,
                match,
                "REVIEW_FIRST",
                "EMPTY_CATCH",
                "空 catch 会吞掉真实失败，确认用户是否能看到失败原因并重试。",
            )
        )
    return findings


def find_spread_merges(path: Path, source_text: str, code_text: str) -> list[Finding]:
    pattern = re.compile(r"=\s*\{(?=[^{}]{0,500}\.\.\.[^{}]{0,500}\.\.\.)[^{}]{0,500}\}", re.DOTALL)
    return [
        finding_from_match(
            path,
            source_text,
            match,
            "REVIEW_FIRST",
            "STATE_MERGE_SPREAD",
            "对象 spread 合并更新，确认新数据是否可能缺字段并残留旧信息。",
        )
        for match in pattern.finditer(code_text)
    ]


def scan_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    code_text = mask_non_code(text)
    code_with_strings = mask_non_code(text, preserve_strings=True)
    findings = find_empty_catches(path, text, code_text)
    findings.extend(find_spread_merges(path, text, code_text))
    source_lines = text.splitlines()
    code_lines = code_text.splitlines()
    string_lines = code_with_strings.splitlines()
    for line_number, source_line in enumerate(source_lines, start=1):
        if not source_line.strip():
            continue
        for rule in LINE_RULES:
            candidate = string_lines[line_number - 1] if rule.scan_strings else code_lines[line_number - 1]
            match = rule.pattern.search(candidate)
            if match:
                findings.append(
                    Finding(
                        path=path,
                        line=line_number,
                        column=match.start() + 1,
                        priority=rule.priority,
                        code=rule.code,
                        message=rule.message,
                        snippet=source_line.strip(),
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
        print(f"{rel_path}:{item.line}:{item.column} [{item.priority}] [{item.code}] {item.message}")
        print(f"  {item.snippet}")

    review_first_count = sum(1 for item in findings if item.priority == "REVIEW_FIRST")
    lead_count = len(findings) - review_first_count
    print(
        f"\nFound {len(findings)} Vue state/async review lead(s): "
        f"{review_first_count} review first, {lead_count} lead."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
