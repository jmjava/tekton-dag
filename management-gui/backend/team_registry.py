"""
Team registry: loads teams/*/team.yaml configs and resolves
cluster context + namespace for each team.

Each team.yaml defines:
  name, namespace, cluster (kubeconfig context), imageRegistry,
  cacheRepo, interceptBackend, maxConcurrentRuns, maxParallelBuilds, stacks
"""

import os
import logging

import yaml

logger = logging.getLogger("mgmt.teams")


class TeamRegistry:
    """Loads team configs and resolves cluster context per team."""

    def __init__(self, teams_dir, team_filter="*"):
        """
        Args:
            teams_dir: path to teams/ directory containing <name>/team.yaml
            team_filter: "*" to load all teams, or a specific team name
        """
        self._teams_dir = teams_dir
        self._team_filter = team_filter
        self._teams = {}
        self.reload()

    def reload(self):
        self._teams = {}
        if not os.path.isdir(self._teams_dir):
            logger.warning("Teams dir not found: %s", self._teams_dir)
            return

        for team_name in sorted(os.listdir(self._teams_dir)):
            if self._team_filter != "*" and team_name != self._team_filter:
                continue
            team_path = os.path.join(self._teams_dir, team_name)
            if not os.path.isdir(team_path):
                continue
            config_path = os.path.join(team_path, "team.yaml")
            if not os.path.isfile(config_path):
                continue
            try:
                with open(config_path) as f:
                    team_config = yaml.safe_load(f)
                self._teams[team_name] = team_config
                logger.info("Loaded team: %s (cluster=%s)", team_name,
                            team_config.get("cluster", "default"))
            except Exception as e:
                logger.error("Failed to load team %s: %s", config_path, e)

        logger.info("Team registry: %d team(s) loaded", len(self._teams))

    def list_teams(self):
        """Return list of team summary dicts."""
        result = []
        for name, cfg in self._teams.items():
            result.append({
                "name": name,
                "namespace": cfg.get("namespace", "tekton-pipelines"),
                "cluster": cfg.get("cluster", ""),
                "imageRegistry": cfg.get("imageRegistry", ""),
                "stacks": cfg.get("stacks", []),
            })
        return result

    def get_team(self, name):
        """Get full team config by name, or None."""
        return self._teams.get(name)

    def resolve_context(self, team_name):
        """
        Resolve a team name to (kubeconfig_context, namespace).
        Returns (None, default_namespace) if team not found.
        """
        team = self._teams.get(team_name)
        if not team:
            return None, "tekton-pipelines"
        return team.get("cluster"), team.get("namespace", "tekton-pipelines")

    @property
    def single_team_mode(self):
        return self._team_filter != "*"
