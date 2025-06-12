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
    """Initialize Supabase client"""
    try:
        from supabase import create_client, Client
        url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            return None, "Missing Supabase credentials"
            
        client = create_client(url, key)
        return client, None
    except Exception as e:
        return None, str(e)

def get_api_keys():
    """Get API keys from database or environment"""
    api_keys = {}
    
    # Try Supabase first
    try:
        client, error = init_supabase()
        if client and not error:
            result = client.table("api_keys").select("key_name, key_value").eq("user_id", 3).execute()
            for item in result.data:
                api_keys[item["key_name"]] = item["key_value"]
    except:
        pass
    
    # Fallback to environment
    if not api_keys.get("openai_api_key"):
        api_keys["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    
    return api_keys

def transcribe_audio_simple(audio_file):
    """Simple, working transcription function"""
    try:
        # Get API key
        api_keys = get_api_keys()
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ No OpenAI API key found. Please add it in the sidebar."
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_file.read())
            temp_file_path = temp_file.name
        
        # Import and use OpenAI
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            with open(temp_file_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            
            # Clean up
            os.unlink(temp_file_path)
            
            return transcript.text
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            return f"❌ Transcription failed: {str(e)}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_content_simple(transcript, content_type="wisdom"):
    """Simple content generation"""
    try:
        api_keys = get_api_keys()
        openai_key = api_keys.get("openai_api_key")
        
        if not openai_key:
            return "❌ No OpenAI API key found."
        
        import openai
        client = openai.OpenAI(api_key=openai_key)
        
        prompts = {
            "wisdom": "Extract key insights, lessons, and wisdom from this transcript. Focus on actionable takeaways.",
            "outline": "Create a detailed outline for an article based on this transcript.",
            "research": "Analyze this content and suggest related research topics, questions, and implications."
        }
        
        prompt = prompts.get(content_type, prompts["wisdom"])
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Transcript: {transcript[:3000]}..."}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Content generation failed: {str(e)}"

def save_to_database(content_data):
    """Save processed content to database"""
    try:
        client, error = init_supabase()
        if not client or error:
            return False
            
        result = client.table("content").insert({
            "user_id": 3,
            "content_data": content_data,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return bool(result.data)
    except:
        return False

def main():
    """Main app - Simple and clean"""
    
    # Apply Aurora styling
    st.markdown(AURORA_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-title">⚡ WhisperForge</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Transform audio into luminous wisdom</div>', unsafe_allow_html=True)
    
    # Sidebar for API key
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_keys = get_api_keys()
        
        # Show current status
        if api_keys.get("openai_api_key"):
            st.success("✅ OpenAI API key loaded")
        else:
            st.error("❌ No OpenAI API key")
            st.markdown("Add your key to Supabase or environment variables")
    
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
                    transcript = transcribe_audio_simple(uploaded_file)
                    
                    if transcript.startswith("❌"):
                        st.error(transcript)
                        status.update(label="❌ Transcription failed", state="error")
                    else:
                        st.success(f"✅ Transcribed {len(transcript)} characters")
                        status.update(label="✅ Transcription complete", state="complete")
                        
                        # Show transcript
                        with st.expander("📝 Transcript", expanded=True):
                            st.text_area("", transcript, height=200, disabled=True)
                        
                        # Content generation tabs
                        tab1, tab2, tab3 = st.tabs(["💡 Wisdom", "📋 Outline", "🔬 Research"])
                        
                        with tab1:
                            with st.spinner("Extracting wisdom..."):
                                wisdom = generate_content_simple(transcript, "wisdom")
                                st.markdown(wisdom)
                        
                        with tab2:
                            with st.spinner("Creating outline..."):
                                outline = generate_content_simple(transcript, "outline")
                                st.markdown(outline)
                        
                        with tab3:
                            with st.spinner("Generating research insights..."):
                                research = generate_content_simple(transcript, "research")
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
                        
                        if save_to_database(content_data):
                            st.success("💾 Content saved to database!")
                        else:
                            st.warning("⚠️ Could not save to database")

if __name__ == "__main__":
    main() 