#!/usr/bin/env python3
"""WhisperForge launcher - sets up the environment if needed and starts the app."""

import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
SETUP_SCRIPT = os.path.join(PROJECT_DIR, "setup.py")
APP_SCRIPT = os.path.join(PROJECT_DIR, "app_simple.py")

if sys.platform == "win32":
    PYTHON = os.path.join(VENV_DIR, "Scripts", "python")
    STREAMLIT = os.path.join(VENV_DIR, "Scripts", "streamlit")
else:
    PYTHON = os.path.join(VENV_DIR, "bin", "python")
    STREAMLIT = os.path.join(VENV_DIR, "bin", "streamlit")


def venv_ready():
    """Check that the venv exists and streamlit is installed."""
    if not os.path.exists(PYTHON):
        return False
    result = subprocess.run(
        [PYTHON, "-c", "import streamlit"],
        capture_output=True,
    )
    return result.returncode == 0


def run_setup():
    """Run setup.py using the system Python to create the venv."""
    print("[whisperforge] Virtual environment not found or incomplete.")
    print("[whisperforge] Running first-time setup...\n")
    subprocess.check_call([sys.executable, SETUP_SCRIPT])
    print()


def start_app(extra_args):
    """Launch the Streamlit app inside the venv."""
    cmd = [STREAMLIT, "run", APP_SCRIPT] + extra_args
    print("[whisperforge] Starting WhisperForge...")
    print(f"[whisperforge] Command: {' '.join(cmd)}")
    print("-" * 50)
    os.execv(STREAMLIT, cmd)


def main():
    args = sys.argv[1:]

    # Handle explicit flags
    if "--setup" in args:
        run_setup()
        return

    if "--help" in args or "-h" in args:
        print(
            "WhisperForge Launcher\n"
            "\n"
            "Usage: python main.py [options] [-- streamlit args]\n"
            "\n"
            "Options:\n"
            "  --setup   Force re-create the virtual environment\n"
            "  --help    Show this help message\n"
            "\n"
            "Any arguments after -- are forwarded to streamlit.\n"
            "\n"
            "Examples:\n"
            "  python main.py                       Start the app\n"
            "  python main.py --setup               Re-create the venv\n"
            "  python main.py -- --server.port 8080 Start on a custom port"
        )
        return

    # Split off streamlit args after --
    st_args = []
    if "--" in args:
        idx = args.index("--")
        st_args = args[idx + 1:]

    # Ensure environment is ready
    if not venv_ready():
        run_setup()
        # Re-check after setup
        if not venv_ready():
            print("[whisperforge] Setup finished but environment still looks broken.")
            print("[whisperforge] Try running: python setup.py")
            sys.exit(1)
    else:
        print("[whisperforge] Virtual environment OK.")

    start_app(st_args)


if __name__ == "__main__":
    main()
