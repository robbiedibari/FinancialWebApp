/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/dashboard.html',
    './templates/home.html',
    './templates/login.html',
    './templates/register.html', // Your HTML templates
    './static/css/tailwind_input.css'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
