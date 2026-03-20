"""
GitHub API client using requests.

All functions accept an optional token parameter; if not provided,
they fall back to the GITHUB_TOKEN environment variable.
"""

import os
import logging

import requests

logger = logging.getLogger("mgmt.github")

GITHUB_API = "https://api.github.com"


def _headers(token=None):
    token = token or os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(path, token=None):
    url = f"{GITHUB_API}{path}"
    r = requests.get(url, headers=_headers(token), timeout=15)
    r.raise_for_status()
    return r.json()


def list_branches(owner, repo, token=None):
    data = _get(f"/repos/{owner}/{repo}/branches?per_page=30", token)
    return [{"name": b["name"], "sha": b.get("commit", {}).get("sha")} for b in data]


def list_tags(owner, repo, token=None):
    data = _get(f"/repos/{owner}/{repo}/tags?per_page=30", token)
    return [{"name": t["name"], "sha": t.get("commit", {}).get("sha")} for t in data]


def list_commits(owner, repo, token=None):
    data = _get(f"/repos/{owner}/{repo}/commits?per_page=20", token)
    return [
        {
            "sha": c["sha"],
            "message": (c.get("commit", {}).get("message") or "").split("\n")[0],
            "date": c.get("commit", {}).get("author", {}).get("date"),
            "url": c.get("html_url"),
        }
        for c in data
    ]


def list_prs(owner, repo, state="open", token=None):
    data = _get(
        f"/repos/{owner}/{repo}/pulls?state={state}&per_page=30&sort=updated",
        token,
    )
    return [
        {
            "number": p["number"],
            "title": p["title"],
            "state": p["state"],
            "url": p.get("html_url"),
        }
        for p in data
    ]


def list_prs_all_repos(repos, state="open", token=None):
    """
    Fetch PRs across a list of repos.

    Args:
        repos: list of {"id", "owner", "repo", "apps", "stacks"} dicts
        state: "open", "closed", or "all"
        token: GitHub token override

    Returns:
        (items, repos_queried, repos_skipped)
    """
    items = []
    repos_queried = []
    repos_skipped = []

    for r in repos[:50]:
        repos_queried.append(r["id"])
        try:
            prs = list_prs(r["owner"], r["repo"], state=state, token=token)
            for pr in prs:
                items.append({
                    "repoId": r["id"],
                    "owner": r["owner"],
                    "repo": r["repo"],
                    "apps": r.get("apps", []),
                    "pr": pr,
                })
        except Exception as e:
            repos_skipped.append({"id": r["id"], "error": str(e)})
            logger.warning("Skipped %s: %s", r["id"], e)

    return items, repos_queried, repos_skipped
