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

def load_prompts():
    """Load all prompt files from the prompts directory"""
    prompts = {}
    prompt_files = glob.glob('prompts/*.md')
    
    for file_path in prompt_files:
        with open(file_path, 'r') as f:
            content = f.read()
            name = os.path.splitext(os.path.basename(file_path))[0].replace('_', ' ').title()
            prompts[name] = content
    
    return prompts

def apply_prompt(text, prompt_content, provider, model):
    """Apply a specific prompt using the selected model and provider"""
    try:
        prompt_parts = prompt_content.split('## Prompt')
        if len(prompt_parts) > 1:
            prompt_text = prompt_parts[1].strip()
        else:
            prompt_text = prompt_content

        if provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": f"Here's the transcription to analyze:\n\n{text}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content

        elif provider == "Anthropic":
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=1500,
                system=prompt_text,
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
                    {"role": "system", "content": prompt_text},
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

def create_notion_blocks(content):
    """Split content into Notion blocks of acceptable size"""
    MAX_BLOCK_SIZE = 1900  # Slightly under Notion's 2000 limit for safety
    blocks = []
    
    # Split content into chunks of MAX_BLOCK_SIZE
    for i in range(0, len(content), MAX_BLOCK_SIZE):
        chunk = content[i:i + MAX_BLOCK_SIZE]
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": chunk}}]
            }
        })
    
    return blocks

def create_notion_entry(title, audio_file, content, analysis):
    """Create a new entry in Notion database with audio, transcription and analysis"""
    try:
        # Create blocks for transcription and analysis
        blocks = [
            # Audio section toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "🎧 Original Audio"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": "Audio file attached"}}]
                            }
                        }
                    ]
                }
            },
            # Divider
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            # Transcription toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "📝 Transcription"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        }
                        for chunk in [content[i:i+1900] for i in range(0, len(content), 1900)]
                    ]
                }
            },
            # Divider
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            # Analysis toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "🔍 Analysis & Insights"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        }
                        for chunk in [analysis[i:i+1900] for i in range(0, len(analysis), 1900)]
                    ]
                }
            }
        ]
        
        # Create the page
        response = notion_client.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": title}}]
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
        
        # Return the URL of the created page
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

    # Load available prompts
    prompts = load_prompts()

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
            
            # Multi-select for prompts
            selected_prompts = st.multiselect(
                "Select analysis prompts to apply:",
                options=list(prompts.keys())
            )
            
            # Analyze button
            if selected_prompts and st.button("Analyze with Selected Prompts"):
                for prompt_name in selected_prompts:
                    with st.spinner(f"Applying {prompt_name} using {selected_provider} {selected_model}..."):
                        analysis = apply_prompt(
                            st.session_state.transcription, 
                            prompts[prompt_name],
                            selected_provider,
                            LLM_MODELS[selected_provider][selected_model]
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