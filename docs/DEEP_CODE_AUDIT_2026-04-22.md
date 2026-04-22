# WhisperForge Deep Audit Report


## Metadata

Generated: 2026-04-22T00:47:53.960652

Root: `/workspace/whisperforge`


## Unit Tests

**Status:** ✅

```
ssssssss........                                                         [100%]
8 passed, 8 skipped in 0.30s
```


## Syntax Audit

**Status:** ❌ Syntax errors detected

- app_simple.py:1728:16 unexpected indent


## Static Analysis

### Ruff
Exit code: 1

```
invalid-syntax: Unexpected indentation
    --> app_simple.py:1728:1
     |
1727 |                 # Enhanced audio player
1728 |                 if file_size < 50:  # Only show player for files under 50MB
     | ^^^^^^^^^^^^^^^^
1729 |                     st.markdown('<div class="aurora-audio-player">', unsafe_allow_html=True)
1730 |                     st.audio(uploaded_file.getvalue())
     |

invalid-syntax: Expected a statement
    --> app_simple.py:1749:5
     |
1747 |                             st.session_state.current_results = results
1748 |     
1749 |     else:
     |     ^^^^
1750 |         # Enhanced large file upload
1751 |         st.markdown("### Enhanced Large File Processing")
     |

invalid-syntax: Expected a statement
    --> app_simple.py:1749:9
     |
1747 |                             st.session_state.current_results = results
1748 |     
1749 |     else:
     |         ^
1750 |         # Enhanced large file upload
1751 |         st.markdown("### Enhanced Large File Processing")
     |

invalid-syntax: Expected a statement
    --> app_simple.py:1749:10
     |
1747 |                             st.session_state.current_results = results
1748 |     
1749 |     else:
     |          ^
1750 |         # Enhanced large file upload
1751 |         st.markdown("### Enhanced Large File Processing")
     |

invalid-syntax: Unexpected indentation
    --> app_simple.py:1751:1
     |
1749 |     else:
1750 |         # Enhanced large file upload
1751 |         st.markdown("### Enhanced Large File Processing")
     | ^^^^^^^^
1752 |         
1753 |         # Initialize enhanced processor
     |

invalid-syntax: Expected a statement
    --> app_simple.py:1854:5
     |
1853 |     # Show results if available
1854 |     if 'current_results' in st.session_state:
     |     ^
1855 |         show_results(st.session_state.current_results)
     |

invalid-syntax: Expected a statement
    --> app_simple.py:1857:1
     |
1855 |         show_results(st.session_state.current_results)
1856 |
1857 | def show_content_library():
     | ^
1858 |     """Content library/history page"""
1859 |     st.markdown("### 📚 Content Library")
     |

F401 [*] `streamlit` imported but unused
 --> core/auth_wrapper.py:7:21
  |
5 | """
6 |
7 | import streamlit as st
  |                     ^^
8 | from typing import Optional, Dict, Any
9 | from .session_manager import get_session_manager
  |
help: Remove unused import: `streamlit`

F401 [*] `.supabase_integration.get_supabase_client` imported but unused
  --> core/auth_wrapper.py:10:35
   |
 8 | from typing import Optional, Dict, Any
 9 | from .session_manager import get_session_manager
10 | from .supabase_integration import get_supabase_client
   |                                   ^^^^^^^^^^^^^^^^^^^
11 | from .utils import hash_password, verify_password, legacy_hash_password
12 | from core.logging_config import logger
   |
help: Remove unused import: `.supabase_integration.get_supabase_client`

F841 Local variable `password_migrated` is assigned to but never used
  --> core/auth_wrapper.py:80:21
   |
78 |                 if legacy_hash_password(password) == stored_password:
79 |                     password_valid = True
80 |                     password_migrated = True
   |                     ^^^^^^^^^^^^^^^^^
81 |                     
82 |                     # Migrate to bcrypt
   |
help: Remove assignment to unused variable `password_migrated`

F401 [*] `os` imported but unused
 --> core/content_generation.py:7:8
  |
6 | import logging
7 | import os
  |        ^^
8 | from typing import Dict, Optional
  |
help: Remove unused import: `os`

F401 [*] `typing.Optional` imported but unused
  --> core/content_generation.py:8:26
   |
 6 | import logging
 7 | import os
 8 | from typing import Dict, Optional
   |                          ^^^^^^^^
 9 |
10 | from .utils import get_openai_client, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt
   |
help: Remove unused import: `typing.Optional`

F401 [*] `.utils.get_prompt` imported but unused
  --> core/content_generation.py:10:39
   |
 8 | from typing import Dict, Optional
 9 |
10 | from .utils import get_openai_client, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt
   |                                       ^^^^^^^^^^
11 |
12 | # Configure logging
   |
help: Remove unused import

F401 [*] `.utils.DEFAULT_PROMPTS` imported but unused
  --> core/content_generation.py:10:51
   |
 8 | from typing import Dict, Optional
 9 |
10 | from .utils import get_openai_client, get_prompt, DEFAULT_PROMPTS, get_enhanced_prompt
   |                                                   ^^^^^^^^^^^^^^^
11 |
12 | # Configure logging
   |
help: Remove unused import

F401 [*] `asyncio` imported but unused
 --> core/file_upload.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import logging
8 | import math
  |
help: Remove unused import: `asyncio`

F401 [*] `mimetypes` imported but unused
  --> core/file_upload.py:9:8
   |
 7 | import logging
 8 | import math
 9 | import mimetypes
   |        ^^^^^^^^^
10 | import os
11 | import tempfile
   |
help: Remove unused import: `mimetypes`

F401 [*] `threading` imported but unused
  --> core/file_upload.py:12:8
   |
10 | import os
11 | import tempfile
12 | import threading
   |        ^^^^^^^^^
13 | import time
14 | from concurrent.futures import ThreadPoolExecutor, as_completed
   |
help: Remove unused import: `threading`

F541 [*] f-string without any placeholders
  --> core/file_upload.py:39:23
   |
38 |           # Enhanced upload zone HTML with large file support
39 |           upload_html = f"""
   |  _______________________^
40 | |         <div class="large-upload-zone-container">
41 | |             <div class="large-upload-zone" id="large-upload-zone">
42 | |                 <div class="upload-icon">
43 | |                     <div class="upload-icon-inner">🎵</div>
44 | |                 </div>
45 | |                 <div class="upload-text">
46 | |                     <h3>Drop your large audio files here</h3>
47 | |                     <p>Supports files up to 2GB with intelligent chunking</p>
48 | |                     <div class="upload-info">
49 | |                         <span class="supported-formats">Audio: MP3, WAV, M4A, AAC, OGG, FLAC, WEBM</span>
50 | |                         <span class="max-size">Max size: 2GB</span>
51 | |                         <span class="chunk-info">Auto-chunked for optimal processing</span>
52 | |                     </div>
53 | |                 </div>
54 | |                 <div class="upload-features">
55 | |                     <div class="feature">
56 | |                         <span class="feature-icon">⚡</span>
57 | |                         <span>Parallel Processing</span>
58 | |                     </div>
59 | |                     <div class="feature">
60 | |                         <span class="feature-icon">📊</span>
61 | |                         <span>Real-time Progress</span>
62 | |                     </div>
63 | |                     <div class="feature">
64 | |                         <span class="feature-icon">🔄</span>
65 | |                         <span>Auto-retry on Errors</span>
66 | |                     </div>
67 | |                 </div>
68 | |             </div>
69 | |         </div>
70 | |         """
   | |___________^
71 |           
72 |           # Enhanced CSS for large file upload
   |
help: Remove extraneous `f` prefix

F821 Undefined name `AudioSegment`
   --> core/file_upload.py:329:21
    |
328 |             # Load audio with pydub
329 |             audio = AudioSegment.from_file(temp_file_path)
    |                     ^^^^^^^^^^^^
330 |             duration_ms = len(audio)
331 |             duration_minutes = duration_ms / (1000 * 60)
    |

F541 [*] f-string without any placeholders
   --> core/file_upload.py:765:23
    |
764 |           # Enhanced upload zone HTML
765 |           upload_html = f"""
    |  _______________________^
766 | |         <div class="enhanced-upload-container">
767 | |             <div class="enhanced-upload-zone" id="enhanced-upload-zone">
768 | |                 <div class="upload-icon-large">
769 | |                     <div class="upload-icon-inner">🎵</div>
770 | |                     <div class="upload-pulse"></div>
771 | |                 </div>
772 | |                 <div class="upload-content">
773 | |                     <h2>Enhanced Large File Upload</h2>
774 | |                     <p class="upload-subtitle">Powered by FFmpeg • Up to 2GB • Intelligent Chunking</p>
775 | |                     <div class="upload-features-grid">
776 | |                         <div class="feature-card">
777 | |                             <span class="feature-icon">⚡</span>
778 | |                             <span class="feature-text">10-min chunks</span>
779 | |                         </div>
780 | |                         <div class="feature-card">
781 | |                             <span class="feature-icon">🔄</span>
782 | |                             <span class="feature-text">Parallel processing</span>
783 | |                         </div>
784 | |                         <div class="feature-card">
785 | |                             <span class="feature-icon">💾</span>
786 | |                             <span class="feature-text">Memory efficient</span>
787 | |                         </div>
788 | |                         <div class="feature-card">
789 | |                             <span class="feature-icon">🎯</span>
790 | |                             <span class="feature-text">Auto-retry</span>
791 | |                         </div>
792 | |                     </div>
793 | |                     <div class="supported-formats-enhanced">
794 | |                         <div class="format-group">
795 | |                             <strong>Audio:</strong> MP3, WAV, M4A, AAC, OGG, FLAC, WEBM
796 | |                         </div>
797 | |                         <div class="format-group">
798 | |                             <strong>Video:</strong> MP4, AVI, MOV, MKV, WMV (audio extraction)
799 | |                         </div>
800 | |                     </div>
801 | |                 </div>
802 | |             </div>
803 | |         </div>
804 | |         """
    | |___________^
805 |           
806 |           # Enhanced CSS
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
 --> core/health_check.py:5:1
  |
3 | """Minimal health check utilities for WhisperForge."""
4 |
5 | from dataclasses import dataclass, asdict
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
6 | from datetime import datetime
7 | from typing import Any, Dict
  |

E402 Module level import not at top of file
 --> core/health_check.py:6:1
  |
5 | from dataclasses import dataclass, asdict
6 | from datetime import datetime
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
7 | from typing import Any, Dict
  |

E402 Module level import not at top of file
 --> core/health_check.py:7:1
  |
5 | from dataclasses import dataclass, asdict
6 | from datetime import datetime
7 | from typing import Any, Dict
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8 |
9 | @dataclass
  |

F401 [*] `os` imported but unused
  --> core/logging_config.py:8:8
   |
 6 | import logging
 7 | import sys
 8 | import os
   |        ^^
 9 | from datetime import datetime
10 | from pathlib import Path
   |
help: Remove unused import: `os`

F401 [*] `typing.List` imported but unused
  --> core/metrics_exporter.py:11:31
   |
10 | import json
11 | from typing import Any, Dict, List
   |                               ^^^^
   |
help: Remove unused import: `typing.List`

F401 [*] `datetime.datetime` imported but unused
  --> core/notifications.py:9:22
   |
 7 | import time
 8 | from typing import Optional, Literal
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 |
11 | class NotificationManager:
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.Optional` imported but unused
  --> core/streaming_pipeline.py:8:26
   |
 6 | import streamlit as st
 7 | import time
 8 | from typing import Dict, Optional, Any
   |                          ^^^^^^^^
 9 | from datetime import datetime
10 | from .content_generation import (
   |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
  --> core/streaming_pipeline.py:9:22
   |
 7 | import time
 8 | from typing import Dict, Optional, Any
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 | from .content_generation import (
11 |     transcribe_audio, generate_wisdom, generate_outline, generate_article,
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `.content_generation.transcribe_audio` imported but unused
  --> core/streaming_pipeline.py:11:5
   |
 9 | from datetime import datetime
10 | from .content_generation import (
11 |     transcribe_audio, generate_wisdom, generate_outline, generate_article,
   |     ^^^^^^^^^^^^^^^^
12 |     generate_social_content, generate_image_prompts, editor_critique
13 | )
   |
help: Remove unused import: `.content_generation.transcribe_audio`

F401 [*] `.visible_thinking.render_thinking_stream` imported but unused
  --> core/streaming_pipeline.py:15:92
   |
13 | )
14 | from .research_enrichment import generate_research_enrichment
15 | from .visible_thinking import thinking_step_start, thinking_step_complete, thinking_error, render_thinking_stream
   |                                                                                            ^^^^^^^^^^^^^^^^^^^^^^
16 | # Removed old complex progress tracker - using simple progress bars now
   |
help: Remove unused import: `.visible_thinking.render_thinking_stream`

F811 [*] Redefinition of unused `transcribe_audio` from line 11
   --> core/streaming_pipeline.py:171:41
    |
169 |     def _transcribe_small_file(self, audio_file) -> str:
170 |         """Transcribe small files directly"""
171 |         from .content_generation import transcribe_audio
    |                                         ^^^^^^^^^^^^^^^^ `transcribe_audio` redefined here
172 |         
173 |         st.write("🎵 **Processing small file directly...**")
    |
   ::: core/streaming_pipeline.py:11:5
    |
  9 | from datetime import datetime
 10 | from .content_generation import (
 11 |     transcribe_audio, generate_wisdom, generate_outline, generate_article,
    |     ---------------- previous definition of `transcribe_audio` here
 12 |     generate_social_content, generate_image_prompts, editor_critique
 13 | )
    |
help: Remove definition: `transcribe_audio`

F401 [*] `html` imported but unused
 --> core/streaming_results.py:7:8
  |
6 | import streamlit as st
7 | import html
  |        ^^^^
8 | import time
9 | from typing import Dict, Any, Optional
  |
help: Remove unused import: `html`

F401 [*] `typing.Optional` imported but unused
  --> core/streaming_results.py:9:31
   |
 7 | import html
 8 | import time
 9 | from typing import Dict, Any, Optional
   |                               ^^^^^^^^
10 | from .streaming_pipeline import get_pipeline_controller
11 | import uuid
   |
help: Remove unused import: `typing.Optional`

F841 Local variable `expand_key` is assigned to but never used
   --> core/streaming_results.py:186:9
    |
185 |         # Expandable full content
186 |         expand_key = generate_unique_key(f"expand_{step_key}")
    |         ^^^^^^^^^^
187 |         with st.expander("📖 Show Full Content", expanded=False):
188 |             st.markdown(content_str)
    |
help: Remove assignment to unused variable `expand_key`

F841 Local variable `card_key` is assigned to but never used
   --> core/streaming_results.py:442:5
    |
441 |     # Create unique key for this card
442 |     card_key = generate_unique_key(f"stream_card_{title.lower()}")
    |     ^^^^^^^^
443 |     
444 |     # Live vs complete styling
    |
help: Remove assignment to unused variable `card_key`

F841 [*] Local variable `e` is assigned to but never used
   --> core/streaming_results.py:884:33
    |
882 |             try:
883 |                 render_thinking_stream(thinking_container)
884 |             except Exception as e:
    |                                 ^
885 |                 st.info(f"💭 AI is thinking... (thinking system loading)")
    |
help: Remove assignment to unused variable `e`

F541 [*] f-string without any placeholders
   --> core/streaming_results.py:885:25
    |
883 |                 render_thinking_stream(thinking_container)
884 |             except Exception as e:
885 |                 st.info(f"💭 AI is thinking... (thinking system loading)")
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
886 |     
887 |     # Main processing status container with st.status()
    |
help: Remove extraneous `f` prefix

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:982:44
    |
980 |             st.markdown("**Generated Content Types:**")
981 |             content_types = []
982 |             if results.get('transcription'): content_types.append("📝 Transcription")
    |                                            ^
983 |             if results.get('wisdom_extraction'): content_types.append("💎 Insights")
984 |             if results.get('research_enrichment'): content_types.append("🔍 Research")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:983:48
    |
981 |             content_types = []
982 |             if results.get('transcription'): content_types.append("📝 Transcription")
983 |             if results.get('wisdom_extraction'): content_types.append("💎 Insights")
    |                                                ^
984 |             if results.get('research_enrichment'): content_types.append("🔍 Research")
985 |             if results.get('outline_creation'): content_types.append("📋 Outline")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:984:50
    |
982 |             if results.get('transcription'): content_types.append("📝 Transcription")
983 |             if results.get('wisdom_extraction'): content_types.append("💎 Insights")
984 |             if results.get('research_enrichment'): content_types.append("🔍 Research")
    |                                                  ^
985 |             if results.get('outline_creation'): content_types.append("📋 Outline")
986 |             if results.get('article_creation'): content_types.append("📰 Article")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:985:47
    |
983 |             if results.get('wisdom_extraction'): content_types.append("💎 Insights")
984 |             if results.get('research_enrichment'): content_types.append("🔍 Research")
985 |             if results.get('outline_creation'): content_types.append("📋 Outline")
    |                                               ^
986 |             if results.get('article_creation'): content_types.append("📰 Article")
987 |             if results.get('social_content'): content_types.append("📱 Social Posts")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:986:47
    |
984 |             if results.get('research_enrichment'): content_types.append("🔍 Research")
985 |             if results.get('outline_creation'): content_types.append("📋 Outline")
986 |             if results.get('article_creation'): content_types.append("📰 Article")
    |                                               ^
987 |             if results.get('social_content'): content_types.append("📱 Social Posts")
988 |             if results.get('image_prompts'): content_types.append("🖼️ Image Prompts")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:987:45
    |
985 |             if results.get('outline_creation'): content_types.append("📋 Outline")
986 |             if results.get('article_creation'): content_types.append("📰 Article")
987 |             if results.get('social_content'): content_types.append("📱 Social Posts")
    |                                             ^
988 |             if results.get('image_prompts'): content_types.append("🖼️ Image Prompts")
    |

E701 Multiple statements on one line (colon)
   --> core/streaming_results.py:988:44
    |
986 |             if results.get('article_creation'): content_types.append("📰 Article")
987 |             if results.get('social_content'): content_types.append("📱 Social Posts")
988 |             if results.get('image_prompts'): content_types.append("🖼️ Image Prompts")
    |                                            ^
989 |             
990 |             if content_types:
    |

E402 Module level import not at top of file
  --> core/supabase_integration.py:20:1
   |
19 | # Import hash_password function from utils instead of app
20 | from .utils import hash_password
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 |
22 | logger = logging.getLogger(__name__)
   |

F841 Local variable `result` is assigned to but never used
  --> core/supabase_integration.py:51:13
   |
49 |         try:
50 |             # Try a simple query to test connectivity
51 |             result = self.client.table("users").select("id").limit(1).execute()
   |             ^^^^^^
52 |             logger.info("Supabase connection test successful")
53 |             return True
   |
help: Remove assignment to unused variable `result`

F401 [*] `time` imported but unused
  --> core/utils.py:9:8
   |
 7 | import bcrypt
 8 | import os
 9 | import time
   |        ^^^^
10 | import logging
11 | import requests
   |
help: Remove unused import: `time`

F401 [*] `requests` imported but unused
  --> core/utils.py:11:8
   |
 9 | import time
10 | import logging
11 | import requests
   |        ^^^^^^^^
12 | from typing import Dict, Optional, Any
13 | from pathlib import Path
   |
help: Remove unused import: `requests`

F401 [*] `typing.Optional` imported but unused
  --> core/utils.py:12:26
   |
10 | import logging
11 | import requests
12 | from typing import Dict, Optional, Any
   |                          ^^^^^^^^
13 | from pathlib import Path
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> core/utils.py:12:36
   |
10 | import logging
11 | import requests
12 | from typing import Dict, Optional, Any
   |                                    ^^^
13 | from pathlib import Path
   |
help: Remove unused import

F401 [*] `streamlit` imported but unused
  --> core/visible_thinking.py:8:21
   |
 6 | import logging
 7 |
 8 | import streamlit as st
   |                     ^^
 9 |
10 | logger = logging.getLogger(__name__)
   |
help: Remove unused import: `streamlit`

F841 Local variable `result` is assigned to but never used
  --> create_missing_tables.py:30:9
   |
29 |     try:
30 |         result = client.client.rpc('exec_sql', {'sql': sql}).execute()
   |         ^^^^^^
31 |         print("✅ Prompts table created successfully")
32 |         return True
   |
help: Remove assignment to unused variable `result`

F841 Local variable `result` is assigned to but never used
  --> create_missing_tables.py:58:9
   |
57 |     try:
58 |         result = client.client.rpc('exec_sql', {'sql': sql}).execute()
   |         ^^^^^^
59 |         print("✅ API keys table created successfully")
60 |         return True
   |
help: Remove assignment to unused variable `result`

F841 Local variable `result` is assigned to but never used
  --> create_missing_tables.py:77:9
   |
75 |     # Test api_keys table
76 |     try:
77 |         result = client.client.table('api_keys').select('*').limit(1).execute()
   |         ^^^^^^
78 |         print("✅ API keys table accessible")
79 |     except Exception as e:
   |
help: Remove assignment to unused variable `result`

F401 [*] `os` imported but unused
 --> deploy_fixes.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import sys
9 | from datetime import datetime
  |
help: Remove unused import: `os`

F401 [*] `sys` imported but unused
 --> deploy_fixes.py:8:8
  |
7 | import os
8 | import sys
  |        ^^^
9 | from datetime import datetime
  |
help: Remove unused import: `sys`

F841 Local variable `result` is assigned to but never used
  --> deploy_fixes.py:33:17
   |
31 |             try:
32 |                 # Test table access
33 |                 result = client.client.table(table).select("*").limit(1).execute()
   |                 ^^^^^^
34 |                 print(f"✅ {table}")
35 |             except Exception:
   |
help: Remove assignment to unused variable `result`

F401 [*] `core.content_generation.transcribe_audio` imported but unused
  --> deploy_fixes.py:58:45
   |
56 |     try:
57 |         # Test imports
58 |         from core.content_generation import transcribe_audio, generate_wisdom
   |                                             ^^^^^^^^^^^^^^^^
59 |         from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
60 |         from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
   |
help: Remove unused import

F401 [*] `core.content_generation.generate_wisdom` imported but unused
  --> deploy_fixes.py:58:63
   |
56 |     try:
57 |         # Test imports
58 |         from core.content_generation import transcribe_audio, generate_wisdom
   |                                                               ^^^^^^^^^^^^^^^
59 |         from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
60 |         from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
   |
help: Remove unused import

F401 [*] `core.file_upload.FileUploadManager` imported but unused
  --> deploy_fixes.py:59:38
   |
57 |         # Test imports
58 |         from core.content_generation import transcribe_audio, generate_wisdom
59 |         from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
   |                                      ^^^^^^^^^^^^^^^^^
60 |         from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
61 |         from core.supabase_integration import get_supabase_client
   |
help: Remove unused import

F401 [*] `core.file_upload.EnhancedLargeFileProcessor` imported but unused
  --> deploy_fixes.py:59:57
   |
57 |         # Test imports
58 |         from core.content_generation import transcribe_audio, generate_wisdom
59 |         from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
   |                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
60 |         from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
61 |         from core.supabase_integration import get_supabase_client
   |
help: Remove unused import

F401 [*] `core.utils.load_prompt_from_file` imported but unused
  --> deploy_fixes.py:60:49
   |
58 |         from core.content_generation import transcribe_audio, generate_wisdom
59 |         from core.file_upload import FileUploadManager, EnhancedLargeFileProcessor
60 |         from core.utils import DEFAULT_PROMPTS, load_prompt_from_file
   |                                                 ^^^^^^^^^^^^^^^^^^^^^
61 |         from core.supabase_integration import get_supabase_client
   |
help: Remove unused import: `core.utils.load_prompt_from_file`

F541 [*] f-string without any placeholders
  --> deploy_fixes.py:95:11
   |
94 |     # Final assessment
95 |     print(f"\n📊 DEPLOYMENT READINESS")
   |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
96 |     print("=" * 60)
   |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
  --> scripts/integration_audit.py:8:8
   |
 7 | import sys
 8 | import os
   |        ^^
 9 | import traceback
10 | from pathlib import Path
   |
help: Remove unused import: `os`

F841 Local variable `func` is assigned to but never used
  --> scripts/integration_audit.py:36:9
   |
34 |     try:
35 |         module = __import__(module_name, fromlist=[function_name])
36 |         func = getattr(module, function_name)
   |         ^^^^
37 |         print(f"✅ {module_name}.{function_name} - {description}")
38 |         return True
   |
help: Remove assignment to unused variable `func`

F841 Local variable `method` is assigned to but never used
  --> scripts/integration_audit.py:48:9
   |
46 |         module = __import__(module_name, fromlist=[class_name])
47 |         cls = getattr(module, class_name)
48 |         method = getattr(cls, method_name)
   |         ^^^^^^
49 |         print(f"✅ {module_name}.{class_name}.{method_name} - {description}")
50 |         return True
   |
help: Remove assignment to unused variable `method`

F401 [*] `os` imported but unused
  --> scripts/test_monitoring.py:13:8
   |
11 | import time
12 | import json
13 | import os
   |        ^^
14 | import traceback
15 | from pathlib import Path
   |
help: Remove unused import: `os`

F841 Local variable `trace_id` is assigned to but never used
  --> scripts/test_monitoring.py:39:9
   |
38 |         # Test trace context
39 |         trace_id = set_trace_context(user_id="test_user", operation="test_operation")
   |         ^^^^^^^^
40 |         structured_logger.info("Message with trace context", test_data="trace_test")
   |
help: Remove assignment to unused variable `trace_id`

F401 [*] `core.metrics_exporter.metrics_exporter` imported but unused
   --> scripts/test_monitoring.py:107:13
    |
105 |     try:
106 |         from core.metrics_exporter import (
107 |             metrics_exporter, track_request, track_pipeline,
    |             ^^^^^^^^^^^^^^^^
108 |             export_prometheus_metrics, export_json_metrics
109 |         )
    |
help: Remove unused import: `core.metrics_exporter.metrics_exporter`

F401 [*] `core.streamlit_monitoring.streamlit_monitor` imported but unused
   --> scripts/test_monitoring.py:217:13
    |
215 |     try:
216 |         from core.streamlit_monitoring import (
217 |             streamlit_monitor, streamlit_page, streamlit_component
    |             ^^^^^^^^^^^^^^^^^
218 |         )
    |
help: Remove unused import: `core.streamlit_monitoring.streamlit_monitor`

F541 [*] f-string without any placeholders
   --> scripts/test_monitoring.py:273:31
    |
271 |                     try:
272 |                         last_entry = json.loads(lines[-1].strip())
273 |                         print(f"   ✅ Last log entry is valid JSON")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
274 |                         if 'timestamp' in last_entry and 'level' in last_entry:
275 |                             print(f"   ✅ Log entry has required fields")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts/test_monitoring.py:275:35
    |
273 |                         print(f"   ✅ Last log entry is valid JSON")
274 |                         if 'timestamp' in last_entry and 'level' in last_entry:
275 |                             print(f"   ✅ Log entry has required fields")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
276 |                     except json.JSONDecodeError:
277 |                         print(f"   ⚠️ Last log entry is not valid JSON")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts/test_monitoring.py:277:31
    |
275 |                             print(f"   ✅ Log entry has required fields")
276 |                     except json.JSONDecodeError:
277 |                         print(f"   ⚠️ Last log entry is not valid JSON")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
278 |                 else:
279 |                     print(f"   ⚠️ Log file is empty")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts/test_monitoring.py:279:27
    |
277 |                         print(f"   ⚠️ Last log entry is not valid JSON")
278 |                 else:
279 |                     print(f"   ⚠️ Log file is empty")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^
280 |         else:
281 |             print(f"   ⚠️ Log file not found: {log_file}")
    |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> scripts/test_oauth.py:7:8
  |
6 | import sys
7 | import os
  |        ^^
8 | from pathlib import Path
9 | import pytest
  |
help: Remove unused import: `os`

F541 [*] f-string without any placeholders
  --> scripts/test_oauth.py:40:19
   |
39 |         if hasattr(auth_response, 'url') and auth_response.url:
40 |             print(f"✅ OAuth URL generated successfully")
   |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
41 |             print(f"   URL: {auth_response.url[:50]}...")
42 |             assert True
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts/test_oauth.py:44:19
   |
42 |             assert True
43 |         else:
44 |             print(f"❌ OAuth URL not generated properly")
   |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
45 |             print(f"   Response: {auth_response}")
46 |             assert False, "OAuth URL not generated properly"
   |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> scripts/ui_ux_audit.py:8:8
  |
7 | import sys
8 | import os
  |        ^^
9 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `core.streaming_results.show_streaming_results` imported but unused
  --> scripts/ui_ux_audit.py:72:44
   |
71 |     try:
72 |         from core.streaming_results import show_streaming_results, show_real_time_content_stream
   |                                            ^^^^^^^^^^^^^^^^^^^^^^
73 |         from core.streaming_pipeline import get_pipeline_controller
74 |         from core.ui_components import AuroraComponents
   |
help: Remove unused import

F401 [*] `core.streaming_results.show_real_time_content_stream` imported but unused
  --> scripts/ui_ux_audit.py:72:68
   |
71 |     try:
72 |         from core.streaming_results import show_streaming_results, show_real_time_content_stream
   |                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
73 |         from core.streaming_pipeline import get_pipeline_controller
74 |         from core.ui_components import AuroraComponents
   |
help: Remove unused import

F401 [*] `core.streaming_pipeline.get_pipeline_controller` imported but unused
  --> scripts/ui_ux_audit.py:73:45
   |
71 |     try:
72 |         from core.streaming_results import show_streaming_results, show_real_time_content_stream
73 |         from core.streaming_pipeline import get_pipeline_controller
   |                                             ^^^^^^^^^^^^^^^^^^^^^^^
74 |         from core.ui_components import AuroraComponents
   |
help: Remove unused import: `core.streaming_pipeline.get_pipeline_controller`

F401 [*] `core.ui_components.AuroraContainer` imported but unused
  --> scripts/ui_ux_audit.py:98:40
   |
97 |     try:
98 |         from core.ui_components import AuroraContainer, AuroraComponents
   |                                        ^^^^^^^^^^^^^^^
99 |         from core.styling import apply_aurora_theme, create_aurora_header
   |
help: Remove unused import: `core.ui_components.AuroraContainer`

F401 [*] `core.styling.apply_aurora_theme` imported but unused
   --> scripts/ui_ux_audit.py:99:34
    |
 97 |     try:
 98 |         from core.ui_components import AuroraContainer, AuroraComponents
 99 |         from core.styling import apply_aurora_theme, create_aurora_header
    |                                  ^^^^^^^^^^^^^^^^^^
100 |         
101 |         ui_features = [
    |
help: Remove unused import

F401 [*] `core.styling.create_aurora_header` imported but unused
   --> scripts/ui_ux_audit.py:99:54
    |
 97 |     try:
 98 |         from core.ui_components import AuroraContainer, AuroraComponents
 99 |         from core.styling import apply_aurora_theme, create_aurora_header
    |                                                      ^^^^^^^^^^^^^^^^^^^^
100 |         
101 |         ui_features = [
    |
help: Remove unused import

F401 [*] `traceback` imported but unused
  --> scripts/validate_app.py:10:8
   |
 8 | import os
 9 | import importlib
10 | import traceback
   |        ^^^^^^^^^
11 | from pathlib import Path
   |
help: Remove unused import: `traceback`

F541 [*] f-string without any placeholders
  --> scripts/validate_app.py:39:15
   |
37 |         total = self.tests_passed + self.tests_failed
38 |         print(f"\n{'='*50}")
39 |         print(f"VALIDATION SUMMARY")
   |               ^^^^^^^^^^^^^^^^^^^^^
40 |         print(f"{'='*50}")
41 |         print(f"Tests Passed: {self.tests_passed}/{total}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts/validate_app.py:46:19
   |
45 |         if self.errors:
46 |             print(f"\n🚨 ERRORS:")
   |                   ^^^^^^^^^^^^^^^
47 |             for error in self.errors:
48 |                 print(f"  - {error}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts/validate_app.py:51:19
   |
50 |         if self.warnings:
51 |             print(f"\n⚠️  WARNINGS:")
   |                   ^^^^^^^^^^^^^^^^^
52 |             for warning in self.warnings:
53 |                 print(f"  - {warning}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts/validate_app.py:56:19
   |
55 |         if self.tests_failed == 0:
56 |             print(f"\n🎉 ALL TESTS PASSED! App is ready for deployment.")
   |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
57 |             return True
58 |         else:
   |
help: Remove extraneous `f` prefix

F841 Local variable `response` is assigned to but never used
   --> scripts/validate_app.py:186:17
    |
184 |             try:
185 |                 # Simple health check
186 |                 response = db.client.table("users").select("count", count="exact").limit(1).execute()
    |                 ^^^^^^^^
187 |                 result.pass_test("Supabase database connection")
188 |             except Exception as e:
    |
help: Remove assignment to unused variable `response`

F841 Local variable `client` is assigned to but never used
   --> scripts/validate_app.py:273:13
    |
271 |             import anthropic
272 |             # Basic client test (don't make actual API calls in validation)
273 |             client = anthropic.Anthropic(api_key=anthropic_key)
    |             ^^^^^^
274 |             result.pass_test("Anthropic configuration")
275 |         except Exception as e:
    |
help: Remove assignment to unused variable `client`

E722 Do not use bare `except`
   --> scripts/validate_app.py:296:9
    |
294 |             else:
295 |                 result.warn_test("Streamlit version", f"Version {version} may be outdated")
296 |         except:
    |         ^^^^^^
297 |             result.warn_test("Streamlit version", "Could not check version")
    |

F401 [*] `core.content_generation.transcribe_audio` imported but unused
   --> scripts/validate_app.py:320:45
    |
319 |     try:
320 |         from core.content_generation import transcribe_audio
    |                                             ^^^^^^^^^^^^^^^^
321 |         result.pass_test("Content generation import")
322 |     except Exception as e:
    |
help: Remove unused import: `core.content_generation.transcribe_audio`

F821 Undefined name `CLAUDE_API_KEY`
  --> shared/config.py:18:53
   |
16 |     logger.info("=== Configuration Status ===")
17 |     logger.info(f"OpenAI API Key present: {'Yes' if OPENAI_API_KEY else 'No'}")
18 |     logger.info(f"Claude API Key present: {'Yes' if CLAUDE_API_KEY else 'No'}")
   |                                                     ^^^^^^^^^^^^^^
19 |     logger.info(f"Notion API Key present: {'Yes' if NOTION_API_KEY else 'No'}")
20 |     logger.info(f"Service Token present: {'Yes' if SERVICE_TOKEN else 'No'}")
   |

F401 [*] `streamlit` imported but unused
  --> tests/conftest.py:11:21
   |
 9 | from pathlib import Path
10 | from unittest.mock import Mock, patch
11 | import streamlit as st
   |                     ^^
12 | from streamlit.testing.v1 import AppTest
   |
help: Remove unused import: `streamlit`

F401 [*] `os` imported but unused
 --> tests/test_basic_functionality.py:6:8
  |
5 | import pytest
6 | import os
  |        ^^
7 | from pathlib import Path
8 | import sys
  |
help: Remove unused import: `os`

F401 `core.content_generation.transcribe_audio` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:16:45
   |
14 |     """Test that core modules can be imported without errors"""
15 |     try:
16 |         from core.content_generation import transcribe_audio, generate_wisdom
   |                                             ^^^^^^^^^^^^^^^^
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
18 |         from core.supabase_integration import get_supabase_client
   |
help: Remove unused import

F401 `core.content_generation.generate_wisdom` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:16:63
   |
14 |     """Test that core modules can be imported without errors"""
15 |     try:
16 |         from core.content_generation import transcribe_audio, generate_wisdom
   |                                                               ^^^^^^^^^^^^^^^
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
18 |         from core.supabase_integration import get_supabase_client
   |
help: Remove unused import

F401 `core.file_upload.FileUploadManager` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:17:38
   |
15 |     try:
16 |         from core.content_generation import transcribe_audio, generate_wisdom
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
   |                                      ^^^^^^^^^^^^^^^^^
18 |         from core.supabase_integration import get_supabase_client
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
   |
help: Remove unused import

F401 `core.file_upload.LargeFileUploadManager` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:17:57
   |
15 |     try:
16 |         from core.content_generation import transcribe_audio, generate_wisdom
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
   |                                                         ^^^^^^^^^^^^^^^^^^^^^^
18 |         from core.supabase_integration import get_supabase_client
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
   |
help: Remove unused import

F401 `core.supabase_integration.get_supabase_client` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:18:47
   |
16 |         from core.content_generation import transcribe_audio, generate_wisdom
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
18 |         from core.supabase_integration import get_supabase_client
   |                                               ^^^^^^^^^^^^^^^^^^^
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
20 |         from core.visible_thinking import thinking_step_start
   |
help: Remove unused import: `core.supabase_integration.get_supabase_client`

F401 `core.utils.hash_password` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:19:32
   |
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
18 |         from core.supabase_integration import get_supabase_client
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
   |                                ^^^^^^^^^^^^^
20 |         from core.visible_thinking import thinking_step_start
21 |         assert True, "All core imports successful"
   |
help: Remove unused import

F401 `core.utils.DEFAULT_PROMPTS` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:19:47
   |
17 |         from core.file_upload import FileUploadManager, LargeFileUploadManager
18 |         from core.supabase_integration import get_supabase_client
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
   |                                               ^^^^^^^^^^^^^^^
20 |         from core.visible_thinking import thinking_step_start
21 |         assert True, "All core imports successful"
   |
help: Remove unused import

F401 `core.visible_thinking.thinking_step_start` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> tests/test_basic_functionality.py:20:43
   |
18 |         from core.supabase_integration import get_supabase_client
19 |         from core.utils import hash_password, DEFAULT_PROMPTS
20 |         from core.visible_thinking import thinking_step_start
   |                                           ^^^^^^^^^^^^^^^^^^^
21 |         assert True, "All core imports successful"
22 |     except ImportError as e:
   |
help: Remove unused import: `core.visible_thinking.thinking_step_start`

F401 [*] `tempfile` imported but unused
  --> whisperforge_cli.py:10:8
   |
 8 | import os
 9 | import sys
10 | import tempfile
   |        ^^^^^^^^
11 | from pathlib import Path
12 | from typing import Optional, Dict, Any
   |
help: Remove unused import: `tempfile`

F401 [*] `typing.Dict` imported but unused
  --> whisperforge_cli.py:12:30
   |
10 | import tempfile
11 | from pathlib import Path
12 | from typing import Optional, Dict, Any
   |                              ^^^^
13 |
14 | # Add the project root to Python path
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> whisperforge_cli.py:12:36
   |
10 | import tempfile
11 | from pathlib import Path
12 | from typing import Optional, Dict, Any
   |                                    ^^^
13 |
14 | # Add the project root to Python path
   |
help: Remove unused import

F541 [*] f-string without any placeholders
   --> whisperforge_cli.py:169:20
    |
168 |     if verbose:
169 |         click.echo(f"🚀 Starting WhisperForge pipeline...")
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
170 |         click.echo(f"Input file: {input_file}")
171 |         click.echo(f"Model: {model}")
    |
help: Remove extraneous `f` prefix

F401 `openai` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> whisperforge_cli.py:336:16
    |
334 |     # Check dependencies
335 |     try:
336 |         import openai
    |                ^^^^^^
337 |
338 |         click.echo("OpenAI library: ✅ Available")
    |
help: Remove unused import: `openai`

F401 `anthropic` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> whisperforge_cli.py:343:16
    |
342 |     try:
343 |         import anthropic
    |                ^^^^^^^^^
344 |
345 |         click.echo("Anthropic library: ✅ Available")
    |
help: Remove unused import: `anthropic`

F401 `pydub.AudioSegment` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> whisperforge_cli.py:351:27
    |
349 |     # Check audio processing
350 |     try:
351 |         from pydub import AudioSegment
    |                           ^^^^^^^^^^^^
352 |
353 |         click.echo("Audio processing (pydub): ✅ Available")
    |
help: Remove unused import: `pydub.AudioSegment`

Found 111 errors.
[*] 66 fixable with the `--fix` option (13 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

### Mypy (strict core)
Exit code: 1

```
core/metrics_exporter.py:71: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
core/health_check.py:39: error: Missing type parameters for generic type "list"  [type-arg]
core/monitoring.py:25: error: Missing type parameters for generic type "LoggerAdapter"  [type-arg]
core/monitoring.py:28: error: Argument 2 of "process" is incompatible with supertype "logging.LoggerAdapter"; supertype defines the argument type as "MutableMapping[str, Any]"  [override]
core/monitoring.py:28: note: This violates the Liskov substitution principle
core/monitoring.py:28: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#incompatible-overrides
core/monitoring.py:63: error: Function is missing a return type annotation  [no-untyped-def]
core/monitoring.py:99: error: Function is missing a return type annotation  [no-untyped-def]
core/monitoring.py:127: error: Function is missing a return type annotation  [no-untyped-def]
core/monitoring.py:130: error: Function is missing a type annotation  [no-untyped-def]
core/monitoring.py:131: error: Function is missing a type annotation  [no-untyped-def]
core/logging_config.py:21: error: Call to untyped function "setup_logging" in typed context  [no-untyped-call]
core/logging_config.py:23: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:23: note: Use "-> None" if function does not return a value
core/logging_config.py:68: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:68: error: Missing type parameters for generic type "Dict"  [type-arg]
core/logging_config.py:89: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:100: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:112: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:128: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:128: error: Missing type parameters for generic type "Dict"  [type-arg]
core/logging_config.py:139: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:160: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:174: error: Function is missing a type annotation  [no-untyped-def]
core/logging_config.py:195: error: Function is missing a type annotation  [no-untyped-def]
core/logging_config.py:204: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:204: error: Missing type parameters for generic type "Dict"  [type-arg]
core/logging_config.py:207: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:210: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:213: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:216: error: Function is missing a return type annotation  [no-untyped-def]
core/logging_config.py:216: error: Missing type parameters for generic type "Dict"  [type-arg]
core/logging_config.py:219: error: Function is missing a return type annotation  [no-untyped-def]
core/streamlit_monitoring.py:11: error: Missing type parameters for generic type "Callable"  [type-arg]
core/streamlit_monitoring.py:15: error: Function is missing a type annotation  [no-untyped-def]
core/streamlit_monitoring.py:24: error: Function is missing a return type annotation  [no-untyped-def]
core/streamlit_monitoring.py:25: error: Missing type parameters for generic type "Callable"  [type-arg]
core/streamlit_monitoring.py:27: error: Function is missing a type annotation  [no-untyped-def]
core/streamlit_monitoring.py:36: error: Function is missing a return type annotation  [no-untyped-def]
core/streamlit_monitoring.py:37: error: Missing type parameters for generic type "Callable"  [type-arg]
core/streamlit_monitoring.py:39: error: Function is missing a type annotation  [no-untyped-def]
core/visible_thinking.py:12: error: Function is missing a return type annotation  [no-untyped-def]
core/visible_thinking.py:18: error: Function is missing a return type annotation  [no-untyped-def]
core/visible_thinking.py:24: error: Function is missing a return type annotation  [no-untyped-def]
core/visible_thinking.py:30: error: Function is missing a return type annotation  [no-untyped-def]
core/visible_thinking.py:30: note: Use "-> None" if function does not return a value
core/styling.py:8: error: Function is missing a return type annotation  [no-untyped-def]
core/styling.py:8: note: Use "-> None" if function does not return a value
core/styling.py:46: error: Function is missing a return type annotation  [no-untyped-def]
core/styling.py:46: note: Use "-> None" if function does not return a value
core/styling.py:180: error: Function is missing a return type annotation  [no-untyped-def]
core/styling.py:269: error: Function is missing a type annotation  [no-untyped-def]
core/styling.py:289: error: Function is missing a type annotation  [no-untyped-def]
core/styling.py:345: error: Function is missing a type annotation  [no-untyped-def]
core/styling.py:378: error: Function is missing a type annotation  [no-untyped-def]
core/styling.py:394: error: Function is missing a type annotation  [no-untyped-def]
core/styling.py:410: error: Function is missing a type annotation  [no-untyped-def]
core/session_manager.py:16: error: Need type annotation for "data"  [var-annotated]
core/session_manager.py:26: error: Call to untyped function "_load" in typed context  [no-untyped-call]
core/session_manager.py:28: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:28: note: Use "-> None" if function does not return a value
core/session_manager.py:43: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:43: note: Use "-> None" if function does not return a value
core/session_manager.py:60: error: Call to untyped function "_save" in typed context  [no-untyped-call]
core/session_manager.py:67: error: Call to untyped function "_save" in typed context  [no-untyped-call]
core/session_manager.py:73: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:76: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:79: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:79: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/session_manager.py:80: error: Unsupported target for indexed assignment ("str | dict[Any, Any] | bool | None")  [index]
core/session_manager.py:82: error: Call to untyped function "_save" in typed context  [no-untyped-call]
core/session_manager.py:85: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:85: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/session_manager.py:86: error: Item "str" of "str | dict[Any, Any] | bool | None" has no attribute "get"  [union-attr]
core/session_manager.py:86: error: Item "bool" of "str | dict[Any, Any] | bool | None" has no attribute "get"  [union-attr]
core/session_manager.py:86: error: Item "None" of "str | dict[Any, Any] | bool | None" has no attribute "get"  [union-attr]
core/session_manager.py:88: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:91: error: Call to untyped function "_save" in typed context  [no-untyped-call]
core/session_manager.py:94: error: Incompatible return value type (got "str | dict[Any, Any] | bool | None", expected "str")  [return-value]
core/session_manager.py:96: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:99: error: Call to untyped function "_save" in typed context  [no-untyped-call]
core/session_manager.py:104: error: Function is missing a return type annotation  [no-untyped-def]
core/session_manager.py:106: error: Call to untyped function "get_user_email" in typed context  [no-untyped-call]
core/session_manager.py:115: error: Returning Any from function declared to return "SessionManager"  [no-any-return]
core/notifications.py:14: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:14: note: Use "-> None" if function does not return a value
core/notifications.py:17: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:147: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:240: error: Call to untyped function "NotificationManager" in typed context  [no-untyped-call]
core/notifications.py:243: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:247: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:251: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:255: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:259: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:263: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:267: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:271: error: Function is missing a return type annotation  [no-untyped-def]
core/notifications.py:348: error: Function is missing a return type annotation  [no-untyped-def]
core/utils.py:11: error: Library stubs not installed for "requests"  [import-untyped]
core/utils.py:11: note: Hint: "python3 -m pip install types-requests"
core/utils.py:11: note: (or run "mypy --install-types" to install all missing stub packages)
core/utils.py:51: error: Incompatible default for argument "user_id" (default has type "None", argument has type "str")  [assignment]
core/utils.py:51: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/utils.py:51: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/utils.py:96: error: Incompatible default for argument "knowledge_base" (default has type "None", argument has type "dict[str, str]")  [assignment]
core/utils.py:96: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/utils.py:96: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/utils.py:96: error: Incompatible default for argument "user_id" (default has type "None", argument has type "str")  [assignment]
core/utils.py:106: error: Function is missing a return type annotation  [no-untyped-def]
core/utils.py:123: error: Function is missing a return type annotation  [no-untyped-def]
core/utils.py:140: error: Function is missing a return type annotation  [no-untyped-def]
core/utils.py:144: error: Function is missing a return type annotation  [no-untyped-def]
core/content_generation.py:15: error: Incompatible default for argument "custom_prompt" (default has type "None", argument has type "str")  [assignment]
core/content_generation.py:15: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/content_generation.py:15: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/content_generation.py:15: error: Incompatible default for argument "knowledge_base" (default has type "None", argument has type "dict[str, str]")  [assignment]
core/content_generation.py:21: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/content_generation.py:34: error: Returning Any from function declared to return "str"  [no-any-return]
core/content_generation.py:40: error: Incompatible default for argument "custom_prompt" (default has type "None", argument has type "str")  [assignment]
core/content_generation.py:40: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/content_generation.py:40: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/content_generation.py:40: error: Incompatible default for argument "knowledge_base" (default has type "None", argument has type "dict[str, str]")  [assignment]
core/content_generation.py:48: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/content_generation.py:61: error: Returning Any from function declared to return "str"  [no-any-return]
core/content_generation.py:67: error: Incompatible default for argument "custom_prompt" (default has type "None", argument has type "str")  [assignment]
core/content_generation.py:67: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/content_generation.py:67: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/content_generation.py:67: error: Incompatible default for argument "knowledge_base" (default has type "None", argument has type "dict[str, str]")  [assignment]
core/content_generation.py:77: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/content_generation.py:90: error: Returning Any from function declared to return "str"  [no-any-return]
core/content_generation.py:96: error: Incompatible default for argument "custom_prompt" (default has type "None", argument has type "str")  [assignment]
core/content_generation.py:96: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/content_generation.py:96: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/content_generation.py:96: error: Incompatible default for argument "knowledge_base" (default has type "None", argument has type "dict[str, str]")  [assignment]
core/content_generation.py:106: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/content_generation.py:119: error: Returning Any from function declared to return "str"  [no-any-return]
core/content_generation.py:125: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/content_generation.py:128: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/content_generation.py:148: error: Returning Any from function declared to return "str"  [no-any-return]
core/file_upload.py:25: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:25: note: Use "-> None" if function does not return a value
core/file_upload.py:196: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:224: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:260: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:316: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:329: error: Name "AudioSegment" is not defined  [name-defined]
core/file_upload.py:377: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:377: error: Missing type parameters for generic type "Dict"  [type-arg]
core/file_upload.py:387: error: Module "core.content_generation" does not explicitly export attribute "get_openai_client"  [attr-defined]
core/file_upload.py:389: error: Missing type parameters for generic type "Dict"  [type-arg]
core/file_upload.py:399: error: Call to untyped function "get_openai_client" in typed context  [no-untyped-call]
core/file_upload.py:516: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:516: error: Missing type parameters for generic type "Dict"  [type-arg]
core/file_upload.py:525: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:547: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:637: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:666: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:666: note: Use "-> None" if function does not return a value
core/file_upload.py:729: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:966: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:986: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:1016: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/file_upload.py:1072: error: Call to untyped function "_cleanup_temp_dir" in typed context  [no-untyped-call]
core/file_upload.py:1088: error: Argument 1 to "join" has incompatible type "Any | None"; expected "str"  [arg-type]
core/file_upload.py:1126: error: Missing type parameters for generic type "Dict"  [type-arg]
core/file_upload.py:1137: error: Missing type parameters for generic type "Dict"  [type-arg]
core/file_upload.py:1209: error: Function is missing a return type annotation  [no-untyped-def]
core/file_upload.py:1209: note: Use "-> None" if function does not return a value
core/supabase_integration.py:30: error: Function is missing a return type annotation  [no-untyped-def]
core/supabase_integration.py:30: note: Use "-> None" if function does not return a value
core/supabase_integration.py:59: error: Incompatible default for argument "metadata" (default has type "None", argument has type "dict[str, Any]")  [assignment]
core/supabase_integration.py:59: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
core/supabase_integration.py:59: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
core/supabase_integration.py:78: error: Argument 1 to "insert" of "SyncRequestBuilder" has incompatible type "dict[str, object]"; expected "JSON"  [arg-type]
core/supabase_integration.py:80: error: Incompatible return value type (got "int | float | Sequence[JSON] | Mapping[str, JSON] | None", expected "dict[str, Any]")  [return-value]
core/supabase_integration.py:89: error: Incompatible return value type (got "int | float | Sequence[JSON] | Mapping[str, JSON] | None", expected "dict[str, Any] | None")  [return-value]
core/supabase_integration.py:98: error: Incompatible return value type (got "int | float | Sequence[JSON] | Mapping[str, JSON] | None", expected "dict[str, Any] | None")  [return-value]
core/supabase_integration.py:139: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:139: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:139: note: Possible overload variants:
core/supabase_integration.py:139: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:139: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:139: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:141: error: Incompatible return value type (got "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None", expected "str | None")  [return-value]
core/supabase_integration.py:151: error: Incompatible return value type (got "list[JSON]", expected "list[dict[str, Any]]")  [return-value]
core/supabase_integration.py:175: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:175: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:175: note: Possible overload variants:
core/supabase_integration.py:175: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:175: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:175: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:176: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:176: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:176: note: Possible overload variants:
core/supabase_integration.py:176: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:176: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:176: error: Incompatible return value type (got "Any | int | float | Sequence[JSON] | Mapping[str, JSON]", expected "dict[str, str]")  [return-value]
core/supabase_integration.py:176: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:205: error: Argument 1 to "insert" of "SyncRequestBuilder" has incompatible type "dict[str, object]"; expected "JSON"  [arg-type]
core/supabase_integration.py:220: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:220: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:220: note: Possible overload variants:
core/supabase_integration.py:220: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:220: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:220: error: Item "None" of "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None" has no attribute "replace"  [union-attr]
core/supabase_integration.py:220: error: Item "int" of "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None" has no attribute "replace"  [union-attr]
core/supabase_integration.py:220: error: Item "float" of "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None" has no attribute "replace"  [union-attr]
core/supabase_integration.py:220: error: Item "Sequence[JSON]" of "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None" has no attribute "replace"  [union-attr]
core/supabase_integration.py:220: error: Item "Mapping[str, JSON]" of "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None" has no attribute "replace"  [union-attr]
core/supabase_integration.py:220: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:221: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:221: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:221: note: Possible overload variants:
core/supabase_integration.py:221: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:221: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:221: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:223: error: Incompatible return value type (got "dict[Any, Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None]", expected "dict[str, str]")  [return-value]
core/supabase_integration.py:251: error: Argument 1 to "insert" of "SyncRequestBuilder" has incompatible type "dict[str, object]"; expected "JSON"  [arg-type]
core/supabase_integration.py:265: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:265: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:265: note: Possible overload variants:
core/supabase_integration.py:265: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:265: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:265: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:267: error: Incompatible return value type (got "dict[Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None, Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None]", expected "dict[str, str]")  [return-value]
core/supabase_integration.py:305: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:305: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:305: note: Possible overload variants:
core/supabase_integration.py:305: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:305: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:305: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:306: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:306: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:306: note: Possible overload variants:
core/supabase_integration.py:306: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:306: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:306: error: Generator has incompatible item type "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None"; expected "bool"  [misc]
core/supabase_integration.py:306: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:307: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:307: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:307: note: Possible overload variants:
core/supabase_integration.py:307: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:307: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:307: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:308: error: Argument 1 to "_get_most_frequent" of "SupabaseClient" has incompatible type "list[JSON]"; expected "list[dict[Any, Any]]"  [arg-type]
core/supabase_integration.py:309: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/supabase_integration.py:309: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/supabase_integration.py:309: note: Possible overload variants:
core/supabase_integration.py:309: note:     def __getitem__(self, int, /) -> JSON
core/supabase_integration.py:309: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/supabase_integration.py:309: error: Generator has incompatible item type "Any | int | float | Sequence[JSON] | Mapping[str, JSON] | None"; expected "bool"  [misc]
core/supabase_integration.py:309: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/supabase_integration.py:317: error: Missing type parameters for generic type "Dict"  [type-arg]
core/supabase_integration.py:324: error: Returning Any from function declared to return "str"  [no-any-return]
core/supabase_integration.py:407: error: Call to untyped function "SupabaseClient" in typed context  [no-untyped-call]
core/streaming_pipeline.py:10: error: Module "core.content_generation" has no attribute "generate_image_prompts"  [attr-defined]
core/streaming_pipeline.py:10: error: Module "core.content_generation" has no attribute "editor_critique"  [attr-defined]
core/streaming_pipeline.py:14: error: Cannot find implementation or library stub for module named "core.research_enrichment"  [import-not-found]
core/streaming_pipeline.py:14: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
core/streaming_pipeline.py:29: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_pipeline.py:29: note: Use "-> None" if function does not return a value
core/streaming_pipeline.py:30: error: Call to untyped function "reset_pipeline" in typed context  [no-untyped-call]
core/streaming_pipeline.py:32: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_pipeline.py:32: note: Use "-> None" if function does not return a value
core/streaming_pipeline.py:40: error: Function is missing a type annotation  [no-untyped-def]
core/streaming_pipeline.py:42: error: Call to untyped function "reset_pipeline" in typed context  [no-untyped-call]
core/streaming_pipeline.py:65: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_pipeline.py:115: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:117: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:121: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:123: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:125: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:127: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:129: error: Incompatible types in assignment (expression has type "str", variable has type "dict[str, Any]")  [assignment]
core/streaming_pipeline.py:169: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/streaming_pipeline.py:186: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/streaming_pipeline.py:193: error: Call to untyped function "FileUploadManager" in typed context  [no-untyped-call]
core/streaming_pipeline.py:216: error: Returning Any from function declared to return "str"  [no-any-return]
core/streaming_pipeline.py:225: error: Too many arguments for "generate_wisdom"  [call-arg]
core/streaming_pipeline.py:256: error: Too many arguments for "generate_wisdom"  [call-arg]
core/streaming_pipeline.py:287: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
core/streaming_pipeline.py:298: error: Too many arguments for "generate_outline"  [call-arg]
core/streaming_pipeline.py:329: error: Too many arguments for "generate_outline"  [call-arg]
core/streaming_pipeline.py:352: error: Too many arguments for "generate_article"  [call-arg]
core/streaming_pipeline.py:383: error: Too many arguments for "generate_article"  [call-arg]
core/streaming_pipeline.py:405: error: Too many arguments for "generate_social_content"  [call-arg]
core/streaming_pipeline.py:436: error: Too many arguments for "generate_social_content"  [call-arg]
core/streaming_pipeline.py:467: error: Returning Any from function declared to return "str"  [no-any-return]
core/streaming_pipeline.py:494: error: Value of type "bool | str | int | float | Sequence[JSON] | Mapping[str, JSON] | None" is not indexable  [index]
core/streaming_pipeline.py:494: error: No overload variant of "__getitem__" of "Sequence" matches argument type "str"  [call-overload]
core/streaming_pipeline.py:494: note: Possible overload variants:
core/streaming_pipeline.py:494: note:     def __getitem__(self, int, /) -> JSON
core/streaming_pipeline.py:494: note:     def __getitem__(self, slice[Any, Any, Any], /) -> Sequence[JSON]
core/streaming_pipeline.py:494: error: Invalid index type "str" for "str"; expected type "SupportsIndex | slice[Any, Any, Any]"  [index]
core/streaming_pipeline.py:508: error: Returning Any from function declared to return "bool"  [no-any-return]
core/streaming_pipeline.py:519: error: Returning Any from function declared to return "int"  [no-any-return]
core/streaming_pipeline.py:528: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
core/streaming_pipeline.py:532: error: Returning Any from function declared to return "dict[str, str]"  [no-any-return]
core/streaming_pipeline.py:539: error: Call to untyped function "StreamingPipelineController" in typed context  [no-untyped-call]
core/streaming_pipeline.py:540: error: Returning Any from function declared to return "StreamingPipelineController"  [no-any-return]
core/auth_wrapper.py:21: error: Function is missing a return type annotation  [no-untyped-def]
core/auth_wrapper.py:21: note: Use "-> None" if function does not return a value
core/auth_wrapper.py:24: error: Call to untyped function "_init_supabase" in typed context  [no-untyped-call]
core/auth_wrapper.py:26: error: Function is missing a return type annotation  [no-untyped-def]
core/auth_wrapper.py:26: note: Use "-> None" if function does not return a value
core/auth_wrapper.py:41: error: Returning Any from function declared to return "str | None"  [no-any-return]
core/auth_wrapper.py:41: error: Call to untyped function "get_user_id" in typed context  [no-untyped-call]
core/auth_wrapper.py:45: error: Returning Any from function declared to return "str | None"  [no-any-return]
core/auth_wrapper.py:45: error: Call to untyped function "get_user_email" in typed context  [no-untyped-call]
core/auth_wrapper.py:170: error: Function is missing a return type annotation  [no-untyped-def]
core/auth_wrapper.py:205: error: Returning Any from function declared to return "dict[str, str]"  [no-any-return]
core/auth_wrapper.py:241: error: Returning Any from function declared to return "dict[str, str]"  [no-any-return]
core/auth_wrapper.py:283: error: Returning Any from function declared to return "bool"  [no-any-return]
core/auth_wrapper.py:303: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
core/auth_wrapper.py:303: error: Call to untyped function "get_session_info" in typed context  [no-untyped-call]
core/auth_wrapper.py:313: error: Call to untyped function "AuthWrapper" in typed context  [no-untyped-call]
core/streaming_results.py:72: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:72: note: Use "-> None" if function does not return a value
core/streaming_results.py:80: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:80: note: Use "-> None" if function does not return a value
core/streaming_results.py:95: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:95: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
core/streaming_results.py:129: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:208: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:265: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:288: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:288: note: Use "-> None" if function does not return a value
core/streaming_results.py:438: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:587: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:794: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:794: note: Use "-> None" if function does not return a value
core/streaming_results.py:883: error: Call to untyped function "render_thinking_stream" in typed context  [no-untyped-call]
core/streaming_results.py:883: error: Too many arguments for "render_thinking_stream"  [call-arg]
core/streaming_results.py:993: error: Function is missing a return type annotation  [no-untyped-def]
core/streaming_results.py:993: note: Use "-> None" if function does not return a value
core/streaming_results.py:995: error: Call to untyped function "show_enhanced_streaming_status" in typed context  [no-untyped-call]
Found 264 errors in 16 files (checked 18 source files)
```

### Bandit
Exit code: 1

```
/root/.pyenv/versions/3.10.19/bin/python: No module named bandit
```


## Secrets Scan

**Status:** ❌ Potential hard-coded secrets found

- tests/test_basic_functionality.py: `password          password = "test_password_123"     hashed = hash`


## Risky API Scan

### Counts
- `exec`: 56
- `subprocess.run(`: 4
- `eval`: 1

### Sample locations
- app_simple.py: `exec`
- app_simple.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/auth_wrapper.py: `exec`
- core/file_upload.py: `exec`
- core/file_upload.py: `exec`
- core/file_upload.py: `subprocess.run(`
- core/file_upload.py: `subprocess.run(`
- core/file_upload.py: `subprocess.run(`
- core/file_upload.py: `exec`
- core/file_upload.py: `exec`
- core/monitoring.py: `exec`
- core/streaming_pipeline.py: `exec`
- core/streaming_pipeline.py: `exec`
- core/supabase_integration.py: `exec`
- core/supabase_integration.py: `exec`
- core/supabase_integration.py: `exec`
- core/supabase_integration.py: `exec`
- core/supabase_integration.py: `exec`


## Dependency Freshness

Outdated packages:
- black 25.12.0 → 26.3.1
- cachetools 6.2.6 → 7.0.6
- click 8.3.1 → 8.3.2
- isort 7.0.0 → 8.0.1
- librt 0.7.7 → 0.9.0
- mypy 1.19.1 → 1.20.2
- packaging 25.0 → 26.1
- pathspec 1.0.3 → 1.0.4
- pip 25.3 → 26.0.1
- platformdirs 4.5.1 → 4.9.6
- Pygments 2.19.2 → 2.20.0
- pytest 9.0.2 → 9.0.3
- pytokens 0.3.0 → 0.4.1
- rich 14.3.4 → 15.0.0
- ruff 0.14.11 → 0.15.11
- setuptools 79.0.1 → 82.0.1
- tomli 2.4.0 → 2.4.1
- websockets 15.0.1 → 16.0


## TODO / FIXME Tally

Total TODO/FIXME markers: **6**

- scripts/audit_project.py: 6
