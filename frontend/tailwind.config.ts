import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep Space Palette
        space: {
          DEFAULT: "#050505",
          50: "#0A0A0B",
          100: "#0F0F10",
          200: "#1A1A1C",
        },
        // Glassmorphic Surfaces
        glass: {
          light: "rgba(255, 255, 255, 0.03)",
          medium: "rgba(255, 255, 255, 0.06)",
          border: "rgba(255, 255, 255, 0.1)",
        },
        // Neon Accents
        cyber: {
          cyan: "#00F2FF",
          purple: "#BC00FF",
          red: "#FF0055",
          green: "#00FF88",
        },
        // Threat Levels
        threat: {
          critical: "#FF0055",
          high: "#FF6B00",
          medium: "#FFB800",
          low: "#00FF88",
        },
        // Legacy support (keeping for backward compatibility)
        void: {
          950: "#050505",
          900: "#0A0A0B",
          800: "#0F0F10",
        },
        cyan: {
          400: "#00F2FF",
          500: "#00F2FF",
        },
        slate: {
          500: "#64748B",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Roboto Mono", "JetBrains Mono", "monospace"],
        display: ["Rajdhani", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      backdropBlur: {
        xs: "2px",
        md: "12px",
        xl: "24px",
      },
      boxShadow: {
        "glow-cyan": "0 0 20px rgba(0, 242, 255, 0.3)",
        "glow-purple": "0 0 20px rgba(188, 0, 255, 0.3)",
        "glow-red": "0 0 20px rgba(255, 0, 85, 0.4)",
        "cyan-glow": "0 0 15px rgba(0, 242, 255, 0.4)",
        "amber-glow": "0 0 15px rgba(245, 158, 11, 0.4)",
        "crimson-glow": "0 0 15px rgba(255, 0, 85, 0.4)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 10px rgba(0, 242, 255, 0.2)" },
          "100%": { boxShadow: "0 0 20px rgba(0, 242, 255, 0.6)" },
        },
      },
    },
  },
  plugins: [
    function ({ addUtilities }: any) {
      addUtilities({
        ".glass": {
          "background-color": "rgba(255, 255, 255, 0.03)",
          "backdrop-filter": "blur(12px)",
          "-webkit-backdrop-filter": "blur(12px)",
          "border": "1px solid rgba(255, 255, 255, 0.1)",
        },
        ".glass-strong": {
          "background-color": "rgba(255, 255, 255, 0.06)",
          "backdrop-filter": "blur(16px)",
          "-webkit-backdrop-filter": "blur(16px)",
          "border": "1px solid rgba(255, 255, 255, 0.15)",
        },
      });
    },
  ],
};

export default config;

