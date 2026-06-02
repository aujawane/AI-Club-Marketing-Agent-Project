#!/usr/bin/env python3
import json
import sys
import os
import ssl
import psycopg2
import uuid
import re
from urllib import request, error
from pathlib import Path
from typing import Any, Dict, List, Optional

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

TONE_GUIDELINES = {
    "professional": "Direct, authoritative, and results-oriented. Use words like 'mastery', 'efficient', 'outcome', and 'proven'. Avoid exclamation marks.",
    "inspiring": "Visionary, uplifting, and ambitious. Use words like 'transform', 'unlock', 'potential', and 'future'. Use evocative and empowering language.",
    "friendly": "Warm, approachable, and encouraging. Use words like 'together', 'step-by-step', 'let\'s', and 'fun'. Use a conversational and welcoming style.",
    "academic": "Rigorous, scholarly, and precise. Use words like 'analyze', 'framework', 'synthesis', and 'comprehensive'. Focus on depth and methodology.",
    "playful": "Engaging, high-energy, and fun. Use words like 'adventure', 'mission', 'awesome', and 'level-up'. Feel free to use exclamation marks and punchy, active verbs.",
    "creative": "Exploratory, imaginative, and expressive. Use words like 'discover', 'design', 'shape', and 'possibility'. Focus on the journey and unique expression."
}

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

    tone = submission.get("tone", "professional")
    tone_desc = TONE_GUIDELINES.get(tone, TONE_GUIDELINES["professional"])

    instructions = (
        "You are a senior creative director and image prompt architect for an education marketplace. "
        "Write one excellent image-generation prompt for a course/project banner. "
        "Return only the final prompt text. Do not include markdown, labels, JSON, or commentary. "
        "The image will later receive overlaid title text, so the generated background must contain no readable text, "
        "no logos, no UI screenshots, no watermarks, and no typography. "
        "Make the prompt visually specific, concrete, and production-ready: include subject-relevant metaphors, "
        "composition, lighting, depth, color palette, style, and quality details. "
        "Keep the center readable/open for later text overlay and push most visual detail toward the edges. "
        f"The visual tone should feel {tone}: {tone_desc}. "
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

    # Important: Instruct the AI to leave space for text
    return (
        f"A professional wide cinematic banner background (16:9) for a course about '{subject}'. "
        f"Style: {visual_style}. Metaphor: {visual_metaphor}. "
        f"Colors: {', '.join(palette) if palette else 'modern professional colors'}. "
        f"Composition: Minimalist and clean. Keep the LEFT HALF of the image very simple, empty, or blurred for text panel placement. "
        f"Push most visual detail strictly to the right side. "
        "CRITICAL: DO NOT include any text, letters, characters, logos, or typography in the image. The image must be purely visual artwork."
    )

def build_gemini_prompt_agent_request(submission: Dict, base_prompt: str) -> str:
    return (
        "Act as a senior creative director. Rewrite the baseline into one high-quality image-generation prompt for a 16:9 educational banner background. "
        "Return only the final prompt text, no markdown. "
        "CRITICAL CONSTRAINT: The generated image MUST contain NO readable text, NO single letters, NO characters, NO logos, NO watermarks, and NO UI screenshots. "
        "IMPORTANT: The composition MUST have a large 'safe zone' on the LEFT side for a text panel. "
        "Ensure the left 40% of the image is simple, clean, or low-contrast, while the visual metaphors are concentrated on the right. "
        f"Respect selected style ({submission.get('imageStyle')}) and colors ({submission.get('palette')}).\n\n"
        f"Baseline prompt: {base_prompt}"
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

def generate_marketing_description(submission: Dict) -> str:
    """Generate a tone-aware marketing description for the banner."""
    title = submission.get('title', 'Education')
    subject = submission.get('subject', 'Education')
    tone = submission.get('tone', 'professional')
    tone_desc = TONE_GUIDELINES.get(tone, TONE_GUIDELINES["professional"])
    objectives = submission.get('objectives', '')

    llm_prompt = (
        f"Act as a professional copywriter. Write a tiny marketing description (max 15 words) "
        f"for a course titled '{title}' about {subject}. "
        f"The tone should be {tone}: {tone_desc}. "
        f"Here are the learning objectives for context: {objectives}. "
        "The description should be one single punchy sentence that highlights the main value. "
        "Return ONLY the description text, no quotes, no labels."
    )
    
    polished_desc = call_gemini_text(llm_prompt)
    if polished_desc:
        return polished_desc.strip().strip('"')
    
    # Fallback if LLM fails
    return f"Master {subject} with our {tone} {title} course."

def clean_text(value: Any) -> str:
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

def string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if clean_text(item)]

def extract_banner_copy_source(submission: Dict) -> Dict:
    uploaded = submission.get("uploadedJson") if isinstance(submission.get("uploadedJson"), dict) else {}
    sections = uploaded.get("sections") if isinstance(uploaded.get("sections"), list) else []
    objectives = []
    for section in sections:
        if isinstance(section, dict) and isinstance(section.get("objectives"), list):
            objectives.extend(section["objectives"])

    objective_titles = [
        clean_text(objective.get("title"))
        for objective in objectives
        if isinstance(objective, dict) and clean_text(objective.get("title"))
    ]
    objective_descriptions = [
        clean_text(objective.get("description"))
        for objective in objectives[:6]
        if isinstance(objective, dict) and clean_text(objective.get("description"))
    ]
    form_objectives = [
        clean_text(line)
        for line in str(submission.get("objectives") or "").splitlines()
        if clean_text(line)
    ]
    skills = (
        string_list(uploaded.get("skills_taught"))
        + string_list(uploaded.get("skills_gained"))
        + string_list(submission.get("tags"))
    )

    total_points = sum(
        objective.get("points", 0)
        for objective in objectives
        if isinstance(objective, dict) and isinstance(objective.get("points"), int)
    )

    return {
        "title": submission.get("title") or uploaded.get("title"),
        "subject": submission.get("subject"),
        "tone": submission.get("tone", "professional"),
        "audience": submission.get("grade") or uploaded.get("audience"),
        "duration": submission.get("duration") or uploaded.get("duration"),
        "difficulty": uploaded.get("difficulty"),
        "activity_count": len(objectives),
        "total_points": total_points,
        "raw_learning_objectives": (
            string_list(uploaded.get("learning_objectives"))
            + string_list(uploaded.get("what_students_learn"))
            + form_objectives
            + objective_titles[:8]
        ),
        "raw_objective_details": objective_descriptions,
        "raw_outcome": uploaded.get("outcome") or uploaded.get("pitch"),
        "raw_skills": list(dict.fromkeys(skills))[:10],
    }

def extract_json_object(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        result = json.loads(match.group(0))
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        return None

def call_openai_banner_copy_agent(source: Dict) -> Optional[Dict]:
    api_key = get_openai_api_key()
    if not api_key:
        return None

    tone = source.get("tone", "professional")
    tone_desc = TONE_GUIDELINES.get(tone, TONE_GUIDELINES["professional"])

    instructions = (
        "You are a concise education marketplace copywriter. Rewrite raw course/project JSON into polished banner-card copy. "
        "Do not copy phrases straight from the JSON. Do not preserve awkward task labels verbatim. "
        f"Use the requested tone ({tone}: {tone_desc}), make learning objectives appealing, specific, and student-facing, "
        "and keep every field short enough for a 16:9 banner card. Return strict JSON only."
    )
    user_prompt = (
        f"Raw source data:\n{json.dumps(source, indent=2, ensure_ascii=False)}\n\n"
        "Return this exact JSON shape:\n"
        "{\n"
        '  "format": "short marketable format line, e.g. Hands-on project • 13 guided activities",\n'
        '  "learn_heading": "short heading tailored to tone",\n'
        '  "learning_items": ["3 to 4 rewritten learning objectives, each 3-8 words"],\n'
        '  "outcome_heading": "short heading tailored to tone",\n'
        '  "outcome": "rewritten final result, 8-14 words",\n'
        '  "focus_areas": ["up to 5 polished focus areas, 1-3 words each"]\n'
        "}\n\n"
        "Rules:\n"
        "- Do NOT use text straight from the JSON file.\n"
        "- Rewrite, simplify, and market the learning objectives.\n"
        "- Avoid classroom admin wording like file setup, rename, completion, points, task, objective.\n"
        "- Make the format line more useful than a raw task count.\n"
        "- Match the description tone exactly."
    )

    context = ssl._create_unverified_context()
    for model in get_openai_prompt_models():
        payload = {
            "model": model,
            "instructions": instructions,
            "input": user_prompt,
            "text": {"format": {"type": "json_object"}},
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
                text = extract_response_text(result)
                parsed = extract_json_object(text or "")
                if parsed:
                    print(f"✅ OpenAI banner card copy used model {model}")
                    return parsed
        except error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"❌ OpenAI banner copy error for {model} ({e.code}): {err_msg}")
            if e.code not in (400, 403, 404):
                break
        except Exception as e:
            print(f"❌ OpenAI banner copy error for {model}: {str(e)}")
            break

    return None

def call_gemini_banner_copy_agent(source: Dict) -> Optional[Dict]:
    tone = source.get("tone", "professional")
    tone_desc = TONE_GUIDELINES.get(tone, TONE_GUIDELINES["professional"])
    
    prompt = (
        "Act as a concise education marketplace copywriter. Rewrite raw project JSON into polished banner-card copy. "
        "Do not copy phrases straight from the JSON. "
        f"Match the requested tone ({tone}: {tone_desc}). Return strict JSON only with keys: "
        "format, learn_heading, learning_items, outcome_heading, outcome, focus_areas. "
        "Learning items must be rewritten, appealing, student-facing, and 3-8 words each. "
        "Format must be marketable, not just a raw count.\n\n"
        f"Raw source data:\n{json.dumps(source, indent=2, ensure_ascii=False)}"
    )
    response = call_gemini_text(prompt)
    if not response:
        return None
    parsed = extract_json_object(response)
    if parsed:
        print("✅ Gemini banner card copy fallback succeeded")
    return parsed

def generate_banner_card_copy(submission: Dict) -> str:
    source = extract_banner_copy_source(submission)

    copy = call_openai_banner_copy_agent(source)
    if not copy:
        copy = call_gemini_banner_copy_agent(source)

    if not copy:
        print("⚠️ No banner copy agent available; using compositor fallback")
        return "{}"

    return json.dumps(copy, ensure_ascii=False)

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
    
    # 1. Generate Image Prompt
    image_prompt = generate_ai_enhanced_prompt(submission)
    save_prompt_to_db(submission_id, "image_prompt", image_prompt)

    # 2. Generate Marketing Description
    marketing_desc = generate_marketing_description(submission)
    save_prompt_to_db(submission_id, "marketing_description", marketing_desc)

    # 3. Generate rewritten banner-card metadata copy
    banner_card_copy = generate_banner_card_copy(submission)
    save_prompt_to_db(submission_id, "banner_card_copy", banner_card_copy)

if __name__ == "__main__":
    main()
