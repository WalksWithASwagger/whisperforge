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
    """Generate a 5-word descriptive title from the transcript"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Create a concise, descriptive 5-word title that captures the main topic or theme of this content. Make it clear and engaging. Return ONLY the 5 words, nothing else."},
                {"role": "user", "content": f"Generate a 5-word title for this transcript:\n\n{text[:2000]}..."} # First 2000 chars for context
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Title generation error: {str(e)}")
        return "Untitled Audio Transcription"

def create_notion_entry(title, audio_file, content, analysis):
    """Create a new entry in Notion database with structured sections"""
    try:
        # Generate summary and AI title
        summary = generate_summary(content, title)
        ai_title = generate_short_title(content)
        notion_title = f"WHISPER: {ai_title}"
        
        # Helper function to create a toggle block
        def create_toggle(title, content_text, color):
            return {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": title}}],
                    "color": color,
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        }
                        for chunk in [content_text[i:i+1900] for i in range(0, len(content_text), 1900)]
                    ]
                }
            }

        blocks = [
            # Original filename
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"Original File: {audio_file.name}"},
                            "annotations": {"italic": True, "color": "gray"}
                        }
                    ]
                }
            },
            # Summary callout
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": summary}}],
                    "icon": {"emoji": "💜"},
                    "color": "purple_background"
                }
            },
            # Spacing
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": []}
            }
        ]

        # Add all toggle sections
        toggle_sections = [
            ("Original Audio", "Audio file attached", "gray_background"),
            ("Transcription", content, "brown_background"),
            ("Wisdom", analysis, "brown_background"),
            ("Socials", "Social media content will go here", "default"),
            ("Image Prompts", "Image generation prompts will go here", "green_background"),
            ("Outline", "Content outline will go here", "blue_background"),
            ("Draft Post", "Draft post content will go here", "purple_background")
        ]

        for title, content_text, color in toggle_sections:
            blocks.append(create_toggle(title, content_text, color))
            # Add spacing after each toggle
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": []}
            })

        # Create the page with the new title format
        response = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": notion_title}}]
                },
                "Created Date": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "Tags": {
                    "multi_select": [{"name": "transcription"}]
                }
            },
            children=blocks
        )
        
        page_id = response['id'].replace('-', '')
        return f"https://notion.so/{page_id}"
    
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

def main():
    st.title("WhisperForge")
    st.write("AI-powered audio transcription and analysis tool")

    # Load available users and their prompts/knowledge bases
    users = load_prompts()
    
    # User selection
    selected_user = st.sidebar.selectbox(
        "Select User",
        options=list(users.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_user:
        st.sidebar.write(f"### Available Knowledge Base Files:")
        for kb_name in users[selected_user]['knowledge_base'].keys():
            st.sidebar.write(f"✓ {kb_name}")
    
    # Session state
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'analyses' not in st.session_state:
        st.session_state.analyses = {}
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None

    # File uploader
    audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
    if audio_file is not None:
        st.session_state.audio_file = audio_file
        st.audio(audio_file)
        
        # Add a title input field
        custom_title = st.text_input("Title (optional)", 
                                   value=f"Transcription - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        col1, col2 = st.columns(2)
        
        # Transcribe button
        if col1.button("Transcribe"):
            with st.spinner("Processing audio..."):
                try:
                    # Save temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                        temp_file.write(audio_file.read())
                        temp_path = temp_file.name
                    
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
                        except Exception as e:
                            st.error(f"Transcription error: {str(e)}")
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    # Reset analyses when new transcription is made
                    if st.session_state.transcription:
                        st.session_state.analyses = {}
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

        # Show transcription and prompt selection if we have a transcription
        if st.session_state.transcription:
            st.write("### Transcription:")
            st.write(st.session_state.transcription)
            
            # Two-step model selection
            col1, col2 = st.columns(2)
            
            # Provider selection
            selected_provider = col1.selectbox(
                "Select AI Provider:",
                options=list(LLM_MODELS.keys())
            )
            
            # Model selection based on provider
            selected_model = col2.selectbox(
                f"Select {selected_provider} Model:",
                options=list(LLM_MODELS[selected_provider].keys()),
                format_func=lambda x: x
            )
            
            # Multi-select for prompts from selected user
            selected_prompts = st.multiselect(
                "Select analysis prompts to apply:",
                options=list(users[selected_user]['prompts'].keys())
            )
            
            # Analyze button
            if selected_prompts and st.button("Analyze with Selected Prompts"):
                for prompt_name in selected_prompts:
                    with st.spinner(f"Applying {prompt_name} using {selected_provider} {selected_model}..."):
                        analysis = apply_prompt(
                            st.session_state.transcription, 
                            users[selected_user]['prompts'][prompt_name],
                            selected_provider,
                            LLM_MODELS[selected_provider][selected_model],
                            user_knowledge=users[selected_user]['knowledge_base']
                        )
                        if analysis:
                            st.session_state.analyses[prompt_name] = analysis
            
            # Display analyses
            if st.session_state.analyses:
                for prompt_name, analysis in st.session_state.analyses.items():
                    st.write(f"### Analysis: {prompt_name}")
                    st.write(analysis)
                
                # Save to Notion button
                if st.button("Save to Notion"):
                    with st.spinner("Saving to Notion..."):
                        # Combine all analyses into one text
                        combined_analysis = "\n\n".join([
                            f"## {name}\n{analysis}" 
                            for name, analysis in st.session_state.analyses.items()
                        ])
                        
                        notion_url = create_notion_entry(
                            custom_title, 
                            st.session_state.audio_file,
                            st.session_state.transcription, 
                            combined_analysis
                        )
                        
                        if notion_url:
                            st.success("Successfully saved to Notion!")
                            st.markdown(f"[View in Notion]({notion_url})")
                        else:
                            st.error("Failed to save to Notion")

if __name__ == "__main__":
    main() 