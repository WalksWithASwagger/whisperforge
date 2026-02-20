#!/bin/bash
# Repository cleanup script
# - Prunes stale remote tracking branches
# - Deletes local branches already merged into main
# - Removes ignored files like caches
set -euo pipefail

git fetch --all --prune

for branch in $(git branch --merged | grep -v "^*" | grep -v main); do
  git branch -d "$branch"
done

echo "The following ignored files will be removed:"
git clean -ndX
read -rp "Proceed with cleanup? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Cleanup cancelled."
  exit 0
fi

git clean -fdX

echo "Cleanup complete."
