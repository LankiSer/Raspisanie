/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Gosuslugi / VKSIT government-style blue palette
        gov: {
          50:  '#e8f0fb',
          100: '#c4d7f5',
          200: '#9ebcee',
          300: '#77a1e7',
          400: '#578ce2',
          500: '#3778dd',
          600: '#1f5abf',   // main brand blue
          700: '#1648a0',
          800: '#0e3780',
          900: '#06265f',
        },
        primary: {
          50:  '#e8f0fb',
          100: '#c4d7f5',
          200: '#9ebcee',
          300: '#77a1e7',
          400: '#578ce2',
          500: '#3778dd',
          600: '#1f5abf',
          700: '#1648a0',
          800: '#0e3780',
          900: '#06265f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
