# WhisperForge Simple - Clean, Focused Audio Content Platform
import streamlit as st
import os
import tempfile
import time
from datetime import datetime
from typing import Dict, Optional

# Essential imports only
from dotenv import load_dotenv
load_dotenv()

# Page config first
st.set_page_config(
    page_title="WhisperForge",
    page_icon="🌌",
    layout="wide"
)

# Core imports
from core.content_generation import transcribe_audio, generate_wisdom, generate_outline, generate_article, generate_social_content, editor_critique
from core.research_enrichment import generate_research_enrichment
from core.styling import apply_aurora_theme, create_aurora_header, create_aurora_progress_card, create_aurora_step_card, AuroraComponents
from core.supabase_integration import get_supabase_client

# Apply beautiful theme
apply_aurora_theme()

# === NOTION INTEGRATION ===
def create_notion_page(title: str, content_data: Dict[str, str]) -> Optional[str]:
    """Create a Notion page with WhisperForge content"""
    try:
        from notion_client import Client
        
        api_key = os.getenv("NOTION_API_KEY")
        database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not api_key or not database_id:
            st.warning("⚠️ Notion not configured. Set NOTION_API_KEY and NOTION_DATABASE_ID to auto-publish.")
            return None
        
        client = Client(auth=api_key)
        
        # Build content blocks
        children = []
        
        # Add summary callout if wisdom exists
        if content_data.get('wisdom'):
            children.append({
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content_data['wisdom'][:2000]}}],
                    "color": "purple_background",
                    "icon": {"type": "emoji", "emoji": "💡"}
                }
            })
        
        # Add content sections as toggles
        sections = [
            ("📝 Transcript", content_data.get('transcript')),
            ("💡 Wisdom", content_data.get('wisdom')),
            ("🔍 Research Links", content_data.get('research')),
            ("📋 Outline", content_data.get('outline')),
            ("📰 Article", content_data.get('article')),
            ("📱 Social Content", content_data.get('social_content'))
        ]
        
        for section_title, section_content in sections:
            if section_content:
                # Handle research data specially
                if section_title == "🔍 Research Links" and isinstance(section_content, dict):
                    research_children = []
                    entities = section_content.get('entities', [])
                    
                    if entities:
                        for entity in entities[:5]:  # Limit entities
                            entity_name = entity.get('name', 'Unknown Entity')
                            why_matters = entity.get('why_matters', 'No description available')
                            links = entity.get('links', [])
                            
                            # Entity header
                            research_children.append({
                                "type": "heading_3",
                                "heading_3": {
                                    "rich_text": [{"type": "text", "text": {"content": entity_name}}]
                                }
                            })
                            
                            # Why it matters
                            research_children.append({
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": why_matters}}]
                                }
                            })
                            
                            # Links
                            for link in links[:3]:  # Limit links
                                link_title = link.get('title', 'Link')
                                link_url = link.get('url', '#')
                                link_desc = link.get('description', '')
                                is_gem = link.get('is_gem', False)
                                
                                gem_icon = "💎 " if is_gem else "🔗 "
                                research_children.append({
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {"content": f"{gem_icon}{link_title}: "}},
                                            {"type": "text", "text": {"content": link_desc}, "annotations": {"italic": True}}
                                        ]
                                    }
                                })
                    else:
                        research_children.append({
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": "No research entities found."}}]
                            }
                        })
                    
                    children.append({
                        "type": "toggle",
                        "toggle": {
                            "rich_text": [{"type": "text", "text": {"content": section_title}}],
                            "children": research_children
                        }
                    })
                else:
                    # Handle regular text content
                    if isinstance(section_content, str):
                        # Chunk content for Notion's limits
                        chunks = [section_content[i:i+1800] for i in range(0, len(section_content), 1800)]
                        
                        children.append({
                            "type": "toggle",
                            "toggle": {
                                "rich_text": [{"type": "text", "text": {"content": section_title}}],
                                "children": [
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                        }
                                    } for chunk in chunks[:5]  # Limit chunks
                                ]
                            }
                        })
        
        # Add metadata
        children.extend([
            {"type": "divider", "divider": {}},
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Created with "}},
                        {"type": "text", "text": {"content": "WhisperForge"}, 
                         "annotations": {"bold": True, "color": "purple"}}
                    ]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                }
            }
        ])
        
        # Create the page
        response = client.pages.create(
            parent={"database_id": database_id},
            icon={"type": "emoji", "emoji": "🌌"},
            properties={
                "Name": {"title": [{"text": {"content": title[:100]}}]}
            },
            children=children[:50]  # Limit total blocks
        )
        
        if response and 'id' in response:
            page_id = response['id']
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            return page_url
        
        return None
        
    except ImportError:
        st.warning("⚠️ Install notion-client to enable Notion publishing: pip install notion-client")
        return None
    except Exception as e:
        st.error(f"❌ Notion publishing failed: {str(e)}")
        return None

def generate_ai_title(transcript: str) -> str:
    """Generate an AI title for the content"""
    try:
        from core.content_generation import generate_content
        
        prompt = f"""Generate a concise, descriptive title (max 60 characters) for this audio transcript:

{transcript[:500]}...

Title should be:
- Clear and specific
- Professional
- Capture the main topic
- No quotes or special characters

Title:"""
        
        title = generate_content(prompt, "OpenAI", "gpt-4", {})
        return title.strip().replace('"', '').replace("'", "")[:60]
    except:
        return f"WhisperForge Content - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

# === SIMPLE AUTHENTICATION ===
def init_session():
    """Initialize simple session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

def show_login():
    """Simple test login"""
    create_aurora_header()
    
    st.markdown("### 🔐 Login to WhisperForge")
    
    # Test login button
    if st.button("🚀 Login with Test Account", type="primary", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user_id = 1
        st.session_state.user_email = "test@whisperforge.ai"
        st.success("✅ Logged in successfully!")
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Demo Mode**: Click above to access WhisperForge")

# === CORE PROCESSING PIPELINE ===
def process_audio_pipeline(audio_file):
    """Core audio to content pipeline"""
    results = {}
    
    # Progress tracking
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    try:
        # Step 1: Transcription
        status_text.text("🎙️ Transcribing audio...")
        progress_bar.progress(0.2)
        
        transcript = transcribe_audio(audio_file)
        if not transcript or "Error" in transcript:
            st.error(f"❌ Transcription failed: {transcript}")
            return None
        
        results['transcript'] = transcript
        st.success(f"✅ Transcription complete ({len(transcript)} characters)")
        
        # Step 2: Wisdom Extraction
        status_text.text("💡 Extracting key insights...")
        progress_bar.progress(0.3)
        
        wisdom = generate_wisdom(transcript, "OpenAI", "gpt-4", knowledge_base={})
        results['wisdom'] = wisdom
        st.success("✅ Wisdom extracted")
        
        # Step 3: Research Enrichment
        if st.session_state.get('research_enabled', True):
            status_text.text("🔍 Finding supporting research...")
            progress_bar.progress(0.45)
            
            research = generate_research_enrichment(wisdom, transcript, "OpenAI", "gpt-4", enabled=True)
            results['research'] = research
            st.success(f"✅ Research enrichment complete ({research.get('total_entities', 0)} entities)")
        else:
            status_text.text("🔍 Research enrichment skipped...")
            progress_bar.progress(0.45)
            
            results['research'] = {"entities": [], "total_entities": 0, "status": "disabled"}
            st.info("ℹ️ Research enrichment disabled")
        
        # Step 4: Outline Creation
        status_text.text("📋 Creating structured outline...")
        progress_bar.progress(0.6)
        
        outline = generate_outline(transcript, wisdom, "OpenAI", "gpt-4", knowledge_base={})
        results['outline'] = outline
        st.success("✅ Outline created")
        
        # Step 5: Article Generation
        status_text.text("📝 Writing comprehensive article...")
        progress_bar.progress(0.75)
        
        article = generate_article(transcript, wisdom, outline, "OpenAI", "gpt-4", knowledge_base={})
        results['article'] = article
        st.success("✅ Article generated")
        
        # Step 6: Social Content
        status_text.text("📱 Creating social media content...")
        progress_bar.progress(0.85)
        
        social = generate_social_content(wisdom, outline, article, "OpenAI", "gpt-4", knowledge_base={})
        results['social_content'] = social
        st.success("✅ Social content created")
        
        # Step 7: Editor Review & Revision (if enabled)
        if st.session_state.get('editor_enabled', False):
            status_text.text("📝 Editor reviewing content...")
            progress_bar.progress(0.9)
            
            # Generate editor notes for key content
            editor_notes = {}
            content_types = [
                ('wisdom', wisdom),
                ('outline', outline), 
                ('article', article),
                ('social_content', social)
            ]
            
            for content_type, content in content_types:
                if content:
                    notes = editor_critique(content, content_type, "OpenAI", "gpt-4", knowledge_base={})
                    editor_notes[content_type] = notes
            
            results['editor_notes'] = editor_notes
            st.success(f"✅ Editor review complete ({len(editor_notes)} items reviewed)")
            
            # One revision pass with editor notes
            status_text.text("🔄 Revising content with editor feedback...")
            progress_bar.progress(0.92)
            
            revised_content = {}
            for content_type, content in content_types:
                if content and content_type in editor_notes:
                    notes = editor_notes[content_type]
                    
                    revision_prompt = f"""Improve this {content_type} based on editor feedback:

ORIGINAL:
{content}

EDITOR NOTES:
{notes}

Provide an improved version that addresses the feedback while maintaining the core message."""
                    
                    if content_type == 'wisdom':
                        revised = generate_wisdom(transcript, "OpenAI", "gpt-4", custom_prompt=revision_prompt, knowledge_base={})
                    elif content_type == 'outline':
                        revised = generate_outline(transcript, wisdom, "OpenAI", "gpt-4", custom_prompt=revision_prompt, knowledge_base={})
                    elif content_type == 'article':
                        revised = generate_article(transcript, wisdom, outline, "OpenAI", "gpt-4", custom_prompt=revision_prompt, knowledge_base={})
                    elif content_type == 'social_content':
                        revised = generate_social_content(wisdom, outline, article, "OpenAI", "gpt-4", custom_prompt=revision_prompt, knowledge_base={})
                    
                    revised_content[content_type] = revised
            
            results['revised_content'] = revised_content
            st.success(f"✅ Content revision complete ({len(revised_content)} items revised)")
        else:
            st.info("ℹ️ Editor review disabled")
        
        # Step 8: Auto-publish to Notion
        if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
            status_text.text("🌌 Publishing to Notion...")
            progress_bar.progress(0.95)
            
            # Generate AI title
            ai_title = generate_ai_title(transcript)
            
            # Publish to Notion
            notion_url = create_notion_page(ai_title, results)
            if notion_url:
                results['notion_url'] = notion_url
                st.success(f"✅ Published to Notion!")
                st.markdown(f"🔗 [Open in Notion]({notion_url})")
            else:
                st.warning("⚠️ Notion publishing skipped")
        else:
            st.info("ℹ️ Configure Notion in sidebar for auto-publishing")
        
        # Complete with Aurora celebration
        progress_bar.progress(1.0)
        
        # Aurora completion celebration
        st.markdown("""
        <div style="text-align: center; padding: 30px; margin: 20px 0;">
            <h1 style="
                color: var(--aurora-primary); 
                text-shadow: var(--aurora-glow-strong); 
                font-size: 3rem;
                margin: 0;
                animation: aurora-pulse 2s ease-in-out infinite;
            ">🎉 Pipeline Complete! 🌌</h1>
            <p style="color: var(--aurora-text); font-size: 1.3rem; margin: 15px 0;">
                Your content has been transformed with AI magic ✨
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Aurora success message
        AuroraComponents.success_message("🚀 All processing steps completed successfully!")
        
        # Save to Supabase database
        try:
            save_content_to_db(results)
        except Exception as e:
            st.warning(f"⚠️ Content saved locally but database save failed: {e}")
        
        return results
        
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        return None

def save_content_to_db(content_data):
    """Save generated content to database"""
    try:
        db = get_supabase_client()
        if db and st.session_state.user_id:
            content_id = db.save_content(st.session_state.user_id, {
                **content_data,
                'title': f"WhisperForge Content {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'created_at': datetime.now().isoformat()
            })
            if content_id:
                st.success(f"💾 Content saved to database (ID: {content_id})")
    except Exception as e:
        st.warning(f"Database save failed: {e}")

# === CONTENT DISPLAY ===
def show_results(results):
    """Display generated content with Aurora styling"""
    if not results:
        return
    
    # Aurora header for results
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin: 20px 0;">
        <h1 style="
            color: var(--aurora-primary); 
            text-shadow: var(--aurora-glow); 
            font-size: 2.5rem;
            margin: 0;
        ">🎉 Content Generated!</h1>
        <p style="color: var(--aurora-text); font-size: 1.2rem; margin: 10px 0;">
            Your audio has been transformed with AI magic ✨
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Aurora Notion link if available
    if results.get('notion_url'):
        st.markdown(f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{results['notion_url']}" target="_blank" style="
                background: linear-gradient(45deg, var(--aurora-primary), var(--aurora-secondary));
                color: black;
                padding: 16px 32px;
                border-radius: 16px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.2rem;
                box-shadow: var(--aurora-glow-strong);
                display: inline-block;
                transition: all 0.3s ease;
                border: none;
            ">🌌 View in Notion</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
    
    # Create tabs for different content types
    tab_names = ["📜 Transcript", "💎 Wisdom", "🔍 Research", "📋 Outline", "📰 Article", "📱 Social Media"]
    
    # Add Editor tab if editor was enabled
    if results.get('editor_notes') or results.get('revised_content'):
        tab_names.append("📝 Editor Review")
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        create_aurora_content_card("🎙️ Audio Transcript", results.get('transcript', ''), "transcript")
    
    with tabs[1]:
        create_aurora_content_card("💡 Key Insights", results.get('wisdom', ''), "text")
    
    with tabs[2]:
        st.markdown("""
        <div class="aurora-card">
            <h3 style="color: var(--aurora-primary); text-shadow: var(--aurora-glow);">
                🔍 Research & Supporting Links
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        research_data = results.get('research', {})
        if research_data and research_data.get('entities'):
            entities = research_data['entities']
            AuroraComponents.success_message(f"Found {len(entities)} research entities in {research_data.get('processing_time', 0):.1f}s")
            
            for entity in entities:
                with st.expander(f"🔬 {entity.get('name', 'Unknown Entity')}"):
                    st.markdown(f"**Type:** {entity.get('type', 'Unknown')}")
                    st.markdown(f"**Why this matters:** {entity.get('why_matters', 'No description')}")
                    
                    links = entity.get('links', [])
                    if links:
                        st.markdown("**Research Links:**")
                        for link in links:
                            gem_icon = "💎" if link.get('is_gem') else "🔗"
                            st.markdown(f"{gem_icon} **{link.get('title', 'Link')}**")
                            st.markdown(f"   {link.get('description', 'No description')}")
                            if link.get('url'):
                                st.markdown(f"   🌐 [Visit Link]({link['url']})")
        else:
            st.info("No research entities found or research was disabled.")
    
    with tabs[3]:
        create_aurora_content_card("📋 Content Outline", results.get('outline', ''), "text")
    
    with tabs[4]:
        create_aurora_content_card("📰 Full Article", results.get('article', ''), "text")
    
    with tabs[5]:
        create_aurora_content_card("📱 Social Media Posts", results.get('social_content', ''), "text")
    
    # Editor tab (if enabled)
    if len(tabs) > 6:
        with tabs[6]:
            st.markdown("""
            <div class="aurora-card">
                <h3 style="color: var(--aurora-primary); text-shadow: var(--aurora-glow);">
                    📝 Editor Review & Revisions
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            editor_notes = results.get('editor_notes', {})
            revised_content = results.get('revised_content', {})
            
            if editor_notes:
                AuroraComponents.success_message(f"Editor reviewed {len(editor_notes)} content sections and provided improvement notes.")
                
                for content_type, notes in editor_notes.items():
                    with st.expander(f"📝 Editor Notes: {content_type.replace('_', ' ').title()}"):
                        st.markdown("**Editor Feedback:**")
                        st.markdown(notes)
                        
                        # Show revised content if available
                        if content_type in revised_content:
                            st.markdown("---")
                            st.markdown("**Revised Content:**")
                            st.markdown(revised_content[content_type])
                        else:
                            st.info("No revision generated for this content.")
            else:
                st.info("No editor notes available.")

# === MAIN APP ===
def show_main_app():
    """Main application interface"""
    create_aurora_header()
    
    st.markdown("### 🎵 Transform Audio into Structured Content")
    
    # API Key setup
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # OpenAI API Key
        api_key = st.text_input("OpenAI API Key", type="password", 
                                help="Your OpenAI API key for transcription and content generation")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        st.markdown("---")
        st.markdown("### 🌌 Notion Integration")
        
        # Notion API Key
        notion_key = st.text_input("Notion API Key", type="password",
                                  value=os.getenv("NOTION_API_KEY", ""),
                                  help="Your Notion integration token for auto-publishing")
        if notion_key:
            os.environ["NOTION_API_KEY"] = notion_key
        
        # Notion Database ID
        notion_db = st.text_input("Notion Database ID",
                                 value=os.getenv("NOTION_DATABASE_ID", ""),
                                 help="Your Notion database ID for content storage")
        if notion_db:
            os.environ["NOTION_DATABASE_ID"] = notion_db
        
        # Show connection status
        if notion_key and notion_db:
            st.success("✅ Notion configured - Auto-publishing enabled")
        else:
            st.info("ℹ️ Configure Notion for auto-publishing")
        
        st.markdown("---")
        st.markdown("### 🔍 Research Settings")
        
        # Research enrichment toggle
        research_enabled = st.checkbox(
            "Enable Research Enrichment",
            value=st.session_state.get('research_enabled', True),
            help="Automatically find supporting research links for key entities"
        )
        st.session_state.research_enabled = research_enabled
        
        # Editor toggle
        editor_enabled = st.checkbox(
            "Enable AI Editor Review",
            value=st.session_state.get('editor_enabled', False),
            help="AI editor provides improvement notes and generates revised content"
        )
        st.session_state.editor_enabled = editor_enabled
        
        # Test connections
        if st.button("🧪 Test Connections"):
            with st.spinner("Testing connections..."):
                # Test Supabase
                try:
                    db = get_supabase_client()
                    if db and db.test_connection():
                        st.success("✅ Supabase connected")
                    else:
                        st.error("❌ Supabase connection failed")
                except Exception as e:
                    st.error(f"❌ Supabase error: {e}")
                
                # Test Notion
                if notion_key and notion_db:
                    try:
                        from notion_client import Client
                        client = Client(auth=notion_key)
                        database = client.databases.retrieve(database_id=notion_db)
                        st.success("✅ Notion connected")
                    except Exception as e:
                        st.error(f"❌ Notion error: {e}")
    
    # File upload
    uploaded_file = st.file_uploader(
        "🎵 Upload your audio file",
        type=['mp3', 'wav', 'm4a', 'flac', 'ogg'],
        help="Upload audio file for processing (max 25MB)"
    )
    
    if uploaded_file:
        # Show file info
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"📊 **{uploaded_file.name}** ({file_size:.1f} MB)")
        
        # Audio player
        st.audio(uploaded_file.getvalue())
        
        # Process button
        if st.button("⚡ Transform Audio to Content", type="primary", use_container_width=True):
            if not os.getenv("OPENAI_API_KEY"):
                st.error("❌ Please enter your OpenAI API key in the sidebar")
                return
            
            with st.container():
                results = process_audio_pipeline(uploaded_file)
                if results:
                    # Store results in session state
                    st.session_state.current_results = results
    
    # Show results if available
    if 'current_results' in st.session_state:
        show_results(st.session_state.current_results)

# === ENTRY POINT ===
def main():
    """Application entry point"""
    init_session()
    
    if st.session_state.authenticated:
        show_main_app()
    else:
        show_login()

if __name__ == "__main__":
    main() 