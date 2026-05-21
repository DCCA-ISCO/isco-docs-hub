# CI/CD

Standardized CI/CD pipeline documentation and workflow templates for Python applications deploying to AWS Windows Servers via Systems Manager (SSM). Designed to be adopted across all DCCA ISCO projects without requiring individual teams to build pipeline infrastructure from scratch.

Source repository: [`DCCA-ISCO/.github`](https://github.com/DCCA-ISCO/.github)

---

## Pipeline Features

**Quality Gates (every PR and push)**

| Check | Tool |
|---|---|
| Unit testing with coverage | pytest (70% coverage threshold) |
| Dependency vulnerabilities | pip-audit, safety |
| Static security analysis | bandit |
| Code quality | flake8, pylint |
| Application smoke test | Import validation + health check |
| Dependency conflict detection | pip check |

**Deployment**

- Passwordless — SSM-based, no SSH or RDP keys
- Multi-environment — dev and prod with approval gates
- Automated pre-deployment backups
- Rollback support

---

## Quick Start

If you're new to this pipeline, read the docs in this order:

1. [Responsibilities](docs/00-RESPONSIBILITIES-BREAKDOWN.md) — Know what your role covers
2. [Pipeline Overview](docs/01-OVERVIEW.md) — Understand the architecture
3. [AWS Infrastructure Setup](docs/02-AWS-INFRASTRUCTURE-SETUP.md) — Provision IAM, EC2, SSM
4. [GitHub Configuration](docs/03-GITHUB-CONFIGURATION.md) — Set up secrets and environments
5. Pick a [workflow template](https://github.com/DCCA-ISCO/.github/tree/main/workflow-templates/) and customize it

---

## Documents

| Document | Audience | Description |
|---|---|---|
| [Overview](README.md) | Everyone | Pipeline overview, template list, quick start |
| [Responsibilities](docs/00-RESPONSIBILITIES-BREAKDOWN.md) | Everyone | DevOps vs Developer responsibility split |
| [Pipeline Overview](docs/01-OVERVIEW.md) | Everyone | Architecture and pipeline flow |
| [AWS Infrastructure Setup](docs/02-AWS-INFRASTRUCTURE-SETUP.md) | DevOps / Infra | IAM roles, EC2, SSM agent setup |
| [GitHub Configuration](docs/03-GITHUB-CONFIGURATION.md) | DevOps / Developers | Secrets, environments, protection rules |
| [Testing Standards](docs/04-TESTING-STANDARDS.md) | Developers / QA | Testing requirements and coverage rules |
| [Security Standards](docs/05-SECURITY-STANDARDS.md) | Security / Developers | Security scanning tools and requirements |
| [SSM Deployment SOP](docs/06-SSM-DEPLOYMENT-SOP.md) | DevOps / Operations | Deployment procedures and rollback |
| [Troubleshooting](docs/07-TROUBLESHOOTING.md) | Everyone | Common failures and fixes |
| [Workflow Customization](docs/08-WORKFLOW-CUSTOMIZATION.md) | Developers / DevOps | Adapting shared workflow templates |
