# Workflow Customization Guide

## Overview

This guide explains how to customize the standard workflow templates for your specific application needs. While the templates provide a solid foundation, each application may require specific adjustments.

## Template Selection

### Template 1: Test-Only Workflow
**File**: `workflow-templates/python-test-only.yml`

**Use When**:
- Setting up CI for the first time
- Don't have AWS infrastructure yet
- Want to test pull requests only
- Need standalone quality checks

**Features**:
- Unit tests
- Security scanning
- Code linting
- No deployment

### Template 2: Full CI/CD with SSM
**File**: `workflow-templates/python-ci-cd-ssm.yml`

**Use When**:
- AWS infrastructure is ready
- Want automated deployments
- Have dev and production environments
- Need complete pipeline

**Features**:
- All testing and quality checks
- Environment-based deployment
- SSM integration
- Health checks

## Customization Points

### 1. Python Version

**Default**:
```yaml
env:
  PYTHON_VERSION: '3.14'
```

**Customize**:
```yaml
env:
  PYTHON_VERSION: '3.11'  # Match your application version
```

**Where to change**: Top of workflow file, `env` section

### 2. Trigger Events

**Default**:
```yaml
on:
  push:
    branches: [ dev, master ]
  pull_request:
    branches: [ dev, master ]
  workflow_dispatch:
```

**Customization Options**:

**Option A: Main branch only**:
```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

**Option B: Feature branches too**:
```yaml
on:
  push:
    branches:
      - dev
      - master
      - 'feature/**'  # All feature branches
```

**Option C: Specific paths only**:
```yaml
on:
  push:
    branches: [ dev, master ]
    paths:
      - 'src/**'        # Only when src/ changes
      - 'requirements.txt'
      - '.github/workflows/**'
```

**Option D: Scheduled runs**:
```yaml
on:
  push:
    branches: [ dev, master ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday at midnight
```

### 3. Test Configuration

**Default**:
```yaml
- name: Run Unit Tests
  run: |
    pytest test_app.py -v --tb=short \
      --cov=app --cov-report=term-missing --cov-report=xml
```

**Customization Options**:

**Option A: Custom test directory**:
```yaml
- name: Run Unit Tests
  run: |
    pytest tests/ -v --tb=short \
      --cov=myapp --cov-report=term-missing
```

**Option B: Multiple test types**:
```yaml
- name: Run Unit Tests
  run: pytest tests/unit/ -v

- name: Run Integration Tests
  run: pytest tests/integration/ -v
```

**Option C: Parallel execution**:
```yaml
- name: Run Unit Tests
  run: pytest tests/ -n auto --dist loadfile
```

**Option D: Different coverage threshold**:
```yaml
- name: Run Unit Tests
  run: |
    pytest tests/ --cov=app --cov-fail-under=80
  # Fails if coverage below 80%
```

### 4. Security Scanning

**Default**:
```yaml
- name: Security - Dependency Vulnerability Scan (pip-audit)
  run: pip-audit --desc --requirement requirements.txt
  continue-on-error: false  # BLOCKING
```

**Customization Options**:

**Option A: Ignore specific vulnerabilities**:
```yaml
- name: Security - Dependency Vulnerability Scan
  run: |
    pip-audit --desc --requirement requirements.txt \
      --ignore-vuln CVE-2023-XXXXX
```

**Option B: Custom requirements file**:
```yaml
- name: Security - Scan Production Dependencies
  run: pip-audit --desc --requirement requirements/prod.txt
```

**Option C: Additional security tools**:
```yaml
- name: Security - Trivy Scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
```

### 5. Linting Configuration

**Default**:
```yaml
- name: Lint with flake8
  run: |
    flake8 app.py --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 app.py --count --max-complexity=10 --max-line-length=127 --statistics --exit-zero
```

**Customization Options**:

**Option A: Scan entire src directory**:
```yaml
- name: Lint with flake8
  run: |
    flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 src/ --count --max-complexity=10 --max-line-length=127 --statistics --exit-zero
```

**Option B: Use configuration file**:
```yaml
# Create .flake8 file in repository root
[flake8]
max-line-length = 127
max-complexity = 10
exclude = .git,__pycache__,venv
ignore = E203,W503

# Workflow uses config automatically
- name: Lint with flake8
  run: flake8 src/
```

**Option C: Add type checking**:
```yaml
- name: Type Check with mypy
  run: mypy src/ --ignore-missing-imports
  continue-on-error: true  # Non-blocking initially
```

### 6. Branch Strategy

**Default**:
```yaml
deploy-dev:
  if: github.ref == 'refs/heads/dev'

deploy-prod:
  if: github.ref == 'refs/heads/master'
```

**Customization Options**:

**Option A: Main instead of master**:
```yaml
deploy-prod:
  if: github.ref == 'refs/heads/main'
```

**Option B: Staging environment**:
```yaml
deploy-dev:
  if: github.ref == 'refs/heads/dev'

deploy-staging:
  if: github.ref == 'refs/heads/staging'
  environment: staging

deploy-prod:
  if: github.ref == 'refs/heads/main'
```

**Option C: Manual approval for dev too**:
```yaml
deploy-dev:
  environment: development  # Add protection rules in GitHub
  if: github.ref == 'refs/heads/dev'
```

### 7. Application-Specific Scripts

**Add custom pre-deployment steps**:

```yaml
- name: Build Assets
  run: |
    npm install
    npm run build

- name: Run Database Migrations
  run: |
    aws ssm send-command \
      --instance-ids "${{ secrets.INSTANCE_ID }}" \
      --document-name "AWS-RunPowerShellScript" \
      --parameters 'commands=[
        "cd ${{ secrets.APP_PATH }}",
        "python manage.py migrate"
      ]'
```

**Add custom post-deployment steps**:

```yaml
- name: Warm Up Cache
  run: |
    curl -X POST https://${{ secrets.SERVER_HOST }}/api/cache/warmup

- name: Notify Team
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"Deployment to ${{ env.DEPLOY_ENV }} complete!"}'
```

## Advanced Customizations

### 1. Matrix Testing

Test against multiple Python versions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Run Tests
      run: pytest tests/
```

### 2. Conditional Deployments

Deploy only when specific files change:

```yaml
jobs:
  check-changes:
    runs-on: ubuntu-latest
    outputs:
      app-changed: ${{ steps.filter.outputs.app }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            app:
              - 'src/**'
              - 'requirements.txt'

  deploy:
    needs: check-changes
    if: needs.check-changes.outputs.app-changed == 'true'
    # ... deployment steps
```

### 3. Artifacts and Caching

Speed up workflows with caching:

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test-reports/
```

### 4. Multiple Deployment Targets

Deploy to multiple servers:

```yaml
deploy-prod:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      instance: ['i-prod-1', 'i-prod-2', 'i-prod-3']

  steps:
  - name: Deploy to instance
    run: |
      aws ssm send-command \
        --instance-ids ${{ matrix.instance }} \
        # ... deployment commands
```

### 5. Environment-Specific Tests

Run different tests for different environments:

```yaml
- name: Run Development Tests
  if: github.ref == 'refs/heads/dev'
  run: pytest tests/ --include-integration

- name: Run Production Tests
  if: github.ref == 'refs/heads/master'
  run: pytest tests/unit/ --strict
```

## Application-Specific Examples

### Flask Application

```yaml
# Add Flask-specific checks
- name: Check Flask Configuration
  run: |
    python -c "
    from app import create_app
    app = create_app('testing')
    assert app.config['TESTING'] == True
    "

- name: Test Flask Routes
  run: pytest tests/test_routes.py -v
```

### Django Application

```yaml
# Django-specific steps
- name: Run Django Checks
  run: python manage.py check

- name: Run Migrations Check
  run: python manage.py makemigrations --check --dry-run

- name: Collect Static Files
  run: python manage.py collectstatic --noinput

- name: Run Django Tests
  run: python manage.py test
```

### API Application

```yaml
# API-specific tests
- name: OpenAPI Schema Validation
  run: |
    pip install openapi-spec-validator
    openapi-spec-validator schema.yaml

- name: API Integration Tests
  run: pytest tests/api/ --api-tests

- name: Load Test (Optional)
  if: github.ref == 'refs/heads/master'
  run: |
    pip install locust
    locust -f tests/load_test.py --headless -u 100 -r 10 --run-time 1m
```

### Scheduled Tasks Application

```yaml
# For applications with cron jobs or scheduled tasks
- name: Test Scheduled Tasks
  run: pytest tests/test_tasks.py

- name: Deploy Task Scheduler
  run: |
    aws ssm send-command \
      --instance-ids "${{ secrets.INSTANCE_ID }}" \
      --parameters 'commands=[
        "schtasks /create /tn MyTask /tr \"${{ secrets.APP_PATH }}\\venv\\Scripts\\python.exe ${{ secrets.APP_PATH }}\\tasks.py\" /sc daily /st 02:00"
      ]'
```

## Custom Reusable Workflows

Create your own reusable workflow for organization-wide use:

**In `.github` repository**:

```yaml
# .github/workflows/custom-python-deploy.yml
name: Custom Python Deployment

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      python-version:
        required: false
        type: string
        default: '3.14'
    secrets:
      AWS_ACCESS_KEY_ID:
        required: true
      AWS_SECRET_ACCESS_KEY:
        required: true
      # ... other secrets

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}

    steps:
      # Custom deployment logic
```

**In application repository**:

```yaml
# Use custom reusable workflow
jobs:
  deploy:
    uses: your-org/.github/.github/workflows/custom-python-deploy.yml@main
    with:
      environment: production
      python-version: '3.11'
    secrets: inherit
```

## Customization Checklist

When adapting a template for your application:

- [ ] Update Python version to match your application
- [ ] Adjust branch names (dev, master, main)
- [ ] Configure test paths and coverage targets
- [ ] Set appropriate linting rules
- [ ] Add application-specific build steps
- [ ] Configure environment-specific secrets
- [ ] Set up health check endpoints
- [ ] Adjust deployment timeouts if needed
- [ ] Add monitoring/notification integrations
- [ ] Document customizations in README
- [ ] Test workflow with manual trigger
- [ ] Verify both dev and prod deployments

## Testing Workflow Changes

### Test locally with act

```bash
# Install act: https://github.com/nektos/act
brew install act  # macOS
# or download from GitHub releases

# Test workflow locally
act -j test-and-quality

# Test with specific event
act push -j deploy-dev
```

### Test in a branch

1. Create feature branch with workflow changes
2. Push to trigger workflow
3. Review workflow run results
4. Iterate until working
5. Merge to main branch

### Use manual triggers for testing

```yaml
on:
  workflow_dispatch:  # Enable manual trigger
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - development
          - production

jobs:
  deploy:
    environment: ${{ github.event.inputs.environment }}
```

## Best Practices

1. **Start with a template** - Don't build from scratch
2. **Customize incrementally** - Add one change at a time
3. **Test thoroughly** - Use manual triggers and dev environment
4. **Document changes** - Comment why customizations were made
5. **Keep it simple** - Avoid over-engineering
6. **Use reusable workflows** - Share common logic across projects
7. **Version control** - Track workflow changes like code
8. **Monitor performance** - Watch workflow execution times
9. **Regular updates** - Keep actions and tools up to date
10. **Security first** - Never commit secrets, use GitHub Secrets

## Common Customization Patterns

### Pattern 1: Multi-Stage Deployment

```yaml
jobs:
  test:
    # ... test steps

  deploy-canary:
    needs: test
    # Deploy to 10% of servers

  deploy-full:
    needs: deploy-canary
    # Deploy to remaining servers
```

### Pattern 2: Manual Approval Gates

```yaml
deploy-prod:
  environment:
    name: production
    # Configure required reviewers in GitHub UI
  needs: test
```

### Pattern 3: Rollback on Failure

```yaml
- name: Deploy New Version
  id: deploy
  run: # deployment commands

- name: Rollback on Failure
  if: failure() && steps.deploy.outcome == 'failure'
  run: # rollback commands
```

## Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Workflow Syntax**: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- **Reusable Workflows**: https://docs.github.com/en/actions/using-workflows/reusing-workflows
- **GitHub Actions Marketplace**: https://github.com/marketplace?type=actions

## Getting Help

For questions about customizing workflows:

1. Review this customization guide
2. Check template comments and documentation
3. Test changes in development environment
4. Consult with DevOps team
5. Review GitHub Actions documentation
6. Check organization's workflow examples

## Next Steps

- Select appropriate template from `workflow-templates/`
- Copy to `.github/workflows/` in your repository
- Customize based on this guide
- Test with manual trigger
- Deploy to development environment
- Monitor and refine as needed
