"""
Stack resolver: loads stacks/*.yaml and provides stack listing,
repo-to-stack mapping, and DAG extraction for visualization.

Adapted from orchestrator/stack_resolver.py with added get_dag().
"""

import os
import logging

import yaml

logger = logging.getLogger("mgmt.stacks")


class StackResolver:
    """Loads stack definitions, resolves repos, and extracts DAG structure."""

    def __init__(self, stacks_dir):
        self._stacks_dir = stacks_dir
        self._stacks = {}
        self._repo_map = {}
        self.reload()

    def reload(self):
        self._stacks = {}
        self._repo_map = {}

        if not os.path.isdir(self._stacks_dir):
            logger.warning("Stacks dir not found: %s", self._stacks_dir)
            return

        for fname in sorted(os.listdir(self._stacks_dir)):
            if not fname.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(self._stacks_dir, fname)
            try:
                with open(path) as f:
                    stack = yaml.safe_load(f)
                if not stack or not isinstance(stack.get("apps"), list):
                    continue
                stack_file = f"stacks/{fname}"
                self._stacks[stack_file] = stack
                for app in stack.get("apps", []):
                    repo = app.get("repo", "")
                    app_name = app.get("name", "")
                    if repo and app_name:
                        repo_short = repo.split("/")[-1] if "/" in repo else repo
                        self._repo_map[repo_short] = {
                            "stack_file": stack_file,
                            "app_name": app_name,
                            "repo": repo,
                        }
                logger.info("Loaded stack: %s (%d apps)", stack_file,
                            len(stack.get("apps", [])))
            except Exception as e:
                logger.error("Failed to load stack %s: %s", path, e)

        logger.info("Stack resolver: %d stacks, %d repo mappings",
                     len(self._stacks), len(self._repo_map))

    def list_stacks(self, allowed_stacks=None):
        """
        Return all loaded stacks (optionally filtered to an allow-list).

        Args:
            allowed_stacks: list of stack_file strings (from team config),
                            or None to return all.
        """
        result = []
        for stack_file, stack in self._stacks.items():
            if allowed_stacks and stack_file not in allowed_stacks:
                continue
            apps = [
                {
                    "name": a["name"],
                    "repo": a.get("repo", ""),
                    "role": a.get("role", ""),
                    "propagationRole": a.get("propagation-role", ""),
                }
                for a in stack.get("apps", [])
            ]
            result.append({
                "stack_file": stack_file,
                "name": stack.get("name", ""),
                "description": stack.get("description", ""),
                "apps": apps,
            })
        return result

    def get_stack(self, stack_file):
        """Get raw stack definition by file path."""
        return self._stacks.get(stack_file)

    def get_dag(self, stack_file):
        """
        Extract DAG nodes and edges for visualization.

        Returns:
            {"nodes": [...], "edges": [...]} or None if stack not found.
            Each node: {"id": "demo-fe", "role": "frontend",
                        "propagationRole": "originator", "repo": "..."}
            Each edge: {"source": "demo-fe", "target": "release-lifecycle-demo"}
        """
        stack = self._stacks.get(stack_file)
        if not stack:
            return None

        nodes = []
        edges = []
        for app in stack.get("apps", []):
            name = app.get("name", "")
            nodes.append({
                "id": name,
                "role": app.get("role", ""),
                "propagationRole": app.get("propagation-role", ""),
                "repo": app.get("repo", ""),
                "build": app.get("build", {}).get("tool", ""),
                "runtime": app.get("build", {}).get("runtime", ""),
            })
            for downstream in app.get("downstream", []):
                edges.append({"source": name, "target": downstream})

        return {"nodes": nodes, "edges": edges}

    def get_all_repos(self):
        """Build a list of all repos across stacks (for Git view)."""
        repo_set = {}
        for stack_file, stack in self._stacks.items():
            for app in stack.get("apps", []):
                repo = app.get("repo", "")
                if not repo or "/" not in repo:
                    continue
                owner, repo_name = repo.split("/", 1)
                repo_id = f"{owner}/{repo_name}"
                if repo_id not in repo_set:
                    repo_set[repo_id] = {
                        "id": repo_id,
                        "owner": owner,
                        "repo": repo_name,
                        "apps": [],
                        "stacks": [],
                    }
                entry = repo_set[repo_id]
                app_name = app.get("name", "")
                if app_name and app_name not in entry["apps"]:
                    entry["apps"].append(app_name)
                if stack_file not in entry["stacks"]:
                    entry["stacks"].append(stack_file)
        return list(repo_set.values())

    def resolve_repo(self, repo_name):
        """Resolve a repo short name to {stack_file, app_name, repo}."""
        return self._repo_map.get(repo_name)
