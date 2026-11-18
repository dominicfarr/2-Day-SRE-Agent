# 2-Day SRE Agent

This project emulates a first-line on-call SRE agent: it diagnoses injected incidents in a toy system, writes a root cause analysis, and decides whether to escalate severity or roll back the deploy it blames.

## Language

**Incident**:
A period during which the toy system's observable behaviour (errors, latency) degrades enough to warrant investigation.
_Avoid_: Issue, outage (reserve "outage" for the dependency-outage fault scenario specifically)

**Root Cause Analysis (RCA)**:
The agent's structured output for an incident: the cause it identifies, the evidence it cites, its confidence, and its recommended action.
_Avoid_: Report, diagnosis

**Evidence**:
A specific, checkable signal (a metric breach, a log pattern, a deploy's timing) that supports or rules out a candidate cause in an RCA.
_Avoid_: Proof, data

**Confidence**:
The agent's own calibrated belief that its stated cause is correct: Low, Medium, or High, depending on how much of the Rollback Policy's evidence checklist is met. Used to gate whether it recommends, asks for approval, or acts.
_Avoid_: Score, certainty percentage (Confidence is categorical, not numeric, so it never overstates precision the agent doesn't have)

**Severity**:
The incident's escalation level: SEV-3 by default, escalated to SEV-2 when the Rollback Policy's breach threshold is crossed. There is no SEV-1; this toy system is too small to earn that scale.
_Avoid_: Priority, P1/P2

**Rollback**:
Reverting a service to a previously deployed version, the action the agent takes only when its rollback policy's threshold is met.
_Avoid_: Revert, undo

**Rollback Policy**:
The explicit rule that decides whether an incident's evidence and confidence are sufficient to roll back automatically, recommend a rollback for approval, or neither.
_Avoid_: Threshold (the policy is more than its numeric threshold)

**Trust Ladder**:
The planned progression of how much the agent is allowed to do unsupervised on an incident: dry-run only, then suggest, then act with approval, then act autonomously within a bounded blast radius.
_Avoid_: Autonomy level, maturity model

**Deploy Ledger**:
The authoritative history of which version of each service is live and which versions preceded it, the record `list_deploys` and `rollback` operate on.
_Avoid_: Deploy history, release log

**Chaos Toggle**:
A fault the agent must diagnose that is deliberately not recorded in the Deploy Ledger, so that blaming "the last deploy" is wrong by construction.
_Avoid_: Fault injection (reserve for the fault injector as a whole, which also drives real deploys)

**Runbook**:
A written procedure the agent follows for one class of incident: symptom, triage steps, decision rule, action. Loaded as a Skill, not stuffed into a single system prompt.
_Avoid_: Playbook, SOP

## Fault scenarios

**Bad Deploy**:
A fault scenario where a genuine regression is introduced in a new deployed version; the only scenario where Rollback is the correct action.
_Avoid_: Regression (the regression is the cause; "Bad Deploy" is the scenario)

**Config Drift**:
A fault scenario where a Chaos Toggle changes the system's behaviour outside of any deploy, so Rollback is the wrong action even though a recent deploy may coincide.
_Avoid_: Configuration error

**Downstream Dependency Outage**:
A fault scenario where a service's dependency degrades via a Chaos Toggle, producing symptoms on a dependent service that must not be attributed to that dependent service's own deploy.
_Avoid_: Dependency failure

**Noisy Decoy**:
A Bad Deploy that also has a second, unrelated, harmless deploy landing around the same time; the incident has one real cause, but two candidate deploys. Tests whether the agent attributes the incident to the actually-guilty deploy, not just the most recent one.
_Avoid_: Red herring, distractor

## Evaluation

**Time to RCA**:
The eval's measure of how fast the agent closes an incident: the clock starts when the fault injector introduces the fault, not when a metric first breaches a threshold.
_Avoid_: Detection time, response time (both imply a monitoring/alerting layer this project doesn't have)

**RCA Accuracy**:
Whether the agent named the right Fault Scenario category for an incident (Bad Deploy, Config Drift, Downstream Dependency Outage, or Noisy Decoy). Graded at the category level; naming the exact deploy is a separate concern, covered by Correct Rollback below.
_Avoid_: Correctness (too broad; this metric is specifically about the cause category)

**Correct Rollback**:
The agent rolled back the right service to the right prior version on a Bad Deploy or Noisy Decoy incident.
_Avoid_: True positive

**False Rollback**:
The agent rolled back on a Config Drift or Downstream Dependency Outage incident, where no deploy was at fault.
_Avoid_: False positive

**Missed Rollback**:
The agent did not roll back on a Bad Deploy or Noisy Decoy incident, where a deploy was at fault.
_Avoid_: False negative

**Token Usage per Incident**:
The total input and output tokens the agent spends across an incident, including every tool call round trip. No dollar conversion: inference runs locally, so there's no API cost to convert to — tokens and wall-clock latency are the resource cost that matters here.
_Avoid_: Token Cost (implies a $ figure this project no longer has), spend
