---
name: sunday-note-query
description: Answer questions from existing Sunday Note vault documents with evidence. Use when the user asks about vault rules, Schema/framework docs, Routine records including Daily, Weekly, Monthly, and Project notes, Wiki pages, or Raw evidence already present in the vault; reference Journal only when explicitly requested by the user.
---

# Sunday Note Query

## Workflow

Read `.sunday-note-agent/config/sunday-note-vault.yaml` to resolve Raw, Routine, Wiki, Journal, and Schema paths. For any factual question, use the cheapest vault lookup that can produce reliable evidence; do not run broad searches when a named page, linked page, or already-open file is enough.

Progressive discovery:

1. If the user names a page, file, date, or project, read that target directly.
2. If the target is unclear, check the configured Wiki index or run a narrow `rg` search over the likely layer.
3. Use `scripts/query_search.py` only as a small top-k candidate finder for broad or ambiguous questions; keep its default Wiki/Schema scope unless Routine context is necessary, and do not paste large search output into the answer context.
4. Search Wiki first, then Schema, then Routine when the question needs personal context or chronology. Use Raw only when the user asks for source evidence or existing Wiki/Routine evidence is insufficient.
5. Expand through Obsidian `[[wikilinks]]`, backlinks, and `sources` frontmatter only when direct candidates are incomplete, conflicting, or weakly supported.
6. Stop searching when the answer has enough relevant evidence; usually one to three strong local sources is enough.

Reference Journal only when explicitly requested by the user. Read `README.md` only when entry or background context is needed.

Treat Wiki as the LLM-owned working knowledge layer. After answering, identify whether the answer should update an existing Wiki page, become a new Wiki page, or remain only an answer. Do not write back into Routine or Journal unless the user explicitly requests it.

Answer with:

- Answer.
- Evidence.
- Uncertainty or 待确认.
- Suggested write-back, if the answer is reusable.

## Rules

- Link to key evidence when answering from local files.
- If no relevant vault evidence is found, say so directly before giving any general answer.
- Mark inference and missing context clearly.
- Do not treat unconfirmed inference as fact.
- Do not modify Routine or Journal without explicit user request.
- Write back to Wiki only when the user asks to save, update, or compile the answer; otherwise suggest the target Wiki page and reason.
