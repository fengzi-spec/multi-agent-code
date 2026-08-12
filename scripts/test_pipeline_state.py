import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pipeline_state


class PipelineStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_task_ids_are_unique_and_include_hash(self):
        tasks = self.project / ".pipeline" / "tasks"
        tasks.mkdir(parents=True)
        now = datetime(2026, 8, 12, tzinfo=timezone.utc)
        first = pipeline_state.unique_task_id(tasks, "Improve parser", now)
        (tasks / first).mkdir()
        second = pipeline_state.unique_task_id(tasks, "Improve parser", now)
        self.assertRegex(first, r"^20260812-improve-parser-[0-9a-f]{8}$")
        self.assertEqual(second, first + "-2")

    def test_initialize_update_and_validate(self):
        result = pipeline_state.initialize(self.project, "增加边界测试", 5)
        task_id = result["task_id"]
        self.assertEqual(pipeline_state.validate_task(self.project, task_id), [])
        state = pipeline_state.update_state(
            self.project,
            task_id,
            ['current_round=1', 'phase="review"'],
        )
        self.assertEqual(state["current_round"], 1)
        self.assertEqual(state["phase"], "review")
        self.assertIsNone(state["severity_hit_round"])
        self.assertEqual(state["fix_rounds_used"], 0)
        stored = json.loads(
            (self.project / ".pipeline" / "tasks" / task_id / "state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(stored["current_round"], 1)

    def test_baseline_excludes_pipeline_artifacts(self):
        existing = self.project / ".pipeline" / "old-task.txt"
        existing.parent.mkdir()
        existing.write_text("metadata", encoding="utf-8")
        user_file = self.project / "user-change.txt"
        user_file.write_text("keep me", encoding="utf-8")
        result = pipeline_state.initialize(self.project, "new task", 5)
        baseline = result["baseline"]
        self.assertIn("user-change.txt", baseline["file_sha256"])
        self.assertNotIn(".pipeline/old-task.txt", baseline["file_sha256"])
        self.assertTrue(all(".pipeline" not in line for line in baseline["status_lines"]))

    def test_dry_run_does_not_write_files(self):
        plan = pipeline_state.plan_initialization(self.project, "preview task", 8)
        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["max_rounds"], 8)
        self.assertFalse((self.project / ".pipeline").exists())
        self.assertTrue(any(path.endswith("state.json") for path in plan["planned_files"]))

    def test_final_state_requires_stop_reason(self):
        result = pipeline_state.initialize(self.project, "task", 1)
        task_id = result["task_id"]
        with self.assertRaisesRegex(ValueError, "final state requires stop_reason"):
            pipeline_state.update_state(self.project, task_id, ['status="completed"'])
        state_path = self.project / ".pipeline" / "tasks" / task_id / "state.json"
        self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["status"], "active")

    def test_update_rejects_invalid_values_before_writing(self):
        result = pipeline_state.initialize(self.project, "task", 1)
        task_id = result["task_id"]
        with self.assertRaisesRegex(ValueError, "current_round must be a non-negative integer"):
            pipeline_state.update_state(self.project, task_id, ["current_round=-1"])
        state_path = self.project / ".pipeline" / "tasks" / task_id / "state.json"
        self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["current_round"], 0)

    def test_validate_rejects_missing_schema_field(self):
        result = pipeline_state.initialize(self.project, "task", 1)
        task_id = result["task_id"]
        state_path = self.project / ".pipeline" / "tasks" / task_id / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        del state["pending_findings"]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.assertIn("state.json missing pending_findings", pipeline_state.validate_task(self.project, task_id))

    def test_validate_rejects_invalid_state_values(self):
        result = pipeline_state.initialize(self.project, "task", 1)
        task_id = result["task_id"]
        state_path = self.project / ".pipeline" / "tasks" / task_id / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"status": "finished", "current_round": 2, "pending_findings": {}, "fix_rounds_used": -1})
        state_path.write_text(json.dumps(state), encoding="utf-8")
        errors = pipeline_state.validate_task(self.project, task_id)
        self.assertTrue(any(error.startswith("status must be one of:") for error in errors))
        self.assertIn("current_round cannot exceed max_rounds", errors)
        self.assertIn("pending_findings must be a list", errors)
        self.assertIn("fix_rounds_used must be a non-negative integer", errors)


if __name__ == "__main__":
    unittest.main()
