# Checkpoint: YouTube Integration & Paragraph Segmentation

**Date:** 2026-04-09

---

## 1. YouTube Video to Audio

### Decision
- Use **yt-dlp** for downloading audio from YouTube
- Integrate with existing Whisper + Ollama pipeline

### API Design
```
POST /api/youtube
Body: { "url": "https://www.youtube.com/watch?v=..." }
Response: { "job_id": "abc123" }
```

### POC Results (Short Video)
| Item | Value |
|------|-------|
| Video Duration | 152s (2:32) |
| Download Time | 7.6s |
| Transcription Time | 50.5s |
| Total Time | 60.8s |
| Accuracy | High (581 chars, coherent) |

### Long Video Test
- Status: **Running in background**
- URL: `https://www.youtube.com/watch?v=yKq_l_tQeq4`
- Estimated time: 20-30 minutes

### Implementation Scope
1. Backend: `/api/youtube` endpoint (background job)
2. Frontend: URL input field
3. Ollama analysis: Reuse existing flow

---

## 2. Transcript Paragraph Segmentation

### Problem
Current: One sentence per line (Whisper segments)
Desired: Grouped into readable paragraphs

### Decision
- Use **AI semantic segmentation** (Ollama)
- Implementation: **Parallel call** (Option B)

### Architecture
```
Current:  analyze() ─────────────> ~20s
New:      segment_paragraphs() ──> ~15s (parallel)
Total:    max(20, 15) = ~20s (no additional wait)
```

### Benefits
- Separation of concerns
- No impact on existing analysis quality
- No additional wait time (parallel execution)

---

## Next Steps

- [x] Confirm long video test results
- [x] Implement `/api/youtube` endpoint
- [x] Add `segment_paragraphs()` to analyzer.py
- [x] Update frontend UI (index.html)
- [x] Add YouTube URL input to frontend

---

## Dependencies

- yt-dlp (installed in venv)
- ffmpeg (available)
- Ollama + gemma4:e4b (existing)
