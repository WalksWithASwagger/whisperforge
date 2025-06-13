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

# === NAVIGATION & PAGES ===
def create_aurora_navigation():
    """Create Aurora-styled navigation"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(64, 224, 208, 0.3);
        box-shadow: 0 8px 32px rgba(64, 224, 208, 0.1);
    ">
        <div style="text-align: center;">
            <h2 style="
                color: #40E0D0;
                text-shadow: 0 0 20px rgba(64, 224, 208, 0.5);
                margin: 0;
                font-size: 1.8rem;
            ">🌌 WhisperForge Aurora</h2>
            <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0;">
                Transform Audio into Structured Content with AI
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tabs = st.tabs([
        "🎵 Transform", 
        "📚 Content Library", 
        "⚙️ Settings", 
        "🧠 Knowledge Base",
        "📝 Prompts"
    ])
    
    return tabs

def show_transform_page():
    """Main transformation page"""
    st.markdown("### 🎵 Transform Audio into Structured Content")
    
    # Sidebar settings (moved from main app)
    with st.sidebar:
        st.markdown("### ⚙️ Quick Settings")
        
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
        st.markdown("### 🔍 Pipeline Settings")
        
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

def show_content_library():
    """Content library/history page"""
    st.markdown("### 📚 Content Library")
    
    # Get content from database
    try:
        db = get_supabase_client()
        if db:
            # Fetch recent content
            response = db.client.table('content').select('*').order('created_at', desc=True).limit(20).execute()
            
            if response.data:
                st.success(f"📊 Found {len(response.data)} content items")
                
                # Search and filter
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_term = st.text_input("🔍 Search content", placeholder="Search by title or content...")
                with col2:
                    content_type = st.selectbox("Filter by type", ["All", "Article", "Social", "Outline"])
                
                # Display content cards
                for item in response.data:
                    if search_term and search_term.lower() not in item.get('title', '').lower():
                        continue
                    
                    with st.expander(f"📄 {item.get('title', 'Untitled')} - {item.get('created_at', '')[:10]}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Created:** {item.get('created_at', 'Unknown')}")
                            if item.get('transcript'):
                                st.markdown("**Transcript Preview:**")
                                st.text(item['transcript'][:200] + "..." if len(item['transcript']) > 200 else item['transcript'])
                        
                        with col2:
                            if st.button(f"🔄 Reprocess", key=f"reprocess_{item.get('id')}"):
                                st.info("Reprocessing feature coming soon!")
                            
                            if st.button(f"📤 Export", key=f"export_{item.get('id')}"):
                                st.info("Export feature coming soon!")
                        
                        # Show generated content
                        if item.get('wisdom'):
                            create_aurora_content_card("💡 Wisdom", item['wisdom'], "text")
                        if item.get('article'):
                            create_aurora_content_card("📰 Article", item['article'], "text")
                        if item.get('social_content'):
                            create_aurora_content_card("📱 Social Content", item['social_content'], "text")
            else:
                st.info("📭 No content found. Process some audio files to see them here!")
        else:
            st.error("❌ Database connection failed")
    except Exception as e:
        st.error(f"❌ Error loading content library: {e}")

def show_settings_page():
    """Settings and configuration page"""
    st.markdown("### ⚙️ Settings & Configuration")
    
    # API Keys section
    st.markdown("#### 🔑 API Keys")
    with st.expander("🔧 API Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # OpenAI settings
            st.markdown("**OpenAI Configuration**")
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                      value=os.getenv("OPENAI_API_KEY", ""),
                                      help="Your OpenAI API key")
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                st.success("✅ OpenAI key configured")
            
            # Model selection
            model_choice = st.selectbox("OpenAI Model", 
                                       ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                                       help="Choose the OpenAI model for content generation")
            st.session_state.openai_model = model_choice
        
        with col2:
            # Notion settings
            st.markdown("**Notion Configuration**")
            notion_key = st.text_input("Notion API Key", type="password",
                                      value=os.getenv("NOTION_API_KEY", ""),
                                      help="Your Notion integration token")
            if notion_key:
                os.environ["NOTION_API_KEY"] = notion_key
            
            notion_db = st.text_input("Notion Database ID",
                                     value=os.getenv("NOTION_DATABASE_ID", ""),
                                     help="Your Notion database ID")
            if notion_db:
                os.environ["NOTION_DATABASE_ID"] = notion_db
            
            if notion_key and notion_db:
                st.success("✅ Notion configured")
    
    # Pipeline settings
    st.markdown("#### 🔄 Pipeline Configuration")
    with st.expander("⚙️ Processing Pipeline", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Core Features**")
            research_enabled = st.checkbox("Enable Research Enrichment", 
                                         value=st.session_state.get('research_enabled', True))
            st.session_state.research_enabled = research_enabled
            
            editor_enabled = st.checkbox("Enable AI Editor Review", 
                                        value=st.session_state.get('editor_enabled', False))
            st.session_state.editor_enabled = editor_enabled
            
            auto_notion = st.checkbox("Auto-publish to Notion", 
                                     value=st.session_state.get('auto_notion', True))
            st.session_state.auto_notion = auto_notion
        
        with col2:
            st.markdown("**Quality Settings**")
            content_length = st.selectbox("Article Length", 
                                        ["Short (500-800 words)", "Medium (800-1200 words)", "Long (1200+ words)"])
            
            tone_style = st.selectbox("Content Tone", 
                                    ["Professional", "Conversational", "Academic", "Creative"])
            
            st.session_state.content_length = content_length
            st.session_state.tone_style = tone_style
    
    # System status
    st.markdown("#### 🔍 System Status")
    with st.expander("📊 Connection Status", expanded=False):
        if st.button("🧪 Test All Connections"):
            with st.spinner("Testing all connections..."):
                # Test OpenAI
                try:
                    if os.getenv("OPENAI_API_KEY"):
                        st.success("✅ OpenAI API key configured")
                    else:
                        st.error("❌ OpenAI API key missing")
                except Exception as e:
                    st.error(f"❌ OpenAI error: {e}")
                
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
                try:
                    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
                        from notion_client import Client
                        client = Client(auth=os.getenv("NOTION_API_KEY"))
                        database = client.databases.retrieve(database_id=os.getenv("NOTION_DATABASE_ID"))
                        st.success("✅ Notion connected")
                    else:
                        st.warning("⚠️ Notion not configured")
                except Exception as e:
                    st.error(f"❌ Notion error: {e}")

def show_knowledge_base():
    """Knowledge base management page"""
    st.markdown("### 🧠 Knowledge Base")
    
    # Check if knowledge base files exist
    kb_path = "prompts/default/knowledge_base"
    
    st.markdown("""
    The knowledge base provides context and expertise to enhance content generation.
    Add domain-specific information, style guides, and reference materials here.
    """)
    
    # Knowledge base sections
    tabs = st.tabs(["📖 View Knowledge", "➕ Add Knowledge", "🔧 Manage Files"])
    
    with tabs[0]:
        st.markdown("#### 📖 Current Knowledge Base")
        try:
            if os.path.exists(kb_path):
                files = [f for f in os.listdir(kb_path) if f.endswith('.md')]
                if files:
                    selected_file = st.selectbox("Select knowledge file:", files)
                    if selected_file:
                        file_path = os.path.join(kb_path, selected_file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        st.markdown(f"**File:** `{selected_file}`")
                        create_aurora_content_card("Knowledge Content", content, "text")
                else:
                    st.info("📭 No knowledge files found")
            else:
                st.info("📁 Knowledge base directory not found")
        except Exception as e:
            st.error(f"❌ Error reading knowledge base: {e}")
    
    with tabs[1]:
        st.markdown("#### ➕ Add New Knowledge")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            kb_title = st.text_input("Knowledge Title", placeholder="e.g., 'Marketing Guidelines'")
        with col2:
            kb_category = st.selectbox("Category", ["General", "Style Guide", "Domain Expertise", "Templates"])
        
        kb_content = st.text_area("Knowledge Content", 
                                 placeholder="Enter your knowledge content here...",
                                 height=300)
        
        if st.button("💾 Save Knowledge", type="primary"):
            if kb_title and kb_content:
                try:
                    os.makedirs(kb_path, exist_ok=True)
                    filename = f"{kb_title.lower().replace(' ', '_')}.md"
                    file_path = os.path.join(kb_path, filename)
                    
                    with open(file_path, 'w') as f:
                        f.write(f"# {kb_title}\n\n")
                        f.write(f"**Category:** {kb_category}\n\n")
                        f.write(kb_content)
                    
                    st.success(f"✅ Knowledge saved as `{filename}`")
                except Exception as e:
                    st.error(f"❌ Error saving knowledge: {e}")
            else:
                st.error("❌ Please provide both title and content")
    
    with tabs[2]:
        st.markdown("#### 🔧 Manage Knowledge Files")
        
        try:
            if os.path.exists(kb_path):
                files = [f for f in os.listdir(kb_path) if f.endswith('.md')]
                if files:
                    for file in files:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"📄 `{file}`")
                        with col2:
                            if st.button("📝 Edit", key=f"edit_{file}"):
                                st.info("Edit functionality coming soon!")
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{file}"):
                                try:
                                    os.remove(os.path.join(kb_path, file))
                                    st.success(f"✅ Deleted `{file}`")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting file: {e}")
                else:
                    st.info("📭 No knowledge files found")
            else:
                st.info("📁 Knowledge base directory not found")
        except Exception as e:
            st.error(f"❌ Error managing files: {e}")

def show_prompts_page():
    """Prompts management page"""
    st.markdown("### 📝 Prompts Management")
    
    st.markdown("""
    Customize the AI prompts used in each step of the content generation pipeline.
    Fine-tune the output style, format, and focus for your specific needs.
    """)
    
    # Prompt categories
    prompt_types = {
        "wisdom": "💡 Wisdom Extraction",
        "outline": "📋 Content Outline", 
        "article": "📰 Article Generation",
        "social": "📱 Social Media Posts",
        "research": "🔍 Research Enrichment",
        "editor": "📝 Editor Review"
    }
    
    tabs = st.tabs(list(prompt_types.values()) + ["🔧 Advanced"])
    
    for i, (prompt_key, prompt_name) in enumerate(prompt_types.items()):
        with tabs[i]:
            st.markdown(f"#### {prompt_name}")
            
            # Load current prompt
            prompt_file = f"prompts/default/{prompt_key}_prompt.md"
            current_prompt = ""
            
            try:
                if os.path.exists(prompt_file):
                    with open(prompt_file, 'r') as f:
                        current_prompt = f.read()
                else:
                    current_prompt = f"# {prompt_name} Prompt\n\nDefault prompt for {prompt_key} generation."
            except Exception as e:
                st.error(f"❌ Error loading prompt: {e}")
            
            # Edit prompt
            new_prompt = st.text_area(
                f"Edit {prompt_name} Prompt",
                value=current_prompt,
                height=400,
                help=f"Customize the prompt used for {prompt_key} generation"
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(f"💾 Save", key=f"save_{prompt_key}"):
                    try:
                        os.makedirs("prompts/default", exist_ok=True)
                        with open(prompt_file, 'w') as f:
                            f.write(new_prompt)
                        st.success(f"✅ {prompt_name} prompt saved!")
                    except Exception as e:
                        st.error(f"❌ Error saving prompt: {e}")
            
            with col2:
                if st.button(f"🔄 Reset", key=f"reset_{prompt_key}"):
                    st.info("Reset to default functionality coming soon!")
            
            with col3:
                st.markdown(f"**File:** `{prompt_file}`")
    
    # Advanced settings
    with tabs[-1]:
        st.markdown("#### 🔧 Advanced Prompt Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Global Settings**")
            temperature = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.number_input("Max Tokens", 100, 4000, 2000)
            
        with col2:
            st.markdown("**Prompt Templates**")
            if st.button("📥 Import Prompt Set"):
                st.info("Import functionality coming soon!")
            if st.button("📤 Export Prompt Set"):
                st.info("Export functionality coming soon!")
        
        st.session_state.temperature = temperature
        st.session_state.max_tokens = max_tokens

# === MAIN APP ===
def show_main_app():
    """Main application interface with navigation"""
    # Create navigation
    tabs = create_aurora_navigation()
    
    # Show different pages based on selected tab
    with tabs[0]:  # Transform
        show_transform_page()
    
    with tabs[1]:  # Content Library
        show_content_library()
    
    with tabs[2]:  # Settings
        show_settings_page()
    
    with tabs[3]:  # Knowledge Base
        show_knowledge_base()
    
    with tabs[4]:  # Prompts
        show_prompts_page()

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