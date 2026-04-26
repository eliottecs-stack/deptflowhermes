from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.control_plane.crm import GoogleSheetsSync
from deptflow_sdr.control_plane.gates import GoLiveGate
from deptflow_sdr.control_plane.profiles import ProfileFactory
from deptflow_sdr.control_plane.registry import Registry
from deptflow_sdr.control_plane.service import ControlPlaneService
from deptflow_sdr.control_plane.vault import Vault


class ControlPlaneTest(unittest.TestCase):
    def test_registry_creates_clients_profiles_and_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Registry(Path(tmp) / "deptflow.db")
            client_id = registry.create_client("Acme France", market="France B2B")
            profile_id = registry.create_profile(client_id, "acme-france")
            release_id = registry.create_release(
                profile_id,
                template_version="0.2.0",
                config_snapshot={"client": {"name": "Acme France"}},
                prompt_snapshot={"SOUL.md": "Mission SDR"},
            )
            registry.record_quota_event(client_id, "linkedin_connection", used=7, limit=20)

            client = registry.get_client(client_id)
            release = registry.get_release(release_id)
            quotas = registry.quota_usage(client_id, "linkedin_connection")

            self.assertEqual(client["name"], "Acme France")
            self.assertEqual(release["profile_id"], profile_id)
            self.assertEqual(release["config_snapshot"]["client"]["name"], "Acme France")
            self.assertEqual(quotas["used"], 7)
            self.assertEqual(quotas["limit"], 20)

    def test_vault_encrypts_values_without_plaintext_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.json"
            vault = Vault(path, passphrase="local-dev-passphrase")
            vault.set_secret("client_1", "BEREACH_API_KEY", "brc_secret_value")

            raw = path.read_text(encoding="utf-8")
            reloaded = Vault(path, passphrase="local-dev-passphrase")

            self.assertNotIn("brc_secret_value", raw)
            self.assertEqual(reloaded.get_secret("client_1", "BEREACH_API_KEY"), "brc_secret_value")

    def test_profile_factory_generates_hermes_profile_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "profiles"
            profile_path = ProfileFactory(ROOT).create_profile(
                target_dir=target,
                profile_slug="client-acme",
                client={
                    "name": "Acme France",
                    "offer_name": "Audit Pipeline",
                    "offer_description": "Aide les CEO B2B à prioriser les opportunités.",
                    "value_proposition": "Identifier les prospects chauds chaque semaine.",
                },
                icp={
                    "target_roles": ["CEO", "Founder"],
                    "target_industries": ["SaaS"],
                    "target_locations": ["France"],
                    "excluded_keywords": ["student"],
                    "competitors": [],
                },
                campaign={"daily_connection_limit": 20, "timezone": "Europe/Paris"},
            )

            manifest = json.loads((profile_path / "profile.manifest.json").read_text(encoding="utf-8"))
            env_template = (profile_path / ".env.template").read_text(encoding="utf-8")
            icp_config = json.loads((profile_path / "icp_config.yaml").read_text(encoding="utf-8"))

            self.assertEqual(manifest["profile_slug"], "client-acme")
            self.assertEqual(manifest["hermes"]["entrypoint"], "scripts/start_dashboard.py")
            self.assertIn("BEREACH_API_KEY=", env_template)
            self.assertNotIn("brc_", env_template)
            self.assertEqual(icp_config["client"]["name"], "Acme France")
            self.assertEqual(icp_config["icp"]["target_roles"], ["CEO", "Founder"])

    def test_go_live_gate_requires_dry_run_ten_approvals_and_quotas(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Registry(Path(tmp) / "deptflow.db")
            client_id = registry.create_client("Acme France")
            profile_id = registry.create_profile(client_id, "acme-france")
            gate = GoLiveGate(registry)

            blocked = gate.evaluate(profile_id)
            self.assertFalse(blocked.allowed)
            self.assertIn("dry-run validé", " ".join(blocked.reasons))

            registry.record_run(profile_id, dry_run=True, status="completed", summary={"qualified": 12})
            for index in range(10):
                registry.upsert_lead(
                    profile_id,
                    lead_key=f"lead-{index}",
                    full_name=f"Lead {index}",
                    linkedin_url=f"https://linkedin.com/in/lead-{index}",
                    score_total=80,
                    tier="HOT",
                    status="approved",
                )
            registry.set_profile_limits(profile_id, daily_connection_limit=20)

            allowed = gate.evaluate(profile_id)
            self.assertTrue(allowed.allowed)
            self.assertEqual(allowed.reasons, [])

    def test_google_sheets_sync_builds_crm_rows_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Registry(Path(tmp) / "deptflow.db")
            client_id = registry.create_client("Acme France")
            profile_id = registry.create_profile(client_id, "acme-france")
            registry.upsert_lead(
                profile_id,
                lead_key="https://linkedin.com/in/claire",
                full_name="Claire Martin",
                linkedin_url="https://linkedin.com/in/claire",
                score_total=91,
                tier="VERY_HOT",
                status="connection_ready",
                message_body="Bonjour Claire, message personnalisé.",
            )
            rows = GoogleSheetsSync(registry).build_rows(profile_id)

            self.assertEqual(rows[0][0:6], ["Nom", "LinkedIn", "Score", "Tier", "Statut", "Message"])
            self.assertEqual(rows[1][0], "Claire Martin")
            self.assertEqual(rows[1][2], 91)
            self.assertNotIn("BEREACH", " ".join(str(cell) for row in rows for cell in row))

    def test_connection_requests_are_blocked_by_gate_then_sent_under_quota(self):
        class FakeBeReach:
            def __init__(self):
                self.connected: list[str] = []

            def get_limits(self):
                return {"connectionRequests": {"remaining": 2}}

            def connect_profile(self, profile: str, note: str | None = None):
                self.connected.append(profile)
                return {"ok": True}

        with tempfile.TemporaryDirectory() as tmp:
            registry = Registry(Path(tmp) / "deptflow.db")
            client_id = registry.create_client("Acme France")
            profile_id = registry.create_profile(client_id, "acme-france")
            service = ControlPlaneService(registry)

            with self.assertRaises(RuntimeError):
                service.send_connection_requests(profile_id, FakeBeReach(), max_count=5)

            registry.record_run(profile_id, dry_run=True, status="completed", summary={"qualified": 12})
            registry.set_profile_limits(profile_id, daily_connection_limit=20)
            for index in range(10):
                registry.upsert_lead(
                    profile_id,
                    lead_key=f"lead-{index}",
                    full_name=f"Lead {index}",
                    linkedin_url=f"https://linkedin.com/in/lead-{index}",
                    score_total=80,
                    tier="HOT",
                    status="connection_ready",
                )

            fake = FakeBeReach()
            outcome = service.send_connection_requests(profile_id, fake, max_count=5)

            self.assertEqual(outcome.sent, 2)
            self.assertEqual(len(fake.connected), 2)
            self.assertEqual(registry.quota_usage(client_id, "linkedin_connection")["used"], 2)
            self.assertEqual(registry.list_leads(profile_id, status="connected")[0]["status"], "connected")

    def test_service_runs_dry_run_and_imports_leads_to_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry = Registry(tmp_path / "deptflow.db")
            client_id = registry.create_client("Acme France")
            profile_id = registry.create_profile(client_id, "acme-france")
            profile_path = ProfileFactory(ROOT).create_profile(
                target_dir=tmp_path / "profiles",
                profile_slug="acme-france",
                client={
                    "name": "Acme France",
                    "offer_name": "Audit Pipeline",
                    "offer_description": "Aide les CEO B2B à prioriser les opportunités.",
                    "value_proposition": "Identifier les prospects chauds.",
                },
                icp={
                    "target_roles": ["CEO", "Founder"],
                    "target_industries": ["SaaS"],
                    "target_locations": ["France"],
                    "excluded_keywords": ["student"],
                    "queries": ['"CEO" SaaS France'],
                },
                campaign={"daily_connection_limit": 20},
            )

            result = ControlPlaneService(registry).run_dry_run(profile_id, profile_path, limit=3)

            self.assertTrue(result["dry_run"])
            self.assertIsNotNone(registry.latest_successful_dry_run(profile_id))
            self.assertGreaterEqual(len(registry.list_leads(profile_id)), 1)


if __name__ == "__main__":
    unittest.main()
