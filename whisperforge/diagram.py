import streamlit as st
import os
import json
import time
import requests
import io
import logging
import base64
import re
from PIL import Image
from pathlib import Path
import textwrap

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Diagram Generator",
    page_icon="🖼️",
    layout="wide"
)

# Apply custom CSS
def load_css():
    with open('static/css/diagram.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Add scanner line animation
    st.markdown('<div class="scanner-line"></div>', unsafe_allow_html=True)

def test_api_key(api_key):
    """Test the API key with a simple request"""
    if not api_key:
        return False, "API key is missing"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Simple test prompt with minimal size
    test_payload = {
        "model": "gpt-image-1",
        "prompt": "A simple test image of a circle",
        "size": "1024x1024",
        "quality": "standard",
        "n": 1
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=test_payload
        )
        
        if response.status_code == 200:
            return True, "API key is valid"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Error testing API key: {str(e)}"

def clean_prompt(prompt):
    """Minimal cleaning to ensure the prompt is safe for API usage
    without losing the original intent and style"""
    # Replace non-standard quotes with standard ones
    prompt = prompt.replace('"', '"').replace('"', '"')
    prompt = prompt.replace(''', "'").replace(''', "'")
    
    return prompt

def extract_diagram_description(prompt):
    """Extract the diagram description from a prompt that follows the pattern:
    create this diagram "DESCRIPTION" """
    match = re.search(r'create this diagram ["\'](.*?)["\']', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return prompt

def generate_and_save_image(api_key, prompt, size, quality, format_type, background=None):
    """Generate an image using OpenAI GPT Image API"""
    try:
        # Clean the prompt minimally to ensure API compatibility
        prompt = clean_prompt(prompt)

        # Set up API parameters
        params = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1  # Just one image
        }
        
        # Add background parameter only if it's provided and not None
        if background is not None and background != "#FFFFFF":
            params["background"] = "transparent" if background.lower() == "transparent" else background
        
        # Print parameters for debugging
        logger.info(f"API Parameters: {json.dumps({k: v for k, v in params.items() if k != 'prompt'})}")
        logger.info(f"Prompt: {prompt[:100]}...")
        
        # Set up headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Make the API request
        with st.status("🔄 Sending request to OpenAI...", expanded=True) as status:
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=params
            )
            
            # Check if the request was successful
            if response.status_code != 200:
                status.update(label=f"❌ API Error: {response.status_code}", state="error")
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None, None
            
            # Parse the response
            data = response.json()
            
            # Debug log the response structure
            logger.info(f"Response structure: {json.dumps(data)}")
            
            # Check if there's image data
            if "data" not in data or not data["data"]:
                status.update(label=f"❌ No image data in response", state="error")
                st.error(f"No image data in response: {data}")
                return None, None
            
            # GPT Image returns base64 data by default
            image_data = None
            
            # Check for base64 data (standard response format for gpt-image-1)
            if "b64_json" in data["data"][0]:
                status.update(label="💾 Processing base64 image data...", state="running")
                
                try:
                    # Decode the base64 data
                    b64_data = data["data"][0]["b64_json"]
                    image_data = base64.b64decode(b64_data)
                except Exception as e:
                    status.update(label=f"❌ Error decoding base64 image", state="error")
                    st.error(f"Error decoding base64 image: {str(e)}")
                    logger.error(f"Error decoding base64: {str(e)}", exc_info=True)
                    return None, None
            
            # If data was returned as a URL instead (fallback)
            elif "url" in data["data"][0]:
                image_url = data["data"][0]["url"]
                status.update(label="📥 Downloading image from URL...", state="running")
                
                # Download the image
                img_response = requests.get(image_url)
                if img_response.status_code != 200:
                    status.update(label=f"❌ Failed to download image: {img_response.status_code}", state="error")
                    st.error(f"Failed to download image: {img_response.status_code}")
                    return None, None
                
                image_data = img_response.content
            
            # If no image data was found
            if not image_data:
                status.update(label="❌ No image data found in response", state="error")
                st.error("No image data found in response")
                return None, None
            
            try:
                # Load the image
                image = Image.open(io.BytesIO(image_data))
                
                # Save the image
                output_dir = Path("generated_images")
                output_dir.mkdir(exist_ok=True)
                
                # Create a more descriptive filename based on diagram title
                # Extract a title from the prompt if possible
                title_match = re.search(r'"([^"]+)"', prompt)
                if title_match:
                    title = title_match.group(1)
                    # Get first few words for filename
                    title_words = title.split()[:3]
                    file_prefix = "_".join(title_words).replace(" ", "_")
                else:
                    file_prefix = "diagram"
                    
                # Clean the file prefix
                file_prefix = re.sub(r'[^\w\s-]', '', file_prefix).strip().lower()
                file_prefix = re.sub(r'[-\s]+', '_', file_prefix)
                
                timestamp = int(time.time())
                filename = f"{file_prefix}_{timestamp}.{format_type}"
                filepath = output_dir / filename
                abs_filepath = os.path.abspath(filepath)
                
                # Save in the requested format
                image.save(filepath)
                status.update(label=f"✅ Image saved to {filename}", state="complete")
                
                return image, abs_filepath
                
            except Exception as e:
                status.update(label=f"❌ Error processing image: {str(e)}", state="error")
                st.error(f"Error processing image: {str(e)}")
                logger.error(f"Error processing image: {str(e)}", exc_info=True)
                return None, None
    
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return None, None

def read_file_content(uploaded_file):
    """Read content from an uploaded file"""
    try:
        if uploaded_file is None:
            return None
            
        # Read the file
        content = uploaded_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # Reset the file pointer so it can be read again
        uploaded_file.seek(0)
            
        return content
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        logger.error(f"Error reading file: {str(e)}", exc_info=True)
        return None

def process_prompts(api_key, prompts, style_guide=None, size="1024x1024", quality="standard", format_type="png", background=None):
    """Process multiple prompts with optional style guide"""
    if not prompts:
        st.error("No prompts provided")
        return
    
    # Log the received prompts for debugging
    logger.info(f"Received prompts (type: {type(prompts)}): {prompts[:100]}...")
        
    # Convert to list if it's a string
    if isinstance(prompts, str):
        prompts = [line.strip() for line in prompts.split('\n') if line.strip()]
        
    # Filter out markdown code blocks and empty lines
    cleaned_prompts = []
    for prompt in prompts:
        if not prompt.strip():
            continue
        if prompt.strip().startswith('```') and prompt.strip().endswith('```'):
            continue
        if prompt.strip().startswith('```'):
            continue
        cleaned_prompts.append(prompt)
    
    if not cleaned_prompts:
        st.error("No valid prompts found after filtering")
        return
        
    st.write(f"Processing {len(cleaned_prompts)} prompts...")
    
    # Create a progress bar
    progress_bar = st.progress(0, text="Processing prompts...")
    
    # Status text at top 
    status_text = st.empty()
    
    # Results container
    results_container = st.container()
    
    success_count = 0
    
    # Process each prompt
    with results_container:
        st.subheader("Generated Images")
        
        for i, prompt in enumerate(cleaned_prompts):
            # Update progress
            progress = i / len(cleaned_prompts)
            progress_bar.progress(progress, text=f"Processing prompt {i+1} of {len(cleaned_prompts)}")
            
            # Update status
            status_text.info(f"Processing prompt {i+1}/{len(cleaned_prompts)}: {prompt[:50]}..." + ("..." if len(prompt) > 50 else ""))
            
            # Create a container for this prompt
            with st.container():
                # Extract the diagram description if it follows the pattern
                diagram_desc = extract_diagram_description(prompt)
                
                st.markdown(f"#### Diagram {i+1}:")
                st.markdown(f"```\n{diagram_desc}\n```")
                
                # Format the combined prompt properly for diagram generation
                if style_guide:
                    # Keep the original style guide without truncation
                    # Simply combine with the diagram description in a natural way
                    combined_prompt = f"{diagram_desc} - Style guide: {style_guide}"
                else:
                    combined_prompt = diagram_desc
                
                # Show the combined prompt
                with st.expander("View prompt sent to API"):
                    st.text_area("Complete prompt", combined_prompt, height=150, disabled=True)
                
                # Generate the image
                image, filepath = generate_and_save_image(
                    api_key=api_key,
                    prompt=combined_prompt,
                    size=size, 
                    quality=quality, 
                    format_type=format_type,
                    background=background
                )
                
                if image and filepath:
                    success_count += 1
                    
                    # Display the image and its information
                    st.image(image, caption=f"Generated diagram for prompt {i+1}", use_container_width=True)
                    st.code(f"Saved to: {filepath}", language="bash")
                    st.markdown("---")  # Add a separator between images
                else:
                    st.error(f"Failed to generate image for prompt {i+1}")
                    st.markdown("---")  # Add a separator even for failures
            
            # Add a small delay to avoid rate limits
            if i < len(cleaned_prompts) - 1:
                time.sleep(1)
    
    # Complete the progress bar
    progress_bar.progress(1.0, text="Processing complete!")
    
    # Update final status
    if success_count > 0:
        st.success(f"Completed: {success_count} of {len(cleaned_prompts)} images generated successfully")
    else:
        st.error("Failed to generate any images. Please check the error messages above.")
    
    return success_count

def main():
    # Initialize session state for tracking count
    if 'success_count' not in st.session_state:
        st.session_state.success_count = 0
    
    # Try to load custom CSS
    try:
        load_css()
    except Exception as e:
        logger.warning(f"Failed to load custom CSS: {e}")
    
    # Header with animation effect
    st.markdown(
        """
        <div class="header-container">
            <h1>Diagram Generator</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # API Key input with validation
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key here. It will not be stored.")
        
        if st.button("Test API Key"):
            with st.spinner("Testing API key..."):
                is_valid, message = test_api_key(api_key)
            
            if is_valid:
                st.success(message)
            else:
                st.error(message)
        
        st.markdown("---")
        st.markdown("## 🎨 Image Parameters")
        
        # Image parameters in sidebar for cleaner interface
        size = st.selectbox("Size", ["1024x1024", "1536x1024", "1024x1536"], index=0)
        quality = st.selectbox("Quality", ["standard", "high", "medium", "low"], index=0, 
                               help="Standard quality is fastest, high quality looks best but costs more tokens")
        format_type = st.selectbox("Format", ["png", "jpeg", "webp"], index=0)
        
        # Background option
        background_options = ["white", "transparent"]
        background = st.selectbox("Background", background_options, index=0,
                                 help="Transparent background only works with PNG and WebP formats")
        bg_param = background if background != "white" else None
    
    # Create a radio button to select the mode instead of tabs
    mode = st.radio("Select Mode", ["Single Prompt", "Multiple Prompts"], horizontal=True)
    
    if mode == "Single Prompt":
        # Single prompt mode
        st.markdown("## ✨ Single Prompt Mode")
        prompt = st.text_area("Enter your diagram prompt:", 
                       placeholder="A detailed diagram of...",
                       height=150)
    
        # Style guide input (optional)
        style_text = st.text_area("Style guide (optional):", 
                            placeholder="Describe the style...",
                            height=100)
        
        # Generate button
        if st.button("💫 Generate Diagram", type="primary"):
            if not api_key:
                st.error("Please enter your OpenAI API key.")
                return
                
            if not prompt:
                st.error("Please enter a prompt.")
                return
                
            # Extract diagram description if it follows the pattern
            diagram_desc = extract_diagram_description(prompt)
            
            # Format the combined prompt properly
            if style_text:
                combined_prompt = f"{diagram_desc} - Style guide: {style_text}"
                # Show the combined prompt
                with st.expander("View prompt sent to API"):
                    st.text_area("Complete prompt", combined_prompt, height=150, disabled=True)
            else:
                combined_prompt = diagram_desc
                
            with st.container():
                # Generate a single image
                image, filepath = generate_and_save_image(
                    api_key=api_key,
                    prompt=combined_prompt,
                    size=size, 
                    quality=quality, 
                    format_type=format_type,
                    background=bg_param
                )
            
            # Display the result
            if image:
                st.session_state.success_count += 1
                st.success(f"✅ Image generated successfully")
                st.image(image, caption="Generated Image", use_container_width=True)
                st.code(f"Saved to: {filepath}", language="bash")
            else:
                st.error("Failed to generate image. Check the error messages above.")
    
    else:
        # Multiple prompts mode
        st.markdown("## 📑 Multiple Prompts Mode")
        st.info("Upload a text file containing diagram descriptions. Each prompt should be on a new line or paragraph.")
        
        prompts_file = st.file_uploader("Upload Prompts File", type=["txt", "md"], key="prompts_file")
        style_file = st.file_uploader("Upload Style Guide (optional)", type=["txt", "md"], key="style_file")
        
        # Store file contents
        prompts_content = None
        style_content = None
        
        # Read file contents if files are uploaded
        if prompts_file is not None:
            prompts_content = read_file_content(prompts_file)
            if prompts_content:
                # Preview prompts
                with st.expander("📝 Preview Prompts", expanded=False):
                    st.text_area("Prompts Content", prompts_content, height=150, disabled=True)
        
        if style_file is not None:
            style_content = read_file_content(style_file)
            if style_content:
                # Preview style guide
                with st.expander("🎨 Preview Style Guide", expanded=False):
                    st.text_area("Style Guide Content", style_content, height=150, disabled=True)
        
        # Generate button for file processing
        if st.button("🚀 Generate Diagrams From File", type="primary"):
            if not api_key:
                st.error("Please enter your OpenAI API key.")
                return
            
            if not prompts_file:
                st.error("Please upload a prompts file.")
                return
            
            # Verify we have content
            if not prompts_content:
                st.error("Could not read prompts file. Please upload it again.")
                # Log the error for debugging
                logger.error(f"Failed to read prompts file. File object: {prompts_file}")
                return
            
            # Process all prompts
            success_count = process_prompts(
                api_key=api_key,
                prompts=prompts_content,
                style_guide=style_content,
                size=size, 
                quality=quality, 
                format_type=format_type,
                background=bg_param
            )
            
            if success_count:
                st.session_state.success_count += success_count
    
    # Output directory information
    output_dir = os.path.abspath("generated_images")
    
    # Footer with information
    st.markdown("---")
    st.markdown(
        """
        <div class="app-footer">
            <p>Generated images are saved to <code>{output_dir}</code>. Successfully generated: {count} images.</p>
        </div>
        """.format(output_dir=output_dir, count=st.session_state.success_count),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 