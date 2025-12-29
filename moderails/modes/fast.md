# FAST MODE

**Active Mode**: FAST  
**Output Format**: Start with `[MODE: FAST]`

## PURPOSE

Access ModeRails' context memory system without following the structured protocol workflow.

Best for small tasks, bug fixes, and quick iterations where you want context-aware development (mandatory context, searchable context, task history) but don't need mode switching and formal task tracking.

## WORKFLOW

1. **Load mandatory context first**:
   ```sh
   moderails context load
   ```
   This loads your conventions, architecture decisions, and critical constraints.

2. **Search for additional context when needed**:
   ```sh
   moderails context search --query <topic>
   # OR
   moderails context search --file <path>
   ```
   Use this to find:
   - Similar implementations
   - Existing patterns
   - Past tasks that touched the same files
   - Documentation in searchable context

3. **Work directly** - make changes, iterate, discuss with the user

4. **That's it!** No task creation, no mode switching, no formal workflow

## PERMITTED

- Read and write code directly
- Search context as needed
- Iterate quickly with the user
- Ask questions and discuss approaches
- Use all available context

## FORBIDDEN

- Don't create tasks or switch to other modes
- Don't follow formal protocol workflows
- Don't spend time on extensive planning (unless user requests it)

**YOU MUST FOLLOW THE WORKFLOW**

