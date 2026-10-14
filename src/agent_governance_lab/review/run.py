"""Run one review arm over a proposal file and write results plus a ledger."""

from __future__ import annotations

import json
from pathlib import Path

from agent_governance_lab.backend.seeded_ollama import SeededOllamaBackend
from agent_governance_lab.constitutions.variants import make_variant
from agent_governance_lab.ledger import Ledger
from agent_governance_lab.review.pipeline import Arm, load_proposals, review

ARM_STAGES: dict[str, tuple[str, ...]] = {
    "S0": ("static",),
    "R0": ("static", "ethics", "safety"),
    "RC": ("static", "ethics", "safety"),
}


def build_arm(aid: str, axioms_path: str | None) -> Arm:
    if aid not in ARM_STAGES:
        raise ValueError(f"unknown arm {aid!r}; implemented: {sorted(ARM_STAGES)}")
    constitution = None
    if aid == "RC":
        if not axioms_path:
            raise ValueError("arm RC needs --axioms (the upstream four-axiom file)")
        constitution = make_variant(Path(axioms_path).read_text(encoding="utf-8"), "C1")
    return Arm(aid, ARM_STAGES[aid], constitution)


def run_arm(
    model: str,
    arm_id: str,
    proposals_path: str,
    out_dir: str,
    axioms: str | None,
    seed: int = 0,
    split: str = "dev",
) -> Path:
    arm = build_arm(arm_id, axioms)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(out / f"{arm_id}.{split}.ledger.jsonl")
    backend = SeededOllamaBackend(model, ledger, base_seed=seed, temperature=0.0)
    res_path = out / f"{arm_id}.{split}.results.jsonl"
    props = [p for p in load_proposals(proposals_path) if split == "all" or p.split == split]
    rows = [review(p, arm, backend) for p in props]
    with res_path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    return res_path
