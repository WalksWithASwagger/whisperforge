# WhisperForge Development Workflow

## 🌟 Git Branching Strategy

### Branch Structure
```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/xxx        # Feature development branches
├── hotfix/xxx         # Critical production fixes
└── release/x.x.x      # Release preparation branches
```

### Branch Rules
- **main**: Always deployable, tagged versions
- **develop**: Latest development changes
- **feature/***: New features, branched from develop
- **hotfix/***: Critical fixes, branched from main
- **release/***: Release preparation, branched from develop

### Workflow Steps
1. Create feature branch: `git checkout -b feature/new-feature develop`
2. Develop and commit changes
3. Push and create pull request to develop
4. Code review and merge to develop
5. Create release branch when ready: `git checkout -b release/1.1.0 develop`
6. Test, fix bugs, update version
7. Merge to main and tag: `git tag v1.1.0`

---

## 🚀 Development Environment Setup

### Prerequisites
```bash
# Python 3.11+
python --version

# Git
git --version

# Node.js (for potential frontend tools)
node --version
```

### Setup Steps
```bash
# 1. Clone repository
git clone https://github.com/WalksWithASwagger/whisperforge.git
cd whisperforge

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
cd whisperforge
pip install -r requirements.txt

# 4. Set up environment variables
cp env.example .env
# Edit .env with your API keys

# 5. Run tests
python -m pytest tests/

# 6. Start development server
streamlit run app_supabase.py
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/              # Unit tests for individual functions
├── integration/       # Integration tests for components
├── e2e/              # End-to-end tests for full workflows
└── fixtures/         # Test data and fixtures
```

### Test Commands
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=whisperforge --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_pipeline.py

# Run tests with verbose output
python -m pytest -v
```

### Test Requirements
- **Unit tests**: All core functions must have tests
- **Integration tests**: API integrations and database operations
- **E2E tests**: Complete user workflows
- **Coverage**: Minimum 80% code coverage

---

## 📦 Release Process

### Version Numbering
- **Major (x.0.0)**: Breaking changes
- **Minor (x.y.0)**: New features, backward compatible
- **Patch (x.y.z)**: Bug fixes, backward compatible

### Release Steps
1. **Prepare Release Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/1.1.0
   ```

2. **Update Version**
   ```bash
   echo "1.1.0" > VERSION
   # Update version in setup.py, __init__.py, etc.
   ```

3. **Test & Fix**
   ```bash
   python -m pytest
   streamlit run app_supabase.py  # Manual testing
   ```

4. **Merge to Main**
   ```bash
   git checkout main
   git merge release/1.1.0
   git tag v1.1.0
   git push origin main --tags
   ```

5. **Deploy to Production**
   - Streamlit Cloud auto-deploys from main
   - Monitor deployment logs
   - Verify functionality

6. **Merge Back to Develop**
   ```bash
   git checkout develop
   git merge main
   git push origin develop
   ```

---

## 🔧 Code Quality Standards

### Code Style
- **Formatter**: Black (`black .`)
- **Linter**: Flake8 (`flake8 .`)
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Performance considerations addressed

---

## 🚨 Hotfix Process

### When to Create Hotfix
- Critical production bugs
- Security vulnerabilities
- Data corruption issues

### Hotfix Steps
1. **Create Hotfix Branch**
   ```bash
   git checkout main
   git checkout -b hotfix/critical-bug-fix
   ```

2. **Fix and Test**
   ```bash
   # Make minimal changes
   python -m pytest
   ```

3. **Deploy Immediately**
   ```bash
   git checkout main
   git merge hotfix/critical-bug-fix
   git tag v1.0.1
   git push origin main --tags
   ```

4. **Merge to Develop**
   ```bash
   git checkout develop
   git merge main
   git push origin develop
   ```

---

## 📊 Monitoring & Analytics

### Key Metrics to Track
- **Application Performance**: Response times, error rates
- **User Behavior**: Feature usage, conversion rates
- **Business Metrics**: Sign-ups, retention, revenue

### Monitoring Tools
- **Logs**: Structured logging with levels
- **Errors**: Sentry or similar error tracking
- **Analytics**: Mixpanel or Google Analytics
- **Uptime**: StatusPage or Pingdom

### Alert Setup
- **Critical**: App down, database errors
- **Warning**: High response times, API rate limits
- **Info**: New deployments, user milestones

---

## 🔐 Security Guidelines

### API Keys & Secrets
- Never commit secrets to repository
- Use environment variables
- Rotate keys regularly
- Implement key access controls

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement proper authentication
- Regular security audits

### Access Control
- Principle of least privilege
- Regular access reviews
- Multi-factor authentication
- Audit logs for sensitive operations

---

*Last Updated: June 2024*
*Version: 1.0* 