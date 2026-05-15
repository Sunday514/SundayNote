---
name: sunday-note-lint
description: Inspect and maintain Sunday Note knowledge-base health. Use when the user asks to check, clean, merge, deduplicate, repair, organize, or maintain the Markdown Wiki, or during monthly knowledge-base maintenance.
---

# Sunday Note Lint

## Workflow

Read `AGENTS.md`, then read `.sunday-note-agent/config/sunday-note-vault.yaml` to resolve Raw, Routine, Wiki, Journal, and Schema paths. Read relevant framework pages from the configured Schema path and the configured Wiki index if it exists. Inspect only the scope needed for the requested maintenance pass.

Check:

- Duplicate topics.
- Missing canonical pages.
- Orphaned or unindexed Wiki pages.
- Stale pages.
- Missing source, status, or updated fields.
- Weak or missing internal links.
- Raw / Routine / Wiki / Journal / Schema boundary confusion.
- Pages that should be merged, archived, moved, or marked stale.

## Output

Use this table:

| Finding | Severity | Evidence | Suggested action |
|---|---|---|---|

Also include checked scope, index updates, and a suggested maintenance-log entry.

## Rules

- Prefer merge and update over creating new pages.
- Do not rewrite pages without user confirmation.
- Do not lint Journal content unless the user explicitly asks.
- Treat the configured Wiki maintenance log as Wiki maintenance metadata, not ordinary journal content.
