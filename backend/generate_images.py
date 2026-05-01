import json
import os
import sys
import base64
import ssl
from urllib import request, error

def get_api_key():
    """Get the Gemini API key from environment variable or .env file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=")[1].strip().strip("'").strip('"')
                    break
    return api_key

def generate_image(prompt, aspect_ratio="16:9"):
    """Call the Nano Banana 2 API to generate an image."""
    api_key = get_api_key()
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY environment variable not set.")
        return None

    # Based on the listModels output, this is the correct model and method
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    context = ssl._create_unverified_context()
    
    print(f"🚀 Sending request to Nano Banana 2 (gemini-3.1-flash-image-preview)...")
    
    try:
        with request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            try:
                # In generateContent, images are usually returned in inlineData
                image_part = result['candidates'][0]['content']['parts'][0]
                if 'inlineData' in image_part:
                    return image_part['inlineData']['data']
                elif 'inline_data' in image_part:
                    return image_part['inline_data']['data']
                
                print("❌ Error: Image data not found in response parts.")
                print(f"Response Structure: {json.dumps(result, indent=2)}")
                return None
            except (KeyError, IndexError):
                print("❌ Error: Could not parse response candidates.")
                print(f"Response: {json.dumps(result, indent=2)}")
                return None
                
    except error.HTTPError as e:
        print(f"❌ API Request failed with status {e.code}")
        err_msg = e.read().decode('utf-8')
        print(f"Details: {err_msg}")
    except error.URLError as e:
        print(f"❌ Connection failed: {e}")
            
    return None

def main():
    # Load prompts
    prompts_file = "generated_prompts.json"
    if not os.path.exists(prompts_file):
        print(f"❌ Error: {prompts_file} not found. Run generate_prompts.py first.")
        return

    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading {prompts_file}: {e}")
        return

    # Find the latest image prompt
    image_prompts = [entry for entry in data if "(Image Prompt)" in entry['title']]
    if not image_prompts:
        print("❌ No image prompts found in generated_prompts.json.")
        return

    latest_prompt = image_prompts[-1]
    print(f"\n🎨 Generating banner for: {latest_prompt['title']}")
    
    # Generate the image
    img_b64 = generate_image(latest_prompt['prompt'])
    
    if img_b64:
        output_dir = "banners"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        safe_title = "".join([c for c in latest_prompt['title'] if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = f"{output_dir}/{safe_title.replace(' ', '_')}.png"
        
        try:
            with open(filename, "wb") as f:
                f.write(base64.b64decode(img_b64))
            print(f"\n✅ SUCCESS! Banner saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
    else:
        print("\n❌ Failed to generate image.")

if __name__ == "__main__":
    main()
