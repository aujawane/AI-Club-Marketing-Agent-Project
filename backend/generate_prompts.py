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
    "port": "5434"
}

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

def get_env_value(name: str) -> Optional[str]:
    """Read an environment value from process env, backend/.env, or repo .env."""
    value = os.environ.get(name)
    if value:
        return value

    for env_path in (Path.cwd() / ".env", SCRIPT_DIR / ".env", PROJECT_ROOT / ".env"):
        if not env_path.exists():
            continue

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, raw_value = line.split("=", 1)
                    if key.strip() == name:
                        return raw_value.strip().strip("'").strip('"')
        except Exception:
            continue

    return None

def get_gemini_api_key():
    return get_env_value("GEMINI_API_KEY")

def get_openai_api_key():
    return get_env_value("OPENAI_API_KEY")

def get_openai_prompt_model():
    return get_env_value("OPENAI_PROMPT_MODEL") or "gpt-4o-mini"

def get_openai_prompt_models():
    configured = get_env_value("OPENAI_PROMPT_MODELS")
    if configured:
        return [model.strip() for model in configured.split(",") if model.strip()]

    primary = get_openai_prompt_model()
    fallbacks = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"]
    return list(dict.fromkeys([primary, *fallbacks]))

def call_gemini_text(prompt: str, model: str = "gemini-flash-latest") -> Optional[str]:
    api_key = get_gemini_api_key()
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

def extract_response_text(result: Dict) -> Optional[str]:
    if isinstance(result.get("output_text"), str) and result["output_text"].strip():
        return result["output_text"].strip()

    chunks = []
    for item in result.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)

    text = "\n".join(chunks).strip()
    return text or None

def call_openai_prompt_agent(submission: Dict, base_prompt: str) -> Optional[str]:
    api_key = get_openai_api_key()
    if not api_key:
        return None

    instructions = (
        "You are a senior creative director and image prompt architect for an education marketplace. "
        "Write one excellent image-generation prompt for a course/project banner. "
        "Return only the final prompt text. Do not include markdown, labels, JSON, or commentary. "
        "The image will later receive overlaid title text, so the generated background must contain no readable text, "
        "no logos, no UI screenshots, no watermarks, and no typography. "
        "Make the prompt visually specific, concrete, and production-ready: include subject-relevant metaphors, "
        "composition, lighting, depth, color palette, style, and quality details. "
        "Keep the center readable/open for later text overlay and push most visual detail toward the edges. "
        "Avoid generic phrases unless they clarify composition or quality."
    )

    user_prompt = (
        "Improve this image prompt for better image generation.\n\n"
        f"Submission data:\n{json.dumps(submission, indent=2, ensure_ascii=False)}\n\n"
        f"Current baseline prompt:\n{base_prompt}\n\n"
        "Constraints:\n"
        "- 16:9 wide course/project banner background.\n"
        "- No text in the image itself.\n"
        "- Respect the selected image style and color palette when present.\n"
        "- Use educational, professional, marketplace-ready visual language.\n"
        "- 80 to 150 words."
    )

    context = ssl._create_unverified_context()

    for model in get_openai_prompt_models():
        payload = {
            "model": model,
            "instructions": instructions,
            "input": user_prompt,
        }

        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        try:
            with request.urlopen(req, context=context, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
                prompt = extract_response_text(result)
                if prompt:
                    print(f"✅ OpenAI prompt agent used model {model}")
                    return prompt
                print(f"⚠️ OpenAI prompt agent returned no text for {model}; trying fallback.")
        except error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"❌ OpenAI API Error for {model} ({e.code}): {err_msg}")
            if e.code not in (400, 403, 404):
                break
        except Exception as e:
            print(f"❌ OpenAI API Error for {model}: {str(e)}")
            break

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

def build_gemini_prompt_agent_request(submission: Dict, base_prompt: str) -> str:
    return (
        "Act as a senior creative director and image prompt architect. "
        "Rewrite the baseline into one high-quality image-generation prompt for a 16:9 educational banner. "
        "Return only the final prompt text, no markdown. "
        "The generated image must contain no readable text, logos, watermarks, or UI screenshots. "
        "Keep the center clean for later title overlay, with subject-relevant visual detail at the edges. "
        "Respect selected style and colors.\n\n"
        f"Submission data:\n{json.dumps(submission, indent=2, ensure_ascii=False)}\n\n"
        f"Baseline prompt:\n{base_prompt}"
    )

def generate_ai_enhanced_prompt(submission: Dict) -> str:
    base_prompt = generate_image_prompt(submission)

    openai_prompt = call_openai_prompt_agent(submission, base_prompt)
    if openai_prompt:
        print("✅ Enhanced prompt with OpenAI prompt agent")
        return openai_prompt

    gemini_prompt = call_gemini_text(build_gemini_prompt_agent_request(submission, base_prompt))
    if gemini_prompt:
        print("✅ Enhanced prompt with Gemini fallback")
        return gemini_prompt

    print("⚠️ No prompt agent API key available; using template prompt")
    return base_prompt

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
    
    image_prompt = generate_ai_enhanced_prompt(submission)

    save_prompt_to_db(submission_id, "image_prompt", image_prompt)

if __name__ == "__main__":
    main()
