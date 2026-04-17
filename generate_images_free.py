import json
import os
import urllib.parse
import ssl
import io
from urllib import request, error
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    """Try to find a good font on macOS."""
    font_paths = []
    if bold:
        font_paths.extend([
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica-Bold.ttf",
            "/Library/Fonts/Arial Unicode.ttf"
        ])
    else:
        font_paths.extend([
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Unicode.ttf"
        ])
        
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def overlay_text(image_bytes, title, tagline=None):
    """Overlays the title and tagline professionally on the image."""
    img = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # --- TITLE ---
    title_font_size = int(width / 18)
    title_font = get_font(title_font_size, bold=True)
    
    # Word wrap title
    words = title.split()
    title_lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if draw.textlength(" ".join(current_line), font=title_font) > width * 0.7:
            title_lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    title_lines.append(" ".join(current_line))
    
    # --- TAGLINE ---
    tagline_lines = []
    tagline_font_size = int(width / 35)
    tagline_font = get_font(tagline_font_size, bold=False)
    
    if tagline:
        words = tagline.split()
        current_line = []
        for word in words:
            current_line.append(word)
            if draw.textlength(" ".join(current_line), font=tagline_font) > width * 0.7:
                tagline_lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        tagline_lines.append(" ".join(current_line))

    # --- CALCULATE HEIGHTS ---
    title_line_height = title_font_size * 1.2
    tagline_line_height = tagline_font_size * 1.3
    
    total_title_h = len(title_lines) * title_line_height
    total_tagline_h = (len(tagline_lines) * tagline_line_height) if tagline else 0
    
    spacing = title_font_size * 0.5 if tagline else 0
    content_h = total_title_h + spacing + total_tagline_h
    
    # --- DRAW OVERLAY ---
    padding = 60
    overlay_h = content_h + padding
    
    # Gradient overlay (darker at bottom)
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Just a centered rectangle for now, but more stylish
    rect_y0 = (height - overlay_h) // 2
    rect_y1 = rect_y0 + overlay_h
    overlay_draw.rectangle([0, rect_y0, width, rect_y1], fill=(0, 0, 0, 160))
    
    img.paste(overlay, (0, 0), overlay)
    
    # --- DRAW TEXT ---
    y_text = (height - content_h) // 2
    
    # Title
    for line in title_lines:
        w = draw.textlength(line, font=title_font)
        draw.text(((width - w) / 2, y_text), line, font=title_font, fill="white")
        y_text += title_line_height
        
    y_text += spacing
    
    # Tagline
    for line in tagline_lines:
        w = draw.textlength(line, font=tagline_font)
        # Slightly yellow/gold for tagline to differentiate
        draw.text(((width - w) / 2, y_text), line, font=tagline_font, fill=(255, 220, 100))
        y_text += tagline_line_height
        
    # Final cleanup
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

def find_tagline(title):
    """Find the tagline for a project in marketing_data.json."""
    if os.path.exists("marketing_data.json"):
        with open("marketing_data.json", "r") as f:
            data = json.load(f)
            for p in data.get("projects", []):
                if p["project_name"].lower() in title.lower() or title.lower() in p["project_name"].lower():
                    return p.get("tagline")
    return None

def main():
    prompts_file = "generated_prompts.json"
    if not os.path.exists(prompts_file):
        print(f"❌ Error: {prompts_file} not found.")
        return

    with open(prompts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    image_prompts = [entry for entry in data if "(Image Prompt)" in entry['title']]
    if not image_prompts: 
        print("❌ No image prompts found.")
        return

    print(f"🚀 Found {len(image_prompts)} banners to generate...")

    for entry in image_prompts:
        display_title = entry['title'].replace(" (Image Prompt)", "").split("(")[0].strip()
        
        print(f"\n🎨 Creating Banner for: {display_title}")
        
        tagline = find_tagline(display_title)
        if tagline:
            print(f"💡 Found tagline: {tagline}")

        # 1. Get the background
        background_bytes = generate_image_free(entry['prompt'])
        
        if background_bytes:
            # 2. Overlay the perfect text
            print(f"✍️ Stamping professional layout...")
            final_image = overlay_text(background_bytes, display_title, tagline)
            
            output_dir = "banners"
            if not os.path.exists(output_dir): os.makedirs(output_dir)
                
            safe_title = "".join([c for c in display_title if c.isalnum() or c in (' ', '_')]).rstrip()
            filename = f"{output_dir}/{safe_title.replace(' ', '_')}_pro.jpg"
            
            with open(filename, "wb") as f:
                f.write(final_image)
            print(f"✅ SUCCESS! Banner saved to: {filename}")
        else:
            print(f"❌ Failed to generate background for '{display_title}'.")

if __name__ == "__main__":
    main()
