/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx}", "./components/**/*.{js,jsx}", "./lib/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7B61FF",
        secondary: "#4F9CF9",
        background: "#0B0F19",
        card: "#121826",
        accent: "#A78BFA",
        success: "#34D399",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(123,97,255,0.3), 0 10px 40px rgba(79,156,249,0.15)",
      },
    },
  },
  plugins: [],
};
