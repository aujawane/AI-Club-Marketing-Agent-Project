import json
import os
import urllib.parse
import ssl
import io
import psycopg2
import uuid
import re
from urllib import request, error
from PIL import Image, ImageDraw, ImageFont

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "marketing_agent",
    "user": "user",
    "password": "password",
    "port": "5434"
}

def hex_to_rgb(color: str, fallback=(124, 58, 237)):
    """Convert hex string to RGB tuple."""
    if not color: return fallback
    try:
        color = color.lstrip('#')
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return fallback

def get_font(font_paths, size):
    """Try to find the first available font from a list of paths."""
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def get_style_theme(style_id, palette):
    """Get theme configuration based on user selection."""
    accent_rgb = hex_to_rgb(palette[0] if palette and len(palette) > 0 else None)
    
    themes = {
        'illustrated': {
            'panel_fill': (255, 255, 255, 230),
            'text_main': (30, 30, 30, 255),
            'text_sub': (70, 70, 70, 255),
            'accent': accent_rgb,
            'fonts_bold': [
                "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
                "/System/Library/Fonts/Avenir Next.ttc",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            'fonts_reg': [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Avenir Next.ttc",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            'radius': 30
        },
        'photoreal': {
            'panel_fill': (10, 10, 10, 180),
            'text_main': (255, 255, 255, 255),
            'text_sub': (200, 200, 200, 255),
            'accent': accent_rgb,
            'fonts_bold': [
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/SFNS.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            'fonts_reg': [
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/SFNS.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            'radius': 0
        },
        'watercolor': {
            'panel_fill': (255, 253, 240, 220),
            'text_main': (44, 24, 16, 255),
            'text_sub': (80, 60, 50, 255),
            'accent': accent_rgb,
            'fonts_bold': [
                "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                "/System/Library/Fonts/Supplemental/Baskerville.ttc",
                "/System/Library/Fonts/Times.ttc"
            ],
            'fonts_reg': [
                "/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/System/Library/Fonts/Supplemental/Baskerville.ttc",
                "/System/Library/Fonts/Times.ttc"
            ],
            'radius': 15
        },
        'geometric': {
            'panel_fill': (255, 255, 255, 255),
            'text_main': (0, 0, 0, 255),
            'text_sub': (50, 50, 50, 255),
            'accent': accent_rgb,
            'fonts_bold': [
                "/System/Library/Fonts/Supplemental/Futura.ttc",
                "/System/Library/Fonts/Avenir Next.ttc",
                "/System/Library/Fonts/Supplemental/Impact.ttf"
            ],
            'fonts_reg': [
                "/System/Library/Fonts/Supplemental/Futura.ttc",
                "/System/Library/Fonts/Avenir Next.ttc",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            'radius': 0
        }
    }
    return themes.get(style_id, themes['illustrated'])

def compose_banner(image_bytes, title, description=None, duration=None, style_id='illustrated', palette=None):
    """Professional banner compositor with side-panel layout."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    theme = get_style_theme(style_id, palette)
    
    # 1. DRAW SIDE PANEL
    panel_width = int(width * 0.44)
    # Create semi-transparent overlay for panel
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    panel_box = [0, 0, panel_width, height]
    if theme['radius'] > 0:
        # Subtle padding for rounded panel
        panel_box = [20, 20, panel_width - 10, height - 20]
        overlay_draw.rounded_rectangle(panel_box, radius=theme['radius'], fill=theme['panel_fill'])
    else:
        overlay_draw.rectangle(panel_box, fill=theme['panel_fill'])
        
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 2. ADD ACCENT BAR
    accent_bar_width = 10
    draw.rectangle([panel_box[0], panel_box[1], panel_box[0] + accent_bar_width, panel_box[3]], fill=(*theme['accent'], 255))

    # 3. DRAW TEXT
    padding = 60
    curr_y = panel_box[1] + padding

    # Title
    title_size = 58
    title_font = get_font(theme['fonts_bold'], title_size)
        
    # Wrap Title
    max_text_width = panel_width - (padding * 2)
    words = title.split()
    lines = []
    curr_line = []
    for word in words:
        curr_line.append(word)
        if draw.textlength(" ".join(curr_line), font=title_font) > max_text_width:
            lines.append(" ".join(curr_line[:-1]))
            curr_line = [word]
    lines.append(" ".join(curr_line))
    
    for line in lines[:3]: # Max 3 lines
        draw.text((panel_box[0] + padding, curr_y), line, font=title_font, fill=theme['text_main'])
        curr_y += title_size + 8
    
    curr_y += 25
    
    # Tiny Description
    if description:
        desc_size = 24
        desc_font = get_font(theme['fonts_reg'], desc_size)
            
        desc_words = description.replace('\n', ' ').split()
        desc_lines = []
        curr_line = []
        for word in desc_words:
            curr_line.append(word)
            if draw.textlength(" ".join(curr_line), font=desc_font) > max_text_width:
                desc_lines.append(" ".join(curr_line[:-1]))
                curr_line = [word]
        desc_lines.append(" ".join(curr_line))
        
        for line in desc_lines[:4]: # Max 4 lines
            draw.text((panel_box[0] + padding, curr_y), line, font=desc_font, fill=theme['text_sub'])
            curr_y += desc_size + 10

    # 4. DURATION BADGE
    if duration:
        dur_font = get_font(theme['fonts_bold'], 16)
        
        dur_text = f"⏳ {duration.upper()}"
        bbox = draw.textbbox((0, 0), dur_text, font=dur_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        badge_x = panel_box[0] + padding
        badge_y = height - padding - 40
        draw.rounded_rectangle([badge_x, badge_y, badge_x + tw + 30, badge_y + th + 20], radius=15, fill=(*theme['accent'], 200))
        draw.text((badge_x + 15, badge_y + 10), dur_text, font=dur_font, fill="white")

    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='JPEG', quality=95)
    return byte_arr.getvalue()

def overlay_text(image_bytes, title, tagline=None, duration=None):
    """Maintain backward compatibility while redirecting to new compositor."""
    # This will be used if the old script structure is called
    return compose_banner(image_bytes, title, description=tagline, duration=duration)
        
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='JPEG', quality=95)
    return byte_arr.getvalue()

def generate_image_free(prompt, width=1280, height=720):
    visual_prompt = f"{prompt}, artistic background, high quality, no text, clean composition."
    encoded_prompt = urllib.parse.quote(visual_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed=456"
    context = ssl._create_unverified_context()
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        print(f"🚀 Generating background...")
        response = request.urlopen(req, context=context)
        return response.read()
    except Exception as e:
        print(f"❌ Image Error: {e}")
        return None

def get_prompt_from_db(submission_id):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT content FROM \"MarketingAsset\" WHERE \"submissionId\" = %s AND \"assetType\" = 'image_prompt' LIMIT 1", (submission_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

def save_image_to_db(submission_id, image_bytes):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute(
            "UPDATE \"MarketingAsset\" SET \"imageData\" = %s WHERE \"submissionId\" = %s AND \"assetType\" = 'image_prompt'",
            (psycopg2.Binary(image_bytes), submission_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Image saved to DB for {submission_id}")
    except Exception as e:
        print(f"❌ DB Image Error: {e}")

def get_submission_data(submission_id):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT \"formData\" FROM \"Submission\" WHERE id = %s", (submission_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else {}
    except Exception: return {}

def get_marketing_description_from_db(submission_id):
    """Fetch the AI-polished description for the banner."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT content FROM \"MarketingAsset\" WHERE \"submissionId\" = %s AND \"assetType\" = 'marketing_description' LIMIT 1", (submission_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 generate_images_free.py <title> <submission_id>")
        return
    
    display_title = sys.argv[1]
    submission_id = sys.argv[2]
    
    prompt = get_prompt_from_db(submission_id)
    if not prompt:
        print(f"❌ No prompt found for {submission_id}")
        return

    sub_data = get_submission_data(submission_id)
    duration = sub_data.get('duration')
    
    # NEW: Try to get the AI-polished description first
    ai_description = get_marketing_description_from_db(submission_id)
    tagline = ai_description if ai_description else sub_data.get('objectives', '')[:200]
    
    style_id = sub_data.get('imageStyle', 'illustrated')
    palette = sub_data.get('palette', [])

    background_bytes = generate_image_free(prompt)
    if background_bytes:
        final_image = compose_banner(
            background_bytes, 
            display_title, 
            description=tagline, 
            duration=duration,
            style_id=style_id,
            palette=palette
        )
        save_image_to_db(submission_id, final_image)
    else:
        print(f"❌ Generation failed.")

if __name__ == "__main__":
    main()
