# ISCO Documentation Hub

Central documentation for the DCCA ISCO team. Aggregates curated docs from GitHub repositories and manually maintained sources into one searchable place.

## How this works

- Each system maintains its source-of-truth docs in its own GitHub repository.
- This hub pulls **selected** files from those repositories on a daily schedule (and on demand).
- The source repo remains canonical. This site is a read-only, rendered, redacted view for stakeholders.

If you spot an error, open a pull request against the **source repository** (linked at the top of each page) — not against `isco-docs-hub`.

---

## Currently published

### WordPress (cca.hawaii.gov)
Source: [`DCCA-ISCO/DCCA-WPSITE`](https://github.com/DCCA-ISCO/DCCA-WPSITE)

| Document | Description |
|---|---|
| [Architecture](imported/wordpress-aws/architecture.md) | AWS infrastructure and solutions architecture |
| [Security Review](imported/wordpress-aws/security.md) | Security posture and review findings |

### CI/CD
Source: [`DCCA-ISCO/.github`](https://github.com/DCCA-ISCO/.github)

| Document | Description |
|---|---|
| [Overview](imported/cicd/README.md) | CI/CD pipeline overview |
| [Responsibilities](imported/cicd/docs/00-RESPONSIBILITIES-BREAKDOWN.md) | Team responsibilities breakdown |
| [Pipeline Overview](imported/cicd/docs/01-OVERVIEW.md) | Detailed pipeline overview |
| [AWS Infrastructure Setup](imported/cicd/docs/02-AWS-INFRASTRUCTURE-SETUP.md) | AWS setup for CI/CD |
| [GitHub Configuration](imported/cicd/docs/03-GITHUB-CONFIGURATION.md) | GitHub Actions configuration |
| [Testing Standards](imported/cicd/docs/04-TESTING-STANDARDS.md) | Testing standards and requirements |
| [Security Standards](imported/cicd/docs/05-SECURITY-STANDARDS.md) | Security standards for pipelines |
| [SSM Deployment SOP](imported/cicd/docs/06-SSM-DEPLOYMENT-SOP.md) | SSM deployment procedures |
| [Troubleshooting](imported/cicd/docs/07-TROUBLESHOOTING.md) | Common issues and fixes |
| [Workflow Customization](imported/cicd/docs/08-WORKFLOW-CUSTOMIZATION.md) | Customizing shared workflows |

### Security
Source: [`DCCA-ISCO/dcca-security`](https://github.com/DCCA-ISCO/dcca-security)

| Document | Description |
|---|---|
| [Knowledge Base](imported/security/knowledge-base.md) | Security knowledge base and reference |
| [Setup Walkthrough](imported/security/setup-walkthrough.md) | Security tooling setup guide |
| [Remediation Process](imported/security/remediation-process.md) | Vulnerability remediation process |
| [Vulnerability Management](imported/security/vulnerability-management-process.md) | Vulnerability management process |

---

## Adding documentation

### From a GitHub repository
Open a PR to [`isco-docs-hub`](https://github.com/DCCA-ISCO/isco-docs-hub) adding an entry to `config/sources.yaml`. The hub pulls; source repos need no changes.

### From SharePoint, local files, or other sources
Place a Markdown file under `docs/manual/` in this repo and add it to `mkdocs.yml`. For SharePoint pages: export or copy content into Markdown format. For local files: convert to Markdown and commit directly.

## Privacy and redaction

This site may be publicly accessible. Documents are filtered through `config/redactions.yaml` before publishing — AWS account IDs, resource identifiers, and ARNs are replaced with placeholders.
