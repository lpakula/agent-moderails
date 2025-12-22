# ARCHIVE MODE

**Active Mode**: ARCHIVE  
**Output Format**: Start with `[MODE: ARCHIVE]`

## PURPOSE
Convert completed epic into a reusable context file, then delete the epic.

## WORKFLOW

1. Verify all tasks in the epic are completed:
```bash
moderails status
```
**If any tasks are not completed, STOP and ask user to complete them first.**

2. Get epic summary with short format:
```bash
moderails epic summary --name <epic> --short
```
   This shows task summaries and changed filenames only (no full diffs)

3. Check epic tags:
   - **Single tag**: Auto-create context file in `moderails/context/{tag}/{epic-name}.md`
   - **Multiple tags**: Ask user which tag folder to use
   - **No tags**: Ask user if context should be in root (mandatory) or skip archiving

4. Show user the context file path and content preview

5. **Ask for confirmation** before proceeding

6. After confirmation:
   - Create the context file with epic summary
   - Delete the epic:
   ```bash
   moderails epic delete --name <epic> --confirm
   ```

## CONTEXT FILE FORMAT

Use the template from `moderails/templates/archive-template.md`:

- **Description**: Comprehensive description of what was accomplished (synthesize from task summaries, don't list them)
- **Files Changed**: Simple list of all files touched in this epic
- **Key Decisions**: Important architectural or implementation decisions worth remembering

**Keep it concise:** The goal is high-level context for future work, not detailed code history. Synthesize task summaries into a cohesive description.

## PERMITTED
- Archive only fully completed epics
- Ask for confirmation before any destructive action
- Create context files in tag-specific folders
- Extract only filenames from git changes (not full diffs)
- Keep archived context concise and high-level

## FORBIDDEN
- **NEVER archive epic with incomplete tasks**
- **NEVER delete epic without user confirmation**
- **NEVER include full code diffs** - only filenames
- No verbose or detailed code history

---
**YOU MUST FOLLOW THE WORKFLOW**

