from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from deptflow_sdr.agents.messaging import MessageWriter
from deptflow_sdr.agents.qa import QAAgent
from deptflow_sdr.agents.scoring import LeadScorer
from deptflow_sdr.config import Settings, load_runtime_config, load_settings, validate_runtime
from deptflow_sdr.domain.models import Lead, LeadScore, PreparedMessage, utc_now_iso
from deptflow_sdr.domain.normalizers import normalize_lead, normalize_posts
from deptflow_sdr.integrations.bereach_client import BeReachClient, BeReachError, extract_people
from deptflow_sdr.integrations.storage import make_store
from deptflow_sdr.observability.reporting import ReportWriter
from deptflow_sdr.safety.dedupe import DedupeIndex


def load_fixture_people(root_dir: Path) -> list[dict[str, Any]]:
    path = root_dir / "tests" / "fixtures" / "bereach_search_people.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return extract_people(data)


def load_fixture_posts(root_dir: Path, lead: Lead) -> list[dict[str, Any]]:
    path = root_dir / "tests" / "fixtures" / "bereach_posts_by_profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    key = lead.public_identifier or lead.linkedin_url.rstrip("/").split("/")[-1]
    return data.get(key, {}).get("posts", [])


def should_use_bereach(settings: Settings, dry_run: bool) -> bool:
    if not settings.has_bereach:
        return False
    if dry_run and not settings.use_bereach_in_dry_run:
        return False
    return True


class DailyProspectingWorkflow:
    def __init__(self, root_dir: Path, dry_run: bool | None = None):
        self.root_dir = root_dir
        self.settings = load_settings(root_dir)
        if dry_run is not None:
            self.settings.dry_run = dry_run
        self.runtime = load_runtime_config(root_dir)
        self.client = BeReachClient(self.settings)
        self.store = make_store(self.settings)
        self.qa = QAAgent()
        self.scorer = LeadScorer(self.runtime.icp, self.runtime.campaign)
        client = self.runtime.icp.get("client", {})
        messaging = self.runtime.icp.get("messaging", {})
        self.writer = MessageWriter(
            offer_description=client.get("offer_description", ""),
            call_to_action=messaging.get("call_to_action", ""),
        )

    def discover(self, limit: int) -> tuple[list[Lead], list[str]]:
        errors: list[str] = []
        use_api = should_use_bereach(self.settings, self.settings.dry_run)
        raw_people: list[dict[str, Any]] = []

        if not use_api:
            raw_people = load_fixture_people(self.root_dir)
        else:
            queries = self.runtime.icp.get("search", {}).get("queries", [])
            max_queries = int(self.runtime.icp.get("search", {}).get("max_queries_per_run", 3))
            per_query = max(1, min(25, limit))
            for query in queries[:max_queries]:
                try:
                    response = self.client.search_people(query, count=per_query)
                    raw_people.extend(extract_people(response))
                except BeReachError as exc:
                    errors.append(str(exc))
                    if exc.status_code == 429:
                        break

        leads = [normalize_lead(item) for item in raw_people]
        # Preserve order, enforce limit after normalization.
        return leads[:limit], errors

    def enrich_posts(self, lead: Lead) -> tuple[list[Any], list[str]]:
        errors: list[str] = []
        collect_posts = bool(self.runtime.campaign.get("enrichment", {}).get("collect_posts", True))
        if not collect_posts:
            return [], errors

        count = int(self.runtime.campaign.get("enrichment", {}).get("posts_per_profile", 5))
        use_api = should_use_bereach(self.settings, self.settings.dry_run)

        if not use_api:
            raw = {"posts": load_fixture_posts(self.root_dir, lead)}
            return normalize_posts(raw), errors

        if not lead.linkedin_url:
            return [], ["Cannot collect posts without linkedin_url"]

        try:
            response = self.client.collect_posts(lead.linkedin_url, count=count)
            return normalize_posts(response), errors
        except BeReachError as exc:
            errors.append(str(exc))
            return [], errors

    def run(self, limit: int = 25) -> dict[str, Any]:
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.reports_dir.mkdir(parents=True, exist_ok=True)
        self.settings.logs_dir.mkdir(parents=True, exist_ok=True)

        started_at = utc_now_iso()
        issues = validate_runtime(self.settings, self.runtime, real_run=not self.settings.dry_run)
        if issues:
            raise RuntimeError("Invalid configuration: " + "; ".join(issues))

        leads, errors = self.discover(limit=limit)
        dedupe = DedupeIndex(self.store.existing_lead_keys())
        accepted: list[tuple[Lead, LeadScore, PreparedMessage | None]] = []
        rejected: list[tuple[Lead, LeadScore]] = []
        saved = 0

        save_rejected = bool(self.runtime.campaign.get("storage", {}).get("save_rejected_leads", False))
        prepare_messages = bool(self.runtime.campaign.get("outreach", {}).get("prepare_messages", True))

        for lead in leads:
            if dedupe.seen(lead):
                continue

            posts, post_errors = self.enrich_posts(lead)
            errors.extend(post_errors)

            score = self.scorer.score(lead, posts)
            qa_ok, qa_issues = self.qa.review_lead(lead, score)
            if not qa_ok:
                for issue in qa_issues:
                    if issue not in score.rejection_reasons:
                        score.rejection_reasons.append(issue)
                score.qualified = False
                score.tier = "REJECTED"

            message = None
            if score.qualified and prepare_messages:
                message = self.writer.first_message(lead, score)

            if score.qualified:
                accepted.append((lead, score, message))
                self.store.save_lead(lead, score, message)
                saved += 1
            else:
                rejected.append((lead, score))
                if save_rejected:
                    self.store.save_lead(lead, score, None)
                    saved += 1

        report_path = ReportWriter(self.settings).write(
            discovered=len(leads),
            accepted=accepted,
            rejected=rejected,
            errors=errors,
            dry_run=self.settings.dry_run,
        )

        result = {
            "started_at": started_at,
            "finished_at": utc_now_iso(),
            "dry_run": self.settings.dry_run,
            "discovered": len(leads),
            "qualified": len(accepted),
            "rejected": len(rejected),
            "saved": saved,
            "messages_prepared": sum(1 for _, _, message in accepted if message),
            "report_path": str(report_path),
            "errors": errors,
        }
        self.store.save_run(result)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DeptFlow SDR daily prospecting.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--dry-run", action="store_true", default=None, help="Force dry-run mode.")
    parser.add_argument("--real", action="store_true", help="Force real mode. Requires BEREACH_API_KEY.")
    args = parser.parse_args(argv)

    root = Path.cwd()
    if args.real:
        dry_run = False
    elif args.dry_run:
        dry_run = True
    else:
        dry_run = None

    workflow = DailyProspectingWorkflow(root_dir=root, dry_run=dry_run)
    result = workflow.run(limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
