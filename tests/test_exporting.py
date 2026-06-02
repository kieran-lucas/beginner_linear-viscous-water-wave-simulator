import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from wave_lab.exporting import (
    readable_snapshot_text,
    save_image,
    snapshot_payload,
    suggested_filename,
    write_diagnostics_csv,
    write_snapshot_json,
)
from wave_lab.settings import LabSettings
from wave_lab.simulation import DiagnosticSample


class ExportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diagnostic = DiagnosticSample(
            time=1.25,
            maximum_amplitude=0.45,
            energy=2.5,
            normalized_energy=0.625,
        )

    def test_suggested_filename_contains_kind_and_timestamp(self) -> None:
        filename = suggested_filename("wave-view", "png", datetime(2026, 6, 3, 14, 5, 9))

        self.assertEqual(filename, "viscous-wave-lab-wave-view-20260603-140509.png")

    def test_snapshot_json_is_human_readable_and_includes_compare_settings(self) -> None:
        payload = snapshot_payload(
            LabSettings(),
            self.diagnostic,
            settings_b=LabSettings(damping_rate=0.8),
            diagnostic_b=self.diagnostic,
            now=datetime(2026, 6, 3, 14, 5, 9),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = write_snapshot_json(Path(directory) / "snapshot.json", payload)
            text = path.read_text(encoding="utf-8")
            loaded = json.loads(text)

        self.assertIn("\n  ", text)
        self.assertEqual(loaded["simulation_a"]["settings"]["boundary_condition"], "fixed")
        self.assertEqual(loaded["simulation_b"]["settings"]["damping_rate_per_s"], 0.8)
        self.assertEqual(loaded["simulation_a"]["diagnostics"]["time_s"], 1.25)

    def test_readable_snapshot_text_uses_units_and_diagnostics(self) -> None:
        text = readable_snapshot_text(LabSettings(), self.diagnostic)

        self.assertIn("Model: u_tt + gamma * u_t = c^2 * u_xx", text)
        self.assertIn("Wave speed: 3 m/s", text)
        self.assertIn("Damping rate: 0.16 1/s", text)
        self.assertIn("Approximate normalized energy: 62.5%", text)

    def test_diagnostics_csv_exports_a_and_b_histories(self) -> None:
        compare = DiagnosticSample(1.5, 0.3, 1.5, 0.375)

        with tempfile.TemporaryDirectory() as directory:
            path = write_diagnostics_csv(
                Path(directory) / "diagnostics.csv",
                [self.diagnostic],
                [compare],
            )
            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(rows[0]["a_time_s"], "1.25")
        self.assertEqual(rows[0]["b_maximum_amplitude_m"], "0.3")
        self.assertEqual(rows[0]["b_normalized_energy"], "0.375")

    def test_image_save_failure_is_reported(self) -> None:
        class FailingImage:
            def save(self, _path: str) -> bool:
                return False

        with self.assertRaisesRegex(OSError, "Could not save image"):
            save_image("wave.png", FailingImage())


if __name__ == "__main__":
    unittest.main()
