# Context Discovery

Protocol uses the following types of context to help the agent understand your project:

## Skills

[Agent Skills](https://agentskills.io) are folders containing instructions and resources that agents can discover and use. Cursor and Claude support skills natively.

**Location:** `skills/<skill-name>/SKILL.md` at project root.

**How ModeRails uses skills:**  
Skill names are listed in `#research` and `#fast` mode output. This serves as reinforcement for long-running sessions — reminding the agent what skills are available without inflating context. The agent already knows how to use skills (read the SKILL.md when relevant).


## Mandatory Context

Files in `.moderails/context/mandatory/` contain essential project knowledge.

**Use this for:**
- Project-specific conventions
- Architecture guidelines
- Critical constraints
- Coding standards

**When it's loaded:**  
Automatically injected when entering `#research` or `#fast` modes. No manual loading required.


## Memories Context

Files in `.moderails/context/memories/` are named context documents that the agent can discover and load.

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
- Optimised git diffs from all epic taks

**When it's loaded:**  
Automatically loaded when working on a task that belongs to an epic. This gives the agent full context of the feature being built, so each new task builds on previous work without repeating questions or decisions.


## Task History

Metadata from all completed tasks is preserved in `history.jsonl`, creating a searchable knowledge base that the agent can use during research.

**When it's loaded:**  
The agent searches this history on-demand during `#research` mode when it needs context about past work, similar features, or specific file changes.


