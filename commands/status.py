#!/usr/bin/env python3
"""
Portfolio Status Dashboard (Terminal Only)

Generates a comprehensive status report for all projects in the portfolio and prints it to the terminal. No files are written.

Features:
- Latest commits by project (with configurable lookback period)
- Roadmap status (exists vs missing)
- Milestone completion percentages
- Open issue counts by priority
- Health scores for each project
- Summary by strategic pillar

Usage:
    python scripts/portfolio_status.py
    python scripts/portfolio_status.py --lookback 30  # Last 30 days only
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import argparse

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.github_client import create_client
from lib.project_utils import (
    load_config,
    get_git_info,
    check_roadmap_exists,
    parse_github_repo,
    format_date,
    get_priority_emoji,
    get_pillar_emoji,
    calculate_health_score
)

console = Console()


def print_terminal_report(data: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    lookback_days = config.get("reports", {}).get("commit_lookback_days", 90)

    console.print(Panel.fit(
        f"[bold]Portfolio Status[/bold]\n[dim]Commit lookback: Last {lookback_days} days[/dim]",
        border_style="blue"
    ))

    # Top-level summary
    total_projects = len(data)
    healthy_projects = len([p for p in data if p.get("health", {}).get("status") == "healthy"])
    warning_projects = len([p for p in data if p.get("health", {}).get("status") == "warning"])
    critical_projects = len([p for p in data if p.get("health", {}).get("status") == "critical"])

    summary = Table(show_header=False, box=None, padding=(0,1))
    summary.add_row("Total Projects", str(total_projects))
    summary.add_row("Healthy ✅", str(healthy_projects))
    summary.add_row("Warning ⚠️", str(warning_projects))
    summary.add_row("Critical 🚨", str(critical_projects))
    console.print(summary)
    console.print()

    # Per-project detail table
    table = Table(title="Projects", show_lines=False)
    table.add_column("Name")
    table.add_column("Priority", justify="center")
    table.add_column("Health", justify="center")
    table.add_column("Latest Commit", overflow="fold")
    table.add_column("Issues", justify="right")

    for project in data:
        name = project.get("name", "Unknown")
        priority = project.get("priority", "unknown")
        priority_emoji = get_priority_emoji(priority)

        health = project.get("health", {})
        status = health.get("status", "unknown")
        score = health.get("score", 0)
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🚨",
            "unknown": "❓"
        }.get(status, "❓")

        git_info = project.get("git", {})
        latest = git_info.get("latest_commit")
        if latest:
            latest_str = f"{latest['sha']} — {latest['message']} (by {latest['author']}, {latest['days_ago']}d ago)"
        else:
            latest_str = "No commits found"

        total_issues = project.get("total_open_issues", 0)

        table.add_row(
            name,
            f"{priority_emoji} {priority.title()}",
            f"{status_emoji} {score}/100",
            latest_str,
            str(total_issues)
        )

    console.print(table)

    console.print()
    console.print("[dim]Note: Roadmap presence, milestones, and issue breakdowns are included in the health score and can be expanded later if needed.[/dim]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Portfolio Status — terminal report only (no files are written)."
    )
    parser.add_argument(
        "--lookback", "-l", type=int,
        help="Number of days to look back for commits (overrides config)"
    )
    return parser.parse_args()


async def gather_project_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Gather data for all projects from both local git and GitHub API.

    Args:
        config: Configuration dictionary

    Returns:
        List of project data dictionaries
    """
    projects = config.get("projects", [])
    lookback_days = config.get("reports", {}).get("commit_lookback_days", 90)

    # Initialize GitHub client
    github_client = create_client()

    # Prepare repository list for batch GitHub query while preserving original project indices
    github_repos = []
    repo_index_map: List[int] = []
    for idx, project in enumerate(projects):
        try:
            owner, name = parse_github_repo(project.get("github_repo", ""))
            github_repos.append({
                "owner": owner,
                "name": name,
                "pillar": project.get("pillar", "unknown"),
                "priority": project.get("priority", "unknown"),
                "path": project.get("path", "")
            })
            repo_index_map.append(idx)
        except (ValueError, KeyError) as e:
            console.print(f"[red]Error parsing {project.get('name', 'unknown')}: {e}[/red]")

    # Fetch GitHub data (only if we have repos)
    github_data = []
    try:
        if github_repos:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching GitHub data...", total=None)
                github_data = await github_client.get_multiple_repositories(github_repos, lookback_days)
                progress.update(task, completed=True)
        else:
            console.print("[yellow]No valid GitHub repositories to query.[/yellow]")

        # Map GitHub data back to original project indices
        github_by_index: Dict[int, Dict[str, Any]] = {}
        for j, info in enumerate(github_data or []):
            if j < len(repo_index_map):
                github_by_index[repo_index_map[j]] = info

        # Combine with local git data
        combined_data = []
        for i, project in enumerate(projects):
            project_info = {
                "name": project.get("name", "Unknown"),
                "description": project.get("description", ""),
                "pillar": project.get("pillar", "unknown"),
                "priority": project.get("priority", "unknown"),
                "path": project.get("path", ""),
            }

            # Add local git info
            console.print(f"Checking local git: {project_info['name']}")
            git_path = project.get("path", "")
            git_info = get_git_info(git_path) if git_path else {}
            project_info["git"] = git_info

            # Add local roadmap check
            roadmap_info = check_roadmap_exists(git_path) if git_path else {"exists": False}
            project_info["local_roadmap"] = roadmap_info

            # Merge with GitHub data if available
            github_info = github_by_index.get(i)
            if github_info:
                if "error" not in github_info:
                    project_info.update(github_info)
                else:
                    project_info["github_error"] = github_info["error"]

            # Calculate health score
            project_info["health"] = calculate_health_score(project_info)

            combined_data.append(project_info)

        return combined_data
    finally:
        await github_client.close()


def generate_markdown_report(data: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    """
    Generate a markdown report from project data.

    Args:
        data: List of project data dictionaries
        config: Configuration dictionary

    Returns:
        Markdown formatted report as string
    """
    today = datetime.now().strftime(config.get("reports", {}).get("date_format", "%Y-%m-%d"))
    lookback_days = config.get("reports", {}).get("commit_lookback_days", 90)

    # Start building the report
    lines = [
        f"# Portfolio Status Report",
        f"**Generated:** {today}",
        f"**Commit Lookback:** Last {lookback_days} days",
        "",
        "---",
        "",
    ]

    # Executive Summary
    lines.extend([
        "## Executive Summary",
        "",
    ])

    total_projects = len(data)
    healthy_projects = len([p for p in data if p.get("health", {}).get("status") == "healthy"])
    warning_projects = len([p for p in data if p.get("health", {}).get("status") == "warning"])
    critical_projects = len([p for p in data if p.get("health", {}).get("status") == "critical"])

    lines.extend([
        f"- **Total Projects:** {total_projects}",
        f"- **Healthy:** {healthy_projects} ✅",
        f"- **Warning:** {warning_projects} ⚠️",
        f"- **Critical:** {critical_projects} 🚨",
        "",
    ])

    # Group by pillar
    pillars = {}
    for project in data:
        pillar = project.get("pillar", "unknown")
        if pillar not in pillars:
            pillars[pillar] = []
        pillars[pillar].append(project)

    # Pillar order (from meta-roadmap)
    pillar_order = ["revenue", "infrastructure", "consistency", "cleanup", "innovation", "unknown"]

    for pillar in pillar_order:
        if pillar not in pillars:
            continue

        pillar_projects = pillars[pillar]
        pillar_emoji = get_pillar_emoji(pillar)

        lines.extend([
            f"## {pillar_emoji} {pillar.title()} Projects",
            "",
        ])

        for project in pillar_projects:
            lines.extend(generate_project_section(project))

    # Footer
    lines.extend([
        "---",
        "",
        f"**Report generated by:** `portfolio_status.py`",
        f"**Owner:** John Junkins (@macjunkins)",
        "",
    ])

    return "\n".join(lines)


def generate_project_section(project: Dict[str, Any]) -> List[str]:
    """
    Generate markdown section for a single project.

    Args:
        project: Project data dictionary

    Returns:
        List of markdown lines
    """
    lines = []

    # Project header
    name = project.get("name", "Unknown")
    priority = project.get("priority", "unknown")
    priority_emoji = get_priority_emoji(priority)
    health = project.get("health", {})
    health_status = health.get("status", "unknown")
    health_score = health.get("score", 0)

    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🚨",
        "unknown": "❓"
    }.get(health_status, "❓")

    lines.extend([
        f"### {priority_emoji} {name}",
        "",
        f"**Priority:** {priority.title()} | **Health:** {status_emoji} {health_score}/100 ({health_status.upper()})",
        "",
    ])

    # Description
    if project.get("description"):
        lines.append(f"**Description:** {project['description']}")
        lines.append("")

    # GitHub info
    if project.get("url"):
        lines.append(f"**Repository:** [{project['url']}]({project['url']})")
        lines.append("")

    # Latest commit
    git_info = project.get("git", {})
    latest_commit = git_info.get("latest_commit")
    if latest_commit:
        lines.extend([
            f"**Latest Commit:** `{latest_commit['sha']}` - {latest_commit['message']}",
            f"  - **Author:** {latest_commit['author']}",
            f"  - **Date:** {format_date(latest_commit['date'], 'short')} ({latest_commit['days_ago']} days ago)",
            "",
        ])
    else:
        lines.append("**Latest Commit:** ❌ No commits found")
        lines.append("")

    # Roadmap status
    has_roadmap = project.get("has_roadmap", False) or project.get("local_roadmap", {}).get("exists", False)
    roadmap_status = "✅ Exists" if has_roadmap else "❌ Missing"
    lines.append(f"**Roadmap:** {roadmap_status}")
    lines.append("")

    # Milestones
    milestones = project.get("milestones", [])
    if milestones:
        lines.append("**Milestones:**")
        for milestone in milestones[:5]:  # Show max 5
            progress = milestone.get("progress", 0)
            title = milestone.get("title", "Untitled")
            open_issues = milestone.get("open_issues", 0)
            closed_issues = milestone.get("closed_issues", 0)
            total = open_issues + closed_issues
            due_date = format_date(milestone.get("due_date"), "short") if milestone.get("due_date") else "No due date"

            lines.append(f"  - **{title}** ({progress}% complete) - {closed_issues}/{total} issues closed - Due: {due_date}")
        lines.append("")
    else:
        lines.append("**Milestones:** None defined")
        lines.append("")

    # Open issues by priority
    issues = project.get("issues", {})
    total_issues = project.get("total_open_issues", 0)
    if total_issues > 0:
        lines.append(f"**Open Issues:** {total_issues} total")
        for priority in ["critical", "high", "medium", "low"]:
            count = len(issues.get(priority, []))
            if count > 0:
                emoji = get_priority_emoji(priority)
                lines.append(f"  - {emoji} {priority.title()}: {count}")
        lines.append("")
    else:
        lines.append("**Open Issues:** None")
        lines.append("")

    # Health reasons
    health_reasons = health.get("reasons", [])
    if health_reasons:
        lines.append("**Health Notes:**")
        for reason in health_reasons:
            lines.append(f"  - {reason}")
        lines.append("")

    lines.append("---")
    lines.append("")

    return lines


async def main():
    """Main entry point for the portfolio status script."""
    console.print("[bold blue]Portfolio Status Dashboard Generator[/bold blue]")
    console.print("")

    # Parse CLI args
    args = parse_args()

    # Load environment variables from script directory (not current working directory)
    script_dir = Path(__file__).parent.parent
    dotenv_path = script_dir / ".env"
    load_dotenv(dotenv_path)

    # Check for GitHub token
    if not os.getenv("GITHUB_TOKEN"):
        console.print("[red]ERROR: GITHUB_TOKEN not found in environment variables.[/red]")
        console.print("Please create a .env file with your GitHub Personal Access Token:")
        console.print("  GITHUB_TOKEN=your_token_here")
        console.print("")
        console.print("Or export it in your shell:")
        console.print("  export GITHUB_TOKEN=your_token_here")
        return 1

    try:
        # Load configuration
        console.print("Loading configuration...")
        config = load_config()

        # Apply CLI overrides
        reports_cfg = config.setdefault("reports", {})
        if args.lookback is not None:
            reports_cfg["commit_lookback_days"] = max(0, int(args.lookback))

        # Early exit if no projects
        if not config.get("projects"):
            console.print("[yellow]No projects found in configuration. Nothing to do.[/yellow]")
            return 0

        # Gather project data
        console.print("Gathering project data...")
        project_data = await gather_project_data(config)

        # Render terminal-only report (no files written)
        console.print("Rendering terminal report...")
        print_terminal_report(project_data, config)

        # Print summary
        console.print("")
        console.print("[bold]Quick Summary:[/bold]")
        for project in project_data:
            name = project.get("name", "Unknown")
            health = project.get("health", {})
            status = health.get("status", "unknown")
            score = health.get("score", 0)

            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "🚨",
                "unknown": "❓"
            }.get(status, "❓")

            console.print(f"  {status_emoji} {name}: {score}/100")

        return 0

    except Exception as e:
        console.print(f"[red]ERROR: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))