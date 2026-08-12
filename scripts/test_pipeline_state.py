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
        first = pipeline_state.unique_task_id(tasks, "Improve login", now)
        (tasks / first).mkdir()
        second = pipeline_state.unique_task_id(tasks, "Improve login", now)
        self.assertRegex(first, r"^20260812-improve-login-[0-9a-f]{8}$")
        self.assertEqual(second, first + "-2")

    def test_initialize_update_and_validate(self):
        result = pipeline_state.initialize(self.project, "增加登录测试", 5)
        task_id = result["task_id"]
        self.assertEqual(pipeline_state.validate_task(self.project, task_id), [])
        state = pipeline_state.update_state(
            self.project,
            task_id,
            ['current_round=1', 'phase="review"'],
        )
        self.assertEqual(state["current_round"], 1)
        self.assertEqual(state["phase"], "review")
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

    def test_final_state_requires_stop_reason(self):
        result = pipeline_state.initialize(self.project, "task", 1)
        task_id = result["task_id"]
        pipeline_state.update_state(self.project, task_id, ['status="completed"'])
        self.assertIn("final state requires stop_reason", pipeline_state.validate_task(self.project, task_id))


if __name__ == "__main__":
    unittest.main()
