import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from notion_client import Client
from datetime import datetime
from pydub import AudioSegment
import tempfile
import math

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI()
notion_client = Client(auth=os.getenv("NOTION_API_KEY"))

# Configure Notion database ID
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def chunk_audio(audio_path, target_size_mb=20):
    """Split audio file into chunks of approximately target_size_mb"""
    audio = AudioSegment.from_file(audio_path)
    
    # Calculate number of chunks needed
    file_size = os.path.getsize(audio_path)
    num_chunks = math.ceil(file_size / (target_size_mb * 1024 * 1024))
    chunk_length_ms = len(audio) // num_chunks
    
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            chunk.export(temp_file.name, format='mp3')
            chunks.append(temp_file.name)
    
    return chunks

def extract_wisdom(text):
    """Extract key insights and wisdom from the transcribed text"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing conversations and extracting key insights, themes, and wisdom. Provide a concise summary followed by key points and insights."},
                {"role": "user", "content": f"Please analyze this transcription and extract the key insights and wisdom:\n\n{text}"}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

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

def create_notion_entry(title, content, analysis):
    """Create a new entry in Notion database with the transcription and analysis"""
    try:
        # Create blocks for transcription and analysis
        transcription_blocks = create_notion_blocks(content)
        analysis_blocks = create_notion_blocks(analysis)
        
        # Combine all blocks with headers
        all_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Transcription"}}]
                }
            },
            *transcription_blocks,
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Analysis & Insights"}}]
                }
            },
            *analysis_blocks
        ]
        
        notion_client.pages.create(
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
            children=all_blocks
        )
        return True
    except Exception as e:
        st.error(f"Notion API Error: {str(e)}")
        return False

def main():
    st.title("WhisperForge")
    st.write("AI-powered audio transcription and analysis tool")

    # Session state for storing transcription
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None

    # File uploader
    audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])

    if audio_file is not None:
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
                        
                        progress_bar = st.progress(0)
                        for i, chunk_path in enumerate(chunks):
                            st.write(f"Transcribing part {i+1} of {len(chunks)}...")
                            with open(chunk_path, "rb") as audio:
                                transcript = openai_client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio
                                )
                                full_transcript += transcript.text + " "
                            os.remove(chunk_path)
                            progress_bar.progress((i + 1) / len(chunks))
                        
                        st.session_state.transcription = full_transcript.strip()
                    else:
                        with open(temp_path, "rb") as audio:
                            transcript = openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio
                            )
                            st.session_state.transcription = transcript.text
                    
                    os.remove(temp_path)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

        # Show transcription and analyze button if we have a transcription
        if st.session_state.transcription:
            st.write("### Transcription:")
            st.write(st.session_state.transcription)
            
            if col2.button("Analyze"):
                with st.spinner("Extracting insights..."):
                    st.session_state.analysis = extract_wisdom(st.session_state.transcription)
        
        # Show analysis and save button if we have both transcription and analysis
        if st.session_state.analysis:
            st.write("### Analysis & Insights:")
            st.write(st.session_state.analysis)
            
            if st.button("Save to Notion"):
                with st.spinner("Saving to Notion..."):
                    if create_notion_entry(custom_title, st.session_state.transcription, st.session_state.analysis):
                        st.success("Successfully saved to Notion database!")
                    else:
                        st.error("Failed to save to Notion")

    # Add this temporary code to see your database structure
    database = notion_client.databases.retrieve(NOTION_DATABASE_ID)
    st.write(database["properties"])

if __name__ == "__main__":
    main() 