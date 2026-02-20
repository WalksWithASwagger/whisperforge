"""
Content Display Components
===========================

Aurora-styled content cards, tab interfaces, and result views for generated content.
"""

import html as html_mod
import uuid
from datetime import datetime

import streamlit as st

from .export import create_text_export, export_to_markdown, export_to_word


def create_enhanced_aurora_content_card(title, content, content_type="text", icon="\U0001f4c4"):
    """Create an Aurora content card with copy/download/expand functionality."""
    card_id = f"card_{uuid.uuid4().hex[:8]}"
    copy_btn_id = f"copy_{uuid.uuid4().hex[:8]}"
    expand_btn_id = f"expand_{uuid.uuid4().hex[:8]}"
    full_content_id = f"full_{uuid.uuid4().hex[:8]}"

    word_count = len(content.split()) if content else 0
    char_count = len(content) if content else 0

    preview_length = 300
    needs_expansion = len(content) > preview_length
    preview_content = content[:preview_length] + "..." if needs_expansion else content

    type_class = content_type.lower()

    # Escape user-controlled content for safe HTML embedding
    safe_title = html_mod.escape(title)
    safe_icon = html_mod.escape(icon)
    escaped_content = html_mod.escape(content)
    escaped_preview = html_mod.escape(preview_content)
    js_safe_content = content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    card_html = f"""
    <div class="aurora-content-card {type_class}" id="{card_id}">
        <div class="aurora-content-card-header">
            <h3 class="aurora-content-card-title">
                <span class="aurora-content-card-icon">{safe_icon}</span>
                {safe_title}
            </h3>
            <div class="aurora-content-card-actions">
                <button class="aurora-content-action-btn copy-btn" id="{copy_btn_id}"
                        onclick="copyToClipboard('{card_id}', '{copy_btn_id}')">
                    <span>\U0001f4cb</span>
                    <span class="copy-text">Copy</span>
                </button>
                <button class="aurora-content-action-btn"
                        onclick="downloadContent('{safe_title}', `{js_safe_content}`)">
                    <span>\U0001f4be</span>
                    <span>Save</span>
                </button>
            </div>
        </div>

        <div class="aurora-content-card-body">
            <div class="aurora-content-preview" id="preview_{card_id}">
                {escaped_preview}
            </div>

            {
        f'''
            <div class="aurora-content-full" id="{full_content_id}">
                {html_mod.escape(content[preview_length:])}
            </div>
            '''
        if needs_expansion
        else ""
    }

            <div class="aurora-content-stats">
                <div class="aurora-content-word-count">
                    <span>\U0001f4ca</span>
                    <span>{word_count} words \u2022 {char_count} characters</span>
                </div>

                {
        f'''
                <button class="aurora-content-expand-btn" id="{expand_btn_id}"
                        onclick="toggleExpand('{full_content_id}', '{expand_btn_id}')">
                    <span>Show more</span>
                    <span class="aurora-content-expand-icon">&#x25BC;</span>
                </button>
                '''
        if needs_expansion
        else ""
    }
            </div>
        </div>

        <!-- Hidden content for copying -->
        <textarea id="content_{card_id}"
                  style="position: absolute; left: -9999px; opacity: 0;">{escaped_content}</textarea>
    </div>

    <script>
    function copyToClipboard(cardId, btnId) {{
        const content = document.getElementById('content_' + cardId).value;
        const button = document.getElementById(btnId);
        const copyText = button.querySelector('.copy-text');

        navigator.clipboard.writeText(content).then(function() {{
            button.classList.add('copied');
            copyText.textContent = 'Copied!';
            setTimeout(() => {{
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Failed to copy: ', err);
            const textarea = document.getElementById('content_' + cardId);
            textarea.select();
            document.execCommand('copy');
            button.classList.add('copied');
            copyText.textContent = 'Copied!';
            setTimeout(() => {{
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }}, 2000);
        }});
    }}

    function toggleExpand(fullContentId, btnId) {{
        const fullContent = document.getElementById(fullContentId);
        const button = document.getElementById(btnId);
        const buttonText = button.querySelector('span:first-child');

        if (fullContent.classList.contains('expanded')) {{
            fullContent.classList.remove('expanded');
            button.classList.remove('expanded');
            buttonText.textContent = 'Show more';
        }} else {{
            fullContent.classList.add('expanded');
            button.classList.add('expanded');
            buttonText.textContent = 'Show less';
        }}
    }}

    function downloadContent(title, content) {{
        const blob = new Blob([content], {{ type: 'text/plain' }});
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }}
    </script>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def create_aurora_tabs(tab_data, default_tab=0):
    """Create Aurora-styled tab interface for content selection."""
    tab_group_id = f"tabs_{uuid.uuid4().hex[:8]}"

    if f"{tab_group_id}_active" not in st.session_state:
        st.session_state[f"{tab_group_id}_active"] = default_tab

    tab_stats = []
    for tab in tab_data:
        content = tab.get("content", "")
        word_count = len(str(content).split()) if content else 0
        tab_stats.append(word_count)

    st.markdown(
        """
    <div class="aurora-tabs-container">
        <div class="aurora-tabs-actions">
            <h3 class="aurora-tabs-title">
                <span>\U0001f4c4</span>
                Generated Content
            </h3>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    tab_options = []
    for i, tab in enumerate(tab_data):
        word_count = tab_stats[i]
        tab_options.append(f"{tab['icon']} {tab['title']} ({word_count} words)")

    st.markdown(
        """
    <style>
    .aurora-tab-selector .stSelectbox > div > div {
        background: var(--aurora-bg-glass) !important;
        border: 2px solid var(--aurora-border) !important;
        border-radius: var(--aurora-radius) !important;
        color: var(--aurora-text) !important;
    }
    .aurora-tab-selector .stSelectbox > div > div:hover {
        border-color: var(--aurora-border-hover) !important;
        box-shadow: var(--aurora-glow-subtle) !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="aurora-tab-selector">', unsafe_allow_html=True)
        selected_tab_label = st.selectbox(
            "Select Content Type:",
            tab_options,
            index=st.session_state[f"{tab_group_id}_active"],
            key=f"tab_select_{tab_group_id}",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    selected_index = 0
    for i, option in enumerate(tab_options):
        if option == selected_tab_label:
            selected_index = i
            break

    st.session_state[f"{tab_group_id}_active"] = selected_index

    if 0 <= selected_index < len(tab_data):
        active_tab = tab_data[selected_index]

        col1, col2, col3, _col4 = st.columns([1, 1, 1, 2])

        with col1:
            if st.button("\U0001f4cb Copy", key=f"copy_{tab_group_id}_{selected_index}", use_container_width=True):
                st.code(active_tab.get("content", ""), language="text")
                st.success("Content displayed above - copy with Ctrl+A, Ctrl+C")

        with col2:
            content = active_tab.get("content", "")
            if content:
                st.download_button(
                    label="\U0001f4be Download",
                    data=content,
                    file_name=f"{active_tab['title'].lower().replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"download_{tab_group_id}_{selected_index}",
                    use_container_width=True,
                )

        with col3:
            if st.button("\U0001f4ca Stats", key=f"stats_{tab_group_id}_{selected_index}", use_container_width=True):
                word_count = len(str(content).split())
                char_count = len(str(content))
                st.info(f"\U0001f4ca **{active_tab['title']}**: {word_count} words, {char_count} characters")

        st.markdown('<div class="aurora-tab-content">', unsafe_allow_html=True)
        create_enhanced_aurora_content_card(
            title=active_tab["title"],
            content=active_tab.get("content", ""),
            content_type=active_tab.get("type", "text"),
            icon=active_tab["icon"],
        )
        st.markdown("</div>", unsafe_allow_html=True)

    return selected_index


def show_results(results):
    """Display generated content with Aurora styling and export options."""
    if not results:
        return

    st.markdown(
        """
    <div class="aurora-results-header">
        <h1 class="aurora-results-title">Content Generated Successfully!</h1>
        <p class="aurora-results-subtitle">Your audio has been transformed with AI magic</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    notion_url = results.get("notion_url", "")
    if notion_url and notion_url.startswith("https://"):
        safe_url = html_mod.escape(notion_url)
        st.markdown(
            f"""
        <div class="aurora-notion-link">
            <a href="{safe_url}" target="_blank" class="aurora-notion-button">
                View in Notion Workspace
            </a>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

    # Content overview stats
    total_words = sum(
        len(str(results.get(key, "")).split())
        for key in ["transcript", "wisdom", "outline", "article", "social_content"]
    )
    content_types = len([k for k in ["transcript", "wisdom", "outline", "article", "social_content"] if results.get(k)])

    st.markdown(
        f"""
    <div class="aurora-content-overview">
        <div class="aurora-overview-stats">
            <div class="aurora-stat-item">
                <span class="aurora-stat-value">{total_words:,}</span>
                <span class="aurora-stat-label">Total Words</span>
            </div>
            <div class="aurora-stat-item">
                <span class="aurora-stat-value">{content_types}</span>
                <span class="aurora-stat-label">Content Types</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Result sections
    result_sections = [
        ("transcript", "Transcript", results.get("transcript", "")),
        ("wisdom", "Wisdom", results.get("wisdom", "")),
        ("article", "Article", results.get("article", "")),
        ("social_content", "Social Content", results.get("social_content", "")),
    ]

    has_content = False
    for key, title, content in result_sections:
        if not content:
            continue
        has_content = True
        st.markdown(f'<div id="result-{key}"></div>', unsafe_allow_html=True)
        word_count = len(str(content).split())
        with st.expander(f"{title} ({word_count} words)", expanded=False):
            col1, col2, _col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("Copy", key=f"copy_{key}", use_container_width=True):
                    st.code(content, language="text")
                    st.success("Content displayed above - copy with Ctrl+A, Ctrl+C")
            with col2:
                st.download_button(
                    label="Download",
                    data=content,
                    file_name=f"{key}.txt",
                    mime="text/plain",
                    key=f"download_{key}",
                    use_container_width=True,
                )
            st.markdown(content)

    if not has_content:
        st.warning("No content available to display.")

    # Export section
    st.markdown("---")
    st.markdown(
        """
    <div class="aurora-export-section">
        <h3 class="aurora-export-title">Additional Export Options</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export as Text", use_container_width=True):
            export_content = create_text_export(results)
            st.download_button(
                label="Download Text File",
                data=export_content,
                file_name=f"whisperforge_content_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                key="download_text_export",
                use_container_width=True,
            )

    with col2:
        if st.button("Export as Markdown", use_container_width=True):
            md_content = export_to_markdown(results)
            st.download_button(
                label="Download Markdown",
                data=md_content,
                file_name=f"whisperforge_content_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                key="download_md_export",
                use_container_width=True,
            )

    with col3:
        try:
            if st.button("Export as Word", use_container_width=True):
                word_bytes = export_to_word(results)
                st.download_button(
                    label="Download Word",
                    data=word_bytes,
                    file_name=f"whisperforge_content_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_word_export",
                    use_container_width=True,
                )
        except ImportError:
            st.info("Install python-docx for Word export")
