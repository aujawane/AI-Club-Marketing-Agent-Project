#!/usr/bin/env python3
"""
Prompt Generator for Marketing Agent
Takes the marketing data and generates prompts suitable for image generation APIs.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def load_marketing_data(filepath: str = "marketing_data.json") -> Dict:
    """Load the marketing data from the exported JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_image_prompt(project: Dict, style: str = "modern educational") -> str:
    """
    Generate an image generation prompt from project data.

    Args:
        project: Project dictionary from marketing_data.json
        style: Visual style for the image (default: modern educational)

    Returns:
        A prompt string suitable for image generation
    """
    title = project.get('project_name', '')
    tagline = project.get('tagline', '')
    skills = project.get('skills_gained', [])
    tools = project.get('tools_and_platforms', [])

    # Build a compelling prompt
    prompt_parts = [
        f"Educational project: {title}",
        f"Topic: {tagline[:100]}..." if len(tagline) > 100 else f"Topic: {tagline}",
        f"Skills taught: {', '.join(skills[:5])}",
        f"Tools used: {', '.join(tools[:5])}",
        f"Style: {style}, clean design, professional, visually engaging"
    ]

    return "\n".join(prompt_parts)


def generate_social_media_post(project: Dict, platform: str = "instagram") -> str:
    """
    Generate a social media post from project data.

    Args:
        project: Project dictionary from marketing_data.json
        platform: Target platform (instagram, linkedin, twitter)

    Returns:
        A formatted social media post
    """
    title = project.get('project_name', '')
    description = project.get('tagline', '')
    skills = project.get('skills_gained', [])
    tasks = project.get('number_of_tasks', 0)

    if platform == "instagram":
        post = f"🎓 **{title}**\n\n"
        post += f"_{description}_\n\n"
        post += "✨ **What you'll learn:**\n"
        for skill in skills[:3]:
            post += f"• {skill}\n"
        post += f"\n📋 **{tasks} hands-on activities**\n"
        post += "#Education #Learning #Skills"

    elif platform == "linkedin":
        post = f"{title}\n\n"
        post += f"{description}\n\n"
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


def generate_email_blast(project: Dict) -> str:
    """
    Generate an email blast from project data.

    Args:
        project: Project dictionary from marketing_data.json

    Returns:
        A formatted email
    """
    title = project.get('project_name', '')
    description = project.get('full_description', '')
    skills = project.get('skills_gained', [])
    tasks = project.get('number_of_tasks', 0)
    points = project.get('total_points', 0)

    email = f"""Subject: New Project Available: {title}

Hi,

We're excited to introduce our latest educational project: **{title}**

**Overview:**
{description[:300]}...

**Key Features:**
- {tasks} engaging tasks
- {points} total points
- Hands-on learning with real-world applications

**Skills You'll Gain:**
"""

    for skill in skills:
        email += f"- {skill}\n"

    sections = project.get('sections', [])
    if sections:
        email += f"\n**What's Included:**\n"
        for section in sections[:3]:
            email += f"- {section['name']}: {section['tasks_count']} activities\n"

    email += "\nBest regards,\nThe Team"

    return email


def list_projects(data: Dict) -> None:
    """List all available projects."""
    print("\n" + "=" * 60)
    print("AVAILABLE PROJECTS")
    print("=" * 60)

    for i, project in enumerate(data.get('projects', []), 1):
        print(f"\n{i}. {project['project_name']}")
        print(f"   Tasks: {project['number_of_tasks']} | Points: {project['total_points']}")
        print(f"   Skills: {', '.join(project['skills_gained'][:5])}")


def main():
    """Main function to demonstrate usage."""
    # Load the data
    data_file = Path(__file__).parent / "marketing_data.json"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run ingest_data.py first.")
        return

    data = load_marketing_data(str(data_file))

    print("=" * 60)
    print("MARKETING PROMPT GENERATOR")
    print("=" * 60)
    print(f"\nLoaded {data['total_projects']} projects")

    # List projects
    list_projects(data)

    # Demo: Generate prompts for the first project
    if data.get('projects'):
        project = data['projects'][0]

        print("\n" + "=" * 60)
        print("SAMPLE OUTPUTS")
        print("=" * 60)

        # Image prompt
        print("\n📷 IMAGE GENERATION PROMPT:")
        print("-" * 40)
        print(generate_image_prompt(project))

        # Social media posts
        print("\n📱 INSTAGRAM POST:")
        print("-" * 40)
        print(generate_social_media_post(project, "instagram"))

        print("\n💼 LINKEDIN POST:")
        print("-" * 40)
        print(generate_social_media_post(project, "linkedin"))

        # Email
        print("\n📧 EMAIL BLAST:")
        print("-" * 40)
        print(generate_email_blast(project)[:500] + "...")


if __name__ == "__main__":
    main()