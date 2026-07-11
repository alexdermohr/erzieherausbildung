from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.build_source_summary import build_summary


class SourceSummaryTests(unittest.TestCase):
    def test_build_summary_is_deterministic_and_skips_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "erzieherausbildung"
            (root / "b").mkdir(parents=True)
            (root / "a").mkdir()
            (root / "a" / "one.pdf").write_bytes(b"eins")
            (root / "a" / "two.txt").write_bytes(b"zwei")
            (root / "b" / "three.md").write_bytes(b"drei")
            (root / "a" / "outside.txt").symlink_to("/etc/passwd")
            outside_directory = Path(temp_dir) / "outside"
            outside_directory.mkdir()
            (outside_directory / "hidden.txt").write_text("nicht lesen", encoding="utf-8")
            (root / "b" / "outside-dir").symlink_to(
                outside_directory, target_is_directory=True
            )

            summary = build_summary(root)

            self.assertEqual(summary["totals"]["files"], 3)
            self.assertEqual(summary["totals"]["bytes"], 12)
            self.assertEqual(
                summary["totals"]["extensions"], {"md": 1, "pdf": 1, "txt": 1}
            )
            self.assertEqual(
                [cluster["title"] for cluster in summary["clusters"]], ["a", "b"]
            )

    def test_build_summary_rejects_missing_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "erzieherausbildung"
            with self.assertRaisesRegex(SystemExit, "source root is not a directory"):
                build_summary(root)

    def test_build_summary_rejects_wrong_root_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "wrong-name"
            root.mkdir()
            with self.assertRaisesRegex(SystemExit, "wrong source root"):
                build_summary(root)


if __name__ == "__main__":
    unittest.main()
