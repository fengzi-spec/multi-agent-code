

# 🤖 Multi-Agent Code Collaboration

> **5 AI agents. One pipeline. Production-quality code.**
>
> Analyst → Architect → Coder → Reviewer → Tester. Working together like a real dev team.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange)](https://claude.ai/code)
[![GitHub stars](https://img.shields.io/github/stars/fengzi-spec/multi-agent-code?style=social)](https://github.com/fengzi-spec/multi-agent-code)
[中文文档](README_CN.md)

> ⭐ **If you find this useful, please star this repo!** It helps others discover it.

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
║  1. 最大轮次:     5     (跑到5轮或触发停止条件时停)       ║
║  2. 可选角色:     无    (analyst / architect / tester)   ║
║  3. 审查时机:     每轮   (每轮 / 每N轮 / 最后)            ║
║  4. 停止条件:     critical (critical/high/medium时停)    ║
║  5. 修复尝试:     1次    (发现严重问题后给几次修复机会)    ║
║  6. 自动/手动:    自动   (修复失败后自动停还是问你)        ║
║  7. 编程语言:     (自动检测)                              ║
║  8. 输出目录:     . (当前项目)                           ║
║  9. 目标评分:     关闭   (达到X分建议达标，0=关闭)        ║
║ 10. 评分稳定性:   1轮    (连续N轮达标才标记稳定)           ║
║ 11. 评分权重:     balanced (balanced/security-first/      ║
║                          performance-first/自定义)        ║
║                                                          ║
║  回复"go"使用默认配置，或者告诉我你想改的参数              ║
╚══════════════════════════════════════════════════════════╝
```

Reply **"go"** to accept the defaults, or change anything inline:
- `"轮次改成5，加上架构师"` → max_rounds=5, roles add architect
- `"每2轮审查，high时停止"` → review_strategy=milestone:2, stop_on=high

Then the pipeline runs. It stops when:
- **Validation passes + no critical/high findings** → quality achieved! ✅
- **Severity threshold hit + fix attempts exhausted** → can't fix, stop ⚠️
- **Progress stalls for 2 rounds** → no improvement 🛑
- **Max rounds reached** → finished all iterations

> 💡 Agents work **in-place** in your project. Code goes to `src/`, `tests/`, etc. Only `.pipeline/` is added. Reviewer scores are advisory diagnostics — **executable validation (build/lint/test)** is the real quality gate.

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
│  Validate/Test   Validate/Test   Validate/Test        │
│       │               │               │              │
│       ▼               ▼               ▼              │
│    Review?         Review?         Review?            │
│   (per_round)     (per_round)     (per_round)         │
│   (batch)         (skip)          (batch)             │
│   (milestone)     (milestone)     (milestone)         │
│  Tester writes or updates tests inside a round when   │
│  behavior changes, a regression is fixed, or coverage │
│  has a demonstrated gap. Existing tests always run.   │
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
| **最大轮次** | `5` | Max coding rounds before the pipeline stops. Can be any positive number. |
| **可选角色** | (none) | Enable `analyst`, `architect`, `tester`. `coder` + `reviewer` are always on. |
| **审查时机** | `per_round` | `per_round` (every round), `milestone:N` (every N rounds), `batch` (after final round). |
| **停止条件** | `critical` | If review finds issues at or above this severity, enter fix-attempt grace period. `critical` / `high` / `medium` / `never`. |
| **修复尝试** | `1` | How many coding rounds to attempt fixes after severity threshold is hit. `0` = stop immediately. |
| **自动/手动** | `true` | When fix attempts exhausted: `true` = auto-stop. `false` = pause and ask you. |
| **编程语言** | auto-detect | Inferred from your task. Override with `--language`. |
| **输出目录** | `.` (current project) | Where code is generated. Agents work in-place by default. Change to `./output` for sandbox mode. |
| **上下文文件** | (none) | Existing files to modify or use as context. |
| **目标评分** | `0` (off) | Advisory score target used to highlight progress. It never overrides validation. |
| **评分稳定性** | `1` | Consecutive rounds above the advisory target before marking the score stable. |
| **评分权重** | `balanced` | Weight preset: `balanced`, `security-first`, `performance-first`, or custom `security:3,performance:0.5`. |

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
| `--target-score X` | `--target-score 8.5` | Target composite score |
| `--score-stability N` | `--score-stability 2` | Consecutive rounds to confirm score |
| `--score-weights X` | `--score-weights security-first` | Weight preset for dimensions |
| `--defaults` | `--defaults` | Skip config screen, use all defaults |

**3. Natural language:**
- "轮次改成8，加上架构师和测试" → max_rounds=8, add architect + tester
- "每3轮审查一次，high时停止，手动确认" → milestone:3, stop_on=high, auto=false
- "用Go写，最后再审查" → language=Go, review_strategy=batch

### Pipeline Stop Logic

The pipeline stops on **four conditions** (whichever happens first): quality gates pass, severity fix attempts are exhausted, progress stalls for two rounds, or max rounds are reached.
When severity threshold is hit, the Critic gets `fix_attempts` chances to fix before stopping:

```
Round 1: Coder → Review → 1 critical issue
         → 进入修复期 (1次机会) → 继续
Round 2: Coder(Critic修复) → Review → critical问题已修复 → ✅ 继续正常迭代
Round 3: Coder → validation passes → Review finds no critical/high → ✅ STOP

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

## Multi-Dimensional Code Scoring 🎯

Each review round, the Reviewer scores code across **6 independent dimensions** (1-10 each) and computes a weighted composite:

| Dimension | What's Scored | Example |
|-----------|--------------|---------|
| **Security** | Injection, XSS, auth bypass, secret exposure | "Parameterized queries in place, but CSRF protection missing" |
| **Correctness** | Logic errors, concurrency, edge cases | "Core logic is sound, but race condition on balance check" |
| **Performance** | Algorithm complexity, N+1 queries, resources | "N+1 query in get_orders — use JOIN" |
| **Maintainability** | Readability, DRY, patterns, docs | "Clean overall, but parse_date has 5 boolean params" |
| **Robustness** | Error handling, validation, retry/timeout | "External calls lack timeout and retry" |
| **Completeness** | Spec coverage, acceptance criteria | "All P0 requirements met, 2 P1 items missing" |

**Composite = Σ(dimension × weight) / Σ(weights)**. Default: all weights = 1.0.

### Weight Presets

```
balanced:          all dimensions = 1.0  (default)
security-first:    security = 2.0        (auth/payment/healthcare)
performance-first: performance = 2.0     (high-throughput/low-latency)
```

Custom: `--score-weights security:3,performance:0.5`

### Score Trend Visualization

The pipeline shows quality evolution at completion:

```
📈 Score Trend:

  R1: ██████░░░░ 6.2  Generator   Sec:5 Cor:7 Perf:6
  R2: ████████░░ 7.8  Critic      Sec:8 Cor:8 Perf:7
  R3: █████████░ 9.1  Refiner     Sec:9 Cor:9 Perf:9

  Start: 6.2 → Final: 9.1 → +2.9 (+47%)
```

### Advisory Score Target

```
/multi-agent-code --target-score 8.5 --score-stability 2 "Build an API"
```

→ Highlights when the composite score is ≥ 8.5 for 2 consecutive rounds. Completion still requires executable validation, satisfied acceptance criteria, and no unresolved critical/high findings.

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
→ Shows default config → Reply "go" → Pipeline runs with 5 max rounds, per_round review.

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

Agents work **in-place within your project** — no isolated `output/` sandbox:

```
your-project/                       # ← Agents work right here
├── src/                            # Application code
├── tests/                          # Tests
├── ...                             # Existing project files
└── .pipeline/                      # Pipeline metadata
    ├── project.json                # Discovered validation commands
    ├── project_tree.txt            # Project structure snapshot
    ├── config.json                 # Resolved parameters
    └── tasks/
        └── <task-id>/
            ├── request.md
            ├── spec.md             # If analyst ran
            ├── architecture.md     # If architect ran
            ├── baseline.json
            ├── baseline.patch
            ├── state.json
            ├── validation.json
            ├── change_log.md
            ├── open_concerns.md
            └── reviews/
```

> 💡 **`.pipeline/` is the only new directory.** Add it to `.gitignore`. All pipeline metadata lives here — your project stays clean.

---

## Workflow Recipes

### "Standard feature" (default)
```
/multi-agent-code "Build a user registration API"
```
Agents work directly in your project. Code lands in `src/`, tests in `tests/`. Max 5 rounds by default, stopping when the quality gates pass.

### "Mission-critical system"
```
/multi-agent-code --roles analyst,architect,tester --stop-on high --max-rounds 15 "Build a payment service"
```
All 5 roles, 15 refinement rounds max.

### "Modify existing code"
```
/multi-agent-code "Add OAuth2 social login to the auth module"
```
Agents auto-discover `src/auth.py` and modify it in-place. No manual file selection needed.

### "Advisory score target"
```
/multi-agent-code --target-score 8.5 --score-stability 2 "Refactor the DB layer"
```
Highlights when code hits 8.5+ for 2 consecutive rounds; executable quality gates still decide completion.

### "Sandbox mode" (when you want isolation)
```
/multi-agent-code --output-dir ./experiment "Try rewriting in Rust"
```
Code goes to `./experiment/` instead of your project.

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

This repository provides two entry points: Claude Code uses `CLAUDE.md`, while Codex uses the standard `SKILL.md`. Both share the role instructions under `prompts/`; the Codex package also includes `agents/openai.yaml` metadata.

### Install for Codex

Copy the complete `multi-agent-code` directory into your Codex skills directory, then invoke it with a prompt such as:

```text
Use $multi-agent-code to implement this request in the current project and verify it through iterative coding, review, and test rounds.
```

The skill uses real subagents when the host provides them. Otherwise it performs explicitly separated role passes with one model and discloses that the roles are simulated.

### Markdown versus scripts

- `SKILL.md` / `CLAUDE.md` define the workflow interpreted by the AI host.
- `prompts/` define role-specific coding and review behavior.
- `scripts/pipeline_state.py` deterministically creates task IDs, captures Git baselines, atomically updates state, and validates resume data.
- The host product performs file edits, command execution, and subagent calls; this repository is not a standalone code-generation service.

The state helper uses only the Python standard library. The pattern below currently matches `scripts/test_pipeline_state.py`:

```bash
python -m unittest discover -s scripts -p "test_*.py" -v
```

### Optional helpers

**1. Request file (recommended)**

Store the complete request in a UTF-8 file to preserve multiline formatting and keep it out of shell history and process arguments:

```bash
python scripts/pipeline_state.py init --project ./my-project --request-file ./task.md --max-rounds 8
```

Five is only the default round limit. Set `--max-rounds` to any positive integer, or tell the skill “run at most 8 rounds.” `--request` remains available for short, non-sensitive requests.

**2. Dry run**

Add `--dry-run` to print the planned task ID, directory, and files without modifying the target project:

```bash
python scripts/pipeline_state.py init --project ./my-project --request-file ./task.md --max-rounds 8 --dry-run
```

Remove `--dry-run` after checking the plan to perform initialization.

**3. Minimal example project**

`examples/calculator-validation/` is a copyable calculator fixture with runnable tests. Its task asks the skill to add input validation and regression coverage, demonstrating the complete iterative workflow. Copy it to a temporary project instead of editing the bundled fixture.

```bash
python -m unittest discover -s examples/calculator-validation -p "test_*.py" -v
```

### Install for Claude Code

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
