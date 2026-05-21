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
            # Update form_data with extracted values
            form_data['title'] = project.title
            form_data['objectives'] = "\n".join(project.learning_objectives)
            form_data['tags'] = project.tags
            # We don't overwrite manual style choices (tone, imageStyle, palette)
            
            # Update DB
            update_submission_in_db(submission_id, project.title, form_data)
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
