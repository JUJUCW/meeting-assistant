# Meeting Assistant

AI-powered meeting notes tool. Upload or record audio, get transcription + decisions + action items automatically.

## Features

- Upload audio files or record directly in browser
- Transcription via Whisper turbo (local, Traditional Chinese)
- AI analysis via Ollama — extracts decisions, action items, and meeting summary
- Background transcription with real-time progress indicator
- Meeting history with search, tags, and category filtering
- Edit titles, decisions, and action items inline
- Track and resolve action items across meetings
- Generate and regenerate AI meeting summary on demand
- Export meetings as Markdown, JSON, or .docx

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python / FastAPI |
| Transcription | openai-whisper (turbo, `language="zh"`) |
| AI Analysis | Ollama + `llama3.1:8b` |
| Storage | JSON files in `meetings/` |
| Frontend | Vue 3 + Vite + TypeScript |

## Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) running locally with `llama3.1:8b`

```bash
ollama pull llama3.1:8b
ollama serve
```

## Setup

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running

```bash
# Terminal 1 — backend
source venv/bin/activate
uvicorn server:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Usage

1. **Upload or record** audio on the home page
2. App navigates to history immediately; transcription runs in background
3. Progress banner shows elapsed / estimated time at the top of the list
4. When complete, the meeting appears with transcript, decisions, and action items
5. Click any meeting to view details, edit inline, or export

## Running Tests

```bash
source venv/bin/activate
pytest
```

## Project Structure

```
server.py          # FastAPI app, transcription job handling
analyzer.py        # Ollama AI analysis
storage.py         # JSON file storage
meetings/          # Meeting data (gitignored)
frontend/
  src/
    views/         # UploadView, HistoryView
    components/    # layout, upload, history, detail
    composables/   # useMeetings, useMeetingDetail, useTranscriptionJob, ...
    api/           # API client functions
    utils/         # export helpers
tests/             # pytest integration tests
```
