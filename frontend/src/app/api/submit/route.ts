import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // ── 1. Save JSON ─────────────────────────────
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `submission-${timestamp}.json`;
    
    const ROOT_DIR = path.join(process.cwd(), '..');
    const submissionsDir = path.join(ROOT_DIR, 'submissions');

    if (!fs.existsSync(submissionsDir)) {
      fs.mkdirSync(submissionsDir, { recursive: true });
    }
    
    const filePath = path.join(submissionsDir, filename);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));

    // ── 2. RUN PYTHON SCRIPTS (PUT THEM HERE) ─────

    const SCRIPTS_DIR = ROOT_DIR;

    // Script 1
    await execAsync(`python3 ${SCRIPTS_DIR}/ingest_data.py`, {
      cwd: SCRIPTS_DIR,
    });

    // Script 2 (use the file you JUST created)
    await execAsync(
      `python3 ${SCRIPTS_DIR}/generate_prompts.py submissions/${filename}`,
      { cwd: SCRIPTS_DIR }
    );

    // Script 3
    await execAsync(`python3 ${SCRIPTS_DIR}/generate_images_free.py`, {
      cwd: SCRIPTS_DIR,
    });

    // step 3.5 -> Find the latest file in /banners
  const bannersDir = path.join(ROOT_DIR, "banners");
  const files = fs.readdirSync(bannersDir)
    .filter(f => f.endsWith(".jpg") || f.endsWith(".png"))
    .map(f => ({
      name: f,
      time: fs.statSync(path.join(bannersDir, f)).mtimeMs,
    }))
    .sort((a, b) => b.time - a.time); // newest first

  if (!files.length) {
    return NextResponse.json({ error: "No banner found" }, { status: 404 });
  }

  const latestFile = path.join(bannersDir, files[0].name);
  const imageBuffer = fs.readFileSync(latestFile);
  const base64 = imageBuffer.toString("base64");
  const mimeType = files[0].name.endsWith(".png") ? "image/png" : "image/jpeg";

    // ── 3. Return response AFTER scripts finish ───
    return NextResponse.json(
      {
         image: `data:${mimeType};base64,${base64}`,
         message: 'Submission + banners generated',
        filename: files[0].name,
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { message: 'Error saving submission or running scripts' },
      { status: 500 }
    );
  }
}