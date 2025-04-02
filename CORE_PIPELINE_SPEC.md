# WhisperForge Core Pipeline Enhancement Specification

This document details the technical requirements for Phase 1 of the WhisperForge implementation plan, focusing on enhancing the core content generation pipeline to meet the requirements outlined in the master specification.

## 1. Pipeline Architecture

### 1.1 Pipeline Orchestrator

The orchestrator will be responsible for managing the flow of data through each pipeline step, tracking state, and handling errors.

```python
class PipelineStep:
    def __init__(self, name, function, required_inputs=None, produces_outputs=None):
        self.name = name
        self.function = function
        self.required_inputs = required_inputs or []
        self.produces_outputs = produces_outputs or []
        self.status = "pending"  # pending, running, completed, failed
        self.start_time = None
        self.end_time = None
        self.error = None
        
    async def execute(self, context):
        """Execute this step with the given context data"""
        self.status = "running"
        self.start_time = time.time()
        try:
            # Check that all required inputs are available
            for input_key in self.required_inputs:
                if input_key not in context:
                    raise ValueError(f"Required input '{input_key}' not available for step '{self.name}'")
            
            # Execute the function with relevant context data
            result = await self.function(context)
            
            # Update context with produced outputs
            for output_key in self.produces_outputs:
                if output_key not in result:
                    logger.warning(f"Expected output '{output_key}' not produced by step '{self.name}'")
                else:
                    context[output_key] = result[output_key]
                    
            self.status = "completed"
            return result
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            logger.error(f"Error in pipeline step '{self.name}': {str(e)}")
            raise
        finally:
            self.end_time = time.time()


class ContentPipeline:
    def __init__(self, steps=None):
        self.steps = steps or self.default_steps()
        self.results = {}
        self.context = {}
        self.status = "pending"
        
    def default_steps(self):
        """Define the default pipeline steps"""
        return [
            PipelineStep(
                name="transcription",
                function=self.transcribe_audio,
                required_inputs=["audio_file"],
                produces_outputs=["transcript"]
            ),
            PipelineStep(
                name="wisdom_extraction",
                function=self.extract_wisdom,
                required_inputs=["transcript"],
                produces_outputs=["wisdom_notes"]
            ),
            PipelineStep(
                name="outline_creation",
                function=self.create_outline,
                required_inputs=["transcript", "wisdom_notes"],
                produces_outputs=["outline"]
            ),
            PipelineStep(
                name="outline_edit",
                function=self.apply_editor,
                required_inputs=["outline"],
                produces_outputs=["edited_outline", "outline_feedback"]
            ),
            # Additional steps omitted for brevity
        ]
    
    async def run(self, input_data, skip_steps=None):
        """Execute the pipeline with the given input data"""
        self.context = input_data.copy()
        self.status = "running"
        results = {}
        
        skip_steps = skip_steps or []
        
        try:
            for step in self.steps:
                if step.name in skip_steps:
                    logger.info(f"Skipping pipeline step: {step.name}")
                    continue
                    
                logger.info(f"Executing pipeline step: {step.name}")
                step_result = await step.execute(self.context)
                results[step.name] = {
                    "status": step.status,
                    "duration": step.end_time - step.start_time if step.end_time else None,
                    "error": step.error,
                    **step_result
                }
                
                # Break pipeline if a step fails
                if step.status == "failed":
                    self.status = "failed"
                    break
            
            if self.status != "failed":
                self.status = "completed"
            
            self.results = results
            return results
        except Exception as e:
            self.status = "failed"
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise
```

### 1.2 Step Configuration System

Each pipeline step will be configurable with the following properties:

- **Enabled/Disabled**: Allow users to toggle steps
- **Parameters**: Customizable parameters (e.g., model selection, prompt customization)
- **Knowledge Base Integration**: Which knowledge base documents to include
- **Retry Behavior**: How to handle failures

```python
class StepConfig:
    def __init__(self, enabled=True, params=None, knowledge_docs=None, retry_attempts=1):
        self.enabled = enabled
        self.params = params or {}
        self.knowledge_docs = knowledge_docs or []
        self.retry_attempts = retry_attempts
```

## 2. Pipeline Steps Implementation

### 2.1 Transcription Enhancement

The transcription step will be enhanced to support:

- Chunking large files efficiently
- Multiple transcription providers (OpenAI, local models)
- Speaker identification (if available)
- Timestamps and confidence scores

```python
async def transcribe_audio(self, context):
    """Transcribe audio file to text"""
    audio_file = context["audio_file"]
    provider = context.get("transcription_provider", "openai")
    
    if provider == "openai":
        client = get_openai_client()
        
        # For large files, implement chunking
        if get_file_size(audio_file) > MAX_OPENAI_FILE_SIZE:
            logger.info(f"Large file detected, using chunked transcription")
            chunks = split_audio_file(audio_file)
            transcripts = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=chunk,
                    response_format="verbose_json"
                )
                transcripts.append(response)
                
            # Combine transcripts with timestamps
            transcript = combine_transcripts(transcripts)
        else:
            # Standard transcription for smaller files
            with open(audio_file, "rb") as f:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json"
                )
            transcript = response.text
    
    return {"transcript": transcript}
```

### 2.2 Wisdom Extraction

This step extracts key insights and wisdom from the transcript:

```python
async def extract_wisdom(self, context):
    """Extract key insights and wisdom points from transcript"""
    transcript = context["transcript"]
    prompt_template = """
    Extract the key insights, wisdom, and actionable takeaways from this transcript.
    Focus on the most valuable, practical, and meaningful points.
    Format as concise bullet points that capture the essence of each insight.
    
    Transcript:
    {transcript}
    
    Key Insights and Wisdom:
    """
    
    # Include knowledge base documents if available
    knowledge_docs = self.get_knowledge_docs(context, "wisdom_extraction")
    if knowledge_docs:
        prompt_template += "\n\nReference materials for voice and style matching:\n{knowledge_docs}"
    
    prompt = prompt_template.format(
        transcript=transcript,
        knowledge_docs="\n".join(knowledge_docs)
    )
    
    # Use the specified AI provider and model
    provider = context.get("ai_provider", "anthropic")
    
    if provider == "anthropic":
        client = get_anthropic_client()
        response = await client.messages.create(
            model=context.get("ai_model", "claude-3-haiku-20240307"),
            max_tokens=2000,
            system="You extract practical wisdom and key insights from transcripts. Focus on actionable takeaways, surprising insights, and memorable quotes.",
            messages=[{"role": "user", "content": prompt}]
        )
        wisdom_notes = response.content[0].text
    else:
        # OpenAI implementation
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=context.get("ai_model", "gpt-4"),
            messages=[
                {"role": "system", "content": "You extract practical wisdom and key insights from transcripts. Focus on actionable takeaways, surprising insights, and memorable quotes."},
                {"role": "user", "content": prompt}
            ]
        )
        wisdom_notes = response.choices[0].message.content
    
    return {"wisdom_notes": wisdom_notes}
```

### 2.3 Outline Creation

Creates a structured outline using the transcript and wisdom notes:

```python
async def create_outline(self, context):
    """Create a structured outline from transcript and wisdom notes"""
    transcript = context["transcript"]
    wisdom_notes = context["wisdom_notes"]
    
    prompt_template = """
    Create a structured outline for a blog post based on this transcript and extracted wisdom notes.
    
    Include:
    1. A compelling working title
    2. A strong hook/intro paragraph
    3. 3-5 main section headings with bullet points for each
    4. A conclusion with call-to-action
    
    Make the outline clear, strategic, and in a voice that matches my style.
    
    Transcript:
    {transcript}
    
    Wisdom Notes:
    {wisdom_notes}
    
    Outline:
    """
    
    # Include knowledge base documents
    knowledge_docs = self.get_knowledge_docs(context, "outline_creation")
    if knowledge_docs:
        prompt_template += "\n\nReference materials for voice and style matching:\n{knowledge_docs}"
    
    prompt = prompt_template.format(
        transcript=transcript,
        wisdom_notes=wisdom_notes,
        knowledge_docs="\n".join(knowledge_docs)
    )
    
    # Implementation for different providers similar to wisdom extraction
    # ...
    
    return {"outline": outline}
```

### 2.4 Editor Pass Implementation

The editor functionality applies a critical review and enhancement to content:

```python
async def apply_editor(self, context, content_key, output_key_prefix):
    """Apply editorial pass to the specified content"""
    content = context[content_key]
    
    editor_prompt = """
    You are a strategic editor who knows my tone and goals.
    Review this draft and return:
    
    1. Clear revision notes (structure, clarity, voice, impact)
    2. A cleaner, improved version of the content
    
    Do not change my voice—refine and focus the ideas. Be concise and specific.
    
    Content to review:
    {content}
    """
    
    # Add voice samples from knowledge base
    knowledge_docs = self.get_knowledge_docs(context, "editor")
    if knowledge_docs:
        editor_prompt += "\n\nReference materials for voice and style matching:\n{knowledge_docs}"
    
    prompt = editor_prompt.format(
        content=content,
        knowledge_docs="\n".join(knowledge_docs)
    )
    
    # API implementation omitted for brevity
    # ...
    
    # Parse response to separate feedback from revised content
    feedback, revised_content = self.parse_editor_response(response_text)
    
    return {
        f"{output_key_prefix}_feedback": feedback,
        f"edited_{content_key}": revised_content
    }
```

## 3. Editor Prompt System

### 3.1 Editor Templates

```python
EDITOR_TEMPLATES = {
    "standard": {
        "name": "Standard Editor",
        "system_prompt": "You are a strategic editor who knows my tone and goals. Your task is to review content and provide both feedback and improvements while maintaining my authentic voice.",
        "instruction_template": """
        Review this {content_type} and return:
        
        1. Clear revision notes (structure, clarity, voice, impact)
        2. A cleaner, improved version of the content
        
        Do not change my voice—refine and focus the ideas. Be concise and specific.
        
        Content to review:
        {content}
        """
    },
    "brevity": {
        "name": "Brevity Editor",
        "system_prompt": "You are an editor focused on brevity and impact. Your task is to tighten content while preserving meaning and voice.",
        "instruction_template": """
        Review this {content_type} and return:
        
        1. Notes on unnecessary text that can be removed
        2. A tighter, more concise version that maintains impact
        
        Cut at least 25% of the length while preserving all key points.
        
        Content to review:
        {content}
        """
    },
    "engagement": {
        "name": "Engagement Editor",
        "system_prompt": "You are an editor specialized in making content more engaging and captivating. Your task is to enhance the hook, flow, and reader connection.",
        "instruction_template": """
        Review this {content_type} and return:
        
        1. Notes on engagement opportunities
        2. A revised version with stronger hooks, better flow, and more compelling language
        
        Make this content impossible to stop reading.
        
        Content to review:
        {content}
        """
    }
}
```

### 3.2 Feedback Parser

```python
def parse_editor_response(self, response_text):
    """Parse the editor response to separate feedback from revised content"""
    # Simple approach: Look for common feedback separator patterns
    separators = [
        "REVISED CONTENT:",
        "IMPROVED VERSION:",
        "EDITED VERSION:",
        "HERE'S THE REVISED VERSION:",
        "IMPROVED CONTENT:"
    ]
    
    # Find the separator used (if any)
    separator_index = -1
    found_separator = None
    
    for separator in separators:
        if separator in response_text:
            index = response_text.find(separator)
            if separator_index == -1 or index < separator_index:
                separator_index = index
                found_separator = separator
    
    if found_separator and separator_index >= 0:
        feedback = response_text[:separator_index].strip()
        revised_content = response_text[separator_index + len(found_separator):].strip()
        return feedback, revised_content
    
    # If no separator is found, use AI to extract the parts
    # (Implementation omitted for brevity)
```

## 4. Knowledge Base System

### 4.1 Knowledge Document Structure

```python
class KnowledgeDocument:
    def __init__(self, id, name, content, doc_type, tags=None, metadata=None):
        self.id = id
        self.name = name
        self.content = content
        self.doc_type = doc_type  # voice_sample, reference, instruction, etc.
        self.tags = tags or []
        self.metadata = metadata or {}
        self.usage_count = 0
        self.last_used = None
```

### 4.2 Knowledge Base Manager

```python
class KnowledgeBaseManager:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        
    async def get_documents(self, filters=None, limit=10):
        """Get knowledge documents matching the filters"""
        # Implementation omitted
        
    async def get_document_by_id(self, doc_id):
        """Get a specific document by ID"""
        # Implementation omitted
        
    async def add_document(self, document):
        """Add a new document to the knowledge base"""
        # Implementation omitted
        
    async def update_document(self, doc_id, updates):
        """Update an existing document"""
        # Implementation omitted
        
    async def delete_document(self, doc_id):
        """Delete a document from the knowledge base"""
        # Implementation omitted
        
    async def track_document_usage(self, doc_id, pipeline_id):
        """Track that a document was used in a pipeline run"""
        # Implementation omitted
```

## 5. Notion Integration

### 5.1 Notion Database Schema

```python
NOTION_SCHEMA = {
    "Title": {"title": {}},
    "Tags": {"multi_select": {}},
    "Summary": {"rich_text": {}},
    "Status": {"select": {
        "options": [
            {"name": "Draft", "color": "yellow"},
            {"name": "In Progress", "color": "blue"},
            {"name": "Published", "color": "green"}
        ]
    }},
    "Content Type": {"select": {
        "options": [
            {"name": "Blog Post", "color": "purple"},
            {"name": "Social Media", "color": "pink"},
            {"name": "Image Prompts", "color": "orange"},
            {"name": "Other", "color": "gray"}
        ]
    }},
    "Created At": {"date": {}},
    "Transcript": {"rich_text": {}},
    "Wisdom Notes": {"rich_text": {}},
    "Outline": {"rich_text": {}},
    "Blog Post": {"rich_text": {}},
    "Social Media Content": {"rich_text": {}},
    "Image Prompts": {"rich_text": {}},
    "Pipeline ID": {"rich_text": {}}
}
```

### 5.2 Notion Sync Function

```python
async def sync_to_notion(self, context):
    """Sync content to Notion database"""
    # Get necessary data from context
    title = context.get("edited_outline", {}).get("title", "Untitled Content")
    tags = self.extract_tags(context)
    summary = self.generate_summary(context)
    
    # Prepare the page properties
    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Tags": {"multi_select": [{"name": tag} for tag in tags]},
        "Summary": {"rich_text": [{"text": {"content": summary}}]},
        "Status": {"select": {"name": "Draft"}},
        "Content Type": {"select": {"name": "Blog Post"}},
        "Created At": {"date": {"start": datetime.now().isoformat()}},
    }
    
    # Add content fields if available
    content_fields = {
        "Transcript": "transcript",
        "Wisdom Notes": "wisdom_notes",
        "Outline": "edited_outline",
        "Blog Post": "edited_blog_post",
        "Social Media Content": "edited_social_content",
        "Image Prompts": "image_prompts"
    }
    
    for notion_field, context_key in content_fields.items():
        if context_key in context and context[context_key]:
            # Truncate to Notion's rich_text limit if needed
            text = str(context[context_key])
            if len(text) > 2000:
                text = text[:1997] + "..."
            
            properties[notion_field] = {
                "rich_text": [{"text": {"content": text}}]
            }
    
    # Add pipeline ID for tracking
    properties["Pipeline ID"] = {
        "rich_text": [{"text": {"content": str(context.get("pipeline_id", "unknown"))}}]
    }
    
    # Create the page in Notion
    notion = get_notion_client()
    database_id = get_notion_database_id()
    
    try:
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        return {"notion_page_id": page.id, "notion_url": f"https://notion.so/{page.id.replace('-', '')}"}
    except Exception as e:
        logger.error(f"Notion sync failed: {str(e)}")
        return {"notion_error": str(e)}
```

## 6. Implementation Timeline

The Core Pipeline Enhancement phase is estimated to take 2-4 weeks with the following timeline:

### Week 1: Architecture and Foundation
- Define and implement the pipeline orchestrator
- Create the pipeline step interface
- Implement the knowledge base system

### Week 2: Core Pipeline Steps
- Enhance the transcription step
- Implement wisdom extraction
- Build structured outline generation
- Create the editor pass functionality

### Week 3: Advanced Pipeline Steps
- Implement blog post generation
- Build social media content generation
- Create image prompt generation
- Develop Notion integration

### Week 4: Testing and Refinement
- End-to-end pipeline testing
- Performance optimization
- Error handling improvements
- Documentation

## 7. Dependencies and Requirements

### External Libraries
- OpenAI Python SDK (v1.0.0+)
- Anthropic Python SDK (v0.5.0+)
- Notion Python SDK (latest)
- AsyncIO for asynchronous processing
- Pydantic for data validation

### Environment Configuration
- API keys for OpenAI, Anthropic, and Notion
- Database connection for storing pipeline state
- File storage for transcripts and generated content

## 8. Testing Strategy

### Unit Tests
- Individual pipeline step tests with mock inputs/outputs
- Editor prompt parsing tests
- Knowledge base access tests

### Integration Tests
- End-to-end pipeline tests with sample audio
- Notion integration tests
- Error handling and recovery tests

### Smoke Tests
- Basic functionality verification script 