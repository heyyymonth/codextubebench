#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "__pycache__", "runs", "build", "dist"}
FORBIDDEN_NAMES = {
    "cookies.json",
    "browser_profile",
    "oauth_token.json",
    "refresh_token.txt",
    "raw_trace.jsonl",
}
PATTERNS = {
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "authorization header": re.compile(r"Authorization:\s*Bearer\s+\S+", re.I),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "absolute user path": re.compile("/Us" + r"ers/[^/\s]+/"),
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".py",
    ".csv", ".ini", ".cfg", ".sh", ".html", ".css",
}


def findings(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.name in FORBIDDEN_NAMES:
            problems.append(f"{relative}: forbidden release artifact name")
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{relative}: possible {label}")
    return problems


def main() -> int:
    problems = findings()
    if problems:
        print("\n".join(problems))
        return 1
    print("release check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
