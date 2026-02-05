# Context Discovery

Protocol uses the following types of context to help the agent understand your project:

## Skills

[Agent Skills](https://agentskills.io) are folders containing instructions and resources that agents can discover and use. Cursor and Claude support skills natively.

**How ModeRails uses skills:**  
The agent already knows how to use skills (read the SKILL.md when relevant). ModeRails ensures skill names stay visible when starting a session and are refreshed on `--rerail`, so they're not forgotten during extended conversations.


## Mandatory Context

Files in `_moderails/context/mandatory/` contain essential project knowledge.

**Use this for:**
- Project-specific conventions
- Architecture guidelines
- Critical constraints
- Coding standards

**When it's loaded:**  
Automatically injected when entering `#research` or `#fast` modes. No manual loading required.


## Memories Context

Files in `_moderails/context/memories/` are named context documents that the agent can discover and load.

**Use this for:**
- Feature documentation (auth.md, payments.md, etc.)
- API references
- Implementation patterns
- Technical guides

**How it works:**
When entering `#research` or `#fast` mode, the agent automatically sees:
- All available memory names
- The project files tree

The agent can load specific memories with `moderails context load --memory auth --memory payments`

This is deterministic - the agent knows exactly what's available and loads full documents by name, rather than searching with random queries that might miss.

## Epic Context

Epics group related tasks together, providing continuity across multiple tasks working toward the same goal. Epics are stored locally in your database — they're for your personal organization only.

**What's included:**
- Completed tasks with summaries (chronological order)
- Files changed across all epic tasks
- Optimised git diffs from all epic tasks
- Epic skills (domain-specific context)

**When it's loaded:**  
Automatically loaded when working on a task that belongs to an epic. This gives the agent full context of the feature being built, so each new task builds on previous work without repeating questions or decisions.

### Epic Skills

Attach skills to epics to provide domain-specific context for all tasks within that epic.

When you work on a task within an epic, attached skills are automatically surfaced so the agent knows which domain knowledge is relevant. This is especially useful for complex features that span multiple skills (e.g., a checkout flow that needs both `payments` and `auth` context).


## Task History

Metadata from all completed tasks is preserved in `history.jsonl`, creating a searchable knowledge base that the agent can use during research.

**When it's loaded:**  
The agent searches this history on-demand during `#research` mode when it needs context about past work, similar features, or specific file changes.


