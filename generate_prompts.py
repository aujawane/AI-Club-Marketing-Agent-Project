#!/usr/bin/env python3
"""
Prompt Generator for Marketing Agent
Takes the marketing data and generates prompts suitable for image generation APIs.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


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
    Generate an image generation prompt from project data and form submission.
    """
    title = submission.get('title') if submission and submission.get('title') else project.get('project_name', '')
    tagline = project.get('tagline', '')
    
    # Use submission data if available
    style = submission.get('imageStyle', 'modern educational') if submission else "modern educational"
    palette = submission.get('palette', 'neutral') if submission else "neutral"
    
    skills = submission.get('tags', []) if submission and submission.get('tags') else project.get('skills_gained', [])
    tools = project.get('tools_and_platforms', [])

    prompt_parts = [
        f"Educational project: {title}",
        f"Topic: {tagline}",
        f"Skills taught: {', '.join(skills[:5])}",
        f"Tools used: {', '.join(tools[:5])}",
        f"Style: {style}",
        f"Color Palette: {palette}",
        "Composition: clean design, professional, visually engaging"
    ]

    return "\n".join(prompt_parts)


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

    # Demo: Generate prompts
    print("\n" + "=" * 60)
    print("GENERATED OUTPUTS")
    print("=" * 60)

    # Image prompt
    print("\n📷 IMAGE GENERATION PROMPT:")
    print("-" * 40)
    print(generate_image_prompt(project, submission))

    # Social media posts
    print("\n📱 INSTAGRAM POST:")
    print("-" * 40)
    print(generate_social_media_post(project, "instagram", submission))

    print("\n💼 LINKEDIN POST:")
    print("-" * 40)
    print(generate_social_media_post(project, "linkedin", submission))

    # Email
    print("\n📧 EMAIL BLAST:")
    print("-" * 40)
    print(generate_email_blast(project, submission))


if __name__ == "__main__":
    main()