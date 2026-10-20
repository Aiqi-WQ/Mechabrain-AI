/**
 * 与后端通信：统一 SSE 解析 + 四条能力接口。
 * 所有密钥都在服务端 .env，前端不接触。
 */

export interface SseEvent {
  type: string
  text?: string
  key?: string
  title?: string
  content?: string
  confidence?: string
  notes?: string
  message?: string
  code?: string
  items?: Array<{ book: string; chapter: string; page: string }>
  backend?: string
  disclaimer?: string
}

export interface MetaInfo {
  app: string
  version: string
  capabilities: { chat: boolean; vision: boolean; rag: boolean }
  rag_backend: string
  limits: { max_upload_mb: number }
  disclaimer: string
}

async function parseSse(
  response: Response,
  onEvent: (event: SseEvent) => void,
): Promise<void> {
  if (!response.body) throw new Error('浏览器不支持流式读取')
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      const line = block.trim()
      if (!line.startsWith('data:')) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      try {
        onEvent(JSON.parse(raw) as SseEvent)
      } catch {
        /* 跳过非 JSON 行 */
      }
    }
  }
}

async function postSse(
  url: string,
  init: RequestInit,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(url, { ...init, signal })
  if (!response.ok) {
    let detail = ''
    try {
      const data = (await response.json()) as { detail?: string }
      detail = data.detail ?? ''
    } catch {
      detail = ''
    }
    throw new Error(detail || `请求失败（HTTP ${response.status}）`)
  }
  await parseSse(response, onEvent)
}

export function chatStream(
  mode: string,
  messages: Array<{ role: 'user' | 'assistant'; content: string }>,
  context: string | null,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return postSse(
    '/api/chat',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, messages, context }),
    },
    onEvent,
    signal,
  )
}

export function ragStream(
  question: string,
  scope: { book?: string; chapter?: string },
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return postSse(
    '/api/rag',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, ...scope }),
    },
    onEvent,
    signal,
  )
}

export function visionStream(
  file: File,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const form = new FormData()
  form.append('file', file)
  return postSse('/api/vision', { method: 'POST', body: form }, onEvent, signal)
}

export async function ocrImage(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch('/api/ocr', { method: 'POST', body: form })
  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(data.detail || `识别失败（HTTP ${response.status}）`)
  }
  const data = (await response.json()) as { text: string }
  return data.text
}

export async function fetchMeta(): Promise<MetaInfo> {
  const response = await fetch('/api/meta')
  if (!response.ok) throw new Error('无法获取服务状态')
  return (await response.json()) as MetaInfo
}
