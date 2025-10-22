import asyncio
import websockets
import subprocess
import argparse
import os
import requests
import tempfile
import json
import platform
import shutil


def _validate_player_cmd(cmd):
    """Return True if the first element of cmd exists on PATH (or is Windows start)."""
    if not cmd:
        return False
    exe = cmd[0]
    # 'cmd' start on Windows is special
    if exe.lower() in ("cmd", "start"):
        return True
    return shutil.which(exe) is not None


def get_player_cmd(audio_format: str | None = None):
    """Return a player command list appropriate for the detected audio_format.

    If a saved `claras_clutch.json` contains a valid `player_cmd`, use that.
    Otherwise choose sensible defaults per OS and audio format.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'clarasvoice', 'claras_clutch.json')
    # Try to load an existing config; tolerate JSON errors and missing keys
    try:
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f)
            pc = cfg.get('player_cmd')
            if pc and _validate_player_cmd(pc):
                return pc
    except Exception:
        # Corrupted config -> ignore and re-create later
        pass

    system = platform.system()

    # Prefer format-aware players
    if system == 'Linux':
        if audio_format == 'mp3':
            candidates = ['mpg123', 'mpv', 'ffplay', 'play']
        elif audio_format == 'ogg':
            candidates = ['mpv', 'ffplay', 'play']
        else:  # default to wav/pcm
            candidates = ['aplay', 'mpv', 'ffplay', 'play', 'mpg123']

        for c in candidates:
            if shutil.which(c):
                player_cmd = [c]
                if c == 'ffplay':
                    player_cmd = [c, '-nodisp', '-autoexit', '-loglevel', 'quiet']
                return player_cmd
    elif system == 'Darwin':
        # macOS: afplay handles wav and mp3; mpv/ffplay may be installed
        if shutil.which('afplay'):
            return ['afplay']
        for c in ('mpv', 'ffplay'):
            if shutil.which(c):
                if c == 'ffplay':
                    return [c, '-nodisp', '-autoexit', '-loglevel', 'quiet']
                return [c]
    elif system == 'Windows':
        return ['cmd', '/c', 'start', '/wait']

    raise RuntimeError(f"No suitable audio player found for OS: {system}. Try installing 'aplay' (alsa-utils), 'mpg123', 'mpv', or 'sox'.")


async def listen_and_play(host: str, port: int):
    uri = f"ws://{host}:{port}/ws/notify"

    async with websockets.connect(uri) as websocket:
        print("Connected to server for notifications.")
        async for guid in websocket:
            print(f"Received GUID: {guid}")
            # Fetch audio stream
            api_url = f"http://{host}:{port}/audio/{guid}"
            try:
                response = requests.get(api_url, stream=True)
                response.raise_for_status()

                # Try to detect extension from content-type; default to .wav
                ct = response.headers.get('content-type', '')
                if ct.startswith('audio/mpeg') or ct.startswith('audio/mp3'):
                    suffix = '.mp3'
                    audio_format = 'mp3'
                elif ct.startswith('audio/ogg'):
                    suffix = '.ogg'
                    audio_format = 'ogg'
                else:
                    suffix = '.wav'
                    audio_format = 'wav'

                player_cmd = get_player_cmd(audio_format)

                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    # Write first chunk and stream the rest
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                    temp_file_path = temp_file.name

                # Play locally
                try:
                    subprocess.run(player_cmd + [temp_file_path], check=True)
                finally:
                    try:
                        os.unlink(temp_file_path)
                    except Exception:
                        pass
                print("Audio played successfully.")
            except Exception as e:
                print(f"Failed to fetch or play audio: {e}")


def main():
    parser = argparse.ArgumentParser(description="Attention listener for Clara notifications.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    asyncio.run(listen_and_play(args.host, args.port))


if __name__ == "__main__":
    main()