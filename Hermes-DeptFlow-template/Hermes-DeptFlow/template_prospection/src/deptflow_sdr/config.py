from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


TRUE_VALUES = {"1", "true", "yes", "y", "on"}


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in TRUE_VALUES


def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
        os.environ.setdefault(key, value)
    return values


def load_structured_file(path: Path) -> Dict[str, Any]:
    """Load JSON-compatible YAML with stdlib, or full YAML when PyYAML exists."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            f"{path} is not JSON-compatible YAML and PyYAML is not installed. "
            "Either install pyyaml or keep the file JSON-compatible."
        ) from exc

    data = yaml.safe_load(text)
    return data or {}


@dataclass
class Settings:
    root_dir: Path
    environment: str
    dry_run: bool
    use_bereach_in_dry_run: bool
    bereach_base_url: str
    bereach_api_key: str
    bereach_auth_header: str
    bereach_auth_scheme: str
    bereach_timeout_seconds: int
    bereach_max_retries: int
    supabase_url: str
    supabase_service_key: str
    data_dir: Path
    reports_dir: Path
    logs_dir: Path

    @property
    def has_bereach(self) -> bool:
        return bool(self.bereach_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)


def load_settings(root_dir: Optional[Path] = None) -> Settings:
    root = root_dir or Path.cwd()
    load_env_file(root / ".env")
    load_env_file(root / ".env.template")

    def getenv(name: str, default: str = "") -> str:
        return os.environ.get(name, default)

    data_dir = root / getenv("DATA_DIR", "data")
    reports_dir = root / getenv("REPORTS_DIR", "reports")
    logs_dir = root / getenv("LOGS_DIR", "logs")

    return Settings(
        root_dir=root,
        environment=getenv("ENVIRONMENT", "production"),
        dry_run=as_bool(getenv("DRY_RUN", "true"), True),
        use_bereach_in_dry_run=as_bool(getenv("USE_BEREACH_IN_DRY_RUN", "false"), False),
        bereach_base_url=getenv("BEREACH_BASE_URL", "https://api.bereach.ai").rstrip("/"),
        bereach_api_key=getenv("BEREACH_API_KEY", ""),
        bereach_auth_header=getenv("BEREACH_AUTH_HEADER", "Authorization"),
        bereach_auth_scheme=getenv("BEREACH_AUTH_SCHEME", "Bearer"),
        bereach_timeout_seconds=int(getenv("BEREACH_TIMEOUT_SECONDS", "30")),
        bereach_max_retries=int(getenv("BEREACH_MAX_RETRIES", "2")),
        supabase_url=getenv("SUPABASE_URL", "").rstrip("/"),
        supabase_service_key=getenv("SUPABASE_SERVICE_KEY", ""),
        data_dir=data_dir,
        reports_dir=reports_dir,
        logs_dir=logs_dir,
    )


@dataclass
class RuntimeConfig:
    icp: Dict[str, Any]
    campaign: Dict[str, Any]


def load_runtime_config(root_dir: Optional[Path] = None) -> RuntimeConfig:
    root = root_dir or Path.cwd()
    return RuntimeConfig(
        icp=load_structured_file(root / "icp_config.yaml"),
        campaign=load_structured_file(root / "campaign_config.yaml"),
    )


def validate_runtime(settings: Settings, runtime: RuntimeConfig, real_run: bool = False) -> list[str]:
    issues: list[str] = []

    icp = runtime.icp.get("icp", {})
    if not icp.get("target_roles"):
        issues.append("icp.target_roles is empty")
    if not runtime.icp.get("search", {}).get("queries"):
        issues.append("search.queries is empty")
    if real_run and not settings.has_bereach:
        issues.append("BEREACH_API_KEY is required for a real BeReach run")

    threshold = runtime.campaign.get("qualification", {}).get("threshold", 75)
    if not isinstance(threshold, int) or threshold < 0 or threshold > 100:
        issues.append("qualification.threshold must be an integer between 0 and 100")

    return issues
