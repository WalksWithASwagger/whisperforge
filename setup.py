"""WhisperForge environment setup - creates a virtual environment and installs dependencies."""

import subprocess
import sys
import os
import venv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
REQUIREMENTS = os.path.join(PROJECT_DIR, "requirements.txt")

if sys.platform == "win32":
    PYTHON = os.path.join(VENV_DIR, "Scripts", "python")
    PIP = os.path.join(VENV_DIR, "Scripts", "pip")
else:
    PYTHON = os.path.join(VENV_DIR, "bin", "python")
    PIP = os.path.join(VENV_DIR, "bin", "pip")


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


def install_requirements():
    """Install project dependencies from requirements.txt."""
    if not os.path.exists(REQUIREMENTS):
        print("  !! requirements.txt not found, skipping dependency install.")
        return

    print_step("Upgrading pip")
    subprocess.check_call(
        [PYTHON, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
    )

    print_step(f"Installing dependencies from {os.path.basename(REQUIREMENTS)}")
    subprocess.check_call([PIP, "install", "-r", REQUIREMENTS])
    print("\n     All dependencies installed.")


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


def run():
    print("=" * 50)
    print("  WhisperForge - Environment Setup")
    print("=" * 50)

    create_venv()
    install_requirements()
    verify_install()

    print("\n" + "=" * 50)
    print("  Setup complete. Run main.py to start the app.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run()
