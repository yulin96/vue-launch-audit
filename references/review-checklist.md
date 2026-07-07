# Vue Launch Review Checklist

Use this checklist when the project is close to release and you need extra coverage beyond the main skill instructions.

## 1. Entry and Routing

- Check `main.ts`, `App.vue`, route setup, and global plugins.
- Trace the real startup chain before page-level debugging: `index.html`, runtime config, app init, router guards, stores, then pages.
- Confirm the default route, 404 route, redirects, and route guards do not trap users or skip required state.
- Verify query parameters and hash routing survive refresh, deep links, and back navigation.
- Check `App.vue` route-shell behavior: `router-view` keys, `Transition`, `keep-alive`, global click handlers, and page wrappers. URL changes with stale content often come from component/cache identity, not from the target page.
- Treat required entry parameters as release-critical. Check what happens on a clean open, a shared link, refresh, and a missing or malformed query value.
- Compare generated share links with the page logic that decides inside/outside, invited/direct, or campaign branches. Do not review share config and entry-page branch checks separately.
- Confirm fallback route names actually exist and do not redirect users into a blank page.

## 2. Critical User Flows

- Open each important page from a cold start.
- Walk the shortest successful path and at least one failure path.
- Check loading, empty, error, retry, and success states.
- Verify forms cannot be submitted twice and buttons do not stay disabled forever after failure.
- Check whether the UI waits for backend confirmation before showing success, jumping pages, updating counts, or clearing user input.
- For scan, share, upload, print, payment, and SDK-backed actions, check that failure paths release locks and do not make a no-op look successful.
- If an SDK action sets a lock before configuration or permission succeeds, check config failure, permission denial, cancel, timeout, thrown error, and callback branches separately.
- For local-test or debug switches that skip startup work, confirm the same switch also updates loading overlays, opacity gates, timers, and disabled states. Skipping the expensive function alone may still leave the page blocked.

## 3. Requests and Data

- Check request wrappers, interceptors, cancel handling, and error reporting.
- Compare request payload shape with how the response is read.
- Look for hidden production failures: missing base URL, wrong upload host, missing auth token, or business status ignored as success.
- Confirm failure messaging matches the actual failure instead of generic or misleading text.
- Search for empty `catch` blocks and swallowed errors in user actions. A silent failure is usually a launch issue, not a cleanup task.
- Verify request locking or duplicate-submit helpers release correctly on both success and failure.
- Check async wrappers that create their own `Promise`: every business branch should finish with the intended `return`, `resolve`, `reject`, or reset behavior.
- In `new Promise(...)` wrappers around SDKs or callbacks, missing `reject`/`resolve` is not the only issue. Also check whether the caller starts loading, disables a button, starts polling, or redirects before the wrapper has really finished.
- Check toast/modal calls with real rendered copy in mind. Some libraries render raw option objects as `[object Object]` when the message/options argument shape is wrong.

## 4. State and Reactivity

- Look for values that are read before they exist.
- Check watchers, lifecycle hooks, and async branches for race conditions or duplicate side effects.
- Confirm state resets correctly when users leave and re-enter the page.
- Check whether cached state can leak across accounts, sessions, or routes.
- Check persisted-store keys against runtime identity values such as URL `id`, `appID`, tenant, campaign, inside/outside mode, or language. Missing identity can collapse separate sessions into one stored bucket.
- Check direct `localStorage` and `sessionStorage` usage outside the store layer. These keys often bypass the normal tenant/activity/session partitioning.
- Check whether callback-updated state is the same state the visible UI reads. First-try-fails, second-try-works bugs often live here.
- Check whether new API, route, or selected-item data is merged into an old object. If the screen is showing a new entity, whole-object replacement is usually safer than `Object.assign`, spread merge, or multiple field assignments.
- Check whether missing fields in a response can leave previous values visible, especially names, status labels, images, QR codes, prices, counts, and permission flags.
- Check whether async helpers actually resolve before timers, redirects, polling, or UI success states start.
- Check one-shot guards around refresh logic, route guards, and `watchEffect`; repeated reactive triggers can look like page loops or repeated initialization.
- For persisted stores, verify the first-load behavior with old localStorage values and with a clean session.

## 5. Mobile H5 Risks

- Check iOS-safe behavior for focus, scrolling, fixed positioning, and viewport-dependent calculations.
- Review WebView-specific logic such as WeChat, DingTalk, or embedded browser detection.
- Verify share metadata, analytics, and monitoring hooks do not crash when SDK globals are absent.
- Check module-level SDK locks, especially scan/share/payment locks, because config failure before the SDK callback can leave the lock stuck.
- Confirm rem scaling or viewport helpers do not break page structure on wider preview screens.
- For mobile/PC preview gates, do not rely on width alone. Check touch/hover/pointer capability when phone landscape can exceed the desktop-preview threshold.
- For visual effects or canvases tied to a container, verify initialization waits until the container has a real `getBoundingClientRect()` size, and check whether an existing `resize()` / `destroy()` lifecycle already exists before adding a new refresh path.
- When an animation or focus helper appears to do nothing, inspect the selected DOM element and visible wrapper. The animated node may be an inner transparent element while the visible border/background is on its parent.
- Split iOS and Android behavior early when deep links, downloads, share, or external app jumps behave differently.

## 6. Release Readiness

- Run available static checks such as type-check and lint.
- Check the repo's actual lint/type-check command shape before running it. ESLint 9, generated config, external public scripts, or separate node tsconfig files can make old commands misleading.
- Inspect build scripts for upload or deploy side effects, but do not run a build unless the user explicitly asks for it.
- Inspect `.env*`, deploy scripts, and Vite config for environment drift.
- Treat frontend env secrets, signing keys, and deploy plugin credentials as release risks, even when type-check and lint pass.
- Check whether prod-only flags disable functionality unexpectedly.
- Review console errors, reporting hooks, and monitoring setup for obvious silent failures.
- Check public runtime config and dynamically loaded third-party scripts. If source calls optional globals, confirm the user-visible behavior when the script fails to load.
- For dynamically loaded print, share, map, analytics, or SDK scripts, inspect both the injection code and every call site. Optional chaining can hide the failure and make a click look successful while nothing happens.
- For preload/resource manifests, compare the exact runtime URL strings in the deployed HTML with the URLs requested by components and CSS. Encoded forms like `%40` versus `@` can cause duplicate loads.
- For 3D, video, high-DPI image, or large-screen Vue pages, inspect `package.json`, the main render component, `vite.config.*`, browser targets, and top asset sizes before making performance, compatibility, or hardware-readiness conclusions.
- When a build was explicitly requested and passes, do not treat that result as sufficient. Environment warnings, missing analytics IDs, and runtime config gaps still need to be called out.

## 7. Copy and Naming

- Check visible page text, button text, titles, alt text, metadata, and share copy.
- Watch for brand/product name mistakes, mixed casing, repeated punctuation, and broken links.
- Run the bundled term scanner and then manually verify the hits.
- Pay special attention to business-critical names where one wrong letter changes meaning.
- Keep display labels aligned with the form or source-of-truth page they summarize.
