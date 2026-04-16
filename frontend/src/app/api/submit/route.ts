import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // Create a unique filename using timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `submission-${timestamp}.json`;
    
    // Define the path to save the JSON file
    // We'll save it in a 'submissions' folder at the project root
    const submissionsDir = path.join(process.cwd(), '..', 'submissions');
    
    // Ensure the directory exists
    if (!fs.existsSync(submissionsDir)) {
      fs.mkdirSync(submissionsDir, { recursive: true });
    }
    
    const filePath = path.join(submissionsDir, filename);
    
    // Write the data to the file
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    
    return NextResponse.json({ message: 'Submission saved successfully', filename }, { status: 200 });
  } catch (error) {
    console.error('Error saving submission:', error);
    return NextResponse.json({ message: 'Error saving submission' }, { status: 500 });
  }
}
