"""Command line entry point: ``agl``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_governance_lab.constitutions.variants import VARIANTS, VariantError, make_variant
from agent_governance_lab.ledger import verify_ledger
from agent_governance_lab.m0 import run_self_check


def _cmd_verify(args: argparse.Namespace) -> int:
    rep = verify_ledger(Path(args.path))
    if rep.ok:
        print(f"OK: {rep.entries} entries, head {rep.last_hash[:12]}")
        return 0
    print(f"FAIL: {rep.error}", file=sys.stderr)
    return 1


def _cmd_variants(args: argparse.Namespace) -> int:
    text = Path(args.axioms).read_text(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ids = [v for v, spec in VARIANTS.items() if spec.lang == args.lang]
    try:
        for vid in ids:
            (out / f"{vid}.md").write_text(make_variant(text, vid), encoding="utf-8", newline="\n")
    except VariantError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {len(ids)} variants to {out}")
    return 0


def _cmd_self_check(args: argparse.Namespace) -> int:
    results = run_self_check(args.model, args.base_url, args.seed)
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name}: {r.detail}")
    return 0 if all(r.ok for r in results) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agl", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify-ledger", help="re-compute a ledger's hash chain")
    v.add_argument("path")
    v.set_defaults(func=_cmd_verify)

    m = sub.add_parser("make-variants", help="write axiom-4 wording variants")
    m.add_argument("--axioms", required=True, help="markdown file containing the axioms")
    m.add_argument("--lang", choices=["en", "zh"], required=True)
    m.add_argument("--out", required=True)
    m.set_defaults(func=_cmd_variants)

    s = sub.add_parser("self-check", help="M0: Ollama reachable, model present, determinism")
    s.add_argument("--model", required=True)
    s.add_argument("--base-url", default="http://127.0.0.1:11434")
    s.add_argument("--seed", type=int, default=0)
    s.set_defaults(func=_cmd_self_check)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code: int = args.func(args)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
