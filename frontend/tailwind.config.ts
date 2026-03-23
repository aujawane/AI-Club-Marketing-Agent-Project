import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        dm: ['DM Sans', 'sans-serif'],
      },
      colors: {
        navy: {
          DEFAULT: '#0d1129',
          2: '#111630',
          surface: '#161d3a',
          surface2: '#1c2444',
        },
      },
      backgroundImage: {
        'gradient-purple-cyan': 'linear-gradient(135deg, #8b5cf6, #22d3ee)',
        'gradient-text': 'linear-gradient(90deg, #a78bfa, #22d3ee)',
      },
    },
  },
  plugins: [],
}

export default config
