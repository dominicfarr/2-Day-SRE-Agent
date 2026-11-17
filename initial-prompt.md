# Session Prompt: 2-Day "Mini SRE AI" Build

I'm applying for Samsara's Senior Manager, AI Developer Productivity (Dev Agents and SRE AI). Their SRE AI is an agent that does first-line on-call work in production: it writes a root cause analysis (RCA), escalates severity when it has proof, and rolls back the deploy it identified as the cause. I'm building a small, honest, working emulation of it in 2 days, to show hands-on agentic AI experience in my application.

## My background (context, don't over-index)

- Former Head of Technology at Policy Expert: 100+ microservices, near-zero high-priority downtime. We relied on monitoring, alerts, dashboards and fix playbooks, but nothing agentic.
- Comfortable with Python, TypeScript, Docker, AWS and CI/CD. I'm newer to building production agents and MCP.
- The narrative: "I built the human version of this (observability plus runbooks); here's the agent version."

## Objective

A public GitHub repo where an agent diagnoses injected incidents in a toy system, writes an RCA, and rolls back only when its evidence crosses a threshold. It must include a measured evaluation, not a demo.

## In scope

1. **Target system:** 2–3 small Python services on Docker Compose, with structured logs, basic metrics (latency, error rate), and a deploy history of versioned images that can be rolled back.
2. **Fault injector:** at least 4 scenarios: a bad deploy (the true positive), config drift, a downstream dependency outage (rollback is wrong), and a noisy decoy (an unrelated recent deploy).
3. **Agent:** Claude API with tools exposed through a small MCP server: `query_logs`, `get_metrics`, `list_deploys`, `rollback(service, version)`.
   - Outputs: a structured RCA (cause, evidence, confidence, recommended action) and a severity escalation decision.
   - Rollback is gated by an explicit evidence or confidence policy, plus a dry-run mode.
   - 2–3 runbooks encoded as skills or prompt files, modelled on real on-call playbooks.
4. **Eval harness:** run 10–15 injected incidents and report RCA accuracy, correct rollbacks, false rollbacks, missed rollbacks, time to RCA, and **token cost per incident**.
5. **README:** architecture diagram, a results table, known failure modes, and a short "trust ladder" section on how I'd expand from 2 teams to every team (dry-run, then suggest, then act with approval, then act autonomously within a bounded blast radius).

## Out of scope

Agent Gateway, cloud runners, Kubernetes, real cloud infra, UI, multi-agent orchestration. I'll mention the gateway only as "next step" in the README.

## Constraints

- Timebox: Day 1 for the target system, fault injector and MCP tools. Day 2 for the agent, eval and README.
- Local only, runnable with `docker compose up` plus one command for the eval.
- Prefer simple and correct over clever. Report results honestly, including failures.

## How to work with me

Ask at most 2 clarifying questions, then start scaffolding. Use a task list. Flag scope creep. At the end, draft one quantified resume bullet and a 3-sentence cover-note paragraph from the real eval numbers.
