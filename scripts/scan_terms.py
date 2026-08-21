#!/usr/bin/env python3
"""Scan selected project text for configured wording review leads.

Exit codes:
0 = no matches
1 = one or more review leads found
2 = invalid usage or rules
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


TEXT_EXTENSIONS = {
    ".vue",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".html",
    ".css",
    ".scss",
    ".less",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".svg",
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
class Rule:
    correct: str
    wrong: str
    case_sensitive: bool = True


@dataclass(frozen=True)
class PatternRule:
    pattern: str
    suggestion: str
    case_sensitive: bool = True


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    column: int
    wrong: str
    correct: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan selected project text for configured wording review leads.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--rules",
        action="append",
        default=[],
        help="JSON rules file. Repeat to combine baseline and approved style rules.",
    )
    parser.add_argument("--pair", action="append", default=[], help="Extra Correct=Wrong rule. Repeat as needed.")
    parser.add_argument("--include-ext", action="append", default=[], help="Extra extension, for example .xml.")
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


def load_rules(rules_paths: list[str], pairs: list[str]) -> tuple[list[Rule], list[PatternRule]]:
    rules: list[Rule] = []
    pattern_rules: list[PatternRule] = []

    for rules_path in rules_paths:
        path = Path(rules_path)
        try:
            raw_rules = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Failed to read rules file {path}: {exc}") from exc
        if not isinstance(raw_rules, list):
            raise ValueError("Rules file must be a JSON array.")

        for item in raw_rules:
            if not isinstance(item, dict):
                raise ValueError("Each rule entry must be a JSON object.")
            correct = item.get("correct")
            wrong_values = item.get("wrong")
            pattern_values = item.get("patterns")
            suggestion = item.get("suggestion", correct)
            case_sensitive = item.get("case_sensitive", True)
            if not isinstance(case_sensitive, bool):
                raise ValueError(f"Rule for {correct!r} has non-boolean 'case_sensitive'.")

            if wrong_values is not None:
                if not isinstance(correct, str) or not correct.strip():
                    raise ValueError("Rules with 'wrong' must include a non-empty 'correct' string.")
                if not isinstance(wrong_values, list) or not wrong_values:
                    raise ValueError(f"Rule for {correct!r} must include a non-empty 'wrong' list.")
                for wrong in wrong_values:
                    if not isinstance(wrong, str) or not wrong.strip():
                        raise ValueError(f"Rule for {correct!r} includes an invalid wrong value.")
                    rules.append(Rule(correct.strip(), wrong.strip(), case_sensitive))

            if pattern_values is not None:
                if not isinstance(suggestion, str) or not suggestion.strip():
                    raise ValueError("Rules with 'patterns' must include 'suggestion' or 'correct'.")
                if not isinstance(pattern_values, list) or not pattern_values:
                    raise ValueError(f"Pattern rule for {suggestion!r} must include a non-empty 'patterns' list.")
                for pattern in pattern_values:
                    if not isinstance(pattern, str) or not pattern.strip():
                        raise ValueError(f"Pattern rule for {suggestion!r} includes an invalid pattern.")
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        raise ValueError(f"Invalid regex pattern {pattern!r}: {exc}") from exc
                    pattern_rules.append(PatternRule(pattern, suggestion.strip(), case_sensitive))

            if wrong_values is None and pattern_values is None:
                raise ValueError("Each rule must include 'wrong' or 'patterns'.")

    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid --pair value {pair!r}. Use Correct=Wrong.")
        correct, wrong = (value.strip() for value in pair.split("=", 1))
        if not correct or not wrong:
            raise ValueError(f"Invalid --pair value {pair!r}. Use Correct=Wrong.")
        rules.append(Rule(correct, wrong))

    if not rules and not pattern_rules:
        raise ValueError("No rules loaded. Provide --rules, --pair, or both.")
    return rules, pattern_rules


def build_pattern(term: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", term):
        return rf"(?<![\w-]){re.escape(term)}(?![\w-])"
    return re.escape(term)


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
        if path.name == ".env" or path.name.startswith(".env."):
            continue
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if include_paths and not matches_path(relative, include_paths):
            continue
        if exclude_paths and matches_path(relative, exclude_paths):
            continue
        selected.append(path)
    yield from sorted(set(selected), key=lambda item: item.relative_to(root).as_posix())


def scan_file(path: Path, rules: list[Rule], pattern_rules: list[PatternRule]) -> list[Finding]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    for line_number, line in enumerate(lines, start=1):
        for rule in rules:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            for match in re.finditer(build_pattern(rule.wrong), line, flags):
                findings.append(
                    Finding(path, line_number, match.start() + 1, match.group(0), rule.correct)
                )
        for rule in pattern_rules:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            for match in re.finditer(rule.pattern, line, flags):
                findings.append(
                    Finding(path, line_number, match.start() + 1, match.group(0), rule.suggestion)
                )
    return findings


def finding_payload(finding: Finding, root: Path) -> dict[str, object]:
    return {
        "path": finding.path.relative_to(root).as_posix(),
        "line": finding.line,
        "column": finding.column,
        "wrong": finding.wrong,
        "correct": finding.correct,
        "evidence_state": "Lead",
    }


def emit_json(root: Path, findings: list[Finding], emitted: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "schema_version": 1,
                "scanner": "vue-copy-terms",
                "root": str(root),
                "total": len(findings),
                "returned": len(emitted),
                "truncated": len(emitted) < len(findings),
                "findings": [finding_payload(item, root) for item in emitted],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def emit_text(root: Path, findings: list[Finding], emitted: list[Finding]) -> None:
    if not findings:
        print(f"No term issues found under {root}")
        return
    for item in emitted:
        rel_path = item.path.relative_to(root)
        print(f"{rel_path}:{item.line}:{item.column} {item.wrong} -> {item.correct}")
    suffix = f"; showing {len(emitted)}" if len(emitted) < len(findings) else ""
    print(f"\nFound {len(findings)} possible term issue(s){suffix}.")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Root not found: {root}", file=sys.stderr)
        return 2
    if args.max_results < 0:
        print("--max-results must be 0 or greater.", file=sys.stderr)
        return 2

    try:
        rules, pattern_rules = load_rules(args.rules, args.pair)
        changed = changed_paths(root) if args.changed_only else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    extensions = set(TEXT_EXTENSIONS)
    for extension in args.include_ext:
        normalized = extension if extension.startswith(".") else f".{extension}"
        extensions.add(normalized.lower())

    ignored_rule_paths = {Path(path).resolve() for path in args.rules}
    findings: list[Finding] = []
    for file_path in iter_files(root, extensions, args.include_path, args.exclude_path, changed):
        if file_path.resolve() in ignored_rule_paths:
            continue
        findings.extend(scan_file(file_path, rules, pattern_rules))
    findings.sort(
        key=lambda item: (item.path.relative_to(root).as_posix(), item.line, item.column, item.wrong)
    )

    emitted = findings if args.max_results == 0 else findings[: args.max_results]
    if args.format == "json":
        emit_json(root, findings, emitted)
    else:
        emit_text(root, findings, emitted)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
