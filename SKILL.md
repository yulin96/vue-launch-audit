---
name: vue-launch-audit
description: Audit Vue release readiness or diagnose a release-related Vue user flow. Use for Vue projects when the user asks for a pre-release review, launch-risk check, targeted route/request/state diagnosis, or user-visible copy audit. Do not use for non-Vue projects, ordinary style review, or unrelated component refactoring.
---

# Vue Launch Audit

Find user-impacting release risks in Vue applications and report only what the available evidence supports.

## Choose One Mode

Select the narrowest mode that satisfies the request. Do not run a full audit for a targeted symptom.

- **Full audit**: The user asks for a general pre-release or launch-risk review. Read [references/review-checklist.md](references/review-checklist.md).
- **Targeted diagnosis**: The user names a broken or suspicious flow, such as stale data, a stuck button, a wrong route branch, or a silent SDK action. Read [references/targeted-diagnosis.md](references/targeted-diagnosis.md).
- **Copy audit**: The request is mainly about visible wording, brand names, links, numbers, or typography. Read [references/copy-audit.md](references/copy-audit.md).
- **Implementation**: The user explicitly asks to fix a confirmed problem. Diagnose first, then make only the scoped change and run targeted validation. Do not widen the task into a full audit.

Read these references only when the project or reported flow needs them:

- Mobile WebView, share, scan, payment, upload, print, or other callback-based SDK flow: [references/sdk-mobile-risks.md](references/sdk-mobile-risks.md).
- 3D, canvas, video, large images, preload manifests, or resource-performance claims: [references/asset-performance-risks.md](references/asset-performance-risks.md).
- Reusable findings format: [references/report-template.md](references/report-template.md).

## Boundaries

- Short review wording such as “检查一下” means inspect and report when the current repository is already known to be Vue and the surrounding request is release-related. It does not authorize edits.
- A review does not authorize build, deploy, upload, browser interaction, real API calls, or external mutations. Inspect scripts and Vite plugins before choosing validation commands.
- Run a build or browser flow only when the user explicitly requests or approves it. If runtime behavior is required for confirmation, report the gap and the shortest useful validation path.
- Never print secret values from `.env*`, deploy configuration, tokens, credentials, signing keys, or private URLs. Report the key name, location, exposure path, and remediation without reproducing the value.
- Scanner output is navigation evidence, not a finding. Trace the affected user flow before assigning severity.
- Stop when the selected mode's completion condition is satisfied. Do not continue into unrelated cleanup, refactoring, UI polish, or broader testing.

## Adaptive Workflow

1. **Confirm applicability and safety.** Verify Vue from `package.json` or source before using the workflow. Read package scripts, lockfile/package-manager metadata, and Vite plugins before running commands. If the project is not Vue, stop using this skill.
2. **Define completion.** State the selected mode, in-scope flows, permitted verification, and what evidence would be sufficient. For a full audit, rank the release surface before reading leaf components. For a targeted diagnosis, start from the reported symptom.
3. **Trace the smallest complete path.** Follow entry/configuration → route or action → request/SDK → state → visible UI → failure and retry. Inspect adjacent code only when it participates in that path.
4. **Use scanners selectively.** Resolve bundled paths relative to this `SKILL.md`. Prefer JSON output and restrict large repositories with `--include-path`, `--changed-only`, or `--rule`. Review the source around every returned lead.
5. **Verify proportionally.** Use the repository's actual package manager and scripts. Prefer type-check, lint, targeted unit tests, and minimal command-line checks. Do not assume `pnpm` or a script name without inspecting the repo.
6. **Report calibrated results.** Separate impact severity from evidence state, list what was run, and state runtime or business gaps explicitly.

## Evidence Model

Assign impact and evidence independently:

- `P0`: release is unsafe, the main path is broken, or data can be lost/corrupted.
- `P1`: an important auth, payment, submit, share, upload, or core business flow can fail or mislead.
- `P2`: a secondary flow, edge case, or visible release defect is wrong but does not block the main path.
- `P3`: low-impact release polish worth fixing when time permits.

Evidence states:

- `Confirmed`: the relevant code path or targeted check proves the behavior.
- `Likely`: static evidence strongly supports the cause, but required runtime behavior was not reproduced.
- `Lead`: a scanner or isolated code shape needs more tracing; do not publish it as a finding.
- `Needs business confirmation`: correctness depends on an API contract, product rule, or deployment assumption not present in the repository.

Do not inflate severity to compensate for weak evidence. Do not downgrade a confirmed high-impact issue because it was found statically.

## Bundled Scanners

Use Python 3 in shell examples:

```bash
skill_dir="<absolute directory containing this SKILL.md>"
python3 "$skill_dir/scripts/scan_vue_state_risks.py" \
  --root . --format json --include-path 'src/**'
```

```bash
skill_dir="<absolute directory containing this SKILL.md>"
python3 "$skill_dir/scripts/scan_terms.py" \
  --root . --rules "$skill_dir/references/term-rules.json" \
  --format json --include-path 'src/**'
```

- `scan_vue_state_risks.py` finds stale-state and async-flow code shapes. Exit `1` means review leads were found, not that execution failed.
- `scan_terms.py` finds configured wording patterns. Add `term-style-rules.json` only after confirming those conventions apply to the project.
- Both scanners support `--include-path`, `--exclude-path`, `--changed-only`, `--format text|json`, and `--max-results`. The state scanner also supports repeated `--rule` filters.

## Completion

- **Full audit**: report confirmed/likely release findings, verification performed, and meaningful untested gaps.
- **Targeted diagnosis**: identify the root cause or state exactly which missing evidence prevents confirmation; do not pad the answer with unrelated findings.
- **Copy audit**: report only user-visible or release-metadata issues after manually confirming scanner hits.
- **Implementation**: complete the scoped edit and targeted validation, then stop.

Use [references/report-template.md](references/report-template.md) when multiple findings need a consistent report. Omit empty severity sections.
