# GitHub Cleanup Recommendations

This project still contains some leftover files and outdated branches that can be cleaned up to reduce clutter. Below are recommended tasks.

## 1. Branch Maintenance
- Run `git fetch --all --prune` to remove stale remote-tracking branches.
- Review `git branch -r` for remote branches that have been merged or are no longer active.
- Delete obsolete local branches with `git branch -D <branch>` once they are safely merged.
- Consider enabling branch protection rules on your main branch to avoid direct pushes.

## 2. Remove Tracked Build Artifacts
- Several `__pycache__` directories and `.pyc` files are committed (see `git ls-files | grep __pycache__`). These should be removed and kept out of Git history.
- Delete existing tracked compiled files and commit the removal.
- Ensure `.gitignore` covers these patterns (it already includes `__pycache__/` and `*.py[cod]`).

## 3. Delete Log Files
- Files such as `test_startup.log` and `streamlit.log` are checked in. Remove them and rely on the existing `*.log` rule in `.gitignore` to avoid future commits.

## 4. Review Archived Directories
- The `archived_docs/` and `archived_old_version/` folders contain historical documents and code. If these are no longer needed in the repo, consider deleting or moving them to a separate archive branch to reduce repository size.

## 5. Check Large Files
- Run `git lfs track` or `git ls-files -s | sort -n -k1` to detect unusually large files. Migrate binaries to Git LFS or remove them if not essential.

## 6. Automated Cleanup Script
- Create a simple script to prune old branches and remove untracked caches. Example commands:
  ```bash
  git fetch --all --prune
  for branch in $(git branch --merged | grep -v '\*' | grep -v main); do
      git branch -d "$branch"
  done
  git clean -fdX
  ```

Cleaning up these items will keep the repository lean and make future development smoother.
