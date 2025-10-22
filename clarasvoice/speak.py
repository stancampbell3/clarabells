import requests
import tempfile
import subprocess
import os
import argparse
import platform
import shutil


def detect_format_from_magic(first_bytes, content_type=None):
    if content_type:
        ct = content_type.split(';', 1)[0].strip().lower()
        if ct in ('audio/mpeg', 'audio/mp3'):
            return 'mp3'
        if ct in ('audio/wav', 'audio/x-wav', 'audio/wave', 'audio/vnd.wave'):
            return 'wav'
        if ct == 'audio/ogg':
            return 'ogg'
        if ct == 'audio/flac':
            return 'flac'
    # Fallback to magic bytes
    if first_bytes.startswith(b'ID3') or (len(first_bytes) >= 2 and first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0):
        return 'mp3'
    if first_bytes.startswith(b'RIFF') and b'WAVE' in first_bytes[:12]:
        return 'wav'
    if first_bytes.startswith(b'OggS'):
        return 'ogg'
    if first_bytes.startswith(b'fLaC'):
        return 'flac'
    return None


def get_player_candidates(system, audio_format):
    """Return list of player command candidates with optimized settings for reliable playback."""
    candidates = []

    if system == 'Linux':
        if audio_format == 'mp3':
            candidates = [
                ['mpg123', '-q'],
                ['mpv', '--really-quiet'],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
                ['play', '-q']
            ]
        else:  # wav or other
            candidates = [
                ['mpv', '--really-quiet'],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'],
                ['aplay', '--buffer-size=8192'],  # Large buffer prevents underruns
                ['play', '-q'],
                ['mpg123', '-q']
            ]
    elif system == 'Darwin':
        candidates = [
            ['afplay'],
            ['mpv', '--really-quiet'],
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet']
        ]
    elif system == 'Windows':
        candidates = [['cmd', '/c', 'start', '/wait']]
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    # Filter to only available players
    available = []
    for cmd in candidates:
        if cmd[0].lower() in ('cmd', 'start') or shutil.which(cmd[0]):
            available.append(cmd)

    if not available:
        raise RuntimeError(f"No suitable audio player found for OS: {system}. Try installing 'mpv', 'ffplay', 'aplay' (alsa-utils), 'mpg123', or 'sox'.")

    return available


def main():
    parser = argparse.ArgumentParser(description="Clarabells client to request and play audio.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--text", help="Text to speak (optional)")
    parser.add_argument("--outloud", action="store_true", help="If set, download and play the audio locally")
    args = parser.parse_args()

    api_url = f"http://{args.host}:{args.port}/clara/api/v1/speak"
    bearer_token = "mysecrettoken"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    payload = {"text": args.text} if args.text else {}

    try:
        # Use stream=True so we can inspect headers/magic bytes without necessarily downloading the body
        resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
        resp.raise_for_status()

        # If the user didn't ask to play out loud, just verify we received a GUID header and close
        if not args.outloud:
            guid = resp.headers.get('X-Clara-Audio-GUID')
            content_type = resp.headers.get('content-type', '')
            if guid:
                print(f"OK: server synthesized audio GUID={guid}")
            else:
                # No GUID header: server likely returned a raw audio file (e.g., fallback or existing file).
                # We can detect the content-type to confirm it's audio and avoid downloading.
                if content_type.startswith('audio/'):
                    print(f"OK: server returned audio (Content-Type: {content_type}) but no GUID header")
                else:
                    print(f"OK: server returned status {resp.status_code}")
            # Close the connection without reading the rest of the body
            try:
                resp.close()
            except Exception:
                pass
            return

        # Otherwise, stream and play the audio locally (existing behavior)
        it = resp.iter_content(chunk_size=8192)
        first_chunk = next(it, b'')
        content_type = resp.headers.get('content-type')
        audio_format = detect_format_from_magic(first_chunk, content_type)
        if not audio_format:
            audio_format = 'wav'

        suffix = f".{audio_format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(first_chunk)
            for chunk in it:
                if chunk:
                    tmp.write(chunk)
            temp_file_path = tmp.name

        system = platform.system()
        player_candidates = get_player_candidates(system, audio_format)

        # Try each player in order until one succeeds
        played = False
        last_error = None
        for player_cmd in player_candidates:
            try:
                # Suppress stderr to avoid "stream is not nice" messages
                subprocess.run(
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
                continue
            except Exception as e:
                last_error = e
                continue

        if not played:
            raise RuntimeError(f"All audio players failed. Last error: {last_error}")

        os.unlink(temp_file_path)

    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Playback failed: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()