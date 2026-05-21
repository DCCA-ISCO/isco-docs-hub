!!! info "Source"
    Imported from [`DCCA-ISCO/DCCA-WPSITE`](https://github.com/DCCA-ISCO/DCCA-WPSITE) · [View on GitHub](https://github.com/DCCA-ISCO/DCCA-WPSITE/blob/main/docs/SECURITY_REVIEW.md)

# Security Review: WordPress AWS Architecture

## 1. AMI Hardening (Packer Build)
The Golden AMI is built using Packer with a multi-stage shell provisioner (`packer/scripts/golden/*.sh`).

*   **Base OS:** Ubuntu 24.04 LTS (Canonical).
*   **System Updates:** All packages are updated to latest versions during build (`apt-get upgrade`).
*   **SSH Hardening:**
    *   Password Authentication: **Disabled**.
    *   Root Login: **Disabled**.
    *   Protocol: SSHv2 only.
*   **Firewall (UFW):**
    *   Default Policy: Deny Incoming, Allow Outgoing.
    *   Allowed Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS).
    *   *Note: In Production, the AWS Security Group overrides the OS firewall for inbound traffic control.*
*   **Automatic Updates:** `unattended-upgrades` package installed and configured for security updates.
*   **Auditing:** `auditd` installed and running.
*   **Cleanup:** Shell history, temporary files, and logs are wiped before AMI creation (`07-cleanup.sh`).

## 2. Network Security (Security Groups)
All resources reside within a VPC. Access is strictly controlled via Security Group referencing (Chain of Trust).

| Resource | Security Group Name | Inbound Rules | Outbound Rules |
| :--- | :--- | :--- | :--- |
| **ALB** | `dcca-prod-sg-alb-1` | **80 (HTTP):** 0.0.0.0/0 (Redirects to 443)<br>**443 (HTTPS):** 0.0.0.0/0 | **All Traffic:** 0.0.0.0/0 |
| **EC2** | `dcca-prod-sg-ec2-1` | **80 (HTTP):** FROM `dcca-prod-sg-alb-1` (ALB Only) | **All Traffic:** 0.0.0.0/0 |
| **RDS** | `dcca-prod-sg-rds-1` | **3306 (MySQL):** FROM `dcca-prod-sg-ec2-1` (EC2 Only) | **All Traffic:** 0.0.0.0/0 |
| **EFS** | `dcca-prod-sg-efs-1` | **2049 (NFS):** FROM `dcca-prod-sg-ec2-1` (EC2 Only) | **All Traffic:** 0.0.0.0/0 |

*   **Key takeaway:** The Database (RDS) and File System (EFS) are **not accessible** from the internet or the ALB. They only accept connections from the application servers. The Application servers only accept HTTP traffic from the Load Balancer.

## 3. Encryption
### Data at Rest
*   **EBS Volumes (EC2):** Encrypted using a Customer Managed KMS Key (`arn:aws:kms:us-west-2:<aws-account-id>:key/8a815b91-593d-409c-a181-272b9896ad65`).
*   **RDS Database:** Encrypted using AWS Managed RDS Key (`storage_encrypted = true`).
*   **EFS File System:** Encrypted using AWS Managed EFS Key.
*   **S3 Bucket:** Server-Side Encryption (SSE-S3, AES-256) enabled by default.

### Data in Transit
*   **Client -> ALB:** HTTPS (TLS 1.2+). Certificate managed by ACM.
    *   *Current Status:* Using Self-Signed Certificate. **MUST** be updated to a Public Certificate for production traffic.
*   **ALB -> EC2:** HTTP (Port 80) over private VPC network.
*   **SSM Session Manager:** Shell sessions are encrypted using the AWS Accelerator KMS Key.

## 4. IAM & Access Control
*   **Principle of Least Privilege:** EC2 Instance Role (`dcca-prod-iam-role-ec2-1`) has minimal permissions:
    *   **S3:** `GetObject`/`PutObject` only on the specific content bucket (`dcca-prod-s3-content-1`).
    *   **SSM:** `GetParameter` only for paths starting with `/wp-prod/`.
    *   **KMS:** `Decrypt` only for the AMI Key and Session Key.
*   **No SSH Keys:** No SSH keys are stored on the instances. Access is exclusively via **AWS Systems Manager (SSM) Session Manager**, which provides audit logging and MFA enforcement (if configured in IAM).
*   **Cross-Account Trust:** Deployment roles trust specific OIDC providers (GitHub Actions) or specific IAM Roles, preventing arbitrary cross-account access.

## 5. Additional Protections
*   **Private Subnets:** EC2, RDS, and EFS reside in Private Subnets with no direct internet ingress. Outbound internet access is routed via NAT Gateway.
*   **WAF (Web Application Firewall):** AWS WAFv2 attached to the ALB (`dcca-{env}-waf-1`). Gated by `enable_waf` variable. Enabled in both dev and prod.

    | Priority | Rule | Type | Action |
    | :--- | :--- | :--- | :--- |
    | 0 | Rate limit (2000 req/5min per IP) | Custom | Block |
    | 1 | AWS Managed - Common Rule Set (CRS) | Managed | Block |
    | 2 | AWS Managed - Known Bad Inputs | Managed | Block |
    | 3 | AWS Managed - SQL Injection | Managed | Block |
    | 4 | AWS Managed - WordPress Application | Managed | Block |
    | 5 | AWS Managed - Amazon IP Reputation List | Managed | Block |
    | 6 | AWS Managed - Anonymous IP List | Managed | Block |
    | 7 | Block wp-config.php access | Custom | Block |
    | 8 | Block xmlrpc.php | Custom | Block |

    *   **Default action:** Allow — WAF only blocks matched requests.
    *   **Logging:** WAF logs to CloudWatch (`aws-waf-logs-dcca-{env}`, 30-day retention).
    *   **Rate limiting** mitigates brute force, DDoS, and search abuse (ref: Feb 27 incident).
    *   **xmlrpc.php** blocked to prevent DDoS amplification and brute force via legacy API.
    *   **wp-config.php** blocked to prevent direct access to database credentials.
    *   **CRS override:** the `SizeRestrictions_BODY` rule in the AWS Common Rule Set is forced to Count mode — its default Block action rejects requests with bodies >8KB, which breaks wp-admin media uploads and page publishing.
*   **CloudWatch Logging:** Application logs (Nginx, PHP) and System logs are shipped to CloudWatch Logs (`/aws/wordpress/dcca-prod-lg-1`) for retention and analysis.

## 6. Vulnerability Detection & Response

### 6.1 WordPress Plugin Vulnerability Scanning (WPScan)
- All active plugins are scanned weekly against the WPScan CVE database via `check-wp-updates.yml`
- WPScan API token is stored exclusively as a GitHub Actions secret (`WPSCAN_API_TOKEN`); never committed to code
- Any plugin with an open CVE triggers an immediate high-priority Teams + SES alert regardless of whether a patched version is available
- Response SLAs (from Patch Management Strategy v1.1):
  - Critical (CVSS ≥ 9.0): patch or disable within 24 hours
  - High (CVSS 7.0–8.9): patch within 7 days
  - Medium/Low: next monthly cycle

### 6.2 Emergency Plugin Disable Procedure
If a plugin has a known CVE and no patch is available, disable it immediately via SSM:
```bash
# Connect via EC2 Instance Connect Endpoint (no SSH key required)
aws ssm start-session --target <instance-id> --region us-west-2

# Disable the vulnerable plugin (EFS-mounted — applies to all instances)
sudo -u www-data wp plugin deactivate <plugin-slug> --path=/var/www/html
```
Document the action in `docs/PATCH_REGISTER.md` with the CVE reference, action taken, and expected remediation date.

### 6.3 Notification & Audit Trail
- All patch events (success and failure) generate a Teams message and SES email using templates from `docs/communications/`
- Every workflow run automatically appends a row to `docs/PATCH_REGISTER.md` (version-controlled in Git), providing an auditable history of all patches
- Quarterly: export Patch Register as PDF and archive for compliance review
