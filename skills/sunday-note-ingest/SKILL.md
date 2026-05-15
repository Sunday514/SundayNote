---
name: sunday-note-ingest
description: Ingest external materials and raw sources into Sunday Note as traceable knowledge candidates. Use when the user asks to summarize, absorb, organize, or process articles, papers, links, screenshots, command output, collected sources, inbox notes, or other raw materials for possible Wiki entry.
---

# Sunday Note Ingest

## Workflow

Read `AGENTS.md` first, then read `.sunday-note-agent/config/sunday-note-vault.yaml` to resolve Raw, Routine, Wiki, Journal, and Schema paths. Do not assume directory names. Read framework files from the configured Schema framework path and existing canonical Wiki pages only when they are needed to place the material.

Produce:

- Source: title, link, path, date, or origin.
- Summary.
- Facts.
- Inferences.
- Open questions.
- Wiki-entry judgment.
- Suggested canonical page.
- Link, index, or maintenance-log updates.

## Rules

- Preserve source identity and distinguish facts from interpretation.
- Prefer updating an existing canonical page over creating a new page.
- Treat compile as the confirmed follow-up to ingest: after user confirmation, suggest how to merge candidates into canonical Wiki.
- Do not write to Wiki, Routine, Schema, or Journal paths before user confirmation.
- Do not ingest Journal content unless the user explicitly asks.
