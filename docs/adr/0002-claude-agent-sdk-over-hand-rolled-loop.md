---
status: superseded by ADR-0003
---

# Claude Agent SDK over a hand-rolled tool-use loop

The agent could be built as a manual loop against the raw Anthropic Messages API, or on the Claude Agent SDK, which has native MCP-server registration and Skills loading. We chose the Agent SDK: the project's stated purpose is demonstrating hands-on experience building production agents for a role centered on Dev Agents and SRE AI, and the SDK's native MCP and Skills support directly line up with how the toy system's tools (`query_logs`, `get_metrics`, `list_deploys`, `rollback`) and runbooks are structured. The trade-off is less bespoke tool-loop code to show off; we judged correct use of the SDK a stronger signal than reimplementing what it already does well.
