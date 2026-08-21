# Full Vue Launch Audit

Read this reference only for a general release-readiness review. Rank the release surface first, then inspect the highest-impact flows. Coverage is risk-based, not a requirement to read every file.

## 1. Establish the Release Surface

- Inspect `package.json`, the lockfile, Vite configuration, `.env*` key names, runtime configuration, entry files, router setup, stores, request utilities, primary pages, and deploy/upload scripts.
- Identify the main user journeys, required entry parameters, persisted identity keys, third-party SDKs, production-only flags, analytics hooks, and large runtime assets.
- Inspect build scripts and plugins for deploy, upload, deletion, or other production side effects before running validation. Do not expose credential values while inspecting configuration.
- Choose the smallest set of flows whose failure would materially affect release. Typical candidates are cold entry, auth, submit, payment/upload/share, confirmation, and retry.

## 2. Trace Critical Flows

- Follow the real startup chain: `index.html` or runtime config → `main.*` → plugins/store initialization → router guards → target page.
- Compare generated links with entry parsing. Check query/hash preservation across cold entry, refresh, deep link, and back navigation.
- Trace each important action through request or SDK invocation, business-status handling, state update, visible result, failure messaging, and retry.
- Confirm the UI does not show success, redirect, clear input, or persist business state before backend confirmation.
- Check loading and submit locks across success, failure, cancellation, timeout, thrown error, and early-return branches.

## 3. State and Identity

- Check whether cached or persisted state is partitioned by the identities that actually define a session: user, tenant, campaign, activity, language, channel, or inside/outside mode.
- Compare clean-session behavior with behavior under old localStorage or persisted-store values.
- Check whether a new entity or response is merged into an old display object, allowing omitted fields to remain visible.
- Check watchers, lifecycle hooks, guards, polling, and callbacks for duplicated requests, redirects, timers, or stale writes.
- Confirm the callback-updated state is the same source read by the visible UI.

## 4. Failure and Production Paths

- Inspect swallowed errors, ignored business codes, missing promise closure, generic or malformed user messages, missing globals, and absent retry paths.
- Check production base URLs, upload domains, public runtime config, generated route maps, third-party script loading, and 404/redirect behavior.
- Treat frontend-exposed secrets as an architectural release risk, but redact their values.
- Inspect analytics and monitoring initialization for crashes or silent loss when configuration is absent.

## 5. Conditional Coverage

- For mobile WebView or SDK-backed actions, read [sdk-mobile-risks.md](sdk-mobile-risks.md).
- For heavy assets, canvas, 3D, or preload behavior, read [asset-performance-risks.md](asset-performance-risks.md).
- For visible copy, read [copy-audit.md](copy-audit.md).

## 6. Verification and Stop Condition

- Infer the package manager from `packageManager` and lockfiles, then use only scripts actually defined by the repository.
- Prefer type-check, lint, targeted unit tests, and minimal script checks. A passing static check does not prove mobile SDKs, remote APIs, layout, or production configuration.
- Do not run build, deploy, browser, E2E, or real API checks without explicit authorization.
- Stop after the ranked release surface has been traced, confirmed/likely findings are documented, and meaningful unverified gaps are named.
