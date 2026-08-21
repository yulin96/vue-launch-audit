# Targeted Vue Flow Diagnosis

Use this mode when the user reports a concrete symptom. Diagnose that flow instead of performing a repository-wide audit.

## Trace Shape

1. Start at the visible symptom and identify the state or DOM output that produces it.
2. Trace backward to the latest request, route input, store/composable, callback, or SDK event that can write that value.
3. Trace forward through success, failure, cancellation, retry, refresh, and repeated-entry behavior.
4. Compare the state written by callbacks with the state actually read by the visible component.
5. Establish the smallest root cause supported by the code. Inspect adjacent modules only when they participate in the same path.

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

## Completion

Finish when one of these is true:

- The root cause and affected behavior are supported by a complete code path or targeted check.
- The remaining uncertainty depends on runtime, credentials, remote APIs, SDK availability, or business rules; name the missing evidence and the shortest validation that would resolve it.

Do not append unrelated repository findings to a targeted diagnosis.
