"""Command line entry point: ``agl``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_governance_lab.backend.seeded_ollama import SeededOllamaBackend
from agent_governance_lab.constitutions.variants import VARIANTS, VariantError, make_variant
from agent_governance_lab.exp01 import (
    compare_logodds,
    headroom,
    read_records,
    run_condition,
    run_condition_probs,
    summarize,
    write_records,
)
from agent_governance_lab.ledger import Ledger, verify_ledger
from agent_governance_lab.m0 import run_self_check
from agent_governance_lab.probes import load_scenarios


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


def _cmd_run_exp01(args: argparse.Namespace) -> int:
    out = Path(args.out)
    scenarios = load_scenarios(Path(args.scenarios))
    if args.condition == "C0":
        axioms: str | None = None
    else:
        if not args.axioms:
            print("FAIL: --axioms is required for conditions other than C0", file=sys.stderr)
            return 1
        try:
            axioms = make_variant(Path(args.axioms).read_text(encoding="utf-8"), args.condition)
        except VariantError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
    langs = ["en", "zh"] if args.lang == "both" else [args.lang]
    ledger = Ledger(out / f"{args.condition}.ledger.jsonl")

    def make_backend(seed: int) -> SeededOllamaBackend:
        return SeededOllamaBackend(args.model, ledger, base_seed=seed)

    records = run_condition(
        args.condition,
        axioms,
        scenarios,
        langs,
        list(range(args.seed_start, args.seed_start + args.seeds)),
        [0, 1],
        make_backend,
    )
    write_records(records, out / f"{args.condition}.results.jsonl")
    valid = sum(1 for r in records if r["valid"])
    print(f"{args.condition}: {len(records)} calls, {valid} valid -> {out}")
    return 0


def _cmd_summarize_exp01(args: argparse.Namespace) -> int:
    records = []
    for path in args.results:
        records.extend(read_records(Path(path)))
    print("condition family lang    n  valid  primary_rate  invalid_rate")
    for r in summarize(records):
        print(
            f"{r['condition']:<9} {r['family']:<6} {r['lang']:<4} {r['n']:>4} {r['n_valid']:>6}"
            f"  {r['primary_rate']:>12.3f}  {r['invalid_rate']:>12.3f}"
        )
    return 0


def _cmd_gate_exp01(args: argparse.Namespace) -> int:
    records = []
    for path in args.results:
        records.extend(read_records(Path(path)))
    print("cond fam lang  scen  rate  interm  both  split  none")
    for r in headroom(records):
        print(
            f"{r['condition']:<5}{r['family']:<4}{r['lang']:<5}{r['n_scenarios']:>4}"
            f"{r['rate']:>7.3f}{r['n_intermediate']:>6}"
            f"{r['both']:>8.3f}{r['split']:>7.3f}{r['none']:>7.3f}"
        )
    return 0


def _cmd_run_probs(args: argparse.Namespace) -> int:
    out = Path(args.out)
    scenarios = load_scenarios(Path(args.scenarios))
    if args.condition == "C0":
        axioms: str | None = None
    else:
        if not args.axioms:
            print("FAIL: --axioms is required for conditions other than C0", file=sys.stderr)
            return 1
        try:
            axioms = make_variant(Path(args.axioms).read_text(encoding="utf-8"), args.condition)
        except VariantError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
    langs = ["en", "zh"] if args.lang == "both" else [args.lang]
    ledger = Ledger(out / f"{args.condition}.probs.ledger.jsonl")
    backend = SeededOllamaBackend(args.model, ledger, base_seed=args.seed)
    records = run_condition_probs(args.condition, axioms, scenarios, langs, [0, 1], backend)
    write_records(records, out / f"{args.condition}.probs.jsonl")
    valid = sum(1 for r in records if r["valid"])
    print(f"{args.condition}: {len(records)} calls, {valid} readable -> {out}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    records = []
    for path in args.results:
        records.extend(read_records(Path(path)))
    print("ref  cond lang   n    diff      lo      hi  margin  equivalent")
    for cond in args.conds:
        r = compare_logodds(
            records,
            args.ref,
            cond,
            args.lang,
            args.num,
            args.den,
            args.margin,
            n_comparisons=len(args.conds),
        )
        print(
            f"{r['ref']:<5}{r['cond']:<5}{r['lang']:<4}{r['n']:>4}{r['diff']:>8.3f}"
            f"{r['lo']:>8.3f}{r['hi']:>8.3f}{r['margin']:>8.2f}  {r['equivalent']}"
        )
    return 0


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

    r = sub.add_parser("run-exp01", help="experiment 1, path A: forced-choice probes")
    r.add_argument("--model", required=True)
    r.add_argument("--condition", required=True, help="C0 (no axioms) or a variant id")
    r.add_argument("--axioms", help="markdown file with the axioms (not needed for C0)")
    r.add_argument("--scenarios", default="data/probes/exp01_pilot.jsonl")
    r.add_argument("--lang", choices=["en", "zh", "both"], default="en")
    r.add_argument("--seeds", type=int, default=1, help="number of seeds")
    r.add_argument("--seed-start", type=int, default=0, help="first seed value")
    r.add_argument("--out", required=True)
    r.set_defaults(func=_cmd_run_exp01)

    q = sub.add_parser("run-exp01-probs", help="experiment 1: probability readout (no sampling)")
    q.add_argument("--model", required=True)
    q.add_argument("--condition", required=True)
    q.add_argument("--axioms")
    q.add_argument("--scenarios", required=True)
    q.add_argument("--lang", choices=["en", "zh", "both"], default="en")
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--out", required=True)
    q.set_defaults(func=_cmd_run_probs)

    k = sub.add_parser("compare-exp01", help="paired log-odds comparison against a reference")
    k.add_argument("results", nargs="+")
    k.add_argument("--ref", default="C1")
    k.add_argument("--conds", nargs="+", required=True)
    k.add_argument("--lang", default="en")
    k.add_argument("--num", default="COMFORT_FALSE")
    k.add_argument("--den", default="HONEST_SUPPORT")
    k.add_argument("--margin", type=float, default=0.5)
    k.set_defaults(func=_cmd_compare)

    g = sub.add_parser("gate-exp01", help="sensitivity diagnostics (headroom, order effects)")
    g.add_argument("results", nargs="+")
    g.set_defaults(func=_cmd_gate_exp01)

    r2 = sub.add_parser("run-exp02", help="score a memory backend on a synthetic dataset")
    r2.add_argument("--dataset", required=True, choices=["D2", "D3", "D4", "D4M", "D5"])
    r2.add_argument("--backend", required=True, choices=["B0", "B2o"])
    r2.add_argument("--k", type=int, default=5)
    r2.add_argument("--n", type=int, default=1000, help="writes for D5")
    r2.add_argument("--seed", type=int, default=0)
    r2.add_argument("--out", required=True)
    r2.set_defaults(func=_cmd_run_exp02)

    r3 = sub.add_parser("run-exp03", help="run one review arm over a proposal file")
    r3.add_argument("--model", required=True)
    r3.add_argument("--arm", required=True)
    r3.add_argument("--proposals", required=True)
    r3.add_argument("--axioms")
    r3.add_argument("--seed", type=int, default=0)
    r3.add_argument("--split", choices=["dev", "holdout", "all"], default="dev")
    r3.add_argument("--out", required=True)
    r3.set_defaults(func=_cmd_run_exp03)

    s3 = sub.add_parser("summarize-exp03", help="metrics for review result files")
    s3.add_argument("results", nargs="+")
    s3.set_defaults(func=_cmd_summarize_exp03)

    z = sub.add_parser("summarize-exp01", help="tabulate results files")
    z.add_argument("results", nargs="+")
    z.set_defaults(func=_cmd_summarize_exp01)
    return p


def _cmd_run_exp03(args: argparse.Namespace) -> int:
    from agent_governance_lab.review.run import run_arm

    path = run_arm(
        args.model,
        args.arm,
        args.proposals,
        args.out,
        args.axioms,
        seed=args.seed,
        split=args.split,
    )
    print(f"{args.arm}: wrote {path}")
    return 0


def _cmd_summarize_exp03(args: argparse.Namespace) -> int:
    from agent_governance_lab.review.metrics import error_phi, read_results, summarize

    for res in args.results:
        rows = read_results(res)
        for split in (None, "dev", "holdout"):
            s = summarize(rows, split)
            rb, fr = s["recall_bad"], s["false_reject_good"]
            print(
                f"{rows[0]['arm'] if rows else '?'} [{s['split']}] n={s['n']} "
                f"recall(C+D)={rb['rate']:.2f} [{rb['lo']:.2f},{rb['hi']:.2f}] "
                f"false-reject(A+B)={fr['rate']:.2f} [{fr['lo']:.2f},{fr['hi']:.2f}] "
                f"escalate={s['escalate_all']['rate']:.2f}"
            )
            if split is None:
                for k, v in s["reject_by_subtype"].items():
                    print(f"    {k:<28} reject {v['k']}/{v['n']}")
                print(f"    phi(ethics,safety errors) = {error_phi(rows):.2f}")
    return 0


def _cmd_run_exp02(args: argparse.Namespace) -> int:
    import json

    from agent_governance_lab.memory.datasets import Dataset, make_d2, make_d3, make_d4, make_d5
    from agent_governance_lab.memory.evaluate import evaluate

    ds: Dataset
    if args.dataset == "D5":
        ds = make_d5(args.n, seed=args.seed)
    elif args.dataset == "D4M":
        ds = make_d4(mislabel=True, seed=args.seed)
    elif args.dataset == "D4":
        ds = make_d4(seed=args.seed)
    elif args.dataset == "D3":
        ds = make_d3(seed=args.seed)
    else:
        ds = make_d2(seed=args.seed)
    res = evaluate(args.backend, ds, k=args.k)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    for kind, d in res["kinds"].items():
        print(
            f"{res['dataset']} {res['backend']} k={res['k']} {kind}: n={d['n']} "
            f"hit={d['hit_rate']:.2f} [{d['hit_lo']:.2f},{d['hit_hi']:.2f}] "
            f"top1_hit={d['top1_hit_rate']:.2f} stale/poison-only={d['stale_or_poison_only']} "
            f"top1_bad={d['top1_bad']}"
        )
    print(
        f"writes={res['n_writes']} write_s={res['write_seconds']:.2f} "
        f"query p50={res['query_p50_ms']:.2f}ms p95={res['query_p95_ms']:.2f}ms"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code: int = args.func(args)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
