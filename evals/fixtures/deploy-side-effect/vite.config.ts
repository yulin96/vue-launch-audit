import { defineConfig } from "vite";

const uploadPlugin = {
  name: "upload-after-build",
  closeBundle() {
    return fetch("https://upload.invalid.example/deploy", { method: "POST" });
  },
};

export default defineConfig({
  plugins: [uploadPlugin],
});
