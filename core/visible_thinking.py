"""
Visible Thinking Module for WhisperForge
Provides chat-bubble persona stream during pipeline processing
"""

import streamlit as st
import time
import logging
import uuid
from typing import Dict, List, Any, Optional
from .utils import get_openai_client
try:
    from .monitoring import track_token_usage
except ImportError:
    # Fallback if monitoring doesn't have token tracking
    def track_token_usage(operation: str, total_tokens: int, prompt_tokens: int, completion_tokens: int):
        logger.info(f"Token usage - {operation}: {total_tokens} total ({prompt_tokens} prompt + {completion_tokens} completion)")

logger = logging.getLogger(__name__)

class ThoughtBubble:
    """Represents a single thought bubble in the stream"""
    
    def __init__(self, text: str, mood: str = "info", emoji: str = "🧠", timestamp: float = None):
        self.text = text
        self.mood = mood  # info, success, error, warning
        self.emoji = emoji
        self.timestamp = timestamp or time.time()
        self.id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "mood": self.mood,
            "emoji": self.emoji,
            "timestamp": self.timestamp
        }

class VisibleThinking:
    """Handles the visible thinking chat bubble stream"""
    
    # Persona configuration
    PERSONA_NAME = "Kris"
    MAX_BUBBLE_LENGTH = 90
    MAX_VISIBLE_BUBBLES = 3
    BUBBLE_INTERVAL = 2.0  # seconds between bubbles
    
    # Mood to emoji mapping
    MOOD_EMOJIS = {
        "info": "🧠",
        "success": "✅", 
        "discovery": "✨",
        "processing": "⚡",
        "error": "🚨",
        "warning": "⚠️"
    }
    
    # Aurora color mapping for moods
    MOOD_COLORS = {
        "info": "var(--aurora-primary)",      # Aurora Cyan
        "success": "var(--aurora-secondary)", # Spring Green
        "discovery": "var(--aurora-tertiary)", # Cosmic Purple
        "processing": "var(--aurora-primary)", # Aurora Cyan
        "error": "#FF6B6B",                   # Coral
        "warning": "#FFB347"                  # Orange
    }
    
    def __init__(self):
        self.enabled = True
        self.thoughts_cache = []
        self.last_bubble_time = 0
        
        # Initialize session state for bubbles
        if "thinking_bubbles" not in st.session_state:
            st.session_state.thinking_bubbles = []
        
        if "thinking_enabled" not in st.session_state:
            st.session_state.thinking_enabled = True
    
    def is_enabled(self) -> bool:
        """Check if visible thinking is enabled"""
        return st.session_state.get("thinking_enabled", True) and self.enabled
    
    def should_add_bubble(self) -> bool:
        """Check if enough time has passed to add a new bubble"""
        current_time = time.time()
        return (current_time - self.last_bubble_time) >= self.BUBBLE_INTERVAL
    
    def add_thought(self, text: str, mood: str = "info", emoji: str = None, force: bool = False) -> None:
        """Add a thought bubble to the stream"""
        
        if not self.is_enabled():
            return
        
        if not force and not self.should_add_bubble():
            return
        
        # Truncate text if too long
        if len(text) > self.MAX_BUBBLE_LENGTH:
            text = text[:self.MAX_BUBBLE_LENGTH - 3] + "..."
        
        # Use mood-appropriate emoji if not specified
        if emoji is None:
            emoji = self.MOOD_EMOJIS.get(mood, "🧠")
        
        # Create bubble
        bubble = ThoughtBubble(text, mood, emoji)
        
        # Add to session state
        st.session_state.thinking_bubbles.append(bubble.to_dict())
        
        # Keep only recent bubbles
        if len(st.session_state.thinking_bubbles) > self.MAX_VISIBLE_BUBBLES:
            st.session_state.thinking_bubbles = st.session_state.thinking_bubbles[-self.MAX_VISIBLE_BUBBLES:]
        
        self.last_bubble_time = time.time()
        
        logger.debug(f"Added thought bubble: {text[:50]}...")
    
    def generate_dynamic_thought(self, step_name: str, context: str = "", ai_model: str = "gpt-3.5-turbo") -> Optional[str]:
        """Generate a dynamic thought using AI"""
        
        if not self.is_enabled():
            return None
        
        try:
            # Prepare persona prompt
            persona_prompt = f"""You are {self.PERSONA_NAME}, a friendly AI assistant working inside WhisperForge. 
Generate ONE short, witty thought bubble (max {self.MAX_BUBBLE_LENGTH} characters) about starting the "{step_name}" process.

Personality guidelines:
- Hopeful and encouraging, never snarky
- Speak like a knowledgeable friend
- Use casual, warm language
- ONE emoji max from: 🧠✨⚡✅🚨
- Avoid technical jargon like "LLM" or "tokens"
- Keep it under {self.MAX_BUBBLE_LENGTH} characters

Context: {context or 'Starting processing step'}

Examples of good thoughts:
"🧠 Diving into your audio - this sounds interesting!"
"⚡ Scanning for golden insights in your content..."
"✨ Time to transform ideas into structured magic!"

Generate exactly one thought bubble:"""

            client = get_openai_client()
            if not client:
                return None
            
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": persona_prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            # Track minimal token usage
            usage = response.usage
            track_token_usage("visible_thinking", usage.total_tokens, usage.prompt_tokens, usage.completion_tokens)
            
            thought = response.choices[0].message.content.strip()
            
            # Clean up the response
            thought = thought.replace('"', '').replace("'", "").strip()
            
            # Ensure length limit
            if len(thought) > self.MAX_BUBBLE_LENGTH:
                thought = thought[:self.MAX_BUBBLE_LENGTH - 3] + "..."
            
            return thought
            
        except Exception as e:
            logger.error(f"Error generating dynamic thought for {step_name}: {e}")
            return None
    
    def add_step_start_thought(self, step_name: str, context: str = "", use_ai: bool = True) -> None:
        """Add a thought when a pipeline step starts"""
        
        if not self.is_enabled():
            return
        
        # Try AI-generated thought first
        if use_ai:
            dynamic_thought = self.generate_dynamic_thought(step_name, context)
            if dynamic_thought:
                self.add_thought(dynamic_thought, "processing")
                return
        
        # Fallback to canned thoughts
        canned_thoughts = {
            "upload_validation": "🧠 Checking your file - making sure everything's perfect!",
            "transcription": "⚡ Converting speech to text - listening carefully...",
            "wisdom_extraction": "✨ Mining for golden insights in your content!",
            "research_enrichment": "🧠 Hunting for brilliant supporting links...",
            "outline_creation": "⚡ Crafting the perfect structure for your ideas!",
            "article_creation": "✨ Weaving your insights into compelling prose!",
            "social_content": "🧠 Creating shareable social media magic!",
            "image_prompts": "⚡ Visualizing your concepts for stunning imagery!",
            "database_storage": "✅ Preserving your content masterpiece!"
        }
        
        thought = canned_thoughts.get(step_name, f"🧠 Working on {step_name.replace('_', ' ')}...")
        self.add_thought(thought, "processing")
    
    def add_step_complete_thought(self, step_name: str, result_info: str = "") -> None:
        """Add a thought when a pipeline step completes"""
        
        if not self.is_enabled():
            return
        
        canned_completions = {
            "upload_validation": "✅ File validated - ready to work!",
            "transcription": "✅ Transcript ready - captured every word!",
            "wisdom_extraction": "✅ Key insights extracted - pure gold!",
            "research_enrichment": "✅ Research links gathered - knowledge enhanced!",
            "outline_creation": "✅ Structure complete - ready to build!",
            "article_creation": "✅ Article crafted - your ideas shine!",
            "social_content": "✅ Social posts ready - time to share!",
            "image_prompts": "✅ Visual concepts captured perfectly!",
            "database_storage": "✅ Everything saved - your content is secure!"
        }
        
        thought = canned_completions.get(step_name, f"✅ {step_name.replace('_', ' ').title()} complete!")
        
        # Add result info if provided
        if result_info and len(thought + result_info) <= self.MAX_BUBBLE_LENGTH:
            thought = f"{thought} {result_info}"
        
        self.add_thought(thought, "success")
    
    def add_error_thought(self, step_name: str, error_msg: str = "") -> None:
        """Add a thought when an error occurs"""
        
        if not self.is_enabled():
            return
        
        error_thoughts = [
            "🚨 Oops, hit a snag - let me try a different approach...",
            "🚨 Technical hiccup - working on a solution...", 
            "🚨 Unexpected challenge - regrouping and retrying..."
        ]
        
        import random
        thought = random.choice(error_thoughts)
        self.add_thought(thought, "error")
    
    def render_bubble_stream(self, container=None) -> None:
        """Render the chat bubble stream with Aurora styling"""
        
        if not self.is_enabled():
            return
        
        bubbles = st.session_state.get("thinking_bubbles", [])
        
        if not bubbles:
            return
        
        # Use provided container or create one
        if container is None:
            container = st.container()
        
        with container:
            # Apply Aurora bubble styling
            st.markdown("""
            <style>
            .thinking-stream {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin: 8px 0;
                max-height: 180px;
                overflow-y: auto;
            }
            
            .thought-bubble {
                display: flex;
                align-items: center;
                padding: 8px 12px;
                border-radius: 16px;
                font-size: 0.9rem;
                opacity: 0;
                animation: bubble-appear 0.5s ease-out forwards;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(8px);
                max-width: 85%;
            }
            
            .thought-bubble.info {
                background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(0, 200, 200, 0.1));
                color: var(--aurora-primary, #00FFFF);
                border-color: rgba(0, 255, 255, 0.3);
            }
            
            .thought-bubble.success {
                background: linear-gradient(135deg, rgba(64, 224, 208, 0.15), rgba(50, 180, 160, 0.1));
                color: var(--aurora-secondary, #40E0D0);
                border-color: rgba(64, 224, 208, 0.3);
            }
            
            .thought-bubble.discovery {
                background: linear-gradient(135deg, rgba(147, 51, 234, 0.15), rgba(120, 40, 200, 0.1));
                color: var(--aurora-tertiary, #9333EA);
                border-color: rgba(147, 51, 234, 0.3);
            }
            
            .thought-bubble.error {
                background: linear-gradient(135deg, rgba(255, 107, 107, 0.15), rgba(255, 80, 80, 0.1));
                color: #FF6B6B;
                border-color: rgba(255, 107, 107, 0.3);
            }
            
            .thought-bubble.processing {
                background: linear-gradient(135deg, rgba(0, 255, 255, 0.15), rgba(0, 200, 200, 0.1));
                color: var(--aurora-primary, #00FFFF);
                border-color: rgba(0, 255, 255, 0.3);
                animation: bubble-pulse 2s ease-in-out infinite;
            }
            
            .bubble-emoji {
                margin-right: 6px;
                font-size: 1.1rem;
            }
            
            .bubble-text {
                flex: 1;
                line-height: 1.3;
            }
            
            @keyframes bubble-appear {
                from {
                    opacity: 0;
                    transform: translateY(10px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            
            @keyframes bubble-pulse {
                0%, 100% { 
                    border-color: rgba(0, 255, 255, 0.3);
                    box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.4);
                }
                50% { 
                    border-color: rgba(0, 255, 255, 0.6);
                    box-shadow: 0 0 0 4px rgba(0, 255, 255, 0.1);
                }
            }
            
            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .thinking-stream {
                    max-height: 120px;
                }
                
                .thought-bubble {
                    font-size: 0.8rem;
                    padding: 6px 10px;
                    max-width: 95%;
                }
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Render bubbles
            bubble_html = '<div class="thinking-stream">'
            
            for bubble in bubbles[-self.MAX_VISIBLE_BUBBLES:]:
                mood_class = bubble.get("mood", "info")
                emoji = bubble.get("emoji", "🧠")
                text = bubble.get("text", "")
                
                bubble_html += f'''
                <div class="thought-bubble {mood_class}">
                    <span class="bubble-emoji">{emoji}</span>
                    <span class="bubble-text">{text}</span>
                </div>
                '''
            
            bubble_html += '</div>'
            
            st.markdown(bubble_html, unsafe_allow_html=True)
    
    def clear_bubbles(self) -> None:
        """Clear all thought bubbles"""
        st.session_state.thinking_bubbles = []
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable visible thinking"""
        st.session_state.thinking_enabled = enabled
        self.enabled = enabled


# Global instance for easy access
visible_thinking = VisibleThinking()

def add_thought(text: str, mood: str = "info", emoji: str = None) -> None:
    """Quick function to add a thought bubble"""
    visible_thinking.add_thought(text, mood, emoji)

def render_thinking_stream(container=None) -> None:
    """Quick function to render the thinking stream"""
    visible_thinking.render_bubble_stream(container)

def thinking_step_start(step_name: str, context: str = "", use_ai: bool = True) -> None:
    """Quick function for step start thoughts"""
    visible_thinking.add_step_start_thought(step_name, context, use_ai)

def thinking_step_complete(step_name: str, result_info: str = "") -> None:
    """Quick function for step completion thoughts"""
    visible_thinking.add_step_complete_thought(step_name, result_info)

def thinking_error(step_name: str, error_msg: str = "") -> None:
    """Quick function for error thoughts"""
    visible_thinking.add_error_thought(step_name, error_msg) 