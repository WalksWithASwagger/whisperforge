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

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI()
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
notion_client = Client(auth=os.getenv("NOTION_API_KEY"))
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROK_API_KEY = os.getenv("GROK_API_KEY")

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

def generate_title(transcript):
    """Generate a descriptive 5-7 word title based on the transcript"""
    try:
        prompt = f"""Create a clear, descriptive title (5-7 words) that captures the main topic of this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the title, no quotes or additional text."""
        
        response = openai_client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, descriptive titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return "Audio Transcription"

def generate_summary(transcript):
    """Generate a one-sentence summary of the audio content"""
    try:
        prompt = f"""Create a single, insightful sentence that summarizes the key message or main insight from this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the summary sentence, no additional text."""
        
        response = openai_client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, insightful summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return "Summary of audio content"

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

def create_notion_entry(title, audio_file, transcript, wisdom=None):
    try:
        # Generate AI title and summary
        ai_title = generate_title(transcript)
        ai_summary = generate_summary(transcript)
        
        # Create the page title with WHISPER prefix
        notion_title = f"WHISPER: {ai_title}"
        
        # Current date and tags
        current_date = datetime.now().isoformat()
        tags = generate_content_tags(transcript, wisdom) if wisdom else ["audio", "transcription"]
        
        # Set up properties with exact names from your database
        properties = {
            "title": {
                "title": [{"text": {"content": notion_title}}]
            },
            "Created Date": {
                "date": {
                    "start": current_date
                }
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in tags]
            }
        }

        def chunk_text(text, chunk_size=2000):
            """Split text into chunks that respect Notion's character limit"""
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

        def create_text_blocks(text):
            """Create multiple paragraph blocks for long text"""
            if not text:
                return [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "Not yet generated."}}]
                    }
                }]
            
            chunks = chunk_text(text)
            return [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            } for chunk in chunks]

        # Create the page blocks with proper formatting
        blocks = [
            # Purple summary callout at the top with AI-generated summary
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": ai_summary}}],
                    "color": "purple",
                    "icon": {
                        "type": "emoji",
                        "emoji": "💜"
                    }
                }
            },
            
            # Original Audio toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "▶️ Original Audio"}}],
                    "color": "default",
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": f"Audio file: {audio_file.name if audio_file else 'Not available'}"}}]
                        }
                    }]
                }
            },
            
            # Transcription toggle with chunked content
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "▶️ Transcription"}}],
                    "color": "brown",
                    "children": create_text_blocks(transcript)
                }
            }
        ]

        # Add Wisdom toggle if available
        if wisdom:
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "▶️ Wisdom"}}],
                    "color": "brown_background",
                    "children": create_text_blocks(wisdom)
                }
            })

        # Add empty toggles for other sections
        additional_toggles = [
            ("▶️ Socials", "yellow_background"),
            ("▶️ Image Prompts", "green_background"),
            ("▶️ Outline", "blue_background"),
            ("▶️ Draft Post", "purple_background")
        ]

        for toggle_title, color in additional_toggles:
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": toggle_title}}],
                    "color": color,
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "Not yet generated."}}]
                        }
                    }]
                }
            })

        # Add metadata section at the bottom
        blocks.extend([
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "**Original Audio:** "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text",
                            "text": {"content": audio_file.name if audio_file else "Not available"}
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "**Created:** "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text",
                            "text": {"content": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
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
                            "annotations": {"bold": True}
                        }
                    ]
                }
            }
        ])

        # Create the page in Notion
        new_page = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties,
            children=blocks
        )

        return f"https://notion.so/{new_page['id'].replace('-', '')}"
    except Exception as e:
        st.error(f"Notion API Error: {str(e)}")
        return None

def generate_content_tags(transcript, wisdom):
    """Generate relevant tags based on content"""
    try:
        # Use OpenAI to generate relevant tags
        prompt = f"""Based on this content:
        Transcript: {transcript[:500]}...
        Wisdom: {wisdom[:500] if wisdom else ''}
        
        Generate 5 relevant one-word tags that describe the main topics and themes.
        Return only the tags separated by commas, lowercase."""
        
        response = openai_client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant content tags."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        # Split the response into individual tags and clean them
        tags = [tag.strip().lower() for tag in response.choices[0].message['content'].split(',')]
        
        # Ensure we have exactly 5 tags
        while len(tags) < 5:
            tags.append("general")
        return tags[:5]
    except Exception as e:
        # Return default tags if there's an error
        return ["audio", "transcription", "content", "notes", "whisperforge"]

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
    st.title("WhisperForge")
    st.write("AI-powered audio transcription and content creation tool")
    
    # Initialize session state variables if they don't exist
    if "transcription" not in st.session_state:
        st.session_state.transcription = None
    if "wisdom" not in st.session_state:
        st.session_state.wisdom = None
    if "outline" not in st.session_state:
        st.session_state.outline = None
    if "social_content" not in st.session_state:
        st.session_state.social_content = None
    if "image_prompts" not in st.session_state:
        st.session_state.image_prompts = None
    if "article" not in st.session_state:
        st.session_state.article = None
    if "audio_file" not in st.session_state:
        st.session_state.audio_file = None
    
    # Load prompts
    users_data = load_prompts()
    
    # Sidebar with user selection
    with st.sidebar:
        available_users = get_available_users()
        selected_user = st.selectbox("Select User", available_users)
        
        # Display knowledge base files if available
        knowledge_base_files = list_knowledge_base_files(selected_user)
        if knowledge_base_files:
            st.subheader("Knowledge Base Available")
            for kb_file in knowledge_base_files:
                st.write(f"✓ {os.path.splitext(os.path.basename(kb_file))[0]}")
        
        # Custom prompt configuration
        with st.expander("Configure Custom Prompts"):
            prompt_types = ["wisdom", "outline", "social", "image", "article"]
            selected_prompt_type = st.selectbox("Select Prompt Type", prompt_types)
            
            # Get existing custom prompt if available
            custom_prompt = get_custom_prompt(selected_user, selected_prompt_type, "")
            
            # Text area for editing the prompt
            edited_prompt = st.text_area("Edit Prompt", custom_prompt, height=200)
            
            # Save button for prompt
            if st.button("Save Prompt", key=f"save_{selected_prompt_type}"):
                if save_custom_prompt(selected_user, selected_prompt_type, edited_prompt):
                    st.success(f"{selected_prompt_type.capitalize()} prompt saved!")
                else:
                    st.error("Failed to save prompt")

    # File upload and transcription
    uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
    
    if uploaded_file:
        # Display audio player
        st.audio(uploaded_file, format="audio/mp3")
        
        # Get the base filename without extension for title suggestion
        filename = os.path.splitext(uploaded_file.name)[0]
        
        # Title input
        title = st.text_input("Title (optional)", value=f"Transcription - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Transcribe button
        if st.button("Transcribe Audio"):
            with st.spinner("Transcribing audio..."):
                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                    temp_path = temp_file.name
                    shutil.copyfileobj(uploaded_file, temp_file)
                
                st.session_state.audio_file = uploaded_file
                
                try:
                    # Check file size and chunk if necessary
                    file_size = os.path.getsize(temp_path)
                    if file_size > 25 * 1024 * 1024:  # 25MB
                        chunks = chunk_audio(temp_path)
                        full_transcript = ""
                        
                        if chunks:  # Only proceed if we have valid chunks
                            progress_bar = st.progress(0)
                            for i, chunk_path in enumerate(chunks):
                                st.write(f"Transcribing part {i+1} of {len(chunks)}...")
                                transcript_text = transcribe_chunk(chunk_path, i, len(chunks))
                                full_transcript += transcript_text + " "
                                progress_bar.progress((i + 1) / len(chunks))
                            
                            if full_transcript.strip():  # If we got any transcription
                                st.session_state.transcription = full_transcript.strip()
                                st.session_state.title = title
                            else:
                                st.error("Failed to get any valid transcription from the audio")
                        else:
                            st.error("Failed to process audio chunks")
                    else:
                        # For files under 25MB, try direct transcription
                        try:
                            with open(temp_path, "rb") as audio:
                                transcript = openai_client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio
                                )
                                st.session_state.transcription = transcript.text
                                st.session_state.title = title
                        except Exception as e:
                            st.error(f"Transcription error: {str(e)}")
                    
                    # Clean up temp file
                    os.unlink(temp_path)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    # Display transcription and provide content generation options
    if st.session_state.transcription:
        st.write("### Transcription:")
        st.write(st.session_state.transcription)
        
        st.write("### AI Model Selection")
        col1, col2 = st.columns(2)
        
        # Provider selection
        provider = col1.selectbox(
            "Select AI Provider:",
            options=list(LLM_MODELS.keys())
        )
        
        # Model selection based on provider
        model_options = list(LLM_MODELS[provider].keys())
        model = col2.selectbox(
            f"Select {provider} Model:",
            options=model_options
        )
        
        # Get the model ID for the selected model
        model_id = LLM_MODELS[provider][model]
        
        # Content generation sections
        wisdom_expander = st.expander("Extract Wisdom")
        with wisdom_expander:
            if st.button("Extract Wisdom", key="extract_wisdom"):
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
                    else:
                        st.error("Failed to extract wisdom.")
            
            if "wisdom" in st.session_state and st.session_state.wisdom:
                st.markdown(st.session_state.wisdom)
        
        # Outline generation
        outline_expander = st.expander("Create Outline")
        with outline_expander:
            if st.button("Generate Outline", key="generate_outline"):
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
                    else:
                        st.error("Failed to generate outline.")
            
            if "outline" in st.session_state and st.session_state.outline:
                st.markdown(st.session_state.outline)
        
        # Social media content generation
        social_expander = st.expander("Generate Social Media Content")
        with social_expander:
            if st.button("Create Social Posts", key="create_social"):
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
                    else:
                        st.error("Failed to create social media content.")
            
            if "social_content" in st.session_state and st.session_state.social_content:
                st.markdown(st.session_state.social_content)
        
        # Image prompt generation
        image_expander = st.expander("Create Image Prompts")
        with image_expander:
            if st.button("Create Image Prompts", key="create_image_prompts"):
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
                    else:
                        st.error("Failed to create image prompts.")
            
            if "image_prompts" in st.session_state and st.session_state.image_prompts:
                st.markdown(st.session_state.image_prompts)
        
        # Article writing (only show if outline exists)
        if "outline" in st.session_state and st.session_state.outline:
            article_expander = st.expander("Write Full Article")
            with article_expander:
                if st.button("Write Article", key="write_article"):
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
                        else:
                            st.error("Failed to write article.")
                
                if "article" in st.session_state and st.session_state.article:
                    st.markdown(st.session_state.article)
        
        # Export to Notion button
        if st.button("Save to Notion", key="save_to_notion"):
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
                notion_url = create_notion_entry(
                    title, 
                    st.session_state.get("audio_file", None),
                    transcript, 
                    wisdom
                )
                
                if notion_url:
                    st.success(f"Successfully saved to Notion!")
                    st.markdown(f"[View in Notion]({notion_url})")
                else:
                    st.error("Failed to save to Notion. Please check your API keys.")

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

if __name__ == "__main__":
    main() 