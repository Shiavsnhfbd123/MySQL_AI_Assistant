/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#07111f',
        panel: '#0b1728',
        line: '#1d3048',
        cyan: '#4de3c1',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      boxShadow: { glow: '0 0 40px rgba(77, 227, 193, .08)' },
    },
  },
  plugins: [],
}
