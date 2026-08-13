---
name: kanban-codex-lane
description: Use when a Hermes Kanban worker wants to run Codex CLI as an isolated implementation lane while Hermes keeps ownership of task lifecycle, reconciliation, testing, and handoff.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, codex, worktrees, autonomous-agents, prediction-market-bot]
    related_skills: [kanban-worker, codex, hermes-agent]
---

# Kanban Codex Lane

## Overview

This skill defines the lightweight Hermes+Codex dual-lane convention for Kanban workers. Hermes is always the task owner: it calls `kanban_show`, decides whether Codex is appropriate, creates or selects an isolated workspace, starts and monitors Codex, reconciles any diff, runs verification, and writes the final `kanban_complete` or `kanban_block` handoff. Codex is an input lane only. Codex output is not a task completion signal, not a trusted reviewer, and not allowed to write durable Kanban state directly.

The convention exists so a Hermes worker can use Codex for bounded implementation help without changing the dispatcher. The dispatcher must still spawn Hermes workers. A worker may optionally spawn Codex inside its own run, then accept, partially accept, or reject the lane after independent review and tests.

## When to Use

Use the Codex lane when all of these are true:

- The Kanban task is a coding, refactor, documentation, test, or mechanical migration task with clear acceptance criteria.
- A bounded diff can be evaluated by Hermes in one run.
- The repo can be copied or checked out in an isolated git worktree/branch.
- Hermes can run the relevant tests itself after Codex exits.
- The prompt can state all safety constraints and files that must not change.

Do not use the Codex lane when any of these are true:

- The task requires human judgment that is not already captured in the Kanban body.
- The worker lacks repo access and cannot evaluate the diff in one run.
- The task modifies durable Kanban state directly.
- The worker cannot run the relevant tests.

## Workflow

1. Read the Kanban task body and acceptance criteria.
2. Decide whether the Codex lane is appropriate.
3. Create or select an isolated git worktree/branch for the change.
4. Start Codex with a self-contained prompt that states the task, constraints, and files that must not change.
5. Monitor Codex until it exits.
6. Reconcile the diff: review each changed file, run tests, reject anything unsafe or off-scope.
7. Accept or reject the lane, then write the final Kanban handoff.

## Verification

- Run the project's test suite after Codex exits.
- Review the full diff before accepting.
- Confirm no durable Kanban state was written by Codex.
