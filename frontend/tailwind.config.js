/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'trinetra': {
          dark: '#0c1017',
          surface: '#151c28',
          card: '#1b2434',
          border: '#2a364f',
          accent: '#38bdf8',
          amber: '#f59e0b',
          orange: '#f97316',
          red: '#ef4444',
          green: '#10b981',
          teal: '#14b8a6',
          greyblue: '#64748b'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
