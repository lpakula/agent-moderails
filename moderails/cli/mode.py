"""Mode CLI -- step navigation for agents (next/current)."""

import click

from ..config import get_repo_root
from ..db.database import get_session, init_db
from ..services.context import ContextService
from ..services.flow import FlowService
from ..services.run import RunService


@click.group("mode")
def mode_cmd():
    """Navigate flow steps. Used by agents during execution."""
    pass


@mode_cmd.command("next")
def mode_next():
    """Advance to the next step and print its content.

    On first call returns the first step of the first flow in the chain.
    When a flow's steps are exhausted, automatically advances to the next
    flow in the chain. After the last flow's last step, returns the
    auto-appended complete step. After complete, prints a finished message.
    """
    repo_root = get_repo_root()
    if repo_root is None:
        click.echo("Not inside a git repository.", err=True)
        raise SystemExit(1)

    moderails_dir = repo_root / ".moderails"
    context_svc = ContextService(moderails_dir)
    task_id = context_svc.get_current_task_id()
    run_id = context_svc.get_current_run_id()

    if not task_id and not run_id:
        click.echo("No task_id or run_id found in .moderails/", err=True)
        raise SystemExit(1)

    init_db()
    session = get_session()
    try:
        flow_svc = FlowService(session)
        run_svc = RunService(session)

        # Load the active run directly from DB — single source of truth
        if run_id:
            from ..db.models import TaskRun
            run = session.query(TaskRun).filter_by(id=run_id).first()
        else:
            run = run_svc.get_active(task_id)

        if not run:
            click.echo("No active run found.", err=True)
            raise SystemExit(1)

        flow_name = run.flow_name
        current = run.current_step or ""
        steps = flow_svc.get_flow_steps(flow_name)

        if not steps:
            click.echo(f"Flow '{flow_name}' not found or has no steps.", err=True)
            raise SystemExit(1)

        if not current:
            next_step = steps[0]
        elif current == "complete":
            click.echo("Flow chain completed. No more steps. Stop.")
            return
        elif current in steps:
            nxt = flow_svc.get_next_step(flow_name, current)
            if nxt:
                next_step = nxt
            else:
                # Current flow exhausted — check chain for next flow
                next_flow = run_svc.get_next_flow_in_chain(task_id) if task_id else None
                if next_flow:
                    click.echo(f"\n---\nFlow '{flow_name}' complete. Continuing with '{next_flow}'...\n---\n",
                               err=True)
                    run_svc.advance_to_next_flow(task_id, next_flow)
                    flow_name = next_flow
                    steps = flow_svc.get_flow_steps(next_flow)
                    next_step = steps[0] if steps else "complete"
                else:
                    next_step = "complete"
        else:
            next_step = "complete"

        # Persist next step to DB
        run_svc.update_step(task_id or run.task_id, next_step)

        if next_step == "complete":
            content = context_svc.load_complete_step()
        else:
            content = flow_svc.get_step_content(flow_name, next_step)

        if not content:
            click.echo(f"No content found for step '{next_step}'.", err=True)
            raise SystemExit(1)

        click.echo(content)
    finally:
        session.close()


@mode_cmd.command("current")
def mode_current():
    """Re-read the current step without advancing (crash recovery)."""
    repo_root = get_repo_root()
    if repo_root is None:
        click.echo("Not inside a git repository.", err=True)
        raise SystemExit(1)

    moderails_dir = repo_root / ".moderails"
    context_svc = ContextService(moderails_dir)
    task_id = context_svc.get_current_task_id()
    run_id = context_svc.get_current_run_id()

    if not task_id and not run_id:
        click.echo("No task_id or run_id found in .moderails/", err=True)
        raise SystemExit(1)

    init_db()
    session = get_session()
    try:
        flow_svc = FlowService(session)
        run_svc = RunService(session)

        if run_id:
            from ..db.models import TaskRun
            run = session.query(TaskRun).filter_by(id=run_id).first()
        else:
            run = run_svc.get_active(task_id)

        if not run:
            click.echo("No active run found.", err=True)
            raise SystemExit(1)

        current = run.current_step or ""
        flow_name = run.flow_name

        if not current:
            click.echo("No current step. Run 'moderails mode next' to start.", err=True)
            raise SystemExit(1)

        if current == "complete":
            content = context_svc.load_complete_step()
        else:
            content = flow_svc.get_step_content(flow_name, current)

        if not content:
            click.echo(f"No content found for step '{current}'.", err=True)
            raise SystemExit(1)

        click.echo(content)
    finally:
        session.close()
