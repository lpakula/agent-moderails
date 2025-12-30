# Agent Modes

Modes define clear boundaries — no skipping ahead, no mixing phases.

```
🔍 Research → 📋 Plan → 🔨 Execute → ✅ Complete
```

## 🏁 Start

```
/moderails
```

The protocol initialisation. 

The agent asks you to describe what you want to build before exploring your codebase.

## 🔍 Research

```
#research
```

The agent explores your codebase, searches for relevant context, and asks clarifying questions to fully understand the requirements.

**No code changes allowed** — understanding first, implementation later.

## 💡 Brainstorm (optional)

```
#brainstorm
```

Optional. Use if you want to explore alternative approaches to what was agreed in Research. The agent proposes up to 3 options with pros and cons.

## 📋 Plan

```
#plan
```

The agent breaks down the work into atomic TODO items in the task file. Review and approve before moving to execution.

## 🔨 Execute

```
#execute
```

Implement TODO items one by one. Mark each item complete `[x]` in the task file.

> Type `--no-confirmation` to work through all TODOs without stopping for confirmation between items.

**Adjusting the plan:** No plan is perfect. You can adjust the approach along the way — add items, modify steps, or change direction. All changes are recorded in the task file, which remains the single source of truth throughout execution.

## ✅ Complete

```
#complete
```

Mark task as completed, commit changes with conventional commit message. Git hash is stored locally for diff retrieval. 

## ⚡ Fast (optional)

```
#fast
```

Context-aware coding without the protocol. Access the same context memory system (mandatory context, searchable context, task history) but skip the structured workflow.

Best for small tasks, bug fixes, and quick iterations where you want memory benefits without mode switching.

> **Snapshot feature**: Type `--snapshot` to create a structured commit with task history in one go, without leaving Fast mode.

## ❌ Abort (optional)

```
#abort
```

Abandon task at any point. Permanently deletes the task and resets all git changes.

