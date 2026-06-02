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

def darken_rgb(rgb, max_channel=96):
    """Keep accent text/borders dark enough to read on a light card."""
    r, g, b = rgb
    if max(r, g, b) <= max_channel:
        return rgb
    scale = max_channel / max(r, g, b)
    return (int(r * scale), int(g * scale), int(b * scale))

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
    accent_rgb = darken_rgb(hex_to_rgb(palette[0] if palette and len(palette) > 0 else None, fallback=(8, 96, 69)))
    
    themes = {
        'illustrated': {
            'panel_fill': (255, 255, 255, 242),
            'text_main': (18, 24, 21, 255),
            'text_sub': (47, 58, 52, 255),
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
            'panel_fill': (255, 255, 255, 244),
            'text_main': (18, 24, 21, 255),
            'text_sub': (47, 58, 52, 255),
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
            'panel_fill': (255, 253, 247, 242),
            'text_main': (29, 22, 18, 255),
            'text_sub': (60, 49, 43, 255),
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
            'text_main': (12, 16, 14, 255),
            'text_sub': (43, 51, 47, 255),
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

def clean_text(value):
    """Convert common HTML-ish project text into compact display text."""
    if not isinstance(value, str):
        return ""
    text = re.sub(r"<[^>]*>", " ", value)
    replacements = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()

def string_list(value):
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if clean_text(item)]

def sentence_case(text):
    text = clean_text(text).strip(" .")
    if not text:
        return ""
    return text[0].upper() + text[1:]

def trim_words(text, max_words=9):
    words = clean_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",.;:") + "..."

def tone_copy(tone):
    tone = clean_text(tone).lower() or "professional"
    copy = {
        "professional": {
            "learn_heading": "Mastery Objectives",
            "outcome_heading": "Professional Outcome",
            "activity_noun": "strategic tasks",
            "verbs": ["Master", "Execute", "Apply", "Develop"],
            "descriptor": "refined, expert",
        },
        "inspiring": {
            "learn_heading": "Your Potential",
            "outcome_heading": "Future Impact",
            "activity_noun": "growth milestones",
            "verbs": ["Ignite", "Transform", "Pioneer", "Achieve"],
            "descriptor": "visionary, bold",
        },
        "friendly": {
            "learn_heading": "Skills we'll build",
            "outcome_heading": "The big result",
            "activity_noun": "simple steps",
            "verbs": ["Try", "Make", "Build", "Grow"],
            "descriptor": "warm, easy-to-follow",
        },
        "academic": {
            "learn_heading": "Scholarly Goals",
            "outcome_heading": "Academic Synthesis",
            "activity_noun": "rigorous exercises",
            "verbs": ["Analyze", "Synthesize", "Evaluate", "Research"],
            "descriptor": "rigorous, methodical",
        },
        "playful": {
            "learn_heading": "Super Powers",
            "outcome_heading": "Mission Complete!",
            "activity_noun": "epic quests",
            "verbs": ["Discover", "Blast", "Build", "Win"],
            "descriptor": "fun, energetic",
        },
        "creative": {
            "learn_heading": "Artistic Journey",
            "outcome_heading": "Studio Portfolio",
            "activity_noun": "creative sparks",
            "verbs": ["Design", "Imagine", "Craft", "Express"],
            "descriptor": "imaginative, unique",
        },
    }
    return copy.get(tone, copy["professional"])

def normalize_learning_item(text, verb):
    """Turn raw JSON/objective labels into compact marketing copy."""
    item = clean_text(text)
    if not item:
        return ""

    item = re.sub(r"^(students?|learners?)\s+will\s+(be able to\s+)?", "", item, flags=re.I)
    item = re.sub(r"^(you'?ll|you will)\s+", "", item, flags=re.I)
    item = re.sub(r"^(the\s+)?(student|learner)\s+", "", item, flags=re.I)
    item = re.sub(r"\busing formulas and rules\b", "with core formulas", item, flags=re.I)
    item = re.sub(r"\busing real demographic data\b", "with real-world data", item, flags=re.I)
    item = re.sub(r"\bGoogle Sheets\b", "spreadsheets", item, flags=re.I)
    item = re.sub(r"\bGoogle Slides\b", "visual slides", item, flags=re.I)
    item = re.sub(r"\s+", " ", item).strip(" .")

    if not item:
        return ""

    lower = item.lower()
    action_starters = (
        "build", "create", "analyze", "apply", "practice", "design", "explain",
        "evaluate", "interpret", "use", "develop", "write", "calculate", "compare",
        "research", "read", "make", "try", "explore", "discover", "refine", "test",
    )
    if lower.startswith(action_starters):
        return sentence_case(trim_words(item, 10))

    skill_rewrites = {
        "ai": "AI-assisted problem solving",
        "ctf": "Prompt-building strategy",
        "infographic": "Infographic design",
        "data analysis": "Data analysis",
        "research": "Research-backed decisions",
        "reflection": "Thoughtful reflection",
        "spreadsheet": "Spreadsheet fluency",
        "google sheets": "Spreadsheet fluency",
        "cornell notes": "Structured note-taking",
        "note-taking": "Better note-taking",
    }
    rewritten = skill_rewrites.get(lower)
    if rewritten:
        return rewritten

    if len(item.split()) <= 3:
        return sentence_case(item)

    return sentence_case(trim_words(f"{verb} {item[0].lower() + item[1:]}", 10))

def marketable_outcome(text, tone):
    item = clean_text(text)
    if not item:
        return ""

    item = re.sub(r"^(students?|learners?)\s+will\s+(be able to\s+)?", "", item, flags=re.I)
    item = re.sub(r"^(create|complete|build)\s+", "", item, flags=re.I)
    item = re.sub(r"\bworldwide\b", "using real-world examples", item, flags=re.I)
    item = trim_words(item, 14).strip(" .")

    verb = tone_copy(tone)["verbs"][2]
    if item:
        return sentence_case(f"{verb} {item[0].lower() + item[1:]}")
    return ""

def marketable_description(text, tone):
    item = clean_text(text)
    if not item:
        return ""

    item = re.sub(r"^(students?|learners?)\s+will\s+(be able to\s+)?", "", item, flags=re.I)
    item = re.sub(r"^(you'?ll|you will)\s+", "", item, flags=re.I)
    item = re.sub(r"\busing formulas and rules\b", "through core formulas", item, flags=re.I)
    item = re.sub(r"\busing real demographic data\b", "with real-world data", item, flags=re.I)
    item = re.sub(r"\s+", " ", item).strip(" .")

    copy = tone_copy(tone)
    descriptor = copy["descriptor"]
    verbs = copy["verbs"]
    if item.lower().startswith(("master", "learn", "build", "create", "analyze", "discover", "design")):
        return sentence_case(trim_words(item, 18))

    if item.lower().startswith("understand "):
        focus = item[len("understand "):]
        return sentence_case(trim_words(f"Build a {descriptor} foundation in {focus}", 18))

    return sentence_case(trim_words(f"{verbs[0]} {descriptor} skills in {item[0].lower() + item[1:]}", 18))

def wrap_text(draw, text, font, max_width):
    words = clean_text(text).split()
    if not words:
        return []

    lines = []
    current = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        lines.append(" ".join(current))
    return lines

def normalized_banner_copy(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if not isinstance(value, dict):
        return {}

    return {
        "format": clean_text(value.get("format")),
        "learn_heading": clean_text(value.get("learn_heading")),
        "learning_items": string_list(value.get("learning_items"))[:4],
        "outcome_heading": clean_text(value.get("outcome_heading")),
        "outcome": clean_text(value.get("outcome")),
        "focus_areas": string_list(value.get("focus_areas"))[:5],
    }

def extract_banner_metadata(submission=None, duration=None, banner_copy=None):
    """Build compact, readable metadata for the banner card."""
    submission = submission or {}
    tone = submission.get("tone", "professional")
    copy = tone_copy(tone)
    generated_copy = normalized_banner_copy(banner_copy)
    uploaded = submission.get("uploadedJson") if isinstance(submission.get("uploadedJson"), dict) else {}
    sections = uploaded.get("sections") if isinstance(uploaded.get("sections"), list) else []
    objectives = []
    for section in sections:
        if isinstance(section, dict) and isinstance(section.get("objectives"), list):
            objectives.extend(section["objectives"])

    form_objectives = [
        clean_text(line)
        for line in str(submission.get("objectives") or "").splitlines()
        if clean_text(line)
    ]

    raw_learning_items = (
        string_list(uploaded.get("learning_objectives"))
        + string_list(uploaded.get("what_students_learn"))
        + string_list(uploaded.get("skills_gained"))
        + form_objectives
    )

    for objective in objectives:
        if len(raw_learning_items) >= 4:
            break
        if isinstance(objective, dict):
            item = clean_text(objective.get("title"))
            if item and item not in raw_learning_items:
                raw_learning_items.append(item)

    tags = string_list(submission.get("tags")) or string_list(uploaded.get("tags"))
    skills = (
        string_list(uploaded.get("skills_taught"))
        + string_list(uploaded.get("skills_gained"))
        + tags
    )

    total_points = sum(
        objective.get("points", 0)
        for objective in objectives
        if isinstance(objective, dict) and isinstance(objective.get("points"), int)
    )

    facts = []
    resolved_duration = clean_text(duration) or clean_text(submission.get("duration")) or clean_text(uploaded.get("duration"))
    audience = clean_text(submission.get("grade")) or clean_text(uploaded.get("audience"))
    difficulty = clean_text(uploaded.get("difficulty"))
    certification = clean_text(uploaded.get("certification"))

    if resolved_duration:
        facts.append(("Time", resolved_duration))
    if audience:
        facts.append(("For", trim_words(audience, 4)))
    if difficulty:
        facts.append(("Difficulty", difficulty))
    if generated_copy.get("format"):
        facts.append(("Format", generated_copy["format"]))
    elif objectives:
        facts.append(("Format", f"Hands-on project • {len(objectives)} {copy['activity_noun']}"))
    if total_points:
        facts.append(("Points", str(total_points)))
    if certification:
        facts.append(("Certificate", certification.replace("Yes - ", "")))

    learning_items = []
    for idx, item in enumerate(raw_learning_items):
        verb = copy["verbs"][idx % len(copy["verbs"])]
        phrased = normalize_learning_item(item, verb)
        if phrased and phrased not in learning_items:
            learning_items.append(phrased)

    outcome = marketable_outcome(
        clean_text(uploaded.get("outcome")) or clean_text(uploaded.get("pitch")),
        tone,
    )

    return {
        "facts": facts[:5],
        "learning_items": generated_copy.get("learning_items") or learning_items[:4],
        "outcome": generated_copy.get("outcome") or outcome,
        "skills": generated_copy.get("focus_areas") or list(dict.fromkeys(skills))[:5],
        "headings": {
            "learn": generated_copy.get("learn_heading") or copy["learn_heading"],
            "outcome": generated_copy.get("outcome_heading") or copy["outcome_heading"],
        },
    }

def draw_wrapped_text(draw, xy, text, font, fill, max_width, line_gap=6, max_lines=None):
    x, y = xy
    lines = wrap_text(draw, text, font, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y

def draw_label(draw, x, y, label, font, fill):
    draw.text((x, y), label.upper(), font=font, fill=fill)
    bbox = draw.textbbox((x, y), label.upper(), font=font)
    return bbox[3] - bbox[1]

def compose_banner(image_bytes, title, description=None, duration=None, style_id='illustrated', palette=None, submission=None, banner_copy=None):
    """Professional banner compositor with side-panel layout."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    theme = get_style_theme(style_id, palette)
    submission = submission or {}
    metadata = extract_banner_metadata(submission, duration, banner_copy=banner_copy)
    tone = submission.get("tone", "professional")
    
    # 1. DRAW SIDE PANEL
    panel_width = int(width * 0.50)
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
    padding = 52
    curr_y = panel_box[1] + 44
    max_text_width = panel_width - (padding * 2)

    # Title
    title_size = 58 if len(title) < 38 else 50
    title_font = get_font(theme['fonts_bold'], title_size)
        
    # Wrap Title
    lines = wrap_text(draw, title, title_font, max_text_width)
    
    for line in lines[:3]: # Max 3 lines
        draw.text((panel_box[0] + padding, curr_y), line, font=title_font, fill=theme['text_main'])
        curr_y += title_size + 6
    
    curr_y += 18
    
    # Tiny Description
    if description:
        desc_size = 20
        desc_font = get_font(theme['fonts_reg'], desc_size)
        curr_y = draw_wrapped_text(
            draw,
            (panel_box[0] + padding, curr_y),
            marketable_description(description, tone),
            desc_font,
            theme['text_sub'],
            max_text_width,
            line_gap=6,
            max_lines=3,
        )

    curr_y += 24

    # 4. STRUCTURED METADATA CARD CONTENT
    label_font = get_font(theme['fonts_bold'], 13)
    body_font = get_font(theme['fonts_reg'], 17)
    body_bold = get_font(theme['fonts_bold'], 17)
    small_font = get_font(theme['fonts_reg'], 14)

    if metadata["facts"]:
        chip_x = panel_box[0] + padding
        chip_y = curr_y
        chip_gap = 10
        row_height = 0
        for label, value in metadata["facts"]:
            chip_text = f"{label}: {value}"
            bbox = draw.textbbox((0, 0), chip_text, font=small_font)
            chip_w = min(bbox[2] - bbox[0] + 24, max_text_width)
            chip_h = bbox[3] - bbox[1] + 16
            if chip_x + chip_w > panel_box[0] + padding + max_text_width:
                chip_x = panel_box[0] + padding
                chip_y += row_height + chip_gap
                row_height = 0
            draw.rounded_rectangle(
                [chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
                radius=12,
                fill=(255, 255, 255, 235),
                outline=(*theme['accent'], 130),
                width=1,
            )
            draw.text((chip_x + 12, chip_y + 8), chip_text, font=small_font, fill=theme['text_main'])
            chip_x += chip_w + chip_gap
            row_height = max(row_height, chip_h)
        curr_y = chip_y + row_height + 32

    if metadata["learning_items"]:
        label_h = draw_label(draw, panel_box[0] + padding, curr_y, metadata["headings"]["learn"], label_font, (*theme['accent'], 255))
        curr_y += label_h + 15
        for item in metadata["learning_items"]:
            if curr_y > height - 126:
                break
            bullet_x = panel_box[0] + padding
            draw.ellipse([bullet_x, curr_y + 8, bullet_x + 7, curr_y + 15], fill=(*theme['accent'], 255))
            next_y = draw_wrapped_text(
                draw,
                (bullet_x + 17, curr_y),
                item,
                body_font,
                theme['text_main'],
                max_text_width - 17,
                line_gap=4,
                max_lines=2,
            )
            curr_y = next_y + 8

    if metadata["outcome"] and curr_y < height - 118:
        curr_y += 14
        label_h = draw_label(draw, panel_box[0] + padding, curr_y, metadata["headings"]["outcome"], label_font, (*theme['accent'], 255))
        curr_y += label_h + 13
        curr_y = draw_wrapped_text(
            draw,
            (panel_box[0] + padding, curr_y),
            metadata["outcome"],
            body_bold,
            theme['text_main'],
            max_text_width,
            line_gap=5,
            max_lines=2,
        )

    if metadata["skills"] and curr_y < height - 72:
        skill_text = "Focus areas: " + ", ".join(metadata["skills"])
        draw_wrapped_text(
            draw,
            (panel_box[0] + padding, height - 58),
            skill_text,
            small_font,
            theme['text_sub'],
            max_text_width,
            line_gap=4,
            max_lines=1,
        )

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

def get_banner_card_copy_from_db(submission_id):
    """Fetch AI-rewritten card copy for the generated banner."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT content FROM \"MarketingAsset\" WHERE \"submissionId\" = %s AND \"assetType\" = 'banner_card_copy' LIMIT 1", (submission_id,))
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
    banner_card_copy = get_banner_card_copy_from_db(submission_id)
    
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
            palette=palette,
            submission=sub_data,
            banner_copy=banner_card_copy
        )
        save_image_to_db(submission_id, final_image)
    else:
        print(f"❌ Generation failed.")

if __name__ == "__main__":
    main()
