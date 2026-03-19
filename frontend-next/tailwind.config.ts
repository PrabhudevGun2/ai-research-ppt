import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#172032',
          950: '#0b1120',
        },
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0f172a 0%, #0c1a3a 40%, #0f172a 100%)',
        'card-gradient': 'linear-gradient(145deg, #1e293b, #162032)',
        'blue-gradient': 'linear-gradient(135deg, #3b82f6, #2563eb)',
        'success-gradient': 'linear-gradient(135deg, #10b981, #059669)',
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'bounce-subtle': 'bounceSubtle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
      boxShadow: {
        'card': '0 4px 24px rgba(0, 0, 0, 0.3)',
        'card-hover': '0 8px 40px rgba(59, 130, 246, 0.15)',
        'blue-glow': '0 0 20px rgba(59, 130, 246, 0.3)',
        'green-glow': '0 0 20px rgba(16, 185, 129, 0.3)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
