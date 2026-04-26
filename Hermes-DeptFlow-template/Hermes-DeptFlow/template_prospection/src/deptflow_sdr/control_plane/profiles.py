from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


TEMPLATE_VERSION = "0.2.0"


class ProfileFactory:
    """Create client-specific Hermes profile folders from the template."""

    def __init__(self, template_root: Path):
        self.template_root = template_root

    def create_profile(
        self,
        target_dir: Path,
        profile_slug: str,
        client: dict[str, Any],
        icp: dict[str, Any],
        campaign: dict[str, Any],
    ) -> Path:
        profile_path = target_dir / profile_slug
        if profile_path.exists():
            shutil.rmtree(profile_path)
        shutil.copytree(self.template_root, profile_path, ignore=self._ignore_generated)

        profile_path.joinpath("profile.manifest.json").write_text(
            json.dumps(self._manifest(profile_slug), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        profile_path.joinpath(".env.template").write_text(self._env_template(), encoding="utf-8")
        profile_path.joinpath("icp_config.yaml").write_text(
            json.dumps(self._icp_config(client, icp), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        profile_path.joinpath("campaign_config.yaml").write_text(
            json.dumps(self._campaign_config(campaign), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return profile_path

    def _ignore_generated(self, _path: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in {"data", "reports", "logs", "control_plane", ".deptflow-control-plane", "__pycache__"}
            or name.endswith(".pyc")
            or name == ".env"
        }

    def _manifest(self, profile_slug: str) -> dict[str, Any]:
        return {
            "name": "Hermes DeptFlow SDR",
            "template_version": TEMPLATE_VERSION,
            "profile_slug": profile_slug,
            "hermes": {
                "entrypoint": "scripts/start_dashboard.py",
                "runtime_script": "scripts/daily_prospecting.py",
                "required_files": ["config.yaml", "SOUL.md", "icp_config.yaml", "campaign_config.yaml"],
            },
            "safety": {
                "dry_run_default": True,
                "requires_go_live_gate": True,
                "connection_request_note": False,
            },
        }

    def _env_template(self) -> str:
        return "\n".join(
            [
                "# DeptFlow Hermes local profile secrets.",
                "# Real secrets are stored by the dashboard vault and injected at run time.",
                "BEREACH_API_KEY=",
                "OPENAI_API_KEY=",
                "GOOGLE_SERVICE_ACCOUNT_JSON=",
                "GOOGLE_SHEET_ID=",
                "DRY_RUN=true",
                "USE_BEREACH_IN_DRY_RUN=false",
                "DATA_DIR=data",
                "REPORTS_DIR=reports",
                "LOGS_DIR=logs",
                "",
            ]
        )

    def _icp_config(self, client: dict[str, Any], icp: dict[str, Any]) -> dict[str, Any]:
        return {
            "client": {
                "name": client.get("name", ""),
                "offer_name": client.get("offer_name", ""),
                "offer_description": client.get("offer_description", ""),
                "value_proposition": client.get("value_proposition", ""),
                "proof_points": client.get("proof_points", []),
            },
            "icp": {
                "target_roles": icp.get("target_roles", []),
                "target_seniority": icp.get("target_seniority", ["founder", "c-level", "director", "head"]),
                "target_industries": icp.get("target_industries", []),
                "target_locations": icp.get("target_locations", ["France"]),
                "excluded_roles": icp.get("excluded_roles", ["student", "intern", "recruiter", "job seeker"]),
                "excluded_industries": icp.get("excluded_industries", []),
                "excluded_keywords": icp.get("excluded_keywords", []),
                "competitors": icp.get("competitors", []),
            },
            "search": {
                "queries": icp.get("queries", []),
                "max_queries_per_run": int(icp.get("max_queries_per_run", 3)),
            },
            "buying_signals": {
                "strong": icp.get("strong_signals", ["hiring", "growth", "outbound", "pipeline"]),
                "medium": icp.get("medium_signals", ["launch", "expansion", "fundraising"]),
                "weak": icp.get("weak_signals", ["sales", "growth", "prospection"]),
            },
            "messaging": {
                "tone": "professionnel, concis, utile",
                "forbidden_claims": ["ROI garanti", "résultat garanti", "nous avons vu vos données internes"],
                "call_to_action": icp.get("call_to_action", "Est-ce un sujet que vous regardez en ce moment ?"),
            },
        }

    def _campaign_config(self, campaign: dict[str, Any]) -> dict[str, Any]:
        daily_connection_limit = int(campaign.get("daily_connection_limit", 20))
        return {
            "campaign": {
                "name": campaign.get("name", "default-linkedin-france"),
                "timezone": campaign.get("timezone", "Europe/Paris"),
                "run_days": campaign.get("run_days", ["monday", "tuesday", "wednesday", "thursday", "friday"]),
            },
            "qualification": {"threshold": int(campaign.get("threshold", 75)), "very_hot_threshold": 88},
            "limits": {
                "daily_searches": int(campaign.get("daily_searches", 100)),
                "daily_profile_enrichments": int(campaign.get("daily_profile_enrichments", 50)),
                "daily_follow_profiles": 0,
                "daily_connection_requests": daily_connection_limit,
                "daily_messages": 0,
            },
            "outreach": {
                "prepare_messages": True,
                "send_messages_automatically": False,
                "allow_follow_profiles": False,
                "allow_connection_requests": daily_connection_limit > 0,
                "connection_request_note": False,
                "allow_comments_or_likes": False,
            },
            "enrichment": {"collect_posts": True, "posts_per_profile": 5, "recent_activity_days": 45},
            "storage": {"save_rejected_leads": False},
            "qa": {"enabled": True, "block_on_qa_failure": True},
        }
