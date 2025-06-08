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

## **🛡️ Error Prevention & UI Stability Guidelines**

### **1. Critical Component Protection**
Never modify these working components without testing:
```
✅ OAuth Integration (Supabase auth flow)
✅ Core Pipeline (streaming_pipeline.py)
✅ Database Operations (Supabase CRUD)
✅ File Upload/Processing
✅ Session State Management
```

### **2. UI Container Architecture**
```css
/* Stable Base Layout */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    min-height: 100vh;
}

.auth-container {
    max-width: 500px;
    margin: 2rem auto;
    padding: 2rem;
}

.content-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}
```

### **3. Development Rules**

#### **Before Making Changes:**
1. **Test Current State**: `streamlit run app.py --server.port 8501`
2. **Create Git Branch**: `git checkout -b feature/your-change`
3. **Document What Works**: Note current functionality
4. **Make Minimal Changes**: One feature at a time

#### **During Development:**
1. **Incremental Testing**: Test after each small change
2. **Version Control**: Commit working states frequently
3. **Rollback Ready**: `git stash` or `git reset --hard` if broken
4. **Port Management**: Use consistent port (8501) to avoid confusion

#### **UI Container Best Practices:**
```python
# ✅ GOOD - Stable Container Pattern
def create_stable_container(content_type="default"):
    """Create consistent, reliable containers"""
    st.markdown(f"""
    <div class="whisperforge-container {content_type}">
    """, unsafe_allow_html=True)
    
    # Your content here
    
    st.markdown("</div>", unsafe_allow_html=True)

# ❌ BAD - Inline styles that break
st.markdown('<div style="complex inline styles">')
```

### **4. Testing Checklist**

#### **OAuth Testing:**
- [ ] "Continue with Google" button appears
- [ ] Clicking redirects to Google
- [ ] After Google auth, returns to main app
- [ ] User is authenticated and sees pipeline

#### **UI Container Testing:**
- [ ] All containers display properly
- [ ] No content below fold on page load
- [ ] Responsive design works on different screens
- [ ] CSS doesn't conflict with Streamlit defaults

#### **Core Functionality Testing:**
- [ ] File upload works
- [ ] Pipeline processes correctly
- [ ] Results display properly
- [ ] Navigation between pages works

### **5. Emergency Procedures**

#### **If OAuth Breaks:**
```bash
# Revert to last working commit
git log --oneline -5
git reset --hard [working_commit_hash]
```

#### **If UI Breaks:**
```bash
# Quick fix - remove custom CSS
# Comment out st.markdown with CSS in show_auth_page()
```

#### **If App Won't Start:**
```bash
# Clean restart
pkill -f streamlit
source venv/bin/activate
streamlit run app.py --server.port 8501
```

### **6. Stable UI Framework**

#### **Core CSS Architecture:**
```css
/* Base Theme - Never Change */
:root {
    --primary-color: #00FFFF;
    --secondary-color: #40E0D0;
    --bg-dark: #0a0f1c;
    --bg-darker: #0d1421;
    --text-light: rgba(255,255,255,0.9);
    --text-muted: rgba(255,255,255,0.6);
}

/* Stable Container Base */
.whisperforge-base {
    font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    background: linear-gradient(180deg, var(--bg-dark) 0%, var(--bg-darker) 100%);
}

/* Component Containers */
.auth-container { /* Auth page specific */ }
.main-container { /* Main app container */ }
.results-container { /* Results display */ }
```

### **7. Component Isolation**

Create separate, testable components:
```python
# components/auth.py
def render_oauth_section():
    """Isolated OAuth component"""
    # OAuth logic here
    
# components/pipeline.py  
def render_pipeline_section():
    """Isolated pipeline component"""
    # Pipeline logic here
```

### **8. Monitoring & Alerts**

```python
def health_check():
    """Monitor critical functionality"""
    checks = {
        "supabase_connection": test_supabase(),
        "oauth_url_generation": test_oauth_generation(),
        "file_upload": test_file_upload(),
        "pipeline_execution": test_pipeline()
    }
    return checks
```

## **⚡ Quick Recovery Commands**

```bash
# If multiple ports are running, kill all
pkill -f streamlit

# Clean start
source venv/bin/activate
streamlit run app.py --server.port 8501

# If Git is messy
git status
git stash  # Save uncommitted changes
git checkout main
git pull origin main

# Emergency reset to last known good state
git reset --hard origin/main
```

## **🎯 UI Stability Principles**

1. **Progressive Enhancement**: Start with basic functionality, add styling
2. **Container Consistency**: Use standard container patterns
3. **CSS Isolation**: Scope CSS to avoid conflicts
4. **Mobile First**: Design for mobile, enhance for desktop
5. **Fallback Ready**: Always have unstyled version working

## **📋 Pre-Deploy Checklist**

- [ ] OAuth flow complete end-to-end
- [ ] All UI containers display correctly
- [ ] No console errors in browser
- [ ] Mobile responsive
- [ ] All navigation works
- [ ] File upload/processing works
- [ ] Results display properly
- [ ] Settings page functional

## **🔄 Version Control Strategy**

```bash
# Feature development
git checkout -b feature/new-feature
# Make small changes
git add .
git commit -m "Small incremental change"
# Test thoroughly
# If works: continue
# If breaks: git reset --hard HEAD~1

# When feature complete
git checkout main
git merge feature/new-feature
git push origin main
```

This workflow prevents the types of errors we encountered and ensures UI containers remain solid and reliable.

*Last Updated: June 2024*
*Version: 1.0* 