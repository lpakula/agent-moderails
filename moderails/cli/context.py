"""Context management CLI commands."""

import click

from .common import get_moderails_dir, get_services_or_exit


@click.group()
@click.pass_context
def context(ctx):
    """Context management commands."""
    pass


@context.command("list")
@click.pass_context
def context_list(ctx):
    """List available skills, memories, and files from history."""
    services = get_services_or_exit(ctx)
    
    click.echo("## AVAILABLE CONTEXT\n")
    
    # 1. List available skills
    skills = services["context"].list_skills()
    click.echo("### SKILLS\n")
    if skills:
        for skill in skills:
            click.echo(f"- {skill}")
    else:
        click.echo("No skills (add to skills/)")
    
    click.echo()
    
    # 2. List available memories
    memories = services["context"].list_memories()
    click.echo("### MEMORIES\n")
    if memories:
        for memory in memories:
            click.echo(f"- {memory}")
    else:
        click.echo("No memories")
    
    click.echo()
    
    # 3. Show files from history
    click.echo("### FILES\n")
    files_tree = services["context"].get_files_tree()
    if files_tree:
        click.echo(files_tree)
    else:
        click.echo("No files")
    
    # 4. Usage instructions
    click.echo("\n---\n")
    click.echo("### USAGE\n")
    click.echo("```sh")
    click.echo("# Load context (flags can be combined)")
    click.echo("moderails context load --mandatory --memory auth --memory payments")
    click.echo("```")


@context.command("save")
@click.option("--name", "-n", required=True, help="Context file name (without .md extension)")
@click.option("--mandatory", "-m", is_flag=True, help="Save as mandatory context (auto-loaded)")
@click.option("--memory", "-M", is_flag=True, help="Save as memory (loaded on demand)")
@click.pass_context
def context_save(ctx, name: str, mandatory: bool, memory: bool):
    """Create a context file for agent editing.
    
    Creates a markdown file in the appropriate context directory.
    The agent should then edit this file in place to populate it.
    """
    if not mandatory and not memory:
        click.echo("❌ Provide --mandatory or --memory to specify context type")
        return
    
    if mandatory and memory:
        click.echo("❌ Provide only one of --mandatory or --memory")
        return
    
    services = get_services_or_exit(ctx)
    
    context_type = "mandatory context" if mandatory else "memory"
    
    # Check if file already exists before creating
    if services["context"].context_file_exists(name, mandatory=mandatory):
        click.echo(f"❌ {context_type.capitalize()} file '{name}' already exists")
        return
    
    file_path = services["context"].save_context_file(name, mandatory=mandatory)
    
    click.echo(f"✅ Created {context_type} file: `{file_path}`")
    click.echo(f"\nEdit this file in place: `{file_path}`")


@context.command("load")
@click.option("--mandatory", "-m", is_flag=True, help="Load mandatory context")
@click.option("--memory", "-M", multiple=True, help="Memory name to load (can specify multiple)")
@click.pass_context
def context_load(ctx, mandatory: bool, memory: tuple):
    """Load context: mandatory and/or memories. Flags can be combined."""
    if not mandatory and not memory:
        click.echo("❌ Provide --mandatory or --memory")
        click.echo("\n💡 Run `moderails context list` to see available options")
        return
    
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    
    output_parts = []
    
    # 1. Load mandatory context
    if mandatory:
        mandatory_context = services["context"].load_mandatory_context()
        if mandatory_context:
            output_parts.append(mandatory_context)
        else:
            output_parts.append("No mandatory context files found.")
            output_parts.append(f"Add markdown files to: {moderails_dir / 'context' / 'mandatory'}/")
    
    # 2. Load memories by name
    if memory:
        memory_content = services["context"].load_memories(list(memory))
        
        if memory_content:
            output_parts.append(memory_content)
            # Track loaded memories in session
            for mem_name in memory:
                services["session"].add_memory(mem_name)
        else:
            available = services["context"].list_memories()
            msg = f"❌ No memories found for: {', '.join(memory)}"
            if available:
                msg += f"\nAvailable: {', '.join(available)}"
            output_parts.append(msg)
    
    # Output all parts with separators
    click.echo("\n---\n".join(output_parts))
