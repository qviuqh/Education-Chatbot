/** @type {import('tailwindcss').Config} */
export default {
  // Chỉ định những file nào sẽ được Tailwind quét để tạo CSS
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Nơi bạn có thể thêm các màu sắc, font chữ tùy chỉnh sau này
    },
  },
  plugins: [],
}