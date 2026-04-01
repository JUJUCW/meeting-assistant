# Meeting Assistant — Design Spec
**Date:** 2026-03-28

## Overview

A browser-based meeting assistant tool that records or accepts uploaded audio, transcribes it using a local Whisper model, and allows the user to tag segments as decisions or action items, then outputs a formatted meeting summary.

## Architecture

Two components:

- **Frontend** (`index.html`) — Step-by-step wizard UI, pure HTML/CSS/JS
- **Backend** (`server.py`) — Python FastAPI server bridging the browser to local Whisper

Frontend communicates with the backend at `http://localhost:8000`.

## User Flow (4 Steps)

### Step 1 — Record / Upload
- Record audio via browser (MediaRecorder API)
- Or upload an existing audio file (supported formats: mp3, wav, m4a)
- Submit to trigger transcription

### Step 2 — Transcribing
- Progress indicator while Whisper processes the audio
- Frontend polls `GET /status/{job_id}` until complete
- On error: show message + retry button

### Step 3 — Review & Tag
- Display transcript as a list of paragraphs/segments
- Each segment can be tagged: **決議 (Decision)** / **待辦 (Action Item)** / untagged
- Tags are toggled by clicking

### Step 4 — Summary Output
- Three sections: full transcript, decisions list, action items list
- One-click copy to clipboard

## Backend API

| Endpoint | Method | Description |
|---|---|---|
| `/transcribe` | POST | Accepts audio file, starts Whisper job, returns `job_id` |
| `/status/{job_id}` | GET | Returns transcription progress |
| `/result/{job_id}` | GET | Returns completed transcript segments |

## Data Structure

Each transcript segment:
```json
{ "id": 1, "text": "今天討論預算問題", "tag": "decision" | "action" | null }
```

## Error Handling

| Scenario | Handling |
|---|---|
| Backend not running | Step 1 shows prompt to start local server |
| Unsupported file format | Show supported formats on upload |
| Transcription failure | Step 2 shows error + retry button |
| Microphone permission denied | Prompt user to enable mic access |

## Out of Scope (this version)

- Language translation
- Multi-format export (PDF, Word, Markdown)
- Agenda / timer management
