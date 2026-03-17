"""
Stack resolver: loads stack YAMLs and builds a repo-to-stack mapping.

Replaces the hardcoded CEL overlays in triggers.yaml and the static
stacks/registry.yaml with a dynamic, in-memory registry.
"""

import os
import logging

import yaml

logger = logging.getLogger("orchestrator.resolver")


class StackResolver:
    """Loads stack definitions and resolves repo names to stacks and apps."""

    def __init__(self, stacks_dir="/stacks", teams_dir="/teams"):
        self._stacks_dir = stacks_dir
        self._teams_dir = teams_dir
        self._stacks = {}
        self._repo_map = {}
        self._teams = {}
        self.reload()

    def reload(self):
        """Reload all stack and team configs from disk."""
        self._stacks = {}
        self._repo_map = {}
        self._teams = {}

        self._load_stacks(self._stacks_dir)
        self._load_teams(self._teams_dir)

        logger.info(
            "Loaded %d stacks, %d repo mappings, %d teams",
            len(self._stacks),
            len(self._repo_map),
            len(self._teams),
        )

    def _load_stacks(self, stacks_dir):
        if not os.path.isdir(stacks_dir):
            logger.warning("Stacks dir not found: %s", stacks_dir)
            return

        for fname in os.listdir(stacks_dir):
            if not fname.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(stacks_dir, fname)
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
                logger.info("  Loaded stack: %s (%d apps)", stack_file, len(stack.get("apps", [])))
            except Exception as e:
                logger.error("Failed to load stack %s: %s", path, e)

    def _load_teams(self, teams_dir):
        if not os.path.isdir(teams_dir):
            logger.info("No teams dir: %s (single-team mode)", teams_dir)
            return

        for team_name in os.listdir(teams_dir):
            team_path = os.path.join(teams_dir, team_name)
            if not os.path.isdir(team_path):
                continue
            config_path = os.path.join(team_path, "team.yaml")
            if not os.path.isfile(config_path):
                continue
            try:
                with open(config_path) as f:
                    team_config = yaml.safe_load(f)
                self._teams[team_name] = team_config
                logger.info("  Loaded team: %s", team_name)
            except Exception as e:
                logger.error("Failed to load team %s: %s", config_path, e)

    def resolve_repo(self, repo_name):
        """
        Resolve a repository name to its stack and app.

        Args:
            repo_name: GitHub repo name (e.g. "tekton-dag-vue-fe")

        Returns:
            dict with {stack_file, app_name, repo} or None
        """
        return self._repo_map.get(repo_name)

    def get_stack(self, stack_file):
        """Get a loaded stack definition by its file path."""
        return self._stacks.get(stack_file)

    def list_stacks(self):
        """Return all loaded stacks with their apps."""
        result = []
        for stack_file, stack in self._stacks.items():
            apps = [
                {"name": a["name"], "repo": a.get("repo", ""), "role": a.get("role", "")}
                for a in stack.get("apps", [])
            ]
            result.append({
                "stack_file": stack_file,
                "name": stack.get("name", ""),
                "description": stack.get("description", ""),
                "apps": apps,
            })
        return result

    def list_teams(self):
        """Return all loaded team configs."""
        return dict(self._teams)

    def get_build_apps(self, stack_file):
        """Get the space-separated build-apps list for a stack."""
        stack = self._stacks.get(stack_file)
        if not stack:
            return ""
        return " ".join(a["name"] for a in stack.get("apps", []))
