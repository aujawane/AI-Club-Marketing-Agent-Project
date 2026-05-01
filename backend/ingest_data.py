#!/usr/bin/env python3
"""
Data Ingestion Script for Marketing Agent
Extracts meaningful data from JSON project files for prompt generation.
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Any
from datetime import datetime


@dataclass
class VideoResource:
    """Represents a video resource in a project."""
    title: str
    url: str
    description: str = ""


@dataclass
class Objective:
    """Represents a task/objective within a project section."""
    title: str
    description: str
    points: int
    evaluation_type: str


@dataclass
class Section:
    """Represents a section within a project."""
    title: str
    description: str
    objectives: List[Objective] = field(default_factory=list)


@dataclass
class Project:
    """Represents a complete project with all extracted data."""
    title: str
    slug: str
    description: str
    status: str
    version: int
    tags: List[str]
    sections: List[Section] = field(default_factory=list)
    video_resources: List[VideoResource] = field(default_factory=list)
    total_objectives: int = 0
    total_points: int = 0
    skills_taught: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    source_file: str = ""
    # Additional metadata for marketing
    audience: str = ""
    duration: str = ""
    pitch: str = ""
    outcome: str = ""
    difficulty: str = ""
    prerequisites: str = ""
    certification: str = ""
    pricing: Optional[float] = None


class DataIngestor:
    """Ingests JSON project files and extracts meaningful data."""

    def __init__(self, json_folder: str):
        self.json_folder = Path(json_folder)
        self.projects: List[Project] = []
        self.project_metadata = self._load_central_metadata()

    def _load_central_metadata(self) -> dict:
        """Load the central project_metadata.json file."""
        metadata_path = self.json_folder.parent / "project_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('projects', {})
            except Exception as e:
                print(f"Warning: Could not load project_metadata.json: {e}")
        return {}

    def load_json_file(self, filepath: Path) -> Optional[dict]:
        """Load a JSON file and return its contents."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {filepath.name}: {e}")
            return None

    def clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Replace HTML entities
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        # Clean up whitespace
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def get_nested(self, data: Union[dict, str], *keys, default="") -> Any:
        """Safely get nested dictionary values."""
        if isinstance(data, str):
            return default
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current if current is not None else default

    def extract_video_resources(self, data: dict) -> List[VideoResource]:
        """Extract video resources from project data."""
        videos = []
        resources = self.get_nested(data, 'resources', default=[])

        for resource in resources:
            if isinstance(resource, dict) and resource.get('kind') == 'video':
                videos.append(VideoResource(
                    title=resource.get('title', ''),
                    url=resource.get('target', ''),
                    description=resource.get('description', '')
                ))

        return videos

    def extract_sections(self, data: dict) -> List[Section]:
        """Extract sections and their objectives from project data."""
        sections = []
        section_data = self.get_nested(data, 'sections', default=[])

        for sec in section_data:
            if not isinstance(sec, dict):
                continue

            objectives = []
            for obj in sec.get('objectives', []):
                if not isinstance(obj, dict):
                    continue
                objectives.append(Objective(
                    title=obj.get('title', ''),
                    description=self.clean_html(obj.get('description', '')),
                    points=obj.get('points', 0),
                    evaluation_type=obj.get('evaluation_type', 'platform')
                ))

            sections.append(Section(
                title=sec.get('title', ''),
                description=self.clean_html(sec.get('description', '')),
                objectives=objectives
            ))

        return sections

    def extract_skills_taught(self, data: dict, sections: List[Section]) -> List[str]:
        """Extract skills that are taught in this project."""
        skills = set()

        # Common skills to look for in descriptions
        skill_keywords = [
            'Google Sheets', 'Google Docs', 'Spreadsheet', 'Formulas',
            'Financial literacy', 'Budgeting', 'Net worth', 'Assets', 'Liabilities',
            'Cornell Notes', 'Note-taking', 'Essentialism', 'Productivity',
            'Population pyramid', 'Demographics', 'Data analysis', 'Infographic',
            'Resume', 'Professional writing', 'Career planning',
            'Latitude', 'Longitude', 'Geography', 'GIS', 'Mapping',
            'AI', 'Artificial Intelligence', 'Prompt', 'CTF',
            'Research', 'Critical thinking', 'Reflection',
            'Video editing', 'Presentation', 'Slideshow',
            'Calculator', 'Excel', 'Data entry', 'Formulas',
            'Communication', 'Leadership', 'Teamwork'
        ]

        # Search in title and description
        title = self.get_nested(data, 'title', default='')
        desc = self.get_nested(data, 'description', default='')

        if isinstance(desc, dict):
            desc = desc.get('body', '')

        text_to_search = f"{title} {desc}".lower()

        # Search in sections
        for section in sections:
            text_to_search += ' ' + section.description.lower()
            for obj in section.objectives:
                text_to_search += ' ' + obj.description.lower()

        for skill in skill_keywords:
            if skill.lower() in text_to_search:
                skills.add(skill)

        return sorted(list(skills))

    def extract_tools_used(self, data: dict) -> List[str]:
        """Extract tools and platforms used in the project."""
        tools = set()

        tool_keywords = [
            'Google Sheets', 'Google Docs', 'Google Slides', 'Google Maps',
            'YouTube', 'NotebookLM', 'GradeFlow', 'Excel', 'Microsoft Office',
            'AI', 'ChatGPT', 'Claude', 'Google', 'Spreadsheet', 'Doc', 'Slides'
        ]

        # Search in entire JSON as string
        text_to_search = json.dumps(data).lower()

        for tool in tool_keywords:
            if tool.lower() in text_to_search:
                tools.add(tool)

        return sorted(list(tools))

    def extract_learning_objectives(self, data: dict, sections: List[Section]) -> List[str]:
        """Extract learning objectives from the project."""
        objectives = []

        # Extract from objectives descriptions
        for section in sections:
            for obj in section.objectives:
                # Look for sentences that describe what students will learn
                desc_text = obj.description
                if 'will' in desc_text.lower() or 'learn' in desc_text.lower():
                    # Take first sentence as a learning objective
                    sentences = desc_text.split('.')
                    if sentences and len(sentences[0]) > 20:
                        obj_clean = sentences[0].strip()
                        if obj_clean not in objectives:
                            objectives.append(obj_clean)

        return objectives[:5]  # Limit to 5 learning objectives

    def is_valid_project(self, data: Optional[dict]) -> bool:
        """Check if the JSON file represents a valid project."""
        if data is None:
            return False

        # Check for project-like fields
        has_title = 'title' in data
        has_sections = 'sections' in data and isinstance(data.get('sections'), list)
        has_resources = 'resources' in data and isinstance(data.get('resources'), list)

        # MarketPlaceObject has different structure
        if 'title' in data and 'description' in data and isinstance(data.get('description'), dict):
            return True

        return has_title or has_sections or has_resources

    def ingest_file(self, filepath: Path) -> Optional[Project]:
        """Ingest a single JSON file and return a Project object."""
        data = self.load_json_file(filepath)

        if data is None:
            print(f"  Skipping (empty/invalid): {filepath.name}")
            return None

        # Skip non-project files (options files, etc.)
        if not self.is_valid_project(data):
            print(f"  Skipping (not a project file): {filepath.name}")
            return None

        try:
            # Get title - handle different structures
            title = data.get('title', '')

            # For marketPlaceObject, title is in description.name
            if not title and isinstance(data.get('description'), dict):
                title = data.get('description', {}).get('name', 'Untitled')

            if not title:
                title = 'Untitled'

            # Get description - handle different structures
            description = data.get('description', '')
            if isinstance(description, dict):
                description = description.get('body', '')
            description = self.clean_html(description)

            # Get slug/status/version
            slug = data.get('slug', title.lower().replace(' ', '-'))
            status = data.get('status', 'active')
            if not status:
                status = data.get('description', {}).get('record_type', 'active')
            version = data.get('version', 1)
            tags = data.get('tags', [])

            # Extract sections and objectives
            sections = self.extract_sections(data)
            video_resources = self.extract_video_resources(data)

            # Calculate totals
            total_objectives = sum(len(s.objectives) for s in sections)
            total_points = sum(obj.points for section in sections for obj in section.objectives)

            # Extract skills, tools, and learning objectives
            skills_taught = self.extract_skills_taught(data, sections)
            tools_used = self.extract_tools_used(data)
            learning_objectives = self.extract_learning_objectives(data, sections)

            project = Project(
                title=title,
                slug=slug,
                description=description,
                status=status,
                version=version,
                tags=tags,
                sections=sections,
                video_resources=video_resources,
                total_objectives=total_objectives,
                total_points=total_points,
                skills_taught=skills_taught,
                learning_objectives=learning_objectives,
                tools_used=tools_used,
                source_file=filepath.name
            )

            return project

        except Exception as e:
            print(f"  Error processing {filepath.name}: {e}")
            return None

    def ingest_all(self) -> List[Project]:
        """Ingest all JSON files in the folder."""
        json_files = list(self.json_folder.glob('*.json'))

        for filepath in json_files:
            project = self.ingest_file(filepath)
            if project:
                self.projects.append(project)
                print(f"✓ Ingested: {project.title}")

        return self.projects

    def to_marketing_dict(self, project: Project) -> dict:
        """Convert project to a dictionary optimized for marketing prompts."""
        return {
            "project_name": project.title,
            "tagline": project.description[:150] + "..." if len(project.description) > 150 else project.description,
            "full_description": project.description,
            "what_students_learn": project.learning_objectives,
            "skills_gained": project.skills_taught,
            "tools_and_platforms": project.tools_used,
            "number_of_tasks": project.total_objectives,
            "total_points": project.total_points,
            "sections": [
                {
                    "name": section.title,
                    "description": section.description,
                    "tasks_count": len(section.objectives),
                    "tasks": [
                        {
                            "title": obj.title,
                            "description": obj.description[:200] + "..." if len(obj.description) > 200 else obj.description,
                            "points": obj.points
                        }
                        for obj in section.objectives
                    ]
                }
                for section in project.sections
            ],
            "videos": [
                {"title": vid.title, "url": vid.url}
                for vid in project.video_resources
            ],
            "source": project.source_file
        }

    def export_for_prompts(self, output_file: str = "marketing_data.json"):
        """Export all projects in a format ready for marketing prompt generation."""
        marketing_data = {
            "export_date": datetime.now().isoformat(),
            "total_projects": len(self.projects),
            "projects": [self.to_marketing_dict(p) for p in self.projects]
        }

        output_path = self.json_folder.parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(marketing_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Exported to: {output_path}")
        return marketing_data

    def load_metadata(self, project: Project) -> dict:
        """
        Load optional metadata file for a project.
        Looks for a file named: <source_file_base>_metadata.json
        """
        # Get base name without .json extension
        base_name = project.source_file.replace('.json', '')
        metadata_file = self.json_folder / f"{base_name}_metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                print(f"  ✓ Found metadata for: {project.title}")
                return metadata
            except (json.JSONDecodeError, IOError) as e:
                print(f"  ⚠ Error loading metadata: {e}")
                return {}

        return {}

    def enrich_with_metadata(self, project: Project) -> dict:
        """Enrich project data with metadata if available."""
        # Try to get metadata from individual file or central project_metadata.json
        metadata = self.load_metadata(project)
        central_meta = self.project_metadata.get(project.source_file, {})
        
        # Merge them, central_meta takes precedence for shared fields
        combined_metadata = {**metadata, **central_meta}
        
        project_dict = self.to_marketing_dict(project)

        # Update project name if a title is specified in metadata
        if combined_metadata.get('title'):
            project_dict['project_name'] = combined_metadata['title']

        # Add metadata fields (only if they have values)
        if combined_metadata:
            project_dict['metadata'] = {
                'audience': combined_metadata.get('audience'),
                'duration': combined_metadata.get('duration'),
                'pitch': combined_metadata.get('pitch'),
                'outcome': combined_metadata.get('outcome'),
                'difficulty': combined_metadata.get('difficulty'),
                'prerequisites': combined_metadata.get('prerequisites'),
                'certification': combined_metadata.get('certification'),
                'pricing': combined_metadata.get('pricing')
            }

            # Update tagline with pitch if available
            if combined_metadata.get('pitch'):
                project_dict['tagline'] = combined_metadata['pitch']

        return project_dict

    def export_with_metadata(self, output_file: str = "marketing_data.json"):
        """Export all projects with optional metadata."""
        marketing_data = {
            "export_date": datetime.now().isoformat(),
            "total_projects": len(self.projects),
            "projects": [self.enrich_with_metadata(p) for p in self.projects]
        }

        output_path = self.json_folder.parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(marketing_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Exported to: {output_path}")
        return marketing_data

    def generate_summary_report(self) -> str:
        """Generate a summary report of all ingested projects."""
        report = []
        report.append("=" * 60)
        report.append("PROJECT DATA INGESTION SUMMARY")
        report.append("=" * 60)
        report.append(f"\nTotal Projects Ingested: {len(self.projects)}")
        report.append(f"Total Tasks/Objectives: {sum(p.total_objectives for p in self.projects)}")
        report.append(f"Total Points: {sum(p.total_points for p in self.projects)}")

        report.append("\n" + "-" * 60)
        report.append("ALL PROJECTS:")
        report.append("-" * 60)

        for i, project in enumerate(self.projects, 1):
            report.append(f"\n{i}. {project.title}")
            report.append(f"   Source: {project.source_file}")
            report.append(f"   Tasks: {project.total_objectives} | Points: {project.total_points}")
            if project.skills_taught:
                report.append(f"   Skills: {', '.join(project.skills_taught[:5])}")
            if project.tools_used:
                report.append(f"   Tools: {', '.join(project.tools_used)}")

        return "\n".join(report)


def main():
    """Main function to run the ingestion script."""
    # Set up paths
    script_dir = Path(__file__).parent
    json_folder = script_dir / "data" / "JSON_files"

    print("Starting data ingestion...")
    print(f"Reading from: {json_folder}\n")

    # Initialize ingestor
    ingestor = DataIngestor(str(json_folder))

    # Ingest all files
    projects = ingestor.ingest_all()

    # Export for marketing prompts (with optional metadata)
    marketing_data = ingestor.export_with_metadata()

    # Print summary
    print(ingestor.generate_summary_report())

    return marketing_data


if __name__ == "__main__":
    main()
