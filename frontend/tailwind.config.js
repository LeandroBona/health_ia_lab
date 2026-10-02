/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1726",
        ocean: {
          50: "#eefcfb",
          100: "#d4f7f4",
          200: "#adeee9",
          300: "#77ded9",
          400: "#3ac5c2",
          500: "#18a6a6",
          600: "#118589",
          700: "#126b70",
          800: "#13565b",
          900: "#14484c"
        }
      },
      boxShadow: {
        card: "0 14px 34px -22px rgba(15, 39, 61, 0.32)"
      }
    }
  },
  plugins: []
};

