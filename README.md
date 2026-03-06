# moderails

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

**Autonomous agent orchestrator** — run Cursor agents on real tasks, in isolated git worktrees, with persistent memory.

---

## What it does

moderails lets you queue tasks for an AI agent (Cursor), execute them autonomously in isolated git worktrees, and review results — all without blocking your main branch.

- **Flows** — define ordered sequences of steps (research → plan → execute → test → commit)
- **Runs** — each task execution is a tracked run with its own log, prompt, and outcome
- **Daemon** — background process that picks up queued runs and launches the agent
- **Web UI** — manage tasks, flows, and runs from a local dashboard
- **Memory** — every run stores its summary; subsequent runs see full history

---

## Quickstart

```bash
# Install
pipx install git+https://github.com/lpakula/agent-moderails

# Register your project
cd my-project
moderails register

# Start the daemon
moderails daemon start

# Open the UI
moderails ui
```

---

## Core concepts

### Flows
A flow is an ordered list of steps. Each step is a markdown prompt loaded into the agent one at a time via `moderails mode next`. The agent completes the step, calls `moderails mode next`, and moves to the next step.

Default flows included out of the box:
- **default** — execute, test, commit
- **ripper-5** — research, brainstorm, plan, execute, test, commit
- **submit-pr** — creates a PR or comments on an existing one

You can create, edit, and reorder flows from the UI or CLI.

### Tasks
A task represents a unit of work (feature, fix, refactor). Tasks belong to a project and have a title and description. Runs are created from tasks.

### Runs
A run is a single agent execution. It belongs to a task, follows a flow (or chain of flows), and records the agent's prompt, log, outcome, and summary. Multiple runs can exist per task.

### Daemon
The daemon picks up queued runs in order and launches Cursor in the task's git worktree. It monitors the agent process and marks the run complete when it exits.

---

## Documentation

- **[Installation](docs/installation.md)** — setup and upgrade
- **[Flows](docs/flows.md)** — understanding flows and steps
- **[CLI Reference](docs/cli.md)** — all commands
