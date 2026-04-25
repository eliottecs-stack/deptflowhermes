import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.agents.scoring import LeadScorer
from deptflow_sdr.config import load_runtime_config
from deptflow_sdr.domain.normalizers import normalize_lead, normalize_posts


class ScoringTest(unittest.TestCase):
    def test_qualified_fixture_lead(self):
        runtime = load_runtime_config(ROOT)
        people = json.loads((ROOT / "tests/fixtures/bereach_search_people.json").read_text())["items"]
        posts_by_profile = json.loads((ROOT / "tests/fixtures/bereach_posts_by_profile.json").read_text())

        lead = normalize_lead(people[0])
        posts = normalize_posts(posts_by_profile["claire-martin-demo"])
        score = LeadScorer(runtime.icp, runtime.campaign).score(lead, posts)

        self.assertTrue(score.qualified)
        self.assertGreaterEqual(score.total, 75)
        self.assertIn(score.tier, {"HOT", "VERY_HOT", "WARM"})

    def test_excluded_student_rejected(self):
        runtime = load_runtime_config(ROOT)
        people = json.loads((ROOT / "tests/fixtures/bereach_search_people.json").read_text())["items"]
        lead = normalize_lead(people[1])
        score = LeadScorer(runtime.icp, runtime.campaign).score(lead, [])
        self.assertFalse(score.qualified)
        self.assertEqual(score.tier, "REJECTED")


if __name__ == "__main__":
    unittest.main()
