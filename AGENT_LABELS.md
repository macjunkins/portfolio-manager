# Agent Label System

A standardized label taxonomy for AI-assisted development workflows with Claude Code.

---

## 1. Agent Labels

Assign issues to a specific AI tool or workflow.

| Label | Purpose |
|-------|---------|
| `agent:claude` | Claude Code for architecture, specs, code generation, and PR creation |
| `agent:copilot` | GitHub Copilot for simple inline fixes or beginner-friendly tasks |
| `agent:cursor` | Cursor IDE for local, multi-file refactors or context-heavy development |
| `agent:warp` | Warp Terminal for CLI scripting, DevOps tasks, or command automation |
| `agent:manual` | Reserved for human work - do not assign to AI |
| `agent:research` | Research or planning tasks (no code changes) |

---

## 2. Scope Labels

Prevent collisions between agents and group by code area.

| Label | Meaning |
|-------|---------|
| `scope:frontend` | UI / Views / Components / Styling |
| `scope:backend` | Business logic / Services / Controllers |
| `scope:api` | API routes / Endpoints / Networking |
| `scope:data` | Models / Entities / Database / Repositories |
| `scope:infra` | Infrastructure / CI/CD / GitHub Actions |
| `scope:devops` | Build systems / Pipelines / Packaging |
| `scope:tests` | Unit / Integration / E2E tests |
| `scope:docs` | Documentation / READMEs |

---

## 3. Difficulty Labels

Determines required reasoning level and tool selection.

| Label | Meaning |
|-------|---------|
| `difficulty:easy` | Simple inline fixes, small patches (Copilot) |
| `difficulty:medium` | Single-file changes (Claude/Cursor) |
| `difficulty:hard` | Multi-file work, refactors (Claude/Cursor) |
| `difficulty:extreme` | Architecture-level or module rewrites (Claude with planning) |

---

## 4. Workflow State Labels

Control automation and prevent work collisions.

| Label | Meaning |
|-------|---------|
| `status:ready` | Issue ready to be worked |
| `status:assigned` | Assigned to an agent, waiting for execution |
| `status:in-progress` | Agent actively working / PR in progress |
| `status:review` | PR created, awaiting human review |
| `status:changes-requested` | PR needs updates |
| `status:done` | Issue completed |
| `status:deferred` | Pushed to later milestone |

---

## 5. Blocking and Dependency Labels

Encode dependencies so agents know when NOT to work an issue.

| Label / Pattern | Meaning |
|-----------------|---------|
| `blocked` | Cannot work this issue yet |
| `blocked-by:#<issue>` | Hard dependency on another issue |
| `depends-on:#<issue>` | Soft dependency (sequential workflow) |
| `conflicts-with:#<issue>` | Cannot be worked simultaneously with another issue |

Note: Dependencies can also be specified in issue body text.

---

## 6. Agent Routing Guidelines

### Default routing by task type:

| Task Type | Agent | Difficulty |
|-----------|-------|------------|
| Small inline fixes | `agent:copilot` | `difficulty:easy` |
| New files, single-module changes | `agent:claude` | `difficulty:medium` |
| Multi-file refactors | `agent:claude` or `agent:cursor` | `difficulty:hard` |
| CLI/DevOps tasks | `agent:warp` | `scope:devops` |
| Architecture planning | `agent:claude` | `difficulty:extreme` |
| Research/investigation | `agent:research` | - |

---

## 7. Label Colors

When creating labels in GitHub, use these colors:

| Category | Color | Hex |
|----------|-------|-----|
| agent:* | Purple | `#7B68EE` |
| scope:* | Blue | `#0366D6` |
| difficulty:easy | Green | `#28A745` |
| difficulty:medium | Yellow | `#FFC107` |
| difficulty:hard | Orange | `#FD7E14` |
| difficulty:extreme | Red | `#DC3545` |
| status:ready | Light Green | `#C2E0C6` |
| status:assigned | Light Blue | `#BFD4F2` |
| status:in-progress | Blue | `#0075CA` |
| status:review | Purple | `#D4C5F9` |
| status:changes-requested | Orange | `#FBCA04` |
| status:done | Dark Green | `#0E8A16` |
| status:deferred | Gray | `#6A737D` |
| blocked* | Red | `#B60205` |

---

## 8. GitHub CLI Commands

Create all labels in a new repo:

```bash
# Agent labels
gh label create "agent:claude" --color "7B68EE" --description "Claude Code for architecture, specs, and code generation"
gh label create "agent:copilot" --color "7B68EE" --description "GitHub Copilot for simple inline fixes"
gh label create "agent:cursor" --color "7B68EE" --description "Cursor IDE for multi-file refactors"
gh label create "agent:warp" --color "7B68EE" --description "Warp Terminal for CLI/DevOps tasks"
gh label create "agent:manual" --color "7B68EE" --description "Reserved for human work"
gh label create "agent:research" --color "7B68EE" --description "Research or planning tasks"

# Scope labels
gh label create "scope:frontend" --color "0366D6" --description "UI / Views / Components / Styling"
gh label create "scope:backend" --color "0366D6" --description "Business logic / Services / Controllers"
gh label create "scope:api" --color "0366D6" --description "API routes / Endpoints / Networking"
gh label create "scope:data" --color "0366D6" --description "Models / Entities / Database / Repositories"
gh label create "scope:infra" --color "0366D6" --description "Infrastructure / CI/CD / GitHub Actions"
gh label create "scope:devops" --color "0366D6" --description "Build systems / Pipelines / Packaging"
gh label create "scope:tests" --color "0366D6" --description "Unit / Integration / E2E tests"
gh label create "scope:docs" --color "0366D6" --description "Documentation / READMEs"

# Difficulty labels
gh label create "difficulty:easy" --color "28A745" --description "Simple inline fixes, small patches"
gh label create "difficulty:medium" --color "FFC107" --description "Single-file changes"
gh label create "difficulty:hard" --color "FD7E14" --description "Multi-file work, refactors"
gh label create "difficulty:extreme" --color "DC3545" --description "Architecture-level or module rewrites"

# Status labels
gh label create "status:ready" --color "C2E0C6" --description "Issue ready to be worked"
gh label create "status:assigned" --color "BFD4F2" --description "Assigned to agent, waiting for execution"
gh label create "status:in-progress" --color "0075CA" --description "Agent actively working"
gh label create "status:review" --color "D4C5F9" --description "PR created, awaiting review"
gh label create "status:changes-requested" --color "FBCA04" --description "PR needs updates"
gh label create "status:done" --color "0E8A16" --description "Issue completed"
gh label create "status:deferred" --color "6A737D" --description "Pushed to later milestone"

# Blocking labels
gh label create "blocked" --color "B60205" --description "Cannot work this issue yet"
```

---

## Usage with Claude Code

When creating milestones and issues, apply labels following this pattern:

1. **Assign agent** - Who will work this? (`agent:claude`, `agent:manual`, etc.)
2. **Set scope** - What area of code? (`scope:backend`, `scope:data`, etc.)
3. **Set difficulty** - How complex? (`difficulty:medium`, etc.)
4. **Set status** - Current state (`status:ready` for new issues)
5. **Add dependencies** - If blocked, add `blocked` or note in body

Claude Code will respect these labels when working issues and creating PRs.
