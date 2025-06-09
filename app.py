"""
WhisperForge - Streamlined Audio Processing App
Clean, native Streamlit implementation that actually works
"""

import streamlit as st

# MUST BE FIRST - Configure page before any other Streamlit commands
st.set_page_config(
    page_title="WhisperForge",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import tempfile
import time
from datetime import datetime
import hashlib
import json
from io import BytesIO

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

# Database functions with enhanced logging
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
        except Exception:
            pass
        
        # Fallback to environment variables
        if not url:
            url = os.getenv("SUPABASE_URL")
        if not key:
            key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            error_msg = f"Missing Supabase credentials - URL: {bool(url)}, KEY: {bool(key)}"
            return None, error_msg
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            error_msg = f"Invalid Supabase URL format: {url}"
            return None, error_msg
            
        client = create_client(url, key)
        
        # Test connection with a simple query
        try:
            result = client.table("api_keys").select("id").limit(1).execute()
            return client, None
        except Exception as test_error:
            error_msg = f"Supabase connection test failed: {str(test_error)}"
            return None, error_msg
        
    except ImportError as e:
        error_msg = f"Supabase Python client not installed: {e}"
        return None, error_msg
    except Exception as e:
        error_msg = f"Supabase initialization error: {str(e)}"
        return None, error_msg

# User Management Functions
def get_current_user():
    """Get current user from session state with native Streamlit"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    return st.session_state.user

def set_current_user(user_data):
    """Set current user in session state"""
    st.session_state.user = user_data

def supabase_oauth_login():
    """Supabase OAuth login with Google"""
    try:
        client, error = init_supabase()
        if not client or error:
            return None, "Database connection failed"
        
        # This would integrate with Supabase Auth
        # For now, we'll use a simplified version
        return None, "OAuth integration ready for Supabase Auth setup"
    except:
        return None, "OAuth error"

def simple_login():
    """Enhanced login system with OAuth option"""
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
            
            # Login tabs
            login_tab1, login_tab2 = st.tabs(["📧 Email", "🔗 OAuth"])
            
            with login_tab1:
                # Simple email-based login
                email = st.text_input("📧 Email")
                if st.button("🔑 Login with Email"):
                    if email:
                        # Create user account or login
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
            
            with login_tab2:
                # OAuth options
                st.markdown("**OAuth Login Options:**")
                
                if st.button("🔗 Login with Google", disabled=True):
                    st.info("Google OAuth integration ready for Supabase Auth setup")
                
                if st.button("🔗 Login with GitHub", disabled=True):
                    st.info("GitHub OAuth integration ready for Supabase Auth setup")
                
                st.markdown("*OAuth providers will be enabled with Supabase Auth configuration*")
            
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

def show_history():
    """Show WhisperForge content library"""
    st.markdown("### 📚 Your WhisperForge Library")
    
    user_id = get_current_user()
    if not user_id:
        st.info("🔐 Login to see your content library")
        return
    
    try:
        client, error = init_supabase()
        if not client or error:
            st.error("Database connection failed")
            return
            
        result = client.table("content").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
        
        if not result.data:
            st.info("No content yet. Upload audio to create your first WhisperForge magic!")
            return
        
        for item in result.data:
            content_data = item.get("content_data", {})
            created_at = item.get("created_at", "")
            
            with st.expander(f"🎵 {content_data.get('file_name', 'Unknown file')} - {created_at[:10]}"):
                
                # Full content tabs like in the pipeline
                if any(content_data.get(key) for key in ['wisdom', 'outline', 'article', 'social_content', 'image_prompts']):
                    wisdom_tab, outline_tab, article_tab, social_tab, research_tab, prompts_tab = st.tabs([
                        "💡 Wisdom", "📋 Outline", "📝 Article", "📱 Social", "🔬 Research", "🎨 Prompts"
                    ])
                    
                    with wisdom_tab:
                        st.markdown(content_data.get('wisdom', 'No wisdom content available'))
                    
                    with outline_tab:
                        st.markdown(content_data.get('outline', 'No outline content available'))
                    
                    with article_tab:
                        st.markdown(content_data.get('article', 'No article content available'))
                    
                    with social_tab:
                        st.markdown(content_data.get('social_content', 'No social content available'))
                    
                    with research_tab:
                        research_data = content_data.get('research_data', {})
                        if research_data.get('entities'):
                            display_research_enrichment(research_data)
                        else:
                            st.info("No research enrichment available")
                    
                    with prompts_tab:
                        st.markdown(content_data.get('image_prompts', 'No image prompts available'))
                
                else:
                    # Fallback for older content format
                    if content_data.get("transcript"):
                        st.markdown("**📝 Transcript:**")
                        st.text_area("", content_data["transcript"], height=100, disabled=True, key=f"transcript_{item['id']}")
                    
                    if content_data.get("research"):
                        st.markdown("**🔬 Legacy Research:**")
                        st.markdown(content_data["research"])
        
    except Exception as e:
        st.error(f"Error loading history: {e}")

# ============================================================================
# VISIBLE THINKING SYSTEM 
# ============================================================================

class VisibleThinking:
    """Kris-tone AI thinking bubbles during processing"""
    
    def __init__(self):
        if "thinking_bubbles" not in st.session_state:
            st.session_state.thinking_bubbles = []
    
    def add_thought(self, text: str, mood: str = "info"):
        """Add a Kris-tone thought bubble"""
        if len(text) > 80:
            text = text[:77] + "..."
            
        bubble = {
            "text": text,
            "mood": mood,
            "time": time.time(),
            "emoji": {
                "info": "🧠",
                "processing": "⚡", 
                "discovery": "✨",
                "success": "✅",
                "research": "🔍"
            }.get(mood, "🧠")
        }
        
        st.session_state.thinking_bubbles.append(bubble)
        
        # Keep only last 4 bubbles
        if len(st.session_state.thinking_bubbles) > 4:
            st.session_state.thinking_bubbles = st.session_state.thinking_bubbles[-4:]
    
    def render_stream(self):
        """Show the thinking bubble stream"""
        if not st.session_state.thinking_bubbles:
            return
            
        with st.container():
            for bubble in st.session_state.thinking_bubbles[-3:]:  # Show last 3
                mood_colors = {
                    "info": "#00D2FF",       # Aurora Cyan
                    "processing": "#00D2FF", # Aurora Cyan  
                    "discovery": "#A855F7",  # Purple
                    "success": "#10B981",    # Green
                    "research": "#F59E0B"    # Amber
                }
                
                color = mood_colors.get(bubble["mood"], "#00D2FF")
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {color}15, {color}25);
                    border-left: 3px solid {color};
                    padding: 8px 12px;
                    border-radius: 8px;
                    margin: 4px 0;
                    font-size: 0.9em;
                    color: #E0E0E0;
                    animation: fadeIn 0.5s ease-in;
                ">
                    {bubble["emoji"]} {bubble["text"]}
                </div>
                """, unsafe_allow_html=True)

# Global thinking instance
thinking = VisibleThinking()

# ============================================================================
# COMPLETE CONTENT PIPELINE
# ============================================================================

def process_audio_pipeline(uploaded_file):
    """Process audio with full WhisperForge pipeline"""
    user_id = get_current_user()
    
    if not user_id:
        st.error("Please log in to process audio")
        return
    
    thinking.add_thought("⚡ Starting the content pipeline...", "processing")
    
    # Step 1: Transcription
    with st.status("🎙️ Transcribing audio...", expanded=True) as status:
        thinking.add_thought("🧠 Converting your speech to text...", "processing")
        transcript = transcribe_audio_simple(uploaded_file, user_id)
        
        if transcript.startswith("❌"):
            st.error(transcript)
            status.update(label="❌ Transcription failed", state="error")
            return
        
        st.success(f"✅ Transcribed {len(transcript)} characters")
        status.update(label="✅ Transcription complete", state="complete")
        thinking.add_thought("✅ Got your words! Now for the magic...", "success")
    
    # Step 2: Research Enrichment
    thinking.add_thought("🔍 Finding brilliant supporting research...", "research")
    research_data = generate_research_enrichment(transcript)
    
    # Step 3: Generate All Content
    st.markdown("## 🎉 Your WhisperForge Results")
    
    # Show transcript first
    with st.expander("📝 Full Transcript", expanded=False):
        st.text_area("", transcript, height=300, disabled=True)
    
    # Content tabs with everything
    wisdom_tab, outline_tab, article_tab, social_tab, research_tab, prompts_tab = st.tabs([
        "💡 Wisdom", "📋 Outline", "📝 Article", "📱 Social", "🔬 Research", "🎨 Prompts"
    ])
    
    with wisdom_tab:
        thinking.add_thought("✨ Extracting pure wisdom from your content...", "discovery")
        wisdom = generate_content_simple(transcript, "wisdom", user_id)
        st.markdown(wisdom)
    
    with outline_tab:
        thinking.add_thought("⚡ Crafting the perfect structure...", "processing")
        outline = generate_content_simple(transcript, "outline", user_id)
        st.markdown(outline)
    
    with article_tab:
        thinking.add_thought("📝 Writing a full article in your voice...", "processing")
        article = generate_article_content(transcript, user_id)
        st.markdown(article)
    
    with social_tab:
        thinking.add_thought("📱 Creating social media gold...", "discovery")
        social_content = generate_social_content(transcript, user_id)
        st.markdown(social_content)
    
    with research_tab:
        if research_data.get("entities"):
            thinking.add_thought("🔍 Here's your research enrichment!", "research")
            display_research_enrichment(research_data)
        else:
            st.info("No specific entities found for research enrichment")
    
    with prompts_tab:
        thinking.add_thought("🎨 Generating vivid image prompts...", "discovery")
        image_prompts = generate_image_prompts(transcript, user_id)
        st.markdown(image_prompts)
    
    # Save everything to database
    thinking.add_thought("💾 Saving everything to your library...", "success")
    content_data = {
        "transcript": transcript,
        "wisdom": wisdom,
        "outline": outline,
        "article": article,
        "social_content": social_content,
        "image_prompts": image_prompts,
        "research_data": research_data,
        "file_name": uploaded_file.name,
        "processed_at": datetime.now().isoformat()
    }
    
    if save_to_database(content_data, user_id):
        thinking.add_thought("✅ All done! Your content is ready to shine!", "success")
        st.balloons()
    else:
        st.warning("⚠️ Could not save to database")

def generate_article_content(transcript: str, user_id: str) -> str:
    """Generate a full 1000+ word article"""
    try:
        api_keys = get_api_keys(user_id)
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ OpenAI API key not found"
        
        client = OpenAI(api_key=openai_key)
        
        prompt = f"""Based on this transcript, write a comprehensive 1000+ word article that:

1. Starts with a compelling hook
2. Develops the main ideas with depth and insight
3. Includes practical takeaways and actionable advice
4. Ends with a strong conclusion
5. Uses engaging, conversational tone

Transcript:
{transcript[:3000]}

Write a complete, ready-to-publish article:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error generating article: {str(e)}"

def generate_social_content(transcript: str, user_id: str) -> str:
    """Generate social media posts for multiple platforms"""
    try:
        api_keys = get_api_keys(user_id)
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ OpenAI API key not found"
        
        client = OpenAI(api_key=openai_key)
        
        prompt = f"""Based on this transcript, create 5 engaging social media posts optimized for different platforms:

1. **Twitter/X** (280 characters) - Punchy, includes hashtags
2. **LinkedIn** (Professional tone, 150-200 words)  
3. **Instagram** (Visual storytelling, 125 words + hashtags)
4. **Facebook** (Conversational, 100-150 words)
5. **TikTok/YouTube Shorts** (Hook + key points, 75 words)

Transcript:
{transcript[:2000]}

Format each post clearly with platform labels:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.8
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error generating social content: {str(e)}"

def generate_image_prompts(transcript: str, user_id: str) -> str:
    """Generate vivid AI image prompts"""
    try:
        api_keys = get_api_keys(user_id)
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ OpenAI API key not found"
        
        client = OpenAI(api_key=openai_key)
        
        prompt = f"""Based on this transcript, create 5-7 vivid, detailed AI image generation prompts that visually represent the key concepts and themes.

Each prompt should be:
- Highly detailed and specific
- Visually compelling
- Include style references (photographic, digital art, etc.)
- Ready to use in AI image generators like Midjourney or DALL-E

Transcript:
{transcript[:2000]}

Generate detailed image prompts:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error generating image prompts: {str(e)}"

def generate_research_enrichment(transcript: str) -> dict:
    """Generate research enrichment with entities and links"""
    try:
        # Extract key entities/topics
        entities = extract_research_entities(transcript)
        
        # Generate supporting research for each entity
        enriched_entities = []
        for entity in entities[:3]:  # Limit to top 3
            research = generate_entity_research(entity)
            if research:
                enriched_entities.append(research)
        
        return {
            "entities": enriched_entities,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e), "entities": []}

def extract_research_entities(transcript: str) -> list:
    """Extract key entities for research"""
    try:
        # Use OpenAI to extract entities
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""Analyze this transcript and extract 3-5 key entities that would benefit from research links.

Focus on:
- People (experts, thought leaders)
- Organizations/Companies
- Concepts/Theories
- Technologies/Methods

Return as JSON array: ["Entity 1", "Entity 2", "Entity 3"]

Transcript: {transcript[:1500]}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        entities_text = response.choices[0].message.content
        
        # Try to parse JSON
        import re
        json_match = re.search(r'\[(.*?)\]', entities_text)
        if json_match:
            entities_str = json_match.group(1)
            entities = [e.strip(' "') for e in entities_str.split(',')]
            return entities[:3]
        
        return []
        
    except Exception:
        return []

def generate_entity_research(entity: str) -> dict:
    """Generate research data for an entity"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""For the entity "{entity}", provide:

1. A brief "why this matters" explanation (2-3 sentences)
2. Suggest 2-3 types of authoritative sources to research
3. Key search terms for further research

Entity: {entity}

Respond in this format:
WHY IT MATTERS: [explanation]
RESEARCH SOURCES: [source types] 
SEARCH TERMS: [terms]"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        result = response.choices[0].message.content
        
        return {
            "name": entity,
            "research_guidance": result
        }
        
    except Exception:
        return None

def display_research_enrichment(research_data: dict):
    """Display research enrichment results"""
    st.markdown("### 🔍 Research Enrichment")
    
    for entity in research_data.get("entities", []):
        with st.expander(f"🔬 Research: {entity['name']}"):
            st.markdown(entity.get("research_guidance", "No research guidance available"))

def show_sidebar_features():
    """Show custom prompts and knowledge base in sidebar"""
    current_user = get_current_user()
    user_id = current_user
    
    if not user_id:
        return
    
    # Custom Prompts
    st.markdown("### 🎯 Custom Prompts")
    with st.expander("✏️ Customize AI"):
        st.info("Personalize how AI processes your content")
        if st.button("🔧 Configure Prompts"):
            st.info("Prompt customization coming in next update!")
    
    # Knowledge Base  
    st.markdown("### 📚 Knowledge Base")
    with st.expander("📁 Add Context"):
        uploaded_kb = st.file_uploader("Upload context files", type=['txt', 'md'])
        if uploaded_kb and st.button("💾 Add to KB"):
            st.success("File added! (Feature completing soon)")
    
    # OAuth Integration
    st.markdown("### 🔗 Connect Accounts")
    with st.expander("🌐 Integrations"):
        col1, col2 = st.columns(2)
        with col1:
            st.button("📊 Notion", disabled=True, help="Coming soon")
        with col2:
            st.button("🐦 Twitter", disabled=True, help="Coming soon")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main app - Simple and clean"""
    # Add Aurora CSS
    st.markdown("""
    <style>
    :root {
        --aurora-primary: #00D2FF;
        --aurora-secondary: #10B981;
        --aurora-tertiary: #A855F7;
        --aurora-bg: #0B1426;
        --aurora-surface: #1E293B;
        --aurora-text: #E2E8F0;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--aurora-bg) 0%, #0F172A 50%, var(--aurora-bg) 100%);
        color: var(--aurora-text);
    }
    
    .aurora-header {
        background: linear-gradient(135deg, var(--aurora-primary)20, var(--aurora-tertiary)20);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid var(--aurora-primary)30;
    }
    
    .aurora-card {
        background: linear-gradient(135deg, var(--aurora-surface)90, var(--aurora-primary)10);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid var(--aurora-primary)30;
        margin-bottom: 1rem;
    }
    
    .thinking-container {
        background: linear-gradient(135deg, var(--aurora-surface)50, var(--aurora-primary)5);
        border: 1px solid var(--aurora-primary)20;
        border-radius: 0.75rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="aurora-header">
        <h1>🎙️ WhisperForge</h1>
        <p>Upload audio → Watch AI think → Get everything you need</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar authentication
    with st.sidebar:
        st.markdown("### 🔐 Authentication")
        current_user = get_current_user()
        
        if not current_user:
            simple_login()
            st.stop()
        else:
            st.success(f"✅ Logged in as: {current_user}")
            if st.button("🚪 Logout"):
                set_current_user(None)
                st.rerun()
    
    # Show thinking stream at top
    with st.container():
        st.markdown('<div class="thinking-container">', unsafe_allow_html=True)
        thinking.render_stream()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="aurora-card">', unsafe_allow_html=True)
        st.markdown("### 🎵 Upload Audio")
        
        uploaded_file = st.file_uploader(
            "Drop your audio file here",
            type=["mp3", "wav", "m4a", "mp4", "webm", "ogg"],
            help="Supported formats: MP3, WAV, M4A, MP4, WebM, OGG"
        )
        
        if uploaded_file:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            
            # Add thinking bubble
            thinking.add_thought("🧠 Got your audio! This looks interesting...", "info")
            
            # Process button
            if st.button("🚀 Process with WhisperForge", type="primary"):
                process_audio_pipeline(uploaded_file)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        show_sidebar_features()
    
    # Show history
    st.markdown("---")
    show_history()

if __name__ == "__main__":
    main() 