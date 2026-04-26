from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.control_plane.web import DashboardApp


class DashboardTest(unittest.TestCase):
    def test_home_page_exposes_onboarding_and_safety_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = DashboardApp(ROOT, state_dir=Path(tmp))
            html = app.render_home()

            self.assertIn("Hermes DeptFlow", html)
            self.assertIn("Créer un client", html)
            self.assertIn("Dry-run obligatoire", html)

    def test_onboarding_creates_registry_profile_and_hermes_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = DashboardApp(ROOT, state_dir=Path(tmp))
            result = app.create_client_from_form(
                {
                    "client_name": "Acme France",
                    "offer_name": "Audit Pipeline",
                    "offer_description": "Aide les dirigeants B2B à trouver les comptes chauds.",
                    "target_roles": "CEO, Founder",
                    "target_industries": "SaaS, Software",
                    "target_locations": "France",
                    "excluded_keywords": "student, recruiter",
                    "daily_connection_limit": "20",
                }
            )

            profile_path = Path(result["profile_path"])
            self.assertTrue((profile_path / "SOUL.md").exists())
            self.assertTrue((profile_path / "profile.manifest.json").exists())
            self.assertEqual(app.registry.get_client(result["client_id"])["name"], "Acme France")
            self.assertEqual(app.registry.get_profile(result["profile_id"])["daily_connection_limit"], 20)
            self.assertIn("Acme France", app.render_home())
            self.assertIn("Lancer dry-run", app.render_home())


if __name__ == "__main__":
    unittest.main()
