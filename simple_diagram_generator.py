import os
import json
import time
import requests
import argparse
import base64
from pathlib import Path
from PIL import Image
import io
import re

def clean_prompt(prompt, max_length=500):
    """Clean and truncate prompt to avoid request header size issues"""
    # Remove any markdown code blocks
    prompt = re.sub(r'```.*?```', '', prompt, flags=re.DOTALL)
    
    # Replace any non-ASCII characters
    prompt = prompt.encode('ascii', 'ignore').decode('ascii')
    
    # Replace quotes and special characters
    prompt = prompt.replace('"', "'").replace('\n', ' ')
    
    # Truncate if too long
    if len(prompt) > max_length:
        print(f"Warning: Truncating prompt from {len(prompt)} to {max_length} characters")
        prompt = prompt[:max_length]
    
    return prompt

def generate_image(api_key, prompt, style=None, size="1024x1024", quality="auto", output_dir="output_images"):
    """Generate an image using OpenAI's GPT Image API"""
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Combine style guide and prompt if style is provided
    if style:
        # For simplicity, just prepend a short instruction based on style
        # This avoids making requests too large
        combined_prompt = f"Using the style of {style[:50]}, create: {prompt}"
    else:
        combined_prompt = prompt
        
    # Clean and limit the prompt size
    final_prompt = clean_prompt(combined_prompt)
    print(f"\nProcessing prompt: '{final_prompt[:100]}...'")
    
    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-image-1",
        "prompt": final_prompt,
        "size": size,
        "quality": quality
    }
    
    # Make the request
    try:
        print(f"Sending request with size={size}, quality={quality}")
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
        
        # Get the image data from response
        data = response.json()
        if "data" not in data or not data["data"]:
            print(f"No data in response: {data}")
            return None
        
        # Check for URL or base64 data
        image_data = None
        
        # Check for URL in response
        if "url" in data["data"][0] and data["data"][0]["url"]:
            print("Found image URL in response")
            image_url = data["data"][0]["url"]
            
            # Download the image
            print(f"Downloading image from URL")
            img_response = requests.get(image_url)
            if img_response.status_code != 200:
                print(f"Failed to download image: {img_response.status_code}")
                return None
            
            # Get the image data from the response
            image_data = img_response.content
        
        # Check for base64 data
        elif "b64_json" in data["data"][0] and data["data"][0]["b64_json"]:
            print("Found base64 encoded image in response")
            try:
                # Decode the base64 data
                b64_data = data["data"][0]["b64_json"]
                image_data = base64.b64decode(b64_data)
            except Exception as e:
                print(f"Error decoding base64 image: {str(e)}")
                return None
        
        # If no image data was found
        if not image_data:
            print("No image data found in response")
            return None
        
        # Save the image
        try:
            # Open the image data
            image = Image.open(io.BytesIO(image_data))
            
            # Create a unique filename
            safe_prompt = re.sub(r'[^\w\s]', '', prompt[:20]).strip().replace(' ', '_')
            timestamp = int(time.time())
            filename = f"{safe_prompt}_{timestamp}.png"
            filepath = output_path / filename
            
            # Save the image
            image.save(filepath)
            print(f"Image saved to {filepath}")
            
            return str(filepath)
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return None
    
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None

def process_prompts_file(api_key, prompts_file, style_file=None, size="1024x1024", quality="auto", output_dir="output_images"):
    """Process a file containing image prompts"""
    # Read prompts from file
    try:
        with open(prompts_file, 'r') as f:
            content = f.read()
        
        # Split into individual prompts
        prompts = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Remove any markdown code block delimiters
        cleaned_prompts = []
        for prompt in prompts:
            if prompt.startswith('```') and prompt.endswith('```'):
                continue
            if prompt.startswith('```'):
                continue
            cleaned_prompts.append(prompt)
        
        print(f"Found {len(cleaned_prompts)} prompts in file")
        
        # Read style guide if provided
        style_guide = None
        if style_file:
            try:
                with open(style_file, 'r') as f:
                    style_guide = f.read()
                print(f"Style guide loaded: {len(style_guide)} characters")
            except Exception as e:
                print(f"Error reading style guide: {str(e)}")
                style_guide = None
        
        # Process each prompt
        success_count = 0
        for i, prompt in enumerate(cleaned_prompts):
            print(f"\nProcessing prompt {i+1} of {len(cleaned_prompts)}")
            
            # Generate the image
            filepath = generate_image(
                api_key=api_key,
                prompt=prompt,
                style=style_guide,
                size=size,
                quality=quality,
                output_dir=output_dir
            )
            
            if filepath:
                success_count += 1
                print(f"Success! Image {i+1} saved to {filepath}")
            else:
                print(f"Failed to generate image for prompt {i+1}")
            
            # Add a delay to avoid rate limits
            if i < len(cleaned_prompts) - 1:
                print("Waiting 2 seconds before next request...")
                time.sleep(2)
        
        print(f"\nProcessing complete: {success_count} of {len(cleaned_prompts)} images generated successfully")
        return success_count
    
    except Exception as e:
        print(f"Error processing prompts file: {str(e)}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Generate images from text prompts using OpenAI's GPT Image API")
    parser.add_argument("--api-key", help="OpenAI API Key (or set OPENAI_API_KEY environment variable)")
    parser.add_argument("--prompts", required=True, help="Path to file containing prompts")
    parser.add_argument("--style", help="Path to style guide file (optional)")
    parser.add_argument("--size", default="1024x1024", choices=["1024x1024", "1536x1024", "1024x1536"], 
                        help="Image size (default: 1024x1024)")
    parser.add_argument("--quality", default="auto", choices=["low", "medium", "high", "auto"], 
                        help="Image quality (default: auto)")
    parser.add_argument("--output", default="output_images", help="Output directory for images")
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key is required. Provide it with --api-key or set OPENAI_API_KEY environment variable.")
        return
    
    # Process the prompts file
    process_prompts_file(
        api_key=api_key,
        prompts_file=args.prompts,
        style_file=args.style,
        size=args.size,
        quality=args.quality,
        output_dir=args.output
    )

if __name__ == "__main__":
    main() 