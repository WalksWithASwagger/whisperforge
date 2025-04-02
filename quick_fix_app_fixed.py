"""
WhisperForge Pipeline Demo - Enhanced version with structured pipeline stages
"""
import streamlit as st
import os
import tempfile
import time
import json
from pathlib import Path
import logging
import asyncio
from openai import OpenAI
from datetime import datetime
import re

# Add Notion client import
try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisperforge")

# Page config
st.set_page_config(
    page_title="WhisperForge Pipeline Demo",
    page_icon="🎙️",
    layout="wide"
)

# Basic styling
st.markdown("""
<style>
/* Modern UI styling */
.main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}
.section-header {
    background-color: #1E1E1E;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #4CAF50;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 16px;
    background-color: #1E1E1E;
    border-radius: 4px 4px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: #2E2E2E;
    border-bottom: 2px solid #4CAF50;
}

/* Button styling */
.stButton button {
    border-radius: 4px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Card-like containers */
.css-card {
    background-color: #1E1E1E;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

/* Progress bar styling */
.stProgress > div > div {
    background-color: #4CAF50;
}

/* Tags styling */
.tag-item {
    display: inline-block;
    background-color: #2E2E2E;
    color: white;
    padding: 5px 10px;
    margin: 5px;
    border-radius: 15px;
    font-size: 0.85rem;
}

/* Status indicators */
.status-success {
    color: #4CAF50;
    font-weight: bold;
}
.status-error {
    color: #F44336;
    font-weight: bold;
}
.status-info {
    color: #2196F3;
    font-weight: bold;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.fade-in {
    animation: fadeIn 0.5s ease-in-out;
}

/* Tables with alternating rows */
.styled-table {
    width: 100%;
    border-collapse: collapse;
}
.styled-table th {
    background-color: #2E2E2E;
    padding: 8px 12px;
    text-align: left;
}
.styled-table tr:nth-child(even) {
    background-color: #1A1A1A;
}
.styled-table tr:nth-child(odd) {
    background-color: #222222;
}
.styled-table td {
    padding: 8px 12px;
    border-top: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="section-header"><h1 style="color:white; margin:0;">🎙️ WhisperForge</h1><p style="color:#CCC; margin:0; font-size:1.1rem;">Audio to Content Generation Pipeline</p></div>', unsafe_allow_html=True)

# Configuration sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Templates (New!)
    st.subheader("Workflow Templates")
    
    # Initialize templates in session state if not exists
    if "workflow_templates" not in st.session_state:
        # Default templates
        st.session_state["workflow_templates"] = {
            "Full Content Package": {
                "description": "Complete content generation with all steps",
                "pipeline_type": "Default (Full)",
                "enable_editor": True,
                "editor_targets": ["Outline", "Blog Post", "Social Media"],
                "generate_images": True
            },
            "Quick Social": {
                "description": "Extract wisdom and generate social posts only",
                "pipeline_type": "Social Media Only", 
                "enable_editor": True,
                "editor_targets": ["Social Media"],
                "generate_images": False
            },
            "Blog Creation": {
                "description": "Create an outline and blog post without social",
                "pipeline_type": "Default (Full)",
                "enable_editor": True,
                "editor_targets": ["Outline", "Blog Post"],
                "generate_images": True
            }
        }
    
    # Template selector
    template_names = list(st.session_state["workflow_templates"].keys()) + ["Custom"]
    selected_template = st.selectbox("Select Workflow Template", template_names)
    
    # Load template if selected
    if selected_template != "Custom":
        template = st.session_state["workflow_templates"][selected_template]
        st.info(f"**{selected_template}**: {template['description']}")
    else:
        st.warning("Using custom configuration")
    
    # API Keys
    with st.expander("API Keys", expanded=False):
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
        API_KEY = st.text_input("OpenAI API Key", value=OPENAI_API_KEY, type="password")
        if API_KEY:
            os.environ["OPENAI_API_KEY"] = API_KEY
        
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
        anthropic_key = st.text_input("Anthropic API Key (Optional)", value=ANTHROPIC_API_KEY, type="password")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        
        # Add Notion API key
        NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
        notion_key = st.text_input("Notion API Key (Optional)", value=NOTION_API_KEY, type="password")
        if notion_key:
            os.environ["NOTION_API_KEY"] = notion_key
        
        # Add Notion Database ID (only show if Notion API key is provided)
        if notion_key:
            NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
            notion_db_id = st.text_input("Notion Database ID", value=NOTION_DATABASE_ID)
            if notion_db_id:
                os.environ["NOTION_DATABASE_ID"] = notion_db_id
    
    # Model selection
    st.subheader("Model Selection")
    ai_provider = st.selectbox("AI Provider", ["OpenAI", "Anthropic"], index=0)
    
    if ai_provider == "OpenAI":
        ai_model = st.selectbox("Model", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"], index=0)
    else:
        ai_model = st.selectbox("Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229"], index=1)
    
    # Knowledge base
    st.subheader("Knowledge Base")
    kb_file = st.file_uploader("Upload Knowledge Base File (Optional)", type=["txt", "md"])
    if kb_file:
        st.session_state["knowledge_base"] = kb_file.getvalue().decode("utf-8")
    
    # Global Style (New!)
    st.subheader("Content Style")
    content_style = st.selectbox(
        "Global Tone",
        ["Strategic/Professional", "Casual/Conversational", "Executive Summary", "Contrarian/Inspirational"],
        index=0
    )
    
    # Set system prompts based on content style if no custom prompts defined
    if "system_prompts" not in st.session_state:
        # Default prompt templates  
        if content_style == "Casual/Conversational":
            # Initialize casual style prompts
            st.session_state["system_prompts"] = {
                "wisdom": """You are a friendly, conversational expert who extracts simple but valuable insights from conversations.
Present your extraction as accessible bullet points using everyday language. Avoid jargon and stiff phrasing.
Make it sound like advice from a smart friend, not a corporate document.""",
                
                "outline": """You are creating a casual, engaging outline for content that feels like a conversation.
Use simple section headings that sound like you're chatting with a friend.
Include questions, personal asides, and a warm, approachable structure.""",
                
                "blog": """You are writing a casual, conversational blog post that feels personal and authentic.
Use first-person perspective, contractions, questions to the reader, and occasional humor.
Write like you're explaining something interesting to a friend - clear, engaging, and without unnecessary formality.""",
                
                "editor": """You are a friendly editor who maintains a conversational, approachable tone.
Your job is to make the content more engaging and personal while keeping it clear.
Add more conversational elements, use contractions, simplify complex ideas, and make it sound authentic."""
            }
        elif content_style == "Executive Summary":
            # Initialize executive style prompts
            st.session_state["system_prompts"] = {
                "wisdom": """You are extracting high-value strategic insights for busy executives.
Focus only on actionable, business-critical points with clear implications.
Format as concise, numbered bullet points with absolutely no fluff or explanation.""",
                
                "outline": """You are creating a highly structured, executive-focused outline.
Use clear, action-oriented section headings focused on strategic outcomes and business value.
Keep everything extremely concise - this is for busy decision-makers who need clarity and brevity.""",
                
                "blog": """You are writing an executive-level briefing that respects the reader's time.
Start with key findings/recommendations first, then supporting evidence.
Use short paragraphs, bullet points, subheadings, and a formal, authoritative tone throughout.""",
                
                "editor": """You are an executive editor who optimizes content for senior leadership.
Your job is to:
1. Eliminate all unnecessary words and explanations
2. Ensure the most important points appear first
3. Create a clear hierarchy of information with business-critical insights highlighted
4. Maintain a professional, authoritative tone"""
            }
        elif content_style == "Contrarian/Inspirational":
            # Initialize contrarian style prompts
            st.session_state["system_prompts"] = {
                "wisdom": """You are extracting provocative, counter-intuitive insights that challenge conventional thinking.
Identify the most surprising or paradigm-shifting ideas in the content.
Format as bold statements that make the reader question their assumptions.""",
                
                "outline": """You are creating an outline for content that will inspire and challenge readers.
Use provocative section headings that confront conventional wisdom.
Structure should build toward a transformative perspective or call-to-action.""",
                
                "blog": """You are writing a bold, inspirational piece that challenges the status quo.
Use powerful, emotionally resonant language and rhetorical techniques (metaphors, contrasts, repetition).
Create a sense of urgency about change while offering a fresh perspective that gives readers hope.""",
                
                "editor": """You are an editor who enhances content to make it more memorable and paradigm-shifting.
Your job is to:
1. Amplify the boldest claims and most provocative insights
2. Add inspirational language and powerful metaphors
3. Create more emotional contrast between problems and solutions
4. Ensure the content feels fresh and different from conventional wisdom"""
            }
    
    # Show selected style description
    if content_style == "Strategic/Professional":
        st.info("**Strategic/Professional**: Clear, insightful tone focused on practical strategy and valuable frameworks. High signal-to-noise ratio with a polished, authoritative voice.")
    elif content_style == "Casual/Conversational":  
        st.info("**Casual/Conversational**: Friendly, approachable tone using everyday language. Sounds like advice from a smart friend rather than a formal document.")
    elif content_style == "Executive Summary":
        st.info("**Executive Summary**: Ultra-concise, high-level content for busy decision-makers. Prioritizes key findings and actionable insights with minimal explanation.")
    elif content_style == "Contrarian/Inspirational":
        st.info("**Contrarian/Inspirational**: Bold, provocative tone that challenges conventional thinking. Uses emotionally resonant language to inspire new perspectives.")
    
    # Pipeline options
    st.subheader("Pipeline Options")
    
    # Apply template settings if template is selected
    if selected_template != "Custom":
        pipeline_type = template["pipeline_type"]
        enable_editor = template["enable_editor"]
        editor_targets = template["editor_targets"]
        generate_images = template["generate_images"]
        
        # Display the template settings
        st.write(f"Template Pipeline: **{pipeline_type}**")
        st.write(f"Editor Enabled: **{'Yes' if enable_editor else 'No'}**")
        if enable_editor:
            st.write(f"Editor Targets: **{', '.join(editor_targets)}**")
        st.write(f"Image Prompts: **{'Enabled' if generate_images else 'Disabled'}**")
        
        # Allow overriding template
        edit_template = st.checkbox("Modify Template Settings", value=False)
        if edit_template:
            # Show standard options but initialize with template values
            pipeline_type = st.selectbox(
                "Pipeline Type",
                ["Default (Full)", "Minimal", "Social Media Only"],
                index=["Default (Full)", "Minimal", "Social Media Only"].index(pipeline_type)
            )
            enable_editor = st.checkbox("Apply Editor Pass", value=enable_editor)
            if enable_editor:
                editor_targets = st.multiselect(
                    "Apply Editor To", 
                    ["Outline", "Blog Post", "Social Media"],
                    default=editor_targets
                )
            generate_images = st.checkbox("Generate Image Prompts", value=generate_images)
    else:
        # Regular options without template
        pipeline_type = st.selectbox(
            "Pipeline Type",
            ["Default (Full)", "Minimal", "Social Media Only"],
            index=0
        )
        enable_editor = st.checkbox("Apply Editor Pass", value=True)
        if enable_editor:
            editor_targets = st.multiselect(
                "Apply Editor To", 
                ["Outline", "Blog Post", "Social Media"],
                default=["Blog Post", "Social Media"]
            )
        generate_images = st.checkbox("Generate Image Prompts", value=True)
    
    # Save template option
    if selected_template == "Custom" or (selected_template != "Custom" and edit_template):
        st.subheader("Save Configuration")
        new_template_name = st.text_input("Template Name (Optional)")
        template_description = st.text_input("Template Description (Optional)")
        
        if st.button("Save as Template") and new_template_name:
            # Create new template
            st.session_state["workflow_templates"][new_template_name] = {
                "description": template_description or f"Custom template created on {datetime.now().strftime('%Y-%m-%d')}",
                "pipeline_type": pipeline_type,
                "enable_editor": enable_editor,
                "editor_targets": editor_targets if enable_editor else [],
                "generate_images": generate_images
            }
            st.success(f"Template '{new_template_name}' saved!")
            # Rerun to update the template selector
            st.experimental_rerun()
            
    # Load existing templates as card view
    with st.expander("Manage Templates", expanded=False):
        st.subheader("Your Templates")
        for name, template_data in st.session_state["workflow_templates"].items():
            st.markdown(f"""
            <div class="css-card">
                <h4>{name}</h4>
                <p><em>{template_data['description']}</em></p>
                <p>Pipeline: <b>{template_data['pipeline_type']}</b></p>
                <p>Editor: {'✅' if template_data['enable_editor'] else '❌'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Load '{name}'", key=f"load_{name}"):
                    # Set the template selector to this template
                    st.session_state["template_selector"] = name
                    st.experimental_rerun()
            with col2:
                if st.button(f"Delete '{name}'", key=f"delete_{name}"):
                    # Ask for confirmation before deleting
                    if name in st.session_state["workflow_templates"]:
                        del st.session_state["workflow_templates"][name]
                        st.success(f"Template '{name}' deleted.")
                        st.experimental_rerun()
    
    # Advanced Settings
    st.subheader("Advanced Settings")
    show_advanced = st.checkbox("Show Advanced Settings", value=False)
    
    if show_advanced:
        # Create tabs for different prompt categories
        adv_tabs = st.tabs(["Content", "Editor", "Social", "Images"])
        
        with adv_tabs[0]:
            # Initialize default prompts if not in session state
            if "system_prompts" not in st.session_state:
                st.session_state["system_prompts"] = {
                    "wisdom": """You are an expert at extracting key insights, lessons, and actionable wisdom from transcripts.
Focus on identifying the most valuable ideas that would be useful to someone who hasn't heard the audio.
Present your extraction as a bullet-point list of wisdom notes.""",
                    
                    "outline": """You are an expert content strategist who creates well-structured outlines.
Create a logical, comprehensive outline with clear sections and subsections.
The outline should follow a natural progression of ideas and cover all key points.""",
                    
                    "blog": """You are an expert content writer who creates engaging, informative articles.
Follow the provided outline closely while expanding on each point with relevant details from the transcript.
Write in a clear, engaging style with good paragraph structure, transitions, and flow.""",
                }
            
            st.markdown("#### Content Generation Prompts")
            
            st.session_state["system_prompts"]["wisdom"] = st.text_area(
                "Wisdom Extraction System Prompt", 
                value=st.session_state["system_prompts"].get("wisdom", ""),
                height=150
            )
            
            st.session_state["system_prompts"]["outline"] = st.text_area(
                "Outline Generation System Prompt", 
                value=st.session_state["system_prompts"].get("outline", ""),
                height=150
            )
            
            st.session_state["system_prompts"]["blog"] = st.text_area(
                "Blog Post Generation System Prompt", 
                value=st.session_state["system_prompts"].get("blog", ""),
                height=150
            )
        
        with adv_tabs[1]:
            # Editor prompt
            if "editor" not in st.session_state["system_prompts"]:
                st.session_state["system_prompts"]["editor"] = """You are a strategic editor who knows my tone and goals.
Your job is to review the content and provide:
1. Clear revision notes (structure, clarity, voice, impact)
2. A cleaner, improved version of the content

Do not change my voice—refine and focus the ideas. Be concise and specific.
Maintain the core message while enhancing its delivery."""
            
            st.markdown("#### Editorial Enhancement Prompt")
            
            st.session_state["system_prompts"]["editor"] = st.text_area(
                "Editor System Prompt", 
                value=st.session_state["system_prompts"].get("editor", ""),
                height=200
            )
        
        with adv_tabs[2]:
            # Social media prompt
            if "social" not in st.session_state["system_prompts"]:
                st.session_state["system_prompts"]["social"] = """You are a social media content specialist who creates engaging posts for different platforms.
For each platform, create content that:
- Respects the platform's style, tone, and length constraints
- Highlights key insights in an engaging way
- Uses appropriate formatting (hashtags for Twitter, more professional tone for LinkedIn)

FORMAT YOUR RESPONSE AS:
## Twitter
[First Tweet]
[Second Tweet]

## LinkedIn
[LinkedIn post]

## Facebook
[Facebook post]"""
            
            st.markdown("#### Social Media Prompts")
            
            st.session_state["system_prompts"]["social"] = st.text_area(
                "Social Media System Prompt", 
                value=st.session_state["system_prompts"].get("social", ""),
                height=200
            )
            
        with adv_tabs[3]:
            # Image prompt generation prompt
            if "image_prompts" not in st.session_state["system_prompts"]:
                st.session_state["system_prompts"]["image_prompts"] = """You are an expert at creating detailed, visually compelling image prompts.
Generate prompts that capture key ideas from content as visual metaphors.
Each prompt should be specific enough to produce a consistent, high-quality image 
when used with DALL-E, Midjourney or similar image generation AI."""
            
            st.markdown("#### Image Prompts")
            
            st.session_state["system_prompts"]["image_prompts"] = st.text_area(
                "Image Prompt Generation System Prompt", 
                value=st.session_state["system_prompts"].get("image_prompts", ""),
                height=200
            )
            
        # Reset button
        if st.button("Reset to Default Prompts"):
            # Default system prompts
            st.session_state["system_prompts"] = {
                "wisdom": """You are an expert at extracting key insights, lessons, and actionable wisdom from transcripts.
Focus on identifying the most valuable ideas that would be useful to someone who hasn't heard the audio.
Present your extraction as a bullet-point list of wisdom notes.""",
                
                "outline": """You are an expert content strategist who creates well-structured outlines.
Create a logical, comprehensive outline with clear sections and subsections.
The outline should follow a natural progression of ideas and cover all key points.""",
                
                "blog": """You are an expert content writer who creates engaging, informative articles.
Follow the provided outline closely while expanding on each point with relevant details from the transcript.
Write in a clear, engaging style with good paragraph structure, transitions, and flow.""",
                
                "editor": """You are a strategic editor who knows my tone and goals.
Your job is to review the content and provide:
1. Clear revision notes (structure, clarity, voice, impact)
2. A cleaner, improved version of the content

Do not change my voice—refine and focus the ideas. Be concise and specific.
Maintain the core message while enhancing its delivery.""",
                
                "social": """You are a social media content specialist who creates engaging posts for different platforms.
For each platform, create content that:
- Respects the platform's style, tone, and length constraints
- Highlights key insights in an engaging way
- Uses appropriate formatting (hashtags for Twitter, more professional tone for LinkedIn)

FORMAT YOUR RESPONSE AS:
## Twitter
[First Tweet]
[Second Tweet]

## LinkedIn
[LinkedIn post]

## Facebook
[Facebook post]""",
                
                "image_prompts": """You are an expert at creating detailed, visually compelling image prompts.
Generate prompts that capture key ideas from content as visual metaphors.
Each prompt should be specific enough to produce a consistent, high-quality image 
when used with DALL-E, Midjourney or similar image generation AI."""
            }
            st.success("Prompts have been reset to defaults.")

# Initialize clients
def get_openai_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

def get_anthropic_client():
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        return None

# Initialize Notion client
def get_notion_client():
    """Initialize and return a Notion client"""
    try:
        if NotionClient is None:
            logger.error("Notion client library not installed")
            return None
            
        notion_key = os.environ.get("NOTION_API_KEY", "")
        if not notion_key:
            logger.warning("Notion API key not set")
            return None
            
        return NotionClient(auth=notion_key)
    except Exception as e:
        logger.error(f"Error initializing Notion client: {str(e)}")
        return None

# Pipeline Steps
async def extract_wisdom(transcript, provider, model, knowledge_base=None):
    """Extract key insights and wisdom from transcript"""
    try:
        if not transcript:
            return "Error: No transcript provided"
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("wisdom", 
            """You are an expert at extracting key insights, lessons, and actionable wisdom from transcripts.
            Focus on identifying the most valuable ideas that would be useful to someone who hasn't heard the audio.
            Present your extraction as a bullet-point list of wisdom notes.""")
        
        prompt = f"Extract the key insights, wisdom, and actionable takeaways from this transcript.\n\nTRANSCRIPT:\n{transcript}"
        
        # Add knowledge base context if provided
        if knowledge_base:
            prompt += f"\n\nUSE THIS ADDITIONAL CONTEXT TO INFORM YOUR EXTRACTION:\n{knowledge_base}"
        
        # Use different providers
        if provider.lower() == "anthropic":
            return await generate_with_anthropic(system_prompt, prompt, model)
        else:
            return await generate_with_openai(system_prompt, prompt, model)
            
    except Exception as e:
        logger.exception(f"Error in wisdom extraction: {str(e)}")
        return f"Error extracting wisdom: {str(e)}"

async def generate_outline(transcript, wisdom, provider, model, knowledge_base=None):
    """Generate a structured outline for content based on transcript and wisdom"""
    try:
        if not transcript:
            return "Error: No transcript provided"
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("outline", 
            """You are an expert content strategist who creates well-structured outlines.
            Create a logical, comprehensive outline with clear sections and subsections.
            The outline should follow a natural progression of ideas and cover all key points.""")
        
        prompt = f"""Create a structured outline for a blog post or article based on this transcript and extracted wisdom.
        
        TRANSCRIPT:
        {transcript[:2000]}... [transcript continues]
        
        EXTRACTED WISDOM:
        {wisdom}
        
        Your outline should have:
        - A compelling headline/title
        - 4-7 main sections with clear headings
        - Relevant subsections where appropriate
        - A logical flow from introduction to conclusion
        """
        
        # Add knowledge base context if provided
        if knowledge_base:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{knowledge_base}"
        
        # Use different providers
        if provider.lower() == "anthropic":
            return await generate_with_anthropic(system_prompt, prompt, model)
        else:
            return await generate_with_openai(system_prompt, prompt, model)
            
    except Exception as e:
        logger.exception(f"Error in outline generation: {str(e)}")
        return f"Error generating outline: {str(e)}"

async def generate_social_content(wisdom, outline, provider, model, knowledge_base=None):
    """Generate social media content from wisdom and outline"""
    try:
        # Basic validation
        if not wisdom and not outline:
            return "Error: No content provided for social media generation"
        
        content_to_generate_from = ""
        if wisdom: 
            content_to_generate_from += f"WISDOM NOTES:\n{wisdom}\n\n"
        if outline:
            content_to_generate_from += f"CONTENT OUTLINE:\n{outline}\n\n"
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("social", 
            """You are a social media content specialist who creates engaging posts for different platforms.
            For each platform, create content that:
            - Respects the platform's style, tone, and length constraints
            - Highlights key insights in an engaging way
            - Uses appropriate formatting (hashtags for Twitter, more professional tone for LinkedIn)
            
            FORMAT YOUR RESPONSE AS:
            ## Twitter
            [First Tweet]
            [Second Tweet]
            
            ## LinkedIn
            [LinkedIn post]
            
            ## Facebook
            [Facebook post]""")
        
        prompt = f"""Generate social media posts based on the following content:
        
        {content_to_generate_from}
        
        Create:
        - 2-3 Twitter posts (under 280 characters each)
        - 1 LinkedIn post (professional tone, up to 3 paragraphs)
        - 1 Facebook post (conversational tone, 2-3 paragraphs)
        
        Each post should highlight different aspects of the content in an engaging way.
        """
        
        # Use different providers
        if provider.lower() == "anthropic":
            return await generate_with_anthropic(system_prompt, prompt, model)
        else:
            return await generate_with_openai(system_prompt, prompt, model)
            
    except Exception as e:
        logger.exception(f"Error in social content generation: {str(e)}")
        return f"Error generating social content: {str(e)}"

async def generate_article(transcript, wisdom, outline, provider, model, knowledge_base=None):
    """Generate a full article from transcript, wisdom and outline"""
    try:
        if not transcript or not outline:
            return "Error: Transcript and outline are required for article generation"
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("blog", 
            """You are an expert content writer who creates engaging, informative articles.
            Follow the provided outline closely while expanding on each point with relevant details from the transcript.
            Write in a clear, engaging style with good paragraph structure, transitions, and flow.""")
        
        prompt = f"""Create a full article based on this transcript, wisdom notes, and outline.
        
        TRANSCRIPT:
        {transcript[:2000]}... [transcript continues]
        
        WISDOM NOTES:
        {wisdom}
        
        OUTLINE:
        {outline}
        
        Create a fully-formed article that:
        - Follows the provided outline structure
        - Incorporates the key points from the wisdom notes
        - Uses relevant information from the transcript
        - Has a clear introduction, body, and conclusion
        - Is written in an engaging, informative style
        """
        
        # Add knowledge base context if provided
        if knowledge_base:
            prompt += f"\n\nADDITIONAL CONTEXT TO INFORM YOUR WRITING:\n{knowledge_base}"
        
        # Use different providers
        if provider.lower() == "anthropic":
            return await generate_with_anthropic(system_prompt, prompt, model)
        else:
            return await generate_with_openai(system_prompt, prompt, model)
            
    except Exception as e:
        logger.exception(f"Error in article generation: {str(e)}")
        return f"Error generating article: {str(e)}"

# Provider-specific generation functions
async def generate_with_openai(system_prompt, user_prompt, model):
    """Generate content using OpenAI"""
    try:
        client = get_openai_client()
        if not client:
            return "Error: OpenAI client not available"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error with OpenAI generation: {str(e)}")
        return f"Error: {str(e)}"

async def generate_with_anthropic(system_prompt, user_prompt, model):
    """Generate content using Anthropic"""
    try:
        client = get_anthropic_client()
        if not client:
            return "Error: Anthropic client not available"
        
        response = client.messages.create(
            model=model,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500
        )
        
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error with Anthropic generation: {str(e)}")
        return f"Error: {str(e)}"

# Simple transcription function
async def transcribe_audio(file_path):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        client = get_openai_client()
        if not client:
            return "Error: OpenAI client not available"
            
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1"
            )
        return response.text
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return f"Error: {str(e)}"

# Function to save content to Notion
async def save_to_notion(title, content_data):
    """Save content to a Notion database
    
    Args:
        title (str): Title for the Notion page
        content_data (dict): Dictionary of content to save
    
    Returns:
        tuple: (success, message)
    """
    try:
        notion_client = get_notion_client()
        if not notion_client:
            return False, "Notion client not available. Check your API key."
        
        database_id = os.environ.get("NOTION_DATABASE_ID", "")
        if not database_id:
            return False, "Notion Database ID not set."
        
        # Create properties for the page
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Generated"}},
            "Source": {"select": {"name": "WhisperForge"}},
            "Date Created": {"date": {"start": datetime.now().isoformat()}}
        }
        
        # Add tags if available
        if "tags" in content_data:
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in content_data["tags"][:5]]}  # Limit to 5 tags
        
        # Create the page
        page = notion_client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=[
                # Summary block
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content": content_data.get("summary", "")}}],
                        "icon": {"emoji": "💡"}
                    }
                },
                # Separator
                {
                    "object": "block",
                    "type": "divider"
                }
            ]
        )
        
        # Add the content blocks
        content_blocks = []
        
        # Add Wisdom Notes
        if "wisdom" in content_data:
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Wisdom Notes"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data["wisdom"]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider"
                }
            ])
        
        # Add Outline
        if "outline" in content_data:
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Content Outline"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data["outline"]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider"
                }
            ])
        
        # Add Blog Post
        if "blog_post" in content_data:
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Blog Post"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data["blog_post"]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider"
                }
            ])
        
        # Add Social Media Content
        if "social_content" in content_data:
            content_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Social Media Content"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content_data["social_content"]}}]
                    }
                }
            ])
        
        # Add the content blocks in batches of 100 (Notion API limit)
        for i in range(0, len(content_blocks), 100):
            batch = content_blocks[i:i+100]
            notion_client.blocks.children.append(
                block_id=page["id"],
                children=batch
            )
        
        return True, f"Content successfully saved to Notion: {page['url']}"
    
    except Exception as e:
        logger.exception(f"Error saving to Notion: {str(e)}")
        return False, f"Error saving to Notion: {str(e)}"

# Additional pipeline steps
async def generate_summary(wisdom, outline, provider, model):
    """Generate a summary of the content"""
    try:
        system_prompt = """You are an expert at creating concise, engaging summaries.
        Create a 2-3 sentence summary that captures the essence of the content and makes the reader want to learn more."""
        
        prompt = f"""Create a brief, compelling summary of this content:
        
        WISDOM NOTES:
        {wisdom}
        
        OUTLINE:
        {outline}
        
        Your summary should:
        - Be 2-3 sentences long
        - Capture the key insight or value
        - Create curiosity to read the full content
        - Use an engaging, professional tone
        """
        
        # Use different providers
        if provider.lower() == "anthropic":
            return await generate_with_anthropic(system_prompt, prompt, model)
        else:
            return await generate_with_openai(system_prompt, prompt, model)
            
    except Exception as e:
        logger.exception(f"Error in summary generation: {str(e)}")
        return f"Error generating summary: {str(e)}"

async def generate_tags(wisdom, outline, provider, model):
    """Generate tags for the content"""
    try:
        system_prompt = """You are an expert at categorizing content and extracting relevant keywords.
        Create a set of tags that accurately represent the content and would be useful for search and organization."""
        
        prompt = f"""Generate 5-7 relevant tags for this content:
        
        WISDOM NOTES:
        {wisdom}
        
        OUTLINE:
        {outline}
        
        Your tags should:
        - Be 1-3 words each
        - Cover the main topics and themes
        - Include important concepts or frameworks mentioned
        - Be relevant for search and categorization
        
        Format your response as a comma-separated list.
        """
        
        # Use different providers
        if provider.lower() == "anthropic":
            tags_text = await generate_with_anthropic(system_prompt, prompt, model)
        else:
            tags_text = await generate_with_openai(system_prompt, prompt, model)
        
        # Parse the comma-separated list into a list of tags
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        return tags
            
    except Exception as e:
        logger.exception(f"Error generating tags: {str(e)}")
        return []

# Add Editor step to pipeline
async def editor_enhancement(content, content_type, provider, model, knowledge_base=None):
    """Apply editorial improvements to content
    
    Args:
        content (str): The content to be edited
        content_type (str): Type of content (outline, blog, social)
        provider (str): AI provider (OpenAI, Anthropic)
        model (str): Model to use
        knowledge_base (str, optional): Optional knowledge base context
        
    Returns:
        dict: Dictionary with edited content and editorial notes
    """
    try:
        if not content:
            return {"edited_content": "", "notes": "Error: No content provided for editing"}
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("editor", 
            """You are a strategic editor who knows my tone and goals.
            Your job is to review the content and provide:
            1. Clear revision notes (structure, clarity, voice, impact)
            2. A cleaner, improved version of the content
            
            Do not change my voice—refine and focus the ideas. Be concise and specific.
            Maintain the core message while enhancing its delivery.""")
        
        # Adjust prompt based on content type
        if content_type == "outline":
            prompt = f"""Review this content outline and improve it:

OUTLINE:
{content}

Provide:
1. REVISION NOTES: Identify 2-3 specific improvements for structure, clarity and impact
2. IMPROVED OUTLINE: A revised version that maintains my voice but enhances the structure and flow

The outline should have a compelling title, clear sections, and a logical progression of ideas.
"""
        elif content_type == "blog":
            prompt = f"""Review this blog post and improve it:

BLOG POST:
{content}

Provide:
1. REVISION NOTES: Identify 3-5 specific improvements for structure, clarity, voice and impact
2. IMPROVED POST: A revised version that maintains my voice but enhances readability and impact

Focus on maintaining a strategic, insightful tone with good paragraph structure and flow.
The post should have a compelling introduction, clear sections, and a meaningful conclusion.
"""
        elif content_type == "social":
            prompt = f"""Review these social media posts and improve them:

SOCIAL POSTS:
{content}

Provide:
1. REVISION NOTES: Identify 2-3 specific improvements for clarity, engagement and platform fit
2. IMPROVED POSTS: Revised versions that maintain my voice but enhance engagement

Each post should be optimized for its platform while maintaining my strategic, insightful voice.
"""
        else:
            prompt = f"""Review this content and improve it:

CONTENT:
{content}

Provide:
1. REVISION NOTES: Identify 2-3 specific improvements for clarity and impact
2. IMPROVED CONTENT: A revised version that maintains my voice but enhances quality
"""
        
        # Add knowledge base context if provided
        if knowledge_base:
            prompt += f"\n\nUSE THIS VOICE REFERENCE TO MATCH MY STYLE:\n{knowledge_base}"
        
        # Use different providers
        if provider.lower() == "anthropic":
            response = await generate_with_anthropic(system_prompt, prompt, model)
        else:
            response = await generate_with_openai(system_prompt, prompt, model)
        
        # Parse the response to separate notes from content
        # Look for common separators in the response
        edited_content = response
        notes = ""
        
        # Try to extract notes and content by looking for common patterns
        for separator in ["IMPROVED CONTENT:", "IMPROVED OUTLINE:", "IMPROVED POST:", "IMPROVED POSTS:", "REVISED VERSION:"]:
            if separator in response:
                parts = response.split(separator, 1)
                if len(parts) > 1:
                    notes = parts[0].replace("REVISION NOTES:", "").strip()
                    edited_content = parts[1].strip()
                    break
        
        # If we couldn't find a separator but there's REVISION NOTES:
        if notes == "" and "REVISION NOTES:" in response:
            parts = response.split("REVISION NOTES:", 1)
            if len(parts) > 1:
                # Further split by an empty line or multiple newlines
                content_parts = parts[1].split("\n\n", 1)
                if len(content_parts) > 1:
                    notes = content_parts[0].strip()
                    edited_content = content_parts[1].strip()
        
        return {
            "edited_content": edited_content,
            "notes": notes if notes else "Editorial review complete. Revisions incorporated."
        }
            
    except Exception as e:
        logger.exception(f"Error in editorial review: {str(e)}")
        return {
            "edited_content": content,
            "notes": f"Error during editorial review: {str(e)}"
        }

# Add image prompt generation function
async def generate_image_prompts(wisdom, outline, blog_post, provider, model, knowledge_base=None):
    """Generate visual image prompts based on the content
    
    Args:
        wisdom (str): Extracted wisdom notes
        outline (str): Content outline
        blog_post (str): Blog post content
        provider (str): AI provider (OpenAI, Anthropic)
        model (str): Model to use
        knowledge_base (str, optional): Optional knowledge base context
        
    Returns:
        list: List of image prompts
    """
    try:
        if not blog_post and not outline:
            return "Error: Insufficient content for generating image prompts"
        
        # Get system prompt from session state or use default
        system_prompt = st.session_state.get("system_prompts", {}).get("image_prompts", 
            """You are an expert at creating detailed, visually compelling image prompts.
            Generate prompts that capture key ideas from content as visual metaphors.
            Each prompt should be specific enough to produce a consistent, high-quality image 
            when used with DALL-E, Midjourney or similar image generation AI.""")
        
        content_to_use = blog_post if blog_post else outline
        
        prompt = f"""Create 5 detailed image prompts that capture the core ideas from this content:

WISDOM NOTES:
{wisdom}

CONTENT:
{content_to_use[:2000]}

For each image prompt:
1. Focus on a key concept, metaphor, or framework from the content
2. Be specific about style, composition, lighting, and mood
3. Include details that make the image unique and compelling
4. Make the image conceptually connected to the content themes
5. Format each prompt to be 2-3 sentences (50-100 words)

Number each prompt from 1-5 and make each one visually distinct from the others.
Each prompt should be suitable for AI image generation tools like DALL-E or Midjourney.
"""
        
        # Use different providers
        if provider.lower() == "anthropic":
            response = await generate_with_anthropic(system_prompt, prompt, model)
        else:
            response = await generate_with_openai(system_prompt, prompt, model)
        
        # Parse the response to extract individual prompts
        # Look for numbered prompts (1., 2., etc.)
        prompts = []
        current_prompt = ""
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new numbered prompt
            if re.match(r'^\d+[\.\)]', line):
                # Save the current prompt if it's not empty
                if current_prompt:
                    prompts.append(current_prompt.strip())
                    
                # Start a new prompt
                current_prompt = line
            else:
                # Continue with the current prompt
                current_prompt += " " + line
        
        # Add the last prompt
        if current_prompt:
            prompts.append(current_prompt.strip())
            
        return prompts
            
    except Exception as e:
        logger.exception(f"Error generating image prompts: {str(e)}")
        return f"Error generating image prompts: {str(e)}"

# Pipeline orchestrator
async def run_pipeline(transcript, pipeline_type, provider, model, knowledge_base=None, enable_editor=True, editor_targets=None, generate_images=True, progress_callback=None):
    """Run the content generation pipeline"""
    start_time = time.time()
    results = {
        "metrics": {
            "start_time": start_time,
            "step_metrics": {}
        },
        "errors": {},  # Track any errors for potential retry
        "retries": {}  # Track retry counts for each step
    }
    
    # If editor_targets is None, initialize with defaults
    if editor_targets is None:
        editor_targets = ["Blog Post", "Social Media"]
    
    # Track step timing
    async def run_step(step_name, step_function, *args, retry_count=0):
        step_start = time.time()
        try:
            result = await step_function(*args)
            step_duration = time.time() - step_start
            
            # Check if result is an error message
            if isinstance(result, str) and result.startswith("Error"):
                status = "error"
                results["errors"][step_name] = {
                    "message": result,
                    "args": args,
                    "function": step_function.__name__
                }
            else:
                status = "success"
                # If this was a retry and it succeeded, clear the error
                if step_name in results["errors"]:
                    del results["errors"][step_name]
            
            results["metrics"]["step_metrics"][step_name] = {
                "duration": step_duration,
                "status": status,
                "retry_count": retry_count
            }
            
            # Report progress if callback is provided
            if progress_callback:
                await progress_callback(step_name, status)
                
            return result
        except Exception as e:
            step_duration = time.time() - step_start
            error_message = f"Error in {step_name}: {str(e)}"
            logger.exception(error_message)
            
            # Store detailed error info for potential retry
            results["errors"][step_name] = {
                "message": error_message,
                "exception": str(e),
                "args": args,
                "function": step_function.__name__
            }
            
            results["metrics"]["step_metrics"][step_name] = {
                "duration": step_duration,
                "status": "error",
                "error": str(e),
                "retry_count": retry_count
            }
            
            # Report error if callback is provided
            if progress_callback:
                await progress_callback(step_name, "error")
                
            return error_message
    
    # Add a retry function
    async def retry_step(step_name):
        """Retry a failed pipeline step
        
        Args:
            step_name: Name of the step to retry
            
        Returns:
            The result of the retried step, or error message
        """
        if step_name not in results["errors"]:
            return f"Error: Step {step_name} has not failed or does not exist"
        
        # Get error info for the step
        error_info = results["errors"][step_name]
        
        # Track retry count
        retry_count = results.get("retries", {}).get(step_name, 0) + 1
        results.setdefault("retries", {})[step_name] = retry_count
        
        # Get the function and args
        step_function = globals()[error_info["function"]]
        args = error_info["args"]
        
        # Run the step again
        logger.info(f"Retrying step {step_name} (attempt {retry_count})")
        return await run_step(step_name, step_function, *args, retry_count=retry_count)
    
    # Store the retry function in results for external use
    results["retry_step"] = retry_step
    
    # Step 1: Extract wisdom (common to all pipeline types)
    wisdom = await run_step("wisdom", extract_wisdom, transcript, provider, model, knowledge_base)
    results["wisdom"] = {"wisdom": wisdom}
    
    # Different pipeline types
    if pipeline_type == "Social Media Only":
        # Social media only pipeline
        social_content = await run_step("social", generate_social_content, wisdom, "", provider, model, knowledge_base)
        results["social"] = {"social_content": social_content, "parsed_social_content": parse_social_content(social_content)}
        
        # Editor pass on social content if enabled
        if enable_editor and "Social Media" in editor_targets:
            editor_result = await run_step("editor_social", editor_enhancement, social_content, "social", provider, model, knowledge_base)
            results["editor_social"] = {
                "edited_social_content": editor_result["edited_content"],
                "editor_notes": editor_result["notes"],
                "parsed_social_content": parse_social_content(editor_result["edited_content"])
            }
    
    elif pipeline_type == "Minimal":
        # Minimal pipeline - wisdom + outline
        outline = await run_step("outline", generate_outline, transcript, wisdom, provider, model, knowledge_base)
        results["outline"] = {"outline": outline}
        
        # Editor pass on outline if enabled
        if enable_editor and "Outline" in editor_targets:
            editor_result = await run_step("editor_outline", editor_enhancement, outline, "outline", provider, model, knowledge_base)
            results["editor_outline"] = {
                "edited_outline": editor_result["edited_content"],
                "editor_notes": editor_result["notes"]
            }
            
            # Use edited outline for subsequent steps if available
            working_outline = editor_result["edited_content"] if "editor_outline" in results else outline
        else:
            working_outline = outline
        
        social_content = await run_step("social", generate_social_content, wisdom, working_outline, provider, model, knowledge_base)
        results["social"] = {"social_content": social_content, "parsed_social_content": parse_social_content(social_content)}
        
        # Editor pass on social content if enabled
        if enable_editor and "Social Media" in editor_targets:
            editor_result = await run_step("editor_social", editor_enhancement, social_content, "social", provider, model, knowledge_base)
            results["editor_social"] = {
                "edited_social_content": editor_result["edited_content"],
                "editor_notes": editor_result["notes"],
                "parsed_social_content": parse_social_content(editor_result["edited_content"])
            }
        
        # Generate image prompts if enabled
        if generate_images:
            image_prompts = await run_step("image_prompts", generate_image_prompts, wisdom, working_outline, "", provider, model, knowledge_base)
            results["image_prompts"] = {"prompts": image_prompts}
    
    else:
        # Full pipeline
        outline = await run_step("outline", generate_outline, transcript, wisdom, provider, model, knowledge_base)
        results["outline"] = {"outline": outline}
        
        # Editor pass on outline if enabled
        if enable_editor and "Outline" in editor_targets:
            editor_result = await run_step("editor_outline", editor_enhancement, outline, "outline", provider, model, knowledge_base)
            results["editor_outline"] = {
                "edited_outline": editor_result["edited_content"],
                "editor_notes": editor_result["notes"]
            }
            
            # Use edited outline for subsequent steps if available
            working_outline = editor_result["edited_content"] if "editor_outline" in results else outline
        else:
            working_outline = outline
        
        # Generate blog post using the outline (original or edited)
        blog_post = await run_step("blog", generate_article, transcript, wisdom, working_outline, provider, model, knowledge_base)
        results["blog"] = {"blog_post": blog_post, "blog_title": extract_title(working_outline)}
        
        # Editor pass on blog post if enabled
        if enable_editor and "Blog Post" in editor_targets:
            editor_result = await run_step("editor_blog", editor_enhancement, blog_post, "blog", provider, model, knowledge_base)
            results["editor_blog"] = {
                "edited_blog_post": editor_result["edited_content"],
                "editor_notes": editor_result["notes"]
            }
            
            # Use edited blog for subsequent steps if available
            working_blog = editor_result["edited_content"] if "editor_blog" in results else blog_post
        else:
            working_blog = blog_post
        
        # Generate social media content based on the outline and wisdom
        social_content = await run_step("social", generate_social_content, wisdom, working_outline, provider, model, knowledge_base)
        results["social"] = {"social_content": social_content, "parsed_social_content": parse_social_content(social_content)}
        
        # Editor pass on social content if enabled
        if enable_editor and "Social Media" in editor_targets:
            editor_result = await run_step("editor_social", editor_enhancement, social_content, "social", provider, model, knowledge_base)
            results["editor_social"] = {
                "edited_social_content": editor_result["edited_content"],
                "editor_notes": editor_result["notes"],
                "parsed_social_content": parse_social_content(editor_result["edited_content"])
            }
        
        # Generate image prompts if enabled
        if generate_images:
            image_prompts = await run_step("image_prompts", generate_image_prompts, wisdom, working_outline, working_blog, provider, model, knowledge_base)
            results["image_prompts"] = {"prompts": image_prompts}
    
    # Generate summary and tags for all pipeline types
    if "outline" in results and "outline" in results["outline"]:
        # Use edited outline if available
        working_outline = results.get("editor_outline", {}).get("edited_outline", results["outline"]["outline"])
        
        summary = await run_step("summary", generate_summary, wisdom, working_outline, provider, model)
        results["summary"] = {"summary": summary}
        
        tags = await run_step("tags", generate_tags, wisdom, working_outline, provider, model)
        results["tags"] = {"tags": tags}
    
    # Calculate total duration
    end_time = time.time()
    results["metrics"]["total_duration"] = end_time - start_time
    
    return results

# Helper functions
def parse_social_content(content):
    """Parse social content into platform-specific posts"""
    if not content or content.startswith("Error"):
        return {}
    
    platforms = {}
    current_platform = None
    current_posts = []
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("##") or line.startswith("# "):
            # Save previous platform posts if they exist
            if current_platform and current_posts:
                platforms[current_platform] = current_posts
                
            # Start new platform
            current_platform = line.replace("#", "").strip()
            current_posts = []
        elif current_platform:
            current_posts.append(line)
    
    # Add the last platform
    if current_platform and current_posts:
        platforms[current_platform] = current_posts
        
    return platforms

def extract_title(outline):
    """Extract title from outline"""
    if not outline:
        return "Generated Blog Post"
        
    lines = outline.split("\n")
    for line in lines[:5]:  # Check first few lines
        line = line.strip()
        if line and not line.startswith("#") and len(line) < 100:
            return line
    
    return "Generated Blog Post"

# Update the results display to include editor results
def display_editor_results(result_tabs, results, tab_index, content_type):
    """Display editor results in UI tabs
    
    Args:
        result_tabs: Streamlit tabs
        results: Pipeline results dict
        tab_index: Current tab index
        content_type: Type of content (outline, blog, social)
    
    Returns:
        int: Updated tab index
    """
    if content_type == "outline":
        with result_tabs[tab_index]:
            if "outline" in results and "outline" in results["outline"]:
                if "editor_outline" in results and "edited_outline" in results["editor_outline"]:
                    # Two columns for before/after
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Original Outline")
                        st.markdown(results["outline"]["outline"])
                    
                    with col2:
                        st.subheader("Edited Outline")
                        st.markdown(results["editor_outline"]["edited_outline"])
                        
                        # Editor notes
                        with st.expander("Editor Notes"):
                            st.markdown(results["editor_outline"]["editor_notes"])
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "Download Original Outline",
                            results["outline"]["outline"],
                            file_name="original_outline.md",
                            mime="text/markdown"
                        )
                    with col2:
                        st.download_button(
                            "Download Edited Outline",
                            results["editor_outline"]["edited_outline"],
                            file_name="edited_outline.md",
                            mime="text/markdown"
                        )
                else:
                    # Just show the original outline
                    st.subheader("Content Outline")
                    st.markdown(results["outline"]["outline"])
                    
                    # Download button
                    st.download_button(
                        "Download Outline",
                        results["outline"]["outline"],
                        file_name="outline.md",
                        mime="text/markdown"
                    )
            else:
                st.info("No outline generated.")
    
    elif content_type == "blog":
        with result_tabs[tab_index]:
            if "blog" in results and "blog_post" in results["blog"]:
                if "editor_blog" in results and "edited_blog_post" in results["editor_blog"]:
                    # Tabs for before/after - simpler way to handle long content
                    blog_tabs = st.tabs(["Edited Blog Post", "Original Blog Post", "Editor Notes"])
                    
                    with blog_tabs[0]:
                        st.subheader(results["blog"].get("blog_title", "Blog Post"))
                        st.markdown(results["editor_blog"]["edited_blog_post"])
                        
                        # Download button for edited blog
                        blog_content = f"# {results['blog'].get('blog_title', 'Blog Post')}\n\n{results['editor_blog']['edited_blog_post']}"
                        st.download_button(
                            "Download Edited Blog Post",
                            blog_content,
                            file_name="edited_blog_post.md",
                            mime="text/markdown"
                        )
                    
                    with blog_tabs[1]:
                        st.subheader(results["blog"].get("blog_title", "Original Blog Post"))
                        st.markdown(results["blog"]["blog_post"])
                        
                        # Download button for original blog
                        blog_content = f"# {results['blog'].get('blog_title', 'Blog Post')}\n\n{results['blog']['blog_post']}"
                        st.download_button(
                            "Download Original Blog Post",
                            blog_content,
                            file_name="original_blog_post.md",
                            mime="text/markdown"
                        )
                        
                    with blog_tabs[2]:
                        st.subheader("Editor Notes")
                        st.markdown(results["editor_blog"]["editor_notes"])
                else:
                    # Just show the original blog post
                    st.subheader(results["blog"].get("blog_title", "Blog Post"))
                    st.markdown(results["blog"]["blog_post"])
                    
                    # Download button for blog
                    blog_content = f"# {results['blog'].get('blog_title', 'Blog Post')}\n\n{results['blog']['blog_post']}"
                    st.download_button(
                        "Download Blog Post",
                        blog_content,
                        file_name="blog_post.md",
                        mime="text/markdown"
                    )
            else:
                st.info("No blog content generated.")
    
    elif content_type == "social":
        with result_tabs[tab_index]:
            if "social" in results and "parsed_social_content" in results["social"]:
                if "editor_social" in results and "edited_social_content" in results["editor_social"]:
                    # Tabs for before/after
                    social_tabs = st.tabs(["Edited Social Posts", "Original Social Posts", "Editor Notes"])
                    
                    with social_tabs[0]:
                        platforms = results["editor_social"]["parsed_social_content"]
                        
                        for platform, posts in platforms.items():
                            st.subheader(f"{platform} Posts")
                            for i, post in enumerate(posts, 1):
                                st.markdown(f"**Post {i}**")
                                st.markdown(post)
                                st.markdown("---")
                        
                        # Download button for edited social content
                        st.download_button(
                            "Download Edited Social Media Content",
                            results["editor_social"]["edited_social_content"],
                            file_name="edited_social_content.md",
                            mime="text/markdown"
                        )
                    
                    with social_tabs[1]:
                        platforms = results["social"]["parsed_social_content"]
                        
                        for platform, posts in platforms.items():
                            st.subheader(f"{platform} Posts")
                            for i, post in enumerate(posts, 1):
                                st.markdown(f"**Post {i}**")
                                st.markdown(post)
                                st.markdown("---")
                        
                        # Download button for original social content
                        st.download_button(
                            "Download Original Social Media Content",
                            results["social"]["social_content"],
                            file_name="original_social_content.md",
                            mime="text/markdown"
                        )
                    
                    with social_tabs[2]:
                        st.subheader("Editor Notes")
                        st.markdown(results["editor_social"]["editor_notes"])
                else:
                    # Just show the original social content
                    platforms = results["social"]["parsed_social_content"]
                    
                    for platform, posts in platforms.items():
                        st.subheader(f"{platform} Posts")
                        for i, post in enumerate(posts, 1):
                            st.markdown(f"**Post {i}**")
                            st.markdown(post)
                            st.markdown("---")
                    
                    # Download button for social content
                    st.download_button(
                        "Download Social Media Content",
                        results["social"]["social_content"],
                        file_name="social_content.md",
                        mime="text/markdown"
                    )
            else:
                st.info("No social media content generated.")
                
    return tab_index + 1

# Main app tabs
tab1, tab2 = st.tabs(["Transcription", "Content Pipeline"])

with tab1:
    st.markdown("### Upload Audio File")
    audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"], key="audio_file_uploader")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if audio_file:
            # Display audio
            st.audio(audio_file, format="audio/wav")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
                tmp_file.write(audio_file.getvalue())
                st.session_state["audio_file_path"] = tmp_file.name
                st.session_state["audio_file_name"] = audio_file.name
    
    with col2:
        # Transcribe button
        if "audio_file_path" in st.session_state:
            if st.button("Transcribe Audio", use_container_width=True):
                with st.spinner("Transcribing... This may take a minute."):
                    start_time = time.time()
                    transcript = asyncio.run(transcribe_audio(st.session_state["audio_file_path"]))
                    duration = time.time() - start_time
                    
                    if transcript.startswith("Error"):
                        st.error(transcript)
                    else:
                        st.session_state["transcript"] = transcript
                        st.success(f"Transcription completed in {duration:.2f} seconds!")
    
    # Show transcript if available
    if "transcript" in st.session_state:
        st.subheader("Transcript")
        st.text_area("", st.session_state["transcript"], height=300)
        
        # Save transcript option
        if st.button("Save Transcript", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{timestamp}.txt"
            
            with open(filename, "w") as f:
                f.write(st.session_state["transcript"])
            
            with open(filename, "rb") as f:
                st.download_button(
                    label="Download Transcript",
                    data=f,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True
                )

with tab2:
    st.markdown("### Content Generation")
    
    if "transcript" not in st.session_state:
        st.info("Please transcribe audio first to generate content.")
    else:
        # Pipeline options from sidebar
        st.write(f"Selected Pipeline: **{pipeline_type}**")
        st.write(f"AI Provider: **{ai_provider}** - Model: **{ai_model}**")
        
        # Display editor settings
        if enable_editor:
            st.write(f"Editor Pass: **Enabled** for {', '.join(editor_targets)}")
        else:
            st.write("Editor Pass: **Disabled**")
            
        # Display image prompt setting
        st.write(f"Image Prompts: **{'Enabled' if generate_images else 'Disabled'}**")
        
        # Knowledge base info
        if "knowledge_base" in st.session_state:
            kb_preview = st.session_state["knowledge_base"][:200] + "..."
            st.success(f"Knowledge base loaded ({len(st.session_state['knowledge_base'])} characters)")
        
        # Generate button
        if st.button("Generate Content", use_container_width=True):
            # Create a progress placeholder
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                progress_text = st.empty()
            
            with status_container:
                status_text = st.empty()
                status_text.info("Starting content generation pipeline...")
            
            with st.spinner("Generating content... This may take a few minutes."):
                knowledge_base = st.session_state.get("knowledge_base", None)
                
                # Track progress for display
                # Use a dictionary for current_step to work around nonlocal reference in nested functions
                progress_state = {"current_step": 0}
                total_steps = 5  # Base number of steps
                
                # Add steps based on pipeline type and options
                if pipeline_type == "Default (Full)":
                    total_steps = 7
                    if enable_editor:
                        total_steps += len(editor_targets)
                    if generate_images:
                        total_steps += 1
                elif pipeline_type == "Minimal":
                    total_steps = 5
                    if enable_editor:
                        total_steps += len(editor_targets)
                    if generate_images:
                        total_steps += 1
                else:  # Social Media Only
                    total_steps = 3
                    if enable_editor and "Social Media" in editor_targets:
                        total_steps += 1
                
                # Create a callback for progress updates
                async def progress_callback(step_name, status):
                    progress_state["current_step"] += 1
                    progress = min(progress_state["current_step"] / total_steps, 1.0)
                    progress_bar.progress(progress)
                    progress_text.text(f"Step {progress_state['current_step']}/{total_steps}: {step_name}")
                    if status == "success":
                        status_text.success(f"Completed: {step_name}")
                    else:
                        status_text.error(f"Error in: {step_name}")
                
                # Modified run_pipeline with progress callback
                results = asyncio.run(run_pipeline(
                    st.session_state["transcript"],
                    pipeline_type,
                    ai_provider,
                    ai_model,
                    knowledge_base,
                    enable_editor,
                    editor_targets,
                    generate_images,
                    progress_callback
                ))
                
                # Complete the progress bar
                progress_bar.progress(1.0)
                progress_text.text(f"Pipeline complete! {progress_state['current_step']}/{total_steps} steps finished")
                
                # Store results
                st.session_state["pipeline_results"] = results
                
                # Show completion message
                if "metrics" in results:
                    duration = results["metrics"]["total_duration"]
                    step_count = len(results["metrics"]["step_metrics"])
                    success_steps = sum(1 for step, metrics in results["metrics"]["step_metrics"].items() if metrics.get("status") == "success")
                    
                    status_text.success(f"Pipeline completed in {duration:.2f} seconds - {success_steps}/{step_count} steps successful!")
        
        # Display results if available
        if "pipeline_results" in st.session_state:
            results = st.session_state["pipeline_results"]
            
            # Calculate number of successful steps
            success_count = sum(1 for step, metrics in results.get("metrics", {}).get("step_metrics", {}).items() 
                               if metrics.get("status") == "success")
            total_steps = len(results.get("metrics", {}).get("step_metrics", {}))
            
            # Create tabs for different content types
            result_tabs = []
            
            if pipeline_type == "Default (Full)":
                result_tabs = st.tabs(["Wisdom", "Outline", "Blog Content", "Social Media", "Image Prompts", "Summary & Tags", "Metrics", "Export"])
            elif pipeline_type == "Minimal":
                result_tabs = st.tabs(["Wisdom", "Outline", "Social Media", "Image Prompts", "Summary & Tags", "Metrics", "Export"])
            else:  # Social Media Only
                result_tabs = st.tabs(["Wisdom", "Social Media", "Summary & Tags", "Metrics", "Export"])
            
            # Wisdom Tab (common to all pipelines)
            with result_tabs[0]:
                if "wisdom" in results and "wisdom" in results["wisdom"]:
                    st.subheader("Extracted Wisdom")
                    st.markdown(results["wisdom"]["wisdom"])
                    
                    # Download button
                    st.download_button(
                        "Download Wisdom Notes",
                        results["wisdom"]["wisdom"],
                        file_name="wisdom_notes.md",
                        mime="text/markdown"
                    )
                else:
                    st.info("No wisdom extracted.")
            
            # Different tabs based on pipeline type
            tab_index = 1
            
            # Outline Tab
            if pipeline_type != "Social Media Only":
                tab_index = display_editor_results(result_tabs, results, tab_index, "outline")
            
            # Blog Content Tab (only for full pipeline)
            if pipeline_type == "Default (Full)":
                tab_index = display_editor_results(result_tabs, results, tab_index, "blog")
            
            # Social Media Tab
            tab_index = display_editor_results(result_tabs, results, tab_index, "social")
            
            # Image Prompts Tab (for Full and Minimal pipelines)
            if pipeline_type != "Social Media Only" and generate_images:
                with result_tabs[tab_index]:
                    if "image_prompts" in results and "prompts" in results["image_prompts"]:
                        prompts = results["image_prompts"]["prompts"]
                        
                        st.subheader("Image Prompts")
                        
                        if isinstance(prompts, list) and prompts:
                            for i, prompt in enumerate(prompts, 1):
                                with st.expander(f"Image Prompt {i}", expanded=i==1):
                                    st.markdown(prompt)
                                    
                                    # Copy button for each prompt
                                    if st.button(f"Copy Prompt {i}", key=f"copy_prompt_{i}"):
                                        st.code(prompt, language="")
                        
                            # Download all prompts
                            all_prompts = "\n\n".join([f"# Image Prompt {i}\n{prompt}" for i, prompt in enumerate(prompts, 1)])
                            st.download_button(
                                "Download All Image Prompts",
                                all_prompts,
                                file_name="image_prompts.md",
                                mime="text/markdown"
                            )
                        elif isinstance(prompts, str):
                            if prompts.startswith("Error"):
                                st.error(prompts)
                            else:
                                st.markdown(prompts)
                        else:
                            st.info("No image prompts generated.")
                    else:
                        st.info("No image prompts generated.")
                
                tab_index += 1
            
            # Summary & Tags Tab
            with result_tabs[tab_index]:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Content Summary")
                    if "summary" in results and "summary" in results["summary"]:
                        st.markdown(results["summary"]["summary"])
                    else:
                        st.info("No summary generated.")
                
                with col2:
                    st.subheader("Content Tags")
                    if "tags" in results and "tags" in results["tags"]:
                        tags = results["tags"]["tags"]
                        if isinstance(tags, list) and tags:
                            # Display tags as chips
                            html_tags = ""
                            for tag in tags:
                                html_tags += f'<span style="background-color: #2E2E2E; padding: 5px 10px; margin: 5px; border-radius: 15px; display: inline-block;">{tag}</span>'
                            
                            st.markdown(html_tags, unsafe_allow_html=True)
                        elif isinstance(tags, str):
                            # If it's a string, try to display directly
                            st.markdown(tags)
                        else:
                            st.info("No tags available.")
                    else:
                        st.info("No tags generated.")
            
            tab_index += 1
            
            # Metrics Tab
            with result_tabs[tab_index]:
                if "metrics" in results:
                    st.subheader("Pipeline Metrics")
                    
                    # Overall metrics 
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Duration", f"{results['metrics']['total_duration']:.2f}s")
                    with col2:
                        st.metric("Success Rate", f"{success_count}/{total_steps}")
                    with col3:
                        st.metric("Success %", f"{success_count/max(1, total_steps)*100:.0f}%")
                    
                    # Create a metrics table
                    metrics_data = []
                    for step_name, step_metrics in results["metrics"]["step_metrics"].items():
                        status = step_metrics.get("status", "unknown")
                        retry_count = step_metrics.get("retry_count", 0)
                        status_display = "❌ Error" if status == "error" else "✅ Success"
                        if retry_count > 0:
                            status_display += f" (Retried {retry_count}x)"
                            
                        metrics_data.append({
                            "Step": step_name,
                            "Duration (s)": f"{step_metrics.get('duration', 0):.2f}",
                            "Status": status_display
                        })
                    
                    st.table(metrics_data)
                    
                    # Error recovery section
                    if "errors" in results and results["errors"]:
                        st.subheader("Error Recovery")
                        st.warning("The following steps encountered errors. You can retry them individually.")
                        
                        for step_name, error_info in results["errors"].items():
                            with st.expander(f"Error in {step_name}", expanded=True):
                                st.error(error_info["message"])
                                
                                # Add retry button
                                if st.button(f"Retry {step_name}", key=f"retry_{step_name}"):
                                    with st.spinner(f"Retrying {step_name}..."):
                                        # Get the retry function from results
                                        retry_function = results.get("retry_step")
                                        if retry_function:
                                            # Run the retry
                                            retry_result = asyncio.run(retry_function(step_name))
                                            
                                            if isinstance(retry_result, str) and retry_result.startswith("Error"):
                                                st.error(f"Retry failed: {retry_result}")
                                            else:
                                                st.success(f"Successfully retried {step_name}")
                                                
                                                # Update the relevant part of the results
                                                if step_name == "wisdom":
                                                    results["wisdom"] = {"wisdom": retry_result}
                                                elif step_name == "outline":
                                                    results["outline"] = {"outline": retry_result}
                                                elif step_name == "blog":
                                                    results["blog"] = {"blog_post": retry_result, "blog_title": extract_title(results.get("outline", {}).get("outline", ""))}
                                                elif step_name == "social":
                                                    results["social"] = {"social_content": retry_result, "parsed_social_content": parse_social_content(retry_result)}
                                                elif step_name == "image_prompts":
                                                    results["image_prompts"] = {"prompts": retry_result}
                                                elif step_name == "summary":
                                                    results["summary"] = {"summary": retry_result}
                                                elif step_name == "tags":
                                                    results["tags"] = {"tags": retry_result}
                                                    
                                                # Refresh the page to show updates
                                                st.experimental_rerun()
                                        else:
                                            st.error("Retry function not available. Please regenerate the content.")
                else:
                    st.info("No metrics available.")

            # Export Tab - New!
            tab_index += 1
            with result_tabs[tab_index]:
                st.subheader("Export Content")
                
                # Get title from outline or default
                content_title = "Generated Content"
                if "outline" in results and "outline" in results["outline"]:
                    content_title = extract_title(results["outline"]["outline"])
                
                # Allow user to customize title
                export_title = st.text_input("Content Title", value=content_title)
                
                # Notion export
                st.subheader("Export to Notion")
                
                if notion_key and "NOTION_DATABASE_ID" in os.environ and os.environ["NOTION_DATABASE_ID"]:
                    st.info("Notion API key and database ID detected. You can export content directly to your Notion database.")
                    
                    # Export button
                    if st.button("Export to Notion", use_container_width=True):
                        with st.spinner("Exporting to Notion..."):
                            # Prepare content data
                            content_data = {
                                "title": export_title
                            }
                            
                            # Add all available content
                            if "wisdom" in results and "wisdom" in results["wisdom"]:
                                content_data["wisdom"] = results["wisdom"]["wisdom"]
                                
                            if "outline" in results:
                                if "editor_outline" in results and "edited_outline" in results["editor_outline"]:
                                    content_data["outline"] = results["editor_outline"]["edited_outline"]
                                else:
                                    content_data["outline"] = results["outline"]["outline"]
                            
                            if "blog" in results:
                                if "editor_blog" in results and "edited_blog_post" in results["editor_blog"]:
                                    content_data["blog_post"] = results["editor_blog"]["edited_blog_post"]
                                else:
                                    content_data["blog_post"] = results["blog"]["blog_post"]
                            
                            if "social" in results:
                                if "editor_social" in results and "edited_social_content" in results["editor_social"]:
                                    content_data["social_content"] = results["editor_social"]["edited_social_content"]
                                else:
                                    content_data["social_content"] = results["social"]["social_content"]
                            
                            if "summary" in results and "summary" in results["summary"]:
                                content_data["summary"] = results["summary"]["summary"]
                                
                            if "tags" in results and "tags" in results["tags"]:
                                content_data["tags"] = results["tags"]["tags"]
                                
                            if "image_prompts" in results and "prompts" in results["image_prompts"]:
                                if isinstance(results["image_prompts"]["prompts"], list):
                                    content_data["image_prompts"] = "\n\n".join(results["image_prompts"]["prompts"])
                                else:
                                    content_data["image_prompts"] = results["image_prompts"]["prompts"]
                            
                            # Export to Notion
                            success, message = asyncio.run(save_to_notion(export_title, content_data))
                            
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                else:
                    st.warning("Notion export requires both API key and Database ID. Configure these in the sidebar to enable export.")
                
                # Download as Markdown
                st.subheader("Download All Content")
                
                if st.button("Prepare Markdown Export", use_container_width=True):
                    # Compile all content into a single markdown file
                    markdown_content = f"# {export_title}\n\n"
                    
                    if "summary" in results and "summary" in results["summary"]:
                        markdown_content += f"## Summary\n\n{results['summary']['summary']}\n\n"
                    
                    if "tags" in results and "tags" in results["tags"] and results["tags"]["tags"]:
                        if isinstance(results["tags"]["tags"], list):
                            markdown_content += f"**Tags**: {', '.join(results['tags']['tags'])}\n\n"
                        else:
                            markdown_content += f"**Tags**: {results['tags']['tags']}\n\n"
                    
                    markdown_content += "---\n\n"
                    
                    if "wisdom" in results and "wisdom" in results["wisdom"]:
                        markdown_content += f"## Wisdom Notes\n\n{results['wisdom']['wisdom']}\n\n---\n\n"
                        
                    if "outline" in results:
                        if "editor_outline" in results and "edited_outline" in results["editor_outline"]:
                            markdown_content += f"## Content Outline (Edited)\n\n{results['editor_outline']['edited_outline']}\n\n---\n\n"
                        else:
                            markdown_content += f"## Content Outline\n\n{results['outline']['outline']}\n\n---\n\n"
                    
                    if "blog" in results:
                        if "editor_blog" in results and "edited_blog_post" in results["editor_blog"]:
                            markdown_content += f"## Blog Post (Edited)\n\n{results['editor_blog']['edited_blog_post']}\n\n---\n\n"
                        else:
                            markdown_content += f"## Blog Post\n\n{results['blog']['blog_post']}\n\n---\n\n"
                    
                    if "social" in results:
                        if "editor_social" in results and "edited_social_content" in results["editor_social"]:
                            markdown_content += f"## Social Media Content (Edited)\n\n{results['editor_social']['edited_social_content']}\n\n---\n\n"
                        else:
                            markdown_content += f"## Social Media Content\n\n{results['social']['social_content']}\n\n---\n\n"
                    
                    if "image_prompts" in results and "prompts" in results["image_prompts"]:
                        markdown_content += "## Image Prompts\n\n"
                        if isinstance(results["image_prompts"]["prompts"], list):
                            for i, prompt in enumerate(results["image_prompts"]["prompts"], 1):
                                markdown_content += f"### Image Prompt {i}\n\n{prompt}\n\n"
                        else:
                            markdown_content += results["image_prompts"]["prompts"]
                        markdown_content += "\n\n---\n\n"
                    
                    # Add generation timestamp
                    markdown_content += f"\n\n*Generated by WhisperForge on {datetime.now().strftime('%Y-%m-%d at %H:%M')}*"
                    
                    # Create download button
                    filename = f"{export_title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
                    st.download_button(
                        "Download Complete Export",
                        markdown_content,
                        file_name=filename,
                        mime="text/markdown",
                        use_container_width=True
                    )

