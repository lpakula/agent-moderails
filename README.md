# Agent ModeRails

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)
![CLI](https://img.shields.io/badge/cli-pipx-orange.svg)

**Plan Mode on steroids** — structured agent workflow with persistent memory.

Inspired by the [RIPPER-5 protocol](https://forum.cursor.com/t/i-created-an-amazing-mode-called-riper-5-mode-fixes-claude-3-7-drastically/65516).

> **Not for vibe coding.** ModeRails turns a coding agent into a collaborator — one that works *with* you, not *for* you. Take full advantage of AI-assisted development while staying in complete control. The protocol encourages you to understand every decision, learn along the way, and own your codebase.

---

## 🤔 Why ModeRails?

Most AI coding agents fail not because they're weak, but because they work without structure.

**Without a protocol, agents tend to:**
- Jump straight into coding
- Mix thinking, planning, and execution
- Change direction mid-task
- Forget earlier decisions
- Lose context in longer sessions

This works for tiny prompts — but breaks down for real projects.

**moderails fixes this** by giving the agent:
- **Explicit modes** with clear boundaries
- **Persistent task memory** across sessions
- **Enforced rules** — research can't write code, execute can't redesign

**Why not just use Plan mode?**  
Plan mode helps you think before acting — but it's session-limited. Close the chat and context is gone. ModeRails gives you persistent memory across sessions and auto-loads relevant context when you return.

---

## 🧭 The Modes

Modes define clear boundaries — no skipping ahead, no mixing phases.

```
🔍 Research → 📋 Plan → ⚡ Execute → ✅ Complete
```

**🔍 Research** — Understand the problem  
**📋 Plan** — Define what will be done  
**⚡ Execute** — Implement the plan  
**✅ Complete** — Finish the task

**Optional:**  
**💡 Brainstorm** — Explore alternative approaches  
**❌ Close** — Abandon task and reset changes

---

## 📦 Installation

```bash
# One-liner (recommended)
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash

# Or manual
pipx install git+https://github.com/lpakula/agent-moderails
```

## ⚙️ Setup

```bash
cd my-project
moderails init
```

This creates the following structure:

```
my-project/
├── .cursor/commands/moderails.md ✨
├── .claude/commands/moderails.md ✨
└── moderails/
    ├── config.json ⚙️
    ├── moderails.db 💾
    ├── tasks/ 📝
    │   └── epic-name/
    │       └── task-name.md
    └── context/ 📚
        ├── project-overview.md 📌
        └── tag-name/ 🏷️
            └── guide.md
```

✨ **Init command** — triggers the protocol in your editor  
⚙️ **Config** — workflow configuration  
💾 **Database** — stores epics, tasks, and status  
📝 **Task files** — markdown with requirements, TODOs, and notes  
📚 **Context files** — project knowledge loaded automatically  
📌 **Required context** — always loaded for every task  
🏷️ **Tag context** — loaded when epic has matching tag

## 🚀 Workflow

### 1. Start the Protocol

Execute the command in your editor to initialize the protocol:

```
/moderails
```

Then, specify your task:

**a) New task:**
```
--new --epic epic-name --task task-name --tags tag1,tag2
```

- `--epic` - group of related tasks (e.g. a feature or milestone)
- `--task` - specific task within the epic (see [Task Template](moderails/templates/task-template.md))
- `--tags` - (optional) auto-load matching context files (see [Context Loading](#-context-loading))

**b) Existing task:**
```
--task task-name
```

- If status is `todo` → start with `#research`
- If status is `in-progress` → continue with `#execute`

> 🔀 **Git Branch**: Epic name = branch name. To avoid conflicts, start new tasks from a clean `main` branch, or checkout to the epic branch before continuing existing work. The protocol enforces this automatically — it creates/switches branches for you.

### 2. 🔍 Research

```
#research 

<explain what you want to build>
```

Describe what you want to build. The agent explores relevant files and asks clarifying questions. Iterate until you agree on the approach. No code changes allowed.

### 3. 💡 Brainstorm (optional)

```
#brainstorm
```

Optional. Use if you want to explore alternative approaches to what was agreed in Research. The agent proposes up to 3 options with pros and cons.

### 4. 📋 Plan

```
#plan
```

The agent breaks down the work into atomic TODO items in the task file. Review and approve before moving to execution.

### 5. ⚡ Execute

```
#execute
```

Implement TODO items one by one. Mark each item complete `[x]` in the task file.

### 6. ✅ Complete

```
#complete
```

Mark task as completed, commit changes with conventional commit message, store git hash.

### 7. ❌ Close (optional)

```
#close
```

Abandon task at any point. Permanently deletes the task and resets all git changes.

## 🧠 Context Loading

When you start or continue a task, the following context is automatically loaded:

### 1. Epic Summary

What's already been done in this epic — completed task summaries in chronological order and git diff from main.

### 2. Context Files

Files in `moderails/context/` are automatically loaded when you start a task:

- 📌 **Required** — files in the root of context folder, loaded for every task
- 🏷️ **Tag-based** — files in subfolders, loaded when epic has a matching tag

## 💻 CLI Commands

```bash
# Initialize in current directory
moderails init

# Start session or create/continue task
moderails start
moderails start --new --task "task" --epic "epic" --tags "auth,api"
moderails start --task "task"

# Show all epics and tasks
moderails status

# Get mode-specific rules
moderails mode --name <mode>

# Task management
moderails task update --task <task> --status <status>
moderails task update --task <task> --summary "..."
moderails task update --task <task> --git-hash <hash>
moderails task delete --task <task> --confirm

# Epic management
moderails epic summary --name <epic>
moderails epic update --name <epic> --tags "..."
moderails epic delete --name <epic> --confirm
```

## 🛠️ Development

```bash
# Clone and install in dev mode
git clone https://github.com/lpakula/agent-moderails.git
cd agent-moderails
pipx install -e .

# Run
moderails --help
```

Changes are reflected immediately — no reinstall needed.
