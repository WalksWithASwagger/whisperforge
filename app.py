import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from notion_client import Client
from datetime import datetime
from pydub import AudioSegment
import tempfile
import math
import glob
from anthropic import Anthropic
import requests  # for Grok API
import shutil
import base64
from io import BytesIO
from PIL import Image
import time

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="WhisperForge",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def local_css():
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            background-color: #f8f9fa;
            padding: 1.5rem;
        }
        
        /* Custom header styling */
        .app-header {
            background-color: #6c5ce7;
            padding: 1.5rem 2rem 1rem 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .app-header h1 {
            margin: 0;
            font-weight: 700;
            color: white;
        }
        
        .app-header p {
            font-size: 1.1rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        /* Card styling */
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #6c5ce7;
        }
        
        /* Content cards */
        .content-card {
            background-color: white;
            border-radius: 8px;
            padding: 1.2rem;
            margin: 0.8rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #6c5ce7;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #6c5ce7;
            color: white;
            border-radius: 20px;
            padding: 0.5rem 1.5rem;
            font-weight: 500;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background-color: #5540e6;
            box-shadow: 0 4px 8px rgba(108, 92, 231, 0.3);
        }
        
        /* Action button variants */
        .transcribe-btn button {
            background-color: #6c5ce7;
        }
        
        .wisdom-btn button {
            background-color: #e17055;
        }
        
        .outline-btn button {
            background-color: #0984e3;
        }
        
        .social-btn button {
            background-color: #00b894;
        }
        
        .image-btn button {
            background-color: #6c5ce7;
        }
        
        .article-btn button {
            background-color: #a29bfe;
        }
        
        .notion-btn button {
            background-color: #2d3436;
        }
        
        /* Progress indicators */
        .progress-container {
            margin: 1rem 0;
        }
        
        /* File uploader */
        .uploadedFile {
            border: 2px dashed #6c5ce7;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            background-color: rgba(108, 92, 231, 0.05);
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        
        /* Audio player */
        .audio-player {
            background-color: #f1f3f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f1f3f6;
            border-radius: 8px;
            padding: 0.5rem;
            font-weight: 500;
        }
        
        /* Markdown content */
        .element-container div[data-testid="stMarkdownContainer"] {
            line-height: 1.6;
        }
        
        /* Success message */
        div[data-testid="stSuccessMessage"] {
            background-color: rgba(0, 184, 148, 0.1);
            border-left-color: #00b894;
            color: #00b894;
        }
        
        /* Error message */
        div[data-testid="stErrorMessage"] {
            background-color: rgba(255, 118, 117, 0.1);
            border-left-color: #ff7675;
            color: #ff7675;
        }
        
        /* Knowledge base labels */
        .knowledge-label {
            background-color: rgba(108, 92, 231, 0.1);
            color: #6c5ce7;
            border-radius: 4px;
            padding: 2px 8px;
            display: inline-block;
            margin: 2px;
            font-size: 0.8rem;
        }
        
        /* Step indicator */
        .step-indicator {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .step-indicator-dot {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 0.5rem;
            color: white;
            font-weight: bold;
        }
        
        .step-indicator-dot.active {
            background-color: #6c5ce7;
        }
        
        .step-indicator-label {
            font-weight: 500;
        }
        
        /* User selector */
        .user-selector {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Pills and tags */
        .pill {
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 0.2rem;
            background-color: rgba(108, 92, 231, 0.1);
            color: #6c5ce7;
        }
        
        /* Model selector */
        .model-selector {
            background-color: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
    </style>
    """, unsafe_allow_html=True)

# Apply the custom CSS
local_css()

# Initialize clients
openai_client = OpenAI()
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
notion_client = Client(auth=os.getenv("NOTION_API_KEY"))
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# UI Helper functions
def display_header():
    """Display the application header with logo and title"""
    col1, col2 = st.columns([1, 6])
    
    with col1:
        # Using an emoji as the logo
        st.markdown("<div style='text-align: center; font-size: 3.5rem;'>🔊</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<h1 style='margin-bottom: 0;'>WhisperForge</h1>", unsafe_allow_html=True)
        st.markdown("<p style='margin-top: 0;'>Transform your spoken ideas into structured content</p>", unsafe_allow_html=True)

def display_step_indicator(current_step, total_steps=5):
    """Display a visual step indicator"""
    steps = ["Upload", "Transcribe", "Extract", "Generate", "Export"]
    
    html = "<div class='step-indicator'>"
    for i in range(total_steps):
        dot_class = "step-indicator-dot active" if i < current_step else "step-indicator-dot"
        html += f"""
        <div style='display: flex; flex-direction: column; align-items: center; margin-right: 1rem;'>
            <div class='{dot_class}'>{i+1}</div>
            <div class='step-indicator-label'>{steps[i]}</div>
        </div>
        """
        # Add connecting line except for the last step
        if i < total_steps - 1:
            line_class = "active" if i < current_step - 1 else ""
            html += f"<div style='flex-grow: 1; height: 2px; background-color: {'#6c5ce7' if line_class else '#ddd'}; margin: 0 0.5rem;'></div>"
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def display_card(title, content, icon="📄"):
    """Display content in a styled card"""
    st.markdown(f"""
    <div class="content-card">
        <h3>{icon} {title}</h3>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)

def display_success_step(title, description=None):
    """Display a step that has been completed"""
    html = f"""
    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
        <div style='width: 24px; height: 24px; border-radius: 50%; background-color: #00b894; 
                  color: white; display: flex; align-items: center; justify-content: center; margin-right: 0.5rem;'>
            ✓
        </div>
        <div style='font-weight: 500;'>{title}</div>
    </div>
    """
    if description:
        html += f"<div style='margin-left: 2rem; color: #555; font-size: 0.9rem;'>{description}</div>"
    
    st.markdown(html, unsafe_allow_html=True)

def display_knowledge_tags(knowledge_base_files):
    """Display knowledge base files as tags"""
    if not knowledge_base_files:
        return
    
    html = "<div style='margin-top: 0.5rem;'>"
    for kb_file in knowledge_base_files:
        name = os.path.splitext(os.path.basename(kb_file))[0]
        html += f"<span class='knowledge-label'>{name}</span> "
    html += "</div>"
    
    st.markdown(html, unsafe_allow_html=True)

def display_progress_bar_with_text(percent, text):
    """Display a progress bar with text overlay"""
    # Streamlit's progress bar
    progress_bar = st.progress(percent)
    
    # Add text overlay
    st.markdown(f"""
    <div style='margin-top: -1.5rem; text-align: center; color: #555; font-size: 0.8rem; margin-bottom: 1rem;'>
        {text}
    </div>
    """, unsafe_allow_html=True)
    
    return progress_bar

def responsive_columns(ratios):
    """Create responsive columns based on ratios"""
    return st.columns(ratios)

def display_model_selector(provider, model, providers, models):
    """Display a visually enhanced model selector"""
    st.markdown("<div class='model-selector'>", unsafe_allow_html=True)
    
    # Provider icons
    provider_icons = {
        "OpenAI": "🧠",
        "Anthropic": "🔮",
        "Grok": "🤖"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_provider = st.selectbox(
            "AI Provider", 
            options=providers,
            format_func=lambda x: f"{provider_icons.get(x, '✨')} {x}"
        )
    
    with col2:
        selected_model = st.selectbox(
            f"Model", 
            options=models[selected_provider]
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return selected_provider, selected_model

def display_action_button(label, key, icon="⚡", button_class=""):
    """Display a styled action button"""
    html_before = f"<div class='{button_class}'>"
    st.markdown(html_before, unsafe_allow_html=True)
    clicked = st.button(f"{icon} {label}", key=key)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked

# Available LLM models grouped by provider
LLM_MODELS = {
    "OpenAI": {
        "GPT-4 (Most Capable)": "gpt-4",
        "GPT-4 Turbo": "gpt-4-turbo-preview",
        "GPT-3.5 Turbo (Faster)": "gpt-3.5-turbo",
    },
    "Anthropic": {
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Claude 3 Haiku": "claude-3-haiku-20240307",
    },
    "Grok": {
        "Grok-1": "grok-1",
    }
}

def load_user_knowledge_base(user):
    """Load knowledge base files for a specific user"""
    knowledge_base = {}
    kb_path = f'prompts/{user}/knowledge_base'
    
    if os.path.exists(kb_path):
        for file in os.listdir(kb_path):
            if file.endswith(('.txt', '.md')):
                with open(os.path.join(kb_path, file), 'r') as f:
                    name = os.path.splitext(file)[0].replace('_', ' ').title()
                    knowledge_base[name] = f.read()
    
    return knowledge_base

def load_prompts():
    """Load prompts organized by user"""
    users = {}
    prompts_dir = 'prompts'
    
    if not os.path.exists(prompts_dir):
        return users
    
    # Get all user directories
    for user_dir in os.listdir(prompts_dir):
        user_path = os.path.join(prompts_dir, user_dir)
        if os.path.isdir(user_path) and not user_dir.startswith('.'):
            users[user_dir] = {
                'prompts': {},
                'knowledge_base': load_user_knowledge_base(user_dir)
            }
            
            # Load prompts for this user
            prompts_path = os.path.join(user_path, 'prompts')
            if os.path.exists(prompts_path):
                # Recursively find all .md files
                for root, _, files in os.walk(prompts_path):
                    for file in files:
                        if file.endswith('.md') and not file.startswith('.'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    # Use the parent directory name as the prompt name
                                    prompt_dir = os.path.basename(os.path.dirname(file_path))
                                    prompt_name = prompt_dir.replace('_', ' ').title()
                                    users[user_dir]['prompts'][prompt_name] = content
                            except Exception as e:
                                st.error(f"Error loading prompt {file_path}")
            
    return users

def apply_prompt(text, prompt_content, provider, model, user_knowledge=None):
    """Apply a specific prompt using the selected model and provider, incorporating user knowledge"""
    try:
        prompt_parts = prompt_content.split('## Prompt')
        if len(prompt_parts) > 1:
            prompt_text = prompt_parts[1].strip()
        else:
            prompt_text = prompt_content

        # Include knowledge base context if available
        system_prompt = prompt_text
        if user_knowledge:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in user_knowledge.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis and match the user's style and perspective:

{knowledge_context}

When analyzing the content, please incorporate these perspectives and style guidelines.

Original Prompt:
{prompt_text}"""

        if provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ]
            )
            return response.content[0].text

        elif provider == "Grok":
            # Grok API endpoint (you'll need to adjust this based on actual Grok API documentation)
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",  # Adjust URL as needed
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        st.error(f"Analysis error with {provider} {model}: {str(e)}")
        return None

def chunk_audio(audio_path, target_size_mb=20):
    """Split audio file into chunks of approximately target_size_mb"""
    try:
        audio = AudioSegment.from_file(audio_path)
        
        # Ensure minimum chunk length (1 second)
        MIN_CHUNK_LENGTH_MS = 1000
        
        # Calculate number of chunks needed
        file_size = os.path.getsize(audio_path)
        num_chunks = math.ceil(file_size / (target_size_mb * 1024 * 1024))
        chunk_length_ms = max(len(audio) // num_chunks, MIN_CHUNK_LENGTH_MS)
        
        chunks = []
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            # Skip chunks that are too short
            if len(chunk) < MIN_CHUNK_LENGTH_MS:
                continue
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                chunk.export(temp_file.name, format='mp3')
                chunks.append(temp_file.name)
        
        return chunks
    except Exception as e:
        st.error(f"Error chunking audio: {str(e)}")
        return []

def transcribe_chunk(chunk_path, i, total_chunks):
    """Transcribe a single chunk with error handling"""
    try:
        with open(chunk_path, "rb") as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
            return transcript.text
    except Exception as e:
        st.warning(f"Warning: Failed to transcribe part {i+1} of {total_chunks}: {str(e)}")
        return ""
    finally:
        # Clean up chunk file
        try:
            os.remove(chunk_path)
        except:
            pass

def generate_summary(text, title):
    """Generate a one-sentence summary of the audio content"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Create a single, concise sentence that summarizes the main topic or content of this audio transcript. Use an engaging, descriptive style."},
                {"role": "user", "content": f"Title: {title}\n\nTranscript: {text[:2000]}..."} # Send first 2000 chars for context
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Summary generation error: {str(e)}")
        return "Summary generation failed"

def generate_short_title(text):
    """Generate a 5-7 word descriptive title from the transcript"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Create a concise, descriptive 5-7 word title that captures the main topic or theme of this content. Make it clear and engaging. Return ONLY the title words, nothing else."},
                {"role": "user", "content": f"Generate a 5-7 word title for this transcript:\n\n{text[:2000]}..."} # First 2000 chars for context
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Title generation error: {str(e)}")
        return "Untitled Audio Transcription"

def create_content_notion_entry(title, audio_file, transcript, wisdom, 
                               outline="", social_posts="", image_prompts="", article=""):
    """Create a comprehensive Notion entry with all generated content"""
    try:
        # Generate a 5-7 word descriptive title
        short_title = generate_short_title(transcript)
        
        # Create the page title with WHISPER prefix
        notion_title = f"WHISPER: {short_title}"
        
        # Generate summary
        summary = generate_summary(transcript, title)
        
        # Get original audio filename if available
        original_filename = ""
        if audio_file:
            original_filename = audio_file.name
        
        # Helper function to create paragraph blocks from text (chunked to respect Notion's limits)
        def create_paragraph_blocks(text):
            if not text:
                return [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Not yet generated."}}]
                    }
                }]
            
            # Split text into chunks of 1900 characters (leaving room for safety)
            blocks = []
            MAX_LENGTH = 1900  # Notion limit is 2000, but we're being cautious
            
            for i in range(0, len(text), MAX_LENGTH):
                chunk = text[i:i + MAX_LENGTH]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
            
            return blocks
        
        # Helper function to create a toggle block with potentially large content
        def create_toggle(title, content_text, color, emoji=None):
            # Create the toggle block with empty children first
            toggle_block = {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": title}}],
                    "color": color,
                    "children": []
                }
            }
            
            # Add paragraph blocks as children
            toggle_block["toggle"]["children"] = create_paragraph_blocks(content_text)
            
            return toggle_block
        
        # Helper function to create a divider
        def create_divider():
            return {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
        
        # Create the new page with all blocks
        page_children = [
            # Purple callout at the top with summary
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}],
                    "color": "purple",
                    "icon": {
                        "type": "emoji",
                        "emoji": "💜"
                    }
                }
            },
            
            # Metadata section
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}],
                    "color": "default"
                }
            },
            
            # Original Audio filename with an icon
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text", 
                            "text": {"content": "🎵 "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text", 
                            "text": {"content": "Original Audio: "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text", 
                            "text": {"content": original_filename}
                        }
                    ]
                }
            },
            
            # Date created
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text", 
                            "text": {"content": "📅 "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text", 
                            "text": {"content": "Created: "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text", 
                            "text": {"content": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        }
                    ]
                }
            },
            
            # Divider before content
            create_divider(),
            
            # Content heading
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Content"}}],
                    "color": "default"
                }
            },
        ]
        
        # Add content toggles with appropriate emojis and colors
        content_blocks = [
            # Transcription toggle
            create_toggle("▶️ Transcription", transcript, "brown"),
            
            # Wisdom toggle
            create_toggle("💎 Wisdom", wisdom, "brown_background"),
        ]
        
        # Add optional content if available
        if social_posts:
            content_blocks.append(create_toggle("📱 Social Media Posts", social_posts, "yellow_background"))
        
        if image_prompts:
            content_blocks.append(create_toggle("🖼️ Image Prompts", image_prompts, "green_background"))
        
        if outline:
            content_blocks.append(create_toggle("📝 Outline", outline, "blue_background"))
        
        if article:
            content_blocks.append(create_toggle("📄 Full Article", article, "purple_background"))
        
        # Add content blocks to page
        page_children.extend(content_blocks)
        
        # Add footer divider and attribution
        page_children.extend([
            create_divider(),
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text", 
                            "text": {"content": "Created with "},
                        },
                        {
                            "type": "text", 
                            "text": {"content": "WhisperForge"},
                            "annotations": {"bold": True, "color": "purple"}
                        }
                    ]
                }
            }
        ])
        
        # Create the new page
        new_page = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "title": {
                    "title": [{"text": {"content": notion_title}}]
                }
            },
            children=page_children
        )
        
        return f"https://notion.so/{new_page['id'].replace('-', '')}"
    
    except Exception as e:
        st.error(f"Notion API Error: {str(e)}")
        return None

def get_available_openai_models():
    """Get current list of available OpenAI models"""
    try:
        models = openai_client.models.list()
        gpt_models = {
            model.id: model.id for model in models 
            if any(x in model.id for x in ['gpt-4', 'gpt-3.5'])
        }
        return gpt_models
    except Exception as e:
        st.error(f"Error fetching OpenAI models: {str(e)}")
        return {}

def get_available_anthropic_models():
    """Get current list of available Anthropic models"""
    # Current as of March 2024
    return {
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Claude 3 Sonnet": "claude-3-sonnet-20240229",
        "Claude 3 Haiku": "claude-3-haiku-20240307",
        "Claude 2.1": "claude-2.1",
    }

def get_available_grok_models():
    """Get current list of available Grok models"""
    # Current as of March 2024
    return {
        "Grok-1": "grok-1",
    }

# Update the LLM_MODELS dictionary dynamically
def get_current_models():
    return {
        "OpenAI": get_available_openai_models(),
        "Anthropic": get_available_anthropic_models(),
        "Grok": get_available_grok_models(),
    }

# Add this function to get available users
def get_available_users():
    """Get a list of available users by scanning the prompts directory"""
    users = []
    prompts_dir = 'prompts'
    
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)
        return ["Default"]
    
    # Get all user directories
    for user_dir in os.listdir(prompts_dir):
        user_path = os.path.join(prompts_dir, user_dir)
        if os.path.isdir(user_path) and not user_dir.startswith('.'):
            users.append(user_dir)
    
    # If no users found, return a default user
    if not users:
        users = ["Default"]
    
    return users

# Make sure this function exists and works properly
def get_custom_prompt(user, prompt_type, default_prompt=""):
    """Get custom prompt if it exists, otherwise return default"""
    prompt_path = os.path.join("prompts", user, "custom_prompts", f"{prompt_type}.txt")
    
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            st.error(f"Error loading custom prompt: {str(e)}")
    
    return default_prompt

# Add this function to save custom prompts
def save_custom_prompt(user, prompt_type, prompt_content):
    """Save a custom prompt for a specific user and prompt type"""
    user_dir = os.path.join("prompts", user, "custom_prompts")
    os.makedirs(user_dir, exist_ok=True)
    
    prompt_path = os.path.join(user_dir, f"{prompt_type}.txt")
    try:
        with open(prompt_path, "w") as f:
            f.write(prompt_content)
        return True
    except Exception as e:
        st.error(f"Error saving custom prompt: {str(e)}")
        return False

def list_knowledge_base_files(user):
    """List knowledge base files for a specific user"""
    kb_path = os.path.join('prompts', user, 'knowledge_base')
    files = []
    
    if os.path.exists(kb_path):
        for file in os.listdir(kb_path):
            if file.endswith(('.txt', '.md')) and not file.startswith('.'):
                files.append(os.path.join(kb_path, file))
    
    return files

def main():
    # Display application header
    display_header()
    
    # Determine current step based on session state
    current_step = 1  # Default: Upload step
    if "audio_file" in st.session_state and st.session_state.audio_file:
        current_step = 2  # Audio uploaded
    if "transcription" in st.session_state and st.session_state.transcription:
        current_step = 3  # Transcription completed
    if "wisdom" in st.session_state and st.session_state.wisdom:
        current_step = 4  # Content extraction started
    if any(x in st.session_state and st.session_state[x] for x in ["outline", "social_content", "image_prompts", "article"]):
        current_step = 5  # Content generation completed
    
    # Display step indicator
    display_step_indicator(current_step)
    
    # Initialize session state variables if they don't exist
    for state_var in ["transcription", "wisdom", "outline", "social_content", "image_prompts", "article", "audio_file"]:
        if state_var not in st.session_state:
            st.session_state[state_var] = None
    
    # Load prompts and user data
    users_data = load_prompts()
    
    # Sidebar with user selection and configuration
    with st.sidebar:
        st.markdown("<h3>Configuration</h3>", unsafe_allow_html=True)
        
        # User selection with visual enhancements
        st.markdown("<div class='user-selector'>", unsafe_allow_html=True)
        available_users = get_available_users()
        selected_user = st.selectbox(
            "Select User Profile", 
            options=available_users,
            format_func=lambda x: f"👤 {x}"
        )
        
        # Display knowledge base files if available
        knowledge_base_files = list_knowledge_base_files(selected_user)
        if knowledge_base_files:
            st.markdown("<div style='margin-top: 0.8rem;'>", unsafe_allow_html=True)
            st.markdown("<strong>💡 Knowledge Base</strong>")
            display_knowledge_tags(knowledge_base_files)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Custom prompt configuration
        with st.expander("✏️ Configure Custom Prompts"):
            prompt_types = ["wisdom", "outline", "social", "image", "article"]
            prompt_icons = {
                "wisdom": "💎",
                "outline": "📝",
                "social": "📱",
                "image": "🖼️",
                "article": "📄"
            }
            
            selected_prompt_type = st.selectbox(
                "Prompt Type", 
                options=prompt_types,
                format_func=lambda x: f"{prompt_icons.get(x, '✨')} {x.capitalize()}"
            )
            
            # Get existing custom prompt if available
            custom_prompt = get_custom_prompt(selected_user, selected_prompt_type, "")
            
            # Text area for editing the prompt
            edited_prompt = st.text_area("Edit Prompt", custom_prompt, height=200)
            
            # Save button for prompt
            if st.button("💾 Save Prompt", key=f"save_{selected_prompt_type}"):
                if save_custom_prompt(selected_user, selected_prompt_type, edited_prompt):
                    st.success(f"{selected_prompt_type.capitalize()} prompt saved!")
                else:
                    st.error("Failed to save prompt")
    
    # Main content area with cards design
    if current_step == 1:
        # Step 1: Upload Audio
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>🎙️ Start with an Audio File</h3>", unsafe_allow_html=True)
        st.markdown("<p>Upload your audio recording to begin the transcription process.</p>", unsafe_allow_html=True)
        
        # Enhanced file uploader
        st.markdown("<div class='uploadedFile'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drop your audio file here", 
            type=["mp3", "wav", "m4a", "ogg"],
            help="Supported formats: MP3, WAV, M4A, OGG"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file or (current_step > 1 and st.session_state.audio_file):
        # Use uploaded file or one from session state
        audio_file = uploaded_file or st.session_state.audio_file
        
        # Audio player with file info
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        filename = os.path.splitext(audio_file.name)[0]
        file_info = f"File: {audio_file.name}"
        
        st.markdown(f"<h3>🎧 Audio Ready</h3><p>{file_info}</p>", unsafe_allow_html=True)
        
        # Audio player with styling
        st.markdown("<div class='audio-player'>", unsafe_allow_html=True)
        st.audio(audio_file, format="audio/mp3")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Title input with better styling
        title = st.text_input(
            "Title for this recording", 
            value=f"Transcription - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            help="This will be used as the title in Notion and other exports"
        )
        
        # Only show transcribe button if not yet transcribed
        if current_step < 3:
            # Transcribe button with enhanced styling
            if display_action_button("Transcribe Audio", "transcribe_audio", "🔤", "transcribe-btn"):
                with st.spinner("Transcribing your audio..."):
                    # Save uploaded file to temp location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as temp_file:
                        temp_path = temp_file.name
                        shutil.copyfileobj(audio_file, temp_file)
                    
                    st.session_state.audio_file = audio_file
                    
                    try:
                        # Check file size and chunk if necessary
                        file_size = os.path.getsize(temp_path)
                        if file_size > 25 * 1024 * 1024:  # 25MB
                            chunks = chunk_audio(temp_path)
                            full_transcript = ""
                            
                            if chunks:  # Only proceed if we have valid chunks
                                progress_text = f"Processing {len(chunks)} audio segments"
                                progress_bar = display_progress_bar_with_text(0, progress_text)
                                
                                for i, chunk_path in enumerate(chunks):
                                    progress_percentage = (i + 1) / len(chunks)
                                    progress_bar.progress(progress_percentage)
                                    st.markdown(f"<div style='text-align: center;'>Transcribing segment {i+1} of {len(chunks)}</div>", unsafe_allow_html=True)
                                    transcript_text = transcribe_chunk(chunk_path, i, len(chunks))
                                    full_transcript += transcript_text + " "
                                
                                if full_transcript.strip():  # If we got any transcription
                                    st.session_state.transcription = full_transcript.strip()
                                    st.session_state.title = title
                                    st.success("Transcription completed!")
                                    st.experimental_rerun()
                                else:
                                    st.error("Failed to get any valid transcription from the audio")
                            else:
                                st.error("Failed to process audio chunks")
                        else:
                            # For files under 25MB, try direct transcription
                            try:
                                progress_bar = display_progress_bar_with_text(0.3, "Analyzing audio...")
                                
                                with open(temp_path, "rb") as audio:
                                    # Update progress
                                    progress_bar.progress(0.6)
                                    st.markdown("<div style='text-align: center;'>Processing audio with Whisper...</div>", unsafe_allow_html=True)
                                    
                                    transcript = openai_client.audio.transcriptions.create(
                                        model="whisper-1",
                                        file=audio
                                    )
                                    
                                    # Final progress
                                    progress_bar.progress(1.0)
                                    st.markdown("<div style='text-align: center;'>Finalizing transcription...</div>", unsafe_allow_html=True)
                                    
                                    st.session_state.transcription = transcript.text
                                    st.session_state.title = title
                                    st.success("Transcription completed!")
                                    time.sleep(1)  # Brief pause for visual feedback
                                    st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Transcription error: {str(e)}")
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display transcription and provide content generation options
    if current_step >= 3 and st.session_state.transcription:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>📝 Transcription</h3>", unsafe_allow_html=True)
        
        # Transcription display with better formatting
        st.markdown("<div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
        st.markdown(st.session_state.transcription)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # AI Model Selection with visual enhancement
        st.markdown("<div class='model-selector'>", unsafe_allow_html=True)
        st.markdown("<h4>🤖 AI Model Selection</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # Provider selection with icons
        provider_icons = {
            "OpenAI": "🧠",
            "Anthropic": "🔮",
            "Grok": "🤖"
        }
        
        with col1:
            provider = st.selectbox(
                "Select AI Provider:",
                options=list(LLM_MODELS.keys()),
                format_func=lambda x: f"{provider_icons.get(x, '✨')} {x}"
            )
        
        # Model selection based on provider
        with col2:
            model_options = list(LLM_MODELS[provider].keys())
            model = st.selectbox(
                f"Select Model:",
                options=model_options
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Get the model ID for the selected model
        model_id = LLM_MODELS[provider][model]
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Content generation section with cards design
        st.markdown("<h3>🔮 Content Generation</h3>", unsafe_allow_html=True)
        
        # Wisdom extraction
        with st.container():
            st.markdown("<div class='content-card' style='border-left-color: #e17055;'>", unsafe_allow_html=True)
            st.markdown("<h4>💎 Extract Wisdom</h4>", unsafe_allow_html=True)
            st.markdown("<p>Extract key insights, quotes, and actionable advice from the transcription.</p>", unsafe_allow_html=True)
            
            # Add wisdom extraction button
            wisdom_exists = "wisdom" in st.session_state and st.session_state.wisdom
            
            if not wisdom_exists:
                if display_action_button("Extract Wisdom", "extract_wisdom", "💡", "wisdom-btn"):
                    with st.spinner("Extracting wisdom..."):
                        # Get custom prompt for wisdom extraction
                        wisdom_prompt = get_custom_prompt(selected_user, "wisdom", "Extract key wisdom, insights, quotes, and actionable advice from this transcription.")
                        
                        # Get user knowledge base if available
                        user_knowledge = users_data.get(selected_user, {}).get('knowledge_base', {})
                        
                        # Apply the prompt to generate wisdom
                        wisdom = apply_prompt(st.session_state.transcription, wisdom_prompt, provider, model_id, user_knowledge)
                        
                        if wisdom:
                            st.session_state.wisdom = wisdom
                            st.success("Wisdom extracted!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to extract wisdom.")
            
            # Display wisdom if it exists
            if wisdom_exists:
                display_success_step("Wisdom extracted successfully")
                st.markdown("<div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 0.8rem;'>", unsafe_allow_html=True)
                st.markdown(st.session_state.wisdom)
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Only show additional content options if wisdom has been extracted
        if "wisdom" in st.session_state and st.session_state.wisdom:
            col1, col2 = st.columns(2)
            
            # Outline generation
            with col1:
                st.markdown("<div class='content-card' style='border-left-color: #0984e3; height: 100%;'>", unsafe_allow_html=True)
                st.markdown("<h4>📝 Create Outline</h4>", unsafe_allow_html=True)
                
                outline_exists = "outline" in st.session_state and st.session_state.outline
                
                if not outline_exists:
                    if display_action_button("Generate Outline", "generate_outline", "📋", "outline-btn"):
                        with st.spinner("Generating outline..."):
                            # Get custom prompt for outline generation
                            outline_prompt = get_custom_prompt(selected_user, "outline", "Create a detailed outline for an article based on this transcription.")
                            
                            # Get user knowledge base if available
                            user_knowledge = users_data.get(selected_user, {}).get('knowledge_base', {})
                            
                            # Apply the prompt to generate outline
                            outline = apply_prompt(st.session_state.transcription, outline_prompt, provider, model_id, user_knowledge)
                            
                            if outline:
                                st.session_state.outline = outline
                                st.success("Outline generated!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to generate outline.")
                
                # Display outline if it exists
                if outline_exists:
                    display_success_step("Outline created")
                    with st.expander("View Outline", expanded=True):
                        st.markdown(st.session_state.outline)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Social media content
            with col2:
                st.markdown("<div class='content-card' style='border-left-color: #00b894; height: 100%;'>", unsafe_allow_html=True)
                st.markdown("<h4>📱 Social Media Content</h4>", unsafe_allow_html=True)
                
                social_exists = "social_content" in st.session_state and st.session_state.social_content
                
                if not social_exists:
                    if display_action_button("Create Social Posts", "create_social", "📣", "social-btn"):
                        with st.spinner("Creating social media content..."):
                            # Get custom prompt for social media content
                            social_prompt = get_custom_prompt(selected_user, "social", "Create engaging social media posts based on this transcription.")
                            
                            # Get user knowledge base if available
                            user_knowledge = users_data.get(selected_user, {}).get('knowledge_base', {})
                            
                            # Apply the prompt to generate social media content
                            social_content = apply_prompt(st.session_state.transcription, social_prompt, provider, model_id, user_knowledge)
                            
                            if social_content:
                                st.session_state.social_content = social_content
                                st.success("Social media content created!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to create social media content.")
                
                # Display social content if it exists
                if social_exists:
                    display_success_step("Social posts created")
                    with st.expander("View Social Posts", expanded=True):
                        st.markdown(st.session_state.social_content)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Second row of content options
            col1, col2 = st.columns(2)
            
            # Image prompts
            with col1:
                st.markdown("<div class='content-card' style='border-left-color: #6c5ce7; margin-top: 1rem; height: 100%;'>", unsafe_allow_html=True)
                st.markdown("<h4>🖼️ Image Prompts</h4>", unsafe_allow_html=True)
                
                image_exists = "image_prompts" in st.session_state and st.session_state.image_prompts
                
                if not image_exists:
                    if display_action_button("Generate Image Prompts", "create_image_prompts", "🎨", "image-btn"):
                        with st.spinner("Creating image prompts..."):
                            # Get custom prompt for image prompts
                            image_prompt = get_custom_prompt(selected_user, "image", "Create detailed image generation prompts based on this transcription.")
                            
                            # Get user knowledge base if available
                            user_knowledge = users_data.get(selected_user, {}).get('knowledge_base', {})
                            
                            # Apply the prompt to generate image prompts
                            image_prompts = apply_prompt(st.session_state.transcription, image_prompt, provider, model_id, user_knowledge)
                            
                            if image_prompts:
                                st.session_state.image_prompts = image_prompts
                                st.success("Image prompts created!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to create image prompts.")
                
                # Display image prompts if they exist
                if image_exists:
                    display_success_step("Image prompts generated")
                    with st.expander("View Image Prompts", expanded=True):
                        st.markdown(st.session_state.image_prompts)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Article writing (only show if outline exists)
            with col2:
                st.markdown("<div class='content-card' style='border-left-color: #a29bfe; margin-top: 1rem; height: 100%;'>", unsafe_allow_html=True)
                st.markdown("<h4>📄 Write Full Article</h4>", unsafe_allow_html=True)
                
                # Only enable if outline exists
                article_button_disabled = "outline" not in st.session_state or not st.session_state.outline
                article_exists = "article" in st.session_state and st.session_state.article
                
                if article_button_disabled and not article_exists:
                    st.markdown("<p style='color: #888;'>First create an outline to enable article writing.</p>", unsafe_allow_html=True)
                
                if not article_exists and not article_button_disabled:
                    if display_action_button("Write Article", "write_article", "📝", "article-btn"):
                        with st.spinner("Writing article..."):
                            # Get custom prompt for article writing
                            article_prompt = get_custom_prompt(selected_user, "article", "Write a comprehensive article based on this outline and transcription.")
                            
                            # Get user knowledge base if available
                            user_knowledge = users_data.get(selected_user, {}).get('knowledge_base', {})
                            
                            # Combine outline and transcription for context
                            context = f"OUTLINE:\n{st.session_state.outline}\n\nTRANSCRIPTION:\n{st.session_state.transcription}"
                            
                            # Apply the prompt to write the article
                            article = apply_prompt(context, article_prompt, provider, model_id, user_knowledge)
                            
                            if article:
                                st.session_state.article = article
                                st.success("Article written!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to write article.")
                
                # Display article if it exists
                if article_exists:
                    display_success_step("Full article written")
                    with st.expander("View Article", expanded=True):
                        st.markdown(st.session_state.article)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Export to Notion button (displayed regardless of content state)
        st.markdown("<div class='card' style='margin-top: 1.5rem; border-left-color: #2d3436;'>", unsafe_allow_html=True)
        st.markdown("<h3>📤 Export Content</h3>", unsafe_allow_html=True)
        st.markdown("<p>Save your generated content to Notion. You can export at any point in the process.</p>", unsafe_allow_html=True)
        
        if display_action_button("Save to Notion", "save_to_notion", "📘", "notion-btn"):
            with st.spinner("Saving to Notion..."):
                # Get all generated content
                title = st.session_state.get("title", "Untitled Transcription")
                transcript = st.session_state.get("transcription", "")
                wisdom = st.session_state.get("wisdom", "")
                outline = st.session_state.get("outline", "")
                social_posts = st.session_state.get("social_content", "")
                image_prompts = st.session_state.get("image_prompts", "")
                article = st.session_state.get("article", "")
                
                # Create Notion entry with available content
                notion_url = create_content_notion_entry(
                    title, 
                    st.session_state.get("audio_file", None),
                    transcript, 
                    wisdom,
                    outline,
                    social_posts,
                    image_prompts,
                    article
                )
                
                if notion_url:
                    st.success("Successfully saved to Notion!")
                    st.markdown(f"<a href='{notion_url}' target='_blank' style='display: inline-block; margin-top: 0.5rem; padding: 0.5rem 1rem; background-color: #2d3436; color: white; border-radius: 4px; text-decoration: none;'>View in Notion</a>", unsafe_allow_html=True)
                else:
                    st.error("Failed to save to Notion. Please check your API keys.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Help section at the bottom
    with st.expander("ℹ️ Need Help?"):
        st.markdown("""
        ### How to use WhisperForge
        
        1. **Upload** your audio recording (MP3, WAV, M4A, or OGG format)
        2. **Transcribe** the audio using OpenAI's Whisper model
        3. **Extract wisdom** from the transcription
        4. **Generate content** like outlines, social posts, and more
        5. **Export to Notion** at any stage of the process
        
        You can customize prompts for each content type in the sidebar.
        """)

# Add these helper functions for model selection
def save_model_selection(user, prompt_type, provider, model):
    """Save the selected model for a prompt type."""
    user_dir = os.path.join("prompts", user, "custom_prompts")
    os.makedirs(user_dir, exist_ok=True)
    
    model_file = os.path.join(user_dir, f"{prompt_type}_model.txt")
    with open(model_file, "w") as f:
        f.write(f"{provider}\n{model}")

def get_model_selection(user, prompt_type):
    """Get the saved model selection for a prompt type."""
    model_file = os.path.join("prompts", user, "custom_prompts", f"{prompt_type}_model.txt")
    
    if os.path.exists(model_file):
        with open(model_file, "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                provider = lines[0].strip()
                model = lines[1].strip()
                return provider, model
    
    # Default to OpenAI GPT-4 if no selection is saved
    return "OpenAI", "GPT-4 (Most Capable)"

def add_reset_button():
    """Add a reset button to start over"""
    with st.sidebar:
        st.markdown("<div style='padding-top: 1rem; border-top: 1px solid #eee; margin-top: 1rem;'>", unsafe_allow_html=True)
        if st.button("🔄 Start Over", help="Reset the application and start fresh"):
            # Reset all session state variables
            for key in list(st.session_state.keys()):
                if key in ["transcription", "wisdom", "outline", "social_content", "image_prompts", "article", "audio_file"]:
                    del st.session_state[key]
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    add_reset_button() 