# Security Standards and Best Practices

## Overview

This document defines security scanning requirements, standards, and standard operating procedures (SOPs) for Python applications in the CI/CD pipeline. Security is a **required gate** for all deployments.

## Security Philosophy

### Core Principles

1. **Security is not optional**: All checks must pass before deployment
2. **Defense in depth**: Multiple layers of security scanning
3. **Shift left**: Catch issues early in development
4. **Continuous monitoring**: Regular dependency updates and scans
5. **Zero trust**: Verify everything, assume nothing

## Security Scanning Tools

The pipeline implements three complementary security tools:

### 1. pip-audit (CVE Detection)
**Status**: **BLOCKING** - Pipeline fails if vulnerabilities found

**Purpose**: Detect known security vulnerabilities (CVEs) in Python dependencies

**What it scans**:
- All packages in `requirements.txt`
- Transitive dependencies
- Known CVEs from PyPI Advisory Database

**Configuration**:
```yaml
- name: Security - Dependency Vulnerability Scan (pip-audit)
  run: |
    pip-audit --desc --requirement requirements.txt
  continue-on-error: false  # BLOCKING
```

**Example Output**:
```
Found 2 known vulnerabilities in 1 package
Name    Version ID             Fix Versions
------- ------- -------------- ------------
requests 2.25.0  PYSEC-2023-74  2.31.0
```

### 2. safety (Dependency Security Database)
**Status**: **NON-BLOCKING** - Warnings only, does not fail pipeline

**Purpose**: Check dependencies against Safety DB for known security issues

**What it scans**:
- All installed packages
- Known security issues from Safety DB
- License issues (optional)

**Configuration**:
```yaml
- name: Security - Check with Safety
  run: |
    safety check --json || true
  continue-on-error: true  # NON-BLOCKING
```

**Why non-blocking**: May have false positives or issues with legacy dependencies

### 3. bandit (Static Security Analysis)
**Status**: **NON-BLOCKING** - Informational, does not fail pipeline

**Purpose**: Static analysis of Python code for common security issues

**What it scans**:
- Hardcoded passwords/secrets
- SQL injection vulnerabilities
- Use of insecure functions (eval, exec, pickle)
- Weak cryptography
- File path traversal issues
- Command injection risks

**Configuration**:
```yaml
- name: Security - Bandit Security Linter
  run: |
    bandit -r app.py -f json -o bandit-report.json || true
    bandit -r app.py -f screen
  continue-on-error: true  # NON-BLOCKING
```

**Example Issues Detected**:
```
Issue: [B201:flask_debug_true] A Flask app appears to be run with debug=True
Severity: High
Confidence: Medium
```

## Required Security Tools Installation

### requirements-dev.txt

```txt
# Security scanning tools
pip-audit>=2.6.0
safety>=2.3.0
bandit>=1.7.5

# Testing tools
pytest>=7.4.0
pytest-cov>=4.1.0

# Code quality
flake8>=6.1.0
pylint>=3.0.0
```

## Security Scanning Schedule

### On Every Push/PR
- pip-audit (blocking)
- safety (non-blocking)
- bandit (non-blocking)
- flake8 (critical errors blocking)

### Weekly (Scheduled Workflow)
- Dependency updates check
- Full security audit
- Generate security report

### Monthly
- Manual security review
- Dependency update sprint
- Access audit

## Common Security Issues and Fixes

### 1. Vulnerable Dependencies

**Issue**: Package has known CVE

**Example**:
```
flask 2.0.0 has known vulnerability CVE-2023-XXXXX
```

**Fix**:
```bash
# Update to latest secure version
pip install --upgrade flask

# Update requirements.txt
pip freeze > requirements.txt

# Verify fix
pip-audit --requirement requirements.txt
```

**SOP**:
1. Review CVE details and impact
2. Check if update has breaking changes
3. Update dependency version
4. Run full test suite
5. Deploy to development first
6. Monitor for issues before production

### 2. Hardcoded Secrets

**Issue**: Credentials in code

**Example**:
```python
# BAD - Hardcoded secret
API_KEY = "sk_live_1234567890abcdef"
DATABASE_URL = "postgresql://user:password@localhost/db"
```

**Fix**:
```python
# GOOD - Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# Validate required variables
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

**SOP**:
1. Move secrets to `.env` file (local development)
2. Add `.env` to `.gitignore`
3. Add secrets to GitHub Secrets (production)
4. Rotate compromised credentials immediately
5. Scan git history for exposed secrets
6. Use tools like `git-secrets` or `truffleHog`

### 3. SQL Injection

**Issue**: Unsanitized user input in SQL queries

**Example**:
```python
# BAD - SQL injection vulnerability
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
```

**Fix**:
```python
# GOOD - Parameterized queries
def get_user(username):
    query = "SELECT * FROM users WHERE username = ?"
    return db.execute(query, (username,))

# Or use ORM
def get_user(username):
    return User.query.filter_by(username=username).first()
```

### 4. Weak Cryptography

**Issue**: Use of insecure hashing or encryption

**Example**:
```python
# BAD - MD5 is cryptographically broken
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
```

**Fix**:
```python
# GOOD - Use bcrypt or argon2 for passwords
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
password_hash = generate_password_hash(password)

# Verify password
is_valid = check_password_hash(password_hash, password_attempt)
```

### 5. Unsafe File Operations

**Issue**: Path traversal or arbitrary file access

**Example**:
```python
# BAD - Path traversal vulnerability
def read_file(filename):
    with open(f'/uploads/{filename}', 'r') as f:
        return f.read()
# User could pass: ../../etc/passwd
```

**Fix**:
```python
# GOOD - Validate and sanitize paths
import os
from pathlib import Path

UPLOAD_DIR = Path('/uploads')

def read_file(filename):
    # Validate filename
    if '..' in filename or filename.startswith('/'):
        raise ValueError("Invalid filename")

    filepath = UPLOAD_DIR / filename

    # Ensure file is within allowed directory
    if not filepath.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise ValueError("Access denied")

    with open(filepath, 'r') as f:
        return f.read()
```

### 6. Command Injection

**Issue**: Unsanitized input to shell commands

**Example**:
```python
# BAD - Command injection vulnerability
import os
def ping_host(host):
    os.system(f'ping -c 1 {host}')
# User could pass: example.com; rm -rf /
```

**Fix**:
```python
# GOOD - Use subprocess with argument list
import subprocess

def ping_host(host):
    # Validate input
    if not host.replace('.', '').replace('-', '').isalnum():
        raise ValueError("Invalid hostname")

    # Use list, not string (prevents injection)
    result = subprocess.run(
        ['ping', '-c', '1', host],
        capture_output=True,
        timeout=5
    )
    return result.stdout
```

## Secure Coding Standards

### 1. Input Validation

**Always validate user input**:
```python
from flask import request, abort

@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    # Validate type (int) via route
    # Validate range
    if user_id < 1 or user_id > 1000000:
        abort(400, "Invalid user ID")

    # Additional validation
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())
```

### 2. Output Encoding

**Prevent XSS attacks**:
```python
from markupsafe import escape

@app.route('/search')
def search():
    query = request.args.get('q', '')
    # Escape user input in HTML
    safe_query = escape(query)
    return f'<h1>Results for: {safe_query}</h1>'
```

### 3. Authentication & Authorization

**Implement proper access control**:
```python
from functools import wraps
from flask import session, abort

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin.html')
```

### 4. Secure Session Management

```python
from flask import Flask
import os

app = Flask(__name__)

# Secure session configuration
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY'),  # Never hardcode
    SESSION_COOKIE_SECURE=True,           # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,         # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',        # CSRF protection
    PERMANENT_SESSION_LIFETIME=3600       # 1 hour timeout
)
```

### 5. HTTPS/TLS Configuration

```python
# Enforce HTTPS in production
if not app.debug:
    from flask_talisman import Talisman
    Talisman(app, force_https=True)
```

### 6. CORS Configuration

```python
from flask_cors import CORS

# Restrictive CORS policy
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://trusted-domain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## Security Configuration Checklist

### Application Security
- [ ] No hardcoded secrets
- [ ] Environment variables for configuration
- [ ] Input validation on all user input
- [ ] Output encoding for HTML/JavaScript
- [ ] Parameterized database queries
- [ ] Secure password hashing (bcrypt/argon2)
- [ ] HTTPS enforced in production
- [ ] Secure session cookies
- [ ] CSRF protection enabled
- [ ] Rate limiting implemented
- [ ] Error messages don't leak sensitive info

### Dependency Security
- [ ] All dependencies up to date
- [ ] No known CVEs in dependencies
- [ ] Minimal dependency footprint
- [ ] Dependencies pinned to specific versions
- [ ] Regular dependency audits scheduled

### Infrastructure Security
- [ ] AWS credentials in GitHub Secrets only
- [ ] IAM roles with least privilege
- [ ] Security groups properly configured
- [ ] VPC endpoints for SSM (if private subnet)
- [ ] S3 buckets not public
- [ ] CloudTrail logging enabled
- [ ] MFA enabled for AWS accounts

### Code Security
- [ ] No use of `eval()` or `exec()`
- [ ] No use of `pickle` for untrusted data
- [ ] No shell command injection
- [ ] No SQL injection vulnerabilities
- [ ] No path traversal vulnerabilities
- [ ] No insecure random number generation
- [ ] No insecure deserialization

## Handling Security Vulnerabilities

### Severity Levels

**Critical** (CVSS 9.0-10.0):
- Immediate action required
- Halt deployments
- Emergency patch within 24 hours

**High** (CVSS 7.0-8.9):
- Patch within 7 days
- Prioritize in current sprint
- Document mitigation if patch unavailable

**Medium** (CVSS 4.0-6.9):
- Patch within 30 days
- Schedule in next sprint
- Monitor for exploit activity

**Low** (CVSS 0.1-3.9):
- Patch within 90 days
- Include in regular maintenance
- Document if accepting risk

### Response Procedure

1. **Identification**
   - Alert received from pip-audit/safety/GitHub Dependabot
   - Review CVE details and CVSS score

2. **Assessment**
   - Determine if vulnerability affects your application
   - Assess exploitability and impact
   - Check if exploit is public

3. **Remediation**
   - Update to patched version if available
   - Apply workaround if no patch available
   - Remove dependency if not critical

4. **Testing**
   - Run full test suite
   - Deploy to development environment
   - Verify vulnerability is resolved

5. **Deployment**
   - Emergency deployment for Critical/High
   - Standard deployment for Medium/Low
   - Document changes in release notes

6. **Documentation**
   - Log incident in security log
   - Update dependencies documentation
   - Share lessons learned with team

## Security Testing

### Manual Security Testing

Periodic manual testing should include:

1. **Authentication bypass attempts**
2. **Authorization escalation testing**
3. **Input fuzzing**
4. **SQL injection testing**
5. **XSS testing**
6. **CSRF testing**
7. **File upload validation**
8. **API abuse testing**

### Automated Security Testing

```python
# test_security.py
import pytest
from app import app

def test_sql_injection_protection(client):
    """Test SQL injection is prevented."""
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f'/user?name={malicious_input}')

    # Should not execute SQL, should return error or empty
    assert response.status_code in [400, 404]
    # Verify table still exists
    from app.models import User
    assert User.query.count() >= 0

def test_xss_protection(client):
    """Test XSS is prevented."""
    xss_payload = "<script>alert('XSS')</script>"
    response = client.post('/comment', data={'text': xss_payload})

    # Payload should be escaped in response
    assert b'<script>' not in response.data
    assert b'&lt;script&gt;' in response.data or b'<script>' not in response.data

def test_unauthorized_access(client):
    """Test unauthorized access is denied."""
    # Without authentication
    response = client.get('/admin/dashboard')
    assert response.status_code == 401

def test_csrf_protection(client):
    """Test CSRF protection is enabled."""
    # POST without CSRF token should fail
    response = client.post('/api/delete', data={'id': 1})
    assert response.status_code in [400, 403]
```

## Security Monitoring

### CloudTrail Events to Monitor
- SSM command executions
- IAM policy changes
- Security group modifications
- S3 bucket policy changes
- Failed authentication attempts

### Application Logs to Monitor
- Failed login attempts
- Authorization failures
- Input validation failures
- Unusual API usage patterns
- Error rate spikes

## Security Compliance

### OWASP Top 10 Coverage

Our pipeline addresses:

1. **Broken Access Control**: Auth decorators, session management
2. **Cryptographic Failures**: Secure hashing, HTTPS enforcement
3. **Injection**: Parameterized queries, input validation
4. **Insecure Design**: Security standards, code review
5. **Security Misconfiguration**: Configuration checks, security headers
6. **Vulnerable Components**: pip-audit, safety, dependency management
7. **Authentication Failures**: Secure session config, password policies
8. **Software and Data Integrity**: Signed commits, dependency verification
9. **Security Logging Failures**: CloudTrail, application logs
10. **Server-Side Request Forgery**: Input validation, allowlist

## Emergency Response Plan

### Security Incident Response

1. **Detection** - Automated alerts or manual discovery
2. **Containment** - Disable affected systems/features
3. **Investigation** - Determine scope and impact
4. **Eradication** - Remove vulnerability/malware
5. **Recovery** - Restore systems and verify
6. **Lessons Learned** - Document and improve

### Emergency Contacts
- Security Team Lead
- DevOps On-Call
- AWS Account Administrator
- Application Owner

## Best Practices Summary

1. **Never commit secrets** - Use environment variables and GitHub Secrets
2. **Keep dependencies updated** - Regular audits and updates
3. **Validate all input** - Trust nothing from users
4. **Use parameterized queries** - Prevent SQL injection
5. **Implement proper authentication** - Secure sessions and access control
6. **Enable HTTPS** - Encrypt all traffic in production
7. **Monitor security events** - CloudTrail and application logs
8. **Regular security reviews** - Code review and penetration testing
9. **Incident response plan** - Be prepared for security events
10. **Security training** - Keep team educated on threats

## Next Steps

- Review **06-SSM-DEPLOYMENT-SOP.md** for deployment procedures
- Implement security testing in your application
- Configure security monitoring and alerts
- Schedule regular security audits
