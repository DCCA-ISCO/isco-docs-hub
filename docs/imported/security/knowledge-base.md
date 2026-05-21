!!! info "Source"
    Imported from [`DCCA-ISCO/dcca-security`](https://github.com/DCCA-ISCO/dcca-security) · [View on GitHub](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/SECURITY_KNOWLEDGE_BASE.md)

# DCCA Security Knowledge Base

What security controls are in place, what they protect, and how to use them.

**Last updated:** 2026-05-20

---

## Architecture Overview

All security services are managed centrally from the **audit account** (delegated admin) using Terraform (`live/security-services/`). Findings from all accounts roll up into Security Hub in the audit account, providing a single dashboard.

```
Management Account
  └── AWS Organizations (10 member accounts)
        ├── Audit Account (delegated admin — 897729111590)
        │     ├── Security Hub ← aggregates all findings
        │     ├── GuardDuty (admin detector)
        │     ├── Inspector v2 (org admin)
        │     ├── IAM Access Analyzer (org-wide, dcca-org-analyzer)
        │     ├── Config Aggregator (all accounts/regions)
        │     └── Config Conformance Packs (CIS v1.4 L1+L2)
        ├── Dev / Prod / Networking / Operations / Log Archive / QA / Prod-Secure
        │     ├── GuardDuty detector (managed by audit, auto-enabled)
        │     ├── Inspector scanning (auto-enabled: EC2 + ECR)
        │     └── Config recorder (Control Tower) + conformance pack rules
        └── Production (<aws-account-id>) — additional
              └── GuardDuty EC2 Runtime Monitoring (ENABLED — ~$97.50/month)
```

---

## Services at a Glance

| Service | What It Does | Coverage | Alerts Via |
|---|---|---|---|
| **GuardDuty** | Threat detection — analyzes CloudTrail, VPC flow logs, DNS logs | All accounts | Security Hub |
| **Inspector v2** | Vulnerability scanning — CVEs in OS packages on EC2, ECR images | All accounts (auto-enabled) | Security Hub |
| **Security Hub** | Central dashboard — aggregates findings, scores against CIS/NIST/FSBP | All accounts | Lambda → Teams + SES (deployed, disabled to reduce noise — see Notifications below) |
| **IAM Access Analyzer** | Detects resource policies granting access outside the org | Org-wide (dcca-org-analyzer) | Security Hub |
| **Config** | Compliance evaluation — checks resources against CIS benchmark rules | All accounts via org conformance packs | Security Hub |
| **CloudTrail** | Audit logging — records all API calls org-wide | All accounts/regions (org trail) | N/A (log source) |
| **WPScan** (GitHub Actions) | WordPress vuln scanning — checks plugins against CVE database | Dev (weekly) | Email/Slack |

---

## What's Protected and How

These services protect **all applications and resources** across every account in the org (~20 applications across dev and prod), not just a single workload.

### All EC2 Instances (all applications)
- **OS vulnerabilities:** Inspector continuously scans installed packages on every EC2 instance across all accounts for known CVEs.
- **Malware:** GuardDuty EBS Malware Protection scans EBS snapshots when a threat is detected on any instance.
- **Compromise indicators:** GuardDuty monitors all instances for crypto mining, C2 communication, unauthorized API usage.
- **CIS compliance:** Config rules check security group settings, EBS encryption, IAM instance profiles, etc.

### All RDS Databases (all applications)
- **Brute force / anomalous logins:** GuardDuty RDS Login Events monitors authentication patterns on every RDS instance org-wide.
- **CIS compliance:** Config rules check encryption at rest, public accessibility, backup retention.

### All S3 Buckets
- **Data exfiltration:** GuardDuty S3 Data Events detects unusual access patterns, mass downloads, public exposure on every bucket.
- **CIS compliance:** Config rules check bucket policies, encryption, versioning, public access blocks.

### IAM / Account Security (org-wide)
- **CIS Config rules enforce:** Access key rotation (90 days), password policy (14 char min, 90-day expiry, 24-generation reuse), MFA on root, unused credentials cleanup.
- **GuardDuty detects:** Compromised credentials, unusual API calls from unexpected geolocations.

### Application-Specific Scanning
Some applications have additional scanning beyond the org-wide baseline:
- **WordPress:** WPScan checks core/plugin CVEs weekly via GitHub Actions (`check-wp-updates.yml`). This covers the application layer that Inspector can't see.
- **Other applications:** Rely on the org-wide services above. Consider adding application-specific scanners as needed.

---

## How to Use

### Viewing Findings

**Security Hub Console** (audit account):
1. Log in to the audit account
2. Navigate to Security Hub → Findings
3. Filter by severity, service, account, or compliance standard

**CLI quick checks:**
```bash
# Critical findings across all services
aws securityhub get-findings \
  --filters '{"SeverityLabel":[{"Value":"CRITICAL","Comparison":"EQUALS"}]}' \
  --profile audit --region us-west-2 \
  --query 'Findings[].[Title,Severity.Label,Resources[0].Id]' \
  --output table

# GuardDuty findings (last 24h)
aws guardduty list-findings \
  --detector-id bcca94c6a6ffb2624305f949263af785 \
  --finding-criteria '{"Criterion":{"updatedAt":{"GreaterThanOrEqual":'"$(date -d '24 hours ago' +%s)"'000}}}' \
  --profile audit --region us-west-2

# Inspector findings — critical EC2 vulns
aws inspector2 list-findings \
  --filter-criteria '{"severity":[{"comparison":"EQUALS","value":"CRITICAL"}],"resourceType":[{"comparison":"EQUALS","value":"AWS_EC2_INSTANCE"}]}' \
  --profile audit --region us-west-2 \
  --query 'findings[].[title,severity,resources[0].id]' \
  --output table

# Config compliance summary
aws configservice get-compliance-summary-by-config-rule \
  --profile audit --region us-west-2
```

### Notifications

Security Hub CRITICAL + HIGH findings trigger a Lambda (`dcca-security-hub-notify`) via EventBridge rule `dcca-security-hub-critical-high`. The Lambda sends:
- **Teams:** Adaptive Card via Power Automate webhook (SSM param: `/dcca/security/teams-webhook-url`)
- **SES email:** To mahhomau@dcca.hawaii.gov, isco-infra@dcca.hawaii.gov, cfaso@dcca.hawaii.gov from noreply-security@dcca.hawaii.gov

**Currently disabled** to reduce noise while baseline findings are being remediated. Re-enable when finding volume is manageable:
```bash
aws events enable-rule --name dcca-security-hub-critical-high --profile audit
```

**Note:** SES is in sandbox mode — emails only reach verified addresses until production access is requested.

---

### Responding to Findings

| Finding Source | Typical Response |
|---|---|
| **GuardDuty — compromised instance** | Isolate instance (security group), investigate, rebuild or patch |
| **GuardDuty — RDS brute force** | Check RDS auth logs, rotate credentials, verify security group rules |
| **Inspector — critical CVE** | Patch the affected instance/AMI; prioritize by severity and application criticality |
| **Config — non-compliant resource** | Fix the resource config (e.g., enable encryption, tighten security group) |
| **WPScan — plugin CVE** | WordPress-specific: patch via `update-wordpress.yml` or disable the vulnerable plugin |

### Compliance Dashboards

Security Hub scores your environment against these frameworks:
- **CIS AWS Foundations Benchmark v1.2, v1.4, v3.0** — AWS account security best practices
- **AWS Foundational Security Best Practices (FSBP)** — AWS-recommended security controls
- **NIST 800-53 v5.0** — US federal security framework

View scores: Security Hub → Security standards → each standard shows a compliance percentage.

---

## Scanning Coverage Summary

| Layer | Scanner | Frequency | Scope |
|---|---|---|---|
| OS packages (CVEs) | Inspector v2 | Continuous | All EC2 instances, all accounts |
| Threat detection | GuardDuty | Continuous (15-min publish) | All accounts — EC2, RDS, S3, IAM, DNS, VPC |
| EC2 runtime behavior | GuardDuty Runtime Monitoring | Continuous | Production account only (<aws-account-id>) |
| CIS compliance | Config conformance packs | Continuous (on resource change) | All accounts — all resource types |
| ECR container images | Inspector v2 | On push + continuous rescan | All accounts (auto-enabled) |
| External access policies | IAM Access Analyzer | Continuous | Org-wide — S3, IAM roles, KMS, SQS, Lambda, Secrets Manager |
| WordPress core/plugins | WPScan + wp-cli | Weekly (Monday) | Dev instance via SSM (app-specific) |
| OS patching (WordPress) | AMI rebuild | Monthly (2nd of month) | Dev → Prod (app-specific) |

---

## Terraform Management

All security service config lives in `live/security-services/`. To make changes:

```bash
cd live/security-services
terraform plan    # review changes
terraform apply   # apply (conformance packs take ~30 min)
```

**Important:** Org conformance pack operations (create/update/delete) take 20-40 minutes. Timeouts are set to 40 minutes in the Terraform config.

---

## Gaps / Future Work

- [ ] **Investigate account 971422687324 ("Production-Secure"):** Excluded from CIS conformance packs — no Config recorder, unknown purpose. Enroll via Control Tower or decommission, then remove from exclusion list.
- **Note:** Management account (273354624047) is permanently excluded from conformance packs — AWS does not allow org conformance packs to target the management account.
- [ ] **SES production access:** Notifications Lambda is deployed but SES is in sandbox mode — submit production access request in SES console.
- [ ] **Re-enable notifications:** EventBridge rule `dcca-security-hub-critical-high` is disabled. Enable once baseline findings are remediated.
- [ ] **Tag enforcement (Step 8):** Config rules requiring specific tags on EC2 and RDS
- [ ] **CloudWatch cross-account observability (Step 9):** OAM sink in audit account + links from all source accounts
- [ ] **Prod WPScan:** Weekly WordPress scan currently only covers dev — extend to prod
- [ ] **Lambda scanning:** Inspector Lambda scanning disabled (no Lambda workloads yet — enable when added)
- [ ] **Central Security Hub config:** Currently `LOCAL` mode — consider `CENTRAL` to push standards uniformly to all member accounts
