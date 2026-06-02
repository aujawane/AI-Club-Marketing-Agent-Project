#!/usr/bin/env python3
import base64
import json
import os
import ssl
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib import error, request

from PIL import Image, ImageOps

from generate_images_free import (
    get_prompt_from_db,
    get_submission_data,
    compose_banner,
    overlay_text,
    save_image_to_db,
    get_banner_card_copy_from_db,
)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def get_env_value(name: str) -> Optional[str]:
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


def get_openai_image_models():
    configured = get_env_value("OPENAI_IMAGE_MODELS")
    if configured:
        return [model.strip() for model in configured.split(",") if model.strip()]

    primary = get_env_value("OPENAI_IMAGE_MODEL") or "gpt-image-1"
    fallbacks = ["gpt-image-1", "gpt-image-1-mini"]
    return list(dict.fromkeys([primary, *fallbacks]))


def get_gemini_image_models():
    configured = get_env_value("GEMINI_IMAGE_MODELS")
    if configured:
        return [model.strip() for model in configured.split(",") if model.strip()]

    primary = get_env_value("GEMINI_IMAGE_MODEL") or "gemini-2.5-flash-image"
    fallbacks = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
    return list(dict.fromkeys([primary, *fallbacks]))


def generate_openai_image_with_model(prompt: str, api_key: str, model: str, size: str, quality: str) -> Optional[bytes]:
    payload = {
        "model": model,
        "prompt": (
            f"{prompt}\n\n"
            "Generate only the background artwork. No readable text, no lettering, no logos, no watermark. "
            "Leave a clean open center area for title overlay."
        ),
        "size": size,
        "quality": quality,
        "n": 1,
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/images/generations",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    print(f"🚀 Generating background with OpenAI Images API ({model}, {size}, {quality})...")
    context = ssl._create_unverified_context()

    with request.urlopen(req, context=context, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
        image_data = result.get("data", [{}])[0]
        b64_image = image_data.get("b64_json")
        if b64_image:
            return base64.b64decode(b64_image)

        image_url = image_data.get("url")
        if image_url:
            with request.urlopen(image_url, context=context, timeout=180) as image_response:
                return image_response.read()

        print(f"❌ OpenAI image response did not include b64_json or url: {json.dumps(result, indent=2)}")
        return None


def generate_openai_image(prompt: str) -> Optional[bytes]:
    api_key = get_env_value("OPENAI_API_KEY")
    if not api_key or api_key == "replace_with_your_openai_api_key":
        print("❌ Error: OPENAI_API_KEY is missing or still set to the placeholder value in backend/.env.")
        return None

    quality = get_env_value("OPENAI_IMAGE_QUALITY") or "medium"
    size = get_env_value("OPENAI_IMAGE_SIZE") or "1536x1024"

    for model in get_openai_image_models():
        try:
            image_bytes = generate_openai_image_with_model(prompt, api_key, model, size, quality)
            if image_bytes:
                print(f"✅ OpenAI image generation used model {model}")
                return image_bytes
        except error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"❌ OpenAI Image API Error for {model} ({e.code}): {err_msg}")
            if e.code not in (400, 403, 404):
                break
        except Exception as e:
            print(f"❌ OpenAI Image API Error for {model}: {e}")
            break

    return None


def extract_gemini_image(result: dict) -> Optional[bytes]:
    candidates = result.get("candidates", [])
    for candidate in candidates:
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            inline_data = part.get("inlineData") or part.get("inline_data")
            if inline_data and inline_data.get("data"):
                return base64.b64decode(inline_data["data"])
    return None


def generate_gemini_image_with_model(prompt: str, api_key: str, model: str) -> Optional[bytes]:
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"{prompt}\n\n"
                            "Generate only the background artwork for a 16:9 educational banner. "
                            "No readable text, no lettering, no logos, no watermark. "
                            "Leave a clean open center area for title overlay."
                        )
                    }
                ]
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )

    print(f"🚀 Generating background with Gemini Images API ({model})...")
    context = ssl._create_unverified_context()

    with request.urlopen(req, context=context, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
        image_bytes = extract_gemini_image(result)
        if image_bytes:
            return image_bytes

        print(f"❌ Gemini image response did not include image data: {json.dumps(result, indent=2)}")
        return None


def generate_gemini_image(prompt: str) -> Optional[bytes]:
    api_key = get_env_value("GEMINI_API_KEY")
    if not api_key or api_key == "replace_with_your_gemini_api_key":
        print("❌ Error: GEMINI_API_KEY is missing or still set to the placeholder value in backend/.env.")
        return None

    for model in get_gemini_image_models():
        try:
            image_bytes = generate_gemini_image_with_model(prompt, api_key, model)
            if image_bytes:
                print(f"✅ Gemini image generation used model {model}")
                return image_bytes
        except error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"❌ Gemini Image API Error for {model} ({e.code}): {err_msg}")
            if e.code not in (400, 403, 404, 429):
                break
        except Exception as e:
            print(f"❌ Gemini Image API Error for {model}: {e}")
            break

    return None


def fit_to_banner(image_bytes: bytes, width: int = 1280, height: int = 720) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    output = BytesIO()
    img.save(output, format="JPEG", quality=95)
    return output.getvalue()


def get_marketing_description_from_db(submission_id):
    """Fetch the AI-polished description for the banner."""
    try:
        from generate_images_free import DB_PARAMS
        import psycopg2
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
    if len(sys.argv) < 3:
        print("Usage: python3 generate_images_openai.py <title> <submission_id>")
        return

    display_title = sys.argv[1]
    submission_id = sys.argv[2]

    prompt = get_prompt_from_db(submission_id)
    if not prompt:
        print(f"❌ No prompt found for {submission_id}")
        return

    sub_data = get_submission_data(submission_id)
    duration = sub_data.get("duration")
    
    # NEW: Try to get the AI-polished description first
    ai_description = get_marketing_description_from_db(submission_id)
    tagline = ai_description if ai_description else sub_data.get("objectives", "")[:200]
    banner_card_copy = get_banner_card_copy_from_db(submission_id)
    
    style_id = sub_data.get("imageStyle", "illustrated")
    palette = sub_data.get("palette", [])

    background_bytes = generate_openai_image(prompt)
    if not background_bytes:
        print("⚠️ OpenAI image generation unavailable. Trying Gemini image generation fallback...")
        background_bytes = generate_gemini_image(prompt)

    if not background_bytes:
        print("❌ Paid image generation failed for both OpenAI and Gemini.")
        sys.exit(1)

    banner_background = fit_to_banner(background_bytes)
    final_image = compose_banner(
        banner_background, 
        display_title, 
        description=tagline, 
        duration=duration,
        style_id=style_id,
        palette=palette,
        submission=sub_data,
        banner_copy=banner_card_copy
    )
    save_image_to_db(submission_id, final_image)


if __name__ == "__main__":
    main()
