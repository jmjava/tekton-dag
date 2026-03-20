"""Tests for github_client.py — mocks the requests library."""

from unittest.mock import patch, MagicMock

import github_client


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(response=resp)
    return resp


@patch("github_client.requests.get")
def test_list_branches(mock_get):
    mock_get.return_value = _mock_response([
        {"name": "main", "commit": {"sha": "abc123"}},
        {"name": "feature", "commit": {"sha": "def456"}},
    ])

    result = github_client.list_branches("jmjava", "tekton-dag")
    assert len(result) == 2
    assert result[0] == {"name": "main", "sha": "abc123"}
    assert result[1] == {"name": "feature", "sha": "def456"}


@patch("github_client.requests.get")
def test_list_tags(mock_get):
    mock_get.return_value = _mock_response([
        {"name": "v1.0", "commit": {"sha": "aaa"}},
    ])

    result = github_client.list_tags("jmjava", "tekton-dag")
    assert len(result) == 1
    assert result[0]["name"] == "v1.0"


@patch("github_client.requests.get")
def test_list_commits(mock_get):
    mock_get.return_value = _mock_response([
        {
            "sha": "abc123",
            "commit": {"message": "Initial commit\n\nBody", "author": {"date": "2026-01-01T00:00:00Z"}},
            "html_url": "https://github.com/jmjava/tekton-dag/commit/abc123",
        },
    ])

    result = github_client.list_commits("jmjava", "tekton-dag")
    assert len(result) == 1
    assert result[0]["sha"] == "abc123"
    assert result[0]["message"] == "Initial commit"
    assert result[0]["date"] == "2026-01-01T00:00:00Z"


@patch("github_client.requests.get")
def test_list_prs(mock_get):
    mock_get.return_value = _mock_response([
        {"number": 1, "title": "Fix bug", "state": "open", "html_url": "https://github.com/pr/1"},
        {"number": 2, "title": "Add feature", "state": "open", "html_url": "https://github.com/pr/2"},
    ])

    result = github_client.list_prs("jmjava", "tekton-dag")
    assert len(result) == 2
    assert result[0]["number"] == 1
    assert result[0]["title"] == "Fix bug"


@patch("github_client.requests.get")
def test_list_prs_all_repos(mock_get):
    mock_get.return_value = _mock_response([
        {"number": 10, "title": "PR in repo", "state": "open", "html_url": "https://url"},
    ])

    repos = [
        {"id": "r1", "owner": "jmjava", "repo": "tekton-dag", "apps": ["demo-fe"]},
        {"id": "r2", "owner": "jmjava", "repo": "tekton-dag-flask", "apps": ["demo-api"]},
    ]
    items, queried, skipped = github_client.list_prs_all_repos(repos)
    assert len(items) == 2
    assert queried == ["r1", "r2"]
    assert skipped == []
    assert items[0]["repoId"] == "r1"
    assert items[0]["pr"]["number"] == 10


@patch("github_client.requests.get")
def test_list_prs_all_repos_with_error(mock_get):
    mock_get.side_effect = Exception("rate limited")

    repos = [{"id": "r1", "owner": "o", "repo": "r", "apps": []}]
    items, queried, skipped = github_client.list_prs_all_repos(repos)
    assert items == []
    assert queried == ["r1"]
    assert len(skipped) == 1
    assert skipped[0]["id"] == "r1"


@patch("github_client.requests.get")
def test_headers_with_token(mock_get):
    mock_get.return_value = _mock_response([])

    github_client.list_branches("o", "r", token="ghp_test123")
    call_args = mock_get.call_args
    headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
    assert headers["Authorization"] == "Bearer ghp_test123"


@patch.dict("os.environ", {"GITHUB_TOKEN": ""})
@patch("github_client.requests.get")
def test_headers_without_token(mock_get):
    mock_get.return_value = _mock_response([])

    github_client.list_branches("o", "r")
    call_args = mock_get.call_args
    headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
    assert "Authorization" not in headers
