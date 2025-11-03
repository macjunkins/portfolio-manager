"""
Project Utilities

Shared utilities for working with project configuration, git repositories,
and generating reports.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml
from git import Repo, InvalidGitRepositoryError
from git.exc import GitCommandError


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load and parse the YAML configuration file.

    Args:
        config_path: Path to config.yaml (relative to script location)

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    # Get the absolute path to the config file
    script_dir = Path(__file__).parent.parent
    full_path = script_dir / config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")

    with open(full_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def get_git_info(repo_path: str) -> Dict[str, Any]:
    """
    Get git repository information from local filesystem.

    Args:
        repo_path: Path to git repository

    Returns:
        Dictionary with git info:
        - is_git_repo: bool
        - current_branch: str or None
        - latest_commit: dict or None
        - is_dirty: bool (uncommitted changes)
        - error: str or None

    Why local git operations?
    - GitHub API has rate limits, local git doesn't
    - Faster for local repository state
    - Can check for uncommitted changes
    """
    result = {
        "is_git_repo": False,
        "current_branch": None,
        "latest_commit": None,
        "is_dirty": False,
        "error": None
    }

    if not os.path.exists(repo_path):
        result["error"] = f"Path does not exist: {repo_path}"
        return result

    try:
        repo = Repo(repo_path)
        result["is_git_repo"] = True
        result["is_dirty"] = repo.is_dirty()

        # Get current branch
        if not repo.head.is_detached:
            result["current_branch"] = repo.active_branch.name
        else:
            result["current_branch"] = "DETACHED"

        # Get latest commit
        if repo.head.is_valid():
            latest = repo.head.commit
            result["latest_commit"] = {
                "sha": latest.hexsha[:7],
                "message": latest.message.strip().split('\n')[0],  # First line only
                "author": str(latest.author),
                "date": datetime.fromtimestamp(latest.committed_date).isoformat(),
                "days_ago": (datetime.now() - datetime.fromtimestamp(latest.committed_date)).days
            }

    except InvalidGitRepositoryError:
        result["error"] = "Not a git repository"
    except GitCommandError as e:
        result["error"] = f"Git command error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result


def check_roadmap_exists(repo_path: str) -> Dict[str, Any]:
    """
    Check if ROADMAP.md exists in the repository.

    Args:
        repo_path: Path to repository

    Returns:
        Dictionary with:
        - exists: bool
        - path: str or None
        - last_modified: str or None
    """
    roadmap_variants = ["ROADMAP.md", "roadmap.md", "Roadmap.md"]

    for variant in roadmap_variants:
        roadmap_path = Path(repo_path) / variant
        if roadmap_path.exists():
            stat = roadmap_path.stat()
            return {
                "exists": True,
                "path": str(roadmap_path),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

    return {
        "exists": False,
        "path": None,
        "last_modified": None
    }


def parse_github_repo(github_repo: str) -> tuple[str, str]:
    """
    Parse GitHub repository string into owner and name.

    Args:
        github_repo: Repository string in format "owner/name"

    Returns:
        Tuple of (owner, name)

    Raises:
        ValueError: If repo string is invalid format
    """
    parts = github_repo.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid GitHub repo format: {github_repo}. Expected 'owner/name'")

    return parts[0], parts[1]


def format_date(date_str: Optional[str], format_type: str = "short") -> str:
    """
    Format ISO date string for display.

    Args:
        date_str: ISO format date string
        format_type: "short" (YYYY-MM-DD) or "relative" (X days ago)

    Returns:
        Formatted date string
    """
    if not date_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        if format_type == "short":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "relative":
            days_ago = (datetime.now(dt.tzinfo) - dt).days
            if days_ago == 0:
                return "Today"
            elif days_ago == 1:
                return "Yesterday"
            elif days_ago < 7:
                return f"{days_ago} days ago"
            elif days_ago < 30:
                weeks = days_ago // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif days_ago < 365:
                months = days_ago // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = days_ago // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    except (ValueError, AttributeError):
        return str(date_str)


def get_priority_emoji(priority: str) -> str:
    """
    Get emoji for priority level.

    Args:
        priority: Priority string (critical, high, medium, low)

    Returns:
        Emoji string
    """
    priority_map = {
        "critical": "🚨",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
        "none": "⚪",
        "unknown": "❓"
    }
    return priority_map.get(priority.lower(), "❓")


def get_pillar_emoji(pillar: str) -> str:
    """
    Get emoji for strategic pillar.

    Args:
        pillar: Pillar name (revenue, infrastructure, consistency, cleanup, innovation)

    Returns:
        Emoji string
    """
    pillar_map = {
        "revenue": "🚨",
        "infrastructure": "🚀",
        "consistency": "📺",
        "cleanup": "🟡",
        "innovation": "🔬"
    }
    return pillar_map.get(pillar.lower(), "📦")


def calculate_health_score(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a health score for a project based on various metrics.

    Scoring factors:
    - Recent commits (activity level)
    - Issue backlog (too many open issues is bad)
    - Roadmap existence
    - Milestone progress
    - Days since last update

    Args:
        project_data: Combined project data (git + GitHub)

    Returns:
        Dictionary with:
        - score: int (0-100)
        - status: str (healthy, warning, critical, unknown)
        - reasons: list of str (why this score)
    """
    score = 100
    reasons = []
    status = "healthy"

    # Factor 1: Recent activity (0-30 points penalty)
    git_info = project_data.get("git", {})
    latest_commit = git_info.get("latest_commit")
    if latest_commit:
        days_ago = latest_commit.get("days_ago", 999)
        if days_ago > 90:
            score -= 30
            reasons.append(f"⚠️ No commits in {days_ago} days")
            status = "critical"
        elif days_ago > 30:
            score -= 15
            reasons.append(f"⚠️ Last commit {days_ago} days ago")
            if status == "healthy":
                status = "warning"
        elif days_ago > 7:
            score -= 5
            reasons.append(f"Last commit {days_ago} days ago")
    else:
        score -= 30
        reasons.append("⚠️ No commit history found")
        status = "critical"

    # Factor 2: Roadmap existence (0-20 points penalty)
    if not project_data.get("has_roadmap", False):
        score -= 20
        reasons.append("⚠️ No ROADMAP.md found")
        if status == "healthy":
            status = "warning"

    # Factor 3: Open issues (0-20 points penalty)
    total_issues = project_data.get("total_open_issues", 0)
    if total_issues > 50:
        score -= 20
        reasons.append(f"⚠️ {total_issues} open issues (backlog growing)")
        if status == "healthy":
            status = "warning"
    elif total_issues > 20:
        score -= 10
        reasons.append(f"{total_issues} open issues")

    # Factor 4: Milestone progress (0-15 points penalty)
    milestones = project_data.get("milestones", [])
    if milestones:
        stalled_milestones = [m for m in milestones if m.get("progress", 0) == 0 and m.get("open_issues", 0) > 0]
        if stalled_milestones:
            score -= 15
            reasons.append(f"⚠️ {len(stalled_milestones)} stalled milestone(s)")
            if status == "healthy":
                status = "warning"

    # Factor 5: Uncommitted changes (0-15 points penalty)
    if git_info.get("is_dirty", False):
        score -= 15
        reasons.append("⚠️ Uncommitted changes detected")

    # Ensure score stays in 0-100 range
    score = max(0, min(100, score))

    # Adjust status based on final score
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"

    if not reasons:
        reasons.append("✅ All metrics healthy")

    return {
        "score": score,
        "status": status,
        "reasons": reasons
    }