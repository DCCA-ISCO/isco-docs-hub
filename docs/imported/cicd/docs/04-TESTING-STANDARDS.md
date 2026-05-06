# Testing Standards and Best Practices

## Overview

This document defines the testing standards and requirements for Python applications using the CI/CD pipeline. All applications must meet minimum testing requirements before deployment to production.

## Testing Philosophy

### Core Principles

1. **Tests are deployment gates**: Failing tests prevent deployment
2. **Fast feedback**: Tests run on every push and pull request
3. **Comprehensive coverage**: Critical paths must be tested
4. **Maintainable tests**: Tests should be clear and easy to update
5. **Environment parity**: Test environment matches production

## Testing Pyramid

```
        /\
       /  \      E2E Tests (Few)
      /____\     - Smoke tests
     /      \    - Health checks
    /________\   Integration Tests (Some)
   /          \  - API endpoints
  /____________\ - Database operations
 /              \ Unit Tests (Many)
/______________\  - Pure functions
                  - Business logic
                  - Utilities
```

## Minimum Testing Requirements

### Required Test Categories

All applications must implement:

1. **Unit Tests** - Test individual functions and methods
2. **Integration Tests** - Test component interactions
3. **Smoke Tests** - Verify application can start
4. **Environment Tests** - Validate configuration

### Coverage Requirements

- **Minimum coverage**: 70% overall
- **Critical paths**: 90%+ coverage
- **New code**: 80%+ coverage (enforced on PRs)

## Test Framework: pytest

### Installation

```bash
# In requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-flask>=1.2.0  # If using Flask
```

### Directory Structure

```
project-root/
├── app.py                    # Application code
├── tests/                    # All tests
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_app.py          # Main application tests
│   ├── test_routes.py       # API/route tests
│   ├── test_models.py       # Data model tests
│   ├── test_utils.py        # Utility function tests
│   └── test_integration.py  # Integration tests
├── requirements.txt          # Production dependencies
└── requirements-dev.txt      # Development dependencies
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual functions in isolation

**Characteristics**:
- Fast execution (< 100ms per test)
- No external dependencies (databases, APIs, files)
- Use mocking for dependencies
- Deterministic results

**Example**:
```python
# test_utils.py
import pytest
from app.utils import calculate_total, validate_email

def test_calculate_total():
    """Test total calculation with valid inputs."""
    assert calculate_total([10, 20, 30]) == 60
    assert calculate_total([]) == 0
    assert calculate_total([5.5, 4.5]) == 10.0

def test_calculate_total_with_invalid_input():
    """Test total calculation handles invalid input."""
    with pytest.raises(TypeError):
        calculate_total(None)

def test_validate_email():
    """Test email validation."""
    assert validate_email("user@example.com") is True
    assert validate_email("invalid-email") is False
    assert validate_email("") is False
```

**Best Practices**:
- One assertion per test (when possible)
- Descriptive test names
- Test edge cases and error conditions
- Use parameterized tests for multiple inputs

### 2. Integration Tests

**Purpose**: Test component interactions

**Characteristics**:
- May use test databases or mock services
- Tests multiple components working together
- Slower than unit tests (< 5 seconds per test)

**Example**:
```python
# test_routes.py
import pytest
from app import create_app

@pytest.fixture
def client():
    """Create test client."""
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test home page returns 200."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_api_endpoint(client):
    """Test API endpoint returns JSON."""
    response = client.get('/api/data')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_post_endpoint(client):
    """Test POST endpoint creates resource."""
    response = client.post('/api/items', json={
        'name': 'Test Item',
        'value': 100
    })
    assert response.status_code == 201

    data = response.get_json()
    assert data['name'] == 'Test Item'
    assert 'id' in data
```

### 3. Smoke Tests

**Purpose**: Verify application can start and basic functionality works

**Characteristics**:
- Critical path testing
- Quick validation (< 10 seconds total)
- Catches configuration errors
- Runs before full test suite

**Example**:
```python
# test_smoke.py
import pytest
from unittest.mock import patch
import os

def test_app_imports():
    """Verify application module can be imported."""
    with patch.dict(os.environ, {
        'REQUIRED_ENV_VAR': 'test-value'
    }):
        import app
        assert app is not None

def test_app_initialization():
    """Verify Flask app initializes."""
    with patch.dict(os.environ, {
        'REQUIRED_ENV_VAR': 'test-value'
    }):
        from app import app
        assert app.name == 'app'
        assert app is not None

def test_critical_routes_registered():
    """Verify critical routes are registered."""
    from app import app

    routes = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/' in routes
    assert '/health' in routes or '/api/health' in routes

def test_database_connection():
    """Verify database connection (if applicable)."""
    # Example for database-backed apps
    from app.database import db

    assert db.engine is not None
    # Optionally: db.engine.connect()
```

### 4. Environment Configuration Tests

**Purpose**: Validate required environment variables and configuration

**Example**:
```python
# test_config.py
import pytest
import os
from app.config import Config, validate_config

def test_required_environment_variables():
    """Test that all required env vars are documented."""
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'API_KEY',
        'AWS_REGION'
    ]

    # Document required variables
    for var in required_vars:
        assert var in Config.REQUIRED_ENV_VARS

def test_config_validation():
    """Test configuration validation catches missing vars."""
    with pytest.raises(ValueError, match="Missing required"):
        validate_config({})

def test_config_with_valid_env(monkeypatch):
    """Test config loads with valid environment."""
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///test.db')
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('API_KEY', 'test-api-key')

    config = Config.from_env()
    assert config.database_url == 'sqlite:///test.db'
    assert config.secret_key == 'test-secret-key'
```

## Coverage Requirements

### Running Coverage

```bash
# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Open report
open htmlcov/index.html  # macOS
start htmlcov\index.html  # Windows
```

### Coverage Configuration

Create `pytest.ini` or `.coveragerc`:

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=70

[coverage:run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

### Exempting Code from Coverage

```python
def debug_only_function():  # pragma: no cover
    """This function only runs in debug mode."""
    print("Debug information")

if __name__ == '__main__':  # pragma: no cover
    # Script execution code
    main()
```

## Test Organization Best Practices

### 1. Use Fixtures

```python
# conftest.py
import pytest
from app import create_app
from app.database import db

@pytest.fixture(scope='session')
def app():
    """Create application instance for testing."""
    app = create_app(config='testing')
    return app

@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()

@pytest.fixture
def sample_user():
    """Provide sample user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePassword123'
    }
```

### 2. Use Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("WORLD", "WORLD"),
    ("", ""),
    ("MiXeD", "MIXED"),
])
def test_uppercase_conversion(input, expected):
    """Test string uppercase conversion."""
    assert input.upper() == expected

@pytest.mark.parametrize("email,is_valid", [
    ("user@example.com", True),
    ("invalid", False),
    ("user@", False),
    ("@example.com", False),
    ("user@example.co.uk", True),
])
def test_email_validation(email, is_valid):
    """Test email validation with various inputs."""
    from app.utils import validate_email
    assert validate_email(email) == is_valid
```

### 3. Use Markers

```python
import pytest

@pytest.mark.slow
def test_large_dataset_processing():
    """Test processing of large dataset."""
    # This test takes > 5 seconds
    pass

@pytest.mark.integration
def test_external_api():
    """Test integration with external API."""
    pass

@pytest.mark.unit
def test_pure_function():
    """Test pure function logic."""
    pass

# Run specific markers
# pytest -m "not slow"  # Skip slow tests
# pytest -m integration  # Run only integration tests
```

### 4. Mock External Dependencies

```python
from unittest.mock import patch, Mock
import pytest

@patch('app.services.external_api.requests.get')
def test_api_call(mock_get):
    """Test API call with mocked response."""
    # Setup mock
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'data': 'test'}
    mock_get.return_value = mock_response

    # Test
    from app.services import fetch_data
    result = fetch_data('endpoint')

    # Assertions
    assert result == {'data': 'test'}
    mock_get.assert_called_once_with('endpoint')

@patch('app.database.Database.connect')
def test_database_error_handling(mock_connect):
    """Test database connection error handling."""
    mock_connect.side_effect = ConnectionError("Database unavailable")

    from app.database import get_connection
    with pytest.raises(ConnectionError):
        get_connection()
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
- name: Run Unit Tests
  run: |
    pytest tests/ \
      -v \
      --tb=short \
      --cov=app \
      --cov-report=term-missing \
      --cov-report=xml \
      --cov-fail-under=70
  continue-on-error: false  # Block deployment on failure

- name: Upload Coverage to Codecov
  uses: codecov/codecov-action@v4
  if: always()
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
  continue-on-error: true  # Don't block on upload failure
```

### Test Failure Handling

**Philosophy**: Tests are gates, not suggestions

- **Unit tests fail**: Pipeline stops, no deployment
- **Integration tests fail**: Pipeline stops, no deployment
- **Smoke tests fail**: Pipeline stops, no deployment
- **Coverage below threshold**: Pipeline stops (configurable)

**Acceptable exceptions** (use `continue-on-error: true`):
- Coverage upload failures (reporting issue, not test issue)
- Optional linting warnings
- Performance benchmarks (informational)

## Testing Checklist

Before committing code, ensure:

- [ ] All tests pass locally
- [ ] New features have corresponding tests
- [ ] Bug fixes include regression tests
- [ ] Coverage meets minimum threshold
- [ ] No skipped tests without justification
- [ ] Mocks are used appropriately
- [ ] Test names are descriptive
- [ ] Tests are independent (no interdependencies)

## Common Testing Patterns

### Testing Flask Routes

```python
def test_route_requires_authentication(client):
    """Test route requires authentication."""
    response = client.get('/protected')
    assert response.status_code == 401

def test_route_with_authentication(client, auth_headers):
    """Test route with valid authentication."""
    response = client.get('/protected', headers=auth_headers)
    assert response.status_code == 200
```

### Testing Error Handling

```python
def test_handles_missing_file():
    """Test graceful handling of missing file."""
    from app.utils import load_config

    with pytest.raises(FileNotFoundError):
        load_config('nonexistent.yml')

def test_handles_invalid_json():
    """Test handling of invalid JSON input."""
    from app.api import process_request

    with pytest.raises(ValueError, match="Invalid JSON"):
        process_request('{ invalid json }')
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous function."""
    from app.async_utils import fetch_async

    result = await fetch_async('https://api.example.com')
    assert result is not None
```

## Performance Testing (Optional)

### Benchmarking

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Example test
def test_performance_of_algorithm(benchmark):
    """Benchmark algorithm performance."""
    from app.algorithms import complex_calculation

    result = benchmark(complex_calculation, 1000)
    assert result > 0
```

## Test Maintenance

### Regular Review
- Monthly review of test suite
- Remove obsolete tests
- Update tests for code changes
- Refactor duplicate test code

### Documentation
- Document complex test setups
- Explain mocking strategies
- Note test dependencies
- Keep README updated with test instructions

## Troubleshooting Common Issues

### Tests Pass Locally but Fail in CI

**Causes**:
- Environment differences
- Missing dependencies in `requirements-dev.txt`
- Hardcoded paths
- Time zone differences

**Solutions**:
- Use environment variables
- Ensure all test dependencies listed
- Use relative paths or `tempfile`
- Use UTC or freeze time with `freezegun`

### Flaky Tests

**Causes**:
- Network dependencies
- Race conditions
- Random data
- Time-dependent logic

**Solutions**:
- Mock network calls
- Use deterministic ordering
- Seed random generators
- Use `freezegun` to control time

### Slow Tests

**Causes**:
- Database operations
- External API calls
- Large dataset processing

**Solutions**:
- Use in-memory databases (SQLite)
- Mock external calls
- Reduce test data size
- Mark as `@pytest.mark.slow` and skip in CI

## Next Steps

- Review **05-SECURITY-STANDARDS.md** for security testing requirements
- Implement test suite following these standards
- Configure CI/CD workflow to run tests
- Monitor coverage trends over time
