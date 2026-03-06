"""FastAPI server for the moderails web UI."""

import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..db.database import get_session, reset_engine
from ..db.models import TaskType
from ..services.agent import AgentService
from ..services.flow import FlowService
from ..services.project import ProjectService
from ..services.run import RunService
from ..services.task import TaskService
from ..services.worktree import WorktreeService

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="moderails", version="2.0.0")


# --- Pydantic models ---

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    type: str = "feature"
    start: bool = False
    flow: str = "default"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class FlowCreate(BaseModel):
    name: str
    description: str = ""
    copy_from: Optional[str] = None


class FlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class StepCreate(BaseModel):
    name: str
    content: str = ""
    position: Optional[int] = None
    gates: Optional[list[dict]] = None


class StepUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    position: Optional[int] = None
    gates: Optional[list[dict]] = None


class ReorderSteps(BaseModel):
    step_ids: list[str]


class TaskStartBody(BaseModel):
    flow: str = "default"
    flow_chain: list[str] = []
    user_prompt: str = ""


# --- Helpers ---

def _get_services():
    reset_engine()
    session = get_session()
    return session, ProjectService(session), TaskService(session)


def _enrich_task(task_dict: dict, project_path: str, session) -> dict:
    """Add dynamic fields from active TaskRun and run count."""
    run_svc = RunService(session)
    active_run = run_svc.get_active(task_dict["id"])
    all_runs = run_svc.list_by_task(task_dict["id"])
    task_dict["agent_active"] = AgentService.is_agent_running(
        project_path, task_dict.get("worktree_branch", ""),
    )
    task_dict["flow"] = active_run.flow_name if active_run else None
    task_dict["current_step"] = active_run.current_step if active_run else None
    task_dict["run_id"] = active_run.id if active_run else None
    task_dict["run_count"] = len(all_runs)
    branch = task_dict.get("worktree_branch", "")
    if branch:
        wt_svc = WorktreeService(project_path)
        wt_path = wt_svc.get_worktree_path(branch)
        task_dict["worktree_path"] = str(wt_path) if wt_path else None
    else:
        task_dict["worktree_path"] = None
    return task_dict


# --- Root ---

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


# --- Daemon endpoints ---

@app.get("/api/daemon/status")
async def daemon_status():
    from ..services.daemon import read_pid_file
    pid = read_pid_file()
    return {"running": pid is not None, "pid": pid}


@app.get("/api/daemon/logs")
async def daemon_logs(lines: int = 200):
    import os
    log_path = os.path.expanduser("~/.moderails/daemon.log")
    if not os.path.exists(log_path):
        return {"lines": []}
    with open(log_path, "r") as f:
        all_lines = f.readlines()
    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
    return {"lines": [line.rstrip() for line in tail]}


# --- Project endpoints ---

@app.get("/api/projects")
async def list_projects():
    session, project_svc, _ = _get_services()
    try:
        projects = project_svc.list_all()
        return [p.to_dict() for p in projects]
    finally:
        session.close()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    session, project_svc, _ = _get_services()
    try:
        project = project_svc.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project.to_dict()
    finally:
        session.close()


class ProjectUpdate(BaseModel):
    name: Optional[str] = None


@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate):
    session, project_svc, _ = _get_services()
    try:
        project = project_svc.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if updates:
            project = project_svc.update(project_id, **updates)
        return project.to_dict()
    finally:
        session.close()


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    session, project_svc, _ = _get_services()
    try:
        if not project_svc.unregister(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        return {"ok": True}
    finally:
        session.close()


# --- Task endpoints ---

@app.get("/api/projects/{project_id}/tasks")
async def list_tasks(project_id: str):
    session, project_svc, task_svc = _get_services()
    try:
        project = project_svc.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        tasks = task_svc.list_by_project(project_id)
        return [_enrich_task(t.to_dict(), project.path, session) for t in tasks]
    finally:
        session.close()


@app.post("/api/projects/{project_id}/tasks")
async def create_task(project_id: str, body: TaskCreate):
    session, project_svc, task_svc = _get_services()
    try:
        project = project_svc.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        try:
            task_type = TaskType(body.type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type: {body.type}")

        task = task_svc.create(
            project_id=project_id,
            name=body.title,
            description=body.description,
            task_type=task_type,
        )

        if body.start:
            run_svc = RunService(session)
            run_svc.enqueue(project_id, task.id, body.flow)

        return _enrich_task(task.to_dict(), project.path, session)
    finally:
        session.close()


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, body: TaskUpdate):
    session, project_svc, task_svc = _get_services()
    try:
        task = task_svc.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        updates = {}
        if body.title is not None:
            updates["name"] = body.title
        if body.description is not None:
            updates["description"] = body.description
        if updates:
            task = task_svc.update(task_id, **updates)

        project = project_svc.get(task.project_id)
        return _enrich_task(task.to_dict(), project.path, session)
    finally:
        session.close()


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    session, _, task_svc = _get_services()
    try:
        if not task_svc.delete(task_id):
            raise HTTPException(status_code=404, detail="Task not found")
        return {"ok": True}
    finally:
        session.close()


@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: str, body: TaskStartBody):
    """Enqueue a new run for a task."""
    session, project_svc, task_svc = _get_services()
    try:
        task = task_svc.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        run_svc = RunService(session)
        chain = body.flow_chain if body.flow_chain else [body.flow]
        run_svc.enqueue(task.project_id, task_id, flow_name=chain[0],
                        user_prompt=body.user_prompt or task.description or "",
                        flow_chain=chain)

        project = project_svc.get(task.project_id)
        task = task_svc.get(task_id)
        return _enrich_task(task.to_dict(), project.path, session)
    finally:
        session.close()


@app.get("/api/tasks/{task_id}/runs")
async def list_task_runs(task_id: str):
    """Execution history for a task."""
    session, _, task_svc = _get_services()
    try:
        task = task_svc.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        run_svc = RunService(session)
        runs = run_svc.list_by_task(task_id)
        return [r.to_dict() for r in runs]
    finally:
        session.close()


@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a completed task run by ID."""
    session, _, _ = _get_services()
    try:
        from ..db.models import TaskRun
        run = session.query(TaskRun).filter_by(id=run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        if not run.completed_at:
            raise HTTPException(status_code=400, detail="Cannot delete an active run")
        session.delete(run)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.get("/api/runs/{run_id}/logs")
async def stream_run_logs(run_id: str):
    """SSE endpoint that tails the agent's NDJSON log file for a TaskRun."""
    session, _, _ = _get_services()
    try:
        run_svc = RunService(session)
        run = run_svc.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        if not run.log_path:
            raise HTTPException(status_code=404, detail="No log path set for this run")
        log_path = Path(run.log_path)
    finally:
        session.close()

    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found on disk")

    async def tail_log():
        pos = 0
        idle_count = 0
        max_idle = 120
        while idle_count < max_idle:
            try:
                size = log_path.stat().st_size
            except FileNotFoundError:
                break

            if size > pos:
                idle_count = 0
                with open(log_path, "r") as f:
                    f.seek(pos)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                            yield f"data: {json.dumps(event)}\n\n"
                        except json.JSONDecodeError:
                            continue
                    pos = f.tell()
            else:
                idle_count += 1

            await asyncio.sleep(1)

        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        tail_log(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- Queue + dashboard ---

@app.get("/api/queue")
async def global_queue():
    """All active TaskRuns globally (executing first, then pending)."""
    session, project_svc, task_svc = _get_services()
    try:
        run_svc = RunService(session)
        runs = run_svc.list_active()
        result = []
        for r in runs:
            d = r.to_dict()
            task = task_svc.get(r.task_id)
            project = project_svc.get(r.project_id) if r.project_id else None
            d["task_name"] = task.name if task else None
            d["project_name"] = project.name if project else None
            result.append(d)
        return result
    finally:
        session.close()


@app.get("/api/projects/{project_id}/queue")
async def project_queue(project_id: str):
    """All TaskRuns for project (pending + executing), ordered."""
    session, project_svc, _ = _get_services()
    try:
        project = project_svc.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        run_svc = RunService(session)
        runs = run_svc.list_by_project(project_id)
        active = [r.to_dict() for r in runs if r.completed_at is None]
        return active
    finally:
        session.close()


@app.get("/api/dashboard")
async def dashboard():
    """System overview: all projects with active run counts, queue depths."""
    session, project_svc, task_svc = _get_services()
    try:
        run_svc = RunService(session)
        projects = project_svc.list_all()
        result = []
        for p in projects:
            tasks = task_svc.list_by_project(p.id)
            all_runs = run_svc.list_by_project(p.id)
            active_runs = [r for r in all_runs if r.completed_at is None]
            pending_runs = [r for r in active_runs if r.started_at is None]
            executing_runs = [r for r in active_runs if r.started_at is not None]
            recent = [r.to_dict() for r in all_runs if r.completed_at is not None][-5:]

            task_ids_with_active = {r.task_id for r in active_runs}
            task_counts = {
                "running": len(executing_runs),
                "queued": len(pending_runs),
                "idle": sum(1 for t in tasks if t.id not in task_ids_with_active),
            }

            result.append({
                "project": p.to_dict(),
                "task_counts": task_counts,
                "queue_depth": len(pending_runs),
                "active_runs": len(executing_runs),
                "executing": [
                    {
                        "run": r.to_dict(),
                        "agent_active": AgentService.is_agent_running(
                            p.path, task_svc.get(r.task_id).worktree_branch if task_svc.get(r.task_id) else "",
                        ),
                    }
                    for r in executing_runs
                ],
                "recent_completions": recent,
            })
        return result
    finally:
        session.close()


# --- Flow endpoints ---

@app.get("/api/flows")
async def list_flows():
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        flows = flow_svc.list_all()
        return [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
                "step_count": len(f.steps),
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in flows
        ]
    finally:
        session.close()


@app.get("/api/flows/{flow_id}")
async def get_flow(flow_id: str):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        flow = flow_svc.get(flow_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        return flow.to_dict()
    finally:
        session.close()


@app.post("/api/flows")
async def create_flow(body: FlowCreate):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        if body.copy_from:
            flow = flow_svc.duplicate(body.copy_from, body.name)
            if not flow:
                raise HTTPException(status_code=404, detail=f"Source flow '{body.copy_from}' not found")
            if body.description:
                flow_svc.update(flow.id, description=body.description)
        else:
            flow = flow_svc.create(
                name=body.name,
                description=body.description,
            )
        return flow.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@app.patch("/api/flows/{flow_id}")
async def update_flow(flow_id: str, body: FlowUpdate):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if body.description is not None:
            updates["description"] = body.description
        flow = flow_svc.update(flow_id, **updates)
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        return flow.to_dict()
    finally:
        session.close()


@app.delete("/api/flows/{flow_id}")
async def delete_flow(flow_id: str):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        flow_svc.delete(flow_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@app.post("/api/flows/{flow_id}/steps")
async def add_flow_step(flow_id: str, body: StepCreate):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        step = flow_svc.add_step(
            flow_id, body.name, body.content, body.position, gates=body.gates,
        )
        if not step:
            raise HTTPException(status_code=404, detail="Flow not found")
        return step.to_dict()
    finally:
        session.close()


@app.patch("/api/flows/{flow_id}/steps/{step_id}")
async def update_flow_step(flow_id: str, step_id: str, body: StepUpdate):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if body.content is not None:
            updates["content"] = body.content
        if body.position is not None:
            updates["position"] = body.position
        if body.gates is not None:
            import json
            updates["gates"] = json.dumps(body.gates)
        step = flow_svc.update_step(step_id, **updates)
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        return step.to_dict()
    finally:
        session.close()


@app.delete("/api/flows/{flow_id}/steps/{step_id}")
async def delete_flow_step(flow_id: str, step_id: str):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        if not flow_svc.remove_step(step_id):
            raise HTTPException(status_code=404, detail="Step not found")
        return {"ok": True}
    finally:
        session.close()


@app.post("/api/flows/{flow_id}/reorder")
async def reorder_flow_steps(flow_id: str, body: ReorderSteps):
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        if not flow_svc.reorder_steps(flow_id, body.step_ids):
            raise HTTPException(status_code=404, detail="Flow not found")
        flow = flow_svc.get(flow_id)
        return flow.to_dict()
    finally:
        session.close()


@app.post("/api/flows/export")
async def export_flows():
    session, _, _ = _get_services()
    try:
        flow_svc = FlowService(session)
        data = flow_svc.export_flows()
        return JSONResponse(content=data)
    finally:
        session.close()


@app.post("/api/flows/import")
async def import_flows(file: UploadFile = File(...)):
    session, _, _ = _get_services()
    try:
        content = await file.read()
        data = json.loads(content)
        flow_svc = FlowService(session)
        count = flow_svc._import_flows_data(data, skip_existing=False)
        return {"imported": count}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    finally:
        session.close()


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
