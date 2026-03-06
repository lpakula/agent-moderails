---
description: Core protocol for moderails-managed agents
globs:
alwaysApply: true
---

# moderails Agent Protocol

You are a moderails-managed agent working in a git worktree.

## Commands

- `moderails mode next` -- get your next step instructions
- `moderails mode current` -- re-read the current step (use after crash/restart)

## Rules

1. Always run `moderails mode next` to get step instructions -- never guess
2. Complete each step fully before moving to the next
3. After completing a step, run `moderails mode next` to continue
