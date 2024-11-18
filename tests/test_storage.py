import pytest
from datetime import datetime
from services.storage.service import StorageRequest, format_notion_blocks, generate_title, create_notion_page

def test_format_blocks():
    markdown_text = """# Main Heading
This is some regular text.

> Important note here
This is more regular text.

# Another Section
Some content here."""
    
    blocks = format_notion_blocks(markdown_text)
    assert blocks["children"][0]["type"] == "paragraph"
    assert "content" in blocks["children"][0]["paragraph"]["rich_text"][0]["text"]

def test_title_generation():
    filename = "test_audio.mp3"
    text = "This is a test transcription.\nWith multiple lines."
    title = generate_title(filename)
    assert "Transcription:" in title
    assert "test_audio" in title

@pytest.mark.asyncio
async def test_full_storage():
    request = StorageRequest(
        transcription="Raw transcription text",
        processed_text="""# Meeting Summary
This is a test meeting transcription.

> Key point: Important discussion about project timeline

# Action Items
1. Review documentation
2. Schedule follow-up""",
        filename="test_meeting.mp3",
        duration=120.5,
        timestamp=datetime.now()
    )
    
    assert request.transcription
    assert request.processed_text
    assert request.filename 