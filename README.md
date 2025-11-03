# Portfolio Manager

Portfolio automation tools for multi-project management and health tracking.

## Purpose

This repository contains Python tools to automate portfolio management tasks, including:
- Multi-project status dashboards
- Milestone tracking across repositories
- Roadmap validation and consistency checking
- GitHub automation via GraphQL API

These tools support the [Portfolio Meta-Roadmap 2026](../meta-roadmap.md) planning document.

---

## Quick Start

### 1. Install Dependencies

```bash
cd portfolio-manager
pip3 install -r requirements.txt
```

### 2. Configure GitHub Token

Create a `.env` file with your GitHub Personal Access Token:

```bash
cd portfolio-manager
cp .env.example .env
# Edit .env and add your token
```

**Required scopes:** `repo`, `read:org`, `read:user`

Generate a token at: https://github.com/settings/tokens

### 3. Configure Projects

Edit `config.yaml` to add your GitHub organizations and adjust project paths/repos as needed.

### 4. Run the Portfolio Status Command

#### Quick install (one-time)
From the repository root, run the installer to place a symlink in a directory on your PATH (or in ~/bin):

```bash
cd portfolio-manager
./bin/install-portfolio-status
```

Then verify:

```bash
portfolio-status -h
```

If your shell can't find it, the installer will print a PATH line to add to your ~/.zshrc or ~/.bashrc.

#### Prefer a home scripts folder (recommended)
If you want a central place for personal commands like `portfolio-status`, install it to `~/scripts` and add that to your PATH:

```bash
cd portfolio-manager
./bin/install-portfolio-status --home-scripts

# One-time PATH setup (zsh)
echo 'export PATH="$HOME/scripts:$PATH"' >> ~/.zshrc
source ~/.zshrc

# or for bash
echo 'export PATH="$HOME/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
portfolio-status -h
```

Notes:
- This installs only a tiny wrapper in `~/scripts` that forwards to the Python in this repo, so you keep code, config, and .env in the repository where they belong.
- You can update the repo without touching your `~/scripts` folder; the wrapper always points to the latest code.

#### Easiest: use the packaged command

Add the bin directory to your PATH once (e.g., in ~/.zshrc or ~/.bashrc):

```bash
export PATH="$HOME/Projects/portfolio-manager/bin:$PATH"
```

Then run the report from anywhere:

```bash
portfolio-status            # prints terminal report only (no files written)
portfolio-status -l 30      # look back 30 days for commits
```

Optional: create a quick alias (example):

```bash
alias psr='portfolio-status -l 30'
```

#### Or run via Python directly

**Scripts can be run from anywhere!** They automatically find their config and .env files.

```bash
# From the Projects directory
cd /Users/johnjunkins/Projects
python3 portfolio-manager/commands/status.py

# Or from the portfolio-manager directory
cd portfolio-manager
python3 commands/status.py

# Or from anywhere with full path
python3 /Users/johnjunkins/Projects/portfolio-manager/commands/status.py
```

---

## Available Commands

### Portfolio Status Dashboard ✅ COMPLETE

**Command:** `commands/status.py`

**Purpose:** Generates a comprehensive status report for all projects in the portfolio.

**Features:**
- Latest commits by project (configurable lookback period)
- Roadmap status (exists vs missing)
- Milestone completion percentages
- Open issue counts by priority
- Health scores for each project (0-100)
- Summary by strategic pillar

**Output:** Terminal only (no files written)

**Usage:**
```bash
# Generate report with default settings (90-day lookback)
portfolio-status

# Custom lookback period
portfolio-status -l 30

# View help
portfolio-status --help
```

**Why this matters:**
- Single source of truth for portfolio health
- Identifies stalled projects quickly
- Tracks roadmap coverage across all repos
- Automates manual status tracking (saves ~5-10 hours/month)

---

## Project Structure

```
portfolio-manager/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── config.yaml                    # Project configuration
├── .env                           # GitHub token (not committed)
├── .env.example                   # Template for .env
├── lib/
│   ├── __init__.py
│   ├── github_client.py           # GraphQL client wrapper
│   └── project_utils.py           # Shared utilities
├── commands/
│   └── status.py                  # ✅ Portfolio Status Dashboard (terminal-only)
├── bin/
│   ├── portfolio-status           # CLI wrapper
│   └── install-portfolio-status   # Installation script
├── docs/
│   ├── portfolio-status-2025-11-01.md
│   └── issue-portfolio-discovery.md
└── tests/                         # Unit tests (coming soon)
```

---

## Configuration

### `config.yaml`

Defines all projects to monitor, organized by strategic pillars:

```yaml
github:
  user: macjunkins
  organizations:
    - name: "your-org-name"

projects:
  - name: EmberCare-Business
    path: /Users/johnjunkins/Projects/EmberCare-Business
    github_repo: macjunkins/EmberCare-Business
    pillar: revenue
    priority: critical
    description: "Backend API and business logic"
  # ... more projects
```

**Pillars:**
- `revenue` - 🚨 Revenue generation (critical path)
- `infrastructure` - 🚀 Infrastructure & productivity
- `consistency` - 📺 Consistency & reputation
- `cleanup` - 🟡 Strategic cleanup
- `innovation` - 🔬 Strategic innovation

**Priorities:**
- `critical` - 🚨 Blocking other work
- `high` - 🔴 Important but not blocking
- `medium` - 🟡 Normal priority
- `low` - 🟢 Nice to have

---

## Why GraphQL?

This project uses **GitHub's GraphQL API** instead of REST or `gh` CLI because:

1. **Efficiency:** Single request can fetch commits, issues, milestones, and roadmap status
2. **Precise data fetching:** Only get exactly what we need (reduces token usage)
3. **Better rate limits:** GraphQL is more efficient than multiple REST calls
4. **Strong typing:** Query validation catches errors before execution
5. **Sophisticated tooling:** The `gql` library provides excellent error handling and retry logic

**Token efficiency:** GraphQL uses ~80-85% fewer tokens than `gh` CLI MCP tools for the same data.

---

## Health Score Calculation

Each project receives a health score (0-100) based on:

| Metric | Max Penalty | Threshold |
|--------|-------------|-----------|
| No commits in 90+ days | -30 points | Critical |
| No commits in 30-90 days | -15 points | Warning |
| No commits in 7-30 days | -5 points | Minor |
| No ROADMAP.md | -20 points | Warning |
| 50+ open issues | -20 points | Warning |
| 20-50 open issues | -10 points | Minor |
| Stalled milestones | -15 points | Warning |
| Uncommitted changes | -15 points | Warning |

**Status levels:**
- ✅ **Healthy:** 80-100 points
- ⚠️ **Warning:** 60-79 points
- 🚨 **Critical:** 0-59 points

---

## Dependencies

**Core:**
- `gql[all]==3.5.0` - GraphQL client for GitHub API
- `PyYAML==6.0.1` - YAML configuration parsing
- `python-dotenv==1.0.0` - Environment variable management
- `GitPython==3.1.40` - Local git repository operations

**Utilities:**
- `python-dateutil==2.8.2` - Date/time utilities
- `rich==13.7.0` - Rich terminal output (pretty printing)

---

## Troubleshooting

### "GITHUB_TOKEN not found"

Create a `.env` file with your token:
```bash
cp .env.example .env
# Edit .env and add: GITHUB_TOKEN=your_token_here
```

### "Repository not found"

Check that:
1. The repository exists and you have access
2. Your token has `repo` scope
3. The `github_repo` format in `config.yaml` is `owner/name`

### "GraphQL query error"

Common causes:
- Invalid token or expired token
- Missing required scopes (need `repo`, `read:org`, `read:user`)
- Repository is private and you don't have access
- Rate limit exceeded (wait and retry)

---

## Migration History

This repository was migrated from the `personal-scripts` monorepo on 2025-11-02.

**Previous location:** `/Users/johnjunkins/GitHub/personal-scripts/`
**New home:** `https://github.com/macjunkins/portfolio-manager`

**Changes:**
- Renamed `scripts/portfolio_status.py` → `commands/status.py`
- Updated all project paths from `GitHub/` → `Projects/`
- Separated concerns: portfolio tools now independent from other scripts

---

## Contributing

This is a personal automation repository. If you'd like to use these tools:

1. Fork the repository
2. Update `config.yaml` with your projects
3. Generate your own `.env` file
4. Adjust paths and settings as needed

---

## Author

**John Junkins** (@macjunkins)

**Created:** 2025-11-02
**Migrated from:** personal-scripts
**Status:** Production ready ✅
