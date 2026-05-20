# DCCA Security Services — Setup Walkthrough

How the centralized security monitoring stack was built, step by step. Written so someone can understand what was done, why, and roughly how — without needing to read every Terraform file.

---

## Prerequisites

- AWS Organizations with Control Tower enabled
- Four accounts: Management, Audit (delegated admin), Dev, Prod
- Control Tower had already provisioned basic GuardDuty detectors and a CloudTrail org trail
- Audit account designated as the delegated admin for GuardDuty, Inspector, and Config (via management account CLI commands — see [Delegated Admin Setup](#delegated-admin-setup))

---

## Step 1 — Terraform Workspace

**What:** Created `live/security-services/` as the Terraform workspace for all centralized security config.

**Why:** Security services span the whole org but are managed from the audit account. A dedicated workspace keeps this config isolated from per-environment infrastructure (dev/prod WordPress stacks).

**How:** Provider targets the audit account as primary, with aliased providers for dev and prod where direct detector management is needed (e.g., GuardDuty EBS Malware). State stored in the existing S3 backend under `security-services/terraform.tfstate`.

---

## Step 2 — GuardDuty Hardening

**What:** Imported and reconfigured the existing GuardDuty detectors across all three accounts.

**Why:** Control Tower enabled GuardDuty but left it on default settings — slow alerting (6-hour publish cycle) and most protection features disabled. For a WordPress workload running on EC2 with RDS, we needed:
- Fast finding delivery for incident response
- S3 monitoring (media uploads, backups)
- EBS malware scanning (EC2 instances)
- RDS login anomaly detection (WordPress database)

**Changes made:**

| Setting | Before | After |
|---|---|---|
| Publishing frequency | 6 hours | 15 minutes |
| S3 Data Events | Off | On (all accounts) |
| EBS Malware Protection | Off | On (all accounts) |
| RDS Login Events | Off | On (audit + org-wide auto-enable) |
| Org auto-enable (S3, RDS) | Off | On — new accounts get these features automatically |

**Technical note:** EBS Malware and the org-level `update-organization-configuration` for some features require the management account. We worked around this by directly importing and configuring the dev/prod detectors via aliased providers, and enabling features individually via `aws_guardduty_organization_configuration_feature` (which works from the delegated admin).

---

## Step 3 — Inspector v2

**What:** Enabled Inspector v2 for EC2 and ECR scanning, org-wide.

**Why:** Inspector continuously scans EC2 instances for known CVEs in installed OS packages (e.g., outdated OpenSSL on a WordPress AMI). It also scans ECR container images. This was completely disabled across the org before.

**What it does NOT cover:** WordPress application-level vulnerabilities (core, plugins, themes). That's handled by the existing `check-wp-updates.yml` GitHub Actions workflow which uses WPScan. Inspector and WPScan are complementary — OS layer vs. application layer.

**How:** Enabled in the audit account first, then configured org-wide auto-enable so dev, prod, and future accounts automatically get EC2 + ECR scanning. Lambda scanning left off (no Lambda workloads currently).

**Prerequisite:** Org admin ran `aws inspector2 enable-delegated-admin-account` from the management account to authorize the audit account.

---

## Step 4 — Security Hub (Codified)

**What:** Imported the existing Security Hub org configuration into Terraform.

**Why:** Security Hub was already well-configured (CIS v1.2, v1.4, v3.0, FSBP, NIST 800-53 all active). The goal was to codify the config so it's managed as code and won't drift silently.

**Current settings:**
- `auto_enable: true` — new member accounts get Security Hub automatically
- `auto_enable_standards: DEFAULT` — new accounts get FSBP enabled by default
- `configuration_type: LOCAL` — each account manages its own standards (avoids disrupting Control Tower's member account setup)

**No changes were made to the actual Security Hub configuration — this was a codify-and-manage step.**

---

## Step 5 — CloudTrail

**What:** Verified the existing org-wide CloudTrail trail. No changes needed.

**Why:** Control Tower had already set up a multi-region org trail. This is the audit log that feeds GuardDuty and is required by many CIS benchmark rules.

---

## Step 6 — AWS Config: Org Aggregator + CIS Conformance Packs

**What:** Deployed an org-wide Config aggregator and CIS v1.4 Level 1 + Level 2 conformance packs.

**Why:** AWS Config evaluates resources against compliance rules. The aggregator pulls compliance data from all accounts/regions into the audit account so there's a single-pane view. The CIS conformance packs deploy ~80+ Config rules based on the CIS AWS Foundations Benchmark v1.4, covering:
- IAM hygiene (access key rotation, password policy, MFA)
- Logging and monitoring (CloudTrail, Config, flow logs)
- Networking (default VPC security groups, open ports)
- Data protection (S3 bucket policies, encryption)

**How:**
- Created an IAM role allowing Config to query Organizations for account membership
- Deployed `aws_config_configuration_aggregator` with `all_regions = true`
- Deployed two `aws_config_organization_conformance_pack` resources (Level 1 and Level 2) using CloudFormation-style YAML templates
- Set 40-minute create/update/delete timeouts because org conformance packs take 20-40 minutes to roll out across all member accounts

**Input parameters configured:** Access key max age (90 days), password max age (90 days), minimum password length (14), password reuse prevention (24).

**Prerequisite:** Org admin ran `aws organizations enable-aws-service-access --service-principal config-multiaccountsetup.amazonaws.com` and registered the audit account as Config delegated admin.

---

## Step 7 — Notifications

**Status:** Not yet implemented.

**Plan:** Wire Security Hub findings to SNS topics for email and/or Slack alerting. This will cover findings from all integrated services (GuardDuty, Inspector, Config) in a single notification pipeline.

---

## Step 8 — Tagging Rules

**Status:** Not yet implemented.

**Plan:** Deploy Config rules enforcing required tags on EC2 and RDS resources.

---

## Step 9 — CloudWatch Cross-Account Observability

**Status:** Not yet implemented.

**What:** Centralize CloudWatch logs, metrics, and traces from all accounts into the audit account so engineers can debug any application without switching accounts.

**Why:** Currently each account is an island — debugging requires logging into the specific account running the application. With ~20 applications across dev and prod, this is unsustainable. Cross-account observability solves this with a single pane of glass.

**Architectural decision:** The audit account will serve as the central observability aggregator in addition to its security role. This is appropriate for the current team size where the same people monitor both security and application health. If the team grows to the point where developers and security engineers are distinct groups, a dedicated monitoring account can be introduced and OAM sinks migrated.

**How:** AWS CloudWatch Observability Access Manager (OAM):
- Audit account gets an OAM **sink** — declares it will accept CloudWatch data from source accounts
- Dev and prod accounts get OAM **links** pointing at the sink — share metrics, logs, and traces into it
- From the audit account, CloudWatch Logs Insights queries, metrics, and dashboards span all accounts simultaneously

**What this enables:**
- One CloudWatch Logs Insights query to search application logs across all accounts at once
- Cross-account dashboards — build once, monitor everything
- Centralized alarm routing from any account into a single SNS topic

---

## Delegated Admin Setup

These one-time commands were run from the **management account** to authorize the audit account (897729111590) as the delegated admin:

```bash
# Inspector
aws inspector2 enable-delegated-admin-account \
  --delegated-admin-account-id 897729111590 \
  --region us-west-2

# Config
aws organizations register-delegated-administrator \
  --account-id 897729111590 \
  --service-principal config-multiaccountsetup.amazonaws.com

aws organizations enable-aws-service-access \
  --service-principal config-multiaccountsetup.amazonaws.com
```

These are idempotent — running them again is harmless.
