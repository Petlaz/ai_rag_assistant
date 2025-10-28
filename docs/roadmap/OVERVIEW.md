# Roadmap Overview

This document tracks the high-level evolution of the AI_RAG platform. Each item below summarises major initiatives, their status, and where to find deeper specifications. Update this file (and companion docs) as priorities shift.

| Initiative | Status | Owner | Notes |
|------------|--------|-------|-------|
| Initial AWS deployment plan | ✅ Completed | Platform Team | See [`DEPLOYMENT_PLAN.md`](../DEPLOYMENT_PLAN.md) |
| Production logging & observability | ⏳ In Progress | Platform Team | Create CloudWatch dashboards and alarm strategy |
| CI/CD automation | 🗓 Planned | DevOps Squad | Automate Docker builds + ECS deploys |
| Multi-model orchestration | 🗓 Planned | ML Team | Dynamic selection between Gemma/Mistral/Llama models |
| Security hardening | 🗓 Planned | Security Team | HTTPS, Secrets Manager, IAM least privilege |

## Usage

- Add new roadmap entries as initiatives are scoped.
- Link to detailed specs or tickets in `/docs/roadmap/*` or external systems.
- Update status (`Planned`, `In Progress`, `Completed`, etc.) as work advances.

## Related Documents

- [`DEPLOYMENT_PLAN.md`](../DEPLOYMENT_PLAN.md)
- [`system_design.md`](../system_design.md)
- Future enhancements list inside `DEPLOYMENT_PLAN.md`

