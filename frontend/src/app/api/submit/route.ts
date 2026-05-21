import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { prisma } from '@/lib/prisma';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const data = await request.json();
    const ROOT_DIR = process.cwd() + '/..';
    const SCRIPTS_DIR = ROOT_DIR + '/backend';
    
    // ── 1. Save to PostgreSQL ONLY ─────────────────────
    const submission = await prisma.submission.create({
      data: {
        title: data.title,
        formData: data,
      }
    });

    const submissionId = submission.id;

    // ── 2. RUN UNIFIED PROCESSING SCRIPT ─────
    // This script handles:
    // a. Data extraction (if JSON was uploaded)
    // b. Prompt generation
    // c. Image generation
    try {
      await execAsync(
        `python3 ${SCRIPTS_DIR}/process_submission.py ${submissionId}`,
        { cwd: SCRIPTS_DIR }
      );
    } catch (scriptError: any) {
      console.error('Python processing failed:', scriptError.stdout, scriptError.stderr);
      const details = [scriptError.stdout, scriptError.stderr, scriptError.message]
        .filter(Boolean)
        .join('\n');
      return NextResponse.json(
        {
          error: 'Banner generation failed during backend processing',
          details,
        },
        { status: 500 }
      );
    }

    // ── 3. Fetch the generated image from DB ───
    const asset = await prisma.marketingAsset.findFirst({
        where: {
            submissionId: submissionId,
            assetType: 'image_prompt'
        }
    });

    if (!asset || !asset.imageData) {
        return NextResponse.json({ error: "Banner generation failed to save to DB" }, { status: 500 });
    }

    const base64 = Buffer.from(asset.imageData).toString('base64');
    const mimeType = "image/jpeg";

    return NextResponse.json(
      {
         image: `data:${mimeType};base64,${base64}`,
         message: 'Banner generated and stored in Database!',
         submissionId: submissionId
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { message: 'Error processing request in database' },
      { status: 500 }
    );
  }
}
