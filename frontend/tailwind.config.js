/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff",
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
        ink: {
          950: "#07060f",
          900: "#0c0a18",
          850: "#121022",
          800: "#191630",
        },
      },
      fontFamily: {
        sans: [
          "Manrope",
          "-apple-system",
          "system-ui",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        glow: "0 8px 30px -10px rgba(99,102,241,.55)",
        "glow-lg": "0 16px 50px -12px rgba(124,58,237,.65)",
        card: "0 16px 40px -24px rgba(0,0,0,.85)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        pop: {
          "0%": { transform: "scale(.9)", opacity: "0" },
          "60%": { transform: "scale(1.03)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-7px)" },
        },
        aurora: {
          "0%,100%": { transform: "translate(0,0) scale(1)" },
          "33%": { transform: "translate(4%,-5%) scale(1.12)" },
          "66%": { transform: "translate(-4%,4%) scale(.94)" },
        },
        shimmer: {
          "100%": { transform: "translateX(200%)" },
        },
      },
      animation: {
        "fade-up": "fade-up .5s cubic-bezier(.2,.7,.2,1) both",
        "fade-in": "fade-in .4s ease both",
        pop: "pop .35s cubic-bezier(.2,.8,.2,1) both",
        float: "float 6s ease-in-out infinite",
        aurora: "aurora 20s ease-in-out infinite",
        shimmer: "shimmer 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
