#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-/home/alex/repos/erzieherausbildung}"
BRANCH="${BRANCH:-feat/homepage-canvas-detail-links-v1}"
BASE="${BASE:-main}"
REMOTE="${REMOTE:-origin}"
EXPECTED_HEAD="${EXPECTED_HEAD:-}"
DRY_RUN="${DRY_RUN:-0}"

cd "$REPO"

echo "==> Fetch $REMOTE/$BASE"
git fetch "$REMOTE" "$BASE" --prune

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: worktree or index is dirty" >&2
  git status --short
  exit 1
fi

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "$BRANCH" ]]; then
  echo "==> Switch $current_branch -> $BRANCH"
  git switch "$BRANCH"
fi

head="$(git rev-parse HEAD)"
echo "==> HEAD $head"
if [[ -n "$EXPECTED_HEAD" && "$head" != "$EXPECTED_HEAD" ]]; then
  echo "ERROR: expected HEAD $EXPECTED_HEAD, got $head" >&2
  echo "Set EXPECTED_HEAD= to intentionally accept this branch head." >&2
  exit 1
fi

if ! git merge-base --is-ancestor "$REMOTE/$BASE" HEAD; then
  echo "ERROR: branch is not based on current $REMOTE/$BASE" >&2
  exit 1
fi

echo "==> Validate"
node --jitless --check assets/app.js
python3 scripts/validate_repository.py
python3 scripts/validate_excerpts.py
python3 scripts/validate_view_export.py

echo "==> Static surface smoke"
grep -q 'canvas-viewer' index.html
grep -q 'learning-map-v1.canvas' assets/app.js
grep -q 'excerptConcepts' assets/app.js
grep -q 'canvas-homepage-detail-plan' README.md

echo "==> Diff summary"
git diff --stat "$REMOTE/$BASE"...HEAD

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN=1: stopping before publish"
  exit 0
fi

echo "==> Push branch"
git push -u "$REMOTE" "$BRANCH"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh not found; branch pushed but PR not created" >&2
  exit 0
fi

if gh pr view "$BRANCH" --repo alexdermohr/erzieherausbildung >/dev/null 2>&1; then
  gh pr view "$BRANCH" --repo alexdermohr/erzieherausbildung --web
  exit 0
fi

echo "==> Create PR"
gh pr create \
  --repo alexdermohr/erzieherausbildung \
  --base "$BASE" \
  --head "$BRANCH" \
  --title "feat: render canvas views in homepage" \
  --body "Canvas views are rendered in the homepage. The detail panel links nodes to source anchors and pilot excerpts. Validation: node --jitless --check assets/app.js; python3 scripts/validate_repository.py; python3 scripts/validate_excerpts.py; python3 scripts/validate_view_export.py."
