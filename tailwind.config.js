/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html', // Explicitly captures templates inside all apps
    './static/src/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}