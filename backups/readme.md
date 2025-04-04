# WhisperForge

Transform spoken ideas into comprehensive content with AI assistance. WhisperForge transcribes audio, extracts insights, and creates structured Notion pages with multiple content formats.

## Features

- **Audio Transcription**: Support for MP3, WAV, OGG, and M4A files
- **Multi-Model AI Integration**: OpenAI, Anthropic, and Grok support
- **Smart Content Generation**: 
  - AI-generated descriptive titles
  - One-sentence content summaries
  - Key wisdom extraction
  - Content tags generation
- **Notion Integration**: 
  - Structured page layout with collapsible sections
  - Automatic metadata and properties
  - Professional formatting

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Configure environment variables in `.env`:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
NOTION_API_KEY=your_key_here
NOTION_DATABASE_ID=your_database_id
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Upload audio file and process content:
   - Select AI provider and model
   - Click "Transcribe Audio"
   - Generate additional content as needed
   - Export to Notion at any point

## Notion Integration Details

Each Notion page includes:
1. AI-generated descriptive title (prefixed with "WHISPER:")
2. Purple callout with AI-generated summary
3. Collapsible sections:
   - ▶️ Original Audio
   - ▶️ Transcription
   - ▶️ Wisdom
   - ▶️ Socials
   - ▶️ Image Prompts
   - ▶️ Outline
   - ▶️ Draft Post
4. Metadata section with:
   - Original audio filename
   - Creation date
   - WhisperForge attribution
5. Database properties:
   - Created Date
   - Tags (AI-generated)

## Technical Notes

- Handles large audio files through chunked processing
- Respects Notion's 2000-character block limit
- Uses GPT for generating titles, summaries, and tags
- Maintains consistent formatting and structure

## Future Enhancements

- Additional content generation options
- More AI provider integrations
- Custom prompt configurations
- Enhanced metadata and tagging

![WhisperForge Banner](assets/whisperforge_banner.png)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
  - [Quick Start](#quick-start)
  - [Step-by-Step Workflow](#step-by-step-workflow)
  - [Customizing Prompts](#customizing-prompts)
  - [Managing Knowledge Base](#managing-knowledge-base)
- [Technical Architecture](#technical-architecture)
- [Configuration](#configuration)
- [The Vision](#the-vision)
- [Appendix: Enhancement Ideas](#appendix-enhancement-ideas)

## Overview

WhisperForge is an AI-powered audio transcription and content creation tool designed for streamlining the process of turning your spoken thoughts into polished, publishable content. Built with OpenAI's Whisper model for transcription and various LLMs (OpenAI, Anthropic, Grok) for content enhancement, WhisperForge creates a seamless pipeline from dictation to publication-ready materials.

Record your thoughts, upload the audio, and let WhisperForge extract wisdom, create outlines, generate social media content, suggest image prompts, and even draft complete articles - all properly formatted and saved to your Notion workspace.

## Installation

### Prerequisites
- Python 3.8 or higher
- Streamlit
- OpenAI API key
- Notion API key and database ID
- (Optional) Anthropic API key
- (Optional) Grok API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/whisperforge.git
   cd whisperforge
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv whisperforge-env
   source whisperforge-env/bin/activate  # On Windows, use: whisperforge-env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following:
   ```
   OPENAI_API_KEY=your_openai_api_key
   NOTION_API_KEY=your_notion_api_key
   NOTION_DATABASE_ID=your_notion_database_id
   ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
   GROK_API_KEY=your_grok_api_key  # Optional
   ```

5. **Create prompt directories**
   ```bash
   mkdir -p prompts/YourName/prompts
   mkdir -p prompts/YourName/knowledge_base
   mkdir -p prompts/YourName/custom_prompts
   ```

## Usage Guide

### Quick Start

1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. Select your user profile in the sidebar

3. Upload an audio file

4. Click "Transcribe Audio"

5. Review the transcription and select your preferred AI model

6. Use the expanders to generate desired content:
   - Extract Wisdom
   - Create Outline
   - Generate Social Posts
   - Create Image Prompts
   - Write Full Article

7. Click "Save to Notion" at any point to export your content

### Step-by-Step Workflow

#### 1. Audio Upload and Transcription
- Upload your audio recording (supports MP3, WAV, M4A, OGG)
- Provide an optional title (defaults to timestamp)
- Click "Transcribe Audio" to process the recording
- Large files are automatically chunked for better processing

#### 2. AI Model Selection
- Choose your preferred AI provider (OpenAI, Anthropic, Grok)
- Select the specific model to use (e.g., GPT-4, Claude 3)

#### 3. Content Generation
- **Extract Wisdom**: Pull key insights and actionable takeaways
- **Create Outline**: Generate a structured outline for an article
- **Generate Social Media**: Create platform-specific social posts
- **Image Prompts**: Develop prompts for AI image generators
- **Write Article**: Draft a complete article based on the outline

#### 4. Export to Notion
- Save all generated content to your Notion database
- Content is organized in toggles with appropriate formatting
- Includes the original audio file reference

### Customizing Prompts

WhisperForge uses AI prompts to guide content generation. Customize these to match your personal voice:

1. In the sidebar, expand "Configure Custom Prompts"
2. Select the prompt type you want to customize
3. Edit the prompt text in the text area
4. Click "Save Prompt"

Your custom prompt will now be used for all future content generation of that type.

#### Default Prompt Types
- **Wisdom Extraction**: How insights are pulled from transcriptions
- **Outline Creation**: How article outlines are structured
- **Social Media**: How social posts are formatted
- **Image Prompts**: How image generation prompts are created
- **Article Writing**: How full articles are drafted

### Managing Knowledge Base

The knowledge base helps the AI understand your voice, style, and perspective:

1. Create .md or .txt files containing:
   - Writing style guides
   - Tone preferences
   - World view and perspectives
   - Subject matter expertise

2. Place these files in `prompts/YourName/knowledge_base/`

3. The AI will reference these when generating content to better match your voice

## Technical Architecture

WhisperForge combines several key technologies:

- **Streamlit**: Front-end interface
- **OpenAI Whisper**: Audio transcription
- **LLM Integration**: Multiple AI providers for content generation
- **Notion API**: Content export and organization
- **File System**: Persistent storage of custom prompts

The application follows this general flow:
1. Audio processing and chunking
2. Transcription via Whisper API
3. Content generation via selected LLM
4. Structured export to Notion

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for transcription and OpenAI models
- `NOTION_API_KEY`: Required for Notion integration
- `NOTION_DATABASE_ID`: ID of the Notion database for content export
- `ANTHROPIC_API_KEY`: Required for Claude models
- `GROK_API_KEY`: Required for Grok models

### Directory Structure
