// vite.config.js
import { defineConfig } from "file:///C:/Users/Arnav%20Mehta/Desktop/Code-Four/software-engineering-project/node_modules/vite/dist/node/index.js";
import vue from "file:///C:/Users/Arnav%20Mehta/Desktop/Code-Four/software-engineering-project/node_modules/@vitejs/plugin-vue/dist/index.mjs";
var vite_config_default = defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: [".ngrok-free.app", ".ngrok.app"],
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true
      }
    }
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
    allowedHosts: [".ngrok-free.app", ".ngrok.app"]
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxBcm5hdiBNZWh0YVxcXFxEZXNrdG9wXFxcXENvZGUtRm91clxcXFxzb2Z0d2FyZS1lbmdpbmVlcmluZy1wcm9qZWN0XFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxBcm5hdiBNZWh0YVxcXFxEZXNrdG9wXFxcXENvZGUtRm91clxcXFxzb2Z0d2FyZS1lbmdpbmVlcmluZy1wcm9qZWN0XFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLmpzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9Bcm5hdiUyME1laHRhL0Rlc2t0b3AvQ29kZS1Gb3VyL3NvZnR3YXJlLWVuZ2luZWVyaW5nLXByb2plY3QvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgdnVlIGZyb20gJ0B2aXRlanMvcGx1Z2luLXZ1ZSdcclxuXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XHJcbiAgcGx1Z2luczogW3Z1ZSgpXSxcclxuICBzZXJ2ZXI6IHtcclxuICAgIGhvc3Q6IFwiMC4wLjAuMFwiLFxyXG4gICAgcG9ydDogNTE3MyxcclxuICAgIGFsbG93ZWRIb3N0czogW1wiLm5ncm9rLWZyZWUuYXBwXCIsIFwiLm5ncm9rLmFwcFwiXSxcclxuICAgIHByb3h5OiB7XHJcbiAgICAgIFwiL2FwaVwiOiB7XHJcbiAgICAgICAgdGFyZ2V0OiBcImh0dHA6Ly8xMjcuMC4wLjE6NTAwMFwiLFxyXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZVxyXG4gICAgICB9XHJcbiAgICB9XHJcbiAgfSxcclxuICBwcmV2aWV3OiB7XHJcbiAgICBob3N0OiBcIjAuMC4wLjBcIixcclxuICAgIHBvcnQ6IDQxNzMsXHJcbiAgICBhbGxvd2VkSG9zdHM6IFtcIi5uZ3Jvay1mcmVlLmFwcFwiLCBcIi5uZ3Jvay5hcHBcIl1cclxuICB9XHJcbn0pXHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBc2EsU0FBUyxvQkFBb0I7QUFDbmMsT0FBTyxTQUFTO0FBRWhCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxJQUFJLENBQUM7QUFBQSxFQUNmLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLGNBQWMsQ0FBQyxtQkFBbUIsWUFBWTtBQUFBLElBQzlDLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQUEsRUFDQSxTQUFTO0FBQUEsSUFDUCxNQUFNO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixjQUFjLENBQUMsbUJBQW1CLFlBQVk7QUFBQSxFQUNoRDtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
