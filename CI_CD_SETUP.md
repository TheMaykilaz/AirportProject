# GitLab CI/CD Setup - Complete Guide

## 📋 Overview

This document describes all changes made to set up a complete CI/CD pipeline with Docker, testing, and linting for the AirportProject.

---

## 🔧 Changes Made

### 1. **Docker & Environment Setup**

#### **Dockerfile** - Fixed Line Endings Issue
**Problem**: Windows line endings (CRLF) in `entrypoint.sh` caused container startup failures.

**Changes**:
```dockerfile
# Added dos2unix to convert line endings
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    dos2unix \  # <-- NEW
    && rm -rf /var/lib/apt/lists/*

# Convert line endings before making executable
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh  # <-- UPDATED
```

#### **entrypoint.sh** - Added Default Environment Variables
**Problem**: Script failed when environment variables weren't set.

**Changes**:
```bash
# Set defaults if not provided
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-airportuser}

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
```

#### **.env File** - Created from Sample
**Problem**: No `.env` file existed, so environment variables weren't loaded.

**Action**: Created `.env` from `.env.sample` with default values.

#### **.gitattributes** - Prevent Future Line Ending Issues
**New file** to enforce Unix line endings:
```
*.sh text eol=lf
*.py text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
Dockerfile text eol=lf
docker-compose*.yml text eol=lf
```

---

### 2. **Dependencies** (`requirements.txt`)

#### **Added Missing Packages**:
```txt
channels==4.0.0          # Django Channels for WebSockets
channels-redis==4.2.0    # Redis backend for Channels
daphne==4.1.0           # ASGI server (was missing, caused startup failure)
ruff==0.8.4             # Fast Python linter and formatter
```

**Why**: 
- `daphne` was referenced in `docker-compose.yml` but not installed
- `channels` and `channels-redis` needed for WebSocket support
- `ruff` for code quality checks

---

### 3. **GitLab CI/CD Pipeline** (`.gitlab-ci.yml`)

#### **Complete Rewrite** - From Docker-in-Docker to Native Services

**Before**: Used Docker-in-Docker (DinD) for tests, which couldn't access services.

**After**: 4-stage pipeline with proper service integration.

#### **New Pipeline Structure**:

```yaml
stages:
  - build      # Build Docker image
  - lint       # Check code quality
  - test       # Run Django tests
  - deploy     # Deploy (manual)
```

---

#### **Stage 1: Build** (`build_image`)

**Purpose**: Build and push Docker image to GitLab Container Registry.

```yaml
build_image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .
    - docker push $IMAGE_NAME:$IMAGE_TAG
    - docker push $IMAGE_NAME:latest
  only:
    - main
```

**Key Points**:
- Uses Docker-in-Docker for building
- Tags with commit SHA and `latest`
- Only runs on `main` branch

---

#### **Stage 2: Lint** (`ruff_lint`) - NEW

**Purpose**: Check code quality with Ruff linter.

```yaml
ruff_lint:
  stage: lint
  image: python:3.12-slim
  variables:
    PIP_DISABLE_PIP_VERSION_CHECK: "1"
    PIP_NO_CACHE_DIR: "1"
  cache:
    key: pip-lint-${CI_COMMIT_REF_SLUG}
    paths:
      - .cache/pip
  before_script:
    - pip install ruff==0.8.4
  script:
    - echo "Running Ruff linter..."
    - ruff check . --output-format=gitlab || true
    - echo "Running Ruff formatter check..."
    - ruff format --check . || true
  allow_failure: true  # Non-blocking (warnings only)
  only:
    - main
    - merge_requests
```

**Key Points**:
- Lightweight Python image (no Docker needed)
- Caches pip packages for speed
- Non-blocking (won't fail pipeline)
- Runs on main and merge requests

---

#### **Stage 3: Test** (`run_tests`) - MAJOR REWRITE

**Purpose**: Run Django tests with real Postgres and Redis services.

**Before** (Broken):
```yaml
# Used Docker-in-Docker - services were unreachable
run_tests:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker run --rm -e DB_HOST=db $IMAGE_NAME:latest python manage.py test
    # ❌ DB_HOST=db doesn't work inside DinD
```

**After** (Working):
```yaml
run_tests:
  stage: test
  image: python:3.12-slim
  services:
    - name: postgres:16-alpine
      alias: db                    # ✅ Accessible as 'db' hostname
    - name: redis:7-alpine
      alias: redis                 # ✅ Accessible as 'redis' hostname
  variables:
    # Django DB settings
    DB_NAME: test_db
    DB_USER: test_user
    DB_PASSWORD: test_pass
    DB_HOST: db                    # ✅ Works because of service alias
    DB_PORT: "5432"
    # Postgres service config
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    # Redis settings
    REDIS_HOST: redis
    REDIS_PORT: "6379"
    # Django settings
    SECRET_KEY: "test-secret-key-for-ci"
    DEBUG: "True"
  cache:
    key: pip-${CI_COMMIT_REF_SLUG}
    paths:
      - .cache/pip
  before_script:
    - python --version
    - pip install --upgrade pip
    - pip install -r requirements.txt
    # Wait for Postgres to be ready
    - python - <<'PY'
from time import sleep
import os, socket
host, port = os.getenv("DB_HOST","db"), int(os.getenv("DB_PORT","5432"))
for i in range(30):
    try:
        with socket.socket() as s:
            s.settimeout(1.0)
            s.connect((host, port))
            print("DB is reachable")
            break
    except Exception:
        print("Waiting for DB...")
        sleep(2)
else:
    raise SystemExit("DB not reachable in time")
PY
  script:
    - python manage.py migrate --noinput
    - python manage.py test --parallel
  only:
    - main
    - merge_requests
```

**Key Improvements**:
- ✅ Uses native GitLab services (Postgres, Redis)
- ✅ Services accessible via hostname aliases
- ✅ DB readiness check prevents race conditions
- ✅ Pip caching speeds up subsequent runs
- ✅ Runs on merge requests for early feedback
- ✅ Parallel test execution

---

#### **Stage 4: Deploy** (`deploy_staging`, `deploy_production`)

**No changes** - Manual deployment jobs remain the same.

---

### 4. **Test Suite** - NEW

#### **Created Comprehensive Tests**

**Before**: 0 tests  
**After**: 30 tests across 2 apps

#### **user/tests.py** - 15 Tests
```python
class UserModelTest(TestCase):
    - test_create_user
    - test_create_superuser
    - test_user_full_name
    - test_user_age_calculation
    - test_user_age_none_without_dob
    - test_can_book_flights_with_required_info
    - test_cannot_book_flights_without_verification

class EmailVerificationCodeTest(TestCase):
    - test_generate_code
    - test_code_is_valid
    - test_expired_code_is_invalid
    - test_mark_code_as_used

class UserProfileTest(TestCase):
    - test_create_user_profile
    - test_passport_validity
    - test_expired_passport_is_invalid

class LoginAttemptTest(TestCase):
    - test_log_successful_attempt
    - test_get_recent_failures
```

#### **airport/tests.py** - 15 Tests
```python
class CountryModelTest(TestCase):
    - test_create_country
    - test_country_code_uppercase

class AirportModelTest(TestCase):
    - test_create_airport
    - test_airport_code_uppercase

class AirlineModelTest(TestCase):
    - test_create_airline
    - test_airline_code_uppercase

class AirplaneModelTest(TestCase):
    - test_create_airplane
    - test_airplane_registration_uppercase

class FlightModelTest(TestCase):
    - test_create_flight
    - test_flight_duration
    - test_flight_is_active

class FlightSeatModelTest(TestCase):
    - test_create_flight_seat
    - test_seat_is_available
    - test_seat_is_not_available_when_booked
```

**Coverage**: Models, properties, validation, business logic

---

### 5. **Ruff Linting Configuration**

#### **ruff.toml** - NEW
```toml
line-length = 120
target-version = "py312"

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DJ",  # flake8-django
    "PIE", # flake8-pie
    "T20", # flake8-print
    "SIM", # flake8-simplify
]

ignore = [
    "E501",   # Line too long
    "B008",   # Function calls in defaults (Django)
    "DJ001",  # null=True on strings
    "T201",   # Print statements
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"settings.py" = ["E501"]
"*/migrations/*.py" = ["ALL"]
"*/views.py" = ["F401"]
"*/urls.py" = ["F401"]
```

#### **Developer Tools** - NEW
- **`lint.sh`** - Quick linting script
- **`.pre-commit-config.yaml`** - Pre-commit hooks
- **`LINTING.md`** - Linting documentation

---

## 🧪 How to Test Everything

### **Test 1: Local Docker Environment**

#### **1.1 Start Services**
```powershell
# Clean start
docker-compose down
docker-compose up -d --build

# Check status
docker-compose ps
```

**Expected Output**:
```
NAME            STATUS
airport_db      Up (healthy)
airport_redis   Up
airport_web     Up
```

#### **1.2 Check Logs**
```powershell
docker-compose logs -f web
```

**Expected Output**:
```
Waiting for PostgreSQL at db:5432...
db:5432 - accepting connections
PostgreSQL is ready!
Running migrations...
Operations to perform: ...
Collecting static files...
Creating superuser if not exists...
Superuser created: admin@airport.com / admin123
Starting server...
2025-10-22 00:00:00,000 INFO     Starting server at tcp:port=8001:interface=0.0.0.0
```

#### **1.3 Access Application**
```powershell
# Open browser
start http://localhost:8001
start http://localhost:8001/admin
```

**Expected**: Application loads, admin panel accessible

---

### **Test 2: Run Tests Locally**

#### **2.1 Run All Tests**
```powershell
docker-compose exec web python manage.py test --parallel
```

**Expected Output**:
```
Found 30 test(s).
Creating test database for alias 'default'...
..............................
----------------------------------------------------------------------
Ran 30 tests in 1.025s

OK
```

#### **2.2 Run Specific App Tests**
```powershell
# User app only
docker-compose exec web python manage.py test user

# Airport app only
docker-compose exec web python manage.py test airport

# Verbose output
docker-compose exec web python manage.py test --verbosity=2
```

#### **2.3 Test with Coverage (Optional)**
```powershell
# Install coverage
docker-compose exec web pip install coverage

# Run tests with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
docker-compose exec web coverage html
```

---

### **Test 3: Run Linting Locally**

#### **3.1 Check Code Quality**
```powershell
# Install ruff (if not already)
docker-compose exec web pip install ruff==0.8.4

# Check for issues
docker-compose exec web ruff check .

# See statistics
docker-compose exec web ruff check . --statistics
```

**Expected Output**:
```
165	W293  	[*] blank-line-with-whitespace
 29	I001  	[*] unsorted-imports
 20	F401  	[*] unused-import
...
[*] fixable with `ruff check --fix`
```

#### **3.2 Auto-Fix Issues**
```powershell
# Fix auto-fixable issues
docker-compose exec web ruff check . --fix

# Format code
docker-compose exec web ruff format .

# Check formatting
docker-compose exec web ruff format --check .
```

#### **3.3 Use Lint Script**
```powershell
# Make executable (Linux/Mac)
chmod +x lint.sh

# Run
./lint.sh
```

---

### **Test 4: GitLab CI/CD Pipeline**

#### **4.1 Validate YAML Syntax**

**Option A: GitLab UI**
1. Go to your project in GitLab
2. Navigate to **CI/CD → Editor**
3. Click **"Validate"** or **"CI Lint"**

**Option B: GitLab API**
```powershell
# Replace with your values
$PROJECT_ID = "your-project-id"
$TOKEN = "your-access-token"
$GITLAB_URL = "https://gitlab.com"

# Validate
$content = Get-Content .gitlab-ci.yml -Raw
$body = @{ content = $content } | ConvertTo-Json

Invoke-RestMethod -Uri "$GITLAB_URL/api/v4/projects/$PROJECT_ID/ci/lint" `
    -Method Post `
    -Headers @{ "PRIVATE-TOKEN" = $TOKEN } `
    -Body $body `
    -ContentType "application/json"
```

**Expected Output**:
```json
{
  "valid": true,
  "errors": []
}
```

#### **4.2 Test on Feature Branch**
```powershell
# Create test branch
git checkout -b test-ci-pipeline

# Stage all changes
git add .

# Commit
git commit -m "Setup CI/CD pipeline with Docker, tests, and linting

Changes:
- Fix Docker line endings with dos2unix
- Add missing dependencies (daphne, channels, ruff)
- Rewrite CI pipeline with native services
- Add 30 comprehensive tests
- Add Ruff linting configuration
- Create developer documentation"

# Push to GitLab
git push origin test-ci-pipeline
```

#### **4.3 Create Merge Request**
1. Go to GitLab → **Merge Requests**
2. Click **"New merge request"**
3. Source: `test-ci-pipeline` → Target: `main`
4. Click **"Create merge request"**

#### **4.4 Monitor Pipeline**
1. Go to **CI/CD → Pipelines**
2. Click on the running pipeline
3. Watch each stage execute

**Expected Pipeline Flow**:
```
Stage 1: build_image
  ✅ Build Docker image (~2-3 min)
  ✅ Push to registry

Stage 2: ruff_lint
  ⚠️  Lint code (warnings, non-blocking) (~30 sec)

Stage 3: run_tests
  ✅ Run 30 tests (~1 min)
  ✅ All tests pass

Stage 4: deploy_staging
  ⏸️  Manual (not triggered)

Stage 4: deploy_production
  ⏸️  Manual (not triggered)
```

#### **4.5 Check Job Logs**

**build_image logs**:
```
$ docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .
Step 1/9 : FROM python:3.12-slim
...
Successfully built abc123def456
Successfully tagged registry.gitlab.com/...
$ docker push $IMAGE_NAME:$IMAGE_TAG
The push refers to repository [registry.gitlab.com/...]
✅ Job succeeded
```

**ruff_lint logs**:
```
$ ruff check . --output-format=gitlab
...
⚠️  Job succeeded (with warnings)
```

**run_tests logs**:
```
$ python manage.py test --parallel
Found 30 test(s).
Creating test database for alias 'default'...
DB is reachable
..............................
Ran 30 tests in 1.025s
OK
✅ Job succeeded
```

---

### **Test 5: Verify Each Component**

#### **5.1 Database Connection**
```powershell
# Connect to Postgres
docker-compose exec db psql -U airportuser -d airportdb

# List tables
\dt

# Exit
\q
```

#### **5.2 Redis Connection**
```powershell
# Connect to Redis
docker-compose exec redis redis-cli

# Test
PING
# Should return: PONG

# Exit
exit
```

#### **5.3 Django Shell**
```powershell
docker-compose exec web python manage.py shell
```

```python
# Test user creation
from user.models import User
user = User.objects.create_user(
    email='test@example.com',
    password='testpass123',
    first_name='Test',
    last_name='User'
)
print(user.full_name)  # Should print: Test User

# Test flight query
from airport.models import Flight
flights = Flight.objects.all()
print(f"Total flights: {flights.count()}")

# Exit
exit()
```

---

## 📊 Success Criteria

### ✅ Local Environment
- [ ] All containers start without errors
- [ ] Application accessible at http://localhost:8001
- [ ] Admin panel accessible at http://localhost:8001/admin
- [ ] Can login with `admin@airport.com` / `admin123`

### ✅ Tests
- [ ] All 30 tests pass locally
- [ ] Tests run in parallel successfully
- [ ] Test database created and destroyed cleanly

### ✅ Linting
- [ ] Ruff runs without crashing
- [ ] Can auto-fix issues with `--fix`
- [ ] Can format code with `ruff format`

### ✅ CI/CD Pipeline
- [ ] YAML syntax is valid
- [ ] Pipeline triggers on push
- [ ] `build_image` job succeeds
- [ ] `ruff_lint` job completes (warnings OK)
- [ ] `run_tests` job succeeds with 30 tests passing
- [ ] Pipeline completes in < 5 minutes

---

## 🐛 Troubleshooting

### Issue: Container fails with "exec /app/entrypoint.sh: no such file or directory"
**Cause**: Line ending issue  
**Fix**: Rebuild with dos2unix
```powershell
docker-compose down
docker-compose build --no-cache web
docker-compose up -d
```

### Issue: Tests fail with "DB not reachable"
**Cause**: Database not ready  
**Fix**: Wait longer or check DB health
```powershell
docker-compose exec web python - <<'PY'
import socket
s = socket.socket()
s.connect(("db", 5432))
print("DB is reachable!")
PY
```

### Issue: CI pipeline fails with "services not accessible"
**Cause**: Using Docker-in-Docker for tests  
**Fix**: Ensure using Python image with service aliases (already fixed in `.gitlab-ci.yml`)

### Issue: Ruff removes needed imports
**Cause**: Imports used in other files (re-exports)  
**Fix**: Already configured in `ruff.toml` per-file-ignores

---

## 📚 Files Changed Summary

| File | Status | Purpose |
|------|--------|---------|
| `.gitlab-ci.yml` | ✏️ Modified | Complete CI/CD pipeline rewrite |
| `Dockerfile` | ✏️ Modified | Added dos2unix, fixed line endings |
| `entrypoint.sh` | ✏️ Modified | Added default env vars |
| `requirements.txt` | ✏️ Modified | Added daphne, channels, ruff |
| `user/tests.py` | ✏️ Modified | Added 15 tests |
| `airport/tests.py` | ✏️ Modified | Added 15 tests |
| `.env` | ➕ Created | Environment variables |
| `.gitattributes` | ➕ Created | Enforce LF line endings |
| `ruff.toml` | ➕ Created | Ruff configuration |
| `lint.sh` | ➕ Created | Linting script |
| `.pre-commit-config.yaml` | ➕ Created | Pre-commit hooks |
| `LINTING.md` | ➕ Created | Linting documentation |
| `CI_CD_SETUP.md` | ➕ Created | This file |

---

## 🚀 Next Steps

1. **Review this document** - Understand all changes
2. **Test locally** - Follow "Test 1" and "Test 2"
3. **Commit changes** - Stage and commit all files
4. **Push to GitLab** - Test CI/CD pipeline
5. **Monitor pipeline** - Ensure all stages pass
6. **Optional: Fix linting** - Run `ruff check --fix`
7. **Merge to main** - Once pipeline passes

---

## 📞 Support

- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **GitLab CI/CD**: https://docs.gitlab.com/ee/ci/
- **Django Testing**: https://docs.djangoproject.com/en/stable/topics/testing/
- **Docker Compose**: https://docs.docker.com/compose/

---

**Last Updated**: 2025-10-22  
**Pipeline Version**: 1.0  
**Test Coverage**: 30 tests across 2 apps
