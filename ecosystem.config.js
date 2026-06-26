module.exports = {
  apps: [
    {
      name: "jetson-gateway",
      script: "src/audio_processor/main.py", 
      interpreter: "python3", 
      cwd: "/app",
      autorestart: true,
      watch: false, // Keep false on production/Jetson to save CPU resources
      max_memory_restart: "1G", // Restarts the app if it leaks memory on an edge device
      env: {
        NODE_ENV: "production",
        PYTHONUNBUFFERED: "1", // Crucial: Forces Python to flush prints to PM2 logs immediately
      },
    },
  ],
};
