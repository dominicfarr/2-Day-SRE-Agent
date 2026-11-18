# PLAN.md

## Intent

A public, honest emulation of Samsara's SRE AI: an agent that diagnoses injected incidents in a toy system, writes an RCA, escalates severity on proof of impact, and rolls back the deploy it identifies as the cause — but only when its evidence actually crosses a threshold. The deliverable is the working system plus a measured evaluation of it, not a demo. It exists to show hands-on agentic AI and MCP experience for a "Dev Agents and SRE AI" role, building on real on-call/observability experience (human playbooks, not agentic ones) at a previous job.

## Goals

- A toy multi-service system with real, versioned deploys and real structured logs/metrics.
- A fault injector covering four distinct scenario shapes, only one of which should ever trigger a rollback.
- An agent that reasons over MCP tools, applies an explicit Rollback Policy, and writes a structured RCA.
- A 12-incident eval harness reporting RCA Accuracy, Correct/False/Missed Rollback, Time to RCA, and Token Usage per Incident.
- A README that reports results honestly, including where the agent gets it wrong.

## Non-Goals

- Agent Gateway, cloud runners, Kubernetes, real cloud infrastructure, a UI, multi-agent orchestration. (Mentioned in the README only as "next step.")
- A production-grade observability stack (Prometheus/Grafana) or a database — files are sufficient for this scope.
- Cloud-hosted model inference for the deployed agent. This is a local, zero-marginal-cost training system.

## Anti-Goals

- A rigged eval where every scenario "obviously" implies its correct action. The Chaos Toggle / Deploy Ledger split (ADR 0001) and the Noisy Decoy's second real deploy exist specifically so the agent can get it wrong, and the eval has to say so when it does.
- Polished-looking RCA output that overstates the agent's actual certainty. Confidence is categorical (Low/Medium/High) precisely to avoid false numeric precision.

## Constraints

- Day 1: target system, fault injector, MCP tools. Day 2: agent, eval, README.
- Fully local: `docker compose up` brings up the target system; one separate command runs the eval. No cloud inference cost — the agent runs against a local Ollama model. Must run comfortably on an Apple M1, 16GB.
- Prefer simple and correct over clever. Report results honestly, including failures.
- Python stack via `uv` (ruff, pyright, pytest) — already settled by this repo's base standards, not re-decided here.

## Architecture

### Target system

Three services in a chain: `api-gateway` → `orders-service` → `payments-service` (the downstream dependency), plus a small load generator driving continuous traffic so logs and metrics are never empty.

Each service emits one structured JSON log line per request to stdout, and appends the same line to a shared `./logs/<service>.jsonl` (bind-mounted). The MCP tools `query_logs` and `get_metrics` read these files directly and compute error-rate / p50 / p95 latency over a requested time window on demand — no Prometheus/Grafana.

### Deploys and fault injection

Each service's live image version is tracked in a **Deploy Ledger**: an append-only record of which version is live and which preceded it, which `list_deploys` and `rollback` operate on. `rollback(service, version)` changes which tagged image is live for that service and restarts it.

Faults split into two mechanisms (ADR 0001):

- **Bad Deploy**: a genuine regression (e.g. a slow query) ships in a new version of `orders-service`, recorded in the Deploy Ledger. The only scenario where Rollback is correct.
- **Noisy Decoy**: a Bad Deploy as above, *plus* a second, unrelated, harmless deploy (a no-op version bump on another service) landing around the same time. Tests whether the agent attributes the incident to the actually-guilty deploy, not just the most recent one.
- **Config Drift**: a Chaos Toggle changes behaviour outside of any deploy. Never touches the Deploy Ledger. Rollback is wrong here even if a recent deploy coincides.
- **Downstream Dependency Outage**: a Chaos Toggle degrades `payments-service`, producing symptoms on `orders-service` that must not be attributed to `orders-service`'s own deploy.

### Agent

Built with `pydantic-ai` against a local `qwen3:8b` model served by Ollama (ADR 0003, superseding ADR 0002's Claude Agent SDK approach — ruled out once cloud-hosted inference was off the table). The toy system's MCP server (`query_logs`, `get_metrics`, `list_deploys`, `rollback`), built on the official `mcp` package's bundled `mcp.server.fastmcp.FastMCP`, is registered as pydantic-ai's MCP tool source. pydantic-ai's structured-output support validates the RCA against its schema directly.

Three Runbooks, each with the shape symptom → triage steps → decision rule → action, loaded in full into the system prompt on every incident (no dynamic selection — unneeded complexity at only three):

1. **Error Rate Triage**
2. **Latency Triage**
3. **Deploy Correlation & Rollback Decision** — applies the Rollback Policy below once a candidate cause is found.

### Rollback and escalation policy

Two-tier:

- **Escalate** Severity from SEV-3 to SEV-2 whenever error rate or p95 latency breaches a threshold for a sustained window.
- **Roll back** only when, additionally, a Deploy Ledger entry's timestamp precedes the breach onset within a short correlation window, the regression signal started only after that deploy (not before), and no Chaos Toggle-shaped explanation fits better.

Confidence (Low/Medium/High) reflects how much of that evidence checklist is met. Anything short of full, unambiguous evidence → the agent recommends but does not execute. A global dry-run flag is a hard safety valve on top of this, independent of confidence — nothing ever touches Docker when it's set, regardless of what the agent decides.

Exact numeric thresholds (breach %, correlation window minutes) are implementation detail for the builder, not re-litigated here.

### Eval harness

12 incidents: 3 runs each of the four scenarios, with randomized timing offsets and (for Noisy Decoy) which service the harmless second deploy touches — not one fixed script repeated identically.

Metrics, per the Evaluation section of `GLOSSARY.md`: RCA Accuracy (category-level only — exact deploy attribution is covered by the rollback metrics, not a separate accuracy sub-metric), Correct Rollback, False Rollback, Missed Rollback, Time to RCA (clock starts at fault injection, not at metric-breach detection), and Token Usage per Incident (tokens + wall-clock latency — no dollar figure; inference is local and free).

## What's left to the builder

Not grilled, because the answer wouldn't change what gets built — pick the obvious thing and move on:

- Exact MCP tool parameter/return shapes for `query_logs`, `get_metrics`, `list_deploys`, `rollback`.
- The specific regression implemented in the Bad Deploy version (e.g. a slow query), and the specific Chaos Toggle implementation (env var vs. small control endpoint) for Config Drift and Downstream Dependency Outage.
- Exact numeric constants in the Rollback Policy (breach thresholds, correlation window).
- Repo/code layout: a single `uv` workspace covering the three services, the MCP server, the agent, the fault injector, and the eval harness.
- Where the agent/MCP server/eval harness process runs relative to Docker: on the host, orchestrating the dockerized target system via the `docker compose` CLI and shared log files — implied directly by "runnable with `docker compose up` plus one command for the eval."
- README's trust-ladder section content (dry-run → suggest → act-with-approval → autonomous) — narrative only, describes a future expansion path beyond what's actually implemented here (dry-run + confidence gate).

## Future versions (explicitly out of this build)

- A real database for the Deploy Ledger, and DB migration-failure as a fifth fault scenario.
- Any of the Non-Goals above, if this ever grows past a training exercise.

## References

- `GLOSSARY.md` — full domain vocabulary (Incident, RCA, Evidence, Confidence, Rollback Policy, Trust Ladder, Deploy Ledger, Chaos Toggle, Runbook, the four Fault Scenarios, and the Evaluation metrics).
- `docs/adr/0001-chaos-toggles-decoupled-from-deploy-ledger.md`
- `docs/adr/0002-claude-agent-sdk-over-hand-rolled-loop.md` (superseded)
- `docs/adr/0003-pydantic-ai-local-ollama-over-claude-agent-sdk.md`
- `docs/DEVELOPMENT.md`, `CONTRIBUTING.md` — this repo's standing engineering practices, settled scope, not re-decided here.
