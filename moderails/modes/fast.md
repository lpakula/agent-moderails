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

## SNAPSHOT WORKFLOW (OPTIONAL)

If the user types `--snapshot`, preserve your work in task history for future context searches. Create a task entry and structured commit in one go:

1. Create task with `in-progress` status, skip file and context:
```sh
   moderails task create --name "<descriptive-task-name>" --type <feature|fix|refactor|chore> --status in-progress --no-file --no-context
```
   Note the returned task ID. The `--no-file` flag skips task file creation and `--no-context` suppresses context output (no plan file needed for snapshots).
2. Review changes for this task:
```bash
git status
```
   Identify which files were changed as part of this task.
3. Stage and commit all changes:
```sh
git add <file1> <file2> <file3>...
git commit -m "<type>: <task-name> - <brief description>"
```
   Use conventional commit format matching the task type.

4. Complete the task:
```sh
moderails task complete --task <task-id> --summary "<brief summary>"
```
This captures the git hash and exports to history.

**Result**: Structured commit with searchable task history preserved for future context, without leaving Fast mode or creating plan files.

## PERMITTED

- Read and write code directly
- Search context as needed
- Iterate quickly with the user
- Ask questions and discuss approaches
- Use all available context
- Execute snapshot workflow when requested

## FORBIDDEN

- Don't create tasks or switch to other modes (except for snapshot workflow)
- Don't follow formal protocol workflows
- Don't spend time on extensive planning (unless user requests it)

**YOU MUST FOLLOW THE WORKFLOW**

