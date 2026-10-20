import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
})

export function renderMarkdown(source: string): string {
  return md.render(source || '')
}

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
