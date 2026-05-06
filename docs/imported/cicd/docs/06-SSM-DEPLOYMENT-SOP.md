# SSM Deployment Standard Operating Procedure (SOP)

## Overview

This document provides standard operating procedures for deploying Python applications to AWS Windows Servers using AWS Systems Manager (SSM). These procedures ensure consistent, secure, and reliable deployments.

## Deployment Architecture

```
GitHub Actions Runner (Ubuntu)
    ↓ AWS CLI Command
AWS Systems Manager Service
    ↓ SSM Agent Communication
EC2 Windows Server (Target)
    ↓ PowerShell Script Execution
Application Deployment & Restart
```

## Deployment Process Overview

### Phase 1: Pre-Deployment (GitHub Actions)
1. Code checkout
2. Quality gates (tests, security, linting)
3. AWS credentials configuration
4. SSM connectivity verification

### Phase 2: Deployment (SSM Command)
1. Create backup of current version
2. Pull latest code from Git
3. Update Python dependencies
4. Verify deployment success

### Phase 3: Application Restart (SSM Command)
1. Stop existing application process
2. Start new application process
3. Verify process is running

### Phase 4: Post-Deployment (GitHub Actions)
1. Health check
2. Log deployment summary
3. Update deployment status

## Detailed Deployment Steps

### Step 1: Pre-Deployment Verification

**Automated Checks**:
```yaml
- name: Verify SSM Connectivity
  run: |
    aws ssm describe-instance-information \
      --filters "Key=InstanceIds,Values=${{ secrets.INSTANCE_ID }}" \
      --query "InstanceInformationList[0].[InstanceId,PingStatus,PlatformType]" \
      --output table
```

**Expected Output**:
```
|  i-xxxxxxxxx  |  Online  |  Windows  |
```

**Failure Conditions**:
- `PingStatus` is not "Online"
- Instance not found
- SSM Agent not responding

**Resolution**: See Troubleshooting section

### Step 2: Code Backup

**PowerShell Command**:
```powershell
# Remove old backup
if (Test-Path "backup_old") {
    Remove-Item -Path "backup_old" -Recurse -Force -ErrorAction SilentlyContinue
}

# Rotate backups
if (Test-Path "backup") {
    Rename-Item -Path "backup" -NewName "backup_old" -ErrorAction SilentlyContinue
}

# Create new backup
if (Test-Path "app.py") {
    New-Item -Path "backup" -ItemType Directory -Force | Out-Null
    Copy-Item -Path "*.py" -Destination "backup" -ErrorAction SilentlyContinue
    Copy-Item -Path "requirements.txt" -Destination "backup" -ErrorAction SilentlyContinue
}
```

**Backup Strategy**:
- **Current backup**: `backup/` - Most recent working version
- **Previous backup**: `backup_old/` - Version before current
- **Retention**: 2 versions (can be extended)

**Purpose**: Enable quick rollback if deployment fails

### Step 3: Code Synchronization

**Git Commands**:
```powershell
cd ${{ secrets.APP_PATH }}

# Fetch latest changes
git fetch origin

# Hard reset to branch
git reset --hard origin/${{ github.ref_name }}

# Pull latest code
git pull origin ${{ github.ref_name }}
```

**Why Hard Reset**:
- Ensures clean synchronization
- Removes any local modifications
- Prevents merge conflicts
- Guarantees deployed code matches repository

**Important**: Local changes on server are **LOST**. All changes must be committed to repository.

### Step 4: Dependency Update

**PowerShell Commands**:
```powershell
# Activate virtual environment
& "${{ secrets.APP_PATH }}\venv\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip 2>&1 | Out-Null

# Install/update dependencies
pip install -r requirements.txt --upgrade 2>&1

# Deactivate
deactivate
```

**Key Points**:
- Uses virtual environment (isolated dependencies)
- Upgrades pip first (ensures compatibility)
- `--upgrade` flag updates existing packages
- Errors are logged but don't fail immediately

**Dependency Management Best Practices**:
- Pin versions in `requirements.txt` (`package==1.2.3`)
- Test dependency updates in development first
- Use `requirements-dev.txt` for development tools

### Step 5: Application Restart

#### Stop Existing Process

**PowerShell Command**:
```powershell
# Find Python processes running the application
$processes = Get-WmiObject Win32_Process -Filter "name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -like "*${{ secrets.SCRIPT_NAME }}*" }

if ($processes) {
    foreach ($proc in $processes) {
        Write-Host "Stopping PID: $($proc.ProcessId)"
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
}
```

**Why pythonw.exe**:
- `pythonw.exe` runs Python without console window
- Suitable for background services
- Logs to file instead of console

**Process Identification**:
- Filters by executable name (`pythonw.exe`)
- Matches command line containing script name (`app.py`)
- Avoids stopping unrelated Python processes

#### Start New Process

**PowerShell Command**:
```powershell
cd ${{ secrets.APP_PATH }}

$pythonw = Join-Path "${{ secrets.APP_PATH }}" "venv\Scripts\pythonw.exe"
$script = Join-Path "${{ secrets.APP_PATH }}" "${{ secrets.SCRIPT_NAME }}"

Start-Process `
    -FilePath $pythonw `
    -ArgumentList $script `
    -WorkingDirectory "${{ secrets.APP_PATH }}" `
    -WindowStyle Hidden
```

**Process Startup Parameters**:
- **FilePath**: Path to `pythonw.exe` in virtual environment
- **ArgumentList**: Script to run (`app.py`)
- **WorkingDirectory**: Application directory (for relative paths)
- **WindowStyle**: Hidden (no visible window)

#### Verify Process Started

**PowerShell Command**:
```powershell
Start-Sleep -Seconds 5

$running = Get-Process pythonw -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*${{ secrets.APP_PATH }}*" }

if ($running) {
    Write-Host "Application started (PID: $($running.Id))"
} else {
    Write-Host "Warning: Could not verify process"
}
```

**Verification Checks**:
1. Wait 5 seconds for process to start
2. Find pythonw.exe process
3. Verify path matches application directory
4. Report PID if successful

### Step 6: Health Check

**HTTP Health Check**:
```yaml
- name: Health Check
  run: |
    sleep 10  # Allow application to fully initialize

    # Check HTTPS endpoint
    if curl -k -s -o /dev/null -w "%{http_code}" --max-time 30 \
        "https://${{ secrets.SERVER_HOST }}" | grep -q "200"; then
      echo "Health check passed (HTTP 200)"
    else
      echo "Health check warning: Could not verify HTTP 200"
    fi
```

**Parameters**:
- `-k`: Accept self-signed certificates (for development)
- `-s`: Silent mode (no progress bar)
- `-o /dev/null`: Discard response body
- `-w "%{http_code}"`: Print HTTP status code
- `--max-time 30`: 30-second timeout

**Expected Results**:
- HTTP 200 OK: Application healthy
- HTTP 503 Service Unavailable: Application starting
- Timeout: Application not responding

**Health Check Endpoints**:

Your application should implement a health check endpoint:

```python
# Example Flask health check
@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
```

### Step 7: Post-Deployment Verification

**Checklist**:
- [ ] SSM command completed successfully
- [ ] No errors in command output
- [ ] Application process running
- [ ] Health check returns 200 OK
- [ ] Logs show application started
- [ ] No error alerts triggered

**Deployment Logs**:
```yaml
- name: Get Deployment Output
  if: always()
  run: |
    aws ssm get-command-invocation \
      --command-id "${{ env.COMMAND_ID }}" \
      --instance-id "${{ secrets.INSTANCE_ID }}" \
      --query "[StandardOutputContent,StandardErrorContent]" \
      --output text
```

**Log Locations**:
- **GitHub Actions**: Workflow run logs
- **S3**: `s3://{SSM_OUTPUT_BUCKET}/ssm-logs/{environment}/`
- **CloudTrail**: API call logs
- **Application**: On-server log files

## Rollback Procedure

### Automated Rollback (If Available)

If deployment fails, manually trigger rollback:

1. **Restore from Backup**:
```powershell
# Connect to server via RDP or SSM Session Manager
cd C:\Apps\YourApp

# Stop current application
Get-Process pythonw | Where-Object { $_.Path -like "*YourApp*" } | Stop-Process -Force

# Restore from backup
Copy-Item -Path "backup\*" -Destination "." -Force

# Restart application
Start-Process -FilePath "venv\Scripts\pythonw.exe" -ArgumentList "app.py" -WindowStyle Hidden
```

2. **Git Rollback**:
```powershell
# Rollback to previous commit
git log --oneline -10  # View recent commits
git reset --hard <previous-commit-sha>

# Restart application (see above)
```

### Manual Rollback via GitHub Actions

Create rollback workflow:

```yaml
name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      commit_sha:
        description: 'Commit SHA to rollback to'
        required: true
      environment:
        description: 'Environment (development/production)'
        required: true
        type: choice
        options:
          - development
          - production

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}

    steps:
      - name: Rollback to Previous Version
        run: |
          aws ssm send-command \
            --instance-ids "${{ secrets.INSTANCE_ID }}" \
            --document-name "AWS-RunPowerShellScript" \
            --parameters "commands=[
              'cd ${{ secrets.APP_PATH }}',
              'git fetch origin',
              'git reset --hard ${{ inputs.commit_sha }}',
              'Write-Host Rolled back to ${{ inputs.commit_sha }}'
            ]"
```

## Deployment Environments

### Development Environment

**Characteristics**:
- Deploys from `dev` branch
- Automatic deployment on push
- Minimal approval requirements
- Lenient error handling
- Self-signed certificates acceptable

**Configuration**:
```yaml
environment: development
if: github.ref == 'refs/heads/dev'
```

### Production Environment

**Characteristics**:
- Deploys from `master` branch
- Manual approval required
- Strict error handling
- Valid SSL certificates required
- Monitored deployments

**Configuration**:
```yaml
environment: production
if: github.ref == 'refs/heads/master'
```

**Protection Rules**:
- 1-2 required approvers
- Optional wait timer (5-10 minutes)
- Branch restriction to `master` only

## Deployment Frequency

### Recommended Schedule

**Development**:
- **Frequency**: Multiple times per day
- **Trigger**: Automatic on push
- **Purpose**: Rapid iteration and testing

**Production**:
- **Frequency**: 1-2 times per week
- **Trigger**: Manual after approval
- **Purpose**: Stable releases

### Emergency Deployments

For critical bugs or security issues:

1. Create hotfix branch
2. Implement fix and test
3. Merge to `master`
4. Manual workflow trigger
5. Expedited approval process
6. Monitor closely post-deployment

## Deployment Windows

### Recommended Timing

**Production Deployments**:
- **Weekdays**: Tuesday-Thursday, 10 AM - 2 PM local time
- **Avoid**: Mondays (start of week issues), Fridays (weekend coverage)
- **Avoid**: After 5 PM (limited support staff)
- **Avoid**: Weekends and holidays

**Why These Times**:
- Staff available for monitoring
- Time to resolve issues before end of day
- Users are typically active (immediate feedback)

### Emergency Deployment Windows

Critical fixes can deploy anytime, but ensure:
- On-call engineer available
- Backup engineer on standby
- Rollback plan ready
- Stakeholders notified

## Monitoring Post-Deployment

### First 15 Minutes
- Watch application logs for errors
- Monitor health check endpoint
- Check CPU/memory usage
- Verify key features functional

### First Hour
- Monitor error rates
- Check application metrics
- Review user feedback
- Watch for alerts

### First 24 Hours
- Daily metrics comparison
- Performance benchmarks
- User-reported issues
- Log aggregation review

### Metrics to Monitor

**Application Metrics**:
- Response time (p50, p95, p99)
- Error rate
- Request throughput
- Active connections

**Infrastructure Metrics**:
- CPU utilization
- Memory usage
- Disk I/O
- Network traffic

**Business Metrics**:
- User activity
- Transaction completion rate
- Feature usage
- Error reports

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing in CI
- [ ] Code reviewed and approved
- [ ] Security scans clean
- [ ] Documentation updated
- [ ] Deployment plan reviewed
- [ ] Rollback plan prepared
- [ ] Stakeholders notified
- [ ] Deployment window scheduled

### During Deployment
- [ ] Monitor GitHub Actions workflow
- [ ] Review SSM command output
- [ ] Verify process restart
- [ ] Check health endpoint
- [ ] Review initial logs

### Post-Deployment
- [ ] Health check passing
- [ ] Key features verified
- [ ] Metrics baseline established
- [ ] Logs monitored (15 min)
- [ ] Team notified of completion
- [ ] Documentation updated
- [ ] Deployment logged

## Common Deployment Scenarios

### Scenario 1: Routine Feature Deployment

1. Merge feature branch to `dev`
2. Automatic deployment to development
3. Test in development environment
4. Create PR from `dev` to `master`
5. Code review and approval
6. Merge to `master`
7. Manual trigger production deployment
8. Approve deployment
9. Monitor post-deployment

### Scenario 2: Hotfix Deployment

1. Create hotfix branch from `master`
2. Implement fix
3. Test locally
4. Merge to `master` (expedited review)
5. Trigger production deployment immediately
6. Monitor closely
7. Cherry-pick to `dev` if needed

### Scenario 3: Dependency Update

1. Update dependencies in `dev` branch
2. Run full test suite
3. Deploy to development
4. Monitor for issues (24-48 hours)
5. Merge to `master` if stable
6. Deploy to production during normal window

### Scenario 4: Failed Deployment

1. Deployment fails (tests or SSM error)
2. Review error logs
3. Fix issue locally
4. Push fix
5. Re-trigger deployment
6. If critical, consider rollback

## Deployment Metrics

Track these metrics to improve deployment process:

- **Deployment frequency**: How often we deploy
- **Lead time**: Time from commit to production
- **Mean time to recovery (MTTR)**: Time to fix failed deployment
- **Change failure rate**: Percentage of deployments causing issues
- **Deployment duration**: Time for full deployment process

**Goals**:
- Increase deployment frequency
- Decrease lead time
- Minimize change failure rate
- Fast MTTR (< 1 hour)

## Best Practices

1. **Small, frequent deployments**: Easier to troubleshoot
2. **Always deploy to dev first**: Catch issues early
3. **Monitor deployments**: Don't deploy and forget
4. **Document changes**: Clear release notes
5. **Have rollback ready**: Plan for failure
6. **Communicate**: Keep stakeholders informed
7. **Automate everything**: Reduce human error
8. **Test thoroughly**: Quality gates prevent issues
9. **Learn from failures**: Post-mortem analysis
10. **Keep backups**: Multiple restore points

## Deployment Communication

### Notification Template

**Pre-Deployment**:
```
Subject: Scheduled Production Deployment - [Date/Time]

Deployment Details:
- Environment: Production
- Scheduled Time: [Date] at [Time]
- Duration: ~15 minutes
- Changes: [Brief description or release notes link]
- Impact: No expected downtime

Deployed by: [Name]
Approval: [Approver names]
```

**Post-Deployment**:
```
Subject: Production Deployment Complete - [Application]

Deployment Status: Successful ✓

- Deployed: [Commit SHA]
- Completed: [Timestamp]
- Health Check: Passing
- Monitoring: Active

Issues: None reported
Next Steps: Monitoring for 24 hours
```

## Next Steps

- Review **07-TROUBLESHOOTING.md** for common deployment issues
- Review **08-WORKFLOW-CUSTOMIZATION.md** for adapting workflows
- Set up deployment monitoring and alerts
- Schedule regular deployment practice runs
