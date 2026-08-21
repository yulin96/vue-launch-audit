# Vue Launch Audit Report

Use this format when multiple findings need a consistent report. Omit empty severity sections and do not force a full report onto a targeted diagnosis.

```markdown
## Findings

### P1

- [Short user-impact title] — [Confirmed | Likely | Needs business confirmation]
  - Location: [file/flow]
  - Impact: [observable release or user consequence]
  - Evidence: [specific code path, command, or reproduction]
  - Cause: [smallest supported root cause]
  - Recommendation: [minimum direct correction]

## Verification

- Ran: [commands or targeted inspection]
- Confirmed: [what the evidence proves]
- Not verified: [runtime, remote service, device, or business gaps]

## Residual Risk

- [Only meaningful remaining release risk]
```

## Reporting Rules

- Severity communicates impact; evidence state communicates confidence. Never merge the two.
- `Lead` items belong in working notes, not published findings.
- Lead with user impact and the evidence that supports it.
- Do not call a cause confirmed when runtime or business evidence is still required.
- Do not hide failed checks or imply that type-check/lint proves runtime behavior.
- Keep file references precise and avoid reproducing secrets or long source excerpts.
