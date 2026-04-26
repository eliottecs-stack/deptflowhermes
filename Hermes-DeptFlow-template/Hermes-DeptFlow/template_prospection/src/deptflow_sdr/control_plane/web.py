from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from deptflow_sdr.control_plane.profiles import ProfileFactory, TEMPLATE_VERSION
from deptflow_sdr.control_plane.registry import Registry


class DashboardApp:
    """Small local dashboard used by Hermes creators."""

    def __init__(self, template_root: Path, state_dir: Path | None = None):
        self.template_root = template_root
        self.state_dir = state_dir or (template_root / "control_plane")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.registry = Registry(self.state_dir / "deptflow.db")
        self.profiles_dir = self.state_dir / "profiles"

    def render_home(self) -> str:
        profiles_html = self._profiles_html()
        return self._page(
            "Hermes DeptFlow",
            f"""
            <section class="hero">
              <div>
                <p class="eyebrow">Control plane local</p>
                <h1>Hermes DeptFlow</h1>
                <p>Créez et pilotez des SDR IA LinkedIn par client, sans terminal.</p>
              </div>
              <a class="button" href="/onboarding">Créer un client</a>
            </section>
            <section class="grid">
              <article><strong>Dry-run obligatoire</strong><span>Le mode réel reste bloqué tant qu'un échantillon n'est pas validé.</span></article>
              <article><strong>Quotas modérés</strong><span>Les connexions utilisent les limites BeReach et un budget local persistant.</span></article>
              <article><strong>CRM Google Sheets</strong><span>Les leads, messages et statuts sont prêts pour synchronisation.</span></article>
            </section>
            <section>
              <h2>Profils clients</h2>
              {profiles_html}
            </section>
            """,
        )

    def render_onboarding(self) -> str:
        return self._page(
            "Créer un client",
            """
            <h1>Créer un client</h1>
            <form method="post" action="/onboarding" class="form">
              <label>Nom client <input name="client_name" required></label>
              <label>Nom de l'offre <input name="offer_name" required></label>
              <label>Description de l'offre <textarea name="offer_description" required></textarea></label>
              <label>Rôles ciblés <input name="target_roles" placeholder="CEO, Founder, Head of Sales"></label>
              <label>Industries <input name="target_industries" placeholder="SaaS, B2B, Software"></label>
              <label>Zones <input name="target_locations" value="France"></label>
              <label>Exclusions <input name="excluded_keywords" placeholder="student, recruiter"></label>
              <label>Quota connexions / jour <input name="daily_connection_limit" type="number" value="20" min="1" max="25"></label>
              <button class="button" type="submit">Générer le profil Hermes</button>
            </form>
            """,
        )

    def render_created(self, result: dict[str, str]) -> str:
        profile_path = html.escape(result["profile_path"])
        return self._page(
            "Profil créé",
            f"""
            <h1>Profil créé</h1>
            <p>Le profil Hermes client est prêt.</p>
            <dl>
              <dt>Client</dt><dd>{html.escape(result['client_id'])}</dd>
              <dt>Profil</dt><dd>{html.escape(result['profile_id'])}</dd>
              <dt>Dossier</dt><dd><code>{profile_path}</code></dd>
            </dl>
            <a class="button" href="/">Retour dashboard</a>
            """,
        )

    def create_client_from_form(self, fields: dict[str, str]) -> dict[str, str]:
        client_name = fields.get("client_name", "").strip()
        if not client_name:
            raise ValueError("Le nom client est requis")

        slug = self._slug(client_name)
        client_id = self.registry.create_client(client_name, market="France B2B")
        profile_id = self.registry.create_profile(client_id, slug)
        daily_connection_limit = int(fields.get("daily_connection_limit") or 20)
        self.registry.set_profile_limits(profile_id, daily_connection_limit=daily_connection_limit)

        client = {
            "name": client_name,
            "offer_name": fields.get("offer_name", "").strip(),
            "offer_description": fields.get("offer_description", "").strip(),
            "value_proposition": fields.get("offer_description", "").strip(),
        }
        icp = {
            "target_roles": self._split_list(fields.get("target_roles", "")),
            "target_industries": self._split_list(fields.get("target_industries", "")),
            "target_locations": self._split_list(fields.get("target_locations", "France")) or ["France"],
            "excluded_keywords": self._split_list(fields.get("excluded_keywords", "")),
            "queries": self._default_queries(fields),
        }
        campaign = {"daily_connection_limit": daily_connection_limit, "timezone": "Europe/Paris"}

        profile_path = ProfileFactory(self.template_root).create_profile(
            target_dir=self.profiles_dir,
            profile_slug=slug,
            client=client,
            icp=icp,
            campaign=campaign,
        )
        self.registry.create_release(
            profile_id,
            template_version=TEMPLATE_VERSION,
            config_snapshot={"client": client, "icp": icp, "campaign": campaign},
            prompt_snapshot={"SOUL.md": (profile_path / "SOUL.md").read_text(encoding="utf-8")},
        )
        return {"client_id": client_id, "profile_id": profile_id, "profile_path": str(profile_path)}

    def run_dry_run(self, profile_id: str, limit: int = 5) -> dict:
        from deptflow_sdr.control_plane.service import ControlPlaneService

        profile = self.registry.get_profile(profile_id)
        profile_path = self.profiles_dir / profile["slug"]
        return ControlPlaneService(self.registry).run_dry_run(profile_id, profile_path, limit=limit)

    def _page(self, title: str, body: str) -> str:
        return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink:#172026; --muted:#5d6972; --line:#d8dee4; --accent:#0f766e; --bg:#f7f8f8; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Arial, sans-serif; color:var(--ink); background:var(--bg); }}
    header {{ height:56px; display:flex; align-items:center; padding:0 28px; border-bottom:1px solid var(--line); background:white; }}
    header a {{ color:var(--ink); text-decoration:none; font-weight:700; }}
    main {{ max-width:1080px; margin:0 auto; padding:32px 24px; }}
    .hero {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; padding:28px 0; }}
    .hero h1, h1 {{ font-size:34px; margin:0 0 10px; letter-spacing:0; }}
    .hero p {{ margin:0; color:var(--muted); }}
    .eyebrow {{ color:var(--accent)!important; text-transform:uppercase; font-size:12px; font-weight:700; letter-spacing:0; }}
    .grid {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:14px; }}
    article {{ background:white; border:1px solid var(--line); border-radius:8px; padding:16px; min-height:116px; }}
    article strong {{ display:block; margin-bottom:8px; }}
    article span, p, dd {{ color:var(--muted); line-height:1.45; }}
    .button {{ display:inline-flex; align-items:center; justify-content:center; min-height:40px; padding:0 14px; border-radius:6px; background:var(--accent); color:white; text-decoration:none; border:0; cursor:pointer; font-weight:700; }}
    .form {{ display:grid; gap:14px; max-width:680px; }}
    label {{ display:grid; gap:6px; font-weight:700; }}
    input, textarea {{ width:100%; border:1px solid var(--line); border-radius:6px; padding:10px; font:inherit; background:white; }}
    table {{ width:100%; border-collapse:collapse; background:white; border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
    th, td {{ padding:12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
    th {{ color:var(--muted); font-size:13px; }}
    textarea {{ min-height:88px; }}
    code {{ white-space:normal; overflow-wrap:anywhere; }}
    @media (max-width: 760px) {{ .hero, .grid {{ display:block; }} article {{ margin:12px 0; }} }}
  </style>
</head>
<body>
  <header><a href="/">DeptFlow Hermes</a></header>
  <main>{body}</main>
</body>
</html>"""

    def _split_list(self, value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    def _slug(self, value: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
        return "-".join(part for part in slug.split("-") if part)[:48] or "client"

    def _default_queries(self, fields: dict[str, str]) -> list[str]:
        roles = self._split_list(fields.get("target_roles", "")) or ["CEO"]
        industries = self._split_list(fields.get("target_industries", "")) or ["B2B"]
        locations = self._split_list(fields.get("target_locations", "")) or ["France"]
        return [f'"{roles[0]}" {industries[0]} {locations[0]}']

    def _profiles_html(self) -> str:
        profiles = self.registry.list_profiles()
        if not profiles:
            return "<p>Aucun profil client pour le moment.</p>"
        rows = []
        for profile in profiles:
            rows.append(
                "<tr>"
                f"<td>{html.escape(profile['client_name'])}</td>"
                f"<td>{html.escape(profile['slug'])}</td>"
                f"<td>{html.escape(profile['status'])}</td>"
                f"<td>{int(profile['daily_connection_limit'])}/jour</td>"
                f"<td><form method='post' action='/profiles/{html.escape(profile['id'])}/dry-run'>"
                "<button class='button' type='submit'>Lancer dry-run</button></form></td>"
                "</tr>"
            )
        return (
            "<table><thead><tr><th>Client</th><th>Profil</th><th>Statut</th><th>Quota</th><th>Action</th></tr></thead>"
            "<tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )


def make_handler(app: DashboardApp):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/onboarding":
                self._send_html(app.render_onboarding())
                return
            self._send_html(app.render_home())

        def do_POST(self) -> None:
            if self.path.startswith("/profiles/") and self.path.endswith("/dry-run"):
                profile_id = self.path.split("/")[2]
                try:
                    result = app.run_dry_run(profile_id, limit=5)
                    self._send_html(app._page("Dry-run terminé", f"<h1>Dry-run terminé</h1><pre>{html.escape(json.dumps(result, ensure_ascii=False, indent=2))}</pre><a class='button' href='/'>Retour</a>"))
                except Exception as exc:
                    self.send_error(400, str(exc))
                return
            if self.path != "/onboarding":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            parsed = {key: values[0] for key, values in parse_qs(raw).items()}
            try:
                result = app.create_client_from_form(parsed)
                self._send_html(app.render_created(result))
            except Exception as exc:
                self.send_error(400, str(exc))

        def log_message(self, _format: str, *args) -> None:
            return

        def _send_html(self, text: str) -> None:
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def run_dashboard(template_root: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    app = DashboardApp(template_root)
    server = ThreadingHTTPServer((host, port), make_handler(app))
    print(f"DeptFlow dashboard: http://{host}:{port}")
    server.serve_forever()
