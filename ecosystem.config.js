module.exports = {
  apps: [
    {
      name: "audio-processor",
      script: "python3",
      args: "-m audio_processor.main",
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
