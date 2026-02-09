# Moderails Protocol

Modal control system for AI agents.

{% if project_root %}
## PROJECT

**Path**: `{{ project_root }}`

> All `moderails` commands must be run from this directory.
{% endif %}

{% include 'partials/protocol.md' %}

{% if current_task %}
## RESUME SESSION

Task in progress: **{{ current_task.name }}** (`{{ current_task.id }}`)
{% if current_task.epic %}- Epic: {{ current_task.epic.name }} (`{{ current_task.epic.id }}`){% endif %}

Ask user: "Continue with this task, or remove existing task and start something new?"

- **If continue**: Run `moderails start --rerail` to load session context
- **If abandon**: Tell user to type `#abort`

{% else %}
## STATUS
**Skills:**
{% if skills %}
{% for s in skills %}- `{{ s }}`
{% endfor %}
{% endif %}
{% if epics %}
**Epics:**
{% for e in epics %}- `{{ e.id }}` - {{ e.name }}
{% endfor %}
{% endif %}
{% if draft_tasks %}
**Draft tasks:**
{% for t in draft_tasks %}- `{{ t.id }}` - {{ t.name }}{% if t.epic %} ({{ t.epic.name }}){% endif %}
{% endfor %}
{% endif %}

---

## WORKFLOW
{% if draft_tasks %}
1. Ask user which draft to start, or create a new task
2. To start a draft: `moderails task update --id <id> --status in-progress`
3. Advise user to type `#research` to begin analysis
{% else %}
1. Ask user in natural language: "What would you like to build?"
2. Wait for user's description
3. Based on the description, propose:
   - A task name
   - Task type (feature/fix/refactor/chore)
{% if epics -%}
4. Suggest an existing epic if related, or create a new one
{% else -%}
4. Create epic with relevant skills: `moderails epic create --name "epic-name" [--skills <skill1> --skills <skill2>]`
{% endif -%}
5. Create task: `moderails task create --name "Task name" [--description "<context>"] [--type feature|fix|refactor|chore] [--epic <epic-id>]` (use --description for draft context)
6. Advise user to type `#research` to begin analysis
{% endif %}

---
**YOU MUST FOLLOW THE WORKFLOW**
{% endif %}
