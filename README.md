# isco-docs-hub

Central documentation hub for DCCA ISCO. Aggregates curated documentation from external GitHub repositories, applies privacy redactions, and publishes a static MkDocs site to AWS (S3 + CloudFront).

## How it works

```
GitHub source repos                   This repo                          AWS                SharePoint
───────────────────                   ─────────                          ───                ──────────
DCCA-WPSITE/docs/*.md  ─┐
                        │
[future repo]/docs/*.md ─┼──> sync_sources.py ──> docs/imported/  ──>  S3 + CloudFront ──> Embed web part
                        │   (allowlist + redactions)                                          on SP page
docs/manual/*.md ───────┘
(non-Git docs committed here)
```

- **Source repos don't push.** This repo *pulls* from them, controlled entirely by `config/sources.yaml`.
- **Selective publishing.** Only files explicitly listed in `sources.yaml` are imported. Source repos can keep their internal docs (operations runbooks, patch registers, etc.) private to their repo.
- **Light redaction.** `config/redactions.yaml` strips AWS account IDs, resource identifiers, and ARNs at sync time. CIDRs and high-level architecture content are preserved.
- **Public site.** The CloudFront URL is publicly accessible. If governance later requires gated access, auth can be added in front of CloudFront (Lambda@Edge + OIDC, or Cognito with Entra federation) without changing the build or content.

## Repository layout

```
.
├── docs/
│   ├── index.md                      # landing page
│   ├── imported/                     # auto-populated by sync_sources.py (gitignored)
│   └── manual/                       # commit non-Git-source docs here directly
├── config/
│   ├── sources.yaml                  # which files to pull from which repos
│   └── redactions.yaml               # regex rules applied to pulled Markdown
├── scripts/
│   └── sync_sources.py               # GitHub API → docs/imported/
├── terraform/
│   ├── main.tf                       # S3 + CloudFront + OAC + IAM deploy role
│   ├── variables.tf
│   └── outputs.tf
├── .github/workflows/
│   ├── sync.yml                      # daily + manual: refresh imports, open PR
│   ├── deploy.yml                    # on push to main: build + s3 sync + invalidate
│   └── ci.yml                        # on PR: mkdocs build --strict
└── mkdocs.yml                        # MkDocs Material config
```

## Adding a new source repository

1. Edit `config/sources.yaml` and append a new source entry.
2. Open a PR. CI validates the YAML and rebuilds the site.
3. On merge, the next sync run (within 24 hours, or trigger `Sync source repos` manually) pulls the listed files into `docs/imported/`. Another PR is auto-opened with the imported content.
4. Review the imported files (especially redactions), then merge to publish.

The source repository requires no setup — no workflows, no permissions, nothing to install. It only needs to be readable by GitHub Actions running in this repo (public repos work without setup; private repos need a token with `contents: read` granted to this repo).

## Adding a non-Git document

Drop the `.md` file directly in `docs/manual/` and commit. It's published the next time `deploy.yml` runs.

## Updating redactions

Edit `config/redactions.yaml` and re-run the sync workflow. CIDRs are intentionally not redacted — they're useful and not sensitive for RFC1918 internal ranges.

## First-time setup (one-time)

These are the bootstrap steps for a brand-new clone of this repo into the dev AWS account:

### 1. Apply Terraform

```bash
cd terraform/
aws sso login --profile development
AWS_PROFILE=development terraform init
AWS_PROFILE=development terraform plan
AWS_PROFILE=development terraform apply
```

### 2. Configure GitHub repository variables

After `terraform apply`, set these as repository **Variables** (Settings → Secrets and variables → Actions → Variables tab) using values from `terraform output`:

| Variable | Source |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `terraform output deploy_role_arn` |
| `AWS_S3_BUCKET` | `terraform output bucket_name` |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID` | `terraform output cloudfront_distribution_id` |

### 3. Trigger the first deploy

Push any change to `main` (or run the `Build and deploy site` workflow manually). The site goes live at the URL in `terraform output cloudfront_url`.

### 4. Add to SharePoint

On your SharePoint hub page, add an **Embed** web part. Set the URL to the CloudFront URL. Save and publish.

## Local development

```bash
pip install mkdocs-material pymdown-extensions pyyaml requests
GH_TOKEN=<token> python scripts/sync_sources.py     # pull latest imported docs
mkdocs serve                                          # preview at http://127.0.0.1:8000
```
