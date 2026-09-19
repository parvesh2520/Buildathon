/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        sidebar: {
          bg: '#0f1117',
          hover: '#1a1d27',
          active: '#1e2235',
          border: '#1e2235',
          text: '#8b92a5',
          textActive: '#e8eaf0',
        },
        brand: {
          DEFAULT: '#6366f1',
          light: '#818cf8',
          dark: '#4f52c8',
        },
        surface: {
          DEFAULT: '#ffffff',
          secondary: '#f8f9fc',
          tertiary: '#f1f3f8',
        },
        border: {
          DEFAULT: '#e4e7ef',
          light: '#f0f2f7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': '0.65rem',
      },
    },
  },
  plugins: [],
};
