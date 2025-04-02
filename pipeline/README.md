# WhisperForge Content Generation Pipeline

This module provides a modular, configurable content generation pipeline for WhisperForge. The pipeline is designed to transform audio transcripts into various content formats through a series of processing steps.

## Key Features

- **Modular Architecture**: Each content generation step is implemented as a separate module.
- **Configurable Pipeline**: Create custom pipelines by enabling/disabling steps and setting parameters.
- **Multiple AI Providers**: Support for both Anthropic and OpenAI LLMs.
- **Editorial Enhancement**: Built-in editing capabilities to refine generated content.
- **Performance Metrics**: Detailed timing and performance tracking for each step.
- **Error Handling**: Graceful failure handling with configurable critical steps.

## Pipeline Steps

The content generation pipeline includes these key steps:

1. **Wisdom Extraction**: Identify key insights and actionable takeaways from transcripts.
2. **Outline Generation**: Create structured content outlines based on transcripts and wisdom.
3. **Blog Post Generation**: Generate complete blog posts based on outlines and transcripts.
4. **Social Media Generation**: Create platform-specific social media posts.
5. **Editorial Enhancement**: Apply editorial improvements to any content type.

## Usage Examples

### Basic Usage

```python
import asyncio
from pipeline import run_default_pipeline

# Run the default pipeline
async def process_transcript(transcript_text):
    results = await run_default_pipeline(transcript_text)
    return results

# Run the async function
results = asyncio.run(process_transcript("Your transcript text here..."))

# Access the results
blog_post = results["blog"]["blog_post"]
social_content = results["social"]["social_content"]
```

### Custom Pipeline

```python
import asyncio
from pipeline import ContentPipeline

# Create a custom pipeline configuration
custom_steps = [
    {
        "name": "wisdom",
        "enabled": True,
        "critical": True,
        "params": {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307"
        }
    },
    {
        "name": "outline",
        "enabled": True,
        "critical": True,
        "params": {
            "content_type": "blog",
            "outline_style": "listicle",  # Using a listicle style
            "ai_provider": "anthropic",
            "ai_model": "claude-3-haiku-20240307"
        }
    },
    {
        "name": "blog",
        "enabled": True,
        "critical": True,
        "params": {
            "blog_style": "conversational",  # Using a conversational style
            "word_count": 1200,  # Longer blog post
            "ai_provider": "anthropic",
            "ai_model": "claude-3-opus-20240229"
        }
    }
]

# Create and run the custom pipeline
async def run_custom_pipeline(transcript_text):
    pipeline = ContentPipeline.create_custom_pipeline(custom_steps)
    context = {"transcript": transcript_text}
    results = await pipeline.run(context)
    return results

# Run the async function
results = asyncio.run(run_custom_pipeline("Your transcript text here..."))
```

### Predefined Pipelines

The module includes several predefined pipeline configurations:

- `run_default_pipeline()`: Full content generation with all steps
- `run_minimal_pipeline()`: Basic pipeline with wisdom, outline, and blog only
- `run_social_pipeline()`: Focused on social media content generation

## Content Styles

Each content generation step supports different styles:

### Blog Styles
- `standard`: Clear, professional blog posts
- `conversational`: Warm, friendly, personal tone
- `educational`: Instructional, helpful content
- `storytelling`: Narrative-driven, engaging content
- `analytical`: Data-driven, thoughtful analysis
- `persuasive`: Convincing, action-oriented content

### Outline Styles
- `standard`: Well-structured general outlines
- `listicle`: Numbered list format
- `howto`: Step-by-step instructional format

### Editor Styles
- `standard`: General editorial improvements
- `brevity`: Focus on conciseness
- `engagement`: Enhance reader engagement
- `strategic`: Business-focused clarity

## Integration with Streamlit UI

The pipeline is integrated with the WhisperForge Streamlit interface, providing:

- Selection of pipeline type
- Real-time progress feedback
- Comprehensive results display with tabs
- Download options for generated content
- Performance metrics visualization

## Adding New Step Types

To add a new step type to the pipeline:

1. Create a new step module in the `pipeline/steps/` directory
2. Implement your step function with async support 
3. Register your step in the `ContentPipeline.available_steps` dictionary
4. Update any UI components to display the results

## Environment Configuration

The pipeline requires these environment variables or config settings:

- `OPENAI_API_KEY`: For OpenAI models
- `ANTHROPIC_API_KEY`: For Anthropic Claude models

## Performance Considerations

- Processing time varies based on transcript length and selected models
- Consider using smaller models for development/testing
- The most compute-intensive steps are blog generation and wisdom extraction 