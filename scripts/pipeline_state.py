#!/usr/bin/env python3
"""Deterministic state management for the multi-agent-code skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_STATUSES = {
    "completed",
    "verified_with_limitations",
    "max_rounds",
    "progress_stalled",
    "blocked",
    "stopped_by_user",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def request_digest(request: str) -> str:
    return hashlib.sha256(request.strip().encode("utf-8")).hexdigest()


def slugify(request: str) -> str:
    ascii_text = request.strip().lower().encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")[:36]
    return slug or "task"


def unique_task_id(tasks_dir: Path, request: str, now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    base = f"{moment:%Y%m%d}-{slugify(request)}-{request_digest(request)[:8]}"
    candidate = base
    counter = 2
    while (tasks_dir / candidate).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def capture_baseline(project: Path, task_dir: Path) -> dict[str, Any]:
    pathspec = ["--", ".", ":(exclude).pipeline", ":(exclude).pipeline/**"]
    status = run_git(project, "status", "--porcelain=v1", "--untracked-files=all", *pathspec)
    head = run_git(project, "rev-parse", "HEAD")
    diff = run_git(project, "diff", "--binary", "HEAD", *pathspec)
    changed = run_git(
        project,
        "ls-files",
        "--modified",
        "--others",
        "--exclude-standard",
        "-z",
        *pathspec,
    )
    git_available = status.returncode == 0
    patch_text = diff.stdout if diff.returncode == 0 else ""
    file_hashes: dict[str, str | None] = {}
    if changed.returncode == 0:
        for relative in filter(None, changed.stdout.split("\0")):
            path = project / relative
            try:
                file_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            except OSError:
                file_hashes[relative] = None
    (task_dir / "baseline.patch").write_text(patch_text, encoding="utf-8", newline="\n")
    baseline = {
        "captured_at": utc_now(),
        "git_available": git_available,
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "status_lines": status.stdout.splitlines() if git_available else [],
        "file_sha256": file_hashes,
        "patch_sha256": hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
        "git_error": None if git_available else status.stderr.strip(),
    }
    atomic_json_write(task_dir / "baseline.json", baseline)
    return baseline


def initialize(project: Path, request: str, max_rounds: int) -> dict[str, Any]:
    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")
    project = project.resolve()
    if not project.is_dir():
        raise ValueError(f"project directory does not exist: {project}")
    pipeline = project / ".pipeline"
    tasks = pipeline / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    task_id = unique_task_id(tasks, request)
    task_dir = tasks / task_id
    (task_dir / "reviews").mkdir(parents=True)
    baseline = capture_baseline(project, task_dir)
    (task_dir / "request.md").write_text(request.strip() + "\n", encoding="utf-8", newline="\n")
    state = {
        "schema_version": 1,
        "task_id": task_id,
        "request_sha256": request_digest(request),
        "status": "active",
        "phase": "init",
        "current_round": 0,
        "max_rounds": max_rounds,
        "rounds_completed": [],
        "pending_findings": [],
        "validation_history": [],
        "score_history": [],
        "stall_counter": 0,
        "stop_reason": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    atomic_json_write(task_dir / "state.json", state)
    for name, initial in (("validation.json", {"status": "not_run", "checks": []}),):
        atomic_json_write(task_dir / name, initial)
    for name in ("change_log.md", "open_concerns.md"):
        (task_dir / name).write_text("", encoding="utf-8")
    return {"task_id": task_id, "task_dir": str(task_dir), "baseline": baseline, "state": state}


def parse_assignment(assignment: str) -> tuple[str, Any]:
    if "=" not in assignment:
        raise ValueError(f"expected KEY=JSON_VALUE, got: {assignment}")
    key, raw = assignment.split("=", 1)
    if not key or not re.fullmatch(r"[a-z][a-z0-9_]*", key):
        raise ValueError(f"invalid state key: {key}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    return key, value


def update_state(project: Path, task_id: str, assignments: list[str]) -> dict[str, Any]:
    state_path = project.resolve() / ".pipeline" / "tasks" / task_id / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    immutable = {"schema_version", "task_id", "request_sha256", "created_at"}
    for assignment in assignments:
        key, value = parse_assignment(assignment)
        if key in immutable:
            raise ValueError(f"state key is immutable: {key}")
        state[key] = value
    state["updated_at"] = utc_now()
    atomic_json_write(state_path, state)
    return state


def validate_task(project: Path, task_id: str) -> list[str]:
    task_dir = project.resolve() / ".pipeline" / "tasks" / task_id
    errors: list[str] = []
    required = ["request.md", "state.json", "baseline.json", "baseline.patch", "validation.json", "reviews"]
    for name in required:
        if not (task_dir / name).exists():
            errors.append(f"missing {name}")
    if errors:
        return errors
    try:
        state = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid state.json: {exc}"]
    for key in ("schema_version", "task_id", "request_sha256", "status", "phase", "current_round", "max_rounds"):
        if key not in state:
            errors.append(f"state.json missing {key}")
    if state.get("task_id") != task_id:
        errors.append("state task_id does not match directory")
    if not isinstance(state.get("current_round"), int) or state.get("current_round", -1) < 0:
        errors.append("current_round must be a non-negative integer")
    if not isinstance(state.get("max_rounds"), int) or state.get("max_rounds", 0) < 1:
        errors.append("max_rounds must be a positive integer")
    if state.get("status") in FINAL_STATUSES and not state.get("stop_reason"):
        errors.append("final state requires stop_reason")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="create a task and capture its Git baseline")
    init.add_argument("--project", type=Path, default=Path.cwd())
    request_group = init.add_mutually_exclusive_group(required=True)
    request_group.add_argument("--request")
    request_group.add_argument("--request-file", type=Path)
    init.add_argument("--max-rounds", type=int, default=5)
    update = subparsers.add_parser("update", help="atomically update task state")
    update.add_argument("--project", type=Path, default=Path.cwd())
    update.add_argument("--task-id", required=True)
    update.add_argument("--set", dest="assignments", action="append", required=True)
    validate = subparsers.add_parser("validate", help="validate a task directory")
    validate.add_argument("--project", type=Path, default=Path.cwd())
    validate.add_argument("--task-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            request = args.request_file.read_text(encoding="utf-8") if args.request_file else args.request
            print(json.dumps(initialize(args.project, request, args.max_rounds), ensure_ascii=False, indent=2))
        elif args.command == "update":
            print(json.dumps(update_state(args.project, args.task_id, args.assignments), ensure_ascii=False, indent=2))
        else:
            errors = validate_task(args.project, args.task_id)
            print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
            return 0 if not errors else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
