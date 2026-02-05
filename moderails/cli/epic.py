"""Epic management CLI commands."""

from typing import Optional

import click

from .common import get_services_or_exit


@click.group()
@click.pass_context
def epic(ctx):
    """Epic management commands."""
    pass


@epic.command("create")
@click.option("--name", "-n", required=True, help="Epic name (can include spaces)")
@click.option("--skills", "-s", multiple=True, help="Skills to assign (can be repeated)")
@click.pass_context
def epic_create(ctx, name: str, skills: tuple):
    """Create a new epic with optional skills."""
    services = get_services_or_exit(ctx)
    
    try:
        e = services["epic"].create(name)
        
        # Add skills if provided
        if skills:
            available_skills = services["context"].list_skills()
            added = []
            invalid = []
            
            for skill in skills:
                if skill in available_skills:
                    if e.add_skill(skill):
                        added.append(skill)
                else:
                    invalid.append(skill)
            
            services["epic"].session.commit()
            
            if invalid:
                click.echo(f"⚠️  Unknown skills ignored: {', '.join(invalid)}")
                click.echo(f"   Available: {', '.join(available_skills) if available_skills else 'none'}")
        
        click.echo(f"✅ Created epic: {e.id} - {e.name}")
        
        if skills:
            assigned = e.get_skills()
            if assigned:
                click.echo(f"   Skills: {', '.join(assigned)}")
    except Exception as ex:
        click.echo(f"❌ Error creating epic: {ex}")


@epic.command("update")
@click.option("--id", "-i", "epic_id", required=True, help="Epic ID (6-character)")
@click.option("--name", "-n", help="New epic name")
@click.option("--add-skill", help="Add a skill to this epic")
@click.option("--remove-skill", help="Remove a skill from this epic")
@click.pass_context
def epic_update(ctx, epic_id: str, name: Optional[str], add_skill: Optional[str], remove_skill: Optional[str]):
    """Update epic name or manage skills."""
    services = get_services_or_exit(ctx)
    
    epic_obj = services["epic"].get(epic_id)
    if not epic_obj:
        click.echo(f"❌ Epic '{epic_id}' not found")
        return
    
    if not name and not add_skill and not remove_skill:
        click.echo("❌ Provide --name, --add-skill, or --remove-skill")
        return
    
    try:
        if name:
            epic_obj.name = name
        
        if add_skill:
            # Validate skill exists
            available_skills = services["context"].list_skills()
            if add_skill not in available_skills:
                click.echo(f"❌ Skill '{add_skill}' not found in skills/ directory")
                click.echo(f"Available: {', '.join(available_skills) if available_skills else 'none'}")
                return
            
            if epic_obj.add_skill(add_skill):
                click.echo(f"✅ Added skill '{add_skill}' to epic: {epic_obj.name}")
            else:
                click.echo(f"ℹ️  Skill '{add_skill}' already assigned to epic")
        
        if remove_skill:
            if epic_obj.remove_skill(remove_skill):
                click.echo(f"✅ Removed skill '{remove_skill}' from epic: {epic_obj.name}")
            else:
                click.echo(f"ℹ️  Skill '{remove_skill}' was not assigned to epic")
        
        services["epic"].session.commit()
        
        if name:
            click.echo(f"✅ Updated epic: {epic_obj.id} - {epic_obj.name}")
        
        # Show current skills
        skills = epic_obj.get_skills()
        if skills:
            click.echo(f"   Skills: {', '.join(skills)}")
    except Exception as ex:
        services["epic"].session.rollback()
        click.echo(f"❌ Error updating epic: {ex}")


@epic.command("list")
@click.pass_context
def epic_list(ctx):
    """List all epics as a simple table (for agents)."""
    services = get_services_or_exit(ctx)
    
    epics = services["epic"].list_all()
    
    if not epics:
        click.echo("No epics found.")
        return
    
    # Simple table format: id | name
    click.echo("id     | name")
    click.echo("-------|--------------------------------------------------")
    for epic in epics:
        click.echo(f"{epic.id} | {epic.name}")


@epic.command("load")
@click.option("--id", "-i", "epic_id", required=True, help="Epic ID (6-character)")
@click.option("--short", "-s", is_flag=True, help="Show only filenames instead of full diffs")
@click.pass_context
def epic_load(ctx, epic_id: str, short: bool):
    """Load epic context (completed tasks, summaries, and changes)."""
    services = get_services_or_exit(ctx)
    
    # Get epic by ID
    epic_obj = services["epic"].get(epic_id)
    if not epic_obj:
        click.echo(f"❌ Epic '{epic_id}' not found")
        return
    
    # Get epic summary
    epic_summary = services["epic"].get_summary(epic_obj.name, short=short)
    if epic_summary:
        click.echo(epic_summary)
    else:
        click.echo(f"# Epic: {epic_obj.name}\n\nNo completed tasks yet.")
