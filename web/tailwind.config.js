/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        paper: '#ecedea',
        panel: '#e2e4e0',
        paper2: '#e6e8e3',
        ink: '#14203a',
        ink2: '#4c5872',
        ink3: '#848da0',
        line: '#b0b7b1',
        linesoft: '#ccd1cb',
        accent: '#c2402a',
        blueprint: '#2a5c8a',
      },
      fontFamily: {
        sans: ['"Microsoft YaHei"', '"PingFang SC"', '"Hiragino Sans GB"', 'system-ui', 'sans-serif'],
        mono: ['"Cascadia Mono"', 'Consolas', '"SFMono-Regular"', 'monospace'],
      },
    },
  },
  plugins: [],
}
