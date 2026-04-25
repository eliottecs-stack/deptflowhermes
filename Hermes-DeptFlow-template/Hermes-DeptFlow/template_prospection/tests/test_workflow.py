from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.workflows.daily_prospecting import DailyProspectingWorkflow


class WorkflowTest(unittest.TestCase):
    def test_dry_run_completes(self):
        workflow = DailyProspectingWorkflow(ROOT, dry_run=True)
        result = workflow.run(limit=3)
        self.assertTrue(result["dry_run"])
        self.assertGreaterEqual(result["discovered"], 1)
        self.assertTrue(Path(result["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
