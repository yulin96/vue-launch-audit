---
name: vue-launch-audit
description: Review Vue applications before release, especially Vue projects built with Vite, mobile H5, campaign, or lightweight app projects. Use when Codex needs to inspect Vue program logic, risky user flows, route/request/state interactions, release blockers, user-facing copy, and brand or product spelling mistakes. Do not use this skill for non-Vue Vite projects.
---

# Vue Launch Audit

Audit launch-bound Vue projects for user-impacting problems, not style trivia. Start with the flows that can break the release, then widen to hidden risks and wording errors.

## Completion Standard

Before inspecting files, define what "done" means for the current request. Use that standard to decide when to stop.

- For a review request, finish with confirmed release risks, verification results, and any untested gaps. Do not report speculative style cleanup as a launch issue.
- For a fix request, identify the root cause, patch the highest-risk user-facing problems first, rerun the relevant checks, and only report back once the changed flow is usable or a real blocker remains.
- If something fails during verification, investigate and fix it when the failure is in scope. Do not hand back a known-broken draft.
- Keep the final response direct and practical: what was checked or changed, what passed, and what still needs attention.

## Audit Workflow

1. Check the project shape and build safety.
   Confirm the project uses Vue, then read `package.json`, `vite.config.*`, scripts, environment files, routing, entry files, main pages, request utilities, and state. Inspect build scripts for deploy, upload, analytics, or other production side effects, but do not run a build unless the user explicitly asks for it.
2. Define the release surface.
   Identify the pages, routes, query parameters, SDKs, API calls, and runtime configuration that can affect the live build.
3. Map the critical flows.
   Identify the paths a real user must complete: page entry, login/auth, route jumps, form submit, payment/upload/share, confirmation, and error recovery.
4. Trace requests, routes, and state together.
   Follow the actual data path from page entry to request to UI result. Look for missing query params, wrong response-shape assumptions, async races, stale state, duplicate submissions, incorrect redirects, and UI success shown before backend confirmation.
5. Review failure paths.
   Empty `catch` blocks, generic toasts, ignored business status codes, disabled buttons that never recover, and fallbacks to missing routes are launch risks when users cannot understand or retry a failure.
6. Check release-specific risks.
   Focus on environment-dependent behavior, tracking/reporting hooks, mobile webview assumptions, production-only switches, missing guards, build-time failures, fragile integrations, and third-party globals that may be absent.
7. Scan copy and terms.
   Run `scripts/scan_terms.py` with `references/term-rules.json`, then manually inspect visible copy for product names, CTA text, numbers, dates, links, and obvious misspellings.
8. Verify before reporting.
   Run the strongest realistic checks available for the repo without building by default. Prefer `pnpm type-check`, `pnpm lint`, and targeted runtime checks when feasible. Only run a build when the user explicitly asks for it. If the task includes UI fixes, open the app and walk the important flows.
9. Report findings by `P0`, `P1`, `P2`, and `P3`.
   Lead with concrete problems, file paths, impact, and how to reproduce. Keep summaries short. Call out what was verified versus what remains a risk hypothesis.

## What to Prioritize

- Broken or misleading user flows over code style.
- Logic that behaves differently on first load, refresh, back navigation, or slow network.
- Places where request, route, and state interact.
- Silent failures, misleading success states, or failure handling that blocks retry.
- User-facing text that can ship to production with the wrong name or spelling.
- Production-only risk: missing env values, analytics hooks, third-party SDK setup, upload domains, share metadata, and 404/redirect behavior.
- High-confidence root causes over broad refactors. Prefer a narrow fix that matches the existing project style.

## Vue-Specific Hotspots

- `src/router`, route guards, route params, redirects, and fallback routes.
- `src/pages` and `src/components` for actual user journeys and conditional rendering.
- `src/stores`, composables, and watchers for stale or duplicated state transitions.
- `src/utils/request*` and submit hooks for retries, duplicate actions, failure messages, and data shape mismatches.
- `src/plugins` and startup code for SDK bootstrapping, rem adaptation, analytics, and global side effects.
- `.env*`, `vite.config.*`, and deploy scripts for release-only drift.
- `config*`, `constants*`, generated route maps, and runtime config files that can disagree with source routes or deployed URLs.

Read `references/review-checklist.md` when you need a broader launch checklist.

## Fix Mode

Use fix mode when the user asks to repair issues, implement audit findings, or make a risky flow release-ready.

- Start from the highest-severity user-facing issue, not from easy cleanup.
- Trace the root cause through the actual route, request, state, and UI flow before editing.
- Keep changes narrow and consistent with the project. Do not bundle unrelated refactors into a release fix.
- Preserve existing working behavior unless it directly causes the bug.
- After each fix, rerun the strongest realistic checks for the touched flow. If verification fails and the failure is in scope, keep investigating until the real cause is handled.
- If a blocker depends on missing credentials, unavailable services, or product decisions, report the blocker clearly and include what was already verified.
- Report fixes using `references/report-template.md` when a concise structure would help the user understand what changed.

## Term Scan

Use the bundled scanner when wording or brand consistency matters.

Example:

```bash
python "$CODEX_HOME/skills/vue-launch-audit/scripts/scan_terms.py" \
  --root . \
  --rules "$CODEX_HOME/skills/vue-launch-audit/references/term-rules.json"
```

- Add project-specific terms to `references/term-rules.json` or pass extra pairs with `--pair Correct=Wrong`.
- The rules file supports fixed `wrong` terms and regex `patterns` for high-confidence Chinese wording or punctuation issues.
- Treat scanner output as leads, not final truth. Confirm whether each hit is user-facing, test-only, or intentional.
- Re-run the scan after making wording fixes.

## Output Shape

Use `references/report-template.md` when a reusable review or fix report format would help.

When the user asks for a review, structure the answer like this:

1. Findings first, grouped under `P0`, `P1`, `P2`, and `P3` headings in that order.
2. Use this severity guide:
   - `P0`: Release blocker. The main path is broken, data can be lost or corrupted, or the live release is unsafe.
   - `P1`: High risk. Important user paths, payment, auth, submit, share, or key business wording can fail or mislead users.
   - `P2`: Medium risk. Secondary flows, edge cases, or visible wording issues are wrong but do not fully block launch.
   - `P3`: Low risk. Minor polish or low-frequency issues worth fixing if time allows.
3. Each finding should include the affected file, the problem, why it matters, and what behavior can go wrong.
4. State what you ran to verify the result.
5. Mention residual risks only after the findings.

If no real issues are found, say so directly and list any testing gaps that still remain.

When the user asks for fixes instead of a pure review, keep the same severity thinking but report in this order: what was fixed, what was verified, and what still has residual risk.
