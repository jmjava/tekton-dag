from protocol import estimate_pod_count
from cluster import clone_manifests, intercept_manifests


def test_manifests_include_width_and_entry():
    clone = clone_manifests("ns", 3, "demo-fe")
    assert clone.count("kind: Deployment") == 3
    assert "name: entry" in clone
    assert "pr/demo-fe/app-0" in clone
    assert "eval.tektondag.io/role: echo" in clone
    intercept = intercept_manifests("ns", 2, "demo-fe")
    assert intercept.count("kind: Deployment") == 4  # 2 baseline + pr + router
    assert "header-router" in intercept
    assert "BASELINE_URL" in intercept
    assert "eval.tektondag.io/role: router" in intercept
    assert estimate_pod_count("intercept", 2) == 4
