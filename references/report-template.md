# Vue Launch Audit Report

Use this format for a full audit or when multiple findings need a consistent report. A full audit always shows P0 and P1 so reports remain comparable; write `None.` when either section has no findings. Include P2 or P3 only when findings exist. Do not force the full format onto a targeted diagnosis.

```markdown
## Release Assessment

- Recommendation: [Block release | Fix before release | Releasable with residual risk | Insufficient evidence]
- P0: [count]
- P1: [count]
- Unverified: [count of material gaps]

## P0

[None. | findings]

### P0-01 [Short user-impact title] — [Confirmed | Likely | Needs business confirmation]

- Location: [file/flow]
- Impact: [observable release or user consequence]
- Evidence: [specific code path, command, or reproduction]
- Root cause: [smallest supported cause]
- Recommendation: [minimum direct correction]

## P1

[None. | findings]

### P1-01 [Short user-impact title] — [Confirmed | Likely | Needs business confirmation]

- Location: [file/flow]
- Impact: [observable release or user consequence]
- Evidence: [specific code path, command, or reproduction]
- Root cause: [smallest supported cause]
- Recommendation: [minimum direct correction]

## P2

### P2-01 [Short user-impact title] — [evidence state]

- Location:
- Impact:
- Evidence:
- Root cause:
- Recommendation:

## Verification

- Ran: [commands or targeted inspection]
- Confirmed: [what the evidence proves]
- Not verified: [runtime, remote service, device, or business gaps]

## Residual Risk

- [Only meaningful remaining release risk]
```

## Reporting Rules

- Sort findings by P0, P1, P2, then P3 and assign sequential identifiers that remain consistent within the report.
- For a full audit, always show P0 and P1. Omit empty P2 and P3 sections.
- Recommend `Block release` for P0, `Fix before release` for P1, and `Releasable with residual risk` when only P2/P3 or non-blocking gaps remain. Use `Insufficient evidence` when missing evidence prevents a release assessment. These are audit recommendations, not a substitute for the owner's release decision.
- Severity communicates impact; evidence state communicates confidence. Never merge the two.
- Scanner priority communicates investigation order only and must not determine severity.
- `Lead` items belong in working notes, not published findings.
- Lead with user impact and the evidence that supports it.
- Do not call a cause confirmed when runtime or business evidence is still required.
- Do not hide failed checks or imply that type-check/lint proves runtime behavior.
- Keep file references precise and avoid reproducing secrets or long source excerpts.
