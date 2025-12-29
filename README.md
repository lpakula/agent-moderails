# Agent ModeRails

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)
![CLI](https://img.shields.io/badge/cli-pipx-orange.svg)
![Coverage](https://img.shields.io/badge/coverage-73%25-brightgreen.svg)

**Plan Mode on steroids** — structured agent workflow with persistent memory.

Inspired by the [RIPER-5 protocol](https://forum.cursor.com/t/i-created-an-amazing-mode-called-riper-5-mode-fixes-claude-3-7-drastically/65516).

> **Not for vibe coding.** ModeRails makes your coding agent a collaborator — working *with* you, not just *for* you. Take full advantage of AI-assisted development while staying in complete control. The protocol encourages you to understand every decision, learn along the way, and own your codebase.

---

## 🤔 Why ModeRails?

Most AI coding agents fail not because they're weak, but because they work without structure.

**Plan mode helps you think before acting — but it has limits:**
- Context is lost when the chat closes
- No task history to learn from
- Can't resume work days later with full context
- No git integration to track what was actually implemented

This works for small isolated tasks — but breaks down for real projects.

**Why ModeRails?**

ModeRails gives you a complete protocol for multi-session development

- **Persistent memory across sessions** — return to tasks days later with full context intact
- **Searchable task history** — agent learns from past work and similar features
- **Epic-based grouping** — organize related tasks under a single epic, with shared context
- **Git integration** — captures diffs, file changes, and commit hashes for every completed task
- **Explicit mode boundaries** — research can't write code, execute must follow the plan
- **Enforced workflow** — prevents scope creep and direction changes mid-implementation

**ModeRails is opt-in, not mandatory.** You choose when to use it:

- **For structured work**: Initialise the protocol with `/moderails` command and follow the full protocol
- **For small tasks & bug fixes**: Use **Fast mode** (`#fast`) — take advantage of persistent memory and context loading without the protocol
- **No need for better context and enhanced agent cooperation?** Keep using regular chat

---

## 📦 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash
```

## 📥 Upgrade

```bash
pipx upgrade moderails
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
🔍 Research → 📋 Plan → 🔨 Execute → ✅ Complete
```

**🔍 Research** — Understand the task  
**📋 Plan** — Define what will be done  
**🔨 Execute** — Implement the plan  
**✅ Complete** — Finish the task

**Optional:**  
**💡 Brainstorm** — Explore alternative approaches after the research  
**❌ Abort** — Abandon task and reset changes  
**⚡ Fast** — Context memory without the protocol (for small tasks and bug fixes)

---

## 📚 Documentation

- **[Installation](docs/installation.md)** — Installation and setup guide
- **[Agent Modes](docs/modes.md)** — Understanding the workflow modes
- **[Context Discovery](docs/context.md)** — Loading and searching project context
- **[CLI Commands](docs/cli.md)** — Complete command reference
- **Configuration** — *(Coming soon)*
- **[Development](docs/development.md)** — Contributing and local setup