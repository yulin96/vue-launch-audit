# Vue Launch Review Checklist

Use this checklist when the project is close to release and you need extra coverage beyond the main skill instructions.

## 1. Entry and Routing

- Check `main.ts`, `App.vue`, route setup, and global plugins.
- Confirm the default route, 404 route, redirects, and route guards do not trap users or skip required state.
- Verify query parameters and hash routing survive refresh, deep links, and back navigation.
- Treat required entry parameters as release-critical. Check what happens on a clean open, a shared link, refresh, and a missing or malformed query value.
- Confirm fallback route names actually exist and do not redirect users into a blank page.

## 2. Critical User Flows

- Open each important page from a cold start.
- Walk the shortest successful path and at least one failure path.
- Check loading, empty, error, retry, and success states.
- Verify forms cannot be submitted twice and buttons do not stay disabled forever after failure.
- Check whether the UI waits for backend confirmation before showing success, jumping pages, updating counts, or clearing user input.

## 3. Requests and Data

- Check request wrappers, interceptors, cancel handling, and error reporting.
- Compare request payload shape with how the response is read.
- Look for hidden production failures: missing base URL, wrong upload host, missing auth token, or business status ignored as success.
- Confirm failure messaging matches the actual failure instead of generic or misleading text.
- Search for empty `catch` blocks and swallowed errors in user actions. A silent failure is usually a launch issue, not a cleanup task.
- Verify request locking or duplicate-submit helpers release correctly on both success and failure.

## 4. State and Reactivity

- Look for values that are read before they exist.
- Check watchers, lifecycle hooks, and async branches for race conditions or duplicate side effects.
- Confirm state resets correctly when users leave and re-enter the page.
- Check whether cached state can leak across accounts, sessions, or routes.
- Check whether callback-updated state is the same state the visible UI reads. First-try-fails, second-try-works bugs often live here.

## 5. Mobile H5 Risks

- Check iOS-safe behavior for focus, scrolling, fixed positioning, and viewport-dependent calculations.
- Review WebView-specific logic such as WeChat, DingTalk, or embedded browser detection.
- Verify share metadata, analytics, and monitoring hooks do not crash when SDK globals are absent.
- Confirm rem scaling or viewport helpers do not break page structure on wider preview screens.
- Split iOS and Android behavior early when deep links, downloads, share, or external app jumps behave differently.

## 6. Release Readiness

- Run available static checks such as type-check, lint, and build.
- Inspect build scripts before running them so local verification does not accidentally upload or deploy.
- Inspect `.env*`, deploy scripts, and Vite config for environment drift.
- Check whether prod-only flags disable functionality unexpectedly.
- Review console errors, reporting hooks, and monitoring setup for obvious silent failures.
- Treat a green build as necessary but not sufficient. Environment warnings, missing analytics IDs, and runtime config gaps still need to be called out.

## 7. Copy and Naming

- Check visible page text, button text, titles, alt text, metadata, and share copy.
- Watch for brand/product name mistakes, mixed casing, repeated punctuation, and broken links.
- Run the bundled term scanner and then manually verify the hits.
- Pay special attention to business-critical names where one wrong letter changes meaning.
- Keep display labels aligned with the form or source-of-truth page they summarize.
