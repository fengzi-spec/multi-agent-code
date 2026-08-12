---
name: multi-agent-code
description: Orchestrate iterative improvement of an existing or new software project with distinct analyst, architect, coder, reviewer, and tester perspectives, persistent task state, executable quality gates, and review-driven repair loops. Use when the user asks Codex to build, modify, harden, refactor, review, test, or repeatedly improve a codebase through multiple agent rounds or role-based collaboration.
---

# Multi-Agent Code

Run a bounded, evidence-driven coding loop inside the user's project. Use real subagents when the host provides them. When subagents are unavailable, perform the same phases sequentially with explicitly separated role passes and tell the user that the roles are simulated rather than independent.

## Read role instructions progressively

Read only the prompt needed for the current phase:

- Requirements clarification: `prompts/analyst.md`
- Architecture work: `prompts/architect.md`
- Initial implementation: `prompts/coder-generator.md`
- Defect and security repair: `prompts/coder-critic.md`
- Focused refinement: `prompts/coder-refiner.md`
- Independent review: `prompts/reviewer.md`
- Test design and execution: `prompts/tester.md`

Do not load every prompt or the whole repository into every agent context.

## Establish scope and safety

1. Treat the current project as the default target unless the user names another directory.
2. Inspect repository instructions, project structure, build files, test configuration, and version-control status before editing.
3. Preserve all pre-existing user changes. Capture the initial commit, status, hashes, and binary diff in the task baseline; never reset, discard, overwrite, or claim those changes as pipeline output.
4. Keep changes inside the requested project and task scope. Ask before destructive, production, deployment, credential, migration, or irreversible operations.
5. Prefer a feature branch or isolated worktree when the host can create one safely. Otherwise record a diff after every round so changes remain attributable and recoverable.

## Initialize or continue task state

Store orchestration metadata under `.pipeline/`. Do not put generated application code there.

- Maintain `.pipeline/project.json` for project-level facts and validation commands.
- Give every user request a stable task ID and store it under `.pipeline/tasks/<task-id>/`.
- Store `request.md`, `state.json`, `change_log.md`, `open_concerns.md`, `validation.json`, and `reviews/` per task.
- Append a new request as a new task. Do not overwrite a completed task's requirements or history.
- If an unfinished task matches the user's request, resume from the last completed phase after verifying the filesystem still matches the recorded state.
- Write state atomically after each completed phase or round. Record status, round, changed files, pending findings, validation results, and stop reason.

Use `python scripts/pipeline_state.py init --project <project> --request "<request>" --max-rounds 5` to initialize task state and capture the baseline. Use its `update` command for atomic state changes and `validate` before resuming or finishing. Resolve the script path relative to this `SKILL.md`, not the target project.

Never add `requirements.md`, `spec.md`, or `architecture.md` to the project root unless the user requests project documentation. Keep pipeline-only artifacts under `.pipeline/`.

## Select relevant context

1. Build a concise project map while excluding generated, dependency, cache, VCS, and pipeline directories.
2. Search for symbols, routes, tests, configuration, and call sites related to the request.
3. Load the smallest coherent context: requested files, direct dependencies, affected tests, interfaces, and repository instructions.
4. Give coders the relevant files plus current findings. Give reviewers the round diff plus affected call paths and tests.
5. Expand to a repository-wide review only for cross-cutting changes or when evidence indicates broader risk.
6. Refresh context from disk before every round. Do not rely on stale code pasted by a previous agent.

## Run the improvement loop

Use a default maximum of 5 coding rounds unless the user chooses another value. Prefer focused rounds over persona rotation for its own sake.

For each round:

1. Choose the next pass based on evidence:
   - Generator for missing functionality.
   - Critic for failed validation or unresolved findings.
   - Refiner only after behavior is correct and verified.
2. Give the coder the task, acceptance criteria, relevant context, current diff, validation failures, unresolved review findings, and explicit file boundaries.
3. Require direct edits in the project, not code pasted only into chat.
4. Inspect the resulting diff. Reject unrelated churn, fabricated outputs, placeholder implementations, and edits outside scope.
5. Discover and run the narrowest relevant formatter, static analysis, build, and tests. Then run the broader project checks when practical.
6. Record exact commands, exit codes, and concise failure output in the task's `validation.json`. Never report a check as passing unless it actually ran successfully.
7. Run an independent review when subagents are available. The reviewer must inspect the current diff and relevant code without seeing the coder's private rationale or target score.
8. Convert every accepted finding and validation failure into a deduplicated pending item with severity, file location, evidence, and required verification.
9. Feed pending items into the next Critic round. After repairs, rerun the checks that exposed them and review the repair diff.

If a test-writing pass adds or changes tests, run those tests immediately. Test failures re-enter the coding loop; testing is not a terminal documentation-only phase.

## Apply quality gates

Use executable evidence as the primary completion criterion. Reviewer scores are advisory and must not override failed checks.

Declare quality achieved only when all applicable conditions hold:

- The stated acceptance criteria are satisfied.
- Relevant build, test, lint, type-check, and security commands that can run locally pass.
- No accepted critical or high finding remains unresolved.
- Newly added behavior has appropriate regression coverage, or the lack of coverage is explicitly justified.
- The final diff is scoped, coherent, and contains no unexplained generated artifacts.

Do not stop merely because one reviewer reports zero findings or a numeric score crosses a threshold. If validation cannot run because of a genuine environmental limitation, record the limitation and use `verified_with_limitations`; do not call it fully verified.

Stop when quality gates pass, the maximum round count is reached, progress stalls for two consecutive rounds, or the user intervenes. Stop immediately and ask for direction when further progress needs new authority or a material product decision.

## Finish and report

Perform a final fresh-context review of the complete diff and rerun applicable checks. Update task state with one of: `completed`, `verified_with_limitations`, `max_rounds`, `blocked`, or `stopped_by_user`.

Report:

- What behavior changed.
- Which files changed.
- Which commands passed or failed.
- Which findings were fixed and which remain.
- Any verification limitation or user-owned pre-existing change preserved.
- The task ID needed to resume or extend the work later.

Keep the user informed during long runs. Never imply that multiple independent agents participated when only a single sequential role simulation was possible.
