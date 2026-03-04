/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        slideIn: {
          'from': {
            transform: 'translateX(400px)',
            opacity: '0',
          },
          'to': {
            transform: 'translateX(0)',
            opacity: '1',
          },
        },
      },
      animation: {
        slideIn: 'slideIn 0.3s ease-out',
      },
    },
  },
  plugins: [],
}