#!/usr/bin/env bash
# Regenerate the units, rebuild every game, and play-test each one. Run before pushing.
# Needs: python3 with playwright and sympy, and a Chromium that Playwright can launch.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== secrets"
if git ls-files -z | xargs -0 grep -l -E 'github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}' 2>/dev/null; then
  echo "a tracked file contains a GitHub token" >&2; exit 1
fi
git check-ignore -q .github-token || { echo ".github-token is not git-ignored" >&2; exit 1; }

echo "== units (answers and figure labels are checked as they are generated)"
python3 units/src/exponent_laws.py | tail -1
python3 units/src/area_of_polygons.py | tail -1

echo "== build"
python3 tools/build.py

for g in games/*.html; do
  echo "== play-test $g"
  log=$(python3 tools/playtest.py "$g") || { echo "$log"; exit 1; }
  echo "$log" | grep -E "unit check|board:|resume|final scores|console errors" || true
  log=$(python3 tools/playtest_sizes.py "$g") || { echo "$log"; exit 1; }
  echo "$log" | grep -E "stale|estimate|errors:" || true
  python3 tools/printtest.py "$g"
done

echo "== tracked files changed by this run (none expected unless you edited sources)"
git status --short -- units games || true
echo "all checks passed; screenshots and PDFs are in out/"
