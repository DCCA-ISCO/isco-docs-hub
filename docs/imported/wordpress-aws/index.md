# WordPress (cca.hawaii.gov)

The DCCA WordPress platform serves the Hawaii Department of Commerce and Consumer Affairs at [https://cca.hawaii.gov](https://cca.hawaii.gov). It is hosted on AWS in `us-west-2` and managed entirely as code — infrastructure via Terraform, AMIs via Packer, and deployments via GitHub Actions.

Source repository: [`DCCA-ISCO/DCCA-WPSITE`](https://github.com/DCCA-ISCO/DCCA-WPSITE)

---

## Architecture at a Glance

| Layer | Technology |
|---|---|
| CDN / WAF | Cloudflare APO + AWS WAFv2 |
| Load Balancer | ALB (application) + NLB (network, static IPs) |
| Compute | EC2 (t3.medium), Ubuntu 24.04, Nginx, PHP 8.4-FPM |
| Database | RDS MySQL 8.0 (Multi-AZ) |
| Shared Storage | EFS (NFS mounted at `/var/www/html`) |
| Secrets | SSM Parameter Store |
| CI/CD | GitHub Actions + OIDC federation |
| IaC | Terraform 1.10, Packer, Ansible |
| Backup | AWS Backup (EFS), RDS automated snapshots |

**Design principles:** Immutable infrastructure (instances replaced via AMI swap, never patched in place), Infrastructure as Code, Least Privilege IAM, Multi-AZ High Availability, and separate AWS accounts for dev and prod.

---

## Documents

| Document | Description |
|---|---|
| [Architecture](architecture.md) | Full solutions architect document — account/network topology, compute, data, security, CI/CD, HA/DR, monitoring, cost, and decision log |
| [Security Review](security.md) | Security posture details — AMI hardening, network security groups, encryption at rest and in transit, IAM access controls, WAF configuration |
