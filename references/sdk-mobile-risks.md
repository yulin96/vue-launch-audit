# Mobile WebView and SDK Risks

Read this reference only for mobile WebView behavior or callback-based integrations such as share, scan, payment, upload, print, maps, analytics, and external-app jumps.

## Initialization and Availability

- Trace environment detection, SDK script injection, configuration, readiness, permission, invocation, callbacks, and user-visible result as one flow.
- Check behavior when the SDK global or dynamic script is missing. Optional chaining must not turn absence into silent success.
- Verify configuration failures are observable and retryable. Module-level readiness or lock state must not permanently retain a failed attempt.
- Separate iOS and Android behavior when deep links, downloads, focus, scrolling, fixed positioning, safe areas, or external apps differ.

## Action Closure

- For every lock/loading flag, check configuration failure, permission denial, cancellation, timeout, thrown error, callback failure, and callback success.
- For handwritten Promise wrappers, confirm every business branch deliberately resolves, rejects, returns, or resets state.
- Ensure redirects, polling, success messages, and disabled buttons depend on actual completion rather than invocation alone.
- Confirm toast/modal argument shapes against the installed library and the visible text it renders.

## Runtime Boundary

Static review cannot prove device WebViews, WeChat/JSSDK behavior, permission prompts, uploads, payments, or physical printing. Report static evidence separately and request only the shortest device/browser flow that would confirm the remaining behavior.
