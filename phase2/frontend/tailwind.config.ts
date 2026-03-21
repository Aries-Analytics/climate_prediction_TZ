import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  corePlugins: {
    // CRITICAL: disable Preflight so Tailwind's reset does not clobber MUI styles
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#040d1a',
          900: '#0a1628',
          800: '#0f2040',
          700: '#162d55',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  // Safelist dynamic gradient classes used in HowItWorksSection
  safelist: [
    'from-cyan-500', 'to-teal-500',
    'from-teal-500', 'to-teal-600',
    'from-teal-600', 'to-amber-500',
    'from-amber-500', 'to-amber-400',
  ],
}

export default config
