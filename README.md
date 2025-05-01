# Audio-to-Subtitle SSH Tool

This script downloads audio files from a remote Linux server via SSH, converts them to WAV, generates English SRT subtitles using [WhisperX](https://github.com/m-bain/whisperX), and uploads the subtitles back.

## Features

- Recursively finds and downloads audio (`aac`, `mp3`, `ogg`, `wav`, etc.) from a server directory
- Converts to `.wav` if needed (using `ffmpeg`)
- Runs WhisperX to generate `.srt` subtitles with fine granularity
- Uploads generated subtitles back to the server via SFTP

## Requirements

- Python 3.7+
- `ffmpeg` in your PATH
- [WhisperX](https://github.com/m-bain/whisperX)
- Python: `pip install paramiko tqdm`

## Usage

1. Edit the script to set:
   - `SERVER_IP`, `SERVER_PORT`, `USERNAME`, `PRIVATE_KEY_PATH`
2. Run:
   ```bash
   python generate_subs_from_server.py /remote/path/to/search
   ```
   Replace `/remote/path/to/search` with the actual remote directory.

## Notes

- Script uses your SSH private key (default: `~/.ssh/id_rsa`)
- Subtitles are generated per audio file and uploaded to the same directory on the server
- Temporary files are cleaned up automatically

---

*Simple, fast, and automated subtitle workflow for your server audio files!*
