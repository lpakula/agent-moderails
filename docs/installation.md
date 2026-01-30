# Installation and Setup

## Installation

```bash
# One-liner (recommended)
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash

# Or manual
pipx install git+https://github.com/lpakula/agent-moderails
```

## Upgrade

```bash
pipx upgrade moderails

# Or manual
pipx install --force git+https://github.com/lpakula/agent-moderails
```

Your tasks and history are preserved during upgrades.

## Setup

```bash
cd my-project
moderails init
```

### Private Mode

For projects where you don't want to commit any moderails files:

```bash
moderails init --private
```

This ignores all `_moderails/` files in git. Task history remains local and won't be committed.

---

This creates the following structure:

```
my-project/
├── .cursor/commands/moderails.md ✨
├── .claude/commands/moderails.md ✨
└── _moderails/
    ├── config.json ⚙️
    ├── moderails.db 💾
    ├── history.jsonl 📜
    ├── tasks/ 📝
    │   └── epic-name/
    │       └── task-name-abc123.plan.md
    └── context/ 📚
        ├── mandatory/ 🔒
        └── memories/ 💭
```

✨ *moderails.md* — triggers the protocol in your editor  
⚙️ *config.json* — workflow configuration  
💾 *moderails.db* — stores epics and tasks for fast search (local only)  
📜 *history.jsonl* — persistent storage of all completed tasks, searchable by the agent  
📝 *tasks/* — temporary working files organized by epic (ignored in git)  
📚 *context/* — project knowledge base  
&nbsp;&nbsp;🔒 *mandatory/* — loaded automatically when entering research/fast modes  
&nbsp;&nbsp;💭 *memories/* — named context documents the agent can discover and load

