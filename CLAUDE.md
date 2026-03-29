# Meeting Assistant — Claude Code Instructions

## Context Management

After a major feature is merged to master (e.g., after `git merge` or finishing a development branch), remind the user:

> "功能已合併。這是執行 `/compact` 的好時機，可以清理 context 為下個功能騰出空間。"

Do this once per merged feature, not repeatedly.

## Implementation Method by Scale

Match the implementation approach to feature size:

| Scale | Method |
|---|---|
| 1–2 files, < 50 lines, straight-line logic | Inline (edit directly in session) |
| 3–5 files, cross-file concerns | executing-plans |
| Multiple tasks, quality gates needed | subagent-driven-development |

## Subagent Prompts — Worktree Warning

When using git worktrees, always include in every implementer subagent prompt:

> "The repo has TWO copies of the test files — the worktree at `.worktrees/<branch>/tests/` and the main project at `tests/`. Only edit files inside `.worktrees/<branch>/`. Do NOT touch anything in the main project directory."

## Spec Reviewer Prompt

Always include in spec reviewer prompts:

> "If you claim a function, test, or feature does not exist, first run `grep` to confirm. Do not rely solely on Read tool output — large files may be truncated."

## Tech Stack

- Python/FastAPI backend (`server.py`)
- Local Whisper (`language="zh"`) for transcription
- Ollama + `llama3.1:8b` for AI analysis
- Storage: JSON files in `meetings/`
- Frontend: Vanilla HTML/CSS/JS (`index.html`, `history.html`)
- Tests: pytest + anyio[trio], run from project root
- Venv: `source venv/bin/activate`
- Worktrees: `.worktrees/` (gitignored)
