# Context Discovery

Protocol uses the following types of context to help the agent understand your project:

## Mandatory Context

Files in `.moderails/context/mandatory/` contain essential project knowledge.

**Use this for:**
- Project-specific conventions
- Architecture guidelines
- Critical constraints
- Coding standards

**When it's loaded:**  
Automatically loaded when you start working on any task (when creating or loading tasks).


## Memories Context

Files in `.moderails/context/memories/` are named context documents that the agent can discover and load.

**Use this for:**
- Feature documentation (auth.md, payments.md, etc.)
- API references
- Implementation patterns
- Technical guides

**How it works:**
1. The agent runs `moderails context list` to see available memories
2. The agent loads specific memories with `moderails context load --memory auth --memory payments`

Flags can be combined: `moderails context load --mandatory --memory auth --file src/auth.ts`

This is deterministic - the agent knows exactly what's available and loads full documents by name, rather than searching with random queries that might miss.

## Epic Context

Epics group related tasks together, providing continuity across multiple tasks working toward the same goal. Epics are stored locally in your database — they're for your personal organization only.

**What's included:**
- Completed tasks with summaries (chronological order)
- Files changed across all epic tasks
- Optimised git diffs from all epic taks

**When it's loaded:**  
Automatically loaded when working on a task that belongs to an epic. This gives the agent full context of the feature being built, so each new task builds on previous work without repeating questions or decisions.


## Task History

Metadata from all completed tasks is preserved in `history.jsonl`, creating a searchable knowledge base that the agent can use during research.

**When it's loaded:**  
The agent searches this history on-demand during `#research` mode when it needs context about past work, similar features, or specific file changes.


