# ADR 0002: Seeded backend and hash-chained ledger

Status: accepted

## Context
Upstream's built-in Ollama call sets no seed, and runs are otherwise hard to audit.

## Decision
Per-call seed = f(base seed, call index, prompt). Every call (prompt, options, response) is appended
to a SHA-256 hash-chained JSONL ledger. Only loopback endpoints are allowed and environment proxies
are ignored.

## Consequences
Repeatability on one machine/build is expected, not guaranteed across hardware or Ollama versions;
M0 measures it. Ledgers contain full prompts, so they are never committed.
