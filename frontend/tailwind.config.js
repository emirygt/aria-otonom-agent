/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:       '#f3f5f8',
        surface:  '#ffffff',
        border:   '#d8dfea',
        text:     '#101726',
        text2:    '#3f4b60',
        muted:    '#6a7890',
        accent:   '#6c47ff',
      },
    },
  },
  plugins: [],
}
