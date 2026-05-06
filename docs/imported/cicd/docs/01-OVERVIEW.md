# CI/CD Pipeline Overview

## Purpose

This documentation provides a standardized, reusable CI/CD pipeline for deploying Python applications to AWS Windows Servers using **AWS Systems Manager (SSM)**. The pipeline enforces quality gates through automated testing, security scanning, and linting before deploying code to target environments.

## Key Benefits

### Security
- **Password-less Deployment**: No SSH/RDP credentials required
- **IAM Role-Based Authentication**: Leverages AWS IAM for secure access
- **Automated Security Scanning**: CVE detection, dependency auditing, and code analysis
- **Audit Trail**: All deployments logged via AWS CloudTrail and S3

### Reliability
- **Quality Gates**: Tests must pass before deployment proceeds
- **Automated Backups**: Previous version backed up before each deployment
- **Health Checks**: Post-deployment verification
- **Process Management**: Graceful application restart

### Efficiency
- **Branch-Based Deployment**: Automatic environment routing (dev/production)
- **Reusable Workflows**: Centralized deployment logic
- **Parallel Testing**: Multiple security/quality checks run concurrently
- **GitHub Environments**: Environment-specific configuration and protection rules

## Architecture

### High-Level Flow

```
Developer Push
    ↓
GitHub Actions (Ubuntu Runner)
    ↓
Quality Gates (Tests, Security, Linting)
    ↓
AWS SSM Send-Command
    ↓
EC2 Windows Server (SSM Agent)
    ↓
PowerShell Script Execution
    ↓
Application Deployment & Restart
```

### Pipeline Stages

#### Stage 1: Quality Assurance (GitHub-Hosted Runner)
- **Unit Tests**: pytest with coverage reporting
- **Security Scanning**:
  - pip-audit (CVE detection - blocking)
  - safety (dependency vulnerabilities - non-blocking)
  - bandit (static security analysis - non-blocking)
- **Code Quality**:
  - flake8 (PEP8 compliance, syntax errors - blocking)
  - pylint (code quality analysis - non-blocking)
- **Smoke Tests**: Application import validation
- **Environment Validation**: Required variables check
- **Dependency Verification**: Conflict detection

#### Stage 2: Deployment (SSM via Ubuntu Runner)
- **Connectivity Verification**: Confirm SSM agent status
- **Code Update**: Git-based synchronization
- **Dependency Installation**: pip install in virtual environment
- **Application Restart**: Process stop/start with verification
- **Health Check**: HTTP endpoint validation
- **Logging**: All output captured to S3

## Workflow Types

### 1. Test-Only Workflow
**Purpose**: Run quality checks without deployment

**Use Cases**:
- Pull request validation
- Development branch testing
- Pre-deployment verification
- Manual quality checks

**Triggers**:
- Push to specified branches
- Pull requests
- Manual dispatch

### 2. Full CI/CD Workflow
**Purpose**: Complete testing and deployment pipeline

**Use Cases**:
- Production deployments
- Automated dev environment updates
- Continuous delivery

**Triggers**:
- Push to dev/master branches
- Manual dispatch

**Features**:
- All test-only workflow checks
- Environment-based deployment
- Automated rollout to AWS servers
- Health verification

### 3. Reusable Deployment Workflow
**Purpose**: Centralized SSM deployment logic

**Use Cases**:
- Called by other workflows
- Shared across multiple projects
- Consistent deployment procedures

**Features**:
- Parameterized inputs (branch, environment)
- Secrets inheritance
- Standard deployment steps
- Comprehensive logging

## Branch Strategy

### Development Branch (`dev`)
- **Target Environment**: development
- **Purpose**: Feature development and testing
- **Protection**: Optional approvals, automated deployment
- **Server**: Development EC2 instance

### Production Branch (`master`)
- **Target Environment**: production
- **Purpose**: Stable releases
- **Protection**: Required approvals, manual deployment trigger recommended
- **Server**: Production EC2 instance

## Environment Configuration

### GitHub Environments
Each environment (development, production) contains:
- **Protection Rules**: Approval requirements, wait timers
- **Secrets**: Environment-specific EC2 instance IDs, hostnames
- **Deployment URL**: Optional health check endpoint

### Repository Secrets
Global secrets shared across environments:
- AWS credentials (access key, secret key, region)
- Application paths and configuration
- S3 bucket names for logging

## Technology Stack

### GitHub Actions Components
- **Runners**: ubuntu-latest (GitHub-hosted)
- **Actions**:
  - `actions/checkout@v6`: Code checkout
  - `actions/setup-python@v5`: Python environment setup
  - `aws-actions/configure-aws-credentials@v5`: AWS authentication
  - `codecov/codecov-action@v4`: Coverage reporting (optional)

### AWS Components
- **Systems Manager (SSM)**: Command execution service
- **EC2**: Windows Server instances with SSM Agent
- **IAM**: Role-based access control
- **S3**: Command output logging
- **CloudTrail**: Audit logging

### Python Ecosystem
- **Testing**: pytest, pytest-cov
- **Security**: pip-audit, safety, bandit
- **Linting**: flake8, pylint
- **Runtime**: Python 3.14+ (configurable)

## Deployment Process

### Pre-Deployment
1. Tests execute on GitHub-hosted runner
2. All quality gates must pass (blocking checks)
3. Branch determines target environment
4. GitHub Environment approval (if configured)

### Deployment Steps
1. **Backup Creation**: Previous version archived with timestamp
2. **Code Synchronization**: `git reset --hard` + `git pull`
3. **Dependency Update**: `pip install -r requirements.txt --upgrade`
4. **Process Management**:
   - Stop existing application processes
   - Start new process in background mode (`pythonw.exe`)
5. **Verification**:
   - Process confirmation
   - HTTP health check (optional)
6. **Logging**: All outputs saved to S3

### Post-Deployment
- Deployment summary displayed in GitHub Actions log
- Application accessible at configured URL
- SSM command outputs available in S3
- CloudTrail events recorded

## Security Considerations

### Credentials Management
- **Never commit credentials**: Use GitHub Secrets exclusively
- **Rotate keys regularly**: Update AWS access keys quarterly
- **Principle of least privilege**: IAM users limited to SSM commands only
- **Environment isolation**: Separate secrets for dev/production

### Network Security
- **No open ports required**: SSM works without SSH/RDP exposure
- **VPC Endpoints**: SSM can function in private subnets
- **SSL/TLS**: Applications should use HTTPS in production
- **Security groups**: Minimize inbound rules

### Code Security
- **Dependency scanning**: Automated CVE detection
- **Static analysis**: Code review for security issues
- **Secret detection**: Avoid committing sensitive files (.env, credentials)
- **Audit trail**: All deployments tracked and logged

## Compliance & Auditing

### Deployment Tracking
- **GitHub Actions Logs**: Complete execution history with timestamps
- **S3 Logs**: SSM command outputs retained
- **CloudTrail Events**: API calls recorded
- **Git History**: Code changes tracked via commits

### Required Information Captured
- Who deployed (GitHub actor)
- What was deployed (commit SHA, branch)
- When deployment occurred (timestamp)
- Where it was deployed (instance ID, environment)
- Deployment outcome (success/failure, error messages)

## Extensibility

### Customization Points
- **Test suites**: Add/modify pytest tests
- **Security tools**: Configure additional scanners
- **Deployment steps**: Extend SSM PowerShell scripts
- **Health checks**: Custom endpoint validation
- **Notifications**: Slack/email integration (future)

### Multi-Language Support
While optimized for Python, the SSM deployment pattern can be adapted for:
- Node.js applications
- .NET applications
- Java applications
- Any Windows-hosted service

## Getting Started

To implement this pipeline in a new project:

1. **Review** `02-AWS-INFRASTRUCTURE-SETUP.md` for server preparation
2. **Configure** GitHub secrets per `03-GITHUB-CONFIGURATION.md`
3. **Select** appropriate workflow template from `workflow-templates/`
4. **Customize** tests and deployment steps as needed
5. **Test** using manual dispatch before enabling automatic triggers

## Documentation Structure

| Document | Purpose |
|----------|---------|
| `01-OVERVIEW.md` | This document - high-level pipeline overview |
| `02-AWS-INFRASTRUCTURE-SETUP.md` | AWS IAM, EC2, SSM configuration |
| `03-GITHUB-CONFIGURATION.md` | Secrets and environment setup |
| `04-TESTING-STANDARDS.md` | Testing requirements and best practices |
| `05-SECURITY-STANDARDS.md` | Security scanning standards and SOPs |
| `06-SSM-DEPLOYMENT-SOP.md` | Standard operating procedures for deployments |
| `07-TROUBLESHOOTING.md` | Common issues and resolutions |
| `08-WORKFLOW-CUSTOMIZATION.md` | How to adapt templates for your needs |

## Support

For issues with:
- **GitHub Actions workflows**: Check repository Actions tab logs
- **AWS SSM connectivity**: Review SSM agent status and IAM permissions
- **Deployment failures**: Check S3 logs for SSM command output
- **Application errors**: Review application logs on target server

## Version History

**v1.0** - Initial standardized pipeline
- Python 3.14 support
- Ubuntu-latest runners
- SSM-based Windows deployment
- Comprehensive testing and security scanning
