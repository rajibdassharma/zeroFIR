/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'ksp-navy': '#0b2c4a',
        'ksp-yellow': '#ffd400',
        'ksp-red': '#b10000',
      },
    },
  },
  plugins: [],
};
