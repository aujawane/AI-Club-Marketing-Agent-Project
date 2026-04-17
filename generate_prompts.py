#!/usr/bin/env python3
"""
Prompt Generator for Marketing Agent
Takes the marketing data and generates prompts suitable for image generation APIs.
"""

import json
import sys
import os
import ssl
from urllib import request, error
from pathlib import Path
from typing import Dict, List, Optional


def get_api_key():
    """Get the Gemini API key from environment variable or .env file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=")[1].strip().strip("'").strip('"')
                        break
        except Exception:
            pass
    return api_key


def call_gemini_text(prompt: str, model: str = "gemini-flash-latest") -> Optional[str]:
    """Call the Gemini API for text generation."""
    api_key = get_api_key()
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
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
    
    try:
        with request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                print(f"❌ Gemini Error: Unexpected response structure: {json.dumps(result)}")
                return None
    except error.HTTPError as e:
        print(f"❌ Gemini API HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Gemini API Error: {str(e)}")
    return None


def generate_ai_image_prompt(project: Dict, submission: Optional[Dict] = None) -> str:
    """
    Use Gemini to generate a highly visual and creative image generation prompt.
    """
    title = submission.get('title') if submission and submission.get('title') else project.get('project_name', '')
    tagline = project.get('tagline', '')
    description = project.get('full_description', '')
    skills = ", ".join(project.get('skills_gained', []))
    
    style = submission.get('imageStyle', 'illustrated') if submission else "illustrated"
    palette = submission.get('palette', 'neutral') if submission else "neutral"

    llm_prompt = f"""
    Act as a professional Creative Director for an educational platform. 
    I need a highly detailed visual prompt for an image generation AI (like Midjourney or Stable Diffusion).
    
    PROJECT INFO:
    - Title: {title}
    - Tagline: {tagline}
    - Core Skills: {skills}
    - Brief: {description[:500]}...
    
    REQUIREMENTS:
    - Style: {style}
    - Color Palette: {palette}
    - Format: Wide cinematic banner (16:9)
    - Tone: Inspiring, modern, and educational
    - Content: Create a symbolic metaphor or a high-quality scene that represents the learning outcome. 
    - Constraints: NO TEXT in the image. Do not use words like "text", "typography", or "labels".
    
    OUTPUT:
    Provide only the visual prompt text, starting with the style and composition.
    """
    
    print(f"🤖 Consulting AI for a better visual prompt for '{title}'...")
    ai_prompt = call_gemini_text(llm_prompt)
    
    if ai_prompt:
        return ai_prompt.strip()
    
    # Fallback to the original method if AI fails
    print("⚠ AI Prompt generation failed, falling back to template.")
    return generate_image_prompt(project, submission)


def load_marketing_data(filepath: str = "marketing_data.json") -> Dict:
    """Load the marketing data from the exported JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_submission(filepath: str) -> Dict:
    """Load the form submission data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_matching_project(marketing_data: Dict, submission: Dict) -> Optional[Dict]:
    """
    Find a project in marketing_data that matches the submission.
    Matches by title (case-insensitive).
    """
    submission_title = submission.get('title', '').strip().lower()
    if not submission_title:
        return None

    for project in marketing_data.get('projects', []):
        if project.get('project_name', '').strip().lower() == submission_title:
            return project
    return None


def generate_image_prompt(project: Dict, submission: Optional[Dict] = None) -> str:
    """
    Generate a highly visual image generation prompt for APIs like Nano Banana.
    Optimized for wide banners.
    """
    title = submission.get('title') if submission and submission.get('title') else project.get('project_name', '')
    
    # Use submission data if available
    style = submission.get('imageStyle', 'illustrated') if submission else "illustrated"
    palette = submission.get('palette', 'neutral') if submission else "neutral"
    
    # Mapping styles to more descriptive visual keywords
    style_modifiers = {
        'illustrated': "stylized digital illustration, clean vector lines, modern flat design",
        'photoreal': "high-resolution photography, cinematic lighting, shallow depth of field, 8k",
        'watercolor': "dreamy watercolor painting, soft edges, artistic bleeding colors, hand-painted texture",
        'geometric': "abstract geometric composition, isometric perspective, sharp edges, mathematical symmetry"
    }
    
    visual_style = style_modifiers.get(style, "modern educational aesthetic")

    prompt_parts = [
        f"A wide cinematic banner with a {visual_style} representing '{title}'.",
        f"Theme: educational excellence and creativity.",
        f"Color Palette: dominated by {palette} tones.",
        "Elements: organized workspace, symbolic educational icons, bright and airy atmosphere.",
        "Atmosphere: inspiring, professional, and high-quality.",
        "Composition: wide angle, panoramic view, high contrast, masterpiece, 4k resolution."
    ]

    return " ".join(prompt_parts)


def generate_social_media_post(project: Dict, platform: str = "instagram", submission: Optional[Dict] = None) -> str:
    """
    Generate a social media post from project data and form submission.
    """
    title = submission.get('title') if submission and submission.get('title') else project.get('project_name', '')
    
    # Use submission duration or objectives if available
    description = submission.get('objectives') if submission and submission.get('objectives') else project.get('tagline', '')
    skills = submission.get('tags', []) if submission and submission.get('tags') else project.get('skills_gained', [])
    
    tone = submission.get('tone', 'professional') if submission else "professional"
    
    tasks = project.get('number_of_tasks', 0)

    # Simple tone adjustment prefix
    tone_prefixes = {
        'professional': "Direct and authoritative: ",
        'inspiring': "Motivational and visionary: ",
        'friendly': "Warm and accessible: ",
        'academic': "Rigorous and scholarly: ",
        'playful': "Fun and engaging: ",
        'creative': "Imaginative and exploratory: "
    }
    
    prefix = tone_prefixes.get(tone, "")

    if platform == "instagram":
        post = f"🎓 **{title}**\n\n"
        post += f"{prefix}_{description}_\n\n"
        post += "✨ **What you'll learn:**\n"
        for skill in skills[:3]:
            post += f"• {skill}\n"
        post += f"\n📋 **{tasks} hands-on activities**\n"
        post += f"Duration: {submission.get('duration') if submission else 'Flexible'}\n"
        post += "#Education #Learning #Skills"

    elif platform == "linkedin":
        post = f"{title}\n\n"
        post += f"{prefix}{description}\n\n"
        post += "🛠️ Skills covered:\n"
        for skill in skills[:5]:
            post += f"• {skill}\n"
        post += f"\n📊 {tasks} practical exercises\n"
        post += "#ProfessionalDevelopment #Education"

    else:  # twitter
        post = f"📚 New Project: {title}\n"
        post += f"{description[:100]}...\n"
        post += f"✨ {', '.join(skills[:3])} #EdTech"

    return post


def generate_email_blast(project: Dict, submission: Optional[Dict] = None) -> str:
    """
    Generate an email blast from project data and form submission.
    """
    title = submission.get('title') if submission and submission.get('title') else project.get('project_name', '')
    objectives = submission.get('objectives') if submission and submission.get('objectives') else project.get('full_description', '')
    skills = submission.get('tags', []) if submission and submission.get('tags') else project.get('skills_gained', [])
    duration = submission.get('duration') if submission and submission.get('duration') else "Flexible"
    
    tasks = project.get('number_of_tasks', 0)
    points = project.get('total_points', 0)

    email = f"""Subject: New Project Available: {title}

Hi,

We're excited to introduce our latest educational project: **{title}**

**Overview:**
{objectives[:500]}

**Quick Info:**
- Duration: {duration}
- {tasks} engaging tasks
- {points} total points
- Hands-on learning with real-world applications

**Skills You'll Gain:**
"""

    for skill in skills:
        email += f"- {skill}\n"

    email += "\nBest regards,\nThe Team"

    return email


def save_prompts_to_json(title: str, outputs: Dict[str, str], filepath: str = "generated_prompts.json"):
    """Save the generated prompts to a JSON file."""
    output_path = Path(filepath)
    
    # Load existing data if file exists
    data = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = []

    # Create new entry
    entry = {
        "title": title,
        "timestamp": Path("marketing_data.json").stat().st_mtime if Path("marketing_data.json").exists() else 0, # Placeholder or use datetime
        "generated_at": str(Path("marketing_data.json").stat().st_mtime), # Using a timestamp would be better
        "prompts": outputs
    }
    
    # We'll use a simpler format as requested: title and prompt field for each
    new_entries = []
    for prompt_type, content in outputs.items():
        new_entries.append({
            "title": f"{title} ({prompt_type})",
            "prompt": content
        })

    data.extend(new_entries)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(outputs)} prompts to {filepath}")


def main():
    """Main function to demonstrate usage."""
    # Load the data
    data_file = Path(__file__).parent / "marketing_data.json"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run ingest_data.py first.")
        return

    data = load_marketing_data(str(data_file))
    
    submission = None
    project = None

    # Check if a submission file was provided
    if len(sys.argv) > 1:
        submission_path = sys.argv[1]
        try:
            submission = load_submission(submission_path)
            project = find_matching_project(data, submission)
            if project:
                print(f"✓ Matched submission '{submission.get('title')}' with project '{project['project_name']}'")
            else:
                print(f"⚠ Could not find a matching project for '{submission.get('title')}'")
                print("Falling back to the first available project for demonstration.")
                project = data['projects'][0] if data.get('projects') else None
        except Exception as e:
            print(f"Error loading submission: {e}")
            project = data['projects'][0] if data.get('projects') else None
    else:
        project = data['projects'][0] if data.get('projects') else None

    if not project:
        print("No project data available.")
        return

    print("=" * 60)
    print("MARKETING PROMPT GENERATOR (WITH FORM INTEGRATION)")
    print("=" * 60)

    # Process all projects if no submission provided
    projects_to_process = [project] if submission else data.get('projects', [])
    
    for proj in projects_to_process:
        print(f"\n--- Processing Project: {proj['project_name']} ---")
        
        # Collect outputs
        title = submission.get('title') if (submission and proj == project) else proj['project_name']
        
        # Pass the submission context if we're processing the matched project
        current_submission = submission if (submission and proj == project) else None
        
        image_prompt = generate_ai_image_prompt(proj, current_submission)
        insta_post = generate_social_media_post(proj, "instagram", current_submission)
        linkedin_post = generate_social_media_post(proj, "linkedin", current_submission)
        email_blast = generate_email_blast(proj, current_submission)

        # Save to JSON
        outputs = {
            "Image Prompt": image_prompt,
            "Instagram Post": insta_post,
            "LinkedIn Post": linkedin_post,
            "Email Blast": email_blast
        }
        save_prompts_to_json(title, outputs)


if __name__ == "__main__":
    main()