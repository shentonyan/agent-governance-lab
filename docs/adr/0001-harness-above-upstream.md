# ADR 0001: Harness sits above upstream, no modification

Status: accepted

## Context
Upstream contemplative-agent keeps module-level state (axiom prompt cache, circuit breaker),
so two conditions cannot share a process. It exposes an `LLMBackend` protocol that can be injected.

## Decision
Run one process per experimental condition. Inject our own backend. Do not edit or vendor
upstream; fetch a pinned revision with `scripts/fetch_upstream.py`.

## Consequences
Upstream upgrades are a deliberate re-pin. Anything upstream does not expose cannot be tested here.
