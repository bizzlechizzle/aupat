/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/renderer/index.html',
    './src/renderer/**/*.{svelte,js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        'aupat-primary': '#1e40af',
        'aupat-secondary': '#64748b',
        'aupat-accent': '#0ea5e9'
      }
    }
  },
  plugins: []
};
