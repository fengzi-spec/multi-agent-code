multi-agent-code — 多Agent协作编码技能

一句话概括

一个 Claude Code 技能，让多个不同角色的 AI Agent 像真实软件团队一样协作：分析师拆需求、架构师做设计、编码者接力写代码、审查者把关质量，所有参数可选配，一句 "go" 就能启动整条流水线。

---
解决了什么问题

单个 AI 写代码就像一个人单干——能跑，但会有盲区。这个技能模拟真实团队的协作模式：

不是你 → AI写代码 → 完事

而是你 → 分析师 → 架构师 → 编码者A → 审查 → 编码者B → 审查 → ... → 质量

---
五个角色

┌────────────────────┬──────────┬──────────────────────────────────────
│        角色        │ 是否必须 │                             干什么                             │
├────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
│ Analyst 需求分析师 │ 可选     │ 把"做个登录功能"这种模糊需求变成带验
├────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
│ Architect 架构师   │ 可选     │ 设计模块划分、数据模型、API 契约，画出架构图                   │
├────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
│ Coder 编码者       │ ✅ 必须  │ 写代码，但每轮是不同的"人格"，在上一
├────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
│ Reviewer 审查者    │ ✅ 必须  │ 系统化审查代码，每个问题分严重级别（c
├────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
│ Tester 测试者      │ 可选     │ 写完整测试套件，输出覆盖率报告
└────────────────────┴──────────┴────────────────────────────────────────────────────────────────┘

编码者三个人格轮换

┌────────┬─────────────────────┬──────────────┬────────────────────────────────────────┐
│  轮次  │        人格         │     心态     │                  做啥                  │
├────────┼─────────────────────┼──────────────┼────────────────────────────────────────┤
│ 第1轮  │ Generator           │ "先跑起来"   │ 快速出活，功能优先，合
├────────┼─────────────────────┼──────────────┼────────────────────────────────────────┤
│ 第2轮  │ Critic              │ "找茬修bug"  │ 安全漏洞、边界条件、并
├────────┼─────────────────────┼──────────────┼────────────────────────────────────────┤
│ 第3轮  │ Refiner             │ "打磨到精品" │ 性能优化、设计模式、可
├────────┼─────────────────────┼──────────────┼────────────────────────────────────────┤
│ 第4轮+ │ Critic/Refiner 交替 │ 继续迭代     │ 直到质量达标或触发停止条件             │
└────────┴─────────────────────┴──────────────┴────────────────────────

---
核心设计理念：参数全可选，默认就能跑

用户不需要记任何参数，输入任务就能启动：

/multi-agent-code "用Python写一个todo API"

技能弹出一个配置界面展示所有默认值，用户回复 "go" 就开跑，想改就改：

╔══════════════════════════════════════════════════════════╗
║           Multi-Agent Code — 当前配置                     ║
╠══════════════════════════════════════════════════════════╣
║  1. 最大轮次:     10    (跑到10轮或触发停止条件时停)      ║
║  2. 可选角色:     无    (analyst / architect / tester)   ║
║  3. 审查时机:     每轮   (每轮 / 每N轮 / 最后)            ║
║  4. 停止条件:     critical (critical/high/medium时停)    ║
║  5. 修复尝试:     1次    (发现严重问题后给几次修复机会)    ║
║  6. 自动/手动:    自动   (修复失败后自动停还是问你)        ║
║  7. 编程语言:     (自动检测)                              ║
║  8. 输出目录:     ./output                               ║
║                                                          ║
║  回复"go"使用默认配置，或者告诉我你想改的参数              ║
╚══════════════════════════════════════════════════════════╝

用户可以说 "轮次改成5，加上架构师，high时停止" 来改任意参数。

---
三种停止条件（满足任一就停）

Round 1: Generator写代码 → Review → 1个critical安全漏洞
         → 进入修复期，给Critic 1次机会修
Round 2: Critic修复 → Review → 0个问题
         → ✅ 质量达标，提前结束！（不用跑满10轮）

或者：
Round 1: Generator写代码 → Review → 1个critical
         → 修复期，继续
Round 2: Critic修复 → Review → critical还在
         → 修复机会用完 → ⚠️ 停止！（重大问题修不好）

┌──────────────────┬──────────┬────────────────────────────┐
│       参数       │  默认值  │            作用            │
├──────────────────┼──────────┼────────────────────────────┤
│ max_rounds       │ 10       │ 最大运行轮次               │
├──────────────────┼──────────┼────────────────────────────┤
│ stop_on_severity │ critical │ 发现什么级别的问题触发停止 │
├──────────────────┼──────────┼────────────────────────────┤
│ fix_attempts     │ 1        │ 触发后给编码者几次修复机会 │
└──────────────────┴──────────┴────────────────────────────┘

---
Agent 之间如何交接

每个编码者产出三样东西给下一轮：

1. 完整代码文件 — 不是 diff，是全量代码
2. 变更日志 — 改了什么、为什么这样改、设计决策
3. 遗留问题 — 哪些地方还有疑虑、建议下一轮重点关注什么

下一位编码者看到的不只是代码，还有前人的思考过程。

---
文件结构

multi-agent-code/
├── CLAUDE.md              # 技能入口，编排整条流水线
├── README.md              # 用户文档
├── LICENSE                # MIT
└── prompts/               # 7个角色的系统提示词
    ├── analyst.md         # 需求分析师
    ├── architect.md       # 架构师
    ├── coder-generator.md # 编码者：生成者
    ├── coder-critic.md    # 编码者：批判者
    ├── coder-refiner.md   # 编码者：精炼者
    ├── reviewer.md        # 代码审查者
    └── tester.md          # 测试工程师

---
安装方式

git clone https://github.com/fengzi-spec/multi-agent-code.git
cp -r multi-agent-code 你的项目/.claude/skills/

然后在 Claude Code 里 /multi-agent-code "你的任务" 即可。

# Multi-Agent Code Collaboration

> Orchestrate multiple AI agents — Analyst, Architect, Coder, Reviewer, Tester — to build production-quality software through iterative handoffs, adversarial review, and configurable quality gates.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange)](https://claude.ai/code)

---

## Why Multi-Agent?

A single AI writing code is like a single developer working alone — it works, but misses things. Real software teams have:
- Different people catching different problems
- Fresh eyes on every code review
- Specialists for requirements and architecture
- Iterative improvement through collaboration

This skill models that. Each agent has a distinct **perspective** and **personality** — they don't just execute tasks, they bring different mindsets to the problem.

---

## Quick Start

Just type your task — **no flags required**:

```
/multi-agent-code "Write a Python REST API for a todo list app with user authentication"
```

The skill shows the **default configuration** and waits for your go-ahead:

```
╔══════════════════════════════════════════════════════════╗
║           Multi-Agent Code — 当前配置                     ║
╠══════════════════════════════════════════════════════════╣
║  1. 最大轮次:     10    (跑到10轮或触发停止条件时停)      ║
║  2. 可选角色:     无    (analyst / architect / tester)   ║
║  3. 审查时机:     每轮   (每轮 / 每N轮 / 最后)            ║
║  4. 停止条件:     critical (critical/high/medium时停)    ║
║  5. 自动/手动:    自动   (触发停止条件时自动停)            ║
║  6. 编程语言:     Python (自动检测)                       ║
║  7. 输出目录:     ./output                               ║
║                                                          ║
║  回复"go"使用默认配置，或者告诉我你想改的参数              ║
╚══════════════════════════════════════════════════════════╝
```

Reply **"go"** to accept the defaults, or change anything inline:
- `"轮次改成5，加上架构师"` → max_rounds=5, roles add architect
- `"每2轮审查，high时停止"` → review_strategy=milestone:2, stop_on=high

Then the pipeline runs. It stops when:
- **Review finds no issues** → quality achieved! ✅
- **Review finds issues >= stop severity** → problem found, stop early ⚠️
- **Max rounds reached** → finished all iterations

You can also skip the config screen entirely:
```
/multi-agent-code --defaults "Create a CLI tool"
/multi-agent-code --max-rounds 5 --roles analyst "Build an API"
```

---

## Architecture

```
User Request
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                  OPTIONAL PHASES                       │
│                                                       │
│  ┌──────────┐      ┌──────────────┐                   │
│  │ Analyst  │ ───→ │  Architect   │                   │
│  │ spec.md  │      │ architecture │                   │
│  └──────────┘      │    .md       │                   │
│                    └──────────────┘                   │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                CODING ITERATIONS                       │
│                                                       │
│  Round 1          Round 2          Round 3            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │Generator │───→│ Critic   │───→│ Refiner  │        │
│  │"Make it  │    │"Break it,│    │"Make it  │        │
│  │  work"   │    │ fix it"  │    │ excellent"│        │
│  └──────────┘    └──────────┘    └──────────┘        │
│       │               │               │              │
│       ▼               ▼               ▼              │
│    Review?         Review?         Review?            │
│   (per_round)     (per_round)     (per_round)         │
│   (batch)         (skip)          (batch)             │
│   (milestone)     (milestone)     (milestone)         │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                  OPTIONAL PHASES                       │
│  ┌──────────┐                                         │
│  │  Tester  │  ──→  Test suite + coverage report      │
│  └──────────┘                                         │
└──────────────────────────────────────────────────────┘
    │
    ▼
  Final Summary + All Artifacts
```

---

## Configuration

**Every parameter has a default. You can change any of them.** There are no presets — each setting is independent.

### All Parameters

| Parameter | Default | What It Does |
|-----------|---------|-------------|
| **最大轮次** | `10` | Max coding rounds before the pipeline stops. Can be any number. |
| **可选角色** | (none) | Enable `analyst`, `architect`, `tester`. `coder` + `reviewer` are always on. |
| **审查时机** | `per_round` | `per_round` (every round), `milestone:N` (every N rounds), `batch` (after final round). |
| **停止条件** | `critical` | If review finds issues at or above this severity, enter fix-attempt grace period. `critical` / `high` / `medium` / `never`. |
| **修复尝试** | `1` | How many coding rounds to attempt fixes after severity threshold is hit. `0` = stop immediately. |
| **自动/手动** | `true` | When fix attempts exhausted: `true` = auto-stop. `false` = pause and ask you. |
| **编程语言** | auto-detect | Inferred from your task. Override with `--language`. |
| **输出目录** | `./output` | Where code, docs, and reports are saved. |
| **上下文文件** | (none) | Existing files to modify or use as context. |

### Three Ways to Configure

**1. Interactive (default):** Just type your task. The skill shows all defaults. Reply "go" or change what you want.

**2. Flags in your message:**
```
/multi-agent-code --max-rounds 5 --roles architect --stop-on high "task"
```

| Flag | Example | Maps To |
|------|---------|---------|
| `--max-rounds N` / `--rounds N` | `--max-rounds 8` | Max coding rounds |
| `--roles X,Y` | `--roles analyst,tester` | Optional roles (analyst, architect, tester) |
| `--review X` | `--review batch` / `--review milestone:3` | Review strategy |
| `--stop-on X` | `--stop-on high` | Stop severity threshold |
| `--fix-attempts N` | `--fix-attempts 3` | Fix attempts before stopping (default 1) |
| `--auto` / `--no-auto` | `--no-auto` | Auto-stop or pause for confirmation |
| `--language X` | `--language Go` | Target programming language |
| `--files X,Y` | `--files src/main.py` | Existing files as context |
| `--output-dir X` | `--output-dir ./my-project` | Output directory |
| `--defaults` | `--defaults` | Skip config screen, use all defaults |

**3. Natural language:**
- "轮次改成8，加上架构师和测试" → max_rounds=8, add architect + tester
- "每3轮审查一次，high时停止，手动确认" → milestone:3, stop_on=high, auto=false
- "用Go写，最后再审查" → language=Go, review_strategy=batch

### Pipeline Stop Logic

The pipeline stops on **three conditions** (whichever happens first).
When severity threshold is hit, the Critic gets `fix_attempts` chances to fix before stopping:

```
Round 1: Coder → Review → 1 critical issue
         → 进入修复期 (1次机会) → 继续
Round 2: Coder(Critic修复) → Review → critical问题已修复 → ✅ 继续正常迭代
Round 3: Coder → Review → 0 issues → ✅ STOP (quality achieved!)

-- 或者修复失败的场景 --
Round 1: Coder → Review → 1 critical issue
         → 进入修复期 (fix_attempts=1) → 继续
Round 2: Coder(Critic修复) → Review → 仍有critical 
         → 修复机会用完 → ⚠️ STOP (severity threshold!)
```

### Role Descriptions

| Role | Required | What It Does |
|------|----------|-------------|
| **Analyst** | No | Translates vague requests into precise, structured requirements with acceptance criteria. |
| **Architect** | No | Designs component architecture, data models, API contracts, and technology choices. |
| **Coder** | **Yes** | Writes and iteratively improves code. Persona changes per round. |
| **Reviewer** | **Yes** | Systematic code audit. Every finding has severity, category, and fix suggestion. |
| **Tester** | No | Writes comprehensive test suite with coverage report. |

### Coder Personas Per Round

| Round | Persona | Mindset | Focus |
|-------|---------|---------|-------|
| 1 | **Generator** | "Make it work" | Functionality, speed, reasonable assumptions |
| 2 | **Critic** | "Break it, fix it" | Bugs, security, edge cases, error handling |
| 3 | **Refiner** | "Make it excellent" | Performance, design patterns, readability |
| 4+ | **Critic/Refiner** | Alternating | Continue hardening and polishing |

---

## Review Strategies Compared

| Strategy | How It Works | Best For | Token Cost |
|----------|-------------|----------|------------|
| `per_round` | Review after every coding round | Maximum quality, safety-critical code | Highest |
| `batch` | One review after all rounds | Quick prototypes, simple features | Lowest |
| `milestone:2` | Review every 2 rounds | Balance of quality and efficiency | Medium |

### Stop Severity Levels

| Level | Example | Pipeline Behavior |
|-------|---------|-------------------|
| `critical` | SQL injection, data loss, auth bypass | Stop by default |
| `high` | Wrong behavior, missing critical error handling | Stop if configured |
| `medium` | Code smell, minor bug, missing edge case | Logged, continues |
| `low` | Style nitpick, naming suggestion | Logged, continues |
| `never` | — | Pipeline never stops |

---

## Usage Examples

### Interactive (accept defaults)
```
/multi-agent-code "Write a function to validate email addresses"
```
→ Shows default config → Reply "go" → Pipeline runs with 10 max rounds, per_round review.

### Change specific params
```
/multi-agent-code "Build a payment processing microservice"
```
→ Shows defaults → Reply "轮次5，加上architect，high时停止" → Pipeline runs with your changes.

### All via flags (skip interactive)
```
/multi-agent-code --max-rounds 5 --roles architect,tester --stop-on high "Build a REST API in Go"
```
→ Skips config screen, runs directly with specified params.

### Quick one-shot
```
/multi-agent-code --max-rounds 1 --review batch "Shell script to backup PostgreSQL to S3"
```
→ One coder, one review at the end. Fastest path.

### Modify existing codebase
```
/multi-agent-code --files src/auth.py,src/models.py "Add OAuth2 social login support"
```
→ Agents see existing files, modify them in place through the iteration rounds.

---

## Output Structure

```
output/
├── requirements.md          # Your original request
├── spec.md                  # Analyst output (if enabled)
├── architecture.md          # Architect output (if enabled)
├── change_log.md            # Latest coder's change log
├── open_concerns.md         # Issues the coder flagged for attention
├── [your code files]        # The actual code
├── reviews/
│   ├── review_round1.md     # Per-round review reports
│   ├── review_round2.md
│   └── review_final.md      # Batch review (if batch strategy)
├── tests/                   # Tester output (if enabled)
│   └── [test files]
└── .pipeline/
    ├── state.json           # Pipeline progress (for resume)
    └── config.json          # Resolved parameters
```

---

## Workflow Recipes

### "Quick prototype"
```
--max-rounds 1 --review batch
```
One coder, one review. ~2 agent calls. Fast.

### "Standard feature" (default)
```
Just use the defaults: max 10 rounds, per_round review, stop on critical.
```
Generator → Critic → Refiner cycling with review each round. Stops when clean or on critical issues.

### "Mission-critical system"
```
--roles analyst,architect,tester --stop-on high --max-rounds 15
```
All 5 roles, stops on any high-severity finding, up to 15 refinement rounds.

### "Safe exploration"
```
--max-rounds 3 --stop-on medium --no-auto
```
Stops and asks you on any medium+ issue. Good when you want tight control.

### "Refactor existing code"
```
--files src/**/*.py "Refactor the DB layer to Repository pattern"
```
Agents work on your existing files through the iteration rounds.

---

## How Agent Handoffs Work

Each coder round produces:

1. **Modified code files** — the complete, working codebase
2. **Change log** — what changed, why, and design decisions
3. **Open concerns** — things the next coder should know or watch for

The next coder sees:
- The full current codebase (not just diffs)
- What the previous coder was thinking (change log + open concerns)
- Review findings that need addressing (if review ran)

This creates a **thinking-out-loud trail** so each agent builds on genuine understanding, not just guessing what the previous agent intended.

---

## Limitations

- **Sequential execution**. Each agent waits for the previous one — no parallel coding (by design, since later coders need earlier output).
- **File-system based**. State passes through files, not memory. Survives interruptions but adds I/O overhead.
- **LLM-dependent quality**. The skill provides structure and prompting; the underlying model determines code quality.
- **No real-time human-in-the-loop editing**. You can pause (`--no-auto`) to review, but you can't edit code mid-pipeline and resume.

---

## Installation

1. Copy the `multi-agent-code/` directory into your Claude Code skills directory:

```
# If using project-level skills
cp -r multi-agent-code/ your-project/.claude/skills/

# If using user-level skills
cp -r multi-agent-code/ ~/.claude/skills/
```

2. The skill is auto-discovered. Invoke with `/multi-agent-code`.

---

## FAQ

**Q: When should I enable the Analyst?**
A: When your requirements are vague or complex. The analyst decomposes fuzzy ideas into testable specs. For simple, well-defined tasks, skip it.

**Q: When should I enable the Architect?**
A: When the system has multiple components, a database, or external APIs. For single-file scripts, skip it.

**Q: What's the difference between Critic and Reviewer?**
A: The **Critic** is a coder — it finds problems AND fixes them. The **Reviewer** finds problems AND reports them (with fix suggestions). The Critic is the fixer; the Reviewer is the auditor.

**Q: Why 3 coder personas instead of 1?**
A: A single coder reviewing its own code has blind spots. Three different perspectives (build fast → break things → polish) cover more ground.

**Q: How much does this cost in tokens?**
A: Each agent call costs roughly the same as a normal Claude interaction. A 2-round pipeline with review is ~4 agent calls. A full pipeline with analyst, architect, 3 coding rounds, and tester is ~7-8 agent calls.

**Q: Can I use this with any language?**
A: Yes. The prompts are language-agnostic. Specify with `--language`.

**Q: What if an agent fails mid-pipeline?**
A: The orchestrator retries once, then falls back gracefully. Pipeline state is saved to disk, so you can resume.

---

## Contributing

Improvements to prompts, new personas, and bug reports are welcome. The `prompts/` directory is designed to be customized — adjust the tone, checklist, or focus areas to match your team's standards.

---

## License

MIT — see [LICENSE](LICENSE).
