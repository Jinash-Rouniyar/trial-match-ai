/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        shellBg: "#0b0c10",
        shellBorder: "#1b1c23",
        surface: "#111217",
        surfaceSoft: "#171821",
      },
    },
  },
  plugins: [],
};

