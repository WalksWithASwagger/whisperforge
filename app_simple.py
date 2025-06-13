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
from core.file_upload import EnhancedLargeFileProcessor

# Apply beautiful theme
apply_aurora_theme()

# === PROMPT LOADING SYSTEM ===
def load_custom_prompts():
    """Load custom prompts from the prompts directory"""
    prompts = {}
    prompt_dir = "prompts/default"
    
    if os.path.exists(prompt_dir):
        for filename in os.listdir(prompt_dir):
            if filename.endswith('.md'):
                prompt_name = filename.replace('.md', '')
                try:
                    with open(os.path.join(prompt_dir, filename), 'r', encoding='utf-8') as f:
                        prompts[prompt_name] = f.read()
                except Exception as e:
                    st.warning(f"Failed to load prompt {filename}: {e}")
    
    return prompts

def get_prompt_for_step(step_name: str, custom_prompts: Dict[str, str] = None) -> Optional[str]:
    """Get the appropriate prompt for a pipeline step"""
    if not custom_prompts:
        custom_prompts = load_custom_prompts()
    
    # Map step names to prompt files
    prompt_mapping = {
        'wisdom': 'wisdom_extraction',
        'outline': 'outline_creation', 
        'social': 'social_media',
        'article': 'article_generation'  # We'll create this
    }
    
    prompt_key = prompt_mapping.get(step_name)
    if prompt_key and prompt_key in custom_prompts:
        return custom_prompts[prompt_key]
    
    return None

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
        
        # Add beautiful header with summary
        children.append({
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {"type": "text", "text": {"content": "🌌 "}, "annotations": {"color": "blue"}},
                    {"type": "text", "text": {"content": title}, "annotations": {"bold": True}}
                ]
            }
        })
        
        # Add creation info
        children.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "✨ Generated with "}},
                    {"type": "text", "text": {"content": "WhisperForge Aurora"}, 
                     "annotations": {"bold": True, "color": "blue"}},
                    {"type": "text", "text": {"content": f" • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"}}
                ]
            }
        })
        
        children.append({"type": "divider", "divider": {}})
        
        # Add wisdom summary callout if exists
        if content_data.get('wisdom'):
            children.append({
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Key Insights & Wisdom"}},
                        {"type": "text", "text": {"content": f"\n\n{content_data['wisdom'][:1800]}"}}
                    ],
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
                            
                            # Entity as beautiful callout
                            research_children.append({
                                "type": "callout",
                                "callout": {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": entity_name}, "annotations": {"bold": True}},
                                        {"type": "text", "text": {"content": f"\n{why_matters}"}}
                                    ],
                                    "color": "blue_background",
                                    "icon": {"type": "emoji", "emoji": "🔬"}
                                }
                            })
                            
                            # Links as bulleted list
                            if links:
                                for link in links[:3]:  # Limit links
                                    link_title = link.get('title', 'Link')
                                    link_url = link.get('url', '#')
                                    link_desc = link.get('description', '')
                                    is_gem = link.get('is_gem', False)
                                    
                                    gem_icon = "💎" if is_gem else "🔗"
                                    color = "orange" if is_gem else "default"
                                    
                                    research_children.append({
                                        "type": "bulleted_list_item",
                                        "bulleted_list_item": {
                                            "rich_text": [
                                                {"type": "text", "text": {"content": f"{gem_icon} "}, "annotations": {"color": color}},
                                                {"type": "text", "text": {"content": link_title}, "annotations": {"bold": True}},
                                                {"type": "text", "text": {"content": f" - {link_desc}"}, "annotations": {"italic": True}}
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
        
        # Add beautiful footer
        children.extend([
            {"type": "divider", "divider": {}},
            {
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Content Generation Complete"}, "annotations": {"bold": True}},
                        {"type": "text", "text": {"content": f"\n\n🤖 AI Pipeline: 8 steps completed successfully"}},
                        {"type": "text", "text": {"content": f"\n⏱️ Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"}},
                        {"type": "text", "text": {"content": f"\n🌌 Powered by WhisperForge Aurora"}}
                    ],
                    "color": "green_background",
                    "icon": {"type": "emoji", "emoji": "✅"}
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
    """Core audio to content pipeline with real-time streaming"""
    results = {}
    
    # Load custom prompts
    custom_prompts = load_custom_prompts()
    if custom_prompts:
        st.info(f"📝 Using {len(custom_prompts)} custom prompts")
    
    # Progress tracking
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    # Create real-time content display containers
    st.markdown("### 🌌 Live Content Generation")
    
    # Create expandable sections for each step
    transcript_container = st.expander("🎙️ Transcription", expanded=False)
    wisdom_container = st.expander("💡 Wisdom Extraction", expanded=False)
    research_container = st.expander("🔍 Research Enrichment", expanded=False)
    outline_container = st.expander("📋 Outline Creation", expanded=False)
    article_container = st.expander("📝 Article Generation", expanded=False)
    social_container = st.expander("📱 Social Content", expanded=False)
    editor_container = st.expander("📝 Editor Review", expanded=False)
    notion_container = st.expander("🌌 Notion Publishing", expanded=False)
    
    try:
        # Step 1: Transcription
        status_text.text("🎙️ Transcribing audio...")
        progress_bar.progress(0.2)
        
        transcript = transcribe_audio(audio_file)
        if not transcript or "Error" in transcript:
            st.error(f"❌ Transcription failed: {transcript}")
            return None
        
        results['transcript'] = transcript
        
        # Stream transcript to UI immediately
        with transcript_container:
            st.markdown("**✅ Transcription Complete**")
            st.text_area("Transcript", transcript, height=200, disabled=True)
        
        st.success(f"✅ Transcription complete ({len(transcript)} characters)")
        
        # Step 2: Wisdom Extraction
        status_text.text("💡 Extracting key insights...")
        progress_bar.progress(0.3)
        
        # Use custom prompt if available
        wisdom_prompt = get_prompt_for_step('wisdom', custom_prompts)
        wisdom = generate_wisdom(transcript, "OpenAI", "gpt-4", 
                                custom_prompt=wisdom_prompt, knowledge_base={})
        results['wisdom'] = wisdom
        
        # Stream wisdom to UI immediately
        with wisdom_container:
            st.markdown("**✅ Wisdom Extraction Complete**")
            st.markdown(wisdom)
        
        st.success("✅ Wisdom extracted")
        
        # Step 3: Research Enrichment
        if st.session_state.get('research_enabled', True):
            status_text.text("🔍 Finding supporting research...")
            progress_bar.progress(0.45)
            
            research = generate_research_enrichment(wisdom, transcript, "OpenAI", "gpt-4", enabled=True)
            results['research'] = research
            
            # Stream research to UI immediately
            with research_container:
                st.markdown("**✅ Research Enrichment Complete**")
                if research.get('entities'):
                    for entity in research['entities'][:3]:  # Show first 3 entities
                        st.markdown(f"**{entity.get('name', 'Entity')}**: {entity.get('why_matters', 'No description')}")
                        if entity.get('links'):
                            for link in entity['links'][:2]:  # Show first 2 links
                                gem_icon = "💎" if link.get('is_gem') else "🔗"
                                st.markdown(f"{gem_icon} [{link.get('title', 'Link')}]({link.get('url', '#')})")
                else:
                    st.markdown("No research entities found.")
            
            st.success(f"✅ Research enrichment complete ({research.get('total_entities', 0)} entities)")
        else:
            status_text.text("🔍 Research enrichment skipped...")
            progress_bar.progress(0.45)
            
            results['research'] = {"entities": [], "total_entities": 0, "status": "disabled"}
            
            # Show disabled status in UI
            with research_container:
                st.markdown("**ℹ️ Research Enrichment Disabled**")
                st.info("Enable in Settings to get research links and entities.")
            
            st.info("ℹ️ Research enrichment disabled")
        
        # Step 4: Outline Creation
        status_text.text("📋 Creating structured outline...")
        progress_bar.progress(0.6)
        
        # Use custom prompt if available
        outline_prompt = get_prompt_for_step('outline', custom_prompts)
        outline = generate_outline(transcript, wisdom, "OpenAI", "gpt-4", 
                                  custom_prompt=outline_prompt, knowledge_base={})
        results['outline'] = outline
        
        # Stream outline to UI immediately
        with outline_container:
            st.markdown("**✅ Outline Creation Complete**")
            st.markdown(outline)
        
        st.success("✅ Outline created")
        
        # Step 5: Article Generation
        status_text.text("📝 Writing comprehensive article...")
        progress_bar.progress(0.75)
        
        # Use custom prompt if available
        article_prompt = get_prompt_for_step('article', custom_prompts)
        article = generate_article(transcript, wisdom, outline, "OpenAI", "gpt-4", 
                                  custom_prompt=article_prompt, knowledge_base={})
        results['article'] = article
        
        # Stream article to UI immediately
        with article_container:
            st.markdown("**✅ Article Generation Complete**")
            st.markdown(article)
        
        st.success("✅ Article generated")
        
        # Step 6: Social Content
        status_text.text("📱 Creating social media content...")
        progress_bar.progress(0.85)
        
        # Use custom prompt if available
        social_prompt = get_prompt_for_step('social', custom_prompts)
        social = generate_social_content(wisdom, outline, article, "OpenAI", "gpt-4", 
                                        custom_prompt=social_prompt, knowledge_base={})
        results['social_content'] = social
        
        # Stream social content to UI immediately
        with social_container:
            st.markdown("**✅ Social Content Creation Complete**")
            st.markdown(social)
        
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
            
            # Stream editor results to UI
            with editor_container:
                st.markdown("**✅ Editor Review & Revision Complete**")
                st.markdown(f"**Editor Notes Generated:** {len(editor_notes)} items")
                st.markdown(f"**Content Revised:** {len(revised_content)} items")
                
                # Show editor notes summary
                for content_type, notes in editor_notes.items():
                    with st.expander(f"📝 {content_type.title()} Notes"):
                        st.markdown(notes[:500] + "..." if len(notes) > 500 else notes)
            
            st.success(f"✅ Content revision complete ({len(revised_content)} items revised)")
        else:
            # Show disabled status in UI
            with editor_container:
                st.markdown("**ℹ️ Editor Review Disabled**")
                st.info("Enable in Settings to get AI editor feedback and content revisions.")
            
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
                
                # Stream Notion success to UI
                with notion_container:
                    st.markdown("**✅ Notion Publishing Complete**")
                    st.markdown(f"**Page Title:** {ai_title}")
                    st.markdown(f"🔗 [Open in Notion]({notion_url})")
                
                st.success(f"✅ Published to Notion!")
                st.markdown(f"🔗 [Open in Notion]({notion_url})")
            else:
                # Stream Notion failure to UI
                with notion_container:
                    st.markdown("**⚠️ Notion Publishing Failed**")
                    st.warning("Check your Notion API configuration in Settings.")
                
                st.warning("⚠️ Notion publishing skipped")
        else:
            # Show disabled status in UI
            with notion_container:
                st.markdown("**ℹ️ Notion Publishing Disabled**")
                st.info("Configure Notion API in Settings to enable auto-publishing.")
            
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

def process_audio_pipeline_with_transcript(transcript: str):
    """Process audio pipeline with pre-transcribed content (for large file processing)"""
    results = {'transcript': transcript}
    
    # Load custom prompts
    custom_prompts = load_custom_prompts()
    if custom_prompts:
        st.info(f"📝 Using {len(custom_prompts)} custom prompts")
    
    # Progress tracking
    progress_bar = st.progress(0.2)  # Start at 20% since transcription is done
    status_text = st.empty()
    
    # Create real-time content display containers
    st.markdown("### 🌌 Live Content Generation")
    
    # Create expandable sections for each step (skip transcription)
    wisdom_container = st.expander("💡 Wisdom Extraction", expanded=False)
    research_container = st.expander("🔍 Research Enrichment", expanded=False)
    outline_container = st.expander("📋 Outline Creation", expanded=False)
    article_container = st.expander("📝 Article Generation", expanded=False)
    social_container = st.expander("📱 Social Content", expanded=False)
    editor_container = st.expander("📝 Editor Review", expanded=False)
    notion_container = st.expander("🌌 Notion Publishing", expanded=False)
    
    try:
        # Show transcript info
        st.success(f"✅ Using pre-transcribed content ({len(transcript)} characters)")
        
        # Step 2: Wisdom Extraction
        status_text.text("💡 Extracting key insights...")
        progress_bar.progress(0.3)
        
        # Use custom prompt if available
        wisdom_prompt = get_prompt_for_step('wisdom', custom_prompts)
        wisdom = generate_wisdom(transcript, "OpenAI", "gpt-4", 
                                custom_prompt=wisdom_prompt, knowledge_base={})
        results['wisdom'] = wisdom
        
        # Stream wisdom to UI immediately
        with wisdom_container:
            st.markdown("**✅ Wisdom Extraction Complete**")
            st.markdown(wisdom)
        
        st.success("✅ Wisdom extracted")
        
        # Step 3: Research Enrichment
        if st.session_state.get('research_enabled', True):
            status_text.text("🔍 Finding supporting research...")
            progress_bar.progress(0.45)
            
            research = generate_research_enrichment(wisdom, transcript, "OpenAI", "gpt-4", enabled=True)
            results['research'] = research
            
            # Stream research to UI immediately
            with research_container:
                st.markdown("**✅ Research Enrichment Complete**")
                if research.get('entities'):
                    for entity in research['entities'][:3]:  # Show first 3 entities
                        st.markdown(f"**{entity.get('name', 'Entity')}**: {entity.get('why_matters', 'No description')}")
                        if entity.get('links'):
                            for link in entity['links'][:2]:  # Show first 2 links
                                gem_icon = "💎" if link.get('is_gem') else "🔗"
                                st.markdown(f"{gem_icon} [{link.get('title', 'Link')}]({link.get('url', '#')})")
                else:
                    st.markdown("No research entities found.")
            
            st.success(f"✅ Research enrichment complete ({research.get('total_entities', 0)} entities)")
        else:
            status_text.text("🔍 Research enrichment skipped...")
            progress_bar.progress(0.45)
            
            results['research'] = {"entities": [], "total_entities": 0, "status": "disabled"}
            
            # Show disabled status in UI
            with research_container:
                st.markdown("**ℹ️ Research Enrichment Disabled**")
                st.info("Enable in Settings to get research links and entities.")
            
            st.info("ℹ️ Research enrichment disabled")
        
        # Step 4: Outline Creation
        status_text.text("📋 Creating structured outline...")
        progress_bar.progress(0.6)
        
        # Use custom prompt if available
        outline_prompt = get_prompt_for_step('outline', custom_prompts)
        outline = generate_outline(transcript, wisdom, "OpenAI", "gpt-4", 
                                  custom_prompt=outline_prompt, knowledge_base={})
        results['outline'] = outline
        
        # Stream outline to UI immediately
        with outline_container:
            st.markdown("**✅ Outline Creation Complete**")
            st.markdown(outline)
        
        st.success("✅ Outline created")
        
        # Step 5: Article Generation
        status_text.text("📝 Writing comprehensive article...")
        progress_bar.progress(0.75)
        
        # Use custom prompt if available
        article_prompt = get_prompt_for_step('article', custom_prompts)
        article = generate_article(transcript, wisdom, outline, "OpenAI", "gpt-4", 
                                  custom_prompt=article_prompt, knowledge_base={})
        results['article'] = article
        
        # Stream article to UI immediately
        with article_container:
            st.markdown("**✅ Article Generation Complete**")
            st.markdown(article)
        
        st.success("✅ Article generated")
        
        # Step 6: Social Content
        status_text.text("📱 Creating social media content...")
        progress_bar.progress(0.85)
        
        # Use custom prompt if available
        social_prompt = get_prompt_for_step('social', custom_prompts)
        social = generate_social_content(wisdom, outline, article, "OpenAI", "gpt-4", 
                                        custom_prompt=social_prompt, knowledge_base={})
        results['social_content'] = social
        
        # Stream social content to UI immediately
        with social_container:
            st.markdown("**✅ Social Content Creation Complete**")
            st.markdown(social)
        
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
            
            # Stream editor results to UI
            with editor_container:
                st.markdown("**✅ Editor Review & Revision Complete**")
                st.markdown(f"**Editor Notes Generated:** {len(editor_notes)} items")
                st.markdown(f"**Content Revised:** {len(revised_content)} items")
                
                # Show editor notes summary
                for content_type, notes in editor_notes.items():
                    with st.expander(f"📝 {content_type.title()} Notes"):
                        st.markdown(notes[:500] + "..." if len(notes) > 500 else notes)
            
            st.success(f"✅ Content revision complete ({len(revised_content)} items revised)")
        else:
            # Show disabled status in UI
            with editor_container:
                st.markdown("**ℹ️ Editor Review Disabled**")
                st.info("Enable in Settings to get AI editor feedback and content revisions.")
            
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
                
                # Stream Notion success to UI
                with notion_container:
                    st.markdown("**✅ Notion Publishing Complete**")
                    st.markdown(f"**Page Title:** {ai_title}")
                    st.markdown(f"🔗 [Open in Notion]({notion_url})")
                
                st.success(f"✅ Published to Notion!")
                st.markdown(f"🔗 [Open in Notion]({notion_url})")
            else:
                # Stream Notion failure to UI
                with notion_container:
                    st.markdown("**⚠️ Notion Publishing Failed**")
                    st.warning("Check your Notion API configuration in Settings.")
                
                st.warning("⚠️ Notion publishing skipped")
        else:
            # Show disabled status in UI
            with notion_container:
                st.markdown("**ℹ️ Notion Publishing Disabled**")
                st.info("Configure Notion API in Settings to enable auto-publishing.")
            
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
                Your large file content has been transformed with AI magic ✨
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
    """Create Aurora-styled navigation with enhanced bioluminescent effects"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, 
            rgba(10, 15, 28, 0.95) 0%, 
            rgba(13, 20, 33, 0.95) 25%,
            rgba(16, 33, 62, 0.95) 50%,
            rgba(15, 52, 96, 0.95) 75%,
            rgba(10, 15, 28, 0.95) 100%);
        padding: 2rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        border: 2px solid rgba(64, 224, 208, 0.4);
        box-shadow: 
            0 0 40px rgba(64, 224, 208, 0.2),
            inset 0 0 40px rgba(64, 224, 208, 0.05);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(64, 224, 208, 0.8), 
                rgba(125, 249, 255, 0.8), 
                rgba(64, 224, 208, 0.8), 
                transparent);
            animation: aurora-scan 6s ease-in-out infinite;
        "></div>
        
        <div style="text-align: center; position: relative; z-index: 1;">
            <h1 style="
                color: #40E0D0;
                text-shadow: 
                    0 0 20px rgba(64, 224, 208, 0.6),
                    0 0 40px rgba(64, 224, 208, 0.4),
                    0 0 60px rgba(64, 224, 208, 0.2);
                margin: 0 0 1rem 0;
                font-size: 2.5rem;
                font-weight: 700;
                background: linear-gradient(45deg, #40E0D0, #7DF9FF, #00FFFF);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: aurora-pulse 3s ease-in-out infinite;
            ">🌌 WhisperForge Aurora</h1>
            <p style="
                color: rgba(255, 255, 255, 0.9); 
                margin: 0;
                font-size: 1.3rem;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
            ">Transform Audio into Structured Content with AI Magic ✨</p>
            
            <div style="
                margin-top: 1.5rem;
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            ">
                <div style="
                    background: rgba(64, 224, 208, 0.1);
                    border: 1px solid rgba(64, 224, 208, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 0.9rem;
                ">🎙️ Transcription</div>
                <div style="
                    background: rgba(64, 224, 208, 0.1);
                    border: 1px solid rgba(64, 224, 208, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 0.9rem;
                ">💡 Wisdom</div>
                <div style="
                    background: rgba(64, 224, 208, 0.1);
                    border: 1px solid rgba(64, 224, 208, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 0.9rem;
                ">🔍 Research</div>
                <div style="
                    background: rgba(64, 224, 208, 0.1);
                    border: 1px solid rgba(64, 224, 208, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 0.9rem;
                ">📝 Article</div>
                <div style="
                    background: rgba(64, 224, 208, 0.1);
                    border: 1px solid rgba(64, 224, 208, 0.3);
                    border-radius: 20px;
                    padding: 8px 16px;
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 0.9rem;
                ">🌌 Notion</div>
            </div>
        </div>
    </div>
    
    <style>
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-pulse {
        0%, 100% { 
            text-shadow: 
                0 0 20px rgba(64, 224, 208, 0.6),
                0 0 40px rgba(64, 224, 208, 0.4),
                0 0 60px rgba(64, 224, 208, 0.2);
        }
        50% { 
            text-shadow: 
                0 0 30px rgba(64, 224, 208, 0.8),
                0 0 60px rgba(64, 224, 208, 0.6),
                0 0 90px rgba(64, 224, 208, 0.4);
        }
    }
    </style>
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
    """Clean transformation page focused on file upload and processing"""
    
    # Aurora-styled header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(64, 224, 208, 0.1) 0%, rgba(138, 43, 226, 0.1) 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(64, 224, 208, 0.3);
        box-shadow: 0 8px 32px rgba(64, 224, 208, 0.1);
    ">
        <h2 style="
            color: #40E0D0;
            text-shadow: 0 0 20px rgba(64, 224, 208, 0.5);
            margin: 0 0 1rem 0;
            font-size: 2.5rem;
        ">🎵 Transform Audio</h2>
        <p style="
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.2rem;
            margin: 0;
        ">Upload your audio and watch it transform into structured content in real-time</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick status check
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if os.getenv("OPENAI_API_KEY"):
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ OpenAI Not Configured")
            st.info("Configure in Settings tab")
    
    with col2:
        if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
            st.success("✅ Notion Connected")
        else:
            st.warning("⚠️ Notion Not Configured")
            st.info("Configure in Settings tab")
    
    with col3:
        research_status = "✅ Enabled" if st.session_state.get('research_enabled', True) else "⚠️ Disabled"
        editor_status = "✅ Enabled" if st.session_state.get('editor_enabled', False) else "⚠️ Disabled"
        st.info(f"🔍 Research: {research_status}")
        st.info(f"📝 Editor: {editor_status}")
    
    st.markdown("---")
    
    # Enhanced file upload selection
    upload_method = st.radio(
        "Choose upload method:",
        ["🎵 Standard Upload (up to 25MB)", "🚀 Enhanced Large File Upload (up to 2GB)"],
        help="Standard upload for smaller files, Enhanced upload for large files with FFmpeg processing"
    )
    
    if upload_method == "🎵 Standard Upload (up to 25MB)":
        # Standard file upload
        uploaded_file = st.file_uploader(
            "🎵 Upload your audio file",
            type=['mp3', 'wav', 'm4a', 'flac', 'ogg'],
            help="Upload audio file for processing (max 25MB)"
        )
        
        if uploaded_file:
            # Show file info
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"📊 **{uploaded_file.name}** ({file_size:.1f} MB)")
            
            # Audio player (only for smaller files)
            if file_size < 50:  # Only show player for files under 50MB
                st.audio(uploaded_file.getvalue())
            else:
                st.info("🎵 Audio preview disabled for large files to conserve memory")
            
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
    
    else:
        # Enhanced large file upload
        st.markdown("### 🚀 Enhanced Large File Processing")
        
        # Initialize enhanced processor
        processor = EnhancedLargeFileProcessor()
        
        # Create enhanced upload interface
        uploaded_file = processor.create_enhanced_upload_interface()
        
        if uploaded_file:
            # Validate file
            validation = processor.validate_file(uploaded_file)
            
            if not validation["valid"]:
                st.error(f"❌ {validation['error']}")
                return
            
            file_size_mb = validation["size_mb"]
            requires_chunking = validation["requires_chunking"]
            
            # Show file info with enhanced details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📁 File Size", f"{file_size_mb:.1f} MB")
            with col2:
                st.metric("🔧 Processing Method", "FFmpeg Chunking" if requires_chunking else "Standard")
            with col3:
                st.metric("🎯 Format", validation["format"].upper())
            
            # Audio preview disabled for large files to conserve memory
            if file_size_mb < 50:
                st.audio(uploaded_file.getvalue())
            else:
                st.info("🎵 Audio preview disabled for large files to conserve memory")
            
            # Enhanced process button
            if st.button("🚀 Transform Large File to Content", type="primary", use_container_width=True):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("❌ Please enter your OpenAI API key in the sidebar")
                    return
                
                with st.container():
                    # Process with enhanced large file processor
                    processing_result = processor.process_large_file(uploaded_file)
                    
                    if processing_result["success"]:
                        transcript = processing_result["transcript"]
                        
                        # Show processing summary
                        st.success(f"✅ Large file processing complete!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📝 Transcript Length", f"{len(transcript):,} chars")
                        with col2:
                            st.metric("🔧 Method", processing_result["method"])
                        with col3:
                            if "chunks_processed" in processing_result:
                                st.metric("📊 Chunks Processed", processing_result["chunks_processed"])
                        
                        # Continue with pipeline using pre-transcribed content
                        st.markdown("---")
                        results = process_audio_pipeline_with_transcript(transcript)
                        
                        if results:
                            # Store results in session state
                            st.session_state.current_results = results
                    else:
                        st.error(f"❌ Large file processing failed: {processing_result['error']}")
                        
                        # Fallback to standard processing for smaller files
                        if file_size_mb < 100:
                            st.info("🔄 Attempting fallback to standard processing...")
                            try:
                                results = process_audio_pipeline(uploaded_file)
                                if results:
                                    st.session_state.current_results = results
                            except Exception as e:
                                st.error(f"❌ Fallback processing also failed: {str(e)}")
    
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