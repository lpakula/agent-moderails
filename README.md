# moderails

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)
![CLI](https://img.shields.io/badge/cli-pipx-orange.svg)

**Autonomous agent orchestrator** — queue tasks, run agents in isolated git worktrees, review results. No babysitting.

---

## Why moderails?

Cloud agent platforms (Devin, Codex, etc.) run in isolated VMs — great for safety, but:

- **No local context** — they can't access your dev environment, databases, local CLI tools, or project-specific setup
- **One-shot execution** — a single prompt, a single attempt, no multi-step workflows
- **No customisation** — you can't control the workflow or define your own execution steps
- **Opaque execution** — limited visibility into what the agent is doing and why
- **Vendor lock-in** — tied to a specific platform and pricing model

moderails solves this:

- **Local context** — agents have access to your local development environment, so they get the same context you get.
- **Multi-step workflows** — define ordered sequences of steps with quality gates. The agent works through them one at a time.
- **Full customisation** — create your own flows, steps, and gates. Control exactly how the agent works.
- **Transparent execution** — stream logs in real time, inspect prompts, review outcomes. Everything is tracked.
- **Open source** — runs on your machine, with your own local agents. No vendor lock-in.

The workflow is simple:

1. **Register a repository** — point moderails at any local git repo
2. **Create a task** — describe what you want done (feature, fix, refactor)
3. **Start a run** — executes the selected flow autonomously in the background
4. **Review the PR** — the agent creates a pull request for you to review and merge

---

## 📦 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/lpakula/agent-moderails/main/scripts/install.sh | bash
```

Or install directly:

```bash
pipx install git+https://github.com/lpakula/agent-moderails
```

### Upgrade

```bash
pipx upgrade moderails
```

### Prerequisites

- Python 3.11+
- Git
- [Cursor agent CLI](https://docs.cursor.com/agent) (`agent` command)

---

## 🚀 Quickstart

```bash
# 1. Start the daemon (once, runs in background)
moderails daemon start

# 2. Register your project
cd my-project
moderails register

# 3. Open the web UI
moderails ui
```

From the UI at `http://localhost:4200`:

1. Create a task — give it a title and description
2. Start a run — pick a flow (or chain multiple flows)
3. Watch the agent work — stream logs in real time
4. Review the branch — the agent's changes are on an isolated worktree branch

Or do it all from the CLI:

```bash
moderails task create -t "Add dark mode" -d "Add dark mode toggle to the settings page"
moderails task start --id <task-id> --flow default
moderails run logs <run-id> --follow
```

---

## 🖥️ Web UI

The dashboard at `http://localhost:4200` lets you:

- **Manage tasks** — create, edit, start runs
- **Monitor runs** — live log streaming, status tracking
- **Edit flows** — drag-and-drop step reordering, inline editing, gate configuration
- **Import/export flows** — share flow definitions as JSON
- **View the queue** — see pending and executing runs across all projects
- and more...

---

## 📚 Documentation

- **[Installation](docs/installation.md)** — setup, upgrade, and project registration
- **[Flows](docs/flows.md)** — flows, steps, gates, and template variables
- **[CLI Reference](docs/cli.md)** — all commands
- **[Development](docs/development.md)** — contributing and local setup
