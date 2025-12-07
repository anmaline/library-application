"""
Virtual environment and Flask dependency bootstrap.
Creates .venv, installs Flask, and relaunches if needed.
"""
import os
import sys
import subprocess
from typing import Tuple


def _is_windows() -> bool:
    return os.name == "nt"


def _venv_paths(base: str = ".venv") -> Tuple[str, str, str]:
    if _is_windows():
        py = os.path.join(base, "Scripts", "python.exe")
        pip = os.path.join(base, "Scripts", "pip.exe")
    else:
        py = os.path.join(base, "bin", "python")
        pip = os.path.join(base, "bin", "pip")
    return base, py, pip


def ensure_setup() -> None:
    """
    Ensure a virtual environment exists and Flask is installed.
    If not running inside a venv, create .venv, install Flask, and re-exec inside the venv.
    If inside a venv, make sure Flask is installed.
    """
    venv_dir, venv_python, _ = _venv_paths()
    in_venv = sys.prefix != sys.base_prefix

    def _has_package(pkg: str) -> bool:
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    if in_venv:
        if not _has_package("flask"):
            print("[setup] Installing Flask in current virtualenv ...")
            subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)
        return

    if not os.path.isdir(venv_dir):
        print("[setup] Creating virtual environment at .venv ...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    print("[setup] Ensuring Flask is installed in .venv ...")
    subprocess.run([venv_python, "-m", "pip", "install", "flask"], check=True)

    print("[setup] Re-launching inside the virtual environment ...\n")
    os.execv(venv_python, [venv_python] + sys.argv)
