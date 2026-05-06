# Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered in the CI/CD pipeline, from GitHub Actions workflows to AWS SSM deployments.

## Quick Diagnostic Commands

### Check SSM Connectivity
```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=i-xxxxxxxxx"
```

### Check Recent SSM Commands
```bash
aws ssm list-commands \
  --instance-id i-xxxxxxxxx \
  --max-results 10
```

### Get Command Output
```bash
aws ssm get-command-invocation \
  --command-id COMMAND-ID \
  --instance-id i-xxxxxxxxx
```

### Check GitHub Actions Logs
Navigate to: **Repository → Actions → Select workflow run → View logs**

## GitHub Actions Issues

### Issue: Workflow Not Triggering

**Symptoms**:
- Push to branch but workflow doesn't run
- No workflow runs appear in Actions tab

**Possible Causes**:
1. Workflow file has syntax errors
2. Trigger conditions not met
3. Actions disabled for repository
4. Branch name doesn't match trigger

**Solutions**:

1. **Validate workflow syntax**:
   ```bash
   # Use GitHub Actions workflow validator
   # Or check YAML syntax locally
   yamllint .github/workflows/ci-cd.yml
   ```

2. **Check trigger configuration**:
   ```yaml
   on:
     push:
       branches: [ dev, master ]  # Ensure branch name matches
   ```

3. **Verify Actions are enabled**:
   - Go to **Settings → Actions → General**
   - Ensure "Allow all actions" or appropriate allowlist

4. **Check branch name**:
   ```bash
   git branch  # Verify exact branch name
   ```

### Issue: Workflow Fails at Checkout

**Symptoms**:
```
Error: fatal: could not read Username for 'https://github.com'
```

**Solutions**:

1. **Check workflow permissions**:
   - **Settings → Actions → General → Workflow permissions**
   - Set to "Read and write permissions"

2. **Use correct checkout action version**:
   ```yaml
   - uses: actions/checkout@v6  # Use latest version
   ```

### Issue: Secrets Not Available

**Symptoms**:
```
Error: Missing required secret AWS_ACCESS_KEY_ID
```

**Solutions**:

1. **Verify secret exists**:
   - **Settings → Secrets and variables → Actions**
   - Check exact name (case-sensitive)

2. **Check secret scope**:
   - Repository secret: Available to all workflows
   - Environment secret: Only available in that environment

3. **Verify environment name**:
   ```yaml
   environment: development  # Must match exactly (lowercase)
   ```

4. **For reusable workflows, ensure secrets inheritance**:
   ```yaml
   uses: DCCA-ISCO/<repo>/.github/workflows/<workflow-name>.yml@main
   secrets: inherit  # Required!
   ```

### Issue: Tests Fail in CI but Pass Locally

**Symptoms**:
- Tests pass on local machine
- Same tests fail in GitHub Actions

**Possible Causes**:
1. Environment variable differences
2. Different Python version
3. Missing dependencies
4. File path issues (Windows vs Linux)
5. Timezone differences

**Solutions**:

1. **Match Python version**:
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: '3.14'  # Match local version
   ```

2. **Add missing dependencies**:
   ```bash
   # Ensure all dev dependencies are in requirements-dev.txt
   pip freeze > requirements-dev.txt
   ```

3. **Use environment variables**:
   ```yaml
   env:
     TESTING: true
     TZ: UTC  # Set consistent timezone
   ```

4. **Check for hardcoded paths**:
   ```python
   # Bad
   file_path = "C:\\Users\\me\\project\\data.json"

   # Good
   import os
   file_path = os.path.join(os.path.dirname(__file__), "data.json")
   ```

### Issue: pip-audit Fails with Vulnerabilities

**Symptoms**:
```
Error: Found 2 known vulnerabilities in 1 package
```

**Solutions**:

1. **Update vulnerable package**:
   ```bash
   # Update to fixed version
   pip install --upgrade package-name

   # Update requirements.txt
   pip freeze > requirements.txt
   ```

2. **Check if vulnerability affects your usage**:
   - Review CVE details
   - Determine if the vulnerable code path is used

3. **Temporarily allow vulnerability** (not recommended):
   ```yaml
   - name: Security Scan
     run: pip-audit --desc --requirement requirements.txt
     continue-on-error: true  # Only for urgent deployments
   ```

4. **Use vulnerability ignore file** (when fix unavailable):
   ```bash
   # Create .pip-audit-ignore.json
   {
     "ignore": [
       {
         "id": "CVE-2023-XXXXX",
         "reason": "Not applicable - using older API version"
       }
     ]
   }
   ```

## AWS SSM Issues

### Issue: Instance Not Appearing in SSM

**Symptoms**:
```
Error: Instance i-xxxxxxxxx not found in SSM
```

**Possible Causes**:
1. SSM Agent not running
2. No IAM role attached to instance
3. Instance in private subnet without VPC endpoints
4. Security group blocking outbound HTTPS

**Solutions**:

1. **Check SSM Agent status** (on Windows server):
   ```powershell
   Get-Service AmazonSSMAgent
   ```

   If not running:
   ```powershell
   Start-Service AmazonSSMAgent
   Set-Service -Name AmazonSSMAgent -StartupType Automatic
   ```

2. **Verify IAM role attached**:
   ```bash
   aws ec2 describe-instances \
     --instance-ids i-xxxxxxxxx \
     --query "Reservations[0].Instances[0].IamInstanceProfile"
   ```

   If no role, attach one:
   - **EC2 Console → Instance → Actions → Security → Modify IAM role**
   - Select role with `AmazonSSMManagedInstanceCore` policy

3. **For private subnet, create VPC endpoints**:
   - `com.amazonaws.{region}.ssm`
   - `com.amazonaws.{region}.ssmmessages`
   - `com.amazonaws.{region}.ec2messages`

4. **Check security group outbound rules**:
   - Must allow HTTPS (443) outbound

### Issue: SSM Command Fails

**Symptoms**:
```
CommandStatus: Failed
```

**Solutions**:

1. **Get detailed error message**:
   ```bash
   aws ssm get-command-invocation \
     --command-id COMMAND-ID \
     --instance-id i-xxxxxxxxx \
     --query "StandardErrorContent" \
     --output text
   ```

2. **Check S3 logs** (if configured):
   ```bash
   aws s3 ls s3://your-ssm-logs-bucket/ssm-logs/development/
   aws s3 cp s3://your-ssm-logs-bucket/ssm-logs/development/COMMAND-ID/ . --recursive
   ```

3. **Common error fixes**:

   **Error: "git: command not found"**
   - Install Git on Windows server
   - Add Git to system PATH

   **Error: "python: command not found"**
   - Install Python on server
   - Add Python to system PATH
   - Use full path in commands

   **Error: "Access denied"**
   - Check file permissions
   - Ensure SSM Agent has necessary permissions
   - Verify application directory exists

### Issue: Permission Denied Errors

**Symptoms**:
```
Error: User: arn:aws:iam::xxx:user/github-actions is not authorized to perform: ssm:SendCommand
```

**Solutions**:

1. **Verify IAM user policy**:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "ssm:SendCommand",
       "ssm:GetCommandInvocation"
     ],
     "Resource": "*"
   }
   ```

2. **Check AWS credentials in GitHub Secrets**:
   - Verify `AWS_ACCESS_KEY_ID` is correct
   - Verify `AWS_SECRET_ACCESS_KEY` is correct
   - Verify credentials belong to correct IAM user

3. **Test credentials locally**:
   ```bash
   aws sts get-caller-identity
   # Should show the IAM user
   ```

### Issue: SSM Wait Timeout

**Symptoms**:
```
Error: Waiter CommandExecuted failed: Max attempts exceeded
```

**Possible Causes**:
1. Command taking longer than timeout (300s default)
2. Command hung or stuck
3. Server overloaded

**Solutions**:

1. **Increase timeout**:
   ```yaml
   aws ssm wait command-executed \
     --command-id "$COMMAND_ID" \
     --instance-id "$INSTANCE_ID" \
     --timeout 600  # Increase to 10 minutes
   ```

2. **Check command status manually**:
   ```bash
   aws ssm list-commands \
     --command-id COMMAND-ID \
     --query "Commands[0].Status"
   ```

3. **Cancel stuck command**:
   ```bash
   aws ssm cancel-command \
     --command-id COMMAND-ID \
     --instance-ids i-xxxxxxxxx
   ```

## Deployment Issues

### Issue: Application Won't Start After Deployment

**Symptoms**:
- SSM command succeeds
- Process starts but immediately exits
- Health check fails

**Solutions**:

1. **Check application logs** (on server):
   ```powershell
   cd C:\Apps\YourApp
   Get-Content logs\app.log -Tail 50
   ```

2. **Test application manually**:
   ```powershell
   cd C:\Apps\YourApp
   .\venv\Scripts\Activate.ps1
   python app.py
   # Watch for errors
   ```

3. **Common issues**:

   **Missing environment variables**:
   ```powershell
   # Check .env file exists
   Get-Content .env

   # Or set system environment variables
   [Environment]::SetEnvironmentVariable("VAR_NAME", "value", "Machine")
   ```

   **Port already in use**:
   ```powershell
   # Find process using port
   netstat -ano | findstr :443

   # Kill process
   Stop-Process -Id PID -Force
   ```

   **File permissions**:
   ```powershell
   # Grant full control to application directory
   icacls "C:\Apps\YourApp" /grant Users:F /T
   ```

### Issue: Git Pull Fails During Deployment

**Symptoms**:
```
Error: Your local changes would be overwritten by merge
```

**Solutions**:

1. **Use git reset --hard** (already in template):
   ```powershell
   git reset --hard origin/dev
   git pull origin dev
   ```

2. **If file is locked**:
   ```powershell
   # Stop application first
   Get-Process pythonw | Stop-Process -Force

   # Then pull
   git reset --hard origin/dev
   ```

3. **Check for uncommitted changes**:
   ```powershell
   git status
   # Should show "nothing to commit, working tree clean"
   ```

### Issue: Dependencies Won't Install

**Symptoms**:
```
Error: Could not find a version that satisfies the requirement
```

**Solutions**:

1. **Update pip**:
   ```powershell
   python -m pip install --upgrade pip
   ```

2. **Check requirements.txt format**:
   ```
   # Good
   flask==2.3.0
   requests>=2.28.0

   # Bad (remove comments in actual file)
   flask  # Missing version
   ```

3. **Install specific package manually**:
   ```powershell
   pip install problematic-package==version
   ```

4. **Clear pip cache**:
   ```powershell
   pip cache purge
   pip install -r requirements.txt
   ```

### Issue: Process Not Stopping

**Symptoms**:
- Old application process keeps running
- New deployment starts second instance
- Port conflict errors

**Solutions**:

1. **Verify process identification**:
   ```powershell
   Get-WmiObject Win32_Process -Filter "name = 'pythonw.exe'" |
     Where-Object { $_.CommandLine -like "*app.py*" }
   ```

2. **Force kill all Python processes**:
   ```powershell
   Get-Process pythonw | Stop-Process -Force
   ```

3. **Add longer wait time**:
   ```powershell
   Stop-Process -Id $proc.ProcessId -Force
   Start-Sleep -Seconds 10  # Increase from 3 to 10
   ```

### Issue: Health Check Always Fails

**Symptoms**:
```
Warning: Health check failed - Could not verify HTTP 200
```

**Possible Causes**:
1. Application not fully started
2. SSL certificate issues
3. Wrong URL/hostname
4. Application error

**Solutions**:

1. **Increase wait time**:
   ```yaml
   - name: Health Check
     run: |
       sleep 30  # Increase from 10 to 30 seconds
   ```

2. **Check URL is correct**:
   ```yaml
   echo "Checking: https://${{ secrets.SERVER_HOST }}"
   # Verify this URL is accessible
   ```

3. **Test curl command manually**:
   ```bash
   curl -k -v https://your-app-hostname
   # -v shows verbose output for debugging
   ```

4. **Implement proper health endpoint**:
   ```python
   @app.route('/health')
   def health():
       return {'status': 'healthy'}, 200
   ```

## Environment Issues

### Issue: Development Environment Works, Production Doesn't

**Possible Causes**:
1. Different environment variables
2. Different instance configuration
3. Different network settings
4. Missing production secrets

**Solutions**:

1. **Compare environment secrets**:
   - Check both environments have all required secrets
   - Verify values are appropriate for each environment

2. **Check instance configuration**:
   ```bash
   # Compare instance details
   aws ec2 describe-instances --instance-ids i-dev i-prod
   ```

3. **Verify security groups**:
   ```bash
   aws ec2 describe-security-groups --group-ids sg-xxxxxx
   ```

### Issue: GitHub Environment Not Found

**Symptoms**:
```
Error: Environment 'production' not found
```

**Solutions**:

1. **Create environment**:
   - **Settings → Environments → New environment**
   - Name must match exactly (case-sensitive)

2. **Check workflow environment reference**:
   ```yaml
   environment: production  # Must match exactly
   ```

## Performance Issues

### Issue: Deployment Takes Too Long

**Symptoms**:
- Deployment exceeds 5 minutes
- Workflow times out

**Solutions**:

1. **Optimize pip install**:
   ```yaml
   # Use pip cache in GitHub Actions
   - uses: actions/setup-python@v5
     with:
       python-version: '3.14'
       cache: 'pip'  # Enables caching
   ```

2. **Reduce command output**:
   ```powershell
   pip install -r requirements.txt --upgrade 2>&1 | Out-Null
   ```

3. **Increase timeout**:
   ```yaml
   aws ssm wait command-executed \
     --timeout 600  # 10 minutes
   ```

### Issue: Tests Run Slowly

**Symptoms**:
- Test suite takes > 5 minutes
- Workflow timeout

**Solutions**:

1. **Run tests in parallel**:
   ```yaml
   - name: Run Tests
     run: pytest -n auto  # Auto-detect CPU count
   ```

2. **Skip slow tests in CI**:
   ```python
   @pytest.mark.slow
   def test_large_dataset():
       pass
   ```

   ```yaml
   - name: Run Tests
     run: pytest -m "not slow"  # Skip slow tests
   ```

3. **Use test markers**:
   ```yaml
   - name: Fast Tests
     run: pytest -m unit

   - name: Slow Tests (on schedule)
     if: github.event_name == 'schedule'
     run: pytest -m integration
   ```

## Debugging Tips

### Enable Debug Logging

**GitHub Actions**:
```yaml
- name: Deploy with Debug
  env:
    ACTIONS_STEP_DEBUG: true
  run: |
    # Your deployment commands
```

**AWS CLI**:
```bash
aws ssm send-command --debug ...
```

**PowerShell**:
```powershell
$VerbosePreference = "Continue"
$DebugPreference = "Continue"
```

### Test SSM Commands Locally

```bash
# Test command syntax before using in workflow
aws ssm send-command \
  --instance-ids i-xxxxxxxxx \
  --document-name "AWS-RunPowerShellScript" \
  --parameters 'commands=["Write-Host Test","Get-Date"]'
```

### Verify Workflow Syntax

```bash
# Install act (local GitHub Actions runner)
# https://github.com/nektos/act

# Run workflow locally
act -j test-and-quality
```

## Getting Help

### Log Collection

When reporting issues, include:

1. **GitHub Actions logs**:
   - Full workflow run log
   - Specific failing step output

2. **SSM command output**:
   ```bash
   aws ssm get-command-invocation \
     --command-id COMMAND-ID \
     --instance-id i-xxxxxxxxx
   ```

3. **Application logs**:
   - Error messages from application
   - Server event logs

4. **Configuration**:
   - Workflow file (sanitized)
   - Environment setup
   - Instance configuration

### Escalation Path

1. **Check this troubleshooting guide**
2. **Review GitHub Actions logs**
3. **Check AWS SSM logs in S3**
4. **Test deployment manually**
5. **Contact DevOps team**
6. **Create incident ticket** (for production issues)

## Common Error Messages

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `Missing required secret` | Secret not configured | Add secret in GitHub Settings |
| `Instance not found in SSM` | SSM Agent not running | Start SSM Agent service |
| `Permission denied` | IAM permissions insufficient | Update IAM policy |
| `Command timeout` | Command taking too long | Increase timeout or optimize command |
| `Health check failed` | Application not responding | Check application logs, increase wait time |
| `Git pull failed` | Local changes conflict | Use `git reset --hard` |
| `Module not found` | Missing dependency | Install dependency in requirements.txt |
| `Port already in use` | Previous process still running | Kill existing process |
| `Connection refused` | Application not listening | Check application is running on correct port |
| `SSL certificate error` | Self-signed certificate | Use `-k` flag for curl in development |

## Prevention

### Best Practices to Avoid Issues

1. **Test in development first** - Always deploy to dev before production
2. **Use version pinning** - Pin dependency versions in requirements.txt
3. **Monitor deployments** - Watch logs during deployment
4. **Keep backups** - Ensure backup strategy is working
5. **Document changes** - Clear commit messages and release notes
6. **Gradual rollout** - Deploy to small percentage of users first (if applicable)
7. **Automated rollback** - Have rollback procedure ready
8. **Regular maintenance** - Update dependencies monthly
9. **Health checks** - Implement comprehensive health endpoints
10. **Alerting** - Set up alerts for deployment failures

## Further Resources

- AWS SSM Documentation: https://docs.aws.amazon.com/systems-manager/
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Python pip-audit: https://pypi.org/project/pip-audit/
- pytest Documentation: https://docs.pytest.org/
