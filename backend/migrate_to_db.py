import os
import json
import psycopg2
from pathlib import Path
import uuid

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "marketing_agent",
    "user": "user",
    "password": "password",
    "port": "5433"
}

def migrate_projects():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        print("Connected to PostgreSQL")

        json_folder = Path("JSON_files")
        
        # Get all project files (not metadata files)
        project_files = [f for f in json_folder.glob("*.json") 
                        if not f.name.endswith("_metadata.json") 
                        and f.name not in ["course_options.json", "grade_level_options.json", 
                                          "label_options.json", "school_level_options.json"]]

        for project_file in project_files:
            print(f"Migrating {project_file.name}...")
            
            with open(project_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Try to find metadata
            metadata_file = json_folder / f"{project_file.stem}_metadata.json"
            metadata = None
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            title = content.get('title', project_file.stem)
            slug = content.get('slug', project_file.stem.lower().replace(' ', '-'))
            
            # Check if exists
            cur.execute("SELECT id FROM \"Project\" WHERE slug = %s", (slug,))
            if cur.fetchone():
                print(f"Project with slug {slug} already exists, skipping.")
                continue

            # Insert
            cur.execute(
                "INSERT INTO \"Project\" (id, title, slug, content, metadata, \"createdAt\", \"updatedAt\") "
                "VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                (str(uuid.uuid4()), title, slug, json.dumps(content), json.dumps(metadata) if metadata else None)
            )
        
        conn.commit()
        print("Migration completed successfully.")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_projects()
