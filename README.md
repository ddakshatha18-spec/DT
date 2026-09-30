# Campus Emergency Assistance System

A digital panic-alert platform designed to bridge the gap between students in distress and campus security through instantaneous room-level alerting, structured administrative review workflows, and progressive escalation for false alert management.

## Project Architecture & Modules
- **P1 - Backend & Data**: Database, authentication, API gateway, location directory, and backend services.
- **P2 - Student App**: Panic button UI, building & room selection, emergency submission.
- **P3 - Alert Queue & QA**: Building/room dataset, shared alert-list components, and testing.
- **P4 - Admin Dashboard**: Alert queue, alert details, genuine/false review actions.
- **P5 - Escalation & Integration**: Warning counter, progressive escalation workflow, and Git integration.

## Development Rules
- **Branching**: Each member works on their feature branch (`feature/p<n>-<name>`).
- **Integration**: Feature branches merge into `dev` on Days 5, 8, and final merge to `main` on Day 10.
- **API Contract**: Standardized REST endpoints and OpenAPI schemas established by P1.
