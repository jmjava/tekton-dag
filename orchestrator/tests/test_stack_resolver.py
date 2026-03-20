"""Unit tests for StackResolver with real YAML on tmp_path."""

import textwrap

import pytest

from stack_resolver import StackResolver


def _write(p, content):
    p.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


@pytest.fixture
def stack_and_team_dirs(tmp_path):
    stacks = tmp_path / "stacks"
    teams = tmp_path / "teams"
    stacks.mkdir()
    teams.mkdir()
    return stacks, teams


def test_init_loads_stacks_and_teams(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "alpha.yaml",
        """
        name: Alpha Stack
        description: First stack
        apps:
          - name: frontend
            repo: github.com/acme/tekton-dag-vue-fe
            role: ui
          - name: api
            repo: acme/api-service
            role: backend
        """,
    )
    team_dir = teams / "squad-one"
    team_dir.mkdir()
    _write(
        team_dir / "team.yaml",
        """
        display_name: Squad One
        repos:
          - tekton-dag-vue-fe
        """,
    )

    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))

    assert r.resolve_repo("tekton-dag-vue-fe") == {
        "stack_file": "stacks/alpha.yaml",
        "app_name": "frontend",
        "repo": "github.com/acme/tekton-dag-vue-fe",
    }
    assert r.resolve_repo("api-service") == {
        "stack_file": "stacks/alpha.yaml",
        "app_name": "api",
        "repo": "acme/api-service",
    }
    assert "squad-one" in r.list_teams()
    assert r.list_teams()["squad-one"]["display_name"] == "Squad One"


def test_resolve_repo_unknown_returns_none(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "only.yaml",
        """
        name: X
        apps:
          - name: a
            repo: org/only-repo
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.resolve_repo("missing-repo") is None


def test_list_stacks_summaries(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "one.yaml",
        """
        name: One
        description: Desc
        apps:
          - name: app1
            repo: r1
            role: worker
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    lst = r.list_stacks()
    assert len(lst) == 1
    assert lst[0]["stack_file"] == "stacks/one.yaml"
    assert lst[0]["name"] == "One"
    assert lst[0]["description"] == "Desc"
    assert lst[0]["apps"] == [{"name": "app1", "repo": "r1", "role": "worker"}]


def test_get_build_apps(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "b.yaml",
        """
        name: B
        apps:
          - name: x
            repo: a/x
          - name: y
            repo: a/y
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.get_build_apps("stacks/b.yaml") == "x y"
    assert r.get_build_apps("stacks/missing.yaml") == ""


def test_get_stack(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "c.yaml",
        """
        name: C
        apps: []
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.get_stack("stacks/c.yaml")["name"] == "C"
    assert r.get_stack("stacks/nope.yaml") is None


def test_reload_clears_and_reloads(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "first.yaml",
        """
        name: First
        apps:
          - name: only
            repo: org/only
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.resolve_repo("only") is not None

    (stacks / "first.yaml").unlink()
    _write(
        stacks / "second.yaml",
        """
        name: Second
        apps:
          - name: newapp
            repo: org/newapp
        """,
    )
    r.reload()
    assert r.resolve_repo("only") is None
    assert r.resolve_repo("newapp")["app_name"] == "newapp"


def test_missing_stacks_dir(stack_and_team_dirs):
    _, teams = stack_and_team_dirs
    missing = "/nonexistent/stacks-path"
    r = StackResolver(stacks_dir=missing, teams_dir=str(teams))
    assert r.list_stacks() == []
    assert r._repo_map == {}


def test_missing_teams_dir(stack_and_team_dirs):
    stacks, _ = stack_and_team_dirs
    _write(
        stacks / "t.yaml",
        """
        name: T
        apps:
          - name: a
            repo: z/a
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir="/no/teams/here")
    assert r.list_teams() == {}


def test_skips_non_yaml_files(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "good.yaml",
        """
        name: G
        apps:
          - name: a
            repo: x/a
        """,
    )
    (stacks / "readme.txt").write_text("no", encoding="utf-8")
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert len(r.list_stacks()) == 1


def test_skips_stack_without_apps_list(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "bad.yaml",
        """
        name: Bad
        apps: not-a-list
        """,
    )
    _write(
        stacks / "empty.yaml",
        """
        name: Empty
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.list_stacks() == []


def test_skips_app_without_repo_or_name(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "partial.yaml",
        """
        name: P
        apps:
          - name: ok
            repo: org/ok
          - name: ""
            repo: org/x
          - name: nor
            repo: ""
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.resolve_repo("ok") is not None
    assert r.resolve_repo("x") is None
    assert r.resolve_repo("nor") is None


def test_yml_extension(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    _write(
        stacks / "legacy.yml",
        """
        name: L
        apps:
          - name: svc
            repo: hello/world-svc
        """,
    )
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.resolve_repo("world-svc")["stack_file"] == "stacks/legacy.yml"


def test_team_subdir_without_team_yaml_ignored(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    (teams / "empty-team").mkdir()
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.list_teams() == {}


def test_malformed_stack_yaml_does_not_crash(stack_and_team_dirs):
    stacks, teams = stack_and_team_dirs
    (stacks / "broken.yaml").write_text("{ not valid yaml :::", encoding="utf-8")
    r = StackResolver(stacks_dir=str(stacks), teams_dir=str(teams))
    assert r.list_stacks() == []
