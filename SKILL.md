---
name: vue-launch-audit
description: Review Vue applications before release, especially Vue projects built with Vite, mobile H5, campaign, or lightweight app projects. Use when Codex needs to inspect Vue program logic, risky user flows, route/request/state interactions, release blockers, user-facing copy, and brand or product spelling mistakes. Also use for Chinese requests like "检查一下", "上线前看一下", "发布前检查", "看看这个 H5/Vue 项目有没有风险", or "帮我扫一下路由/请求/状态/文案问题". Do not use this skill for non-Vue Vite projects.
---

# Vue Launch Audit

Audit launch-bound Vue projects for user-impacting problems, not style trivia. Start with the flows that can break the release, then widen to hidden risks and wording errors.

## Completion Standard

Before inspecting files, define what "done" means for the current request. Use that standard to decide when to stop.

- If the user says only "检查一下", "看一下", or similar short Chinese review wording, treat it as an audit request. Inspect and report first; do not edit code unless the user asks for fixes.
- For a review request, finish with confirmed release risks, verification results, and any untested gaps. Do not report speculative style cleanup as a launch issue.
- If the user asks to fix an issue, first finish the audit-level diagnosis: root cause, affected flow, and recommended change. Only edit code if the user explicitly asks for implementation after that.
- If something fails during verification, investigate far enough to identify the likely root cause and user impact. Do not silently convert a review into a patching session.
- Keep the final response direct and practical: what was checked, what was confirmed, and what still needs attention.

## Audit Workflow

1. Check the project shape and build safety.
   Confirm the project uses Vue, then read `package.json`, `vite.config.*`, scripts, environment files, routing, entry files, main pages, request utilities, and state. Inspect build scripts for deploy, upload, analytics, or other production side effects before choosing verification commands. Do not run a build unless the user explicitly asks for it.
2. Define the release surface.
   Identify the pages, routes, query parameters, persisted keys, SDKs, API calls, runtime configuration, heavy assets, and rendering engines that can affect the live build.
3. Map the critical flows.
   Identify the paths a real user must complete: page entry, login/auth, route jumps, form submit, payment/upload/share, confirmation, and error recovery.
4. Trace requests, routes, and state together.
   Follow the actual data path from page entry to request to UI result. Start from the real startup chain (`index.html`/`main.ts`/init config/router guards) before diving into leaf components. Look for missing query params, wrong response-shape assumptions, async races, stale state, duplicate submissions, incorrect redirects, and UI success shown before backend confirmation.
5. Scan recent Codex-prone bug patterns.
   Run `scripts/scan_vue_state_risks.py` when the audit includes state, async flow, page data, storage, SDK actions, dynamic scripts, toasts, or user-visible stale information. Treat its output as leads that need manual confirmation. Prioritize cases where new API or route data is merged into an existing object, because stale fields from the previous user/page/item can stay visible. Prefer replacing the whole display data object when the response represents a new entity or page state; only keep field-level updates when the UI is intentionally editing one field.
6. Review failure paths.
   Empty `catch` blocks, generic toasts, ignored business status codes, promise branches that never `return`/`resolve`/`reject`, locks that are not released, disabled buttons that never recover, and fallbacks to missing routes are launch risks when users cannot understand or retry a failure.
7. Check release-specific risks.
   Focus on environment-dependent behavior, tracking/reporting hooks, mobile webview assumptions, production-only switches, missing guards, build-time failures, fragile integrations, frontend-exposed secrets, deploy/upload scripts, and third-party globals or dynamically loaded scripts that may be absent. For asset-heavy or 3D pages, inspect dependencies, model/image sizes, browser targets, preload paths, and first-load/rendering cost before giving performance or hardware conclusions.
8. Scan copy and terms.
   Run `scripts/scan_terms.py` with `references/term-rules.json`, then manually inspect visible copy for product names, CTA text, numbers, dates, links, and obvious misspellings.
9. Verify before reporting.
   Run the strongest realistic checks available for the repo without building by default. Prefer `pnpm type-check`, `pnpm lint`, and targeted code or script checks when feasible, but check the repo's actual scripts and tool versions first because ESLint 9 and custom config files may need different commands. Only run a build or browser check when the user explicitly approves it. When a risk depends on real page behavior, report that browser verification is recommended and wait for approval before opening the app.
10. Report findings by `P0`, `P1`, `P2`, and `P3`.
   Lead with concrete problems, file paths, impact, and how to reproduce. Keep summaries short. Call out what was verified versus what remains a risk hypothesis.

## What to Prioritize

- Broken or misleading user flows over code style.
- Logic that behaves differently on first load, refresh, back navigation, or slow network.
- Places where request, route, and state interact.
- Entry parameters, share links, hash routes, and persisted storage keys that decide first-load behavior.
- `App.vue` route shells, `router-view` keys, `Transition`, and `keep-alive` identity. If the URL changes but the page looks stuck, check component reuse and cache identity before removing animation or cache behavior the app needs.
- State replacement mistakes where a new API result, selected item, or route entry is merged into old object data and can leave previous fields behind.
- Callback-updated state that is not the same state read by the visible UI.
- Watchers, route guards, or polling paths that can retrigger requests, redirects, timers, or refresh logic without a one-shot guard.
- Silent failures, misleading success states, request locks that stay locked, or failure handling that blocks retry.
- Runtime identity and session partitioning, especially URL `id`/`appid` values, store persistence keys, and clean-session versus old-localStorage behavior.
- Layout/bootstrap problems that come from global rem, viewport, preview-mode, or container-size gates. Check the central sizing setup before treating the visible component as the root cause.
- Animation or focus utilities that run but appear invisible. Confirm the exact DOM node being selected is the visible shell, not an inner transparent wrapper.
- Preload/resource identity mismatches, especially raw HTML-injected URLs versus runtime asset URLs. Encoded characters such as `%40` and `@` can defeat browser reuse even when the file is the same.
- Temporary local-test switches that bypass startup work. If 3D, SDK, or loading code is skipped, verify the overlay/loading state is derived from the same switch so the test UI can actually appear.
- User-facing text that can ship to production with the wrong name or spelling.
- User-facing messages produced through toast/modal libraries. Passing the wrong shape can render raw objects such as `[object Object]`, so verify visible output, not only the function call.
- Request locks and SDK locks that are set before config, permission, or callback success is guaranteed. Check cancel, timeout, config failure, and thrown-error branches, not only the SDK `complete` callback.
- Hand-written `new Promise(...)` wrappers around SDKs, timers, uploads, or print/share flows. Every branch should deliberately finish or reset state; missing closure often looks like a stuck button or no-op.
- Production-only risk: missing env values, analytics hooks, third-party SDK setup, upload domains, share metadata, and 404/redirect behavior.
- High-confidence root causes over broad refactors. Recommend the smallest change that would remove the confirmed risk, but do not implement it during a pure audit.

## Vue-Specific Hotspots

- `src/router`, route guards, route params, redirects, and fallback routes.
- `src/pages` and `src/components` for actual user journeys and conditional rendering.
- `src/stores`, composables, and watchers for stale or duplicated state transitions.
- `src/utils/request*` and submit hooks for retries, duplicate actions, failure messages, and data shape mismatches.
- `src/plugins` and startup code for SDK bootstrapping, rem adaptation, analytics, and global side effects.
- `src/App.vue` route shells, `router-view` wrappers, `Transition`, `keep-alive`, global click/haptic handlers, and startup/loading overlays.
- `index.html`, public runtime config, and dynamically injected scripts for globals that source code assumes are present.
- `.env*`, `vite.config.*`, and deploy scripts for release-only drift.
- `config*`, `constants*`, generated route maps, and runtime config files that can disagree with source routes or deployed URLs.
- Direct `localStorage` / `sessionStorage` reads and persisted-store setup, especially when the app can be entered by different activity IDs, tenants, languages, inside/outside modes, or share links.
- Heavy runtime assets such as `.glb`, `.gltf`, high-density images, video, sprite sheets, and generated preload manifests.

Read `references/review-checklist.md` when you need a broader launch checklist.

## Browser Verification

Use browser verification only after the user approves it. Code reading and lightweight checks are the default.

- Do not open the app during the initial audit. If browser confirmation would materially change the confidence of a finding, mention it in the report and ask for approval.
- Recommend browser verification when the audit depends on a real flow: route entry, form submit, modal/popup, scan/share/payment/upload, mobile viewport behavior, or a suspected stale-state display.
- After approval, walk the shortest path that proves or disproves the risk. Avoid turning browser verification into unrelated UI polish review.
- Record what was reproduced, what was not reproducible, and any environment limits such as missing credentials, unavailable API, or SDK-only behavior.
- Do not edit UI or code as part of this skill unless the user explicitly changes the task from checking to implementation.

## Term Scan

Use the bundled scanner when wording or brand consistency matters.

PowerShell example:

```powershell
python "$env:CODEX_HOME/skills/vue-launch-audit/scripts/scan_terms.py" `
  --root . `
  --rules "$env:CODEX_HOME/skills/vue-launch-audit/references/term-rules.json"
```

Bash example:

```bash
python "$CODEX_HOME/skills/vue-launch-audit/scripts/scan_terms.py" \
  --root . \
  --rules "$CODEX_HOME/skills/vue-launch-audit/references/term-rules.json"
```

- Prefer passing project-specific brand or product names with `--pair Correct=Wrong`. Add them to `references/term-rules.json` only when they are useful across many Vue release reviews.
- The rules file supports fixed `wrong` terms and regex `patterns` for high-confidence Chinese wording or punctuation issues.
- Treat scanner output as leads, not final truth. Confirm whether each hit is user-facing, test-only, or intentional.
- Re-run the scan after making wording fixes.

## State Risk Scan

Use the bundled state scanner when the release risk may involve stale page data, async handoff, duplicated requests, or watcher-driven navigation.

Example:

```powershell
python "$env:CODEX_HOME/skills/vue-launch-audit/scripts/scan_vue_state_risks.py" --root .
```

```bash
python "$CODEX_HOME/skills/vue-launch-audit/scripts/scan_vue_state_risks.py" --root .
```

- Confirm every hit manually. The scanner finds code shapes that often hide launch bugs; it does not prove a bug by itself.
- The scanner exits with code `1` when it finds review leads. Treat that as "needs inspection", not as a command failure.
- Check `[HIGH]` hits first. They are more likely to affect user-visible state or failure handling. `[LEAD]` hits are context clues that may be harmless.
- Start with hits in pages, stores, composables, request hooks, and route guards.
- Pay special attention to `Object.assign(...)`, spread merges such as `{ ...oldData, ...newData }`, and `ref.value.xxx = ...` updates after fetching a new entity. These often mean old fields can remain visible when the new response omits them.
- When a response represents a new page/entity/status, recommend whole-object replacement. Field-level mutation is only appropriate for deliberate partial edits, counters, local form typing, or known incremental updates.
- Empty `catch` blocks, swallowed errors, and non-awaited async calls should be checked against the real user flow before being reported as confirmed launch issues.
- `PROMISE_BRANCH_CLOSURE`, `LOCK_SET_TRUE`, `TOAST_OBJECT_PAYLOAD`, `DYNAMIC_SCRIPT_LOAD`, and `DIRECT_STORAGE_ACCESS` are common false-positive shapes. Use them to choose what to read next; report them only when the affected user flow can really get stuck, mislead users, or leak state.

## Output Shape

Use `references/report-template.md` when a reusable review report format would help.

When the user asks for a review, structure the answer like this:

1. Findings first, grouped under `P0`, `P1`, `P2`, and `P3` headings in that order.
2. Use this severity guide:
   - `P0`: Release blocker. The main path is broken, data can be lost or corrupted, or the live release is unsafe.
   - `P1`: High risk. Important user paths, payment, auth, submit, share, or key business wording can fail or mislead users.
   - `P2`: Medium risk. Secondary flows, edge cases, or visible wording issues are wrong but do not fully block launch.
   - `P3`: Low risk. Minor polish or low-frequency issues worth reporting if time allows.
3. Each finding should include the affected file, the problem, why it matters, and what behavior can go wrong.
4. State what you ran to verify the result.
5. Mention residual risks only after the findings.

If no real issues are found, say so directly and list any testing gaps that still remain.

When the user asks for implementation instead of a pure review, pause after the audit diagnosis and confirm the intended change scope before editing unless the request was already explicit.
