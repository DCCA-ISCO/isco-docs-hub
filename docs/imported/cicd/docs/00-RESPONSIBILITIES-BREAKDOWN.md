# Roles & Responsibilities Breakdown
Recommended division of responsibilities between **DevOps** and **Solutions Team**.
## 🏗️ DevOps Responsibilities
*Example Files: `02-AWS-INFRASTRUCTURE-SETUP.md`, `03-GITHUB-CONFIGURATION.md`, `06-SSM-DEPLOYMENT-SOP.md`, `08-WORKFLOW-CUSTOMIZATION.md`*
These tasks involve setting up the "factory" and infrastructure that allows developers to work.
*   **Infrastructure Provisioning**:
    *   Setting up AWS IAM roles, EC2 instances, and SSM Agents.
    *   Creating S3 buckets for logs.
    *   Network security (Security Groups, VPC endpoints).
*   **Pipeline Configuration**:
    *   Creating and maintaining GitHub Actions workflow templates (`.yml` files).
    *   Configuring GitHub "Environments" (Dev vs Prod) and protection rules.
    *   Managing Repository Secrets (AWS Credentials, global keys).
*   **Deployment Operations**:
    *   Managing the Standard Operating Procedure (SOP) for deployments.
    *   Handling Production deployments (approvals, scheduling, rollbacks).
    *   Troubleshooting infrastructure connectivity (SSM failures, permission issues).
## 💻 Developer Responsibilities
*Example Files: `04-TESTING-STANDARDS.md`, `05-SECURITY-STANDARDS.md`*
These tasks involve the daily work of building the application within the guardrails set by DevOps.
*   **Code Quality & Testing**:
    *   Writing and maintaining Unit, Integration, and Smoke tests.
    *   Ensuring code coverage meets the 70% threshold.
    *   Running tests locally before pushing to CI.
*   **Application Security**:
    *   Fixing vulnerable dependencies found by `pip-audit`.
    *   Writing secure code (input validation, avoiding hardcoded secrets).
    *   Managing application-specific secrets (requesting them to be added to GitHub).
*   **Configuration**:
    *   Updating `requirements.txt` and `requirements-dev.txt`.
    *   Ensuring the application starts correctly (Smoke Tests) and exposes a health check endpoint.
## 🤝 Shared Responsibilities
*Example Files: `01-OVERVIEW.md`, `07-TROUBLESHOOTING.md`, `README.md`*
*   **Troubleshooting**:
    *   *Devs*: Fix test failures, linting errors, and logic bugs.
    *   *DevOps*: Fix "Instance Not Found", "Permission Denied", or "Deployment Timeout" errors.
*   **Documentation**:
    *   Both teams should keep the `README.md` and `TROUBLESHOOTING.md` up to date as new issues/patterns emerge.
---
### Summary Table
| Document | Primary Owner | Audience | Action Required |
| :--- | :--- | :--- | :--- |
| `01-OVERVIEW.md` | DevOps | Everyone | Read to understand architecture. |
| **`02-AWS-INFRASTRUCTURE-SETUP.md`** | **DevOps** | DevOps | **Setup/Execute**. Run once per env. |
| **`03-GITHUB-CONFIGURATION.md`** | **DevOps** | DevOps | **Setup/Execute**. Config secrets & envs. |
| **`04-TESTING-STANDARDS.md`** | Developers | **Developers** | **Adhere**. Daily coding practice. |
| **`05-SECURITY-STANDARDS.md`** | Security/DevOps | **Developers** | **Adhere**. Fix findings. |
| **`06-SSM-DEPLOYMENT-SOP.md`** | DevOps | DevOps | **Execute**. Run production deploys. |
| `07-TROUBLESHOOTING.md` | DevOps | Everyone | Reference when issues occur. |
| `08-WORKFLOW-CUSTOMIZATION.md` | DevOps | DevOps | Reference for pipeline changes. |
