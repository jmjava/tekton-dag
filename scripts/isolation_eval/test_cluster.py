"""Unit tests for cluster probe helpers (no Kind required)."""

from __future__ import annotations

import io
import unittest
from unittest.mock import MagicMock, patch

from cluster import curl_entry, wait_ready


class CurlEntryTests(unittest.TestCase):
    def test_port_forward_returns_body(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdout = io.StringIO("")

        class FakeResp:
            def read(self) -> bytes:
                return b"pr/demo-fe/app-0\n"

            def __enter__(self) -> "FakeResp":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        with (
            patch("cluster.subprocess.Popen", return_value=proc) as popen,
            patch("cluster._free_port", return_value=18080),
            patch("cluster.urllib.request.urlopen", return_value=FakeResp()),
        ):
            self.assertEqual(curl_entry("demo-ns", True), "pr/demo-fe/app-0")

        argv = popen.call_args[0][0]
        self.assertEqual(argv[:5], ["kubectl", "-n", "demo-ns", "port-forward", "svc/entry"])
        self.assertIn("18080:80", argv)
        proc.terminate.assert_called()

    def test_port_forward_exit_is_probe_error(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = 1
        proc.stdout = io.StringIO("forward failed\n")

        with (
            patch("cluster.subprocess.Popen", return_value=proc),
            patch("cluster._free_port", return_value=18081),
            patch(
                "cluster.urllib.request.urlopen",
                side_effect=OSError("connection refused"),
            ),
        ):
            out = curl_entry("demo-ns", False)
        self.assertTrue(out.startswith("probe-error:port-forward:"))
        proc.terminate.assert_called()


class WaitReadyTests(unittest.TestCase):
    def test_polls_until_pods_exist_then_waits(self) -> None:
        empty = MagicMock(returncode=1, stdout="", stderr="No resources found")
        listed = MagicMock(returncode=0, stdout="app-0-xxx   1/1   Running\n")
        waited = MagicMock(returncode=0, stdout="", stderr="")
        calls = {"n": 0}

        def fake_run(args, **kwargs):
            if args[:2] == ["kubectl", "get"]:
                calls["n"] += 1
                return empty if calls["n"] == 1 else listed
            if args[:2] == ["kubectl", "wait"]:
                return waited
            raise AssertionError(args)

        with patch("cluster.subprocess.run", side_effect=fake_run):
            wait_ready("eval-ns", timeout_s=5)
        self.assertEqual(calls["n"], 2)


if __name__ == "__main__":
    unittest.main()
