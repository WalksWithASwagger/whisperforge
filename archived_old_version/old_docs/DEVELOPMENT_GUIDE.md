# WhisperForge Development Guide

## 🎯 **CRITICAL: READ THIS FIRST**

**This document is essential for maintaining WhisperForge stability. Follow these guidelines to prevent 502 errors and system breakages.**

## 🏗️ **Architecture Overview**

WhisperForge is a production-grade AI audio transformation platform with the following core architecture:

### **Core Modules (DO NOT BREAK)**
```
core/
├── authentication.py          # User auth & session management
├── supabase_client.py        # Database operations
├── file_upload_manager.py    # Large file handling & chunking
├── transcription_service.py  # Audio-to-text conversion
├── content_generator.py      # AI content generation
├── streaming_pipeline.py     # Real-time UI updates
├── prompt_manager.py         # Custom prompts & knowledge base
├── ui_components.py          # Aurora UI components
├── logging_config.py         # Enhanced logging system
└── error_handler.py          # Graceful error handling
```

### **Key Features**
- **Large File Support**: Up to 2GB with intelligent chunking
- **Real-time Streaming**: Aurora-styled progress indicators
- **Multi-AI Integration**: OpenAI, Anthropic, Groq
- **User Authentication**: Supabase-based auth system
- **Content History**: Persistent user data
- **Custom Prompts**: Personalized AI instructions

## 🚨 **CRITICAL RULES - NEVER VIOLATE**

### **1. NEVER Remove Core Features**
- ❌ **DO NOT** simplify by removing large file upload
- ❌ **DO NOT** remove streaming pipeline
- ❌ **DO NOT** remove authentication system
- ❌ **DO NOT** remove database integration
- ❌ **DO NOT** remove error handling

### **2. ALWAYS Maintain Graceful Degradation**
```python
# ✅ CORRECT: Graceful fallback
try:
    result = supabase_operation()
except Exception as e:
    log_error(e, "Supabase operation failed")
    return fallback_behavior()

# ❌ WRONG: Hard failure
result = supabase_operation()  # Will crash if Supabase is down
```

### **3. ALWAYS Use Proper Error Handling**
```python
# ✅ CORRECT: Comprehensive error handling
from core.logging_config import log_error, log_pipeline_step

def process_audio(file_path):
    try:
        log_pipeline_step("audio_processing", "started")
        result = transcribe_audio(file_path)
        log_pipeline_step("audio_processing", "completed")
        return result
    except Exception as e:
        log_pipeline_step("audio_processing", "failed", {"error": str(e)})
        log_error(e, f"Audio processing failed for {file_path}")
        return None
```

### **4. ALWAYS Test Before Deploying**
```bash
# Run full test suite
pytest tests/ -v

# Run specific test categories
pytest tests/ -m unit          # Fast unit tests
pytest tests/ -m integration   # Integration tests
pytest tests/ -m supabase      # Database tests
```

## 🔧 **Development Workflow**

### **Before Making Changes**
1. **Read the logs**: Check `logs/` directory for recent issues
2. **Run tests**: Ensure current state is stable
3. **Check dependencies**: Verify all imports work
4. **Review architecture**: Understand impact of changes

### **Making Changes**
1. **Start small**: Make incremental changes
2. **Test frequently**: Run tests after each change
3. **Log everything**: Use the logging system extensively
4. **Maintain fallbacks**: Always provide graceful degradation

### **After Changes**
1. **Run full test suite**: `pytest tests/ -v`
2. **Test locally**: `streamlit run app.py`
3. **Check logs**: Verify no new errors
4. **Test deployment**: Ensure requirements.txt is correct

## 📊 **Testing Strategy**

### **Systematic Error-Fixing Process**
**CRITICAL: Follow this exact process when fixing errors to prevent breakages**

#### **Phase 1: Identify & Isolate**
1. **Read the error message completely** - don't guess
2. **Check import statements** - verify module names exist
3. **Test individual components** - isolate the failing part
4. **Use grep/search** to find actual function/class names

#### **Phase 2: Fix Methodically**
1. **Fix one error at a time** - don't batch changes
2. **Test after each fix** - verify it works before moving on
3. **Check related code** - ensure changes don't break other parts
4. **Update tests to match reality** - not the other way around

#### **Phase 3: Verify Integration**
1. **Run full test suite** after all fixes
2. **Test app startup** with real imports
3. **Check logs** for any warnings or errors
4. **Test core functionality** end-to-end

#### **Example: Fixing Import Errors**
```bash
# 1. Identify the actual module structure
ls core/
grep -r "class.*Manager" core/

# 2. Test the import in isolation
python -c "from core.file_upload import LargeFileUploadManager; print('✅')"

# 3. Fix the test to match reality
# Change: from core.file_upload_manager import LargeFileUploadManager
# To:     from core.file_upload import LargeFileUploadManager

# 4. Verify the fix works
pytest tests/test_specific.py -v

# 5. Run full suite
pytest tests/ -v
```

### **Local Testing Setup**
```bash
# Activate virtual environment
source venv/bin/activate

# Set up environment variables (use actual values)
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_anon_key"  # Note: ANON_KEY not KEY
export OPENAI_API_KEY="your_openai_key"

# Install test dependencies
pip install pytest pytest-mock streamlit

# Run tests systematically
pytest tests/ -v                    # Full suite
pytest tests/ -m unit               # Fast unit tests only
pytest tests/ -m integration        # Integration tests
pytest tests/ -m supabase          # Database tests
```

### **Test Categories**
- **Unit Tests** (`-m unit`): Fast, isolated component tests
- **Integration Tests** (`-m integration`): Multi-component workflows
- **Supabase Tests** (`-m supabase`): Real database operations
- **AI Tests** (`-m ai`): API integration tests

### **Continuous Testing**
```bash
# Watch for changes and auto-test
pytest-watch tests/ -v

# Test specific functionality
pytest tests/test_core_functionality.py::TestLargeFileUploadManager -v
```

## 🗄️ **Database Integration**

### **Supabase Connection**
```python
from core.supabase_client import SupabaseClient

# Always use try-catch for database operations
try:
    client = SupabaseClient()
    result = client.store_content(content_data)
except Exception as e:
    log_error(e, "Database operation failed")
    # Continue without database (graceful degradation)
```

### **Local Database Testing**
- Tests can connect to real Supabase for integration testing
- Use `@pytest.mark.supabase` for database-dependent tests
- Mock database for unit tests to ensure speed

## 🚀 **Deployment Guidelines**

### **Comprehensive Audit Process**
**CRITICAL: Run these audits before any deployment**

#### **1. Integration Audit**
```bash
# Verify all components work together
python scripts/integration_audit.py
# Target: 90%+ integration health score
```

#### **2. UI/UX Audit**
```bash
# Verify OAuth, progress indicators, and user experience
python scripts/ui_ux_audit.py
# Target: 95%+ UI/UX quality score
```

#### **3. Basic Functionality Tests**
```bash
# Run core functionality tests
pytest tests/test_basic_functionality.py -v
# Target: All tests passing
```

### **Pre-Deployment Checklist**
- [ ] Integration audit: 90%+ score ✅ (Currently: 90.0%)
- [ ] UI/UX audit: 95%+ score ✅ (Currently: 96.9%)
- [ ] All basic tests passing ✅ (Currently: 9/9)
- [ ] Database connection verified ✅
- [ ] Environment variables set ✅
- [ ] Error handling tested ✅
- [ ] OAuth flow verified ✅
- [ ] Large file upload tested ✅
- [ ] Streaming pipeline working ✅
- [ ] Aurora UI theme active ✅
- [ ] App starts locally: `streamlit run app.py`
- [ ] No import errors in logs
- [ ] Requirements.txt is up to date
- [ ] No hardcoded secrets in code

### **Deployment-Safe Practices**
```python
# ✅ CORRECT: Environment-based configuration
import os
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    st.warning("Database not configured - running in offline mode")

# ❌ WRONG: Hardcoded values
SUPABASE_URL = "https://hardcoded-url.supabase.co"
```

### **Common Deployment Issues**
1. **Missing Dependencies**: Always update requirements.txt
2. **Import Errors**: Test all imports in clean environment
3. **Environment Variables**: Ensure all secrets are set
4. **File Paths**: Use relative paths, not absolute

## 🔍 **Debugging Guide**

### **Log Analysis**
```bash
# Check recent logs
tail -f logs/whisperforge_$(date +%Y%m%d).log

# Check error logs
tail -f logs/errors_$(date +%Y%m%d).log

# Analyze structured logs
cat logs/structured_$(date +%Y%m%d).jsonl | jq '.'
```

### **Common Issues & Solutions**

#### **502 Errors**
- **Cause**: Usually unhandled exceptions in request processing
- **Solution**: Check error logs, add try-catch blocks
- **Prevention**: Use comprehensive error handling

#### **Import Errors**
- **Cause**: Missing dependencies or circular imports
- **Solution**: Check requirements.txt, verify import order
- **Prevention**: Test in clean environment

#### **Database Connection Issues**
- **Cause**: Network issues or incorrect credentials
- **Solution**: Implement graceful fallback
- **Prevention**: Always use try-catch for database operations

#### **Memory Issues with Large Files**
- **Cause**: Loading entire file into memory
- **Solution**: Use chunking and streaming
- **Prevention**: Monitor file sizes and implement limits

## 🎨 **UI/UX Guidelines**

### **Aurora Theme Consistency**
- Use bioluminescent color scheme
- Implement smooth animations
- Maintain dark theme with glowing accents
- Ensure responsive design

### **User Experience Principles**
- **Real-time feedback**: Show progress for all operations
- **Graceful errors**: Never show raw error messages to users
- **Intuitive flow**: Guide users through the process
- **Performance**: Optimize for large file handling

## 🔐 **Security Best Practices**

### **API Key Management**
```python
# ✅ CORRECT: Environment variables
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("API key not configured")
    return

# ❌ WRONG: Hardcoded keys
api_key = "sk-hardcoded-key-here"
```

### **File Upload Security**
- Validate file types and sizes
- Sanitize file names
- Implement upload limits
- Scan for malicious content

### **Database Security**
- Use parameterized queries
- Implement proper authentication
- Validate all user inputs
- Log security events

## 📈 **Performance Optimization**

### **Large File Handling**
- Chunk files > 20MB
- Use parallel processing for chunks
- Implement progress tracking
- Clean up temporary files

### **AI API Optimization**
- Implement request caching
- Use appropriate model sizes
- Monitor token usage
- Implement rate limiting

### **Database Optimization**
- Use indexes for common queries
- Implement connection pooling
- Cache frequently accessed data
- Monitor query performance

## 🔄 **Version Control Best Practices**

### **Commit Guidelines**
- Use descriptive commit messages
- Test before committing
- Keep commits focused and small
- Include relevant documentation updates

### **Branch Strategy**
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `hotfix/*`: Critical fixes

## 📚 **Additional Resources**

### **Documentation**
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/)

### **Monitoring & Logging**
- Check `logs/` directory regularly
- Monitor application performance
- Track user engagement metrics
- Set up alerts for critical errors

---

## ⚠️ **EMERGENCY PROCEDURES**

### **If App is Down (502 Errors)**
1. Check error logs immediately
2. Identify the failing component
3. Implement graceful fallback
4. Deploy hotfix
5. Monitor recovery

### **If Database is Unavailable**
1. App should continue in offline mode
2. Show user-friendly message
3. Cache operations for later sync
4. Monitor database status

### **If AI APIs are Down**
1. Show service status to users
2. Queue requests for retry
3. Provide alternative options
4. Log service outages

---

**Remember: The goal is to build a robust, user-friendly platform that gracefully handles all edge cases while maintaining the complete WhisperForge vision.** 