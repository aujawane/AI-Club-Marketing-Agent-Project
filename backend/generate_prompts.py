#!/usr/bin/env python3
import json
import sys
import os
import ssl
import psycopg2
import uuid
from urllib import request, error
from pathlib import Path
from typing import Dict, List, Optional

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "marketing_agent",
    "user": "user",
    "password": "password",
    "port": "5433"
}

def get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=")[1].strip().strip("'").strip('"')
                        break
        except Exception: pass
    return api_key

def call_gemini_text(prompt: str, model: str = "gemini-flash-latest") -> Optional[str]:
    api_key = get_api_key()
    if not api_key: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    context = ssl._create_unverified_context()
    try:
        with request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Gemini API Error: {str(e)}")
    return None

def get_submission_from_db(submission_id):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT \"formData\" FROM \"Submission\" WHERE id = %s", (submission_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

def save_prompt_to_db(submission_id, asset_type, content):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        asset_id = str(uuid.uuid4())
        # Delete old prompt of same type if exists
        cur.execute("DELETE FROM \"MarketingAsset\" WHERE \"submissionId\" = %s AND \"assetType\" = %s", (submission_id, asset_type))
        cur.execute(
            "INSERT INTO \"MarketingAsset\" (id, \"submissionId\", \"assetType\", content, \"createdAt\") "
            "VALUES (%s, %s, %s, %s, NOW())",
            (asset_id, submission_id, asset_type, content)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Saved {asset_type} to DB")
    except Exception as e:
        print(f"❌ DB Save Error: {e}")

def generate_image_prompt(submission: Dict) -> str:
    title = submission.get('title', 'Education')
    subject = submission.get('subject', 'Education').lower()
    objectives = submission.get('objectives', '')
    palette = submission.get('palette', [])
    style = submission.get('imageStyle', 'illustrated')

    subject_map = {
        'mathematics': "calculus curves, geometric shapes, mathematical formulas, abstract graphs",
        'science': "molecular structures, laboratory glassware, cosmic nebulae, biological cells",
        'history': "vintage maps, ancient scrolls, architectural pillars, sepia-toned relics",
        'computer science': "digital circuitry, glowing code syntax, holographic interfaces, networking nodes",
        'creative arts': "vibrant paint splashes, floating musical notes, charcoal sketches, artistic tools",
        'english': "floating ink droplets, flying book pages, elegant calligraphy, typewriter keys",
    }
    visual_metaphor = subject_map.get(subject, "educational icons and symbolic learning tools")
    
    style_modifiers = {
        'illustrated': "modern 3D isometric illustration, soft claymorphism, high-end digital art",
        'photoreal': "cinematic 8k photography, volumetric lighting, macro lens",
        'watercolor': "ethereal watercolor wash, hand-painted textures, soft bleeding edges",
        'geometric': "minimalist Bauhaus style, sharp geometric abstraction, hard shadows"
    }
    visual_style = style_modifiers.get(style, "clean modern aesthetic")

    return (
        f"A professional wide cinematic banner (16:9) for '{title}'. "
        f"Style: {visual_style}. Metaphor: {visual_metaphor}. "
        f"Colors: {', '.join(palette) if palette else 'modern colors'}. "
        f"Composition: Clean center, elements at edges. 4k, ultra-detailed, no text."
    )

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_prompts.py <submission_id>")
        return

    submission_id = sys.argv[1]
    submission = get_submission_from_db(submission_id)
    
    if not submission:
        print(f"❌ Submission {submission_id} not found in DB")
        return

    print(f"🤖 Processing submission: {submission.get('title')}")
    
    # Use AI if key exists, else template
    api_key = get_api_key()
    if api_key:
        llm_prompt = f"Act as a Creative Director. Generate a high-quality 16:9 banner prompt for a '{submission.get('subject')}' course titled '{submission.get('title')}'. Focus on visual metaphors, clean center for text, and use colors {submission.get('palette')}. No text in image."
        image_prompt = call_gemini_text(llm_prompt) or generate_image_prompt(submission)
    else:
        image_prompt = generate_image_prompt(submission)

    save_prompt_to_db(submission_id, "image_prompt", image_prompt)

if __name__ == "__main__":
    main()
