#!/usr/bin/env python3
"""Push Sarangsho Plus published editions to the public GitHub Pages repo.

After an edition is published (editions/data-YYYY-MM-DD.json + updated
editions/index.json), this script mirrors the full published set to
Amiroudro/sarangsho-plus-editions so the app can fetch new editions
itself from https://amiroudro.github.io/sarangsho-plus-editions/editions/index.json

Upload path: /opt/hatch/bin/github push-files (the GitHub connector's
snapshot push; see /opt/hatch/connectors/github/references/snapshot-push.md).
NEVER blocks publishing: every failure is logged and the script exits 0,
printing a clear PUSH OK / PUSH FAILED line for the caller (cron run report).

Usage:
  python3 push_editions.py [--dry-run] [--message MSG]
  --dry-run: build staging + manifest, print what would be pushed, do not push.
"""
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # ~/workspace/sarangsho-plus
OWNER = "Amiroudro"
REPO = "sarangsho-plus-editions"
BRANCH = "main"
GITHUB_CLI = "/opt/hatch/bin/github"

# Persistent staging dir (canonical, no trailing slash). The sync record
# lives adjacent: <staging>.muse-github-snapshot-sync.json
STAGING = ROOT / "github-pages"
SYNC_RECORD = Path(str(STAGING) + ".muse-github-snapshot-sync.json")
MANIFEST = Path("/tmp/sarangsho-push-manifest")
LOG = HERE / "push_editions.log"

# Never upload credentials. These basenames are refused even if they
# somehow land in the staging dir.
FORBIDDEN = {"sarangsho-plus-release.keystore", "keystore.properties"}
FORBIDDEN_SUFFIXES = (".keystore", ".pem", ".key", ".p12", ".jks")

README_TEXT = """# Sarangsho Plus — daily editions

Public feed for the Sarangsho Plus app's automatic updates.
`editions/index.json` lists every published edition; the app fetches it
and downloads any edition newer than the ones bundled with it.

- `editions/data-YYYY-MM-DD.json` — one edition (stories, words, phrases,
  MCQs, revision words), English.
- `editions/bn-YYYY-MM-DD.json` — Bengali overlay for the same date.
- `editions/index.json` — the index the app reads.

Published by the Sarangsho Plus daily engine. Human-reviewed before publish.
"""


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def stage():
    """Mirror the live published files into the staging dir. Returns the
    list of repo-relative paths staged."""
    import shutil

    (STAGING / "editions").mkdir(parents=True, exist_ok=True)
    (STAGING / "README.md").write_text(README_TEXT)
    (STAGING / ".gitignore").write_text(
        "*.keystore\nkeystore.properties\n*.pem\n*.key\n*.p12\n*.jks\n"
    )
    paths = ["README.md", ".gitignore"]
    for src in sorted((ROOT / "editions").glob("*.json")):
        if src.name in FORBIDDEN or src.suffix in FORBIDDEN_SUFFIXES:
            raise SystemExit(f"refusing to stage forbidden file: {src.name}")
        shutil.copy2(src, STAGING / "editions" / src.name)
        paths.append(f"editions/{src.name}")
    for src in sorted((ROOT / "app" / "assets" / "editions").glob("bn-*.json")):
        if src.name in FORBIDDEN or src.suffix in FORBIDDEN_SUFFIXES:
            raise SystemExit(f"refusing to stage forbidden file: {src.name}")
        shutil.copy2(src, STAGING / "editions" / src.name)
        paths.append(f"editions/{src.name}")
    return sorted(set(paths))


def write_manifest(paths):
    data = "".join(p + "\0" for p in paths).encode("utf-8")
    if len(data) > 1024 * 1024:
        raise SystemExit("manifest exceeds 1 MiB")
    MANIFEST.write_bytes(data)
    return MANIFEST


def read_sync_record():
    try:
        return json.loads(SYNC_RECORD.read_text())
    except (OSError, ValueError):
        return []


def record_success(commit_sha, paths):
    entries = read_sync_record()
    entries.append(
        {
            "owner": OWNER,
            "repo": REPO,
            "branch": BRANCH,
            "source_dir": str(STAGING),
            "commit_sha": commit_sha,
            "paths": paths,
        }
    )
    tmp = Path(str(SYNC_RECORD) + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(entries, indent=1))
    tmp.replace(SYNC_RECORD)


def remote_head():
    """Current head SHA of the target branch, or None if the repo/branch
    cannot be read (missing repo, empty repo, no access)."""
    try:
        out = subprocess.run(
            [GITHUB_CLI, "call-read-tool", "--name", "list_commits",
             "--arguments-json",
             json.dumps({"owner": OWNER, "repo": REPO, "sha": BRANCH,
                         "perPage": 1})],
            capture_output=True, text=True, timeout=120,
        )
        data = json.loads(out.stdout)
        text = data["result"]["content"][0]["text"]
        commits = json.loads(text)
        if isinstance(commits, list) and commits:
            return commits[0].get("sha")
    except Exception as e:  # noqa: BLE001 - any lookup failure = unknown head
        log(f"remote head lookup failed (treated as unknown): {e}")
    return None


def push(paths, message):
    cmd = [
        GITHUB_CLI, "push-files",
        "--owner", OWNER, "--repo", REPO, "--branch", BRANCH,
        "--message", message,
        "--source-dir", str(STAGING),
        "--paths-file", str(MANIFEST),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, "push-files timed out after 600s"
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return None, f"push-files exit {proc.returncode}: {out.strip()[-500:]}"
    # Confirmed success needs a full commit SHA from the provider result.
    sha = None
    try:
        data = json.loads(proc.stdout)
        sha = data.get("result", {}).get("commit_sha") or data.get("commit_sha")
    except (ValueError, AttributeError):
        pass
    if not sha:
        # Fall back to the text of the result; never invent a SHA.
        import re
        m = re.search(r"\b[0-9a-f]{40}\b", out)
        sha = m.group(0) if m else None
    return sha, out.strip()[-500:]


def main():
    dry_run = "--dry-run" in sys.argv
    message = "Sarangsho Plus editions sync"
    if "--message" in sys.argv:
        i = sys.argv.index("--message")
        if i + 1 < len(sys.argv):
            message = sys.argv[i + 1]
    try:
        paths = stage()
        write_manifest(paths)
        log(f"staged {len(paths)} paths: {paths}")
    except SystemExit as e:
        log(f"PUSH FAILED: staging error: {e}")
        return 0
    if dry_run:
        print("DRY RUN — would push these paths:")
        for p in paths:
            print(f"  {p}")
        print(f"manifest: {MANIFEST} ({MANIFEST.stat().st_size} bytes)")
        print(f"sync record: {SYNC_RECORD} "
              f"({'exists' if SYNC_RECORD.exists() else 'absent'})")
        return 0
    head = remote_head()
    log(f"remote head on {BRANCH}: {head or 'unknown (repo/branch may not exist)'}")
    sha, detail = push(paths, message)
    if not sha:
        log(f"PUSH FAILED: {detail}")
        return 0
    try:
        record_success(sha, paths)
    except OSError as e:
        log(f"PUSH OK commit {sha} but sync record NOT saved: {e}")
        return 0
    log(f"PUSH OK commit {sha} ({len(paths)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
