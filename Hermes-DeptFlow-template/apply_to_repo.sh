#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./apply_to_repo.sh /path/to/deptflowhermes
#
# This copies the prepared Hermes-DeptFlow folder into the target repo.
# Then review, test, commit and push.

TARGET_REPO="${1:-}"
if [ -z "$TARGET_REPO" ]; then
  echo "Usage: ./apply_to_repo.sh /path/to/deptflowhermes"
  exit 1
fi

if [ ! -d "$TARGET_REPO/.git" ]; then
  echo "Target is not a git repository: $TARGET_REPO"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/Hermes-DeptFlow"

if [ ! -d "$SRC" ]; then
  echo "Missing source folder: $SRC"
  exit 1
fi

rm -rf "$TARGET_REPO/Hermes-DeptFlow"
cp -R "$SRC" "$TARGET_REPO/Hermes-DeptFlow"

cd "$TARGET_REPO"
git status --short

echo
echo "Next:"
echo "  cd $TARGET_REPO/Hermes-DeptFlow/template_prospection"
echo "  cp .env.template .env"
echo "  python3 scripts/validate_config.py"
echo "  python3 scripts/dry_run.py --limit 5"
echo
echo "Then commit:"
echo "  git add Hermes-DeptFlow"
echo "  git commit -m 'Build functional DeptFlow Hermes SDR profile template'"
echo "  git push origin main"
