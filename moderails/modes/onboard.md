# ONBOARD MODE

**Active Mode**: ONBOARD  
**Output Format**: Start with `[MODE: ONBOARD]`

## PURPOSE
One-time codebase analysis to bootstrap moderails with initial context files and tags.

## WHEN TO USE
- **Primary use**: Immediately after `moderails init` (first-time setup)
- **Optional**: Can be re-run manually via `#onboard` if needed

## CONTEXT BUILDING STRATEGY

**Initial setup** (this mode): Quick bootstrap to get started
**Ongoing context** (recommended): Use `#archive` mode to convert completed epics into context files

This ensures context stays accurate and reflects actual implemented features.

## WORKFLOW

### Phase 1: Codebase Analysis

1. **Discover project structure**:
   - Scan directory tree (respect .gitignore)
   - Identify project type (language, framework)
   - Find config files (package.json, pyproject.toml, requirements.txt, etc.)
   - Locate README, documentation, key entry points

2. **Understand architecture**:
   - Read README for project overview
   - Examine config files for dependencies and scripts
   - Identify main entry points (main.py, index.js, etc.)
   - Map major components/modules/packages
   - Understand tech stack and patterns

3. **Analyze features and structure**:
   - Identify major functional areas (auth, API, database, etc.)
   - Map folder structure (backend, frontend, services, etc.)
   - Note important patterns or conventions
   - Find testing setup and build configuration

### Phase 2: Tag Proposal

Propose tags using **mixed approach**:

**Structural tags** (based on folder organization):
- Examples: `backend`, `frontend`, `api`, `cli`, `database`, `ui`, `mobile`

**Functional tags** (based on feature domains):
- Examples: `auth`, `payments`, `analytics`, `notifications`, `search`, `storage`

**Present as numbered list**:
```
## Proposed Tags

Based on codebase analysis, I recommend these tags:

1. **backend** - Server-side API and business logic
2. **frontend** - React web application
3. **auth** - Authentication and authorization
4. **database** - PostgreSQL schema and migrations
5. **api** - REST API endpoints and OpenAPI specs
6. **testing** - Test infrastructure and utilities

Which tags would you like context files for?
(Enter numbers: e.g., "1,2,3" or "all" or "none")
```

### Phase 3: Context File Drafting

For each selected tag, draft context files:

**Mandatory context** (`moderails/context/project-overview.md`):
```markdown
# {Project Name}

## Overview
{High-level description of what the project does}

## Tech Stack
- **Language**: {language and version}
- **Framework**: {main frameworks}
- **Database**: {database if applicable}
- **Key Dependencies**: {important libraries}

## Project Structure
{Tree or description of main directories}

## Key Files
- `{file}` - {purpose}
- `{file}` - {purpose}

## Important Patterns
{Architectural patterns, conventions, coding standards}

## Getting Started
{Brief setup instructions or reference to docs}
```

**Tag-specific context** (`moderails/context/{tag}/{filename}.md`):
```markdown
# {Tag Name} - {Aspect}

## Overview
{What this tag covers}

## Key Components
- **{Component}**: {description}
- **{Component}**: {description}

## Important Files
- `{file}` - {purpose}
- `{file}` - {purpose}

## Patterns & Conventions
{Specific to this area}

## Common Tasks
- {Task description and key files involved}
- {Task description and key files involved}
```

### Phase 4: Preview & Approval

Show what will be created:

```
## Proposed Context Files

### 📌 Mandatory (moderails/context/)
- **project-overview.md** (~{estimated lines} lines)
  
  Preview:
  ```
  {first 15-20 lines}
  ```

### 🏷️ Tag-specific

**{tag}/** (moderails/context/{tag}/)
- **{filename}.md** (~{estimated lines} lines)
  
  Preview:
  ```
  {first 15-20 lines}
  ```

**Total**: {N} files, ~{total lines} lines

---

Options:
- Type "yes" to create all files
- Type "preview:{filename}" to see full content before creating
- Type "skip:{tag}" to exclude specific tag
- Type "no" to cancel
```

### Phase 5: File Creation

After approval:
1. Create `moderails/context/` directory if needed
2. Write mandatory context file(s)
3. Create tag subdirectories
4. Write tag-specific context files
5. Report completion:

```
✅ Context files created:

📌 Mandatory:
- moderails/context/project-overview.md

🏷️ Tag-specific:
- moderails/context/backend/architecture.md
- moderails/context/frontend/components.md
- moderails/context/auth/implementation.md

---

💡 Next steps:
1. Review and edit context files as needed
2. Create your first task:
   moderails start --new --task "task-name" --epic "epic-name" --tags "backend,auth"

3. The context files will be automatically loaded based on epic tags
```

## ANALYSIS GUIDELINES

### Read Strategically
- **DO**: Read README, main config, entry points, key architectural files
- **DO**: Skim package structure and major modules
- **DO**: Check for documentation in docs/ or wiki
- **DON'T**: Read every file in detail (too expensive)
- **DON'T**: Include code snippets in context (keep high-level)

### Keep Context Concise
- **Target**: 100-300 lines per context file
- **Focus**: What an agent needs to know to work on tasks
- **Include**: File paths, architecture, patterns, conventions
- **Exclude**: Implementation details, full code listings

### Tag Quantity
- **Recommended**: 3-8 tags for most projects
- **Too few**: Generic, not useful for filtering
- **Too many**: Fragmented, hard to manage
- **Balance**: Cover major areas without over-segmenting

## PERMITTED
- Read codebase files (non-destructively)
- Scan directory structure
- Propose tags based on analysis
- Draft context files for preview
- Create files in `moderails/context/` after approval
- Ask clarifying questions about project structure

## FORBIDDEN
- **NEVER create context files without user approval**
- **NEVER modify code files**
- **NEVER include sensitive data** (API keys, credentials)
- **NEVER make git commits**
- No task creation or epic management
- No changes outside `moderails/context/` directory

## EXAMPLE ANALYSIS OUTPUT

```
[MODE: ONBOARD]

🔍 Analyzing codebase...

## Project Analysis Complete

**Project**: moderails  
**Type**: Python CLI application  
**Framework**: Click (CLI), SQLAlchemy (ORM)  
**Structure**: Single package with service-oriented architecture

### Directory Structure
```
moderails/
├── cli.py              # Click-based CLI commands
├── db/                 # Database models (SQLAlchemy)
├── services/           # Business logic services
├── modes/              # Mode definition markdown files
├── utils/              # Helper utilities (git, etc.)
└── templates/          # File templates
```

### Tech Stack
- Python 3.11+
- Click for CLI interface
- SQLAlchemy for database (SQLite)
- Rich for terminal output
- Pytest for testing

---

## Proposed Tags

1. **cli** - Command-line interface and commands
2. **database** - Database models, schema, and ORM
3. **services** - Core business logic (task, epic, context services)
4. **modes** - Mode system and workflow definitions
5. **git** - Git integration and diff utilities

Which tags would you like context files for? (e.g., "1,2,3" or "all")
```

---
**YOU MUST FOLLOW THE WORKFLOW**

