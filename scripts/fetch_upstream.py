"""Clone pinned upstream repositories into ./third_party (gitignored).

Usage: python scripts/fetch_upstream.py
Requires git. Uses whatever proxy git is configured with.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PINS = {
    "contemplative-agent": (
        "https://github.com/shentonyan/contemplative-agent.git",
        "4f070f2b2e2b36864762656a70aa7cb42adb0273",
    ),
    "contemplative-agent-rules": (
        "https://github.com/shimo4228/contemplative-agent-rules.git",
        "c21be2b45f26e06505a4b9d4ce3bd985fce828bb",
    ),
}


def run(*cmd: str, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "third_party"
    root.mkdir(exist_ok=True)
    for name, (url, sha) in PINS.items():
        dest = root / name
        if not dest.exists():
            run("git", "clone", "--quiet", url, str(dest))
        run("git", "fetch", "--quiet", "origin", sha, cwd=dest)
        run("git", "checkout", "--quiet", sha, cwd=dest)
        print(f"{name} @ {sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
