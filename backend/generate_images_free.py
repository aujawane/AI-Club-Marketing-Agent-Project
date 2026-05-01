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
    "port": "5433"
}

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

def overlay_text(image_bytes, title, tagline=None, duration=None):
    """Overlays the title, tagline, and duration professionally on the image."""
    img = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # --- DURATION BADGE (Top Right) ---
    if duration:
        dur_font_size = int(width / 45)
        dur_font = get_font(dur_font_size, bold=True)
        dur_text = f"⏳ {duration.upper()}"
        bbox = draw.textbbox((0, 0), dur_text, font=dur_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        badge_padding = 20
        badge_w, badge_h = tw + (badge_padding * 2), th + (badge_padding * 2)
        badge_x, badge_y = width - badge_w - 40, 40
        draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=(124, 58, 237, 200))
        draw.text((badge_x + badge_padding, badge_y + badge_padding), dur_text, font=dur_font, fill="white")

    # --- TITLE ---
    title_font_size = int(width / 18)
    title_font = get_font(title_font_size, bold=True)
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
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    rect_y0 = (height - overlay_h) // 2
    rect_y1 = rect_y0 + overlay_h
    overlay_draw.rectangle([0, rect_y0, width, rect_y1], fill=(0, 0, 0, 160))
    img.paste(overlay, (0, 0), overlay)
    
    # --- DRAW TEXT ---
    y_text = (height - content_h) // 2
    for line in title_lines:
        w = draw.textlength(line, font=title_font)
        draw.text(((width - w) / 2, y_text), line, font=title_font, fill="white")
        y_text += title_line_height
    y_text += spacing
    for line in tagline_lines:
        w = draw.textlength(line, font=tagline_font)
        draw.text(((width - w) / 2, y_text), line, font=tagline_font, fill=(255, 220, 100))
        y_text += tagline_line_height
        
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
    tagline = sub_data.get('objectives', '')[:100]

    background_bytes = generate_image_free(prompt)
    if background_bytes:
        final_image = overlay_text(background_bytes, display_title, tagline, duration)
        save_image_to_db(submission_id, final_image)
    else:
        print(f"❌ Generation failed.")

if __name__ == "__main__":
    main()
