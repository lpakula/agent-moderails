# Context

Add markdown files with project context to help agents understand your codebase.

## `mandatory/` - Auto-loaded

Files here are automatically loaded when creating or loading tasks.
Use for: conventions, architecture decisions, critical constraints.

## `memories/` - On-demand

Named context documents the agent can discover and load.
Use for: feature documentation (auth.md, payments.md), implementation guides, API references.

Agent runs `moderails context list` to see available memories, then loads with `moderails context load --memory <name>`.

