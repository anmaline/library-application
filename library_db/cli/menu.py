"""
Robust keypress menu for Windows and non-Windows platforms.
"""
import sys


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def get_keypress() -> str:
    """
    Read a single keypress in a cross-platform manner.
    Returns the pressed key as a string (e.g., '1', '2', 'q').
    """
    if _is_windows():
        import msvcrt
        key_bytes = msvcrt.getch()
        try:
            return key_bytes.decode("utf-8").lower()
        except UnicodeDecodeError:
            return ""
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
