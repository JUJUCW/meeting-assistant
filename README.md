# Meeting Assistant

AI-powered meeting notes and document translation tool. Upload or record audio to get transcription, decisions, and action items automatically. Translate PDF documents to Traditional Chinese offline.

## Features

### Meeting Assistant
- Upload audio files or record directly in browser
- Transcription via Whisper turbo (local, Traditional Chinese)
- AI analysis via Ollama — extracts decisions, action items, and meeting summary
- Background transcription with real-time progress indicator
- Meeting history with search, tags, and category filtering
- Pagination with configurable page size (10 / 20 / 50)
- Edit titles, decisions, and action items inline
- Track and resolve action items across meetings
- Generate and regenerate AI meeting summary on demand
- Export meetings as Markdown, JSON, or .docx

### PDF Document Translation
- Translate PDF documents to Traditional Chinese
- Auto-detect source language
- Supports text-based PDFs and scanned PDFs (via EasyOCR)
- Download translated file as PDF or DOCX
- DOCX output preserves heading hierarchy based on font sizes
- Translation history persists across restarts
- Fully offline — no external APIs required

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python / FastAPI |
| Transcription | faster-whisper (turbo, `language="zh"`) |
| AI Analysis & Translation | Ollama + `llama3.1:8b` |
| PDF Processing | PyMuPDF (fitz) |
| OCR | EasyOCR (offline, for scanned PDFs) |
| Storage | JSON files in `meetings/` and `translations/` |
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

### Meeting Assistant
1. **Upload or record** audio on the home page
2. App navigates to history immediately; transcription runs in background
3. Progress banner shows elapsed / estimated time at the top of the list
4. When complete, the meeting appears with transcript, decisions, and action items
5. Click any meeting to view details, edit inline, or export

### PDF Translation
1. Click **文件翻譯 →** on the home page
2. Drag and drop a PDF or click to select
3. Click **開始翻譯** — progress updates in real time
4. Download the result as **PDF** or **DOCX**
5. Past translations are listed below with download and delete buttons

> First use of scanned PDF (OCR) will download EasyOCR language models (~500 MB) — requires internet connection once.

## Running Tests

```bash
source venv/bin/activate
pytest
```

## Project Structure

```
server.py            # FastAPI app, transcription and translation job handling
analyzer.py          # Ollama AI analysis
storage.py           # JSON file storage for meetings
pdf_translator.py    # PDF translation pipeline (extract, OCR, translate, rebuild)
meetings/            # Meeting data (gitignored)
translations/        # Translated PDF/DOCX outputs and metadata (gitignored)
frontend/
  src/
    views/           # UploadView, HistoryView, TranslateView
    components/      # layout, upload, history, detail
    composables/     # useMeetings, useMeetingDetail, useTranscriptionJob, ...
    api/             # API client functions (meetings, transcription, translate)
    utils/           # export helpers
tests/               # pytest integration tests
```
