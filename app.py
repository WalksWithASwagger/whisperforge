"""
WhisperForge - Streamlined Audio Processing App
Clean, native Streamlit implementation that actually works
"""

import streamlit as st
import os
import tempfile
import time
from datetime import datetime

# Configuration
st.set_page_config(
    page_title="WhisperForge",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Aurora CSS - Clean and Beautiful
AURORA_CSS = """
<style>
.stApp {
    background: linear-gradient(135deg, #000A0E 0%, #001419 50%, #000A0E 100%);
    font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* Aurora glow effects */
.main-title {
    text-align: center;
    font-size: 3rem;
    font-weight: 300;
    background: linear-gradient(120deg, #00FFFF, #7DF9FF, #40E0D0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
    margin-bottom: 1rem;
}

.subtitle {
    text-align: center;
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.1rem;
    margin-bottom: 3rem;
}

/* File uploader styling */
.uploadedFile {
    background: rgba(0, 255, 255, 0.05) !important;
    border: 1px solid rgba(0, 255, 255, 0.2) !important;
    border-radius: 8px !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(64, 224, 208, 0.15)) !important;
    border: 1px solid rgba(0, 255, 255, 0.3) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(64, 224, 208, 0.25)) !important;
    border-color: rgba(0, 255, 255, 0.5) !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(0, 255, 255, 0.15);
}

/* Progress bar styling */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00FFFF, #40E0D0) !important;
    border-radius: 4px !important;
}

/* Success/Error styling */
.stSuccess {
    background: rgba(0, 255, 0, 0.1) !important;
    border: 1px solid rgba(0, 255, 0, 0.3) !important;
    color: #00FF88 !important;
}

.stError {
    background: rgba(255, 100, 100, 0.1) !important;
    border: 1px solid rgba(255, 100, 100, 0.3) !important;
    color: #FF6B6B !important;
}
</style>
"""

# Database functions (simplified)
@st.cache_resource
def init_supabase():
    """Initialize Supabase client with robust error handling"""
    try:
        from supabase import create_client, Client
        
        # Try multiple sources for credentials
        url = None
        key = None
        
        # Try Streamlit secrets first
        try:
            if hasattr(st, 'secrets'):
                url = st.secrets.get("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_ANON_KEY")
        except:
            pass
        
        # Fallback to environment variables
        if not url:
            url = os.getenv("SUPABASE_URL")
        if not key:
            key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            return None, "Missing Supabase credentials in secrets or environment variables"
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return None, "Invalid Supabase URL format"
            
        client = create_client(url, key)
        
        # Test connection with a simple query
        try:
            client.table("api_keys").select("id").limit(1).execute()
        except Exception as test_error:
            return None, f"Supabase connection test failed: {str(test_error)}"
        
        return client, None
        
    except ImportError:
        return None, "Supabase Python client not installed"
    except Exception as e:
        return None, f"Supabase initialization error: {str(e)}"

# User Management Functions
def get_current_user():
    """Get current user from session state with native Streamlit"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    return st.session_state.user

def set_current_user(user_data):
    """Set current user in session state"""
    st.session_state.user = user_data

def simple_login():
    """Simple login system using native Streamlit"""
    with st.sidebar:
        st.markdown("### 🔐 Authentication")
        
        current_user = get_current_user()
        
        if current_user:
            st.success(f"✅ Logged in as: {current_user.get('email', 'User')}")
            if st.button("🚪 Logout"):
                st.session_state.user = None
                st.rerun()
            return current_user
        else:
            st.info("Please log in to access all features")
            
            # Simple email-based login for now
            email = st.text_input("📧 Email")
            if st.button("🔑 Login"):
                if email:
                    # For now, create a simple user - we'll add OAuth later
                    user_data = {
                        "id": hash(email) % 10000,  # Simple ID generation
                        "email": email,
                        "name": email.split("@")[0]
                    }
                    set_current_user(user_data)
                    st.success("✅ Logged in!")
                    st.rerun()
                else:
                    st.error("Please enter an email")
            return None

def get_api_keys(user_id=None):
    """Get API keys from database or environment"""
    api_keys = {}
    
    # If no user, use environment only
    if not user_id:
        api_keys["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        return api_keys
    
    # Try Supabase first for authenticated users
    try:
        client, error = init_supabase()
        if client and not error:
            result = client.table("api_keys").select("key_name, key_value").eq("user_id", user_id).execute()
            for item in result.data:
                api_keys[item["key_name"]] = item["key_value"]
    except Exception as e:
        st.warning(f"Database access failed: {e}")
    
    # Fallback to environment
    if not api_keys.get("openai_api_key"):
        api_keys["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    
    return api_keys

def get_user_custom_prompts(user_id):
    """Get user's custom prompts from database"""
    try:
        client, error = init_supabase()
        if not client or error:
            return {}
            
        result = client.table("user_prompts").select("prompt_type, prompt_text").eq("user_id", user_id).execute()
        
        prompts = {}
        for item in result.data:
            prompts[item["prompt_type"]] = item["prompt_text"]
        
        return prompts
    except:
        return {}

def save_user_custom_prompt(user_id, prompt_type, prompt_text):
    """Save user's custom prompt to database"""
    try:
        client, error = init_supabase()
        if not client or error:
            return False
        
        # Upsert the prompt
        result = client.table("user_prompts").upsert({
            "user_id": user_id,
            "prompt_type": prompt_type,
            "prompt_text": prompt_text
        }).execute()
        
        return bool(result.data)
    except:
        return False

def get_user_knowledge_base(user_id):
    """Get user's knowledge base files from database"""
    try:
        client, error = init_supabase()
        if not client or error:
            return []
            
        result = client.table("knowledge_base").select("*").eq("user_id", user_id).execute()
        return result.data
    except:
        return []

def save_knowledge_base_file(user_id, file_name, file_content):
    """Save knowledge base file to database"""
    try:
        client, error = init_supabase()
        if not client or error:
            return False
        
        result = client.table("knowledge_base").insert({
            "user_id": user_id,
            "file_name": file_name,
            "content": file_content,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return bool(result.data)
    except:
        return False

def delete_knowledge_base_file(user_id, file_id):
    """Delete knowledge base file"""
    try:
        client, error = init_supabase()
        if not client or error:
            return False
        
        result = client.table("knowledge_base").delete().eq("id", file_id).eq("user_id", user_id).execute()
        return bool(result.data)
    except:
        return False

def transcribe_audio_simple(audio_file, user_id=None):
    """Rock solid transcription function with bulletproof error handling"""
    try:
        # Get API key
        api_keys = get_api_keys(user_id)
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ No OpenAI API key found. Add your key to Supabase database or environment variables."
        
        # Validate file size (OpenAI limit is 25MB)
        file_size = len(audio_file.getvalue())
        if file_size > 25 * 1024 * 1024:
            return f"❌ File too large: {file_size/(1024*1024):.1f}MB. Maximum is 25MB."
        
        if file_size == 0:
            return "❌ File is empty. Please upload a valid audio file."
        
        # Reset file pointer
        audio_file.seek(0)
        
        # Get proper file extension
        file_name = audio_file.name.lower()
        if file_name.endswith(('.mp3', '.wav', '.m4a', '.flac')):
            ext = file_name.split('.')[-1]
        elif file_name.endswith(('.mp4', '.webm')):
            ext = file_name.split('.')[-1]
        else:
            ext = "mp3"  # Default fallback
        
        # Save uploaded file temporarily with correct extension
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
                temp_file.write(audio_file.read())
                temp_file_path = temp_file.name
            
            # Verify temp file was created and has content
            if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                return "❌ Failed to save audio file temporarily."
            
            # Import OpenAI and transcribe
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            with open(temp_file_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="text"
                )
            
            # Validate transcript
            if not transcript or len(transcript.strip()) == 0:
                return "❌ Transcription returned empty result. Audio may be silent or corrupted."
            
            return transcript.strip()
            
        except openai.APIError as e:
            return f"❌ OpenAI API error: {str(e)}"
        except openai.RateLimitError:
            return "❌ OpenAI rate limit exceeded. Please try again in a moment."
        except openai.AuthenticationError:
            return "❌ Invalid OpenAI API key. Please check your key in settings."
        except Exception as e:
            return f"❌ Transcription failed: {str(e)}"
        finally:
            # Always clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # Don't fail if cleanup fails
        
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

def generate_content_simple(transcript, content_type="wisdom", user_id=None):
    """Rock solid content generation with error handling"""
    try:
        # Validate input
        if not transcript or len(transcript.strip()) == 0:
            return "❌ No transcript provided for content generation."
        
        api_keys = get_api_keys(user_id)
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ No OpenAI API key found."
        
        import openai
        client = openai.OpenAI(api_key=openai_key)
        
        # Get custom prompts for user, fallback to defaults
        custom_prompts = get_user_custom_prompts(user_id) if user_id else {}
        
        default_prompts = {
            "wisdom": "Extract key insights, lessons, and wisdom from this transcript. Focus on actionable takeaways and practical lessons that readers can apply.",
            "outline": "Create a detailed, well-structured outline for an article based on this transcript. Include main sections, subsections, and key points.",
            "research": "Act as a researcher. Analyze this content and provide: 1) Related research questions, 2) Key implications, 3) Connections to broader topics, 4) Suggested further research areas."
        }
        
        # Use custom prompt if available, otherwise default
        prompt = custom_prompts.get(content_type, default_prompts.get(content_type, default_prompts["wisdom"]))
        
        # Get knowledge base context
        knowledge_base_context = ""
        if user_id:
            kb_files = get_user_knowledge_base(user_id)
            if kb_files:
                kb_content = []
                for kb_file in kb_files[:3]:  # Limit to 3 files to avoid token limits
                    kb_content.append(f"**{kb_file['file_name']}:**\n{kb_file['content'][:500]}...")
                knowledge_base_context = "\n\n**Knowledge Base Context:**\n" + "\n\n".join(kb_content)
        
        # Truncate transcript smartly - keep beginning and end
        if len(transcript) > 2500:  # Reduced to make room for knowledge base
            truncated = transcript[:1500] + "\n\n[...content truncated...]\n\n" + transcript[-1000:]
        else:
            truncated = transcript
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Transcript:\n{truncated}{knowledge_base_context}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            if not content or len(content.strip()) == 0:
                return f"❌ {content_type.title()} generation returned empty result."
            
            return content.strip()
            
        except openai.APIError as e:
            return f"❌ OpenAI API error: {str(e)}"
        except openai.RateLimitError:
            return "❌ OpenAI rate limit exceeded. Please try again in a moment."
        except openai.AuthenticationError:
            return "❌ Invalid OpenAI API key. Please check your key in settings."
        except Exception as e:
            return f"❌ {content_type.title()} generation failed: {str(e)}"
        
    except Exception as e:
        return f"❌ Unexpected error in content generation: {str(e)}"

def save_to_database(content_data, user_id=None):
    """Save processed content to database"""
    try:
        if not user_id:
            return False  # Don't save without user
            
        client, error = init_supabase()
        if not client or error:
            return False
            
        result = client.table("content").insert({
            "user_id": user_id,
            "content_data": content_data,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return bool(result.data)
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def show_history(user_id=None):
    """Show content history using native Streamlit"""
    st.markdown("### 📋 Content History")
    
    if not user_id:
        st.info("👋 Please login to view your content history")
        return
    
    try:
        client, error = init_supabase()
        if not client or error:
            st.error("Database connection failed")
            return
            
        result = client.table("content").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
        
        if not result.data:
            st.info("No content found yet. Process some audio files to see history here!")
            return
        
        for item in result.data:
            content_data = item.get("content_data", {})
            created_at = item.get("created_at", "")
            
            with st.expander(f"🎵 {content_data.get('file_name', 'Unknown file')} - {created_at[:10]}"):
                
                if content_data.get("transcript"):
                    st.markdown("**📝 Transcript:**")
                    st.text_area("", content_data["transcript"], height=100, disabled=True, key=f"transcript_{item['id']}")
                
                if content_data.get("wisdom"):
                    st.markdown("**💡 Wisdom:**")
                    st.markdown(content_data["wisdom"])
                
                if content_data.get("research"):
                    st.markdown("**🔬 Research:**")
                    st.markdown(content_data["research"])
        
    except Exception as e:
        st.error(f"Error loading history: {e}")

def main():
    """Main app - Simple and clean"""
    
    # Apply Aurora styling
    st.markdown(AURORA_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-title">⚡ WhisperForge</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Transform audio into luminous wisdom</div>', unsafe_allow_html=True)
    
    # Authentication
    current_user = simple_login()
    user_id = current_user.get("id") if current_user else None
    
    # Navigation using native tabs
    tab1, tab2 = st.tabs(["🎙️ Process Audio", "📋 History"])
    
    with tab1:
        # Show API key status in sidebar
        with st.sidebar:
            if current_user:
                st.markdown("### ⚙️ Configuration")
                api_keys = get_api_keys(user_id)
                
                # Show current status
                if api_keys.get("openai_api_key"):
                    st.success("✅ OpenAI API key loaded")
                else:
                    st.error("❌ No OpenAI API key")
                    st.markdown("Add your key to Supabase or environment variables")
                
                # Custom Prompts Section
                st.markdown("---")
                st.markdown("### 🎯 Custom Prompts")
                
                with st.expander("✏️ Edit Prompts"):
                    prompt_type = st.selectbox(
                        "Select prompt type:",
                        ["wisdom", "outline", "research"],
                        help="Choose which prompt to customize"
                    )
                    
                    # Get current custom prompts
                    custom_prompts = get_user_custom_prompts(user_id)
                    current_prompt = custom_prompts.get(prompt_type, "")
                    
                    # Show default for reference
                    default_prompts = {
                        "wisdom": "Extract key insights, lessons, and wisdom from this transcript. Focus on actionable takeaways and practical lessons that readers can apply.",
                        "outline": "Create a detailed, well-structured outline for an article based on this transcript. Include main sections, subsections, and key points.",
                        "research": "Act as a researcher. Analyze this content and provide: 1) Related research questions, 2) Key implications, 3) Connections to broader topics, 4) Suggested further research areas."
                    }
                    
                    st.markdown(f"**Default {prompt_type} prompt:**")
                    st.text_area("", default_prompts[prompt_type], height=100, disabled=True, key=f"default_{prompt_type}")
                    
                    # Custom prompt editor
                    new_prompt = st.text_area(
                        f"Your custom {prompt_type} prompt:",
                        value=current_prompt,
                        height=150,
                        placeholder=f"Enter your custom {prompt_type} prompt here...",
                        key=f"custom_{prompt_type}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save", key=f"save_{prompt_type}"):
                            if save_user_custom_prompt(user_id, prompt_type, new_prompt):
                                st.success("✅ Prompt saved!")
                            else:
                                st.error("❌ Failed to save")
                    
                    with col2:
                        if st.button("🔄 Reset", key=f"reset_{prompt_type}"):
                                                         if save_user_custom_prompt(user_id, prompt_type, ""):
                                 st.success("✅ Reset to default!")
                             else:
                                 st.error("❌ Failed to reset")
                
                # Knowledge Base Section
                st.markdown("---")
                st.markdown("### 📚 Knowledge Base")
                
                with st.expander("📁 Manage Files"):
                    # Upload new knowledge base file
                    uploaded_kb_file = st.file_uploader(
                        "Upload knowledge base file:",
                        type=['txt', 'md', 'pdf'],
                        help="Upload text files to provide context for AI generation"
                    )
                    
                    if uploaded_kb_file:
                        if st.button("💾 Save to Knowledge Base"):
                            try:
                                # Read file content
                                if uploaded_kb_file.type == "application/pdf":
                                    st.warning("PDF support coming soon. Please use .txt or .md files.")
                                else:
                                    content = uploaded_kb_file.read().decode('utf-8')
                                    if save_knowledge_base_file(user_id, uploaded_kb_file.name, content):
                                        st.success("✅ File saved to knowledge base!")
                                    else:
                                        st.error("❌ Failed to save file")
                            except Exception as e:
                                st.error(f"Error reading file: {e}")
                    
                    # Show existing knowledge base files
                    kb_files = get_user_knowledge_base(user_id)
                    if kb_files:
                        st.markdown("**Your Knowledge Base Files:**")
                        for kb_file in kb_files:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(f"📄 {kb_file['file_name']}")
                            with col2:
                                if st.button("🗑️", key=f"delete_{kb_file['id']}", help="Delete file"):
                                    if delete_knowledge_base_file(user_id, kb_file['id']):
                                        st.success("✅ File deleted!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete")
                    else:
                        st.info("No knowledge base files yet. Upload some to provide context for AI generation.")
        
        # Main interface
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # File upload
            uploaded_file = st.file_uploader(
                "🎵 Drop audio file here",
                type=['mp3', 'wav', 'm4a', 'flac', 'mp4', 'webm'],
                help="Max 25MB • Supports MP3, WAV, M4A, FLAC, MP4, WEBM"
            )
            
            if uploaded_file:
                # Show file info
                file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.info(f"📊 **{uploaded_file.name}** ({file_size:.1f} MB)")
                
                # Audio player
                st.audio(uploaded_file.getvalue())
                
                # Process button
                if st.button("⚡ Process Audio", type="primary", use_container_width=True):
                    
                    # Transcription
                    with st.status("🎙️ Transcribing audio...", expanded=True) as status:
                        transcript = transcribe_audio_simple(uploaded_file, user_id)
                        
                        if transcript.startswith("❌"):
                            st.error(transcript)
                            status.update(label="❌ Transcription failed", state="error")
                        else:
                            st.success(f"✅ Transcribed {len(transcript)} characters")
                            status.update(label="✅ Transcription complete", state="complete")
                    
                    # Show results outside of status context to avoid nesting issues
                    if not transcript.startswith("❌"):
                        # Show transcript
                        st.markdown("### 📝 Transcript")
                        st.text_area("", transcript, height=200, disabled=True, key="main_transcript")
                        
                        # Content generation tabs
                        wisdom_tab, outline_tab, research_tab = st.tabs(["💡 Wisdom", "📋 Outline", "🔬 Research"])
                        
                        with wisdom_tab:
                            with st.spinner("Extracting wisdom..."):
                                wisdom = generate_content_simple(transcript, "wisdom", user_id)
                                st.markdown(wisdom)
                        
                        with outline_tab:
                            with st.spinner("Creating outline..."):
                                outline = generate_content_simple(transcript, "outline", user_id)
                                st.markdown(outline)
                        
                        with research_tab:
                            with st.spinner("Generating research insights..."):
                                research = generate_content_simple(transcript, "research", user_id)
                                st.markdown(research)
                        
                        # Save to database
                        content_data = {
                            "transcript": transcript,
                            "wisdom": wisdom,
                            "outline": outline,
                            "research": research,
                            "file_name": uploaded_file.name,
                            "processed_at": datetime.now().isoformat()
                        }
                        
                        if save_to_database(content_data, user_id):
                            st.success("💾 Content saved to database!")
                        else:
                            if user_id:
                                st.warning("⚠️ Could not save to database")
                            else:
                                st.info("💡 Login to save your content history")
    
    with tab2:
        show_history(user_id)

if __name__ == "__main__":
    main() 