"""
Notion Integration
==================

Create formatted Notion pages from WhisperForge content.
"""

import logging
import os
from datetime import datetime

from .content_generation import ContentGenerationError, _chat_completion

logger = logging.getLogger(__name__)

# Notion API limits content blocks to 2000 chars each
_NOTION_CHUNK_SIZE = 1800
_MAX_NOTION_BLOCKS = 50


def generate_ai_title(transcript: str) -> str:
    """Generate a concise AI-powered title from a transcript excerpt."""
    try:
        system_prompt = (
            "Generate a concise, descriptive title (max 60 characters) for an audio transcript. "
            "The title should be clear, specific, professional, and capture the main topic. "
            "No quotes or special characters. Respond with only the title."
        )
        user_content = f"Here is the transcript excerpt:\n\n{transcript[:500]}..."

        title = _chat_completion(system_prompt, user_content, max_tokens=30)
        return title.strip().replace('"', "").replace("'", "")[:60]
    except ContentGenerationError:
        return f"WhisperForge Content - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    except Exception:
        return f"WhisperForge Content - {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def create_notion_page(title: str, content_data: dict[str, str]) -> str | None:
    """Create a Notion page with WhisperForge content.

    Returns the page URL on success, or None on failure.
    """
    try:
        from notion_client import Client
    except ImportError:
        logger.warning("Install notion-client to enable Notion publishing: pip install notion-client")
        return None

    try:
        api_key = os.getenv("NOTION_API_KEY")
        database_id = os.getenv("NOTION_DATABASE_ID")

        if not api_key or not database_id:
            logger.warning("Notion not configured. Set NOTION_API_KEY and NOTION_DATABASE_ID to auto-publish.")
            return None

        client = Client(auth=api_key)
        children = _build_notion_children(title, content_data)

        response = client.pages.create(
            parent={"database_id": database_id},
            icon={"type": "emoji", "emoji": "\U0001f30c"},
            properties={"Name": {"title": [{"text": {"content": title[:100]}}]}},
            children=children[:_MAX_NOTION_BLOCKS],
        )

        if response and "id" in response:
            page_id = response["id"]
            return f"https://notion.so/{page_id.replace('-', '')}"

        return None

    except (ContentGenerationError, OSError) as e:
        logger.error(f"Notion publishing failed: {e!s}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Notion publishing: {e!s}")
        return None


def _build_notion_children(title: str, content_data: dict) -> list[dict]:
    """Build the list of Notion block children for a page."""
    children: list[dict] = []

    # Header
    children.append(
        {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {"type": "text", "text": {"content": "\U0001f30c "}, "annotations": {"color": "blue"}},
                    {"type": "text", "text": {"content": title}, "annotations": {"bold": True}},
                ]
            },
        }
    )

    # Creation info
    children.append(
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Generated with "}},
                    {
                        "type": "text",
                        "text": {"content": "WhisperForge Aurora"},
                        "annotations": {"bold": True, "color": "blue"},
                    },
                    {
                        "type": "text",
                        "text": {"content": f" \u2022 {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"},
                    },
                ]
            },
        }
    )

    children.append({"type": "divider", "divider": {}})

    # Wisdom callout
    if content_data.get("wisdom"):
        children.append(
            {
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Key Insights & Wisdom"}},
                        {"type": "text", "text": {"content": f"\n\n{content_data['wisdom'][:_NOTION_CHUNK_SIZE]}"}},
                    ],
                    "color": "purple_background",
                    "icon": {"type": "emoji", "emoji": "\U0001f4a1"},
                },
            }
        )

    # Content sections as toggles
    sections = [
        ("\U0001f4dd Transcript", content_data.get("transcript")),
        ("\U0001f4a1 Wisdom", content_data.get("wisdom")),
        ("\U0001f50d Research Links", content_data.get("research")),
        ("\U0001f4cb Outline", content_data.get("outline")),
        ("\U0001f4f0 Article", content_data.get("article")),
        ("\U0001f4f1 Social Content", content_data.get("social_content")),
    ]

    for section_title, section_content in sections:
        if not section_content:
            continue

        if section_title == "\U0001f50d Research Links" and isinstance(section_content, dict):
            children.append(_build_research_toggle(section_title, section_content))
        elif isinstance(section_content, str):
            chunks = [
                section_content[i : i + _NOTION_CHUNK_SIZE] for i in range(0, len(section_content), _NOTION_CHUNK_SIZE)
            ]
            children.append(
                {
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": section_title}}],
                        "children": [
                            {
                                "type": "paragraph",
                                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
                            }
                            for chunk in chunks[:5]
                        ],
                    },
                }
            )

    # Footer
    children.extend(
        [
            {"type": "divider", "divider": {}},
            {
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Content Generation Complete"},
                            "annotations": {"bold": True},
                        },
                        {"type": "text", "text": {"content": "\n\nAI Pipeline: completed successfully"}},
                        {
                            "type": "text",
                            "text": {"content": f"\nGenerated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"},
                        },
                        {"type": "text", "text": {"content": "\nPowered by WhisperForge Aurora"}},
                    ],
                    "color": "green_background",
                    "icon": {"type": "emoji", "emoji": "\u2705"},
                },
            },
        ]
    )

    return children


def _build_research_toggle(section_title: str, section_content: dict) -> dict:
    """Build a Notion toggle block for research data."""
    research_children: list[dict] = []
    entities = section_content.get("entities", [])

    if entities:
        for entity in entities[:5]:
            entity_name = entity.get("name", "Unknown Entity")
            why_matters = entity.get("why_matters", "No description available")
            links = entity.get("links", [])

            research_children.append(
                {
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {"type": "text", "text": {"content": entity_name}, "annotations": {"bold": True}},
                            {"type": "text", "text": {"content": f"\n{why_matters}"}},
                        ],
                        "color": "blue_background",
                        "icon": {"type": "emoji", "emoji": "\U0001f52c"},
                    },
                }
            )

            for link in links[:3]:
                link_title = link.get("title", "Link")
                link_desc = link.get("description", "")
                is_gem = link.get("is_gem", False)
                gem_icon = "\U0001f48e" if is_gem else "\U0001f517"
                color = "orange" if is_gem else "default"

                research_children.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"{gem_icon} "}, "annotations": {"color": color}},
                                {"type": "text", "text": {"content": link_title}, "annotations": {"bold": True}},
                                {
                                    "type": "text",
                                    "text": {"content": f" - {link_desc}"},
                                    "annotations": {"italic": True},
                                },
                            ]
                        },
                    }
                )
    else:
        research_children.append(
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "No research entities found."}}]},
            }
        )

    return {
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": section_title}}],
            "children": research_children,
        },
    }
