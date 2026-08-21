# User-Visible Copy Audit

Use this mode for rendered labels, CTA text, validation/error messages, titles, metadata, share copy, links, dates, numbers, and product or brand spelling.

## Scope First

- Identify likely user-visible sources such as Vue templates, locale/message files, page metadata, public HTML, share configuration, and toast/modal calls.
- Restrict scanner paths to those sources when practical. Do not treat comments, tests, internal identifiers, dependency names, or documentation as visible copy without tracing a render path.
- Never scan or print `.env*` values as copy.

## Rules

- Use `term-rules.json` for cross-project, high-confidence mistakes.
- Add `term-style-rules.json` only when the project explicitly follows those terminology and typography conventions.
- Pass project-specific brand pairs with repeated `--pair Correct=Wrong`; do not promote a one-project convention into the baseline rules.
- Scanner results remain leads until their rendered or release-metadata path is confirmed.

## Completion

Report the visible text, source location, intended correction, and why it is user-facing. Exclude intentional variants and non-rendered hits. If brand or product spelling has no repository source of truth, mark it `Needs business confirmation`.
