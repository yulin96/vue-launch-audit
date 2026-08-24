from __future__ import annotations

import importlib.util
import json
import subprocess
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
    def scan(self, source: str, rules: set[str] | None = None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.ts"
            path.write_text(source, encoding="utf-8")
            return state_scanner.scan_file(path, rules)

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
        self.assertEqual(
            {
                "EMPTY_CATCH",
                "STATE_MERGE_OBJECT_ASSIGN",
                "STATE_MERGE_SPREAD",
                "LOCK_SET_TRUE",
                "DYNAMIC_SCRIPT_LOAD",
            },
            {finding.code for finding in findings},
        )
        self.assertTrue(all(finding.priority in {"REVIEW_FIRST", "LEAD"} for finding in findings))

    def test_rule_filter_and_sensitive_snippet_redaction(self):
        findings = self.scan(
            'const apiKey = "private-value"; apiKeyLoading = true',
            {"LOCK_SET_TRUE"},
        )
        self.assertEqual(["LOCK_SET_TRUE"], [finding.code for finding in findings])
        self.assertNotIn("private-value", findings[0].snippet)
        self.assertIn("<redacted>", findings[0].snippet)

    def test_fixture_json_output_and_path_filter(self):
        fixture = ROOT / "evals" / "fixtures" / "state-residual"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "scan_vue_state_risks.py"),
                "--root",
                str(fixture),
                "--format",
                "json",
                "--include-path",
                "src/**",
                "--rule",
                "STATE_MERGE_OBJECT_ASSIGN",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual("vue-state-risks", payload["scanner"])
        self.assertEqual(1, payload["total"])
        self.assertEqual("Lead", payload["findings"][0]["evidence_state"])
        self.assertEqual("src/UserPage.vue", payload["findings"][0]["path"])


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

        self.assertEqual(["优惠卷"], [item.wrong for item in baseline_hits])
        self.assertEqual({"优惠卷", "Wechat", "！！"}, {item.wrong for item in combined_hits})

    def test_json_output_limit_and_env_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "copy.vue").write_text("优惠卷 优惠卷", encoding="utf-8")
            (root / ".env.production").write_text("TITLE=优惠卷", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "scan_terms.py"),
                    "--root",
                    str(root),
                    "--rules",
                    str(ROOT / "references" / "term-rules.json"),
                    "--format",
                    "json",
                    "--max-results",
                    "1",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual(2, payload["total"])
        self.assertEqual(1, payload["returned"])
        self.assertTrue(payload["truncated"])
        self.assertEqual("src/copy.vue", payload["findings"][0]["path"])


class ChangedOnlyTests(unittest.TestCase):
    def test_changed_paths_include_modified_and_untracked_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            tracked = root / "tracked.vue"
            tracked.write_text("<template>ok</template>", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.vue"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=Skill Test",
                    "-c",
                    "user.email=skill@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            tracked.write_text("<template>changed</template>", encoding="utf-8")
            (root / "new.ts").write_text("const value = 1", encoding="utf-8")

            self.assertEqual({"new.ts", "tracked.vue"}, state_scanner.changed_paths(root))
            self.assertEqual({"new.ts", "tracked.vue"}, term_scanner.changed_paths(root))


class EvalManifestTests(unittest.TestCase):
    def test_eval_manifest_has_existing_fixtures_and_observable_assertions(self):
        payload = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(2, payload["schema_version"])
        modes = {item["mode"] for item in payload["evals"]}
        self.assertEqual(
            {"full_audit", "targeted_diagnosis", "copy_audit", "implementation", "not_applicable"},
            modes,
        )
        for item in payload["evals"]:
            self.assertTrue(item["assertions"])
            if item["fixture"]:
                self.assertTrue((ROOT / "evals" / item["fixture"]).is_dir())

    def test_full_audit_evals_cover_reporting_contract(self):
        payload = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        full_audits = {
            item["id"]: set(item["assertions"])
            for item in payload["evals"]
            if item["mode"] == "full_audit"
        }

        self.assertIn("full-audit-p0-cross-user-corruption", full_audits)
        self.assertIn("full-audit-mixed-severity-ordering", full_audits)

        assertions = set().union(*full_audits.values())
        self.assertTrue(
            {
                "shows_p0_and_p1_sections_even_when_empty",
                "orders_findings_by_severity",
                "uses_stable_finding_identifiers",
                "separates_severity_from_evidence_state",
                "does_not_map_scanner_priority_to_severity",
            }.issubset(assertions)
        )


if __name__ == "__main__":
    unittest.main()
