# Targeted Vue Flow Diagnosis

Use this mode when the user reports a concrete symptom. Diagnose that flow instead of performing a repository-wide audit.

## Trace Shape

1. Start at the visible symptom and locate its exact control, state, or generated output. A screenshot provides context; the user's named request determines the target. For an export defect, trace the exported image rather than stopping at the preview DOM.
2. Trace backward to the latest request, route input, store/composable, callback, or SDK event that can write that value.
3. Trace forward through success, failure, cancellation, retry, refresh, and repeated-entry behavior.
4. Compare the state written by callbacks with the state actually read by the visible component.
5. Establish the smallest root cause supported by the code. Inspect adjacent modules only when they participate in the same path.

When history describes an earlier fix or failure, re-read the current path and relevant diff before treating it as an open defect. Preserve newer product decisions over superseded implementations.

## Common Leads

These are hypotheses to test, not default conclusions:

- A new API result, selected item, or route entity is merged into an existing object, so omitted fields survive from the previous entity.
- A watcher, guard, or polling callback retriggers initialization, navigation, or requests without a one-shot condition.
- `router-view`, `Transition`, or `keep-alive` uses an identity that reuses the wrong component instance after the URL changes.
- A lock or loading flag is set before configuration/permission succeeds and is not reset on cancellation, timeout, thrown error, or an early return.
- A handwritten Promise wrapper has a business branch that never resolves/rejects or leaves caller state pending.
- A dynamic global is optional-chained, causing a missing dependency to look like a successful no-op.
- A test/debug switch skips startup work but does not release the overlay, opacity gate, timer, or disabled state controlled by that work.

Run the state scanner only when its rules match the symptom. Restrict it to the affected paths or rules when possible. Every hit remains `Lead` until the user-visible flow is traced.

## Follow the Symptom

- Back navigation, repeated messages, callbacks after leaving, or stale async results: read [state-lifecycle-risks.md](state-lifecycle-risks.md).
- Missing images, configuration/resource mismatch, export seams, text placement, or device-only canvas failure: read [asset-performance-risks.md](asset-performance-risks.md).
- A button stays disabled during an entrance animation: inspect transition phases, debounce, `pointer-events`, and disabled state separately. A lock may intentionally protect a leaving view but accidentally block the newly visible view; do not remove all duplicate-submit protection.
- A source edit is correct but the served output remains old: trace generated HTML, plugin caching, development-server lifetime, and the actual requested URL. Use an authorized read-only command-line check when sufficient; a source diff alone does not prove the served artifact changed.

## Completion

Finish when one of these is true:

- The root cause and affected behavior are supported by a complete code path or targeted check.
- The remaining uncertainty depends on runtime, credentials, remote APIs, SDK availability, or business rules; name the missing evidence and the shortest validation that would resolve it.

Do not append unrelated repository findings to a targeted diagnosis.
