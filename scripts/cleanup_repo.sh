#!/bin/bash
# Repository cleanup script
# - Prunes stale remote tracking branches
# - Deletes local branches already merged into main
# - Removes ignored files like caches
set -e

git fetch --all --prune

for branch in $(git branch --merged | grep -v "^*" | grep -v main); do
  git branch -d "$branch"
done

git clean -fdX

echo "Cleanup complete."
