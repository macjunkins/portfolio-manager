# AI Coding Agent Instructions

## Project Overview

This is a **Python-based portfolio automation toolkit** focused on multi-project status tracking and productivity automation. The core architecture follows a **batch processing pattern** using async GitHub GraphQL API calls combined with local git repository analysis.

## Architecture Pattern: Async Data Aggregation + Terminal Output

**Key Design:** Scripts gather data from multiple sources (GitHub API + local git) asynchronously, then render comprehensive terminal reports. No files are written by default - this is intentional for rapid iteration.

```python
# Core pattern used throughout:
async def gather_project_data(config):
    # 1. Parse config.yaml for project list
    # 2. Batch GitHub GraphQL queries (efficient API usage)
    # 3. Parallel local git repository checks
    # 4. Combine + calculate health scores
    return combined_data
```

## Essential File Relationships

- **`config.yaml`** → Central project registry organized by strategic pillars (revenue, infrastructure, etc.)
- **`lib/github_client.py`** → GraphQL wrapper with sophisticated batch querying
- **`lib/project_utils.py`** → Shared utilities for git operations, health scoring, date formatting
- **`scripts/portfolio_status.py`** → Main executable demonstrating the full pattern
- **`bin/`** → Symlink-based command installation system for global CLI access

## Critical Conventions

### 1. Environment & Configuration Discovery
Scripts auto-discover their config files relative to the script location, NOT the current working directory:
```python
script_dir = Path(__file__).parent.parent
config = load_config(script_dir / "config.yaml")
load_dotenv(script_dir / ".env")
```

### 2. GitHub API Efficiency Pattern
Always use GraphQL with batch queries to minimize API calls. The `get_multiple_repositories()` method in `github_client.py` demonstrates proper pagination and error handling.

### 3. Health Score Calculation
Projects receive 0-100 health scores based on:
- Recent activity (commit recency)
- Roadmap existence
- Issue backlog size
- Milestone progress
- Uncommitted changes
See `calculate_health_score()` in `project_utils.py` for the exact algorithm.

### 4. Command Installation Pattern
Use the `bin/install-portfolio-status` approach for creating globally accessible commands:
- Symlinks to wrapper scripts (not direct Python files)
- Auto-detects appropriate PATH directory
- Handles both `/usr/local/bin` and `~/scripts` patterns

## Development Workflow

### Adding New Scripts
1. Create in `scripts/` directory following the async pattern
2. Import from `lib/` for shared functionality
3. Add corresponding wrapper to `bin/` for CLI access
4. Update `config.yaml` if new project metadata is needed

### GitHub Token Requirements
All scripts require `GITHUB_TOKEN` environment variable with scopes: `repo`, `read:org`, `read:user`

### Testing Locally
```bash
# Always run from repo root or use full paths
python3 scripts/portfolio_status.py --lookback 30
# OR after installation:
portfolio-status -l 30
```

## Key Integration Points

- **GitPython** for local repository state (uncommitted changes, latest commits)
- **gql[all]** for GraphQL API efficiency
- **rich** for terminal formatting (tables, progress bars, panels)
- **PyYAML** for configuration parsing

## Project-Specific Patterns

### Strategic Pillar Organization
Projects are categorized by business pillars in `config.yaml`:
- `revenue` (🚨) - Critical path work
- `infrastructure` (🚀) - Force multipliers  
- `consistency` (📺) - Daily practice
- `cleanup` (🟡) - Lower priority
- `innovation` (🔬) - Exploratory

### Data Combination Strategy
Local git data is merged with GitHub API data to provide complete project health visibility:
- Local: uncommitted changes, branch state
- GitHub: issues, milestones, recent commits, stars/forks

### Error Handling Philosophy
Scripts continue processing even if individual repositories fail (e.g., network issues, permission problems). Errors are collected and reported but don't stop the entire batch process.

This architecture enables rapid portfolio insights while maintaining efficiency and reliability across multiple repositories and organizations.