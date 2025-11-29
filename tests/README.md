# Tests

This directory contains test files for the Task Manager Agent project.

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_models.py` - Tests for data models and schemas
- `test_services.py` - Tests for service layer (business logic)
- `test_api.py` - Tests for API endpoints
- `test_agents.py` - Tests for AI agent functionality

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_models.py
pytest tests/test_services.py
pytest tests/test_api.py
pytest tests/test_agents.py
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=backend --cov=frontend
```

## Test Notes

- Some tests may be skipped if required services (database, OpenAI API) are not configured
- Database tests require Supabase to be set up and configured
- Agent tests require a valid OpenAI API key
- API tests use FastAPI's TestClient and don't require a running server

## Writing New Tests

When adding new tests:

1. Follow the existing test structure
2. Use fixtures from `conftest.py` when possible
3. Mark async tests with `@pytest.mark.asyncio`
4. Use `pytest.skip()` for tests that require external services
5. Add docstrings explaining what each test does

