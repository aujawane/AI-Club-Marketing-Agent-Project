import json
import os
import urllib.parse
import ssl
import io
from urllib import request, error
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    """Try to find a good font on macOS."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def overlay_text(image_bytes, title):
    """Overlays the title text professionally on the image."""
    img = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Calculate font size (1/12th of width)
    font_size = int(width / 15)
    font = get_font(font_size)
    
    # Word wrap the title if it's too long
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        # Check width of current line
        w = draw.textlength(" ".join(current_line), font=font)
        if w > width * 0.8:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    # Calculate total height of text block
    line_height = font_size * 1.2
    total_text_height = len(lines) * line_height
    
    # Draw a semi-transparent dark overlay for better readability
    overlay_h = total_text_height + 40
    overlay = Image.new('RGBA', (width, int(overlay_h)), (0, 0, 0, 100))
    img.paste(overlay, (0, int((height - overlay_h) / 2)), overlay)
    
    # Draw the text line by line
    y_text = (height - total_text_height) / 2
    for line in lines:
        w = draw.textlength(line, font=font)
        # Draw white text
        draw.text(((width - w) / 2, y_text), line, font=font, fill="white")
        y_text += line_height
        
    # Final cleanup: convert back to RGB for saving as JPG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='JPEG', quality=95)
    return byte_arr.getvalue()

def generate_image_free(prompt, width=1280, height=720):
    """
    Uses Pollinations.ai to generate a CLEAN background.
    """
    # Clean background prompt (explicitly NO TEXT for the AI part)
    visual_prompt = f"{prompt}, artistic background, high quality, no text, no words, clean composition."
    encoded_prompt = urllib.parse.quote(visual_prompt)
    
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed=456"
    
    context = ssl._create_unverified_context()
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        print(f"🚀 Generating artistic background...")
        response = request.urlopen(req, context=context)
        return response.read()
    except error.URLError as e:
        print(f"❌ Failed to connect to image service: {e}")
        return None

def main():
    prompts_file = "generated_prompts.json"
    if not os.path.exists(prompts_file):
        print(f"❌ Error: {prompts_file} not found.")
        return

    with open(prompts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    image_prompts = [entry for entry in data if "(Image Prompt)" in entry['title']]
    if not image_prompts: return

    latest_prompt = image_prompts[-1]
    display_title = latest_prompt['title'].replace(" (Image Prompt)", "")
    
    print(f"\n🎨 Creating Banner for: {display_title}")
    
    # 1. Get the background
    background_bytes = generate_image_free(latest_prompt['prompt'])
    
    if background_bytes:
        # 2. Overlay the perfect text
        print(f"✍️ Stamping perfect title: '{display_title}'")
        final_image = overlay_text(background_bytes, display_title)
        
        output_dir = "banners"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
            
        safe_title = "".join([c for c in display_title if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = f"{output_dir}/{safe_title.replace(' ', '_')}_pro.jpg"
        
        with open(filename, "wb") as f:
            f.write(final_image)
        print(f"\n✅ SUCCESS! Professional banner saved to: {filename}")
    else:
        print("\n❌ Failed to generate background.")

if __name__ == "__main__":
    main()
