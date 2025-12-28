# Context

Add markdown files with project context to help agents understand your codebase.

## `mandatory/` - Auto-loaded

Files here are automatically loaded when creating or loading tasks.
Use for: conventions, architecture decisions, critical constraints.

## `search/` - On-demand

Files here are searched dynamically by the agent based on task requirements.
Use for: feature documentation (auth, payments, etc), implementation guides, API references.

