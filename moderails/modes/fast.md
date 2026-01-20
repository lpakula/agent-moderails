# FAST MODE

**Active Mode**: FAST  
**Output Format**: Start with `[MODE: FAST]`

{% if mandatory_context %}
---

{{ mandatory_context }}

---
{% endif %}

## AVAILABLE CONTEXT

### MEMORIES
{% if memories %}
{% for m in memories %}- {{ m }}
{% endfor %}
{% else %}
No memories available.
{% endif %}

### FILES (from past tasks)
{% if files_tree %}
{{ files_tree }}
{% else %}
No files in history yet.
{% endif %}

### LOAD MORE
```sh
moderails context load --memory <name>
```

---

## PURPOSE

Access ModeRails' context memory system without following the structured protocol workflow.

Best for small tasks, bug fixes, and quick iterations where you want context-aware development (mandatory context, searchable context, task history) but don't need mode switching and formal task tracking.

## WORKFLOW

1. **Work directly** - make changes, iterate, discuss with the user

2. **That's it!** No task creation, no mode switching, no formal workflow

## SNAPSHOT WORKFLOW (OPTIONAL)

If the user types `--snapshot`, preserve your work in task history for future context searches. Create a task entry and structured commit in one go:

1. Create task with `in-progress` status, skip file creation:
```sh
moderails task create --name "<descriptive-task-name>" --type <feature|fix|refactor|chore> --status in-progress --no-file
```
   Note the returned task ID. The `--no-file` flag skips task file creation (no plan file needed for snapshots).

2. Review and stage changes for this task:
```bash
git status
git add <file1> <file2> <file3>...
```
   Stage only the files that are part of this task. Do NOT use `git add -A`.

3. Complete the task (exports staged files to history.jsonl and auto-stages it):
```sh
moderails task complete --task <task-id> --summary "<brief summary>"
```

4. Commit:
```sh
git commit -m "<type>: <task-name> - <brief description>"
```
   Use conventional commit format matching the task type.

5. Update task with git hash:
```sh
moderails task update --task <task-id> --git-hash $(git rev-parse HEAD)
```

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

---
**YOU MUST FOLLOW THE WORKFLOW**
