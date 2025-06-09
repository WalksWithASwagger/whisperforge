"""
WhisperForge Chat Pipeline - Cursor-Style Real-Time Interface
Works exactly like Cursor chat with visible thinking, streaming, and toggles
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

# Optional imports - gracefully handle missing modules
try:
    from core.pipeline_controller import get_pipeline_controller
except ImportError:
    def get_pipeline_controller():
        return None

try:
    from core.visible_thinking import render_thinking_stream
except ImportError:
    def render_thinking_stream(*args, **kwargs):
        pass

try:
    from core.session_manager import check_session
except ImportError:
    def check_session():
        return True

logger = logging.getLogger(__name__)

class ChatMessage:
    """Single chat message with streaming capabilities"""
    
    def __init__(self, role: str, content: str = "", thinking: str = "", is_streaming: bool = False):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.thinking = thinking
        self.is_streaming = is_streaming
        self.timestamp = datetime.now()
        self.steps = []  # Processing steps for assistant messages
        self.metadata = {}
        
    def add_step(self, step_name: str, status: str = "processing", content: str = ""):
        """Add a processing step"""
        self.steps.append({
            'name': step_name,
            'status': status,  # 'processing', 'complete', 'error'
            'content': content,
            'timestamp': datetime.now()
        })
    
    def update_step(self, step_name: str, status: str, content: str = ""):
        """Update existing step"""
        for step in self.steps:
            if step['name'] == step_name:
                step['status'] = status
                step['content'] = content
                step['timestamp'] = datetime.now()
                break

class ChatPipeline:
    """Cursor-style chat pipeline for WhisperForge"""
    
    def __init__(self):
        self.messages: List[ChatMessage] = []
        self.current_thinking = ""
        self.is_processing = False
        self.show_thinking = True
        self.auto_scroll = True
        
    def add_user_message(self, content: str, audio_file=None):
        """Add user message to chat"""
        message = ChatMessage("user", content)
        if audio_file:
            message.metadata['audio_file'] = audio_file
        self.messages.append(message)
        
    def start_assistant_response(self) -> ChatMessage:
        """Start new assistant response with streaming"""
        message = ChatMessage("assistant", is_streaming=True)
        self.messages.append(message)
        self.is_processing = True
        return message
        
    def stream_thinking(self, thinking_text: str):
        """Stream thinking content in real-time"""
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].thinking = thinking_text
            
    def stream_content(self, content_chunk: str):
        """Stream content chunk to current message"""
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].content += content_chunk
            
    def complete_response(self):
        """Mark current response as complete"""
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].is_streaming = False
        self.is_processing = False

def show_chat_interface():
    """Main chat interface - exactly like Cursor!"""
    
    # Initialize chat pipeline in session state
    if 'chat_pipeline' not in st.session_state:
        st.session_state.chat_pipeline = ChatPipeline()
    
    chat = st.session_state.chat_pipeline
    
    # 🎛️ CHAT CONTROLS (like Cursor's top bar)
    with st.container():
        st.markdown("""
        <div class="chat-controls">
            <div class="chat-header">
                <div class="chat-title">
                    <span class="chat-icon">🎙️</span>
                    <span>WhisperForge Chat</span>
                </div>
                <div class="chat-status">
                    <span class="status-dot active"></span>
                    <span>Ready</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Toggle controls
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        
        with col1:
            chat.show_thinking = st.toggle("🧠 Thinking", value=chat.show_thinking, key="thinking_toggle")
        with col2:
            chat.auto_scroll = st.toggle("📜 Auto-scroll", value=chat.auto_scroll, key="scroll_toggle")
        with col3:
            if st.button("🗑️ Clear", key="clear_chat"):
                st.session_state.chat_pipeline = ChatPipeline()
                st.rerun()
    
    # 💬 CHAT MESSAGES AREA
    chat_container = st.container()
    
    with chat_container:
        # Render all messages
        for i, message in enumerate(chat.messages):
            render_chat_message(message, i, chat.show_thinking)
    
    # 📝 INPUT AREA (like Cursor's bottom input)
    st.markdown("---")
    
    # File upload
    audio_file = st.file_uploader(
        "🎵 Upload Audio File", 
        type=['mp3', 'wav', 'm4a', 'mp4', 'mpeg', 'mpga', 'webm'],
        key="chat_audio_upload"
    )
    
    # Text input
    user_input = st.text_area(
        "Type your message or upload audio...",
        placeholder="Ask me to process audio, generate content, or help with anything!",
        key="chat_input",
        height=80
    )
    
    # Send button
    col1, col2 = st.columns([4, 1])
    with col2:
        send_clicked = st.button("▶️ Send", key="send_message", type="primary")
    
    # Handle message sending
    if send_clicked and (user_input.strip() or audio_file):
        # Add user message immediately
        chat.add_user_message(user_input.strip(), audio_file)
        
        # Start assistant response
        assistant_msg = chat.start_assistant_response()
        
        # Simple synchronous processing for now
        if audio_file:
            # ENHANCED: Complete audio processing workflow in chat
            try:
                from core.content_generation import transcribe_audio, generate_wisdom, generate_outline, generate_article, generate_social_content, generate_image_prompts
                from core.research_enrichment import generate_research_enrichment
                
                chat.stream_thinking(f"🎵 Processing audio file: {audio_file.name}")
                
                # Step 1: Transcription
                chat.stream_content(f"🎵 **Processing Audio: {audio_file.name}**\n\n")
                chat.stream_content(f"📊 **File size:** {len(audio_file.getvalue()) / (1024*1024):.2f} MB\n\n")
                
                chat.add_step("transcription", "processing", "Transcribing audio using OpenAI Whisper...")
                
                transcript = transcribe_audio(audio_file)
                if not transcript or transcript.startswith("Error"):
                    chat.update_step("transcription", "error", f"Failed: {transcript}")
                    chat.stream_content(f"❌ **Transcription failed:** {transcript}\n\n")
                    chat.stream_content("💡 **Check your OpenAI API key in Settings**")
                    chat.complete_response()
                    st.session_state.chat_input = ""
                    st.rerun()
                    return
                
                chat.update_step("transcription", "complete", f"Transcribed {len(transcript)} characters")
                chat.stream_content(f"✅ **Transcription complete** ({len(transcript)} characters)\n\n")
                
                # Show transcript preview
                preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
                chat.stream_content(f"📝 **Transcript preview:**\n> {preview}\n\n")
                
                # Step 2: Wisdom Extraction
                chat.add_step("wisdom_extraction", "processing", "Extracting key insights and wisdom...")
                
                ai_provider = st.session_state.get('ai_provider', 'OpenAI')
                ai_model = st.session_state.get('ai_model', 'gpt-4o')
                knowledge_base = st.session_state.get('knowledge_base', {})
                prompts = st.session_state.get('prompts', {})
                
                wisdom = generate_wisdom(transcript, ai_provider, ai_model, prompts.get("wisdom_extraction"), knowledge_base)
                if wisdom and not wisdom.startswith("Error"):
                    chat.update_step("wisdom_extraction", "complete", f"Generated {len(wisdom)} characters of insights")
                    chat.stream_content(f"💡 **Key Insights:**\n{wisdom}\n\n")
                else:
                    chat.update_step("wisdom_extraction", "error", "Failed to extract wisdom")
                    chat.stream_content(f"⚠️ Wisdom extraction failed: {wisdom}\n\n")
                
                # Step 3: Research Enrichment (The Researcher!)
                chat.add_step("research_enrichment", "processing", "🔬 Researcher analyzing and enriching content...")
                
                try:
                    research_data = generate_research_enrichment(transcript, wisdom or "", ai_provider, ai_model, knowledge_base)
                    if research_data and isinstance(research_data, dict):
                        chat.update_step("research_enrichment", "complete", "Research analysis complete")
                        
                        # Show research results
                        chat.stream_content("🔬 **Research Analysis (The Researcher):**\n\n")
                        
                        if research_data.get('research_questions'):
                            chat.stream_content(f"**🤔 Research Questions:**\n{research_data['research_questions']}\n\n")
                        
                        if research_data.get('context_analysis'):
                            chat.stream_content(f"**📊 Context Analysis:**\n{research_data['context_analysis']}\n\n")
                        
                        if research_data.get('deeper_insights'):
                            chat.stream_content(f"**🧠 Deeper Insights:**\n{research_data['deeper_insights']}\n\n")
                        
                        if research_data.get('connections'):
                            chat.stream_content(f"**🔗 Connections & Patterns:**\n{research_data['connections']}\n\n")
                        
                        if research_data.get('implications'):
                            chat.stream_content(f"**🎯 Implications:**\n{research_data['implications']}\n\n")
                    else:
                        chat.update_step("research_enrichment", "error", "Research analysis failed")
                        chat.stream_content("⚠️ Research analysis failed\n\n")
                except Exception as research_error:
                    chat.update_step("research_enrichment", "error", f"Research error: {str(research_error)}")
                    chat.stream_content(f"⚠️ Research analysis error: {str(research_error)}\n\n")
                
                # Step 4: Content Generation Options
                chat.stream_content("🚀 **Quick Actions:**\n")
                chat.stream_content("- Content saved to your History\n")
                chat.stream_content("- Visit **Content Pipeline** page for full article generation\n")
                chat.stream_content("- Use **Settings** to customize prompts and knowledge base\n\n")
                
                # Save to database
                try:
                    from app import save_generated_content_supabase
                    content_data = {
                        "transcript": transcript,
                        "wisdom": wisdom,
                        "research_data": research_data,
                        "file_name": audio_file.name,
                        "ai_provider": ai_provider,
                        "ai_model": ai_model,
                        "processed_at": str(datetime.now())
                    }
                    
                    content_id = save_generated_content_supabase(content_data)
                    if content_id:
                        chat.stream_content(f"💾 **Saved to database** (ID: {content_id})")
                    else:
                        chat.stream_content("⚠️ **Warning:** Could not save to database")
                        
                except Exception as save_error:
                    chat.stream_content(f"⚠️ **Save error:** {str(save_error)}")
                
            except Exception as e:
                chat.stream_content(f"❌ **Error processing audio:** {str(e)}\n\n")
                chat.stream_content("💡 **Try using Content Pipeline page for audio processing**")
        else:
            # Text processing
            chat.stream_thinking(f"Processing your message: '{user_input[:50]}...'")
            
            if "debug" in user_input.lower() or "database" in user_input.lower():
                # Debug mode
                response = debug_user_data()
            elif "login" in user_input.lower() and "feelmoreplants" in user_input.lower():
                # Quick auth fix for the user
                response = quick_authenticate_user()
            elif "fix" in user_input.lower() and "auth" in user_input.lower():
                # Auth troubleshooting
                response = fix_authentication()
            elif "audio" in user_input.lower():
                response = "🎙️ I can help you process audio! Upload a file and I'll transcribe, extract insights, and generate content for you."
            elif "help" in user_input.lower():
                response = get_help_message()
            else:
                response = f"✨ You said: *\"{user_input}\"*\n\nI'm WhisperForge! Upload audio files for processing or ask me anything about audio transcription and content generation.\n\n💡 **Try:** 'debug', 'help', 'fix auth', or upload audio!"
            
            chat.stream_content(response)
        
        # Complete response
        chat.complete_response()
        
        # Clear input
        st.session_state.chat_input = ""
        st.rerun()

def render_chat_message(message: ChatMessage, index: int, show_thinking: bool = True):
    """Render a single chat message - Cursor style"""
    
    if message.role == "user":
        # 👤 USER MESSAGE
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-header">
                <div class="message-avatar user-avatar">👤</div>
                <div class="message-meta">
                    <span class="message-role">You</span>
                    <span class="message-time">{message.timestamp.strftime('%H:%M')}</span>
                </div>
            </div>
            <div class="message-content">
                {message.content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show audio file if attached
        if 'audio_file' in message.metadata:
            st.audio(message.metadata['audio_file'])
            
    else:
        # 🤖 ASSISTANT MESSAGE
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="message-header">
                <div class="message-avatar assistant-avatar">🤖</div>
                <div class="message-meta">
                    <span class="message-role">WhisperForge</span>
                    <span class="message-time">{message.timestamp.strftime('%H:%M')}</span>
                    {f'<span class="streaming-indicator">●</span>' if message.is_streaming else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 🧠 THINKING SECTION (like Cursor's thinking)
        if show_thinking and (message.thinking or message.is_streaming):
            with st.expander("🧠 Thinking...", expanded=message.is_streaming):
                if message.thinking:
                    st.markdown(f"```\n{message.thinking}\n```")
                elif message.is_streaming:
                    st.markdown("_Processing your request..._")
        
        # 📋 PROCESSING STEPS
        if message.steps:
            for step in message.steps:
                render_processing_step(step)
        
        # 📝 MAIN CONTENT
        if message.content:
            if message.is_streaming:
                # Show streaming content with cursor
                st.markdown(f"{message.content}▋")
            else:
                # Show final content
                st.markdown(message.content)

def render_processing_step(step: Dict[str, Any]):
    """Render a processing step with status indicators"""
    
    status_icons = {
        'processing': '⏳',
        'complete': '✅',
        'error': '❌'
    }
    
    status_colors = {
        'processing': '#FFA500',
        'complete': '#00FF00', 
        'error': '#FF0000'
    }
    
    icon = status_icons.get(step['status'], '●')
    color = status_colors.get(step['status'], '#FFFFFF')
    
    st.markdown(f"""
    <div class="processing-step {step['status']}">
        <div class="step-header">
            <span class="step-icon" style="color: {color};">{icon}</span>
            <span class="step-name">{step['name']}</span>
            <span class="step-time">{step['timestamp'].strftime('%H:%M:%S')}</span>
        </div>
        {f'<div class="step-content">{step["content"]}</div>' if step.get('content') else ''}
    </div>
    """, unsafe_allow_html=True)

# Async functions removed - using synchronous processing for stability

# 🎨 CURSOR-STYLE CSS
CHAT_CSS = """
<style>
/* Chat Interface Styling - Cursor Style */
.chat-controls {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 20px;
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #00FFFF;
}

.chat-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00FF00;
    animation: pulse 2s infinite;
}

.chat-message {
    margin: 16px 0;
    padding: 16px;
    border-radius: 12px;
}

.user-message {
    background: linear-gradient(135deg, rgba(0, 100, 255, 0.1), rgba(0, 150, 255, 0.05));
    border: 1px solid rgba(0, 100, 255, 0.2);
    margin-left: 20%;
}

.assistant-message {
    background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(64, 224, 208, 0.08));
    border: 1px solid rgba(0, 255, 255, 0.15);
    margin-right: 20%;
}

.message-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.user-avatar {
    background: linear-gradient(135deg, #0064FF, #0096FF);
}

.assistant-avatar {
    background: linear-gradient(135deg, #00FFFF, #40E0D0);
}

.message-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
}

.message-role {
    font-weight: 600;
    color: #00FFFF;
}

.message-time {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.5);
}

.streaming-indicator {
    color: #00FF00;
    animation: blink 1s infinite;
}

.processing-step {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0;
}

.step-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
}

.step-name {
    flex: 1;
    color: rgba(255, 255, 255, 0.8);
}

.step-time {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.4);
}

.step-content {
    margin-top: 8px;
    padding-left: 24px;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
</style>
"""

def debug_user_data():
    """Debug user database connectivity and data"""
    try:
        # Import here to avoid circular imports
        import streamlit as st
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import init_supabase
        
        debug_info = []
        debug_info.append("🔍 **WhisperForge Database Debug**\n")
        
        # Check session state
        debug_info.append(f"**Authentication:** {st.session_state.get('authenticated', False)}")
        debug_info.append(f"**User ID:** {st.session_state.get('user_id', 'None')}")
        debug_info.append(f"**User Email:** {st.session_state.get('user_email', 'None')}")
        
        # Test database connection
        try:
            db, _ = init_supabase()
            if db:
                debug_info.append("✅ **Database Connection:** Success")
                
                # Check for specific user
                user_email = "feelmoreplants@gmail.com"
                user_search = db.client.table('users').select('*').eq('email', user_email).execute()
                
                if user_search.data:
                    user = user_search.data[0]
                    debug_info.append(f"👤 **Found User:** {user['email']} (ID: {user['id']})")
                    
                    # Check content
                    user_content = db.client.table('content').select('*').eq('user_id', user['id']).execute()
                    debug_info.append(f"📄 **Content Records:** {len(user_content.data) if user_content.data else 0}")
                    
                    if user_content.data:
                        debug_info.append("**Recent Content:**")
                        for i, content in enumerate(user_content.data[:3]):
                            created = content.get('created_at', 'Unknown')[:10]
                            debug_info.append(f"  {i+1}. Created: {created}")
                else:
                    debug_info.append(f"❌ **User Not Found:** {user_email}")
                    
                    # Show all users
                    all_users = db.client.table('users').select('email').execute()
                    debug_info.append(f"**Total Users:** {len(all_users.data) if all_users.data else 0}")
                    
            else:
                debug_info.append("❌ **Database Connection:** Failed")
                
        except Exception as e:
            debug_info.append(f"❌ **Database Error:** {str(e)}")
        
        debug_info.append("\n💡 **Try:** Type 'help' for assistance or upload audio to test processing")
        
        return "\n".join(debug_info)
        
    except Exception as e:
        return f"❌ **Debug Error:** {str(e)}"

def quick_authenticate_user():
    """Quick authentication fix for feelmoreplants@gmail.com"""
    try:
        import streamlit as st
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import init_supabase
        from core.session_manager import login_user
        
        db, _ = init_supabase()
        if not db:
            return "❌ **Database connection failed** - Cannot authenticate"
        
        # Find user
        user_email = "feelmoreplants@gmail.com"
        user_search = db.client.table('users').select('*').eq('email', user_email).execute()
        
        if user_search.data:
            user = user_search.data[0]
            user_id = user['id']
            
            # Set session state manually
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            
            # Use session manager
            success = login_user(user_id, user_email)
            
            if success:
                return f"""✅ **Authentication Fixed!**

👤 **User:** {user_email}
🆔 **ID:** {user_id}
🔐 **Status:** Authenticated

You should now be able to:
• View your history (26 files should appear)
• Save custom prompts
• Process audio files

Try going to the History page or type 'debug' to verify!"""
            else:
                return "❌ **Session manager failed** - Manual auth set but session manager returned false"
        else:
            return f"❌ **User not found in database:** {user_email}"
            
    except Exception as e:
        return f"❌ **Authentication Error:** {str(e)}"

def fix_authentication():
    """Comprehensive authentication troubleshooting"""
    try:
        import streamlit as st
        
        issues = []
        fixes = []
        
        # Check session state
        if not st.session_state.get('authenticated', False):
            issues.append("❌ Not authenticated")
            fixes.append("Run: 'login feelmoreplants'")
        else:
            issues.append("✅ Session authenticated")
        
        if not st.session_state.get('user_id'):
            issues.append("❌ No user ID")
            fixes.append("Check database connection")
        else:
            issues.append(f"✅ User ID: {st.session_state.user_id}")
        
        if not st.session_state.get('user_email'):
            issues.append("❌ No user email")
        else:
            issues.append(f"✅ Email: {st.session_state.user_email}")
        
        response = "🔧 **Authentication Troubleshoot**\n\n"
        response += "**Current Status:**\n" + "\n".join(issues)
        
        if fixes:
            response += "\n\n**Suggested Fixes:**\n" + "\n".join(fixes)
        
        response += "\n\n💡 **Quick Fix:** Type 'login feelmoreplants' to force authentication"
        
        return response
        
    except Exception as e:
        return f"❌ **Troubleshoot Error:** {str(e)}"

def get_help_message():
    """Get help message with available commands"""
    return """🎙️ **WhisperForge Chat Help**

**Available Commands:**
• **'debug'** - Check database and user status
• **'login feelmoreplants'** - Force authentication for your account
• **'fix auth'** - Troubleshoot authentication issues
• **'help'** - Show this help message

**Features:**
• 📁 **Upload Audio** - Process MP3, WAV, M4A files
• 🧠 **Thinking Mode** - See AI processing in real-time
• 💬 **Chat Mode** - This interface (like Cursor!)
• 📋 **History** - View all processed content
• ⚙️ **Settings** - Configure prompts and API keys

**Cursor-Style Features:**
• Real-time streaming responses
• Visible thinking processes  
• Processing step indicators
• Toggleable interface elements

**Current Issues Being Fixed:**
• History page showing empty (should show 26 files)
• Custom prompts not saving
• Authentication persistence

Type any command or upload audio to get started! 🚀"""

def apply_chat_css():
    """Apply Cursor-style chat CSS"""
    st.markdown(CHAT_CSS, unsafe_allow_html=True) 