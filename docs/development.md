# Development

## Setup

```bash
# Clone and install in dev mode
git clone https://github.com/lpakula/agent-moderails.git
cd agent-moderails
pipx install -e .

# Run
moderails --help
```

Changes are reflected immediately — no reinstall needed.

## Running Tests

The project includes a comprehensive test suite covering all CLI commands and core functionality:

```bash
# Run all tests in Docker (recommended)
./scripts/test.sh

# Run specific test file
./scripts/test.sh tests/test_cli.py

# Run specific test
./scripts/test.sh tests/test_cli.py::TestInitCommand::test_init_success

# Rebuild image (after updating dependencies in pyproject.toml)
./scripts/test.sh --rebuild
```

## Database Migrations

When you modify the database schema, add a new migration in `moderails/db/migrations.py`:

```python
# moderails/db/migrations.py
MIGRATIONS = {
    1: """...""",  # Initial schema
    2: """
        -- Add priority field to tasks
        ALTER TABLE tasks ADD COLUMN priority TEXT;
    """,  # Your new migration
}
```
**Testing:**
```bash
moderails start  # Auto-runs pending migrations
```
