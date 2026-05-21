# AI-Club Marketing Agent

AI-powered marketplace listing optimizer that transforms project descriptions into structured, conversion-ready listings.

## Project Structure

- `frontend/`: Next.js application with Tailwind CSS and Prisma.
- `backend/`: Python scripts for prompt and image generation, and database configuration.

## Prerequisites

- **Docker & Docker Compose**: For the PostgreSQL database.
- **Node.js** (v18+): For the frontend.
- **Python 3.x**: For the backend AI scripts.
- **npm** or **yarn**: Package manager.

## Setup Instructions

### 1. Database Setup
The application requires a PostgreSQL database.
```bash
start docker on your computer
cd backend
docker-compose up -d
```
*The database will be available at `localhost:5434`.*

### 2. Python Environment Setup
The frontend calls Python scripts for generation. You must install the required Python packages:
```bash
# It is recommended to use a virtual environment
pip3 install psycopg2-binary Pillow
```

### 3. Backend Configuration
Create a `.env` file in the `backend/` directory to enable AI features:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_PROMPT_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_QUALITY=medium
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

`OPENAI_API_KEY` is used by `backend/generate_prompts.py` to run a prompt-writing agent that improves image prompts before banner generation. `backend/generate_images_openai.py` tries OpenAI image generation first, then falls back to Gemini image generation with `GEMINI_API_KEY` if the OpenAI project does not have image-model access.

### 4. Frontend Setup
Navigate to the `frontend` directory, install dependencies, and configure the environment:
```bash
cd ../frontend
npm install
```

Create a `.env` file in the `frontend/` directory:
```env
DATABASE_URL="postgresql://user:password@localhost:5434/marketing_agent?schema=public"
```

### 5. Database Migration
Initialize the database and generate the Prisma client:
```bash
npx prisma migrate dev --name init
```

### 6. Run the Application
Start the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Troubleshooting

- **Database Connection**: Ensure Docker is running. If you change the database port in `docker-compose.yml`, update the `DATABASE_URL` and the `DB_PARAMS` in the Python scripts in `backend/`.
- **Python Scripts**: The frontend expects `python3` to be available in your PATH. If you use `python` or a specific path, you may need to update `frontend/src/app/api/submit/route.ts`.
- **Image Generation**: Ensure you have an active internet connection as the app uses external APIs (Gemini and Pollinations.ai) for generation.
