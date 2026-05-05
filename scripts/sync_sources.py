#!/usr/bin/env python3
"""
Pulls files listed in config/sources.yaml from their source repositories,
applies redactions from config/redactions.yaml, and writes the results into
docs/imported/.

Usage:
    python scripts/sync_sources.py

Authentication:
    Uses GH_TOKEN or GITHUB_TOKEN from the environment for GitHub API requests.
    Public source repos work without a token but get tighter rate limits.
"""
from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path
from typing import Iterable

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "config" / "sources.yaml"
REDACTIONS_FILE = REPO_ROOT / "config" / "redactions.yaml"
IMPORTED_DIR = REPO_ROOT / "docs" / "imported"

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp", ".ico"}


def load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


def github_session() -> requests.Session:
    s = requests.Session()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Accept"] = "application/vnd.github+json"
    s.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return s


def fetch_file(session: requests.Session, repo: str, branch: str, path: str) -> bytes:
    """Fetch a file from a GitHub repo via the contents API."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    r = session.get(url, params={"ref": branch}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, list):
        raise ValueError(f"{repo}:{path} is a directory, expected a file")
    if payload.get("encoding") != "base64":
        raise ValueError(f"unexpected encoding: {payload.get('encoding')}")
    return base64.b64decode(payload["content"])


def apply_redactions(text: str, rules: Iterable[dict]) -> str:
    for rule in rules:
        text = re.sub(rule["pattern"], rule["replace"], text)
    return text


def apply_link_rewrites(text: str, rules: Iterable[dict]) -> str:
    """Source-specific link rewrites — e.g., point links to unpublished
    sibling docs at their GitHub source URL, or remap renamed files."""
    for rule in rules:
        text = re.sub(rule["pattern"], rule["replace"], text)
    return text


def write_file(dest: Path, data: bytes) -> bool:
    """Write data to dest if changed. Returns True if written, False if no change."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.read_bytes() == data:
        return False
    dest.write_bytes(data)
    return True


def main() -> int:
    sources = load_yaml(SOURCES_FILE)["sources"]
    redactions = load_yaml(REDACTIONS_FILE)["redactions"]
    session = github_session()

    written = 0
    skipped = 0
    failures = 0

    for source in sources:
        name = source["name"]
        repo = source["repo"]
        branch = source.get("branch", "main")
        link_rewrites = source.get("link_rewrites", [])
        for entry in source["files"]:
            src = entry["src"]
            dest_rel = entry["dest"]
            dest = IMPORTED_DIR / dest_rel
            try:
                raw = fetch_file(session, repo, branch, src)
                
                suffix = Path(src).suffix.lower()
                if suffix in BINARY_SUFFIXES:
                    data = raw
                else:
                    text = raw.decode("utf-8")
                    text = apply_redactions(text, redactions)
                    text = apply_link_rewrites(text, link_rewrites)
                    data = text.encode("utf-8")
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {repo}:{src} — {exc}", file=sys.stderr)
                failures += 1
                continue

            if write_file(dest, data):
                print(f"  WROTE  {dest.relative_to(REPO_ROOT)}  ({name}: {src})")
                written += 1
            else:
                skipped += 1

    print(f"\nSummary: {written} written, {skipped} unchanged, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
