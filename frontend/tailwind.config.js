/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        navy: {
          950: '#04080f',
          900: '#060b18',
          800: '#0a1020',
          700: '#0d1628',
        },
      },
      animation: {
        'blob-drift': 'blobDrift 22s ease-in-out infinite',
        'blob-drift-slow': 'blobDriftSlow 30s ease-in-out infinite',
        'blob-drift-fast': 'blobDriftFast 16s ease-in-out infinite',
        'fade-up': 'fadeUp 0.6s ease-out both',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
        'scan': 'scan 3s linear infinite',
      },
      keyframes: {
        blobDrift: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%': { transform: 'translate(40px, -30px) scale(1.05)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.95)' },
        },
        blobDriftSlow: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '50%': { transform: 'translate(-50px, 30px) scale(1.08)' },
        },
        blobDriftFast: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '25%': { transform: 'translate(30px, -40px) scale(1.03)' },
          '75%': { transform: 'translate(-30px, 20px) scale(0.97)' },
        },
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(96,165,250,0.2)' },
          '50%': { boxShadow: '0 0 40px rgba(96,165,250,0.45)' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
