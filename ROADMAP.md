# Portfolio Manager Roadmap

**Last Updated:** 2025-11-21
**Status:** Active Development

---

## Current State

The portfolio-manager has a working foundation:

| Component | Status | Notes |
|-----------|--------|-------|
| `portfolio-status` command | ✅ Complete | Terminal-only dashboard |
| GitHub GraphQL client | ✅ Complete | Async, handles rate limits |
| Local git integration | ✅ Complete | Via GitPython |
| Health score calculation | ✅ Complete | Configurable penalties |
| Unit tests | ❌ Missing | Mentioned in README but not implemented |
| Cross-platform support | ❌ Partial | Config uses hardcoded macOS paths |
| CI/CD | ❌ Missing | No GitHub Actions |

---

## Phase 1: Foundation Hardening

**Goal:** Make the existing code robust and portable.

### 1.1 Add Unit Tests
- [ ] Test `project_utils.py` functions (pure functions, easy wins)
- [ ] Test `calculate_health_score()` with various inputs
- [ ] Test `parse_github_repo()` edge cases
- [ ] Mock-based tests for `GitHubClient`
- [ ] Integration test for `status.py` with mock data

### 1.2 Cross-Platform Config
- [ ] Replace hardcoded `/Users/johnjunkins/Projects/` paths
- [ ] Support `~` expansion and environment variables in config
- [ ] Add config validation on load (warn about missing paths)
- [ ] Create `config.example.yaml` for new users

### 1.3 Error Handling Improvements
- [ ] Graceful handling when GitHub API is unreachable
- [ ] Better error messages for invalid tokens
- [ ] Timeout handling for slow network requests
- [ ] Partial results when some repos fail

---

## Phase 2: New Commands

**Goal:** Expand beyond status reporting.

### 2.1 Milestone Tracker (`commands/milestones.py`)
- [ ] List all milestones across portfolio
- [ ] Filter by due date (overdue, this week, this month)
- [ ] Filter by project or pillar
- [ ] Show milestone progress bars
- [ ] Output formats: terminal, JSON, markdown

### 2.2 Roadmap Validator (`commands/validate.py`)
- [ ] Check all projects have ROADMAP.md
- [ ] Validate roadmap format (headings, dates, sections)
- [ ] Cross-reference milestones in roadmap with GitHub milestones
- [ ] Generate report of inconsistencies
- [ ] Exit with non-zero code if validation fails (for CI)

### 2.3 Issue Triage Helper (`commands/triage.py`)
- [ ] List issues without priority labels
- [ ] List issues without milestones
- [ ] Show stale issues (no activity in N days)
- [ ] Suggest priority based on keywords
- [ ] Bulk labeling suggestions

---

## Phase 3: Automation & CI

**Goal:** Run portfolio health checks automatically.

### 3.1 GitHub Actions Integration
- [ ] Create workflow to run `portfolio-status` on schedule
- [ ] Store reports as artifacts
- [ ] Fail builds if critical health score < threshold
- [ ] Optional Slack/Discord notifications

### 3.2 Pre-commit Hooks
- [ ] Validate config.yaml syntax
- [ ] Check for secrets in committed files
- [ ] Run linter (ruff/flake8)

### 3.3 Scheduled Reports
- [ ] Weekly portfolio summary email/notification
- [ ] Trend tracking (health score over time)
- [ ] Alert when project goes from healthy to warning/critical

---

## Phase 4: Advanced Features

**Goal:** Power-user capabilities.

### 4.1 Interactive Mode
- [ ] TUI dashboard with `textual` or `rich`
- [ ] Real-time refresh
- [ ] Drill-down into individual projects
- [ ] Quick actions (open repo, open issues, etc.)

### 4.2 Multi-User Support
- [ ] Config profiles for different portfolios
- [ ] Team-level aggregation
- [ ] Organization-wide scanning

### 4.3 Historical Tracking
- [ ] SQLite database for historical data
- [ ] Health score trends over time
- [ ] Commit velocity metrics
- [ ] Issue resolution rates

### 4.4 Export Capabilities
- [ ] Export to JSON/CSV
- [ ] Generate static HTML dashboard
- [ ] Notion/Confluence integration

---

## Deferred / Out of Scope

The following are explicitly **not planned**:

- **Web UI:** This is a CLI tool by design
- **Multi-tenant SaaS:** Personal/team tool, not a service
- **Real-time sync:** Polling-based, not webhooks
- **Project management features:** Use GitHub Projects for that

---

## Contributing

See README.md for setup instructions. Key guidelines:

1. Keep commands self-contained in `commands/`
2. Shared logic goes in `lib/`
3. All new features need tests
4. Use type hints throughout
5. Follow existing code style (black, ruff)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-11-02 | Initial release (status command only) |
| 0.2.0 | TBD | Phase 1 complete |
