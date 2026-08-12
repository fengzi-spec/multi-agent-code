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

## Reliability Rules (override conflicting instructions below)

1. Preserve pre-existing user changes. Inspect version-control status before editing, record the baseline under `.pipeline/`, and never reset or overwrite unrelated work.
2. Keep project-level state separate from task history. Store each new request under `.pipeline/tasks/<task-id>/`; resume an unfinished matching task, but never overwrite a completed task's requirements or evidence.
3. Select relevant files with repository search and dependency/call-site tracing. Give coders the smallest coherent context and give reviewers the current diff plus affected paths. Do not resend the entire repository by default.
4. After every coding or test-writing round, run applicable build, lint, type-check, security, and test commands. Record exact commands and exit codes. Any failure must return to a Critic repair round.
5. Treat executable validation as the primary quality gate. Reviewer scores are advisory. Do not declare success solely because a reviewer found zero issues or a target score was reached.
6. Declare quality achieved only when acceptance criteria are satisfied, applicable checks pass, no accepted critical/high finding remains, and the final diff stays in scope. If checks cannot run, use `verified_with_limitations` rather than claiming full success.
7. Testing is part of the coding loop, not a terminal artifact phase. Run new tests immediately, repair failures, and rerun the exposing checks.
8. Use real subagents only when the host supports them. Otherwise perform separated sequential role passes and disclose that the roles were simulated.
9. Stop when quality gates pass, maximum rounds are reached, progress stalls for two rounds, or further work requires user authority or a material product decision.

For Codex-compatible packaging and the canonical cross-product workflow, use `SKILL.md`. The detailed role prompts in `prompts/` are shared by both entry points.

---

## Phase 0: Configuration

### 0a. Extract the Task

The user's task is the core content — what they want built. Everything else
is configuration. Extract the task description from whatever is not a flag.

### 0b. All Parameters (every one has a default, every one can be changed)

| Parameter | Default | What It Does |
|-----------|---------|-------------|
| `max_rounds` | `5` | Maximum coding rounds. Pipeline stops when this is reached OR when stop condition triggers. |
| `roles` | `coder,reviewer` | Roles enabled. `coder` and `reviewer` are mandatory. Optional: `analyst`, `architect`, `tester`. |
| `review_strategy` | `per_round` | When review runs: `per_round` (every round), `milestone:N` (every N rounds), `batch` (only after final round). |
| `stop_on_severity` | `critical` | **Early stop trigger.** If review finds issues at or above this severity, the pipeline enters the fix-attempt grace period (see `fix_attempts`). Options: `critical`, `high`, `medium`, `never`. |
| `fix_attempts` | `1` | How many additional coding rounds to attempt fixes after severity threshold is first hit. If issues persist at that severity after these rounds, the pipeline stops. 0 = stop immediately with no fix attempt. |
| `auto_continue` | `true` | When the stop condition is final (fix_attempts exhausted): `true` = stop and report automatically, `false` = pause and ask the user what to do. |
| `language` | auto-detect | Target programming language. Inferred from the task if not specified. |
| `output_dir` | `.` (current directory) | Where code is generated. Defaults to the current project — agents work in-place like a real developer. Change to `./output` or any path for sandbox mode. |
| `context_files` | (none) | Existing files to use as context or modify in-place. |
| `target_score` | `0` (disabled) | Advisory composite score target. It highlights progress but never overrides executable quality gates. 0 = disabled. |
| `score_stability` | `1` | Consecutive rounds meeting the advisory target before highlighting stable score quality. |
| `score_weights` | `balanced` | Dimension weight preset: `balanced`, `security-first`, `performance-first`, or custom like `security:3,performance:0.5`. |

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
   - `--target-score 8.5` / "评分达到8.5时提醒" → target_score
   - `--score-stability 2` / "连续2轮达标才停" → score_stability
   - `--score-weights security-first` / "安全优先" → score_weights
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
║  1. 最大轮次:     5     (跑到5轮或触发停止条件时停)       ║
║  2. 可选角色:     无    (analyst / architect / tester)   ║
║  3. 审查时机:     每轮   (每轮 / 每N轮 / 最后)            ║
║  4. 停止条件:     critical (critical/high/medium时停)    ║
║  5. 修复尝试:     1次    (发现严重问题后给几次修复机会)    ║
║  6. 自动/手动:    自动   (修复失败后自动停还是问你)        ║
║  7. 编程语言:     (自动检测)                              ║
║  8. 输出目录:     . (当前项目)                           ║
║  9. 目标评分:     关闭   (达到X分时提示，0=关闭)          ║
║ 10. 评分稳定性:   1轮    (连续N轮达标才标记稳定)           ║
║ 11. 评分权重:     balanced (balanced/security-first/      ║
║                          performance-first/自定义)        ║
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

1. If `output_dir` is `.` (current directory), skip creation — agents work in-place within the existing project. Otherwise, create `{output_dir}/`.
2. **Preview deterministic task state before creating pipeline directories.** Put the exact request in a temporary UTF-8 file outside the target project and run `python <skill-dir>/scripts/pipeline_state.py init --project {output_dir} --request-file <request-file> --max-rounds {max_rounds} --dry-run`. This must not create `.pipeline/` or any project file.
3. After checking the preview, rerun without `--dry-run`; the script creates `.pipeline/tasks/` and the task files. Use `--request` only for short, non-sensitive requests. Delete only the temporary request file created for this initialization. Use the returned task ID. This records the initial commit, full status, changed-file hashes, and tracked binary diff under `.pipeline/tasks/<task-id>/baseline.*`.
4. **Discover project validation commands** — check for build/lint/test configuration (Makefile, package.json scripts, pyproject.toml, go.mod, etc.). Record discovered commands in `.pipeline/project.json`:
   ```json
   {
     "language": "<detected>",
     "build_cmd": "<e.g. cargo build, go build ./...>",
     "lint_cmd": "<e.g. ruff check ., eslint .>",
     "test_cmd": "<e.g. pytest, go test ./...>",
     "type_check_cmd": "<e.g. mypy ., tsc --noEmit>",
     "security_cmd": "<e.g. bandit -r ., npm audit>",
     "formatter_cmd": "<e.g. black ., gofmt -w .>"
   }
   ```
5. Use the collision-resistant task ID generated by the state script (`date-slug-requesthash`, with a numeric suffix when needed).
6. Write `.pipeline/config.json` with all resolved parameters.
7. Treat the script-generated `request.md`, `state.json`, `validation.json`, baseline files, and task directories as authoritative. Do not recreate `state.json` manually. Use the script's `update` command for changes and `validate` before resume or completion.
8. **Discover project structure** — scan `{output_dir}/` to build a file tree:
   - Use glob or `ls` to list all non-hidden files and directories (skip `.pipeline/`, `.git/`, `node_modules/`, `__pycache__/`, `venv/`, `.venv/`, `*.pyc`, etc.)
   - Store this tree at `.pipeline/project_tree.txt` for reuse across rounds.
   - If the directory is empty (greenfield project), note: "Empty project — you are writing the first files."

> **Note:** `requirements.md`, `spec.md`, and `architecture.md` stay inside `.pipeline/tasks/<task-id>/` by default. Only copy them to the project root if the user explicitly asks for project documentation.

---

## Phase 2: Requirements Analysis (only if `analyst` in roles)

1. Update state: `"phase": "analysis"`.
2. Read `prompts/analyst.md`.
3. Spawn agent (subagent_type: "general-purpose"):
   - Description: "Analyst: requirements analysis"
   - Prompt: role prompt + user's task + context_files
4. Wait for completion. Verify `.pipeline/tasks/<task-id>/spec.md` exists. Retry once if not.
5. Update state: `"phase": "architecture"` or `"phase": "coding"`.

---

## Phase 3: Architecture Design (only if `architect` in roles)

1. Update state: `"phase": "architecture"`.
2. Read `prompts/architect.md`.
3. Spawn agent with role prompt + spec.md (or task if no analyst) + context_files.
   - Description: "Architect: system design"
4. Wait for completion. Verify `.pipeline/tasks/<task-id>/architecture.md` exists. Retry once if not.
5. Update state: `"phase": "coding"`.

---

## Phase 4: Coding Loop (the core)

```
For each round R from 1 to max_rounds:
    
    ┌─────────────────────────────────────────────┐
    │ 4a. Select persona & spawn coder            │
    │ 4b. Validate coder output                   │
    │ 4b2. Run validation (build/lint/test)       │
    │     ├─ checks pass? → continue              │
    │     └─ checks fail? → force Critic next     │
    │ 4c. Review decision → maybe run reviewer    │
    │ 4d. Check stop conditions                   │
    │     ├─ severity threshold met? → STOP EARLY │
    │     ├─ validation + review clean? → STOP    │
    │     ├─ progress stalled 2 rounds? → STOP    │
    │     └─ R == max_rounds? → STOP              │
    │ 4e. Update state, continue loop             │
    └─────────────────────────────────────────────┘
```

### 4a. Spawn Coder

1. Determine persona from the rotation table (0e).
2. Read the corresponding prompt file from `prompts/`.
3. Read the project tree from `{output_dir}/.pipeline/project_tree.txt`.
4. Collect current code from `{output_dir}/` (skip `.pipeline/`, `.git/`, `node_modules/`, `__pycache__/`).
5. Compose prompt: role prompt + task context (task request, spec, architecture, **project tree**, current code, previous change_log, previous open_concerns, latest review findings, latest validation results).
6. Spawn agent:
   - Description: `"Coder R{R}: {persona}"`
   - subagent_type: "general-purpose"
7. Wait for completion.

### 4b. Validate Output

1. Check that code files were created/modified in `{output_dir}/` (not in a random subdirectory outside the project).
2. Check `.pipeline/tasks/<task-id>/change_log.md` exists.
3. Check `.pipeline/tasks/<task-id>/open_concerns.md` exists.
4. Update `.pipeline/project_tree.txt` if the coder added new directories.
5. Reject unrelated churn, placeholder implementations, and edits outside scope. Inspect the diff.
6. Missing items? Ask agent to retry once. Second failure: warn and continue.

### 4b2. Run Validation (executable quality gate)

Per Reliability Rule #4: after every coding round, run applicable checks. **Any failure returns to a Critic repair round.**

1. Load `.pipeline/project.json` for discovered commands.
2. Run the narrowest relevant check first (e.g., formatter on changed files, then linter, then type-check, then build, then tests).
3. Record every command, its exit code, and concise failure output in `.pipeline/tasks/<task-id>/validation.json`:
   ```json
   {
     "round": R,
     "checks": [
       {"cmd": "ruff check src/", "exit_code": 0, "status": "passed"},
       {"cmd": "pytest tests/ -q", "exit_code": 1, "status": "failed", "summary": "2 failed: test_login, test_register"}
     ],
     "overall": "failed"
   }
   ```
4. If any check fails:
   - Report: "Round {R}: validation failed — {N} check(s) did not pass."
   - Force the next round to use the **Critic** persona (regardless of rotation).
   - Feed the failure output as context.
5. If all checks pass: record and proceed normally.
6. If checks cannot run (e.g., no test runner configured for this language):
   - Record `"status": "skipped"` with reason.
   - Do NOT claim verification passed. This is `verified_with_limitations` at best.

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
- `stall_counter`: how many consecutive rounds with zero net improvement
- `validation_history`: list of per-round validation results
- `score_history`: list of per-round scorecards

#### Condition 1: Severity Threshold Met → Enter Fix-Attempt Grace Period

If review ran and found issues at or above `stop_on_severity`:

```
severity_levels = { critical: 4, high: 3, medium: 2, low: 1, info: 0 }
threshold = severity_levels[stop_on_severity]  // "never" → Infinity
worst_finding = max severity across all findings

if worst_finding >= threshold:
    
    if fix_attempts == 0:
        STOP_REASON = "severity_threshold"
        Report and stop (see "Final Stop" below).
    
    else if severity_hit_round is None:
        severity_hit_round = R
        fix_rounds_used = 0
        Report: "Round {R}: {severity} issues found. Coder has {fix_attempts} round(s) to fix."
        Continue to next round.
    
    else:
        fix_rounds_used += 1
        
        if fix_rounds_used >= fix_attempts:
            STOP_REASON = "severity_threshold"
            Report: "Round {R}: {severity} issues persist after {fix_attempts} fix attempt(s). Stopping."
            Execute "Final Stop" below.
        else:
            remaining = fix_attempts - fix_rounds_used
            Report: "Round {R}: {severity} issues still present. {remaining} fix attempt(s) remaining."
            Continue to next round.

else:
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

#### Condition 2: Quality Gates Passed → STOP (Quality Achieved)

Per Reliability Rules #5-6: scores are advisory. The primary gate is **executable validation passing** + **no unresolved critical/high findings** + **acceptance criteria satisfied**.

```
all_checks_passed = every applicable check ran and exited successfully
checks_unavailable = one or more required checks could not run for a documented environmental reason
review_clean = review ran and found zero critical AND zero high issues
scores_are_advisory = true  // scores never block; they inform only

if all_checks_passed AND review_clean AND acceptance_criteria_satisfied:
    STOP_REASON = "quality_achieved"
    STATUS = "completed"
    Pipeline stops successfully.
    "Pipeline complete at round {R}: validation passes and review finds no critical/high issues."

if checks_unavailable AND review_clean AND acceptance_criteria_satisfied:
    STOP_REASON = "verification_limited"
    STATUS = "verified_with_limitations"
    Report exactly which checks could not run. Do not call this fully verified.
```

> **Score is advisory only.** If composite score ≥ target_score, show a highlight in the report: *"🎯 Advisory: score {score} meets target {target_score}"* — but do NOT auto-stop on score alone. The scorecard is diagnostic; validation + findings are the real gate.

#### Condition 3: Progress Stalled → STOP

Per Reliability Rule #9: stop when progress stalls for two consecutive rounds.

```
A round has "no progress" when ALL of these are true:
  - validation result unchanged from previous round (same checks passed/failed)
  - no net reduction in open critical or high findings
  - composite score changed by ≤ 0.3 (negligible)

if round has "no progress":
    stall_counter += 1
    if stall_counter >= 2:
        STOP_REASON = "progress_stalled"
        Report: "Round {R}: no meaningful progress for 2 consecutive rounds. Stopping."
        Pipeline stops.
    else:
        Report: "Round {R}: minimal change detected. 1 more stalled round will trigger stop."
else:
    stall_counter = 0  // reset on any meaningful progress
```

#### Condition 4: Max Rounds Reached → STOP

If R == max_rounds (we just finished the last round):

```
STOP_REASON = "max_rounds"
Pipeline stops.
"Max rounds ({max_rounds}) reached."
If review found unresolved issues: mention them in the summary.
```

#### Condition 5: Continue

If none of the above triggered, continue to the next round.

**Weight Presets** (resolved at pipeline start, passed to Reviewer):
```
balanced:        all dimensions = 1.0
security-first:  security = 2.0, others = 1.0
performance-first: performance = 2.0, others = 1.0
```

Custom weights like `security:3,performance:0.5` → unresolved dimensions default to 1.0.

### 4e. Update State & Loop

```
state.current_round = R
state.rounds_completed.push(R)

// Always record validation results
state.validation_history.push({
    "round": R,
    "result": validation.overall,  // "passed" | "failed" | "skipped"
    "checks": validation.checks
})

// Track stall detection
if no_progress_this_round:
    state.stall_counter += 1
else:
    state.stall_counter = 0

if review ran:
    state.last_review_round = R
    // Parse scorecard_round{R}.json and append to score_history
    score_entry = {
        "round": R,
        "composite": <parsed composite_score>,
        "dimensions": <parsed dimensions>,
        "critical": <count>, "high": <count>, "medium": <count>, "low": <count>
    }
    state.score_history.push(score_entry)

// Write state atomically to .pipeline/tasks/<task-id>/state.json
Continue to round R+1
```

---

## Phase 5: Review Process

### 5a: Single Round Review

1. Read `prompts/reviewer.md`.
2. Read the project tree from `{output_dir}/.pipeline/project_tree.txt`.
3. Collect the current round diff, affected call paths, relevant tests, interfaces, and repository instructions. Expand to a repository-wide review only for cross-cutting or high-risk changes.
4. Resolve weights from `score_weights` parameter (use preset or parse custom weights).
5. Compute the weight values for each dimension.
6. Compose prompt: role prompt + project tree + code + spec + architecture + previous review reports + previous scorecards + **"Use these dimension weights: security={w1}, correctness={w2}, performance={w3}, maintainability={w4}, robustness={w5}, completeness={w6}"**.
7. Spawn agent:
   - Description: `"Reviewer: round {R}"`
   - subagent_type: "general-purpose"
8. Wait for completion.
9. Verify `.pipeline/tasks/<task-id>/reviews/review_round{R}.md` was created.
10. Verify `.pipeline/tasks/<task-id>/reviews/scorecard_round{R}.json` was created. If missing, extract the JSON block from the review markdown and write it. If still missing, retry once.
11. Parse `scorecard_round{R}.json` to get `composite_score` and dimension scores.
12. Parse findings: count critical, high, medium, low issues.
13. Report to user: "Round {R} review: {C} critical, {H} high, {M} medium, {L} low — Score: {composite}/10"
14. Return findings and scores for stop condition check.

### 5b: Batch Review (only if `review_strategy == "batch"`)

After the planned coding rounds:
1. Run a final review on the complete task diff and affected paths.
2. Write to `.pipeline/tasks/<task-id>/reviews/review_final.md`.
3. If accepted critical/high findings or validation failures remain, run up to `fix_attempts` Critic repair rounds, rerunning the exposing checks and final review after each repair.
4. Finish only through the normal quality gates. Batch review is never informational-only when it finds a release-blocking issue.

---

## Phase 6: Testing (inside the coding loop)

Per Reliability Rule #7: testing is part of the coding loop, not a terminal phase. When `tester` is in roles, the tester runs **within each round** after the coder (and optionally after review).

### 6a: Test Writing (runs when behavior or coverage changes)

1. Read `prompts/tester.md`.
2. Spawn the tester only when a round adds behavior, fixes a regression, or reveals an explicit coverage gap. Always run existing relevant tests even when no tester agent is needed.
   - Description: `"Tester R{R}: writing/updating tests"`
   - subagent_type: "general-purpose"
3. Verify test files were created or updated.
4. **Run the new tests immediately** as part of 4b2 validation:
   - If tests fail → the failure enters the validation report → next round forced to Critic.
   - If tests pass → continue normally.
   - Do NOT treat test writing as a documentation-only artifact. Tests that don't run are useless.

### 6b: Tester-Only Mode (deprecated — testing always runs)

The old behavior (Tester runs once at the end) is replaced. If the user explicitly wants tests only after all coding, they should omit `tester` from roles and rely on the validation step (4b2) to run existing project tests.

---

## Phase 7: Final Summary

```
╔══════════════════════════════════════════════════════════╗
║              Pipeline Complete                           ║
╠══════════════════════════════════════════════════════════╣
║ 停止原因:  质量达标 (验证通过 + 审查无critical/high)       ║
║ 完成轮次:  3 / 5                                         ║
║ 流水线:    generator → critic → refiner                   ║
║ 审查:      每轮                                           ║
╠══════════════════════════════════════════════════════════╣
║ 📁 项目: {output_dir}/                                   ║
║   ├── src/ ...               (你的代码 — Agent 原地修改)  ║
║   └── .pipeline/             (元数据 — 加到 .gitignore)  ║
║       ├── project.json                                   ║
║       ├── config.json                                    ║
║       ├── project_tree.txt                               ║
║       └── tasks/<task-id>/                               ║
║           ├── request.md                                 ║
║           ├── state.json                                 ║
║           ├── baseline.json                              ║
║           ├── baseline.patch                             ║
║           ├── change_log.md                              ║
║           ├── open_concerns.md                           ║
║           ├── validation.json                            ║
║           └── reviews/                                   ║
║               ├── review_round1.md                       ║
║               ├── scorecard_round1.json                  ║
║               └── ...                                    ║
╠══════════════════════════════════════════════════════════╣
║ 📊 统计:                                                 ║
║   总轮次:     3 轮执行 / 5 轮最大                         ║
║   验证结果:   ✅ build | ✅ lint | ✅ test (12 passed)    ║
║   发现问题:   5 (0 critical, 1 high, 3 medium, 1 low)    ║
║   已修复:     5                                           ║
║   最终审查:   ✅ 0 critical/high — 质量达标               ║
╠══════════════════════════════════════════════════════════╣
║ 📈 质量评分趋势 (仅供参考):                               ║
║                                                          ║
║   R1: ██████░░░░ 6.2  Generator  安全:5 正确:7 性能:6   ║
║   R2: ████████░░ 7.8  Critic     安全:8 正确:8 性能:7   ║
║   R3: █████████░ 9.1  Refiner    安全:9 正确:9 性能:9   ║
║                                                          ║
║   起始: 6.2 → 最终: 9.1 → 提升: +2.9 (+47%)              ║
╠══════════════════════════════════════════════════════════╣
║ 🎯 最终评分卡 (Round 3):                                 ║
║   安全性: 9/10    正确性: 9/10    性能: 9/10             ║
║   可维护性: 9/10  健壮性: 9/10    完整性: 10/10          ║
║   综合得分: 9.1/10  (权重: balanced) [仅供参考]           ║
╠══════════════════════════════════════════════════════════╣
║ ⚠️  遗留关注点:                                          ║
║   - [from open_concerns.md]                              ║
╠══════════════════════════════════════════════════════════╣
║ 💡 评分是诊断参考，不是质量门。真正的门是：                 ║
║   验证命令全部通过 + 无 critical/high 问题                ║
║   Task ID: <task-id> (用于后续恢复)                      ║
╚══════════════════════════════════════════════════════════╝
```

**Score Trend Chart Construction:**

Build the ASCII bar chart from `state.score_history`:

1. Find the max composite score across all rounds.
2. For each round, render a bar: `█` characters = floor(score), `░` characters = 10 - floor(score).
3. Show round number, bar, numeric score, persona, and top 3 dimension scores.
4. Calculate: start score (R1), final score (last R), absolute delta, percentage improvement.
5. Find the highest and lowest dimension averages across all rounds for the summary line.

If `target_score` was set and not met, show: `⚠️ 目标评分 {target_score} 未达到 (最终: {score})`

If no reviews ran (e.g., batch strategy with no final review), skip the score section and show: `(评分不可用 — 审查策略: batch 且未执行最终审查)`

---

## State Management

All pipeline state lives under `.pipeline/`. Task-specific state under `.pipeline/tasks/<task-id>/`:

```
{output_dir}/
├── .pipeline/                       # Pipeline metadata (hidden)
│   ├── project.json                 # Detected language + validation commands
│   ├── config.json                  # All resolved parameters
│   ├── project_tree.txt             # Discovered project structure
│   └── tasks/
│       └── <task-id>/               # Per-request isolation
│           ├── request.md           # Original task
│           ├── spec.md              # Analyst output (if enabled)
│           ├── architecture.md      # Architect output (if enabled)
│           ├── state.json           # Phase, round, findings, scores, stall
│           ├── baseline.json        # Initial commit, status, and patch hash
│           ├── baseline.patch       # Tracked pre-existing Git diff
│           ├── change_log.md        # Latest coder change log
│           ├── open_concerns.md     # Latest coder concerns
│           ├── validation.json      # Per-round validation results
│           └── reviews/
│               ├── review_round{N}.md
│               ├── scorecard_round{N}.json
│               └── ...
├── src/                             # Your actual code — in the real project
├── tests/                           # Your tests
└── ...                              # Your existing files
```

**Key design decisions:**
- **`.pipeline/`** is the ONLY hidden directory added. Everything pipeline-related lives here.
- **Task isolation** — each user request gets its own `tasks/<task-id>/` subdirectory. Resuming an unfinished task picks up where it left off.
- **Per-task `baseline.json` and `baseline.patch`** identify and preserve changes that existed before that task started.
- **`project.json`** caches discovered build/test commands so every round doesn't re-scan.
- **No project-root pollution** — `requirements.md`, `spec.md`, `architecture.md` stay inside `.pipeline/tasks/<id>/` unless user explicitly asks for project documentation.
- **All generated code** goes where it naturally belongs based on the project structure.

---

## Agent Communication

When composing a prompt for any agent, include:

```
## ROLE PROMPT
[full content of the appropriate prompts/*.md file]

## TASK CONTEXT
### Task
[.pipeline/tasks/<task-id>/request.md]

### Project Structure
[project_tree.txt content — this is the ACTUAL project layout. Place new files in the appropriate existing directories. Create new directories only when justified.]
IMPORTANT: You are working INSIDE this project, not in a sandbox. Your code files go where they naturally belong in this structure. Do NOT create an `output/` or `generated/` directory.

### Spec (if analyst ran)
[.pipeline/tasks/<task-id>/spec.md content]

### Architecture (if architect ran)
[.pipeline/tasks/<task-id>/architecture.md content]

### Current Code
[relevant code files from {output_dir}/ — use minimal context; don't send the whole repo]

### Previous Change Log
[.pipeline/tasks/<task-id>/change_log.md — or "Round 1, no previous changes"]

### Open Concerns
[.pipeline/tasks/<task-id>/open_concerns.md — or "None"]

### Review Findings to Address
[latest review report — or "No pending review findings"]

### Validation Results to Address
[latest validation.json — or "No pending validation failures"]

### Previous Scorecards
[previous scorecard JSON files — or "No previous scores"]

### Dimension Weights
[Resolved weights for each dimension. e.g.: security=1.0, correctness=1.0, performance=1.0, maintainability=1.0, robustness=1.0, completeness=1.0]

## OUTPUT INSTRUCTIONS
- Write code files into the EXISTING project structure shown above. Match the language/framework conventions.
- Write change log to .pipeline/tasks/<task-id>/change_log.md
- Write open concerns to .pipeline/tasks/<task-id>/open_concerns.md
- Follow your role's output format exactly
- Do NOT create a separate output directory for your code
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
- `.pipeline/tasks/<task-id>/state.json` records last completed round.
- On restart, check for existing task state: "Found partial task `<task-id>` at round {N}. Resume or restart?"

**Empty context_files:**
- Verify each file exists. Warn and skip missing files.

**Output directory already has content:**
- If `output_dir` is `.` (current project): this is the NORMAL case. Just warn: "Working in current project. Existing files may be modified by agents." No need to block.
- If `output_dir` is a custom path: warn "Output directory exists. Files may be overwritten. Continue?"

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

1. **max_rounds can be any number.** User picks it. Default is 5.
2. **Pipeline stops on four conditions (whichever comes first):**
   - Severity threshold exhausted (fix_attempts used up with issues still >= stop_on_severity)
   - Quality gates passed (validation passes + no critical/high findings)
   - Progress stalled (two consecutive rounds with no meaningful improvement)
   - Max rounds reached
3. **Executable validation is the primary quality gate.** Build/lint/test must pass. Reviewer scores are advisory diagnostics, not stop conditions.
4. **All pipeline metadata lives in `.pipeline/`.** Hidden from the project root. Per-task state under `.pipeline/tasks/<task-id>/`.
5. **Testing is inside the loop.** New tests run immediately. Failures re-enter the Critic repair round.
6. **The Critic persona FIXES problems** (not just reports them). The Reviewer REPORTS problems.
7. **Coders hand off to each other.** Each round's coder sees the previous round's code + change log + concerns + review findings + validation results.
8. **State survives interruptions.** Always check for `.pipeline/tasks/<task-id>/state.json` before starting. Resume unfinished tasks.
