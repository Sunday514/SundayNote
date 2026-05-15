---
name: sunday-note-query
description: Answer questions from existing Sunday Note records with evidence. Use when the user asks about vault rules, architecture, project state, historical notes, Routine records, framework docs, or Wiki knowledge already present in the Sunday Note vault.
---

# Sunday Note Query

## Workflow

Read `AGENTS.md` before interpreting vault content. Then read `.sunday-note-agent/config/sunday-note-vault.yaml` to resolve Raw, Routine, Wiki, Journal, and Schema paths. Read the smallest useful set of files: `README.md`, relevant framework pages from the configured Schema path, the configured Wiki index if it exists, and the relevant Routine, Project, or Wiki pages.

Answer with:

- Answer.
- Evidence.
- Uncertainty or 待确认.
- Suggested write-back, if the answer is reusable.

## Rules

- Link to key evidence when answering from local files.
- Mark inference and missing context clearly.
- Do not treat unconfirmed inference as fact.
- Do not modify formal notes without user confirmation.
- Suggest write-back instead of writing directly unless the user explicitly asks to save the result.
