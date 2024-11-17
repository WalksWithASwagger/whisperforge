import streamlit as st
from streamlit.components.v1 import html
import tempfile
import os
from pathlib import Path
from openai import OpenAI
from datetime import datetime
from notion_client import Client

# Initialize the OpenAI client
client = None

def local_css():
    st.markdown("""
        <style>
        /* Main theme colors */
        :root {
            --main-bg-color: #000000;
            --text-color: #ffffff;
            --accent-color: #ff4d4d;
            --border-color: rgba(255,255,255,0.1);
            --secondary-bg: #1a1a1a;
        }
        
        /* Global styles */
        .stApp {
            background-color: var(--main-bg-color);
            color: var(--text-color);
        }
        
        /* Header styling */
        .brand-header {
            text-align: left;
            padding: 1.5rem 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2rem;
        }
        
        .brand-name {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: var(--text-color);
        }
        
        /* Input fields */
        .stTextInput input {
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }
        
        /* Dropdowns */
        .stSelectbox select {
            background-color: var(--secondary-bg);
            color: var(--text-color);
        }
        
        /* File uploader */
        .stFileUploader {
            background-color: var(--secondary-bg);
            border: 1px dashed var(--border-color);
            padding: 1rem;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background-color: var(--accent-color);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: var(--secondary-bg);
        }
        
        .stTabs [data-baseweb="tab"] {
            color: var(--text-color);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: var(--secondary-bg);
            color: var(--text-color);
        }
        
        /* Text areas */
        .stTextArea textarea {
            background-color: var(--secondary-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="brand-header"><h1 class="brand-name">WhisperForge</h1></div>', unsafe_allow_html=True)

def render_footer():
    st.markdown("""
        <div class="footer">
            <p>Created by Kris Krüg © 2024 | WhisperForge.ai v0.1 alpha</p>
        </div>
    """, unsafe_allow_html=True)

def split_audio(file_path, chunk_length_ms):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    st.info(f"Loading audio file: {filename}")
    
    # Use ffmpeg directly instead of pydub
    import subprocess
    import math
    
    # Get duration using ffprobe
    duration_cmd = [
        'ffprobe', 
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    
    duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
    num_chunks = math.ceil(duration / (chunk_length_ms / 1000))
    
    chunk_files = []
    for i in range(num_chunks):
        start_time = i * chunk_length_ms / 1000
        chunk_file = f"whisperforge_{filename}_chunk_{i}.mp3"
        
        # Use ffmpeg to extract chunk
        subprocess.run([
            'ffmpeg',
            '-y',  # Overwrite output files
            '-i', file_path,
            '-ss', str(start_time),
            '-t', str(chunk_length_ms / 1000),
            '-acodec', 'libmp3lame',
            chunk_file
        ], stderr=subprocess.DEVNULL)
        
        chunk_files.append(chunk_file)
        st.info(f"Created chunk {i+1} of {num_chunks}")
    
    return chunk_files

def transcribe_chunks(chunk_files):
    transcriptions = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, chunk_file in enumerate(chunk_files):
        try:
            with open(chunk_file, "rb") as audio_file:
                # Update progress bar and status
                progress = (i + 1) / len(chunk_files)
                progress_bar.progress(progress)
                status_text.text(f"Transcribing: {i + 1}/{len(chunk_files)}")
                
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcriptions.append(transcription.text)
                
                # Clean up chunk file after processing
                os.remove(chunk_file)
        except Exception as e:
            st.error(f"Error transcribing chunk {i+1}: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    return transcriptions

def process_with_gpt(text, mode, custom_prompt=""):
    # Convert mode to lowercase and handle spaces
    mode = mode.lower().replace(" ", "_")
    
    prompts = {
        "extract_insights": """Analyze this text and extract:

1. Key Insights (5-7 bullet points)
- Focus on main themes and important realizations
- Start each point with a dash (-)
- Be specific and actionable

2. Actionable Takeaways (3-5 bullet points)
- Focus on practical steps or applications
- Start each point with a dash (-)
- Make them specific and implementable

3. Notable Quotes (2-3 quotes)
- Select the most impactful or meaningful quotes
- Start each with a dash (-)
- Include context if necessary

Format the output with these exact headers and bullet points.""",
        "summarize": """Create a structured summary of this text with:

1. A one-line summary (max 20 words)
2. Key themes (3-5 bullet points)
3. Main conclusions (2-3 bullet points)

Format with headers and bullet points.""",
        "custom_instructions": custom_prompt
    }
    
    try:
        prompt = prompts.get(mode, custom_prompt)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error processing with GPT: {str(e)}")
        return None

def chunk_text(text, limit=1900):
    """Split text into chunks, trying to break at sentences."""
    if len(text) <= limit:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split into sentences (roughly)
    sentences = text.replace("\n", ". ").split(". ")
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < limit:
            current_chunk += sentence + ". "
        else:
            # Save current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_title_summary_tags(text):
    """Generate a 5-word title, one-line summary, and 3 relevant tags using GPT."""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Generate:
                1. A compelling 5-word title that captures the essence
                2. A one-line summary (max 15 words)
                3. Three relevant tags (single words or short phrases)

                Format as:
                TITLE: [5 words]
                SUMMARY: [one line]
                TAGS: [tag1], [tag2], [tag3]"""},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content
        title = result.split("TITLE: ")[1].split("\n")[0].strip()
        summary = result.split("SUMMARY: ")[1].split("\n")[0].strip()
        tags = result.split("TAGS: ")[1].strip().split(", ")
        return title, summary, tags
    except Exception as e:
        st.error(f"Error generating title and summary: {str(e)}")
        return "Untitled Transcription", "[Summary generation failed]", ["transcription"]

def parse_processed_text(text):
    """Parse the processed text into sections."""
    sections = {
        "insights": [],
        "takeaways": [],
        "quotes": []
    }
    
    current_section = None
    for line in text.split('\n'):
        line = line.strip()
        if "1. Key Insights" in line:
            current_section = "insights"
        elif "2. Actionable Takeaways" in line:
            current_section = "takeaways"
        elif "3. Notable Quotes" in line:
            current_section = "quotes"
        elif line.startswith("- ") and current_section:
            sections[current_section].append(line[2:])  # Remove "- " prefix
            
    return sections

def send_to_notion(transcription, processed_text, notion_key, filename, database_id="124c6f79-9a33-8065-93b1-c7afdc34ef94"):
    try:
        notion = Client(auth=notion_key)
        
        # Parse the processed text into sections
        sections = parse_processed_text(processed_text)
        
        # Split transcription into chunks for Notion's block limit
        transcription_chunks = chunk_text(transcription)
        
        # Generate title, summary, and tags
        title, summary, tags = generate_title_summary_tags(transcription)
        
        # Get current timestamp for Created Date
        current_time = datetime.now().isoformat()
        
        # Create the page structure
        children = [
            # Divider before summary
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            # Summary in callout block with black square
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": summary}}],
                    "icon": {"emoji": "💡"}
                }
            },
            # Divider after summary
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            # Key Insights toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "Key Insights"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"text": {"content": insight}}]
                            }
                        } for insight in sections["insights"]
                    ]
                }
            },
            # Actionable Takeaways toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "Actionable Takeaways"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"text": {"content": takeaway}}]
                            }
                        } for takeaway in sections["takeaways"]
                    ]
                }
            },
            # Notable Quotes toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "Notable Quotes"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"text": {"content": quote}}]
                            }
                        } for quote in sections["quotes"]
                    ]
                }
            },
            # Transcription toggle
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"text": {"content": "Transcription"}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": chunk}}]
                            }
                        } for chunk in transcription_chunks
                    ]
                }
            }
        ]
        
        # Create the page
        base_filename = os.path.splitext(filename)[0]
        page_title = f"{title} - {base_filename}"
        
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                },
                "Created Date": {
                    "date": {
                        "start": current_time
                    }
                },
                "Tags": {
                    "multi_select": [
                        {"name": tag.lower()} for tag in tags + ["transcription"]
                    ]
                }
            },
            children=children
        )
        
        # Get the page URL
        page_id = response["id"]
        page_url = f"https://notion.so/{page_id.replace('-', '')}"
        
        return True, "Successfully sent to Notion database!", page_url
    except Exception as e:
        st.error(f"Detailed error: {str(e)}")
        if hasattr(e, 'response'):
            st.error(f"Response content: {e.response.text}")
        return False, f"Error sending to Notion: {str(e)}", None

def setup_notion_integration():
    st.sidebar.markdown("### Notion Integration")
    notion_key = st.sidebar.text_input(
        "Notion API Key", 
        value=os.getenv("NOTION_API_KEY", ""),
        type="password",
        help="Your Notion integration token"
    )
    return notion_key, "124c6f799a33806593b1c7afdc34ef94"

def cleanup_temp_files():
    """Clean up any temporary files created during processing."""
    try:
        for file in os.listdir():
            if file.startswith("whisperforge_") and file.endswith(".mp3"):
                os.remove(file)
    except Exception as e:
        st.error(f"Error cleaning up temporary files: {str(e)}")

def main():
    local_css()
    render_header()

    # Initialize session state variables if they don't exist
    if 'transcription_text' not in st.session_state:
        st.session_state.transcription_text = None
    if 'processed_text' not in st.session_state:
        st.session_state.processed_text = None

    # Sidebar configuration
    with st.sidebar:
        st.markdown("### Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        notion_key = None
        enable_notion = st.checkbox("Enable Notion Export")
        if enable_notion:
            notion_key = st.text_input("Notion API Key", type="password")

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Audio File", type=['mp3', 'wav', 'm4a', 'ogg'])
        
    with col2:
        with st.expander("Advanced Settings"):
            chunk_length = st.slider("Chunk Length (min)", 1, 30, 5)
            language = st.selectbox("Language", ["Auto-detect", "English", "Spanish", "French", "German"])
    
    # Processing Mode Selection
    processing_mode = st.selectbox(
        "Processing Mode",
        ["Extract Insights", "Summarize", "Custom Instructions"],
        format_func=lambda x: x.title()
    )
    
    custom_prompt = ""
    if processing_mode == "Custom Instructions":
        custom_prompt = st.text_area("Custom Instructions", height=100)

    # Process button
    if uploaded_file:
        if st.button("Process Audio"):
            if not api_key:
                st.error("Please enter your OpenAI API key")
                return
            
            try:
                cleanup_temp_files()  # Clean up any leftover files
                st.session_state.processing_complete = False
                st.session_state.current_file = uploaded_file.name
                
                # Initialize OpenAI client
                global client
                client = OpenAI(api_key=api_key)
                
                # First Phase: Transcription
                with st.spinner("Transcribing audio..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        audio_path = tmp_file.name

                    # Split audio
                    chunk_files = split_audio(audio_path, chunk_length * 60 * 1000)
                    transcriptions = []
                    
                    # Display progress message
                    progress_message = st.empty()
                    for i, chunk_file in enumerate(chunk_files):
                        progress_message.markdown(f"<div class='progress-message'>Transcribing chunk {i + 1} of {len(chunk_files)}...</div>", unsafe_allow_html=True)
                        transcription = transcribe_chunks([chunk_file])
                        transcriptions.append(transcription[0])  # Assuming transcribe_chunks returns a list

                    # Combine transcriptions
                    transcription_text = "\n".join(transcriptions)
                    st.session_state.transcription_text = transcription_text

                    st.success("Transcription completed!")

                # Second Phase: Post-Processing
                with st.spinner("Processing with GPT..."):
                    processed_text = process_with_gpt(transcription_text, processing_mode.lower(), custom_prompt)
                    st.session_state.processed_text = processed_text
                
                if processed_text:
                    st.success("Processing completed!")

                # Third Phase: Notion Export
                if enable_notion and notion_key:
                    with st.spinner("Sending to Notion..."):
                        success, message, page_url = send_to_notion(
                            transcription_text,
                            processed_text,
                            notion_key,
                            uploaded_file.name
                        )
                        if success:
                            st.success("✅ " + message)
                            st.markdown(f"[Open in Notion]({page_url})", unsafe_allow_html=True)
                        else:
                            st.error("❌ " + message)

                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "Download Transcription",
                        st.session_state.transcription_text,
                        "transcription.txt",
                        "text/plain"
                    )
                with col2:
                    if st.session_state.processed_text:
                        st.download_button(
                            "Download Processed Result",
                            st.session_state.processed_text,
                            "processed_result.txt",
                            "text/plain"
                        )

                st.session_state.processing_complete = True

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                cleanup_temp_files()  # Clean up after processing

    # Show results if they exist in session state
    if st.session_state.transcription_text:
        st.text_area("Full Transcription", st.session_state.transcription_text, height=300)
        
    if st.session_state.processed_text:
        st.text_area("Processed Result", st.session_state.processed_text, height=300)

    render_footer()

if __name__ == "__main__":
    main()
