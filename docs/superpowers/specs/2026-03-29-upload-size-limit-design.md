# Upload Size Limit — Design Spec
**Date:** 2026-03-29

## Overview

Add file size validation for audio uploads. Currently there is no size check on either the client or server. A 200 MB limit is appropriate for compressed meeting recordings (hand phone voice memos, Zoom/Teams exports) up to ~3–4 hours.

## Architecture

| Change | Responsibility |
|---|---|
| Modify `index.html` | Client-side check on file select; immediate inline error |
| Modify `server.py` | Server-side check after read; 413 response |

No changes to `history.html`, `storage.py`, or `analyzer.py`.

## Limit

`MAX_UPLOAD_BYTES = 200 * 1024 * 1024` (200 MB)

## index.html Changes

In the `#fileInput` `change` event handler (currently lines ~745–749), replace the existing handler with:

```javascript
document.getElementById('fileInput').addEventListener('change', (e) => {
  const file = e.target.files[0] || null;
  if (file && file.size > 200 * 1024 * 1024) {
    document.getElementById('file-error').textContent = '檔案過大，上限為 200 MB。';
    document.getElementById('file-error').style.display = 'block';
    selectedFile = null;
    e.target.value = '';
  } else {
    document.getElementById('file-error').style.display = 'none';
    selectedFile = file;
  }
  recordedBlob = null;
  updateSubmitBtn();
});
```

- Oversized file: show error in existing `#file-error`, clear `selectedFile`, reset input value (so the same file can be re-selected after user trims it)
- Valid file: hide any previous error, set `selectedFile` as normal
- `recordedBlob` cleared and `updateSubmitBtn()` called in both paths (same as current behaviour)

## server.py Changes

Add constant near the top of the file (after `ALLOWED_EXTENSIONS`):

```python
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB
```

In the `/transcribe` endpoint, after `content = await file.read()`, add a size check before any processing:

```python
content = await file.read()
if len(content) > MAX_UPLOAD_BYTES:
    raise HTTPException(status_code=413, detail="檔案過大，上限為 200 MB。")
```

The existing client error handler (`if (!res.ok) { ... err.detail ... }`) already displays `detail` strings from HTTP errors, so no UI changes are needed to surface this message.

## Error Messages

| Scenario | Where shown | Message |
|---|---|---|
| File selected > 200 MB | `#file-error` (client-side, immediate) | 檔案過大，上限為 200 MB。 |
| POST with body > 200 MB | `#file-error` (after server response) | 檔案過大，上限為 200 MB。 |

## Testing

- `test_server.py`: one test for the 413 path (mock a large `file.read()` return value)
- Manual: select a file > 200 MB in the browser and confirm the inline error appears without any network request

## Out of Scope

- Per-format size limits
- Progress bar for large uploads
- Streaming upload (chunked transfer)
