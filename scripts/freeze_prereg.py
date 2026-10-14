"""Append file hashes and the model digest to the Experiment 1 pre-registration.

Run once, immediately before committing the freeze tag. Idempotent: refuses to append twice.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREREG = ROOT / "docs" / "experiments" / "exp01" / "PREREG.md"
MARK = "<!-- frozen-artefacts -->"
FILES = [
    "data/probes/exp01_f1_pool.jsonl",
    "data/probes/exp01_pilot2.jsonl",
    "third_party/contemplative-agent-rules/rules/contemplative/contemplative-axioms.md",
    "src/agent_governance_lab/probes.py",
    "src/agent_governance_lab/exp01.py",
    "src/agent_governance_lab/constitutions/variants.py",
]
MODEL = "llama3.1:8b"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_row() -> str:
    out = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        if line.startswith(MODEL):
            return " ".join(line.split())
    raise SystemExit(f"model {MODEL} not found in `ollama list`")


def main() -> int:
    text = PREREG.read_text(encoding="utf-8")
    if MARK in text:
        print("already frozen; nothing to do")
        return 0
    rows = [f"| `{f}` | `{sha(ROOT / f)}` |" for f in FILES]
    block = [
        "",
        MARK,
        "",
        f"Model row from `ollama list` at freeze time: `{model_row()}`",
        "",
        "Upstream pins: see `scripts/fetch_upstream.py`.",
        "",
        "| file | SHA-256 |",
        "|---|---|",
        *rows,
        "",
    ]
    PREREG.write_text(text.rstrip("\n") + "\n" + "\n".join(block), encoding="utf-8", newline="\n")
    print("\n".join(block))
    return 0


if __name__ == "__main__":
    sys.exit(main())
