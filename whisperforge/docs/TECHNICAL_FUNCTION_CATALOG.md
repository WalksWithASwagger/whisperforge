# WhisperForge: Technical Function Catalog

## 📚 COMPLETE FUNCTION & CLASS REFERENCE

### 🎯 MAIN APPLICATION FILES

---

## 📱 `app_supabase.py` - Current Main Application (Supabase-enabled)

**Purpose**: Primary Streamlit application with Supabase integration for user management and data persistence.

### Core Functions
- `run_content_pipeline(transcript, provider, model, knowledge_base=None)` - Main content generation orchestrator
- `init_supabase()` - Initialize Supabase client connection
- `show_auth_page()` - Display authentication interface
- `show_main_app()` - Main application interface with tabs
- `show_home_page()` - File upload and processing interface
- `process_audio_pipeline(audio_file)` - Handle audio file processing workflow
- `show_content_history_page()` - Display user's content generation history
- `show_settings_page()` - User settings and API key management
- `main()` - Application entry point

### Authentication Functions
- `authenticate_user_supabase(email: str, password: str) -> bool` - User login validation
- `register_user_supabase(email: str, password: str) -> bool` - New user registration

### Data Management Functions
- `get_user_api_keys_supabase() -> dict` - Retrieve user's API keys
- `update_api_key_supabase(key_name: str, key_value: str) -> bool` - Update API key
- `get_user_prompts_supabase() -> dict` - Get custom prompts
- `save_user_prompt_supabase(prompt_type: str, content: str) -> bool` - Save custom prompt
- `get_user_knowledge_base_supabase() -> dict` - Get knowledge base files
- `save_knowledge_base_file_supabase(filename: str, content: str) -> bool` - Save knowledge file
- `save_generated_content_supabase(content_data: dict) -> str` - Store generated content
- `get_user_content_history_supabase(limit: int = 20) -> list` - Get content history
- `log_pipeline_execution_supabase(pipeline_data: dict) -> bool` - Log execution metrics

---

## 📱 `app.py` - Legacy Main Application (SQLite-based)

**Purpose**: Original comprehensive Streamlit application with SQLite database, authentication, and full feature set.

### Core Application Functions
- `main()` - Main application entry point with navigation
- `show_main_page()` - Primary content generation interface
- `show_api_keys_page()` - API key management interface
- `show_login_page()` - User authentication interface
- `show_admin_page()` - Admin dashboard and user management
- `show_legal_page()` - Terms of service and privacy policy
- `show_user_config_page()` - User configuration and custom prompts

### Database Functions
- `get_db_connection()` - Get SQLite database connection
- `init_db()` - Initialize database schema
- `init_admin_user()` - Create default admin user

### Authentication & Security
- `hash_password(password)` - Hash password using SHA-256
- `create_jwt_token(user_id)` - Create JWT authentication token
- `validate_jwt_token(token)` - Validate JWT token
- `authenticate_user(email, password)` - User login validation
- `register_user(email, password)` - New user registration
- `is_admin_user()` - Check if current user is admin
- `add_security_headers()` - Add HTTP security headers

### AI Provider Integration
- `get_openai_client()` - Get configured OpenAI client
- `get_anthropic_client()` - Get configured Anthropic client
- `get_notion_client()` - Get configured Notion client
- `get_notion_database_id()` - Get Notion database ID
- `get_grok_api_key()` - Get Grok API key
- `test_notion_connection()` - Test Notion API connection

### Content Generation Pipeline
- `transcribe_audio(audio_file)` - Main audio transcription function
- `generate_wisdom(transcript, ai_provider, model, custom_prompt=None, knowledge_base=None)` - Extract key insights
- `generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None)` - Create content outline
- `generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None)` - Generate social posts
- `generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None)` - Create image descriptions
- `generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None)` - Write full article
- `process_all_content(text, ai_provider, model, knowledge_base=None)` - Run complete pipeline
- `run_full_pipeline(transcription, ai_provider, model, knowledge_base=None)` - Execute full workflow

### Audio Processing
- `chunk_audio(audio_path, target_size_mb=25)` - Split large audio files
- `transcribe_chunk(chunk_path, i, total_chunks, api_key=None)` - Transcribe audio chunk
- `transcribe_large_file(file_path)` - Handle large file transcription
- `direct_transcribe_audio(audio_file_path, api_key=None)` - Direct transcription
- `transcribe_with_whisper(file_path)` - Whisper API transcription

### Content Enhancement
- `generate_title(transcript)` - Generate content title
- `generate_summary(transcript)` - Create content summary
- `generate_short_title(text)` - Create short title
- `generate_seo_metadata(content, title)` - Generate SEO metadata
- `generate_content_tags(transcript, wisdom=None)` - Create content tags
- `estimate_token_usage(transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None)` - Estimate API costs

### Notion Integration
- `create_content_notion_entry(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None)` - Create Notion page
- `chunk_text_for_notion(text, chunk_size=1500)` - Split text for Notion
- `export_to_notion()` - Export content to Notion
- `direct_notion_save(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None)` - Direct save

### User Management
- `get_available_users()` - Get list of users
- `show_account_sidebar()` - Display account information
- `get_user_api_keys()` - Get user's API keys
- `update_usage_tracking(duration_seconds)` - Track usage statistics
- `update_api_key(key_name, key_value)` - Update API key
- `get_api_key_for_service(service_name)` - Get specific API key

### Model Management
- `get_available_openai_models()` - Get OpenAI model list
- `get_available_anthropic_models()` - Get Anthropic model list
- `get_available_grok_models()` - Get Grok model list
- `get_available_models(provider)` - Get models for provider
- `get_current_models()` - Get currently selected models

### Prompt & Knowledge Base Management
- `load_prompts()` - Load system prompts
- `configure_prompts(prompts)` - Configure prompt system
- `get_custom_prompt(user, prompt_type, users_prompts, default_prompts)` - Get user prompt
- `save_custom_prompt(user, prompt_type, prompt_content)` - Save custom prompt
- `get_prompt(prompt_type, prompts, default_prompts)` - Get prompt by type
- `save_prompt(prompt_type, prompt_content)` - Save prompt
- `load_user_knowledge_base(user)` - Load user's knowledge base
- `list_knowledge_base_files(user)` - List knowledge files
- `load_knowledge_base()` - Load knowledge base system
- `apply_prompt(text, prompt_content, provider, model, user_knowledge=None)` - Apply prompt to text

### Utility Functions
- `local_css()` - Apply custom CSS styling
- `add_production_css()` - Add production CSS
- `create_custom_header()` - Create custom header
- `load_js()` - Load JavaScript components
- `direct_anthropic_completion(prompt, api_key=None, model="claude-3-7-sonnet-20250219")` - Direct Anthropic API call

---

## 📱 `app_v2.py` - Simplified Application (Under Development)

**Purpose**: Streamlined version of the application with modular design.

### Main Functions
- `main()` - Application entry point
- `init_session_state()` - Initialize Streamlit session state
- `configure_app()` - Configure application settings
- `show_main_interface()` - Display main interface
- `show_audio_interface()` - Audio upload interface
- `show_text_interface()` - Text input interface
- `process_audio_file(uploaded_file, generate_all: bool, selected_types: list)` - Process audio
- `process_text_input(text_input: str, selected_types: list)` - Process text input
- `show_results()` - Display generation results
- `show_footer()` - Application footer

---

## 🔧 CORE MODULE CLASSES & FUNCTIONS

---

## 🏗️ `core/pipeline.py` - Content Pipeline Orchestration

### Classes
**`PipelineResult`** - Container for pipeline execution results
- `__init__(transcript, content, metadata, notion_page_id)` - Initialize result
- `get_content(content_type: str) -> Optional[str]` - Get specific content
- `has_content(content_type: str) -> bool` - Check content exists
- `to_dict() -> Dict[str, Any]` - Convert to dictionary

**`ContentPipeline`** - Main pipeline orchestrator
- `__init__(config: Config)` - Initialize pipeline with config
- `run(audio_path: Path, progress_callback: Callable = None) -> PipelineResult` - Execute pipeline
- `run_from_transcript(transcript: str, progress_callback: Callable = None) -> PipelineResult` - Run from text
- `_update_progress(message: str, progress: float)` - Update progress indicator
- `_transcribe(audio_path: Path) -> str` - Transcribe audio
- `_generate_content(transcript: str) -> Dict[str, str]` - Generate all content
- `_export_to_notion(result: PipelineResult) -> str` - Export to Notion

---

## 🎛️ `core/processors.py` - Content Processing Classes

### Classes
**`AudioProcessor`** - Audio file handling and transcription
- `__init__(ai_provider: AIProvider)` - Initialize with AI provider
- `estimate_duration(audio_path: Path) -> Optional[float]` - Get audio duration
- `should_chunk_audio(audio_path: Path) -> bool` - Check if chunking needed
- `chunk_audio(audio_path: Path) -> List[Path]` - Split audio file
- `transcribe(audio_path: Path) -> str` - Transcribe audio file
- `_transcribe_chunks(chunks: List[Path]) -> str` - Transcribe multiple chunks
- `_cleanup_chunks(chunks: List[Path])` - Clean up temporary files

**`ContentGenerator`** - Content generation orchestrator
- `__init__(ai_provider: AIProvider, cache: ContentCache = None)` - Initialize generator
- `generate_wisdom(transcript: str, custom_prompt: str = None) -> str` - Extract insights
- `generate_outline(transcript: str, wisdom: str, custom_prompt: str = None) -> str` - Create outline
- `generate_social_content(wisdom: str, outline: str, custom_prompt: str = None) -> str` - Generate social posts
- `generate_image_prompts(wisdom: str, outline: str, custom_prompt: str = None) -> str` - Create image prompts
- `generate_article(transcript: str, wisdom: str, outline: str, custom_prompt: str = None) -> str` - Write article
- `generate_all(transcript: str, selected_types: List[str] = None, custom_prompts: Dict[str, str] = None) -> Dict[str, str]` - Generate all content
- `_load_prompt_template(prompt_type: str, custom_prompt: str = None) -> str` - Load prompt template
- `_generate_with_retry(system_prompt: str, user_content: str, max_retries: int = 3) -> str` - Generate with retries

**`ContentCache`** - File-based content caching
- `__init__(cache_dir: Path = None)` - Initialize cache
- `get(transcript: str, content_type: str) -> Optional[str]` - Get cached content
- `set(transcript: str, content_type: str, content: str)` - Cache content
- `clear()` - Clear all cached content
- `_get_cache_key(content: str, content_type: str) -> str` - Generate cache key

---

## 🔌 `core/integrations.py` - External Service Integrations

### Abstract Base Classes
**`AIProvider(ABC)`** - Base class for AI providers
- `transcribe_audio(audio_path: Path) -> str` - Abstract transcription method
- `generate_completion(system_prompt: str, user_content: str, model: str = None) -> str` - Abstract completion method

### AI Provider Implementations
**`OpenAIProvider(AIProvider)`** - OpenAI integration
- `__init__(config: AIProviderConfig)` - Initialize with config
- `transcribe_audio(audio_path: Path) -> str` - Whisper transcription
- `generate_completion(system_prompt: str, user_content: str, model: str = None) -> str` - ChatGPT completion

**`AnthropicProvider(AIProvider)`** - Anthropic Claude integration
- `__init__(config: AIProviderConfig)` - Initialize with config
- `transcribe_audio(audio_path: Path) -> str` - Not supported, raises error
- `generate_completion(system_prompt: str, user_content: str, model: str = None) -> str` - Claude completion

**`GrokProvider(AIProvider)`** - Grok integration
- `__init__(config: AIProviderConfig)` - Initialize with config
- `transcribe_audio(audio_path: Path) -> str` - Not supported, raises error
- `generate_completion(system_prompt: str, user_content: str, model: str = None) -> str` - Grok completion

### Export Integrations
**`NotionExporter`** - Notion database integration
- `__init__(config: NotionConfig)` - Initialize with Notion config
- `create_page(title: str, content: Dict[str, str], metadata: Dict[str, Any] = None) -> str` - Create Notion page
- `_format_content_for_notion(content: Dict[str, str]) -> List[Dict]` - Format content blocks

### Factory Functions
- `create_ai_provider(provider_name: str, config: Config) -> AIProvider` - Create AI provider instance
- `create_notion_exporter(config: Config) -> Optional[NotionExporter]` - Create Notion exporter

---

## ⚙️ `core/config.py` - Configuration Management

### Data Classes  
**`AIProviderConfig`** - AI provider configuration
- `name: str` - Provider name
- `api_key: Optional[str]` - API key
- `base_url: Optional[str]` - Base URL
- `models: Dict[str, Any]` - Available models
- `rate_limits: Dict[str, int]` - Rate limiting settings

**`NotionConfig`** - Notion integration configuration
- `api_key: Optional[str]` - Notion API key
- `database_id: Optional[str]` - Database ID

**`Config`** - Main configuration class
- `project_root: Path` - Project root directory
- `data_dir: Path` - Data storage directory
- `prompts_dir: Path` - Prompts directory
- `temp_dir: Path` - Temporary files directory
- `openai: AIProviderConfig` - OpenAI configuration
- `anthropic: AIProviderConfig` - Anthropic configuration
- `grok: AIProviderConfig` - Grok configuration
- `notion: NotionConfig` - Notion configuration
- `audio_chunk_size_mb: int` - Audio chunking size
- `max_tokens: int` - Maximum tokens per request
- `stream_responses: bool` - Enable response streaming
- `debug_mode: bool` - Debug mode flag
- `log_level: str` - Logging level

### Class Methods
- `from_env() -> 'Config'` - Load configuration from environment variables
- `from_file(config_path: Path) -> 'Config'` - Load from file (simplified)

### Global Functions
- `get_config() -> Config` - Get global configuration instance
- `set_config(config: Config)` - Set global configuration instance

---

## 🗄️ `core/supabase_integration.py` - Supabase Database Integration

### Classes
**`SupabaseClient`** - Main Supabase integration class
- `__init__(url: str, key: str)` - Initialize Supabase client
- `authenticate(email: str, password: str) -> dict` - User authentication
- `register(email: str, password: str) -> dict` - User registration
- `get_user() -> dict` - Get current user
- `logout()` - User logout
- `get_api_keys(user_id: str) -> dict` - Get user's API keys
- `update_api_key(user_id: str, key_name: str, key_value: str) -> bool` - Update API key
- `get_custom_prompts(user_id: str) -> dict` - Get custom prompts
- `save_custom_prompt(user_id: str, prompt_type: str, content: str) -> bool` - Save prompt
- `get_knowledge_base(user_id: str) -> dict` - Get knowledge base
- `save_knowledge_base_file(user_id: str, filename: str, content: str) -> bool` - Save knowledge file
- `save_generated_content(user_id: str, content_data: dict) -> str` - Save generated content
- `get_content_history(user_id: str, limit: int = 20) -> list` - Get content history
- `log_pipeline_execution(user_id: str, pipeline_data: dict) -> bool` - Log execution

**`MCPSupabaseIntegration`** - MCP (Model Context Protocol) integration
- `__init__(project_id: str)` - Initialize with project ID
- Various MCP-specific methods for advanced database operations

---

## 🎨 `core/content_generation.py` - Content Generation Functions

### Content Generation Functions
- `generate_wisdom(transcript: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str` - Extract key insights
- `generate_outline(transcript: str, wisdom: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str` - Create content outline
- `generate_social_content(wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str` - Generate social media content
- `generate_image_prompts(wisdom: str, outline: str, ai_provider: str, model: str, custom_prompt: str = None, knowledge_base: Dict[str, str] = None) -> str` - Create image generation prompts
- `transcribe_audio(audio_file) -> str` - Transcribe audio file

---

## 🛠️ UTILITY MODULES

---

## 🔧 `core/utils.py` - Shared Utilities

### Utility Functions
- `hash_password(password: str) -> str` - Hash password using SHA-256
- Various shared utility functions for file handling, validation, etc.

---

## 🖼️ `simple_diagram_generator.py` - Image Generation Utility

### Functions
- `clean_prompt(prompt, max_length=500)` - Clean and truncate image prompt
- `generate_image(api_key, prompt, style=None, size="1024x1024", quality="auto", output_dir="output_images")` - Generate image using DALL-E
- `process_prompts_file(api_key, prompts_file, style_file=None, size="1024x1024", quality="auto", output_dir="output_images")` - Process multiple prompts
- `main()` - Command-line interface

---

## 🧪 TEST MODULES

---

## 🧪 `tests/test_notion.py` - Notion Integration Tests

### Test Functions  
- Various test functions for Notion API integration
- Test database connection and page creation
- Validate content formatting and export

---

## 🧪 `tests/test_supabase.py` - Supabase Integration Tests

### Test Functions
- Test user authentication and registration
- Test API key management
- Test content storage and retrieval
- Validate database operations

---

## 📊 FUNCTION USAGE PATTERNS

### Authentication Flow
1. `authenticate_user_supabase()` → `init_supabase()` → User session established
2. `register_user_supabase()` → Account creation → Auto-login

### Content Generation Flow
1. `transcribe_audio()` → Audio to text conversion
2. `run_content_pipeline()` → Orchestrates all generation steps
3. `generate_wisdom()` → Extract key insights
4. `generate_outline()` → Create structure
5. `generate_social_content()` / `generate_image_prompts()` / `generate_article()` → Generate specific content types
6. `save_generated_content_supabase()` → Store results

### Data Persistence Flow
1. `get_user_api_keys_supabase()` → Load user settings
2. `update_api_key_supabase()` → Save API keys
3. `get_user_prompts_supabase()` → Load custom prompts
4. `save_user_prompt_supabase()` → Save custom prompts
5. `log_pipeline_execution_supabase()` → Analytics tracking

---

## 🚨 CRITICAL FUNCTIONS FOR DEVELOPMENT

### Must Understand Functions
1. **`run_content_pipeline()`** - Core business logic orchestrator
2. **`process_audio_pipeline()`** - Main user-facing workflow
3. **`init_supabase()`** - Database connection management
4. **`authenticate_user_supabase()`** - User authentication
5. **`ContentPipeline.run()`** - Modular pipeline execution

### Entry Points
- **`app_supabase.py:main()`** - Current production entry point
- **`app.py:main()`** - Legacy application entry point
- **`app_v2.py:main()`** - Simplified application entry point

### Extension Points
- **`core/integrations.py`** - Add new AI providers
- **`core/processors.py`** - Add new content types
- **`core/pipeline.py`** - Modify generation workflow
- **`core/config.py`** - Add new configuration options

---

*This catalog provides complete reference for all functions and classes in WhisperForge. Use this for understanding code structure, finding specific functionality, and planning new features.*

**Last Updated**: June 2024  
**Total Functions**: 100+  
**Total Classes**: 15+  
**Lines of Code**: ~8,000+ across all modules** 