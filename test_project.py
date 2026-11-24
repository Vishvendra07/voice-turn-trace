import json
import unittest
from pathlib import Path
from project import report, summarize


class TraceTests(unittest.TestCase):
    def test_overlap_and_interruption_accounting(self):
        source = json.loads(Path(__file__).with_name("fixtures.json").read_text())
        output = report(source)
        first, _, interrupted, _ = output["turns"]
        self.assertGreater(sum(first["stages_ms"].values()), first["wall_ms"])
        self.assertEqual(interrupted["post_interrupt_playback_ms"], 3)
        self.assertEqual(output["completed_only"], {"n": 3, "first_audio_p95_ms": 955})

    def test_rejects_duplicate_stage(self):
        with self.assertRaises(ValueError):
            summarize({"id": "x", "spans": [("inference", 0, 1), ("inference", 1, 2)]})
