# Installation and Setup

## Installation

```bash
# One-liner (recommended)
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash

# Or manual
pipx install git+https://github.com/lpakula/agent-moderails
```

## Setup

```bash
cd my-project
moderails init
```

This creates the following structure:

```
my-project/
├── .cursor/commands/moderails.md ✨
├── .claude/commands/moderails.md ✨
└── .moderails/
    ├── config.json ⚙️
    ├── moderails.db 💾
    ├── history.json 📜
    ├── tasks/ 📝
    │   ├── task-name-abc123.plan.md
    │   └── another-task-xyz789.plan.md
    └── context/ 📚
        ├── mandatory/ 🔒
        └── search/ 🔍
```

✨ **Init command** — triggers the protocol in your editor  
⚙️ **Config** — workflow configuration  
💾 **Database** — stores epics and tasks (local only)  
📜 **History** — completed tasks (Git-tracked, shared across team)  
📝 **Task files** — markdown with requirements, TODOs, and notes  
📚 **Context** — project knowledge base  
&nbsp;&nbsp;🔒 **mandatory/** — loaded automatically with every task (conventions, architecture)  
&nbsp;&nbsp;🔍 **search/** — searched by agent when relevant (features, APIs, patterns)

