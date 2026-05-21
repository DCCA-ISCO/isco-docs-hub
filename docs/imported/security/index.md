# Security

Centralized security monitoring and vulnerability management for the DCCA Hawaii AWS organization. All security services are managed from the **audit account** as delegated admin using Terraform, with findings from all accounts rolling up into Security Hub for a single dashboard view.

Source repository: [`DCCA-ISCO/dcca-security`](https://github.com/DCCA-ISCO/dcca-security)  
Owner: ISCO-INFRA (`isco-infra@dcca.hawaii.gov`)

---

## Security Services at a Glance

| Service | What It Does | Scope |
|---|---|---|
| **GuardDuty** | Threat detection — CloudTrail, VPC flow logs, DNS logs | All accounts (org-managed) |
| **Inspector v2** | CVE scanning — OS packages on EC2 and ECR images | All accounts (auto-enabled) |
| **Security Hub** | Central findings dashboard — CIS/NIST/FSBP scoring | All accounts |
| **IAM Access Analyzer** | Detects resource policies granting access outside the org | Org-wide |
| **AWS Config** | CIS benchmark compliance evaluation | All accounts via org conformance packs |
| **CloudTrail** | Audit logging — all API calls org-wide | All accounts and regions (org trail) |
| **WPScan** | WordPress core and plugin CVE scanning | Dev (weekly via GitHub Actions) |

All findings aggregate into Security Hub in the audit account, which is the single source of truth for vulnerability status across ~10 accounts.

---

## Remediation SLAs

| Severity | Target Window | Escalation |
|---|---|---|
| **CRITICAL** | 15 calendar days | Immediate escalation to Peter Faso |
| **HIGH** | 30 calendar days | Escalate at 30 days |
| **MEDIUM** | 90 calendar days | Document at monthly review |
| **LOW** | 180 calendar days | Accept or document at monthly review |
| **CISA KEV** | 7 calendar days | Regardless of severity assigned by Security Hub |

---

## Documents

| Document | Description |
|---|---|
| [Knowledge Base](knowledge-base.md) | What security controls are in place, what they protect, and how to use them |
| [Setup Walkthrough](setup-walkthrough.md) | How the centralized security stack was built — step by step with rationale |
| [Remediation Process](remediation-process.md) | Risk-based remediation workflow and SLAs for Security Hub findings |
| [Vulnerability Management](vulnerability-management-process.md) | Org-wide vulnerability identification, tracking, and reporting process |
