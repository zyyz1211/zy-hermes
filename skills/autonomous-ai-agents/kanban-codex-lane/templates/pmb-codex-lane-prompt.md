# PMB Codex Lane Prompt Template

This template is used to spawn a Codex CLI instance as an isolated implementation lane for a Kanban task.

## Template

```
You are working on task [TASK_ID]: [TASK_TITLE].

Acceptance criteria:
[CRITERIA]

Constraints:
- Do not modify: [FILES_THAT_MUST_NOT_CHANGE]
- Keep changes minimal and focused on the task.
- Run the project tests before finishing.

Working directory: [WORKDIR]
```
