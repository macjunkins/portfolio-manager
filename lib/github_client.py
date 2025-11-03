"""
GitHub GraphQL API Client

Provides a sophisticated wrapper around the GitHub GraphQL API using the gql library.
Handles authentication, rate limiting, and provides clean methods for querying
repository data.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError


class GitHubClient:
    """
    GitHub GraphQL API client with methods for querying repository data.

    Why GraphQL?
    - More efficient than REST (single request for multiple data points)
    - Precise data fetching (only get what we need)
    - Better rate limit usage
    - Strong typing and validation
    """

    def __init__(self, token: str):
        """
        Initialize the GitHub GraphQL client.

        Args:
            token: GitHub Personal Access Token with repo, read:org, read:user scopes
        """
        self.token = token

        # Set up the GraphQL transport with authentication
        self.transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Create the GraphQL client
        self.client = Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        )

    async def get_repository_overview(
        self,
        owner: str,
        name: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Get comprehensive repository overview including:
        - Latest commits (last N days)
        - Open issues by priority
        - Milestones and their completion status
        - Repository metadata (stars, forks, etc.)

        Args:
            owner: Repository owner (username or org name)
            name: Repository name
            lookback_days: How many days back to look for commits (default: 90)

        Returns:
            Dictionary with repository data
        """
        # Calculate the date for commit lookback
        since_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()

        query = gql("""
            query GetRepositoryOverview($owner: String!, $name: String!, $since: GitTimestamp) {
              repository(owner: $owner, name: $name) {
                name
                description
                url
                createdAt
                updatedAt
                pushedAt

                # Repository stats
                stargazerCount
                forkCount

                # Check for ROADMAP.md
                roadmap: object(expression: "HEAD:ROADMAP.md") {
                  ... on Blob {
                    text
                  }
                }

                # Latest commits
                defaultBranchRef {
                  name
                  target {
                    ... on Commit {
                      history(first: 10, since: $since) {
                        totalCount
                        edges {
                          node {
                            oid
                            messageHeadline
                            committedDate
                            author {
                              name
                              email
                              date
                            }
                          }
                        }
                      }
                    }
                  }
                }

                # Open issues
                issues(states: OPEN, first: 100) {
                  totalCount
                  edges {
                    node {
                      number
                      title
                      createdAt
                      updatedAt
                      labels(first: 10) {
                        edges {
                          node {
                            name
                          }
                        }
                      }
                    }
                  }
                }

                # Milestones
                milestones(first: 20, states: OPEN) {
                  edges {
                    node {
                      title
                      description
                      dueOn
                      state
                      progressPercentage
                      createdAt
                      updatedAt
                      closedIssues: issues(states: CLOSED) {
                        totalCount
                      }
                      openIssues: issues(states: OPEN) {
                        totalCount
                      }
                    }
                  }
                }

                # Pull requests
                pullRequests(states: OPEN, first: 10) {
                  totalCount
                }
              }

              # Rate limit info
              rateLimit {
                limit
                cost
                remaining
                resetAt
              }
            }
        """)

        variables = {
            "owner": owner,
            "name": name,
            "since": since_date
        }

        try:
            async with self.client as session:
                result = await session.execute(query, variable_values=variables)
                return self._process_repository_data(result)
        except TransportQueryError as e:
            # Handle GraphQL errors (e.g., repository not found, permission issues)
            return {
                "error": str(e),
                "owner": owner,
                "name": name
            }

    def _process_repository_data(self, raw_data: Dict) -> Dict[str, Any]:
        """
        Process raw GraphQL response into a clean, usable format.

        Args:
            raw_data: Raw GraphQL response

        Returns:
            Cleaned and structured repository data
        """
        repo = raw_data.get("repository", {})

        if not repo:
            return {"error": "Repository not found or inaccessible"}

        # Extract commit data
        commits = []
        default_branch = repo.get("defaultBranchRef", {})
        if default_branch and default_branch.get("target"):
            history = default_branch["target"].get("history", {})
            commits = [
                {
                    "sha": edge["node"]["oid"][:7],
                    "message": edge["node"]["messageHeadline"],
                    "date": edge["node"]["committedDate"],
                    "author": edge["node"]["author"]["name"]
                }
                for edge in history.get("edges", [])
            ]

        # Extract issue data with priority labels
        issues_by_priority = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "none": []
        }

        for edge in repo.get("issues", {}).get("edges", []):
            issue = edge["node"]
            labels = [label["node"]["name"].lower() for label in issue.get("labels", {}).get("edges", [])]

            # Determine priority from labels
            priority = "none"
            for label in labels:
                if "critical" in label or "p0" in label:
                    priority = "critical"
                    break
                elif "high" in label or "p1" in label:
                    priority = "high"
                    break
                elif "medium" in label or "p2" in label:
                    priority = "medium"
                    break
                elif "low" in label or "p3" in label:
                    priority = "low"
                    break

            issues_by_priority[priority].append({
                "number": issue["number"],
                "title": issue["title"],
                "created": issue["createdAt"],
                "updated": issue["updatedAt"]
            })

        # Extract milestone data
        milestones = []
        for edge in repo.get("milestones", {}).get("edges", []):
            milestone = edge["node"]
            milestones.append({
                "title": milestone["title"],
                "description": milestone.get("description", ""),
                "due_date": milestone.get("dueOn"),
                "state": milestone["state"],
                "progress": milestone.get("progressPercentage", 0),
                "open_issues": milestone["openIssues"]["totalCount"],
                "closed_issues": milestone["closedIssues"]["totalCount"]
            })

        # Check for roadmap file
        has_roadmap = bool(repo.get("roadmap"))

        return {
            "name": repo["name"],
            "description": repo.get("description", ""),
            "url": repo["url"],
            "created_at": repo["createdAt"],
            "updated_at": repo["updatedAt"],
            "pushed_at": repo["pushedAt"],
            "stars": repo["stargazerCount"],
            "forks": repo["forkCount"],
            "default_branch": default_branch.get("name", "main"),
            "has_roadmap": has_roadmap,
            "commits": commits,
            "total_commits": default_branch.get("target", {}).get("history", {}).get("totalCount", 0) if default_branch else 0,
            "issues": issues_by_priority,
            "total_open_issues": repo.get("issues", {}).get("totalCount", 0),
            "milestones": milestones,
            "open_pull_requests": repo.get("pullRequests", {}).get("totalCount", 0),
            "rate_limit": raw_data.get("rateLimit", {})
        }

    async def get_multiple_repositories(
        self,
        repos: List[Dict[str, str]],
        lookback_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get data for multiple repositories efficiently.

        Args:
            repos: List of dicts with 'owner' and 'name' keys
            lookback_days: How many days back to look for commits

        Returns:
            List of repository data dictionaries
        """
        results = []

        for repo in repos:
            owner = repo.get("owner")
            name = repo.get("name")

            if not owner or not name:
                results.append({"error": "Missing owner or name", "repo": repo})
                continue

            data = await self.get_repository_overview(owner, name, lookback_days)

            # Add metadata from the input
            data["pillar"] = repo.get("pillar", "unknown")
            data["priority"] = repo.get("priority", "unknown")
            data["local_path"] = repo.get("path", "")

            results.append(data)

        return results

    async def close(self):
        """Close the GraphQL client and cleanup resources."""
        await self.transport.close()


def create_client(token: Optional[str] = None) -> GitHubClient:
    """
    Create a GitHub GraphQL client with token from environment or parameter.

    Args:
        token: GitHub token (if not provided, reads from GITHUB_TOKEN env var)

    Returns:
        Configured GitHubClient instance

    Raises:
        ValueError: If no token is provided or found in environment
    """
    if token is None:
        token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError(
            "GitHub token not found. Please set GITHUB_TOKEN environment variable "
            "or pass token parameter."
        )

    return GitHubClient(token)