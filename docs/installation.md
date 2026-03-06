# Installation and Setup

## Install

```bash
pipx install git+https://github.com/lpakula/agent-moderails
```

## Upgrade

```bash
pipx install --force git+https://github.com/lpakula/agent-moderails
```

## Register a project

Run this inside any git repository you want to manage with moderails:

```bash
cd my-project
moderails register
```

This will:
- Register the project in the moderails database (`~/.moderails/moderails.db`)
- Create a `.moderails/` directory in the project root
- Add `.worktrees/` to `.gitignore`
- Generate `.cursor/rules/moderails.md` — the agent rules file

You can give the project a custom name:

```bash
moderails register --name "My App"
```

## Start the daemon

The daemon is required for autonomous agent execution:

```bash
moderails daemon start
```

Run in the foreground (useful for debugging):

```bash
moderails daemon start --foreground
```

Stop:

```bash
moderails daemon stop
```

## Open the UI

```bash
moderails ui
```

Opens the local dashboard at `http://localhost:8000`.

## Database

The system database lives at `~/.moderails/moderails.db`. To wipe everything and start fresh:

```bash
moderails db reset
```

Re-register your projects afterwards:

```bash
cd my-project && moderails register
```
