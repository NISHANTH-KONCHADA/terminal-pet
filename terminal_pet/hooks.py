"""Logic for installing the post-commit git hook."""

import os
import stat
import sys
from pathlib import Path

HOOK_NAME = "post-commit"

HOOK_TEMPLATE = """#!/bin/sh
# Installed by Terminal Pet -- feeds your pet after every commit.
{python} -m terminal_pet.cli feed --quiet
"""

APPEND_TEMPLATE = """
# --- Installed by Terminal Pet -- feeds your pet after every commit. ---
{python} -m terminal_pet.cli feed --quiet
"""


def find_git_dir(start_path="."):
    """Walk upward from start_path to find a .git directory."""
    path = Path(start_path).resolve()
    for parent in [path, *path.parents]:
        git_dir = parent / ".git"
        if git_dir.is_dir():
            return git_dir
    return None


def install_hook(start_path="."):
    """Install (or upgrade) the post-commit hook in the current repo.

    Returns a tuple: (success: bool, message: str)
    """
    git_dir = find_git_dir(start_path)
    if git_dir is None:
        return False, "No .git directory found. Run this inside a git repository."

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / HOOK_NAME

    if hook_path.exists():
        existing = hook_path.read_text()
        if "Terminal Pet" in existing:
            return True, f"Hook already installed at {hook_path}"
        # Don't clobber an existing custom hook -- append instead.
        appended = existing.rstrip("\n") + "\n" + APPEND_TEMPLATE.format(python=sys.executable)
        hook_path.write_text(appended)
        _make_executable(hook_path)
        return True, f"Appended Terminal Pet hook to existing hook at {hook_path}"

    hook_path.write_text(HOOK_TEMPLATE.format(python=sys.executable))
    _make_executable(hook_path)
    return True, f"Installed post-commit hook at {hook_path}"


def _make_executable(path):
    current = os.stat(path).st_mode
    os.chmod(path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
