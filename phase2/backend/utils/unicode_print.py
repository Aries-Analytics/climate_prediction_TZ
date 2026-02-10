"""
Unicode-safe printing utility for Windows compatibility.

This module provides safe printing functions that handle Unicode characters
properly on Windows systems where the default console encoding may not be UTF-8.
"""

import io
import sys


def ensure_utf8_output():
    """
    Ensure stdout and stderr use UTF-8 encoding.

    This is particularly important on Windows where the default console
    encoding is often cp1252 or cp437, which cannot handle Unicode characters
    like ✓, ✗, ×, etc.
    """
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def safe_print(*args, **kwargs):
    """
    Print with automatic fallback for Unicode characters.

    If Unicode characters cannot be encoded, they are replaced with ASCII equivalents.

    Args:
        *args: Arguments to print
        **kwargs: Keyword arguments for print function
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace Unicode characters with ASCII equivalents
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                arg = arg.replace("✓", "[OK]")
                arg = arg.replace("✗", "[X]")
                arg = arg.replace("×", "x")
                arg = arg.replace("═", "=")
                arg = arg.replace("─", "-")
            safe_args.append(arg)
        print(*safe_args, **kwargs)


# Initialize UTF-8 output on module import
ensure_utf8_output()
