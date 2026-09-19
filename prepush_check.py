"""
prepush_check.py - run before `git push`. Exit code 1 if anything looks unsafe.

Checks
  1. No hardcoded credentials in tracked files (falls back to a directory walk outside a git repo)
  2. `.env` is git-ignored and NOT tracked
  3. `.env.example` exists (documents required variables without values)

    python prepush_check.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

SECRET_PATTERNS = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    "elevenlabs_key": re.compile(r"\bxi-api-key\s*[:=]\s*['\"][A-Za-z0-9]{20,}['\"]", re.I),
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "assigned_secret": re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|passwd|bearer)\b\s*[:=]\s*['\"][A-Za-z0-9_\-\.\/+=]{16,}['\"]"),
}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".ico", ".woff", ".woff2", ".pyc", ".db", ".sqlite"}
SAFE_LINE = re.compile(r"os\.(getenv|environ)|process\.env|getenv\(|<your[_-]|example|placeholder|xxxx|changeme", re.I)


def tracked_files(root: str) -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
        return [os.path.join(root, p) for p in out.splitlines() if p]
    except Exception:
        found = []
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            found += [os.path.join(d, f) for f in files]
        return found


def scan(root: str) -> list[str]:
    problems = []
    for path in tracked_files(root):
        if os.path.splitext(path)[1].lower() in SKIP_EXT or os.path.basename(path) == "prepush_check.py":
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = os.path.relpath(path, root)
        if os.path.basename(path) == ".env":
            problems.append(f"{rel}: .env is tracked/present in the file set - remove it from git and rotate any keys in it")
        for i, line in enumerate(lines, 1):
            if SAFE_LINE.search(line):
                continue
            for name, pat in SECRET_PATTERNS.items():
                if pat.search(line):
                    problems.append(f"{rel}:{i}: possible {name}")
    return problems


def check_env_hygiene(root: str) -> list[str]:
    problems = []
    gi = os.path.join(root, ".gitignore")
    ignored = os.path.exists(gi) and any(l.strip() in {".env", ".env*", "*.env"} for l in open(gi, encoding="utf-8"))
    if not ignored:
        problems.append(".gitignore does not ignore .env")
    if not os.path.exists(os.path.join(root, ".env.example")):
        problems.append(".env.example is missing (list required variable NAMES only, no values)")
    return problems


def main() -> int:
    root = os.getcwd()
    problems = check_env_hygiene(root) + scan(root)
    if problems:
        print("PRE-PUSH CHECK FAILED")
        for p in problems:
            print("  -", p)
        print("\nIf a real key was ever committed, rotating it is mandatory: deleting the file does not remove it from git history.")
        return 1
    print("Pre-push check passed: no hardcoded credentials found, .env is ignored, .env.example present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
