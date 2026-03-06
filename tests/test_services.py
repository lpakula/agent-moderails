"""Tests for service layer."""

import json
import tempfile
from pathlib import Path

from moderails.db.models import Flow, FlowStep, Task, TaskRun, TaskType
from moderails.services.flow import FlowService
from moderails.services.project import ProjectService
from moderails.services.run import RunService
from moderails.services.task import TaskService


class TestProjectService:
    def test_register(self, test_db):
        svc = ProjectService(test_db)
        project = svc.register("test", "/tmp/test")
        assert project.name == "test"
        assert project.path == "/tmp/test"

    def test_register_idempotent(self, test_db):
        svc = ProjectService(test_db)
        p1 = svc.register("test", "/tmp/test")
        p2 = svc.register("test", "/tmp/test")
        assert p1.id == p2.id

    def test_unregister(self, test_db):
        svc = ProjectService(test_db)
        project = svc.register("test", "/tmp/test")
        assert svc.unregister(project.id) is True
        assert svc.get(project.id) is None

    def test_unregister_nonexistent(self, test_db):
        svc = ProjectService(test_db)
        assert svc.unregister("nope") is False

    def test_list_all(self, test_db):
        svc = ProjectService(test_db)
        svc.register("a", "/tmp/a")
        svc.register("b", "/tmp/b")
        assert len(svc.list_all()) == 2

    def test_get_by_path(self, test_db):
        svc = ProjectService(test_db)
        svc.register("test", "/tmp/test")
        found = svc.get_by_path("/tmp/test")
        assert found is not None
        assert found.name == "test"

    def test_get_by_path_not_found(self, test_db):
        svc = ProjectService(test_db)
        assert svc.get_by_path("/tmp/nope") is None


class TestTaskService:
    def test_create(self, test_db, test_project):
        svc = TaskService(test_db)
        task = svc.create(test_project.id, "Test task", description="A description")
        assert task.name == "Test task"
        assert task.description == "A description"
        assert task.project_id == test_project.id

    def test_create_with_options(self, test_db, test_project):
        svc = TaskService(test_db)
        task = svc.create(
            test_project.id,
            "Fix the bug",
            description="It crashes on Safari",
            task_type=TaskType.FIX,
        )
        assert task.name == "Fix the bug"
        assert task.type == TaskType.FIX

    def test_list_by_project(self, test_db, test_project):
        svc = TaskService(test_db)
        svc.create(test_project.id, "Task 1")
        svc.create(test_project.id, "Task 2")
        tasks = svc.list_by_project(test_project.id)
        assert len(tasks) == 2

    def test_update_fields(self, test_db, test_project):
        svc = TaskService(test_db)
        task = svc.create(test_project.id, "Test")
        svc.update(task.id, worktree_branch="task-abc123")
        updated = svc.get(task.id)
        assert updated.worktree_branch == "task-abc123"

    def test_delete(self, test_db, test_project):
        svc = TaskService(test_db)
        task = svc.create(test_project.id, "Delete me")
        assert svc.delete(task.id) is True
        assert svc.get(task.id) is None

    def test_delete_nonexistent(self, test_db, test_project):
        svc = TaskService(test_db)
        assert svc.delete("nope") is False


class TestFlowService:
    def test_create_flow(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("test-flow", description="A test flow")
        assert flow.name == "test-flow"
        assert flow.description == "A test flow"

    def test_create_flow_with_steps(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("with-steps", steps=[
            {"name": "research", "position": 0, "content": "# Research"},
            {"name": "execute", "position": 1, "content": "# Execute"},
        ])
        assert len(flow.steps) == 2
        assert flow.steps[0].name == "research"

    def test_create_flow_duplicate_name(self, test_db):
        import pytest
        svc = FlowService(test_db)
        svc.create("dup-test")
        with pytest.raises(ValueError, match="already exists"):
            svc.create("dup-test")

    def test_get_by_name(self, test_db):
        svc = FlowService(test_db)
        svc.create("lookup")
        found = svc.get_by_name("lookup")
        assert found is not None
        assert found.name == "lookup"

    def test_list_all(self, test_db):
        svc = FlowService(test_db)
        svc.create("flow-a")
        svc.create("flow-b")
        flows = svc.list_all()
        assert len(flows) == 2

    def test_update(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("update-test", description="Old")
        svc.update(flow.id, description="New")
        updated = svc.get(flow.id)
        assert updated.description == "New"

    def test_delete(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("delete-me")
        assert svc.delete(flow.id) is True
        assert svc.get(flow.id) is None

    def test_delete_default_flow_raises(self, test_db):
        import pytest
        svc = FlowService(test_db)
        flow = svc.create("default")
        with pytest.raises(ValueError, match="Cannot delete"):
            svc.delete(flow.id)

    def test_add_step(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("step-test")
        step = svc.add_step(flow.id, "research", "# Research content")
        assert step.name == "research"
        assert step.content == "# Research content"

    def test_update_step(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("step-update")
        step = svc.add_step(flow.id, "test", "old content")
        svc.update_step(step.id, content="new content")
        updated = test_db.query(FlowStep).filter_by(id=step.id).first()
        assert updated.content == "new content"

    def test_remove_step(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("step-remove")
        step = svc.add_step(flow.id, "test", "content")
        assert svc.remove_step(step.id) is True
        assert test_db.query(FlowStep).filter_by(id=step.id).first() is None

    def test_reorder_steps(self, test_db):
        svc = FlowService(test_db)
        flow = svc.create("reorder")
        s1 = svc.add_step(flow.id, "a", "", 0)
        s2 = svc.add_step(flow.id, "b", "", 1)
        s3 = svc.add_step(flow.id, "c", "", 2)
        svc.reorder_steps(flow.id, [s3.id, s1.id, s2.id])
        flow = svc.get(flow.id)
        names = [s.name for s in sorted(flow.steps, key=lambda s: s.position)]
        assert names == ["c", "a", "b"]

    def test_get_step_content(self, test_db):
        svc = FlowService(test_db)
        svc.create("content-test", steps=[
            {"name": "research", "content": "# Do Research"},
        ])
        content = svc.get_step_content("content-test", "research")
        assert content == "# Do Research"

    def test_get_step_content_not_found(self, test_db):
        svc = FlowService(test_db)
        svc.create("no-step")
        assert svc.get_step_content("no-step", "nonexistent") is None

    def test_get_flow_steps(self, test_db):
        svc = FlowService(test_db)
        svc.create("ordered", steps=[
            {"name": "b", "position": 1},
            {"name": "a", "position": 0},
            {"name": "c", "position": 2},
        ])
        steps = svc.get_flow_steps("ordered")
        assert steps == ["a", "b", "c"]

    def test_get_next_step(self, test_db):
        svc = FlowService(test_db)
        svc.create("next-test", steps=[
            {"name": "research", "position": 0},
            {"name": "execute", "position": 1},
            {"name": "summary", "position": 2},
        ])
        assert svc.get_next_step("next-test", "research") == "execute"
        assert svc.get_next_step("next-test", "execute") == "summary"
        assert svc.get_next_step("next-test", "summary") is None

    def test_duplicate(self, test_db):
        svc = FlowService(test_db)
        svc.create("source", description="Original", steps=[
            {"name": "step1", "position": 0, "content": "Content 1"},
        ])
        copy = svc.duplicate("source", "copy")
        assert copy.name == "copy"
        assert copy.description == "Original"
        assert len(copy.steps) == 1
        assert copy.steps[0].content == "Content 1"

    def test_seed_defaults(self, test_db):
        svc = FlowService(test_db)
        svc.seed_defaults()
        flow = svc.get_by_name("default")
        assert flow is not None
        assert len(flow.steps) == 3

    def test_seed_defaults_idempotent(self, test_db):
        svc = FlowService(test_db)
        svc.seed_defaults()
        svc.seed_defaults()
        flows = svc.list_all()
        defaults = [f for f in flows if f.name == "default"]
        assert len(defaults) == 1

    def test_export_import_round_trip(self, test_db):
        svc = FlowService(test_db)
        svc.create("export-test", description="For export", steps=[
            {"name": "step1", "position": 0, "content": "# Step 1"},
            {"name": "step2", "position": 1, "content": "# Step 2"},
        ])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        svc.export_flows(path)

        data = json.loads(path.read_text())
        assert data["version"] == 1
        assert len(data["flows"]) == 1
        assert data["flows"][0]["name"] == "export-test"
        assert len(data["flows"][0]["steps"]) == 2

        for step in list(svc.get_by_name("export-test").steps):
            test_db.delete(step)
        test_db.delete(svc.get_by_name("export-test"))
        test_db.commit()

        count = svc.import_flows(path)
        assert count == 1
        reimported = svc.get_by_name("export-test")
        assert reimported is not None
        assert len(reimported.steps) == 2

        path.unlink()


class TestRunService:
    def test_enqueue(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Test")

        run = run_svc.enqueue(test_project.id, task.id, "default")
        assert run.flow_name == "default"
        assert run.started_at is None
        assert run.status == "queued"

    def test_get_pending(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Pending")
        run_svc.enqueue(test_project.id, task.id)

        pending = run_svc.get_pending(test_project.id)
        assert pending is not None
        assert pending.task_id == task.id

    def test_mark_started(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Start me")
        run = run_svc.enqueue(test_project.id, task.id)

        run_svc.mark_started(run.id)
        assert run.started_at is not None
        assert run.status == "running"

    def test_update_step(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Step test")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.update_step(task.id, "research")
        assert run.current_step == "research"
        completed = json.loads(run.steps_completed)
        assert "research" in completed

        run_svc.update_step(task.id, "execute")
        assert run.current_step == "execute"
        completed = json.loads(run.steps_completed)
        assert completed == ["research", "execute"]

    def test_set_log_path(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Log path test")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.set_log_path(run.id, "/tmp/wt/.moderails/agent-abc123.log")
        assert run.log_path == "/tmp/wt/.moderails/agent-abc123.log"

    def test_set_prompt(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Prompt test")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.set_prompt(run.id, "# Full agent prompt\nDo the task.")
        assert run.prompt == "# Full agent prompt\nDo the task."

    def test_set_summary(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Summary test")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.set_summary(task.id, "Did everything right.")
        assert run.summary == "Did everything right."
        assert run.outcome == "completed"

    def test_mark_completed(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Complete me")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.mark_completed(run.id, outcome="completed")
        assert run.completed_at is not None
        assert run.outcome == "completed"
        assert run.status == "completed"

    def test_mark_completed_failed(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Fail me")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        run_svc.mark_completed(run.id, outcome="failed")
        assert run.outcome == "failed"

    def test_get_active(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "Active test")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)

        active = run_svc.get_active(task.id)
        assert active is not None
        assert active.id == run.id

    def test_get_active_none_after_completion(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "No active")
        run = run_svc.enqueue(test_project.id, task.id)
        run_svc.mark_started(run.id)
        run_svc.mark_completed(run.id)

        assert run_svc.get_active(task.id) is None

    def test_get_history(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        task = task_svc.create(test_project.id, "History test")

        r1 = run_svc.enqueue(test_project.id, task.id, "default")
        run_svc.mark_started(r1.id)
        run_svc.set_summary(task.id, "First run summary")
        run_svc.mark_completed(r1.id)

        r2 = run_svc.enqueue(test_project.id, task.id, "custom")
        run_svc.mark_started(r2.id)
        run_svc.set_summary(task.id, "Second run summary")
        run_svc.mark_completed(r2.id)

        history = run_svc.get_history(task.id)
        assert len(history) == 2
        assert history[0].flow_name == "default"
        assert history[1].flow_name == "custom"

    def test_list_by_project(self, test_db, test_project):
        task_svc = TaskService(test_db)
        run_svc = RunService(test_db)
        t1 = task_svc.create(test_project.id, "Task 1")
        t2 = task_svc.create(test_project.id, "Task 2")
        run_svc.enqueue(test_project.id, t1.id)
        run_svc.enqueue(test_project.id, t2.id)

        runs = run_svc.list_by_project(test_project.id)
        assert len(runs) == 2
