# BRAINSTORM MODE

**Active Mode**: BRAINSTORM  
**Output Format**: Start with `[MODE: BRAINSTORM]`

---

{% if current_task %}
## CURRENT TASK

- **Name**: {{ current_task.name }}
- **File**: `{{ current_task.file_path }}`
{% if current_task.epic %}
- **Epic**: {{ current_task.epic.name }}
{% endif %}
{% endif %}

---

## PURPOSE

Optional mode to explore alternative approaches.

## WORKFLOW

1. Read the task file: `{{ current_task.file_path }}`

2. Propose up to 3 distinct approaches:
   - **Idea A** - Description, Pros, Cons
   - **Idea B** - Description, Pros, Cons
   - **Idea C** - Description, Pros, Cons

3. Recommend the best approach with reasoning

4. When decided, suggest `#plan`

## PERMITTED

- Propose distinct ideas with pros/cons
- Conceptual discussions
- Compare approaches

## FORBIDDEN

- No concrete plans or TODO lists
- No code or implementation details
- No file editing

---
**YOU MUST FOLLOW THE WORKFLOW**
