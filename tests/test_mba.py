from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MBA = ROOT / "bin" / "mba"


class MbaCliTest(unittest.TestCase):
    def test_adversarial_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "Thuion.md").write_text(
                "[[Distinction]] [[Source and Mystery]] [[Memory as Coherence Bias]]\n",
                encoding="utf-8",
            )
            (vault / "Distinction.md").write_text("# Distinction\n", encoding="utf-8")
            (vault / "Source and Mystery.md").write_text("# Source and Mystery\n", encoding="utf-8")
            (vault / "Memory as Coherence Bias.md").write_text("# Memory as Coherence Bias\n", encoding="utf-8")
            (vault / "Life and Evolution.md").write_text("# Life and Evolution\n", encoding="utf-8")
            (vault / "Primordial Geometry.md").write_text("# Primordial Geometry\n", encoding="utf-8")
            (vault / "Light as Projection Constraint.md").write_text("# Light as Projection Constraint\n", encoding="utf-8")

            result = subprocess.run(
                [str(MBA), "adversarial", "--vault", str(vault), "--seed", "Thuion.md"],
                check=True,
                text=True,
                capture_output=True,
            )

            report_path = vault / ".markov" / "adversarial-evaluation.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["seedPath"], "Thuion.md")
            self.assertEqual(len(report["probes"]), 6)
            self.assertIn("underconstrained", result.stdout)


if __name__ == "__main__":
    unittest.main()
