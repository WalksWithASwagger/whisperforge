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
from pathlib import Path

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
    """Load prompt templates from the prompts directory"""
    users = []
    users_prompts = {}  # Initialize as dictionary
    
    # Check if prompts directory exists
    if not os.path.exists("prompts"):
        os.makedirs("prompts")
        st.info("Created prompts directory. Please add prompt templates.")
        return users, users_prompts
    
    # Get list of user directories
    user_dirs = [d for d in os.listdir("prompts") if os.path.isdir(os.path.join("prompts", d))]
    
    # If no user directories, create a default one
    if not user_dirs:
        default_dir = os.path.join("prompts", "default_user")
        os.makedirs(default_dir, exist_ok=True)
        user_dirs = ["default_user"]
        
    # Add users to the list
    for user in user_dirs:
        users.append(user)
        users_prompts[user] = {}  # Initialize each user with an empty dictionary
        
        # Get prompt files for each user
        user_dir = os.path.join("prompts", user)
        prompt_files = []
        try:
            prompt_files = [f for f in os.listdir(user_dir) if f.endswith('.md')]
        except Exception as e:
            st.warning(f"Error accessing prompts for {user}: {str(e)}")
        
        # Load each prompt file
        for prompt_file in prompt_files:
            prompt_name = os.path.splitext(prompt_file)[0]
            try:
                with open(os.path.join(user_dir, prompt_file), 'r') as f:
                    prompt_content = f.read()
                users_prompts[user][prompt_name] = prompt_content
            except Exception as e:
                st.warning(f"Error loading prompt {prompt_file}: {str(e)}")
    
    return users, users_prompts

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
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, descriptive titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Audio Transcription"

def generate_summary(transcript):
    """Generate a one-sentence summary of the audio content"""
    try:
        prompt = f"""Create a single, insightful sentence that summarizes the key message or main insight from this transcript:
        Transcript: {transcript[:1000]}...
        
        Return only the summary sentence, no additional text."""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, insightful summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
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

def chunk_text_for_notion(text, chunk_size=1900):
    """Split text into chunks that respect Notion's character limit"""
    if not text:
        return []
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def create_content_notion_entry(title, transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
    """Create a new entry in the Notion database with all content sections"""
    try:
        # Initialize audio_filename at the beginning of the function
        audio_filename = "None"
        if hasattr(st.session_state, 'audio_file') and st.session_state.audio_file:
            audio_filename = st.session_state.audio_file.name
        
        # Generate AI title if none provided
        if not title or title.startswith("Transcription -") or title.startswith("Content -"):
            ai_title = generate_short_title(transcript)
            title = f"WHISPER: {ai_title}"
        
        # Generate tags for the content
        content_tags = generate_content_tags(transcript, wisdom)
        
        # Generate summary
        summary = generate_summary(transcript)
        
        # Track model usage for metadata
        used_models = []
        if hasattr(st.session_state, 'ai_provider') and hasattr(st.session_state, 'ai_model'):
            if st.session_state.ai_provider and st.session_state.ai_model:
                used_models.append(f"{st.session_state.ai_provider} {st.session_state.ai_model}")
        if transcript:  # If we have a transcript, we likely used Whisper
            used_models.append("OpenAI Whisper-1")
            
        # Estimate token usage
        total_tokens = estimate_token_usage(transcript, wisdom, outline, social_content, image_prompts, article)
        
        # Format content with toggles
        content = []
        
        # Add summary section with AI-generated summary
        content.extend([
            {
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}],
                    "color": "purple_background",
                    "icon": {
                        "type": "emoji",
                        "emoji": "💜"
                    }
                }
            },
            {
                "type": "divider",
                "divider": {}
            }
        ])
        
        # Add Transcript section with chunked content and color
        content.extend([
            {
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": "Transcription"}}],
                    "color": "default", # dark gray/black
                    "children": [
                        {
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        } for chunk in chunk_text_for_notion(transcript)
                    ]
                }
            }
        ])

        # Add Wisdom section if available
        if wisdom:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Wisdom"}}],
                        "color": "brown_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(wisdom)
                        ]
                    }
                }
            ])

        # Add Socials section with golden brown background
        if social_content:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Socials"}}],
                        "color": "orange_background", # closest to golden brown
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(social_content)
                        ]
                    }
                }
            ])

        # Add Image Prompts with green background
        if image_prompts:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Image Prompts"}}],
                        "color": "green_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(image_prompts)
                        ]
                    }
                }
            ])

        # Add Outline with blue background
        if outline:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Outline"}}],
                        "color": "blue_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(outline)
                        ]
                    }
                }
            ])

        # Add Draft Post with purple background
        if article:
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Draft Post"}}],
                        "color": "purple_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                                }
                            } for chunk in chunk_text_for_notion(article)
                        ]
                    }
                }
            ])
            
        # Add Original Audio section with maroon/red background if audio file exists
        if audio_filename != "None":
            content.extend([
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "Original Audio"}}],
                        "color": "red_background",
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": audio_filename}}]
                                }
                            }
                        ]
                    }
                }
            ])
        
        # Add metadata section
        content.extend([
            {
                "type": "divider",
                "divider": {}
            },
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Original Audio:** {audio_filename}"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Models Used:** {', '.join(used_models) if used_models else 'None'}"}}]
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"**Estimated Tokens:** {total_tokens:,}"}}]
                }
            }
        ])

        # Create the page in Notion
        response = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Tags": {"multi_select": [{"name": tag} for tag in content_tags]},
            },
            children=content
        )
        
        # Make the Notion link clickable in the UI
        if response and isinstance(response, dict) and 'id' in response:
            page_id = response['id']
            page_url = f"https://notion.so/{page_id.replace('-', '')}"
            st.success(f"Successfully saved to Notion!")
            st.markdown(f"[Open in Notion]({page_url})")
            return page_url
        else:
            st.error("Notion API returned an invalid response")
            st.write("Response:", response)  # Debug info
            return False
            
    except Exception as e:
        st.error(f"Detailed error creating Notion entry: {str(e)}")
        return False

def estimate_token_usage(transcript, wisdom=None, outline=None, social_content=None, image_prompts=None, article=None):
    """Estimate token usage for all content generated"""
    # Approximate token count (roughly 4 chars per token for English)
    token_count = 0
    
    # Count tokens in all content
    if transcript:
        token_count += len(transcript) / 4
    if wisdom:
        token_count += len(wisdom) / 4
    if outline:
        token_count += len(outline) / 4
    if social_content:
        token_count += len(social_content) / 4
    if image_prompts:
        token_count += len(image_prompts) / 4
    if article:
        token_count += len(article) / 4
        
    # Add approximate prompt tokens and overhead
    token_count += 1000  # For system prompts, etc.
    
    return int(token_count)

def generate_content_tags(transcript, wisdom=None):
    """Generate relevant tags based on content"""
    try:
        # Use OpenAI to generate relevant tags
        prompt = f"""Based on this content:
        Transcript: {transcript[:500]}...
        Wisdom: {wisdom[:500] if wisdom else ''}
        
        Generate 5 relevant one-word tags that describe the main topics and themes.
        Return only the tags separated by commas, lowercase. Examples: spiritual, history, technology, motivation, business"""
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant content tags."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        # Split the response into individual tags and clean them
        tags = [tag.strip().lower() for tag in response.choices[0].message.content.split(',')]
        
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
def get_custom_prompt(user, prompt_type, users_prompts, default_prompts):
    """Safely retrieve a custom prompt for the user, or use default if not available"""
    # Ensure users_prompts is a dictionary
    if not isinstance(users_prompts, dict):
        return default_prompts.get(prompt_type, "")
        
    # Get user's prompts or empty dict if user not found
    user_prompts = users_prompts.get(user, {})
    if not isinstance(user_prompts, dict):
        return default_prompts.get(prompt_type, "")
    
    # Return the custom prompt if available, otherwise use the default
    return user_prompts.get(prompt_type, default_prompts.get(prompt_type, ""))

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

def get_available_models(provider):
    """Fetch available models from the selected AI provider"""
    try:
        if provider == "OpenAI":
            models = openai_client.models.list()
            # Filter for chat-capable models
            available_models = [
                model.id for model in models 
                if any(name in model.id.lower() for name in ["gpt-4", "gpt-3.5"])
            ]
            # Sort to put GPT-4 models first
            available_models.sort(key=lambda x: "gpt-4" in x.lower(), reverse=True)
            if not available_models:
                return ["gpt-4", "gpt-3.5-turbo"]
            return available_models
            
        elif provider == "Anthropic":
            # Anthropic's API doesn't provide model list, use known models
            return [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            
        elif provider == "Grok":
            # Add Grok model fetching when API available
            return ["grok-1"]
            
        return []
    except Exception as e:
        st.error(f"Error fetching models from {provider}: {str(e)}")
        # Fallback models if API fails
        if provider == "OpenAI":
            return ["gpt-4", "gpt-3.5-turbo"]
        elif provider == "Anthropic":
            return ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
        elif provider == "Grok":
            return ["grok-1"]
        return []

def configure_prompts(selected_user, users_prompts):
    """Configure custom prompts for the selected user"""
    st.subheader("Custom Prompts")
    st.write("Configure custom prompts for different content types:")
    
    # List of prompt types
    prompt_types = ["wisdom_extraction", "summary", "outline_creation", "social_media", "image_prompts"]
    
    for prompt_type in prompt_types:
        # Get current prompt for the user and type
        current_prompt = get_custom_prompt(selected_user, prompt_type, users_prompts, DEFAULT_PROMPTS)
        
        # Display text area for editing
        new_prompt = st.text_area(
            f"{prompt_type.replace('_', ' ').title()}",
            value=current_prompt,
            height=150,
            key=f"prompt_{prompt_type}"
        )
        
        # Save button for this prompt
        if st.button(f"Save {prompt_type.replace('_', ' ').title()} Prompt"):
            # Create user directory if it doesn't exist
            user_dir = os.path.join("prompts", selected_user)
            os.makedirs(user_dir, exist_ok=True)
            
            # Save the prompt
            with open(os.path.join(user_dir, f"{prompt_type}.md"), "w") as f:
                f.write(new_prompt)
            
            st.success(f"Saved custom {prompt_type} prompt for {selected_user}")
            
            # Update the in-memory prompts
            if selected_user not in users_prompts:
                users_prompts[selected_user] = {}
            users_prompts[selected_user][prompt_type] = new_prompt

def transcribe_large_file(file_path):
    """Process a large audio file by chunking it and transcribing each chunk"""
    st.info("Processing large audio file in chunks...")
    
    # Create progress bar
    progress_text = "Chunking audio file..."
    progress_bar = st.progress(0)
    
    # Split audio into chunks
    chunks = chunk_audio(file_path)
    if not chunks:
        st.error("Failed to chunk audio file.")
        return ""
    
    # Update progress bar
    progress_text = "Transcribing chunks..."
    
    # Process each chunk
    transcriptions = []
    for i, chunk_path in enumerate(chunks):
        # Update progress
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)
        
        # Transcribe this chunk
        chunk_text = transcribe_chunk(chunk_path, i, len(chunks))
        transcriptions.append(chunk_text)
    
    # Combine all transcriptions
    full_transcript = " ".join(transcriptions)
    
    # Complete progress
    progress_bar.progress(1.0)
    
    return full_transcript

def transcribe_audio(audio_file):
    """Transcribe an audio file directly"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp_file:
            tmp_file.write(audio_file.getvalue())
            tmp_path = tmp_file.name
        
        # Transcribe using OpenAI's Whisper
        with open(tmp_path, "rb") as audio:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return transcript.text
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return ""

def generate_wisdom(transcript, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Extract key insights and wisdom from a transcript"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["wisdom_extraction"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When analyzing the content, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content

        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            )
            return response.content[0].text

        elif ai_provider == "Grok":
            # Grok API endpoint (you'll need to adjust this based on actual Grok API documentation)
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{transcript}"}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",  # Adjust URL as needed
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Analysis error with {ai_provider} {model}: {str(e)}")
        return None

def generate_outline(transcript, wisdom, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create a structured outline based on transcript and wisdom"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["outline_creation"]
        
        # Include knowledge base context if available
        if knowledge_base:
            knowledge_context = "\n\n".join([
                f"## {name}\n{content}" 
                for name, content in knowledge_base.items()
            ])
            system_prompt = f"""Use the following knowledge base to inform your analysis:

{knowledge_context}

When creating the outline, please incorporate these perspectives and guidelines.

Original Prompt:
{prompt}"""
        else:
            system_prompt = prompt
        
        # Combine transcript and wisdom for better context
        content = f"TRANSCRIPT:\n{transcript}\n\nWISDOM:\n{wisdom}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error creating outline with {ai_provider} {model}: {str(e)}")
        return None

def generate_social_content(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create social media posts based on the content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["social_media"]
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error creating social content with {ai_provider} {model}: {str(e)}")
        return None

def generate_image_prompts(wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Create image generation prompts based on the content"""
    try:
        prompt = custom_prompt or DEFAULT_PROMPTS["image_prompts"]
        
        # Combine wisdom and outline for context
        content = f"WISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1000,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error creating image prompts with {ai_provider} {model}: {str(e)}")
        return None

def generate_article(transcript, wisdom, outline, ai_provider, model, custom_prompt=None, knowledge_base=None):
    """Write a full article based on the outline and content"""
    try:
        prompt = custom_prompt or """Write a comprehensive, engaging article based on the provided outline and wisdom.
        Include an introduction, developed sections following the outline, and a conclusion.
        Maintain a conversational yet authoritative tone."""
        
        # Combine all content for context
        content = f"TRANSCRIPT EXCERPT:\n{transcript[:1000]}...\n\nWISDOM:\n{wisdom}\n\nOUTLINE:\n{outline}"
        
        # Use the selected AI provider and model
        if ai_provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=2500
            )
            return response.choices[0].message.content
            
        elif ai_provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=2500,
                system=prompt,
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
            
        elif ai_provider == "Grok":
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            }
            response = requests.post(
                "https://api.grok.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error writing article with {ai_provider} {model}: {str(e)}")
        return None

def generate_seo_metadata(content, title):
    """Generate SEO metadata for the content"""
    try:
        prompt = f"""As an SEO expert, analyze this content and generate essential SEO metadata:

Content Title: {title}
Content Preview: {content[:1000]}...

Please provide:
1. SEO-optimized title (50-60 chars)
2. Meta description (150-160 chars)
3. Primary keyword
4. 3-4 secondary keywords
5. Recommended URL slug
6. Schema type recommendation

Format as JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO expert that provides metadata in JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating SEO metadata: {str(e)}")
        return None

def process_all_content(text, ai_provider, model, knowledge_base=None):
    """Process all content stages at once"""
    try:
        results = {
            'wisdom': None,
            'outline': None,
            'social_posts': None,
            'image_prompts': None,
            'article': None
        }
        
        # Sequential processing with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Generate wisdom
        status_text.text("Extracting wisdom...")
        results['wisdom'] = generate_wisdom(text, ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.2)
        
        # Generate outline
        status_text.text("Creating outline...")
        results['outline'] = generate_outline(text, results['wisdom'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.4)
        
        # Generate social content
        status_text.text("Generating social media content...")
        results['social_posts'] = generate_social_content(results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.6)
        
        # Generate image prompts
        status_text.text("Creating image prompts...")
        results['image_prompts'] = generate_image_prompts(results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(0.8)
        
        # Generate article
        status_text.text("Writing full article...")
        results['article'] = generate_article(text, results['wisdom'], results['outline'], ai_provider, model, knowledge_base=knowledge_base)
        progress_bar.progress(1.0)
        
        status_text.text("Content generation complete!")
        return results
        
    except Exception as e:
        st.error(f"Error in batch processing: {str(e)}")
        return None

def main():
    st.title("WhisperForge")
    st.write("Transform your spoken ideas into polished content with AI assistance.")
    
    # Initialize session state for model selection
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = "OpenAI"
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = None
    
    # ===== SIDEBAR CONFIGURATION =====
    with st.sidebar:
        st.header("Configuration")
        
        # Move user selection to a less prominent location
        with st.expander("Advanced Settings", expanded=False):
            selected_user = st.selectbox("User Profile", options=["default"], key="user_profile")
        
        # Load knowledge base for selected user
        knowledge_base = load_user_knowledge_base(selected_user)
        
        # Knowledge Base Management
        with st.expander("Knowledge Base", expanded=False):
            st.write("Current Knowledge Base Files:")
            if knowledge_base:
                # Use selectbox instead of nested expanders
                selected_file = st.selectbox(
                    "Select file to view",
                    options=list(knowledge_base.keys()),
                    key="kb_file_selector"
                )
                if selected_file:
                    st.text_area(
                        "Content",
                        value=knowledge_base[selected_file],
                        height=100,
                        key=f"kb_{selected_file}"
                    )
            else:
                st.info("No knowledge base files found.")
            
            # Upload new knowledge base file
            uploaded_kb = st.file_uploader(
                "Add Knowledge Base File", 
                type=['txt', 'md'],
                key="kb_uploader"
            )
            
            if uploaded_kb:
                kb_name = st.text_input("File Name (without extension)", 
                                      value=os.path.splitext(uploaded_kb.name)[0])
                if st.button("Save to Knowledge Base"):
                    try:
                        kb_path = f'prompts/{selected_user}/knowledge_base'
                        os.makedirs(kb_path, exist_ok=True)
                        
                        with open(os.path.join(kb_path, f"{kb_name}.md"), "wb") as f:
                            f.write(uploaded_kb.getvalue())
                        st.success("Knowledge base file added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error saving knowledge base file: {str(e)}")
        
        # AI Provider selection in sidebar
        ai_provider = st.selectbox(
            "AI Provider", 
            options=["OpenAI", "Anthropic", "Grok"],
            key="ai_provider_select",
            on_change=lambda: setattr(st.session_state, 'ai_model', None)  # Reset model when provider changes
        )
        st.session_state.ai_provider = ai_provider
        
        # Fetch and display available models based on provider
        available_models = get_available_models(ai_provider)
        
        # Model descriptions for helpful UI
        model_descriptions = {
            "gpt-4": "Most capable OpenAI model",
            "gpt-3.5-turbo": "Faster, cost-effective OpenAI model",
            "claude-3-opus-20240229": "Most capable Anthropic model",
            "claude-3-sonnet-20240229": "Balanced Anthropic model",
            "claude-3-haiku-20240307": "Fast, efficient Anthropic model",
            "grok-1": "Grok's base model"
        }
        
        # If no model is selected or previous model isn't in new provider's list, select first
        if not st.session_state.ai_model or st.session_state.ai_model not in available_models:
            if available_models:
                st.session_state.ai_model = available_models[0]
        
        # AI Model selection in sidebar
        selected_model = st.selectbox(
            "AI Model",
            options=available_models,
            format_func=lambda x: f"{x}" + (f" ({model_descriptions[x]})" if x in model_descriptions else ""),
            key="ai_model_select"
        )
        st.session_state.ai_model = selected_model
        
        # Configure custom prompts
        with st.expander("Configure Custom Prompts", expanded=False):
            configure_prompts(selected_user, {})
    
    # Initialize session state for content
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'wisdom' not in st.session_state:
        st.session_state.wisdom = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    
    # Add tabs for input selection
    input_type = st.tabs(["Audio Upload", "Text Input"])
    
    with input_type[0]:
        # Existing audio upload functionality
        uploaded_file = st.file_uploader("Upload Audio File", type=['mp3', 'wav', 'ogg', 'm4a'])
        
        if uploaded_file is not None:
            st.audio(uploaded_file)
            
            # Input field for title
            title = st.text_input("Title (Optional)", 
                                value="Transcription - " + datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                key="audio_title")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Regular transcribe button
                if st.button("Transcribe Audio"):
                    with st.spinner("Transcribing audio..."):
                        # Check file size and use appropriate method
                        file_size = uploaded_file.size
                        
                        if file_size > 25 * 1024 * 1024:  # 25 MB
                            st.warning("Large file detected. Using chunked processing.")
                            # Save uploaded file temporarily to process it
                            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                            
                            # Process large file in chunks
                            st.session_state.transcription = transcribe_large_file(tmp_path)
                            os.unlink(tmp_path)  # Remove temp file
                        else:
                            # Use simpler method for smaller files
                            transcript = transcribe_audio(uploaded_file)
                            st.session_state.transcription = transcript
            
            with col2:
                # I'm Feeling Lucky button
                if st.button("I'm Feeling Lucky 🎲"):
                    with st.spinner("Processing everything..."):
                        # First transcribe
                        transcript = transcribe_audio(uploaded_file)
                        st.session_state.transcription = transcript
                        
                        # Then process all content
                        results = process_all_content(
                            transcript,
                            st.session_state.ai_provider,
                            st.session_state.ai_model,
                            knowledge_base
                        )
                        
                        if results:
                            # Store results in session state
                            st.session_state.wisdom = results['wisdom']
                            st.session_state.outline = results['outline']
                            st.session_state.social_posts = results['social_posts']
                            st.session_state.image_prompts = results['image_prompts']
                            st.session_state.article = results['article']
                            
                            # Automatically post to Notion
                            with st.spinner("Saving to Notion..."):
                                notion_success = create_content_notion_entry(
                                    title,
                                    transcript,
                                    results['wisdom'],
                                    results['outline'],
                                    results['social_posts'],
                                    results['image_prompts'],
                                    results['article']
                                )
                                if notion_success:
                                    st.success("Everything processed and saved to Notion!")
                                
    with input_type[1]:
        # New text input functionality
        st.write("Paste your text below to analyze and generate content:")
        input_text = st.text_area("Input Text", height=200)
        title = st.text_input("Title (Optional)", 
                             value="Content - " + datetime.now().strftime("%Y-%m-%d %H:%M"), 
                             key="text_title")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Regular process button
            if st.button("Process Text"):
                if input_text:
                    st.session_state.transcription = input_text
                else:
                    st.error("Please enter some text to process")
        
        with col2:
            # I'm Feeling Lucky button for text
            if st.button("I'm Feeling Lucky 🎲", key="lucky_text"):
                if input_text:
                    with st.spinner("Processing everything..."):
                        st.session_state.transcription = input_text
                        
                        results = process_all_content(
                            input_text,
                            st.session_state.ai_provider,
                            st.session_state.ai_model,
                            knowledge_base
                        )
                        
                        if results:
                            # Store results and post to Notion
                            st.session_state.wisdom = results['wisdom']
                            st.session_state.outline = results['outline']
                            st.session_state.social_posts = results['social_posts']
                            st.session_state.image_prompts = results['image_prompts']
                            st.session_state.article = results['article']
                            
                            with st.spinner("Saving to Notion..."):
                                notion_success = create_content_notion_entry(
                                    title,
                                    input_text,
                                    results['wisdom'],
                                    results['outline'],
                                    results['social_posts'],
                                    results['image_prompts'],
                                    results['article']
                                )
                                if notion_success:
                                    st.success("Everything processed and saved to Notion!")
                else:
                    st.error("Please enter some text to process")

    # Rest of the content generation code remains the same since it all works from st.session_state.transcription
    if st.session_state.transcription:
        st.header("Content:")
        st.write(st.session_state.transcription)
        
        # Extract wisdom section with knowledge base
        with st.expander("Extract Wisdom", expanded=False):
            if st.button("Generate Wisdom"):
                try:
                    if not st.session_state.ai_model:
                        st.error("Please select an AI model in the sidebar configuration.")
                        return
                        
                    # Get the custom prompt if available
                    wisdom_prompt = get_custom_prompt(selected_user, "wisdom_extraction", {}, DEFAULT_PROMPTS)
                    
                    with st.spinner("Extracting wisdom from transcript..."):
                        st.session_state.wisdom = generate_wisdom(
                            st.session_state.transcription, 
                            st.session_state.ai_provider, 
                            st.session_state.ai_model,
                            wisdom_prompt,
                            knowledge_base  # Pass knowledge base to generation function
                        )
                except Exception as e:
                    st.error(f"Error generating wisdom: {str(e)}")
        
        # Display wisdom if available
        if st.session_state.wisdom:
            st.subheader("Extracted Wisdom:")
            st.write(st.session_state.wisdom)
            
            # Initialize session states for other content types if not already done
            if 'outline' not in st.session_state:
                st.session_state.outline = ""
            if 'social_posts' not in st.session_state:
                st.session_state.social_posts = ""
            if 'image_prompts' not in st.session_state:
                st.session_state.image_prompts = ""
            if 'article' not in st.session_state:
                st.session_state.article = ""
            
            # Create outline
            with st.expander("Create Outline", expanded=False):
                if st.button("Generate Outline"):
                    try:
                        # Get the custom prompt if available
                        outline_prompt = get_custom_prompt(selected_user, "outline_creation", {}, DEFAULT_PROMPTS)
                        
                        with st.spinner("Creating outline..."):
                            st.session_state.outline = generate_outline(
                                st.session_state.transcription,
                                st.session_state.wisdom,
                                st.session_state.ai_provider,
                                st.session_state.ai_model,
                                outline_prompt,
                                knowledge_base
                            )
                    except Exception as e:
                        st.error(f"Error generating outline: {str(e)}")
            
            # Display outline if available
            if st.session_state.outline:
                st.subheader("Content Outline:")
                st.write(st.session_state.outline)
                
                # Social media content
                with st.expander("Create Social Media Content", expanded=False):
                    if st.button("Generate Social Posts"):
                        try:
                            # Get the custom prompt if available
                            social_prompt = get_custom_prompt(selected_user, "social_media", {}, DEFAULT_PROMPTS)
                            
                            with st.spinner("Creating social media content..."):
                                st.session_state.social_posts = generate_social_content(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    social_prompt,
                                    knowledge_base
                                )
                        except Exception as e:
                            st.error(f"Error generating social content: {str(e)}")
                
                # Display social posts if available
                if st.session_state.social_posts:
                    st.subheader("Social Media Content:")
                    st.write(st.session_state.social_posts)
                
                # Image prompts section
                with st.expander("Create Image Prompts", expanded=False):
                    if st.button("Generate Image Prompts"):
                        try:
                            # Get the custom prompt if available
                            image_prompt = get_custom_prompt(selected_user, "image_prompts", {}, DEFAULT_PROMPTS)
                            
                            with st.spinner("Creating image generation prompts..."):
                                st.session_state.image_prompts = generate_image_prompts(
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    image_prompt,
                                    knowledge_base
                                )
                        except Exception as e:
                            st.error(f"Error generating image prompts: {str(e)}")
                
                # Display image prompts if available
                if st.session_state.image_prompts:
                    st.subheader("Image Prompts:")
                    st.write(st.session_state.image_prompts)
                
                # Full article section
                with st.expander("Write Full Article", expanded=False):
                    if st.button("Generate Article"):
                        try:
                            # Get the custom prompt if available
                            article_prompt = get_custom_prompt(selected_user, "article_writing", {}, DEFAULT_PROMPTS)
                            
                            with st.spinner("Writing full article..."):
                                st.session_state.article = generate_article(
                                    st.session_state.transcription,
                                    st.session_state.wisdom,
                                    st.session_state.outline,
                                    st.session_state.ai_provider,
                                    st.session_state.ai_model,
                                    article_prompt,
                                    knowledge_base
                                )
                        except Exception as e:
                            st.error(f"Error generating article: {str(e)}")
                
                # Display article if available
                if st.session_state.article:
                    st.subheader("Full Article:")
                    st.write(st.session_state.article)
        
        # Export to Notion button - available at any stage
        if st.button("Save to Notion"):
            with st.spinner("Exporting to Notion..."):
                # Check if Notion API key is configured
                if not os.getenv("NOTION_API_KEY") or not os.getenv("NOTION_DATABASE_ID"):
                    st.error("Notion API key or database ID not configured. Please set them in your .env file.")
                else:
                    # Get title from input or use a default
                    if 'title' not in locals() or not title:
                        title = "Transcription - " + datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # Safely get all content types from session state
                    wisdom = st.session_state.get('wisdom', None)
                    outline = st.session_state.get('outline', None)  
                    social_posts = st.session_state.get('social_posts', None)
                    image_prompts = st.session_state.get('image_prompts', None)
                    article = st.session_state.get('article', None)
                    
                    # Create Notion entry with all available content
                    notion_url = create_content_notion_entry(
                        title,
                        st.session_state.transcription,
                        wisdom,
                        outline,
                        social_posts,
                        image_prompts,
                        article
                    )
                    
                    if notion_url:
                        st.success(f"Successfully saved to Notion! [Open in Notion]({notion_url})")
                    else:
                        st.error("Failed to save to Notion. Please check your API keys.")

# Default prompts in case user prompts are not available
DEFAULT_PROMPTS = {
    "wisdom_extraction": """Extract key insights, lessons, and wisdom from the transcript. Focus on actionable takeaways and profound realizations.""",
    
    "summary": """## Summary
Create a concise summary of the main points and key messages in the transcript.
Capture the essence of the content in a few paragraphs.""",
    
    "outline_creation": """Create a detailed outline for an article or blog post based on the transcript and extracted wisdom. Include major sections and subsections.""",
    
    "social_media": """Generate engaging social media posts for different platforms (Twitter, LinkedIn, Instagram) based on the key insights.""",
    
    "image_prompts": """Create detailed image generation prompts that visualize the key concepts and metaphors from the content.""",
    
    "article_writing": """Write a comprehensive article based on the provided outline and wisdom. Maintain a clear narrative flow and engaging style.""",
    
    "seo_analysis": """Analyze the content from an SEO perspective and provide optimization recommendations for better search visibility while maintaining content quality."""
}

if __name__ == "__main__":
    main() 