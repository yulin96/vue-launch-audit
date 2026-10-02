# State, Events, Navigation, and Cleanup

Read only the sections participating in the reported flow. These are inspection hypotheses, not scanner rules or automatic findings.

## Route History and Async Identity

- Compare route parameters, request identity, persisted history, and the identity used when saving. For competing requests, check whether an older response can overwrite the newly selected entity.
- For a custom back/history stack, trace when it is mutated relative to navigation completion. Check thrown errors and resolved navigation failures, including guard cancellation, using the installed router's contract. An awaited navigation is not necessarily successful.
- Check duplicate current entries, return to an existing target, fallback navigation, and overlapping navigation only where supported by the existing history API. Preserve the distinction between history back and explicitly navigating to a target.
- If browser back or swipe is supported, inspect how it synchronizes the custom stack. Do not claim device navigation is verified from router mocks.

## Event Delivery Versus Latest State

- Identify whether the requirement is to handle every message or only changes to the latest value. Watching a ref may suppress repeated equal values or batch updates; it is not an event queue.
- Trace the transport callback through parsing, topic filtering, business callback, and rendered state. Check repeated equal payloads and bursts when each delivery matters.
- Check unsubscribe ownership and callbacks already queued when a component is destroyed. When the SDK cannot unsubscribe, a disposed guard may be necessary; inspect its actual API before adding one.
- Do not flag a watcher used only to display the latest value as a lost-event defect. Confirm that a business action is actually missing.

## Resource Lifetime

- Trace creation and cleanup of media elements, DOM listeners, subscriptions, timers, GSAP contexts, and object URLs. Check repeated entry, unmount, and KeepAlive deactivation only when the component uses those paths.
- If cleanup reads a template ref, check whether that ref still exists at the chosen hook. DOM-dependent cleanup may need `onBeforeUnmount`; `onUnmounted` can still be correct for a resource captured independently of the DOM ref.
- Inspect the actual callback identity and options when removing listeners. Check late async writes after teardown, not just the presence of an unmount hook.
- For dynamically enabled SDKs or print scripts, compare enabled → disabled and disabled → enabled transitions. Inspect stale script nodes, globals, readiness promises, and locks. Do not remove a shared dependency owned by another active consumer.
- For media failure, distinguish listener/resource cleanup from user-gesture and autoplay restrictions. One does not prove the other is solved.

## Focused Evidence

Use existing test infrastructure to exercise the specific risk: repeated deliveries, stale response ordering, guard cancellation, rejected navigation, mount/unmount, or feature disable/re-enable. Prefer a real Vue lifecycle in a small unit test when a mock would preserve a ref that Vue clears. Do not turn an unresolved defect into a green result with an expected-failure marker without explicitly reporting it.

State what mocks prove. Real transport delivery, browser gestures, autoplay, and printer behavior still require their corresponding runtime evidence when authorized.
