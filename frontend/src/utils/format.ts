export function formatDate(createdAt: string): string {
  return (createdAt || '').replace('T', ' ').slice(0, 16)
}

export function priorityLabel(priority: string): string {
  return { low: '低', medium: '中', high: '高' }[priority] ?? priority
}

export function statusLabel(status: string): string {
  return { pending: '待處理', done: '已完成', confirmed: '確認', cancelled: '取消' }[status] ?? status
}
