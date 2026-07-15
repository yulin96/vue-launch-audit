from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


state_scanner = load_module("scan_vue_state_risks", ROOT / "scripts" / "scan_vue_state_risks.py")
term_scanner = load_module("scan_terms", ROOT / "scripts" / "scan_terms.py")


class StateScannerTests(unittest.TestCase):
    def scan(self, source: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.ts"
            path.write_text(source, encoding="utf-8")
            return state_scanner.scan_file(path)

    def test_ignores_comments_strings_and_safe_object_creation(self):
        findings = self.scan(
            """
// catch (error) {}
const example = "catch (error) {}";
async function fetchData() {}
await(fetchData())
const merged = Object.assign({}, defaults)
"""
        )
        self.assertEqual([], findings)

    def test_finds_actionable_review_leads(self):
        findings = self.scan(
            """
try { run() } catch (error) {}
Object.assign(pageState, response.data)
pageState.value = {
  ...pageState.value,
  ...response.data,
}
scanLoading.value = true
document.createElement('script')
"""
        )
        codes = {finding.code for finding in findings}
        self.assertEqual(
            {
                "EMPTY_CATCH",
                "STATE_MERGE_OBJECT_ASSIGN",
                "STATE_MERGE_SPREAD",
                "LOCK_SET_TRUE",
                "DYNAMIC_SCRIPT_LOAD",
            },
            codes,
        )
        self.assertTrue(all(finding.priority in {"REVIEW_FIRST", "LEAD"} for finding in findings))


class TermScannerTests(unittest.TestCase):
    def test_baseline_and_optional_style_rules_are_separate(self):
        baseline, baseline_patterns = term_scanner.load_rules(
            [str(ROOT / "references" / "term-rules.json")],
            [],
        )
        combined, combined_patterns = term_scanner.load_rules(
            [
                str(ROOT / "references" / "term-rules.json"),
                str(ROOT / "references" / "term-style-rules.json"),
            ],
            [],
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "copy.vue"
            path.write_text("优惠卷 Wechat！！", encoding="utf-8")
            baseline_hits = term_scanner.scan_file(path, baseline, baseline_patterns)
            combined_hits = term_scanner.scan_file(path, combined, combined_patterns)

        self.assertEqual(["优惠卷"], [item["wrong"] for item in baseline_hits])
        self.assertEqual({"优惠卷", "Wechat", "！！"}, {item["wrong"] for item in combined_hits})


if __name__ == "__main__":
    unittest.main()
