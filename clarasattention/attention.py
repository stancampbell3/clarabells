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
    """Return a list of player command candidates with optimized settings.

    If a saved `claras_clutch.json` contains a valid `player_cmd`, use that.
    Otherwise return multiple candidates to try in order (with fallbacks).
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'clarasvoice', 'claras_clutch.json')
    # Try to load an existing config; tolerate JSON errors and missing keys
    try:
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg = json.load(f)
            pc = cfg.get('player_cmd')
            if pc and _validate_player_cmd(pc):
                return [pc]  # Return as list for consistency
    except Exception:
        # Corrupted config -> ignore and re-create later
        pass

    system = platform.system()
    candidates = []

    # Build priority list of players with optimized flags
    if system == 'Linux':
        if audio_format == 'mp3':
            candidates = [
                ['mpg123', '-q'],  # quiet mode
                ['mpv', '--really-quiet'],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
                ['play', '-q']  # sox play command
            ]
        elif audio_format == 'ogg':
            candidates = [
                ['mpv', '--really-quiet'],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
                ['play', '-q']
            ]
        else:  # default to wav/pcm - prefer robust players over aplay
            candidates = [
                ['mpv', '--really-quiet'],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
                ['aplay', '--buffer-size=8192'],  # Large buffer to prevent underruns
                ['play', '-q'],
                ['mpg123', '-q']  # Can play WAV files too
            ]
    elif system == 'Darwin':
        # macOS: afplay handles wav and mp3; prefer more robust players
        candidates = [
            ['afplay'],
            ['mpv', '--really-quiet'],
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet']
        ]
    elif system == 'Windows':
        candidates = [['cmd', '/c', 'start', '/wait']]

    # Filter to only available players
    available = []
    for cmd in candidates:
        if _validate_player_cmd(cmd):
            available.append(cmd)

    if not available:
        raise RuntimeError(f"No suitable audio player found for OS: {system}. Try installing 'mpv', 'ffplay', 'aplay' (alsa-utils), 'mpg123', or 'sox'.")

    return available


async def listen_and_play(host: str, port: int):
    uri = f"ws://{host}:{port}/ws/notify"

    async with websockets.connect(uri) as websocket:
        print("Connected to server for notifications.")
        async for guid in websocket:
            print(f"Received GUID: {guid}")
            # Fetch audio stream
            api_url = f"http://{host}:{port}/audio/{guid}"
            try:
                response = requests.get(api_url, stream=True, timeout=30)
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

                player_cmds = get_player_cmd(audio_format)

                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    # Write first chunk and stream the rest
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                    temp_file_path = temp_file.name

                # Try each player in order until one succeeds
                played = False
                last_error = None
                for player_cmd in player_cmds:
                    try:
                        # Suppress stderr to avoid "stream is not nice" messages
                        result = subprocess.run(
                            player_cmd + [temp_file_path],
                            check=True,
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE
                        )
                        played = True
                        print(f"Audio played successfully with {player_cmd[0]}.")
                        break
                    except subprocess.CalledProcessError as e:
                        last_error = e
                        # Try next player
                        continue
                    except Exception as e:
                        last_error = e
                        continue

                if not played and last_error:
                    print(f"All players failed. Last error: {last_error}")

                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

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