"""Unit tests for cluster probe helpers (no Kind required)."""

from __future__ import annotations

import io
import unittest
from unittest.mock import MagicMock, patch

from cluster import curl_entry


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


if __name__ == "__main__":
    unittest.main()
