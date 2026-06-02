#!/usr/bin/env python3
import json
import sys
import os
import subprocess
import psycopg2
from pathlib import Path
from ingest_data import DataIngestor

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "marketing_agent",
    "user": "user",
    "password": "password",
    "port": "5434"
}

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

def update_submission_in_db(submission_id, title, form_data):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute(
            "UPDATE \"Submission\" SET title = %s, \"formData\" = %s WHERE id = %s",
            (title, json.dumps(form_data), submission_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Updated submission {submission_id} with extracted data")
    except Exception as e:
        print(f"❌ DB Update Error: {e}")

def clean_title(value):
    return " ".join(str(value or "").lower().split())

def find_matching_metadata(uploaded_json, json_folder):
    """Find sibling *_metadata.json for an uploaded project by matching title."""
    uploaded_title = uploaded_json.get("title")
    if not uploaded_title and isinstance(uploaded_json.get("description"), dict):
        uploaded_title = uploaded_json.get("description", {}).get("name")

    normalized_uploaded_title = clean_title(uploaded_title)
    if not normalized_uploaded_title:
        return {}

    for project_path in Path(json_folder).glob("*.json"):
        if project_path.name.endswith("_metadata.json") or project_path.name.startswith("_"):
            continue

        try:
            with open(project_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)
        except Exception:
            continue

        candidate_title = project_data.get("title")
        if not candidate_title and isinstance(project_data.get("description"), dict):
            candidate_title = project_data.get("description", {}).get("name")

        if clean_title(candidate_title) != normalized_uploaded_title:
            continue

        metadata_path = project_path.with_name(f"{project_path.stem}_metadata.json")
        if not metadata_path.exists():
            return {}

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                print(f"✅ Matched metadata file: {metadata_path.name}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load matched metadata {metadata_path.name}: {e}")
            return {}

    return {}

def run_script(args):
    result = subprocess.run(args, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        script_name = Path(args[1]).name if len(args) > 1 else args[0]
        print(f"❌ {script_name} failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 process_submission.py <submission_id>")
        return

    submission_id = sys.argv[1]
    form_data = get_submission_from_db(submission_id)
    
    if not form_data:
        print(f"❌ Submission {submission_id} not found")
        return

    # Check if there is uploaded JSON to process
    uploaded_json = form_data.get('uploadedJson')
    if uploaded_json:
        print(f"📂 Found uploaded JSON. Extracting details...")
        ingestor = DataIngestor(str(Path(__file__).parent / "data" / "JSON_files"))
        project = ingestor.ingest_data(uploaded_json)
        
        if project:
            metadata = find_matching_metadata(
                uploaded_json,
                Path(__file__).parent / "data" / "JSON_files"
            )
            # ONLY fill if missing or empty in form_data
            # This ensures that if the user EDITed the form, we keep their edits.
            
            # Metadata merge
            if metadata:
                uploaded_json.update({k: v for k, v in metadata.items() if v is not None})
                form_data['uploadedJson'] = uploaded_json
                if not form_data.get('duration'):
                    form_data['duration'] = metadata.get('duration', '')
                if not form_data.get('grade'):
                    form_data['grade'] = metadata.get('audience', '')

            # Form fields
            if not form_data.get('title'):
                form_data['title'] = project.title
                print(f"  - Populated missing title: {project.title}")

            if not form_data.get('objectives'):
                if project.learning_objectives:
                    form_data['objectives'] = "\n".join(project.learning_objectives)
                elif metadata.get('outcome'):
                    form_data['objectives'] = metadata['outcome']
                elif metadata.get('pitch'):
                    form_data['objectives'] = metadata['pitch']
                print("  - Populated missing objectives")

            if not form_data.get('tags') or len(form_data.get('tags', [])) == 0:
                if project.tags:
                    form_data['tags'] = project.tags
                    print(f"  - Populated missing tags: {project.tags}")
            
            # Update DB with final form_data (prioritizing manual edits)
            update_submission_in_db(submission_id, form_data.get('title', project.title), form_data)
        else:
            print("⚠️ Could not extract project data from JSON")

    # Now trigger the generation scripts
    script_dir = Path(__file__).parent
    
    print("🤖 Triggering prompt generation...")
    run_script(["python3", str(script_dir / "generate_prompts.py"), submission_id])
    
    print("🎨 Triggering OpenAI image generation...")
    title = form_data.get('title', 'Project')
    run_script(["python3", str(script_dir / "generate_images_openai.py"), title, submission_id])

    print("✨ Submission processing complete!")

if __name__ == "__main__":
    main()
