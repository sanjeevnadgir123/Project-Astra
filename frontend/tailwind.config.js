/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hud: {
          cyan: "#00E5FF",
          blue: "#0088FF",
          darkblue: "#001B3A",
          bg: "#020813",
          green: "#00FF66",
          red: "#FF355E",
          yellow: "#FFCC00",
          glow: "rgba(0, 229, 255, 0.15)"
        }
      },
      fontFamily: {
        orbitron: ["Orbitron", "sans-serif"],
        inter: ["Inter", "sans-serif"],
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 15s linear infinite',
        'spin-reverse-slow': 'spin-reverse 10s linear infinite',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        'spin-reverse': {
          from: { transform: 'rotate(360deg)' },
          to: { transform: 'rotate(0deg)' }
        },
        'scanline': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' }
        }
      },
      boxShadow: {
        'neon-cyan': '0 0 15px rgba(0, 229, 255, 0.4)',
        'neon-blue': '0 0 15px rgba(0, 136, 255, 0.4)',
        'neon-green': '0 0 15px rgba(0, 255, 102, 0.4)',
        'neon-red': '0 0 15px rgba(255, 53, 94, 0.4)',
        'panel': 'inset 0 0 20px rgba(0, 136, 255, 0.1), 0 2px 10px rgba(0, 0, 0, 0.5)'
      }
    },
  },
  plugins: [],
}
