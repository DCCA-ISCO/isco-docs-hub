!!! info "Source"
    Imported from [`DCCA-ISCO/dcca-security`](https://github.com/DCCA-ISCO/dcca-security) · [View on GitHub](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/REMEDIATION_PROCESS.md)

# Remediation Process

**CIS Control:** Safeguard 7.2  
**Owner:** ISCO-INFRA (isco-infra@dcca.hawaii.gov)  
**Last reviewed:** 2026-05-20  
**Review cadence:** Monthly

---

## Purpose

This document defines the risk-based remediation strategy for security findings identified across the DCCA Hawaii AWS organization. It applies to all findings surfaced in Security Hub, GuardDuty, Inspector v2, IAM Access Analyzer, and WPScan.

---

## Remediation SLAs

Remediation targets are based on finding severity:

| Severity | Target Remediation Window | Escalation If Missed |
|---|---|---|
| **CRITICAL** | 15 calendar days | Escalate to Peter Faso (<personal-email>) immediately |
| **HIGH** | 30 calendar days | Escalate to Peter Faso (<personal-email>) at 30 days |
| **MEDIUM** | 90 calendar days | Document at next monthly review |
| **LOW** | 180 calendar days | Accept or document at next monthly review |

The clock starts when the finding first appears as NEW/ACTIVE in Security Hub (or in the source tool for WPScan findings).

**Exception — CISA Known Exploited Vulnerabilities (KEV):** Any finding tied to a vulnerability listed in the [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) must be remediated within **7 calendar days**, regardless of the severity assigned by Security Hub. Inspector findings include CVE identifiers that can be cross-referenced against the KEV catalog.

---

## Remediation Workflow

1. **Identify** — Findings appear in Security Hub. CRITICAL and HIGH findings trigger automated notification via the `dcca-security-hub-critical-high` EventBridge rule (when enabled) to Teams and email.

2. **Triage** — ISCO-INFRA reviews the finding to confirm it is valid (not a false positive) and determines the affected resource and account owner.

3. **Track** — Open findings are tracked in [`docs/TODOS.md`](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/docs/TODOS.md). Each finding entry includes the Security Hub control ID, affected account, and the specific remediation action required.

4. **Remediate** — Apply the fix. Infrastructure changes are made via Terraform in `live/security-services/` where possible. Console-only fixes are documented with the account and steps taken.

5. **Verify** — Security Hub auto-resolves findings when the underlying condition is corrected (typically within 24 hours for Config-based controls; Inspector re-scans occur within hours of package changes). Confirm the finding moves to `RESOLVED` status.

6. **Close** — Mark the item in [`docs/TODOS.md`](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/docs/TODOS.md) as complete with the date resolved.

---

## Monthly Review

ISCO-INFRA conducts a monthly review of all open Security Hub findings. The review covers:

- New CRITICAL and HIGH findings since the last review
- Findings approaching or past their SLA window
- Risk acceptances and suppressions — confirm they are still justified
- Progress on findings tracked in [`docs/TODOS.md`](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/docs/TODOS.md)

The monthly review date and a brief summary of actions taken should be noted in the git commit history for [`docs/TODOS.md`](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/docs/TODOS.md).

---

## Risk Acceptance

When a finding cannot be remediated within the SLA (due to architectural constraints, vendor dependency, cost, or deliberate policy decision), it may be formally accepted:

1. Document the finding, reason for acceptance, and risk owner in the **Policy Decisions** table in `CLAUDE.md`
2. Suppress the finding in Security Hub via `batch-update-findings` (set `WorkflowStatus = SUPPRESSED`)
3. Record the acceptance in [`docs/TODOS.md`](https://github.com/DCCA-ISCO/dcca-security/blob/main/docs/docs/TODOS.md) as a closed item with rationale
4. Review accepted risks at each monthly review cycle to confirm they remain appropriate

Risk acceptance decisions for CRITICAL findings require Peter Faso (<personal-email>) sign-off.

---

## Escalation Path

| Condition | Action |
|---|---|
| CRITICAL finding open > 15 days | ISCO-INFRA notifies Peter Faso (<personal-email>) (<personal-email>) |
| HIGH finding open > 30 days | ISCO-INFRA notifies Peter Faso (<personal-email>) |
| Finding requires cross-account coordination | ISCO-INFRA contacts the relevant account owner directly |
| Finding in networking account may be intentional | Coordinate with networking team before remediating |
