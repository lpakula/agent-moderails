# Agent ModeRails

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)
![CLI](https://img.shields.io/badge/cli-pipx-orange.svg)
![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)

**Plan Mode on steroids** — structured agent workflow with persistent memory.

Inspired by the [RIPER-5 protocol](https://forum.cursor.com/t/i-created-an-amazing-mode-called-riper-5-mode-fixes-claude-3-7-drastically/65516).

> **Not for vibe coding.** ModeRails makes your coding agent a collaborator — working *with* you, not just *for* you. Take full advantage of AI-assisted development while staying in complete control. The protocol encourages you to understand every decision, learn along the way, and own your codebase.

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

**ModeRails fixes this** by giving the agent:
- **Explicit modes** with clear boundaries
- **Persistent task memory** across sessions
- **Enforced rules** — research can't write code, execute can't redesign

**Why not just use Plan mode?**  
Plan mode helps you think before acting — but it's session-limited. Close the chat and context is gone. ModeRails gives you persistent memory across sessions and auto-loads relevant context when you return.

---

## 📦 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash
```

## 🚀 Quickstart

```bash
cd my-project
moderails init
```

Then in your editor:

```
/moderails
```

**And that's it!** The agent will guide you step-by-step through the workflow for your next task:
```
🔍 Research → 📋 Plan → ⚡ Execute → ✅ Complete
```

**🔍 Research** — Understand the task  
**📋 Plan** — Define what will be done  
**⚡ Execute** — Implement the plan  
**✅ Complete** — Finish the task

**Optional:**  
**💡 Brainstorm** — Explore alternative approaches after the research  
**❌ Abort** — Abandon task and reset changes

---

## 📚 Documentation

- **[Installation](docs/installation.md)** — Installation and setup guide
- **[Agent Modes](docs/modes.md)** — Understanding the workflow modes
- **[Context Discovery](docs/context.md)** — Loading and searching project context
- **[CLI Commands](docs/cli.md)** — Complete command reference
- **Configuration** — *(Coming soon)*
- **[Development](docs/development.md)** — Contributing and local setup