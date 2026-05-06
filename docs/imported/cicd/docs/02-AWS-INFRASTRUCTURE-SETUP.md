# AWS Infrastructure Setup Guide

## Overview

This guide provides step-by-step instructions for configuring AWS infrastructure to support SSM-based deployments. This is a **one-time setup** per environment (development, production).

## Prerequisites

- AWS account with administrative access
- AWS CLI installed and configured locally (for testing)
- Target application EC2 Windows Server instance(s)
- Basic understanding of IAM roles and policies

## Architecture Components

```
GitHub Actions
    ↓ (AWS API calls)
IAM User (with ssm:SendCommand permissions)
    ↓
AWS Systems Manager (SSM)
    ↓
EC2 Instance (with IAM Role)
    ↓
SSM Agent (running on Windows)
    ↓
PowerShell Script Execution
```

## Step 1: Create IAM Role for EC2 Instances

### 1.1 Create the Role

1. Navigate to **IAM Console** → **Roles** → **Create role**
2. Select **AWS service** as trusted entity type
3. Choose **EC2** as the use case
4. Click **Next**

### 1.2 Attach Managed Policy

Attach the following AWS managed policy:
- **`AmazonSSMManagedInstanceCore`**

This policy provides:
- SSM agent registration
- Command execution permissions
- S3 access for logs (if using output to S3.  - Possibly set up in central logging, *Audit OU*)
- CloudWatch integration

### 1.3 Name the Role

**Suggested Naming Convention**:
```
{AppName}-SSM-Role
```

**Examples**:
- `WebApp-SSM-Role`
- `APIService-SSM-Role`
- `ChatbotApp-SSM-Role`

### 1.4 Add Optional Policies

Depending on your application needs:
- **CloudWatch Logs**: `CloudWatchAgentServerPolicy`
- **S3 Access**: Custom policy for application-specific buckets
- **Secrets Manager**: `SecretsManagerReadWrite` (if app uses secrets)

### 1.5 Review Trust Relationship

Ensure the trust policy allows EC2:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Step 2: Attach IAM Role to EC2 Instance

### 2.1 For Existing Instances

1. Navigate to **EC2 Console** → **Instances**
2. Select your target instance
3. Click **Actions** → **Security** → **Modify IAM role**
4. Select the role created in Step 1
5. Click **Update IAM role**

### 2.2 For New Instances

When launching a new instance:
1. In the **Configure Instance Details** step
2. Under **IAM role**, select the role created in Step 1

### 2.3 Verify Attachment

```bash
# From AWS CLI
aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxx \
  --query "Reservations[0].Instances[0].IamInstanceProfile"
```

## Step 3: Verify SSM Agent Installation

### 3.1 Check SSM Agent Status (on Windows Server)

```powershell
# Open PowerShell as Administrator
Get-Service AmazonSSMAgent
```

**Expected Output**:
```
Status   Name               DisplayName
------   ----               -----------
Running  AmazonSSMAgent     Amazon SSM Agent
```

### 3.2 If SSM Agent is Not Running

```powershell
# Start the service
Start-Service AmazonSSMAgent

# Set to start automatically
Set-Service -Name AmazonSSMAgent -StartupType Automatic
```

### 3.3 If SSM Agent is Not Installed

Download and install from AWS:

1. Download the installer:
   ```
   https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe
   ```

2. Run the installer as Administrator

3. Verify installation:
   ```powershell
   Get-Service AmazonSSMAgent
   ```

### 3.4 Verify SSM Connectivity (from AWS CLI)

```bash
# Check if instance appears in SSM
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=i-xxxxxxxxx"
```

**Expected Fields**:
- `PingStatus`: "Online"
- `PlatformType`: "Windows"
- `IsLatestVersion`: true (SSM Agent version)

## Step 4: Create IAM User for GitHub Actions

### 4.1 Create the User

1. Navigate to **IAM Console** → **Users** → **Add users**
2. **User name**: `github-actions-deployer` (or similar)
3. **Access type**: Select **Access key - Programmatic access**
4. Click **Next**

### 4.2 Create Custom Policy

Create an inline policy with **minimum required permissions**:

**Policy Name**: `SSM-SendCommand-Policy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SSMSendCommand",
      "Effect": "Allow",
      "Action": [
        "ssm:SendCommand",
        "ssm:GetCommandInvocation",
        "ssm:ListCommands",
        "ssm:ListCommandInvocations",
        "ssm:DescribeInstanceInformation"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:document/AWS-RunPowerShellScript",
        "arn:aws:ssm:*:*:*"
      ]
    },
    {
      "Sid": "S3LogAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-SSM-LOGS-BUCKET/*"
    }
  ]
}
```

**Important**: Replace `YOUR-SSM-LOGS-BUCKET` with your actual S3 bucket name.

### 4.3 Optionally Restrict by Instance ID

For tighter security, limit to specific instances:

```json
{
  "Sid": "SSMSendCommandSpecificInstances",
  "Effect": "Allow",
  "Action": "ssm:SendCommand",
  "Resource": [
    "arn:aws:ec2:us-east-1:123456789012:instance/i-dev-instance-id",
    "arn:aws:ec2:us-east-1:123456789012:instance/i-prod-instance-id"
  ]
}
```

### 4.4 Save Access Credentials

After user creation:
1. **Download the CSV** or copy the credentials immediately
2. Store **Access Key ID** and **Secret Access Key** securely
3. These will be added to GitHub Secrets (next section)

**Security Note**: These credentials will only be shown once. Store them securely.

## Step 5: Create S3 Bucket for SSM Logs

### 5.1 Create Bucket

1. Navigate to **S3 Console** → **Create bucket**
2. **Bucket name**: `{organization}-ssm-logs` or `{app}-ssm-command-logs`
3. **Region**: Same region as your EC2 instances
4. **Block Public Access**: Keep all public access blocked
5. Click **Create bucket**

### 5.2 Configure Lifecycle Policy (Optional)

To automatically delete old logs:

1. Select the bucket → **Management** tab
2. **Create lifecycle rule**
3. **Rule name**: `Delete-Old-SSM-Logs`
4. **Prefix**: `ssm-logs/` (or leave empty for entire bucket)
5. **Expire current versions**: 90 days (or as needed)
6. **Delete expired object delete markers**: Check
7. Create rule

### 5.3 Verify Bucket Policy

Ensure the EC2 IAM role can write to this bucket. If using the `AmazonSSMManagedInstanceCore` policy, this should work automatically for SSM output.

## Step 6: Prepare Application Directory on EC2

### 6.1 Connect to EC2 Instance

Use one of:
- **RDP** (Remote Desktop Protocol)
- **SSM Session Manager** (browser-based terminal)
- **Fleet Manager** (AWS Console)

### 6.2 Create Application Directory

```powershell
# Create application directory
New-Item -Path "C:\Apps\YourApp" -ItemType Directory

# Navigate to directory
cd C:\Apps\YourApp
```

**Recommended Directory Structure**:
```
C:\Apps\YourApp\
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── venv\                  # Virtual environment
├── .env                   # Environment variables (DO NOT commit to Git)
├── logs\                  # Application logs
└── backup\                # Deployment backups (auto-created)
```

### 6.3 Clone Repository (First Time)

```powershell
# Clone your repository
git clone https://github.com/your-org/your-app.git C:\Apps\YourApp

cd C:\Apps\YourApp
```

**Important**: Ensure the server has Git installed and configured.

### 6.4 Create Python Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

### 6.5 Configure Application

Create `.env` file or set environment variables:
```powershell
# Example: Create .env file
@"
PROJECT_ID=your-project-id
API_KEY=your-api-key
DATABASE_URL=your-database-url
"@ | Out-File -FilePath ".env" -Encoding utf8
```

**Security**: Never commit `.env` files. Add to `.gitignore`.

### 6.6 Test Application Manually

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run application
python app.py

# Or for background execution (silent mode)
Start-Process -FilePath ".\venv\Scripts\pythonw.exe" -ArgumentList "app.py" -WindowStyle Hidden
```

### 6.7 Configure Firewall (if needed)

```powershell
# Allow application port (example: 443 for HTTPS)
New-NetFirewallRule -DisplayName "Allow App Port 443" `
  -Direction Inbound `
  -LocalPort 443 `
  -Protocol TCP `
  -Action Allow
```

## Step 7: Configure Security Groups

### 7.1 SSM Requirements

**No inbound rules required** for SSM functionality.

SSM communication is **outbound-only** from the EC2 instance:
- EC2 → SSM endpoints
- EC2 → S3 (for logs)

### 7.2 Application Access

Add inbound rules based on application needs:

**Example for HTTPS application**:
- **Type**: HTTPS
- **Protocol**: TCP
- **Port**: 443
- **Source**: Your desired CIDR (e.g., `0.0.0.0/0` for public, or specific IPs)

**Example for HTTP application**:
- **Type**: HTTP
- **Protocol**: TCP
- **Port**: 80
- **Source**: Your desired CIDR

### 7.3 VPC Endpoints (Optional - for Private Subnets)

If your EC2 instance is in a **private subnet** without internet access, create VPC endpoints:

Required endpoints:
- `com.amazonaws.{region}.ssm`
- `com.amazonaws.{region}.ssmmessages`
- `com.amazonaws.{region}.ec2messages`
- `com.amazonaws.{region}.s3` (Gateway endpoint for S3 logs)

## Step 8: Verification Checklist

Before proceeding to GitHub configuration, verify:

- [ ] IAM role created and attached to EC2 instance
- [ ] SSM Agent installed and running on EC2
- [ ] Instance appears as "Online" in SSM console
- [ ] IAM user created with SSM permissions
- [ ] Access keys saved securely
- [ ] S3 bucket created for logs
- [ ] Application directory created on EC2
- [ ] Git repository cloned
- [ ] Python virtual environment created
- [ ] Application runs successfully when started manually
- [ ] Security groups configured for application access

## Step 9: Test SSM Connectivity

### From AWS CLI (Local Machine)

```bash
# List managed instances
aws ssm describe-instance-information

# Send a test command
aws ssm send-command \
  --instance-ids "i-xxxxxxxxx" \
  --document-name "AWS-RunPowerShellScript" \
  --parameters 'commands=["Write-Host \"SSM Test Successful\"","Get-Date"]' \
  --output text \
  --query "Command.CommandId"

# Get command results (replace COMMAND_ID)
aws ssm get-command-invocation \
  --command-id "COMMAND_ID" \
  --instance-id "i-xxxxxxxxx" \
  --query "[StandardOutputContent,StandardErrorContent]" \
  --output text
```

**Expected**: Command executes successfully and returns output.

## Common Issues

### Instance Not Appearing in SSM

**Causes**:
- IAM role not attached
- SSM Agent not running
- Instance in private subnet without VPC endpoints
- Security group blocking outbound HTTPS (port 443)

**Solutions**:
1. Verify IAM role attachment
2. Check SSM Agent service status
3. Create VPC endpoints if needed
4. Allow outbound HTTPS in security group

### Permission Denied Errors

**Causes**:
- IAM user lacks SSM permissions
- IAM role lacks required policies
- Resource ARNs in policy incorrect

**Solutions**:
1. Verify IAM user policy includes `ssm:SendCommand`
2. Verify IAM role has `AmazonSSMManagedInstanceCore`
3. Check ARN formats in policies

## Next Steps

Once AWS infrastructure is configured:
1. Proceed to **03-GITHUB-CONFIGURATION.md**
2. Add AWS credentials to GitHub Secrets
3. Configure GitHub Environments
4. Deploy workflow templates

## Security Best Practices

1. **Rotate access keys** every 90 days
2. **Enable CloudTrail** for audit logging
3. **Use least privilege** IAM policies
4. **Enable MFA** for AWS console access
5. **Monitor SSM activity** via CloudWatch
6. **Encrypt S3 buckets** (SSE-S3 or SSE-KMS)
7. **Restrict instance metadata** access (IMDSv2)
8. **Keep SSM Agent updated** to latest version
