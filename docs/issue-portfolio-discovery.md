### Description
Implement dynamic project discovery so the portfolio status dashboard no longer depends on a hardcoded project list. Instead, scan a root directory for local Git repositories, derive GitHub repo info from the `origin` remote, and feed the discovered project list into the existing reporting pipeline.

Requested: 2025-11-01 21:37 local

---

### Goal
Make the portfolio status dynamic by discovering projects from a parent directory of local repos (e.g., `~/GitHub`), deriving GitHub `owner/repo` from each folder’s `origin` remote, and using that list in the existing report. Keep current config behavior as fallback and add opt-in flags/config.

### Scope of Work
- Add repo discovery via filesystem scan (subfolders with a `.git` directory)
- Parse `origin` to get `owner/repo` for GitHub aggregation
- Introduce CLI flags for discovery and root selection
- Optional: support config-driven discovery and per-repo metadata overrides
- Update docs and provide tests

### High-Level Design
1. Discovery function returns project dicts compatible with the current pipeline: `name`, `path`, `github_repo`, `pillar`, `priority`, `description`.
2. `main()` chooses projects:
   - If `--discover` is set, run discovery and use results when non-empty.
   - If not set but `config["projects"]` is empty, auto-run discovery.
   - If discovery yields 0 repos, fall back to config (and show a warning).
3. Existing data gathering (local git + GitHub) and health scoring remain unchanged.

### Implementation Steps
1) CLI additions in `parse_args()`:
```python
parser.add_argument(
    "--discover", action="store_true",
    help="Discover projects by scanning a root directory for Git repos (defaults to parent of this repo)."
)
parser.add_argument(
    "--root", type=str,
    help="Root directory to scan when using --discover. Defaults to the parent directory containing this repo."
)
```

2) Discovery utilities (new helpers):
- Imports: `subprocess`, `re`
- `_parse_origin_to_owner_repo(origin_url: str) -> str` supports SSH/HTTPS forms and returns `"owner/repo"` for GitHub remotes.
- `discover_projects(root_dir: Path, *, exclude: list[str] | None = None, include_hidden: bool = False)`:
  - Iterate non-hidden subdirectories
  - Include those with a `.git` directory
  - `git -C <dir> config --get remote.origin.url` → parse to `github_repo` if GitHub; otherwise `""`
  - Return list with defaults: `pillar="unknown"`, `priority="unknown"`, `description=""`

3) Wire into `main()`:
- Compute `default_discovery_root` as the parent of the current repo directory.
- Determine `should_discover` from `--discover` or when `config["projects"]` is empty (or config `discover.enabled`).
- If discovering, pick root from `--root`, config `discover.root`, or default; call `discover_projects()`; if any found, set `config["projects"]` to them.

4) Optional config-driven discovery (overridden by CLI):
```json
{
  "discover": {
    "enabled": true,
    "root": "~/GitHub",
    "exclude": ["personal-scripts", ".archive", "_templates"],
    "include_hidden": false,
    "depth": 1
  }
}
```

5) Documentation:
- README: document `--discover`, `--root`, config block, behavior notes, and examples.

6) Tests:
- Unit tests for origin parsing, including SSH/HTTPS variants and non-GitHub remotes
- Functional test for discovery using a temp directory
- Integration smoke test for discovery path and legacy config-based behavior

### Behavior and Edge Cases
- Non-GitHub remotes: included for local info; `github_repo` empty → skipped for GitHub API calls
- Missing/non-standard `origin`: keep project; only skip GitHub calls
- Performance: one `git config` per repo; GitHub calls remain batched
- Prevent self-inclusion if desired: provide `exclude` denylist

### Acceptance Criteria
- Running `python scripts/portfolio_status.py` with empty `projects` discovers repos under default root and prints a terminal report without errors.
- `python scripts/portfolio_status.py --discover --root ~/GitHub` discovers repos under `~/GitHub` and prints a report.
- Repos with non-GitHub or missing `origin` appear with local git info and health; GitHub sections omitted without crashing.
- Existing config-based project lists continue to work as-is.
- README documents flags and behavior.

### Rollout Plan
1. Implement helpers and flags; wire into `main()` guarded by flags/config
2. Update README
3. Add unit/functional tests for parsing and discovery
4. Manual verification on local repo sets

### Nice-to-Have (Post-MVP)
- Depth-limited recursive discovery
- `.portfolio.json` per-repo metadata for `name/description/pillar/priority`
- Glob-based allowlist/denylist
- Cache discovery results to `.cache/portfolio_discovery.json`
- Concurrency for origin lookups if needed

---

### How to Use (after implementation)
- Auto-discovery when config has no projects:
  - `python scripts/portfolio_status.py`
- Force discovery and choose a root:
  - `python scripts/portfolio_status.py --discover --root ~/GitHub`
- Combine with a custom lookback:
  - `python scripts/portfolio_status.py --discover --root ~/GitHub --lookback 30`
