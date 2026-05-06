# GitHub Configuration Guide

## Overview

This guide covers the configuration of GitHub repository settings, secrets, and environments required for the CI/CD pipeline. This setup enables secure, environment-specific deployments without exposing credentials in code.

## Prerequisites

- Completed AWS infrastructure setup (see `02-AWS-INFRASTRUCTURE-SETUP.md`)
- AWS Access Key ID and Secret Access Key for IAM user
- EC2 Instance IDs for dev and production servers
- Repository admin access

## Architecture: Secrets & Environments

```
Repository Secrets (Global)
├── AWS_ACCESS_KEY_ID
├── AWS_SECRET_ACCESS_KEY
├── AWS_REGION
├── APP_PATH
├── SCRIPT_NAME
└── SSM_OUTPUT_BUCKET

GitHub Environments
├── development
│   ├── INSTANCE_ID (dev server)
│   └── SERVER_HOST (dev hostname)
└── production
    ├── INSTANCE_ID (prod server)
    ├── SERVER_HOST (prod hostname)
    └── Protection Rules (approvals, delays)
```

## Step 1: Create GitHub Environments

### 1.1 Navigate to Environments

1. Go to your repository on GitHub
2. Click **Settings** (repository settings)
3. In the left sidebar, click **Environments**
4. Click **New environment**

### 1.2 Create Development Environment

**Environment name**: `development`

Click **Configure environment**

**Protection Rules** (Optional but recommended):
- [ ] **Required reviewers**: Select team members who must approve deployments
- [ ] **Wait timer**: Set delay before deployment (0-43,200 minutes)
- [ ] **Deployment branches**: Limit to `dev` branch only

Click **Save protection rules**

### 1.3 Create Production Environment

**Environment name**: `production`

Click **Configure environment**

**Protection Rules** (Highly recommended):
- [x] **Required reviewers**: Select 1-2 senior team members
- [x] **Wait timer**: Optional 5-10 minute delay for last-minute cancellation
- [x] **Deployment branches**: Limit to `master/main` branch only

Click **Save protection rules**

### 1.4 Environment Variables (Optional)

If you have environment-specific non-secret configuration:
- Click **Add variable**
- Examples: `LOG_LEVEL=DEBUG`, `FEATURE_FLAGS=true`

## Step 2: Configure Repository Secrets

### 2.1 Navigate to Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

### 2.2 Add AWS Credentials

#### AWS_ACCESS_KEY_ID
- **Name**: `AWS_ACCESS_KEY_ID`
- **Secret**: Paste the Access Key ID from IAM user creation
- **Example**: `AKIAIOSFODNN7EXAMPLE`

Click **Add secret**

#### AWS_SECRET_ACCESS_KEY
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Secret**: Paste the Secret Access Key from IAM user
- **Example**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

Click **Add secret**

#### AWS_REGION
- **Name**: `AWS_REGION`
- **Secret**: AWS region where your EC2 instances are located
- **Example**: `us-east-1`, `us-west-2`, `eu-west-1`

Click **Add secret**

### 2.3 Add Application Configuration

#### APP_PATH
- **Name**: `APP_PATH`
- **Secret**: Full Windows path to your application directory on EC2
- **Example**: `C:\Apps\YourApplication`

**Important**:
- Use backslashes (`\`) for Windows paths
- Do NOT include trailing slash
- Ensure this path exists on ALL target servers

Click **Add secret**

#### SCRIPT_NAME
- **Name**: `SCRIPT_NAME`
- **Secret**: Main Python script filename
- **Example**: `app.py`, `main.py`, `server.py`

**Important**: This should be the entry point script that runs your application

Click **Add secret**

#### SSM_OUTPUT_BUCKET
- **Name**: `SSM_OUTPUT_BUCKET`
- **Secret**: S3 bucket name for SSM command logs
- **Example**: `my-company-ssm-logs`

**Important**:
- Use bucket name only (not ARN or URL)
- Do NOT include `s3://` prefix

Click **Add secret**

## Step 3: Configure Environment Secrets

### 3.1 Development Environment Secrets

1. Go to **Settings** → **Environments**
2. Click **development**
3. Scroll to **Environment secrets**
4. Click **Add secret**

#### INSTANCE_ID (Development)
- **Name**: `INSTANCE_ID`
- **Secret**: EC2 Instance ID for development server
- **Example**: `i-0123456789abcdef0`

**How to find**:
```bash
# From AWS CLI
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=YourAppDev" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text
```

Or from AWS Console: **EC2** → **Instances** → Select instance → Copy Instance ID

Click **Add secret**

#### SERVER_HOST (Development)
- **Name**: `SERVER_HOST`
- **Secret**: Hostname or IP for health check
- **Examples**:
  - `dev-app.yourcompany.com`
  - `10.0.1.50`
  - `ec2-xx-xx-xx-xx.compute-1.amazonaws.com`

**Important**: This should be the URL where your application is accessible (without `https://`)

Click **Add secret**

### 3.2 Production Environment Secrets

1. Go to **Settings** → **Environments**
2. Click **production**
3. Click **Add secret**

#### INSTANCE_ID (Production)
- **Name**: `INSTANCE_ID`
- **Secret**: EC2 Instance ID for production server
- **Example**: `i-9876543210fedcba0`

Click **Add secret**

#### SERVER_HOST (Production)
- **Name**: `SERVER_HOST`
- **Secret**: Production hostname or IP
- **Examples**:
  - `app.yourcompany.com`
  - `www.yourcompany.com`
  - `api.yourcompany.com`

Click **Add secret**

## Step 4: Secrets Verification Checklist

Before proceeding, verify all secrets are configured:

### Repository Secrets
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] `AWS_REGION`
- [ ] `APP_PATH`
- [ ] `SCRIPT_NAME`
- [ ] `SSM_OUTPUT_BUCKET`

### Development Environment Secrets
- [ ] `INSTANCE_ID`
- [ ] `SERVER_HOST`

### Production Environment Secrets
- [ ] `INSTANCE_ID`
- [ ] `SERVER_HOST`

## Step 5: Additional Application Secrets (Optional)

If your application requires additional secrets (API keys, database credentials, etc.), add them as environment secrets:

### Examples

**Database Credentials**:
```
Environment: production
Secret Name: DATABASE_URL
Secret Value: postgresql://user:pass@host:5432/dbname
```

**API Keys**:
```
Environment: production
Secret Name: THIRD_PARTY_API_KEY
Secret Value: sk_live_xxxxxxxxxxxxx
```

**Google Cloud Credentials**:
```
Environment: production
Secret Name: GCP_PROJECT_ID
Secret Value: your-project-id-12345
```

### Accessing in Workflows

Application secrets can be accessed in workflow files:

```yaml
- name: Deploy with Environment Variables
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    API_KEY: ${{ secrets.THIRD_PARTY_API_KEY }}
  run: |
    # These environment variables are available in this step
```

## Step 6: Branch Protection Rules (Recommended)

### 6.1 Protect Production Branch

1. Go to **Settings** → **Branches**
2. Click **Add branch protection rule**

**Branch name pattern**: `master` (or `main`)

**Recommended settings**:
- [x] **Require a pull request before merging**
  - [x] Require approvals: 1-2
  - [x] Dismiss stale pull request approvals
- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date
  - Search for and select: `Tests & Code Quality` (after first workflow run)
- [x] **Require conversation resolution before merging**
- [x] **Include administrators** (enforce for everyone)

Click **Create**

### 6.2 Protect Development Branch (Optional)

**Branch name pattern**: `dev`

**Lighter settings**:
- [x] **Require status checks to pass before merging**
  - [x] Select: `Tests & Code Quality`

## Step 7: Configure Workflow Permissions

### 7.1 Set Token Permissions

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests** (if needed)
5. Click **Save**

**Why**: Allows workflows to checkout code, create deployment records, and update statuses.

### 7.2 Allow Workflow Secrets

Ensure **Actions secrets** are enabled:
1. **Settings** → **Actions** → **General**
2. Under **Actions permissions**, verify **Allow all actions and reusable workflows** is selected (or configure allow list)

## Step 8: Test Configuration

### 8.1 Manual Workflow Trigger Test

1. Add a workflow file to your repository (see `workflow-templates/`)
2. Go to **Actions** tab
3. Select your workflow
4. Click **Run workflow** dropdown
5. Select branch (e.g., `dev`)
6. Click **Run workflow**

**Expected**:
- Workflow starts
- Tests execute successfully
- Deployment job requests environment approval (if configured)
- After approval, deployment proceeds

### 8.2 Verify Secrets Access

Add a debug step to your workflow (temporary):

```yaml
- name: Verify Secrets (Debug Only - Remove After Testing)
  run: |
    echo "AWS Region: ${{ secrets.AWS_REGION }}"
    echo "App Path: ${{ secrets.APP_PATH }}"
    echo "Instance ID: ${{ secrets.INSTANCE_ID }}"
    echo "Note: Actual secret values are masked in logs"
```

**Expected**: Masked values appear as `***` in logs, confirming secrets are accessible.

**Important**: Remove debug steps before production use.

## Security Best Practices

### Secrets Management

1. **Never commit secrets** to repository
   - Add to `.gitignore`: `.env`, `credentials.json`, `*.key`

2. **Rotate regularly**
   - AWS keys: Every 90 days minimum
   - Application keys: Per vendor recommendations

3. **Use environment-specific secrets**
   - Separate dev/prod credentials
   - Never use production credentials in development

4. **Minimize secret scope**
   - Use IAM roles over access keys when possible
   - Grant least privilege permissions

5. **Monitor access**
   - Enable CloudTrail for AWS API calls
   - Review GitHub audit log for secret access

### Access Control

1. **Limit repository access**
   - Grant write access only to necessary team members
   - Use read-only access for most developers

2. **Require reviews**
   - Enforce pull request reviews for protected branches
   - Require approval for production deployments

3. **Enable MFA**
   - Require two-factor authentication for all team members
   - Use SSO if available

## Common Configuration Issues

### Workflow Can't Access Secrets

**Symptoms**: `Error: Missing required secret AWS_ACCESS_KEY_ID`

**Solutions**:
1. Verify secret name matches exactly (case-sensitive)
2. Check secret is in correct scope (repository vs environment)
3. Ensure workflow has `secrets: inherit` if calling reusable workflow

### Environment Not Found

**Symptoms**: `Error: Environment 'development' not found`

**Solutions**:
1. Verify environment name matches workflow exactly
2. Check environment was created (Settings → Environments)
3. Ensure environment name is lowercase

### Permission Denied

**Symptoms**: `Error: Resource not accessible by integration`

**Solutions**:
1. Check workflow permissions (Settings → Actions → General)
2. Grant "Read and write permissions"
3. Verify GitHub token has required scopes

## Additional Secrets (By Application Type)

### Flask Applications
```
FLASK_SECRET_KEY - Application secret key
FLASK_ENV - Environment (development/production)
```

### Django Applications
```
DJANGO_SECRET_KEY - Secret key
DATABASE_URL - Database connection string
ALLOWED_HOSTS - Comma-separated hostnames
```

### API Applications
```
JWT_SECRET - JWT signing key
API_RATE_LIMIT - Rate limiting configuration
CORS_ORIGINS - Allowed CORS origins
```

### Applications with Cloud Services
```
GCP_SERVICE_ACCOUNT_KEY - Google Cloud service account JSON
AWS_S3_BUCKET - S3 bucket for file storage
REDIS_URL - Redis connection string
```

## Next Steps

Once GitHub is configured:
1. Review **04-TESTING-STANDARDS.md** for test requirements
2. Review **05-SECURITY-STANDARDS.md** for security scanning
3. Select and customize workflow template from `workflow-templates/`
4. Test deployment to development environment
5. After validation, enable production deployments

## Updating Secrets

To update existing secrets:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Find the secret name
3. Click **Update** (repository secrets) or navigate to environment (environment secrets)
4. Enter new value
5. Click **Update secret**

**Important**: Workflows using updated secrets will use new values on next run. No need to restart running workflows.

## Deleting Secrets

To remove secrets:
1. Navigate to secret location
2. Click **Remove** or **Delete**
3. Confirm deletion

**Warning**: Workflows depending on deleted secrets will fail. Update workflows before deleting secrets.
