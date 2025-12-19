/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Node category colors
        'semantic-function': {
          bg: '#ede7f6',
          border: '#7b68ee',
          text: '#4c1d95',
        },
        'semantic-value': {
          bg: '#dbeafe',
          border: '#3b82f6',
          text: '#1e3a8a',
        },
        'syntactic-function': {
          bg: '#f1f5f9',
          border: '#64748b',
          text: '#334155',
        },
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
