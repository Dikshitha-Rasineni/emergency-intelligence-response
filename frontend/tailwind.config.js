/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EEF3F2", surface: "#FFFFFF", ink: "#0F1E33", muted: "#566476", line: "#DCE3E1",
        navy: { DEFAULT: "#0B1A2E", 2: "#12263F", 3: "#1B3350" },
        teal: { DEFAULT: "#0E5F63", mid: "#0E8C8F", glow: "#6EE7E2", dark: "#0A4A4D", soft: "#E1F2F1" },
        sos: { DEFAULT: "#C8102E", glow: "#FF4A64", dark: "#9E0C24", soft: "#FDE7EB" },
        sun: "#F5B700",
        pri: { critical: "#C8102E", high: "#D2561A", moderate: "#A07C00", low: "#2F7A55" },
      },
      fontFamily: {
        sans: ['"Public Sans"', '"Noto Sans Telugu"', '"Noto Sans Tamil"', '"Noto Sans Devanagari"', "system-ui", "sans-serif"],
      },
      borderRadius: { DEFAULT: "10px", panel: "20px", xl2: "28px" },
      maxWidth: { measure: "68ch" },
      boxShadow: {
        card: "0 18px 40px -18px rgba(15,30,51,.25), 0 2px 6px rgba(15,30,51,.06)",
        lift: "0 28px 60px -20px rgba(15,30,51,.35)",
        glowred: "0 10px 30px -6px rgba(200,16,46,.55)",
        glowteal: "0 10px 30px -6px rgba(14,140,143,.55)",
      },
      keyframes: {
        ring: { "0%": { transform: "scale(.6)", opacity: ".9" }, "100%": { transform: "scale(2.6)", opacity: "0" } },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-10px)" } },
        travel: { "0%": { left: "0%", opacity: "0" }, "10%": { opacity: "1" }, "90%": { opacity: "1" }, "100%": { left: "100%", opacity: "0" } },
        sweep: { to: { transform: "rotate(360deg)" } },
        rise: { "0%": { opacity: "0", transform: "translateY(18px)" }, "100%": { opacity: "1", transform: "none" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: ".35" } },
      },
      animation: {
        ring: "ring 3s cubic-bezier(.2,.6,.3,1) infinite",
        float: "float 6s ease-in-out infinite",
        travel: "travel 4.5s linear infinite",
        sweep: "sweep 7s linear infinite",
        rise: "rise .7s cubic-bezier(.2,.7,.2,1) both",
        shimmer: "shimmer 2.2s linear infinite",
        blink: "blink 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
