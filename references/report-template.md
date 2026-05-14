# Vue Launch Audit Report Template

Use these templates to keep release review and fix reports short, practical, and comparable across projects.

## Review Report

Start with the highest-risk findings. Omit empty severity sections unless the user explicitly asked for a full matrix.

```markdown
## Findings

### P0

- [Title]
  - Location: [file or flow]
  - Impact: [what users or the release can lose]
  - Cause: [confirmed root cause]
  - Reproduce: [short path or condition]
  - Recommendation: [direct fix]

### P1

- [Title]
  - Location:
  - Impact:
  - Cause:
  - Reproduce:
  - Recommendation:

### P2

- [Title]
  - Location:
  - Impact:
  - Cause:
  - Reproduce:
  - Recommendation:

### P3

- [Title]
  - Location:
  - Impact:
  - Cause:
  - Reproduce:
  - Recommendation:

## Verification

- Ran: [commands or manual flow]
- Passed: [what is confirmed]
- Not verified: [only meaningful gaps]

## Residual Risk

- [Remaining launch risk, if any]
```

If no real launch issue is found, say that directly before listing verification and gaps.

## Fix Report

Use this when the user asked for fixes or when review findings were fixed in the same turn.

```markdown
## Fixed

- [User-facing issue fixed]
- [User-facing issue fixed]

## Verified

- [Command or flow] passed.
- [Command or flow] passed.

## Still Watch

- [Residual risk or untested environment, only if meaningful]
```

## Reporting Rules

- Lead with user impact, not implementation detail.
- Do not list speculative cleanup as launch risk.
- Do not hide failed checks. If a failed check is in scope, investigate before reporting.
- Keep file references precise enough to act on, but do not paste long code excerpts.
- Separate confirmed issues from things that only need manual business confirmation.
