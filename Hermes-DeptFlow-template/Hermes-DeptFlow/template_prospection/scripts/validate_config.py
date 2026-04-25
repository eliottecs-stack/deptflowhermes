#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deptflow_sdr.config import load_runtime_config, load_settings, validate_runtime

settings = load_settings(ROOT)
runtime = load_runtime_config(ROOT)
issues = validate_runtime(settings, runtime, real_run=not settings.dry_run)

if issues:
    print("Configuration invalid:")
    for issue in issues:
        print(f"- {issue}")
    raise SystemExit(1)

print(json.dumps({
    "ok": True,
    "dry_run": settings.dry_run,
    "has_bereach_api_key": settings.has_bereach,
    "has_supabase": settings.has_supabase,
    "data_dir": str(settings.data_dir),
    "reports_dir": str(settings.reports_dir)
}, indent=2))
