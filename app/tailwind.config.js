/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'ogiggle' : {
          'light': '#ff8a00',
          'dark': '#bd5d1d'
        }
      }
    },
  },
  plugins: [],
}

