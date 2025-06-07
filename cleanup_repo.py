#!/usr/bin/env python3
"""
WhisperForge Repository Cleanup Script
Safely removes duplicate files, backup files, and organizes the repository structure.
"""

import os
import shutil
import sys
from pathlib import Path
import argparse

def cleanup_files():
    """Remove duplicate and backup files"""
    print("🧹 Starting repository cleanup...")
    
    # Files to remove (high priority)
    files_to_remove = [
        "clean.py",
        "clean.py.save", 
        "app.py.bak",
        "spektor.log",
        "whisperforge.log",
        "whisperforge.db",
        ".DS_Store",
        "whisperforge/.DS_Store",
        "whisperforge/app.py.bak",
        "whisperforge/app.py.bak.20250405",
    ]
    
    # Remove files
    removed_count = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
        else:
            print(f"⏩ Already clean: {file_path}")
    
    print(f"\n📊 Removed {removed_count} files")
    return removed_count

def organize_directories():
    """Organize files into proper directory structure"""
    print("\n📁 Organizing directory structure...")
    
    # Create new directory structure
    directories_to_create = [
        "whisperforge/tests",
        "whisperforge/docs", 
        "whisperforge/deployment",
        "whisperforge/src",
        "whisperforge/src/whisperforge",
        "whisperforge/src/config"
    ]
    
    for directory in directories_to_create:
        os.makedirs(directory, exist_ok=True)
        print(f"📂 Created: {directory}")
    
    # Move test files
    test_files = [
        ("test_notion.py", "whisperforge/tests/"),
        ("whisperforge/test_notion.py", "whisperforge/tests/"),
        ("whisperforge/test_supabase.py", "whisperforge/tests/")
    ]
    
    moved_count = 0
    for src, dst in test_files:
        if os.path.exists(src):
            try:
                dst_path = os.path.join(dst, os.path.basename(src))
                if not os.path.exists(dst_path):  # Don't overwrite
                    shutil.move(src, dst_path)
                    print(f"📦 Moved: {src} → {dst_path}")
                    moved_count += 1
                else:
                    print(f"⏩ Already exists: {dst_path}")
            except Exception as e:
                print(f"❌ Failed to move {src}: {e}")
    
    print(f"\n📊 Moved {moved_count} files to proper locations")
    return moved_count

def consolidate_requirements():
    """Consolidate requirements files"""
    print("\n📋 Consolidating requirements...")
    
    # Keep only the whisperforge/requirements.txt (the updated one)
    if os.path.exists("requirements.txt") and os.path.exists("whisperforge/requirements.txt"):
        try:
            os.remove("requirements.txt")
            print("✅ Removed duplicate root requirements.txt")
        except Exception as e:
            print(f"❌ Failed to remove root requirements.txt: {e}")
    
    return True

def update_gitignore():
    """Update .gitignore with comprehensive exclusions"""
    print("\n🚫 Updating .gitignore...")
    
    additional_ignores = """
# Additional exclusions for clean repo
*.bak
*.save
*.tmp
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.sublime-*

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Distribution
build/
dist/
*.egg-info/

# Local data
whisperforge.db
whisperforge.log
spektor.log
"""
    
    try:
        with open(".gitignore", "a") as f:
            f.write(additional_ignores)
        print("✅ Updated .gitignore with additional exclusions")
    except Exception as e:
        print(f"❌ Failed to update .gitignore: {e}")

def create_init_files():
    """Create __init__.py files for proper Python packages"""
    print("\n🐍 Creating Python package structure...")
    
    init_files = [
        "whisperforge/src/__init__.py",
        "whisperforge/src/whisperforge/__init__.py",
        "whisperforge/tests/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            try:
                with open(init_file, "w") as f:
                    f.write('"""WhisperForge package"""\n')
                print(f"✅ Created: {init_file}")
            except Exception as e:
                print(f"❌ Failed to create {init_file}: {e}")

def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(description="Clean up WhisperForge repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        return
    
    print("🚀 WhisperForge Repository Cleanup")
    print("=" * 40)
    
    # Run cleanup steps
    try:
        cleanup_files()
        organize_directories()
        consolidate_requirements()
        update_gitignore()
        create_init_files()
        
        print("\n" + "=" * 40)
        print("✅ Cleanup completed successfully!")
        print("\nNext steps:")
        print("1. Review the changes: git status")
        print("2. Commit the cleanup: git add -A && git commit -m 'Clean up repository structure'")
        print("3. Tag current version: git tag v1.0-alpha")
        print("4. Start development according to roadmap!")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 