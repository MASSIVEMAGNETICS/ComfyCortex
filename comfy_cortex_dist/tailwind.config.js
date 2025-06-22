/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}", // Assuming src will be inside comfy_cortex_dist for this simulation
    // If Vue components are directly in comfy_cortex_dist:
    "./*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // or 'media' if preferred, class allows manual toggling
  theme: {
    extend: {
      colors: {
        'cortex-dark': '#0d0d0d',        // Deepest background
        'cortex-bg-primary': '#1a1a1a',  // Primary background for panels, nodes
        'cortex-bg-secondary': '#2c2c2c',// Secondary background, slightly lighter
        'cortex-border': '#404040',      // Borders for elements
        'cortex-text-primary': '#e0e0e0',// Primary text color
        'cortex-text-secondary': '#b0b0b0',// Secondary text color (dimmer)

        'cortex-neon-green': '#39ff14',
        'cortex-neon-cyan': '#00ffff',
        'cortex-neon-magenta': '#ff00ff',
        'cortex-neon-blue': '#007bff',
        'cortex-neon-red': '#ff1744',
        'cortex-neon-yellow': '#f0ff00',

        // Specific UI elements
        'cortex-button-bg': '#2a2a2a',
        'cortex-button-hover-bg': '#383838',
        'cortex-input-bg': '#252525',
      },
      boxShadow: {
        'neon-green': '0 0 5px #39ff14, 0 0 10px #39ff14, 0 0 15px #39ff14, 0 0 20px #39ff14',
        'neon-cyan': '0 0 5px #00ffff, 0 0 10px #00ffff, 0 0 15px #00ffff, 0 0 20px #00ffff',
        'neon-magenta': '0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 15px #ff00ff, 0 0 20px #ff00ff',
        'neon-blue': '0 0 5px #007bff, 0 0 10px #007bff, 0 0 15px #007bff, 0 0 20px #007bff',
      },
      // If we need custom fonts for a more futuristic feel
      // fontFamily: {
      //   'orbitron': ['Orbitron', 'sans-serif'],
      // },
    },
  },
  plugins: [
    // require('@tailwindcss/forms'), // If forms styling is needed
  ],
}
