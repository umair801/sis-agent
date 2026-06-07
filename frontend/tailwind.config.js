/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        surface: {
          DEFAULT: "#f5f6fa",
          card:    "#ffffff",
          border:  "#e4e7ef",
          muted:   "#f0f2f8",
        },
        text: {
          primary:   "#111827",
          secondary: "#4b5563",
          muted:     "#9ca3af",
        },
        sidebar: {
          bg:     "#1e1b4b",
          hover:  "#2d2a6e",
          active: "#4338ca",
          text:   "#c7d2fe",
          muted:  "#818cf8",
        },
      },
      fontFamily: {
        sans:    ["'DM Sans'", "sans-serif"],
        display: ["'Syne'", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        xl:    "0.875rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
}
