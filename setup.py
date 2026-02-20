"""WhisperForge environment setup - creates a virtual environment and installs dependencies."""

import subprocess
import sys
import os
import venv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
REQUIREMENTS = os.path.join(PROJECT_DIR, "requirements.txt")
REQUIREMENTS_DEV = os.path.join(PROJECT_DIR, "requirements-dev.txt")

if sys.platform == "win32":
    PYTHON = os.path.join(VENV_DIR, "Scripts", "python")
    PIP = os.path.join(VENV_DIR, "Scripts", "pip")
    PRE_COMMIT = os.path.join(VENV_DIR, "Scripts", "pre-commit")
else:
    PYTHON = os.path.join(VENV_DIR, "bin", "python")
    PIP = os.path.join(VENV_DIR, "bin", "pip")
    PRE_COMMIT = os.path.join(VENV_DIR, "bin", "pre-commit")


def print_step(msg):
    print(f"\n  >> {msg}")


def create_venv():
    """Create a fresh virtual environment."""
    if os.path.exists(VENV_DIR):
        print_step(f"Removing existing venv at {VENV_DIR}")
        import shutil
        shutil.rmtree(VENV_DIR)

    print_step(f"Creating virtual environment in {VENV_DIR}")
    venv.create(VENV_DIR, with_pip=True)

    if not os.path.exists(PYTHON):
        print("  !! Failed to create virtual environment.")
        sys.exit(1)

    print("     Done.")


def install_requirements(dev=False):
    """Install project dependencies from requirements.txt (and dev deps if requested)."""
    if not os.path.exists(REQUIREMENTS):
        print("  !! requirements.txt not found, skipping dependency install.")
        return

    print_step("Upgrading pip")
    subprocess.check_call(
        [PYTHON, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
    )

    if dev:
        req_file = REQUIREMENTS_DEV
        if not os.path.exists(req_file):
            print("  !! requirements-dev.txt not found, falling back to requirements.txt")
            req_file = REQUIREMENTS
    else:
        req_file = REQUIREMENTS

    print_step(f"Installing dependencies from {os.path.basename(req_file)}")
    subprocess.check_call([PIP, "install", "-r", req_file])
    print("\n     All dependencies installed.")


def install_pre_commit_hooks():
    """Install pre-commit git hooks into the repository."""
    print_step("Installing pre-commit hooks")
    subprocess.check_call([PRE_COMMIT, "install"], cwd=PROJECT_DIR)
    print("     Hooks installed.")


def verify_install():
    """Quick sanity check that key packages are importable."""
    print_step("Verifying installation")
    result = subprocess.run(
        [PYTHON, "-c", "import streamlit; print(f'  streamlit {streamlit.__version__}')"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(result.stdout.strip())
        print("     Verification passed.")
    else:
        print("  !! Verification failed - streamlit could not be imported.")
        print(result.stderr.strip())
        sys.exit(1)


def run(dev=False):
    print("=" * 50)
    print("  WhisperForge - Environment Setup")
    if dev:
        print("  (dev mode)")
    print("=" * 50)

    create_venv()
    install_requirements(dev=dev)
    verify_install()

    if dev:
        install_pre_commit_hooks()

    print("\n" + "=" * 50)
    print("  Setup complete. Run main.py to start the app.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    dev = "--dev" in sys.argv
    run(dev=dev)
