module.exports = {
  apps: [
    {
      name: "jetson-gateway",
      script: "main.py", // Your application entry point
      interpreter: "./.venv/bin/python", // Forces PM2 to use your local virtual environment
      cwd: "/home/fuinha/Documents/Faculdade/pipe", // Absolute path to your project root
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
