import type { Meeting } from '../types'

export function exportMarkdown(meeting: Meeting): void {
  const date = (meeting.created_at || '').replace('T', ' ').slice(0, 16)
  const title = meeting.title || '未命名會議'
  const decisions = (meeting.decisions || [])
    .map(d => `- **${d.content}**${d.rationale ? `\n  > ${d.rationale}` : ''}`)
    .join('\n')
  const actions = (meeting.action_items || [])
    .map(a => `- [ ] ${a.content}${a.assignee ? ` (@${a.assignee})` : ''}${a.deadline ? ` — ${a.deadline}` : ''}`)
    .join('\n')
  const md = `# ${title}\n\n**時間：** ${date}\n\n## 決議事項\n\n${decisions || '（無）'}\n\n## 行動項目\n\n${actions || '（無）'}\n\n## 逐字稿\n\n${meeting.transcript || '（無）'}\n`
  downloadText(md, `${meeting.id}.md`, 'text/markdown')
}

export function exportJson(meeting: Meeting): void {
  downloadText(JSON.stringify(meeting, null, 2), `${meeting.id}.json`, 'application/json')
}

function downloadText(content: string, filename: string, type: string): void {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([content], { type }))
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}
