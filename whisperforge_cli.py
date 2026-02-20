#!/usr/bin/env python3
"""
WhisperForge CLI - Command Line Interface
Run the WhisperForge pipeline from the command line
"""

import os
import sys
from pathlib import Path

import click

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core functionality
try:
    from dotenv import load_dotenv

    from core.content_generation import transcribe_audio
    from core.logging_config import logger
    from core.pipeline_engine import NullListener, PipelineConfig, run_pipeline

    # Load environment variables
    load_dotenv()

except ImportError as e:
    print(f"Error importing WhisperForge modules: {e}")
    print("Make sure you're running this from the WhisperForge project directory.")
    sys.exit(1)


class CLIPipelineListener(NullListener):
    """Pipeline listener that prints progress to the terminal via click."""

    def on_step_start(self, step_index, step_name, message):
        click.echo(f"  [{step_index + 1}/6] {step_name}: {message}")

    def on_step_complete(self, step_index, step_name, result):
        click.echo(f"  [{step_index + 1}/6] {step_name}: done")

    def on_error(self, step_index, error):
        click.echo(f"  Error at step {step_index}: {error}", err=True)


class CLIFile:
    """Simple file wrapper for CLI usage"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.name = self.file_path.name
        self.type = self._get_mime_type()

    def _get_mime_type(self) -> str:
        """Get MIME type based on file extension"""
        ext = self.file_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
        }
        return mime_types.get(ext, "audio/mpeg")

    def read(self) -> bytes:
        """Read file content"""
        with open(self.file_path, "rb") as f:
            return f.read()

    def getvalue(self) -> bytes:
        """Get file content (Streamlit compatibility)"""
        return self.read()


def validate_audio_file(file_path: str) -> bool:
    """Validate that the input file is a supported audio format"""
    if not os.path.exists(file_path):
        click.echo(f"Error: File '{file_path}' does not exist.", err=True)
        return False

    supported_extensions = [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm"]
    file_ext = Path(file_path).suffix.lower()

    if file_ext not in supported_extensions:
        click.echo(
            f"Error: Unsupported file format '{file_ext}'. Supported formats: {', '.join(supported_extensions)}",
            err=True,
        )
        return False

    return True


def validate_api_keys() -> bool:
    """Validate that required API keys are available"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key and not anthropic_key:
        click.echo(
            "Error: No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.",
            err=True,
        )
        return False

    return True


@click.group()
@click.option(
    "--env",
    type=click.Choice(["development", "production"]),
    help="Runtime environment",
)
@click.version_option(version="2.0.0", prog_name="WhisperForge CLI")
def cli(env: str | None):
    """WhisperForge CLI - Transform audio into structured content"""
    if env:
        os.environ["ENVIRONMENT"] = env
        if env == "development":
            os.environ.setdefault("DEBUG", "true")
            os.environ.setdefault("LOG_LEVEL", "DEBUG")
        else:
            os.environ.setdefault("DEBUG", "false")
            os.environ.setdefault("LOG_LEVEL", "INFO")


@cli.group()
def pipeline():
    """Pipeline operations"""
    pass


@pipeline.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input audio file path",
)
@click.option(
    "--model",
    "-m",
    default="gpt-4o",
    help="AI model to use (gpt-4o, gpt-4o-mini, claude-3-5-sonnet-20241022)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory (default: current directory)",
)
@click.option(
    "--format",
    "output_format",
    default="all",
    type=click.Choice(["transcript", "wisdom", "outline", "article", "all"]),
    help="Output format(s) to generate",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(
    input_file: str,
    model: str,
    output: str | None,
    output_format: str,
    verbose: bool,
):
    """Run the complete WhisperForge pipeline on an audio file"""

    if verbose:
        click.echo("🚀 Starting WhisperForge pipeline...")
        click.echo(f"Input file: {input_file}")
        click.echo(f"Model: {model}")
        click.echo(f"Output format: {output_format}")

    # Validate inputs
    if not validate_audio_file(input_file):
        sys.exit(1)

    if not validate_api_keys():
        sys.exit(1)

    # Set up output directory
    if output:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path.cwd()

    # Create CLI file wrapper
    audio_file = CLIFile(input_file)
    stem = Path(input_file).stem

    try:
        # --- Transcription-only shortcut ---
        if output_format == "transcript":
            click.echo("Transcribing audio...")
            transcript = transcribe_audio(str(audio_file.file_path))
            if not transcript:
                click.echo("Transcription failed: empty result", err=True)
                sys.exit(1)

            transcript_file = output_dir / f"{stem}_transcript.txt"
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript)
            click.echo(f"Transcript saved: {transcript_file}")
            if verbose:
                click.echo(f"Preview: {transcript[:200]}...")
            return

        # --- Full pipeline via engine ---
        config = PipelineConfig(publish_to_notion=False)
        listener = CLIPipelineListener() if verbose else NullListener()

        results = run_pipeline(
            audio_file=audio_file,
            config=config,
            listener=listener,
        )

        if results is None:
            click.echo("Pipeline failed -- see errors above.", err=True)
            sys.exit(1)

        # --- Write results to files ---
        output_map = {
            "transcript": ("_transcript.txt", "transcript"),
            "wisdom": ("_wisdom.md", "wisdom"),
            "outline": ("_outline.md", "outline"),
            "article": ("_article.md", "article"),
            "social_content": ("_social.md", "social_content"),
        }

        saved_files: dict[str, Path] = {}
        for key, (suffix, result_key) in output_map.items():
            content = results.get(result_key)
            if not content:
                continue
            if output_format not in ("all", key):
                continue
            out_path = output_dir / f"{stem}{suffix}"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            saved_files[key] = out_path

        # Summary
        click.echo("\nPipeline completed successfully!")
        click.echo(f"Output directory: {output_dir}")
        for content_type, file_path in saved_files.items():
            click.echo(f"  {content_type}: {file_path}")

        if verbose and results.get("transcript"):
            click.echo(f"\nTranscript preview:\n{results['transcript'][:300]}...")

    except Exception as e:
        logger.error(f"CLI pipeline error: {e}")
        click.echo(f"Pipeline failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input audio file path",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: input_name_transcript.txt)",
)
def transcribe(input_file: str, output: str | None):
    """Transcribe audio file to text only"""

    if not validate_audio_file(input_file):
        sys.exit(1)

    if not validate_api_keys():
        sys.exit(1)

    # Set up output file
    output_file = Path(output) if output else Path(f"{Path(input_file).stem}_transcript.txt")

    try:
        click.echo("Transcribing audio...")
        transcript = transcribe_audio(input_file)

        if not transcript:
            click.echo("Transcription failed: empty result", err=True)
            sys.exit(1)

        # Save transcript
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)

        click.echo(f"Transcript saved: {output_file}")
        click.echo(f"Preview: {transcript[:200]}...")

    except Exception as e:
        logger.error(f"CLI transcription error: {e}")
        click.echo(f"Transcription failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Check system status and configuration"""
    click.echo("🔍 WhisperForge CLI Status")
    click.echo("=" * 30)

    env = os.getenv("ENVIRONMENT", "development")
    click.echo(f"Environment: {env}")
    click.echo(f"Debug: {os.getenv('DEBUG', 'false')}")
    click.echo(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")

    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    click.echo(f"OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    click.echo(f"Anthropic API Key: {'✅ Set' if anthropic_key else '❌ Not set'}")

    # Check dependencies
    try:
        import openai  # noqa: F401

        click.echo("OpenAI library: ✅ Available")
    except ImportError:
        click.echo("OpenAI library: ❌ Not available")

    try:
        import anthropic  # noqa: F401

        click.echo("Anthropic library: ✅ Available")
    except ImportError:
        click.echo("Anthropic library: ❌ Not available")

    # Check audio processing
    try:
        from pydub import AudioSegment  # noqa: F401

        click.echo("Audio processing (pydub): ✅ Available")
    except ImportError:
        click.echo("Audio processing (pydub): ❌ Not available")

    click.echo("\n💡 To get started:")
    click.echo("1. Set your API key: export OPENAI_API_KEY='your-key-here'")
    click.echo("2. Run: python whisperforge_cli.py pipeline run --input audio.mp3")


if __name__ == "__main__":
    cli()
