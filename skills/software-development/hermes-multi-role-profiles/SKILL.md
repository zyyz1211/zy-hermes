---
name: hermes-multi-role-profiles
description: "Set up multiple Hermes profiles with distinct SOUL.md personalities for role-based collaboration — e.g. a creative/planning agent, an execution agent, and a review/critique agent, with the human as final decision-maker."
version: 1.0.0
author: Hermes Agent
tags: [hermes, profiles, multi-agent, SOUL, personality, collaboration]
---

# Hermes Multi-Role Profiles

Configure Hermes with multiple profiles, each with a distinct **SOUL.md** personality, so different agent roles handle different phases of work — planning → execution → review → human decision.

## When to Use

- You want more than one "Hermes personality" for different kinds of tasks
- You want a **workflow pipeline**: Agent A plans → Agent B executes → Agent C reviews → you decide
- Each profile should have independent memory, skills, and session history
- You want the default profile untouched while adding new roles

## How It Works

Each profile gets its own:
- `~/.hermes/profiles/<name>/` directory with isolated config.yaml, .env, SOUL.md, sessions, memory
- **SOUL.md** — loaded fresh each message as the personality definition (no restart needed)
- Independent skills and tool config

## Setup

### 1. Create Profiles

```bash
# Clone from default to inherit model/api config
hermes profile create office --clone --clone-from default \
  --description '日常办公：执行落地，写文件、处理周报'

hermes profile create review --clone --clone-from default \
  --description '审核内容：检查质量，挑问题提意见'

hermes profile create think --clone --clone-from default \
  --description '创意规划：出主意、做方案、定计划'
```

### 2. Write SOUL.md for Each Profile

Each `~/.hermes/profiles/<name>/SOUL.md` defines the role. Example structure:

**think (创意规划)** — generates options, does NOT execute:
```
你是一名富有创意的策划者，负责提供思路和方案。
- 每次至少给出 2-3 个可选方案
- 标注推荐方案及其理由
- 最终决策权在用户
```

**office (日常办公)** — executes, does NOT plan or review:
```
你是一名高效的办公助理，负责执行落地。
- 按指令精确执行，不擅自创作
- 输出格式规范、条理清晰
- 涉及文件操作时给出文件路径
```

**review (审核内容)** — critiques, does NOT execute:
```
你是一名严格的内容审核员。
- 用 bullet point 列出问题，每条带严重级别
  🔴 严重 / 🟡 一般 / 🟢 建议
- 最后给出总体评价：通过 / 修改后通过 / 不通过
- 直来直去，不拐弯抹角
```

> SOUL.md is loaded on every message — you can edit it and the change takes effect immediately without restarting the session.

### 3. Using the Profiles

```bash
# Start a specific profile
hermes -p think
hermes -p office
hermes -p review

# Or via the wrapper scripts (automatically created)
think      # shortcut to hermes -p think
office     # shortcut to hermes -p office
```

Wrapper scripts live in `~/.local/bin/`. Add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Workflow Pipeline

```
你                 → think: "帮我规划下周重点工作"
think (方案A/B/C)  → 你 (选方案A)
你                 → office: "按方案A执行，写周报"
office (周报草稿)  → 你
你                 → review: "检查这份周报"
review (审核意见)  → 你 (最终决策)
```

Each profile has **isolated memory and sessions** — they don't know what the others said unless you tell them.

## Tips

- Keep SOUL.md **focused on the role**, not the task. The role is durable; tasks change.
- Use `--description` during creation — it's used by kanban for task routing later
- Profiles share the same API key pool by default (cloned .env). Set different keys per profile if needed in `~/.hermes/profiles/<name>/.env`
- Gateway can be started per-profile: `hermes -p office gateway start`
- List all profiles: `hermes profile list`
- Show profile detail: `hermes profile show <name>`

## Maintenance: Bulk Config Changes

When you need to apply the same setting across multiple profiles (e.g. change `display.language` or `display.personality`), use the right tool per profile type:

### Main Profile

The main `~/.hermes/config.yaml` is security-restricted — agent tools like `patch` are blocked. Use the CLI:

```bash
hermes config set display.language zh
hermes config set display.personality concise
```

### Sub-Profiles (`~/.hermes/profiles/<name>/config.yaml`)

Agent `patch` works directly on sub-profile configs. But beware of **duplicate keys**: settings like `language: en` may appear both under `display:` and under auxiliary provider configs (e.g. `stt.language`). Always include enough context lines to make the match unique:

```patch
# GOOD — unique context
  file_mutation_verifier: true
  show_cost: false
  skin: default
- language: en
+ language: zh
  tui_status_indicator: kaomoji
  user_message_preview:

# BAD — matches twice in the file
language: en  →  language: zh   # ✗
```

### Verify Changes

```bash
grep -n "language:" ~/.hermes/config.yaml
grep -n "language:" ~/.hermes/profiles/*/config.yaml
grep -n "personality:" ~/.hermes/profiles/*/config.yaml
```

## Pitfalls

- SOUL.md can only set personality/tone — it cannot add or remove tools
- Each profile has its OWN `.env` file cloned from the source. If the source's .env has placeholders (like `sk-ea9...b910`), the clone gets the same placeholder — not the resolved key
- Wrapper scripts (`~/.local/bin/`) are `.bat` on Windows — they work in cmd.exe but not in git-bash/WSL directly. Use `hermes -p <name>` in bash
- Deleting a profile removes all its sessions and memory irreversibly
