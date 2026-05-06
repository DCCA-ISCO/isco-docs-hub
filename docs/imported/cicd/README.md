# CI/CD Pipeline Documentation & Templates

This repository contains standardized CI/CD pipeline documentation, workflow templates, and best practices for Python applications deploying to AWS Windows Servers using Systems Manager (SSM).

## Quick Start

**New to this pipeline?** Start here:

1. Read **[docs/01-OVERVIEW.md](docs/01-OVERVIEW.md)** - Understand the pipeline architecture
2. Read **[docs/00-RESPONSIBILITIES-BREAKDOWN.md](docs/00-RESPONSIBILITIES-BREAKDOWN.md)** - Know what you are responsible for
3. Follow **[docs/02-AWS-INFRASTRUCTURE-SETUP.md](docs/02-AWS-INFRASTRUCTURE-SETUP.md)** - Set up AWS resources
4. Configure **[docs/03-GITHUB-CONFIGURATION.md](docs/03-GITHUB-CONFIGURATION.md)** - Set up secrets and environments
5. Select a workflow template from **[workflow-templates/](https://github.com/DCCA-ISCO/.github/tree/main/workflow-templates/)**
6. Customize using **[docs/08-WORKFLOW-CUSTOMIZATION.md](docs/08-WORKFLOW-CUSTOMIZATION.md)**

## Documentation Structure

### Core Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [00-RESPONSIBILITIES-BREAKDOWN.md](docs/00-RESPONSIBILITIES-BREAKDOWN.md) | What is expected of members | Everyone |
| [01-OVERVIEW.md](docs/01-OVERVIEW.md) | High-level pipeline architecture and benefits | Everyone |
| [02-AWS-INFRASTRUCTURE-SETUP.md](docs/02-AWS-INFRASTRUCTURE-SETUP.md) | AWS IAM, EC2, SSM setup guide | DevOps, Infrastructure |
| [03-GITHUB-CONFIGURATION.md](docs/03-GITHUB-CONFIGURATION.md) | GitHub secrets and environments setup | DevOps, Developers |
| [04-TESTING-STANDARDS.md](docs/04-TESTING-STANDARDS.md) | Testing requirements and best practices | Developers, QA |
| [05-SECURITY-STANDARDS.md](docs/05-SECURITY-STANDARDS.md) | Security scanning standards and SOPs | Security, Developers |
| [06-SSM-DEPLOYMENT-SOP.md](docs/06-SSM-DEPLOYMENT-SOP.md) | Deployment procedures and operations | DevOps, Operations |
| [07-TROUBLESHOOTING.md](docs/07-TROUBLESHOOTING.md) | Common issues and solutions | Everyone |
| [08-WORKFLOW-CUSTOMIZATION.md](docs/08-WORKFLOW-CUSTOMIZATION.md) | How to adapt workflow templates | Developers, DevOps |

### Workflow Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| [python-test-only.yml](https://github.com/DCCA-ISCO/.github/tree/main/workflow-templates/python-test-only.yml) | Testing and quality checks only, no deployment | Pull request validation, CI-only |
| [python-ci-cd-ssm.yml](https://github.com/DCCA-ISCO/.github/tree/main/workflow-templates/python-ci-cd-ssm.yml) | Complete CI/CD with SSM deployment | Full pipeline with automated deployment |

### Reusable Workflows

| Workflow | Description | Usage |
|----------|-------------|-------|
| [ssm-deploy-reusable.yml](https://github.com/DCCA-ISCO/.github/blob/main/workflows/ssm-deploy-reusable.yml) | Centralized SSM deployment logic | Called by other workflows |

## Pipeline Features

### Quality Gates
- **Unit Testing**: pytest with coverage reporting
- **Security Scanning**: pip-audit, safety, bandit
- **Code Quality**: flake8, pylint
- **Smoke Tests**: Application import validation
- **Dependency Verification**: Conflict detection

### Deployment
- **Password-less**: SSM-based deployment (no SSH/RDP)
- **Multi-Environment**: Development and production support
- **Automated Backups**: Pre-deployment backup creation
- **Health Checks**: Post-deployment verification
- **Comprehensive Logging**: S3 and CloudTrail integration

### Security
- **CVE Detection**: Automated vulnerability scanning
- **IAM Role-Based**: No credentials in code
- **Audit Trail**: Complete deployment tracking
- **Environment Isolation**: Separate dev/prod configurations

## Implementation Checklist

### Phase 1: AWS Setup (One-Time)
- [ ] Create IAM role for EC2 instances
- [ ] Attach role to target servers
- [ ] Verify SSM Agent running
- [ ] Create IAM user for GitHub Actions
- [ ] Create S3 bucket for SSM logs
- [ ] Set up application directory on servers

### Phase 2: GitHub Configuration
- [ ] Create GitHub Environments (development, production)
- [ ] Add repository secrets (AWS credentials, paths)
- [ ] Add environment secrets (instance IDs, hostnames)
- [ ] Configure branch protection rules
- [ ] Set environment approval requirements

### Phase 3: Workflow Setup
- [ ] Select appropriate workflow template
- [ ] Copy to `.github/workflows/` in your repository
- [ ] Customize for your application
- [ ] Test with manual trigger
- [ ] Verify development deployment
- [ ] Enable production deployment after validation

## Repository Structure

```
.github/
├── README.md                              # This file
│
├── docs/                                  # Documentation
│   ├── 01-OVERVIEW.md
│   ├── 02-AWS-INFRASTRUCTURE-SETUP.md
│   ├── 03-GITHUB-CONFIGURATION.md
│   ├── 04-TESTING-STANDARDS.md
│   ├── 05-SECURITY-STANDARDS.md
│   ├── 06-SSM-DEPLOYMENT-SOP.md
│   ├── 07-TROUBLESHOOTING.md
│   └── 08-WORKFLOW-CUSTOMIZATION.md
│
├── workflow-templates/                    # Starter templates
│   ├── python-test-only.yml
│   ├── python-test-only.properties.json
│   ├── python-ci-cd-ssm.yml
│   └── python-ci-cd-ssm.properties.json
│
└── workflows/                             # Reusable workflows
    └── ssm-deploy-reusable.yml
```

## Usage Examples

### Example 1: Test-Only Workflow

Copy `workflow-templates/python-test-only.yml` to your repository for CI without deployment:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
# ... (use template content)
```

### Example 2: Full CI/CD Pipeline

Copy `workflow-templates/python-ci-cd-ssm.yml` for complete pipeline:

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD
on:
  push:
    branches: [ dev, master ]
# ... (use template content)
```

### Example 3: Using Reusable Workflow

Reference the centralized deployment logic:

```yaml
# In your repository's workflow file
jobs:
  test:
    # ... your test steps

  deploy:
    needs: test
    uses: YOUR-ORG/.github/.github/workflows/ssm-deploy-reusable.yml@main
    with:
      branch-name: dev
      server-env: development
    secrets: inherit
```

## Key Technologies

- **CI/CD**: GitHub Actions
- **Cloud**: AWS (EC2, SSM, IAM, S3, CloudTrail)
- **Language**: Python 3.14+
- **Testing**: pytest, pytest-cov
- **Security**: pip-audit, safety, bandit
- **Linting**: flake8, pylint
- **Deployment**: AWS Systems Manager (SSM)

## Best Practices

### Testing
- Maintain 70%+ code coverage
- Run tests on every push and pull request
- Fix failing tests before merging
- Use meaningful test names

### Security
- Never commit secrets or credentials
- Rotate AWS keys quarterly
- Update dependencies monthly
- Fix critical vulnerabilities within 24 hours

### Deployment
- Always deploy to dev first
- Monitor deployments for 15 minutes
- Have rollback plan ready
- Deploy during business hours (production)

### Documentation
- Update docs when changing workflows
- Document customizations
- Keep README current
- Share knowledge with team

## Support & Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| SSM connectivity fails | Check IAM role and SSM Agent | [02-AWS-INFRASTRUCTURE-SETUP.md](docs/02-AWS-INFRASTRUCTURE-SETUP.md#step-3-verify-ssm-agent-installation) |
| Secrets not found | Verify secret names and scope | [03-GITHUB-CONFIGURATION.md](docs/03-GITHUB-CONFIGURATION.md#step-4-secrets-verification-checklist) |
| Tests fail in CI | Check environment differences | [07-TROUBLESHOOTING.md](docs/07-TROUBLESHOOTING.md#issue-tests-fail-in-ci-but-pass-locally) |
| Deployment timeout | Increase timeout or optimize | [07-TROUBLESHOOTING.md](docs/07-TROUBLESHOOTING.md#issue-ssm-wait-timeout) |

### Getting Help

1. **Check documentation** - Start with [07-TROUBLESHOOTING.md](docs/07-TROUBLESHOOTING.md)
2. **Review logs** - GitHub Actions and S3 SSM logs
3. **Test manually** - Use workflow_dispatch trigger
4. **Contact DevOps** - For infrastructure issues
5. **Create issue** - For bugs or feature requests

## Maintenance

### Regular Tasks

**Weekly**:
- Review failed deployments
- Check security scan results
- Monitor pipeline performance

**Monthly**:
- Update Python dependencies
- Review and update documentation
- Audit AWS permissions
- Check disk space on servers

**Quarterly**:
- Rotate AWS access keys
- Review and update standards
- Pipeline performance review
- Security audit

## Contributing

### Improving Documentation

1. Identify gaps or outdated information
2. Create branch with updates
3. Submit pull request
4. Request review from DevOps team

### Adding New Templates

1. Create template in `workflow-templates/`
2. Add `.properties.json` metadata file
3. Document usage in this README
4. Test template in sample project
5. Submit pull request

## Version History

**v1.0** (Current)
- Initial standardized documentation
- Python 3.14 support
- SSM-based Windows deployment
- Test-only and full CI/CD templates
- Reusable deployment workflow
- Comprehensive security scanning

## License

Internal use only. Not licensed for external distribution.

## Contact

For questions or support:
- DevOps Team: [Peter Faso - Solutions Architect]
- Documentation Issues: [Issue Tracker]
- Security Concerns: [Security Team Contact]

---

**Last Updated**: 2025-12-11
**Maintained By**: DevOps Team
**Documentation Version**: 1.0
