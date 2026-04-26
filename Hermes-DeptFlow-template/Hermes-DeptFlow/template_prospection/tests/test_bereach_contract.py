from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.config import Settings
from deptflow_sdr.integrations.bereach_client import BeReachClient


class RecordingBeReachClient(BeReachClient):
    def __init__(self):
        settings = Settings(
            root_dir=ROOT,
            environment="test",
            dry_run=True,
            use_bereach_in_dry_run=False,
            bereach_base_url="https://api.bereach.ai",
            bereach_api_key="brc_test",
            bereach_auth_header="Authorization",
            bereach_auth_scheme="Bearer",
            bereach_timeout_seconds=30,
            bereach_max_retries=0,
            supabase_url="",
            supabase_service_key="",
            data_dir=ROOT / "data",
            reports_dir=ROOT / "reports",
            logs_dir=ROOT / "logs",
        )
        super().__init__(settings)
        self.calls = []

    def _request(self, method, path, payload=None, params=None):
        self.calls.append({"method": method, "path": path, "payload": payload, "params": params})
        return {"ok": True}


class BeReachContractTest(unittest.TestCase):
    def test_people_search_uses_dedicated_people_endpoint(self):
        client = RecordingBeReachClient()
        client.search_people("CEO SaaS France", count=30)
        call = client.calls[-1]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/search/linkedin/people")
        self.assertEqual(call["payload"]["keywords"], "CEO SaaS France")
        self.assertEqual(call["payload"]["count"], 25)

    def test_connect_profile_sends_no_note_by_default(self):
        client = RecordingBeReachClient()
        client.connect_profile("https://linkedin.com/in/claire")
        call = client.calls[-1]
        self.assertEqual(call["path"], "/connect/linkedin/profile")
        self.assertEqual(call["payload"], {"profile": "https://linkedin.com/in/claire"})

    def test_limits_endpoint_is_available_for_safe_budgeting(self):
        client = RecordingBeReachClient()
        client.get_limits()
        call = client.calls[-1]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["path"], "/me/limits")


if __name__ == "__main__":
    unittest.main()
