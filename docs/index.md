# ISCO Documentation Hub

Central documentation for the DCCA ISCO team. Aggregates curated docs from GitHub repositories and manually maintained sources into one searchable place.

Source-of-truth docs stay in their own repositories. This hub pulls selected files, applies redactions, and publishes a rendered, read-only view for stakeholders.

If you spot an error, open a pull request against the **source repository** (linked at the top of each page) — not against `isco-docs-hub`.

---

## Currently Published

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

## Adding Documentation

### From a GitHub Repository

The hub pulls files from external repositories using an allowlist defined in [`config/sources.yaml`](https://github.com/DCCA-ISCO/isco-docs-hub/blob/master/config/sources.yaml). The source repository needs **no changes** — the hub pulls; sources don't push.

#### Prerequisites

The `GH_SYNC_TOKEN` secret in this repo must have read access to the source repository. If it does not, the sync will fail with a 404. Contact a repo admin to update the token scope before opening your PR.

#### Step 1 — Identify the files you want to publish

In the source repository, find the exact file paths you want to include. Example: `docs/ARCHITECTURE.md`, `docs/images/diagram.png`. Only files you explicitly list will be pulled — there is no wildcard or folder-level import.

#### Step 2 — Edit `config/sources.yaml`

Add a new entry to the `sources` list. Each entry has the following fields:

```yaml
sources:
  - name: my-system              # Short ID. Becomes the folder under docs/imported/.
    title: My System             # Display name shown in the site nav.
    repo: DCCA-ISCO/my-repo      # GitHub org/repo.
    branch: main                 # Branch to pull from.
    files:
      - src: docs/OVERVIEW.md    # Path to the file in the source repo.
        dest: my-system/overview.md  # Published path under docs/imported/.
        nav_title: Overview      # Label shown in the nav sidebar.
      - src: docs/images/arch.png
        dest: my-system/images/arch.png  # Images are copied as-is (no nav_title needed).
```

**`title`** — the section label in the left nav. If omitted, defaults to the title-cased `name` (e.g., `my-system` → `My System`).

**`nav_title`** — the page label in the left nav. If omitted, defaults to the title-cased destination filename stem (e.g., `overview.md` → `Overview`).

**Naming the `dest` path:** Use lowercase, hyphen-separated names (e.g., `my-system/setup-guide.md`). Avoid keeping the original uppercase filename — the hub uses clean, readable URLs.

**Binary files** (`.png`, `.jpg`, `.gif`, `.svg`, `.pdf`) are copied without modification and are never added to the nav. Markdown files are passed through redactions (see below).

#### Step 3 — Handle broken links (optional but recommended)

When a document links to a file in the source repo that you are **not** publishing in the hub, that link will break. Use `link_rewrites` to redirect those links to their GitHub source instead:

```yaml
    link_rewrites:
      - description: Point unpublished sibling docs at GitHub
        pattern: '\]\(OPERATIONS\.md(#[^)]*)?\)'
        replace: '](https://github.com/DCCA-ISCO/my-repo/blob/main/docs/OPERATIONS.md\1)'
```

You can also use `link_rewrites` to remap a filename if you renamed it in `dest`:

```yaml
      - description: Remap renamed file to its published path
        pattern: '\]\(ARCHITECTURE\.md(#[^)]*)?\)'
        replace: '](overview.md\1)'
```

Each rule is a Python-compatible regex `pattern` and a `replace` string. Rules are applied in order.

#### Step 4 — Open a PR

CI will validate `sources.yaml` and do a full site build. Once the PR merges, the next scheduled sync (daily at 08:00 HST) will automatically:

- Pull the files into `docs/imported/`
- Create a section landing page at `docs/imported/<name>/index.md` (if one doesn't already exist)
- Add the section and its pages to the site nav in `mkdocs.yml`

You can also trigger a sync immediately rather than waiting for the schedule:

=== "GitHub web UI"
    1. Go to the [isco-docs-hub Actions tab](https://github.com/DCCA-ISCO/isco-docs-hub/actions/workflows/sync.yml)
    2. Click **Run workflow** on the right side of the page
    3. Leave the branch as `master` and click the green **Run workflow** button

=== "gh CLI"
    ```
    gh workflow run sync.yml
    ```

The sync creates a follow-up PR (`chore/sync-imported-docs`) containing the pulled files, an auto-generated section landing page, and the updated nav. Review the diff to verify redactions look correct, then merge to publish.

---

### From SharePoint, Local Files, or Other Non-GitHub Sources

For documents that do not live in a GitHub repository, add them manually to the `docs/manual/` directory. These files are committed directly to `isco-docs-hub` and published on merge — no sync step required.

#### Step 1 — Convert the document to Markdown

The hub renders Markdown. You need to convert your source document before adding it. See the **[Conversion Guide](manual/converting-to-markdown.md)** for format-by-format instructions covering Word, SharePoint, PDF, HTML, and Google Docs — including how to install and use [Pandoc](https://pandoc.org/), handle images, and clean up the output before committing.

Images referenced in the document should be placed in a subfolder alongside the markdown file (e.g., `docs/manual/my-doc/images/`).

#### Step 2 — Add the file to `docs/manual/`

Place your converted file under `docs/manual/`. Use a descriptive, hyphen-separated filename:

```
docs/manual/
  patch-management-policy.md
  incident-response-plan.md
  onboarding-checklist.md
```

If the document has images, create a subdirectory:

```
docs/manual/
  patch-management/
    index.md
    images/
      process-diagram.png
```

#### Step 3 — Update `mkdocs.yml`

Add your file to the `Manual Docs` section in `mkdocs.yml`:

```yaml
  - Manual Docs:
    - manual/index.md
    - Patch Management Policy: manual/patch-management-policy.md
    - Incident Response Plan: manual/incident-response-plan.md
```

#### Step 4 — Open a PR

CI will build the site and catch any broken references. On merge, the deploy workflow publishes the site automatically — no sync needed.

**Note:** Manually maintained documents are not automatically kept in sync with their source. If the SharePoint page or original file is updated, you will need to re-export and update the file in `isco-docs-hub` manually.

---

## Privacy and Redaction

This site may be publicly accessible. All Markdown files pulled from GitHub repositories are passed through `config/redactions.yaml` before publishing. By default, AWS account IDs, resource ARNs, and specific resource identifiers are replaced with placeholders. The Git source repo remains unredacted.

Manually maintained documents (`docs/manual/`) are **not** passed through redactions — review them for sensitive content before committing.
