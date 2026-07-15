#!/usr/bin/env python3
"""
Scan a repository for common wrong spellings and text quality patterns.

Exit codes:
0 = no matches
1 = one or more matches found
2 = invalid usage or rules file
"""

from __future__ import annotations

import argparse
import json
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan text files for known wrong spellings.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--rules",
        action="append",
        default=[],
        help="Path to a JSON rules file. Repeat to combine baseline and project style rules.",
    )
    parser.add_argument(
        "--pair",
        action="append",
        default=[],
        help="Extra rule in Correct=Wrong format. Repeat as needed.",
    )
    parser.add_argument(
        "--include-ext",
        action="append",
        default=[],
        help="Extra file extension to scan, for example .xml.",
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
                    rules.append(Rule(correct=correct.strip(), wrong=wrong.strip(), case_sensitive=case_sensitive))

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
                    pattern_rules.append(
                        PatternRule(
                            pattern=pattern,
                            suggestion=suggestion.strip(),
                            case_sensitive=case_sensitive,
                        )
                    )

            if wrong_values is None and pattern_values is None:
                raise ValueError("Each rule must include 'wrong' or 'patterns'.")

    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid --pair value {pair!r}. Use Correct=Wrong.")
        correct, wrong = pair.split("=", 1)
        correct = correct.strip()
        wrong = wrong.strip()
        if not correct or not wrong:
            raise ValueError(f"Invalid --pair value {pair!r}. Use Correct=Wrong.")
        rules.append(Rule(correct=correct, wrong=wrong, case_sensitive=True))

    if not rules and not pattern_rules:
        raise ValueError("No rules loaded. Provide --rules, --pair, or both.")

    return rules, pattern_rules


def should_scan_file(path: Path, extensions: set[str]) -> bool:
    is_env_file = path.name == ".env" or path.name.startswith(".env.")
    return path.is_file() and (is_env_file or path.suffix.lower() in extensions)


def build_pattern(term: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", term):
        return rf"(?<![\w-]){re.escape(term)}(?![\w-])"
    return re.escape(term)


def iter_files(root: Path, extensions: set[str]):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if should_scan_file(path, extensions):
            yield path


def scan_file(path: Path, rules: list[Rule], pattern_rules: list[PatternRule]):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    findings = []
    for line_number, line in enumerate(lines, start=1):
        for rule in rules:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            for match in re.finditer(build_pattern(rule.wrong), line, flags):
                findings.append(
                    {
                        "path": path,
                        "line": line_number,
                        "column": match.start() + 1,
                        "wrong": match.group(0),
                        "correct": rule.correct,
                    }
                )
        for rule in pattern_rules:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            for match in re.finditer(rule.pattern, line, flags):
                findings.append(
                    {
                        "path": path,
                        "line": line_number,
                        "column": match.start() + 1,
                        "wrong": match.group(0),
                        "correct": rule.suggestion,
                    }
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

    try:
        rules, pattern_rules = load_rules(args.rules, args.pair)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ignored_paths = set()
    for rules_path in args.rules:
        ignored_paths.add(Path(rules_path).resolve())

    findings = []
    for file_path in iter_files(root, extensions):
        if file_path.resolve() in ignored_paths:
            continue
        findings.extend(scan_file(file_path, rules, pattern_rules))

    if not findings:
        print(f"No term issues found under {root}")
        return 0

    for item in findings:
        rel_path = item["path"].relative_to(root)
        print(
            f"{rel_path}:{item['line']}:{item['column']} "
            f"{item['wrong']} -> {item['correct']}"
        )

    print(f"\nFound {len(findings)} possible term issue(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
