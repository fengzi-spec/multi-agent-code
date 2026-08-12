---
name: multi-agent-code
description: >
  Orchestrate multiple AI agents (Analyst, Architect, Coder, Reviewer, Tester)
  to collaborate on software development through iterative coding rounds with
  structured handoffs and configurable review strategies. Use when the user
  wants multi-agent software development, agent collaboration, iterative code
  generation, automated code review with multiple agents, multi-role development
  pipeline, AI-powered code review, or wants different AI personas to write
  and review code together.
---

# Multi-Agent Code Collaboration

You are an **orchestrator** managing a pipeline of AI agents that collaborate
to produce high-quality software. Your job is to help the user configure the
pipeline, then execute it — spawning agents, managing state, and handling errors.

---

## Phase 0: Configuration

### 0a. Extract the Task

The user's task is the core content — what they want built. Everything else
is configuration. Extract the task description from whatever is not a flag.

### 0b. All Parameters (every one has a default, every one can be changed)

| Parameter | Default | What It Does |
|-----------|---------|-------------|
| `max_rounds` | `10` | Maximum coding rounds. Pipeline stops when this is reached OR when stop condition triggers. |
| `roles` | `coder,reviewer` | Roles enabled. `coder` and `reviewer` are mandatory. Optional: `analyst`, `architect`, `tester`. |
| `review_strategy` | `per_round` | When review runs: `per_round` (every round), `milestone:N` (every N rounds), `batch` (only after final round). |
| `stop_on_severity` | `critical` | **Early stop trigger.** If review finds issues at or above this severity, the pipeline enters the fix-attempt grace period (see `fix_attempts`). Options: `critical`, `high`, `medium`, `never`. |
| `fix_attempts` | `1` | How many additional coding rounds to attempt fixes after severity threshold is first hit. If issues persist at that severity after these rounds, the pipeline stops. 0 = stop immediately with no fix attempt. |
| `auto_continue` | `true` | When the stop condition is final (fix_attempts exhausted): `true` = stop and report automatically, `false` = pause and ask the user what to do. |
| `language` | auto-detect | Target programming language. Inferred from the task if not specified. |
| `output_dir` | `./output` | Where all code, docs, and reports are saved. |
| `context_files` | (none) | Existing files to use as context or modify in-place. |

### 0c. Parameter Sources (priority order)

Parameters can come from three sources. Later sources override earlier ones:

1. **Defaults** — the values in the table above
2. **User's message** — anything the user typed alongside their task:
   - `--max-rounds 5` / `--rounds 5` / "5轮" → max_rounds
   - `--roles analyst,tester` / "加上架构师" → roles
   - `--review per_round` / "每轮审查" / "最后审查" → review_strategy
   - `--stop-on high` / "严重问题停止" → stop_on_severity
   - `--fix-attempts N` / "修复N轮" / "给N次修复机会" → fix_attempts
   - `--auto` / `--no-auto` / "自动" / "手动确认" → auto_continue
   - `--language Python` / "用Go写" → language
   - `--files x.py,y.py` → context_files
   - `--output-dir ./src` → output_dir
   - `--defaults` / "默认配置" / "全部默认" → use all defaults, skip step 0d
3. **User's changes** in step 0d below

### 0d. Present Defaults, Let User Adjust

If the user already said `--defaults` or "全部默认", skip this step.

Otherwise, **show the current configuration** (defaults merged with anything the user specified) and let them change anything:

```
╔══════════════════════════════════════════════════════════╗
║           Multi-Agent Code — 当前配置                     ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
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
║  例如: "轮次改成5，加上架构师，high时停止"                 ║
╚══════════════════════════════════════════════════════════╝
```

The user can reply with:
- **"go" / "开始" / "ok"** — accept the current config and start
- **Specific changes** — e.g. "轮次5，加上architect和tester，每2轮审查，high停止，手动确认" → update those params in the config, show the updated table, then start
- **More questions** — answer them

**Rules for showing this:**
- If the user specified ALL parameters explicitly in their first message, you can skip this and proceed directly
- If anything is using a default, show this so the user knows what will happen
- Keep it one screen. Don't paginate.

### 0e. Coder Persona Rotation

Coder persona for each round (used in Phase 3):

| Round | Persona | Prompt File |
|-------|---------|-------------|
| 1 | Generator | `prompts/coder-generator.md` |
| 2 | Critic | `prompts/coder-critic.md` |
| 3 | Refiner | `prompts/coder-refiner.md` |
| 4 | Critic | `prompts/coder-critic.md` |
| 5 | Refiner | `prompts/coder-refiner.md` |
| ... | Alternating Critic/Refiner | pattern continues |

---

## Phase 1: Initialization

1. Create `{output_dir}/` and `{output_dir}/.pipeline/`.
2. Write `.pipeline/config.json` with all resolved parameters.
3. Write `requirements.md` with the user's task description.
4. Write `.pipeline/state.json`:
   ```json
   {
     "phase": "init",
     "current_round": 0,
     "max_rounds": 10,
     "rounds_completed": [],
     "stop_reason": null,
     "severity_hit_round": null,
     "fix_rounds_used": 0,
     "pipeline_started": "<ISO timestamp>"
   }
   ```

---

## Phase 2: Requirements Analysis (only if `analyst` in roles)

1. Update state: `"phase": "analysis"`.
2. Read `prompts/analyst.md`.
3. Spawn agent (subagent_type: "general-purpose"):
   - Description: "Analyst: requirements analysis"
   - Prompt: role prompt + user's task + context_files
4. Wait for completion. Verify `{output_dir}/spec.md` exists. Retry once if not.
5. Update state: `"phase": "architecture"` or `"phase": "coding"`.

---

## Phase 3: Architecture Design (only if `architect` in roles)

1. Update state: `"phase": "architecture"`.
2. Read `prompts/architect.md`.
3. Spawn agent with role prompt + spec.md (or task if no analyst) + context_files.
   - Description: "Architect: system design"
4. Wait for completion. Verify `{output_dir}/architecture.md` exists. Retry once if not.
5. Update state: `"phase": "coding"`.

---

## Phase 4: Coding Loop (the core)

```
For each round R from 1 to max_rounds:
    
    ┌─────────────────────────────────────────────┐
    │ 4a. Select persona & spawn coder            │
    │ 4b. Validate coder output                   │
    │ 4c. Review decision → maybe run reviewer    │
    │ 4d. Check stop conditions                   │
    │     ├─ severity threshold met? → STOP EARLY │
    │     ├─ review is clean (0 issues)? → STOP   │
    │     └─ R == max_rounds? → STOP (max rounds) │
    │ 4e. Update state, continue loop             │
    └─────────────────────────────────────────────┘
```

### 4a. Spawn Coder

1. Determine persona from the rotation table (0e).
2. Read the corresponding prompt file from `prompts/`.
3. Collect current code from `{output_dir}/` (skip `.pipeline/`, `reviews/`, `*.md`).
4. Compose prompt: role prompt + task context (task, spec, architecture, current code, previous change_log, previous open_concerns, latest review findings).
5. Spawn agent:
   - Description: `"Coder R{R}: {persona}"`
   - subagent_type: "general-purpose"
6. Wait for completion.

### 4b. Validate Output

1. Check for code files in `{output_dir}/`.
2. Check `{output_dir}/change_log.md` exists.
3. Check `{output_dir}/open_concerns.md` exists.
4. Missing items? Ask agent to retry once. Second failure: warn and continue.

### 4c. Review Decision

```
should_review = false
if review_strategy == "per_round":
    should_review = true
elif review_strategy == "batch":
    should_review = false   // only after the final round
elif review_strategy matches "milestone:N":
    should_review = (R % N == 0)
```

If `should_review` is true, run the reviewer now (Phase 5a).

### 4d. Check Stop Conditions (CRITICAL)

After review (or after coding if no review this round), evaluate in this order.

**Tracking state** (maintain across rounds):
- `severity_hit_round`: the round where the severity threshold was first hit (null if not hit yet)
- `fix_rounds_used`: how many fix-attempt rounds have been used since the hit

#### Condition 1: Severity Threshold Met → Enter Fix-Attempt Grace Period

If review ran and found issues at or above `stop_on_severity`:

```
severity_levels = { critical: 4, high: 3, medium: 2, low: 1, info: 0 }
threshold = severity_levels[stop_on_severity]  // "never" → Infinity
worst_finding = max severity across all findings

if worst_finding >= threshold:
    
    if fix_attempts == 0:
        // No grace period — stop immediately
        STOP_REASON = "severity_threshold"
        Report and stop (see "Final Stop" below).
    
    else if severity_hit_round is None:
        // First time hitting threshold — start grace period
        severity_hit_round = R
        fix_rounds_used = 0
        Report: "Round {R}: {severity} issues found. Coder has {fix_attempts} round(s) to fix."
        Continue to next round (the Critic/Refiner will try to fix).
    
    else:
        // Still above threshold after fix attempt
        fix_rounds_used += 1
        
        if fix_rounds_used >= fix_attempts:
            // Fix attempts exhausted — stop
            STOP_REASON = "severity_threshold"
            Report: "Round {R}: {severity} issues persist after {fix_attempts} fix attempt(s). Stopping."
            Execute "Final Stop" below.
        else:
            // More fix attempts remain
            remaining = fix_attempts - fix_rounds_used
            Report: "Round {R}: {severity} issues still present. {remaining} fix attempt(s) remaining."
            Continue to next round.

else:
    // Review found issues but none above threshold
    // Reset the grace period if it was active (code improved!)
    if severity_hit_round is not None:
        Report: "Round {R}: issues have dropped below {stop_on_severity} threshold. Grace period reset."
        severity_hit_round = None
        fix_rounds_used = 0
```

**Final Stop** (when fix_attempts exhausted or fix_attempts==0):

```
If auto_continue == true:
    Stop pipeline. Show summary.
    "Pipeline stopped at round {R}: {severity} severity issues persist."

If auto_continue == false:
    Present findings to user.
    Ask: "Continue fixing (next round), stop here, or ignore and finish?"
    - Continue → override stop, reset grace counter, continue
    - Stop → end pipeline
    - Ignore → skip remaining reviews, finish remaining rounds
```

#### Condition 2: Review Clean → STOP EARLY (Quality Achieved)

If review ran and found **zero issues** (no findings at all):

```
STOP_REASON = "quality_achieved"
Pipeline stops successfully.
"Pipeline complete at round {R}: code passes review with no issues."
```

#### Condition 3: Max Rounds Reached → STOP

If R == max_rounds (we just finished the last round):

```
STOP_REASON = "max_rounds"
Pipeline stops.
"Max rounds ({max_rounds}) reached."
If review found unresolved issues: mention them in the summary.
```

#### Condition 4: Continue

If none of the above triggered, continue to the next round.

### 4e. Update State & Loop

```
state.current_round = R
state.rounds_completed.push(R)
if review ran: state.last_review_round = R
Continue to round R+1
```

---

## Phase 5: Review Process

### 5a: Single Round Review

1. Read `prompts/reviewer.md`.
2. Collect all code files from `{output_dir}/`.
3. Compose prompt: role prompt + code + spec + architecture + previous review reports.
4. Spawn agent:
   - Description: `"Reviewer: round {R}"`
   - subagent_type: "general-purpose"
5. Wait for completion.
6. Verify `{output_dir}/reviews/review_round{R}.md` was created.
7. Parse findings: count critical, high, medium, low issues.
8. Report to user: "Round {R} review: {C} critical, {H} high, {M} medium, {L} low."
9. Return findings for stop condition check.

### 5b: Batch Review (only if `review_strategy == "batch"`)

After the coding loop ends (Phase 4 complete):
1. Run review once on the final codebase.
2. Write to `{output_dir}/reviews/review_final.md`.
3. This is purely informational — no stop conditions apply (pipeline is already done).

---

## Phase 6: Testing (only if `tester` in roles)

1. Update state: `"phase": "testing"`.
2. Read `prompts/tester.md`.
3. Spawn agent with final code + spec.
   - Description: "Tester: writing tests"
   - subagent_type: "general-purpose"
4. Verify test files were created.

---

## Phase 7: Final Summary

```
╔══════════════════════════════════════════════════════════╗
║              Pipeline Complete                           ║
╠══════════════════════════════════════════════════════════╣
║ 停止原因:  质量达标 (审查无问题)                          ║
║ 完成轮次:  4 / 10                                        ║
║ 流水线:    generator → critic → refiner → critic          ║
║ 审查:      每轮                                          ║
╠══════════════════════════════════════════════════════════╣
║ 📁 输出: {output_dir}/                                   ║
║   ├── requirements.md                                    ║
║   ├── spec.md                 (analyst output)           ║
║   ├── architecture.md         (architect output)         ║
║   ├── [code files]                                       ║
║   ├── change_log.md                                      ║
║   ├── open_concerns.md                                   ║
║   └── reviews/                                           ║
║       ├── review_round1.md                               ║
║       ├── review_round2.md                               ║
║       ├── review_round3.md                               ║
║       └── review_round4.md                               ║
╠══════════════════════════════════════════════════════════╣
║ 📊 统计:                                                 ║
║   总轮次:     4 轮执行 / 10 轮最大                        ║
║   发现问题:   8 (0 critical, 1 high, 5 medium, 2 low)    ║
║   已修复:     8                                           ║
║   最终审查:   ✅ 0 issues — 代码通过审查                  ║
╠══════════════════════════════════════════════════════════╣
║ ⚠️  遗留关注点:                                          ║
║   - [from open_concerns.md]                              ║
╚══════════════════════════════════════════════════════════╝
```

---

## State Management

All state at `{output_dir}/.pipeline/`:

```
{output_dir}/
├── .pipeline/
│   ├── state.json       # Phase, round, stop_reason
│   └── config.json      # All resolved parameters
├── requirements.md       # Original task
├── spec.md               # Analyst output
├── architecture.md       # Architect output
├── change_log.md         # Latest coder change log
├── open_concerns.md      # Latest coder concerns
├── [code files...]       # The actual code
└── reviews/
    ├── review_round1.md
    ├── review_round2.md
    └── ...
```

---

## Agent Communication

When composing a prompt for any agent, include:

```
## ROLE PROMPT
[full content of the appropriate prompts/*.md file]

## TASK CONTEXT
### Task
[user's requirements.md]

### Spec (if analyst ran)
[spec.md content]

### Architecture (if architect ran)
[architecture.md content]

### Current Code
[all code files from {output_dir}/ — or "Empty, you are writing the first version"]

### Previous Change Log
[change_log.md — or "Round 1, no previous changes"]

### Open Concerns
[open_concerns.md — or "None"]

### Review Findings to Address
[latest review report — or "No pending review findings"]

## OUTPUT INSTRUCTIONS
- Write code files to {output_dir}/
- Write change log to {output_dir}/change_log.md
- Write open concerns to {output_dir}/open_concerns.md
- Follow your role's output format exactly
```

---

## Error Handling

**Agent failure** (API error, timeout, no output):
1. Retry once with same prompt.
2. Second failure:
   - Coder round 1: abort (no code to fall back on).
   - Coder round N>1: use round N-1 code, flag in summary.
   - Reviewer: skip review, warn user.
   - Analyst/Architect/Tester: skip phase, continue.

**Missing output files:**
1. Tell agent what's missing, retry once.
2. Second failure: apply fallback above.

**User interruption mid-pipeline:**
- `state.json` records last completed round.
- On restart, check for existing state: "Found partial pipeline at round {N}. Resume or restart?"

**Empty context_files:**
- Verify each file exists. Warn and skip missing files.

**Output directory already has content:**
- Warn: "Output directory exists. Files may be overwritten. Continue?"

---

## Quick Reference

| Agent | Description label |
|-------|------------------|
| Analyst | "Analyst: requirements analysis" |
| Architect | "Architect: system design" |
| Coder R1 | "Coder R1: generator" |
| Coder R2 | "Coder R2: critic" |
| Coder R3 | "Coder R3: refiner" |
| Coder RN | "Coder R{N}: {persona}" |
| Reviewer | "Reviewer: round {N}" |
| Batch Reviewer | "Reviewer: final review" |
| Tester | "Tester: writing tests" |

---

## Key Rules

1. **max_rounds can be any number.** User picks it. Default is 10.
2. **Pipeline stops early on two conditions:**
   - Severity threshold met (review found issues >= stop_on_severity)
   - Quality achieved (review found zero issues — code is done)
3. **Pipeline always stops at max_rounds** regardless of remaining issues.
4. **Coders hand off to each other.** Each round's coder sees the previous round's full code + change log + concerns + review findings.
5. **The Critic persona FIXES problems** (not just reports them). The Reviewer REPORTS problems.
6. **All parameters are independent with defaults.** User changes what they want, keeps defaults for the rest.
7. **State survives interruptions.** Always check for existing state.json before starting.
